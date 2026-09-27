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
    title="Claims Analytics",
    subtitle=(
        "Payer and insurance-claims intelligence covering claim volume, "
        "outcomes, financial conversion, processing efficiency, rejection "
        "exposure and claim-level management review."
    ),
    icon="🧾",
)


# ============================================================
# HELPERS
# ============================================================

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


def normalized_status(value):
    value = str(value).strip()

    if not value:
        return "Unknown"

    return value


def processing_band(days):
    days = safe_number(days)

    if days <= 7:
        return "0–7 Days"

    if days <= 15:
        return "8–15 Days"

    if days <= 30:
        return "16–30 Days"

    if days <= 45:
        return "31–45 Days"

    return "46+ Days"


def claim_value_band(value):
    value = safe_number(value)

    if value < 25_000:
        return "Below ₹25K"

    if value < 50_000:
        return "₹25K – ₹49.9K"

    if value < 100_000:
        return "₹50K – ₹99.9K"

    if value < 200_000:
        return "₹100K – ₹199.9K"

    return "₹200K+"


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


# ============================================================
# PAGE STYLING
# ============================================================

st.markdown(
    """
    <style>
    .h360-flow {
        background: linear-gradient(
            135deg,
            #f0f9ff 0%,
            #f8fcff 100%
        );
        border: 1px solid #bae6fd;
        border-radius: 18px;
        padding: 22px 24px;
        margin: 8px 0 30px 0;
        box-shadow: 0 5px 18px rgba(3, 105, 161, 0.06);
    }

    .h360-flow-title {
        color: #075985;
        font-size: 1.08rem;
        font-weight: 800;
        margin-bottom: 8px;
    }

    .h360-flow-text {
        color: #5f6b73;
        font-size: 0.95rem;
        line-height: 1.7;
    }

    .h360-section-banner {
        display: flex;
        align-items: center;
        gap: 16px;
        background: linear-gradient(
            135deg,
            #f0f9ff 0%,
            #f8fcff 100%
        );
        border: 1px solid #bae6fd;
        border-left: 5px solid #0284c7;
        border-radius: 16px;
        padding: 18px 20px;
        margin-top: 34px;
        margin-bottom: 18px;
        box-shadow: 0 4px 14px rgba(3, 105, 161, 0.05);
    }

    .h360-section-number {
        min-width: 46px;
        height: 46px;
        border-radius: 13px;
        background: #0369a1;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 0.95rem;
    }

    .h360-section-title {
        color: #075985;
        font-size: 1.22rem;
        font-weight: 800;
        margin-bottom: 4px;
    }

    .h360-section-description {
        color: #64727b;
        font-size: 0.92rem;
        line-height: 1.55;
    }

    .h360-card-heading {
        background: #ffffff;
        border: 1px solid #dbeafe;
        border-radius: 14px;
        padding: 15px 17px;
        margin: 6px 0 10px 0;
        box-shadow: 0 3px 12px rgba(3, 105, 161, 0.04);
    }

    .h360-card-title {
        color: #075985;
        font-weight: 800;
        font-size: 1rem;
        margin-bottom: 4px;
    }

    .h360-card-description {
        color: #6b7780;
        font-size: 0.87rem;
        line-height: 1.5;
    }

    .h360-explanation {
        background: #f8fcff;
        border: 1px solid #dbeafe;
        border-radius: 13px;
        padding: 14px 16px;
        margin-top: 6px;
        margin-bottom: 16px;
    }

    .h360-explanation-title {
        color: #075985;
        font-weight: 800;
        font-size: 0.9rem;
        margin-bottom: 5px;
    }

    .h360-explanation-text {
        color: #64727b;
        font-size: 0.87rem;
        line-height: 1.6;
    }

    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #dbeafe;
        border-radius: 15px;
        padding: 16px;
        box-shadow: 0 4px 14px rgba(3, 105, 161, 0.05);
    }

    div[data-testid="stPlotlyChart"] {
        background: #ffffff;
        border: 1px solid #dbeafe;
        border-radius: 16px;
        padding: 8px;
        box-shadow: 0 4px 14px rgba(3, 105, 161, 0.05);
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid #dbeafe;
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
# DATA
# ============================================================

@st.cache_data(
    ttl=60,
    show_spinner=False,
)
def load_claim_data():
    """
    Claim-grain dataset.

    One row = one warehouse claim.

    Billing and admission attributes are joined only through
    one-to-one / many-to-one paths from each claim.
    """

    return read_sql(
        """
        SELECT
            c.claim_key,
            c.claim_id,
            c.billing_key,
            c.patient_key,
            c.insurer_key,

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
            c.processing_days,

            b.bill_id,
            b.net_amount AS bill_net_amount,
            b.paid_amount AS bill_paid_amount,
            b.outstanding_amount AS bill_outstanding_amount,
            b.payment_status,

            dep.department_name

        FROM warehouse.fact_claim c

        LEFT JOIN warehouse.dim_patient p
            ON p.patient_key = c.patient_key

        LEFT JOIN warehouse.dim_insurer i
            ON i.insurer_key = c.insurer_key

        LEFT JOIN warehouse.dim_date sd
            ON sd.date_key = c.submission_date_key

        LEFT JOIN warehouse.dim_date std
            ON std.date_key = c.settlement_date_key

        LEFT JOIN warehouse.fact_billing b
            ON b.billing_key = c.billing_key

        LEFT JOIN warehouse.fact_admission a
            ON a.admission_key = b.admission_key

        LEFT JOIN warehouse.dim_department dep
            ON dep.department_key = a.department_key
        """
    )


try:
    claims = load_claim_data()

except Exception as exc:
    st.error(
        "Claims Analytics could not load claim-level warehouse data."
    )
    st.exception(exc)
    st.stop()


if claims.empty:
    st.warning(
        "No claim records are available."
    )
    st.stop()


# ============================================================
# NORMALIZATION
# ============================================================

for column in [
    "submission_date",
    "settlement_date",
]:
    claims[column] = pd.to_datetime(
        claims[column],
        errors="coerce",
    )


for column in [
    "claim_amount",
    "approved_amount",
    "rejected_amount",
    "processing_days",
    "bill_net_amount",
    "bill_paid_amount",
    "bill_outstanding_amount",
]:
    claims[column] = pd.to_numeric(
        claims[column],
        errors="coerce",
    ).fillna(0)


for column in [
    "insurer_name",
    "insurer_type",
    "claim_status",
    "rejection_reason",
    "payment_status",
    "department_name",
]:
    claims[column] = (
        claims[column]
        .fillna("Unknown")
        .astype(str)
        .str.strip()
    )


claims["claim_status"] = (
    claims["claim_status"]
    .apply(normalized_status)
)


claims["status_normalized"] = (
    claims["claim_status"]
    .str.upper()
    .str.strip()
)


claims["processing_band"] = (
    claims["processing_days"]
    .apply(processing_band)
)


claims["claim_value_band"] = (
    claims["claim_amount"]
    .apply(claim_value_band)
)


claims["approval_rate_record"] = claims.apply(
    lambda row: pct(
        row["approved_amount"],
        row["claim_amount"],
    ),
    axis=1,
)


claims["rejection_rate_record"] = claims.apply(
    lambda row: pct(
        row["rejected_amount"],
        row["claim_amount"],
    ),
    axis=1,
)


# ============================================================
# INTRODUCTION
# ============================================================

st.markdown(
    """
    <div class="h360-flow">
        <div class="h360-flow-title">
            How to read this dashboard
        </div>
        <div class="h360-flow-text">
            Start with the selected claim population and executive
            scorecard. Review claim outcomes and financial conversion,
            then inspect monthly movement, insurer performance,
            processing efficiency and rejection exposure. Continue
            through claim-value and department concentration before
            reviewing high-value records and individual claims.
            Claim counts, claim values and processing metrics are
            descriptive warehouse measures rather than contractual,
            legal or fraud determinations.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 01 — SCOPE
# ============================================================

page_section(
    "01",
    "Claims Scope",
    (
        "Define the claim population using submission period, "
        "insurer, recorded claim status and hospital department."
    ),
)


filtered = claims.copy()

valid_dates = (
    claims["submission_date"]
    .dropna()
)


f1, f2, f3, f4 = st.columns(4)


with f1:
    if not valid_dates.empty:
        minimum = valid_dates.min().date()
        maximum = valid_dates.max().date()

        period = st.date_input(
            "Submission Period",
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
    insurers = sorted(
        claims["insurer_name"]
        .unique()
        .tolist()
    )

    selected_insurers = st.multiselect(
        "Insurer",
        insurers,
        placeholder="All insurers",
    )


with f3:
    statuses = sorted(
        claims["claim_status"]
        .unique()
        .tolist()
    )

    selected_statuses = st.multiselect(
        "Claim Status",
        statuses,
        placeholder="All statuses",
    )


with f4:
    departments = sorted(
        claims["department_name"]
        .unique()
        .tolist()
    )

    selected_departments = st.multiselect(
        "Department",
        departments,
        placeholder="All departments",
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

    filtered = filtered[
        (
            filtered["submission_date"]
            >= start
        )
        &
        (
            filtered["submission_date"]
            < end
        )
    ]


if selected_insurers:
    filtered = filtered[
        filtered["insurer_name"]
        .isin(selected_insurers)
    ]


if selected_statuses:
    filtered = filtered[
        filtered["claim_status"]
        .isin(selected_statuses)
    ]


if selected_departments:
    filtered = filtered[
        filtered["department_name"]
        .isin(selected_departments)
    ]


if filtered.empty:
    st.warning(
        "No claims match the current filters."
    )
    st.stop()


# ============================================================
# CORE MEASURES
# ============================================================

total_claims = len(filtered)

claim_value = safe_number(
    filtered["claim_amount"].sum()
)

approved_value = safe_number(
    filtered["approved_amount"].sum()
)

rejected_value = safe_number(
    filtered["rejected_amount"].sum()
)


approved_count = int(
    (
        filtered["status_normalized"]
        == "APPROVED"
    ).sum()
)


rejected_count = int(
    (
        filtered["status_normalized"]
        == "REJECTED"
    ).sum()
)


pending_count = int(
    (
        filtered["status_normalized"]
        == "PENDING"
    ).sum()
)


partial_count = int(
    filtered["status_normalized"]
    .isin(
        [
            "PARTIAL",
            "PARTIALLY APPROVED",
            "PARTIALLY_APPROVED",
        ]
    )
    .sum()
)


approval_rate = pct(
    approved_count,
    total_claims,
)

rejection_rate = pct(
    rejected_count,
    total_claims,
)

pending_rate = pct(
    pending_count,
    total_claims,
)

approved_value_rate = pct(
    approved_value,
    claim_value,
)

rejected_value_rate = pct(
    rejected_value,
    claim_value,
)

average_claim = (
    claim_value / total_claims
    if total_claims
    else 0
)

average_processing = safe_number(
    filtered["processing_days"].mean()
)


# ============================================================
# 02 — EXECUTIVE SCORECARD
# ============================================================

page_section(
    "02",
    "Claims Executive Scorecard",
    (
        "Core volume, financial outcome and processing indicators "
        "for the selected claim population."
    ),
)


metric_row(
    [
        (
            "Total Claims",
            format_integer(total_claims),
        ),
        (
            "Claim Value",
            format_currency_compact(
                claim_value
            ),
        ),
        (
            "Approved Value",
            format_currency_compact(
                approved_value
            ),
        ),
        (
            "Rejected Value",
            format_currency_compact(
                rejected_value
            ),
        ),
    ]
)


metric_row(
    [
        (
            "Approval Rate",
            format_percentage(
                approval_rate
            ),
        ),
        (
            "Rejection Rate",
            format_percentage(
                rejection_rate
            ),
        ),
        (
            "Average Claim",
            format_currency_compact(
                average_claim
            ),
        ),
        (
            "Average Processing",
            f"{average_processing:.1f} days",
        ),
    ]
)


management_insight(
    (
        f"The selected scope contains "
        f"{format_integer(total_claims)} claims worth "
        f"{format_currency_compact(claim_value)}. "
        f"{format_integer(approved_count)} claims are recorded as "
        f"approved, {format_integer(rejected_count)} as rejected, "
        f"{format_integer(pending_count)} as pending and "
        f"{format_integer(partial_count)} as partial. "
        f"Recorded rejected value totals "
        f"{format_currency_compact(rejected_value)}, while average "
        f"processing time is {average_processing:.1f} days."
    ),
    label="Claims Management Snapshot",
)


# ============================================================
# 03 — OUTCOMES
# ============================================================

page_section(
    "03",
    "Claim Outcome Intelligence",
    (
        "Separate status-based claim outcomes from recorded "
        "financial values to avoid mixing count and value semantics."
    ),
)


status_summary = (
    filtered.groupby(
        "claim_status",
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
        approved_amount=(
            "approved_amount",
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
    )
)


status_summary["claim_share_pct"] = (
    status_summary.apply(
        lambda row: pct(
            row["claims"],
            total_claims,
        ),
        axis=1,
    )
)


left, right = st.columns(2)


with left:
    card_heading(
        "Claims by Recorded Status",
        (
            "Count of claim records grouped by their "
            "recorded warehouse claim status."
        ),
    )

    chart = status_summary.sort_values(
        "claims",
        ascending=False,
    )

    fig = px.bar(
        chart,
        x="claim_status",
        y="claims",
        text_auto=True,
    )

    fig.update_xaxes(
        title=None
    )

    fig.update_yaxes(
        title="Claims"
    )

    st.plotly_chart(
        style_figure(
            fig,
            390,
        ),
        width="stretch",
    )


with right:
    card_heading(
        "Claim Status Share",
        (
            "Percentage of selected claim records represented "
            "by each recorded status."
        ),
    )

    fig = px.pie(
        status_summary,
        names="claim_status",
        values="claims",
        hole=0.55,
    )

    st.plotly_chart(
        style_figure(
            fig,
            390,
        ),
        width="stretch",
    )


explanation_box(
    "Status-rate semantics",
    (
        "Approval and rejection rates on this page are count-based. "
        "For example, Approval Rate equals claims whose recorded "
        "status is Approved divided by total claims in the selected "
        "population. These rates are distinct from approved-value "
        "and rejected-value percentages."
    ),
)


# ============================================================
# 04 — VALUE CONVERSION
# ============================================================

page_section(
    "04",
    "Claim Value Conversion",
    (
        "Show how submitted claim value is represented by "
        "recorded approved and rejected amounts."
    ),
)


metric_row(
    [
        (
            "Approved Value / Claim Value",
            format_percentage(
                approved_value_rate
            ),
        ),
        (
            "Rejected Value / Claim Value",
            format_percentage(
                rejected_value_rate
            ),
        ),
        (
            "Pending Claim Share",
            format_percentage(
                pending_rate
            ),
        ),
        (
            "Rejected Claim Share",
            format_percentage(
                rejection_rate
            ),
        ),
    ]
)


value_summary = pd.DataFrame(
    {
        "Value Type": [
            "Total Claim Value",
            "Approved Value",
            "Rejected Value",
        ],
        "Amount": [
            claim_value,
            approved_value,
            rejected_value,
        ],
    }
)


left, right = st.columns([1, 1])


with left:
    card_heading(
        "Claims Value Position",
        (
            "Absolute recorded submitted, approved "
            "and rejected claim values."
        ),
    )

    fig = px.bar(
        value_summary,
        x="Value Type",
        y="Amount",
        text_auto=True,
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
            390,
        ),
        width="stretch",
    )


with right:
    card_heading(
        "Recorded Value Conversion",
        (
            "Relative share of submitted claim value represented "
            "by approved and rejected amounts."
        ),
    )

    conversion = pd.DataFrame(
        {
            "Metric": [
                "Approved Value",
                "Rejected Value",
            ],
            "Percentage": [
                approved_value_rate,
                rejected_value_rate,
            ],
        }
    )

    fig = px.bar(
        conversion,
        x="Metric",
        y="Percentage",
        text_auto=True,
    )

    fig.update_xaxes(
        title=None
    )

    fig.update_yaxes(
        title="Share of Claim Value (%)"
    )

    st.plotly_chart(
        style_figure(
            fig,
            390,
        ),
        width="stretch",
    )


st.caption(
    "Approved and rejected amounts are reported directly from claim "
    "records. They are not cash receipts or accounting collections."
)


# ============================================================
# 05 — MONTHLY TREND
# ============================================================

page_section(
    "05",
    "Claims Trend",
    (
        "Track submission volume, financial value and rejection "
        "behavior over time."
    ),
)


monthly = filtered[
    filtered["submission_date"].notna()
].copy()


monthly["month_start"] = (
    monthly["submission_date"]
    .dt.to_period("M")
    .dt.to_timestamp()
)


monthly = (
    monthly.groupby(
        "month_start",
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
        approved_amount=(
            "approved_amount",
            "sum",
        ),
        rejected_amount=(
            "rejected_amount",
            "sum",
        ),
        rejected_claims=(
            "status_normalized",
            lambda values:
                (values == "REJECTED").sum(),
        ),
        pending_claims=(
            "status_normalized",
            lambda values:
                (values == "PENDING").sum(),
        ),
        average_processing_days=(
            "processing_days",
            "mean",
        ),
    )
    .sort_values(
        "month_start"
    )
)


monthly["rejection_rate_pct"] = (
    monthly.apply(
        lambda row: pct(
            row["rejected_claims"],
            row["claims"],
        ),
        axis=1,
    )
)


left, right = st.columns(2)


with left:
    card_heading(
        "Monthly Claim Submissions",
        (
            "Submission volume based on the recorded "
            "claim submission date."
        ),
    )

    fig = px.line(
        monthly,
        x="month_start",
        y="claims",
        markers=True,
    )

    fig.update_xaxes(
        title=None
    )

    fig.update_yaxes(
        title="Claims"
    )

    st.plotly_chart(
        style_figure(
            fig,
            400,
            unified_hover=True,
        ),
        width="stretch",
    )


with right:
    card_heading(
        "Monthly Rejection Rate",
        (
            "Count-based rejected-claim share for each "
            "submission month."
        ),
    )

    fig = px.line(
        monthly,
        x="month_start",
        y="rejection_rate_pct",
        markers=True,
    )

    fig.update_xaxes(
        title=None
    )

    fig.update_yaxes(
        title="Rejection Rate (%)"
    )

    st.plotly_chart(
        style_figure(
            fig,
            400,
            unified_hover=True,
        ),
        width="stretch",
    )


card_heading(
    "Monthly Claim Value Movement",
    (
        "Submitted, approved and rejected values "
        "by claim submission month."
    ),
)


monthly_values = monthly[
    [
        "month_start",
        "claim_amount",
        "approved_amount",
        "rejected_amount",
    ]
].melt(
    id_vars="month_start",
    var_name="Metric",
    value_name="Amount",
)


monthly_values["Metric"] = (
    monthly_values["Metric"]
    .map(
        {
            "claim_amount":
                "Claim Value",
            "approved_amount":
                "Approved Value",
            "rejected_amount":
                "Rejected Value",
        }
    )
)


fig = px.line(
    monthly_values,
    x="month_start",
    y="Amount",
    color="Metric",
    markers=True,
)


fig.update_xaxes(
    title=None
)


st.plotly_chart(
    style_figure(
        fig,
        420,
        unified_hover=True,
    ),
    width="stretch",
)


# ============================================================
# 06 — INSURER PERFORMANCE
# ============================================================

page_section(
    "06",
    "Insurer Performance",
    (
        "Compare payer claim volume, value conversion, "
        "rejection exposure and processing performance."
    ),
)


insurer = (
    filtered.groupby(
        [
            "insurer_name",
            "insurer_type",
        ],
        dropna=False,
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
        approved_amount=(
            "approved_amount",
            "sum",
        ),
        rejected_amount=(
            "rejected_amount",
            "sum",
        ),
        approved_claims=(
            "status_normalized",
            lambda values:
                (values == "APPROVED").sum(),
        ),
        rejected_claims=(
            "status_normalized",
            lambda values:
                (values == "REJECTED").sum(),
        ),
        pending_claims=(
            "status_normalized",
            lambda values:
                (values == "PENDING").sum(),
        ),
        average_processing_days=(
            "processing_days",
            "mean",
        ),
    )
)


insurer["approval_rate_pct"] = insurer.apply(
    lambda row: pct(
        row["approved_claims"],
        row["claims"],
    ),
    axis=1,
)


insurer["rejection_rate_pct"] = insurer.apply(
    lambda row: pct(
        row["rejected_claims"],
        row["claims"],
    ),
    axis=1,
)


insurer["approved_value_rate_pct"] = insurer.apply(
    lambda row: pct(
        row["approved_amount"],
        row["claim_amount"],
    ),
    axis=1,
)


left, right = st.columns(2)


with left:
    card_heading(
        "Claim Value by Insurer",
        (
            "Aggregate submitted claim value associated "
            "with each insurer."
        ),
    )

    chart = insurer.sort_values(
        "claim_amount",
        ascending=True,
    )

    fig = px.bar(
        chart,
        x="claim_amount",
        y="insurer_name",
        orientation="h",
        text_auto=True,
    )

    fig.update_yaxes(
        title=None
    )

    fig.update_xaxes(
        title="Claim Value"
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
        "Rejected Value by Insurer",
        (
            "Aggregate recorded rejected amount "
            "associated with each insurer."
        ),
    )

    chart = insurer.sort_values(
        "rejected_amount",
        ascending=True,
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
        title="Rejected Value"
    )

    st.plotly_chart(
        style_figure(
            fig,
            420,
        ),
        width="stretch",
    )


left, right = st.columns(2)


with left:
    card_heading(
        "Rejection Rate by Insurer",
        (
            "Count-based rejected-claim share for "
            "each insurer in the selected scope."
        ),
    )

    chart = insurer.sort_values(
        "rejection_rate_pct",
        ascending=True,
    )

    fig = px.bar(
        chart,
        x="rejection_rate_pct",
        y="insurer_name",
        orientation="h",
        text_auto=True,
    )

    fig.update_yaxes(
        title=None
    )

    fig.update_xaxes(
        title="Rejection Rate (%)"
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
        "Average Processing by Insurer",
        (
            "Average recorded claim processing duration "
            "for each insurer."
        ),
    )

    chart = insurer.sort_values(
        "average_processing_days",
        ascending=True,
    )

    fig = px.bar(
        chart,
        x="average_processing_days",
        y="insurer_name",
        orientation="h",
        text_auto=True,
    )

    fig.update_yaxes(
        title=None
    )

    fig.update_xaxes(
        title="Average Processing Days"
    )

    st.plotly_chart(
        style_figure(
            fig,
            420,
        ),
        width="stretch",
    )


insurer_display = insurer[
    [
        "insurer_name",
        "insurer_type",
        "claims",
        "claim_amount",
        "approved_amount",
        "rejected_amount",
        "approved_claims",
        "rejected_claims",
        "pending_claims",
        "approval_rate_pct",
        "rejection_rate_pct",
        "approved_value_rate_pct",
        "average_processing_days",
    ]
].rename(
    columns={
        "insurer_name":
            "Insurer",
        "insurer_type":
            "Type",
        "claims":
            "Claims",
        "claim_amount":
            "Claim Value",
        "approved_amount":
            "Approved Value",
        "rejected_amount":
            "Rejected Value",
        "approved_claims":
            "Approved Claims",
        "rejected_claims":
            "Rejected Claims",
        "pending_claims":
            "Pending Claims",
        "approval_rate_pct":
            "Approval Rate %",
        "rejection_rate_pct":
            "Rejection Rate %",
        "approved_value_rate_pct":
            "Approved Value Rate %",
        "average_processing_days":
            "Avg Processing Days",
    }
)


card_heading(
    "Insurer Performance Table",
    (
        "Detailed payer-level comparison across volume, "
        "financial outcomes and processing measures."
    ),
)


dataframe(
    insurer_display,
    height=400,
)


explanation_box(
    "Payer interpretation boundary",
    (
        "These comparisons describe historical records in the "
        "synthetic Hospital 360 dataset. They do not constitute "
        "contractual, legal or insurer-quality assessments."
    ),
)


# ============================================================
# 07 — PROCESSING
# ============================================================

page_section(
    "07",
    "Processing-Time Intelligence",
    (
        "Identify the distribution and concentration of "
        "recorded claim processing duration."
    ),
)


processing_order = [
    "0–7 Days",
    "8–15 Days",
    "16–30 Days",
    "31–45 Days",
    "46+ Days",
]


processing = (
    filtered["processing_band"]
    .value_counts()
    .reindex(
        processing_order,
        fill_value=0,
    )
    .rename_axis(
        "Processing Band"
    )
    .reset_index(
        name="Claims"
    )
)


slow_claims = int(
    (
        filtered["processing_days"]
        > 30
    ).sum()
)


metric_row(
    [
        (
            "Average Processing",
            f"{average_processing:.1f} days",
        ),
        (
            "Claims > 30 Days",
            format_integer(
                slow_claims
            ),
        ),
        (
            "Claims > 30 Days Share",
            format_percentage(
                pct(
                    slow_claims,
                    total_claims,
                )
            ),
        ),
        (
            "Maximum Processing",
            (
                f"{safe_number(filtered['processing_days'].max()):.0f} days"
            ),
        ),
    ]
)


card_heading(
    "Processing-Time Distribution",
    (
        "Claim volume grouped into consistent recorded "
        "processing-duration bands."
    ),
)


fig = px.bar(
    processing,
    x="Processing Band",
    y="Claims",
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


# ============================================================
# 08 — REJECTION INTELLIGENCE
# ============================================================

page_section(
    "08",
    "Rejection Intelligence",
    (
        "Analyze recorded rejection reasons, rejected "
        "claim counts and associated financial exposure."
    ),
)


rejected = filtered[
    (
        filtered["status_normalized"]
        == "REJECTED"
    )
    |
    (
        filtered["rejected_amount"]
        > 0
    )
].copy()


if not rejected.empty:
    rejection_reason = (
        rejected.groupby(
            "rejection_reason",
            as_index=False,
        )
        .agg(
            claims=(
                "claim_id",
                "count",
            ),
            rejected_amount=(
                "rejected_amount",
                "sum",
            ),
            claim_amount=(
                "claim_amount",
                "sum",
            ),
            average_processing_days=(
                "processing_days",
                "mean",
            ),
        )
        .sort_values(
            "rejected_amount",
            ascending=False,
        )
    )


    rejection_reason[
        "rejected_value_share_pct"
    ] = rejection_reason.apply(
        lambda row: pct(
            row["rejected_amount"],
            rejected_value,
        ),
        axis=1,
    )


    left, right = st.columns(2)


    with left:
        card_heading(
            "Rejected Claims by Reason",
            (
                "Count of affected claims grouped by "
                "recorded rejection reason."
            ),
        )

        chart = (
            rejection_reason
            .head(15)
            .sort_values(
                "claims",
                ascending=True,
            )
        )

        fig = px.bar(
            chart,
            x="claims",
            y="rejection_reason",
            orientation="h",
            text_auto=True,
        )

        fig.update_yaxes(
            title=None
        )

        fig.update_xaxes(
            title="Claims"
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
            "Rejected Value by Reason",
            (
                "Recorded rejected financial value "
                "associated with each reason."
            ),
        )

        chart = (
            rejection_reason
            .head(15)
            .sort_values(
                "rejected_amount",
                ascending=True,
            )
        )

        fig = px.bar(
            chart,
            x="rejected_amount",
            y="rejection_reason",
            orientation="h",
            text_auto=True,
        )

        fig.update_yaxes(
            title=None
        )

        fig.update_xaxes(
            title="Rejected Value"
        )

        st.plotly_chart(
            style_figure(
                fig,
                430,
            ),
            width="stretch",
        )


    rejection_display = (
        rejection_reason.rename(
            columns={
                "rejection_reason":
                    "Rejection Reason",
                "claims":
                    "Claims",
                "rejected_amount":
                    "Rejected Value",
                "claim_amount":
                    "Claim Value",
                "average_processing_days":
                    "Avg Processing Days",
                "rejected_value_share_pct":
                    "Rejected Value Share %",
            }
        )
    )


    card_heading(
        "Rejection Reason Table",
        (
            "Detailed view of rejection frequency, "
            "financial exposure and processing duration."
        ),
    )


    dataframe(
        rejection_display,
        height=390,
    )

else:
    st.success(
        "No rejected claims or rejected values exist "
        "in the current selection."
    )


# ============================================================
# 09 — VALUE CONCENTRATION
# ============================================================

page_section(
    "09",
    "Claim Value Concentration",
    (
        "Understand where claim volume and rejected "
        "financial exposure sit across claim-size bands."
    ),
)


value_band_order = [
    "Below ₹25K",
    "₹25K – ₹49.9K",
    "₹50K – ₹99.9K",
    "₹100K – ₹199.9K",
    "₹200K+",
]


value_bands = (
    filtered.groupby(
        "claim_value_band",
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
        approved_amount=(
            "approved_amount",
            "sum",
        ),
        rejected_amount=(
            "rejected_amount",
            "sum",
        ),
    )
)


value_bands["claim_value_band"] = pd.Categorical(
    value_bands["claim_value_band"],
    categories=value_band_order,
    ordered=True,
)


value_bands = value_bands.sort_values(
    "claim_value_band"
)


left, right = st.columns(2)


with left:
    card_heading(
        "Claims by Value Band",
        (
            "Distribution of claim records across "
            "defined submitted-value ranges."
        ),
    )

    fig = px.bar(
        value_bands,
        x="claim_value_band",
        y="claims",
        text_auto=True,
    )

    fig.update_xaxes(
        title=None
    )

    fig.update_yaxes(
        title="Claims"
    )

    st.plotly_chart(
        style_figure(
            fig,
            390,
        ),
        width="stretch",
    )


with right:
    card_heading(
        "Rejected Value by Claim Band",
        (
            "Recorded rejected amount concentrated "
            "within each claim-size range."
        ),
    )

    fig = px.bar(
        value_bands,
        x="claim_value_band",
        y="rejected_amount",
        text_auto=True,
    )

    fig.update_xaxes(
        title=None
    )

    fig.update_yaxes(
        title="Rejected Value"
    )

    st.plotly_chart(
        style_figure(
            fig,
            390,
        ),
        width="stretch",
    )


# ============================================================
# 10 — DEPARTMENT EXPOSURE
# ============================================================

page_section(
    "10",
    "Department Claims Exposure",
    (
        "Attribute claims to hospital departments through "
        "their associated billing and admission records."
    ),
)


department = (
    filtered.groupby(
        "department_name",
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
        approved_amount=(
            "approved_amount",
            "sum",
        ),
        rejected_amount=(
            "rejected_amount",
            "sum",
        ),
        rejected_claims=(
            "status_normalized",
            lambda values:
                (values == "REJECTED").sum(),
        ),
        average_processing_days=(
            "processing_days",
            "mean",
        ),
    )
)


department["rejection_rate_pct"] = (
    department.apply(
        lambda row: pct(
            row["rejected_claims"],
            row["claims"],
        ),
        axis=1,
    )
)


left, right = st.columns(2)


with left:
    card_heading(
        "Claim Value by Department",
        (
            "Aggregate submitted claim value attributed "
            "to each hospital department."
        ),
    )

    chart = department.sort_values(
        "claim_amount",
        ascending=True,
    )

    fig = px.bar(
        chart,
        x="claim_amount",
        y="department_name",
        orientation="h",
        text_auto=True,
    )

    fig.update_yaxes(
        title=None
    )

    fig.update_xaxes(
        title="Claim Value"
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
        "Rejected Value by Department",
        (
            "Recorded rejected claim value attributed "
            "to each hospital department."
        ),
    )

    chart = department.sort_values(
        "rejected_amount",
        ascending=True,
    )

    fig = px.bar(
        chart,
        x="rejected_amount",
        y="department_name",
        orientation="h",
        text_auto=True,
    )

    fig.update_yaxes(
        title=None
    )

    fig.update_xaxes(
        title="Rejected Value"
    )

    st.plotly_chart(
        style_figure(
            fig,
            430,
        ),
        width="stretch",
    )


# ============================================================
# 11 — HIGH VALUE REGISTER
# ============================================================

page_section(
    "11",
    "High-Value Claim Register",
    (
        "Surface the largest individual claims for "
        "financial visibility and management review."
    ),
)


high_value = (
    filtered.sort_values(
        [
            "claim_amount",
            "rejected_amount",
        ],
        ascending=[
            False,
            False,
        ],
    )
    .head(100)
)


high_value_display = high_value[
    [
        "claim_id",
        "patient_id",
        "insurer_name",
        "department_name",
        "submission_date",
        "settlement_date",
        "claim_status",
        "claim_amount",
        "approved_amount",
        "rejected_amount",
        "processing_days",
        "rejection_reason",
    ]
].rename(
    columns={
        "claim_id":
            "Claim ID",
        "patient_id":
            "Patient ID",
        "insurer_name":
            "Insurer",
        "department_name":
            "Department",
        "submission_date":
            "Submitted",
        "settlement_date":
            "Settled",
        "claim_status":
            "Status",
        "claim_amount":
            "Claim Value",
        "approved_amount":
            "Approved Value",
        "rejected_amount":
            "Rejected Value",
        "processing_days":
            "Processing Days",
        "rejection_reason":
            "Rejection Reason",
    }
)


dataframe(
    high_value_display,
    height=460,
)


st.caption(
    "The register is ranked by submitted claim value and then "
    "recorded rejected value. Inclusion does not indicate an error "
    "or inappropriate claim."
)


# ============================================================
# 12 — MANAGEMENT SIGNALS
# ============================================================

page_section(
    "12",
    "Claims Review Signals",
    (
        "Surface deterministic concentrations in payer, "
        "rejection, processing and individual claim exposure."
    ),
)


signals = []


if not insurer.empty:
    row = (
        insurer.sort_values(
            "claim_amount",
            ascending=False,
        )
        .iloc[0]
    )

    signals.append(
        {
            "Signal":
                "Largest Claim Value",
            "Entity":
                row["insurer_name"],
            "Value":
                format_currency_compact(
                    row["claim_amount"]
                ),
            "Review Context":
                (
                    "Largest aggregate claim value "
                    "among insurers."
                ),
        }
    )


    row = (
        insurer.sort_values(
            "rejected_amount",
            ascending=False,
        )
        .iloc[0]
    )

    signals.append(
        {
            "Signal":
                "Largest Rejected Value",
            "Entity":
                row["insurer_name"],
            "Value":
                format_currency_compact(
                    row["rejected_amount"]
                ),
            "Review Context":
                (
                    "Largest aggregate rejected claim "
                    "value among insurers."
                ),
        }
    )


    meaningful = insurer[
        insurer["claims"] >= 25
    ]


    if not meaningful.empty:
        row = (
            meaningful.sort_values(
                "rejection_rate_pct",
                ascending=False,
            )
            .iloc[0]
        )

        signals.append(
            {
                "Signal":
                    "Highest Rejection Rate",
                "Entity":
                    row["insurer_name"],
                "Value":
                    format_percentage(
                        row["rejection_rate_pct"]
                    ),
                "Review Context":
                    (
                        "Highest recorded rejection share "
                        "among insurers with at least 25 claims."
                    ),
            }
        )


        row = (
            meaningful.sort_values(
                "average_processing_days",
                ascending=False,
            )
            .iloc[0]
        )

        signals.append(
            {
                "Signal":
                    "Longest Average Processing",
                "Entity":
                    row["insurer_name"],
                "Value":
                    (
                        f"{row['average_processing_days']:.1f} days"
                    ),
                "Review Context":
                    (
                        "Longest average recorded processing "
                        "time among insurers with at least 25 claims."
                    ),
            }
        )


if not monthly.empty:
    row = (
        monthly.sort_values(
            "rejected_amount",
            ascending=False,
        )
        .iloc[0]
    )

    signals.append(
        {
            "Signal":
                "Highest Monthly Rejected Value",
            "Entity":
                row["month_start"].strftime(
                    "%b %Y"
                ),
            "Value":
                format_currency_compact(
                    row["rejected_amount"]
                ),
            "Review Context":
                (
                    "Submission month with the largest "
                    "recorded rejected claim value."
                ),
        }
    )


if not filtered.empty:
    row = (
        filtered.sort_values(
            "claim_amount",
            ascending=False,
        )
        .iloc[0]
    )

    signals.append(
        {
            "Signal":
                "Largest Individual Claim",
            "Entity":
                row["claim_id"],
            "Value":
                format_currency_compact(
                    row["claim_amount"]
                ),
            "Review Context":
                (
                    "Largest individual submitted claim "
                    "value in the selected scope."
                ),
        }
    )


if signals:
    dataframe(
        pd.DataFrame(signals),
        height=390,
    )


explanation_box(
    "How to use review signals",
    (
        "These observations identify concentrations directly from "
        "the selected claim population. They indicate areas for "
        "management investigation and do not constitute findings "
        "of fraud, misconduct, contractual non-compliance or "
        "insurer-quality problems."
    ),
)


# ============================================================
# 13 — CLAIM EXPLORER
# ============================================================

page_section(
    "13",
    "Claim Explorer",
    (
        "Search and inspect individual claim records, "
        "payer outcomes, financial values and processing details."
    ),
)


s1, s2, s3 = st.columns(
    [2, 1, 1]
)


with s1:
    search = st.text_input(
        "Search Claim / Patient / Bill",
        placeholder=(
            "Enter claim ID, patient ID or bill ID..."
        ),
    )


with s2:
    selected_processing_band = (
        st.selectbox(
            "Processing Band",
            [
                "All",
                *processing_order,
            ],
        )
    )


with s3:
    selected_value_band = (
        st.selectbox(
            "Claim Value Band",
            [
                "All",
                *value_band_order,
            ],
        )
    )


explorer = filtered.copy()


if search.strip():
    query = search.strip().lower()

    explorer = explorer[
        (
            explorer["claim_id"]
            .astype(str)
            .str.lower()
            .str.contains(
                query,
                na=False,
            )
        )
        |
        (
            explorer["patient_id"]
            .astype(str)
            .str.lower()
            .str.contains(
                query,
                na=False,
            )
        )
        |
        (
            explorer["bill_id"]
            .astype(str)
            .str.lower()
            .str.contains(
                query,
                na=False,
            )
        )
    ]


if selected_processing_band != "All":
    explorer = explorer[
        explorer["processing_band"]
        == selected_processing_band
    ]


if selected_value_band != "All":
    explorer = explorer[
        explorer["claim_value_band"]
        == selected_value_band
    ]


explorer = explorer.sort_values(
    [
        "submission_date",
        "claim_amount",
    ],
    ascending=[
        False,
        False,
    ],
)


explorer_display = explorer[
    [
        "claim_id",
        "bill_id",
        "patient_id",
        "insurer_name",
        "department_name",
        "submission_date",
        "settlement_date",
        "claim_status",
        "claim_amount",
        "approved_amount",
        "rejected_amount",
        "processing_days",
        "processing_band",
        "rejection_reason",
    ]
].rename(
    columns={
        "claim_id":
            "Claim ID",
        "bill_id":
            "Bill ID",
        "patient_id":
            "Patient ID",
        "insurer_name":
            "Insurer",
        "department_name":
            "Department",
        "submission_date":
            "Submitted",
        "settlement_date":
            "Settled",
        "claim_status":
            "Status",
        "claim_amount":
            "Claim Value",
        "approved_amount":
            "Approved Value",
        "rejected_amount":
            "Rejected Value",
        "processing_days":
            "Processing Days",
        "processing_band":
            "Processing Band",
        "rejection_reason":
            "Rejection Reason",
    }
)


dataframe(
    explorer_display,
    height=520,
)


st.caption(
    f"Showing {format_integer(len(explorer_display))} claim records."
)


# ============================================================
# 14 — SEMANTICS
# ============================================================

page_section(
    "14",
    "Claims Metric Semantics",
    (
        "Document the definitions and interpretation boundaries "
        "used throughout the Claims Analytics workspace."
    ),
)


semantics = pd.DataFrame(
    [
        {
            "Metric":
                "Claim Value",
            "Interpretation":
                (
                    "Recorded claim_amount submitted "
                    "against insurance."
                ),
        },
        {
            "Metric":
                "Approved Value",
            "Interpretation":
                (
                    "Recorded approved_amount on "
                    "claim records."
                ),
        },
        {
            "Metric":
                "Rejected Value",
            "Interpretation":
                (
                    "Recorded rejected_amount on "
                    "claim records."
                ),
        },
        {
            "Metric":
                "Approval Rate",
            "Interpretation":
                (
                    "Count of claims whose recorded status is "
                    "Approved divided by total claims in scope."
                ),
        },
        {
            "Metric":
                "Rejection Rate",
            "Interpretation":
                (
                    "Count of claims whose recorded status is "
                    "Rejected divided by total claims in scope."
                ),
        },
        {
            "Metric":
                "Approved Value Rate",
            "Interpretation":
                (
                    "Recorded approved amount divided by "
                    "recorded submitted claim value."
                ),
        },
        {
            "Metric":
                "Processing Days",
            "Interpretation":
                (
                    "Recorded claim processing duration. "
                    "It is not inferred from settlement dates."
                ),
        },
        {
            "Metric":
                "Payer Performance",
            "Interpretation":
                (
                    "Descriptive historical analytics within the "
                    "synthetic dataset; not a contractual, legal "
                    "or quality assessment."
                ),
        },
    ]
)


dataframe(
    semantics,
    height=390,
)


# ============================================================
# 15 — CONTINUE
# ============================================================

page_section(
    "15",
    "Continue the Analysis",
    (
        "Move between enterprise risk, claims intelligence "
        "and the next analytical workspace."
    ),
)


nav1, nav2 = st.columns(2)


with nav1:
    card_heading(
        "Risk Analytics",
        (
            "Return to enterprise patient, financial "
            "and claims risk intelligence."
        ),
    )

    st.page_link(
        "pages/05_Risk_Analytics_Dashboard.py",
        label="Open Risk Analytics",
        icon="⚠️",
        width="stretch",
    )


with nav2:
    card_heading(
        "Next Workspace",
        (
            "Continue through the Hospital 360 "
            "enterprise analytics workflow."
        ),
    )

    st.info(
        "Use this card for the next dashboard in your "
        "final page sequence."
    )


# ============================================================
# DIAGNOSTICS
# ============================================================

with st.expander(
    "Technical Data Diagnostics",
    expanded=False,
):
    diagnostics = pd.DataFrame(
        [
            {
                "Measure":
                    "Warehouse Claims",
                "Value":
                    len(claims),
            },
            {
                "Measure":
                    "Claims in Current Scope",
                "Value":
                    len(filtered),
            },
            {
                "Measure":
                    "Unique Claim IDs",
                "Value":
                    filtered["claim_id"].nunique(),
            },
            {
                "Measure":
                    "Unique Insurers",
                "Value":
                    filtered["insurer_name"].nunique(),
            },
            {
                "Measure":
                    "Unique Patients",
                "Value":
                    filtered["patient_id"].nunique(),
            },
            {
                "Measure":
                    "Analytical Grain",
                "Value":
                    "Claim",
            },
        ]
    )

    dataframe(
        diagnostics,
        height=280,
    )


# ============================================================
# FOOTER
# ============================================================

st.info(
    "Claims analytics are based on synthetic Hospital 360 data. "
    "Rejection, processing-time and payer signals support analytical "
    "management review only. They do not establish fraud, misconduct, "
    "contractual non-compliance or insurer quality."
)


st.divider()


footer_left, footer_right = st.columns(
    [4, 1]
)


with footer_left:
    st.caption(
        "Claims Analytics · Hospital 360 Enterprise Intelligence "
        "Platform · Claim-grain analytics · Synthetic healthcare data · "
        "Downloads and report generation remain centralized in the "
        "Admin Control Center."
    )


with footer_right:
    render_refresh_button(
        key="claims_refresh",
    )