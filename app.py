from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from analytics.data_loader import read_sql
from utils.app_helpers import (
    bootstrap_page,
    format_currency_compact,
    format_integer,
    format_percentage,
    load_latest_etl_status,
    load_system_health,
    load_warehouse_counts,
    management_insight,
    metric_row,
    safe_scalar,
    section_header,
    status_panel,
)


bootstrap_page(
    title="Hospital 360",
    subtitle=(
        "Enterprise Healthcare Analytics & Management "
        "Intelligence Platform"
    ),
    icon="🏥",
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
        LIMIT 1
        """
    )


@st.cache_data(
    ttl=60,
    show_spinner=False,
)
def load_department_performance() -> pd.DataFrame:
    return read_sql(
        """
        SELECT
            department_name,
            admissions,
            net_revenue
        FROM analytics.vw_department_performance
        ORDER BY admissions DESC
        LIMIT 5
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
        ORDER BY month_start
        """
    )


def resolve_value(
    frame: pd.DataFrame,
    columns: list[str],
    default: Any = None,
) -> Any:
    if frame is None or frame.empty:
        return default

    for column in columns:
        if column not in frame.columns:
            continue

        value = frame.iloc[0][column]

        try:
            if pd.isna(value):
                continue
        except (TypeError, ValueError):
            pass

        return value

    return default


try:
    executive = load_executive_kpis()
    warehouse_counts = load_warehouse_counts()
    system_health = load_system_health()
    latest_etl = load_latest_etl_status()
    departments = load_department_performance()
    monthly = load_monthly_performance()

except Exception as exc:
    st.error(
        "Hospital 360 could not load the application overview. "
        "Confirm that PostgreSQL and the analytics warehouse "
        "are available."
    )
    st.exception(exc)
    st.stop()


count_map = dict(
    zip(
        warehouse_counts["entity"],
        warehouse_counts["row_count"],
    )
)


patients = resolve_value(
    executive,
    [
        "total_patients",
        "patients",
    ],
    count_map.get("Patients", 0),
)

admissions = resolve_value(
    executive,
    [
        "total_admissions",
        "admissions",
    ],
    count_map.get("Admissions", 0),
)

net_revenue = resolve_value(
    executive,
    [
        "net_revenue",
        "total_net_revenue",
        "total_revenue",
    ],
    0,
)

collection_efficiency = resolve_value(
    executive,
    [
        "collection_efficiency_pct",
        "collection_efficiency",
        "collection_rate_pct",
    ],
)

outstanding_amount = resolve_value(
    executive,
    [
        "outstanding_amount",
        "total_outstanding",
        "outstanding_balance",
    ],
)

readmission_rate = resolve_value(
    executive,
    [
        "readmission_rate_pct",
        "readmission_rate",
    ],
)

claim_rejection_rate = resolve_value(
    executive,
    [
        "claim_rejection_rate_pct",
        "claim_rejection_rate",
        "rejection_rate_pct",
        "rejection_rate",
    ],
)

average_los = resolve_value(
    executive,
    [
        "average_length_of_stay",
        "avg_length_of_stay",
        "avg_los",
        "alos",
    ],
)


st.markdown(
    """
    ### Welcome to Hospital 360

    Hospital 360 brings hospital operations, patients, finance,
    claims, risk, doctors, management reporting, data engineering
    and AI-assisted analytics into one governed analytical platform.

    This Home page provides a simple starting point. Use the
    navigation menu to move from hospital-wide performance into
    each specialist analytical workspace.
    """
)


section_header(
    "01 · Hospital at a Glance",
    (
        "Start with the hospital's overall scale and the most "
        "important management indicators."
    ),
)


metric_row(
    [
        (
            "Patients",
            format_integer(patients),
        ),
        (
            "Admissions",
            format_integer(admissions),
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
                f"{float(average_los):,.2f} days"
                if average_los is not None
                else "—"
            ),
        ),
        (
            "Readmission Rate",
            format_percentage(readmission_rate),
        ),
        (
            "Claim Rejection Rate",
            format_percentage(claim_rejection_rate),
        ),
        (
            "Outstanding Amount",
            format_currency_compact(outstanding_amount),
        ),
    ]
)


insight_parts: list[str] = []

if collection_efficiency is not None:
    insight_parts.append(
        "Collection efficiency is "
        f"{format_percentage(collection_efficiency)}."
    )

if readmission_rate is not None:
    insight_parts.append(
        "Readmissions represent "
        f"{format_percentage(readmission_rate)} "
        "of recorded admissions."
    )

if outstanding_amount is not None:
    insight_parts.append(
        "Outstanding billing exposure is "
        f"{format_currency_compact(outstanding_amount)}."
    )

if claim_rejection_rate is not None:
    insight_parts.append(
        "Claim rejection rate is "
        f"{format_percentage(claim_rejection_rate)}."
    )


management_insight(
    " ".join(insight_parts),
    label="Management Snapshot",
)


section_header(
    "02 · Understand the Project Flow",
    (
        "Hospital 360 follows a clear sequence from synthetic "
        "source data to management intelligence."
    ),
)


flow1, flow2, flow3, flow4 = st.columns(4)


with flow1:
    st.markdown(
        """
        #### 1 · Data Generation

        Synthetic healthcare activity is generated for patients,
        admissions, billing, insurance claims, laboratory activity
        and medication events.
        """
    )


with flow2:
    st.markdown(
        """
        #### 2 · Data Engineering

        Incremental ETL validates incoming batches, applies data
        quality controls and loads the governed PostgreSQL
        dimensional warehouse.
        """
    )


with flow3:
    st.markdown(
        """
        #### 3 · Analytics

        SQL semantic views and Python analytical pipelines produce
        operational, financial, patient, claims, risk, statistical
        and management intelligence.
        """
    )


with flow4:
    st.markdown(
        """
        #### 4 · Decision Support

        Streamlit dashboards, MIS outputs, BI-ready datasets and
        governed AI analytics make the results understandable for
        management users.
        """
    )

section_header(
    "03 · Explore Hospital Performance",
    (
        "Move through Hospital 360's analytical workspaces. "
        "Each workspace answers a different management question."
    ),
)

st.markdown(
    """
    <style>
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 16px;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        padding-top: 0.15rem;
    }

    .workspace-icon {
        font-size: 2rem;
        margin-bottom: 0.35rem;
    }

    .workspace-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #123b63;
        margin-bottom: 0.45rem;
    }

    .workspace-description {
        min-height: 74px;
        color: #425466;
        font-size: 0.94rem;
        line-height: 1.55;
        margin-bottom: 0.65rem;
    }

    .workspace-label {
        display: inline-block;
        background: #eaf4ff;
        color: #174a78;
        border: 1px solid #c9e2f7;
        border-radius: 999px;
        padding: 0.22rem 0.65rem;
        font-size: 0.78rem;
        font-weight: 600;
        margin-bottom: 0.75rem;
    }

    .workspace-question {
        background: #f7fafc;
        border-left: 3px solid #4f8fc0;
        border-radius: 6px;
        padding: 0.65rem 0.75rem;
        margin: 0.25rem 0 0.9rem 0;
        color: #526579;
        font-size: 0.84rem;
        line-height: 1.45;
        min-height: 68px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

row1a, row1b, row1c = st.columns(
    3,
    gap="large",
)

with row1a:
    with st.container(border=True):
        st.markdown(
            """
            <div class="workspace-icon">📊</div>
            <div class="workspace-title">
                Executive Command Center
            </div>
            <div class="workspace-description">
                Hospital-wide KPIs, management trends and
                enterprise performance in one executive view.
            </div>
            <div class="workspace-label">
                Leadership & Management
            </div>
            <div class="workspace-question">
                <b>Helps answer:</b><br>
                How is the hospital performing overall?
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.page_link(
            "pages/01_Executive_Command_Center.py",
            label="Open Executive Command Center",
            icon="➡️",
            width="stretch",
        )


with row1b:
    with st.container(border=True):
        st.markdown(
            """
            <div class="workspace-icon">👥</div>
            <div class="workspace-title">
                Patient Analytics
            </div>
            <div class="workspace-description">
                Patient population, demographics, utilization,
                admissions and patient behavior analysis.
            </div>
            <div class="workspace-label">
                Patient Intelligence
            </div>
            <div class="workspace-question">
                <b>Helps answer:</b><br>
                Who are our patients and how do they use services?
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.page_link(
            "pages/02_Patient_Analytics_Dashboard.py",
            label="Open Patient Analytics",
            icon="➡️",
            width="stretch",
        )


with row1c:
    with st.container(border=True):
        st.markdown(
            """
            <div class="workspace-icon">🏥</div>
            <div class="workspace-title">
                Operations Analytics
            </div>
            <div class="workspace-description">
                Admissions, length of stay, emergency activity
                and department-level operational workload.
            </div>
            <div class="workspace-label">
                Hospital Operations
            </div>
            <div class="workspace-question">
                <b>Helps answer:</b><br>
                Where is operational demand concentrated?
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.page_link(
            "pages/03_Operations_Analytics_Dashboard.py",
            label="Open Operations Analytics",
            icon="➡️",
            width="stretch",
        )


st.write("")


row2a, row2b, row2c = st.columns(
    3,
    gap="large",
)

with row2a:
    with st.container(border=True):
        st.markdown(
            """
            <div class="workspace-icon">💰</div>
            <div class="workspace-title">
                Finance Analytics
            </div>
            <div class="workspace-description">
                Revenue, collections, outstanding balances and
                departmental financial performance.
            </div>
            <div class="workspace-label">
                Finance & Revenue Cycle
            </div>
            <div class="workspace-question">
                <b>Helps answer:</b><br>
                Where is revenue generated and money outstanding?
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.page_link(
            "pages/04_Finance_Analytics_Dashboard.py",
            label="Open Finance Analytics",
            icon="➡️",
            width="stretch",
        )


with row2b:
    with st.container(border=True):
        st.markdown(
            """
            <div class="workspace-icon">🛡️</div>
            <div class="workspace-title">
                Risk Analytics
            </div>
            <div class="workspace-description">
                Patient, admission, billing, claim and statistical
                analytical risk signals for structured review.
            </div>
            <div class="workspace-label">
                Risk Intelligence
            </div>
            <div class="workspace-question">
                <b>Helps answer:</b><br>
                Which areas require additional analytical review?
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.page_link(
            "pages/05_Risk_Analytics_Dashboard.py",
            label="Open Risk Analytics",
            icon="➡️",
            width="stretch",
        )


with row2c:
    with st.container(border=True):
        st.markdown(
            """
            <div class="workspace-icon">📄</div>
            <div class="workspace-title">
                Claims Analytics
            </div>
            <div class="workspace-description">
                Insurance claims, payer performance, rejected
                amounts and claim-processing intelligence.
            </div>
            <div class="workspace-label">
                Claims & Payers
            </div>
            <div class="workspace-question">
                <b>Helps answer:</b><br>
                Which insurers and claims drive rejection exposure?
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.page_link(
            "pages/06_Claims_Analytics_Dashboard.py",
            label="Open Claims Analytics",
            icon="➡️",
            width="stretch",
        )


st.write("")


row3a, row3b, row3c = st.columns(
    3,
    gap="large",
)

with row3a:
    with st.container(border=True):
        st.markdown(
            """
            <div class="workspace-icon">🩺</div>
            <div class="workspace-title">
                Doctor Performance
            </div>
            <div class="workspace-description">
                Physician workload, hospital activity and
                doctor-level performance intelligence.
            </div>
            <div class="workspace-label">
                Physician Analytics
            </div>
            <div class="workspace-question">
                <b>Helps answer:</b><br>
                How does physician activity differ across the hospital?
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.page_link(
            "pages/07_Doctor_Performance_Dashboard.py",
            label="Open Doctor Performance",
            icon="➡️",
            width="stretch",
        )


with row3b:
    with st.container(border=True):
        st.markdown(
            """
            <div class="workspace-icon">🤖</div>
            <div class="workspace-title">
                AI Analyst
            </div>
            <div class="workspace-description">
                Natural-language management questions answered
                through governed read-only hospital analytics.
            </div>
            <div class="workspace-label">
                Conversational Analytics
            </div>
            <div class="workspace-question">
                <b>Helps answer:</b><br>
                Can I explore Hospital 360 using normal questions?
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.page_link(
            "pages/08_AI_Analyst_Assistant.py",
            label="Open AI Analyst",
            icon="➡️",
            width="stretch",
        )


with row3c:
    with st.container(border=True):
        st.markdown(
            """
            <div class="workspace-icon">🔎</div>
            <div class="workspace-title">
                Data Explorer
            </div>
            <div class="workspace-description">
                Controlled exploration of approved warehouse and
                semantic-layer datasets for deeper investigation.
            </div>
            <div class="workspace-label">
                Detailed Data Review
            </div>
            <div class="workspace-question">
                <b>Helps answer:</b><br>
                What does the underlying governed dataset contain?
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.page_link(
            "pages/09_Data_Explorer.py",
            label="Open Data Explorer",
            icon="➡️",
            width="stretch",
        )


section_header(
    "04 · Reporting, Data Engineering & Administration",
    (
        "Operational and administrative capabilities are separated "
        "from the analytical dashboards."
    ),
)


admin1, admin2, admin3 = st.columns(3)


with admin1:
    st.markdown(
        """
        #### 📑 MIS Reports Center

        Review generated management reporting outputs and the
        structured reporting layer used by Hospital 360.

        Report generation and downloads are centrally managed
        through the Admin Control Center.
        """
    )

    st.page_link(
        "pages/10_MIS_Reports_Center.py",
        label="Open MIS Reports",
        width="stretch",
    )


with admin2:
    st.markdown(
        """
        #### ⚙️ ETL Control Center

        Understand batch processing, data-quality results and
        warehouse pipeline status.

        This workspace focuses on monitoring rather than
        analytical visualization.
        """
    )

    st.page_link(
        "pages/11_ETL_Control_Center.py",
        label="Open ETL Control",
        width="stretch",
    )


with admin3:
    st.markdown(
        """
        #### 🛠️ Admin Control Center

        Central administrative workspace for generation,
        validation, export management and controlled platform
        operations.

        **All downloadable assets will be centralized here.**
        """
    )

    st.page_link(
        "pages/12_Admin_Control_Center.py",
        label="Open Admin Control Center",
        width="stretch",
    )


section_header(
    "05 · Current Platform Status",
    (
        "A simple operational check confirms whether the analytical "
        "platform is ready for use."
    ),
)


database_online = (
    str(
        system_health.get(
            "status",
            "",
        )
    ).upper()
    == "ONLINE"
)

latest_etl_status = str(
    latest_etl.get(
        "status",
        "UNKNOWN",
    )
).upper()


status1, status2, status3, status4 = st.columns(4)


with status1:
    status_panel(
        "Analytics Database",
        (
            "Online"
            if database_online
            else "Unavailable"
        ),
        (
            "good"
            if database_online
            else "danger"
        ),
    )


with status2:
    status_panel(
        "Latest ETL",
        latest_etl_status.replace("_", " ").title(),
        (
            "good"
            if latest_etl_status == "SUCCESS"
            else "warning"
        ),
    )


with status3:
    status_panel(
        "Patients Available",
        format_integer(patients),
        "good",
    )


with status4:
    status_panel(
        "Admissions Available",
        format_integer(admissions),
        "good",
    )


section_header(
    "06 · Quick Performance View",
    (
        "A small preview of current hospital activity before moving "
        "into the specialist dashboards."
    ),
)


preview_left, preview_right = st.columns(
    [1, 1],
)


with preview_left:
    st.markdown(
        "#### Highest-Volume Departments"
    )

    if departments.empty:
        st.info(
            "Department performance data is not available."
        )
    else:
        department_chart = (
            departments[
                [
                    "department_name",
                    "admissions",
                ]
            ]
            .set_index(
                "department_name"
            )
        )

        st.bar_chart(
            department_chart,
            height=330,
        )

        top_department = departments.iloc[0]

        st.caption(
            f"{top_department['department_name']} currently "
            f"has the highest admission volume in this view "
            f"with {format_integer(top_department['admissions'])} "
            "admissions."
        )


with preview_right:
    st.markdown(
        "#### Recent Hospital Activity"
    )

    if (
        monthly.empty
        or "month_start" not in monthly.columns
        or "admissions" not in monthly.columns
    ):
        st.info(
            "Monthly hospital activity is not available."
        )

    else:
        trend = monthly.copy()

        trend["month_start"] = pd.to_datetime(
            trend["month_start"],
            errors="coerce",
        )

        trend = (
            trend.dropna(
                subset=["month_start"]
            )
            .sort_values(
                "month_start"
            )
            .tail(12)
        )

        trend_chart = (
            trend[
                [
                    "month_start",
                    "admissions",
                ]
            ]
            .set_index(
                "month_start"
            )
        )

        st.line_chart(
            trend_chart,
            height=330,
        )

        st.caption(
            "This preview shows recent admission activity. "
            "Detailed trend interpretation is available in the "
            "Executive and Operations workspaces."
        )


section_header(
    "07 · How to Use Hospital 360",
    (
        "Follow this sequence when presenting or reviewing the "
        "project."
    ),
)


step1, step2, step3, step4 = st.columns(4)


with step1:
    st.markdown(
        """
        #### Step 1

        **Start with Executive**

        Understand hospital-wide performance before moving into
        individual business areas.
        """
    )


with step2:
    st.markdown(
        """
        #### Step 2

        **Investigate the Drivers**

        Use Patient, Operations, Finance, Claims, Risk and Doctor
        dashboards to understand the underlying performance.
        """
    )


with step3:
    st.markdown(
        """
        #### Step 3

        **Review Reporting**

        Use MIS, Data Explorer and AI Analyst for deeper analytical
        interpretation and management reporting.
        """
    )


with step4:
    st.markdown(
        """
        #### Step 4

        **Use Admin for Outputs**

        Generate, validate and download analytical assets,
        reporting packages and BI-ready files from one controlled
        administrative location.
        """
    )


st.divider()


footer_left, footer_right = st.columns(
    [3, 1],
)


with footer_left:
    st.caption(
        "Hospital 360 · Synthetic healthcare analytics portfolio · "
        "PostgreSQL · Python · SQL · Streamlit · MIS · BI · AI"
    )


with footer_right:
    st.caption(
        "Management Analytics Platform"
    )