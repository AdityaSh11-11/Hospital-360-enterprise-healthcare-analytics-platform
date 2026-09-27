from __future__ import annotations

import pandas as pd
import plotly.express as px
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
    title="MIS Reports",
    subtitle=(
        "Management Information System for understanding Hospital 360 "
        "performance across patients, operations, finance, departments, "
        "claims, payers and physicians."
    ),
    icon="📑",
)


def safe_number(value, default=0.0):
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value):
    return int(round(safe_number(value)))


def pct(numerator, denominator):
    denominator = safe_number(denominator)

    if denominator == 0:
        return 0.0

    return (
        safe_number(numerator)
        / denominator
        * 100
    )


def first_existing(
    frame: pd.DataFrame,
    candidates: list[str],
):
    for column in candidates:
        if column in frame.columns:
            return column

    return None


def scalar_from(
    frame: pd.DataFrame,
    candidates: list[str],
    default=0,
):
    if frame.empty:
        return default

    column = first_existing(
        frame,
        candidates,
    )

    if column is None:
        return default

    return frame.iloc[0][column]


def style_figure(
    fig,
    height=400,
):
    fig.update_layout(
        height=height,
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20,
        ),
        legend_title_text="",
        hoverlabel=dict(
            font_size=13,
        ),
    )

    return fig


@st.cache_data(
    ttl=60,
    show_spinner=False,
)
def load_executive_kpis():
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
def load_monthly_performance():
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
def load_department_performance():
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
def load_claim_performance():
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
def load_doctor_performance():
    return read_sql(
        """
        SELECT *
        FROM analytics.vw_doctor_performance
        """
    )


@st.cache_data(
    ttl=60,
    show_spinner=False,
)
def load_finance_summary():
    return read_sql(
        """
        SELECT *
        FROM analytics.vw_finance_summary
        """
    )


@st.cache_data(
    ttl=60,
    show_spinner=False,
)
def load_monthly_finance():
    return read_sql(
        """
        SELECT *
        FROM analytics.vw_monthly_finance
        """
    )


load_errors = {}


def safe_load(
    name,
    loader,
):
    try:
        return loader()

    except Exception as exc:
        load_errors[name] = str(exc)
        return pd.DataFrame()


executive = safe_load(
    "Executive KPIs",
    load_executive_kpis,
)

monthly = safe_load(
    "Monthly Hospital Performance",
    load_monthly_performance,
)

departments = safe_load(
    "Department Performance",
    load_department_performance,
)

claims = safe_load(
    "Claim Performance",
    load_claim_performance,
)

doctors = safe_load(
    "Doctor Performance",
    load_doctor_performance,
)

finance = safe_load(
    "Finance Summary",
    load_finance_summary,
)

monthly_finance = safe_load(
    "Monthly Finance",
    load_monthly_finance,
)


section_header(
    "1. MIS Reporting Overview",
    (
        "Start here to understand what this management-reporting workspace "
        "contains and how it fits into the Hospital 360 application."
    ),
)

st.info(
    "This page is the management reporting and interpretation workspace. "
    "It displays governed MIS information but does not generate or download "
    "project files. Report generation, exports, Power BI assets and other "
    "downloadable deliverables are centralized in the Admin Control Center."
)

available_datasets = sum(
    [
        not executive.empty,
        not monthly.empty,
        not departments.empty,
        not claims.empty,
        not doctors.empty,
        not finance.empty,
        not monthly_finance.empty,
    ]
)

metric_row(
    [
        (
            "Reporting Sources",
            f"{available_datasets}/7",
        ),
        (
            "Reporting Domains",
            "6",
        ),
        (
            "MIS Mode",
            "Read Only",
        ),
        (
            "Export Control",
            "Admin Center",
        ),
    ]
)

management_insight(
    (
        "Hospital 360 MIS brings together enterprise KPIs, monthly trends, "
        "department activity, finance, claims, payer and physician reporting "
        "into one management-oriented sequence. Each section should be read "
        "as a descriptive analytical view of the synthetic hospital."
    ),
    label="How to Read This Page",
)

if load_errors:
    with st.expander(
        "Reporting source diagnostics",
        expanded=False,
    ):
        diagnostics = pd.DataFrame(
            [
                {
                    "Reporting Source": key,
                    "Status": "Unavailable",
                    "Details": value,
                }
                for key, value
                in load_errors.items()
            ]
        )

        dataframe(
            diagnostics,
            height=280,
        )


section_header(
    "2. Executive Management Scorecard",
    (
        "Review the hospital's headline operational, financial and "
        "claims indicators before moving into detailed reporting."
    ),
)

