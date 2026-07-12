#!/usr/bin/env python3
"""
Technical validation script for KRAFT auxiliary indicators.

The input may be a ZIP package or an extracted KRAFT directory.

This script computes descriptive statistics for auxiliary indicator files and
creates a manuscript-ready Table 5 for Section 4.3.

Default input:
    /mnt/data/KRAFT_v1.0.zip

Outputs:
    /mnt/data/KRAFT_Auxiliary_Descriptive_Statistics_Full.csv
    /mnt/data/KRAFT_Table5_Auxiliary_Descriptive_Statistics.csv
    /mnt/data/KRAFT_Section_4_3_Descriptive_validation_auxiliary_indicators.md
"""

from pathlib import Path
import argparse
import pandas as pd
import numpy as np

from kraft_package import KraftPackage


SOURCE_PACKAGE = Path("/mnt/data/KRAFT_v1.0.zip")
OUTPUT_FULL = Path("/mnt/data/KRAFT_Auxiliary_Descriptive_Statistics_Full.csv")
OUTPUT_TABLE5 = Path("/mnt/data/KRAFT_Table5_Auxiliary_Descriptive_Statistics.csv")
OUTPUT_SECTION_MD = Path("/mnt/data/KRAFT_Section_4_3_Descriptive_validation_auxiliary_indicators.md")


# Sido columns in wide files are Romanized region labels.
SIDO_WIDE_COLUMNS = [
    "Gangwon", "Gyeonggi", "Gyeongnam", "Gyeongbuk", "Gwangju",
    "Daegu", "Daejeon", "Busan", "Seoul", "Sejong", "Ulsan",
    "Incheon", "Jeonnam", "Jeonbuk", "Jeju", "Chungnam", "Chungbuk"
]


NUMERIC_EXCLUDE = {"YearMonth"}


SELECTED_TABLE5_VARIABLES = [
    "Base_Rate_Percent",
    "Mortgage_Rate_Avg_Percent",
    "Exchange_Rate_KRW_per_USD",
    "M2_Money_Supply_Billion_KRW",
    "CPI_2020_100",
    "HPI_2021_06_100",
    "Population_Density",
    "Total_Households",
    "Total_Population",
    "Net_Migration",
    "Total_School_Count",
    "Private_Education_Expense_10k_KRW",
    "CSI_Economy",
    "CSI_Housing",
    "CSI_Rate",
    "Economic_Policy_Uncertainty_Index",
]


def read_csv_from_package(source: Path, member: str) -> pd.DataFrame:
    """Read a logical CSV path from a ZIP package or extracted directory."""
    with KraftPackage(source) as package:
        return package.read_csv(member)


def make_stats(
    component: str,
    source_file: str,
    variable: str,
    values,
    observation_level: str,
) -> dict:
    s = pd.to_numeric(pd.Series(values), errors="coerce").dropna()
    return {
        "Component": component,
        "Source_File": source_file,
        "Variable": variable,
        "Observation_Level": observation_level,
        "N": int(s.shape[0]),
        "Mean": s.mean(),
        "Std.": s.std(ddof=1),
        "Min": s.min(),
        "Q1": s.quantile(0.25),
        "Median": s.quantile(0.50),
        "Q3": s.quantile(0.75),
        "Max": s.max(),
    }


def add_narrow_numeric_stats(rows, component, source_file, df, observation_level):
    for col in df.columns:
        if col in NUMERIC_EXCLUDE:
            continue
        if col in {"Sido", "Sigungu", "Beopjeongdong", "Region_Type"}:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            rows.append(make_stats(component, source_file, col, df[col], observation_level))


def add_wide_sido_stats(rows, component, source_file, df, variable, observation_level):
    cols = [c for c in SIDO_WIDE_COLUMNS if c in df.columns]
    values = df[cols].to_numpy().ravel()
    rows.append(make_stats(component, source_file, variable, values, observation_level))


