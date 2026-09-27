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
    section_header,
)


bootstrap_page(
    title="Data Explorer",
    subtitle=(
        "Explore approved Hospital 360 datasets through a governed, "
        "read-only workspace for structure, quality, filtering, distributions, "
        "trends and record-level inspection."
    ),
    icon="🔎",
)


DATASETS = {
    "Executive KPIs": {
        "object": "analytics.vw_executive_kpis",
        "layer": "Analytics",
        "grain": "Enterprise summary",
        "description": "Executive-level hospital KPI summary.",
        "business_use": (
            "Use this dataset for a compact enterprise view of hospital "
            "performance and headline management indicators."
        ),
    },
    "Monthly Hospital Performance": {
        "object": "analytics.vw_monthly_hospital_performance",
        "layer": "Analytics",
        "grain": "Month",
        "description": "Monthly enterprise performance and trend dataset.",
        "business_use": (
            "Use this dataset to understand how overall hospital activity "
            "changes from month to month."
        ),
    },
    "Department Performance": {
        "object": "analytics.vw_department_performance",
        "layer": "Analytics",
        "grain": "Department",
        "description": "Department-level operational and financial analytics.",
        "business_use": (
            "Use this dataset to compare departments across operational and "
            "financial performance measures."
        ),
    },
    "Doctor Performance": {
        "object": "analytics.vw_doctor_performance",
        "layer": "Analytics",
        "grain": "Doctor",
        "description": "Physician-level analytical performance dataset.",
        "business_use": (
            "Use this dataset to inspect and compare doctor-level analytical "
            "performance measures."
        ),
    },
    "Claim Performance": {
        "object": "analytics.vw_claim_performance",
        "layer": "Analytics",
        "grain": "Insurer / payer",
        "description": "Claims and payer analytical performance.",
        "business_use": (
            "Use this dataset to understand claims activity and payer-level "
            "performance."
        ),
    },
    "Daily Operations": {
        "object": "analytics.vw_daily_operations",
        "layer": "Analytics",
        "grain": "Day",
        "description": "Daily hospital operational activity.",
        "business_use": (
            "Use this dataset to inspect daily hospital activity and "
            "operational movement."
        ),
    },
    "Patient Utilization": {
        "object": "analytics.vw_patient_utilization",
        "layer": "Analytics",
        "grain": "Patient",
        "description": "Patient-level utilization and admission behavior.",
        "business_use": (
            "Use this dataset to explore patient utilization patterns in the "
            "synthetic Hospital 360 population."
        ),
    },
    "Monthly Department Performance": {
        "object": "analytics.vw_monthly_department_performance",
        "layer": "Analytics",
        "grain": "Department × month",
        "description": "Monthly department-level performance trends.",
        "business_use": (
            "Use this dataset when both department comparison and monthly "
            "movement are important."
        ),
    },
    "Finance Summary": {
        "object": "analytics.vw_finance_summary",
        "layer": "Analytics",
        "grain": "Enterprise summary",
        "description": "Enterprise finance and revenue-cycle summary.",
        "business_use": (
            "Use this dataset for a consolidated view of hospital financial "
            "and revenue-cycle measures."
        ),
    },
    "Monthly Finance": {
        "object": "analytics.vw_monthly_finance",
        "layer": "Analytics",
        "grain": "Billing month",
        "description": "Monthly financial activity and collections view.",
        "business_use": (
            "Use this dataset to inspect financial and collection movement "
            "across time."
        ),
    },
    "Patients": {
        "object": "warehouse.dim_patient",
        "layer": "Warehouse Dimension",
        "grain": "Patient",
        "description": (
            "Patient master dimension containing synthetic demographics and "
            "registration attributes."
        ),
        "business_use": (
            "Use this dataset to inspect the synthetic patient master and "
            "descriptive patient attributes."
        ),
    },
    "Doctors": {
        "object": "warehouse.dim_doctor",
        "layer": "Warehouse Dimension",
        "grain": "Doctor",
        "description": "Doctor master dimension.",
        "business_use": (
            "Use this dataset to inspect doctor reference and descriptive "
            "attributes."
        ),
    },
    "Departments": {
        "object": "warehouse.dim_department",
        "layer": "Warehouse Dimension",
        "grain": "Department",
        "description": "Hospital department master dimension.",
        "business_use": (
            "Use this dataset to inspect the hospital department reference "
            "structure."
        ),
    },
    "Insurers": {
        "object": "warehouse.dim_insurer",
        "layer": "Warehouse Dimension",
        "grain": "Insurer",
        "description": "Insurance and payer master dimension.",
        "business_use": (
            "Use this dataset to inspect insurer and payer reference data."
        ),
    },
    "Diagnoses": {
        "object": "warehouse.dim_diagnosis",
        "layer": "Warehouse Dimension",
        "grain": "Diagnosis",
        "description": "Diagnosis reference dimension.",
        "business_use": (
            "Use this dataset to inspect diagnosis reference information "
            "available in Hospital 360."
        ),
    },
    "Procedures": {
        "object": "warehouse.dim_procedure",
        "layer": "Warehouse Dimension",
        "grain": "Procedure",
        "description": "Procedure reference dimension.",
        "business_use": (
            "Use this dataset to inspect procedure reference information."
        ),
    },
    "Medications": {
        "object": "warehouse.dim_medication",
        "layer": "Warehouse Dimension",
        "grain": "Medication",
        "description": "Medication reference dimension.",
        "business_use": (
            "Use this dataset to inspect medication reference information."
        ),
    },
    "Date Dimension": {
        "object": "warehouse.dim_date",
        "layer": "Warehouse Dimension",
        "grain": "Calendar day",
        "description": "Hospital 360 calendar dimension.",
        "business_use": (
            "Use this dataset to inspect the calendar structure supporting "
            "time-based analytics."
        ),
    },
    "Admissions": {
        "object": "warehouse.fact_admission",
        "layer": "Warehouse Fact",
        "grain": "Admission",
        "description": "One record per hospital admission.",
        "business_use": (
            "Use this dataset to inspect individual synthetic hospital "
            "admission events."
        ),
    },
    "Billing": {
        "object": "warehouse.fact_billing",
        "layer": "Warehouse Fact",
        "grain": "Bill",
        "description": "Billing and payment fact dataset.",
        "business_use": (
            "Use this dataset to inspect individual synthetic billing and "
            "payment records."
        ),
    },
    "Claims": {
        "object": "warehouse.fact_claim",
        "layer": "Warehouse Fact",
        "grain": "Claim",
        "description": "Insurance claim fact dataset.",
        "business_use": (
            "Use this dataset to inspect individual synthetic insurance "
            "claim records."
        ),
    },
    "Lab Tests": {
        "object": "warehouse.fact_lab_test",
        "layer": "Warehouse Fact",
        "grain": "Lab test event",
        "description": "Patient laboratory test events.",
        "business_use": (
            "Use this dataset to inspect synthetic laboratory event records."
        ),
    },
    "Medication Events": {
        "object": "warehouse.fact_medication",
        "layer": "Warehouse Fact",
        "grain": "Medication event",
        "description": "Patient medication events.",
        "business_use": (
            "Use this dataset to inspect synthetic medication event records."
        ),
    },
    "ETL Batches": {
        "object": "control.etl_batch",
        "layer": "Control",
        "grain": "ETL batch",
        "description": "Pipeline execution history and batch metadata.",
        "business_use": (
            "Use this dataset to inspect historical ETL batch execution "
            "information."
        ),
    },
    "Data Quality Log": {
        "object": "control.data_quality_log",
        "layer": "Control",
        "grain": "Data-quality rule execution",
        "description": "Data-quality validation results.",
        "business_use": (
            "Use this dataset to inspect recorded data-quality validation "
            "results."
        ),
    },
    "Rejected Records": {
        "object": "control.rejected_record",
        "layer": "Control",
        "grain": "Rejected record",
        "description": "Records rejected by ETL or validation rules.",
        "business_use": (
            "Use this dataset to inspect records rejected by governed "
            "pipeline controls."
        ),
    },
    "Audit Log": {
        "object": "control.audit_log",
        "layer": "Control",
        "grain": "Audit event",
        "description": "Application and administrative audit events.",
        "business_use": (
            "Use this dataset to inspect application and administrative "
            "audit history."
        ),
    },
}


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