if not executive.empty:
    total_patients = safe_int(
        scalar_from(
            executive,
            [
                "total_patients",
                "patient_count",
            ],
        )
    )

    admissions = safe_int(
        scalar_from(
            executive,
            [
                "total_admissions",
                "admissions",
                "admission_count",
            ],
        )
    )

    admitted_patients = safe_int(
        scalar_from(
            executive,
            [
                "admitted_patients",
                "unique_admitted_patients",
            ],
        )
    )

    average_los = safe_number(
        scalar_from(
            executive,
            [
                "average_length_of_stay",
                "avg_length_of_stay",
                "average_los",
                "avg_los",
            ],
        )
    )

    readmissions = safe_int(
        scalar_from(
            executive,
            [
                "readmissions",
                "total_readmissions",
            ],
        )
    )

    readmission_rate = safe_number(
        scalar_from(
            executive,
            [
                "readmission_rate",
                "readmission_rate_pct",
            ],
        )
    )

    net_revenue = safe_number(
        scalar_from(
            executive,
            [
                "net_revenue",
                "total_net_revenue",
                "net_amount",
            ],
        )
    )

    collected = safe_number(
        scalar_from(
            executive,
            [
                "collected_amount",
                "paid_amount",
                "total_paid",
            ],
        )
    )

    outstanding = safe_number(
        scalar_from(
            executive,
            [
                "outstanding_amount",
                "total_outstanding",
            ],
        )
    )

    collection_efficiency = safe_number(
        scalar_from(
            executive,
            [
                "collection_efficiency",
                "collection_efficiency_pct",
            ],
        )
    )

    total_claims = safe_int(
        scalar_from(
            executive,
            [
                "total_claims",
                "claims",
                "claim_count",
            ],
        )
    )

    rejected_claims = safe_int(
        scalar_from(
            executive,
            [
                "rejected_claims",
                "rejected_claim_count",
            ],
        )
    )

    rejection_rate = safe_number(
        scalar_from(
            executive,
            [
                "claim_rejection_rate_pct",
                "claim_rejection_rate",
                "rejection_rate",
                "rejection_rate_pct",
            ],
        )
    )

    metric_row(
        [
            (
                "Total Patients",
                format_integer(
                    total_patients
                ),
            ),
            (
                "Admissions",
                format_integer(
                    admissions
                ),
            ),
            (
                "Admitted Patients",
                format_integer(
                    admitted_patients
                ),
            ),
            (
                "Average Length of Stay",
                f"{average_los:.2f} days",
            ),
        ]
    )

    metric_row(
        [
            (
                "Readmissions",
                format_integer(
                    readmissions
                ),
            ),
            (
                "Readmission Rate",
                format_percentage(
                    readmission_rate
                ),
            ),
            (
                "Net Revenue",
                format_currency_compact(
                    net_revenue
                ),
            ),
            (
                "Recorded Paid",
                format_currency_compact(
                    collected
                ),
            ),
        ]
    )

    metric_row(
        [
            (
                "Recorded Outstanding",
                format_currency_compact(
                    outstanding
                ),
            ),
            (
                "Collection Efficiency",
                format_percentage(
                    collection_efficiency
                ),
            ),
            (
                "Total Claims",
                format_integer(
                    total_claims
                ),
            ),
            (
                "Claim Rejection Rate",
                format_percentage(
                    rejection_rate
                ),
            ),
        ]
    )

    management_insight(
        (
            f"The current MIS scorecard reports "
            f"{format_integer(admissions)} admissions across "
            f"{format_integer(total_patients)} registered patients. "
            f"Net revenue is {format_currency_compact(net_revenue)}, "
            f"with {format_currency_compact(collected)} recorded as paid "
            f"and {format_currency_compact(outstanding)} recorded as "
            f"outstanding. The observed readmission rate is "
            f"{format_percentage(readmission_rate)}, while the observed "
            f"claim rejection rate is "
            f"{format_percentage(rejection_rate)}."
        ),
        label="Executive Interpretation",
    )

else:
    st.warning(
        "Executive KPI reporting is currently unavailable."
    )


section_header(
    "3. Monthly Hospital Performance",
    (
        "Follow hospital performance over time to understand changes in "
        "activity and financial reporting."
    ),
)

