from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from analytics.data_loader import read_sql
from utils.app_helpers import (
    bootstrap_page,
    dataframe,
    format_integer,
    format_percentage,
    management_insight,
    metric_row,
    render_refresh_button,
)


bootstrap_page(
    title="Operations Analytics",
    subtitle=(
        "Hospital operations intelligence for patient flow, "
        "department workload, emergency demand, ICU activity, "
        "length of stay, service demand and admission-level review."
    ),
    icon="🏥",
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


def style_figure(fig, height=390, unified_hover=False):
    fig.update_layout(
        height=height,
        margin=dict(
            l=15,
            r=15,
            t=35,
            b=15,
        ),
        legend_title_text="",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            size=13,
        ),
    )

    if unified_hover:
        fig.update_layout(
            hovermode="x unified",
        )

    return fig


def page_section(number, title, description):
    st.markdown(
        f"""
        <div class="h360-section-banner">
            <div class="h360-section-number">{number}</div>
            <div>
                <div class="h360-section-title">{title}</div>
                <div class="h360-section-description">
                    {description}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def card_heading(title, description):
    st.markdown(
        f"""
        <div class="h360-card-heading">
            <div class="h360-card-title">{title}</div>
            <div class="h360-card-description">
                {description}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def explanation_box(title, text):
    st.markdown(
        f"""
        <div class="h360-explanation">
            <div class="h360-explanation-title">
                {title}
            </div>
            <div class="h360-explanation-text">
                {text}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.markdown(
    """
    <style>
    .h360-flow {
        background: linear-gradient(
            135deg,
            #eff6ff 0%,
            #f8fbff 100%
        );
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
        background: linear-gradient(
            135deg,
            #edf6ff 0%,
            #f8fbff 100%
        );
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
        padding: 16px;
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
def load_operations_base():
    return read_sql(
        """
        SELECT
            a.admission_key,
            a.admission_id,
            p.patient_id,
            a.admission_timestamp,
            a.discharge_timestamp,
            ad.full_date AS admission_date,
            dd.full_date AS discharge_date,
            dep.department_name,
            dep.department_type,
            dep.floor_number,
            dep.bed_capacity,
            doc.doctor_id,
            doc.doctor_name,
            doc.specialization,
            dx.diagnosis_code,
            dx.diagnosis_name,
            dx.diagnosis_category,
            a.admission_type,
            a.room_type,
            a.bed_number,
            a.length_of_stay,
            a.icu_flag,
            a.readmission_flag,
            a.emergency_flag,
            a.outcome
        FROM warehouse.fact_admission a

        INNER JOIN warehouse.dim_patient p
            ON p.patient_key = a.patient_key

        INNER JOIN warehouse.dim_date ad
            ON ad.date_key = a.admission_date_key

        LEFT JOIN warehouse.dim_date dd
            ON dd.date_key = a.discharge_date_key

        LEFT JOIN warehouse.dim_department dep
            ON dep.department_key = a.department_key

        LEFT JOIN warehouse.dim_doctor doc
            ON doc.doctor_key = a.doctor_key

        LEFT JOIN warehouse.dim_diagnosis dx
            ON dx.diagnosis_key = a.diagnosis_key
        """
    )


try:
    operations = load_operations_base()

except Exception as exc:
    st.error(
        "Operations Analytics could not load "
        "admission-level warehouse data."
    )
    st.exception(exc)
    st.stop()


if operations.empty:
    st.warning(
        "No admission records are available."
    )
    st.stop()


for column in [
    "admission_timestamp",
    "discharge_timestamp",
    "admission_date",
    "discharge_date",
]:
    operations[column] = pd.to_datetime(
        operations[column],
        errors="coerce",
    )


operations[
    "length_of_stay"
] = pd.to_numeric(
    operations[
        "length_of_stay"
    ],
    errors="coerce",
).fillna(0)


for column in [
    "icu_flag",
    "readmission_flag",
    "emergency_flag",
]:
    operations[column] = (
        operations[column]
        .fillna(False)
        .astype(bool)
    )


for column in [
    "department_name",
    "department_type",
    "doctor_name",
    "specialization",
    "diagnosis_name",
    "diagnosis_category",
    "admission_type",
    "room_type",
    "outcome",
]:
    operations[column] = (
        operations[column]
        .fillna("Unknown")
        .astype(str)
    )


st.markdown(
    """
    <div class="h360-flow">
        <div class="h360-flow-title">
            How to read this dashboard
        </div>
        <div class="h360-flow-text">
            Start by defining the operating period and service scope.
            Review the hospital scorecard first, then follow patient flow
            over time. Continue into department workload, length of stay,
            emergency and ICU intensity, admission mix, demand timing and
            diagnosis demand. Finish with management review signals and the
            admission explorer for record-level investigation.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


page_section(
    "01",
    "Operations Scope",
    (
        "Define the admission period, departments and admission "
        "types used throughout this dashboard."
    ),
)


filtered = operations.copy()
valid_dates = filtered[
    "admission_date"
].dropna()

f1, f2, f3 = st.columns(3)


with f1:
    if not valid_dates.empty:
        minimum = valid_dates.min().date()
        maximum = valid_dates.max().date()

        period = st.date_input(
            "Admission Period",
            value=(
                minimum,
                maximum,
            ),
            min_value=minimum,
            max_value=maximum,
        )

    else:
        period = None


with f2:
    departments = sorted(
        filtered[
            "department_name"
        ].unique().tolist()
    )

    selected_departments = st.multiselect(
        "Department",
        departments,
        placeholder="All departments",
    )


with f3:
    admission_types = sorted(
        filtered[
            "admission_type"
        ].unique().tolist()
    )

    selected_types = st.multiselect(
        "Admission Type",
        admission_types,
        placeholder="All admission types",
    )


if (
    isinstance(
        period,
        (tuple, list),
    )
    and len(period) == 2
):
    start = pd.Timestamp(
        period[0]
    )

    end = (
        pd.Timestamp(
            period[1]
        )
        + pd.Timedelta(
            days=1
        )
    )

    filtered = filtered[
        (
            filtered[
                "admission_date"
            ]
            >= start
        )
        & (
            filtered[
                "admission_date"
            ]
            < end
        )
    ]


if selected_departments:
    filtered = filtered[
        filtered[
            "department_name"
        ].isin(
            selected_departments
        )
    ]


if selected_types:
    filtered = filtered[
        filtered[
            "admission_type"
        ].isin(
            selected_types
        )
    ]


if filtered.empty:
    st.warning(
        "No admissions match the current filters."
    )
    st.stop()


page_section(
    "02",
    "Hospital Operations Scorecard",
    (
        "Executive view of patient flow, inpatient demand "
        "and major operational indicators."
    ),
)


admissions = len(
    filtered
)

patients = filtered[
    "patient_id"
].nunique()

inpatient_days = int(
    filtered[
        "length_of_stay"
    ].sum()
)

avg_los = safe_number(
    filtered[
        "length_of_stay"
    ].mean()
)

emergency_count = int(
    filtered[
        "emergency_flag"
    ].sum()
)

icu_count = int(
    filtered[
        "icu_flag"
    ].sum()
)

readmission_count = int(
    filtered[
        "readmission_flag"
    ].sum()
)


metric_row(
    [
        (
            "Admissions",
            format_integer(
                admissions
            ),
        ),
        (
            "Unique Patients",
            format_integer(
                patients
            ),
        ),
        (
            "Inpatient Days",
            format_integer(
                inpatient_days
            ),
        ),
        (
            "Average LOS",
            f"{avg_los:.2f} days",
        ),
    ]
)


metric_row(
    [
        (
            "Emergency Admissions",
            format_integer(
                emergency_count
            ),
        ),
        (
            "Emergency Rate",
            format_percentage(
                pct(
                    emergency_count,
                    admissions,
                )
            ),
        ),
        (
            "ICU Admission Rate",
            format_percentage(
                pct(
                    icu_count,
                    admissions,
                )
            ),
        ),
        (
            "Readmission Rate",
            format_percentage(
                pct(
                    readmission_count,
                    admissions,
                )
            ),
        ),
    ]
)


management_insight(
    (
        f"The selected scope contains "
        f"{format_integer(admissions)} admissions across "
        f"{format_integer(patients)} unique patients, generating "
        f"{format_integer(inpatient_days)} inpatient days. "
        f"Average length of stay is {avg_los:.2f} days. "
        f"Emergency admissions account for "
        f"{format_percentage(pct(emergency_count, admissions))}, "
        f"ICU admissions for "
        f"{format_percentage(pct(icu_count, admissions))}, "
        f"and recorded readmissions for "
        f"{format_percentage(pct(readmission_count, admissions))}."
    ),
    label="Operations Management Snapshot",
)


page_section(
    "03",
    "Patient Flow Trend",
    (
        "Track how admission demand and key operational "
        "activity change over time."
    ),
)


daily = (
    filtered.groupby(
        "admission_date",
        as_index=False,
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
    )
    .sort_values(
        "admission_date"
    )
)


card_heading(
    "Daily Admissions",
    (
        "Shows day-by-day admission volume across "
        "the selected operating period."
    ),
)

fig = px.line(
    daily,
    x="admission_date",
    y="admissions",
    markers=True,
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
        unified_hover=True,
    ),
    width="stretch",
)

explanation_box(
    "What this chart tells you",
    (
        "Peaks represent days with higher admission demand, "
        "while lower points indicate quieter admission periods."
    ),
)


monthly = filtered.copy()

monthly[
    "month_start"
] = (
    monthly[
        "admission_date"
    ]
    .dt.to_period("M")
    .dt.to_timestamp()
)


monthly = (
    monthly.groupby(
        "month_start",
        as_index=False,
    )
    .agg(
        admissions=(
            "admission_id",
            "count",
        ),
        emergency=(
            "emergency_flag",
            "sum",
        ),
        icu=(
            "icu_flag",
            "sum",
        ),
        readmissions=(
            "readmission_flag",
            "sum",
        ),
    )
)


monthly_long = monthly.melt(
    id_vars="month_start",
    value_vars=[
        "admissions",
        "emergency",
        "icu",
        "readmissions",
    ],
    var_name="Activity",
    value_name="Admissions",
)


monthly_long[
    "Activity"
] = monthly_long[
    "Activity"
].map(
    {
        "admissions":
            "Total Admissions",
        "emergency":
            "Emergency Admissions",
        "icu":
            "ICU Admissions",
        "readmissions":
            "Readmissions",
    }
)


card_heading(
    "Monthly Operational Activity",
    (
        "Compares total admissions with emergency, ICU "
        "and readmission activity by month."
    ),
)

fig = px.line(
    monthly_long,
    x="month_start",
    y="Admissions",
    color="Activity",
    markers=True,
)

fig.update_xaxes(
    title=None
)

st.plotly_chart(
    style_figure(
        fig,
        410,
        unified_hover=True,
    ),
    width="stretch",
)

explanation_box(
    "What this chart tells you",
    (
        "Use this view to compare overall admission volume "
        "with emergency, ICU and readmission activity across time."
    ),
)


page_section(
    "04",
    "Department Operations",
    (
        "Compare department workload, patient volume, inpatient "
        "days and operational intensity."
    ),
)


department = (
    filtered.groupby(
        [
            "department_name",
            "department_type",
            "floor_number",
            "bed_capacity",
        ],
        dropna=False,
        as_index=False,
    )
    .agg(
        admissions=(
            "admission_id",
            "count",
        ),
        patients=(
            "patient_id",
            "nunique",
        ),
        inpatient_days=(
            "length_of_stay",
            "sum",
        ),
        average_los=(
            "length_of_stay",
            "mean",
        ),
        emergency=(
            "emergency_flag",
            "sum",
        ),
        icu=(
            "icu_flag",
            "sum",
        ),
        readmissions=(
            "readmission_flag",
            "sum",
        ),
    )
)


department[
    "emergency_rate_pct"
] = department.apply(
    lambda row: pct(
        row["emergency"],
        row["admissions"],
    ),
    axis=1,
)


department[
    "icu_rate_pct"
] = department.apply(
    lambda row: pct(
        row["icu"],
        row["admissions"],
    ),
    axis=1,
)


department[
    "readmission_rate_pct"
] = department.apply(
    lambda row: pct(
        row["readmissions"],
        row["admissions"],
    ),
    axis=1,
)


left, right = st.columns(2)


with left:
    card_heading(
        "Admissions by Department",
        (
            "Ranks departments according to the number "
            "of admissions in the selected scope."
        ),
    )

    chart = department.sort_values(
        "admissions",
        ascending=True,
    )

    fig = px.bar(
        chart,
        x="admissions",
        y="department_name",
        orientation="h",
        text_auto=True,
    )

    fig.update_yaxes(
        title=None
    )

    fig.update_xaxes(
        title="Admissions"
    )

    st.plotly_chart(
        style_figure(
            fig,
            430,
        ),
        width="stretch",
    )

    explanation_box(
        "What this chart tells you",
        (
            "Departments with longer bars handle larger "
            "admission volumes in the selected period."
        ),
    )


with right:
    card_heading(
        "Inpatient Days by Department",
        (
            "Compares total recorded inpatient days "
            "generated by each department."
        ),
    )

    chart = department.sort_values(
        "inpatient_days",
        ascending=True,
    )

    fig = px.bar(
        chart,
        x="inpatient_days",
        y="department_name",
        orientation="h",
        text_auto=True,
    )

    fig.update_yaxes(
        title=None
    )

    fig.update_xaxes(
        title="Inpatient Days"
    )

    st.plotly_chart(
        style_figure(
            fig,
            430,
        ),
        width="stretch",
    )

    explanation_box(
        "What this chart tells you",
        (
            "A department may have moderate admission volume "
            "but still generate high inpatient demand when stays "
            "are longer."
        ),
    )


department_display = department.rename(
    columns={
        "department_name":
            "Department",
        "department_type":
            "Type",
        "floor_number":
            "Floor",
        "bed_capacity":
            "Bed Capacity",
        "admissions":
            "Admissions",
        "patients":
            "Patients",
        "inpatient_days":
            "Inpatient Days",
        "average_los":
            "Average LOS",
        "emergency_rate_pct":
            "Emergency Rate %",
        "icu_rate_pct":
            "ICU Rate %",
        "readmission_rate_pct":
            "Readmission Rate %",
    }
)


card_heading(
    "Department Performance Table",
    (
        "Detailed operational comparison of workload, "
        "length of stay and major admission indicators."
    ),
)

dataframe(
    department_display,
    height=390,
)

st.info(
    "Bed Capacity is shown as department reference data. "
    "This dashboard does not calculate occupancy because the "
    "current dataset does not contain a validated point-in-time "
    "census or bed-day occupancy methodology."
)


page_section(
    "05",
    "Length-of-Stay Intelligence",
    (
        "Understand the distribution of inpatient stay duration "
        "and identify departments associated with longer stays."
    ),
)


def los_band(value):
    value = safe_number(
        value
    )

    if value <= 1:
        return "0–1 Day"

    if value <= 3:
        return "2–3 Days"

    if value <= 7:
        return "4–7 Days"

    if value <= 10:
        return "8–10 Days"

    return "Above 10 Days"


los_data = filtered.copy()

los_data[
    "LOS Band"
] = (
    los_data[
        "length_of_stay"
    ]
    .apply(
        los_band
    )
)


los_order = [
    "0–1 Day",
    "2–3 Days",
    "4–7 Days",
    "8–10 Days",
    "Above 10 Days",
]


los_summary = (
    los_data[
        "LOS Band"
    ]
    .value_counts()
    .reindex(
        los_order,
        fill_value=0,
    )
    .rename_axis(
        "LOS Band"
    )
    .reset_index(
        name="Admissions"
    )
)


left, right = st.columns(2)


with left:
    card_heading(
        "Length-of-Stay Distribution",
        (
            "Groups admissions according to their "
            "recorded stay duration."
        ),
    )

    fig = px.bar(
        los_summary,
        x="LOS Band",
        y="Admissions",
        text_auto=True,
    )

    fig.update_xaxes(
        title=None
    )

    st.plotly_chart(
        style_figure(
            fig,
            390,
        ),
        width="stretch",
    )

    explanation_box(
        "What this chart tells you",
        (
            "This distribution separates short stays from "
            "longer inpatient episodes and helps reveal the "
            "overall stay-duration profile."
        ),
    )


with right:
    card_heading(
        "Average LOS by Department",
        (
            "Compares the average recorded length of stay "
            "across hospital departments."
        ),
    )

    dept_los = (
        filtered.groupby(
            "department_name",
            as_index=False,
        )
        .agg(
            average_los=(
                "length_of_stay",
                "mean",
            )
        )
        .sort_values(
            "average_los",
            ascending=True,
        )
    )

    fig = px.bar(
        dept_los,
        x="average_los",
        y="department_name",
        orientation="h",
        text_auto=True,
    )

    fig.update_yaxes(
        title=None
    )

    fig.update_xaxes(
        title="Average LOS (Days)"
    )

    st.plotly_chart(
        style_figure(
            fig,
            390,
        ),
        width="stretch",
    )

    explanation_box(
        "What this chart tells you",
        (
            "Departments farther to the right have higher "
            "average recorded lengths of stay in the selected scope."
        ),
    )


page_section(
    "06",
    "Operational Intensity",
    (
        "Compare emergency, ICU and readmission shares "
        "across hospital departments."
    ),
)


intensity = department[
    [
        "department_name",
        "emergency_rate_pct",
        "icu_rate_pct",
        "readmission_rate_pct",
    ]
].melt(
    id_vars="department_name",
    var_name="Indicator",
    value_name="Rate",
)


intensity[
    "Indicator"
] = intensity[
    "Indicator"
].map(
    {
        "emergency_rate_pct":
            "Emergency Rate",
        "icu_rate_pct":
            "ICU Rate",
        "readmission_rate_pct":
            "Readmission Rate",
    }
)


card_heading(
    "Operational Intensity by Department",
    (
        "Places three major operational rates side by side "
        "for department-level comparison."
    ),
)

fig = px.bar(
    intensity,
    x="department_name",
    y="Rate",
    color="Indicator",
    barmode="group",
)

fig.update_xaxes(
    title=None
)

fig.update_yaxes(
    title="Rate (%)"
)

st.plotly_chart(
    style_figure(
        fig,
        440,
    ),
    width="stretch",
)

explanation_box(
    "How to interpret this view",
    (
        "A high rate does not automatically mean poor performance. "
        "Department case mix, specialization and patient complexity "
        "can materially affect emergency, ICU and readmission shares."
    ),
)


page_section(
    "07",
    "Admission & Room Mix",
    (
        "Understand how hospital activity is distributed "
        "across admission types, room types and outcomes."
    ),
)


c1, c2, c3 = st.columns(3)


with c1:
    card_heading(
        "Admission Type",
        (
            "Distribution of admissions across the "
            "recorded admission categories."
        ),
    )

    admission_mix = (
        filtered[
            "admission_type"
        ]
        .value_counts()
        .rename_axis(
            "Admission Type"
        )
        .reset_index(
            name="Admissions"
        )
    )

    fig = px.pie(
        admission_mix,
        names="Admission Type",
        values="Admissions",
        hole=0.5,
    )

    st.plotly_chart(
        style_figure(
            fig,
            350,
        ),
        width="stretch",
    )


with c2:
    card_heading(
        "Room Type",
        (
            "Distribution of admissions according to "
            "the recorded room category."
        ),
    )

    room_mix = (
        filtered[
            "room_type"
        ]
        .value_counts()
        .rename_axis(
            "Room Type"
        )
        .reset_index(
            name="Admissions"
        )
    )

    fig = px.pie(
        room_mix,
        names="Room Type",
        values="Admissions",
        hole=0.5,
    )

    st.plotly_chart(
        style_figure(
            fig,
            350,
        ),
        width="stretch",
    )


with c3:
    card_heading(
        "Admission Outcome",
        (
            "Distribution of recorded outcomes associated "
            "with admission events."
        ),
    )

    outcomes = (
        filtered[
            "outcome"
        ]
        .value_counts()
        .rename_axis(
            "Outcome"
        )
        .reset_index(
            name="Admissions"
        )
    )

    fig = px.pie(
        outcomes,
        names="Outcome",
        values="Admissions",
        hole=0.5,
    )

    st.plotly_chart(
        style_figure(
            fig,
            350,
        ),
        width="stretch",
    )


explanation_box(
    "What these charts tell you",
    (
        "Together these views describe the composition of hospital "
        "activity: how patients enter the hospital, which room types "
        "are recorded and how admission episodes are categorized "
        "by outcome."
    ),
)


page_section(
    "08",
    "Demand Patterns",
    (
        "Identify when admission demand occurs by weekday "
        "and hour of arrival."
    ),
)


demand = filtered.copy()

demand[
    "Weekday"
] = demand[
    "admission_timestamp"
].dt.day_name()

demand[
    "Admission Hour"
] = demand[
    "admission_timestamp"
].dt.hour


weekday_order = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


weekday = (
    demand[
        "Weekday"
    ]
    .value_counts()
    .reindex(
        weekday_order,
        fill_value=0,
    )
    .rename_axis(
        "Weekday"
    )
    .reset_index(
        name="Admissions"
    )
)


hourly = (
    demand.groupby(
        "Admission Hour",
        as_index=False,
    )
    .agg(
        Admissions=(
            "admission_id",
            "count",
        )
    )
)


left, right = st.columns(2)


with left:
    card_heading(
        "Admissions by Weekday",
        (
            "Shows how admission volume is distributed "
            "across the days of the week."
        ),
    )

    fig = px.bar(
        weekday,
        x="Weekday",
        y="Admissions",
        text_auto=True,
    )

    fig.update_xaxes(
        title=None
    )

    st.plotly_chart(
        style_figure(
            fig,
            390,
        ),
        width="stretch",
    )

    explanation_box(
        "What this chart tells you",
        (
            "Use weekday patterns to identify comparatively "
            "busier and quieter admission days."
        ),
    )


with right:
    card_heading(
        "Admissions by Hour",
        (
            "Shows admission arrivals according to "
            "the recorded hour of admission."
        ),
    )

    fig = px.line(
        hourly,
        x="Admission Hour",
        y="Admissions",
        markers=True,
    )

    fig.update_xaxes(
        dtick=1
    )

    st.plotly_chart(
        style_figure(
            fig,
            390,
        ),
        width="stretch",
    )

    explanation_box(
        "What this chart tells you",
        (
            "Hourly peaks identify times when admission "
            "arrival demand is comparatively higher."
        ),
    )


page_section(
    "09",
    "Diagnosis Demand",
    (
        "Identify the diagnosis categories and recorded "
        "diagnoses most frequently associated with admissions."
    ),
)


left, right = st.columns(2)


with left:
    card_heading(
        "Diagnosis Categories",
        (
            "Ranks the leading diagnosis categories "
            "associated with admission events."
        ),
    )

    categories = (
        filtered[
            "diagnosis_category"
        ]
        .value_counts()
        .head(12)
        .rename_axis(
            "Diagnosis Category"
        )
        .reset_index(
            name="Admissions"
        )
    )

    fig = px.bar(
        categories.sort_values(
            "Admissions"
        ),
        x="Admissions",
        y="Diagnosis Category",
        orientation="h",
        text_auto=True,
    )

    fig.update_yaxes(
        title=None
    )

    st.plotly_chart(
        style_figure(
            fig,
            420,
        ),
        width="stretch",
    )

    explanation_box(
        "What this chart tells you",
        (
            "This view identifies the diagnosis categories "
            "most frequently represented in admission records."
        ),
    )


with right:
    card_heading(
        "Top Diagnoses",
        (
            "Ranks individual recorded diagnoses by "
            "their associated admission volume."
        ),
    )

    diagnoses = (
        filtered[
            "diagnosis_name"
        ]
        .value_counts()
        .head(12)
        .rename_axis(
            "Diagnosis"
        )
        .reset_index(
            name="Admissions"
        )
    )

    fig = px.bar(
        diagnoses.sort_values(
            "Admissions"
        ),
        x="Admissions",
        y="Diagnosis",
        orientation="h",
        text_auto=True,
    )

    fig.update_yaxes(
        title=None
    )

    st.plotly_chart(
        style_figure(
            fig,
            420,
        ),
        width="stretch",
    )

    explanation_box(
        "What this chart tells you",
        (
            "The ranking shows diagnoses most commonly "
            "associated with admissions in the selected scope. "
            "It is not a population prevalence estimate."
        ),
    )


page_section(
    "10",
    "Operational Review Signals",
    (
        "Deterministic observations that highlight areas "
        "for management investigation."
    ),
)


signals = []


if not department.empty:
    row = department.sort_values(
        "admissions",
        ascending=False,
    ).iloc[0]

    signals.append(
        {
            "Signal":
                "Highest Admission Volume",
            "Department":
                row["department_name"],
            "Value":
                format_integer(
                    row["admissions"]
                ),
            "Management Context":
                "Largest observed admission workload.",
        }
    )


    row = department.sort_values(
        "inpatient_days",
        ascending=False,
    ).iloc[0]

    signals.append(
        {
            "Signal":
                "Highest Inpatient-Day Demand",
            "Department":
                row["department_name"],
            "Value":
                format_integer(
                    row["inpatient_days"]
                ),
            "Management Context":
                "Largest recorded inpatient-day workload.",
        }
    )


    row = department.sort_values(
        "average_los",
        ascending=False,
    ).iloc[0]

    signals.append(
        {
            "Signal":
                "Highest Average LOS",
            "Department":
                row["department_name"],
            "Value":
                f"{row['average_los']:.2f} days",
            "Management Context":
                "Largest observed average length of stay.",
        }
    )


    row = department.sort_values(
        "emergency_rate_pct",
        ascending=False,
    ).iloc[0]

    signals.append(
        {
            "Signal":
                "Highest Emergency Share",
            "Department":
                row["department_name"],
            "Value":
                format_percentage(
                    row[
                        "emergency_rate_pct"
                    ]
                ),
            "Management Context":
                "Largest emergency-admission share.",
        }
    )


    row = department.sort_values(
        "icu_rate_pct",
        ascending=False,
    ).iloc[0]

    signals.append(
        {
            "Signal":
                "Highest ICU Share",
            "Department":
                row["department_name"],
            "Value":
                format_percentage(
                    row[
                        "icu_rate_pct"
                    ]
                ),
            "Management Context":
                "Largest ICU-admission share.",
        }
    )


    row = department.sort_values(
        "readmission_rate_pct",
        ascending=False,
    ).iloc[0]

    signals.append(
        {
            "Signal":
                "Highest Readmission Share",
            "Department":
                row["department_name"],
            "Value":
                format_percentage(
                    row[
                        "readmission_rate_pct"
                    ]
                ),
            "Management Context":
                "Largest observed readmission share.",
        }
    )


if signals:
    dataframe(
        pd.DataFrame(
            signals
        ),
        height=330,
    )


explanation_box(
    "How to interpret these signals",
    (
        "These observations identify the highest values within "
        "the current filter scope. They are investigation prompts, "
        "not automatic judgments of department quality or clinical "
        "performance."
    ),
)


page_section(
    "11",
    "Admission Explorer",
    (
        "Search and inspect individual admission records "
        "and operational indicators."
    ),
)


search_col, signal_col = st.columns(
    [2, 1]
)


with search_col:
    search = st.text_input(
        "Search Admission / Patient / Doctor",
        placeholder=(
            "Enter an admission ID, patient ID "
            "or doctor name..."
        ),
    )


with signal_col:
    signal_filter = st.selectbox(
        "Operational Signal",
        [
            "All",
            "Emergency",
            "ICU",
            "Readmission",
            "LOS > 10 Days",
        ],
    )


explorer = filtered.copy()


if search.strip():
    query = search.strip().lower()

    explorer = explorer[
        explorer[
            "admission_id"
        ]
        .astype(str)
        .str.lower()
        .str.contains(
            query,
            na=False,
        )
        |
        explorer[
            "patient_id"
        ]
        .astype(str)
        .str.lower()
        .str.contains(
            query,
            na=False,
        )
        |
        explorer[
            "doctor_name"
        ]
        .astype(str)
        .str.lower()
        .str.contains(
            query,
            na=False,
        )
    ]


if signal_filter == "Emergency":
    explorer = explorer[
        explorer[
            "emergency_flag"
        ]
    ]

elif signal_filter == "ICU":
    explorer = explorer[
        explorer[
            "icu_flag"
        ]
    ]

elif signal_filter == "Readmission":
    explorer = explorer[
        explorer[
            "readmission_flag"
        ]
    ]

elif signal_filter == "LOS > 10 Days":
    explorer = explorer[
        explorer[
            "length_of_stay"
        ] > 10
    ]


explorer = explorer.sort_values(
    "admission_timestamp",
    ascending=False,
)


display_columns = [
    "admission_id",
    "patient_id",
    "admission_timestamp",
    "discharge_timestamp",
    "department_name",
    "doctor_name",
    "diagnosis_name",
    "admission_type",
    "room_type",
    "bed_number",
    "length_of_stay",
    "emergency_flag",
    "icu_flag",
    "readmission_flag",
    "outcome",
]


explorer_display = explorer[
    display_columns
].rename(
    columns={
        "admission_id":
            "Admission ID",
        "patient_id":
            "Patient ID",
        "admission_timestamp":
            "Admitted",
        "discharge_timestamp":
            "Discharged",
        "department_name":
            "Department",
        "doctor_name":
            "Doctor",
        "diagnosis_name":
            "Diagnosis",
        "admission_type":
            "Admission Type",
        "room_type":
            "Room Type",
        "bed_number":
            "Bed",
        "length_of_stay":
            "LOS",
        "emergency_flag":
            "Emergency",
        "icu_flag":
            "ICU",
        "readmission_flag":
            "Readmission",
        "outcome":
            "Outcome",
    }
)


dataframe(
    explorer_display,
    height=500,
)

st.caption(
    f"Showing "
    f"{format_integer(len(explorer_display))} "
    f"admission records."
)


page_section(
    "12",
    "Continue the Analysis",
    (
        "Follow the Hospital 360 analysis flow into finance, "
        "risk or claims performance."
    ),
)


nav1, nav2, nav3 = st.columns(3)


with nav1:
    card_heading(
        "Finance Analytics",
        (
            "Move from operational activity into billing, "
            "collections and outstanding financial exposure."
        ),
    )

    st.page_link(
        "pages/04_Finance_Analytics_Dashboard.py",
        label="Open Finance Analytics",
        icon="💰",
        width="stretch",
    )


with nav2:
    card_heading(
        "Risk Analytics",
        (
            "Review operational, financial and patient-level "
            "risk indicators."
        ),
    )

    st.page_link(
        "pages/05_Risk_Analytics_Dashboard.py",
        label="Open Risk Analytics",
        icon="⚠️",
        width="stretch",
    )


with nav3:
    card_heading(
        "Claims Analytics",
        (
            "Continue into insurer, claim-status and rejection "
            "performance analysis."
        ),
    )

    st.page_link(
        "pages/06_Claims_Analytics_Dashboard.py",
        label="Open Claims Analytics",
        icon="🧾",
        width="stretch",
    )


with st.expander(
    "Technical Data Diagnostics",
    expanded=False,
):
    diagnostics = pd.DataFrame(
        [
            {
                "Dataset":
                    "Admission Operations",
                "Rows":
                    len(operations),
                "Filtered Rows":
                    len(filtered),
                "Available Fields":
                    ", ".join(
                        operations.columns.tolist()
                    ),
            }
        ]
    )

    dataframe(
        diagnostics,
        height=180,
    )


st.divider()

footer_left, footer_right = st.columns(
    [4, 1]
)


with footer_left:
    st.caption(
        "Operations Analytics · Hospital 360 synthetic healthcare "
        "data. Operational indicators support management analysis "
        "and are not clinical recommendations. Centralized report "
        "generation and downloads are managed from the Admin "
        "Control Center."
    )


with footer_right:
    render_refresh_button(
        key="operations_refresh",
    )