def style_figure(fig, height=390):
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


def classify_columns(frame: pd.DataFrame):
    numeric = []
    datetime = []
    boolean = []
    categorical = []

    for column in frame.columns:
        series = frame[column]

        if pd.api.types.is_bool_dtype(series):
            boolean.append(column)
        elif pd.api.types.is_numeric_dtype(series):
            numeric.append(column)
        elif pd.api.types.is_datetime64_any_dtype(series):
            datetime.append(column)
        else:
            categorical.append(column)

    return {
        "numeric": numeric,
        "datetime": datetime,
        "boolean": boolean,
        "categorical": categorical,
    }


def normalize_possible_dates(frame: pd.DataFrame):
    result = frame.copy()

    for column in result.columns:
        name = column.lower()

        if name == "date_key" or name.endswith("_date_key"):
            continue

        if (
            "date" in name
            or "timestamp" in name
            or name.endswith("_at")
            or name in {
                "start_time",
                "end_time",
            }
        ):
            if not pd.api.types.is_datetime64_any_dtype(result[column]):
                converted = pd.to_datetime(
                    result[column],
                    errors="coerce",
                )

                original_non_null = result[column].notna().sum()
                converted_non_null = converted.notna().sum()

                if (
                    original_non_null == 0
                    or converted_non_null >= original_non_null * 0.8
                ):
                    result[column] = converted

    return result


