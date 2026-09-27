from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

from analytics.data_loader import (
    load_admission_analysis_dataset,
    load_department_performance,
    load_doctor_performance,
    load_monthly_hospital_performance,
)
from analytics.profiling import (
    categorical_profile,
    column_profile,
    correlation_matrix,
    dataset_overview,
    iqr_outlier_profile,
    numeric_profile,
    strongest_correlations,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_EXPORT_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "exports"
    / "eda"
)


CORRELATION_COLUMNS = [
    "length_of_stay",
    "gross_amount",
    "discount_amount",
    "insurance_amount",
    "patient_amount",
    "tax_amount",
    "net_amount",
    "paid_amount",
    "outstanding_amount",
]


OUTLIER_EXCLUDE_COLUMNS = {
    "admission_key",
    "patient_key",
    "doctor_key",
    "department_key",
    "diagnosis_key",
    "billing_key",
    "bed_capacity",
}


def add_derived_features(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:

    result = dataframe.copy()

    if (
        "date_of_birth"
        in result.columns
        and "admission_date"
        in result.columns
    ):

        age_days = (
            result["admission_date"]
            - result["date_of_birth"]
        ).dt.days

        result[
            "patient_age_at_admission"
        ] = np.floor(
            age_days / 365.2425
        )

        result.loc[
            result[
                "patient_age_at_admission"
            ] < 0,
            "patient_age_at_admission",
        ] = np.nan

    if "admission_date" in result.columns:

        result[
            "admission_year"
        ] = result[
            "admission_date"
        ].dt.year

        result[
            "admission_month"
        ] = result[
            "admission_date"
        ].dt.month

        result[
            "admission_month_name"
        ] = result[
            "admission_date"
        ].dt.month_name()

        result[
            "admission_day_name"
        ] = result[
            "admission_date"
        ].dt.day_name()

        result[
            "admission_year_month"
        ] = result[
            "admission_date"
        ].dt.to_period(
            "M"
        ).astype(str)

    if (
        "net_amount"
        in result.columns
        and "length_of_stay"
        in result.columns
    ):

        denominator = result[
            "length_of_stay"
        ].replace(
            0,
            np.nan,
        )

        result[
            "revenue_per_inpatient_day"
        ] = (
            result["net_amount"]
            / denominator
        )

    if (
        "paid_amount"
        in result.columns
        and "net_amount"
        in result.columns
    ):

        denominator = result[
            "net_amount"
        ].replace(
            0,
            np.nan,
        )

        result[
            "admission_collection_ratio"
        ] = (
            result["paid_amount"]
            / denominator
        )

    return result


def build_department_eda(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:

    result = (
        dataframe
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
            net_revenue=(
                "net_amount",
                "sum",
            ),
            collected_amount=(
                "paid_amount",
                "sum",
            ),
            outstanding_amount=(
                "outstanding_amount",
                "sum",
            ),
        )
        .reset_index()
    )

    result[
        "average_length_of_stay"
    ] = result[
        "average_length_of_stay"
    ].round(2)

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
        "collection_efficiency_pct"
    ] = (
        100.0
        * result["collected_amount"]
        / result["net_revenue"].replace(
            0,
            np.nan,
        )
    ).round(2)

    money_columns = [
        "net_revenue",
        "collected_amount",
        "outstanding_amount",
    ]

    result[money_columns] = result[
        money_columns
    ].round(2)

    return result.sort_values(
        "net_revenue",
        ascending=False,
    ).reset_index(
        drop=True
    )


