from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

EXPORT_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "exports"
    / "anomalies"
)


EXPECTED_FILES = [
    "monthly_hospital_anomalies.csv",
    "monthly_operations_anomalies.csv",
    "monthly_claim_anomalies.csv",
    "department_anomalies.csv",
    "aggregate_anomalies.csv",
    "bill_value_anomalies.csv",
    "los_anomalies.csv",
    "anomaly_summary.csv",
    "anomaly_management_insights.csv",
]


def separator() -> None:
    print("=" * 104)


def small_separator() -> None:
    print("-" * 104)


def main() -> None:
    separator()

    print(
        "HOSPITAL 360 — "
        "PHASE 8.3 ANOMALY EXPORT CHECK"
    )

    separator()

    if not EXPORT_DIRECTORY.exists():
        raise RuntimeError(
            "Anomaly export directory "
            f"does not exist: {EXPORT_DIRECTORY}"
        )

    print()
    print("EXPORT FILES")
    small_separator()

    for filename in EXPECTED_FILES:
        path = (
            EXPORT_DIRECTORY
            / filename
        )

        if not path.exists():
            raise RuntimeError(
                f"Missing export: {filename}"
            )

        dataframe = pd.read_csv(
            path
        )

        print(
            f"{filename:<52}"
            f"{len(dataframe):>14,}"
            f"{'PASS':>14}"
        )

    print()
    separator()

    print(
        "PHASE 8.3 ANOMALY "
        "EXPORT VALIDATION PASSED"
    )

    separator()


if __name__ == "__main__":
    main()