def build_profile(frame: pd.DataFrame):
    rows = []
    total_rows = len(frame)

    for column in frame.columns:
        series = frame[column]

        non_null = int(series.notna().sum())
        null_count = int(series.isna().sum())
        unique_count = int(series.nunique(dropna=True))

        rows.append(
            {
                "Column": column,
                "Data Type": str(series.dtype),
                "Non-Null": non_null,
                "Null": null_count,
                "Null %": pct(
                    null_count,
                    total_rows,
                ),
                "Unique": unique_count,
                "Unique %": pct(
                    unique_count,
                    non_null,
                ),
            }
        )

    return pd.DataFrame(rows)


def apply_global_search(
    frame: pd.DataFrame,
    query: str,
):
    if not query.strip():
        return frame

    query = query.strip()
    searchable = frame.astype("string")

    mask = pd.Series(
        False,
        index=frame.index,
    )

    for column in searchable.columns:
        mask = mask | searchable[column].str.contains(
            query,
            case=False,
            na=False,
            regex=False,
        )

    return frame[mask]


@st.cache_data(
    ttl=60,
    show_spinner=False,
)
def load_dataset(
    object_name: str,
    row_limit: int,
):
    approved_objects = {
        config["object"]
        for config in DATASETS.values()
    }

    if object_name not in approved_objects:
        raise ValueError(
            "Dataset is not approved for Data Explorer access."
        )

    row_limit = max(
        1,
        min(
            int(row_limit),
            25_000,
        ),
    )

    return read_sql(
        f"""
        SELECT *
        FROM {object_name}
        LIMIT {row_limit}
        """
    )


@st.cache_data(
    ttl=60,
    show_spinner=False,
)
def load_object_metadata(
    object_name: str,
):
    approved_objects = {
        config["object"]
        for config in DATASETS.values()
    }

    if object_name not in approved_objects:
        raise ValueError(
            "Dataset is not approved for metadata inspection."
        )

    schema_name, table_name = object_name.split(
        ".",
        maxsplit=1,
    )

    return read_sql(
        f"""
        SELECT
            ordinal_position,
            column_name,
            data_type,
            is_nullable
        FROM information_schema.columns
        WHERE table_schema = '{schema_name}'
          AND table_name = '{table_name}'
        ORDER BY ordinal_position
        """
    )


@st.cache_data(
    ttl=60,
    show_spinner=False,
)
def load_exact_row_count(
    object_name: str,
):
    approved_objects = {
        config["object"]
        for config in DATASETS.values()
    }

    if object_name not in approved_objects:
        raise ValueError(
            "Dataset is not approved for row-count access."
        )

    result = read_sql(
        f"""
        SELECT COUNT(*) AS row_count
        FROM {object_name}
        """
    )

    if result.empty:
        return 0

    return int(
        result.iloc[0]["row_count"]
    )


section_header(
    "1. Choose a Dataset",
    (
        "Start by selecting the Hospital 360 dataset you want to explore. "
        "Only approved analytical, warehouse and control datasets are "
        "available here."
    ),
)

st.info(
    "This page is an exploration workspace. It does not accept arbitrary SQL "
    "and it does not generate project exports. Centralized downloads and "
    "generated deliverables are managed from the Admin Control Center."
)

s1, s2, s3 = st.columns(
    [2, 1, 1]
)

with s1:
    selected_name = st.selectbox(
        "Hospital 360 Dataset",
        list(DATASETS.keys()),
        key="data_explorer_dataset",
        help=(
            "Choose the business dataset you want to inspect. "
            "The underlying database object is selected automatically."
        ),
    )

selected_config = DATASETS[
    selected_name
]

