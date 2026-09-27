from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

import numpy as np
import pandas as pd

from analytics.data_loader import (
    load_table,
    read_sql,
)


ROBUST_Z_THRESHOLD = 3.5
IQR_MULTIPLIER = 1.5


AGGREGATE_COLUMNS = [
    "anomaly_domain",
    "entity_type",
    "entity_id",
    "metric",
    "observed_value",
    "median_value",
    "mad_value",
    "robust_z_score",
    "direction",
    "threshold",
    "method",
]


@dataclass(frozen=True)
class RobustStatistics:
    median: float
    mad: float
    lower_threshold: float | None
    upper_threshold: float | None


def _numeric_series(
    series: pd.Series,
) -> pd.Series:
    return pd.to_numeric(
        series,
        errors="coerce",
    )


def _empty_aggregate_anomaly_frame() -> pd.DataFrame:
    return pd.DataFrame(
        columns=AGGREGATE_COLUMNS
    )


def robust_z_scores(
    series: pd.Series,
) -> tuple[pd.Series, RobustStatistics]:
    values = _numeric_series(
        series
    )

    median = float(
        values.median()
    )

    absolute_deviation = (
        values - median
    ).abs()

    mad = float(
        absolute_deviation.median()
    )

    if (
        np.isnan(mad)
        or mad == 0
    ):
        scores = pd.Series(
            0.0,
            index=values.index,
            dtype="float64",
        )

        statistics = RobustStatistics(
            median=median,
            mad=mad,
            lower_threshold=None,
            upper_threshold=None,
        )

        return scores, statistics

    scores = (
        0.6745
        * (values - median)
        / mad
    )

    lower_threshold = (
        median
        - (
            ROBUST_Z_THRESHOLD
            * mad
            / 0.6745
        )
    )

    upper_threshold = (
        median
        + (
            ROBUST_Z_THRESHOLD
            * mad
            / 0.6745
        )
    )

    statistics = RobustStatistics(
        median=median,
        mad=mad,
        lower_threshold=float(
            lower_threshold
        ),
        upper_threshold=float(
            upper_threshold
        ),
    )

    return scores, statistics


def iqr_bounds(
    series: pd.Series,
) -> tuple[float, float, float, float]:
    values = _numeric_series(
        series
    ).dropna()

    if values.empty:
        raise RuntimeError(
            "Cannot calculate IQR bounds "
            "for an empty numeric series."
        )

    q1 = float(
        values.quantile(0.25)
    )

    q3 = float(
        values.quantile(0.75)
    )

    iqr = q3 - q1

    lower = (
        q1
        - IQR_MULTIPLIER
        * iqr
    )

    upper = (
        q3
        + IQR_MULTIPLIER
        * iqr
    )

    return (
        q1,
        q3,
        float(lower),
        float(upper),
    )


def classify_robust_direction(
    score: float,
) -> str:
    if score >= ROBUST_Z_THRESHOLD:
        return "High"

    if score <= -ROBUST_Z_THRESHOLD:
        return "Low"

    return "Normal"


def _build_robust_anomalies(
    dataframe: pd.DataFrame,
    metrics: list[str],
    anomaly_domain: str,
    entity_type: str,
    entity_column: str,
) -> pd.DataFrame:
    rows: list[dict] = []

    for metric in metrics:
        scores, statistics = robust_z_scores(
            dataframe[metric]
        )

        for index in dataframe.index:
            score = scores.loc[index]

            if pd.isna(score):
                continue

            direction = classify_robust_direction(
                float(score)
            )

            if direction == "Normal":
                continue

            observed = dataframe.loc[
                index,
                metric,
            ]

            if not pd.api.types.is_scalar(observed):
                continue

            observed_is_na = pd.isna(observed)
            if pd.api.types.is_scalar(observed_is_na) and bool(observed_is_na):
                continue

            rows.append(
                {
                    "anomaly_domain":
                        anomaly_domain,
                    "entity_type":
                        entity_type,
                    "entity_id":
                        dataframe.loc[
                            index,
                            entity_column,
                        ],
                    "metric":
                        metric,
                    "observed_value":
                        float(cast(Any, observed)),
                    "median_value":
                        statistics.median,
                    "mad_value":
                        statistics.mad,
                    "robust_z_score":
                        round(
                            float(score),
                            4,
                        ),
                    "direction":
                        direction,
                    "threshold":
                        ROBUST_Z_THRESHOLD,
                    "method":
                        "Median/MAD Robust Z",
                }
            )

    if not rows:
        return _empty_aggregate_anomaly_frame()

    result = pd.DataFrame(
        rows,
        columns=AGGREGATE_COLUMNS,
    )

    return (
        result
        .sort_values(
            [
                "metric",
                "robust_z_score",
            ],
            ascending=[
                True,
                False,
            ],
        )
        .reset_index(drop=True)
    )