if not monthly.empty:
    monthly_work = monthly.copy()

    date_column = first_existing(
        monthly_work,
        [
            "month_start",
            "month_date",
            "report_month",
            "month",
            "period_start",
            "full_date",
        ],
    )

    admission_column = first_existing(
        monthly_work,
        [
            "total_admissions",
            "admissions",
            "admission_count",
        ],
    )

    revenue_column = first_existing(
        monthly_work,
        [
            "net_revenue",
            "total_net_revenue",
            "net_amount",
            "revenue",
        ],
    )

    outstanding_column = first_existing(
        monthly_work,
        [
            "outstanding_amount",
            "total_outstanding",
            "outstanding",
        ],
    )

    if date_column:
        monthly_work[
            date_column
        ] = pd.to_datetime(
            monthly_work[
                date_column
            ],
            errors="coerce",
        )

        monthly_work = (
            monthly_work
            .sort_values(
                date_column
            )
        )

    left, right = st.columns(2)

    with left:
        st.markdown(
            "#### Monthly Admission Activity"
        )

        if (
            date_column
            and admission_column
        ):
            monthly_work[
                admission_column
            ] = pd.to_numeric(
                monthly_work[
                    admission_column
                ],
                errors="coerce",
            ).fillna(0)

            fig = px.line(
                monthly_work,
                x=date_column,
                y=admission_column,
                markers=True,
                title="Admissions by Reporting Month",
            )

            fig.update_xaxes(
                title=None
            )

            fig.update_yaxes(
                title="Admissions"
            )

            st.plotly_chart(
                style_figure(
                    fig,
                    390,
                ),
                width="stretch",
            )

            st.caption(
                "This chart shows how recorded hospital admission activity "
                "changes across reporting months."
            )

        else:
            st.info(
                "Monthly admission fields are not available in the current "
                "semantic dataset."
            )

    with right:
        st.markdown(
            "#### Monthly Revenue Activity"
        )

        if (
            date_column
            and revenue_column
        ):
            monthly_work[
                revenue_column
            ] = pd.to_numeric(
                monthly_work[
                    revenue_column
                ],
                errors="coerce",
            ).fillna(0)

            fig = px.line(
                monthly_work,
                x=date_column,
                y=revenue_column,
                markers=True,
                title="Net Revenue by Reporting Month",
            )

            fig.update_xaxes(
                title=None
            )

            fig.update_yaxes(
                title="Net Revenue"
            )

            st.plotly_chart(
                style_figure(
                    fig,
                    390,
                ),
                width="stretch",
            )

            st.caption(
                "This chart shows recorded net billing revenue across "
                "reporting months."
            )

        else:
            st.info(
                "Monthly revenue fields are not available in the current "
                "semantic dataset."
            )

    if (
        date_column
        and outstanding_column
    ):
        st.markdown(
            "#### Monthly Outstanding Exposure"
        )

        monthly_work[
            outstanding_column
        ] = pd.to_numeric(
            monthly_work[
                outstanding_column
            ],
            errors="coerce",
        ).fillna(0)

        fig = px.area(
            monthly_work,
            x=date_column,
            y=outstanding_column,
            title="Recorded Outstanding by Reporting Month",
        )

        fig.update_xaxes(
            title=None
        )

        fig.update_yaxes(
            title="Outstanding"
        )

        st.plotly_chart(
            style_figure(
                fig,
                380,
            ),
            width="stretch",
        )

        st.caption(
            "Outstanding represents the recorded outstanding amount in "
            "Hospital 360 billing data. It is not formal accounts-receivable "
            "aging."
        )

    with st.expander(
        "View monthly management data",
        expanded=False,
    ):
        dataframe(
            monthly_work,
            height=430,
        )

else:
    st.info(
        "Monthly hospital performance data is unavailable."
    )


section_header(
    "4. Department Management Report",
    (
        "Compare hospital departments across workload and available "
        "financial measures."
    ),
)

if not departments.empty:
    department_work = departments.copy()

    department_column = first_existing(
        department_work,
        [
            "department_name",
            "department",
        ],
    )

    admission_column = first_existing(
        department_work,
        [
            "total_admissions",
            "admissions",
            "admission_count",
        ],
    )

    revenue_column = first_existing(
        department_work,
        [
            "net_revenue",
            "net_amount",
            "total_net_revenue",
            "revenue",
        ],
    )

    outstanding_column = first_existing(
        department_work,
        [
            "outstanding_amount",
            "total_outstanding",
            "outstanding",
        ],
    )

    left, right = st.columns(2)

    with left:
        st.markdown(
            "#### Department Workload"
        )

        if (
            department_column
            and admission_column
        ):
            department_work[
                admission_column
            ] = pd.to_numeric(
                department_work[
                    admission_column
                ],
                errors="coerce",
            ).fillna(0)

            chart = (
                department_work
                .sort_values(
                    admission_column,
                    ascending=True,
                )
            )

            fig = px.bar(
                chart,
                x=admission_column,
                y=department_column,
                orientation="h",
                title="Admissions by Department",
                text_auto=True,
            )

            fig.update_yaxes(
                title=None
            )

            st.plotly_chart(
                style_figure(
                    fig,
                    450,
                ),
                width="stretch",
            )

            st.caption(
                "Higher values indicate departments handling a larger "
                "recorded admission workload."
            )

        else:
            st.info(
                "Department workload fields are unavailable."
            )

    with right:
        st.markdown(
            "#### Department Financial Exposure"
        )

        if (
            department_column
            and outstanding_column
        ):
            department_work[
                outstanding_column
            ] = pd.to_numeric(
                department_work[
                    outstanding_column
                ],
                errors="coerce",
            ).fillna(0)

            chart = (
                department_work
                .sort_values(
                    outstanding_column,
                    ascending=True,
                )
            )

            fig = px.bar(
                chart,
                x=outstanding_column,
                y=department_column,
                orientation="h",
                title="Recorded Outstanding by Department",
                text_auto=True,
            )

            fig.update_yaxes(
                title=None
            )

            st.plotly_chart(
                style_figure(
                    fig,
                    450,
                ),
                width="stretch",
            )

            st.caption(
                "This chart compares recorded outstanding billing exposure "
                "across departments."
            )

        elif (
            department_column
            and revenue_column
        ):
            department_work[
                revenue_column
            ] = pd.to_numeric(
                department_work[
                    revenue_column
                ],
                errors="coerce",
            ).fillna(0)

            chart = (
                department_work
                .sort_values(
                    revenue_column,
                    ascending=True,
                )
            )

            fig = px.bar(
                chart,
                x=revenue_column,
                y=department_column,
                orientation="h",
                title="Net Revenue by Department",
                text_auto=True,
            )

            fig.update_yaxes(
                title=None
            )

            st.plotly_chart(
                style_figure(
                    fig,
                    450,
                ),
                width="stretch",
            )

            st.caption(
                "Department revenue represents billing attributed through "
                "Hospital 360 analytical logic."
            )

        else:
            st.info(
                "Department financial fields are unavailable."
            )

    with st.expander(
        "View department management table",
        expanded=False,
    ):
        dataframe(
            department_work,
            height=480,
        )

