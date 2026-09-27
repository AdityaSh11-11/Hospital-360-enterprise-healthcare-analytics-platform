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
    title="Finance Analytics",
    subtitle=(
        "CFO and revenue-cycle intelligence for billing, collections, "
        "recorded outstanding exposure, payment behavior, charge "
        "composition and department-level financial performance."
    ),
    icon="💰",
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


def exposure_band(value):
    value = safe_number(value)

    if value <= 0:
        return "No Outstanding"

    if value < 10_000:
        return "Below ₹10K"

    if value < 25_000:
        return "₹10K – ₹24.9K"

    if value < 50_000:
        return "₹25K – ₹49.9K"

    return "₹50K+"


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
def load_finance_data():
    return read_sql(
        """
        SELECT
            b.billing_key,
            b.bill_id,
            b.admission_key,
            b.patient_key,
            d.full_date AS billing_date,
            p.patient_id,
            dep.department_name,
            b.room_charge,
            b.doctor_charge,
            b.procedure_charge,
            b.medication_charge,
            b.lab_charge,
            b.other_charge,
            b.gross_amount,
            b.discount_amount,
            b.insurance_amount,
            b.patient_amount,
            b.tax_amount,
            b.net_amount,
            b.paid_amount,
            b.outstanding_amount,
            b.payment_status,
            b.payment_method
        FROM warehouse.fact_billing b

        INNER JOIN warehouse.dim_date d
            ON d.date_key = b.billing_date_key

        LEFT JOIN warehouse.fact_admission a
            ON a.admission_key = b.admission_key

        LEFT JOIN warehouse.dim_department dep
            ON dep.department_key = a.department_key

        LEFT JOIN warehouse.dim_patient p
            ON p.patient_key = b.patient_key
        """
    )


try:
    finance = load_finance_data()

except Exception as exc:
    st.error(
        "Finance Analytics could not load billing data."
    )
    st.exception(exc)
    st.stop()


if finance.empty:
    st.warning(
        "No billing records are available."
    )
    st.stop()


finance["billing_date"] = pd.to_datetime(
    finance["billing_date"],
    errors="coerce",
)


numeric_columns = [
    "room_charge",
    "doctor_charge",
    "procedure_charge",
    "medication_charge",
    "lab_charge",
    "other_charge",
    "gross_amount",
    "discount_amount",
    "insurance_amount",
    "patient_amount",
    "tax_amount",
    "net_amount",
    "paid_amount",
    "outstanding_amount",
]


for column in numeric_columns:
    finance[column] = pd.to_numeric(
        finance[column],
        errors="coerce",
    ).fillna(0)


for column in [
    "department_name",
    "payment_status",
    "payment_method",
]:
    finance[column] = (
        finance[column]
        .fillna("Unknown")
        .astype(str)
    )


finance["exposure_band"] = (
    finance["outstanding_amount"]
    .apply(exposure_band)
)


