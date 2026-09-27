from __future__ import annotations

from pathlib import Path

from analytics.risk import run_risk_analysis


PROJECT_ROOT = Path(__file__).resolve().parents[1]

EXPORT_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "exports"
    / "risk"
)


def separator() -> None:
    print("=" * 112)


def small_separator() -> None:
    print("-" * 112)


def main() -> None:
    separator()

    print(
        "HOSPITAL 360 — "
        "PHASE 8.1 PATIENT RISK ANALYSIS"
    )

    separator()

    outputs = run_risk_analysis()

    EXPORT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    print()
    print("RISK ANALYTICS OUTPUTS")
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
    print("RISK KPI TABLE")
    small_separator()

    print(
        outputs[
            "risk_kpis"
        ].to_string(
            index=False
        )
    )

    print()
    print("RISK BAND SUMMARY")
    small_separator()

    print(
        outputs[
            "risk_band_summary"
        ].to_string(
            index=False
        )
    )

    print()
    print("RISK FACTOR PREVALENCE")
    small_separator()

    print(
        outputs[
            "risk_factor_prevalence"
        ].to_string(
            index=False
        )
    )

    print()
    print("TOP DEPARTMENT RISK")
    small_separator()

    department = (
        outputs[
            "department_risk"
        ]
        .head(10)
    )

    display_columns = [
        "department_name",
        "admissions",
        "average_risk_score",
        "high_risk_admissions",
        "high_risk_admission_rate_pct",
        "readmission_rate_pct",
        "emergency_rate_pct",
        "icu_rate_pct",
    ]

    print(
        department[
            display_columns
        ].to_string(
            index=False
        )
    )

    print()
    print("MANAGEMENT INSIGHTS")
    small_separator()

    print(
        outputs[
            "risk_management_insights"
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
        "PHASE 8.1 PATIENT RISK "
        "ANALYSIS COMPLETED"
    )

    separator()


if __name__ == "__main__":
    main()