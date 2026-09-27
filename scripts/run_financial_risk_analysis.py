from __future__ import annotations

from pathlib import Path

from analytics.financial_risk import (
    run_financial_risk_analysis,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

EXPORT_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "exports"
    / "financial_risk"
)


def separator() -> None:
    print("=" * 112)


def small_separator() -> None:
    print("-" * 112)


def main() -> None:
    separator()

    print(
        "HOSPITAL 360 — "
        "PHASE 8.2 FINANCIAL & CLAIMS RISK ANALYSIS"
    )

    separator()

    outputs = (
        run_financial_risk_analysis()
    )

    EXPORT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    print()
    print("FINANCIAL RISK OUTPUTS")
    small_separator()

    print(
        f"{'Dataset':<48}"
        f"{'Rows':>14}"
        f"{'Columns':>14}"
    )

    small_separator()

    for (
        name,
        dataframe,
    ) in outputs.items():

        dataframe.to_csv(
            EXPORT_DIRECTORY
            / f"{name}.csv",
            index=False,
        )

        print(
            f"{name:<48}"
            f"{len(dataframe):>14,}"
            f"{len(dataframe.columns):>14,}"
        )

    print()
    print("FINANCIAL RISK KPI TABLE")
    small_separator()

    print(
        outputs[
            "financial_risk_kpis"
        ].to_string(
            index=False
        )
    )

    print()
    print("FINANCIAL RISK BAND SUMMARY")
    small_separator()

    print(
        outputs[
            "financial_risk_band_summary"
        ].to_string(
            index=False
        )
    )

    print()
    print("INSURER CLAIM RISK")
    small_separator()

    insurer_columns = [
        "insurer_name",
        "total_claims",
        "claim_amount",
        "rejected_amount",
        "high_risk_claims",
        "average_claim_risk_score",
        "claim_rejection_rate_pct",
        "rejected_value_rate_pct",
        "high_risk_claim_rate_pct",
    ]

    print(
        outputs[
            "insurer_claim_risk"
        ][
            insurer_columns
        ].to_string(
            index=False
        )
    )

    print()
    print("FINANCIAL RISK FACTORS")
    small_separator()

    print(
        outputs[
            "financial_risk_factor_prevalence"
        ].to_string(
            index=False
        )
    )

    print()
    print("MANAGEMENT INSIGHTS")
    small_separator()

    print(
        outputs[
            "financial_risk_insights"
        ].to_string(
            index=False
        )
    )

    print()
    print(
        "Exports written to:"
    )

    print(EXPORT_DIRECTORY)

    print()
    separator()

    print(
        "PHASE 8.2 FINANCIAL & CLAIMS "
        "RISK ANALYSIS COMPLETED"
    )

    separator()


if __name__ == "__main__":
    main()