with s2:
    row_limit = st.selectbox(
        "Rows to Load",
        [
            500,
            1_000,
            2_500,
            5_000,
            10_000,
            25_000,
        ],
        index=3,
        key="data_explorer_limit",
        help=(
            "Controls how many rows are loaded into this interactive "
            "workspace. The maximum is 25,000."
        ),
    )

with s3:
    load_count = st.checkbox(
        "Show Exact Row Count",
        value=True,
        help=(
            "Calculates the complete number of records in the selected "
            "approved dataset."
        ),
    )

object_name = selected_config[
    "object"
]

try:
    raw_frame = load_dataset(
        object_name,
        row_limit,
    )

    metadata = load_object_metadata(
        object_name
    )

    if load_count:
        total_row_count = load_exact_row_count(
            object_name
        )
    else:
        total_row_count = len(
            raw_frame
        )

except Exception as exc:
    st.error(
        f"Could not load {selected_name}."
    )

    st.caption(
        "Verify that the selected Hospital 360 database object exists and "
        "that the application database connection is available."
    )

    st.exception(exc)
    st.stop()

frame = normalize_possible_dates(
    raw_frame
)


section_header(
    "2. Understand the Dataset",
    (
        "Review what the selected dataset represents before interpreting "
        "individual values or charts."
    ),
)

metric_row(
    [
        (
            "Data Layer",
            selected_config["layer"],
        ),
        (
            "Business Grain",
            selected_config["grain"],
        ),
        (
            "Dataset Rows",
            format_integer(
                total_row_count
            ),
        ),
        (
            "Available Columns",
            format_integer(
                len(frame.columns)
            ),
        ),
    ]
)

management_insight(
    selected_config["business_use"],
    label="How to Use This Dataset",
)

management_insight(
    (
        f"{selected_name} is backed by {object_name}. "
        f"{selected_config['description']} "
        f"The current interactive workspace loaded up to "
        f"{format_integer(row_limit)} records."
    ),
    label="Dataset Context",
)

if total_row_count > len(frame):
    st.warning(
        f"The complete dataset contains {format_integer(total_row_count)} "
        f"records. This page currently holds "
        f"{format_integer(len(frame))} records because interactive "
        f"exploration is capped by the selected row limit."
    )
else:
    st.success(
        "The current interactive workspace contains all rows reported for "
        "this dataset."
    )


section_header(
    "3. Review the Dataset Structure",
    (
        "Understand the physical fields, database types and nullability "
        "before moving into data analysis."
    ),
)

if not metadata.empty:
    schema_display = metadata.rename(
        columns={
            "ordinal_position": "Position",
            "column_name": "Column",
            "data_type": "Database Type",
            "is_nullable": "Nullable",
        }
    )

    dataframe(
        schema_display,
        height=390,
    )
else:
    st.info(
        "No database column metadata was returned for this object."
    )


section_header(
    "4. Check Data Quality",
    (
        "Review completeness, duplicate records and field-level structure "
        "for the data currently loaded into the workspace."
    ),
)

duplicate_rows = int(
    frame.duplicated().sum()
)

missing_cells = int(
    frame.isna().sum().sum()
)

total_cells = (
    len(frame)
    * len(frame.columns)
)

missing_rate = pct(
    missing_cells,
    total_cells,
)

classification = classify_columns(
    frame
)

metric_row(
    [
        (
            "Loaded Records",
            format_integer(
                len(frame)
            ),
        ),
        (
            "Duplicate Records",
            format_integer(
                duplicate_rows
            ),
        ),
        (
            "Missing Values",
            format_integer(
                missing_cells
            ),
        ),
        (
            "Missing Value Rate",
            format_percentage(
                missing_rate
            ),
        ),
    ]
)

metric_row(
    [
        (
            "Numeric Fields",
            format_integer(
                len(
                    classification[
                        "numeric"
                    ]
                )
            ),
        ),
        (
            "Categorical Fields",
            format_integer(
                len(
                    classification[
                        "categorical"
                    ]
                )
            ),
        ),
        (
            "Date / Time Fields",
            format_integer(
                len(
                    classification[
                        "datetime"
                    ]
                )
            ),
        ),
        (
            "Boolean Fields",
            format_integer(
                len(
                    classification[
                        "boolean"
                    ]
                )
            ),
        ),
    ]
)

profile = build_profile(
    frame
)

st.markdown("#### Field-Level Quality Profile")

st.caption(
    "Each row below explains completeness and uniqueness for one field in "
    "the currently loaded dataset."
)

dataframe(
    profile,
    height=440,
)


section_header(
    "5. Inspect Missing Values",
    (
        "Identify which fields contain missing information and where "
        "completeness requires additional attention."
    ),
)

