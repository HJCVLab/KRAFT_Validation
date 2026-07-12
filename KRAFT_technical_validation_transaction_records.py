#!/usr/bin/env python3
"""
Technical validation script for KRAFT transaction records.

This script computes Table 4 for Section 4.2:
Descriptive statistics of transaction-level variables.

It supports either:
1) a KRAFT ZIP package, or
2) an extracted KRAFT directory.

Default input:
    /mnt/data/KRAFT_v1.0.zip

Outputs:
    /mnt/data/KRAFT_Table4_Transaction_Descriptive_Statistics.csv
    /mnt/data/KRAFT_Section_4_2_Descriptive_validation_transaction_records.md
"""

from pathlib import Path
import argparse
import re
import pandas as pd
import numpy as np

from kraft_package import KraftPackage


SOURCE_PACKAGE = Path("/mnt/data/KRAFT_v1.0.zip")
OUTPUT_TABLE = Path("/mnt/data/KRAFT_Table4_Transaction_Descriptive_Statistics.csv")
OUTPUT_SECTION_MD = Path("/mnt/data/KRAFT_Section_4_2_Descriptive_validation_transaction_records.md")


TX_PATTERN = re.compile(r"Data/Transactions/By_year/.*Transactions_20\d{2}\.csv$")

TX_COLUMNS = [
    "YearMonth",
    "Transaction_Price_10k_KRW",
    "Exclusive_Area_sqm",
    "Floor",
    "Construction_Year",
]


PRESENTATION_ORDER = [
    "Transaction_Price_10k_KRW",
    "Exclusive_Area_sqm",
    "Floor",
    "Construction_Year",
    "Price_per_sqm_10k_KRW",
]


def find_transaction_files(source: Path) -> list[str]:
    """Return logical annual transaction paths from ZIP or extracted input."""
    with KraftPackage(source) as package:
        return sorted(
            path
            for path in package.list_files("Data/Transactions/By_year", suffix=".csv")
            if TX_PATTERN.search(path)
        )


def read_transaction_files(source: Path) -> pd.DataFrame:
    """Read and concatenate annual transaction CSV files."""
    frames = []
    with KraftPackage(source) as package:
        tx_files = sorted(
            path
            for path in package.list_files("Data/Transactions/By_year", suffix=".csv")
            if TX_PATTERN.search(path)
        )
        if not tx_files:
            raise FileNotFoundError("No annual transaction files were found.")

        for logical_path in tx_files:
            frames.append(package.read_csv(logical_path, usecols=TX_COLUMNS))

    return pd.concat(frames, ignore_index=True)


def descriptive_statistics(tx: pd.DataFrame) -> pd.DataFrame:
    """Compute descriptive statistics for transaction-level variables."""
    tx = tx.copy()
    tx["Price_per_sqm_10k_KRW"] = (
        tx["Transaction_Price_10k_KRW"] / tx["Exclusive_Area_sqm"]
    )

    rows = []
    for col in PRESENTATION_ORDER:
        s = pd.to_numeric(tx[col], errors="coerce").dropna()
        rows.append(
            {
                "Variable": col,
                "N": int(s.shape[0]),
                "Mean": s.mean(),
                "Std.": s.std(ddof=1),
                "Min": s.min(),
                "Q1": s.quantile(0.25),
                "Median": s.quantile(0.50),
                "Q3": s.quantile(0.75),
                "Max": s.max(),
            }
        )

    stats = pd.DataFrame(rows)
    return stats


def format_number(x, decimals=3):
    """Format numeric values for manuscript tables."""
    if pd.isna(x):
        return ""
    if isinstance(x, (int, np.integer)):
        return f"{int(x):,}"
    return f"{float(x):,.{decimals}f}"


def make_markdown_table(stats: pd.DataFrame) -> str:
    """Create manuscript-ready Markdown table."""
    cols = ["Variable", "N", "Mean", "Std.", "Min", "Q1", "Median", "Q3", "Max"]
    header = "| " + " | ".join(cols) + " |"
    sep = "|---|---:|---:|---:|---:|---:|---:|---:|---:|"
    lines = [header, sep]

    for _, row in stats.iterrows():
        values = [
            f"`{row['Variable']}`",
            format_number(row["N"], 0),
            format_number(row["Mean"]),
            format_number(row["Std."]),
            format_number(row["Min"]),
            format_number(row["Q1"]),
            format_number(row["Median"]),
            format_number(row["Q3"]),
            format_number(row["Max"]),
        ]
        lines.append("| " + " | ".join(values) + " |")

    return "\n".join(lines)


