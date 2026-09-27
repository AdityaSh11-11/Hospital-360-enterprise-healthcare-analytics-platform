from __future__ import annotations

import numpy as np
import pandas as pd


def absolute_variance(
    actual: pd.Series,
    comparison: pd.Series,
) -> pd.Series:
    return (
        actual
        - comparison
    )


def percentage_variance(
    actual: pd.Series,
    comparison: pd.Series,
) -> pd.Series:
    return (
        (
            actual
            - comparison
        )
        / comparison.replace(
            0,
            np.nan,
        )
        * 100.0
    )


def index_vs_average(
    series: pd.Series,
) -> pd.Series:
    average = series.mean()

    if (
        pd.isna(average)
        or average == 0
    ):
        return pd.Series(
            np.nan,
            index=series.index,
        )

    return (
        100.0
        * series
        / average
    )


def weighted_average(
    values: pd.Series,
    weights: pd.Series,
) -> float:
    valid = (
        values.notna()
        & weights.notna()
    )

    clean_values = values.loc[
        valid
    ].astype(float)

    clean_weights = weights.loc[
        valid
    ].astype(float)

    if clean_values.empty:
        return np.nan

    weight_total = (
        clean_weights.sum()
    )

    if weight_total == 0:
        return np.nan

    return float(
        np.average(
            clean_values,
            weights=clean_weights,
        )
    )


def rolling_average(
    series: pd.Series,
    window: int = 3,
) -> pd.Series:
    if window <= 0:
        raise ValueError(
            "window must be greater than zero."
        )

    return (
        series
        .rolling(
            window=window,
            min_periods=1,
        )
        .mean()
    )


def period_over_period_analysis(
    dataframe: pd.DataFrame,
    date_column: str,
    metrics: list[str],
) -> pd.DataFrame:
    """
    Generic period-over-period variance engine.
    """

    if date_column not in dataframe.columns:
        raise ValueError(
            f"Missing date column: {date_column}"
        )

    result = dataframe.copy()

    result[date_column] = pd.to_datetime(
        result[date_column],
        errors="coerce",
    )

    result = (
        result
        .sort_values(date_column)
        .reset_index(drop=True)
    )

    for metric in metrics:
        if metric not in result.columns:
            continue

        previous = (
            result[metric]
            .shift(1)
        )

        result[
            f"{metric}_previous_period"
        ] = previous

        result[
            f"{metric}_absolute_variance"
        ] = absolute_variance(
            result[metric],
            previous,
        )

        result[
            f"{metric}_variance_pct"
        ] = (
            percentage_variance(
                result[metric],
                previous,
            )
            .replace(
                [np.inf, -np.inf],
                np.nan,
            )
            .round(2)
        )

        result[
            f"{metric}_rolling_3_period_average"
        ] = (
            rolling_average(
                result[metric],
                window=3,
            )
            .round(2)
        )

    return result