else:
    st.info(
        "Department MIS data is unavailable."
    )


section_header(
    "5. Finance and Revenue Cycle Report",
    (
        "Review the hospital's recorded financial position using governed "
        "billing, payment and outstanding-balance semantics."
    ),
)

if not finance.empty:
    finance_net = safe_number(
        scalar_from(
            finance,
            [
                "net_revenue",
                "total_net_revenue",
                "net_amount",
            ],
        )
    )

    finance_paid = safe_number(
        scalar_from(
            finance,
            [
                "paid_amount",
                "collected_amount",
                "total_paid",
            ],
        )
    )

    finance_outstanding = safe_number(
        scalar_from(
            finance,
            [
                "outstanding_amount",
                "total_outstanding",
            ],
        )
    )

    finance_efficiency = safe_number(
        scalar_from(
            finance,
            [
                "collection_efficiency",
                "collection_efficiency_pct",
            ],
        )
    )

    metric_row(
        [
            (
                "Net Revenue",
                format_currency_compact(
                    finance_net
                ),
            ),
            (
                "Recorded Paid",
                format_currency_compact(
                    finance_paid
                ),
            ),
            (
                "Recorded Outstanding",
                format_currency_compact(
                    finance_outstanding
                ),
            ),
            (
                "Collection Efficiency",
                format_percentage(
                    finance_efficiency
                ),
            ),
        ]
    )

    management_insight(
        (
            f"Hospital 360 currently records "
            f"{format_currency_compact(finance_net)} in net revenue, "
            f"{format_currency_compact(finance_paid)} as paid and "
            f"{format_currency_compact(finance_outstanding)} as "
            f"outstanding. Collection efficiency is interpreted using the "
            f"project's recorded paid-to-net-billing definition."
        ),
        label="Revenue Cycle Interpretation",
    )

else:
    st.info(
        "Finance summary data is unavailable."
    )


if not monthly_finance.empty:
    finance_work = monthly_finance.copy()

    finance_date = first_existing(
        finance_work,
        [
            "month_start",
            "month_date",
            "billing_month",
            "report_month",
            "month",
            "period_start",
        ],
    )

    finance_revenue = first_existing(
        finance_work,
        [
            "net_revenue",
            "total_net_revenue",
            "net_amount",
            "revenue",
        ],
    )

    finance_paid_column = first_existing(
        finance_work,
        [
            "paid_amount",
            "collected_amount",
            "total_paid",
        ],
    )

    finance_outstanding_column = first_existing(
        finance_work,
        [
            "outstanding_amount",
            "total_outstanding",
            "outstanding",
        ],
    )

    if finance_date:
        finance_work[
            finance_date
        ] = pd.to_datetime(
            finance_work[
                finance_date
            ],
            errors="coerce",
        )

        finance_work = finance_work.sort_values(
            finance_date
        )

    st.markdown(
        "#### Monthly Revenue Cycle Movement"
    )

    if (
        finance_date
        and finance_revenue
    ):
        finance_work[
            finance_revenue
        ] = pd.to_numeric(
            finance_work[
                finance_revenue
            ],
            errors="coerce",
        ).fillna(0)

        y_columns = [
            finance_revenue
        ]

        if finance_paid_column:
            finance_work[
                finance_paid_column
            ] = pd.to_numeric(
                finance_work[
                    finance_paid_column
                ],
                errors="coerce",
            ).fillna(0)

            y_columns.append(
                finance_paid_column
            )

        if finance_outstanding_column:
            finance_work[
                finance_outstanding_column
            ] = pd.to_numeric(
                finance_work[
                    finance_outstanding_column
                ],
                errors="coerce",
            ).fillna(0)

            y_columns.append(
                finance_outstanding_column
            )

        fig = px.line(
            finance_work,
            x=finance_date,
            y=y_columns,
            markers=True,
            title="Monthly Financial Movement",
        )

        fig.update_xaxes(
            title=None
        )

        fig.update_yaxes(
            title="Amount"
        )

        st.plotly_chart(
            style_figure(
                fig,
                430,
            ),
            width="stretch",
        )

        st.caption(
            "Monthly finance follows billing and reporting-date semantics. "
            "Financial activity in a month does not necessarily correspond "
            "to admissions occurring in the same month."
        )

    with st.expander(
        "View monthly finance data",
        expanded=False,
    ):
        dataframe(
            finance_work,
            height=420,
        )


section_header(
    "6. Claims and Payer Report",
    (
        "Review insurer-level claim activity, rejection volume and "
        "rejected-value exposure."
    ),
)