def build_monthly_anomalies() -> pd.DataFrame:
    dataframe = load_table(
        "analytics",
        "vw_monthly_hospital_performance",
    ).copy()

    required = {
        "month_start",
        "admissions",
        "net_revenue",
        "collected_amount",
        "outstanding_amount",
    }

    missing = (
        required
        - set(dataframe.columns)
    )

    if missing:
        raise RuntimeError(
            "Monthly hospital view missing columns: "
            + ", ".join(
                sorted(missing)
            )
        )

    dataframe["month_start"] = pd.to_datetime(
        dataframe["month_start"].array,
        errors="coerce",
    )

    return _build_robust_anomalies(
        dataframe=dataframe,
        metrics=[
            "admissions",
            "net_revenue",
            "collected_amount",
            "outstanding_amount",
        ],
        anomaly_domain="Monthly Hospital",
        entity_type="Month",
        entity_column="month_start",
    )


def build_monthly_operations_anomalies() -> pd.DataFrame:
    """
    Build operational monthly anomalies from columns that are
    actually present in vw_monthly_operations_trend.

    We intentionally use raw operational counts instead of assuming
    emergency_rate_pct and icu_rate_pct exist in the SQL view.
    """

    dataframe = load_table(
        "analytics",
        "vw_monthly_operations_trend",
    ).copy()

    required = {
        "month_start",
        "admissions",
        "average_length_of_stay",
        "emergency_admissions",
        "icu_admissions",
        "readmissions",
        "readmission_rate_pct",
    }

    missing = (
        required
        - set(dataframe.columns)
    )

    if missing:
        raise RuntimeError(
            "Monthly operations view missing columns: "
            + ", ".join(
                sorted(missing)
            )
        )

    dataframe["month_start"] = pd.to_datetime(
        dataframe["month_start"],
        errors="coerce",
    )

    return _build_robust_anomalies(
        dataframe=dataframe,
        metrics=[
            "admissions",
            "average_length_of_stay",
            "emergency_admissions",
            "icu_admissions",
            "readmissions",
            "readmission_rate_pct",
        ],
        anomaly_domain="Monthly Operations",
        entity_type="Month",
        entity_column="month_start",
    )


def build_monthly_claim_anomalies() -> pd.DataFrame:
    dataframe = load_table(
        "analytics",
        "vw_monthly_claim_risk",
    ).copy()

    required = {
        "month_start",
        "total_claims",
        "claim_amount",
        "rejected_amount",
        "high_risk_claim_rate_pct",
        "rejected_value_rate_pct",
    }

    missing = (
        required
        - set(dataframe.columns)
    )

    if missing:
        raise RuntimeError(
            "Monthly claim risk view missing columns: "
            + ", ".join(
                sorted(missing)
            )
        )

    dataframe["month_start"] = pd.to_datetime(
        dataframe["month_start"],
        errors="coerce",
    )

    return _build_robust_anomalies(
        dataframe=dataframe,
        metrics=[
            "total_claims",
            "claim_amount",
            "rejected_amount",
            "high_risk_claim_rate_pct",
            "rejected_value_rate_pct",
        ],
        anomaly_domain="Monthly Claims",
        entity_type="Month",
        entity_column="month_start",
    )


