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
    / "risk_intelligence"
)


EXPECTED_FILES = [
    "enterprise_risk_kpis.csv",
    "risk_domain_summary.csv",
    "patient_priority_register.csv",
    "financial_priority_register.csv",
    "claim_priority_register.csv",
    "department_risk_matrix.csv",
    "insurer_risk_summary.csv",
    "aggregate_review_signals.csv",
    "risk_dashboard_feed.csv",
    "enterprise_risk_insights.csv",
]


def separator() -> None:
    print("=" * 108)


def small_separator() -> None:
    print("-" * 108)


def main() -> None:
    separator()

    print(
        "HOSPITAL 360 — "
        "PHASE 8.4 UNIFIED RISK EXPORT CHECK"
    )

    separator()

    if not EXPORT_DIRECTORY.exists():
        raise RuntimeError(
            "Unified risk export directory "
            "does not exist: "
            f"{EXPORT_DIRECTORY}"
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
            f"{filename:<54}"
            f"{len(dataframe):>14,}"
            f"{'PASS':>14}"
        )

    print()
    separator()

    print(
        "PHASE 8.4 UNIFIED RISK "
        "EXPORT VALIDATION PASSED"
    )

    separator()


if __name__ == "__main__":
    main()