if not claims.empty:
    claim_work = claims.copy()

    insurer_column = first_existing(
        claim_work,
        [
            "insurer_name",
            "insurer",
            "payer_name",
        ],
    )

    claims_column = first_existing(
        claim_work,
        [
            "total_claims",
            "claims",
            "claim_count",
        ],
    )

    rejected_column = first_existing(
        claim_work,
        [
            "rejected_claims",
            "rejected_count",
        ],
    )

    rejected_amount_column = first_existing(
        claim_work,
        [
            "rejected_amount",
            "total_rejected_amount",
            "rejected_value",
        ],
    )

    rejection_rate_column = first_existing(
        claim_work,
        [
            "rejection_rate",
            "rejection_rate_pct",
            "claim_rejection_rate",
        ],
    )

    left, right = st.columns(2)

    with left:
        st.markdown(
            "#### Claim Volume by Payer"
        )

        if (
            insurer_column
            and claims_column
        ):
            claim_work[
                claims_column
            ] = pd.to_numeric(
                claim_work[
                    claims_column
                ],
                errors="coerce",
            ).fillna(0)

            chart = (
                claim_work
                .sort_values(
                    claims_column,
                    ascending=True,
                )
            )

            fig = px.bar(
                chart,
                x=claims_column,
                y=insurer_column,
                orientation="h",
                title="Claims by Insurer",
                text_auto=True,
            )

            fig.update_yaxes(
                title=None
            )

            st.plotly_chart(
                style_figure(
                    fig,
                    410,
                ),
                width="stretch",
            )

            st.caption(
                "This chart compares recorded insurance claim volume across "
                "payers."
            )

        else:
            st.info(
                "Claim-volume fields are unavailable."
            )

    with right:
        st.markdown(
            "#### Claim Rejection Exposure"
        )

        if (
            insurer_column
            and rejected_amount_column
        ):
            claim_work[
                rejected_amount_column
            ] = pd.to_numeric(
                claim_work[
                    rejected_amount_column
                ],
                errors="coerce",
            ).fillna(0)

            chart = (
                claim_work
                .sort_values(
                    rejected_amount_column,
                    ascending=True,
                )
            )

            fig = px.bar(
                chart,
                x=rejected_amount_column,
                y=insurer_column,
                orientation="h",
                title="Rejected Claim Value by Insurer",
                text_auto=True,
            )

            fig.update_yaxes(
                title=None
            )

            st.plotly_chart(
                style_figure(
                    fig,
                    410,
                ),
                width="stretch",
            )

            st.caption(
                "This chart compares the recorded value associated with "
                "rejected claims across insurers."
            )

        elif (
            insurer_column
            and rejected_column
        ):
            claim_work[
                rejected_column
            ] = pd.to_numeric(
                claim_work[
                    rejected_column
                ],
                errors="coerce",
            ).fillna(0)

            chart = (
                claim_work
                .sort_values(
                    rejected_column,
                    ascending=True,
                )
            )

            fig = px.bar(
                chart,
                x=rejected_column,
                y=insurer_column,
                orientation="h",
                title="Rejected Claims by Insurer",
                text_auto=True,
            )

            fig.update_yaxes(
                title=None
            )

            st.plotly_chart(
                style_figure(
                    fig,
                    410,
                ),
                width="stretch",
            )

        else:
            st.info(
                "Claim-rejection fields are unavailable."
            )

    if (
        insurer_column
        and rejection_rate_column
    ):
        claim_work[
            rejection_rate_column
        ] = pd.to_numeric(
            claim_work[
                rejection_rate_column
            ],
            errors="coerce",
        ).fillna(0)

        rejection_table = (
            claim_work[
                [
                    insurer_column,
                    rejection_rate_column,
                ]
            ]
            .sort_values(
                rejection_rate_column,
                ascending=False,
            )
        )

        st.markdown(
            "#### Payer Rejection Rate Review"
        )

        dataframe(
            rejection_table,
            height=300,
        )

    with st.expander(
        "View complete claims management table",
        expanded=False,
    ):
        dataframe(
            claim_work,
            height=450,
        )

else:
    st.info(
        "Claims and payer MIS data is unavailable."
    )


section_header(
    "7. Physician Management Report",
    (
        "Review physician workload and available descriptive performance "
        "measures without treating them as clinical-quality rankings."
    ),
)

