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
)


bootstrap_page(
    title="Risk Analytics",
    subtitle=(
        "Enterprise risk intelligence across patient utilization, "
        "financial exposure and insurance claims with transparent "
        "deterministic scoring and management review signals."
    ),
    icon="⚠️",
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


def risk_band(score, medium_threshold, high_threshold):
    score = safe_number(score)

    if score >= high_threshold:
        return "High"

    if score >= medium_threshold:
        return "Medium"

    return "Low"


def style_figure(fig, height=390, unified_hover=False):
    fig.update_layout(
        height=height,
        margin=dict(
            l=15,
            r=15,
            t=30,
            b=15,
        ),
        legend_title_text="",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(size=13),
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
        background: linear-gradient(
            135deg,
            #fff7ed 0%,
            #fffaf5 100%
        );
        border: 1px solid #fed7aa;
        border-radius: 18px;
        padding: 22px 24px;
        margin: 8px 0 30px 0;
        box-shadow: 0 5px 18px rgba(154, 52, 18, 0.06);
    }

    .h360-flow-title {
        color: #9a3412;
        font-size: 1.08rem;
        font-weight: 800;
        margin-bottom: 8px;
    }

    .h360-flow-text {
        color: #6b625c;
        font-size: 0.95rem;
        line-height: 1.7;
    }

    .h360-section-banner {
        display: flex;
        align-items: center;
        gap: 16px;
        background: linear-gradient(
            135deg,
            #fff7ed 0%,
            #fffaf5 100%
        );
        border: 1px solid #fed7aa;
        border-left: 5px solid #c2410c;
        border-radius: 16px;
        padding: 18px 20px;
        margin-top: 34px;
        margin-bottom: 18px;
        box-shadow: 0 4px 14px rgba(154, 52, 18, 0.05);
    }

    .h360-section-number {
        min-width: 46px;
        height: 46px;
        border-radius: 13px;
        background: #9a3412;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 0.95rem;
    }

    .h360-section-title {
        color: #7c2d12;
        font-size: 1.22rem;
        font-weight: 800;
        margin-bottom: 4px;
    }

    .h360-section-description {
        color: #75675e;
        font-size: 0.92rem;
        line-height: 1.55;
    }

    .h360-card-heading {
        background: #ffffff;
        border: 1px solid #f1ddd1;
        border-radius: 14px;
        padding: 15px 17px;
        margin: 6px 0 10px 0;
        box-shadow: 0 3px 12px rgba(154, 52, 18, 0.04);
    }

    .h360-card-title {
        color: #9a3412;
        font-weight: 800;
        font-size: 1rem;
        margin-bottom: 4px;
    }

    .h360-card-description {
        color: #756b65;
        font-size: 0.87rem;
        line-height: 1.5;
    }

    .h360-explanation {
        background: #fffaf5;
        border: 1px solid #f1ddd1;
        border-radius: 13px;
        padding: 14px 16px;
        margin-top: 6px;
        margin-bottom: 16px;
    }

    .h360-explanation-title {
        color: #9a3412;
        font-weight: 800;
        font-size: 0.9rem;
        margin-bottom: 5px;
    }

    .h360-explanation-text {
        color: #6f665f;
        font-size: 0.87rem;
        line-height: 1.6;
    }

    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #f1ddd1;
        border-radius: 15px;
        padding: 16px;
        box-shadow: 0 4px 14px rgba(154, 52, 18, 0.05);
    }

    div[data-testid="stPlotlyChart"] {
        background: #ffffff;
        border: 1px solid #f1ddd1;
        border-radius: 16px;
        padding: 8px;
        box-shadow: 0 4px 14px rgba(154, 52, 18, 0.05);
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid #f1ddd1;
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
def load_patient_risk_base():
    return read_sql(
        """
        SELECT
            a.admission_key,
            a.admission_id,
            p.patient_key,
            p.patient_id,
            p.first_name,
            p.last_name,
            p.gender,
            p.date_of_birth,
            p.city,
            p.state,
            p.insurance_status,
            p.chronic_condition,
            ad.full_date AS admission_date,
            dep.department_name,
            doc.doctor_id,
            doc.doctor_name,
            doc.specialization,
            dx.diagnosis_name,
            dx.diagnosis_category,
            a.admission_type,
            a.length_of_stay,
            a.icu_flag,
            a.readmission_flag,
            a.emergency_flag,
            a.outcome,
            COALESCE(billing.net_amount, 0) AS net_amount,
            COALESCE(billing.paid_amount, 0) AS paid_amount,
            COALESCE(
                billing.outstanding_amount,
                0
            ) AS outstanding_amount

        FROM warehouse.fact_admission a

        INNER JOIN warehouse.dim_patient p
            ON p.patient_key = a.patient_key

        INNER JOIN warehouse.dim_date ad
            ON ad.date_key = a.admission_date_key

        LEFT JOIN warehouse.dim_department dep
            ON dep.department_key = a.department_key

        LEFT JOIN warehouse.dim_doctor doc
            ON doc.doctor_key = a.doctor_key

        LEFT JOIN warehouse.dim_diagnosis dx
            ON dx.diagnosis_key = a.diagnosis_key

        LEFT JOIN (
            SELECT
                admission_key,
                SUM(net_amount) AS net_amount,
                SUM(paid_amount) AS paid_amount,
                SUM(outstanding_amount) AS outstanding_amount

            FROM warehouse.fact_billing

            GROUP BY admission_key
        ) billing
            ON billing.admission_key = a.admission_key
        """
    )


@st.cache_data(
    ttl=60,
    show_spinner=False,
)
def load_financial_risk_base():
    return read_sql(
        """
        SELECT
            b.billing_key,
            b.bill_id,
            b.patient_key,
            b.admission_key,
            d.full_date AS billing_date,
            p.patient_id,
            dep.department_name,
            b.gross_amount,
            b.net_amount,
            b.paid_amount,
            b.outstanding_amount,
            b.payment_status,
            b.payment_method,
            COALESCE(
                claims.claim_count,
                0
            ) AS claim_count,
            COALESCE(
                claims.rejected_claims,
                0
            ) AS rejected_claims,
            COALESCE(
                claims.pending_claims,
                0
            ) AS pending_claims

        FROM warehouse.fact_billing b

        INNER JOIN warehouse.dim_date d
            ON d.date_key = b.billing_date_key

        LEFT JOIN warehouse.dim_patient p
            ON p.patient_key = b.patient_key

        LEFT JOIN warehouse.fact_admission a
            ON a.admission_key = b.admission_key

        LEFT JOIN warehouse.dim_department dep
            ON dep.department_key = a.department_key

        LEFT JOIN (
            SELECT
                billing_key,
                COUNT(*) AS claim_count,

                SUM(
                    CASE
                        WHEN UPPER(
                            COALESCE(
                                claim_status,
                                ''
                            )
                        ) = 'REJECTED'
                        THEN 1
                        ELSE 0
                    END
                ) AS rejected_claims,

                SUM(
                    CASE
                        WHEN UPPER(
                            COALESCE(
                                claim_status,
                                ''
                            )
                        ) = 'PENDING'
                        THEN 1
                        ELSE 0
                    END
                ) AS pending_claims

            FROM warehouse.fact_claim

            GROUP BY billing_key
        ) claims
            ON claims.billing_key = b.billing_key
        """
    )


@st.cache_data(
    ttl=60,
    show_spinner=False,
)
def load_claim_risk_base():
    return read_sql(
        """
        SELECT
            c.claim_key,
            c.claim_id,
            c.billing_key,
            c.patient_key,
            p.patient_id,
            i.insurer_id,
            i.insurer_name,
            i.insurer_type,
            sd.full_date AS submission_date,
            std.full_date AS settlement_date,
            c.claim_amount,
            c.approved_amount,
            c.rejected_amount,
            c.claim_status,
            c.rejection_reason,
            c.processing_days

        FROM warehouse.fact_claim c

        LEFT JOIN warehouse.dim_patient p
            ON p.patient_key = c.patient_key

        LEFT JOIN warehouse.dim_insurer i
            ON i.insurer_key = c.insurer_key

        LEFT JOIN warehouse.dim_date sd
            ON sd.date_key = c.submission_date_key

        LEFT JOIN warehouse.dim_date std
            ON std.date_key = c.settlement_date_key
        """
    )


try:
    patient_risk = load_patient_risk_base()
    financial_risk = load_financial_risk_base()
    claim_risk = load_claim_risk_base()

except Exception as exc:
    st.error(
        "Risk Analytics could not load the required warehouse data."
    )
    st.exception(exc)
    st.stop()


if patient_risk.empty:
    st.warning(
        "No admission records are available for risk analysis."
    )
    st.stop()


patient_risk["admission_date"] = pd.to_datetime(
    patient_risk["admission_date"],
    errors="coerce",
)

patient_risk["date_of_birth"] = pd.to_datetime(
    patient_risk["date_of_birth"],
    errors="coerce",
)


for column in [
    "length_of_stay",
    "net_amount",
    "paid_amount",
    "outstanding_amount",
]:
    patient_risk[column] = pd.to_numeric(
        patient_risk[column],
        errors="coerce",
    ).fillna(0)


for column in [
    "icu_flag",
    "readmission_flag",
    "emergency_flag",
]:
    patient_risk[column] = (
        patient_risk[column]
        .fillna(False)
        .astype(bool)
    )


for column in [
    "department_name",
    "doctor_name",
    "specialization",
    "diagnosis_name",
    "diagnosis_category",
    "chronic_condition",
]:
    patient_risk[column] = (
        patient_risk[column]
        .fillna("Unknown")
        .astype(str)
    )


financial_risk["billing_date"] = pd.to_datetime(
    financial_risk["billing_date"],
    errors="coerce",
)


for column in [
    "gross_amount",
    "net_amount",
    "paid_amount",
    "outstanding_amount",
    "claim_count",
    "rejected_claims",
    "pending_claims",
]:
    financial_risk[column] = pd.to_numeric(
        financial_risk[column],
        errors="coerce",
    ).fillna(0)


for column in [
    "department_name",
    "payment_status",
    "payment_method",
]:
    financial_risk[column] = (
        financial_risk[column]
        .fillna("Unknown")
        .astype(str)
    )


claim_risk["submission_date"] = pd.to_datetime(
    claim_risk["submission_date"],
    errors="coerce",
)

claim_risk["settlement_date"] = pd.to_datetime(
    claim_risk["settlement_date"],
    errors="coerce",
)


for column in [
    "claim_amount",
    "approved_amount",
    "rejected_amount",
    "processing_days",
]:
    claim_risk[column] = pd.to_numeric(
        claim_risk[column],
        errors="coerce",
    ).fillna(0)


for column in [
    "insurer_name",
    "insurer_type",
    "claim_status",
    "rejection_reason",
]:
    claim_risk[column] = (
        claim_risk[column]
        .fillna("Unknown")
        .astype(str)
    )


latest_date = patient_risk[
    "admission_date"
].max()


if pd.isna(latest_date):
    latest_date = (
        pd.Timestamp.today()
        .normalize()
    )


patient_risk["age"] = (
    (
        latest_date
        - patient_risk[
            "date_of_birth"
        ]
    ).dt.days
    / 365.25
).fillna(0).astype(int)


def has_chronic_condition(value):
    value = str(
        value
    ).strip().lower()

    return value not in {
        "",
        "none",
        "no",
        "no chronic condition",
        "nan",
        "unknown",
        "not applicable",
        "n/a",
    }


patient_risk["chronic_flag"] = (
    patient_risk[
        "chronic_condition"
    ].apply(
        has_chronic_condition
    )
)


patient_risk["patient_risk_score"] = (
    patient_risk[
        "readmission_flag"
    ].astype(int) * 25
    + (
        patient_risk["age"] > 70
    ).astype(int) * 15
    + patient_risk[
        "chronic_flag"
    ].astype(int) * 15
    + patient_risk[
        "icu_flag"
    ].astype(int) * 20
    + (
        patient_risk[
            "length_of_stay"
        ] > 10
    ).astype(int) * 10
    + (
        patient_risk[
            "outstanding_amount"
        ] > 0
    ).astype(int) * 5
    + patient_risk[
        "emergency_flag"
    ].astype(int) * 10
)


patient_risk[
    "patient_risk_band"
] = patient_risk[
    "patient_risk_score"
].apply(
    lambda score: risk_band(
        score,
        medium_threshold=30,
        high_threshold=60,
    )
)


financial_risk[
    "financial_risk_score"
] = (
    (
        financial_risk[
            "outstanding_amount"
        ] > 0
    ).astype(int) * 15
    + (
        financial_risk[
            "outstanding_amount"
        ] >= 10_000
    ).astype(int) * 10
    + (
        financial_risk[
            "outstanding_amount"
        ] >= 25_000
    ).astype(int) * 10
    + (
        financial_risk[
            "outstanding_amount"
        ] >= 50_000
    ).astype(int) * 15
    + (
        financial_risk[
            "net_amount"
        ] >= 100_000
    ).astype(int) * 10
    + (
        financial_risk[
            "paid_amount"
        ]
        < financial_risk[
            "net_amount"
        ]
    ).astype(int) * 15
    + (
        financial_risk[
            "rejected_claims"
        ] > 0
    ).astype(int) * 20
    + (
        financial_risk[
            "pending_claims"
        ] > 0
    ).astype(int) * 10
)


financial_risk[
    "financial_risk_band"
] = financial_risk[
    "financial_risk_score"
].apply(
    lambda score: risk_band(
        score,
        medium_threshold=25,
        high_threshold=50,
    )
)


claim_status_upper = (
    claim_risk[
        "claim_status"
    ]
    .str.upper()
    .str.strip()
)


claim_risk[
    "claim_risk_score"
] = (
    (
        claim_status_upper
        == "REJECTED"
    ).astype(int) * 30
    + (
        claim_status_upper
        == "PENDING"
    ).astype(int) * 20
    + claim_status_upper.isin(
        [
            "PARTIALLY APPROVED",
            "PARTIAL",
            "PARTIALLY_APPROVED",
        ]
    ).astype(int) * 10
    + (
        claim_risk[
            "rejected_amount"
        ] >= 25_000
    ).astype(int) * 15
    + (
        claim_risk[
            "claim_amount"
        ] >= 100_000
    ).astype(int) * 10
    + (
        claim_risk[
            "processing_days"
        ] > 30
    ).astype(int) * 10
)


claim_risk[
    "claim_risk_band"
] = claim_risk[
    "claim_risk_score"
].apply(
    lambda score: risk_band(
        score,
        medium_threshold=20,
        high_threshold=40,
    )
)


st.markdown(
    """
    <div class="h360-flow">
        <div class="h360-flow-title">
            How to read this dashboard
        </div>
        <div class="h360-flow-text">
            Begin with the patient-risk scope and enterprise
            scorecard. Review how risk is distributed across the
            patient, financial and claim domains. Then investigate
            patient risk drivers and department concentrations,
            followed by the patient priority register, financial
            exposure and claims risk. Finish with cross-domain
            management signals and the transparent scoring
            methodology. These scores are analytical prioritization
            rules, not predictive clinical or fraud models.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


page_section(
    "01",
    "Patient Risk Scope",
    (
        "Define the admission population used for patient-risk "
        "analysis. Financial and claim domains remain enterprise-wide."
    ),
)


filtered_patient = patient_risk.copy()

valid_dates = filtered_patient[
    "admission_date"
].dropna()


f1, f2, f3 = st.columns(3)


with f1:
    if not valid_dates.empty:
        minimum = (
            valid_dates.min()
            .date()
        )

        maximum = (
            valid_dates.max()
            .date()
        )

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
        filtered_patient[
            "department_name"
        ]
        .unique()
        .tolist()
    )

    selected_departments = (
        st.multiselect(
            "Department",
            departments,
            placeholder="All departments",
        )
    )


with f3:
    selected_patient_band = (
        st.multiselect(
            "Patient Risk Band",
            [
                "High",
                "Medium",
                "Low",
            ],
            placeholder="All risk bands",
        )
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
        + pd.Timedelta(days=1)
    )

    filtered_patient = (
        filtered_patient[
            (
                filtered_patient[
                    "admission_date"
                ] >= start
            )
            &
            (
                filtered_patient[
                    "admission_date"
                ] < end
            )
        ]
    )


if selected_departments:
    filtered_patient = (
        filtered_patient[
            filtered_patient[
                "department_name"
            ].isin(
                selected_departments
            )
        ]
    )


if selected_patient_band:
    filtered_patient = (
        filtered_patient[
            filtered_patient[
                "patient_risk_band"
            ].isin(
                selected_patient_band
            )
        ]
    )


if filtered_patient.empty:
    st.warning(
        "No patient-risk records match the current filters."
    )
    st.stop()


st.info(
    "The controls above apply to the patient/admission risk domain. "
    "Financial-risk and claim-risk sections intentionally retain "
    "enterprise-wide populations so that unlike event dates are not "
    "silently treated as equivalent."
)


page_section(
    "02",
    "Enterprise Risk Scorecard",
    (
        "Executive view of high-priority analytical signals "
        "across patient, financial and claim risk domains."
    ),
)


patient_high = int(
    (
        filtered_patient[
            "patient_risk_band"
        ] == "High"
    ).sum()
)

patient_medium = int(
    (
        filtered_patient[
            "patient_risk_band"
        ] == "Medium"
    ).sum()
)

financial_high = int(
    (
        financial_risk[
            "financial_risk_band"
        ] == "High"
    ).sum()
)

claim_high = int(
    (
        claim_risk[
            "claim_risk_band"
        ] == "High"
    ).sum()
)


high_outstanding = safe_number(
    financial_risk.loc[
        financial_risk[
            "financial_risk_band"
        ] == "High",
        "outstanding_amount",
    ].sum()
)


metric_row(
    [
        (
            "High-Risk Admissions",
            format_integer(
                patient_high
            ),
        ),
        (
            "High-Risk Admission Rate",
            format_percentage(
                pct(
                    patient_high,
                    len(
                        filtered_patient
                    ),
                )
            ),
        ),
        (
            "High Financial-Risk Bills",
            format_integer(
                financial_high
            ),
        ),
        (
            "High Claim-Risk Records",
            format_integer(
                claim_high
            ),
        ),
    ]
)


metric_row(
    [
        (
            "Medium-Risk Admissions",
            format_integer(
                patient_medium
            ),
        ),
        (
            "Average Patient Risk Score",
            (
                f"{filtered_patient['patient_risk_score'].mean():.2f}"
            ),
        ),
        (
            "High-Risk Bill Outstanding",
            format_currency_compact(
                high_outstanding
            ),
        ),
        (
            "Claims Reviewed",
            format_integer(
                len(
                    claim_risk
                )
            ),
        ),
    ]
)


management_insight(
    (
        f"The selected patient-risk population contains "
        f"{format_integer(patient_high)} high-risk admission records "
        f"({format_percentage(pct(patient_high, len(filtered_patient)))}) "
        f"and {format_integer(patient_medium)} medium-risk records. "
        f"Across the enterprise billing population, "
        f"{format_integer(financial_high)} bills meet the defined "
        f"high financial-risk threshold. Across the claims population, "
        f"{format_integer(claim_high)} claims meet the high claim-risk "
        f"threshold."
    ),
    label="Enterprise Risk Snapshot",
)


st.warning(
    "Risk scores are deterministic analytical prioritization "
    "signals. Patient risk is not a clinical diagnosis or validated "
    "clinical prediction. Financial and claim risk are not fraud "
    "determinations."
)


page_section(
    "03",
    "Risk Domain Distribution",
    (
        "Compare low, medium and high analytical risk "
        "distribution across all three domains."
    ),
)


patient_bands = (
    filtered_patient[
        "patient_risk_band"
    ]
    .value_counts()
    .reindex(
        [
            "High",
            "Medium",
            "Low",
        ],
        fill_value=0,
    )
    .rename_axis(
        "Risk Band"
    )
    .reset_index(
        name="Records"
    )
)


financial_bands = (
    financial_risk[
        "financial_risk_band"
    ]
    .value_counts()
    .reindex(
        [
            "High",
            "Medium",
            "Low",
        ],
        fill_value=0,
    )
    .rename_axis(
        "Risk Band"
    )
    .reset_index(
        name="Records"
    )
)


claim_bands = (
    claim_risk[
        "claim_risk_band"
    ]
    .value_counts()
    .reindex(
        [
            "High",
            "Medium",
            "Low",
        ],
        fill_value=0,
    )
    .rename_axis(
        "Risk Band"
    )
    .reset_index(
        name="Records"
    )
)


c1, c2, c3 = st.columns(3)


with c1:
    card_heading(
        "Patient Admission Risk",
        (
            "Distribution of admission-level patient "
            "risk in the selected patient scope."
        ),
    )

    fig = px.pie(
        patient_bands,
        names="Risk Band",
        values="Records",
        hole=0.55,
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
        "Financial Risk",
        (
            "Distribution of deterministic bill-level "
            "financial risk across the enterprise."
        ),
    )

    fig = px.pie(
        financial_bands,
        names="Risk Band",
        values="Records",
        hole=0.55,
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
        "Claim Risk",
        (
            "Distribution of deterministic claim-level "
            "risk across the enterprise."
        ),
    )

    fig = px.pie(
        claim_bands,
        names="Risk Band",
        values="Records",
        hole=0.55,
    )

    st.plotly_chart(
        style_figure(
            fig,
            350,
        ),
        width="stretch",
    )


explanation_box(
    "Important comparison note",
    (
        "The three charts represent different analytical units: "
        "admissions, bills and claims. Their record counts should "
        "therefore not be directly added together."
    ),
)


page_section(
    "04",
    "Patient Risk Drivers",
    (
        "Show how frequently each deterministic patient-risk "
        "factor occurs and how strongly it contributes to scoring."
    ),
)


risk_factors = pd.DataFrame(
    [
        {
            "Risk Factor":
                "Readmission",
            "Weight":
                25,
            "Admissions":
                int(
                    filtered_patient[
                        "readmission_flag"
                    ].sum()
                ),
        },
        {
            "Risk Factor":
                "Age > 70",
            "Weight":
                15,
            "Admissions":
                int(
                    (
                        filtered_patient[
                            "age"
                        ] > 70
                    ).sum()
                ),
        },
        {
            "Risk Factor":
                "Chronic Condition",
            "Weight":
                15,
            "Admissions":
                int(
                    filtered_patient[
                        "chronic_flag"
                    ].sum()
                ),
        },
        {
            "Risk Factor":
                "ICU Admission",
            "Weight":
                20,
            "Admissions":
                int(
                    filtered_patient[
                        "icu_flag"
                    ].sum()
                ),
        },
        {
            "Risk Factor":
                "LOS > 10 Days",
            "Weight":
                10,
            "Admissions":
                int(
                    (
                        filtered_patient[
                            "length_of_stay"
                        ] > 10
                    ).sum()
                ),
        },
        {
            "Risk Factor":
                "Outstanding Balance",
            "Weight":
                5,
            "Admissions":
                int(
                    (
                        filtered_patient[
                            "outstanding_amount"
                        ] > 0
                    ).sum()
                ),
        },
        {
            "Risk Factor":
                "Emergency Admission",
            "Weight":
                10,
            "Admissions":
                int(
                    filtered_patient[
                        "emergency_flag"
                    ].sum()
                ),
        },
    ]
)


risk_factors[
    "Prevalence %"
] = (
    risk_factors[
        "Admissions"
    ]
    / len(
        filtered_patient
    )
    * 100
)


left, right = st.columns(2)


with left:
    card_heading(
        "Risk-Factor Prevalence",
        (
            "Shows how often each patient-risk factor "
            "occurs in the selected admission population."
        ),
    )

    chart = (
        risk_factors.sort_values(
            "Prevalence %",
            ascending=True,
        )
    )

    fig = px.bar(
        chart,
        x="Prevalence %",
        y="Risk Factor",
        orientation="h",
        text_auto=True,
    )

    fig.update_yaxes(
        title=None
    )

    fig.update_xaxes(
        title="Prevalence (%)"
    )

    st.plotly_chart(
        style_figure(
            fig,
            420,
        ),
        width="stretch",
    )


with right:
    card_heading(
        "Risk Scoring Weights",
        (
            "Shows the deterministic score contribution "
            "assigned to each patient-risk factor."
        ),
    )

    chart = (
        risk_factors.sort_values(
            "Weight",
            ascending=True,
        )
    )

    fig = px.bar(
        chart,
        x="Weight",
        y="Risk Factor",
        orientation="h",
        text_auto=True,
    )

    fig.update_yaxes(
        title=None
    )

    fig.update_xaxes(
        title="Score Weight"
    )

    st.plotly_chart(
        style_figure(
            fig,
            420,
        ),
        width="stretch",
    )


explanation_box(
    "How to interpret these charts",
    (
        "Prevalence describes how common a factor is in the selected "
        "population. Weight describes how many deterministic score "
        "points the factor contributes. A common factor is not "
        "necessarily the highest-weighted factor."
    ),
)


page_section(
    "05",
    "Department Risk Intelligence",
    (
        "Compare patient-risk concentration and average "
        "deterministic risk scores across departments."
    ),
)


department_risk = (
    filtered_patient.groupby(
        "department_name",
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
        average_risk_score=(
            "patient_risk_score",
            "mean",
        ),
        high_risk_admissions=(
            "patient_risk_band",
            lambda values:
                (
                    values
                    == "High"
                ).sum(),
        ),
        medium_risk_admissions=(
            "patient_risk_band",
            lambda values:
                (
                    values
                    == "Medium"
                ).sum(),
        ),
        outstanding_amount=(
            "outstanding_amount",
            "sum",
        ),
    )
)


department_risk[
    "high_risk_rate_pct"
] = department_risk.apply(
    lambda row: pct(
        row[
            "high_risk_admissions"
        ],
        row[
            "admissions"
        ],
    ),
    axis=1,
)


left, right = st.columns(2)


with left:
    card_heading(
        "High-Risk Admission Rate",
        (
            "Compares the share of admission records "
            "classified as high risk by department."
        ),
    )

    chart = (
        department_risk
        .sort_values(
            "high_risk_rate_pct",
            ascending=True,
        )
    )

    fig = px.bar(
        chart,
        x="high_risk_rate_pct",
        y="department_name",
        orientation="h",
        text_auto=True,
    )

    fig.update_yaxes(
        title=None
    )

    fig.update_xaxes(
        title="High-Risk Rate (%)"
    )

    st.plotly_chart(
        style_figure(
            fig,
            430,
        ),
        width="stretch",
    )


with right:
    card_heading(
        "Average Patient Risk Score",
        (
            "Compares average deterministic admission-risk "
            "scores across departments."
        ),
    )

    chart = (
        department_risk
        .sort_values(
            "average_risk_score",
            ascending=True,
        )
    )

    fig = px.bar(
        chart,
        x="average_risk_score",
        y="department_name",
        orientation="h",
        text_auto=True,
    )

    fig.update_yaxes(
        title=None
    )

    fig.update_xaxes(
        title="Average Risk Score"
    )

    st.plotly_chart(
        style_figure(
            fig,
            430,
        ),
        width="stretch",
    )


department_display = (
    department_risk.rename(
        columns={
            "department_name":
                "Department",
            "admissions":
                "Admissions",
            "patients":
                "Patients",
            "average_risk_score":
                "Average Risk Score",
            "high_risk_admissions":
                "High Risk",
            "medium_risk_admissions":
                "Medium Risk",
            "high_risk_rate_pct":
                "High-Risk Rate %",
            "outstanding_amount":
                "Recorded Outstanding",
        }
    )
)


card_heading(
    "Department Risk Table",
    (
        "Detailed department view of admission volumes, "
        "risk concentration and recorded outstanding balances."
    ),
)

dataframe(
    department_display,
    height=390,
)


page_section(
    "06",
    "Patient Priority Register",
    (
        "Consolidate patients associated with high-risk "
        "admission records for analytical management review."
    ),
)


high_patient = (
    filtered_patient[
        filtered_patient[
            "patient_risk_band"
        ] == "High"
    ].copy()
)


if not high_patient.empty:
    patient_priority = (
        high_patient.groupby(
            [
                "patient_id",
                "first_name",
                "last_name",
                "gender",
                "age",
                "chronic_condition",
            ],
            as_index=False,
        )
        .agg(
            high_risk_admissions=(
                "admission_id",
                "count",
            ),
            maximum_risk_score=(
                "patient_risk_score",
                "max",
            ),
            average_risk_score=(
                "patient_risk_score",
                "mean",
            ),
            latest_admission=(
                "admission_date",
                "max",
            ),
            total_outstanding=(
                "outstanding_amount",
                "sum",
            ),
        )
        .sort_values(
            [
                "maximum_risk_score",
                "high_risk_admissions",
                "total_outstanding",
            ],
            ascending=[
                False,
                False,
                False,
            ],
        )
    )


    patient_priority[
        "Patient"
    ] = (
        patient_priority[
            "first_name"
        ].fillna("")
        + " "
        + patient_priority[
            "last_name"
        ].fillna("")
    ).str.strip()


    patient_priority_display = (
        patient_priority[
            [
                "patient_id",
                "Patient",
                "gender",
                "age",
                "chronic_condition",
                "high_risk_admissions",
                "maximum_risk_score",
                "average_risk_score",
                "latest_admission",
                "total_outstanding",
            ]
        ]
        .rename(
            columns={
                "patient_id":
                    "Patient ID",
                "gender":
                    "Gender",
                "age":
                    "Age",
                "chronic_condition":
                    "Chronic Condition",
                "high_risk_admissions":
                    "High-Risk Admissions",
                "maximum_risk_score":
                    "Maximum Risk Score",
                "average_risk_score":
                    "Average Risk Score",
                "latest_admission":
                    "Latest Admission",
                "total_outstanding":
                    "Recorded Outstanding",
            }
        )
    )


    dataframe(
        patient_priority_display,
        height=460,
    )

    st.caption(
        "This register prioritizes records for analytical review. "
        "It is not a clinical triage or treatment list."
    )

else:
    st.success(
        "No high-risk patient admission records exist "
        "in the current selection."
    )


page_section(
    "07",
    "Financial Exposure Risk",
    (
        "Review deterministic bill-level risk associated with "
        "outstanding balances, bill value, payment completion "
        "and linked claim-status signals."
    ),
)


high_financial = (
    financial_risk[
        financial_risk[
            "financial_risk_band"
        ] == "High"
    ].copy()
)


financial_high_outstanding = (
    safe_number(
        high_financial[
            "outstanding_amount"
        ].sum()
    )
)


total_outstanding = safe_number(
    financial_risk[
        "outstanding_amount"
    ].sum()
)


metric_row(
    [
        (
            "High-Risk Bills",
            format_integer(
                len(
                    high_financial
                )
            ),
        ),
        (
            "High-Risk Bill Rate",
            format_percentage(
                pct(
                    len(
                        high_financial
                    ),
                    len(
                        financial_risk
                    ),
                )
            ),
        ),
        (
            "High-Risk Outstanding",
            format_currency_compact(
                financial_high_outstanding
            ),
        ),
        (
            "Share of Total Outstanding",
            format_percentage(
                pct(
                    financial_high_outstanding,
                    total_outstanding,
                )
            ),
        ),
    ]
)


department_financial = (
    financial_risk.groupby(
        "department_name",
        as_index=False,
    )
    .agg(
        bills=(
            "bill_id",
            "count",
        ),
        high_risk_bills=(
            "financial_risk_band",
            lambda values:
                (
                    values
                    == "High"
                ).sum(),
        ),
        net_amount=(
            "net_amount",
            "sum",
        ),
        outstanding_amount=(
            "outstanding_amount",
            "sum",
        ),
    )
)


department_financial[
    "high_risk_bill_rate_pct"
] = department_financial.apply(
    lambda row: pct(
        row[
            "high_risk_bills"
        ],
        row[
            "bills"
        ],
    ),
    axis=1,
)


left, right = st.columns(2)


with left:
    card_heading(
        "Outstanding Exposure by Department",
        (
            "Ranks departments by recorded outstanding "
            "balance across enterprise billing records."
        ),
    )

    chart = (
        department_financial
        .sort_values(
            "outstanding_amount",
            ascending=True,
        )
    )

    fig = px.bar(
        chart,
        x="outstanding_amount",
        y="department_name",
        orientation="h",
        text_auto=True,
    )

    fig.update_yaxes(
        title=None
    )

    fig.update_xaxes(
        title="Recorded Outstanding"
    )

    st.plotly_chart(
        style_figure(
            fig,
            430,
        ),
        width="stretch",
    )


with right:
    card_heading(
        "High Financial-Risk Bill Rate",
        (
            "Compares the proportion of bills meeting "
            "the defined high-risk threshold."
        ),
    )

    chart = (
        department_financial
        .sort_values(
            "high_risk_bill_rate_pct",
            ascending=True,
        )
    )

    fig = px.bar(
        chart,
        x="high_risk_bill_rate_pct",
        y="department_name",
        orientation="h",
        text_auto=True,
    )

    fig.update_yaxes(
        title=None
    )

    fig.update_xaxes(
        title="High-Risk Bill Rate (%)"
    )

    st.plotly_chart(
        style_figure(
            fig,
            430,
        ),
        width="stretch",
    )


if not high_financial.empty:
    high_financial_display = (
        high_financial.sort_values(
            [
                "financial_risk_score",
                "outstanding_amount",
            ],
            ascending=[
                False,
                False,
            ],
        )
        .head(150)
    )


    high_financial_display = (
        high_financial_display[
            [
                "bill_id",
                "billing_date",
                "patient_id",
                "department_name",
                "payment_status",
                "net_amount",
                "paid_amount",
                "outstanding_amount",
                "rejected_claims",
                "pending_claims",
                "financial_risk_score",
                "financial_risk_band",
            ]
        ]
        .rename(
            columns={
                "bill_id":
                    "Bill ID",
                "billing_date":
                    "Billing Date",
                "patient_id":
                    "Patient ID",
                "department_name":
                    "Department",
                "payment_status":
                    "Payment Status",
                "net_amount":
                    "Net Amount",
                "paid_amount":
                    "Recorded Paid",
                "outstanding_amount":
                    "Recorded Outstanding",
                "rejected_claims":
                    "Rejected Claims",
                "pending_claims":
                    "Pending Claims",
                "financial_risk_score":
                    "Risk Score",
                "financial_risk_band":
                    "Risk Band",
            }
        )
    )


    card_heading(
        "High Financial-Risk Bill Register",
        (
            "Highest-priority bills according to the "
            "defined deterministic financial-risk rules."
        ),
    )

    dataframe(
        high_financial_display,
        height=460,
    )


explanation_box(
    "Financial risk interpretation",
    (
        "A high financial-risk score identifies bills matching "
        "multiple predefined exposure signals. It does not establish "
        "fraud, billing error, creditworthiness or collectability."
    ),
)


page_section(
    "08",
    "Claims Risk Intelligence",
    (
        "Review deterministic claim-level risk using status, "
        "rejected value, claim size and processing duration."
    ),
)


high_claim = (
    claim_risk[
        claim_risk[
            "claim_risk_band"
        ] == "High"
    ].copy()
)


high_claim_amount = safe_number(
    high_claim[
        "claim_amount"
    ].sum()
)


high_rejected_amount = safe_number(
    high_claim[
        "rejected_amount"
    ].sum()
)


metric_row(
    [
        (
            "High-Risk Claims",
            format_integer(
                len(
                    high_claim
                )
            ),
        ),
        (
            "High-Risk Claim Rate",
            format_percentage(
                pct(
                    len(
                        high_claim
                    ),
                    len(
                        claim_risk
                    ),
                )
            ),
        ),
        (
            "High-Risk Claim Value",
            format_currency_compact(
                high_claim_amount
            ),
        ),
        (
            "Rejected Value in High Risk",
            format_currency_compact(
                high_rejected_amount
            ),
        ),
    ]
)


insurer_risk = (
    claim_risk.groupby(
        "insurer_name",
        as_index=False,
    )
    .agg(
        claims=(
            "claim_id",
            "count",
        ),
        claim_amount=(
            "claim_amount",
            "sum",
        ),
        rejected_amount=(
            "rejected_amount",
            "sum",
        ),
        average_processing_days=(
            "processing_days",
            "mean",
        ),
        high_risk_claims=(
            "claim_risk_band",
            lambda values:
                (
                    values
                    == "High"
                ).sum(),
        ),
    )
)


insurer_risk[
    "high_risk_claim_rate_pct"
] = insurer_risk.apply(
    lambda row: pct(
        row[
            "high_risk_claims"
        ],
        row[
            "claims"
        ],
    ),
    axis=1,
)


left, right = st.columns(2)


with left:
    card_heading(
        "Rejected Claim Value by Insurer",
        (
            "Compares aggregate rejected claim value "
            "across insurers."
        ),
    )

    chart = (
        insurer_risk
        .sort_values(
            "rejected_amount",
            ascending=True,
        )
    )

    fig = px.bar(
        chart,
        x="rejected_amount",
        y="insurer_name",
        orientation="h",
        text_auto=True,
    )

    fig.update_yaxes(
        title=None
    )

    fig.update_xaxes(
        title="Rejected Claim Value"
    )

    st.plotly_chart(
        style_figure(
            fig,
            400,
        ),
        width="stretch",
    )


with right:
    card_heading(
        "High Claim-Risk Rate by Insurer",
        (
            "Compares the proportion of each insurer's "
            "claims meeting the high-risk threshold."
        ),
    )

    chart = (
        insurer_risk
        .sort_values(
            "high_risk_claim_rate_pct",
            ascending=True,
        )
    )

    fig = px.bar(
        chart,
        x="high_risk_claim_rate_pct",
        y="insurer_name",
        orientation="h",
        text_auto=True,
    )

    fig.update_yaxes(
        title=None
    )

    fig.update_xaxes(
        title="High-Risk Rate (%)"
    )

    st.plotly_chart(
        style_figure(
            fig,
            400,
        ),
        width="stretch",
    )


if not high_claim.empty:
    claim_display = (
        high_claim.sort_values(
            [
                "claim_risk_score",
                "rejected_amount",
            ],
            ascending=[
                False,
                False,
            ],
        )
        .head(150)
    )


    claim_display = (
        claim_display[
            [
                "claim_id",
                "patient_id",
                "insurer_name",
                "submission_date",
                "settlement_date",
                "claim_status",
                "claim_amount",
                "approved_amount",
                "rejected_amount",
                "processing_days",
                "rejection_reason",
                "claim_risk_score",
            ]
        ]
        .rename(
            columns={
                "claim_id":
                    "Claim ID",
                "patient_id":
                    "Patient ID",
                "insurer_name":
                    "Insurer",
                "submission_date":
                    "Submitted",
                "settlement_date":
                    "Settled",
                "claim_status":
                    "Status",
                "claim_amount":
                    "Claim Amount",
                "approved_amount":
                    "Approved Amount",
                "rejected_amount":
                    "Rejected Amount",
                "processing_days":
                    "Processing Days",
                "rejection_reason":
                    "Rejection Reason",
                "claim_risk_score":
                    "Risk Score",
            }
        )
    )


    card_heading(
        "High Claim-Risk Register",
        (
            "Highest-priority claim records according "
            "to the deterministic claim-risk rules."
        ),
    )

    dataframe(
        claim_display,
        height=460,
    )


explanation_box(
    "Claim risk interpretation",
    (
        "Claim risk combines predefined status, value and processing "
        "signals for management prioritization. It is not evidence "
        "of fraud, misconduct or inappropriate insurer behavior."
    ),
)


page_section(
    "09",
    "Enterprise Risk Review Signals",
    (
        "Surface the largest cross-domain concentrations "
        "for management investigation."
    ),
)


signals = []


if not department_risk.empty:
    row = (
        department_risk
        .sort_values(
            "high_risk_rate_pct",
            ascending=False,
        )
        .iloc[0]
    )

    signals.append(
        {
            "Domain":
                "Patient",
            "Signal":
                "Largest High-Risk Admission Rate",
            "Entity":
                row[
                    "department_name"
                ],
            "Value":
                format_percentage(
                    row[
                        "high_risk_rate_pct"
                    ]
                ),
            "Review Context":
                (
                    "Largest observed high-risk admission "
                    "share in the selected patient scope."
                ),
        }
    )


if not department_financial.empty:
    row = (
        department_financial
        .sort_values(
            "outstanding_amount",
            ascending=False,
        )
        .iloc[0]
    )

    signals.append(
        {
            "Domain":
                "Financial",
            "Signal":
                "Largest Department Outstanding",
            "Entity":
                row[
                    "department_name"
                ],
            "Value":
                format_currency_compact(
                    row[
                        "outstanding_amount"
                    ]
                ),
            "Review Context":
                (
                    "Largest recorded enterprise "
                    "outstanding exposure by department."
                ),
        }
    )


if not insurer_risk.empty:
    row = (
        insurer_risk
        .sort_values(
            "rejected_amount",
            ascending=False,
        )
        .iloc[0]
    )

    signals.append(
        {
            "Domain":
                "Claims",
            "Signal":
                "Largest Rejected Claim Value",
            "Entity":
                row[
                    "insurer_name"
                ],
            "Value":
                format_currency_compact(
                    row[
                        "rejected_amount"
                    ]
                ),
            "Review Context":
                (
                    "Largest aggregate rejected claim "
                    "value among insurers."
                ),
        }
    )


if not high_patient.empty:
    row = (
        high_patient
        .sort_values(
            "patient_risk_score",
            ascending=False,
        )
        .iloc[0]
    )

    signals.append(
        {
            "Domain":
                "Patient",
            "Signal":
                "Maximum Admission Risk Score",
            "Entity":
                row[
                    "patient_id"
                ],
            "Value":
                str(
                    int(
                        row[
                            "patient_risk_score"
                        ]
                    )
                ),
            "Review Context":
                (
                    "Highest deterministic admission-level "
                    "risk score observed."
                ),
        }
    )


if not high_financial.empty:
    row = (
        high_financial
        .sort_values(
            "outstanding_amount",
            ascending=False,
        )
        .iloc[0]
    )

    signals.append(
        {
            "Domain":
                "Financial",
            "Signal":
                "Largest High-Risk Bill Outstanding",
            "Entity":
                row[
                    "bill_id"
                ],
            "Value":
                format_currency_compact(
                    row[
                        "outstanding_amount"
                    ]
                ),
            "Review Context":
                (
                    "Largest recorded outstanding balance "
                    "among high-risk bills."
                ),
        }
    )


if not high_claim.empty:
    row = (
        high_claim
        .sort_values(
            [
                "claim_risk_score",
                "rejected_amount",
            ],
            ascending=[
                False,
                False,
            ],
        )
        .iloc[0]
    )

    signals.append(
        {
            "Domain":
                "Claims",
            "Signal":
                "Maximum Claim Risk",
            "Entity":
                row[
                    "claim_id"
                ],
            "Value":
                str(
                    int(
                        row[
                            "claim_risk_score"
                        ]
                    )
                ),
            "Review Context":
                (
                    "Highest deterministic claim-level "
                    "risk score observed."
                ),
        }
    )


if signals:
    dataframe(
        pd.DataFrame(
            signals
        ),
        height=390,
    )


explanation_box(
    "How to use these signals",
    (
        "The review table highlights concentrations generated "
        "directly from the deterministic scoring framework. "
        "Signals indicate where management may investigate further; "
        "they are not findings or conclusions."
    ),
)


page_section(
    "10",
    "Risk Scoring Methodology",
    (
        "Make every scoring rule and threshold visible "
        "so that users can understand exactly how risk is classified."
    ),
)


patient_rules = pd.DataFrame(
    [
        [
            "Readmission",
            "+25",
        ],
        [
            "Age > 70",
            "+15",
        ],
        [
            "Chronic condition",
            "+15",
        ],
        [
            "ICU admission",
            "+20",
        ],
        [
            "Length of stay > 10 days",
            "+10",
        ],
        [
            "Outstanding balance > 0",
            "+5",
        ],
        [
            "Emergency admission",
            "+10",
        ],
        [
            "Low",
            "0–29",
        ],
        [
            "Medium",
            "30–59",
        ],
        [
            "High",
            "60+",
        ],
    ],
    columns=[
        "Patient Rule",
        "Score / Band",
    ],
)


financial_rules = pd.DataFrame(
    [
        [
            "Outstanding > 0",
            "+15",
        ],
        [
            "Outstanding ≥ 10K",
            "+10",
        ],
        [
            "Outstanding ≥ 25K",
            "+10",
        ],
        [
            "Outstanding ≥ 50K",
            "+15",
        ],
        [
            "Net bill ≥ 100K",
            "+10",
        ],
        [
            "Bill not fully paid",
            "+15",
        ],
        [
            "Rejected claim linked",
            "+20",
        ],
        [
            "Pending claim linked",
            "+10",
        ],
        [
            "Low",
            "0–24",
        ],
        [
            "Medium",
            "25–49",
        ],
        [
            "High",
            "50+",
        ],
    ],
    columns=[
        "Financial Rule",
        "Score / Band",
    ],
)


claim_rules = pd.DataFrame(
    [
        [
            "Rejected status",
            "+30",
        ],
        [
            "Pending status",
            "+20",
        ],
        [
            "Partial approval",
            "+10",
        ],
        [
            "Rejected amount ≥ 25K",
            "+15",
        ],
        [
            "Claim amount ≥ 100K",
            "+10",
        ],
        [
            "Processing > 30 days",
            "+10",
        ],
        [
            "Low",
            "0–19",
        ],
        [
            "Medium",
            "20–39",
        ],
        [
            "High",
            "40+",
        ],
    ],
    columns=[
        "Claim Rule",
        "Score / Band",
    ],
)


tab1, tab2, tab3 = st.tabs(
    [
        "Patient Risk",
        "Financial Risk",
        "Claim Risk",
    ]
)


with tab1:
    dataframe(
        patient_rules,
        height=390,
    )


with tab2:
    dataframe(
        financial_rules,
        height=420,
    )


with tab3:
    dataframe(
        claim_rules,
        height=370,
    )


st.info(
    "The scoring methodology is intentionally transparent and "
    "deterministic. Thresholds are analytical demonstration rules "
    "for the Hospital 360 synthetic dataset and are not validated "
    "clinical, actuarial, credit or fraud models."
)


page_section(
    "11",
    "Continue the Analysis",
    (
        "Move from enterprise risk intelligence into "
        "detailed insurance claims analysis."
    ),
)


nav1, nav2 = st.columns(2)


with nav1:
    card_heading(
        "Finance Analytics",
        (
            "Return to billing, collection and "
            "outstanding-exposure analysis."
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
        "Claims Analytics",
        (
            "Continue into insurer performance, claim "
            "status, approval and rejection intelligence."
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
                "Risk Domain":
                    "Patient / Admission",
                "Source Rows":
                    len(
                        patient_risk
                    ),
                "Current Rows":
                    len(
                        filtered_patient
                    ),
                "Analytical Unit":
                    "Admission",
            },
            {
                "Risk Domain":
                    "Financial",
                "Source Rows":
                    len(
                        financial_risk
                    ),
                "Current Rows":
                    len(
                        financial_risk
                    ),
                "Analytical Unit":
                    "Bill",
            },
            {
                "Risk Domain":
                    "Claims",
                "Source Rows":
                    len(
                        claim_risk
                    ),
                "Current Rows":
                    len(
                        claim_risk
                    ),
                "Analytical Unit":
                    "Claim",
            },
        ]
    )

    dataframe(
        diagnostics,
        height=220,
    )


st.divider()


footer_left, footer_right = st.columns(
    [4, 1]
)


with footer_left:
    st.caption(
        "Risk Analytics · Hospital 360 synthetic healthcare data · "
        "Transparent deterministic scoring · Patient scores are not "
        "clinical predictions · Financial and claim scores are not "
        "fraud determinations · Downloads and report generation remain "
        "centralized in the Admin Control Center."
    )


with footer_right:
    render_refresh_button(
        key="risk_refresh",
    )