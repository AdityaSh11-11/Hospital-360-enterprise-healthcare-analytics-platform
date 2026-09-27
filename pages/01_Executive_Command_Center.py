from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from analytics.data_loader import read_sql
from utils.app_helpers import (
    bootstrap_page,
    dataframe,
    format_currency_compact,
    format_integer,
    format_percentage,
    management_insight,
    metric_row,
    render_refresh_button,
    section_header,
)


bootstrap_page(
    title="Executive Command Center",
    subtitle=(
        "Hospital-wide leadership view of patients, operations, finance, "
        "departments and insurance claims."
    ),
    icon="🏥",
)


def first_existing(
    df: pd.DataFrame,
    candidates: list[str],
) -> str | None:
    if df is None or df.empty:
        return None

    for column in candidates:
        if column in df.columns:
            return column

    return None


def value_from(
    df: pd.DataFrame,
    candidates: list[str],
    default: Any = None,
) -> Any:
    if df is None or df.empty:
        return default

    column = first_existing(
        df,
        candidates,
    )

    if column is None:
        return default

    value = df.iloc[0][column]

    try:
        if pd.isna(value):
            return default
    except (TypeError, ValueError):
        pass

    return value


def safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        if value is None:
            return default

        if pd.isna(value):
            return default

        return float(value)

    except (TypeError, ValueError):
        return default


def clean_label(value: Any) -> str:
    return (
        str(value)
        .replace("_", " ")
        .strip()
        .title()
    )


def style_figure(
    figure: go.Figure,
    *,
    height: int = 390,
    unified_hover: bool = False,
) -> go.Figure:
    figure.update_layout(
        height=height,
        margin=dict(
            l=15,
            r=15,
            t=55,
            b=15,
        ),
        legend_title_text="",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            size=13,
        ),
        title=dict(
            font=dict(
                size=17,
            ),
        ),
    )

    if unified_hover:
        figure.update_layout(
            hovermode="x unified",
        )

    return figure


def normalize_date_column(
    df: pd.DataFrame,
    candidates: list[str],
) -> tuple[pd.DataFrame, str | None]:
    result = df.copy()

    column = first_existing(
        result,
        candidates,
    )

    if column is None:
        return result, None

    result[column] = pd.to_datetime(
        result[column],
        errors="coerce",
    )

    result = result.sort_values(
        column,
        ascending=True,
        na_position="last",
    )

    return result, column


