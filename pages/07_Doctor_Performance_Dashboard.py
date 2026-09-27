from __future__ import annotations

import html

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
    title="Doctor Performance",
    subtitle=(
        "Understand physician workload, patient reach, utilization, case mix, "
        "readmission observations and admission-linked financial activity."
    ),
    icon="🩺",
)


st.markdown(
    """
    <style>
    .doctor-intro {
        background: linear-gradient(135deg, #eef7ff 0%, #f8fbff 100%);
        border: 1px solid #cfe3f5;
        border-radius: 18px;
        padding: 1.35rem 1.5rem;
        margin: 0.35rem 0 1.25rem 0;
        box-shadow: 0 5px 18px rgba(29, 78, 121, 0.06);
    }

    .doctor-intro-title {
        color: #123d68;
        font-size: 1.08rem;
        font-weight: 800;
        margin-bottom: 0.45rem;
    }

    .doctor-intro-text {
        color: #536b80;
        font-size: 0.93rem;
        line-height: 1.65;
    }

    .doctor-guide {
        background: #ffffff;
        border: 1px solid #dce8f2;
        border-radius: 15px;
        padding: 1rem 1.05rem;
        min-height: 138px;
        box-shadow: 0 4px 14px rgba(29, 78, 121, 0.05);
    }

    .doctor-guide-number {
        display: inline-flex;
        width: 31px;
        height: 31px;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        background: #e5f2ff;
        color: #1768a8;
        font-weight: 800;
        margin-bottom: 0.65rem;
    }

    .doctor-guide-title {
        color: #183f66;
        font-size: 0.92rem;
        font-weight: 750;
        margin-bottom: 0.3rem;
    }

    .doctor-guide-text {
        color: #65788b;
        font-size: 0.81rem;
        line-height: 1.5;
    }

    .doctor-panel {
        background: #ffffff;
        border: 1px solid #dce8f2;
        border-radius: 16px;
        padding: 1.1rem 1.2rem;
        margin: 0.3rem 0 1rem 0;
        box-shadow: 0 4px 14px rgba(29, 78, 121, 0.04);
    }

    .doctor-panel-title {
        color: #173e65;
        font-weight: 800;
        font-size: 0.95rem;
        margin-bottom: 0.35rem;
    }

    .doctor-panel-text {
        color: #64778a;
        font-size: 0.86rem;
        line-height: 1.55;
    }

    .doctor-profile {
        background: linear-gradient(135deg, #edf6ff 0%, #ffffff 100%);
        border: 1px solid #cee2f4;
        border-left: 5px solid #2474b5;
        border-radius: 16px;
        padding: 1.15rem 1.3rem;
        margin: 0.4rem 0 1rem 0;
    }

    .doctor-profile-name {
        color: #153e68;
        font-size: 1.18rem;
        font-weight: 800;
        margin-bottom: 0.3rem;
    }

    .doctor-profile-meta {
        color: #607589;
        font-size: 0.88rem;
        line-height: 1.55;
    }

    .doctor-warning {
        background: #fffdf5;
        border: 1px solid #eee1b8;
        border-radius: 14px;
        padding: 1rem 1.1rem;
        color: #665a35;
        font-size: 0.86rem;
        line-height: 1.55;
        margin: 0.5rem 0 1rem 0;
    }

    .doctor-info {
        background: #f5faff;
        border: 1px solid #d3e6f7;
        border-radius: 14px;
        padding: 1rem 1.1rem;
        color: #4f687e;
        font-size: 0.86rem;
        line-height: 1.55;
        margin: 0.5rem 0 1rem 0;
    }

    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #dce8f2;
        border-radius: 14px;
        padding: 0.8rem 0.9rem;
        box-shadow: 0 3px 10px rgba(29, 78, 121, 0.035);
    }

    div[data-testid="stPlotlyChart"] {
        background: #ffffff;
        border: 1px solid #e0e9f1;
        border-radius: 16px;
        padding: 0.35rem;
        box-shadow: 0 4px 14px rgba(29, 78, 121, 0.035);
    }

    div[data-testid="stSelectbox"],
    div[data-testid="stMultiSelect"],
    div[data-testid="stDateInput"] {
        margin-bottom: 0.35rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def safe_number(value, default=0.0):
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def pct(numerator, denominator):
    denominator = safe_number(denominator)
    if denominator == 0:
        return 0.0
    return safe_number(numerator) / denominator * 100


def yes_no(value):
    return "Yes" if bool(value) else "No"


def style_figure(fig, height=420):
    fig.update_layout(
        height=height,
        margin=dict(l=20, r=20, t=60, b=25),
        legend_title_text="",
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(
            family="Arial",
            size=12,
            color="#3f5366",
        ),
        title=dict(
            font=dict(
                size=17,
                color="#173e65",
            ),
            x=0.02,
            xanchor="left",
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
        ),
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor="#edf2f6",
        zeroline=False,
    )
    fig.update_yaxes(
        showgrid=False,
        zeroline=False,
    )
    return fig


def chart_heading(title, description):
    st.markdown(
        f"""
        <div class="doctor-panel">
            <div class="doctor-panel-title">{html.escape(title)}</div>
            <div class="doctor-panel-text">{html.escape(description)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=60, show_spinner=False)
def load_doctor_admissions():
    return read_sql(
        """
        SELECT
            a.admission_key,
            a.admission_id,
            ad.full_date AS admission_date,
            p.patient_id,
            doc.doctor_key,
            doc.doctor_id,
            doc.doctor_name,
            doc.gender AS doctor_gender,
            doc.specialization,
            doc.qualification,
            doc.experience_years,
            doc.consultation_fee,
            doc.joining_date,
            doc.employment_status,
            dep.department_name,
            dep.department_type,
            dx.diagnosis_name,
            dx.diagnosis_category,
            a.admission_type,
            a.length_of_stay,
            a.icu_flag,
            a.readmission_flag,
            a.emergency_flag,
            a.outcome,
            COALESCE(bill.bill_count, 0) AS bill_count,
            COALESCE(bill.gross_amount, 0) AS gross_amount,
            COALESCE(bill.net_amount, 0) AS net_amount,
            COALESCE(bill.paid_amount, 0) AS paid_amount,
            COALESCE(bill.outstanding_amount, 0) AS outstanding_amount
        FROM warehouse.fact_admission a
        INNER JOIN warehouse.dim_date ad
            ON ad.date_key = a.admission_date_key
        INNER JOIN warehouse.dim_patient p
            ON p.patient_key = a.patient_key
        LEFT JOIN warehouse.dim_doctor doc
            ON doc.doctor_key = a.doctor_key
        LEFT JOIN warehouse.dim_department dep
            ON dep.department_key = a.department_key
        LEFT JOIN warehouse.dim_diagnosis dx
            ON dx.diagnosis_key = a.diagnosis_key
        LEFT JOIN (
            SELECT
                admission_key,
                COUNT(*) AS bill_count,
                SUM(gross_amount) AS gross_amount,
                SUM(net_amount) AS net_amount,
                SUM(paid_amount) AS paid_amount,
                SUM(outstanding_amount) AS outstanding_amount
            FROM warehouse.fact_billing
            GROUP BY admission_key
        ) bill
            ON bill.admission_key = a.admission_key
        """
    )


try:
    admissions = load_doctor_admissions()
except Exception as exc:
    st.error(
        "Doctor Performance could not load the physician analytics dataset."
    )
    with st.expander("Technical details"):
        st.exception(exc)
    st.stop()


if admissions.empty:
    st.warning("No physician admission records are available.")
    st.stop()


admissions["admission_date"] = pd.to_datetime(
    admissions["admission_date"],
    errors="coerce",
)

admissions["joining_date"] = pd.to_datetime(
    admissions["joining_date"],
    errors="coerce",
)

for column in [
    "length_of_stay",
    "experience_years",
    "consultation_fee",
    "bill_count",
    "gross_amount",
    "net_amount",
    "paid_amount",
    "outstanding_amount",
]:
    admissions[column] = pd.to_numeric(
        admissions[column],
        errors="coerce",
    ).fillna(0)

for column in [
    "icu_flag",
    "readmission_flag",
    "emergency_flag",
]:
    admissions[column] = (
        admissions[column]
        .fillna(False)
        .astype(bool)
    )

for column in [
    "doctor_id",
    "doctor_name",
    "doctor_gender",
    "specialization",
    "qualification",
    "employment_status",
    "department_name",
    "department_type",
    "diagnosis_name",
    "diagnosis_category",
    "admission_type",
    "outcome",
]:
    admissions[column] = (
        admissions[column]
        .fillna("Unknown")
        .astype(str)
        .str.strip()
    )


st.markdown(
    """
    <div class="doctor-intro">
        <div class="doctor-intro-title">
            Physician Analytics Workspace
        </div>
        <div class="doctor-intro-text">
            This workspace follows physician activity from hospital workload
            and patient reach through utilization, observed case mix,
            readmission signals and admission-linked financial activity.
            Use the Doctor 360 section for individual physician drill-down.
            The page is analytical and descriptive; it does not calculate
            a physician quality score or clinical ranking.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


section_header(
    "01 · Page Guide",
    "Follow the dashboard from population scope to physician-level drill-down.",
)

g1, g2, g3, g4, g5 = st.columns(5)

guide_content = [
    (
        "1",
        "Define Scope",
        "Choose the admission period, department, specialization and physician population.",
    ),
    (
        "2",
        "Understand Workload",
        "Review admissions, patient reach, inpatient utilization and service-line activity.",
    ),
    (
        "3",
        "Review Case Mix",
        "Explore LOS, emergency, ICU and observed readmission patterns.",
    ),
    (
        "4",
        "Review Finance",
        "Understand admission-linked net billing, paid and outstanding amounts.",
    ),
    (
        "5",
        "Doctor 360",
        "Inspect one physician's profile, activity, financial attribution and cases.",
    ),
]

for column, content in zip(
    [g1, g2, g3, g4, g5],
    guide_content,
):
    number, title, text = content
    with column:
        st.markdown(
            f"""
            <div class="doctor-guide">
                <div class="doctor-guide-number">{number}</div>
                <div class="doctor-guide-title">{html.escape(title)}</div>
                <div class="doctor-guide-text">{html.escape(text)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


section_header(
    "02 · Physician Analytics Scope",
    (
        "Set the population for every metric and chart below. "
        "All downstream analysis responds to these filters."
    ),
)

filtered = admissions.copy()
valid_dates = admissions["admission_date"].dropna()

f1, f2 = st.columns(2)

with f1:
    if not valid_dates.empty:
        minimum = valid_dates.min().date()
        maximum = valid_dates.max().date()

        period = st.date_input(
            "Admission Period",
            value=(minimum, maximum),
            min_value=minimum,
            max_value=maximum,
        )
    else:
        period = None

with f2:
    departments = sorted(
        admissions["department_name"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_departments = st.multiselect(
        "Department",
        departments,
        placeholder="All departments",
    )

f3, f4 = st.columns(2)

with f3:
    specializations = sorted(
        admissions["specialization"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_specializations = st.multiselect(
        "Specialization",
        specializations,
        placeholder="All specializations",
    )

with f4:
    doctors = sorted(
        admissions["doctor_name"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_doctors = st.multiselect(
        "Doctor",
        doctors,
        placeholder="All doctors",
    )

if isinstance(period, (tuple, list)) and len(period) == 2:
    start = pd.Timestamp(period[0])
    end = pd.Timestamp(period[1]) + pd.Timedelta(days=1)

    filtered = filtered[
        (filtered["admission_date"] >= start)
        & (filtered["admission_date"] < end)
    ]

if selected_departments:
    filtered = filtered[
        filtered["department_name"].isin(selected_departments)
    ]

if selected_specializations:
    filtered = filtered[
        filtered["specialization"].isin(selected_specializations)
    ]

if selected_doctors:
    filtered = filtered[
        filtered["doctor_name"].isin(selected_doctors)
    ]

if filtered.empty:
    st.warning(
        "No physician activity matches the selected analytical scope."
    )
    st.stop()

scope1, scope2, scope3, scope4 = st.columns(4)

with scope1:
    st.metric(
        "Records in Scope",
        format_integer(len(filtered)),
    )

with scope2:
    st.metric(
        "Doctors in Scope",
        format_integer(filtered["doctor_key"].nunique()),
    )

with scope3:
    st.metric(
        "Departments",
        format_integer(filtered["department_name"].nunique()),
    )

with scope4:
    st.metric(
        "Specializations",
        format_integer(filtered["specialization"].nunique()),
    )


total_admissions = len(filtered)
unique_doctors = filtered["doctor_key"].nunique()
unique_patients = filtered["patient_id"].nunique()
total_inpatient_days = safe_number(
    filtered["length_of_stay"].sum()
)
average_los = safe_number(
    filtered["length_of_stay"].mean()
)
emergency_count = int(
    filtered["emergency_flag"].sum()
)
icu_count = int(
    filtered["icu_flag"].sum()
)
readmission_count = int(
    filtered["readmission_flag"].sum()
)
net_amount = safe_number(
    filtered["net_amount"].sum()
)
paid_amount = safe_number(
    filtered["paid_amount"].sum()
)
outstanding_amount = safe_number(
    filtered["outstanding_amount"].sum()
)


section_header(
    "03 · Executive Physician Scorecard",
    (
        "A single management view of workload, utilization, observed "
        "case mix and admission-linked financial activity."
    ),
)

metric_row(
    [
        (
            "Doctors in Scope",
            format_integer(unique_doctors),
        ),
        (
            "Admissions",
            format_integer(total_admissions),
        ),
        (
            "Unique Patients",
            format_integer(unique_patients),
        ),
        (
            "Inpatient Days",
            format_integer(total_inpatient_days),
        ),
    ]
)

metric_row(
    [
        (
            "Average LOS",
            f"{average_los:.2f} days",
        ),
        (
            "Emergency Share",
            format_percentage(
                pct(emergency_count, total_admissions)
            ),
        ),
        (
            "ICU Share",
            format_percentage(
                pct(icu_count, total_admissions)
            ),
        ),
        (
            "Readmission Share",
            format_percentage(
                pct(readmission_count, total_admissions)
            ),
        ),
    ]
)

metric_row(
    [
        (
            "Attributed Net Billing",
            format_currency_compact(net_amount),
        ),
        (
            "Recorded Paid",
            format_currency_compact(paid_amount),
        ),
        (
            "Recorded Outstanding",
            format_currency_compact(outstanding_amount),
        ),
        (
            "Paid / Net",
            format_percentage(
                pct(paid_amount, net_amount)
            ),
        ),
    ]
)

management_insight(
    (
        f"The selected scope contains {format_integer(unique_doctors)} doctors "
        f"across {format_integer(total_admissions)} admissions and "
        f"{format_integer(unique_patients)} unique patients. "
        f"Average LOS is {average_los:.2f} days. Emergency cases represent "
        f"{format_percentage(pct(emergency_count, total_admissions))}, "
        f"ICU cases {format_percentage(pct(icu_count, total_admissions))}, "
        f"and admissions carrying the readmission flag "
        f"{format_percentage(pct(readmission_count, total_admissions))}."
    ),
    label="Management Snapshot",
)


doctor_summary = (
    filtered.groupby(
        [
            "doctor_key",
            "doctor_id",
            "doctor_name",
            "specialization",
            "department_name",
            "qualification",
            "experience_years",
            "employment_status",
        ],
        dropna=False,
        as_index=False,
    )
    .agg(
        admissions=("admission_id", "count"),
        patients=("patient_id", "nunique"),
        inpatient_days=("length_of_stay", "sum"),
        average_los=("length_of_stay", "mean"),
        emergency_admissions=("emergency_flag", "sum"),
        icu_admissions=("icu_flag", "sum"),
        readmissions=("readmission_flag", "sum"),
        net_amount=("net_amount", "sum"),
        paid_amount=("paid_amount", "sum"),
        outstanding_amount=("outstanding_amount", "sum"),
    )
)

doctor_summary["emergency_rate_pct"] = doctor_summary.apply(
    lambda row: pct(
        row["emergency_admissions"],
        row["admissions"],
    ),
    axis=1,
)

doctor_summary["icu_rate_pct"] = doctor_summary.apply(
    lambda row: pct(
        row["icu_admissions"],
        row["admissions"],
    ),
    axis=1,
)

doctor_summary["readmission_rate_pct"] = doctor_summary.apply(
    lambda row: pct(
        row["readmissions"],
        row["admissions"],
    ),
    axis=1,
)

doctor_summary["paid_to_net_pct"] = doctor_summary.apply(
    lambda row: pct(
        row["paid_amount"],
        row["net_amount"],
    ),
    axis=1,
)

doctor_summary["net_amount_per_admission"] = doctor_summary.apply(
    lambda row: (
        safe_number(row["net_amount"])
        / safe_number(row["admissions"])
        if safe_number(row["admissions"]) > 0
        else 0
    ),
    axis=1,
)


section_header(
    "04 · Physician Workload & Patient Reach",
    (
        "Compare admission workload and distinct patient reach. "
        "Volume describes activity and should not be interpreted as quality."
    ),
)

threshold_left, threshold_right = st.columns([2, 3])

with threshold_left:
    minimum_case_count = st.slider(
        "Minimum admissions for physician comparison",
        min_value=1,
        max_value=max(
            1,
            min(
                100,
                int(doctor_summary["admissions"].max()),
            ),
        ),
        value=min(
            25,
            max(
                1,
                int(doctor_summary["admissions"].max()),
            ),
        ),
        key="doctor_min_case_count",
    )

with threshold_right:
    st.markdown(
        f"""
        <div class="doctor-info">
            Physician comparison charts currently include doctors with at
            least <b>{format_integer(minimum_case_count)}</b> admissions.
            The threshold helps avoid emphasizing very small case volumes.
        </div>
        """,
        unsafe_allow_html=True,
    )

comparison_doctors = doctor_summary[
    doctor_summary["admissions"] >= minimum_case_count
].copy()

if comparison_doctors.empty:
    comparison_doctors = doctor_summary.copy()

left, right = st.columns(2)

with left:
    chart_heading(
        "Admission Workload",
        "Doctors with the largest admission volumes in the selected scope.",
    )

    chart = (
        comparison_doctors
        .sort_values(
            "admissions",
            ascending=False,
        )
        .head(20)
        .sort_values(
            "admissions",
            ascending=True,
        )
    )

    fig = px.bar(
        chart,
        x="admissions",
        y="doctor_name",
        orientation="h",
        title="Admissions by Doctor",
        hover_data=[
            "specialization",
            "department_name",
            "patients",
        ],
        text_auto=True,
    )

    fig.update_yaxes(title=None)
    fig.update_xaxes(title="Admissions")

    st.plotly_chart(
        style_figure(fig, 520),
        width="stretch",
    )

with right:
    chart_heading(
        "Unique Patient Reach",
        "Distinct patients associated with each physician's admissions.",
    )

    chart = (
        comparison_doctors
        .sort_values(
            "patients",
            ascending=False,
        )
        .head(20)
        .sort_values(
            "patients",
            ascending=True,
        )
    )

    fig = px.bar(
        chart,
        x="patients",
        y="doctor_name",
        orientation="h",
        title="Unique Patients by Doctor",
        hover_data=[
            "specialization",
            "department_name",
            "admissions",
        ],
        text_auto=True,
    )

    fig.update_yaxes(title=None)
    fig.update_xaxes(title="Unique Patients")

    st.plotly_chart(
        style_figure(fig, 520),
        width="stretch",
    )


section_header(
    "05 · Service-Line Workload",
    (
        "Understand how physician activity is distributed across "
        "specializations and hospital departments."
    ),
)

specialization_summary = (
    filtered.groupby(
        "specialization",
        as_index=False,
    )
    .agg(
        doctors=("doctor_key", "nunique"),
        admissions=("admission_id", "count"),
        patients=("patient_id", "nunique"),
        inpatient_days=("length_of_stay", "sum"),
        average_los=("length_of_stay", "mean"),
    )
)

department_summary = (
    filtered.groupby(
        "department_name",
        as_index=False,
    )
    .agg(
        doctors=("doctor_key", "nunique"),
        admissions=("admission_id", "count"),
        patients=("patient_id", "nunique"),
        inpatient_days=("length_of_stay", "sum"),
        average_los=("length_of_stay", "mean"),
    )
)

left, right = st.columns(2)

with left:
    chart_heading(
        "Specialization Distribution",
        "Admission workload grouped by physician specialization.",
    )

    chart = specialization_summary.sort_values(
        "admissions",
        ascending=True,
    )

    fig = px.bar(
        chart,
        x="admissions",
        y="specialization",
        orientation="h",
        title="Admissions by Specialization",
        hover_data=[
            "doctors",
            "patients",
            "average_los",
        ],
        text_auto=True,
    )

    fig.update_yaxes(title=None)
    fig.update_xaxes(title="Admissions")

    st.plotly_chart(
        style_figure(fig, 450),
        width="stretch",
    )

with right:
    chart_heading(
        "Department Distribution",
        "Admission workload grouped by hospital department.",
    )

    chart = department_summary.sort_values(
        "admissions",
        ascending=True,
    )

    fig = px.bar(
        chart,
        x="admissions",
        y="department_name",
        orientation="h",
        title="Admissions by Department",
        hover_data=[
            "doctors",
            "patients",
            "average_los",
        ],
        text_auto=True,
    )

    fig.update_yaxes(title=None)
    fig.update_xaxes(title="Admissions")

    st.plotly_chart(
        style_figure(fig, 450),
        width="stretch",
    )


section_header(
    "06 · Length of Stay & Acute Case Mix",
    (
        "Review observed LOS together with emergency, ICU and readmission "
        "shares. These measures describe the recorded case mix."
    ),
)

left, right = st.columns(2)

with left:
    chart_heading(
        "Average Length of Stay",
        "Observed average LOS among physicians meeting the comparison threshold.",
    )

    chart = (
        comparison_doctors
        .sort_values(
            "average_los",
            ascending=False,
        )
        .head(20)
        .sort_values(
            "average_los",
            ascending=True,
        )
    )

    fig = px.bar(
        chart,
        x="average_los",
        y="doctor_name",
        orientation="h",
        title="Average LOS by Doctor",
        hover_data=[
            "admissions",
            "specialization",
            "department_name",
        ],
        text_auto=True,
    )

    fig.update_yaxes(title=None)
    fig.update_xaxes(title="Average LOS (Days)")

    st.plotly_chart(
        style_figure(fig, 520),
        width="stretch",
    )

with right:
    chart_heading(
        "Acute Case-Mix Shares",
        "Emergency, ICU and readmission shares for higher-volume physicians.",
    )

    case_mix = (
        comparison_doctors[
            [
                "doctor_name",
                "admissions",
                "emergency_rate_pct",
                "icu_rate_pct",
                "readmission_rate_pct",
            ]
        ]
        .melt(
            id_vars=[
                "doctor_name",
                "admissions",
            ],
            value_vars=[
                "emergency_rate_pct",
                "icu_rate_pct",
                "readmission_rate_pct",
            ],
            var_name="Metric",
            value_name="Rate",
        )
    )

    case_mix["Metric"] = case_mix["Metric"].map(
        {
            "emergency_rate_pct": "Emergency",
            "icu_rate_pct": "ICU",
            "readmission_rate_pct": "Readmission",
        }
    )

    top_volume_doctors = (
        comparison_doctors
        .sort_values(
            "admissions",
            ascending=False,
        )
        .head(15)["doctor_name"]
        .tolist()
    )

    case_mix = case_mix[
        case_mix["doctor_name"].isin(top_volume_doctors)
    ]

    fig = px.bar(
        case_mix,
        x="doctor_name",
        y="Rate",
        color="Metric",
        barmode="group",
        title="Acute Case-Mix Rates",
    )

    fig.update_xaxes(
        title=None,
        tickangle=-45,
    )
    fig.update_yaxes(title="Share (%)")

    st.plotly_chart(
        style_figure(fig, 520),
        width="stretch",
    )

st.markdown(
    """
    <div class="doctor-warning">
        Length of stay, emergency use, ICU use and readmission flags are
        descriptive observations. Hospital 360 does not apply severity
        adjustment, expected-outcome modelling or risk-adjusted physician
        quality benchmarking in this workspace.
    </div>
    """,
    unsafe_allow_html=True,
)


section_header(
    "07 · Readmission Observation",
    (
        "Review observed physician-level readmission shares while keeping "
        "case-volume and case-mix limitations visible."
    ),
)

readmission_view = (
    comparison_doctors[
        [
            "doctor_name",
            "specialization",
            "department_name",
            "admissions",
            "readmissions",
            "readmission_rate_pct",
        ]
    ]
    .sort_values(
        "readmission_rate_pct",
        ascending=False,
    )
)

left, right = st.columns([3, 2])

with left:
    chart_heading(
        "Observed Readmission Share",
        (
            f"Physicians shown meet the current threshold of "
            f"{format_integer(minimum_case_count)} admissions."
        ),
    )

    chart = (
        readmission_view
        .head(20)
        .sort_values(
            "readmission_rate_pct",
            ascending=True,
        )
    )

    fig = px.bar(
        chart,
        x="readmission_rate_pct",
        y="doctor_name",
        orientation="h",
        title="Observed Readmission Share by Doctor",
        hover_data=[
            "admissions",
            "readmissions",
            "specialization",
            "department_name",
        ],
        text_auto=True,
    )

    fig.update_yaxes(title=None)
    fig.update_xaxes(title="Readmission Share (%)")

    st.plotly_chart(
        style_figure(fig, 510),
        width="stretch",
    )

with right:
    chart_heading(
        "How to Read This View",
        "Use this chart as a management review signal, not a standalone physician rating.",
    )

    st.markdown(
        f"""
        <div class="doctor-info">
            <b>Current comparison threshold</b><br>
            {format_integer(minimum_case_count)} admissions
            <br><br>
            <b>What the value means</b><br>
            Share of admissions carrying the recorded readmission flag.
            <br><br>
            <b>What it does not control for</b><br>
            Patient complexity, specialty, severity, admission type and
            other clinical factors.
            <br><br>
            <b>Recommended use</b><br>
            Identify areas for deeper review rather than labeling physician
            quality.
        </div>
        """,
        unsafe_allow_html=True,
    )


section_header(
    "08 · Physician-Attributed Financial Activity",
    (
        "Review billing linked to admissions managed by each physician. "
        "This is financial attribution, not physician compensation."
    ),
)

left, right = st.columns(2)

with left:
    chart_heading(
        "Attributed Net Billing",
        "Admission-linked net billing associated with each physician.",
    )

    chart = (
        comparison_doctors
        .sort_values(
            "net_amount",
            ascending=False,
        )
        .head(20)
        .sort_values(
            "net_amount",
            ascending=True,
        )
    )

    fig = px.bar(
        chart,
        x="net_amount",
        y="doctor_name",
        orientation="h",
        title="Attributed Net Billing by Doctor",
        hover_data=[
            "admissions",
            "specialization",
            "department_name",
        ],
        text_auto=True,
    )

    fig.update_yaxes(title=None)
    fig.update_xaxes(title="Net Billing")

    st.plotly_chart(
        style_figure(fig, 520),
        width="stretch",
    )

with right:
    chart_heading(
        "Recorded Outstanding",
        "Admission-linked outstanding billing associated with each physician.",
    )

    chart = (
        comparison_doctors
        .sort_values(
            "outstanding_amount",
            ascending=False,
        )
        .head(20)
        .sort_values(
            "outstanding_amount",
            ascending=True,
        )
    )

    fig = px.bar(
        chart,
        x="outstanding_amount",
        y="doctor_name",
        orientation="h",
        title="Recorded Outstanding by Doctor",
        hover_data=[
            "net_amount",
            "paid_amount",
            "admissions",
        ],
        text_auto=True,
    )

    fig.update_yaxes(title=None)
    fig.update_xaxes(title="Outstanding")

    st.plotly_chart(
        style_figure(fig, 520),
        width="stretch",
    )

st.markdown(
    """
    <div class="doctor-warning">
        Financial values are attributed through admission-linked billing.
        They do not represent physician salary, compensation, profitability
        or contribution margin. Paid / Net is a simple recorded paid-to-net
        ratio and is not period-matched cash collection. Outstanding is not
        formal accounts-receivable aging.
    </div>
    """,
    unsafe_allow_html=True,
)


section_header(
    "09 · Physician Analytical Matrix",
    (
        "Compare physician workload, utilization, case mix and financial "
        "attribution in one structured table without a composite score."
    ),
)

doctor_display = (
    doctor_summary.sort_values(
        [
            "admissions",
            "patients",
        ],
        ascending=[
            False,
            False,
        ],
    )
    [
        [
            "doctor_id",
            "doctor_name",
            "specialization",
            "department_name",
            "qualification",
            "experience_years",
            "employment_status",
            "admissions",
            "patients",
            "inpatient_days",
            "average_los",
            "emergency_rate_pct",
            "icu_rate_pct",
            "readmission_rate_pct",
            "net_amount",
            "paid_amount",
            "outstanding_amount",
            "paid_to_net_pct",
        ]
    ]
    .rename(
        columns={
            "doctor_id": "Doctor ID",
            "doctor_name": "Doctor",
            "specialization": "Specialization",
            "department_name": "Department",
            "qualification": "Qualification",
            "experience_years": "Experience Years",
            "employment_status": "Employment Status",
            "admissions": "Admissions",
            "patients": "Patients",
            "inpatient_days": "Inpatient Days",
            "average_los": "Average LOS",
            "emergency_rate_pct": "Emergency Share %",
            "icu_rate_pct": "ICU Share %",
            "readmission_rate_pct": "Readmission Share %",
            "net_amount": "Net Billing",
            "paid_amount": "Paid",
            "outstanding_amount": "Outstanding",
            "paid_to_net_pct": "Paid / Net %",
        }
    )
)

dataframe(
    doctor_display,
    height=520,
)


section_header(
    "10 · Clinical Case Mix",
    (
        "Understand the diagnosis categories and admission types represented "
        "in the selected physician population."
    ),
)

diagnosis_mix = (
    filtered.groupby(
        "diagnosis_category",
        as_index=False,
    )
    .agg(
        admissions=("admission_id", "count"),
        patients=("patient_id", "nunique"),
        average_los=("length_of_stay", "mean"),
    )
    .sort_values(
        "admissions",
        ascending=False,
    )
)

admission_mix = (
    filtered.groupby(
        "admission_type",
        as_index=False,
    )
    .agg(
        admissions=("admission_id", "count"),
        patients=("patient_id", "nunique"),
        average_los=("length_of_stay", "mean"),
    )
    .sort_values(
        "admissions",
        ascending=False,
    )
)

left, right = st.columns(2)

with left:
    chart_heading(
        "Diagnosis Category Mix",
        "Admission volume grouped by diagnosis category.",
    )

    chart = (
        diagnosis_mix
        .head(15)
        .sort_values(
            "admissions",
            ascending=True,
        )
    )

    fig = px.bar(
        chart,
        x="admissions",
        y="diagnosis_category",
        orientation="h",
        title="Admissions by Diagnosis Category",
        hover_data=[
            "patients",
            "average_los",
        ],
        text_auto=True,
    )

    fig.update_yaxes(title=None)
    fig.update_xaxes(title="Admissions")

    st.plotly_chart(
        style_figure(fig, 440),
        width="stretch",
    )

with right:
    chart_heading(
        "Admission Type Mix",
        "How the selected physician population is distributed by admission type.",
    )

    fig = px.bar(
        admission_mix,
        x="admission_type",
        y="admissions",
        title="Admissions by Admission Type",
        hover_data=[
            "patients",
            "average_los",
        ],
        text_auto=True,
    )

    fig.update_xaxes(title=None)
    fig.update_yaxes(title="Admissions")

    st.plotly_chart(
        style_figure(fig, 440),
        width="stretch",
    )


section_header(
    "11 · Management Review Signals",
    (
        "Descriptive signals that help management decide where deeper "
        "investigation may be useful. They are not an overall doctor ranking."
    ),
)

signals = []

if not comparison_doctors.empty:
    row = comparison_doctors.sort_values(
        "admissions",
        ascending=False,
    ).iloc[0]

    signals.append(
        {
            "Review Signal": "Largest Admission Workload",
            "Doctor": row["doctor_name"],
            "Department": row["department_name"],
            "Observed Value": format_integer(row["admissions"]),
            "Management Context": (
                "Largest admission count among physicians meeting the "
                "current comparison threshold."
            ),
        }
    )

    row = comparison_doctors.sort_values(
        "average_los",
        ascending=False,
    ).iloc[0]

    signals.append(
        {
            "Review Signal": "Largest Average LOS",
            "Doctor": row["doctor_name"],
            "Department": row["department_name"],
            "Observed Value": f"{row['average_los']:.2f} days",
            "Management Context": (
                "Largest observed average LOS among physicians meeting "
                "the current comparison threshold."
            ),
        }
    )

    row = comparison_doctors.sort_values(
        "readmission_rate_pct",
        ascending=False,
    ).iloc[0]

    signals.append(
        {
            "Review Signal": "Largest Observed Readmission Share",
            "Doctor": row["doctor_name"],
            "Department": row["department_name"],
            "Observed Value": format_percentage(
                row["readmission_rate_pct"]
            ),
            "Management Context": (
                "Observed readmission share only; not adjusted for "
                "severity, specialty or case complexity."
            ),
        }
    )

    row = comparison_doctors.sort_values(
        "icu_rate_pct",
        ascending=False,
    ).iloc[0]

    signals.append(
        {
            "Review Signal": "Largest ICU Case Share",
            "Doctor": row["doctor_name"],
            "Department": row["department_name"],
            "Observed Value": format_percentage(
                row["icu_rate_pct"]
            ),
            "Management Context": (
                "Largest observed ICU share among physicians meeting "
                "the current comparison threshold."
            ),
        }
    )

    row = comparison_doctors.sort_values(
        "net_amount",
        ascending=False,
    ).iloc[0]

    signals.append(
        {
            "Review Signal": "Largest Attributed Net Billing",
            "Doctor": row["doctor_name"],
            "Department": row["department_name"],
            "Observed Value": format_currency_compact(
                row["net_amount"]
            ),
            "Management Context": (
                "Largest admission-linked net billing total in the "
                "selected scope."
            ),
        }
    )

    row = comparison_doctors.sort_values(
        "outstanding_amount",
        ascending=False,
    ).iloc[0]

    signals.append(
        {
            "Review Signal": "Largest Recorded Outstanding",
            "Doctor": row["doctor_name"],
            "Department": row["department_name"],
            "Observed Value": format_currency_compact(
                row["outstanding_amount"]
            ),
            "Management Context": (
                "Largest admission-linked recorded outstanding billing "
                "balance in the comparison population."
            ),
        }
    )

if signals:
    dataframe(
        pd.DataFrame(signals),
        height=390,
    )


section_header(
    "12 · Doctor 360 Drill-Down",
    (
        "Select one physician to inspect profile information, operational "
        "activity, financial attribution and admission history."
    ),
)

doctor_options = (
    doctor_summary[
        [
            "doctor_key",
            "doctor_id",
            "doctor_name",
            "specialization",
            "department_name",
        ]
    ]
    .drop_duplicates()
    .sort_values(
        [
            "doctor_name",
            "doctor_id",
        ]
    )
)

doctor_options["selector"] = (
    doctor_options["doctor_name"]
    + " · "
    + doctor_options["doctor_id"].astype(str)
    + " · "
    + doctor_options["department_name"]
)

selected_doctor_label = st.selectbox(
    "Select Doctor",
    doctor_options["selector"].tolist(),
    key="doctor_360_selector",
)

selected_doctor_key = doctor_options.loc[
    doctor_options["selector"] == selected_doctor_label,
    "doctor_key",
].iloc[0]

doctor_cases = filtered[
    filtered["doctor_key"] == selected_doctor_key
].copy()

if doctor_cases.empty:
    doctor_cases = admissions[
        admissions["doctor_key"] == selected_doctor_key
    ].copy()

profile = doctor_cases.iloc[0]

st.markdown(
    f"""
    <div class="doctor-profile">
        <div class="doctor-profile-name">
            {html.escape(str(profile["doctor_name"]))}
        </div>
        <div class="doctor-profile-meta">
            {html.escape(str(profile["doctor_id"]))}
            &nbsp; · &nbsp;
            {html.escape(str(profile["specialization"]))}
            &nbsp; · &nbsp;
            {html.escape(str(profile["department_name"]))}
            &nbsp; · &nbsp;
            {html.escape(str(profile["employment_status"]))}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

tabs = st.tabs(
    [
        "Profile",
        "Operational Performance",
        "Financial Attribution",
        "Admission History",
    ]
)

with tabs[0]:
    p1, p2, p3, p4 = st.columns(4)

    with p1:
        st.metric(
            "Doctor ID",
            str(profile["doctor_id"]),
        )

    with p2:
        st.metric(
            "Specialization",
            str(profile["specialization"]),
        )

    with p3:
        st.metric(
            "Experience",
            f"{safe_number(profile['experience_years']):.0f} years",
        )

    with p4:
        st.metric(
            "Employment",
            str(profile["employment_status"]),
        )

    profile_table = pd.DataFrame(
        [
            {
                "Profile Attribute": "Doctor",
                "Value": profile["doctor_name"],
            },
            {
                "Profile Attribute": "Department",
                "Value": profile["department_name"],
            },
            {
                "Profile Attribute": "Department Type",
                "Value": profile["department_type"],
            },
            {
                "Profile Attribute": "Specialization",
                "Value": profile["specialization"],
            },
            {
                "Profile Attribute": "Qualification",
                "Value": profile["qualification"],
            },
            {
                "Profile Attribute": "Experience Years",
                "Value": int(
                    safe_number(
                        profile["experience_years"]
                    )
                ),
            },
            {
                "Profile Attribute": "Consultation Fee",
                "Value": safe_number(
                    profile["consultation_fee"]
                ),
            },
            {
                "Profile Attribute": "Joining Date",
                "Value": (
                    profile["joining_date"].date()
                    if pd.notna(profile["joining_date"])
                    else "Unknown"
                ),
            },
            {
                "Profile Attribute": "Employment Status",
                "Value": profile["employment_status"],
            },
        ]
    )

    dataframe(
        profile_table,
        height=380,
    )

with tabs[1]:
    doctor_admissions = len(doctor_cases)
    doctor_patients = doctor_cases["patient_id"].nunique()
    doctor_avg_los = safe_number(
        doctor_cases["length_of_stay"].mean()
    )
    doctor_emergency = int(
        doctor_cases["emergency_flag"].sum()
    )
    doctor_icu = int(
        doctor_cases["icu_flag"].sum()
    )
    doctor_readmissions = int(
        doctor_cases["readmission_flag"].sum()
    )

    metric_row(
        [
            (
                "Admissions",
                format_integer(doctor_admissions),
            ),
            (
                "Unique Patients",
                format_integer(doctor_patients),
            ),
            (
                "Average LOS",
                f"{doctor_avg_los:.2f} days",
            ),
            (
                "Inpatient Days",
                format_integer(
                    doctor_cases["length_of_stay"].sum()
                ),
            ),
        ]
    )

    metric_row(
        [
            (
                "Emergency Share",
                format_percentage(
                    pct(
                        doctor_emergency,
                        doctor_admissions,
                    )
                ),
            ),
            (
                "ICU Share",
                format_percentage(
                    pct(
                        doctor_icu,
                        doctor_admissions,
                    )
                ),
            ),
            (
                "Readmission Share",
                format_percentage(
                    pct(
                        doctor_readmissions,
                        doctor_admissions,
                    )
                ),
            ),
            (
                "Diagnosis Categories",
                format_integer(
                    doctor_cases[
                        "diagnosis_category"
                    ].nunique()
                ),
            ),
        ]
    )

    doctor_monthly = doctor_cases[
        doctor_cases["admission_date"].notna()
    ].copy()

    doctor_monthly["month"] = (
        doctor_monthly["admission_date"]
        .dt.to_period("M")
        .dt.to_timestamp()
    )

    doctor_monthly = (
        doctor_monthly.groupby(
            "month",
            as_index=False,
        )
        .agg(
            admissions=("admission_id", "count"),
            average_los=("length_of_stay", "mean"),
        )
        .sort_values("month")
    )

    if not doctor_monthly.empty:
        chart_heading(
            "Monthly Workload",
            "Admission activity for the selected physician over time.",
        )

        fig = px.line(
            doctor_monthly,
            x="month",
            y="admissions",
            markers=True,
            title="Monthly Admission Workload",
        )

        fig.update_xaxes(title=None)
        fig.update_yaxes(title="Admissions")

        st.plotly_chart(
            style_figure(fig, 390),
            width="stretch",
        )

with tabs[2]:
    doctor_net = safe_number(
        doctor_cases["net_amount"].sum()
    )
    doctor_paid = safe_number(
        doctor_cases["paid_amount"].sum()
    )
    doctor_outstanding = safe_number(
        doctor_cases["outstanding_amount"].sum()
    )

    metric_row(
        [
            (
                "Net Billing",
                format_currency_compact(
                    doctor_net
                ),
            ),
            (
                "Recorded Paid",
                format_currency_compact(
                    doctor_paid
                ),
            ),
            (
                "Recorded Outstanding",
                format_currency_compact(
                    doctor_outstanding
                ),
            ),
            (
                "Paid / Net",
                format_percentage(
                    pct(
                        doctor_paid,
                        doctor_net,
                    )
                ),
            ),
        ]
    )

    doctor_financial = pd.DataFrame(
        {
            "Metric": [
                "Net Billing",
                "Paid",
                "Outstanding",
            ],
            "Amount": [
                doctor_net,
                doctor_paid,
                doctor_outstanding,
            ],
        }
    )

    chart_heading(
        "Admission-Linked Financial Position",
        (
            "Financial values linked to admissions managed by the selected "
            "physician."
        ),
    )

    fig = px.bar(
        doctor_financial,
        x="Metric",
        y="Amount",
        title="Admission-Linked Financial Position",
        text_auto=True,
    )

    fig.update_xaxes(title=None)
    fig.update_yaxes(title="Amount")

    st.plotly_chart(
        style_figure(fig, 390),
        width="stretch",
    )

    st.markdown(
        """
        <div class="doctor-warning">
            These amounts represent billing attributed through admissions
            managed by the selected physician. They do not represent
            physician income, compensation, margin or profitability.
        </div>
        """,
        unsafe_allow_html=True,
    )

with tabs[3]:
    history = (
        doctor_cases.sort_values(
            "admission_date",
            ascending=False,
        )
        [
            [
                "admission_id",
                "patient_id",
                "admission_date",
                "admission_type",
                "diagnosis_name",
                "diagnosis_category",
                "length_of_stay",
                "emergency_flag",
                "icu_flag",
                "readmission_flag",
                "outcome",
                "net_amount",
                "paid_amount",
                "outstanding_amount",
            ]
        ]
        .copy()
    )

    history["emergency_flag"] = (
        history["emergency_flag"].apply(yes_no)
    )

    history["icu_flag"] = (
        history["icu_flag"].apply(yes_no)
    )

    history["readmission_flag"] = (
        history["readmission_flag"].apply(yes_no)
    )

    history = history.rename(
        columns={
            "admission_id": "Admission ID",
            "patient_id": "Patient ID",
            "admission_date": "Admission Date",
            "admission_type": "Admission Type",
            "diagnosis_name": "Diagnosis",
            "diagnosis_category": "Diagnosis Category",
            "length_of_stay": "LOS",
            "emergency_flag": "Emergency",
            "icu_flag": "ICU",
            "readmission_flag": "Readmission",
            "outcome": "Outcome",
            "net_amount": "Net Billing",
            "paid_amount": "Paid",
            "outstanding_amount": "Outstanding",
        }
    )

    chart_heading(
        "Admission History",
        (
            "Case-level admission history for the selected physician within "
            "the current analytical scope."
        ),
    )

    dataframe(
        history,
        height=520,
    )


section_header(
    "13 · Metric Definitions & Interpretation",
    (
        "Use these definitions when reading physician analytics and "
        "communicating results to management."
    ),
)

semantics = pd.DataFrame(
    [
        {
            "Metric": "Admissions",
            "Business Meaning": (
                "Admission records attributed to the physician through "
                "the hospital admission fact."
            ),
        },
        {
            "Metric": "Unique Patients",
            "Business Meaning": (
                "Distinct patient IDs represented across the physician's "
                "admissions."
            ),
        },
        {
            "Metric": "Average LOS",
            "Business Meaning": (
                "Mean recorded length of stay across admissions in the "
                "selected scope."
            ),
        },
        {
            "Metric": "Emergency Share",
            "Business Meaning": (
                "Share of physician admissions carrying the recorded "
                "emergency flag."
            ),
        },
        {
            "Metric": "ICU Share",
            "Business Meaning": (
                "Share of physician admissions carrying the recorded ICU flag."
            ),
        },
        {
            "Metric": "Readmission Share",
            "Business Meaning": (
                "Share of admissions carrying readmission_flag = true. "
                "The measure is not severity-adjusted."
            ),
        },
        {
            "Metric": "Net Billing",
            "Business Meaning": (
                "Net billing linked to the physician's admissions. "
                "It is financial attribution, not physician compensation."
            ),
        },
        {
            "Metric": "Paid / Net",
            "Business Meaning": (
                "Recorded paid amount divided by net billing. "
                "It is not period-matched cash collection."
            ),
        },
        {
            "Metric": "Outstanding",
            "Business Meaning": (
                "Recorded billing outstanding linked to admissions. "
                "It is not formal accounts-receivable aging."
            ),
        },
    ]
)

dataframe(
    semantics,
    height=410,
)


section_header(
    "14 · Responsible Use",
    (
        "Important boundaries for interpreting physician-level analytics."
    ),
)

r1, r2, r3 = st.columns(3)

with r1:
    st.info(
        """
**Workload ≠ Quality**

Higher admission volume or patient reach describes physician workload. It does not mean a physician is better or worse.
        """
    )

with r2:
    st.info(
        """
**Case Mix ≠ Quality Score**

LOS, emergency, ICU and readmission measures are observed values. They are not risk-adjusted clinical quality ratings.
        """
    )

with r3:
    st.info(
        """
**Billing ≠ Compensation**

Admission-linked billing is financial attribution. It is not physician salary, profitability or contribution margin.
        """
    )


st.markdown(
    """
    <div class="doctor-info">
        <b>Dashboard role:</b> This page is a visualization and analytical
        workspace. Report generation, downloadable deliverables and platform
        administration are intentionally handled through the Admin Control
        Center so that operational controls remain centralized.
    </div>
    """,
    unsafe_allow_html=True,
)


render_refresh_button(
    key="doctor_performance_refresh",
)