def build_monthly_eda(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:

    result = (
        dataframe
        .groupby(
            "admission_year_month",
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
            net_revenue=(
                "net_amount",
                "sum",
            ),
            collected_amount=(
                "paid_amount",
                "sum",
            ),
            outstanding_amount=(
                "outstanding_amount",
                "sum",
            ),
        )
        .reset_index()
        .sort_values(
            "admission_year_month"
        )
    )

    result[
        "average_length_of_stay"
    ] = result[
        "average_length_of_stay"
    ].round(2)

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
        "revenue_mom_growth_pct"
    ] = (
        result["net_revenue"]
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
            window=3,
            min_periods=1,
        )
        .mean()
        .round(2)
    )

    result[
        "rolling_3_month_revenue"
    ] = (
        result["net_revenue"]
        .rolling(
            window=3,
            min_periods=1,
        )
        .mean()
        .round(2)
    )

    money_columns = [
        "net_revenue",
        "collected_amount",
        "outstanding_amount",
    ]

    result[money_columns] = result[
        money_columns
    ].round(2)

    return result.reset_index(
        drop=True
    )


def build_category_analysis(
    dataframe: pd.DataFrame,
    column: str,
) -> pd.DataFrame:

    if column not in dataframe.columns:
        return pd.DataFrame()

    result = (
        dataframe
        .groupby(
            column,
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
        "average_length_of_stay"
    ] = result[
        "average_length_of_stay"
    ].round(2)

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


def run_eda(
    export_directory: Path | None = None,
) -> dict[str, pd.DataFrame]:

    export_directory = (
        export_directory
        or DEFAULT_EXPORT_DIRECTORY
    )

    export_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    admissions = (
        load_admission_analysis_dataset()
    )

    admissions = add_derived_features(
        admissions
    )

    overview = dataset_overview(
        admissions,
        "admission_analysis_dataset",
    )

    overview_df = pd.DataFrame(
        [
            asdict(
                overview
            )
        ]
    )

    columns_df = column_profile(
        admissions
    )

    numeric_df = numeric_profile(
        admissions
    )

    categorical_df = categorical_profile(
        admissions
    )

    outliers_df = iqr_outlier_profile(
        admissions,
        exclude_columns=OUTLIER_EXCLUDE_COLUMNS,
    )

    correlation_df = correlation_matrix(
        admissions,
        columns=CORRELATION_COLUMNS
        + [
            "patient_age_at_admission",
            "revenue_per_inpatient_day",
            "admission_collection_ratio",
        ],
    )

    strong_correlations_df = (
        strongest_correlations(
            correlation_df,
            minimum_absolute_correlation=0.20,
        )
    )

    department_df = build_department_eda(
        admissions
    )

    monthly_df = build_monthly_eda(
        admissions
    )

    admission_type_df = (
        build_category_analysis(
            admissions,
            "admission_type",
        )
    )

    room_type_df = (
        build_category_analysis(
            admissions,
            "room_type",
        )
    )

    outcome_df = (
        build_category_analysis(
            admissions,
            "outcome",
        )
    )

    diagnosis_df = (
        build_category_analysis(
            admissions,
            "diagnosis_name",
        )
    )

    chronic_df = (
        build_category_analysis(
            admissions,
            "chronic_condition",
        )
    )

    sql_department_df = (
        load_department_performance()
    )

    sql_doctor_df = (
        load_doctor_performance()
    )

    sql_monthly_df = (
        load_monthly_hospital_performance()
    )

    outputs = {
        "dataset_overview": overview_df,
        "column_profile": columns_df,
        "numeric_profile": numeric_df,
        "categorical_profile": categorical_df,
        "outlier_profile": outliers_df,
        "correlation_matrix": correlation_df,
        "strongest_correlations": strong_correlations_df,
        "department_analysis": department_df,
        "monthly_analysis": monthly_df,
        "admission_type_analysis": admission_type_df,
        "room_type_analysis": room_type_df,
        "outcome_analysis": outcome_df,
        "diagnosis_analysis": diagnosis_df,
        "chronic_condition_analysis": chronic_df,
        "sql_department_reference": sql_department_df,
        "sql_doctor_reference": sql_doctor_df,
        "sql_monthly_reference": sql_monthly_df,
    }

    for name, dataframe in outputs.items():

        dataframe.to_csv(
            export_directory
            / f"{name}.csv",
            index=(
                name
                == "correlation_matrix"
            ),
        )

    return outputs