if not doctors.empty:
    doctor_work = doctors.copy()

    doctor_column = first_existing(
        doctor_work,
        [
            "doctor_name",
            "doctor",
        ],
    )

    specialization_column = first_existing(
        doctor_work,
        [
            "specialization",
            "specialty",
        ],
    )

    admission_column = first_existing(
        doctor_work,
        [
            "total_admissions",
            "admissions",
            "admission_count",
        ],
    )

    readmission_column = first_existing(
        doctor_work,
        [
            "readmission_rate",
            "readmission_rate_pct",
        ],
    )

    revenue_column = first_existing(
        doctor_work,
        [
            "net_revenue",
            "net_amount",
            "attributed_net_revenue",
        ],
    )

    if (
        doctor_column
        and admission_column
    ):
        doctor_work[
            admission_column
        ] = pd.to_numeric(
            doctor_work[
                admission_column
            ],
            errors="coerce",
        ).fillna(0)

        chart = (
            doctor_work
            .sort_values(
                admission_column,
                ascending=False,
            )
            .head(20)
            .sort_values(
                admission_column,
                ascending=True,
            )
        )

        hover_columns = []

        if specialization_column:
            hover_columns.append(
                specialization_column
            )

        fig = px.bar(
            chart,
            x=admission_column,
            y=doctor_column,
            orientation="h",
            title="Higher-Volume Physicians",
            hover_data=hover_columns,
            text_auto=True,
        )

        fig.update_yaxes(
            title=None
        )

        st.plotly_chart(
            style_figure(
                fig,
                520,
            ),
            width="stretch",
        )

        st.caption(
            "This chart ranks physicians by recorded admission workload. "
            "It is a workload view, not a clinical-quality ranking."
        )

    doctor_columns = []

    for column in [
        doctor_column,
        specialization_column,
        admission_column,
        readmission_column,
        revenue_column,
    ]:
        if (
            column
            and column not in doctor_columns
        ):
            doctor_columns.append(
                column
            )

    st.markdown(
        "#### Physician Management Table"
    )

    if doctor_columns:
        doctor_table = doctor_work[
            doctor_columns
        ].copy()

        if admission_column:
            doctor_table = (
                doctor_table
                .sort_values(
                    admission_column,
                    ascending=False,
                )
            )

        dataframe(
            doctor_table,
            height=470,
        )

    else:
        dataframe(
            doctor_work,
            height=470,
        )

    st.info(
        "Physician metrics in Hospital 360 are descriptive management "
        "analytics. They are not risk-adjusted clinical-quality rankings "
        "and should not be interpreted as physician performance judgments."
    )

else:
    st.info(
        "Doctor MIS data is unavailable."
    )


section_header(
    "8. Management Exception Monitor",
    (
        "Bring important operational and financial signals together so "
        "management can identify areas that may deserve further review."
    ),
)

exceptions = []

# Executive KPI values are only populated when the source is available.
# Initialize exception-monitor inputs so the unavailable-data path is safe.
outstanding = 0.0
rejection_rate = 0.0
readmission_rate = 0.0

if not executive.empty:
    if outstanding > 0:
        exceptions.append(
            {
                "Area": "Finance",
                "Management Signal":
                    "Recorded Outstanding Balance",
                "Current Value":
                    format_currency_compact(
                        outstanding
                    ),
                "Interpretation": (
                    "Outstanding billing balances exist and can be reviewed "
                    "through the Finance dashboard."
                ),
            }
        )

    if rejection_rate > 0:
        exceptions.append(
            {
                "Area": "Claims",
                "Management Signal":
                    "Claim Rejections Present",
                "Current Value":
                    format_percentage(
                        rejection_rate
                    ),
                "Interpretation": (
                    "Rejected claims are present in the synthetic claims "
                    "population and can be reviewed through Claims analytics."
                ),
            }
        )

    if readmission_rate > 0:
        exceptions.append(
            {
                "Area": "Operations",
                "Management Signal":
                    "Readmissions Present",
                "Current Value":
                    format_percentage(
                        readmission_rate
                    ),
                "Interpretation": (
                    "Observed readmissions are present. The metric is "
                    "descriptive and is not risk adjusted."
                ),
            }
        )

if not departments.empty:
    dep_col = first_existing(
        departments,
        [
            "department_name",
            "department",
        ],
    )

    dep_outstanding = first_existing(
        departments,
        [
            "outstanding_amount",
            "total_outstanding",
            "outstanding",
        ],
    )

    if (
        dep_col
        and dep_outstanding
    ):
        temp = departments.copy()

        temp[
            dep_outstanding
        ] = pd.to_numeric(
            temp[
                dep_outstanding
            ],
            errors="coerce",
        ).fillna(0)

        if not temp.empty:
            row = temp.sort_values(
                dep_outstanding,
                ascending=False,
            ).iloc[0]

            exceptions.append(
                {
                    "Area":
                        "Department Finance",
                    "Management Signal":
                        "Largest Department Outstanding",
                    "Current Value": (
                        f"{row[dep_col]} · "
                        f"{format_currency_compact(row[dep_outstanding])}"
                    ),
                    "Interpretation": (
                        "This department has the largest recorded "
                        "outstanding balance in the department semantic view."
                    ),
                }
            )

if not claims.empty:
    payer_col = first_existing(
        claims,
        [
            "insurer_name",
            "insurer",
            "payer_name",
        ],
    )

    rejected_value_col = first_existing(
        claims,
        [
            "rejected_amount",
            "total_rejected_amount",
            "rejected_value",
        ],
    )

    if (
        payer_col
        and rejected_value_col
    ):
        temp = claims.copy()

        temp[
            rejected_value_col
        ] = pd.to_numeric(
            temp[
                rejected_value_col
            ],
            errors="coerce",
        ).fillna(0)

        if not temp.empty:
            row = temp.sort_values(
                rejected_value_col,
                ascending=False,
            ).iloc[0]

            exceptions.append(
                {
                    "Area":
                        "Payer",
                    "Management Signal":
                        "Largest Rejected Claim Value",
                    "Current Value": (
                        f"{row[payer_col]} · "
                        f"{format_currency_compact(row[rejected_value_col])}"
                    ),
                    "Interpretation": (
                        "This payer has the largest recorded rejected claim "
                        "value in the payer-level semantic dataset."
                    ),
                }
            )

