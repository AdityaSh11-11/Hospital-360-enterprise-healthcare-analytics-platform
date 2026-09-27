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
)


# ============================================================
# PAGE
# ============================================================

bootstrap_page(
    title="Patient Analytics",
    subtitle=(
        "Patient 360 intelligence for population structure, "
        "utilization, admission behavior, service demand and "
        "patient-linked financial exposure."
    ),
    icon="👥",
)


# ============================================================
# HELPERS
# ============================================================

def first_existing(
    dataframe_result: pd.DataFrame,
    candidates: list[str],
) -> str | None:
    if dataframe_result is None or dataframe_result.empty:
        return None

    for column in candidates:
        if column in dataframe_result.columns:
            return column

    return None


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


def safe_int(
    value: Any,
    default: int = 0,
) -> int:
    try:
        if value is None:
            return default

        if pd.isna(value):
            return default

        return int(value)

    except (TypeError, ValueError):
        return default


def format_days(
    value: Any,
) -> str:
    if value is None:
        return "—"

    try:
        if pd.isna(value):
            return "—"
    except (TypeError, ValueError):
        pass

    return f"{safe_float(value):,.2f} days"


def format_date(
    value: Any,
) -> str:
    if value is None:
        return "—"

    try:
        if pd.isna(value):
            return "—"
    except (TypeError, ValueError):
        pass

    try:
        return pd.to_datetime(
            value
        ).strftime(
            "%d %b %Y"
        )

    except Exception:
        return str(value)


def clean_label(
    value: Any,
) -> str:
    return (
        str(value)
        .replace("_", " ")
        .strip()
        .title()
    )


