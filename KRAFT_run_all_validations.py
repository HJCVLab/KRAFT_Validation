#!/usr/bin/env python3
"""Run all KRAFT technical-validation scripts sequentially."""

from pathlib import Path
import argparse
import subprocess
import sys

import pandas as pd


SCRIPTS = [
    "KRAFT_technical_validation_transaction_records.py",
    "KRAFT_technical_validation_auxiliary_indicators.py",
    "KRAFT_technical_validation_distributional_regional_coverage.py",
    "KRAFT_technical_validation_metadata_consistency.py",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run all KRAFT validation scripts.")
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

    source = Path(args.input).expanduser().resolve()
    if not source.exists():
        parser.error(f"Input package does not exist: {source}")

    script_dir = Path(__file__).resolve().parent
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    for script in SCRIPTS:
        script_path = script_dir / script
        if not script_path.exists():
            raise FileNotFoundError(f"Validation script not found: {script_path}")

        print(f"\n[RUN] {script}", flush=True)
        subprocess.check_call(
            [
                sys.executable,
                str(script_path),
                "--input",
                str(source),
                "--output-dir",
                str(output_dir),
            ],
            cwd=script_dir,
        )

    metadata_report = output_dir / "KRAFT_Metadata_Consistency_Report.csv"
    summary = ""
    if metadata_report.exists():
        report = pd.read_csv(metadata_report)
        counts = report["Status"].value_counts().to_dict() if "Status" in report else {}
        summary = "; ".join(f"{status}: {count}" for status, count in counts.items())

    print(
        f"\n[DONE] All KRAFT validation scripts executed. "
        f"Outputs saved to: {output_dir}",
        flush=True,
    )
    if summary:
        print(f"Metadata consistency status summary: {summary}", flush=True)


if __name__ == "__main__":
    main()
