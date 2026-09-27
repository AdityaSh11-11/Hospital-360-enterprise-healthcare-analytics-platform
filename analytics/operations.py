from __future__ import annotations

import numpy as np
import pandas as pd

from analytics.data_loader import (
    load_admission_analysis_dataset,
)
from analytics.statistics import (
    distribution_summary,
    percentile_segment,
)


def length_of_stay_statistics(
    admissions: pd.DataFrame,
) -> pd.DataFrame:

    return distribution_summary(
        admissions,
        [
            "length_of_stay",
        ],
    )


def department_operations_statistics(
    admissions: pd.DataFrame,
) -> pd.DataFrame:

    result = (
        admissions
        .groupby(
            "department_name",
            dropna=False,
        )
        .agg(
            admissions=(
                "admission_id",
                "count",
            ),
            unique_patients=(
                "patient_id",
                "nunique",
            ),
            average_length_of_stay=(
                "length_of_stay",
                "mean",
            ),
            median_length_of_stay=(
                "length_of_stay",
                "median",
            ),
            los_std_dev=(
                "length_of_stay",
                "std",
            ),
            total_inpatient_days=(
                "length_of_stay",
                "sum",
            ),
            emergency_admissions=(
                "emergency_flag",
                "sum",
            ),
            icu_admissions=(
                "icu_flag",
                "sum",
            ),
            readmissions=(
                "readmission_flag",
                "sum",
            ),
        )
        .reset_index()
    )

    result[
        "emergency_rate_pct"
    ] = (
        100.0
        * result["emergency_admissions"]
        / result["admissions"].replace(
            0,
            np.nan,
        )
    ).round(2)

    result[
        "icu_rate_pct"
    ] = (
        100.0
        * result["icu_admissions"]
        / result["admissions"].replace(
            0,
            np.nan,
        )
    ).round(2)

    result[
        "readmission_rate_pct"
    ] = (
        100.0
        * result["readmissions"]
        / result["admissions"].replace(
            0,
            np.nan,
        )
    ).round(2)

    result[
        "los_cv_pct"
    ] = (
        100.0
        * result["los_std_dev"]
        / result[
            "average_length_of_stay"
        ].replace(
            0,
            np.nan,
        )
    ).round(2)

    result[
        "workload_segment"
    ] = percentile_segment(
        result["admissions"],
        labels=(
            "Lower Volume",
            "Moderate Volume",
            "High Volume",
            "Very High Volume",
        ),
    )

    numeric_round = [
        "average_length_of_stay",
        "median_length_of_stay",
        "los_std_dev",
    ]

    result[
        numeric_round
    ] = result[
        numeric_round
    ].round(2)

    return result.sort_values(
        "admissions",
        ascending=False,
    ).reset_index(
        drop=True
    )


def admission_type_statistics(
    admissions: pd.DataFrame,
) -> pd.DataFrame:

    result = (
        admissions
        .groupby(
            "admission_type",
            dropna=False,
        )
        .agg(
            admissions=(
                "admission_id",
                "count",
            ),
            unique_patients=(
                "patient_id",
                "nunique",
            ),
            average_length_of_stay=(
                "length_of_stay",
                "mean",
            ),
            median_length_of_stay=(
                "length_of_stay",
                "median",
            ),
            icu_admissions=(
                "icu_flag",
                "sum",
            ),
            readmissions=(
                "readmission_flag",
                "sum",
            ),
            net_revenue=(
                "net_amount",
                "sum",
            ),
        )
        .reset_index()
    )

    result[
        "icu_rate_pct"
    ] = (
        100.0
        * result["icu_admissions"]
        / result["admissions"].replace(
            0,
            np.nan,
        )
    ).round(2)

    result[
        "readmission_rate_pct"
    ] = (
        100.0
        * result["readmissions"]
        / result["admissions"].replace(
            0,
            np.nan,
        )
    ).round(2)

    result[
        "revenue_per_admission"
    ] = (
        result["net_revenue"]
        / result["admissions"].replace(
            0,
            np.nan,
        )
    ).round(2)

    result[
        "average_length_of_stay"
    ] = result[
        "average_length_of_stay"
    ].round(2)

    result[
        "median_length_of_stay"
    ] = result[
        "median_length_of_stay"
    ].round(2)

    result[
        "net_revenue"
    ] = result[
        "net_revenue"
    ].round(2)

    return result.sort_values(
        "admissions",
        ascending=False,
    ).reset_index(
        drop=True
    )


