#!/usr/bin/env python3
"""Technical validation for KRAFT metadata and package consistency.

The input may be either a KRAFT ZIP package or an extracted directory. ZIP
packages with a top-level release folder such as ``KRAFT_v1.0/`` are handled
automatically.
"""

from pathlib import Path
import argparse
import re

import pandas as pd

from kraft_package import KraftPackage


SOURCE_PACKAGE = Path("/mnt/data/KRAFT_v1.0.zip")

OUTPUT_REPORT = Path("/mnt/data/KRAFT_Metadata_Consistency_Report.csv")
OUTPUT_FILE_COVERAGE = Path("/mnt/data/KRAFT_Metadata_File_Coverage.csv")
OUTPUT_VARIABLE_COVERAGE = Path("/mnt/data/KRAFT_Variable_Dictionary_Coverage.csv")
OUTPUT_SOURCE_COVERAGE = Path("/mnt/data/KRAFT_Source_Metadata_Coverage.csv")
OUTPUT_RELEASED_VARIABLE_COVERAGE = Path(
    "/mnt/data/KRAFT_Source_Metadata_Released_Variables_Coverage.csv"
)
OUTPUT_SECTION_MD = Path(
    "/mnt/data/KRAFT_Section_4_5_Metadata_consistency_and_validation_outputs.md"
)

EXPECTED_DOCUMENTATION_FILES = [
    "README.md",
    "LICENSE",
    "CITATION.cff",
    "Variable_Dictionary.csv",
    "Source_Metadata.csv",
    "Region_Mapping.csv",
    "Validation_Report.csv",
    "Preprocessing_Summary.md",
]

DATA_FILE_PATTERN = re.compile(r"^Data/.+\.csv$")
TX_PATTERN = re.compile(
    r"^Data/Transactions/By_year/.*Transactions_20\d{2}\.csv$"
)


def normalise_path(value) -> str:
    """Normalise metadata paths to forward-slash logical paths."""
    text = str(value).replace("\\", "/").strip()
    while text.startswith("./"):
        text = text[2:]
    return text.lstrip("/")


def normalise_var_list(value) -> list[str]:
    if pd.isna(value):
        return []
    parts = re.split(r";|,", str(value))
    return [p.strip().strip("`") for p in parts if p.strip()]


def source_file_matches(actual_file: str, metadata_file: str) -> bool:
    actual_file = normalise_path(actual_file)
    metadata_file = normalise_path(metadata_file)
    if actual_file == metadata_file:
        return True
    if metadata_file.endswith("_Transactions_YYYY.csv") and TX_PATTERN.match(actual_file):
        return True
    if "Transactions_YYYY.csv" in metadata_file and TX_PATTERN.match(actual_file):
        return True
    return False


def best_metadata_source_for_file(
    actual_file: str,
    metadata_files: list[str],
) -> str | None:
    normalised = [(m, normalise_path(m)) for m in metadata_files]
    exact = [original for original, clean in normalised if actual_file == clean]
    if exact:
        return exact[0]
    candidates = [
        original
        for original, clean in normalised
        if source_file_matches(actual_file, clean)
    ]
    return candidates[0] if candidates else None


