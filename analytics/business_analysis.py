from __future__ import annotations

import numpy as np
import pandas as pd

from analytics.data_loader import (
    load_admission_analysis_dataset,
    load_table,
)


def safe_pct(
    numerator: pd.Series,
    denominator: pd.Series,
) -> pd.Series:
    return (
        100.0
        * numerator
        / denominator.replace(0, np.nan)
    )


def build_monthly_kpi_variance() -> pd.DataFrame:
    """
    Build management-facing month-over-month KPI variance.

    Operational KPIs follow admission month.
    Financial KPIs come from the locked monthly hospital
    analytical view.

    The source view contains operational months only, so
    finance-only future billing months are intentionally
    excluded from this comparison.
    """

    data = load_table(
        "analytics",
        "vw_hospital_monthly_comparison",
    ).copy()

    date_column = None

    for candidate in [
        "month_start",
        "month_date",
        "month",
    ]:
        if candidate in data.columns:
            date_column = candidate
            break

    if date_column is None:
        raise RuntimeError(
            "vw_hospital_monthly_comparison does not "
            "contain a recognized month column."
        )

    data[date_column] = pd.to_datetime(
        data[date_column],
        errors="coerce",
    )

    data = (
        data
        .sort_values(date_column)
        .reset_index(drop=True)
    )

    metrics = [
        "admissions",
        "average_length_of_stay",
        "readmission_rate_pct",
        "net_revenue",
        "collected_amount",
        "outstanding_amount",
    ]

    existing_metrics = [
        metric
        for metric in metrics
        if metric in data.columns
    ]

    for metric in existing_metrics:
        data[
            f"{metric}_previous_month"
        ] = data[metric].shift(1)

        data[
            f"{metric}_absolute_variance"
        ] = (
            data[metric]
            - data[
                f"{metric}_previous_month"
            ]
        )

        data[
            f"{metric}_variance_pct"
        ] = (
            data[metric]
            .pct_change(fill_method=None)
            .mul(100)
            .replace(
                [np.inf, -np.inf],
                np.nan,
            )
            .round(2)
        )

    return data


def build_department_benchmark() -> pd.DataFrame:
    """
    Benchmark departments against hospital averages.

    Positive/negative variance is descriptive only.
    It is not a quality score or clinical judgment.
    """

    data = load_table(
        "analytics",
        "vw_department_performance",
    ).copy()

    required = [
        "department_name",
        "admissions",
        "average_length_of_stay",
        "readmission_rate_pct",
        "net_revenue",
    ]

    missing = [
        column
        for column in required
        if column not in data.columns
    ]

    if missing:
        raise RuntimeError(
            "vw_department_performance missing columns: "
            + ", ".join(missing)
        )

    hospital_admissions = data[
        "admissions"
    ].sum()

    hospital_revenue = data[
        "net_revenue"
    ].sum()

    hospital_alos = np.average(
        data["average_length_of_stay"],
        weights=data["admissions"],
    )

    hospital_readmission_rate = np.average(
        data["readmission_rate_pct"],
        weights=data["admissions"],
    )

    data[
        "admission_share_pct"
    ] = (
        100.0
        * data["admissions"]
        / hospital_admissions
    ).round(2)

    data[
        "revenue_share_pct"
    ] = (
        100.0
        * data["net_revenue"]
        / hospital_revenue
    ).round(2)

    data[
        "alos_vs_hospital"
    ] = (
        data["average_length_of_stay"]
        - hospital_alos
    ).round(2)

    data[
        "readmission_rate_vs_hospital_pct_point"
    ] = (
        data["readmission_rate_pct"]
        - hospital_readmission_rate
    ).round(2)

    data[
        "revenue_per_admission"
    ] = (
        data["net_revenue"]
        / data["admissions"].replace(
            0,
            np.nan,
        )
    ).round(2)

    data[
        "admission_index"
    ] = (
        100.0
        * data["admissions"]
        / data["admissions"].mean()
    ).round(2)

    data[
        "revenue_index"
    ] = (
        100.0
        * data["net_revenue"]
        / data["net_revenue"].mean()
    ).round(2)

    data[
        "revenue_per_admission_index"
    ] = (
        100.0
        * data["revenue_per_admission"]
        / data[
            "revenue_per_admission"
        ].mean()
    ).round(2)

    return (
        data
        .sort_values(
            "net_revenue",
            ascending=False,
        )
        .reset_index(drop=True)
    )