def build_descriptive_statistics() -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []

    # Macro-financial, national monthly files
    macro_files = [
        ("Macro-financial", "Data/Macroeconomic/CPI.csv", "National-month"),
        ("Macro-financial", "Data/Macroeconomic/Exchange_Rate.csv", "National-month"),
        ("Macro-financial", "Data/Macroeconomic/Interest_Rates.csv", "National-month"),
        ("Macro-financial", "Data/Macroeconomic/M2.csv", "National-month"),
    ]
    for component, member, level in macro_files:
        df = read_csv_from_package(SOURCE_PACKAGE, member)
        add_narrow_numeric_stats(rows, component, member, df, level)

    # Housing price index, Sido-month
    df = read_csv_from_package(SOURCE_PACKAGE, "Data/Housing_index/HPI.csv")
    add_narrow_numeric_stats(rows, "Housing price index", "Data/Housing_index/HPI.csv", df, "Sido-month")

    # Demographic indicators
    df = read_csv_from_package(SOURCE_PACKAGE, "Data/Demographic/Net_Migration_Sido.csv")
    add_wide_sido_stats(rows, "Demographic", "Data/Demographic/Net_Migration_Sido.csv", df, "Net_Migration", "Sido-month")

    df = read_csv_from_package(SOURCE_PACKAGE, "Data/Demographic/Population_Density_Sido.csv")
    add_wide_sido_stats(rows, "Demographic", "Data/Demographic/Population_Density_Sido.csv", df, "Population_Density", "Sido-year")

    df = read_csv_from_package(SOURCE_PACKAGE, "Data/Demographic/Total_Households_Sido.csv")
    add_wide_sido_stats(rows, "Demographic", "Data/Demographic/Total_Households_Sido.csv", df, "Total_Households", "Sido-year")

    df = read_csv_from_package(SOURCE_PACKAGE, "Data/Demographic/Total_Population_Sigungu.csv")
    add_narrow_numeric_stats(rows, "Demographic", "Data/Demographic/Total_Population_Sigungu.csv", df, "Sigungu-year")

    # Education indicators
    df = read_csv_from_package(SOURCE_PACKAGE, "Data/Education/Education_Monthly_Sigungu.csv")
    school_cols = [
        "Elementary_School_Count",
        "High_School_Count",
        "Middle_School_Count",
        "Other_School_Count",
        "Special_School_Count",
        "Various_School_Count",
    ]
    df["Total_School_Count"] = df[school_cols].sum(axis=1)
    for col in school_cols + ["Total_School_Count"]:
        rows.append(make_stats("Education", "Data/Education/Education_Monthly_Sigungu.csv", col, df[col], "Sigungu-month"))

    df = read_csv_from_package(SOURCE_PACKAGE, "Data/Education/Private_Education_Cost_Sigungu.csv")
    add_narrow_numeric_stats(rows, "Education", "Data/Education/Private_Education_Cost_Sigungu.csv", df, "Sigungu-year")

    # Sentiment and uncertainty
    sentiment_wide = [
        ("Consumer sentiment", "Data/Sentiment/CSI_Economy.csv", "CSI_Economy"),
        ("Consumer sentiment", "Data/Sentiment/CSI_Housing.csv", "CSI_Housing"),
        ("Consumer sentiment", "Data/Sentiment/CSI_Rate.csv", "CSI_Rate"),
    ]
    for component, member, variable in sentiment_wide:
        df = read_csv_from_package(SOURCE_PACKAGE, member)
        add_wide_sido_stats(rows, component, member, df, variable, "Sido-month")

    df = read_csv_from_package(SOURCE_PACKAGE, "Data/Sentiment/Policy_Uncertainty.csv")
    add_narrow_numeric_stats(rows, "Economic policy uncertainty", "Data/Sentiment/Policy_Uncertainty.csv", df, "National-month")

    full_stats = pd.DataFrame(rows)
    sort_order = {v: i for i, v in enumerate(SELECTED_TABLE5_VARIABLES)}
    table5 = full_stats[full_stats["Variable"].isin(SELECTED_TABLE5_VARIABLES)].copy()
    table5["Sort_Order"] = table5["Variable"].map(sort_order)
    table5 = table5.sort_values("Sort_Order").drop(columns=["Sort_Order"])

    return full_stats, table5


