from __future__ import annotations

from pathlib import Path

import pandas as pd

from analytics.business_analysis import (
    run_business_analysis,
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
    / "business_analysis"
)


def separator() -> None:
    print("=" * 110)


def small_separator() -> None:
    print("-" * 110)


def export_outputs(
    outputs: dict[str, pd.DataFrame],
) -> None:
    EXPORT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    for name, dataframe in (
        outputs.items()
    ):
        dataframe.to_csv(
            EXPORT_DIRECTORY
            / f"{name}.csv",
            index=False,
        )


def main() -> None:
    separator()

    print(
        "HOSPITAL 360 — "
        "PHASE 6.3 ADVANCED BUSINESS ANALYSIS"
    )

    separator()

    print()
    print(
        "Running management analytics..."
    )

    outputs = (
        run_business_analysis()
    )

    export_outputs(
        outputs
    )

    print()
    print("BUSINESS ANALYSIS OUTPUTS")
    small_separator()

    print(
        f"{'Output':<52}"
        f"{'Rows':>12}"
        f"{'Columns':>14}"
    )

    small_separator()

    for name, dataframe in (
        outputs.items()
    ):
        print(
            f"{name:<52}"
            f"{len(dataframe):>12,}"
            f"{len(dataframe.columns):>14,}"
        )

    print()
    print("DEPARTMENT BENCHMARK")
    small_separator()

    departments = outputs[
        "department_benchmark"
    ]

    department_columns = [
        "department_name",
        "admissions",
        "net_revenue",
        "admission_share_pct",
        "revenue_share_pct",
        "alos_vs_hospital",
        "readmission_rate_vs_hospital_pct_point",
        "revenue_per_admission",
    ]

    print(
        departments[
            [
                column
                for column
                in department_columns
                if column
                in departments.columns
            ]
        ]
        .to_string(
            index=False
        )
    )

    print()
    print("FINANCE DIAGNOSTICS")
    small_separator()

    finance = outputs[
        "finance_diagnostics"
    ]

    finance_columns = [
        "department_name",
        "net_revenue",
        "collected_amount",
        "outstanding_amount",
        "collection_efficiency_pct_python",
        "outstanding_rate_pct_python",
        "outstanding_share_pct",
        "outstanding_rank",
    ]

    print(
        finance[
            [
                column
                for column
                in finance_columns
                if column
                in finance.columns
            ]
        ]
        .to_string(
            index=False
        )
    )

    print()
    print("CLAIM DIAGNOSTICS")
    small_separator()

    claims = outputs[
        "claim_diagnostics"
    ]

    claim_columns = [
        "insurer_name",
        "total_claims",
        "claim_amount",
        "rejected_amount",
        "rejection_rate_pct_python",
        "rejected_amount_rate_pct",
        "rejected_amount_share_pct",
        "rejected_amount_rank",
    ]

    print(
        claims[
            [
                column
                for column
                in claim_columns
                if column
                in claims.columns
            ]
        ]
        .to_string(
            index=False
        )
    )

    print()
    print("MANAGEMENT INSIGHTS")
    small_separator()

    insights = outputs[
        "management_insights"
    ]

    if insights.empty:
        print(
            "No management observations generated."
        )
    else:
        print(
            insights[
                [
                    "domain",
                    "subject",
                    "comparison_unit",
                    "observation",
                ]
            ]
            .to_string(
                index=False
            )
        )

    print()
    print("Exports written to:")
    print(EXPORT_DIRECTORY)

    print()
    separator()

    print(
        "PHASE 6.3 ADVANCED BUSINESS "
        "ANALYSIS COMPLETED"
    )

    separator()


if __name__ == "__main__":
    main()