if exceptions:
    dataframe(
        pd.DataFrame(
            exceptions
        ),
        height=380,
    )

    st.caption(
        "Management exceptions are deterministic analytical observations. "
        "They are not automated decisions or clinical alerts."
    )

else:
    st.info(
        "No management exception signals could be derived from the "
        "currently available MIS datasets."
    )


section_header(
    "9. MIS Report Catalogue",
    (
        "Understand the sections represented by the Hospital 360 MIS "
        "reporting framework and the management purpose of each section."
    ),
)

report_structure = pd.DataFrame(
    [
        {
            "MIS Section":
                "Executive Scorecard",
            "Management Purpose": (
                "Provides a concise enterprise KPI snapshot for hospital "
                "leadership."
            ),
            "Primary Domain":
                "Enterprise",
        },
        {
            "MIS Section":
                "Monthly Performance",
            "Management Purpose": (
                "Shows month-by-month operational and financial movement."
            ),
            "Primary Domain":
                "Operations",
        },
        {
            "MIS Section":
                "Department Performance",
            "Management Purpose": (
                "Compares service-line workload and available financial "
                "measures."
            ),
            "Primary Domain":
                "Departments",
        },
        {
            "MIS Section":
                "Finance & Receivables",
            "Management Purpose": (
                "Summarizes billing, recorded payment and outstanding "
                "exposure."
            ),
            "Primary Domain":
                "Finance",
        },
        {
            "MIS Section":
                "Claims",
            "Management Purpose": (
                "Reviews claim volume, rejection activity and claim status."
            ),
            "Primary Domain":
                "Claims",
        },
        {
            "MIS Section":
                "Payer Performance",
            "Management Purpose": (
                "Compares insurer-level claim and rejection measures."
            ),
            "Primary Domain":
                "Claims",
        },
        {
            "MIS Section":
                "Doctor Performance",
            "Management Purpose": (
                "Reviews physician workload and descriptive attributed "
                "activity."
            ),
            "Primary Domain":
                "Physicians",
        },
        {
            "MIS Section":
                "Management Exceptions",
            "Management Purpose": (
                "Surfaces operational and financial observations requiring "
                "management review."
            ),
            "Primary Domain":
                "Cross Functional",
        },
        {
            "MIS Section":
                "Management Commentary",
            "Management Purpose": (
                "Explains important reporting signals in business language."
            ),
            "Primary Domain":
                "Management",
        },
        {
            "MIS Section":
                "Management Summary",
            "Management Purpose": (
                "Provides a consolidated management-level reporting output."
            ),
            "Primary Domain":
                "Enterprise",
        },
    ]
)

dataframe(
    report_structure,
    height=520,
)


section_header(
    "10. MIS Metric Definitions",
    (
        "Use these definitions to interpret Hospital 360 management "
        "measures correctly and avoid overstating what the data represents."
    ),
)

semantics = pd.DataFrame(
    [
        {
            "Metric":
                "Collection Efficiency",
            "What It Means": (
                "Recorded paid amount divided by net billing."
            ),
            "What It Does Not Mean": (
                "It is not period-matched cash collection."
            ),
        },
        {
            "Metric":
                "Outstanding",
            "What It Means": (
                "Recorded outstanding amount on billing records."
            ),
            "What It Does Not Mean": (
                "It is not formal accounts-receivable aging."
            ),
        },
        {
            "Metric":
                "Outstanding Exposure",
            "What It Means": (
                "Recorded unpaid billing exposure grouped or summarized "
                "analytically."
            ),
            "What It Does Not Mean": (
                "Monetary exposure bands are not aging buckets."
            ),
        },
        {
            "Metric":
                "Department Revenue",
            "What It Means": (
                "Billing attributed to departments through Hospital 360 "
                "analytical logic."
            ),
            "What It Does Not Mean": (
                "It is not department profitability."
            ),
        },
        {
            "Metric":
                "Doctor Financial Activity",
            "What It Means": (
                "Billing attributed through physician-linked admissions."
            ),
            "What It Does Not Mean": (
                "It is not physician compensation or contribution margin."
            ),
        },
        {
            "Metric":
                "Readmission Rate",
            "What It Means": (
                "Observed share of admissions flagged as readmissions."
            ),
            "What It Does Not Mean": (
                "It is not risk-adjusted clinical-quality benchmarking."
            ),
        },
        {
            "Metric":
                "Claim Rejection Rate",
            "What It Means": (
                "Observed rejected claims relative to the claims population."
            ),
            "What It Does Not Mean": (
                "It is descriptive synthetic claims analytics."
            ),
        },
        {
            "Metric":
                "Profit / Margin",
            "What It Means": (
                "Not reported as a genuine Hospital 360 enterprise KPI."
            ),
            "What It Does Not Mean": (
                "Profitability cannot be inferred without complete cost "
                "accounting and budget data."
            ),
        },
    ]
)

dataframe(
    semantics,
    height=500,
)


section_header(
    "11. Reporting Governance",
    (
        "Review the controls that keep Hospital 360 management reporting "
        "consistent, reproducible and appropriately interpreted."
    ),
)

