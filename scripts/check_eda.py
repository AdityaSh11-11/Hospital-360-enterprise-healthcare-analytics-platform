from __future__ import annotations

from pathlib import Path

import pandas as pd

from analytics.data_loader import (
    load_admission_analysis_dataset,
    read_sql,
)
from analytics.eda import (
    DEFAULT_EXPORT_DIRECTORY,
)


EXPECTED_EXPORTS = [
    "dataset_overview.csv",
    "column_profile.csv",
    "numeric_profile.csv",
    "categorical_profile.csv",
    "outlier_profile.csv",
    "correlation_matrix.csv",
    "strongest_correlations.csv",
    "department_analysis.csv",
    "monthly_analysis.csv",
    "admission_type_analysis.csv",
    "room_type_analysis.csv",
    "outcome_analysis.csv",
    "diagnosis_analysis.csv",
    "chronic_condition_analysis.csv",
    "sql_department_reference.csv",
    "sql_doctor_reference.csv",
    "sql_monthly_reference.csv",
]


def separator() -> None:
    print("=" * 100)


def small_separator() -> None:
    print("-" * 100)


def check_exports(
    directory: Path,
) -> None:

    print()
    print("EDA EXPORT FILES")
    small_separator()

    failed = []

    for filename in EXPECTED_EXPORTS:

        path = (
            directory
            / filename
        )

        if not path.exists():

            print(
                f"{filename:<52}"
                f"{'MISSING':>16}"
            )

            failed.append(
                filename
            )

            continue

        dataframe = pd.read_csv(
            path
        )

        print(
            f"{filename:<52}"
            f"{len(dataframe):>12,}"
            f" rows   PASS"
        )

    if failed:

        raise RuntimeError(
            "Missing EDA exports: "
            + ", ".join(failed)
        )


def reconcile_admission_dataset() -> None:

    dataframe = (
        load_admission_analysis_dataset()
    )

    source = read_sql(
        """
        SELECT
            COUNT(*) AS admissions,

            COUNT(
                DISTINCT patient_key
            ) AS patients,

            ROUND(
                SUM(length_of_stay)::numeric,
                2
            ) AS inpatient_days

        FROM warehouse.fact_admission
        """
    ).iloc[0]

    print()
    print("ADMISSION DATASET RECONCILIATION")
    small_separator()

    source_admissions = int(
        source["admissions"]
    )

    python_admissions = len(
        dataframe
    )

    source_patients = int(
        source["patients"]
    )

    python_patients = int(
        dataframe[
            "patient_key"
        ].nunique()
    )

    source_days = float(
        source["inpatient_days"]
    )

    python_days = float(
        dataframe[
            "length_of_stay"
        ].sum()
    )

    print(
        f"{'Metric':<36}"
        f"{'Warehouse':>22}"
        f"{'Python':>22}"
    )

    small_separator()

    print(
        f"{'Admissions':<36}"
        f"{source_admissions:>22,}"
        f"{python_admissions:>22,}"
    )

    print(
        f"{'Distinct patients':<36}"
        f"{source_patients:>22,}"
        f"{python_patients:>22,}"
    )

    print(
        f"{'Inpatient days':<36}"
        f"{source_days:>22,.0f}"
        f"{python_days:>22,.0f}"
    )

    if (
        source_admissions
        != python_admissions
    ):
        raise RuntimeError(
            "Admission row reconciliation failed."
        )

    if (
        source_patients
        != python_patients
    ):
        raise RuntimeError(
            "Patient reconciliation failed."
        )

    if (
        source_days
        != python_days
    ):
        raise RuntimeError(
            "Inpatient-day reconciliation failed."
        )

    if dataframe[
        "admission_id"
    ].duplicated().any():

        raise RuntimeError(
            "Admission-level EDA dataset contains "
            "duplicate admission_id values."
        )

    print()
    print(
        "[PASS] Admission-level grain reconciled."
    )


def reconcile_department_export() -> None:

    export_path = (
        DEFAULT_EXPORT_DIRECTORY
        / "department_analysis.csv"
    )

    dataframe = pd.read_csv(
        export_path
    )

    total_admissions = int(
        dataframe[
            "admissions"
        ].sum()
    )

    source = read_sql(
        """
        SELECT
            COUNT(*) AS admissions

        FROM warehouse.fact_admission
        """
    ).iloc[0]

    source_admissions = int(
        source["admissions"]
    )

    print()
    print("DEPARTMENT EDA RECONCILIATION")
    small_separator()

    print(
        f"{'Warehouse admissions':<40}"
        f"{source_admissions:>20,}"
    )

    print(
        f"{'EDA department admissions':<40}"
        f"{total_admissions:>20,}"
    )

    if (
        source_admissions
        != total_admissions
    ):
        raise RuntimeError(
            "Department EDA reconciliation failed."
        )

    print()
    print(
        "[PASS] Department EDA reconciled."
    )


def check_overview() -> None:

    path = (
        DEFAULT_EXPORT_DIRECTORY
        / "dataset_overview.csv"
    )

    overview = pd.read_csv(
        path
    ).iloc[0]

    print()
    print("EDA PROFILE SUMMARY")
    small_separator()

    print(
        f"Rows              : "
        f"{int(overview['row_count']):,}"
    )

    print(
        f"Columns           : "
        f"{int(overview['column_count']):,}"
    )

    print(
        f"Duplicate rows    : "
        f"{int(overview['duplicate_rows']):,}"
    )

    print(
        f"Missing values    : "
        f"{int(overview['total_missing_values']):,}"
    )

    print(
        f"Memory MB         : "
        f"{overview['memory_mb']}"
    )

    if int(
        overview[
            "duplicate_rows"
        ]
    ) != 0:

        raise RuntimeError(
            "EDA dataset contains duplicate rows."
        )


def main() -> None:

    separator()

    print(
        "HOSPITAL 360 — "
        "PHASE 6.1 EDA VALIDATION"
    )

    separator()

    if not DEFAULT_EXPORT_DIRECTORY.exists():

        raise RuntimeError(
            "EDA export directory does not exist. "
            "Run scripts.run_eda first."
        )

    check_exports(
        DEFAULT_EXPORT_DIRECTORY
    )

    reconcile_admission_dataset()

    reconcile_department_export()

    check_overview()

    print()
    separator()

    print(
        "PHASE 6.1 PYTHON EDA "
        "VALIDATION PASSED"
    )

    separator()


if __name__ == "__main__":
    main()