from __future__ import annotations

import numpy as np
import pandas as pd
from typing import cast


def safe_percentage(
    numerator,
    denominator,
):
    if denominator is None:
        return np.nan

    if pd.isna(denominator):
        return np.nan

    if denominator == 0:
        return np.nan

    return (
        100.0
        * numerator
        / denominator
    )


def coefficient_of_variation(
    series: pd.Series,
) -> float:
    """
    CV = standard deviation / mean * 100.

    Useful for comparing variability between metrics
    with different scales.
    """

    clean = pd.to_numeric(
        series,
        errors="coerce",
    ).dropna()

    if clean.empty:
        return np.nan

    mean_value = clean.mean()

    if mean_value == 0:
        return np.nan

    return round(
        float(
            100.0
            * clean.std(ddof=1)
            / mean_value
        ),
        2,
    )


def percentile_summary(
    series: pd.Series,
) -> dict[str, float]:
    clean = pd.to_numeric(
        series,
        errors="coerce",
    ).dropna()

    if clean.empty:
        return {
            "minimum": np.nan,
            "p10": np.nan,
            "p25": np.nan,
            "median": np.nan,
            "p75": np.nan,
            "p90": np.nan,
            "p95": np.nan,
            "p99": np.nan,
            "maximum": np.nan,
        }

    return {
        "minimum": float(clean.min()),
        "p10": float(clean.quantile(0.10)),
        "p25": float(clean.quantile(0.25)),
        "median": float(clean.quantile(0.50)),
        "p75": float(clean.quantile(0.75)),
        "p90": float(clean.quantile(0.90)),
        "p95": float(clean.quantile(0.95)),
        "p99": float(clean.quantile(0.99)),
        "maximum": float(clean.max()),
    }


def distribution_summary(
    dataframe: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:
    rows = []

    for column in columns:

        if column not in dataframe.columns:
            continue

        series = pd.to_numeric(
            dataframe[column],
            errors="coerce",
        )

        clean = series.dropna()

        if clean.empty:
            continue

        percentiles = percentile_summary(
            clean
        )

        rows.append(
            {
                "metric": column,
                "count": int(clean.count()),
                "mean": round(
                    float(clean.mean()),
                    2,
                ),
                "std_dev": round(
                    float(clean.std(ddof=1)),
                    2,
                ),
                "coefficient_of_variation_pct":
                    coefficient_of_variation(
                        clean
                    ),
                "minimum": round(
                    percentiles["minimum"],
                    2,
                ),
                "p10": round(
                    percentiles["p10"],
                    2,
                ),
                "p25": round(
                    percentiles["p25"],
                    2,
                ),
                "median": round(
                    percentiles["median"],
                    2,
                ),
                "p75": round(
                    percentiles["p75"],
                    2,
                ),
                "p90": round(
                    percentiles["p90"],
                    2,
                ),
                "p95": round(
                    percentiles["p95"],
                    2,
                ),
                "p99": round(
                    percentiles["p99"],
                    2,
                ),
                "maximum": round(
                    percentiles["maximum"],
                    2,
                ),
                "skewness": round(
                    float(cast(float, clean.skew())),
                    4,
                ),
            }
        )

    return pd.DataFrame(rows)


def percentile_segment(
    series: pd.Series,
    labels: tuple[str, str, str, str] = (
        "Low",
        "Moderate",
        "High",
        "Very High",
    ),
) -> pd.Series:
    """
    Segment values using quartile thresholds.

    This is descriptive segmentation only.
    """

    numeric = pd.to_numeric(
        series,
        errors="coerce",
    )

    valid = numeric.dropna()

    result = pd.Series(
        pd.NA,
        index=series.index,
        dtype="object",
    )

    if valid.empty:
        return result

    q25 = valid.quantile(0.25)
    q50 = valid.quantile(0.50)
    q75 = valid.quantile(0.75)

    result.loc[
        numeric <= q25
    ] = labels[0]

    result.loc[
        (numeric > q25)
        & (numeric <= q50)
    ] = labels[1]

    result.loc[
        (numeric > q50)
        & (numeric <= q75)
    ] = labels[2]

    result.loc[
        numeric > q75
    ] = labels[3]

    return result


def zscore_flags(
    series: pd.Series,
    threshold: float = 3.0,
) -> pd.DataFrame:
    numeric = pd.to_numeric(
        series,
        errors="coerce",
    )

    mean_value = numeric.mean()
    std_value = numeric.std(
        ddof=1
    )

    if (
        pd.isna(std_value)
        or std_value == 0
    ):
        z_scores = pd.Series(
            np.nan,
            index=series.index,
        )
    else:
        z_scores = (
            numeric
            - mean_value
        ) / std_value

    return pd.DataFrame(
        {
            "value": numeric,
            "z_score": z_scores.round(4),
            "is_zscore_outlier":
                z_scores.abs() > threshold,
        }
    )


def concentration_metrics(
    series: pd.Series,
) -> dict[str, float]:
    """
    Calculate descriptive concentration metrics.

    HHI is returned on the 0-10,000 scale.
    """

    clean = pd.to_numeric(
        series,
        errors="coerce",
    ).fillna(0)

    total = clean.sum()

    if total <= 0:
        return {
            "top_1_share_pct": np.nan,
            "top_3_share_pct": np.nan,
            "top_5_share_pct": np.nan,
            "hhi": np.nan,
        }

    shares = (
        clean
        .sort_values(
            ascending=False
        )
        / total
    )

    return {
        "top_1_share_pct": round(
            float(
                shares.head(1).sum()
                * 100
            ),
            2,
        ),
        "top_3_share_pct": round(
            float(
                shares.head(3).sum()
                * 100
            ),
            2,
        ),
        "top_5_share_pct": round(
            float(
                shares.head(5).sum()
                * 100
            ),
            2,
        ),
        "hhi": round(
            float(
                (
                    shares.pow(2).sum()
                    * 10000
                )
            ),
            2,
        ),
    }