governance = pd.DataFrame(
    [
        {
            "Governance Control":
                "Semantic KPI Layer",
            "Why It Matters": (
                "Management reporting uses governed analytical definitions "
                "where available."
            ),
        },
        {
            "Governance Control":
                "Read-Only MIS Workspace",
            "Why It Matters": (
                "This page focuses on management review rather than "
                "administrative file-generation actions."
            ),
        },
        {
            "Governance Control":
                "Centralized Admin Exports",
            "Why It Matters": (
                "Generated files, downloads, Power BI assets and managed "
                "exports remain in one administrative workspace."
            ),
        },
        {
            "Governance Control":
                "Financial Semantics",
            "Why It Matters": (
                "Revenue, payment, collection and outstanding measures retain "
                "their documented Hospital 360 definitions."
            ),
        },
        {
            "Governance Control":
                "No Fabricated Profitability",
            "Why It Matters": (
                "Profit and margin are not presented without complete cost "
                "accounting data."
            ),
        },
        {
            "Governance Control":
                "Descriptive Physician Analytics",
            "Why It Matters": (
                "Doctor measures are not presented as risk-adjusted "
                "clinical-quality rankings."
            ),
        },
        {
            "Governance Control":
                "Synthetic Healthcare Data",
            "Why It Matters": (
                "The portfolio project demonstrates healthcare analytics "
                "without representing real patient PHI."
            ),
        },
    ]
)

dataframe(
    governance,
    height=460,
)


section_header(
    "12. End-to-End MIS Reporting Flow",
    (
        "Follow how raw hospital activity becomes governed management "
        "information and finally reaches dashboards, reports and BI tools."
    ),
)

reporting_flow = pd.DataFrame(
    [
        {
            "Step":
                "1",
            "Stage":
                "Source & Warehouse",
            "What Happens": (
                "Synthetic patient, admission, billing, claim, laboratory "
                "and medication data is stored in governed warehouse tables."
            ),
        },
        {
            "Step":
                "2",
            "Stage":
                "Analytics Layer",
            "What Happens": (
                "Hospital, department, doctor, finance and claims semantic "
                "views create reusable analytical definitions."
            ),
        },
        {
            "Step":
                "3",
            "Stage":
                "Business Analysis",
            "What Happens": (
                "KPIs, trends, reconciliations and management exceptions "
                "are derived from the governed analytical layer."
            ),
        },
        {
            "Step":
                "4",
            "Stage":
                "MIS Reporting",
            "What Happens": (
                "This page organizes the analytical information into a "
                "management-readable reporting sequence."
            ),
        },
        {
            "Step":
                "5",
            "Stage":
                "Admin Control Center",
            "What Happens": (
                "Authorized generation, exports, report packages and "
                "downloadable project deliverables are centrally managed."
            ),
        },
        {
            "Step":
                "6",
            "Stage":
                "Power BI / External BI",
            "What Happens": (
                "Prepared analytical assets can be consumed by Power BI or "
                "other supported reporting tools."
            ),
        },
    ]
)

dataframe(
    reporting_flow,
    height=420,
)


section_header(
    "13. Continue the Hospital 360 Workflow",
    (
        "Choose the next workspace according to whether you need deeper "
        "analysis, detailed records or administrative deliverables."
    ),
)

next_left, next_middle, next_right = st.columns(3)

with next_left:
    st.markdown(
        "#### Need Detailed Analysis?"
    )

    st.write(
        "Open the dedicated Patient, Operations, Finance, Risk, Claims or "
        "Doctor dashboard for deeper domain-specific visual analysis."
    )

with next_middle:
    st.markdown(
        "#### Need Record-Level Exploration?"
    )

    st.write(
        "Use Data Explorer to inspect approved Hospital 360 datasets, "
        "columns, distributions, filters and individual records."
    )

with next_right:
    st.markdown(
        "#### Need Reports or Downloads?"
    )

    st.write(
        "Use the Admin Control Center for MIS generation, downloadable "
        "reports, analytical exports, Power BI assets and other managed "
        "project deliverables."
    )

management_insight(
    (
        "The MIS Reports page is the management interpretation layer of "
        "Hospital 360. Dedicated dashboards provide deeper domain analysis, "
        "Data Explorer provides governed record-level inspection, and the "
        "Admin Control Center owns generation and downloadable outputs."
    ),
    label="Where MIS Fits",
)


section_header(
    "Important Reporting Note",
    (
        "Hospital 360 reporting should always be interpreted within the "
        "analytical boundaries of the synthetic project."
    ),
)

st.warning(
    "Outstanding balances are not formal accounts-receivable aging, "
    "collection efficiency represents recorded paid amount divided by net "
    "billing, physician analytics are not risk-adjusted clinical-quality "
    "rankings, and profitability is not inferred because complete "
    "cost-accounting and budget data are not available."
)

st.info(
    "Hospital 360 is built using synthetic healthcare data for analytics, "
    "data engineering, BI and portfolio demonstration. MIS outputs are "
    "management analytics and are not clinical decision-support outputs."
)

st.divider()

footer_left, footer_right = st.columns(
    [4, 1]
)

with footer_left:
    st.caption(
        "MIS Reports · Hospital 360 Enterprise Intelligence Platform · "
        "Executive reporting · Operations · Finance · Claims · "
        "Departments · Physicians"
    )

with footer_right:
    render_refresh_button(
        key="mis_reports_refresh",
    )