def build_department_anomalies() -> pd.DataFrame:
    dataframe = load_table(
        "analytics",
        "vw_department_performance",
    ).copy()

    required = {
        "department_name",
        "admissions",
        "average_length_of_stay",
        "readmission_rate_pct",
        "net_revenue",
        "outstanding_amount",
    }

    missing = (
        required
        - set(dataframe.columns)
    )

    if missing:
        raise RuntimeError(
            "Department performance view "
            "missing columns: "
            + ", ".join(
                sorted(missing)
            )
        )

    return _build_robust_anomalies(
        dataframe=dataframe,
        metrics=[
            "admissions",
            "average_length_of_stay",
            "readmission_rate_pct",
            "net_revenue",
            "outstanding_amount",
        ],
        anomaly_domain="Department",
        entity_type="Department",
        entity_column="department_name",
    )


def build_bill_value_anomalies() -> pd.DataFrame:
    dataframe = load_table(
        "analytics",
        "vw_bill_financial_risk",
    ).copy()

    required = {
        "bill_id",
        "patient_id",
        "department_name",
        "doctor_name",
        "billing_date",
        "net_amount",
        "outstanding_amount",
        "financial_risk_score",
        "financial_risk_band",
    }

    missing = (
        required
        - set(dataframe.columns)
    )

    if missing:
        raise RuntimeError(
            "Bill financial risk view "
            "missing columns: "
            + ", ".join(
                sorted(missing)
            )
        )

    metrics = [
        "net_amount",
        "outstanding_amount",
    ]

    rows: list[dict] = []

    for metric in metrics:
        (
            q1,
            q3,
            lower_bound,
            upper_bound,
        ) = iqr_bounds(
            dataframe[metric]
        )

        values = _numeric_series(
            dataframe[metric]
        )

        mask = (
            (values < lower_bound)
            | (values > upper_bound)
        )

        subset = dataframe.loc[
            mask
        ].copy()

        for _, row in subset.iterrows():
            observed = float(
                row[metric]
            )

            direction = (
                "High"
                if observed > upper_bound
                else "Low"
            )

            rows.append(
                {
                    "bill_id":
                        row["bill_id"],
                    "patient_id":
                        row["patient_id"],
                    "department_name":
                        row["department_name"],
                    "doctor_name":
                        row["doctor_name"],
                    "billing_date":
                        row["billing_date"],
                    "metric":
                        metric,
                    "observed_value":
                        observed,
                    "q1":
                        q1,
                    "q3":
                        q3,
                    "lower_bound":
                        lower_bound,
                    "upper_bound":
                        upper_bound,
                    "direction":
                        direction,
                    "financial_risk_score":
                        row[
                            "financial_risk_score"
                        ],
                    "financial_risk_band":
                        row[
                            "financial_risk_band"
                        ],
                    "method":
                        "IQR 1.5x",
                }
            )

    columns = [
        "bill_id",
        "patient_id",
        "department_name",
        "doctor_name",
        "billing_date",
        "metric",
        "observed_value",
        "q1",
        "q3",
        "lower_bound",
        "upper_bound",
        "direction",
        "financial_risk_score",
        "financial_risk_band",
        "method",
    ]

    if not rows:
        return pd.DataFrame(
            columns=columns
        )

    result = pd.DataFrame(
        rows,
        columns=columns,
    )

    return (
        result
        .sort_values(
            [
                "metric",
                "observed_value",
            ],
            ascending=[
                True,
                False,
            ],
        )
        .reset_index(drop=True)
    )