def run_validation() -> pd.DataFrame:
    rows: list[dict] = []

    with KraftPackage(SOURCE_PACKAGE) as package:
        names = package.logical_files
        name_set = set(names)

        data_files = sorted(n for n in names if DATA_FILE_PATTERN.match(n))
        tx_files = sorted(n for n in data_files if TX_PATTERN.match(n))

        file_rows = []
        for expected in EXPECTED_DOCUMENTATION_FILES:
            present = package.exists(expected)
            file_rows.append(
                {
                    "File": expected,
                    "Present": present,
                    "Status": "Pass" if present else "Warning",
                    "Notes": "" if present else (
                        "Expected for final release but not found in the inspected package."
                    ),
                }
            )

        ds_store_files = [n for n in names if n.endswith(".DS_Store")]
        code_dir_exists = any(n.startswith("Code/") for n in names)
        kraft_tx_naming = (
            all("KRAFT_Transactions_" in n for n in tx_files) if tx_files else False
        )
        kapt_tx_naming = any("K_APT_Transactions_" in n for n in tx_files)

        vd = (
            package.read_csv("Variable_Dictionary.csv")
            if package.exists("Variable_Dictionary.csv")
            else pd.DataFrame()
        )
        sm = (
            package.read_csv("Source_Metadata.csv")
            if package.exists("Source_Metadata.csv")
            else pd.DataFrame()
        )
        rm = (
            package.read_csv("Region_Mapping.csv")
            if package.exists("Region_Mapping.csv")
            else pd.DataFrame()
        )
        vr = (
            package.read_csv("Validation_Report.csv")
            if package.exists("Validation_Report.csv")
            else pd.DataFrame()
        )

        file_columns = {
            logical_path: package.read_csv_header(logical_path)
            for logical_path in data_files
        }

        # Source metadata coverage.
        metadata_files = (
            sm["Released_File"].dropna().astype(str).tolist()
            if not sm.empty and "Released_File" in sm.columns
            else []
        )
        source_rows = []
        for actual_file in data_files:
            match = best_metadata_source_for_file(actual_file, metadata_files)
            source_rows.append(
                {
                    "Actual_Data_File": actual_file,
                    "Matched_Source_Metadata_Record": match or "",
                    "Documented": bool(match),
                    "Status": "Pass" if match else "Fail",
                }
            )
        source_coverage = pd.DataFrame(source_rows)

        # Variable dictionary coverage.
        vd_files = (
            vd["Source_File"].dropna().astype(str).unique().tolist()
            if not vd.empty and "Source_File" in vd.columns
            else []
        )
        var_rows = []
        for actual_file in data_files:
            matched_vd_source = best_metadata_source_for_file(actual_file, vd_files)
            if matched_vd_source:
                documented_vars = set(
                    vd.loc[
                        vd["Source_File"].astype(str) == matched_vd_source,
                        "Variable_Name",
                    ]
                    .dropna()
                    .astype(str)
                    .tolist()
                )
            else:
                documented_vars = set()

            for column in file_columns[actual_file]:
                documented = column in documented_vars
                var_rows.append(
                    {
                        "Actual_Data_File": actual_file,
                        "Matched_Variable_Dictionary_Source_File": (
                            matched_vd_source or ""
                        ),
                        "Variable": column,
                        "Documented": documented,
                        "Status": "Pass" if documented else "Fail",
                    }
                )
        var_coverage = pd.DataFrame(var_rows)

        # Source_Metadata Released_Variables coverage.
        released_var_rows = []
        required_sm_columns = {"Released_File", "Released_Variables"}
        if not sm.empty and required_sm_columns.issubset(sm.columns):
            for _, row in sm.iterrows():
                rel_file = normalise_path(row["Released_File"])
                rel_vars = normalise_var_list(row.get("Released_Variables", ""))
                matched_actuals = [
                    f for f in data_files if source_file_matches(f, rel_file)
                ]
                if not matched_actuals:
                    released_var_rows.append(
                        {
                            "Source_Metadata_Record": rel_file,
                            "Matched_Actual_Files": 0,
                            "Released_Variable": "",
                            "Present_In_All_Matched_Files": False,
                            "Status": "Fail",
                        }
                    )
                    continue

                for variable in rel_vars:
                    present_all = all(
                        variable in set(file_columns[f]) for f in matched_actuals
                    )
                    released_var_rows.append(
                        {
                            "Source_Metadata_Record": rel_file,
                            "Matched_Actual_Files": len(matched_actuals),
                            "Released_Variable": variable,
                            "Present_In_All_Matched_Files": present_all,
                            "Status": "Pass" if present_all else "Fail",
                        }
                    )
        released_var_coverage = pd.DataFrame(released_var_rows)

        status_counts: dict = {}
        if not vr.empty and "Status" in vr.columns:
            status_counts = vr["Status"].value_counts(dropna=False).to_dict()

        def add_check(
            check_id: str,
            category: str,
            item: str,
            observed: str,
            status: str,
            notes: str = "",
        ) -> None:
            rows.append(
                {
                    "Check_ID": check_id,
                    "Category": category,
                    "Validation_Item": item,
                    "Observed_Result": observed,
                    "Status": status,
                    "Notes": notes,
                }
            )

        add_check(
            "META_4_5_001",
            "Documentation",
            "Required documentation files present",
            f"{sum(r['Present'] for r in file_rows)} of "
            f"{len(file_rows)} expected files present",
            "Pass" if all(r["Present"] for r in file_rows) else "Warning",
        )
        add_check(
            "META_4_5_002",
            "Source metadata",
            "Actual data files documented in Source_Metadata.csv",
            f"{int(source_coverage['Documented'].sum())} of "
            f"{len(source_coverage)} data files documented",
            "Pass" if not source_coverage.empty and source_coverage["Documented"].all() else "Fail",
        )
        add_check(
            "META_4_5_003",
            "Variable dictionary",
            "Actual file columns documented in Variable_Dictionary.csv",
            f"{int(var_coverage['Documented'].sum())} of "
            f"{len(var_coverage)} file-column pairs documented",
            "Pass" if not var_coverage.empty and var_coverage["Documented"].all() else "Fail",
        )
        if not released_var_coverage.empty:
            add_check(
                "META_4_5_004",
                "Source metadata",
                "Released_Variables listed in Source_Metadata.csv exist in matched data files",
                f"{int(released_var_coverage['Present_In_All_Matched_Files'].sum())} "
                f"of {len(released_var_coverage)} released-variable entries present",
                "Pass"
                if released_var_coverage["Present_In_All_Matched_Files"].all()
                else "Fail",
                "Generic descriptions such as 'Sido-level ... variables' are not "
                "treated as literal column names; list the actual released columns "
                "when exact variable-level validation is intended.",
            )
        add_check(
            "META_4_5_005",
            "Region mapping",
            "Region_Mapping.csv contains documented harmonization cases",
            f"{len(rm)} mapping rows" if not rm.empty else "Region_Mapping.csv not found",
            "Pass" if not rm.empty else "Fail",
        )
        add_check(
            "META_4_5_006",
            "Validation report",
            "Validation_Report.csv status summary",
            "; ".join(f"{k}: {v}" for k, v in status_counts.items())
            if status_counts
            else "Validation_Report.csv not found or has no Status column",
            "Pass" if status_counts and set(status_counts) == {"Pass"} else "Warning",
        )
        add_check(
            "META_4_5_007",
            "Package cleanliness",
            "No .DS_Store files in final package",
            f"{len(ds_store_files)} .DS_Store file(s) detected",
            "Pass" if not ds_store_files else "Warning",
            "; ".join(ds_store_files[:5]),
        )
        add_check(
            "META_4_5_008",
            "Package naming",
            "Transaction files use final KRAFT naming convention",
            "KRAFT transaction naming detected"
            if kraft_tx_naming
            else (
                "K_APT transaction naming detected"
                if kapt_tx_naming
                else "Other transaction naming detected"
            ),
            "Pass" if kraft_tx_naming else "Warning",
            "" if kraft_tx_naming else (
                "Rename K_APT_Transactions_YYYY.csv to KRAFT_Transactions_YYYY.csv "
                "for the final release."
            ),
        )
        add_check(
            "META_4_5_009",
            "Package structure",
            "Code directory status",
            "Code/ directory exists" if code_dir_exists else "No Code/ directory detected",
            "Warning" if code_dir_exists else "Pass",
            "Validation code may be released separately through Git. An empty "
            "Code/ directory should not remain in the data package.",
        )

        report = pd.DataFrame(rows)

        report.to_csv(OUTPUT_REPORT, index=False, encoding="utf-8-sig")
        pd.DataFrame(file_rows).to_csv(
            OUTPUT_FILE_COVERAGE, index=False, encoding="utf-8-sig"
        )
        var_coverage.to_csv(
            OUTPUT_VARIABLE_COVERAGE, index=False, encoding="utf-8-sig"
        )
        source_coverage.to_csv(
            OUTPUT_SOURCE_COVERAGE, index=False, encoding="utf-8-sig"
        )
        released_var_coverage.to_csv(
            OUTPUT_RELEASED_VARIABLE_COVERAGE,
            index=False,
            encoding="utf-8-sig",
        )

        doc_present_count = int(sum(r["Present"] for r in file_rows))
        expected_doc_count = len(file_rows)
        data_doc_count = int(source_coverage["Documented"].sum())
        data_file_count = len(source_coverage)
        var_doc_count = int(var_coverage["Documented"].sum())
        var_pair_count = len(var_coverage)
        released_var_count = (
            int(released_var_coverage["Present_In_All_Matched_Files"].sum())
            if not released_var_coverage.empty
            else 0
        )
        released_var_total = len(released_var_coverage)
        validation_pass_count = int(status_counts.get("Pass", 0))
        validation_total_count = int(sum(status_counts.values())) if status_counts else 0

        section_text = f"""### 4.5. Metadata consistency and validation outputs

Metadata consistency checks were performed to verify that the released data files were accompanied by sufficient documentation for transparent reuse. The checks focused on documentation-file availability, source-level metadata coverage, variable-level metadata coverage, administrative-region mapping documentation, and validation-output consistency.

The documentation files were checked to confirm that the dataset package included the expected reuse materials, including `README.md`, `LICENSE`, `CITATION.cff`, `Variable_Dictionary.csv`, `Source_Metadata.csv`, `Region_Mapping.csv`, `Validation_Report.csv`, and `Preprocessing_Summary.md`. In the inspected package, {doc_present_count} of {expected_doc_count} expected documentation files were present. The final public release should include all expected documentation files so that users can identify the dataset structure, licensing conditions, citation information, variable definitions, source information, preprocessing decisions, administrative harmonization rules, and validation results.

Source-level consistency was assessed by comparing the released data files with `Source_Metadata.csv`. A total of {data_doc_count} of {data_file_count} released data files were documented in the source metadata file. The transaction records were documented using an annual-file template, while the auxiliary indicators were documented at the component-file level. The source metadata file records the source institution, source dataset or statistical series, collection period, temporal and spatial resolution, released variables, preprocessing summary, and license or attribution notes for each data component.

Variable-level consistency was assessed by comparing the columns in the released data files with `Variable_Dictionary.csv`. A total of {var_doc_count} of {var_pair_count} file-column pairs were documented in the variable dictionary. The variable dictionary provides variable names, descriptions, units, data types, temporal resolution, spatial resolution, source information, and original variable names where applicable. In addition, {released_var_count} of {released_var_total} released-variable entries listed in `Source_Metadata.csv` were confirmed to exist in the matched data files.

Administrative-region documentation was checked using `Region_Mapping.csv`. This file contained {len(rm)} documented harmonization rows covering administrative-region standardization cases and join-related decisions. These records support interpretation of historical or source-specific region labels and help users reproduce joins between transaction records and auxiliary indicators.

Finally, the validation outputs were reviewed for consistency. `Validation_Report.csv` contained {validation_total_count} validation checks, of which {validation_pass_count} were marked as passing in the inspected package. The generated validation scripts and derived validation outputs provide additional reproducibility for the descriptive, distributional, regional coverage, and metadata consistency checks reported in Sections 4.2–4.5. Together, these metadata and validation outputs support the transparency, traceability, and reuse of KRAFT.
"""
        OUTPUT_SECTION_MD.write_text(section_text, encoding="utf-8")

        return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="KRAFT metadata consistency validation."
    )
    parser.add_argument(
        "--input",
        default="KRAFT_v1.0.zip",
        help="Path to KRAFT ZIP package or extracted directory.",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs",
        help="Directory for validation outputs.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    SOURCE_PACKAGE = Path(args.input)
    OUTPUT_REPORT = output_dir / "KRAFT_Metadata_Consistency_Report.csv"
    OUTPUT_FILE_COVERAGE = output_dir / "KRAFT_Metadata_File_Coverage.csv"
    OUTPUT_VARIABLE_COVERAGE = (
        output_dir / "KRAFT_Variable_Dictionary_Coverage.csv"
    )
    OUTPUT_SOURCE_COVERAGE = output_dir / "KRAFT_Source_Metadata_Coverage.csv"
    OUTPUT_RELEASED_VARIABLE_COVERAGE = (
        output_dir / "KRAFT_Source_Metadata_Released_Variables_Coverage.csv"
    )
    OUTPUT_SECTION_MD = (
        output_dir
        / "KRAFT_Section_4_5_Metadata_consistency_and_validation_outputs.md"
    )
    print(run_validation().to_string(index=False))
