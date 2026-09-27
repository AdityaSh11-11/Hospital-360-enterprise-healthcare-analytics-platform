from __future__ import annotations

from pathlib import Path

from analytics.risk_intelligence import (
    run_unified_risk_intelligence,
)


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


def separator() -> None:
    print("=" * 116)


def small_separator() -> None:
    print("-" * 116)


def main() -> None:
    separator()

    print(
        "HOSPITAL 360 — "
        "PHASE 8.4 UNIFIED RISK INTELLIGENCE"
    )

    separator()

    outputs = (
        run_unified_risk_intelligence()
    )

    EXPORT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    print()
    print("UNIFIED RISK OUTPUTS")
    small_separator()

    print(
        f"{'Dataset':<50}"
        f"{'Rows':>14}"
        f"{'Columns':>14}"
    )

    small_separator()

    for name, dataframe in outputs.items():
        dataframe.to_csv(
            EXPORT_DIRECTORY
            / f"{name}.csv",
            index=False,
        )

        print(
            f"{name:<50}"
            f"{len(dataframe):>14,}"
            f"{len(dataframe.columns):>14,}"
        )

    print()
    print("ENTERPRISE RISK KPIs")
    small_separator()

    print(
        outputs[
            "enterprise_risk_kpis"
        ].to_string(
            index=False
        )
    )

    print()
    print("RISK DOMAIN SUMMARY")
    small_separator()

    print(
        outputs[
            "risk_domain_summary"
        ].to_string(
            index=False
        )
    )

    print()
    print("DEPARTMENT RISK MATRIX")
    small_separator()

    department = outputs[
        "department_risk_matrix"
    ]

    preferred_columns = [
        "department_name",
        "admissions",
        "average_risk_score",
        "high_risk_admission_rate_pct",
        "net_revenue",
        "outstanding_amount",
        "average_financial_risk_score",
        "high_risk_bill_rate_pct",
    ]

    available_columns = [
        column
        for column in preferred_columns
        if column in department.columns
    ]

    print(
        department[
            available_columns
        ].to_string(
            index=False
        )
    )

    print()
    print("ENTERPRISE RISK INSIGHTS")
    small_separator()

    print(
        outputs[
            "enterprise_risk_insights"
        ].to_string(
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
        "PHASE 8.4 UNIFIED RISK "
        "INTELLIGENCE COMPLETED"
    )

    separator()


if __name__ == "__main__":
    main()