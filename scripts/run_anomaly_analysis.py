from __future__ import annotations

from pathlib import Path

from analytics.anomalies import (
    run_anomaly_analysis,
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
    / "anomalies"
)


def separator() -> None:
    print("=" * 112)


def small_separator() -> None:
    print("-" * 112)


def main() -> None:
    separator()

    print(
        "HOSPITAL 360 — "
        "PHASE 8.3 STATISTICAL ANOMALY DETECTION"
    )

    separator()

    outputs = (
        run_anomaly_analysis()
    )

    EXPORT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    print()
    print("ANOMALY ANALYTICS OUTPUTS")
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
    print("ANOMALY SUMMARY")
    small_separator()

    summary = outputs[
        "anomaly_summary"
    ]

    if summary.empty:
        print(
            "No statistical anomalies "
            "identified."
        )
    else:
        print(
            summary.to_string(
                index=False
            )
        )

    print()
    print("TOP AGGREGATE ANOMALIES")
    small_separator()

    aggregate = outputs[
        "aggregate_anomalies"
    ]

    if aggregate.empty:
        print(
            "No aggregate anomalies "
            "identified."
        )

    else:
        columns = [
            "anomaly_domain",
            "entity_id",
            "metric",
            "observed_value",
            "median_value",
            "robust_z_score",
            "direction",
        ]

        print(
            aggregate[
                columns
            ]
            .head(20)
            .to_string(
                index=False
            )
        )

    print()
    print("ANOMALY MANAGEMENT INSIGHTS")
    small_separator()

    insights = outputs[
        "anomaly_management_insights"
    ]

    if insights.empty:
        print(
            "No management insights "
            "generated."
        )
    else:
        print(
            insights.to_string(
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
        "PHASE 8.3 STATISTICAL "
        "ANOMALY ANALYSIS COMPLETED"
    )

    separator()


if __name__ == "__main__":
    main()