def build_doctor_benchmark() -> pd.DataFrame:
    """
    Benchmark doctors against department-level peers.

    No clinical quality ranking is produced.
    """

    data = load_table(
        "analytics",
        "vw_doctor_analytics_summary",
    ).copy()

    required = [
        "doctor_id",
        "doctor_name",
        "department_name",
        "admissions",
        "net_revenue",
    ]

    missing = [
        column
        for column in required
        if column not in data.columns
    ]

    if missing:
        raise RuntimeError(
            "vw_doctor_analytics_summary missing columns: "
            + ", ".join(missing)
        )

    department = (
        data
        .groupby(
            "department_name",
            dropna=False,
        )
        .agg(
            department_doctors=(
                "doctor_id",
                "nunique",
            ),
            department_average_admissions=(
                "admissions",
                "mean",
            ),
            department_average_revenue=(
                "net_revenue",
                "mean",
            ),
        )
        .reset_index()
    )

    data = data.merge(
        department,
        on="department_name",
        how="left",
        validate="many_to_one",
    )

    data[
        "admissions_vs_department_average"
    ] = (
        data["admissions"]
        - data[
            "department_average_admissions"
        ]
    ).round(2)

    data[
        "revenue_vs_department_average"
    ] = (
        data["net_revenue"]
        - data[
            "department_average_revenue"
        ]
    ).round(2)

    data[
        "admission_index"
    ] = (
        100.0
        * data["admissions"]
        / data[
            "department_average_admissions"
        ].replace(
            0,
            np.nan,
        )
    ).round(2)

    data[
        "revenue_index"
    ] = (
        100.0
        * data["net_revenue"]
        / data[
            "department_average_revenue"
        ].replace(
            0,
            np.nan,
        )
    ).round(2)

    data[
        "department_admission_rank"
    ] = (
        data
        .groupby(
            "department_name"
        )["admissions"]
        .rank(
            method="dense",
            ascending=False,
        )
        .astype(int)
    )

    data[
        "department_revenue_rank"
    ] = (
        data
        .groupby(
            "department_name"
        )["net_revenue"]
        .rank(
            method="dense",
            ascending=False,
        )
        .astype(int)
    )

    return (
        data
        .sort_values(
            [
                "department_name",
                "department_revenue_rank",
                "doctor_name",
            ]
        )
        .reset_index(drop=True)
    )


def build_finance_diagnostics() -> pd.DataFrame:
    """
    Build department-level finance diagnostic metrics.
    """

    data = load_table(
        "analytics",
        "vw_department_finance",
    ).copy()

    required = [
        "department_name",
        "net_revenue",
        "collected_amount",
        "outstanding_amount",
    ]

    missing = [
        column
        for column in required
        if column not in data.columns
    ]

    if missing:
        raise RuntimeError(
            "vw_department_finance missing columns: "
            + ", ".join(missing)
        )

    data[
        "collection_efficiency_pct_python"
    ] = safe_pct(
        data["collected_amount"],
        data["net_revenue"],
    ).round(2)

    data[
        "outstanding_rate_pct_python"
    ] = safe_pct(
        data["outstanding_amount"],
        data["net_revenue"],
    ).round(2)

    total_outstanding = data[
        "outstanding_amount"
    ].sum()

    data[
        "outstanding_share_pct"
    ] = (
        100.0
        * data["outstanding_amount"]
        / total_outstanding
    ).round(2)

    data[
        "collection_efficiency_vs_hospital_pct_point"
    ] = (
        data[
            "collection_efficiency_pct_python"
        ]
        - (
            100.0
            * data["collected_amount"].sum()
            / data["net_revenue"].sum()
        )
    ).round(2)

    data[
        "outstanding_rate_vs_hospital_pct_point"
    ] = (
        data[
            "outstanding_rate_pct_python"
        ]
        - (
            100.0
            * data["outstanding_amount"].sum()
            / data["net_revenue"].sum()
        )
    ).round(2)

    data[
        "outstanding_rank"
    ] = (
        data["outstanding_amount"]
        .rank(
            method="dense",
            ascending=False,
        )
        .astype(int)
    )

    return (
        data
        .sort_values(
            "outstanding_rank"
        )
        .reset_index(drop=True)
    )