def build_los_anomalies() -> pd.DataFrame:
    dataframe = read_sql(
        """
        SELECT
            a.admission_id,
            p.patient_id,
            d.department_name,
            doc.doctor_name,
            a.admission_timestamp,
            a.length_of_stay,
            a.readmission_flag,
            a.emergency_flag,
            a.icu_flag

        FROM warehouse.fact_admission a

        INNER JOIN warehouse.dim_patient p
            ON p.patient_key = a.patient_key

        INNER JOIN warehouse.dim_department d
            ON d.department_key = a.department_key

        INNER JOIN warehouse.dim_doctor doc
            ON doc.doctor_key = a.doctor_key
        """
    )

    (
        q1,
        q3,
        lower_bound,
        upper_bound,
    ) = iqr_bounds(
        dataframe[
            "length_of_stay"
        ]
    )

    values = _numeric_series(
        dataframe[
            "length_of_stay"
        ]
    )

    mask = (
        (values < lower_bound)
        | (values > upper_bound)
    )

    result = dataframe.loc[
        mask
    ].copy()

    result["q1"] = q1
    result["q3"] = q3
    result["lower_bound"] = lower_bound
    result["upper_bound"] = upper_bound

    result["direction"] = np.where(
        result[
            "length_of_stay"
        ] > upper_bound,
        "High",
        "Low",
    )

    result["method"] = "IQR 1.5x"

    return (
        result
        .sort_values(
            "length_of_stay",
            ascending=False,
        )
        .reset_index(drop=True)
    )


def combine_aggregate_anomalies(
    *dataframes: pd.DataFrame,
) -> pd.DataFrame:
    available = [
        dataframe
        for dataframe in dataframes
        if not dataframe.empty
    ]

    if not available:
        result = (
            _empty_aggregate_anomaly_frame()
        )

        result[
            "absolute_robust_z_score"
        ] = pd.Series(
            dtype="float64"
        )

        return result

    result = pd.concat(
        available,
        ignore_index=True,
    )

    result[
        "absolute_robust_z_score"
    ] = (
        result[
            "robust_z_score"
        ].abs()
    )

    return (
        result
        .sort_values(
            "absolute_robust_z_score",
            ascending=False,
        )
        .reset_index(drop=True)
    )


def build_anomaly_summary(
    aggregate_anomalies: pd.DataFrame,
    bill_anomalies: pd.DataFrame,
    los_anomalies: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict] = []

    if not aggregate_anomalies.empty:
        grouped = (
            aggregate_anomalies
            .groupby(
                [
                    "anomaly_domain",
                    "direction",
                ],
                dropna=False,
            )
            .size()
            .reset_index(
                name="anomaly_count"
            )
        )

        for _, row in grouped.iterrows():
            rows.append(
                {
                    "anomaly_scope":
                        row[
                            "anomaly_domain"
                        ],
                    "direction":
                        row["direction"],
                    "anomaly_count":
                        int(
                            row[
                                "anomaly_count"
                            ]
                        ),
                    "method":
                        "Median/MAD Robust Z",
                }
            )

    if not bill_anomalies.empty:
        grouped = (
            bill_anomalies
            .groupby(
                [
                    "metric",
                    "direction",
                ],
                dropna=False,
            )
            .size()
            .reset_index(
                name="anomaly_count"
            )
        )

        for _, row in grouped.iterrows():
            rows.append(
                {
                    "anomaly_scope":
                        (
                            "Bill - "
                            f"{row['metric']}"
                        ),
                    "direction":
                        row["direction"],
                    "anomaly_count":
                        int(
                            row[
                                "anomaly_count"
                            ]
                        ),
                    "method":
                        "IQR 1.5x",
                }
            )

    if not los_anomalies.empty:
        grouped = (
            los_anomalies
            .groupby(
                "direction",
                dropna=False,
            )
            .size()
            .reset_index(
                name="anomaly_count"
            )
        )

        for _, row in grouped.iterrows():
            rows.append(
                {
                    "anomaly_scope":
                        "Admission LOS",
                    "direction":
                        row["direction"],
                    "anomaly_count":
                        int(
                            row[
                                "anomaly_count"
                            ]
                        ),
                    "method":
                        "IQR 1.5x",
                }
            )

    return pd.DataFrame(
        rows,
        columns=[
            "anomaly_scope",
            "direction",
            "anomaly_count",
            "method",
        ],
    )