def style_figure(
    figure: go.Figure,
    *,
    height: int = 380,
    unified_hover: bool = False,
) -> go.Figure:
    figure.update_layout(
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
        figure.update_layout(
            hovermode="x unified",
        )

    return figure


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
                <div class="h360-section-description">
                    {description}
                </div>
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
            <div class="h360-card-description">
                {description}
            </div>
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


# ============================================================
# LOCAL PAGE STYLING
# ============================================================

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

    .stAlert {
        border-radius: 14px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# DATA LOADERS
# ============================================================

@st.cache_data(
    ttl=60,
    show_spinner=False,
)
def load_patient_master() -> pd.DataFrame:
    return read_sql(
        """
        SELECT
            patient_id,
            first_name,
            last_name,
            gender,
            date_of_birth,
            blood_group,
            city,
            state,
            insurance_status,
            chronic_condition,
            registration_date,
            is_active
        FROM warehouse.dim_patient
        """
    )


@st.cache_data(
    ttl=60,
    show_spinner=False,
)
def load_patient_utilization() -> pd.DataFrame:
    return read_sql(
        """
        SELECT *
        FROM analytics.vw_patient_utilization
        """
    )


@st.cache_data(
    ttl=60,
    show_spinner=False,
)
def load_admission_history() -> pd.DataFrame:
    return read_sql(
        """
        SELECT
            a.admission_id,
            p.patient_id,
            p.first_name,
            p.last_name,
            d.full_date AS admission_date,
            a.admission_timestamp,
            a.discharge_timestamp,
            a.admission_type,
            a.length_of_stay,
            a.icu_flag,
            a.readmission_flag,
            a.emergency_flag,
            a.outcome,
            dep.department_name,
            doc.doctor_name,
            dx.diagnosis_name
        FROM warehouse.fact_admission a

        INNER JOIN warehouse.dim_patient p
            ON p.patient_key = a.patient_key

        LEFT JOIN warehouse.dim_date d
            ON d.date_key = a.admission_date_key

        LEFT JOIN warehouse.dim_department dep
            ON dep.department_key = a.department_key

        LEFT JOIN warehouse.dim_doctor doc
            ON doc.doctor_key = a.doctor_key

        LEFT JOIN warehouse.dim_diagnosis dx
            ON dx.diagnosis_key = a.diagnosis_key
        """
    )


@st.cache_data(
    ttl=60,
    show_spinner=False,
)
def load_patient_financials() -> pd.DataFrame:
    return read_sql(
        """
        SELECT
            p.patient_id,
            COUNT(*)::bigint AS bill_count,
            COALESCE(
                SUM(b.net_amount),
                0
            ) AS net_billed_amount,
            COALESCE(
                SUM(b.paid_amount),
                0
            ) AS paid_amount,
            COALESCE(
                SUM(b.outstanding_amount),
                0
            ) AS outstanding_amount
        FROM warehouse.fact_billing b

        INNER JOIN warehouse.dim_patient p
            ON p.patient_key = b.patient_key

        GROUP BY
            p.patient_id
        """
    )


# ============================================================
# LOAD DATA
# ============================================================

try:
    patients = load_patient_master()
    utilization = load_patient_utilization()
    admissions = load_admission_history()
    financials = load_patient_financials()

except Exception as exc:
    st.error(
        "Patient Analytics could not load the required "
        "warehouse datasets."
    )
    st.exception(exc)
    st.stop()


# ============================================================
# PREPARE DATA
# ============================================================

patients = patients.copy()
admissions = admissions.copy()
financials = financials.copy()

patients["date_of_birth"] = pd.to_datetime(
    patients["date_of_birth"],
    errors="coerce",
)

patients["registration_date"] = pd.to_datetime(
    patients["registration_date"],
    errors="coerce",
)

if "admission_timestamp" in admissions.columns:
    admissions["admission_timestamp"] = pd.to_datetime(
        admissions["admission_timestamp"],
        errors="coerce",
    )

if "discharge_timestamp" in admissions.columns:
    admissions["discharge_timestamp"] = pd.to_datetime(
        admissions["discharge_timestamp"],
        errors="coerce",
    )


reference_date_candidates: list[pd.Timestamp] = []

if (
    not admissions.empty
    and "admission_timestamp" in admissions.columns
):
    max_admission = admissions[
        "admission_timestamp"
    ].max()

    if pd.notna(max_admission):
        reference_date_candidates.append(
            max_admission
        )


if (
    not patients.empty
    and "registration_date" in patients.columns
):
    max_registration = patients[
        "registration_date"
    ].max()

    if pd.notna(max_registration):
        reference_date_candidates.append(
            max_registration
        )


reference_date = (
    max(reference_date_candidates)
    if reference_date_candidates
    else pd.Timestamp.today()
)


patients["age"] = (
    (
        reference_date
        - patients["date_of_birth"]
    ).dt.days
    / 365.2425
).floordiv(1)

patients.loc[
    patients["age"] < 0,
    "age",
] = pd.NA


patients["age_band"] = pd.cut(
    patients["age"],
    bins=[
        -1,
        17,
        30,
        45,
        60,
        70,
        200,
    ],
    labels=[
        "0-17",
        "18-30",
        "31-45",
        "46-60",
        "61-70",
        "71+",
    ],
)


patients["patient_name"] = (
    patients["first_name"].fillna("")
    + " "
    + patients["last_name"].fillna("")
).str.strip()


# ============================================================
# PAGE GUIDE
# ============================================================

st.markdown(
    """
    <div class="h360-flow">
        <div class="h360-flow-title">
            How to read this dashboard
        </div>
        <div class="h360-flow-text">
            Define the patient cohort first. Then review the population
            scorecard, demographic and geographic composition, insurance
            and chronic-condition profile, utilization behavior and service
            demand. Finish with the high-utilization register and Patient 360
            drill-down for individual patient context.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 01 FILTERS
# ============================================================

page_section(
    "01",
    "Patient Cohort",
    (
        "Define the registered patient population used throughout "
        "the dashboard."
    ),
)

filter1, filter2, filter3, filter4 = st.columns(4)


gender_options = sorted(
    patients["gender"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)

state_options = sorted(
    patients["state"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)

insurance_options = sorted(
    patients["insurance_status"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)

chronic_options = sorted(
    patients["chronic_condition"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)


with filter1:
    selected_genders = st.multiselect(
        "Gender",
        options=gender_options,
        default=gender_options,
    )


with filter2:
    selected_states = st.multiselect(
        "State",
        options=state_options,
        default=state_options,
    )


with filter3:
    selected_insurance = st.multiselect(
        "Insurance Status",
        options=insurance_options,
        default=insurance_options,
    )


with filter4:
    selected_chronic = st.multiselect(
        "Chronic Condition",
        options=chronic_options,
        default=chronic_options,
    )


filtered_patients = patients.copy()

if gender_options:
    filtered_patients = filtered_patients[
        filtered_patients[
            "gender"
        ].astype(str).isin(
            selected_genders
        )
    ]

if state_options:
    filtered_patients = filtered_patients[
        filtered_patients[
            "state"
        ].astype(str).isin(
            selected_states
        )
    ]

if insurance_options:
    filtered_patients = filtered_patients[
        filtered_patients[
            "insurance_status"
        ].astype(str).isin(
            selected_insurance
        )
    ]

if chronic_options:
    filtered_patients = filtered_patients[
        filtered_patients[
            "chronic_condition"
        ].astype(str).isin(
            selected_chronic
        )
    ]


selected_patient_ids = set(
    filtered_patients[
        "patient_id"
    ].astype(str)
)


filtered_utilization = (
    utilization[
        utilization[
            "patient_id"
        ].astype(str).isin(
            selected_patient_ids
        )
    ].copy()
    if (
        not utilization.empty
        and "patient_id" in utilization.columns
    )
    else utilization.copy()
)


filtered_admissions = (
    admissions[
        admissions[
            "patient_id"
        ].astype(str).isin(
            selected_patient_ids
        )
    ].copy()
    if (
        not admissions.empty
        and "patient_id" in admissions.columns
    )
    else admissions.copy()
)


filtered_financials = (
    financials[
        financials[
            "patient_id"
        ].astype(str).isin(
            selected_patient_ids
        )
    ].copy()
    if not financials.empty
    else financials.copy()
)


# ============================================================
# 02 SCORECARD
# ============================================================

page_section(
    "02",
    "Patient Scorecard",
    (
        "Core population, utilization and financial indicators "
        "for the selected patient cohort."
    ),
)


patient_count = len(
    filtered_patients
)

admitted_patient_count = (
    filtered_admissions[
        "patient_id"
    ].nunique()
    if not filtered_admissions.empty
    else 0
)

admission_count = len(
    filtered_admissions
)

average_age = (
    pd.to_numeric(
        filtered_patients["age"],
        errors="coerce",
    ).mean()
    if not filtered_patients.empty
    else None
)


readmission_count = (
    pd.to_numeric(
        filtered_admissions[
            "readmission_flag"
        ],
        errors="coerce",
    ).fillna(0).sum()
    if (
        not filtered_admissions.empty
        and "readmission_flag"
        in filtered_admissions.columns
    )
    else 0
)


icu_count = (
    pd.to_numeric(
        filtered_admissions[
            "icu_flag"
        ],
        errors="coerce",
    ).fillna(0).sum()
    if (
        not filtered_admissions.empty
        and "icu_flag"
        in filtered_admissions.columns
    )
    else 0
)


emergency_count = (
    pd.to_numeric(
        filtered_admissions[
            "emergency_flag"
        ],
        errors="coerce",
    ).fillna(0).sum()
    if (
        not filtered_admissions.empty
        and "emergency_flag"
        in filtered_admissions.columns
    )
    else 0
)


average_los = (
    pd.to_numeric(
        filtered_admissions[
            "length_of_stay"
        ],
        errors="coerce",
    ).mean()
    if (
        not filtered_admissions.empty
        and "length_of_stay"
        in filtered_admissions.columns
    )
    else None
)


readmission_rate = (
    readmission_count
    / admission_count
    * 100
    if admission_count
    else 0
)

icu_rate = (
    icu_count
    / admission_count
    * 100
    if admission_count
    else 0
)

emergency_rate = (
    emergency_count
    / admission_count
    * 100
    if admission_count
    else 0
)


total_outstanding = (
    pd.to_numeric(
        filtered_financials[
            "outstanding_amount"
        ],
        errors="coerce",
    ).fillna(0).sum()
    if (
        not filtered_financials.empty
        and "outstanding_amount"
        in filtered_financials.columns
    )
    else 0
)


metric_row(
    [
        (
            "Registered Patients",
            format_integer(
                patient_count
            ),
        ),
        (
            "Patients Admitted",
            format_integer(
                admitted_patient_count
            ),
        ),
        (
            "Admissions",
            format_integer(
                admission_count
            ),
        ),
        (
            "Average Age",
            (
                f"{average_age:,.1f} years"
                if pd.notna(average_age)
                else "—"
            ),
        ),
    ]
)


metric_row(
    [
        (
            "Average LOS",
            format_days(
                average_los
            ),
        ),
        (
            "Readmission Rate",
            format_percentage(
                readmission_rate
            ),
        ),
        (
            "Emergency Admission Rate",
            format_percentage(
                emergency_rate
            ),
        ),
        (
            "ICU Admission Rate",
            format_percentage(
                icu_rate
            ),
        ),
    ]
)


management_insight(
    (
        f"The selected cohort contains "
        f"{format_integer(patient_count)} registered patients "
        f"and {format_integer(admission_count)} recorded admissions. "
        f"Average length of stay is {format_days(average_los)}. "
        f"Readmissions represent "
        f"{format_percentage(readmission_rate)} of admissions, "
        f"while patient-linked outstanding billing exposure is "
        f"{format_currency_compact(total_outstanding)}."
    ),
    label="Patient Population Snapshot",
)


# ============================================================
# 03 DEMOGRAPHICS
# ============================================================

page_section(
    "03",
    "Demographic Profile",
    (
        "Understand the age and gender composition of the "
        "selected registered population."
    ),
)

demo_left, demo_right = st.columns(2)


with demo_left:
    card_heading(
        "Age Distribution",
        (
            "Shows how the selected patient population is "
            "distributed across age groups."
        ),
    )

    age_distribution = (
        filtered_patients["age_band"]
        .value_counts(
            sort=False
        )
        .rename_axis(
            "Age Band"
        )
        .reset_index(
            name="Patients"
        )
    )

    age_distribution = age_distribution[
        age_distribution[
            "Patients"
        ] > 0
    ]

    if not age_distribution.empty:
        fig = px.bar(
            age_distribution,
            x="Age Band",
            y="Patients",
            text_auto=True,
        )

        fig.update_xaxes(
            title=None
        )

        fig.update_yaxes(
            title="Patients"
        )

        st.plotly_chart(
            style_figure(
                fig,
                height=370,
            ),
            width="stretch",
        )

        explanation_box(
            "What this chart tells you",
            (
                "This view highlights which age bands account "
                "for the largest shares of the selected patient "
                "population."
            ),
        )

    else:
        st.info(
            "No age-distribution data is available "
            "for the selected cohort."
        )


with demo_right:
    card_heading(
        "Gender Mix",
        (
            "Shows the recorded gender composition of the "
            "selected patient population."
        ),
    )

    gender_distribution = (
        filtered_patients["gender"]
        .fillna("Unknown")
        .value_counts()
        .rename_axis(
            "Gender"
        )
        .reset_index(
            name="Patients"
        )
    )

    if not gender_distribution.empty:
        fig = px.pie(
            gender_distribution,
            names="Gender",
            values="Patients",
            hole=0.55,
        )

        st.plotly_chart(
            style_figure(
                fig,
                height=370,
            ),
            width="stretch",
        )

        explanation_box(
            "What this chart tells you",
            (
                "The chart provides a proportional view of the "
                "recorded gender categories represented in the "
                "current cohort."
            ),
        )

    else:
        st.info(
            "No gender data is available "
            "for the selected cohort."
        )


# ============================================================
# 04 GEOGRAPHY
# ============================================================

page_section(
    "04",
    "Patient Geography",
    (
        "Identify where registered patients are concentrated "
        "across the states and cities represented in the dataset."
    ),
)

geo_left, geo_right = st.columns(2)


with geo_left:
    card_heading(
        "Patients by State",
        (
            "Compares the size of the selected patient population "
            "across recorded states."
        ),
    )

    state_distribution = (
        filtered_patients["state"]
        .fillna("Unknown")
        .value_counts()
        .rename_axis(
            "State"
        )
        .reset_index(
            name="Patients"
        )
        .sort_values(
            "Patients",
            ascending=True,
        )
    )

    if not state_distribution.empty:
        fig = px.bar(
            state_distribution,
            x="Patients",
            y="State",
            orientation="h",
            text_auto=True,
        )

        fig.update_yaxes(
            title=None
        )

        st.plotly_chart(
            style_figure(
                fig,
                height=420,
            ),
            width="stretch",
        )

        explanation_box(
            "What this chart tells you",
            (
                "Longer bars identify states with larger numbers "
                "of registered patients in the selected cohort."
            ),
        )


with geo_right:
    card_heading(
        "Top Cities",
        (
            "Shows the leading cities represented in the "
            "selected registered population."
        ),
    )

    city_distribution = (
        filtered_patients["city"]
        .fillna("Unknown")
        .value_counts()
        .head(15)
        .rename_axis(
            "City"
        )
        .reset_index(
            name="Patients"
        )
        .sort_values(
            "Patients",
            ascending=True,
        )
    )

    if not city_distribution.empty:
        fig = px.bar(
            city_distribution,
            x="Patients",
            y="City",
            orientation="h",
            text_auto=True,
        )

        fig.update_yaxes(
            title=None
        )

        st.plotly_chart(
            style_figure(
                fig,
                height=420,
            ),
            width="stretch",
        )

        explanation_box(
            "What this chart tells you",
            (
                "This ranking highlights the cities that contribute "
                "the largest numbers of patients to the selected cohort."
            ),
        )


# ============================================================
# 05 COVERAGE & CHRONIC PROFILE
# ============================================================

page_section(
    "05",
    "Coverage & Chronic Condition Profile",
    (
        "Review patient-master insurance and chronic-condition "
        "attributes for the selected population."
    ),
)

profile_left, profile_right = st.columns(2)


with profile_left:
    card_heading(
        "Insurance Status",
        (
            "Shows the distribution of recorded insurance "
            "status across the selected patient population."
        ),
    )

    insurance_distribution = (
        filtered_patients[
            "insurance_status"
        ]
        .fillna("Unknown")
        .astype(str)
        .value_counts()
        .rename_axis(
            "Insurance Status"
        )
        .reset_index(
            name="Patients"
        )
    )

    if not insurance_distribution.empty:
        fig = px.pie(
            insurance_distribution,
            names="Insurance Status",
            values="Patients",
            hole=0.55,
        )

        st.plotly_chart(
            style_figure(
                fig,
                height=370,
            ),
            width="stretch",
        )

        explanation_box(
            "What this chart tells you",
            (
                "This view shows the relative mix of insurance "
                "statuses recorded for patients in the current cohort."
            ),
        )


with profile_right:
    card_heading(
        "Chronic Condition Profile",
        (
            "Shows the recorded chronic-condition categories "
            "within the selected patient population."
        ),
    )

    chronic_distribution = (
        filtered_patients[
            "chronic_condition"
        ]
        .fillna("Unknown")
        .astype(str)
        .value_counts()
        .rename_axis(
            "Chronic Condition"
        )
        .reset_index(
            name="Patients"
        )
    )

    if not chronic_distribution.empty:
        fig = px.pie(
            chronic_distribution,
            names="Chronic Condition",
            values="Patients",
            hole=0.55,
        )

        st.plotly_chart(
            style_figure(
                fig,
                height=370,
            ),
            width="stretch",
        )

        explanation_box(
            "What this chart tells you",
            (
                "The chart describes the chronic-condition attribute "
                "recorded in the patient master. It is descriptive "
                "population segmentation, not clinical assessment."
            ),
        )


# ============================================================
# 06 UTILIZATION
# ============================================================

page_section(
    "06",
    "Patient Utilization",
    (
        "Segment patients according to their recorded hospital "
        "admission frequency."
    ),
)


admission_frequency = (
    filtered_admissions.groupby(
        "patient_id",
        as_index=False,
    )
    .agg(
        admissions=(
            "admission_id",
            "count",
        ),
        total_inpatient_days=(
            "length_of_stay",
            "sum",
        ),
        average_los=(
            "length_of_stay",
            "mean",
        ),
        readmissions=(
            "readmission_flag",
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
    )
    if not filtered_admissions.empty
    else pd.DataFrame(
        columns=[
            "patient_id",
            "admissions",
            "total_inpatient_days",
            "average_los",
            "readmissions",
            "emergency_admissions",
            "icu_admissions",
        ]
    )
)


patient_utilization_base = (
    filtered_patients[
        [
            "patient_id",
            "patient_name",
            "gender",
            "age",
            "city",
            "state",
            "insurance_status",
            "chronic_condition",
        ]
    ]
    .merge(
        admission_frequency,
        on="patient_id",
        how="left",
    )
)


for column in [
    "admissions",
    "total_inpatient_days",
    "readmissions",
    "emergency_admissions",
    "icu_admissions",
]:
    if column in patient_utilization_base.columns:
        patient_utilization_base[
            column
        ] = (
            pd.to_numeric(
                patient_utilization_base[
                    column
                ],
                errors="coerce",
            )
            .fillna(0)
        )


patient_utilization_base[
    "utilization_segment"
] = pd.cut(
    patient_utilization_base[
        "admissions"
    ],
    bins=[
        -1,
        0,
        1,
        3,
        5,
        float("inf"),
    ],
    labels=[
        "No Admission",
        "Single Admission",
        "2-3 Admissions",
        "4-5 Admissions",
        "6+ Admissions",
    ],
)


segment_summary = (
    patient_utilization_base[
        "utilization_segment"
    ]
    .value_counts(
        sort=False
    )
    .rename_axis(
        "Utilization Segment"
    )
    .reset_index(
        name="Patients"
    )
)

segment_summary = segment_summary[
    segment_summary[
        "Patients"
    ] > 0
]


util_left, util_right = st.columns(
    [1.35, 0.65]
)


with util_left:
    card_heading(
        "Admission Frequency Segmentation",
        (
            "Groups patients by the number of recorded hospital "
            "admissions in the warehouse."
        ),
    )

    if not segment_summary.empty:
        fig = px.bar(
            segment_summary,
            x="Utilization Segment",
            y="Patients",
            text_auto=True,
        )

        fig.update_xaxes(
            title=None
        )

        st.plotly_chart(
            style_figure(
                fig,
                height=410,
            ),
            width="stretch",
        )

        explanation_box(
            "What this chart tells you",
            (
                "The distribution separates patients with no recorded "
                "admissions, one admission, repeat use and higher "
                "admission frequency."
            ),
        )


with util_right:
    card_heading(
        "Utilization Counts",
        (
            "Key counts derived from the same admission-frequency "
            "segmentation."
        ),
    )

    no_admission = int(
        (
            patient_utilization_base[
                "admissions"
            ]
            == 0
        ).sum()
    )

    single_admission = int(
        (
            patient_utilization_base[
                "admissions"
            ]
            == 1
        ).sum()
    )

    repeat_users = int(
        (
            patient_utilization_base[
                "admissions"
            ]
            >= 2
        ).sum()
    )

    high_utilizers = int(
        (
            patient_utilization_base[
                "admissions"
            ]
            >= 6
        ).sum()
    )

    st.metric(
        "No Admission",
        format_integer(
            no_admission
        ),
    )

    st.metric(
        "Single Admission",
        format_integer(
            single_admission
        ),
    )

    st.metric(
        "Repeat Users",
        format_integer(
            repeat_users
        ),
    )

    st.metric(
        "6+ Admission Patients",
        format_integer(
            high_utilizers
        ),
    )


# ============================================================
# 07 ADMISSION BEHAVIOR
# ============================================================

page_section(
    "07",
    "Admission Behavior",
    (
        "Understand how the selected patient cohort enters "
        "and exits hospital services."
    ),
)

behavior1, behavior2 = st.columns(2)


with behavior1:
    card_heading(
        "Admissions by Type",
        (
            "Compares the recorded admission types associated "
            "with the selected cohort."
        ),
    )

    admission_type_distribution = (
        filtered_admissions[
            "admission_type"
        ]
        .fillna("Unknown")
        .value_counts()
        .rename_axis(
            "Admission Type"
        )
        .reset_index(
            name="Admissions"
        )
        if not filtered_admissions.empty
        else pd.DataFrame()
    )

    if not admission_type_distribution.empty:
        fig = px.bar(
            admission_type_distribution,
            x="Admission Type",
            y="Admissions",
            text_auto=True,
        )

        fig.update_xaxes(
            title=None
        )

        st.plotly_chart(
            style_figure(
                fig,
                height=370,
            ),
            width="stretch",
        )

        explanation_box(
            "What this chart tells you",
            (
                "This comparison shows which recorded admission "
                "types account for the greatest share of hospital use."
            ),
        )


with behavior2:
    card_heading(
        "Recorded Admission Outcomes",
        (
            "Shows the proportional distribution of recorded "
            "outcomes for admissions in the selected cohort."
        ),
    )

    outcome_distribution = (
        filtered_admissions[
            "outcome"
        ]
        .fillna("Unknown")
        .value_counts()
        .rename_axis(
            "Outcome"
        )
        .reset_index(
            name="Admissions"
        )
        if not filtered_admissions.empty
        else pd.DataFrame()
    )

    if not outcome_distribution.empty:
        fig = px.pie(
            outcome_distribution,
            names="Outcome",
            values="Admissions",
            hole=0.50,
        )

        st.plotly_chart(
            style_figure(
                fig,
                height=370,
            ),
            width="stretch",
        )

        explanation_box(
            "What this chart tells you",
            (
                "The chart summarizes the outcomes recorded against "
                "admission events. It is descriptive of the synthetic "
                "warehouse data."
            ),
        )


# ============================================================
# 08 SERVICE UTILIZATION
# ============================================================

page_section(
    "08",
    "Service Utilization",
    (
        "Identify the departments and recorded diagnoses most "
        "frequently associated with patient admissions."
    ),
)

service_left, service_right = st.columns(2)


with service_left:
    card_heading(
        "Admissions by Department",
        (
            "Compares recorded patient admission workload "
            "across hospital departments."
        ),
    )

    department_distribution = (
        filtered_admissions[
            "department_name"
        ]
        .fillna("Unknown")
        .value_counts()
        .rename_axis(
            "Department"
        )
        .reset_index(
            name="Admissions"
        )
        .sort_values(
            "Admissions",
            ascending=True,
        )
        if not filtered_admissions.empty
        else pd.DataFrame()
    )

    if not department_distribution.empty:
        fig = px.bar(
            department_distribution,
            x="Admissions",
            y="Department",
            orientation="h",
            text_auto=True,
        )

        fig.update_yaxes(
            title=None
        )

        st.plotly_chart(
            style_figure(
                fig,
                height=430,
            ),
            width="stretch",
        )

        explanation_box(
            "What this chart tells you",
            (
                "Departments with longer bars account for more "
                "recorded admissions among patients in the current cohort."
            ),
        )


with service_right:
    card_heading(
        "Top Recorded Diagnoses",
        (
            "Ranks the most frequently recorded diagnoses "
            "associated with admissions."
        ),
    )

    diagnosis_distribution = (
        filtered_admissions[
            "diagnosis_name"
        ]
        .fillna("Unknown")
        .value_counts()
        .head(15)
        .rename_axis(
            "Diagnosis"
        )
        .reset_index(
            name="Admissions"
        )
        .sort_values(
            "Admissions",
            ascending=True,
        )
        if not filtered_admissions.empty
        else pd.DataFrame()
    )

    if not diagnosis_distribution.empty:
        fig = px.bar(
            diagnosis_distribution,
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
                height=430,
            ),
            width="stretch",
        )

        explanation_box(
            "What this chart tells you",
            (
                "This ranking identifies diagnoses most frequently "
                "represented in the selected cohort's admission records. "
                "It is not a prevalence estimate for the wider population."
            ),
        )


# ============================================================
# 09 HIGH UTILIZATION REGISTER
# ============================================================

page_section(
    "09",
    "High-Utilization Patient Register",
    (
        "Operational review of patients with repeated hospital use "
        "and associated patient-linked billing exposure."
    ),
)


patient_register = (
    patient_utilization_base.merge(
        filtered_financials,
        on="patient_id",
        how="left",
    )
)


for column in [
    "net_billed_amount",
    "paid_amount",
    "outstanding_amount",
]:
    if column in patient_register.columns:
        patient_register[
            column
        ] = (
            pd.to_numeric(
                patient_register[
                    column
                ],
                errors="coerce",
            )
            .fillna(0)
        )


patient_register = patient_register.sort_values(
    [
        "admissions",
        "total_inpatient_days",
    ],
    ascending=[
        False,
        False,
    ],
)


register_columns = [
    column
    for column in [
        "patient_id",
        "patient_name",
        "gender",
        "age",
        "city",
        "state",
        "admissions",
        "total_inpatient_days",
        "average_los",
        "readmissions",
        "emergency_admissions",
        "icu_admissions",
        "outstanding_amount",
        "utilization_segment",
    ]
    if column in patient_register.columns
]


register_display = (
    patient_register[
        register_columns
    ]
    .head(100)
    .copy()
)


if (
    "outstanding_amount"
    in register_display.columns
):
    register_display[
        "outstanding_amount"
    ] = register_display[
        "outstanding_amount"
    ].map(
        format_currency_compact
    )


if "average_los" in register_display.columns:
    register_display[
        "average_los"
    ] = register_display[
        "average_los"
    ].map(
        lambda value: (
            f"{safe_float(value):,.2f}"
            if pd.notna(value)
            else "—"
        )
    )


register_display = register_display.rename(
    columns={
        column: clean_label(column)
        for column in register_display.columns
    }
)


card_heading(
    "Operational Patient Review",
    (
        "Sorted first by admission frequency and then by total "
        "recorded inpatient days. This is not a clinical risk score."
    ),
)

dataframe(
    register_display,
    height=430,
)

explanation_box(
    "How to use this table",
    (
        "Use this register to identify patients associated with "
        "repeated hospital use for further operational analysis. "
        "The ordering reflects utilization only and should not be "
        "interpreted as diagnosis, prognosis or treatment guidance."
    ),
)


# ============================================================
# 10 PATIENT 360
# ============================================================

page_section(
    "10",
    "Patient 360 Drill-Down",
    (
        "Select one patient and connect demographic context, "
        "hospital utilization, admission history and billing exposure."
    ),
)


if filtered_patients.empty:
    st.info(
        "No patients are available under the "
        "current filters."
    )

else:
    selector_data = (
        filtered_patients[
            [
                "patient_id",
                "patient_name",
            ]
        ]
        .drop_duplicates()
        .copy()
    )

    selector_data[
        "selector"
    ] = (
        selector_data[
            "patient_id"
        ].astype(str)
        + " · "
        + selector_data[
            "patient_name"
        ].fillna(
            "Unnamed Patient"
        )
    )


    selected_patient_label = st.selectbox(
        "Select Patient",
        options=selector_data[
            "selector"
        ].tolist(),
    )


    selected_patient_id = (
        selector_data.loc[
            selector_data[
                "selector"
            ]
            == selected_patient_label,
            "patient_id",
        ]
        .iloc[0]
    )


    patient_row = (
        filtered_patients[
            filtered_patients[
                "patient_id"
            ]
            == selected_patient_id
        ]
        .iloc[0]
    )


    patient_admissions = (
        admissions[
            admissions[
                "patient_id"
            ]
            == selected_patient_id
        ]
        .copy()
    )


    patient_finance = (
        financials[
            financials[
                "patient_id"
            ]
            == selected_patient_id
        ]
        .copy()
    )


    patient_admission_count = len(
        patient_admissions
    )


    patient_total_days = (
        pd.to_numeric(
            patient_admissions[
                "length_of_stay"
            ],
            errors="coerce",
        ).fillna(0).sum()
        if not patient_admissions.empty
        else 0
    )


    patient_readmissions = (
        pd.to_numeric(
            patient_admissions[
                "readmission_flag"
            ],
            errors="coerce",
        ).fillna(0).sum()
        if not patient_admissions.empty
        else 0
    )


    patient_outstanding = (
        safe_float(
            patient_finance[
                "outstanding_amount"
            ].iloc[0]
        )
        if not patient_finance.empty
        else 0
    )


    detail1, detail2, detail3, detail4 = (
        st.columns(4)
    )


    detail1.metric(
        "Age",
        (
            f"{safe_int(patient_row['age'])} years"
            if pd.notna(
                patient_row["age"]
            )
            else "—"
        ),
    )


    detail2.metric(
        "Admissions",
        format_integer(
            patient_admission_count
        ),
    )


    detail3.metric(
        "Inpatient Days",
        format_integer(
            patient_total_days
        ),
    )


    detail4.metric(
        "Outstanding",
        format_currency_compact(
            patient_outstanding
        ),
    )


    profile_tab, history_tab, finance_tab = st.tabs(
        [
            "Patient Profile",
            "Admission History",
            "Financial Context",
        ]
    )


    with profile_tab:
        profile_data = pd.DataFrame(
            [
                {
                    "Patient ID":
                        patient_row[
                            "patient_id"
                        ],

                    "Patient Name":
                        patient_row[
                            "patient_name"
                        ],

                    "Gender":
                        patient_row[
                            "gender"
                        ],

                    "Age":
                        patient_row[
                            "age"
                        ],

                    "Blood Group":
                        patient_row[
                            "blood_group"
                        ],

                    "City":
                        patient_row[
                            "city"
                        ],

                    "State":
                        patient_row[
                            "state"
                        ],

                    "Insurance Status":
                        patient_row[
                            "insurance_status"
                        ],

                    "Chronic Condition":
                        patient_row[
                            "chronic_condition"
                        ],

                    "Registration Date":
                        format_date(
                            patient_row[
                                "registration_date"
                            ]
                        ),

                    "Active":
                        patient_row[
                            "is_active"
                        ],
                }
            ]
        )

        dataframe(
            profile_data,
            height=150,
        )

        st.caption(
            "Patient profile is derived from the "
            "synthetic patient dimension."
        )


    with history_tab:
        if patient_admissions.empty:
            st.info(
                "This patient has no recorded admissions."
            )

        else:
            history_columns = [
                column
                for column in [
                    "admission_id",
                    "admission_timestamp",
                    "discharge_timestamp",
                    "admission_type",
                    "department_name",
                    "doctor_name",
                    "diagnosis_name",
                    "length_of_stay",
                    "emergency_flag",
                    "icu_flag",
                    "readmission_flag",
                    "outcome",
                ]
                if column in patient_admissions.columns
            ]


            history_display = (
                patient_admissions[
                    history_columns
                ]
                .sort_values(
                    "admission_timestamp",
                    ascending=False,
                )
                .copy()
            )


            history_display = (
                history_display.rename(
                    columns={
                        column:
                            clean_label(
                                column
                            )
                        for column
                        in history_display.columns
                    }
                )
            )


            dataframe(
                history_display,
                height=400,
            )

            st.caption(
                f"Recorded readmissions for this patient: "
                f"{format_integer(patient_readmissions)}."
            )


    with finance_tab:
        if patient_finance.empty:
            st.info(
                "No billing records are available "
                "for this patient."
            )

        else:
            finance_row = (
                patient_finance.iloc[0]
            )

            f1, f2, f3, f4 = st.columns(4)

            f1.metric(
                "Bills",
                format_integer(
                    finance_row[
                        "bill_count"
                    ]
                ),
            )

            f2.metric(
                "Net Billed",
                format_currency_compact(
                    finance_row[
                        "net_billed_amount"
                    ]
                ),
            )

            f3.metric(
                "Paid",
                format_currency_compact(
                    finance_row[
                        "paid_amount"
                    ]
                ),
            )

            f4.metric(
                "Outstanding",
                format_currency_compact(
                    finance_row[
                        "outstanding_amount"
                    ]
                ),
            )

            explanation_box(
                "Financial context",
                (
                    "These values reflect recorded synthetic billing "
                    "linked to the selected patient. They are not a "
                    "formal receivables-aging analysis."
                ),
            )


# ============================================================
# 11 POPULATION TABLE
# ============================================================

page_section(
    "11",
    "Patient Population Table",
    (
        "Review the patient-master records remaining after "
        "the active dashboard filters."
    ),
)


population_columns = [
    column
    for column in [
        "patient_id",
        "patient_name",
        "gender",
        "age",
        "age_band",
        "blood_group",
        "city",
        "state",
        "insurance_status",
        "chronic_condition",
        "registration_date",
        "is_active",
    ]
    if column in filtered_patients.columns
]


population_display = (
    filtered_patients[
        population_columns
    ]
    .copy()
)


population_display = (
    population_display.rename(
        columns={
            column:
                clean_label(
                    column
                )
            for column
            in population_display.columns
        }
    )
)


dataframe(
    population_display,
    height=430,
)


# ============================================================
# 12 CONTINUE ANALYSIS
# ============================================================

page_section(
    "12",
    "Continue the Analysis",
    (
        "Move from the patient view into hospital operations, "
        "finance or risk analytics."
    ),
)

nav1, nav2, nav3 = st.columns(3)


with nav1:
    card_heading(
        "Operations Analytics",
        (
            "Analyze hospital admissions, LOS, emergency, ICU, "
            "department and doctor performance."
        ),
    )

    st.page_link(
        "pages/03_Operations_Analytics_Dashboard.py",
        label="Open Operations Analytics",
        icon="🏥",
        width="stretch",
    )


with nav2:
    card_heading(
        "Finance Analytics",
        (
            "Review billing, collections, outstanding balances "
            "and hospital financial performance."
        ),
    )

    st.page_link(
        "pages/04_Finance_Analytics_Dashboard.py",
        label="Open Finance Analytics",
        icon="💰",
        width="stretch",
    )


with nav3:
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


# ============================================================
# DIAGNOSTICS
# ============================================================

with st.expander(
    "Technical Data Diagnostics",
    expanded=False,
):
    diagnostic_rows = [
        {
            "Dataset": "Patient Master",
            "Rows": len(patients),
            "Available Fields": ", ".join(
                patients.columns.tolist()
            ),
        },
        {
            "Dataset": "Patient Utilization",
            "Rows": len(utilization),
            "Available Fields": ", ".join(
                utilization.columns.tolist()
            ),
        },
        {
            "Dataset": "Admission History",
            "Rows": len(admissions),
            "Available Fields": ", ".join(
                admissions.columns.tolist()
            ),
        },
        {
            "Dataset": "Patient Financials",
            "Rows": len(financials),
            "Available Fields": ", ".join(
                financials.columns.tolist()
            ),
        },
    ]

    dataframe(
        pd.DataFrame(
            diagnostic_rows
        ),
        height=280,
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

footer_left, footer_right = st.columns(
    [4, 1]
)

with footer_left:
    st.caption(
        "Patient Analytics · Synthetic healthcare data only. "
        "Utilization metrics support operational and analytical "
        "review and should not be interpreted as clinical "
        "diagnosis or treatment guidance. Report generation "
        "and centralized downloads are managed from the "
        "Admin Control Center."
    )

with footer_right:
    render_refresh_button(
        key="patient_analytics_refresh"
    )