st.markdown(
    """
    <div class="h360-flow">
        <div class="h360-flow-title">
            How to read this dashboard
        </div>
        <div class="h360-flow-text">
            Begin with the finance scope and CFO scorecard.
            Then follow billing and recorded collection movement
            over time. Continue through payment behavior, financial
            responsibility and charge composition. Compare department
            performance, review outstanding exposure, inspect high-value
            balances and finish with the billing explorer. All report
            generation and downloads remain centralized in the Admin
            Control Center.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


page_section(
    "01",
    "Finance Scope",
    (
        "Define the billing period, department, payment status "
        "and payment method used throughout this dashboard."
    ),
)


filtered = finance.copy()

valid_dates = filtered[
    "billing_date"
].dropna()


f1, f2, f3, f4 = st.columns(4)


with f1:
    if not valid_dates.empty:
        minimum = valid_dates.min().date()
        maximum = valid_dates.max().date()

        period = st.date_input(
            "Billing Period",
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
        finance[
            "department_name"
        ].unique().tolist()
    )

    selected_departments = st.multiselect(
        "Department",
        departments,
        placeholder="All departments",
    )


with f3:
    statuses = sorted(
        finance[
            "payment_status"
        ].unique().tolist()
    )

    selected_statuses = st.multiselect(
        "Payment Status",
        statuses,
        placeholder="All statuses",
    )


with f4:
    methods = sorted(
        finance[
            "payment_method"
        ].unique().tolist()
    )

    selected_methods = st.multiselect(
        "Payment Method",
        methods,
        placeholder="All methods",
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
            filtered[
                "billing_date"
            ] >= start
        )
        &
        (
            filtered[
                "billing_date"
            ] < end
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


if selected_statuses:
    filtered = filtered[
        filtered[
            "payment_status"
        ].isin(
            selected_statuses
        )
    ]


if selected_methods:
    filtered = filtered[
        filtered[
            "payment_method"
        ].isin(
            selected_methods
        )
    ]


if filtered.empty:
    st.warning(
        "No billing records match the current filters."
    )
    st.stop()


bills = len(filtered)

patients = filtered[
    "patient_id"
].nunique()

gross = safe_number(
    filtered[
        "gross_amount"
    ].sum()
)

discount = safe_number(
    filtered[
        "discount_amount"
    ].sum()
)

tax = safe_number(
    filtered[
        "tax_amount"
    ].sum()
)

net = safe_number(
    filtered[
        "net_amount"
    ].sum()
)

paid = safe_number(
    filtered[
        "paid_amount"
    ].sum()
)

outstanding = safe_number(
    filtered[
        "outstanding_amount"
    ].sum()
)

insurance = safe_number(
    filtered[
        "insurance_amount"
    ].sum()
)

patient_responsibility = safe_number(
    filtered[
        "patient_amount"
    ].sum()
)

collection_efficiency = pct(
    paid,
    net,
)

outstanding_rate = pct(
    outstanding,
    net,
)

discount_rate = pct(
    discount,
    gross,
)

average_bill = (
    net / bills
    if bills
    else 0
)


page_section(
    "02",
    "CFO Scorecard",
    (
        "Executive summary of billing volume, revenue, recorded "
        "collections, outstanding balances and discounts."
    ),
)


metric_row(
    [
        (
            "Bills",
            format_integer(
                bills
            ),
        ),
        (
            "Billed Patients",
            format_integer(
                patients
            ),
        ),
        (
            "Gross Revenue",
            format_currency_compact(
                gross
            ),
        ),
        (
            "Net Revenue",
            format_currency_compact(
                net
            ),
        ),
    ]
)


metric_row(
    [
        (
            "Recorded Paid",
            format_currency_compact(
                paid
            ),
        ),
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
            "Average Bill",
            format_currency_compact(
                average_bill
            ),
        ),
    ]
)


metric_row(
    [
        (
            "Discount Amount",
            format_currency_compact(
                discount
            ),
        ),
        (
            "Discount Rate",
            format_percentage(
                discount_rate
            ),
        ),
        (
            "Tax Amount",
            format_currency_compact(
                tax
            ),
        ),
        (
            "Outstanding Rate",
            format_percentage(
                outstanding_rate
            ),
        ),
    ]
)


management_insight(
    (
        f"The selected finance scope contains "
        f"{format_integer(bills)} bills across "
        f"{format_integer(patients)} patients and "
        f"{format_currency_compact(net)} in recorded net billing. "
        f"The recorded paid amount is "
        f"{format_currency_compact(paid)}, representing "
        f"{format_percentage(collection_efficiency)} of net billing. "
        f"Recorded outstanding exposure is "
        f"{format_currency_compact(outstanding)}."
    ),
    label="Finance Management Snapshot",
)


st.info(
    "Collection Efficiency = recorded paid amount ÷ net billing. "
    "It is not period-matched cash collection. Recorded Outstanding "
    "is the balance stored against billing records and is not formal "
    "accounts-receivable aging."
)


page_section(
    "03",
    "Revenue & Collection Trend",
    (
        "Follow monthly net billing, recorded paid amounts and "
        "recorded outstanding balances using each bill's billing date."
    ),
)


monthly = filtered.copy()

monthly["month_start"] = (
    monthly["billing_date"]
    .dt.to_period("M")
    .dt.to_timestamp()
)


monthly = (
    monthly.groupby(
        "month_start",
        as_index=False,
    )
    .agg(
        bills=(
            "bill_id",
            "count",
        ),
        gross_revenue=(
            "gross_amount",
            "sum",
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
    .sort_values(
        "month_start"
    )
)


monthly_long = monthly.melt(
    id_vars=[
        "month_start"
    ],
    value_vars=[
        "net_revenue",
        "collected_amount",
        "outstanding_amount",
    ],
    var_name="Metric",
    value_name="Amount",
)


monthly_long["Metric"] = (
    monthly_long["Metric"].map(
        {
            "net_revenue":
                "Net Revenue",
            "collected_amount":
                "Recorded Paid",
            "outstanding_amount":
                "Recorded Outstanding",
        }
    )
)


card_heading(
    "Monthly Revenue-Cycle Trend",
    (
        "Compares recorded net billing, paid amount and "
        "outstanding balance by billing month."
    ),
)

fig = px.line(
    monthly_long,
    x="month_start",
    y="Amount",
    color="Metric",
    markers=True,
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
        420,
        unified_hover=True,
    ),
    width="stretch",
)


explanation_box(
    "How to interpret this chart",
    (
        "The values are grouped using each bill's billing date. "
        "Recorded paid and outstanding amounts therefore describe "
        "the current values stored on bills from that billing month; "
        "they do not establish the date when cash was received or "
        "when a balance became outstanding."
    ),
)


page_section(
    "04",
    "Payment Behavior",
    (
        "Understand financial activity across recorded payment "
        "statuses and payment methods."
    ),
)


left, right = st.columns(2)


with left:
    card_heading(
        "Net Revenue by Payment Status",
        (
            "Shows the amount of net billing associated "
            "with each recorded payment status."
        ),
    )

    status_summary = (
        filtered.groupby(
            "payment_status",
            as_index=False,
        )
        .agg(
            bills=(
                "bill_id",
                "count",
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
        .sort_values(
            "net_revenue",
            ascending=False,
        )
    )

    fig = px.bar(
        status_summary,
        x="payment_status",
        y="net_revenue",
        text_auto=True,
    )

    fig.update_xaxes(
        title=None
    )

    fig.update_yaxes(
        title="Net Revenue"
    )

    st.plotly_chart(
        style_figure(fig),
        width="stretch",
    )

    explanation_box(
        "What this chart tells you",
        (
            "This view shows where net billing is concentrated "
            "across the payment statuses recorded in the warehouse."
        ),
    )


with right:
    card_heading(
        "Net Revenue by Payment Method",
        (
            "Shows net billing associated with each "
            "recorded payment method."
        ),
    )

    method_summary = (
        filtered.groupby(
            "payment_method",
            as_index=False,
        )
        .agg(
            bills=(
                "bill_id",
                "count",
            ),
            net_revenue=(
                "net_amount",
                "sum",
            ),
            collected_amount=(
                "paid_amount",
                "sum",
            ),
        )
        .sort_values(
            "net_revenue",
            ascending=False,
        )
    )

    fig = px.bar(
        method_summary,
        x="payment_method",
        y="net_revenue",
        text_auto=True,
    )

    fig.update_xaxes(
        title=None
    )

    fig.update_yaxes(
        title="Net Revenue"
    )

    st.plotly_chart(
        style_figure(fig),
        width="stretch",
    )

    explanation_box(
        "What this chart tells you",
        (
            "This view compares the financial value associated "
            "with the payment methods stored against billing records."
        ),
    )


page_section(
    "05",
    "Billing Responsibility",
    (
        "Compare recorded insurance responsibility with "
        "recorded patient responsibility."
    ),
)


responsibility = pd.DataFrame(
    {
        "Responsibility": [
            "Insurance",
            "Patient",
        ],
        "Amount": [
            insurance,
            patient_responsibility,
        ],
    }
)


responsibility_total = (
    insurance
    + patient_responsibility
)


left, right = st.columns(
    [1.15, 1]
)


with left:
    card_heading(
        "Insurance vs Patient Responsibility",
        (
            "Shows the relative financial responsibility "
            "recorded against insurers and patients."
        ),
    )

    fig = px.pie(
        responsibility,
        names="Responsibility",
        values="Amount",
        hole=0.55,
    )

    st.plotly_chart(
        style_figure(
            fig,
            360,
        ),
        width="stretch",
    )


with right:
    card_heading(
        "Responsibility Summary",
        (
            "Absolute amounts and proportional shares "
            "of recorded billing responsibility."
        ),
    )

    metric_row(
        [
            (
                "Insurance",
                format_currency_compact(
                    insurance
                ),
            ),
            (
                "Patient",
                format_currency_compact(
                    patient_responsibility
                ),
            ),
        ]
    )

    metric_row(
        [
            (
                "Insurance Share",
                format_percentage(
                    pct(
                        insurance,
                        responsibility_total,
                    )
                ),
            ),
            (
                "Patient Share",
                format_percentage(
                    pct(
                        patient_responsibility,
                        responsibility_total,
                    )
                ),
            ),
        ]
    )


explanation_box(
    "What this section tells you",
    (
        "This section describes how recorded financial responsibility "
        "is divided between insurance and patients. It does not indicate "
        "whether those amounts have already been paid."
    ),
)


page_section(
    "06",
    "Charge Composition",
    (
        "Understand which service components contribute "
        "to recorded gross billing."
    ),
)


charges = pd.DataFrame(
    {
        "Charge Component": [
            "Room",
            "Doctor",
            "Procedure",
            "Medication",
            "Lab",
            "Other",
        ],
        "Amount": [
            filtered[
                "room_charge"
            ].sum(),
            filtered[
                "doctor_charge"
            ].sum(),
            filtered[
                "procedure_charge"
            ].sum(),
            filtered[
                "medication_charge"
            ].sum(),
            filtered[
                "lab_charge"
            ].sum(),
            filtered[
                "other_charge"
            ].sum(),
        ],
    }
).sort_values(
    "Amount",
    ascending=True,
)


card_heading(
    "Gross Charge Composition",
    (
        "Compares room, doctor, procedure, medication, "
        "laboratory and other recorded charges."
    ),
)

fig = px.bar(
    charges,
    x="Amount",
    y="Charge Component",
    orientation="h",
    text_auto=True,
)

fig.update_yaxes(
    title=None
)

fig.update_xaxes(
    title="Amount"
)

st.plotly_chart(
    style_figure(
        fig,
        400,
    ),
    width="stretch",
)


explanation_box(
    "What this chart tells you",
    (
        "Longer bars identify charge categories contributing "
        "more value to gross billing in the selected finance scope."
    ),
)


page_section(
    "07",
    "Department Financial Performance",
    (
        "Compare billing, recorded collections and outstanding "
        "exposure attributed to hospital departments."
    ),
)


department = (
    filtered.groupby(
        "department_name",
        as_index=False,
    )
    .agg(
        bills=(
            "bill_id",
            "count",
        ),
        gross_revenue=(
            "gross_amount",
            "sum",
        ),
        discount_amount=(
            "discount_amount",
            "sum",
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
)


department[
    "collection_efficiency_pct"
] = department.apply(
    lambda row: pct(
        row[
            "collected_amount"
        ],
        row[
            "net_revenue"
        ],
    ),
    axis=1,
)


department[
    "average_bill"
] = (
    department[
        "net_revenue"
    ]
    /
    department[
        "bills"
    ].replace(
        0,
        pd.NA,
    )
)


department = department.sort_values(
    "net_revenue",
    ascending=False,
)


left, right = st.columns(2)


with left:
    card_heading(
        "Net Revenue by Department",
        (
            "Ranks departments by their contribution "
            "to recorded net billing."
        ),
    )

    chart = department.sort_values(
        "net_revenue",
        ascending=True,
    )

    fig = px.bar(
        chart,
        x="net_revenue",
        y="department_name",
        orientation="h",
        text_auto=True,
    )

    fig.update_yaxes(
        title=None
    )

    fig.update_xaxes(
        title="Net Revenue"
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
            "Departments with longer bars contribute more "
            "recorded net billing within the current selection."
        ),
    )


with right:
    card_heading(
        "Recorded Outstanding by Department",
        (
            "Ranks departments by the outstanding balances "
            "stored against their billing records."
        ),
    )

    chart = department.sort_values(
        "outstanding_amount",
        ascending=True,
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

    explanation_box(
        "What this chart tells you",
        (
            "This ranking identifies departments associated "
            "with the largest recorded outstanding balances."
        ),
    )


department_display = department.rename(
    columns={
        "department_name":
            "Department",
        "bills":
            "Bills",
        "gross_revenue":
            "Gross Revenue",
        "discount_amount":
            "Discount",
        "net_revenue":
            "Net Revenue",
        "collected_amount":
            "Recorded Paid",
        "outstanding_amount":
            "Recorded Outstanding",
        "collection_efficiency_pct":
            "Collection Efficiency %",
        "average_bill":
            "Average Bill",
    }
)


card_heading(
    "Department Finance Table",
    (
        "Detailed department-level view of billing, recorded "
        "payments, outstanding balances and average bill value."
    ),
)

dataframe(
    department_display,
    height=390,
)


page_section(
    "08",
    "Outstanding Exposure",
    (
        "Understand how recorded outstanding balances are "
        "concentrated by balance value."
    ),
)


exposure_order = [
    "No Outstanding",
    "Below ₹10K",
    "₹10K – ₹24.9K",
    "₹25K – ₹49.9K",
    "₹50K+",
]


exposure = (
    filtered.groupby(
        "exposure_band",
        as_index=False,
    )
    .agg(
        bills=(
            "bill_id",
            "count",
        ),
        net_revenue=(
            "net_amount",
            "sum",
        ),
        outstanding_amount=(
            "outstanding_amount",
            "sum",
        ),
    )
)


exposure[
    "exposure_band"
] = pd.Categorical(
    exposure[
        "exposure_band"
    ],
    categories=exposure_order,
    ordered=True,
)


exposure = exposure.sort_values(
    "exposure_band"
)


left, right = st.columns(2)


with left:
    card_heading(
        "Bills by Exposure Band",
        (
            "Counts billing records according to the "
            "value of their outstanding balance."
        ),
    )

    fig = px.bar(
        exposure,
        x="exposure_band",
        y="bills",
        text_auto=True,
    )

    fig.update_xaxes(
        title=None
    )

    fig.update_yaxes(
        title="Bills"
    )

    st.plotly_chart(
        style_figure(fig),
        width="stretch",
    )


with right:
    card_heading(
        "Outstanding Value by Exposure Band",
        (
            "Shows how total outstanding value is distributed "
            "across the defined exposure bands."
        ),
    )

    exposure_value = exposure[
        exposure[
            "outstanding_amount"
        ] > 0
    ]

    fig = px.bar(
        exposure_value,
        x="exposure_band",
        y="outstanding_amount",
        text_auto=True,
    )

    fig.update_xaxes(
        title=None
    )

    fig.update_yaxes(
        title="Outstanding Value"
    )

    st.plotly_chart(
        style_figure(fig),
        width="stretch",
    )


st.info(
    "These are value-based exposure bands only. They do not "
    "represent 30-day, 60-day, 90-day or any other age-based "
    "accounts-receivable classification."
)


page_section(
    "09",
    "High-Exposure Billing Register",
    (
        "Inspect billing records carrying the largest "
        "recorded outstanding balances."
    ),
)


high_exposure = (
    filtered[
        filtered[
            "outstanding_amount"
        ] > 0
    ]
    .sort_values(
        "outstanding_amount",
        ascending=False,
    )
    .head(100)
)


if not high_exposure.empty:
    high_display = high_exposure[
        [
            "bill_id",
            "billing_date",
            "patient_id",
            "department_name",
            "payment_status",
            "payment_method",
            "net_amount",
            "paid_amount",
            "outstanding_amount",
            "exposure_band",
        ]
    ].rename(
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
            "payment_method":
                "Payment Method",
            "net_amount":
                "Net Revenue",
            "paid_amount":
                "Recorded Paid",
            "outstanding_amount":
                "Outstanding",
            "exposure_band":
                "Exposure Band",
        }
    )

    dataframe(
        high_display,
        height=420,
    )

    st.caption(
        "Showing up to 100 billing records with the "
        "largest positive recorded outstanding balances."
    )

else:
    st.success(
        "No recorded outstanding balances exist "
        "in the current selection."
    )


page_section(
    "10",
    "Finance Review Signals",
    (
        "Deterministic financial observations that highlight "
        "concentrations requiring management attention."
    ),
)


signals = []


if not department.empty:
    revenue_row = (
        department.sort_values(
            "net_revenue",
            ascending=False,
        )
        .iloc[0]
    )

    signals.append(
        {
            "Signal":
                "Largest Department Revenue",
            "Entity":
                revenue_row[
                    "department_name"
                ],
            "Value":
                format_currency_compact(
                    revenue_row[
                        "net_revenue"
                    ]
                ),
            "Review Context":
                "Largest contribution to recorded net billing.",
        }
    )


    outstanding_row = (
        department.sort_values(
            "outstanding_amount",
            ascending=False,
        )
        .iloc[0]
    )

    signals.append(
        {
            "Signal":
                "Largest Department Outstanding",
            "Entity":
                outstanding_row[
                    "department_name"
                ],
            "Value":
                format_currency_compact(
                    outstanding_row[
                        "outstanding_amount"
                    ]
                ),
            "Review Context":
                "Largest recorded department outstanding exposure.",
        }
    )


    discount_row = (
        department.sort_values(
            "discount_amount",
            ascending=False,
        )
        .iloc[0]
    )

    signals.append(
        {
            "Signal":
                "Largest Department Discount",
            "Entity":
                discount_row[
                    "department_name"
                ],
            "Value":
                format_currency_compact(
                    discount_row[
                        "discount_amount"
                    ]
                ),
            "Review Context":
                "Largest total recorded discount amount.",
        }
    )


    meaningful = department[
        department[
            "bills"
        ] >= 25
    ]


    if not meaningful.empty:
        collection_row = (
            meaningful.sort_values(
                "collection_efficiency_pct",
                ascending=True,
            )
            .iloc[0]
        )

        signals.append(
            {
                "Signal":
                    "Lowest Collection Efficiency",
                "Entity":
                    collection_row[
                        "department_name"
                    ],
                "Value":
                    format_percentage(
                        collection_row[
                            "collection_efficiency_pct"
                        ]
                    ),
                "Review Context":
                    (
                        "Lowest recorded paid-to-net ratio "
                        "among departments with at least 25 bills."
                    ),
            }
        )


outstanding_bills = filtered[
    filtered[
        "outstanding_amount"
    ] > 0
]


if not outstanding_bills.empty:
    largest_bill = (
        outstanding_bills.sort_values(
            "outstanding_amount",
            ascending=False,
        )
        .iloc[0]
    )

    signals.append(
        {
            "Signal":
                "Largest Individual Outstanding",
            "Entity":
                largest_bill[
                    "bill_id"
                ],
            "Value":
                format_currency_compact(
                    largest_bill[
                        "outstanding_amount"
                    ]
                ),
            "Review Context":
                "Largest recorded outstanding balance on one bill.",
        }
    )


if signals:
    dataframe(
        pd.DataFrame(
            signals
        ),
        height=340,
    )


explanation_box(
    "How to interpret these signals",
    (
        "These are rule-based observations from the selected "
        "billing records. They identify concentrations for review "
        "and should not be interpreted as audited findings."
    ),
)


page_section(
    "11",
    "Billing Explorer",
    (
        "Search bill-level records and investigate individual "
        "financial transactions in the selected scope."
    ),
)


search_col, exposure_col = st.columns(
    [2, 1]
)


with search_col:
    search = st.text_input(
        "Search Bill / Patient ID",
        placeholder=(
            "Enter a bill ID or patient ID..."
        ),
    )


with exposure_col:
    selected_exposure = st.selectbox(
        "Exposure Band",
        [
            "All",
            *exposure_order,
        ],
    )


explorer = filtered.copy()


if search.strip():
    query = search.strip().lower()

    explorer = explorer[
        explorer[
            "bill_id"
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
    ]


if selected_exposure != "All":
    explorer = explorer[
        explorer[
            "exposure_band"
        ] == selected_exposure
    ]


explorer = explorer.sort_values(
    [
        "billing_date",
        "outstanding_amount",
    ],
    ascending=[
        False,
        False,
    ],
)


explorer_display = explorer[
    [
        "bill_id",
        "billing_date",
        "patient_id",
        "department_name",
        "payment_status",
        "payment_method",
        "gross_amount",
        "discount_amount",
        "tax_amount",
        "net_amount",
        "paid_amount",
        "outstanding_amount",
        "exposure_band",
    ]
].rename(
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
        "payment_method":
            "Payment Method",
        "gross_amount":
            "Gross Revenue",
        "discount_amount":
            "Discount",
        "tax_amount":
            "Tax",
        "net_amount":
            "Net Revenue",
        "paid_amount":
            "Recorded Paid",
        "outstanding_amount":
            "Outstanding",
        "exposure_band":
            "Exposure Band",
    }
)


dataframe(
    explorer_display,
    height=500,
)


st.caption(
    f"Showing "
    f"{format_integer(len(explorer_display))} "
    f"billing records."
)


page_section(
    "12",
    "Finance Metric Guide",
    (
        "Plain-language definitions that explain exactly "
        "how financial measures should be interpreted."
    ),
)


semantics = pd.DataFrame(
    [
        {
            "Metric":
                "Gross Revenue",
            "Meaning":
                "Recorded gross billing before discounts and other adjustments.",
        },
        {
            "Metric":
                "Net Revenue",
            "Meaning":
                "Recorded net billing amount.",
        },
        {
            "Metric":
                "Recorded Paid",
            "Meaning":
                "paid_amount currently stored against billing records.",
        },
        {
            "Metric":
                "Collection Efficiency",
            "Meaning":
                (
                    "Recorded paid amount divided by net billing. "
                    "It is not period-matched cash collection."
                ),
        },
        {
            "Metric":
                "Recorded Outstanding",
            "Meaning":
                (
                    "Outstanding balance currently stored against "
                    "billing records. It is not formal AR aging."
                ),
        },
        {
            "Metric":
                "Exposure Band",
            "Meaning":
                (
                    "Grouping based on outstanding balance value, "
                    "not the age of the receivable."
                ),
        },
        {
            "Metric":
                "Insurance Responsibility",
            "Meaning":
                "Recorded insurance_amount on billing records.",
        },
        {
            "Metric":
                "Patient Responsibility",
            "Meaning":
                "Recorded patient_amount on billing records.",
        },
        {
            "Metric":
                "Profit / Margin",
            "Meaning":
                (
                    "Not reported because validated budget and "
                    "complete cost-accounting data are unavailable."
                ),
        },
    ]
)


dataframe(
    semantics,
    height=360,
)


page_section(
    "13",
    "Continue the Analysis",
    (
        "Move from financial performance into risk and "
        "claims intelligence."
    ),
)


nav1, nav2 = st.columns(2)


with nav1:
    card_heading(
        "Risk Analytics",
        (
            "Continue into patient, operational and "
            "financial risk indicators."
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
        "Claims Analytics",
        (
            "Continue into insurer performance, claim "
            "status and rejection analysis."
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
                    "Billing Finance",
                "Source Rows":
                    len(finance),
                "Filtered Rows":
                    len(filtered),
                "Unique Bills":
                    finance[
                        "bill_id"
                    ].nunique(),
                "Available Fields":
                    ", ".join(
                        finance.columns.tolist()
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
        "Finance Analytics · Hospital 360 synthetic healthcare "
        "data. Financial indicators support management analytics "
        "and should not be interpreted as audited financial "
        "statements. Report generation, exports and Power BI "
        "downloads are centralized in the Admin Control Center."
    )


with footer_right:
    render_refresh_button(
        key="finance_refresh",
    )