missing_profile = profile[
    profile["Null"] > 0
].copy()

if missing_profile.empty:
    st.success(
        "No missing values were found in the currently loaded records."
    )
else:
    missing_profile = missing_profile.sort_values(
        "Null %",
        ascending=False,
    )

    fig = px.bar(
        missing_profile,
        x="Null %",
        y="Column",
        orientation="h",
        title="Missing Value Rate by Field",
        text_auto=True,
    )

    fig.update_yaxes(
        title=None
    )

    fig.update_xaxes(
        title="Missing Values (%)"
    )

    st.plotly_chart(
        style_figure(
            fig,
            max(
                360,
                min(
                    700,
                    len(
                        missing_profile
                    )
                    * 32,
                ),
            ),
        ),
        width="stretch",
    )

    dataframe(
        missing_profile[
            [
                "Column",
                "Null",
                "Null %",
                "Non-Null",
            ]
        ],
        height=360,
    )


section_header(
    "6. Filter the Data",
    (
        "Narrow the loaded dataset using a simple search or one "
        "field-specific filter. All filtering happens inside the governed "
        "interactive workspace."
    ),
)

f1, f2 = st.columns(
    [2, 1]
)

with f1:
    global_search = st.text_input(
        "Search Across Loaded Data",
        placeholder=(
            "Search for a visible ID, department, status, insurer or "
            "other value..."
        ),
        key="data_explorer_search",
        help=(
            "Searches visible values across all columns in the currently "
            "loaded records."
        ),
    )

with f2:
    filter_column = st.selectbox(
        "Filter One Field",
        [
            "None",
            *frame.columns.tolist(),
        ],
        key="data_explorer_filter_column",
    )

filtered = apply_global_search(
    frame,
    global_search,
)

if filter_column != "None":
    series = frame[
        filter_column
    ]

    if pd.api.types.is_numeric_dtype(
        series
    ):
        valid_numeric = pd.to_numeric(
            series,
            errors="coerce",
        ).dropna()

        if not valid_numeric.empty:
            minimum = float(
                valid_numeric.min()
            )

            maximum = float(
                valid_numeric.max()
            )

            if minimum < maximum:
                selected_range = st.slider(
                    f"{filter_column} Range",
                    min_value=minimum,
                    max_value=maximum,
                    value=(
                        minimum,
                        maximum,
                    ),
                    key=(
                        "data_explorer_numeric_"
                        f"{filter_column}"
                    ),
                )

                filtered_numeric = pd.to_numeric(
                    filtered[
                        filter_column
                    ],
                    errors="coerce",
                )

                filtered = filtered[
                    filtered_numeric.between(
                        selected_range[0],
                        selected_range[1],
                    )
                ]
            else:
                st.info(
                    f"{filter_column} has only one numeric value in the "
                    "currently loaded dataset."
                )

    elif pd.api.types.is_datetime64_any_dtype(
        series
    ):
        valid_dates = series.dropna()

        if not valid_dates.empty:
            minimum = valid_dates.min().date()
            maximum = valid_dates.max().date()

            if minimum < maximum:
                selected_dates = st.date_input(
                    f"{filter_column} Date Range",
                    value=(
                        minimum,
                        maximum,
                    ),
                    min_value=minimum,
                    max_value=maximum,
                    key=(
                        "data_explorer_date_"
                        f"{filter_column}"
                    ),
                )

                if (
                    isinstance(
                        selected_dates,
                        (tuple, list),
                    )
                    and len(
                        selected_dates
                    ) == 2
                ):
                    start = pd.Timestamp(
                        selected_dates[0]
                    )

                    end = (
                        pd.Timestamp(
                            selected_dates[1]
                        )
                        + pd.Timedelta(
                            days=1
                        )
                    )

                    filtered = filtered[
                        (
                            filtered[
                                filter_column
                            ]
                            >= start
                        )
                        &
                        (
                            filtered[
                                filter_column
                            ]
                            < end
                        )
                    ]
            else:
                st.info(
                    f"{filter_column} contains only one date in the "
                    "currently loaded dataset."
                )

    else:
        unique_values = (
            series
            .dropna()
            .astype(str)
            .value_counts()
            .head(200)
            .index
            .tolist()
        )

        selected_values = st.multiselect(
            f"{filter_column} Values",
            unique_values,
            placeholder="All values",
            key=(
                "data_explorer_category_"
                f"{filter_column}"
            ),
        )

        if selected_values:
            filtered = filtered[
                filtered[
                    filter_column
                ]
                .astype(str)
                .isin(
                    selected_values
                )
            ]

