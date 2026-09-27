from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import numpy as np
import pandas as pd


@dataclass
class DatasetProfile:
    dataset_name: str
    row_count: int
    column_count: int
    duplicate_rows: int
    total_missing_values: int
    memory_mb: float


def dataset_overview(
    dataframe: pd.DataFrame,
    dataset_name: str,
) -> DatasetProfile:

    memory_bytes = dataframe.memory_usage(
        deep=True
    ).sum()

    return DatasetProfile(
        dataset_name=dataset_name,
        row_count=len(dataframe),
        column_count=len(dataframe.columns),
        duplicate_rows=int(
            dataframe.duplicated().sum()
        ),
        total_missing_values=int(
            dataframe.isna().sum().sum()
        ),
        memory_mb=round(
            memory_bytes / 1024 / 1024,
            2,
        ),
    )


def column_profile(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:

    rows = []

    total_rows = len(dataframe)

    for column in dataframe.columns:

        series = dataframe[column]

        missing_count = int(
            series.isna().sum()
        )

        non_null_count = int(
            series.notna().sum()
        )

        unique_count = int(
            series.nunique(
                dropna=True
            )
        )

        if total_rows:
            missing_pct = round(
                100.0
                * missing_count
                / total_rows,
                2,
            )
        else:
            missing_pct = 0.0

        rows.append(
            {
                "column_name": column,
                "data_type": str(
                    series.dtype
                ),
                "non_null_count": non_null_count,
                "missing_count": missing_count,
                "missing_pct": missing_pct,
                "unique_count": unique_count,
                "is_unique": bool(
                    series.is_unique
                ),
            }
        )

    return pd.DataFrame(rows)


def numeric_profile(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:

    numeric = dataframe.select_dtypes(
        include=[
            np.number,
        ]
    )

    if numeric.empty:
        return pd.DataFrame()

    result = numeric.describe(
        percentiles=[
            0.01,
            0.05,
            0.25,
            0.50,
            0.75,
            0.95,
            0.99,
        ]
    ).T

    result = result.rename(
        columns={
            "1%": "p01",
            "5%": "p05",
            "25%": "p25",
            "50%": "median",
            "75%": "p75",
            "95%": "p95",
            "99%": "p99",
        }
    )

    result["missing_count"] = (
        numeric.isna().sum()
    )

    result["missing_pct"] = (
        numeric.isna().mean()
        * 100
    ).round(2)

    result["skewness"] = numeric.skew(
        numeric_only=True
    )

    result = result.reset_index().rename(
        columns={
            "index": "column_name",
        }
    )

    return result


def categorical_profile(
    dataframe: pd.DataFrame,
    max_unique: int = 100,
) -> pd.DataFrame:

    rows = []

    candidate_columns = dataframe.select_dtypes(
        include=[
            "object",
            "string",
            "category",
            "bool",
        ]
    ).columns

    for column in candidate_columns:

        series = dataframe[column]

        unique_count = int(
            series.nunique(
                dropna=True
            )
        )

        if unique_count > max_unique:
            continue

        non_null = series.dropna()

        if non_null.empty:

            top_value = None
            top_count = 0
            top_pct = 0.0

        else:

            counts = non_null.value_counts()

            top_value = counts.index[0]
            top_count = int(
                counts.iloc[0]
            )

            top_pct = round(
                100.0
                * top_count
                / len(non_null),
                2,
            )

        rows.append(
            {
                "column_name": column,
                "unique_count": unique_count,
                "missing_count": int(
                    series.isna().sum()
                ),
                "top_value": top_value,
                "top_count": top_count,
                "top_pct_of_non_null": top_pct,
            }
        )

    return pd.DataFrame(rows)


def iqr_outlier_profile(
    dataframe: pd.DataFrame,
    exclude_columns: set[str] | None = None,
) -> pd.DataFrame:

    exclude_columns = (
        exclude_columns
        or set()
    )

    numeric = dataframe.select_dtypes(
        include=[
            np.number,
        ]
    )

    rows = []

    for column in numeric.columns:

        if column in exclude_columns:
            continue

        series = numeric[column].dropna()

        if series.empty:
            continue

        if series.nunique() <= 2:
            continue

        q1 = series.quantile(
            0.25
        )

        q3 = series.quantile(
            0.75
        )

        iqr = q3 - q1

        lower_bound = (
            q1
            - 1.5 * iqr
        )

        upper_bound = (
            q3
            + 1.5 * iqr
        )

        outlier_mask = (
            (series < lower_bound)
            | (series > upper_bound)
        )

        outlier_count = int(
            outlier_mask.sum()
        )

        outlier_pct = round(
            100.0
            * outlier_count
            / len(series),
            2,
        )

        rows.append(
            {
                "column_name": column,
                "q1": q1,
                "q3": q3,
                "iqr": iqr,
                "lower_bound": lower_bound,
                "upper_bound": upper_bound,
                "outlier_count": outlier_count,
                "outlier_pct": outlier_pct,
            }
        )

    result = pd.DataFrame(rows)

    if not result.empty:
        result = result.sort_values(
            [
                "outlier_pct",
                "outlier_count",
            ],
            ascending=[
                False,
                False,
            ],
        ).reset_index(
            drop=True
        )

    return result


def correlation_matrix(
    dataframe: pd.DataFrame,
    columns: list[str] | None = None,
) -> pd.DataFrame:

    if columns is not None:

        existing_columns = [
            column
            for column in columns
            if column in dataframe.columns
        ]

        numeric = dataframe[
            existing_columns
        ].select_dtypes(
            include=[
                np.number,
            ]
        )

    else:

        numeric = dataframe.select_dtypes(
            include=[
                np.number,
            ]
        )

    if numeric.empty:
        return pd.DataFrame()

    return numeric.corr(
        method="pearson"
    )


def strongest_correlations(
    correlation: pd.DataFrame,
    minimum_absolute_correlation: float = 0.20,
) -> pd.DataFrame:

    if correlation.empty:
        return pd.DataFrame(
            columns=[
                "variable_1",
                "variable_2",
                "correlation",
                "absolute_correlation",
            ]
        )

    rows = []

    columns = list(
        correlation.columns
    )

    for left_index in range(
        len(columns)
    ):

        for right_index in range(
            left_index + 1,
            len(columns),
        ):

            left = columns[
                left_index
            ]

            right = columns[
                right_index
            ]

            value = correlation.loc[
                left,
                right,
            ]

            if pd.isna(value):
                continue

            numeric_value = cast(float, value)

            absolute_value = abs(
                numeric_value
            )

            if (
                absolute_value
                < minimum_absolute_correlation
            ):
                continue

            rows.append(
                {
                    "variable_1": left,
                    "variable_2": right,
                    "correlation": round(
                        numeric_value,
                        4,
                    ),
                    "absolute_correlation": round(
                        absolute_value,
                        4,
                    ),
                }
            )

    result = pd.DataFrame(rows)

    if not result.empty:

        result = result.sort_values(
            "absolute_correlation",
            ascending=False,
        ).reset_index(
            drop=True
        )

    return result