def build_claim_diagnostics() -> pd.DataFrame:
    """
    Build insurer-level claim diagnostics.
    """

    data = load_table(
        "analytics",
        "vw_insurer_claim_performance",
    ).copy()

    required = [
        "insurer_name",
        "total_claims",
        "claim_amount",
        "rejected_amount",
    ]

    missing = [
        column
        for column in required
        if column not in data.columns
    ]

    if missing:
        raise RuntimeError(
            "vw_insurer_claim_performance missing columns: "
            + ", ".join(missing)
        )

    if "rejected_claims" in data.columns:
        data[
            "rejection_rate_pct_python"
        ] = safe_pct(
            data["rejected_claims"],
            data["total_claims"],
        ).round(2)

    data[
        "rejected_amount_rate_pct"
    ] = safe_pct(
        data["rejected_amount"],
        data["claim_amount"],
    ).round(2)

    total_claim_amount = data[
        "claim_amount"
    ].sum()

    total_rejected_amount = data[
        "rejected_amount"
    ].sum()

    data[
        "claim_amount_share_pct"
    ] = (
        100.0
        * data["claim_amount"]
        / total_claim_amount
    ).round(2)

    data[
        "rejected_amount_share_pct"
    ] = (
        100.0
        * data["rejected_amount"]
        / total_rejected_amount
    ).round(2)

    data[
        "rejected_amount_rank"
    ] = (
        data["rejected_amount"]
        .rank(
            method="dense",
            ascending=False,
        )
        .astype(int)
    )

    return (
        data
        .sort_values(
            "rejected_amount_rank"
        )
        .reset_index(drop=True)
    )


def build_operational_driver_analysis(
    admissions: pd.DataFrame,
) -> pd.DataFrame:
    """
    Compare major operational cohorts.

    These are descriptive cohort statistics,
    not causal estimates.
    """

    cohort_definitions = {
        "All Admissions":
            pd.Series(
                True,
                index=admissions.index,
            ),

        "Emergency":
            admissions[
                "emergency_flag"
            ].fillna(False).astype(bool),

        "Non-Emergency":
            ~admissions[
                "emergency_flag"
            ].fillna(False).astype(bool),

        "ICU":
            admissions[
                "icu_flag"
            ].fillna(False).astype(bool),

        "Non-ICU":
            ~admissions[
                "icu_flag"
            ].fillna(False).astype(bool),

        "Readmission Flag":
            admissions[
                "readmission_flag"
            ].fillna(False).astype(bool),

        "No Readmission Flag":
            ~admissions[
                "readmission_flag"
            ].fillna(False).astype(bool),
    }

    rows = []

    for cohort_name, mask in (
        cohort_definitions.items()
    ):
        cohort = admissions.loc[
            mask
        ]

        admission_count = len(cohort)

        if admission_count == 0:
            continue

        rows.append(
            {
                "cohort": cohort_name,

                "admissions":
                    admission_count,

                "unique_patients":
                    cohort[
                        "patient_id"
                    ].nunique(),

                "average_length_of_stay":
                    round(
                        float(
                            cohort[
                                "length_of_stay"
                            ].mean()
                        ),
                        2,
                    ),

                "median_length_of_stay":
                    round(
                        float(
                            cohort[
                                "length_of_stay"
                            ].median()
                        ),
                        2,
                    ),

                "average_net_revenue":
                    round(
                        float(
                            cohort[
                                "net_amount"
                            ].mean()
                        ),
                        2,
                    ),

                "total_net_revenue":
                    round(
                        float(
                            cohort[
                                "net_amount"
                            ].sum()
                        ),
                        2,
                    ),

                "average_outstanding":
                    round(
                        float(
                            cohort[
                                "outstanding_amount"
                            ].mean()
                        ),
                        2,
                    ),

                "readmission_rate_pct":
                    round(
                        float(
                            100.0
                            * cohort[
                                "readmission_flag"
                            ].mean()
                        ),
                        2,
                    ),

                "icu_rate_pct":
                    round(
                        float(
                            100.0
                            * cohort[
                                "icu_flag"
                            ].mean()
                        ),
                        2,
                    ),

                "emergency_rate_pct":
                    round(
                        float(
                            100.0
                            * cohort[
                                "emergency_flag"
                            ].mean()
                        ),
                        2,
                    ),
            }
        )

    return pd.DataFrame(rows)


