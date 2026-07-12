#!/usr/bin/env python3
"""Example: join annual private-education indicators to transaction records.

The private-education file uses year-end ``YearMonth`` keys such as ``202412``
for annual observations. This example joins by calendar year and a normalized
parent-city Sigungu key rather than treating the annual record as specific to
December. The original transaction ``YearMonth`` and ``Sigungu`` values are
retained.
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
PRIVATE_EDUCATION_FILE = "Data/Education/Private_Education_Cost_Sigungu.csv"
JOIN_KEY = "Education_Join_Sigungu"
YEAR_KEY = "Calendar_Year"


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
        private_education = package.read_csv(PRIVATE_EDUCATION_FILE)

    tx_join = add_education_join_keys(transactions, output_column=JOIN_KEY)
    edu_join = add_education_join_keys(private_education, output_column=JOIN_KEY)

    tx_join[YEAR_KEY] = pd.to_numeric(tx_join["YearMonth"], errors="raise") // 100
    edu_join[YEAR_KEY] = pd.to_numeric(edu_join["YearMonth"], errors="raise") // 100

    join_columns = [YEAR_KEY, "Sido", JOIN_KEY]
    duplicate_rows = int(edu_join.duplicated(join_columns, keep=False).sum())

    value_columns = [
        column
        for column in private_education.columns
        if column not in {"YearMonth", "Sido", "Sigungu"}
    ]

    # Several general-gu rows can collapse to the same parent-city key. In the
    # released annual file these rows carry the same mapped region type and
    # expenditure value. Confirm that the values are identical before keeping
    # one row per annual parent-city key.
    conflicting_groups = 0
    if duplicate_rows:
        duplicated = edu_join[edu_join.duplicated(join_columns, keep=False)]
        for _, group in duplicated.groupby(join_columns, dropna=False):
            if len(group[value_columns].drop_duplicates()) > 1:
                conflicting_groups += 1
        if conflicting_groups:
            raise ValueError(
                "Conflicting private-education values were found after parent-city "
                f"normalisation in {conflicting_groups} annual join-key group(s)."
            )

    education_for_merge = (
        edu_join[join_columns + value_columns]
        .drop_duplicates(join_columns)
        .copy()
    )

    match_mask = key_match_mask(tx_join, education_for_merge, join_columns)

    merged = tx_join.merge(
        education_for_merge,
        on=join_columns,
        how="left",
        validate="many_to_one",
        suffixes=("", "_Private_Education"),
    )

    diagnostics = {
        "Year": year,
        "Transaction_Rows": int(len(transactions)),
        "Matched_Rows": int(match_mask.sum()),
        "Match_Rate": float(match_mask.mean()),
        "Unmatched_Rows": int((~match_mask).sum()),
        "Collapsed_Duplicate_Source_Rows": duplicate_rows,
        "Conflicting_Annual_Join_Key_Groups": conflicting_groups,
    }

    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        merged.to_csv(output, index=False, encoding="utf-8-sig")

    if sample_output is not None:
        sample_output.parent.mkdir(parents=True, exist_ok=True)
        sample_columns = [
            "YearMonth",
            YEAR_KEY,
            "Sido",
            "Sigungu",
            JOIN_KEY,
            "Region_Type",
            "Private_Education_Expense_10k_KRW",
        ]
        merged[sample_columns].head(100).to_csv(
            sample_output,
            index=False,
            encoding="utf-8-sig",
        )

    return diagnostics


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Example KRAFT annual private-education join."
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
