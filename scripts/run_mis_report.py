from __future__ import annotations

from reports.management_summary import (
    build_management_summary,
)
from reports.mis_report import (
    build_mis_report_pack,
    export_mis_report_pack,
)
from reports.mis_validation import (
    validate_mis_report_pack,
)


def separator() -> None:
    print("=" * 112)


def small_separator() -> None:
    print("-" * 112)


def main() -> None:
    separator()

    print(
        "HOSPITAL 360 — "
        "PHASE 7.2 MIS & MANAGEMENT REPORTING"
    )

    separator()

    print()
    print(
        "Building MIS reporting pack..."
    )

    report_pack = (
        build_mis_report_pack()
    )

    print(
        "Validating MIS reporting pack..."
    )

    validate_mis_report_pack(
        report_pack
    )

    management_summary = (
        build_management_summary(
            executive_scorecard=
                report_pack.outputs[
                    "executive_scorecard"
                ],
            executive_commentary=
                report_pack.outputs[
                    "executive_commentary"
                ],
            management_exceptions=
                report_pack.outputs[
                    "management_exceptions"
                ],
        )
    )

    report_pack.outputs[
        "management_summary"
    ] = management_summary

    export_directory = (
        export_mis_report_pack(
            report_pack
        )
    )

    print()
    print("MIS OUTPUTS")
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
    ) in report_pack.outputs.items():
        print(
            f"{name:<48}"
            f"{len(dataframe):>14,}"
            f"{len(dataframe.columns):>14,}"
        )

    print()
    print("EXECUTIVE SCORECARD")
    small_separator()

    scorecard = (
        report_pack.outputs[
            "executive_scorecard"
        ]
    )

    print(
        scorecard.to_string(
            index=False
        )
    )

    print()
    print("EXECUTIVE COMMENTARY")
    small_separator()

    commentary = (
        report_pack.outputs[
            "executive_commentary"
        ]
    )

    print(
        commentary.to_string(
            index=False
        )
    )

    print()
    print("MANAGEMENT EXCEPTIONS")
    small_separator()

    exceptions = (
        report_pack.outputs[
            "management_exceptions"
        ]
    )

    if exceptions.empty:
        print(
            "No management review signals generated."
        )
    else:
        display_columns = [
            "domain",
            "entity_type",
            "entity_name",
            "metric",
            "metric_value",
            "benchmark_value",
            "variance",
        ]

        print(
            exceptions[
                display_columns
            ].to_string(
                index=False
            )
        )

    print()
    print("Report date:")
    print(
        report_pack.report_date.date()
    )

    print()
    print("Exports written to:")
    print(export_directory)

    print()
    separator()

    print(
        "PHASE 7.2 MIS REPORT "
        "GENERATION COMPLETED"
    )

    separator()


if __name__ == "__main__":
    main()