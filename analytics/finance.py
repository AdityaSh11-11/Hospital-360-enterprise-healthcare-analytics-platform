from __future__ import annotations

import numpy as np
import pandas as pd

from analytics.data_loader import (
    load_admission_analysis_dataset,
    load_table,
)
from analytics.statistics import (
    concentration_metrics,
    distribution_summary,
)


def finance_distribution(
    admissions: pd.DataFrame,
) -> pd.DataFrame:
    return distribution_summary(
        admissions,
        [
            "gross_amount",
            "discount_amount",
            "insurance_amount",
            "patient_amount",
            "tax_amount",
            "net_amount",
            "paid_amount",
            "outstanding_amount",
        ],
    )


def payment_status_analysis(
    admissions: pd.DataFrame,
) -> pd.DataFrame:

    result = (
        admissions
        .groupby(
            "payment_status",
            dropna=False,
        )
        .agg(
            bills=(
                "bill_id",
                "count",
            ),
            patients=(
                "patient_id",
                "nunique",
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

    total_bills = result[
        "bills"
    ].sum()

    result[
        "bill_share_pct"
    ] = (
        100.0
        * result["bills"]
        / total_bills
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

    result[
        "outstanding_rate_pct"
    ] = (
        100.0
        * result["outstanding_amount"]
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

    result[
        money_columns
    ] = result[
        money_columns
    ].round(2)

    return result.sort_values(
        "net_revenue",
        ascending=False,
    ).reset_index(
        drop=True
    )


def department_finance_statistics(
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
            average_bill=(
                "net_amount",
                "mean",
            ),
            median_bill=(
                "net_amount",
                "median",
            ),
            bill_std_dev=(
                "net_amount",
                "std",
            ),
        )
        .reset_index()
    )

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
        "collection_efficiency_pct"
    ] = (
        100.0
        * result["collected_amount"]
        / result["net_revenue"].replace(
            0,
            np.nan,
        )
    ).round(2)

    result[
        "bill_cv_pct"
    ] = (
        100.0
        * result["bill_std_dev"]
        / result["average_bill"].replace(
            0,
            np.nan,
        )
    ).round(2)

    total_revenue = result[
        "net_revenue"
    ].sum()

    result[
        "hospital_revenue_share_pct"
    ] = (
        100.0
        * result["net_revenue"]
        / total_revenue
    ).round(2)

    result[
        "revenue_rank"
    ] = result[
        "net_revenue"
    ].rank(
        method="dense",
        ascending=False,
    ).astype(int)

    money_columns = [
        "net_revenue",
        "collected_amount",
        "outstanding_amount",
        "average_bill",
        "median_bill",
        "bill_std_dev",
    ]

    result[
        money_columns
    ] = result[
        money_columns
    ].round(2)

    return result.sort_values(
        [
            "revenue_rank",
            "department_name",
        ]
    ).reset_index(
        drop=True
    )


def monthly_finance_statistics(
    admissions: pd.DataFrame,
) -> pd.DataFrame:

    working = admissions.copy()

    working[
        "billing_date"
    ] = pd.to_datetime(
        working["billing_date"],
        errors="coerce",
    )

    working = working[
        working["billing_date"].notna()
    ].copy()

    working[
        "billing_month"
    ] = (
        working["billing_date"]
        .dt.to_period("M")
        .astype(str)
    )

    result = (
        working
        .groupby(
            "billing_month",
            dropna=False,
        )
        .agg(
            bills=(
                "bill_id",
                "count",
            ),
            billed_patients=(
                "patient_id",
                "nunique",
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
            average_bill=(
                "net_amount",
                "mean",
            ),
        )
        .reset_index()
        .sort_values(
            "billing_month"
        )
    )

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
        "rolling_3_month_revenue"
    ] = (
        result["net_revenue"]
        .rolling(
            3,
            min_periods=1,
        )
        .mean()
        .round(2)
    )

    result[
        "rolling_3_month_collection"
    ] = (
        result["collected_amount"]
        .rolling(
            3,
            min_periods=1,
        )
        .mean()
        .round(2)
    )

    money_columns = [
        "net_revenue",
        "collected_amount",
        "outstanding_amount",
        "average_bill",
    ]

    result[
        money_columns
    ] = result[
        money_columns
    ].round(2)

    return result.reset_index(
        drop=True
    )


def doctor_revenue_concentration() -> pd.DataFrame:

    doctors = load_table(
        "analytics",
        "vw_doctor_analytics_summary",
    )

    metrics = concentration_metrics(
        doctors["net_revenue"]
    )

    return pd.DataFrame(
        [
            {
                "entity": "doctor",
                "entity_count": len(
                    doctors
                ),
                **metrics,
            }
        ]
    )


def department_revenue_concentration(
    admissions: pd.DataFrame,
) -> pd.DataFrame:

    department = (
        admissions
        .groupby(
            "department_name",
            dropna=False,
        )["net_amount"]
        .sum()
    )

    metrics = concentration_metrics(
        department
    )

    return pd.DataFrame(
        [
            {
                "entity": "department",
                "entity_count": len(
                    department
                ),
                **metrics,
            }
        ]
    )


def run_finance_analysis(
    admissions: pd.DataFrame | None = None,
) -> dict[str, pd.DataFrame]:

    if admissions is None:
        admissions = (
            load_admission_analysis_dataset()
        )

    return {
        "finance_distribution":
            finance_distribution(
                admissions
            ),
        "payment_status_statistics":
            payment_status_analysis(
                admissions
            ),
        "department_finance_statistics":
            department_finance_statistics(
                admissions
            ),
        "monthly_finance_statistics":
            monthly_finance_statistics(
                admissions
            ),
        "doctor_revenue_concentration":
            doctor_revenue_concentration(),
        "department_revenue_concentration":
            department_revenue_concentration(
                admissions
            ),
    }