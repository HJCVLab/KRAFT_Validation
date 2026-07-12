#!/usr/bin/env python3
"""Example: join transaction records with monthly education indicators.

The transaction files preserve general-gu labels such as ``용인시 수지구`` and
``수원시 영통구``. The education file is aggregated at the parent-city level
(``용인시`` and ``수원시``). This example creates a dedicated join key without
modifying the original ``Sigungu`` field.

The script reports the exact-key match rate and the match rate after parent-city
normalisation. It can optionally write the merged result for one year.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import re

import pandas as pd

from kraft_package import KraftPackage
from kraft_region_join import add_education_join_keys


TX_PATTERN = re.compile(
    r"^Data/Transactions/By_year/.*Transactions_(?P<year>20\d{2})\.csv$"
)
EDUCATION_FILE = "Data/Education/Education_Monthly_Sigungu.csv"
JOIN_KEY = "Education_Join_Sigungu"


def transaction_file_for_year(package: KraftPackage, year: int) -> str:
    matches = []
    for path in package.list_files("Data/Transactions/By_year", suffix=".csv"):
        match = TX_PATTERN.match(path)
        if match and int(match.group("year")) == year:
            matches.append(path)
    if len(matches) != 1:
        raise FileNotFoundError(
            f"Expected one transaction file for {year}, found {len(matches)}: {matches}"
        )
    return matches[0]


def key_match_mask(
    left: pd.DataFrame,
    right: pd.DataFrame,
    columns: list[str],
) -> pd.Series:
    right_index = pd.MultiIndex.from_frame(right[columns].drop_duplicates())
    left_index = pd.MultiIndex.from_frame(left[columns])
    return pd.Series(left_index.isin(right_index), index=left.index)


def run_example(
    source: Path,
    year: int,
    output: Path | None,
    sample_output: Path | None,
) -> dict:
    with KraftPackage(source) as package:
        tx_file = transaction_file_for_year(package, year)
        transactions = package.read_csv(tx_file)
        education = package.read_csv(EDUCATION_FILE)

    exact_columns = ["YearMonth", "Sido", "Sigungu"]
    exact_mask = key_match_mask(transactions, education, exact_columns)

    tx_join = add_education_join_keys(transactions, output_column=JOIN_KEY)
    edu_join = add_education_join_keys(education, output_column=JOIN_KEY)

    normalised_columns = ["YearMonth", "Sido", JOIN_KEY]
    duplicate_education_keys = int(
        edu_join.duplicated(normalised_columns, keep=False).sum()
    )
    if duplicate_education_keys:
        raise ValueError(
            "Education data contain duplicate rows after Sigungu normalisation: "
            f"{duplicate_education_keys} rows. Review the aggregation rule before merging."
        )

    normalised_mask = key_match_mask(tx_join, edu_join, normalised_columns)

    diagnostics = {
        "Year": year,
        "Transaction_Rows": int(len(transactions)),
        "Exact_Key_Matched_Rows": int(exact_mask.sum()),
        "Exact_Key_Match_Rate": float(exact_mask.mean()),
        "Normalised_Key_Matched_Rows": int(normalised_mask.sum()),
        "Normalised_Key_Match_Rate": float(normalised_mask.mean()),
        "Unmatched_Rows_After_Normalisation": int((~normalised_mask).sum()),
        "Education_Duplicate_Keys_After_Normalisation": duplicate_education_keys,
    }

    education_value_columns = [
        column
        for column in education.columns
        if column not in {"Sido", "Sigungu"}
    ]
    education_for_merge = edu_join[
        ["Sido", JOIN_KEY] + education_value_columns
    ].copy()

    # YearMonth is already included in education_value_columns. The original
    # transaction Sigungu is retained, while JOIN_KEY is used only for merging.
    merged = tx_join.merge(
        education_for_merge,
        on=["YearMonth", "Sido", JOIN_KEY],
        how="left",
        validate="many_to_one",
        suffixes=("", "_Education"),
    )

    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        merged.to_csv(output, index=False, encoding="utf-8-sig")

    if sample_output is not None:
        sample_output.parent.mkdir(parents=True, exist_ok=True)
        sample_columns = [
            "YearMonth",
            "Sido",
            "Sigungu",
            JOIN_KEY,
            "Elementary_School_Count",
            "Middle_School_Count",
            "High_School_Count",
        ]
        merged[sample_columns].head(100).to_csv(
            sample_output,
            index=False,
            encoding="utf-8-sig",
        )

    return diagnostics


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Example KRAFT transaction-to-education join."
    )
    parser.add_argument(
        "--input",
        default="../Dataset/KRAFT_v1.0",
        help="Path to KRAFT ZIP package or extracted directory.",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=2024,
        choices=range(2015, 2025),
        metavar="2015-2024",
        help="Annual transaction file used in the example.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path for the full merged CSV.",
    )
    parser.add_argument(
        "--sample-output",
        type=Path,
        default=None,
        help="Optional path for a 100-row merged sample CSV.",
    )
    args = parser.parse_args()

    diagnostics = run_example(
        Path(args.input),
        args.year,
        args.output,
        args.sample_output,
    )
    print(pd.DataFrame([diagnostics]).to_string(index=False))


if __name__ == "__main__":
    main()