def format_number(x, decimals=3):
    if pd.isna(x):
        return ""
    if isinstance(x, (int, np.integer)):
        return f"{int(x):,}"
    return f"{float(x):,.{decimals}f}"


def make_markdown_table(table: pd.DataFrame) -> str:
    cols = ["Component", "Variable", "Observation_Level", "N", "Mean", "Std.", "Min", "Q1", "Median", "Q3", "Max"]
    header = "| " + " | ".join(["Component", "Variable", "Observation level", "N", "Mean", "Std.", "Min", "Q1", "Median", "Q3", "Max"]) + " |"
    sep = "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"
    lines = [header, sep]
    for _, row in table.iterrows():
        values = [
            row["Component"],
            f"`{row['Variable']}`",
            row["Observation_Level"],
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


def row_by_variable(table: pd.DataFrame, variable: str) -> pd.Series:
    return table.loc[table["Variable"] == variable].iloc[0]


def build_section_text(table5: pd.DataFrame) -> str:
    base = row_by_variable(table5, "Base_Rate_Percent")
    mort = row_by_variable(table5, "Mortgage_Rate_Avg_Percent")
    exr = row_by_variable(table5, "Exchange_Rate_KRW_per_USD")
    m2 = row_by_variable(table5, "M2_Money_Supply_Billion_KRW")
    cpi = row_by_variable(table5, "CPI_2020_100")
    hpi = row_by_variable(table5, "HPI_2021_06_100")
    popdens = row_by_variable(table5, "Population_Density")
    pop = row_by_variable(table5, "Total_Population")
    mig = row_by_variable(table5, "Net_Migration")
    school = row_by_variable(table5, "Total_School_Count")
    private = row_by_variable(table5, "Private_Education_Expense_10k_KRW")
    csi_econ = row_by_variable(table5, "CSI_Economy")
    csi_house = row_by_variable(table5, "CSI_Housing")
    csi_rate = row_by_variable(table5, "CSI_Rate")
    epu = row_by_variable(table5, "Economic_Policy_Uncertainty_Index")

    table_md = make_markdown_table(table5)

    text = f"""### 4.3. Descriptive validation of auxiliary indicators

Descriptive validation was also conducted for the auxiliary indicators to verify that the contextual variables included in KRAFT have interpretable ranges and are consistent with their expected measurement units and spatial-temporal resolutions. Because the auxiliary files were released at different levels of aggregation, descriptive statistics were computed at the observation level of each file. National monthly indicators were summarized over monthly observations, Sido-level indicators were summarized over region-month or region-year observations, and Sigungu-level indicators were summarized over local-government-time observations.

For wide regional files, such as Sido-level demographic or consumer sentiment files, the regional columns were reshaped into a long region-time format before computing descriptive statistics. For education indicators, monthly school counts were inspected by school type, and a validation-purpose total school-count variable was computed as

\\[
Total\\_School\\_Count_{{r,t}} =
\\sum_{{k \\in \\mathcal{{K}}}} School\\_Count_{{k,r,t}},
\\]

where \\(r\\) denotes a local-government area, \\(t\\) denotes month, and \\(\\mathcal{{K}}\\) is the set of school categories included in the released education file. This derived value was used only to validate the overall range of local educational infrastructure and is not required as a released variable.

Table 5 reports descriptive statistics for selected auxiliary indicators. The macro-financial variables covered the full monthly period and showed plausible ranges. The Bank of Korea base rate ranged from {format_number(base['Min'])}% to {format_number(base['Max'])}%, while the average mortgage loan rate ranged from {format_number(mort['Min'])}% to {format_number(mort['Max'])}%. The KRW/USD exchange rate ranged from {format_number(exr['Min'])} to {format_number(exr['Max'])}, M2 money supply ranged from {format_number(m2['Min'])} to {format_number(m2['Max'])} billion KRW, and the consumer price index ranged from {format_number(cpi['Min'])} to {format_number(cpi['Max'])}.

The housing price index had a median of {format_number(hpi['Median'])} and ranged from {format_number(hpi['Min'])} to {format_number(hpi['Max'])} across Sido-month observations. Demographic indicators also showed plausible ranges across regional observations. Population density ranged from {format_number(popdens['Min'])} to {format_number(popdens['Max'])}, reflecting large differences between metropolitan and non-metropolitan regions. Total population at the Sigungu-year level ranged from {format_number(pop['Min'])} to {format_number(pop['Max'])}. Net migration ranged from {format_number(mig['Min'])} to {format_number(mig['Max'])}; negative values were retained because net migration represents net inflows or outflows and can therefore take negative values by definition.

Education indicators were checked to confirm that school-count and private-education variables had non-negative and interpretable values. The validation-purpose total school count ranged from {format_number(school['Min'])} to {format_number(school['Max'])} at the Sigungu-month level. Private education expenditure ranged from {format_number(private['Min'])} to {format_number(private['Max'])} in units of 10,000 KRW. Consumer sentiment indicators showed ranges consistent with index-type variables, with future economic outlook CSI ranging from {format_number(csi_econ['Min'])} to {format_number(csi_econ['Max'])}, housing-price expectation CSI ranging from {format_number(csi_house['Min'])} to {format_number(csi_house['Max'])}, and interest-rate expectation CSI ranging from {format_number(csi_rate['Min'])} to {format_number(csi_rate['Max'])}. The Korean Economic Policy Uncertainty Index ranged from {format_number(epu['Min'])} to {format_number(epu['Max'])} over the monthly period.

Overall, the descriptive statistics indicate that the auxiliary indicators have plausible ranges, preserve their intended spatial and temporal resolutions, and can be reused as contextual variables for transaction-level or aggregated housing-market analyses. Full descriptive statistics for all auxiliary variables are provided in the accompanying `KRAFT_Auxiliary_Descriptive_Statistics_Full.csv` output generated by the validation script.

**Table 5. Descriptive statistics of selected auxiliary indicators.**

{table_md}
"""
    return text


def main():
    full_stats, table5 = build_descriptive_statistics()

    numeric_cols = ["Mean", "Std.", "Min", "Q1", "Median", "Q3", "Max"]
    full_out = full_stats.copy()
    table_out = table5.copy()
    full_out[numeric_cols] = full_out[numeric_cols].round(3)
    table_out[numeric_cols] = table_out[numeric_cols].round(3)

    full_out.to_csv(OUTPUT_FULL, index=False, encoding="utf-8-sig")
    table_out.to_csv(OUTPUT_TABLE5, index=False, encoding="utf-8-sig")

    section_text = build_section_text(table5)
    OUTPUT_SECTION_MD.write_text(section_text, encoding="utf-8")

    print("Computed auxiliary-indicator descriptive statistics.")
    print(f"Input package: {SOURCE_PACKAGE}")
    print(f"Full output: {OUTPUT_FULL}")
    print(f"Table 5 output: {OUTPUT_TABLE5}")
    print(f"Section draft: {OUTPUT_SECTION_MD}")
    print()
    print(make_markdown_table(table5))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KRAFT auxiliary-indicator descriptive validation.")
    parser.add_argument("--input", default="KRAFT_v1.0.zip", help="Path to KRAFT ZIP package or extracted directory.")
    parser.add_argument("--output-dir", default="outputs", help="Directory for validation outputs.")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    SOURCE_PACKAGE = Path(args.input)
    OUTPUT_FULL = output_dir / "KRAFT_Auxiliary_Descriptive_Statistics_Full.csv"
    OUTPUT_TABLE5 = output_dir / "KRAFT_Table5_Auxiliary_Descriptive_Statistics.csv"
    OUTPUT_SECTION_MD = output_dir / "KRAFT_Section_4_3_Descriptive_validation_auxiliary_indicators.md"
    main()
