# KRAFT Code Execution Guide

## 1. Directory layout used in this release

```text
workspace/
├── KRAFT/                      # code repository
└── Dataset/
    └── KRAFT_v1.0/             # extracted dataset release
        ├── Data/
        ├── README.md
        ├── Source_Metadata.csv
        └── ...
```

Run all commands from the `KRAFT/` code-repository directory.

## 2. Environment setup

Python 3.10 or later is recommended.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

When PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### Linux or macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Run the complete validation workflow

### Windows PowerShell

```powershell
python KRAFT_run_all_validations.py `
  --input "..\Dataset\KRAFT_v1.0" `
  --output-dir "validation_outputs"
```

### Linux or macOS

```bash
python KRAFT_run_all_validations.py \
  --input ../Dataset/KRAFT_v1.0 \
  --output-dir validation_outputs
```

The dataset remains unchanged. Results are written to `validation_outputs/`.

## 4. Successful-run indicators

```text
[DONE] All KRAFT validation scripts executed.
Metadata consistency status summary: Pass: 9
```

The main package checks should report:

```text
Total transaction rows: 5,320,379
Actual data files documented: 25 of 25
File-column pairs documented: 224 of 224
Released-variable entries present: 152 of 152
Region mapping rows: 7
Validation_Report.csv status summary: Pass: 19
```

`Pass: 9` is the number of checks executed by the metadata-consistency script. `Pass: 19` is the number of checks recorded in the released dataset's `Validation_Report.csv`.

## 5. Generated outputs

The complete validation command generates 19 files in `validation_outputs/`:

```text
KRAFT_Table4_Transaction_Descriptive_Statistics.csv
KRAFT_Table5_Auxiliary_Descriptive_Statistics.csv
KRAFT_Auxiliary_Descriptive_Statistics_Full.csv
KRAFT_Annual_Transaction_Counts.csv
KRAFT_Sido_Transaction_Counts.csv
KRAFT_Sido_Month_Coverage.csv
KRAFT_Price_per_sqm_Distribution_Summary.csv
KRAFT_Figure2_Annual_Transaction_Counts.png
KRAFT_Figure3_Sido_Transaction_Counts.png
KRAFT_Figure4_Log_Price_per_sqm_Distribution.png
KRAFT_Metadata_Consistency_Report.csv
KRAFT_Metadata_File_Coverage.csv
KRAFT_Variable_Dictionary_Coverage.csv
KRAFT_Source_Metadata_Coverage.csv
KRAFT_Source_Metadata_Released_Variables_Coverage.csv
KRAFT_Section_4_2_Descriptive_validation_transaction_records.md
KRAFT_Section_4_3_Descriptive_validation_auxiliary_indicators.md
KRAFT_Section_4_4_Distributional_and_regional_coverage_checks.md
KRAFT_Section_4_5_Metadata_consistency_and_validation_outputs.md
```

## 6. Run individual validation scripts

```bash
python KRAFT_technical_validation_transaction_records.py --input ../Dataset/KRAFT_v1.0 --output-dir validation_outputs
python KRAFT_technical_validation_auxiliary_indicators.py --input ../Dataset/KRAFT_v1.0 --output-dir validation_outputs
python KRAFT_technical_validation_distributional_regional_coverage.py --input ../Dataset/KRAFT_v1.0 --output-dir validation_outputs
python KRAFT_technical_validation_metadata_consistency.py --input ../Dataset/KRAFT_v1.0 --output-dir validation_outputs
```

## 7. Monthly education join example

```bash
python KRAFT_example_education_join.py \
  --input ../Dataset/KRAFT_v1.0 \
  --year 2024 \
  --sample-output examples/KRAFT_Education_Join_Sample_2024.csv
```

The original `Sigungu` is retained and a separate `Education_Join_Sigungu` column is created.

## 8. Annual private-education join example

```bash
python KRAFT_example_private_education_join.py \
  --input ../Dataset/KRAFT_v1.0 \
  --year 2024 \
  --sample-output examples/KRAFT_Private_Education_Join_Sample_2024.csv
```

This example extracts calendar year from `YearMonth` and joins annual observations by year, `Sido`, and normalized parent-city `Sigungu`.

## 9. Git inclusion

The released validation outputs should remain in the repository because the manuscript states that generated statistics, figures, and count tables are provided with the validation code. The supplied `.gitignore` explicitly allows `validation_outputs/` and `examples/` to be tracked.