def page_section(
    number: str,
    title: str,
    description: str,
) -> None:
    st.markdown(
        f"""
        <div class="h360-section-banner">
            <div class="h360-section-number">{number}</div>
            <div>
                <div class="h360-section-title">{title}</div>
                <div class="h360-section-description">{description}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def card_heading(
    title: str,
    description: str,
) -> None:
    st.markdown(
        f"""
        <div class="h360-card-heading">
            <div class="h360-card-title">{title}</div>
            <div class="h360-card-description">{description}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def explanation_box(
    title: str,
    text: str,
) -> None:
    st.markdown(
        f"""
        <div class="h360-explanation">
            <div class="h360-explanation-title">{title}</div>
            <div class="h360-explanation-text">{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.markdown(
    """
    <style>
    .h360-flow {
        background: linear-gradient(135deg, #eff6ff 0%, #f8fbff 100%);
        border: 1px solid #bfdbfe;
        border-radius: 18px;
        padding: 22px 24px;
        margin: 8px 0 30px 0;
        box-shadow: 0 5px 18px rgba(15, 71, 122, 0.06);
    }

    .h360-flow-title {
        color: #0f3d66;
        font-size: 1.08rem;
        font-weight: 800;
        margin-bottom: 8px;
    }

    .h360-flow-text {
        color: #526579;
        font-size: 0.95rem;
        line-height: 1.7;
    }

    .h360-section-banner {
        display: flex;
        align-items: center;
        gap: 16px;
        background: linear-gradient(135deg, #edf6ff 0%, #f8fbff 100%);
        border: 1px solid #c9e1f7;
        border-left: 5px solid #2563a6;
        border-radius: 16px;
        padding: 18px 20px;
        margin-top: 34px;
        margin-bottom: 18px;
        box-shadow: 0 4px 14px rgba(15, 61, 102, 0.05);
    }

    .h360-section-number {
        min-width: 46px;
        height: 46px;
        border-radius: 13px;
        background: #174f7f;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 0.95rem;
    }

    .h360-section-title {
        color: #143b5d;
        font-size: 1.22rem;
        font-weight: 800;
        margin-bottom: 4px;
    }

    .h360-section-description {
        color: #60758a;
        font-size: 0.92rem;
        line-height: 1.55;
    }

    .h360-card-heading {
        background: #ffffff;
        border: 1px solid #d8e6f3;
        border-radius: 14px;
        padding: 15px 17px;
        margin: 6px 0 10px 0;
        box-shadow: 0 3px 12px rgba(15, 61, 102, 0.04);
    }

    .h360-card-title {
        color: #174f7f;
        font-weight: 800;
        font-size: 1rem;
        margin-bottom: 4px;
    }

    .h360-card-description {
        color: #687d90;
        font-size: 0.87rem;
        line-height: 1.5;
    }

    .h360-explanation {
        background: #f8fbff;
        border: 1px solid #d7e8f7;
        border-radius: 13px;
        padding: 14px 16px;
        margin-top: 6px;
        margin-bottom: 16px;
    }

    .h360-explanation-title {
        color: #174f7f;
        font-weight: 800;
        font-size: 0.9rem;
        margin-bottom: 5px;
    }

    .h360-explanation-text {
        color: #5c7083;
        font-size: 0.87rem;
        line-height: 1.6;
    }

    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #d8e6f3;
        border-radius: 15px;
        padding: 16px 16px 14px 16px;
        box-shadow: 0 4px 14px rgba(15, 61, 102, 0.05);
    }

    div[data-testid="stPlotlyChart"] {
        background: #ffffff;
        border: 1px solid #d8e6f3;
        border-radius: 16px;
        padding: 8px;
        box-shadow: 0 4px 14px rgba(15, 61, 102, 0.05);
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid #d8e6f3;
        border-radius: 14px;
        overflow: hidden;
    }

    div[data-testid="stDateInput"] {
        max-width: 650px;
    }

    .stAlert {
        border-radius: 14px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(
    ttl=60,
    show_spinner=False,
)
def load_executive_kpis() -> pd.DataFrame:
    return read_sql(
        """
        SELECT *
        FROM analytics.vw_executive_kpis
        """
    )


@st.cache_data(
    ttl=60,
    show_spinner=False,
)
def load_monthly_performance() -> pd.DataFrame:
    return read_sql(
        """
        SELECT *
        FROM analytics.vw_monthly_hospital_performance
        """
    )


@st.cache_data(
    ttl=60,
    show_spinner=False,
)
def load_department_performance() -> pd.DataFrame:
    return read_sql(
        """
        SELECT *
        FROM analytics.vw_department_performance
        """
    )


@st.cache_data(
    ttl=60,
    show_spinner=False,
)
def load_claim_performance() -> pd.DataFrame:
    return read_sql(
        """
        SELECT *
        FROM analytics.vw_claim_performance
        """
    )


@st.cache_data(
    ttl=60,
    show_spinner=False,
)
def load_daily_operations() -> pd.DataFrame:
    return read_sql(
        """
        SELECT *
        FROM analytics.vw_daily_operations
        """
    )


try:
    executive = load_executive_kpis()
    monthly = load_monthly_performance()
    departments = load_department_performance()
    claims = load_claim_performance()
    daily = load_daily_operations()

except Exception as exc:
    st.error(
        "Executive Command Center could not load the required "
        "analytics views."
    )
    st.exception(exc)
    st.stop()


monthly, month_column = normalize_date_column(
    monthly,
    [
        "month_start",
        "month_date",
        "reporting_month",
        "month",
        "period_start",
        "year_month",
    ],
)

daily, daily_date_column = normalize_date_column(
    daily,
    [
        "full_date",
        "operation_date",
        "activity_date",
        "admission_date",
        "date",
        "calendar_date",
    ],
)


total_patients = value_from(
    executive,
    [
        "total_patients",
        "patients",
    ],
    0,
)

total_admissions = value_from(
    executive,
    [
        "total_admissions",
        "admissions",
    ],
    0,
)

admitted_patients = value_from(
    executive,
    [
        "admitted_patients",
        "unique_admitted_patients",
        "unique_patients",
    ],
    None,
)

average_los = value_from(
    executive,
    [
        "average_length_of_stay",
        "avg_length_of_stay",
        "average_los",
        "avg_los",
        "alos",
    ],
    None,
)

readmissions = value_from(
    executive,
    [
        "readmissions",
        "total_readmissions",
    ],
    None,
)

readmission_rate = value_from(
    executive,
    [
        "readmission_rate_pct",
        "readmission_rate",
    ],
    None,
)

net_revenue = value_from(
    executive,
    [
        "net_revenue",
        "total_net_revenue",
        "total_revenue",
        "revenue",
    ],
    0,
)

collected_amount = value_from(
    executive,
    [
        "collected_amount",
        "total_collected",
        "paid_amount",
        "total_paid",
    ],
    None,
)

outstanding_amount = value_from(
    executive,
    [
        "outstanding_amount",
        "total_outstanding",
        "outstanding_balance",
    ],
    None,
)

collection_efficiency = value_from(
    executive,
    [
        "collection_efficiency_pct",
        "collection_efficiency",
        "collection_rate_pct",
        "collection_rate",
    ],
    None,
)

total_claims = value_from(
    executive,
    [
        "total_claims",
        "claims",
    ],
    0,
)

rejected_claims = value_from(
    executive,
    [
        "rejected_claims",
        "total_rejected_claims",
    ],
    None,
)

claim_rejection_rate = value_from(
    executive,
    [
        "claim_rejection_rate_pct",
        "claim_rejection_rate",
        "rejection_rate_pct",
        "rejection_rate",
    ],
    None,
)


st.markdown(
    """
    <div class="h360-flow">
        <div class="h360-flow-title">How to read this dashboard</div>
        <div class="h360-flow-text">
            Start with the hospital scorecard to understand overall scale.
            Then review financial position and the selected reporting period.
            Continue through hospital trends, department performance,
            claims and daily operations. Finish with management signals
            to identify where deeper analysis is required.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


page_section(
    "01",
    "Hospital Scorecard",
    "A quick leadership snapshot of hospital scale, utilization, finance and claims.",
)

metric_row(
    [
        (
            "Patients",
            format_integer(total_patients),
        ),
        (
            "Admissions",
            format_integer(total_admissions),
        ),
        (
            "Net Revenue",
            format_currency_compact(net_revenue),
        ),
        (
            "Collection Efficiency",
            format_percentage(collection_efficiency),
        ),
    ]
)

metric_row(
    [
        (
            "Average Length of Stay",
            (
                f"{safe_float(average_los):,.2f} days"
                if average_los is not None
                else "—"
            ),
        ),
        (
            "Readmission Rate",
            format_percentage(readmission_rate),
        ),
        (
            "Outstanding Amount",
            format_currency_compact(outstanding_amount),
        ),
        (
            "Claim Rejection Rate",
            format_percentage(claim_rejection_rate),
        ),
    ]
)

insight_parts: list[str] = []

if admitted_patients is not None:
    insight_parts.append(
        f"{format_integer(admitted_patients)} unique patients "
        "have recorded hospital admissions."
    )

if average_los is not None:
    insight_parts.append(
        f"Average length of stay is "
        f"{safe_float(average_los):,.2f} days."
    )

if readmission_rate is not None:
    insight_parts.append(
        f"Recorded readmission rate is "
        f"{format_percentage(readmission_rate)}."
    )

if collection_efficiency is not None:
    insight_parts.append(
        f"Collection efficiency is "
        f"{format_percentage(collection_efficiency)}."
    )

if claim_rejection_rate is not None:
    insight_parts.append(
        f"Claim rejection rate is "
        f"{format_percentage(claim_rejection_rate)}."
    )

management_insight(
    (
        " ".join(insight_parts)
        if insight_parts
        else (
            "Hospital-wide analytics data is available "
            "for executive review."
        )
    ),
    label="Executive Summary",
)


page_section(
    "02",
    "Financial Position",
    "Understand how much the hospital has billed, collected and still has outstanding.",
)

finance1, finance2, finance3, finance4 = st.columns(4)

finance1.metric(
    "Net Revenue",
    format_currency_compact(net_revenue),
)

finance2.metric(
    "Collected Amount",
    format_currency_compact(collected_amount),
)

finance3.metric(
    "Outstanding Amount",
    format_currency_compact(outstanding_amount),
)

finance4.metric(
    "Collection Efficiency",
    format_percentage(collection_efficiency),
)

explanation_box(
    "How to interpret this section",
    (
        "Net Revenue represents recorded net billing. Collected Amount "
        "shows recorded payments, while Outstanding Amount represents "
        "the remaining billing balance in the synthetic warehouse. "
        "Collection Efficiency shows the share of net billing represented "
        "by recorded paid amounts."
    ),
)


filtered_monthly = monthly.copy()
filtered_daily = daily.copy()

page_section(
    "03",
    "Reporting Period",
    "Choose the period used by the monthly and daily trend sections below.",
)

if (
    month_column is not None
    and not monthly.empty
):
    valid_months = (
        monthly[month_column]
        .dropna()
        .sort_values()
    )

    if not valid_months.empty:
        min_date = valid_months.min().date()
        max_date = valid_months.max().date()

        selected_period = st.date_input(
            "Select analysis period",
            value=(
                min_date,
                max_date,
            ),
            min_value=min_date,
            max_value=max_date,
        )

        if (
            isinstance(
                selected_period,
                (tuple, list),
            )
            and len(selected_period) == 2
        ):
            start_date = pd.Timestamp(
                selected_period[0]
            )

            end_date = (
                pd.Timestamp(
                    selected_period[1]
                )
                + pd.offsets.MonthEnd(1)
            )

            filtered_monthly = (
                monthly[
                    (
                        monthly[month_column]
                        >= start_date
                    )
                    & (
                        monthly[month_column]
                        <= end_date
                    )
                ]
                .copy()
            )

            if daily_date_column is not None:
                filtered_daily = (
                    daily[
                        (
                            daily[daily_date_column]
                            >= start_date
                        )
                        & (
                            daily[daily_date_column]
                            <= end_date
                        )
                    ]
                    .copy()
                )
else:
    st.info(
        "The current monthly analytics view does not expose "
        "a recognized reporting-period field."
    )


page_section(
    "04",
    "Hospital Performance Trend",
    "Explore how admissions, revenue and patient activity change over time.",
)

monthly_admissions_col = first_existing(
    filtered_monthly,
    [
        "total_admissions",
        "admissions",
        "admission_count",
    ],
)

monthly_revenue_col = first_existing(
    filtered_monthly,
    [
        "net_revenue",
        "total_net_revenue",
        "revenue",
        "total_revenue",
    ],
)

monthly_patient_col = first_existing(
    filtered_monthly,
    [
        "unique_patients",
        "patients",
        "patient_count",
        "admitted_patients",
    ],
)

trend_left, trend_right = st.columns(2)

with trend_left:
    card_heading(
        "Monthly Admissions",
        "Tracks hospital admission workload across the selected reporting period.",
    )

    if (
        month_column is not None
        and monthly_admissions_col is not None
        and not filtered_monthly.empty
    ):
        fig = px.line(
            filtered_monthly,
            x=month_column,
            y=monthly_admissions_col,
            markers=True,
        )

        fig.update_xaxes(
            title=None,
        )

        fig.update_yaxes(
            title="Admissions",
        )

        st.plotly_chart(
            style_figure(
                fig,
                height=370,
                unified_hover=True,
            ),
            width="stretch",
        )

        explanation_box(
            "What this chart tells you",
            (
                "Use this trend to identify periods with higher or lower "
                "hospital admission activity. Peaks indicate heavier "
                "hospital workload during the selected period."
            ),
        )

    else:
        st.info(
            "Monthly admission trend is not exposed by "
            "the current analytics view."
        )


with trend_right:
    card_heading(
        "Monthly Net Revenue",
        "Shows how recorded hospital net revenue changes month by month.",
    )

    if (
        month_column is not None
        and monthly_revenue_col is not None
        and not filtered_monthly.empty
    ):
        fig = px.line(
            filtered_monthly,
            x=month_column,
            y=monthly_revenue_col,
            markers=True,
        )

        fig.update_xaxes(
            title=None,
        )

        fig.update_yaxes(
            title="Net Revenue",
        )

        st.plotly_chart(
            style_figure(
                fig,
                height=370,
                unified_hover=True,
            ),
            width="stretch",
        )

        explanation_box(
            "What this chart tells you",
            (
                "This trend shows the movement of recorded net revenue "
                "across the selected period and helps leadership compare "
                "financial activity between months."
            ),
        )

    else:
        st.info(
            "Monthly revenue trend is not exposed by "
            "the current analytics view."
        )


if (
    month_column is not None
    and monthly_patient_col is not None
    and not filtered_monthly.empty
):
    card_heading(
        "Monthly Patient Activity",
        "Shows the number of patients represented in hospital activity over time.",
    )

    fig = px.area(
        filtered_monthly,
        x=month_column,
        y=monthly_patient_col,
    )

    fig.update_xaxes(
        title=None,
    )

    fig.update_yaxes(
        title="Patients",
    )

    st.plotly_chart(
        style_figure(
            fig,
            height=340,
            unified_hover=True,
        ),
        width="stretch",
    )

    explanation_box(
        "What this chart tells you",
        (
            "Patient activity provides another view of hospital demand. "
            "Compare this pattern with admissions to understand how "
            "patient volume changes across the reporting period."
        ),
    )


page_section(
    "05",
    "Department Performance",
    "Compare hospital departments by workload, financial contribution and available performance indicators.",
)

department_name_col = first_existing(
    departments,
    [
        "department_name",
        "department",
    ],
)

department_admissions_col = first_existing(
    departments,
    [
        "total_admissions",
        "admissions",
        "admission_count",
    ],
)

department_revenue_col = first_existing(
    departments,
    [
        "net_revenue",
        "total_net_revenue",
        "revenue",
        "total_revenue",
    ],
)

department_los_col = first_existing(
    departments,
    [
        "average_length_of_stay",
        "avg_length_of_stay",
        "average_los",
        "avg_los",
    ],
)

department_readmission_col = first_existing(
    departments,
    [
        "readmission_rate_pct",
        "readmission_rate",
    ],
)

dept_left, dept_right = st.columns(2)

with dept_left:
    card_heading(
        "Admissions by Department",
        "Compares department workload using recorded admission volume.",
    )

    if (
        department_name_col is not None
        and department_admissions_col is not None
        and not departments.empty
    ):
        chart_data = departments[
            [
                department_name_col,
                department_admissions_col,
            ]
        ].copy()

        chart_data[
            department_admissions_col
        ] = pd.to_numeric(
            chart_data[
                department_admissions_col
            ],
            errors="coerce",
        )

        chart_data = chart_data.sort_values(
            department_admissions_col,
            ascending=True,
        )

        fig = px.bar(
            chart_data,
            x=department_admissions_col,
            y=department_name_col,
            orientation="h",
            text_auto=True,
        )

        fig.update_xaxes(
            title="Admissions",
        )

        fig.update_yaxes(
            title=None,
        )

        st.plotly_chart(
            style_figure(
                fig,
                height=440,
            ),
            width="stretch",
        )

        explanation_box(
            "What this chart tells you",
            (
                "Departments with longer bars handle more recorded "
                "admissions and therefore represent a larger share "
                "of hospital admission workload."
            ),
        )

    else:
        st.info(
            "Department admission volume is not exposed "
            "by the current analytics view."
        )


with dept_right:
    card_heading(
        "Net Revenue by Department",
        "Compares the recorded financial contribution of each department.",
    )

    if (
        department_name_col is not None
        and department_revenue_col is not None
        and not departments.empty
    ):
        chart_data = departments[
            [
                department_name_col,
                department_revenue_col,
            ]
        ].copy()

        chart_data[
            department_revenue_col
        ] = pd.to_numeric(
            chart_data[
                department_revenue_col
            ],
            errors="coerce",
        )

        chart_data = chart_data.sort_values(
            department_revenue_col,
            ascending=True,
        )

        fig = px.bar(
            chart_data,
            x=department_revenue_col,
            y=department_name_col,
            orientation="h",
        )

        fig.update_xaxes(
            title="Net Revenue",
        )

        fig.update_yaxes(
            title=None,
        )

        st.plotly_chart(
            style_figure(
                fig,
                height=440,
            ),
            width="stretch",
        )

        explanation_box(
            "What this chart tells you",
            (
                "This comparison identifies departments associated "
                "with larger or smaller recorded net revenue values. "
                "It should be interpreted alongside department workload."
            ),
        )

    else:
        st.info(
            "Department revenue is not exposed "
            "by the current analytics view."
        )


card_heading(
    "Department Management Matrix",
    (
        "A single management table combining the department indicators "
        "available in the analytics layer."
    ),
)

department_columns: list[str] = []

for candidate_group in [
    [
        "department_name",
        "department",
    ],
    [
        "total_admissions",
        "admissions",
    ],
    [
        "unique_patients",
        "patients",
    ],
    [
        "average_length_of_stay",
        "avg_length_of_stay",
        "average_los",
        "avg_los",
    ],
    [
        "readmission_rate_pct",
        "readmission_rate",
    ],
    [
        "net_revenue",
        "total_net_revenue",
        "revenue",
    ],
]:
    resolved = first_existing(
        departments,
        candidate_group,
    )

    if (
        resolved is not None
        and resolved not in department_columns
    ):
        department_columns.append(
            resolved
        )

if department_columns:
    department_table = departments[
        department_columns
    ].copy()

    department_table = department_table.rename(
        columns={
            column: clean_label(column)
            for column in department_table.columns
        }
    )

    dataframe(
        department_table,
        height=390,
    )

else:
    st.info(
        "No recognized department management columns "
        "are exposed by the current analytics view."
    )


page_section(
    "06",
    "Claims & Payer Performance",
    "Review claim volume and compare insurer performance using the available claims indicators.",
)

claims1, claims2, claims3 = st.columns(3)

claims1.metric(
    "Total Claims",
    format_integer(total_claims),
)

claims2.metric(
    "Rejected Claims",
    format_integer(rejected_claims),
)

claims3.metric(
    "Claim Rejection Rate",
    format_percentage(claim_rejection_rate),
)

claim_name_col = first_existing(
    claims,
    [
        "insurer_name",
        "insurer",
        "payer_name",
    ],
)

claim_count_col = first_existing(
    claims,
    [
        "total_claims",
        "claims",
        "claim_count",
    ],
)

claim_rejection_col = first_existing(
    claims,
    [
        "rejection_rate_pct",
        "rejection_rate",
        "claim_rejection_rate_pct",
        "claim_rejection_rate",
    ],
)

claim_amount_col = first_existing(
    claims,
    [
        "claim_amount",
        "total_claim_amount",
        "claimed_amount",
    ],
)

claim_left, claim_right = st.columns(2)

with claim_left:
    card_heading(
        "Claim Volume by Insurer",
        "Compares the number of claims associated with each insurer.",
    )

    if (
        claim_name_col is not None
        and claim_count_col is not None
        and not claims.empty
    ):
        chart_data = claims[
            [
                claim_name_col,
                claim_count_col,
            ]
        ].copy()

        chart_data[
            claim_count_col
        ] = pd.to_numeric(
            chart_data[
                claim_count_col
            ],
            errors="coerce",
        )

        chart_data = chart_data.sort_values(
            claim_count_col,
            ascending=True,
        )

        fig = px.bar(
            chart_data,
            x=claim_count_col,
            y=claim_name_col,
            orientation="h",
            text_auto=True,
        )

        fig.update_yaxes(
            title=None,
        )

        fig.update_xaxes(
            title="Claims",
        )

        st.plotly_chart(
            style_figure(
                fig,
                height=380,
            ),
            width="stretch",
        )

        explanation_box(
            "What this chart tells you",
            (
                "This chart identifies insurers responsible for larger "
                "or smaller shares of the hospital's recorded claim volume."
            ),
        )

    else:
        st.info(
            "Insurer claim volume is not exposed "
            "by the current analytics view."
        )


with claim_right:
    if (
        claim_name_col is not None
        and claim_rejection_col is not None
        and not claims.empty
    ):
        card_heading(
            "Claim Rejection Rate by Insurer",
            "Compares the recorded rejection rate across insurers.",
        )

        chart_data = claims[
            [
                claim_name_col,
                claim_rejection_col,
            ]
        ].copy()

        chart_data[
            claim_rejection_col
        ] = pd.to_numeric(
            chart_data[
                claim_rejection_col
            ],
            errors="coerce",
        )

        chart_data = chart_data.sort_values(
            claim_rejection_col,
            ascending=True,
        )

        fig = px.bar(
            chart_data,
            x=claim_rejection_col,
            y=claim_name_col,
            orientation="h",
            text_auto=True,
        )

        fig.update_yaxes(
            title=None,
        )

        fig.update_xaxes(
            title="Rejection Rate",
        )

        st.plotly_chart(
            style_figure(
                fig,
                height=380,
            ),
            width="stretch",
        )

        explanation_box(
            "What this chart tells you",
            (
                "Higher rejection rates indicate insurers that may require "
                "closer review of claim outcomes and rejection patterns."
            ),
        )

    elif (
        claim_name_col is not None
        and claim_amount_col is not None
        and not claims.empty
    ):
        card_heading(
            "Claim Value by Insurer",
            "Compares recorded claim amounts across insurers.",
        )

        chart_data = claims[
            [
                claim_name_col,
                claim_amount_col,
            ]
        ].copy()

        chart_data[
            claim_amount_col
        ] = pd.to_numeric(
            chart_data[
                claim_amount_col
            ],
            errors="coerce",
        )

        chart_data = chart_data.sort_values(
            claim_amount_col,
            ascending=True,
        )

        fig = px.bar(
            chart_data,
            x=claim_amount_col,
            y=claim_name_col,
            orientation="h",
        )

        fig.update_yaxes(
            title=None,
        )

        fig.update_xaxes(
            title="Claim Value",
        )

        st.plotly_chart(
            style_figure(
                fig,
                height=380,
            ),
            width="stretch",
        )

        explanation_box(
            "What this chart tells you",
            (
                "This comparison highlights insurers associated with "
                "larger recorded claim values in the hospital dataset."
            ),
        )

    else:
        card_heading(
            "Payer Comparison",
            "Insurer-level rejection or claim-value comparison.",
        )

        st.info(
            "Payer rejection or value comparison is not exposed "
            "by the current analytics view."
        )


page_section(
    "07",
    "Operational Activity",
    "Follow daily hospital workload and understand how major operational event types move together.",
)

daily_admission_col = first_existing(
    filtered_daily,
    [
        "total_admissions",
        "admissions",
        "admission_count",
    ],
)

daily_emergency_col = first_existing(
    filtered_daily,
    [
        "emergency_admissions",
        "emergency_count",
        "total_emergency_admissions",
    ],
)

daily_icu_col = first_existing(
    filtered_daily,
    [
        "icu_admissions",
        "icu_count",
        "total_icu_admissions",
    ],
)

daily_readmission_col = first_existing(
    filtered_daily,
    [
        "readmissions",
        "readmission_count",
        "total_readmissions",
    ],
)

card_heading(
    "Daily Hospital Activity",
    (
        "Daily movement in admissions and any available emergency, ICU "
        "and readmission activity."
    ),
)

if (
    daily_date_column is not None
    and daily_admission_col is not None
    and not filtered_daily.empty
):
    value_columns = [
        column
        for column in [
            daily_admission_col,
            daily_emergency_col,
            daily_icu_col,
            daily_readmission_col,
        ]
        if column is not None
    ]

    chart_data = filtered_daily[
        [
            daily_date_column,
            *value_columns,
        ]
    ].copy()

    for column in value_columns:
        chart_data[column] = pd.to_numeric(
            chart_data[column],
            errors="coerce",
        )

    chart_data = chart_data.melt(
        id_vars=[
            daily_date_column,
        ],
        value_vars=value_columns,
        var_name="Metric",
        value_name="Events",
    )

    chart_data[
        "Metric"
    ] = chart_data[
        "Metric"
    ].map(clean_label)

    fig = px.line(
        chart_data,
        x=daily_date_column,
        y="Events",
        color="Metric",
    )

    fig.update_xaxes(
        title=None,
    )

    fig.update_yaxes(
        title="Events",
    )

    st.plotly_chart(
        style_figure(
            fig,
            height=420,
            unified_hover=True,
        ),
        width="stretch",
    )

    explanation_box(
        "What this chart tells you",
        (
            "The daily view helps leadership see short-term workload "
            "movement. Compare admissions with emergency, ICU and "
            "readmission activity when those measures are available."
        ),
    )

else:
    st.info(
        "The daily operations view loaded successfully, but "
        "no recognized date and admission combination is "
        "available for the trend chart."
    )


page_section(
    "08",
    "Management Review Signals",
    "Translate the executive metrics into clear areas for further investigation.",
)

review_rows: list[dict[str, str]] = []

if average_los is not None:
    review_rows.append(
        {
            "Area": "Operations",
            "Indicator": "Average Length of Stay",
            "Current Value": (
                f"{safe_float(average_los):,.2f} days"
            ),
            "Next Analysis": (
                "Review department and patient utilization patterns."
            ),
        }
    )

if readmission_rate is not None:
    review_rows.append(
        {
            "Area": "Patient Flow",
            "Indicator": "Readmission Rate",
            "Current Value": format_percentage(
                readmission_rate
            ),
            "Next Analysis": (
                "Review patient, department and doctor-level "
                "readmission patterns."
            ),
        }
    )

if outstanding_amount is not None:
    review_rows.append(
        {
            "Area": "Finance",
            "Indicator": "Outstanding Amount",
            "Current Value": format_currency_compact(
                outstanding_amount
            ),
            "Next Analysis": (
                "Review payment status and financial-risk concentration."
            ),
        }
    )

if collection_efficiency is not None:
    review_rows.append(
        {
            "Area": "Finance",
            "Indicator": "Collection Efficiency",
            "Current Value": format_percentage(
                collection_efficiency
            ),
            "Next Analysis": (
                "Review collections, payment methods and "
                "outstanding exposure."
            ),
        }
    )

if claim_rejection_rate is not None:
    review_rows.append(
        {
            "Area": "Claims",
            "Indicator": "Claim Rejection Rate",
            "Current Value": format_percentage(
                claim_rejection_rate
            ),
            "Next Analysis": (
                "Review insurer performance and rejection reasons."
            ),
        }
    )

if review_rows:
    dataframe(
        pd.DataFrame(
            review_rows
        ),
        height=300,
    )

    explanation_box(
        "How to use these signals",
        (
            "These are management review prompts based on the current "
            "hospital indicators. They direct the user toward deeper "
            "analysis and should not be interpreted as automated decisions."
        ),
    )
else:
    st.info(
        "No management review indicators are currently available."
    )


page_section(
    "09",
    "Continue the Analysis",
    "Use the dedicated dashboards to move from the hospital overview into detailed analysis.",
)

drill1, drill2, drill3, drill4 = st.columns(4)

with drill1:
    card_heading(
        "Patient Analytics",
        (
            "Understand patient demographics, admission behavior, "
            "utilization and patient-level patterns."
        ),
    )

    st.page_link(
        "pages/02_Patient_Analytics_Dashboard.py",
        label="Open Patient Analytics",
        icon="👥",
        width="stretch",
    )

with drill2:
    card_heading(
        "Operations Analytics",
        (
            "Investigate admissions, length of stay, emergency, ICU "
            "and department workload."
        ),
    )

    st.page_link(
        "pages/03_Operations_Analytics_Dashboard.py",
        label="Open Operations Analytics",
        icon="🏥",
        width="stretch",
    )

with drill3:
    card_heading(
        "Finance Analytics",
        (
            "Review revenue, collections, outstanding balances "
            "and hospital financial performance."
        ),
    )

    st.page_link(
        "pages/04_Finance_Analytics_Dashboard.py",
        label="Open Finance Analytics",
        icon="💰",
        width="stretch",
    )

with drill4:
    card_heading(
        "Risk Analytics",
        (
            "Explore patient, admission, financial and claims "
            "risk indicators."
        ),
    )

    st.page_link(
        "pages/05_Risk_Analytics_Dashboard.py",
        label="Open Risk Analytics",
        icon="⚠️",
        width="stretch",
    )


with st.expander(
    "Technical Data Diagnostics",
    expanded=False,
):
    st.caption(
        "Development reference showing the analytics views "
        "used by this page."
    )

    diagnostic_rows = []

    for view_name, frame in [
        (
            "vw_executive_kpis",
            executive,
        ),
        (
            "vw_monthly_hospital_performance",
            monthly,
        ),
        (
            "vw_department_performance",
            departments,
        ),
        (
            "vw_claim_performance",
            claims,
        ),
        (
            "vw_daily_operations",
            daily,
        ),
    ]:
        diagnostic_rows.append(
            {
                "Analytics View": view_name,
                "Rows": len(frame),
                "Available Fields": ", ".join(
                    frame.columns.tolist()
                ),
            }
        )

    dataframe(
        pd.DataFrame(
            diagnostic_rows
        ),
        height=300,
    )


st.divider()

footer_left, footer_right = st.columns(
    [4, 1]
)

with footer_left:
    st.caption(
        "Executive Command Center · Hospital 360 synthetic analytics "
        "environment · This page is designed for visualization and "
        "management interpretation. Report generation and centralized "
        "downloads are managed from the Admin Control Center."
    )

with footer_right:
    render_refresh_button(
        key="executive_refresh",
    )