def day_of_week_statistics(
    admissions: pd.DataFrame,
) -> pd.DataFrame:

    working = admissions.copy()

    working[
        "admission_date"
    ] = pd.to_datetime(
        working["admission_date"],
        errors="coerce",
    )

    working[
        "day_of_week"
    ] = working[
        "admission_date"
    ].dt.day_name()

    working[
        "day_number"
    ] = working[
        "admission_date"
    ].dt.dayofweek

    result = (
        working
        .groupby(
            [
                "day_number",
                "day_of_week",
            ],
            dropna=False,
        )
        .agg(
            admissions=(
                "admission_id",
                "count",
            ),
            emergency_admissions=(
                "emergency_flag",
                "sum",
            ),
            icu_admissions=(
                "icu_flag",
                "sum",
            ),
            readmissions=(
                "readmission_flag",
                "sum",
            ),
            average_length_of_stay=(
                "length_of_stay",
                "mean",
            ),
        )
        .reset_index()
        .sort_values(
            "day_number"
        )
    )

    result[
        "admission_share_pct"
    ] = (
        100.0
        * result["admissions"]
        / result["admissions"].sum()
    ).round(2)

    result[
        "emergency_rate_pct"
    ] = (
        100.0
        * result["emergency_admissions"]
        / result["admissions"].replace(
            0,
            np.nan,
        )
    ).round(2)

    result[
        "readmission_rate_pct"
    ] = (
        100.0
        * result["readmissions"]
        / result["admissions"].replace(
            0,
            np.nan,
        )
    ).round(2)

    result[
        "average_length_of_stay"
    ] = result[
        "average_length_of_stay"
    ].round(2)

    return result.reset_index(
        drop=True
    )


def monthly_operations_statistics(
    admissions: pd.DataFrame,
) -> pd.DataFrame:

    working = admissions.copy()

    working[
        "admission_date"
    ] = pd.to_datetime(
        working["admission_date"],
        errors="coerce",
    )

    working[
        "month_start"
    ] = (
        working["admission_date"]
        .dt.to_period("M")
        .dt.to_timestamp()
    )

    result = (
        working
        .groupby(
            "month_start",
            dropna=False,
        )
        .agg(
            admissions=(
                "admission_id",
                "count",
            ),
            unique_patients=(
                "patient_id",
                "nunique",
            ),
            inpatient_days=(
                "length_of_stay",
                "sum",
            ),
            average_length_of_stay=(
                "length_of_stay",
                "mean",
            ),
            emergency_admissions=(
                "emergency_flag",
                "sum",
            ),
            icu_admissions=(
                "icu_flag",
                "sum",
            ),
            readmissions=(
                "readmission_flag",
                "sum",
            ),
        )
        .reset_index()
        .sort_values(
            "month_start"
        )
    )

    result[
        "readmission_rate_pct"
    ] = (
        100.0
        * result["readmissions"]
        / result["admissions"].replace(
            0,
            np.nan,
        )
    ).round(2)

    result[
        "emergency_rate_pct"
    ] = (
        100.0
        * result["emergency_admissions"]
        / result["admissions"].replace(
            0,
            np.nan,
        )
    ).round(2)

    result[
        "icu_rate_pct"
    ] = (
        100.0
        * result["icu_admissions"]
        / result["admissions"].replace(
            0,
            np.nan,
        )
    ).round(2)

    result[
        "average_length_of_stay"
    ] = result[
        "average_length_of_stay"
    ].round(2)

    result[
        "admission_mom_growth_pct"
    ] = (
        result["admissions"]
        .pct_change(
            fill_method=None
        )
        .mul(100)
        .round(2)
    )

    result[
        "rolling_3_month_admissions"
    ] = (
        result["admissions"]
        .rolling(
            3,
            min_periods=1,
        )
        .mean()
        .round(2)
    )

    return result.reset_index(
        drop=True
    )


def run_operations_analysis(
    admissions: pd.DataFrame | None = None,
) -> dict[str, pd.DataFrame]:

    if admissions is None:
        admissions = (
            load_admission_analysis_dataset()
        )

    return {
        "los_statistics":
            length_of_stay_statistics(
                admissions
            ),
        "department_operations_statistics":
            department_operations_statistics(
                admissions
            ),
        "admission_type_statistics":
            admission_type_statistics(
                admissions
            ),
        "day_of_week_statistics":
            day_of_week_statistics(
                admissions
            ),
        "monthly_operations_statistics":
            monthly_operations_statistics(
                admissions
            ),
    }