def build_anomaly_management_insights(
    aggregate_anomalies: pd.DataFrame,
    bill_anomalies: pd.DataFrame,
    los_anomalies: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict] = []

    if not aggregate_anomalies.empty:
        strongest = (
            aggregate_anomalies
            .sort_values(
                "absolute_robust_z_score",
                ascending=False,
            )
            .iloc[0]
        )

        rows.append(
            {
                "sequence": 1,
                "domain":
                    "Aggregate Anomaly",
                "insight":
                    (
                        "The strongest aggregate "
                        "statistical anomaly is "
                        f"{strongest['metric']} for "
                        f"{strongest['entity_id']}, "
                        "with a robust z-score of "
                        f"{float(strongest['robust_z_score']):+.2f}. "
                        "This is a review signal, "
                        "not evidence of an error, "
                        "fraud, or misconduct."
                    ),
            }
        )

    if not bill_anomalies.empty:
        net_bill = bill_anomalies[
            bill_anomalies[
                "metric"
            ] == "net_amount"
        ]

        outstanding = bill_anomalies[
            bill_anomalies[
                "metric"
            ] == "outstanding_amount"
        ]

        rows.append(
            {
                "sequence": 2,
                "domain":
                    "Bill Values",
                "insight":
                    (
                        f"{len(net_bill):,} bill observations "
                        "are outside the 1.5×IQR range for "
                        "net amount, while "
                        f"{len(outstanding):,} are outside "
                        "the range for recorded outstanding "
                        "amount."
                    ),
            }
        )

    if not los_anomalies.empty:
        rows.append(
            {
                "sequence": 3,
                "domain":
                    "Length of Stay",
                "insight":
                    (
                        f"{len(los_anomalies):,} admissions "
                        "fall outside the 1.5×IQR range for "
                        "length of stay. These observations "
                        "are statistical extremes and are "
                        "not automatically invalid stays."
                    ),
            }
        )

    if aggregate_anomalies.empty:
        high_count = 0
        low_count = 0
    else:
        high_count = int(
            (
                aggregate_anomalies[
                    "direction"
                ]
                == "High"
            ).sum()
        )

        low_count = int(
            (
                aggregate_anomalies[
                    "direction"
                ]
                == "Low"
            ).sum()
        )

    rows.append(
        {
            "sequence": 4,
            "domain":
                "Aggregate Direction",
            "insight":
                (
                    f"{high_count:,} aggregate observations "
                    "are unusually high and "
                    f"{low_count:,} are unusually low "
                    "under the configured robust-z "
                    "threshold."
                ),
        }
    )

    return (
        pd.DataFrame(
            rows,
            columns=[
                "sequence",
                "domain",
                "insight",
            ],
        )
        .sort_values("sequence")
        .reset_index(drop=True)
    )


def run_anomaly_analysis() -> dict[str, pd.DataFrame]:
    monthly_hospital = (
        build_monthly_anomalies()
    )

    monthly_operations = (
        build_monthly_operations_anomalies()
    )

    monthly_claims = (
        build_monthly_claim_anomalies()
    )

    departments = (
        build_department_anomalies()
    )

    bills = (
        build_bill_value_anomalies()
    )

    los = (
        build_los_anomalies()
    )

    aggregate = (
        combine_aggregate_anomalies(
            monthly_hospital,
            monthly_operations,
            monthly_claims,
            departments,
        )
    )

    summary = (
        build_anomaly_summary(
            aggregate_anomalies=
                aggregate,
            bill_anomalies=
                bills,
            los_anomalies=
                los,
        )
    )

    insights = (
        build_anomaly_management_insights(
            aggregate_anomalies=
                aggregate,
            bill_anomalies=
                bills,
            los_anomalies=
                los,
        )
    )

    return {
        "monthly_hospital_anomalies":
            monthly_hospital,

        "monthly_operations_anomalies":
            monthly_operations,

        "monthly_claim_anomalies":
            monthly_claims,

        "department_anomalies":
            departments,

        "aggregate_anomalies":
            aggregate,

        "bill_value_anomalies":
            bills,

        "los_anomalies":
            los,

        "anomaly_summary":
            summary,

        "anomaly_management_insights":
            insights,
    }