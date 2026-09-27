from __future__ import annotations

import subprocess
import sys
from datetime import date
from pathlib import Path

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
    title="ETL Control Center",
    subtitle=(
        "Monitor and operate the Hospital 360 data pipeline from incremental "
        "source generation through validation, warehouse loading, quality "
        "control, reconciliation and analytics readiness."
    ),
    icon="⚙️",
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INCREMENTAL_ROOT = PROJECT_ROOT / "data" / "incremental"
GENERATOR_MODULE = "scripts.generate_incremental_data"
ETL_MODULE = "scripts.run_incremental_etl"
MAX_LOG_LENGTH = 20_000


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


def run_project_command(
    command: list[str],
    timeout: int = 600,
):
    completed = subprocess.run(
        command,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    return {
        "command": " ".join(command),
        "returncode": completed.returncode,
        "stdout": (
            completed.stdout.strip()
            if completed.stdout
            else ""
        ),
        "stderr": (
            completed.stderr.strip()
            if completed.stderr
            else ""
        ),
    }


def render_execution_log(result: dict):
    command = result.get("command", "")
    returncode = result.get("returncode", "")
    stdout = result.get("stdout", "")
    stderr = result.get("stderr", "")

    if len(stdout) > MAX_LOG_LENGTH:
        stdout = stdout[-MAX_LOG_LENGTH:]

    if len(stderr) > MAX_LOG_LENGTH:
        stderr = stderr[-MAX_LOG_LENGTH:]

    st.code(
        (
            f"Command:\n{command}\n\n"
            f"Return code:\n{returncode}\n\n"
            f"STDOUT:\n{stdout or '[empty]'}\n\n"
            f"STDERR:\n{stderr or '[empty]'}"
        ),
        language="text",
    )


def discover_incremental_directories():
    columns = [
        "Batch Directory",
        "Business Date",
        "Files",
        "Size MB",
        "Modified",
        "Path",
    ]

    if not INCREMENTAL_ROOT.exists():
        return pd.DataFrame(columns=columns)

    rows = []

    for directory in sorted(
        INCREMENTAL_ROOT.iterdir()
    ):
        if not directory.is_dir():
            continue

        files = [
            path
            for path in directory.rglob("*")
            if path.is_file()
        ]

        size_bytes = sum(
            path.stat().st_size
            for path in files
        )

        modified = max(
            (
                path.stat().st_mtime
                for path in files
            ),
            default=directory.stat().st_mtime,
        )

        rows.append(
            {
                "Batch Directory": directory.name,
                "Business Date": directory.name,
                "Files": len(files),
                "Size MB": round(
                    size_bytes / 1024 / 1024,
                    2,
                ),
                "Modified": pd.to_datetime(
                    modified,
                    unit="s",
                ),
                "Path": str(directory),
            }
        )

    if not rows:
        return pd.DataFrame(columns=columns)

    return (
        pd.DataFrame(rows)
        .sort_values(
            "Modified",
            ascending=False,
        )
        .reset_index(drop=True)
    )


@st.cache_data(
    ttl=30,
    show_spinner=False,
)
def load_etl_batches():
    return read_sql(
        """
        SELECT
            batch_id,
            batch_name,
            batch_type,
            source_name,
            start_time,
            end_time,
            status,
            records_received,
            records_inserted,
            records_updated,
            records_rejected,
            error_message,
            created_at,
            source_batch_id,
            business_date,
            duration_seconds,
            source_path
        FROM control.etl_batch
        ORDER BY batch_id DESC
        """
    )


@st.cache_data(
    ttl=30,
    show_spinner=False,
)
def load_quality_log():
    return read_sql(
        """
        SELECT
            quality_log_id,
            batch_id,
            table_name,
            rule_name,
            rule_type,
            records_checked,
            failed_records,
            severity,
            status,
            checked_at
        FROM control.data_quality_log
        ORDER BY checked_at DESC, quality_log_id DESC
        """
    )


@st.cache_data(
    ttl=30,
    show_spinner=False,
)
def load_rejected_records():
    return read_sql(
        """
        SELECT
            rejection_id,
            batch_id,
            dataset_name,
            record_identifier,
            rule_name,
            rejection_reason,
            record_data,
            rejected_at
        FROM control.rejected_record
        ORDER BY rejected_at DESC, rejection_id DESC
        """
    )


@st.cache_data(
    ttl=30,
    show_spinner=False,
)
def load_warehouse_counts():
    return read_sql(
        """
        SELECT
            'Patients' AS dataset,
            COUNT(*)::BIGINT AS row_count
        FROM warehouse.dim_patient

        UNION ALL

        SELECT
            'Doctors',
            COUNT(*)::BIGINT
        FROM warehouse.dim_doctor

        UNION ALL

        SELECT
            'Admissions',
            COUNT(*)::BIGINT
        FROM warehouse.fact_admission

        UNION ALL

        SELECT
            'Billing',
            COUNT(*)::BIGINT
        FROM warehouse.fact_billing

        UNION ALL

        SELECT
            'Claims',
            COUNT(*)::BIGINT
        FROM warehouse.fact_claim

        UNION ALL

        SELECT
            'Lab Tests',
            COUNT(*)::BIGINT
        FROM warehouse.fact_lab_test

        UNION ALL

        SELECT
            'Medication Events',
            COUNT(*)::BIGINT
        FROM warehouse.fact_medication
        """
    )


@st.cache_data(
    ttl=30,
    show_spinner=False,
)
def load_warehouse_freshness():
    return read_sql(
        """
        SELECT
            MAX(admission_timestamp)::timestamp
                AS latest_admission_timestamp,
            MAX(discharge_timestamp)::timestamp
                AS latest_discharge_timestamp
        FROM warehouse.fact_admission
        """
    )


load_errors = {}


def safe_load(name, loader):
    try:
        return loader()
    except Exception as exc:
        load_errors[name] = str(exc)
        return pd.DataFrame()


etl_batches = safe_load(
    "ETL Batch Ledger",
    load_etl_batches,
)

quality_log = safe_load(
    "Data Quality Ledger",
    load_quality_log,
)

rejected_records = safe_load(
    "Rejected Record Register",
    load_rejected_records,
)

warehouse_counts = safe_load(
    "Warehouse Counts",
    load_warehouse_counts,
)

warehouse_freshness = safe_load(
    "Warehouse Freshness",
    load_warehouse_freshness,
)

incremental_inventory = (
    discover_incremental_directories()
)


if not etl_batches.empty:
    status_series = (
        etl_batches["status"]
        .fillna("UNKNOWN")
        .astype(str)
        .str.upper()
    )

    success_count = int(
        status_series.eq("SUCCESS").sum()
    )

    failed_count = int(
        status_series.str.contains(
            "FAIL",
            regex=False,
        ).sum()
    )

    running_count = int(
        status_series.isin(
            [
                "RUNNING",
                "STARTED",
                "IN_PROGRESS",
            ]
        ).sum()
    )

    latest_status = str(
        etl_batches.iloc[0].get(
            "status",
            "Unavailable",
        )
    )

else:
    success_count = 0
    failed_count = 0
    running_count = 0
    latest_status = "Unavailable"


if not quality_log.empty:
    failed_series = pd.to_numeric(
        quality_log["failed_records"],
        errors="coerce",
    ).fillna(0)

    total_quality_checks = len(
        quality_log
    )

    checks_with_failure = int(
        (failed_series > 0).sum()
    )

    failed_rule_rows = int(
        failed_series.sum()
    )

else:
    total_quality_checks = 0
    checks_with_failure = 0
    failed_rule_rows = 0


section_header(
    "1. Pipeline Control Overview",
    (
        "Start here to understand the current state of the Hospital 360 "
        "data pipeline before reviewing or executing operational actions."
    ),
)

st.info(
    "ETL Control Center is the operational data-engineering workspace. "
    "Use it to monitor pipeline runs, create synthetic incremental source "
    "batches, execute approved incremental ETL, inspect data-quality "
    "results and verify warehouse freshness. Reports, business exports "
    "and Power BI deliverables belong in the Admin Control Center."
)

metric_row(
    [
        (
            "Latest Pipeline Status",
            latest_status,
        ),
        (
            "Successful Runs",
            format_integer(
                success_count
            ),
        ),
        (
            "Failed Runs",
            format_integer(
                failed_count
            ),
        ),
        (
            "Running",
            format_integer(
                running_count
            ),
        ),
    ]
)

metric_row(
    [
        (
            "Quality Checks",
            format_integer(
                total_quality_checks
            ),
        ),
        (
            "Checks With Failures",
            format_integer(
                checks_with_failure
            ),
        ),
        (
            "Failed Records",
            format_integer(
                failed_rule_rows
            ),
        ),
        (
            "Rejected Records",
            format_integer(
                len(rejected_records)
            ),
        ),
    ]
)

management_insight(
    (
        "The pipeline follows a controlled sequence: synthetic source data "
        "is created in the incremental landing area, validated by approved "
        "ETL logic, loaded into PostgreSQL warehouse tables and recorded "
        "through control-schema audit tables. Historical failures remain "
        "visible even when a later retry succeeds."
    ),
    label="How This Page Works",
)

if load_errors:
    with st.expander(
        "Pipeline source diagnostics",
        expanded=False,
    ):
        diagnostics = pd.DataFrame(
            [
                {
                    "Control Source": name,
                    "Status": "Unavailable",
                    "Details": error,
                }
                for name, error
                in load_errors.items()
            ]
        )

        dataframe(
            diagnostics,
            height=280,
        )


section_header(
    "2. Latest Pipeline Activity",
    (
        "Review the most recent ETL execution and its record-processing "
        "outcome before inspecting historical trends."
    ),
)

if not etl_batches.empty:
    latest = etl_batches.iloc[0]

    metric_row(
        [
            (
                "Batch ID",
                str(
                    latest.get(
                        "batch_id",
                        "—",
                    )
                ),
            ),
            (
                "Batch Name",
                str(
                    latest.get(
                        "batch_name",
                        "—",
                    )
                ),
            ),
            (
                "Business Date",
                str(
                    latest.get(
                        "business_date",
                        "—",
                    )
                ),
            ),
            (
                "Status",
                str(
                    latest.get(
                        "status",
                        "—",
                    )
                ),
            ),
        ]
    )

    duration = latest.get(
        "duration_seconds"
    )

    metric_row(
        [
            (
                "Received",
                format_integer(
                    latest.get(
                        "records_received",
                        0,
                    )
                ),
            ),
            (
                "Inserted",
                format_integer(
                    latest.get(
                        "records_inserted",
                        0,
                    )
                ),
            ),
            (
                "Updated",
                format_integer(
                    latest.get(
                        "records_updated",
                        0,
                    )
                ),
            ),
            (
                "Rejected",
                format_integer(
                    latest.get(
                        "records_rejected",
                        0,
                    )
                ),
            ),
        ]
    )

    st.caption(
        (
            f"Latest recorded execution duration: "
            f"{safe_number(duration):,.2f} seconds."
            if pd.notna(duration)
            else
            "No execution duration is recorded for the latest batch."
        )
    )

    error_message = latest.get(
        "error_message"
    )

    if pd.notna(error_message):
        error_text = str(
            error_message
        ).strip()

        if error_text:
            st.warning(
                f"Latest pipeline message: {error_text}"
            )

    with st.expander(
        "View recent pipeline executions",
        expanded=False,
    ):
        dataframe(
            etl_batches.head(50),
            height=430,
        )

else:
    st.info(
        "No ETL batch history is currently available."
    )


section_header(
    "3. Pipeline Execution Analysis",
    (
        "Understand pipeline reliability, processing duration and record "
        "throughput across historical ETL executions."
    ),
)

if not etl_batches.empty:
    status_summary = (
        etl_batches["status"]
        .fillna("UNKNOWN")
        .astype(str)
        .value_counts()
        .rename_axis("Status")
        .reset_index(name="Runs")
    )

    left, right = st.columns(2)

    with left:
        st.markdown(
            "#### Execution Status"
        )

        fig = px.bar(
            status_summary,
            x="Status",
            y="Runs",
            title="ETL Runs by Status",
            text_auto=True,
        )

        fig.update_xaxes(
            title=None
        )

        fig.update_yaxes(
            title="Runs"
        )

        st.plotly_chart(
            style_figure(
                fig,
                360,
            ),
            width="stretch",
        )

        st.caption(
            "Historical failures remain in the control ledger for "
            "auditability and should not be removed simply because a "
            "later retry succeeds."
        )

    with right:
        st.markdown(
            "#### Execution Duration"
        )

        duration_data = (
            etl_batches[
                [
                    "batch_id",
                    "duration_seconds",
                ]
            ]
            .copy()
        )

        duration_data[
            "duration_seconds"
        ] = pd.to_numeric(
            duration_data[
                "duration_seconds"
            ],
            errors="coerce",
        )

        duration_data = (
            duration_data
            .dropna(
                subset=[
                    "duration_seconds"
                ]
            )
            .sort_values(
                "batch_id"
            )
        )

        if not duration_data.empty:
            fig = px.line(
                duration_data,
                x="batch_id",
                y="duration_seconds",
                markers=True,
                title="ETL Duration Trend",
            )

            fig.update_xaxes(
                title="Batch ID"
            )

            fig.update_yaxes(
                title="Seconds"
            )

            st.plotly_chart(
                style_figure(
                    fig,
                    360,
                ),
                width="stretch",
            )

            st.caption(
                "Execution duration helps identify unusually slow pipeline "
                "runs and changing processing behavior."
            )

        else:
            st.info(
                "No ETL duration values are available."
            )

    st.markdown(
        "#### Recent Record Throughput"
    )

    throughput = etl_batches[
        [
            "batch_id",
            "records_received",
            "records_inserted",
            "records_updated",
            "records_rejected",
        ]
    ].copy()

    for column in [
        "records_received",
        "records_inserted",
        "records_updated",
        "records_rejected",
    ]:
        throughput[column] = (
            pd.to_numeric(
                throughput[column],
                errors="coerce",
            )
            .fillna(0)
        )

    throughput = (
        throughput
        .sort_values(
            "batch_id"
        )
        .tail(30)
    )

    throughput_long = throughput.melt(
        id_vars=[
            "batch_id"
        ],
        value_vars=[
            "records_received",
            "records_inserted",
            "records_updated",
            "records_rejected",
        ],
        var_name="Processing Measure",
        value_name="Records",
    )

    fig = px.line(
        throughput_long,
        x="batch_id",
        y="Records",
        color="Processing Measure",
        markers=True,
        title="Recent ETL Record Throughput",
    )

    fig.update_xaxes(
        title="Batch ID"
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
        "Pipeline execution analysis requires ETL batch history."
    )


section_header(
    "4. Incremental Data Intake",
    (
        "Inspect synthetic incremental source batches waiting in or already "
        "processed from the approved data landing area."
    ),
)

total_incremental_files = (
    safe_int(
        incremental_inventory[
            "Files"
        ].sum()
    )
    if not incremental_inventory.empty
    else 0
)

total_incremental_size = (
    safe_number(
        incremental_inventory[
            "Size MB"
        ].sum()
    )
    if not incremental_inventory.empty
    else 0.0
)

latest_incremental = (
    str(
        incremental_inventory.iloc[0][
            "Batch Directory"
        ]
    )
    if not incremental_inventory.empty
    else "None"
)

metric_row(
    [
        (
            "Batch Directories",
            format_integer(
                len(
                    incremental_inventory
                )
            ),
        ),
        (
            "Source Files",
            format_integer(
                total_incremental_files
            ),
        ),
        (
            "Landing Size",
            f"{total_incremental_size:,.2f} MB",
        ),
        (
            "Latest Batch",
            latest_incremental,
        ),
    ]
)

st.caption(
    "Landing root: data/incremental · Source type: synthetic incremental "
    "hospital data · Processing mode: controlled incremental ETL."
)

if not incremental_inventory.empty:
    dataframe(
        incremental_inventory,
        height=420,
    )

else:
    st.info(
        "No incremental batch directories were found under data/incremental."
    )


section_header(
    "5. Pipeline Operations",
    (
        "Use the approved controls below to create synthetic incremental "
        "source data or load currently pending batches into the warehouse."
    ),
)

st.warning(
    "These are write-producing pipeline operations. They are intentionally "
    "kept in ETL Control rather than the reporting Admin Center. Only fixed "
    "Hospital 360 modules can be executed; arbitrary shell commands and "
    "user-provided SQL are not accepted."
)

operation_left, operation_right = st.columns(2)

with operation_left:
    st.markdown(
        "#### A. Create Incremental Source Batch"
    )

    st.write(
        "Creates a new synthetic source batch for a selected business date "
        "inside the approved incremental landing area. This step does not "
        "load the batch into PostgreSQL."
    )

    generator_date = st.date_input(
        "Business Date",
        value=date.today(),
        key="etl_generator_date",
    )

    confirm_generation = st.checkbox(
        "I understand this creates new synthetic source files.",
        value=False,
        key="etl_confirm_generation",
    )

    generate_clicked = st.button(
        "Generate Incremental Batch",
        type="primary",
        width="stretch",
        disabled=not confirm_generation,
        key="etl_generate_batch",
    )

    if generate_clicked:
        command = [
            sys.executable,
            "-m",
            GENERATOR_MODULE,
            "--date",
            generator_date.isoformat(),
        ]

        try:
            with st.spinner(
                "Generating incremental synthetic data..."
            ):
                result = run_project_command(
                    command,
                    timeout=600,
                )

            st.session_state[
                "etl_generator_result"
            ] = result

            if result[
                "returncode"
            ] == 0:
                st.success(
                    "Incremental source batch generated successfully."
                )
                st.cache_data.clear()
            else:
                st.error(
                    "Incremental generation returned a non-zero exit code."
                )

        except subprocess.TimeoutExpired:
            st.error(
                "Incremental generation exceeded the execution time limit."
            )

        except Exception as exc:
            st.error(
                "Incremental generation could not be started."
            )
            st.exception(exc)

    generator_result = st.session_state.get(
        "etl_generator_result"
    )

    if generator_result:
        with st.expander(
            "Latest generator execution log",
            expanded=False,
        ):
            render_execution_log(
                generator_result
            )


with operation_right:
    st.markdown(
        "#### B. Process Pending Incremental Batches"
    )

    st.write(
        "Runs the approved incremental ETL workflow for all currently "
        "pending source batches. Validated records can be written into "
        "the Hospital 360 warehouse."
    )

    st.code(
        "python -m scripts.run_incremental_etl --all-pending",
        language="text",
    )

    confirm_etl = st.checkbox(
        "I understand this can write validated data to the warehouse.",
        value=False,
        key="etl_confirm_run",
    )

    run_etl_clicked = st.button(
        "Run All Pending ETL",
        type="primary",
        width="stretch",
        disabled=not confirm_etl,
        key="etl_run_pending",
    )

    if run_etl_clicked:
        command = [
            sys.executable,
            "-m",
            ETL_MODULE,
            "--all-pending",
        ]

        try:
            with st.spinner(
                "Running pending incremental ETL..."
            ):
                result = run_project_command(
                    command,
                    timeout=900,
                )

            st.session_state[
                "etl_run_result"
            ] = result

            if result[
                "returncode"
            ] == 0:
                st.success(
                    "Incremental ETL completed successfully."
                )
                st.cache_data.clear()
            else:
                st.error(
                    "Incremental ETL returned a non-zero exit code."
                )

        except subprocess.TimeoutExpired:
            st.error(
                "Incremental ETL exceeded the execution time limit."
            )

        except Exception as exc:
            st.error(
                "Incremental ETL could not be started."
            )
            st.exception(exc)

    etl_run_result = st.session_state.get(
        "etl_run_result"
    )

    if etl_run_result:
        with st.expander(
            "Latest ETL execution log",
            expanded=False,
        ):
            render_execution_log(
                etl_run_result
            )


section_header(
    "6. Data Quality Control",
    (
        "Review validation checks applied during pipeline processing and "
        "identify datasets or rules associated with failed records."
    ),
)

if not quality_log.empty:
    quality_work = quality_log.copy()

    quality_work[
        "records_checked"
    ] = pd.to_numeric(
        quality_work[
            "records_checked"
        ],
        errors="coerce",
    ).fillna(0)

    quality_work[
        "failed_records"
    ] = pd.to_numeric(
        quality_work[
            "failed_records"
        ],
        errors="coerce",
    ).fillna(0)

    quality_work[
        "Failure Rate %"
    ] = quality_work.apply(
        lambda row: pct(
            row[
                "failed_records"
            ],
            row[
                "records_checked"
            ],
        ),
        axis=1,
    )

    total_records_checked = (
        quality_work[
            "records_checked"
        ].sum()
    )

    total_failed = (
        quality_work[
            "failed_records"
        ].sum()
    )

    metric_row(
        [
            (
                "Validation Checks",
                format_integer(
                    len(
                        quality_work
                    )
                ),
            ),
            (
                "Records Checked",
                format_integer(
                    total_records_checked
                ),
            ),
            (
                "Failed Records",
                format_integer(
                    total_failed
                ),
            ),
            (
                "Overall Failure Rate",
                format_percentage(
                    pct(
                        total_failed,
                        total_records_checked,
                    )
                ),
            ),
        ]
    )

    severity_summary = (
        quality_work[
            "severity"
        ]
        .fillna("UNKNOWN")
        .astype(str)
        .value_counts()
        .rename_axis("Severity")
        .reset_index(name="Checks")
    )

    failed_checks = (
        quality_work[
            quality_work[
                "failed_records"
            ] > 0
        ]
        .copy()
    )

    left, right = st.columns(2)

    with left:
        st.markdown(
            "#### Validation Severity"
        )

        fig = px.bar(
            severity_summary,
            x="Severity",
            y="Checks",
            title="Quality Checks by Severity",
            text_auto=True,
        )

        fig.update_xaxes(
            title=None
        )

        st.plotly_chart(
            style_figure(
                fig,
                350,
            ),
            width="stretch",
        )

    with right:
        st.markdown(
            "#### Failed Records by Dataset"
        )

        if not failed_checks.empty:
            failure_summary = (
                failed_checks.groupby(
                    "table_name",
                    as_index=False,
                )
                .agg(
                    failed_records=(
                        "failed_records",
                        "sum",
                    )
                )
            )

            failure_summary = failure_summary.sort_values(
                by=["failed_records"],
                ascending=[True],
            ).reset_index(drop=True)

            fig = px.bar(
                failure_summary,
                x="failed_records",
                y="table_name",
                orientation="h",
                title="Failed Records by Dataset",
                text_auto=True,
            )

            fig.update_yaxes(
                title=None
            )

            fig.update_xaxes(
                title="Failed Records"
            )

            st.plotly_chart(
                style_figure(
                    fig,
                    350,
                ),
                width="stretch",
            )

        else:
            st.success(
                "No failed records are present in the loaded quality history."
            )

    filter_left, filter_right = st.columns(2)

    with filter_left:
        selected_severity = st.multiselect(
            "Filter by Severity",
            sorted(
                quality_work[
                    "severity"
                ]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            ),
            key="etl_quality_severity",
        )

    with filter_right:
        selected_quality_status = st.multiselect(
            "Filter by Quality Status",
            sorted(
                quality_work[
                    "status"
                ]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            ),
            key="etl_quality_status",
        )

    filtered_quality = quality_work.copy()

    if selected_severity:
        filtered_quality = (
            filtered_quality[
                filtered_quality[
                    "severity"
                ]
                .astype(str)
                .isin(
                    selected_severity
                )
            ]
        )

    if selected_quality_status:
        filtered_quality = (
            filtered_quality[
                filtered_quality[
                    "status"
                ]
                .astype(str)
                .isin(
                    selected_quality_status
                )
            ]
        )

    st.markdown(
        "#### Validation Ledger"
    )

    dataframe(
        filtered_quality,
        height=500,
    )

else:
    st.info(
        "No data-quality control history is currently available."
    )


section_header(
    "7. Rejected Record Register",
    (
        "Inspect records rejected by validation or ETL rules while retaining "
        "their failure reason for traceability and remediation analysis."
    ),
)

if not rejected_records.empty:
    filter_left, filter_right = st.columns(2)

    with filter_left:
        rejected_dataset = st.multiselect(
            "Filter by Dataset",
            sorted(
                rejected_records[
                    "dataset_name"
                ]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            ),
            key="etl_rejected_dataset",
        )

    with filter_right:
        rejected_rule = st.multiselect(
            "Filter by Rule",
            sorted(
                rejected_records[
                    "rule_name"
                ]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            ),
            key="etl_rejected_rule",
        )

    rejected_filtered = (
        rejected_records.copy()
    )

    if rejected_dataset:
        rejected_filtered = (
            rejected_filtered[
                rejected_filtered[
                    "dataset_name"
                ]
                .astype(str)
                .isin(
                    rejected_dataset
                )
            ]
        )

    if rejected_rule:
        rejected_filtered = (
            rejected_filtered[
                rejected_filtered[
                    "rule_name"
                ]
                .astype(str)
                .isin(
                    rejected_rule
                )
            ]
        )

    metric_row(
        [
            (
                "Rejected Records",
                format_integer(
                    len(
                        rejected_filtered
                    )
                ),
            ),
            (
                "Affected Datasets",
                format_integer(
                    rejected_filtered[
                        "dataset_name"
                    ].nunique()
                ),
            ),
            (
                "Triggered Rules",
                format_integer(
                    rejected_filtered[
                        "rule_name"
                    ].nunique()
                ),
            ),
            (
                "Register",
                "control.rejected_record",
            ),
        ]
    )

    dataframe(
        rejected_filtered,
        height=500,
    )

    st.caption(
        "Rejected records are intentionally retained instead of silently "
        "discarded so failed validation can be audited and investigated."
    )

else:
    st.success(
        "No rejected records are currently present in the rejection register."
    )


section_header(
    "8. Warehouse Load Position",
    (
        "Confirm the current amount of data loaded into the core Hospital "
        "360 dimensional warehouse."
    ),
)

if not warehouse_counts.empty:
    count_chart = (
        warehouse_counts.copy()
    )

    count_chart[
        "row_count"
    ] = pd.to_numeric(
        count_chart[
            "row_count"
        ],
        errors="coerce",
    ).fillna(0)

    total_rows = (
        count_chart[
            "row_count"
        ].sum()
    )

    largest_row = (
        count_chart
        .sort_values(
            "row_count",
            ascending=False,
        )
        .iloc[0]
    )

    metric_row(
        [
            (
                "Tracked Warehouse Rows",
                format_integer(
                    total_rows
                ),
            ),
            (
                "Tracked Datasets",
                format_integer(
                    len(
                        count_chart
                    )
                ),
            ),
            (
                "Largest Dataset",
                str(
                    largest_row[
                        "dataset"
                    ]
                ),
            ),
            (
                "Warehouse",
                "PostgreSQL",
            ),
        ]
    )

    fig = px.bar(
        count_chart.sort_values(
            "row_count",
            ascending=True,
        ),
        x="row_count",
        y="dataset",
        orientation="h",
        title="Warehouse Record Volume",
        text_auto=True,
    )

    fig.update_yaxes(
        title=None
    )

    fig.update_xaxes(
        title="Rows"
    )

    st.plotly_chart(
        style_figure(
            fig,
            410,
        ),
        width="stretch",
    )

    dataframe(
        count_chart,
        height=300,
    )

else:
    st.info(
        "Warehouse record counts are currently unavailable."
    )


section_header(
    "9. Data Freshness",
    (
        "Check the latest business timestamps currently represented in the "
        "admission fact table."
    ),
)

if not warehouse_freshness.empty:
    freshness = (
        warehouse_freshness.iloc[0]
    )

    latest_admission = freshness.get(
        "latest_admission_timestamp"
    )

    latest_discharge = freshness.get(
        "latest_discharge_timestamp"
    )

    admission_text = (
        pd.to_datetime(
            latest_admission
        ).strftime(
            "%d %b %Y %H:%M"
        )
        if pd.notna(
            latest_admission
        )
        else "—"
    )

    discharge_text = (
        pd.to_datetime(
            latest_discharge
        ).strftime(
            "%d %b %Y %H:%M"
        )
        if pd.notna(
            latest_discharge
        )
        else "—"
    )

    metric_row(
        [
            (
                "Latest Admission",
                admission_text,
            ),
            (
                "Latest Discharge",
                discharge_text,
            ),
            (
                "Freshness Basis",
                "Business Data",
            ),
            (
                "Source",
                "warehouse.fact_admission",
            ),
        ]
    )

    management_insight(
        (
            "Freshness on this page refers to the latest business timestamp "
            "represented in warehouse admission data. It should not be "
            "confused with the wall-clock time of the most recent ETL run."
        ),
        label="Freshness Interpretation",
    )

else:
    st.info(
        "Warehouse freshness information is unavailable."
    )


section_header(
    "10. ETL Control Ledger",
    (
        "Search the auditable pipeline history retained in control.etl_batch "
        "to review successful, failed, skipped and retried executions."
    ),
)

if not etl_batches.empty:
    filter_left, filter_right = st.columns(2)

    with filter_left:
        selected_statuses = st.multiselect(
            "Filter by Batch Status",
            sorted(
                etl_batches[
                    "status"
                ]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            ),
            key="etl_batch_status",
        )

    with filter_right:
        selected_batch_types = st.multiselect(
            "Filter by Batch Type",
            sorted(
                etl_batches[
                    "batch_type"
                ]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            ),
            key="etl_batch_type",
        )

    batch_filtered = (
        etl_batches.copy()
    )

    if selected_statuses:
        batch_filtered = (
            batch_filtered[
                batch_filtered[
                    "status"
                ]
                .astype(str)
                .isin(
                    selected_statuses
                )
            ]
        )

    if selected_batch_types:
        batch_filtered = (
            batch_filtered[
                batch_filtered[
                    "batch_type"
                ]
                .astype(str)
                .isin(
                    selected_batch_types
                )
            ]
        )

    metric_row(
        [
            (
                "Visible Runs",
                format_integer(
                    len(
                        batch_filtered
                    )
                ),
            ),
            (
                "Successful",
                format_integer(
                    batch_filtered[
                        "status"
                    ]
                    .fillna("")
                    .astype(str)
                    .str.upper()
                    .eq("SUCCESS")
                    .sum()
                ),
            ),
            (
                "Failed",
                format_integer(
                    batch_filtered[
                        "status"
                    ]
                    .fillna("")
                    .astype(str)
                    .str.upper()
                    .str.contains(
                        "FAIL",
                        regex=False,
                    )
                    .sum()
                ),
            ),
            (
                "Ledger",
                "control.etl_batch",
            ),
        ]
    )

    dataframe(
        batch_filtered,
        height=560,
    )

else:
    st.info(
        "No ETL control-ledger records are currently available."
    )


section_header(
    "11. ETL Architecture",
    (
        "Follow the complete data-engineering path from synthetic source "
        "generation to governed analytics used by dashboards, MIS and AI."
    ),
)

architecture = pd.DataFrame(
    [
        {
            "Step": "01",
            "Stage": "Synthetic Data Generator",
            "What Happens": (
                "Creates reproducible synthetic Hospital 360 source data."
            ),
            "Output": "Synthetic source records",
        },
        {
            "Step": "02",
            "Stage": "Incremental Landing Area",
            "What Happens": (
                "Stores append-only incremental source batches under "
                "data/incremental."
            ),
            "Output": "Incremental source files",
        },
        {
            "Step": "03",
            "Stage": "Extraction",
            "What Happens": (
                "Reads approved source files and prepares batch-level "
                "processing."
            ),
            "Output": "Extracted batch data",
        },
        {
            "Step": "04",
            "Stage": "Validation",
            "What Happens": (
                "Applies schema, business and temporal data-quality rules."
            ),
            "Output": "Validated and rejected records",
        },
        {
            "Step": "05",
            "Stage": "Transformation",
            "What Happens": (
                "Standardizes validated source records for dimensional "
                "warehouse loading."
            ),
            "Output": "Warehouse-ready records",
        },
        {
            "Step": "06",
            "Stage": "Warehouse Load",
            "What Happens": (
                "Loads dimensions and fact tables using controlled ETL logic."
            ),
            "Output": "PostgreSQL warehouse",
        },
        {
            "Step": "07",
            "Stage": "Reconciliation",
            "What Happens": (
                "Checks business-key and record-count consistency after load."
            ),
            "Output": "Reconciliation status",
        },
        {
            "Step": "08",
            "Stage": "Control Logging",
            "What Happens": (
                "Records execution, quality, rejection and audit information."
            ),
            "Output": "Control-schema history",
        },
        {
            "Step": "09",
            "Stage": "Analytics Layer",
            "What Happens": (
                "Publishes governed semantic views for dashboards, MIS, "
                "Power BI and AI consumption."
            ),
            "Output": "Analytics views",
        },
    ]
)

dataframe(
    architecture,
    height=520,
)

management_insight(
    (
        "The operational pipeline is intentionally separated from business "
        "reporting. ETL Control owns source generation, validation and data "
        "loading. Analytical pages consume the resulting governed data, "
        "while Admin Control Center owns downloadable reporting and BI "
        "deliverables."
    ),
    label="Application Architecture",
)


section_header(
    "12. Operational Governance",
    (
        "Understand the safeguards that control pipeline execution, data "
        "quality, rejected records and audit history."
    ),
)

governance = pd.DataFrame(
    [
        {
            "Control": "Approved modules only",
            "Purpose": (
                "The UI executes fixed Hospital 360 modules instead of "
                "accepting arbitrary shell commands."
            ),
        },
        {
            "Control": "Explicit execution confirmation",
            "Purpose": (
                "Write-producing pipeline actions require user confirmation "
                "before execution."
            ),
        },
        {
            "Control": "Incremental landing isolation",
            "Purpose": (
                "New source batches are created only under the approved "
                "data/incremental landing root."
            ),
        },
        {
            "Control": "Validation before load",
            "Purpose": (
                "Source records pass data-quality controls before warehouse "
                "insertion."
            ),
        },
        {
            "Control": "Rejected-record retention",
            "Purpose": (
                "Invalid records remain available for traceability instead "
                "of disappearing silently."
            ),
        },
        {
            "Control": "Batch audit history",
            "Purpose": (
                "Successful and failed attempts remain visible in the "
                "control ledger."
            ),
        },
        {
            "Control": "Idempotent incremental processing",
            "Purpose": (
                "Previously successful batches can be skipped by the "
                "incremental workflow."
            ),
        },
        {
            "Control": "Synthetic healthcare data",
            "Purpose": (
                "Hospital 360 pipeline records are synthetic and do not "
                "represent real patient PHI."
            ),
        },
    ]
)

dataframe(
    governance,
    height=480,
)


section_header(
    "13. Where to Go Next",
    (
        "Move to the appropriate Hospital 360 workspace after confirming "
        "that the data pipeline is healthy and current."
    ),
)

next_left, next_middle, next_right = st.columns(3)

with next_left:
    st.markdown(
        "#### Analyze the Data"
    )

    st.write(
        "Use Executive, Patient, Operations, Finance, Risk, Claims and "
        "Doctor dashboards for business-facing visual analysis."
    )

with next_middle:
    st.markdown(
        "#### Explore or Ask"
    )

    st.write(
        "Use Data Explorer for governed record-level inspection or AI "
        "Analyst for natural-language analytical questions."
    )

with next_right:
    st.markdown(
        "#### Generate Deliverables"
    )

    st.write(
        "Use Admin Control Center for report generation, MIS downloads, "
        "dataset exports and Power BI deliverables."
    )

st.info(
    "A historical FAILED or RECONCILIATION_FAILED row should not be deleted "
    "after a successful retry. Retaining both attempts preserves pipeline "
    "auditability. SUCCESS and SKIPPED are valid non-failure outcomes in "
    "the incremental workflow."
)

st.divider()

footer_left, footer_right = st.columns(
    [4, 1]
)

with footer_left:
    st.caption(
        "ETL Control Center · Hospital 360 Enterprise Intelligence Platform · "
        "Incremental processing · Data quality · Warehouse loading · "
        "Reconciliation · Operational governance"
    )

with footer_right:
    render_refresh_button(
        key="etl_control_refresh",
    )