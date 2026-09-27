from __future__ import annotations

from pathlib import Path

import pandas as pd

from analytics.data_loader import (
    load_admission_analysis_dataset,
)
from analytics.finance import (
    run_finance_analysis,
)
from analytics.operations import (
    run_operations_analysis,
)
from analytics.patients import (
    run_patient_analysis,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

EXPORT_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "exports"
    / "statistics"
)


def separator() -> None:
    print("=" * 104)


def small_separator() -> None:
    print("-" * 104)


def export_outputs(
    outputs: dict[str, pd.DataFrame],
) -> None:

    EXPORT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    for name, dataframe in outputs.items():

        dataframe.to_csv(
            EXPORT_DIRECTORY
            / f"{name}.csv",
            index=False,
        )


def main() -> None:

    separator()

    print(
        "HOSPITAL 360 — "
        "PHASE 6.2 STATISTICAL BUSINESS ANALYTICS"
    )

    separator()

    print()
    print(
        "Loading admission-level analytical dataset..."
    )

    admissions = (
        load_admission_analysis_dataset()
    )

    print(
        f"Loaded admissions : {len(admissions):,}"
    )

    print()
    print(
        "Running finance statistics..."
    )

    finance_outputs = (
        run_finance_analysis(
            admissions
        )
    )

    print(
        "Running operations statistics..."
    )

    operations_outputs = (
        run_operations_analysis(
            admissions
        )
    )

    print(
        "Running patient statistics..."
    )

    patient_outputs = (
        run_patient_analysis(
            admissions
        )
    )

    outputs = {
        **finance_outputs,
        **operations_outputs,
        **patient_outputs,
    }

    export_outputs(
        outputs
    )

    print()
    print("STATISTICAL OUTPUTS")
    small_separator()

    print(
        f"{'Output':<52}"
        f"{'Rows':>12}"
        f"{'Columns':>12}"
    )

    small_separator()

    for name, dataframe in outputs.items():

        print(
            f"{name:<52}"
            f"{len(dataframe):>12,}"
            f"{len(dataframe.columns):>12,}"
        )

    print()
    print("FINANCE DISTRIBUTION")
    small_separator()

    finance_distribution = outputs[
        "finance_distribution"
    ]

    display_columns = [
        "metric",
        "mean",
        "median",
        "p90",
        "p95",
        "p99",
        "coefficient_of_variation_pct",
        "skewness",
    ]

    print(
        finance_distribution[
            display_columns
        ].to_string(
            index=False
        )
    )

    print()
    print("DEPARTMENT OPERATIONS")
    small_separator()

    department_operations = outputs[
        "department_operations_statistics"
    ]

    display_columns = [
        "department_name",
        "admissions",
        "average_length_of_stay",
        "emergency_rate_pct",
        "icu_rate_pct",
        "readmission_rate_pct",
        "workload_segment",
    ]

    print(
        department_operations[
            display_columns
        ].to_string(
            index=False
        )
    )

    print()
    print("REVENUE CONCENTRATION")
    small_separator()

    concentration = pd.concat(
        [
            outputs[
                "doctor_revenue_concentration"
            ],
            outputs[
                "department_revenue_concentration"
            ],
        ],
        ignore_index=True,
    )

    print(
        concentration.to_string(
            index=False
        )
    )

    print()
    print(
        "Exports written to:"
    )

    print(
        EXPORT_DIRECTORY
    )

    print()
    separator()

    print(
        "PHASE 6.2 STATISTICAL ANALYSIS COMPLETED"
    )

    separator()


if __name__ == "__main__":
    main()