def build_management_insight_table(
    monthly: pd.DataFrame,
    departments: pd.DataFrame,
    doctors: pd.DataFrame,
    finance: pd.DataFrame,
    claims: pd.DataFrame,
) -> pd.DataFrame:
    """
    Produce machine-readable management observations.

    These are deterministic analytical observations,
    not AI-generated conclusions.
    """

    insights = []

    if not monthly.empty:
        latest = monthly.iloc[-1]

        month_column = next(
            (
                column
                for column in [
                    "month_start",
                    "month_date",
                    "month",
                ]
                if column in monthly.columns
            ),
            None,
        )

        month_value = (
            latest[month_column]
            if month_column
            else None
        )

        for metric in [
            "admissions",
            "net_revenue",
            "collected_amount",
            "outstanding_amount",
        ]:
            variance_column = (
                f"{metric}_variance_pct"
            )

            if (
                metric in monthly.columns
                and variance_column
                in monthly.columns
                and pd.notna(
                    latest[
                        variance_column
                    ]
                )
            ):
                insights.append(
                    {
                        "domain": "Monthly Trend",
                        "subject": metric,
                        "period": month_value,
                        "metric_value":
                            latest[metric],
                        "comparison_value":
                            latest[
                                variance_column
                            ],
                        "comparison_unit":
                            "MoM %",
                        "observation":
                            (
                                f"{metric} changed "
                                f"{latest[variance_column]:.2f}% "
                                "versus the previous month."
                            ),
                    }
                )

    if not departments.empty:
        highest_revenue = (
            departments
            .sort_values(
                "net_revenue",
                ascending=False,
            )
            .iloc[0]
        )

        insights.append(
            {
                "domain": "Department",
                "subject":
                    highest_revenue[
                        "department_name"
                    ],
                "period": None,
                "metric_value":
                    highest_revenue[
                        "net_revenue"
                    ],
                "comparison_value":
                    highest_revenue[
                        "revenue_share_pct"
                    ],
                "comparison_unit":
                    "Hospital revenue share %",
                "observation":
                    (
                        f"{highest_revenue['department_name']} "
                        "has the highest department net revenue "
                        f"and represents "
                        f"{highest_revenue['revenue_share_pct']:.2f}% "
                        "of hospital revenue."
                    ),
            }
        )

    if not doctors.empty:
        highest_doctor_revenue = (
            doctors
            .sort_values(
                "net_revenue",
                ascending=False,
            )
            .iloc[0]
        )

        insights.append(
            {
                "domain": "Doctor",
                "subject":
                    highest_doctor_revenue[
                        "doctor_name"
                    ],
                "period": None,
                "metric_value":
                    highest_doctor_revenue[
                        "net_revenue"
                    ],
                "comparison_value":
                    highest_doctor_revenue[
                        "revenue_index"
                    ],
                "comparison_unit":
                    "Department revenue index",
                "observation":
                    (
                        f"{highest_doctor_revenue['doctor_name']} "
                        "has the highest doctor net revenue; "
                        f"their department-relative revenue "
                        f"index is "
                        f"{highest_doctor_revenue['revenue_index']:.2f}."
                    ),
            }
        )

    if not finance.empty:
        highest_outstanding = (
            finance
            .sort_values(
                "outstanding_amount",
                ascending=False,
            )
            .iloc[0]
        )

        insights.append(
            {
                "domain": "Finance",
                "subject":
                    highest_outstanding[
                        "department_name"
                    ],
                "period": None,
                "metric_value":
                    highest_outstanding[
                        "outstanding_amount"
                    ],
                "comparison_value":
                    highest_outstanding[
                        "outstanding_share_pct"
                    ],
                "comparison_unit":
                    "Outstanding share %",
                "observation":
                    (
                        f"{highest_outstanding['department_name']} "
                        "has the largest department outstanding "
                        "balance and represents "
                        f"{highest_outstanding['outstanding_share_pct']:.2f}% "
                        "of department-level outstanding balances."
                    ),
            }
        )

    if not claims.empty:
        highest_rejected = (
            claims
            .sort_values(
                "rejected_amount",
                ascending=False,
            )
            .iloc[0]
        )

        insights.append(
            {
                "domain": "Claims",
                "subject":
                    highest_rejected[
                        "insurer_name"
                    ],
                "period": None,
                "metric_value":
                    highest_rejected[
                        "rejected_amount"
                    ],
                "comparison_value":
                    highest_rejected[
                        "rejected_amount_share_pct"
                    ],
                "comparison_unit":
                    "Rejected amount share %",
                "observation":
                    (
                        f"{highest_rejected['insurer_name']} "
                        "has the largest rejected claim amount "
                        "among insurers and represents "
                        f"{highest_rejected['rejected_amount_share_pct']:.2f}% "
                        "of rejected claim value."
                    ),
            }
        )

    return pd.DataFrame(insights)


def run_business_analysis() -> dict[str, pd.DataFrame]:
    admissions = (
        load_admission_analysis_dataset()
    )

    monthly = (
        build_monthly_kpi_variance()
    )

    departments = (
        build_department_benchmark()
    )

    doctors = (
        build_doctor_benchmark()
    )

    finance = (
        build_finance_diagnostics()
    )

    claims = (
        build_claim_diagnostics()
    )

    operational_drivers = (
        build_operational_driver_analysis(
            admissions
        )
    )

    management_insights = (
        build_management_insight_table(
            monthly=monthly,
            departments=departments,
            doctors=doctors,
            finance=finance,
            claims=claims,
        )
    )

    return {
        "monthly_kpi_variance":
            monthly,

        "department_benchmark":
            departments,

        "doctor_benchmark":
            doctors,

        "finance_diagnostics":
            finance,

        "claim_diagnostics":
            claims,

        "operational_driver_analysis":
            operational_drivers,

        "management_insights":
            management_insights,
    }