metric_row(
    [
        (
            "Filtered Records",
            format_integer(
                len(filtered)
            ),
        ),
        (
            "Loaded Records",
            format_integer(
                len(frame)
            ),
        ),
        (
            "Records Retained",
            format_percentage(
                pct(
                    len(filtered),
                    len(frame),
                )
            ),
        ),
        (
            "Dataset",
            selected_name,
        ),
    ]
)

if filtered.empty:
    st.warning(
        "No records match the current search and filter combination. "
        "Change or clear the filters to continue exploring."
    )


section_header(
    "7. Explore Numeric Measures",
    (
        "Study the distribution, typical value, range and potential "
        "outliers of numeric fields."
    ),
)

numeric_columns = (
    filtered
    .select_dtypes(
        include="number"
    )
    .columns
    .tolist()
)

if numeric_columns:
    numeric_column = st.selectbox(
        "Numeric Measure",
        numeric_columns,
        key="data_explorer_numeric_column",
    )

    numeric_series = pd.to_numeric(
        filtered[
            numeric_column
        ],
        errors="coerce",
    ).dropna()

    if not numeric_series.empty:
        metric_row(
            [
                (
                    "Average",
                    f"{numeric_series.mean():,.2f}",
                ),
                (
                    "Median",
                    f"{numeric_series.median():,.2f}",
                ),
                (
                    "Minimum",
                    f"{numeric_series.min():,.2f}",
                ),
                (
                    "Maximum",
                    f"{numeric_series.max():,.2f}",
                ),
            ]
        )

        left, right = st.columns(2)

        with left:
            histogram_frame = pd.DataFrame(
                {
                    numeric_column:
                        numeric_series
                }
            )

            fig = px.histogram(
                histogram_frame,
                x=numeric_column,
                nbins=40,
                title=(
                    f"Distribution of {numeric_column}"
                ),
            )

            fig.update_yaxes(
                title="Records"
            )

            st.plotly_chart(
                style_figure(
                    fig,
                    400,
                ),
                width="stretch",
            )

            st.caption(
                "This chart shows how frequently values occur across the "
                "selected numeric measure."
            )

        with right:
            box_frame = pd.DataFrame(
                {
                    numeric_column:
                        numeric_series
                }
            )

            fig = px.box(
                box_frame,
                y=numeric_column,
                points=False,
                title=(
                    f"Range and Outliers — {numeric_column}"
                ),
            )

            st.plotly_chart(
                style_figure(
                    fig,
                    400,
                ),
                width="stretch",
            )

            st.caption(
                "This chart summarizes the central range and highlights "
                "potential extreme values."
            )

        numeric_stats = (
            numeric_series
            .describe(
                percentiles=[
                    0.01,
                    0.05,
                    0.25,
                    0.50,
                    0.75,
                    0.95,
                    0.99,
                ]
            )
            .rename(
                "Value"
            )
            .reset_index()
            .rename(
                columns={
                    "index": "Statistic"
                }
            )
        )

        st.markdown(
            "#### Detailed Numeric Summary"
        )

        dataframe(
            numeric_stats,
            height=420,
        )
    else:
        st.info(
            "The selected numeric field has no usable values after filtering."
        )
else:
    st.info(
        "No numeric fields are available in the current filtered dataset."
    )


section_header(
    "8. Explore Categories and Statuses",
    (
        "Understand the most common groups, labels and statuses in the "
        "current filtered data."
    ),
)

categorical_columns = [
    column
    for column in filtered.columns
    if (
        not pd.api.types.is_numeric_dtype(
            filtered[column]
        )
        and not pd.api.types.is_datetime64_any_dtype(
            filtered[column]
        )
    )
]

if categorical_columns:
    category_column = st.selectbox(
        "Category or Status Field",
        categorical_columns,
        key="data_explorer_category_column",
    )

    category_summary = (
        filtered[
            category_column
        ]
        .fillna("NULL")
        .astype(str)
        .value_counts(
            dropna=False
        )
        .head(25)
        .rename_axis(
            category_column
        )
        .reset_index(
            name="Records"
        )
    )

    category_summary[
        "Share %"
    ] = category_summary[
        "Records"
    ].apply(
        lambda value: pct(
            value,
            len(filtered),
        )
    )

    left, right = st.columns(
        [3, 2]
    )

    with left:
        chart = (
            category_summary
            .head(15)
            .sort_values(
                "Records",
                ascending=True,
            )
        )

        fig = px.bar(
            chart,
            x="Records",
            y=category_column,
            orientation="h",
            title=(
                f"Most Common Values — {category_column}"
            ),
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
            "The chart ranks the most frequently occurring values in the "
            "selected field."
        )

    with right:
        dataframe(
            category_summary,
            height=450,
        )
