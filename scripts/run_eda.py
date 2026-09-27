from __future__ import annotations

from analytics.eda import (
    DEFAULT_EXPORT_DIRECTORY,
    run_eda,
)


def separator() -> None:
    print("=" * 96)


def small_separator() -> None:
    print("-" * 96)


def main() -> None:

    separator()

    print(
        "HOSPITAL 360 — "
        "PHASE 6.1 PYTHON EDA"
    )

    separator()

    print()
    print(
        "Loading warehouse analytical dataset..."
    )

    outputs = run_eda()

    print()
    print("EDA OUTPUTS")
    small_separator()

    print(
        f"{'Output':<42}"
        f"{'Rows':>14}"
        f"{'Columns':>14}"
    )

    small_separator()

    for name, dataframe in outputs.items():

        print(
            f"{name:<42}"
            f"{len(dataframe):>14,}"
            f"{len(dataframe.columns):>14,}"
        )

    overview = outputs[
        "dataset_overview"
    ].iloc[0]

    print()
    print("DATASET OVERVIEW")
    small_separator()

    print(
        f"Rows                 : "
        f"{int(overview['row_count']):,}"
    )

    print(
        f"Columns              : "
        f"{int(overview['column_count']):,}"
    )

    print(
        f"Duplicate rows       : "
        f"{int(overview['duplicate_rows']):,}"
    )

    print(
        f"Missing values       : "
        f"{int(overview['total_missing_values']):,}"
    )

    print(
        f"Memory usage (MB)    : "
        f"{overview['memory_mb']}"
    )

    strong = outputs[
        "strongest_correlations"
    ]

    print()
    print("STRONGEST CORRELATIONS")
    small_separator()

    if strong.empty:

        print(
            "No correlations met the configured threshold."
        )

    else:

        print(
            strong.head(
                15
            ).to_string(
                index=False
            )
        )

    outliers = outputs[
        "outlier_profile"
    ]

    print()
    print("TOP IQR OUTLIER FLAGS")
    small_separator()

    if outliers.empty:

        print(
            "No numeric columns available "
            "for IQR profiling."
        )

    else:

        columns = [
            "column_name",
            "outlier_count",
            "outlier_pct",
        ]

        print(
            outliers[
                columns
            ].head(
                15
            ).to_string(
                index=False
            )
        )

    print()
    print(
        "Exports written to:"
    )

    print(
        DEFAULT_EXPORT_DIRECTORY
    )

    print()
    separator()

    print(
        "PHASE 6.1 EDA EXECUTION COMPLETED"
    )

    separator()


if __name__ == "__main__":
    main()