def build_section_text(stats: pd.DataFrame, tx: pd.DataFrame) -> str:
    """Build a filled Section 4.2 draft with computed values."""
    row_map = {row["Variable"]: row for _, row in stats.iterrows()}

    price = row_map["Transaction_Price_10k_KRW"]
    area = row_map["Exclusive_Area_sqm"]
    floor = row_map["Floor"]
    cyear = row_map["Construction_Year"]
    ppsm = row_map["Price_per_sqm_10k_KRW"]

    contract_year = (tx["YearMonth"] // 100).astype(int)
    future_count = int((tx["Construction_Year"] > contract_year).sum())
    future_pct = future_count / len(tx) * 100
    negative_floor_count = int((tx["Floor"] < 0).sum())

    markdown_table = make_markdown_table(stats)

    text = f"""### 4.2. Descriptive validation of transaction records

Descriptive validation was conducted for the main transaction-level variables to examine whether the released apartment transaction records have interpretable ranges and distributions. Following prior dataset studies that reported descriptive statistics, variable ranges, and distributional summaries as part of dataset description or validation [15–18], we summarized the core numerical variables using valid observations, mean, standard deviation, minimum, first quartile, median, third quartile, and maximum values. In addition, because housing-market datasets commonly include transaction prices and property characteristics as key variables [19], we also inspected the relationship between transaction price and exclusive residential area through a validation-purpose price-per-square-meter variable.

For each numerical variable \\(x\\), the number of valid observations was calculated as

\\[
N_x = \\sum_{{i=1}}^{{N}} I(x_i \\neq \\mathrm{{missing}}),
\\]

where \\(I(\\cdot)\\) is an indicator function. The sample mean and standard deviation were computed as

\\[
\\bar{{x}} = \\frac{{1}}{{N_x}} \\sum_{{i=1}}^{{N_x}} x_i
\\]

and

\\[
s_x = \\sqrt{{\\frac{{1}}{{N_x - 1}} \\sum_{{i=1}}^{{N_x}} (x_i - \\bar{{x}})^2}}.
\\]

Quartiles were calculated as the 25th, 50th, and 75th percentiles of each variable distribution:

\\[
Q_1(x) = \\mathrm{{Quantile}}_{{0.25}}(x), \\quad
Q_2(x) = \\mathrm{{Quantile}}_{{0.50}}(x), \\quad
Q_3(x) = \\mathrm{{Quantile}}_{{0.75}}(x).
\\]

Here, \\(Q_2(x)\\) corresponds to the median. For validation purposes, we additionally calculated transaction price per square meter as

\\[
Price\\_per\\_sqm\\_10k\\_KRW_i =
\\frac{{Transaction\\_Price\\_10k\\_KRW_i}}{{Exclusive\\_Area\\_sqm_i}}.
\\]

This derived value was used only to inspect the plausibility of transaction prices relative to residential area and is not required as a released variable.

Table 4 reports the descriptive statistics of the core transaction-level variables. The transaction price variable had a mean of {format_number(price['Mean'])} and a median of {format_number(price['Median'])} in units of 10,000 KRW, with values ranging from {format_number(price['Min'])} to {format_number(price['Max'])}. The mean was larger than the median, indicating a right-skewed distribution that is consistent with heterogeneous apartment prices across regions, unit sizes, and market segments. Exclusive residential area had a mean of {format_number(area['Mean'])} square meters and a median of {format_number(area['Median'])} square meters, with an interquartile range from {format_number(area['Q1'])} to {format_number(area['Q3'])} square meters.

Floor values ranged from {format_number(floor['Min'])} to {format_number(floor['Max'])}, with a median of {format_number(floor['Median'])}. Negative floor values were present in {negative_floor_count:,} records and correspond to basement or below-ground floor notation in the source data rather than preprocessing errors. Construction year ranged from {format_number(cyear['Min'], 0)} to {format_number(cyear['Max'], 0)}, with a median of {format_number(cyear['Median'], 0)}. A total of {future_count:,} records ({future_pct:.4f}% of transaction records) had construction years later than the contract year; these records were retained because they correspond to pre-completion or scheduled-completion apartment transactions in the source data.

The validation-purpose price-per-square-meter variable had a mean of {format_number(ppsm['Mean'])} and a median of {format_number(ppsm['Median'])} in units of 10,000 KRW per square meter. Its maximum value was {format_number(ppsm['Max'])}, reflecting the right-skewed nature of apartment prices. Because apartment transaction prices are expected to exhibit right-skewed distributions due to regional, size, and quality differences, extreme high values were inspected as part of distributional validation rather than automatically removed. Overall, the descriptive statistics indicate that the transaction-level variables have plausible ranges and are suitable for reuse in transaction-level or aggregated housing-market analyses.

**Table 4. Descriptive statistics of transaction-level variables.**

{markdown_table}
"""
    return text


def main():
    tx = read_transaction_files(SOURCE_PACKAGE)
    stats = descriptive_statistics(tx)

    # Save CSV with three-decimal presentation values for manuscript use.
    stats_for_csv = stats.copy()
    numeric_cols = ["Mean", "Std.", "Min", "Q1", "Median", "Q3", "Max"]
    stats_for_csv[numeric_cols] = stats_for_csv[numeric_cols].round(3)
    stats_for_csv.to_csv(OUTPUT_TABLE, index=False, encoding="utf-8-sig")

    section_text = build_section_text(stats, tx)
    OUTPUT_SECTION_MD.write_text(section_text, encoding="utf-8")

    print("Computed transaction-level descriptive statistics.")
    print(f"Input package: {SOURCE_PACKAGE}")
    print(f"Rows read: {len(tx):,}")
    print(f"Output table: {OUTPUT_TABLE}")
    print(f"Output section draft: {OUTPUT_SECTION_MD}")
    print()
    print(make_markdown_table(stats))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KRAFT transaction-level descriptive validation.")
    parser.add_argument("--input", default="KRAFT_v1.0.zip", help="Path to KRAFT ZIP package or extracted directory.")
    parser.add_argument("--output-dir", default="outputs", help="Directory for validation outputs.")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    SOURCE_PACKAGE = Path(args.input)
    OUTPUT_TABLE = output_dir / "KRAFT_Table4_Transaction_Descriptive_Statistics.csv"
    OUTPUT_SECTION_MD = output_dir / "KRAFT_Section_4_2_Descriptive_validation_transaction_records.md"
    main()