else:
    st.info(
        "No categorical fields are available in the current filtered dataset."
    )


section_header(
    "9. Explore Time Coverage",
    (
        "Review the time span represented by the data and understand how "
        "record activity changes across months."
    ),
)

date_columns = [
    column
    for column in filtered.columns
    if pd.api.types.is_datetime64_any_dtype(
        filtered[column]
    )
]

if date_columns:
    date_column = st.selectbox(
        "Date or Time Field",
        date_columns,
        key="data_explorer_date_column",
    )

    dated = filtered[
        filtered[
            date_column
        ].notna()
    ].copy()

    if not dated.empty:
        minimum_date = dated[
            date_column
        ].min()

        maximum_date = dated[
            date_column
        ].max()

        metric_row(
            [
                (
                    "Earliest Record",
                    minimum_date.strftime(
                        "%d %b %Y"
                    ),
                ),
                (
                    "Latest Record",
                    maximum_date.strftime(
                        "%d %b %Y"
                    ),
                ),
                (
                    "Dated Records",
                    format_integer(
                        len(dated)
                    ),
                ),
                (
                    "Distinct Dates",
                    format_integer(
                        dated[
                            date_column
                        ]
                        .dt.date
                        .nunique()
                    ),
                ),
            ]
        )

        dated["__month"] = (
            dated[
                date_column
            ]
            .dt.to_period("M")
            .dt.to_timestamp()
        )

        time_summary = (
            dated.groupby(
                "__month",
                as_index=False,
            )
            .size()
            .rename(
                columns={
                    "__month": "Month",
                    "size": "Records",
                }
            )
        )

        fig = px.line(
            time_summary,
            x="Month",
            y="Records",
            markers=True,
            title=(
                f"Monthly Record Activity — {date_column}"
            ),
        )

        fig.update_xaxes(
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
            "This view shows record volume by month for the selected "
            "date field. It describes activity volume, not necessarily "
            "business performance."
        )
    else:
        st.info(
            "The selected date field has no usable values after filtering."
        )
else:
    st.info(
        "No date or time fields were detected in the current dataset."
    )


section_header(
    "10. Compare Numeric Relationships",
    (
        "Explore whether two numeric measures move together. This is a "
        "descriptive analytical view and should not be interpreted as "
        "evidence that one measure causes the other."
    ),
)

if len(numeric_columns) >= 2:
    c1, c2 = st.columns(2)

    with c1:
        x_column = st.selectbox(
            "Horizontal Axis",
            numeric_columns,
            index=0,
            key="data_explorer_x",
        )

    with c2:
        y_default = (
            1
            if len(
                numeric_columns
            ) > 1
            else 0
        )

        y_column = st.selectbox(
            "Vertical Axis",
            numeric_columns,
            index=y_default,
            key="data_explorer_y",
        )

    relationship = filtered[
        [
            x_column,
            y_column,
        ]
    ].copy()

    relationship[
        x_column
    ] = pd.to_numeric(
        relationship[
            x_column
        ],
        errors="coerce",
    )

    relationship[
        y_column
    ] = pd.to_numeric(
        relationship[
            y_column
        ],
        errors="coerce",
    )

    relationship = relationship.dropna()

    if not relationship.empty:
        correlation = relationship[
            x_column
        ].corr(
            relationship[
                y_column
            ]
        )

        metric_row(
            [
                (
                    "Relationship Records",
                    format_integer(
                        len(relationship)
                    ),
                ),
                (
                    "Pearson Correlation",
                    (
                        f"{correlation:.4f}"
                        if pd.notna(
                            correlation
                        )
                        else "N/A"
                    ),
                ),
            ]
        )

        chart_data = relationship

        if len(
            chart_data
        ) > 5_000:
            chart_data = chart_data.sample(
                5_000,
                random_state=42,
            )

        fig = px.scatter(
            chart_data,
            x=x_column,
            y=y_column,
            opacity=0.55,
            title=(
                f"{y_column} Compared with {x_column}"
            ),
        )

        st.plotly_chart(
            style_figure(
                fig,
                440,
            ),
            width="stretch",
        )

        st.info(
            "Correlation is an exploratory statistical association. "
            "It does not establish clinical, operational or financial "
            "causation."
        )
    else:
        st.info(
            "No complete numeric pairs are available for the selected fields."
        )
else:
    st.info(
        "At least two numeric fields are required for relationship analysis."
    )


section_header(
    "11. Inspect Individual Records",
    (
        "Review the filtered rows directly after completing the structural "
        "and analytical exploration above."
    ),
)

preview_limit = st.selectbox(
    "Records to Display",
    [
        50,
        100,
        250,
        500,
        1_000,
    ],
    index=2,
    key="data_explorer_preview_rows",
)

preview = filtered.head(
    preview_limit
)

dataframe(
    preview,
    height=580,
)

st.caption(
    f"Showing {format_integer(len(preview))} of "
    f"{format_integer(len(filtered))} records that currently match "
    f"the active exploration filters."
)


section_header(
    "12. Understand Explorer Governance",
    (
        "Hospital 360 separates interactive analysis from unrestricted "
        "database access and centralized administrative exports."
    ),
)

governance = pd.DataFrame(
    [
        {
            "Control": "Approved dataset catalog",
            "What It Means": (
                "Only datasets explicitly registered for Hospital 360 "
                "exploration can be selected."
            ),
        },
        {
            "Control": "Read-only exploration",
            "What It Means": (
                "This workspace is designed for analytical inspection and "
                "does not modify source or warehouse records."
            ),
        },
        {
            "Control": "No arbitrary SQL editor",
            "What It Means": (
                "Users cannot submit unrestricted SQL statements from "
                "this page."
            ),
        },
        {
            "Control": "Interactive row limit",
            "What It Means": (
                "A maximum of 25,000 rows can be loaded into the "
                "interactive explorer."
            ),
        },
        {
            "Control": "In-memory filtering",
            "What It Means": (
                "Search and field filters operate against the approved "
                "records already loaded into the page."
            ),
        },
        {
            "Control": "Schema transparency",
            "What It Means": (
                "Users can inspect database field names, types and "
                "nullability without receiving unrestricted database access."
            ),
        },
        {
            "Control": "Centralized exports",
            "What It Means": (
                "Project downloads, generated deliverables and managed "
                "exports belong in the Admin Control Center."
            ),
        },
    ]
)

dataframe(
    governance,
    height=440,
)


section_header(
    "13. Continue the Hospital 360 Workflow",
    (
        "Use this explorer for detailed inspection, then continue to the "
        "appropriate dashboard or administrative workspace depending on "
        "what you need to do next."
    ),
)

workflow_left, workflow_middle, workflow_right = st.columns(3)

with workflow_left:
    st.markdown("#### Need Business Visuals?")
    st.write(
        "Use the dedicated Patient, Operations, Finance, Risk, Claims or "
        "Doctor dashboards for management-ready KPIs, charts and business "
        "interpretation."
    )

with workflow_middle:
    st.markdown("#### Need AI Analysis?")
    st.write(
        "Use the AI Analyst Assistant to ask governed natural-language "
        "questions about Hospital 360 analytical data."
    )

with workflow_right:
    st.markdown("#### Need Files or Exports?")
    st.write(
        "Use the Admin Control Center for centralized downloads, generated "
        "outputs, MIS deliverables, analytical exports and Power BI assets."
    )

management_insight(
    (
        "The Data Explorer is intentionally positioned between the visual "
        "dashboards and the administrative control layer. Dashboards explain "
        "business performance, this page allows deeper governed inspection, "
        "and the Admin Control Center owns operational generation and "
        "download workflows."
    ),
    label="Where This Page Fits",
)


section_header(
    "Important Usage Note",
    (
        "Hospital 360 contains multiple datasets with different business "
        "grains. Understanding grain is essential before comparing or "
        "combining information."
    ),
)

st.warning(
    "Admission, billing, claims, laboratory and medication fact datasets "
    "represent different event types and grains. They should not be joined "
    "directly without first aggregating them to compatible analytical grains."
)

st.info(
    "Hospital 360 uses synthetic healthcare data and is designed for "
    "analytics, engineering and portfolio demonstration. The Data Explorer "
    "is a governed analytical inspection workspace and is not a clinical "
    "decision system."
)

st.divider()

footer_left, footer_right = st.columns(
    [4, 1]
)

with footer_left:
    st.caption(
        "Data Explorer · Hospital 360 Enterprise Intelligence Platform · "
        "Governed read-only exploration · Synthetic healthcare data"
    )

with footer_right:
    render_refresh_button(
        key="data_explorer_refresh",
    )