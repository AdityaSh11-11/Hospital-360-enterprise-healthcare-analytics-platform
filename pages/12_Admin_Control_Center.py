from __future__ import annotations

import os
import platform
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from analytics.data_loader import read_sql
from utils.app_helpers import (
    bootstrap_page,
    clear_application_cache,
    dataframe,
    format_integer,
    management_insight,
    metric_row,
    render_refresh_button,
    section_header,
)


# ============================================================
# HOSPITAL 360 — ENTERPRISE CONTROL TOWER
# ============================================================

bootstrap_page(
    title="Control Tower",
    subtitle=(
        "Enterprise operations, data engineering, governance, "
        "analytics distribution and platform administration."
    ),
    icon="🛡️",
)


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_ROOT = PROJECT_ROOT / "data"

RAW_ROOT = DATA_ROOT / "raw"
PROCESSED_ROOT = DATA_ROOT / "processed"
REJECTED_ROOT = DATA_ROOT / "rejected"
INCREMENTAL_ROOT = DATA_ROOT / "incremental"
EXPORT_ROOT = DATA_ROOT / "exports"

REPORTS_ROOT = PROJECT_ROOT / "reports"


# ============================================================
# BI / REPORT LOCATIONS
# ============================================================

POWERBI_CANDIDATES = [
    PROJECT_ROOT / "powerbi",
    PROJECT_ROOT / "PowerBI",
    PROJECT_ROOT / "bi" / "powerbi",
    PROJECT_ROOT / "dashboards" / "powerbi",
    EXPORT_ROOT / "powerbi",
]

TABLEAU_CANDIDATES = [
    PROJECT_ROOT / "tableau",
    PROJECT_ROOT / "Tableau",
    PROJECT_ROOT / "bi" / "tableau",
    PROJECT_ROOT / "dashboards" / "tableau",
    EXPORT_ROOT / "tableau",
]

MIS_CANDIDATES = [
    EXPORT_ROOT,
    REPORTS_ROOT,
    PROJECT_ROOT / "mis",
]


ALLOWED_ARTIFACT_SUFFIXES = {
    ".xlsx",
    ".xls",
    ".csv",
    ".pdf",
    ".pbix",
    ".pbit",
    ".twb",
    ".twbx",
    ".hyper",
    ".png",
    ".jpg",
    ".jpeg",
    ".json",
    ".txt",
}


# ============================================================
# GENERIC HELPERS
# ============================================================

def safe_number(value, default=0.0):
    try:
        if value is None or pd.isna(value):
            return default

        return float(value)

    except (TypeError, ValueError):
        return default


def format_bytes(size_bytes: int) -> str:
    size = float(size_bytes or 0)

    for unit in [
        "B",
        "KB",
        "MB",
        "GB",
        "TB",
    ]:
        if size < 1024:
            return f"{size:,.1f} {unit}"

        size /= 1024

    return f"{size:,.1f} PB"


def style_figure(fig, height=390):
    fig.update_layout(
        height=height,
        margin=dict(
            l=10,
            r=10,
            t=50,
            b=10,
        ),
        legend_title_text="",
    )

    return fig


def safe_read_bytes(path: Path):
    try:
        return path.read_bytes()

    except OSError:
        return None


def mime_for(path: Path):
    suffix = path.suffix.lower()

    mapping = {
        ".xlsx": (
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        ".xls": "application/vnd.ms-excel",
        ".csv": "text/csv",
        ".pdf": "application/pdf",
        ".pbix": "application/octet-stream",
        ".pbit": "application/octet-stream",
        ".twb": "application/xml",
        ".twbx": "application/octet-stream",
        ".hyper": "application/octet-stream",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".json": "application/json",
        ".txt": "text/plain",
    }

    return mapping.get(
        suffix,
        "application/octet-stream",
    )


# ============================================================
# STATUS HELPERS
# ============================================================

def normalize_status(value):
    if value is None or pd.isna(value):
        return "UNKNOWN"

    return str(value).strip().upper()


def status_is_success(value):
    return normalize_status(value) in {
        "SUCCESS",
        "SUCCEEDED",
        "COMPLETED",
        "COMPLETE",
        "PASSED",
        "PASS",
        "OK",
        "HEALTHY",
    }


def status_is_failure(value):
    return normalize_status(value) in {
        "FAILED",
        "FAILURE",
        "ERROR",
        "REJECTED",
        "CRITICAL",
    }


def status_is_running(value):
    return normalize_status(value) in {
        "RUNNING",
        "STARTED",
        "IN_PROGRESS",
        "PROCESSING",
        "PENDING",
    }


# ============================================================
# ARTIFACT CLASSIFICATION
# ============================================================

def artifact_category(path: Path):
    suffix = path.suffix.lower()

    lower_path = str(path).lower()
    lower_name = path.name.lower()

    if suffix in {
        ".pbix",
        ".pbit",
    }:
        return "Power BI"

    if suffix in {
        ".twb",
        ".twbx",
        ".hyper",
    }:
        return "Tableau"

    if (
        "mis" in lower_name
        or "management" in lower_name
    ):
        return "MIS"

    if suffix in {
        ".xlsx",
        ".xls",
    }:
        return "Excel"

    if suffix == ".csv":
        return "Data Export"

    if suffix == ".pdf":
        return "PDF Report"

    if (
        "powerbi" in lower_path
        or "power_bi" in lower_path
    ):
        return "Power BI"

    if "tableau" in lower_path:
        return "Tableau"

    return "Other"


# ============================================================
# ARTIFACT DISCOVERY
# ============================================================

def discover_artifacts():
    search_roots = [
        EXPORT_ROOT,
        REPORTS_ROOT,
        PROJECT_ROOT / "powerbi",
        PROJECT_ROOT / "PowerBI",
        PROJECT_ROOT / "tableau",
        PROJECT_ROOT / "Tableau",
        PROJECT_ROOT / "dashboards",
        PROJECT_ROOT / "bi",
    ]

    discovered = {}

    for root in search_roots:
        if not root.exists():
            continue

        try:
            paths = root.rglob("*")

        except OSError:
            continue

        for path in paths:
            try:
                if not path.is_file():
                    continue

                if (
                    path.suffix.lower()
                    not in ALLOWED_ARTIFACT_SUFFIXES
                ):
                    continue

                resolved = path.resolve()

                key = str(resolved).lower()

                if key in discovered:
                    continue

                stat = resolved.stat()

                discovered[key] = {
                    "Artifact": resolved.name,
                    "Category": artifact_category(
                        resolved
                    ),
                    "Type": (
                        resolved.suffix
                        .replace(".", "")
                        .upper()
                    ),
                    "Size": format_bytes(
                        stat.st_size
                    ),
                    "Size Bytes": stat.st_size,
                    "Modified": datetime.fromtimestamp(
                        stat.st_mtime
                    ),
                    "Location": str(
                        resolved.parent
                    ),
                    "Path": str(
                        resolved
                    ),
                    "_path": resolved,
                }

            except OSError:
                continue

    if not discovered:
        return pd.DataFrame(
            columns=[
                "Artifact",
                "Category",
                "Type",
                "Size",
                "Size Bytes",
                "Modified",
                "Location",
                "Path",
                "_path",
            ]
        )

    return (
        pd.DataFrame(
            discovered.values()
        )
        .sort_values(
            "Modified",
            ascending=False,
        )
        .reset_index(drop=True)
    )


# ============================================================
# STORAGE INVENTORY
# ============================================================

def folder_inventory():
    folders = {
        "Raw Data": RAW_ROOT,
        "Incremental Data": INCREMENTAL_ROOT,
        "Processed Data": PROCESSED_ROOT,
        "Rejected Data": REJECTED_ROOT,
        "Exports": EXPORT_ROOT,
        "Reports": REPORTS_ROOT,
    }

    rows = []

    for name, path in folders.items():
        file_count = 0
        total_size = 0

        if path.exists():
            try:
                for file_path in path.rglob("*"):
                    if not file_path.is_file():
                        continue

                    file_count += 1

                    try:
                        total_size += (
                            file_path.stat().st_size
                        )

                    except OSError:
                        pass

            except OSError:
                pass

        rows.append(
            {
                "Area": name,
                "Exists": path.exists(),
                "Files": file_count,
                "Size Bytes": total_size,
                "Size": format_bytes(
                    total_size
                ),
                "Path": str(path),
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# DATABASE LOADERS
# ============================================================

@st.cache_data(
    ttl=30,
    show_spinner=False,
)
def load_database_health():
    return read_sql(
        """
        SELECT
            current_database() AS database_name,
            current_user AS database_user,
            version() AS database_version,
            current_timestamp AS database_time
        """
    )


@st.cache_data(
    ttl=30,
    show_spinner=False,
)
def load_schema_counts():
    return read_sql(
        """
        SELECT
            table_schema AS schema_name,
            COUNT(*) AS object_count
        FROM information_schema.tables
        WHERE table_schema IN (
            'warehouse',
            'analytics',
            'control',
            'staging'
        )
        GROUP BY table_schema
        ORDER BY table_schema
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
            'Patients' AS entity,
            COUNT(*)::BIGINT AS row_count
        FROM warehouse.dim_patient

        UNION ALL

        SELECT
            'Doctors',
            COUNT(*)::BIGINT
        FROM warehouse.dim_doctor

        UNION ALL

        SELECT
            'Departments',
            COUNT(*)::BIGINT
        FROM warehouse.dim_department

        UNION ALL

        SELECT
            'Insurers',
            COUNT(*)::BIGINT
        FROM warehouse.dim_insurer

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
            details,
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
            rejected_at
        FROM control.rejected_record
        ORDER BY rejected_at DESC, rejection_id DESC
        """
    )


@st.cache_data(
    ttl=30,
    show_spinner=False,
)
def load_audit_log():
    return read_sql(
        """
        SELECT
            audit_id,
            event_timestamp,
            username,
            module,
            action,
            entity_type,
            entity_id,
            status,
            details
        FROM control.audit_log
        ORDER BY event_timestamp DESC, audit_id DESC
        """
    )


@st.cache_data(
    ttl=30,
    show_spinner=False,
)
def load_analytics_objects():
    return read_sql(
        """
        SELECT
            table_name AS object_name,
            table_type
        FROM information_schema.tables
        WHERE table_schema = 'analytics'

        UNION ALL

        SELECT
            table_name AS object_name,
            'VIEW' AS table_type
        FROM information_schema.views
        WHERE table_schema = 'analytics'

        ORDER BY object_name
        """
    )


# ============================================================
# SAFE LOADING
# ============================================================

load_errors = {}


def safe_load(name, loader):
    try:
        return loader()

    except Exception as exc:
        load_errors[name] = str(exc)

        return pd.DataFrame()


database_health = safe_load(
    "Database Health",
    load_database_health,
)

schema_counts = safe_load(
    "Schema Counts",
    load_schema_counts,
)

warehouse_counts = safe_load(
    "Warehouse Counts",
    load_warehouse_counts,
)

etl_batches = safe_load(
    "ETL Batches",
    load_etl_batches,
)

quality_log = safe_load(
    "Data Quality",
    load_quality_log,
)

rejected_records = safe_load(
    "Rejected Records",
    load_rejected_records,
)

audit_log = safe_load(
    "Audit Log",
    load_audit_log,
)

analytics_objects = safe_load(
    "Analytics Objects",
    load_analytics_objects,
)

artifacts = discover_artifacts()

storage = folder_inventory()


# ============================================================
# DERIVED CONTROL-TOWER METRICS
# ============================================================

database_online = not database_health.empty


warehouse_total = (
    pd.to_numeric(
        warehouse_counts["row_count"],
        errors="coerce",
    )
    .fillna(0)
    .sum()
    if not warehouse_counts.empty
    else 0
)


analytics_count = (
    analytics_objects[
        "object_name"
    ].nunique()
    if not analytics_objects.empty
    else 0
)


latest_etl_status = (
    normalize_status(
        etl_batches.iloc[0]["status"]
    )
    if not etl_batches.empty
    else "UNAVAILABLE"
)


etl_success_count = 0
etl_failure_count = 0
etl_running_count = 0


if not etl_batches.empty:
    normalized_etl_status = (
        etl_batches["status"]
        .apply(normalize_status)
    )

    etl_success_count = int(
        normalized_etl_status
        .apply(status_is_success)
        .sum()
    )

    etl_failure_count = int(
        normalized_etl_status
        .apply(status_is_failure)
        .sum()
    )

    etl_running_count = int(
        normalized_etl_status
        .apply(status_is_running)
        .sum()
    )


dq_failed_records = 0
dq_failed_checks = 0


if not quality_log.empty:
    quality_log = quality_log.copy()

    quality_log[
        "failed_records"
    ] = pd.to_numeric(
        quality_log[
            "failed_records"
        ],
        errors="coerce",
    ).fillna(0)

    dq_failed_records = int(
        quality_log[
            "failed_records"
        ].sum()
    )

    dq_failed_checks = int(
        (
            quality_log[
                "failed_records"
            ]
            > 0
        ).sum()
    )


total_storage_files = (
    int(
        storage["Files"].sum()
    )
    if not storage.empty
    else 0
)


total_storage_bytes = (
    int(
        storage[
            "Size Bytes"
        ].sum()
    )
    if not storage.empty
    else 0
)


powerbi_count = (
    int(
        (
            artifacts[
                "Category"
            ]
            == "Power BI"
        ).sum()
    )
    if not artifacts.empty
    else 0
)


tableau_count = (
    int(
        (
            artifacts[
                "Category"
            ]
            == "Tableau"
        ).sum()
    )
    if not artifacts.empty
    else 0
)


mis_count = (
    int(
        (
            artifacts[
                "Category"
            ]
            == "MIS"
        ).sum()
    )
    if not artifacts.empty
    else 0
)


# ============================================================
# CONTROL TOWER HEALTH MODEL
# ============================================================

health_signals = []


health_signals.append(
    {
        "Component": "PostgreSQL",
        "Domain": "Database",
        "Status": (
            "Healthy"
            if database_online
            else "Unavailable"
        ),
        "Priority": (
            "Normal"
            if database_online
            else "Critical"
        ),
    }
)


health_signals.append(
    {
        "Component": "Latest ETL",
        "Domain": "Data Engineering",
        "Status": latest_etl_status,
        "Priority": (
            "Critical"
            if status_is_failure(
                latest_etl_status
            )
            else (
                "Watch"
                if status_is_running(
                    latest_etl_status
                )
                else "Normal"
            )
        ),
    }
)


health_signals.append(
    {
        "Component": "Data Quality",
        "Domain": "Governance",
        "Status": (
            f"{dq_failed_checks:,} checks with failures"
            if dq_failed_checks
            else "No recorded failures"
        ),
        "Priority": (
            "Watch"
            if dq_failed_checks
            else "Normal"
        ),
    }
)


health_signals.append(
    {
        "Component": "Rejected Register",
        "Domain": "Data Engineering",
        "Status": (
            f"{len(rejected_records):,} records"
        ),
        "Priority": (
            "Watch"
            if len(rejected_records)
            else "Normal"
        ),
    }
)


health_signals.append(
    {
        "Component": "Analytics Layer",
        "Domain": "BI Platform",
        "Status": (
            f"{analytics_count:,} objects"
        ),
        "Priority": (
            "Normal"
            if analytics_count
            else "Watch"
        ),
    }
)


health_signals.append(
    {
        "Component": "Artifact Vault",
        "Domain": "Reporting",
        "Status": (
            f"{len(artifacts):,} artifacts"
        ),
        "Priority": (
            "Normal"
            if len(artifacts)
            else "Watch"
        ),
    }
)


health_df = pd.DataFrame(
    health_signals
)


critical_signal_count = int(
    (
        health_df[
            "Priority"
        ]
        == "Critical"
    ).sum()
)


watch_signal_count = int(
    (
        health_df[
            "Priority"
        ]
        == "Watch"
    ).sum()
)


if critical_signal_count:
    platform_health = "CRITICAL"

elif watch_signal_count:
    platform_health = "ATTENTION"

else:
    platform_health = "HEALTHY"

# ============================================================
# CONTROL TOWER COMMAND STRIP
# ============================================================

command_left, command_refresh, command_cache = st.columns(
    [5, 1, 1]
)

with command_left:
    st.markdown(
        """
        ### Hospital 360 Enterprise Control Tower
        Monitor platform health, data pipelines, governance,
        reporting assets and administrative operations from one workspace.
        """
    )

with command_refresh:
    render_refresh_button(
        key="control_tower_refresh",
    )

with command_cache:
    if st.button(
        "Clear Cache",
        width="stretch",
        key="control_tower_clear_cache",
    ):
        clear_application_cache()
        st.success(
            "Application cache cleared successfully."
        )
        st.rerun()


# ============================================================
# PLATFORM STATUS
# ============================================================

section_header(
    "Platform Status",
    (
        "Immediate operational status of the Hospital 360 "
        "analytics platform."
    ),
)


metric_row(
    [
        (
            "Platform Health",
            platform_health,
        ),
        (
            "Database",
            (
                "Online"
                if database_online
                else "Unavailable"
            ),
        ),
        (
            "Latest ETL",
            latest_etl_status,
        ),
        (
            "Attention Items",
            format_integer(
                critical_signal_count
                + watch_signal_count
            ),
        ),
    ]
)


metric_row(
    [
        (
            "Warehouse Rows",
            format_integer(
                warehouse_total
            ),
        ),
        (
            "Analytics Objects",
            format_integer(
                analytics_count
            ),
        ),
        (
            "Reporting Assets",
            format_integer(
                len(artifacts)
            ),
        ),
        (
            "Audit Events",
            format_integer(
                len(audit_log)
            ),
        ),
    ]
)


# ============================================================
# MANAGEMENT SUMMARY
# ============================================================

if platform_health == "CRITICAL":
    management_insight(
        (
            "Hospital 360 currently has at least one critical "
            "platform signal. Review the Control Tower health "
            "matrix and ETL operations before relying on newly "
            "refreshed analytical outputs."
        ),
        label="Control Tower Assessment",
    )

elif platform_health == "ATTENTION":
    management_insight(
        (
            "The core Hospital 360 platform is available, but "
            "one or more operational areas require attention. "
            "Review pipeline, data-quality and rejection indicators "
            "before the next reporting cycle."
        ),
        label="Control Tower Assessment",
    )

else:
    management_insight(
        (
            "Core Hospital 360 platform signals are healthy. "
            "Database connectivity, analytical publishing and "
            "administrative monitoring are available for the "
            "current session."
        ),
        label="Control Tower Assessment",
    )


# ============================================================
# CONTROL TOWER NAVIGATION
# ============================================================

section_header(
    "Control Tower Workspaces",
    (
        "Each workspace has one administrative purpose so "
        "operations, monitoring and distribution remain easy "
        "to understand."
    ),
)


tabs = st.tabs(
    [
        "Command Center",
        "ETL Operations",
        "Data Quality",
        "Database & Warehouse",
        "Audit & Governance",
        "Download Center",
        "Storage",
        "Environment",
        "Platform Map",
        "Admin Actions",
    ]
)


# ============================================================
# TAB 1 — COMMAND CENTER
# ============================================================

with tabs[0]:
    section_header(
        "Enterprise Command Center",
        (
            "Single-screen operational overview of the Hospital 360 "
            "data and analytics platform."
        ),
    )


    # ========================================================
    # CORE PLATFORM
    # ========================================================

    st.markdown("### Core Platform")

    metric_row(
        [
            (
                "Database",
                (
                    "Healthy"
                    if database_online
                    else "Unavailable"
                ),
            ),
            (
                "Warehouse Records",
                format_integer(
                    warehouse_total
                ),
            ),
            (
                "Semantic Objects",
                format_integer(
                    analytics_count
                ),
            ),
            (
                "Storage Files",
                format_integer(
                    total_storage_files
                ),
            ),
        ]
    )


    # ========================================================
    # DATA ENGINEERING
    # ========================================================

    st.markdown("### Data Engineering")

    metric_row(
        [
            (
                "ETL Runs",
                format_integer(
                    len(etl_batches)
                ),
            ),
            (
                "Successful Runs",
                format_integer(
                    etl_success_count
                ),
            ),
            (
                "Failed Runs",
                format_integer(
                    etl_failure_count
                ),
            ),
            (
                "Running / Pending",
                format_integer(
                    etl_running_count
                ),
            ),
        ]
    )


    # ========================================================
    # DATA GOVERNANCE
    # ========================================================

    st.markdown("### Data Governance")

    metric_row(
        [
            (
                "Quality Checks",
                format_integer(
                    len(quality_log)
                ),
            ),
            (
                "Checks With Failures",
                format_integer(
                    dq_failed_checks
                ),
            ),
            (
                "Failed Records",
                format_integer(
                    dq_failed_records
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


    # ========================================================
    # REPORTING DISTRIBUTION
    # ========================================================

    st.markdown("### Analytics Distribution")

    metric_row(
        [
            (
                "All Artifacts",
                format_integer(
                    len(artifacts)
                ),
            ),
            (
                "Power BI",
                format_integer(
                    powerbi_count
                ),
            ),
            (
                "Tableau",
                format_integer(
                    tableau_count
                ),
            ),
            (
                "MIS Reports",
                format_integer(
                    mis_count
                ),
            ),
        ]
    )


    # ========================================================
    # PLATFORM HEALTH MATRIX
    # ========================================================

    section_header(
        "Platform Health Matrix",
        (
            "Operational signals requiring normal monitoring, "
            "attention or immediate investigation."
        ),
    )

    dataframe(
        health_df,
        height=320,
    )


    # ========================================================
    # HEALTH DISTRIBUTION
    # ========================================================

    if not health_df.empty:
        health_summary = (
            health_df[
                "Priority"
            ]
            .value_counts()
            .rename_axis(
                "Priority"
            )
            .reset_index(
                name="Signals"
            )
        )

        fig = px.bar(
            health_summary,
            x="Priority",
            y="Signals",
            title="Platform Health Signals",
            text_auto=True,
        )

        fig.update_xaxes(
            title=None
        )

        fig.update_yaxes(
            title="Signals"
        )

        st.plotly_chart(
            style_figure(
                fig,
                340,
            ),
            width="stretch",
        )


    # ========================================================
    # ETL SNAPSHOT
    # ========================================================

    section_header(
        "ETL Operations Snapshot",
        (
            "Latest pipeline execution status and recent "
            "data movement activity."
        ),
    )

    if etl_batches.empty:
        st.info(
            "No ETL execution history is currently available."
        )

    else:
        etl_status_summary = (
            etl_batches[
                "status"
            ]
            .fillna(
                "UNKNOWN"
            )
            .astype(str)
            .value_counts()
            .rename_axis(
                "Status"
            )
            .reset_index(
                name="Runs"
            )
        )

        left_chart, right_table = st.columns(
            [1, 1.35]
        )

        with left_chart:
            fig = px.bar(
                etl_status_summary,
                x="Status",
                y="Runs",
                title="ETL Run Status",
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
                    390,
                ),
                width="stretch",
            )

        with right_table:
            recent_columns = [
                column
                for column in [
                    "batch_id",
                    "batch_name",
                    "batch_type",
                    "source_name",
                    "status",
                    "records_received",
                    "records_inserted",
                    "records_rejected",
                    "duration_seconds",
                    "start_time",
                ]
                if column in etl_batches.columns
            ]

            dataframe(
                etl_batches[
                    recent_columns
                ].head(10),
                height=390,
            )


    # ========================================================
    # WAREHOUSE SNAPSHOT
    # ========================================================

    section_header(
        "Warehouse Estate",
        (
            "Record volume across the Hospital 360 "
            "dimensional warehouse."
        ),
    )

    if warehouse_counts.empty:
        st.info(
            "Warehouse inventory is currently unavailable."
        )

    else:
        warehouse_chart = (
            warehouse_counts.copy()
        )

        warehouse_chart[
            "row_count"
        ] = pd.to_numeric(
            warehouse_chart[
                "row_count"
            ],
            errors="coerce",
        ).fillna(0)

        fig = px.bar(
            warehouse_chart.sort_values(
                "row_count",
                ascending=True,
            ),
            x="row_count",
            y="entity",
            orientation="h",
            title="Warehouse Record Volume",
            text_auto=True,
        )

        fig.update_xaxes(
            title="Records"
        )

        fig.update_yaxes(
            title=None
        )

        st.plotly_chart(
            style_figure(
                fig,
                430,
            ),
            width="stretch",
        )

        dataframe(
            warehouse_chart,
            height=330,
        )


    # ========================================================
    # STORAGE SNAPSHOT
    # ========================================================

    section_header(
        "Storage Estate",
        (
            "Project storage footprint across ingestion, "
            "processing and reporting areas."
        ),
    )

    metric_row(
        [
            (
                "Tracked Areas",
                format_integer(
                    len(storage)
                ),
            ),
            (
                "Files",
                format_integer(
                    total_storage_files
                ),
            ),
            (
                "Storage Used",
                format_bytes(
                    total_storage_bytes
                ),
            ),
            (
                "Project",
                PROJECT_ROOT.name,
            ),
        ]
    )

    if not storage.empty:
        storage_chart = (
            storage.copy()
        )

        fig = px.bar(
            storage_chart,
            x="Area",
            y="Size Bytes",
            title="Storage by Platform Area",
            text="Size",
        )

        fig.update_xaxes(
            title=None
        )

        fig.update_yaxes(
            title="Bytes"
        )

        st.plotly_chart(
            style_figure(
                fig,
                370,
            ),
            width="stretch",
        )


    # ========================================================
    # REPORTING ASSETS
    # ========================================================

    section_header(
        "Reporting Asset Estate",
        (
            "Current reporting and business-intelligence "
            "deliverables discovered in the project."
        ),
    )

    if artifacts.empty:
        st.info(
            "No reporting artifacts have been discovered yet."
        )

    else:
        artifact_summary = (
            artifacts[
                "Category"
            ]
            .fillna(
                "Other"
            )
            .value_counts()
            .rename_axis(
                "Category"
            )
            .reset_index(
                name="Artifacts"
            )
        )

        fig = px.bar(
            artifact_summary,
            x="Category",
            y="Artifacts",
            title="Reporting Assets by Category",
            text_auto=True,
        )

        fig.update_xaxes(
            title=None
        )

        fig.update_yaxes(
            title="Artifacts"
        )

        st.plotly_chart(
            style_figure(
                fig,
                350,
            ),
            width="stretch",
        )

        artifact_columns = [
            column
            for column in [
                "Artifact",
                "Category",
                "Type",
                "Size",
                "Modified",
            ]
            if column in artifacts.columns
        ]

        dataframe(
            artifacts[
                artifact_columns
            ].head(15),
            height=390,
        )


    # ========================================================
    # ADMINISTRATIVE EXCEPTIONS
    # ========================================================

    section_header(
        "Administrative Exceptions",
        (
            "Components that could not be loaded during the "
            "current Control Tower session."
        ),
    )

    if not load_errors:
        st.success(
            "All configured Control Tower data sources loaded successfully."
        )

    else:
        diagnostics = pd.DataFrame(
            [
                {
                    "Component": name,
                    "Status": "Unavailable",
                    "Details": error,
                }
                for name, error
                in load_errors.items()
            ]
        )

        dataframe(
            diagnostics,
            height=320,
        )


    # ========================================================
    # CONTROL TOWER INTERPRETATION
    # ========================================================

    section_header(
        "How to Read This Control Tower",
        (
            "Operational sequence for administrators and "
            "project reviewers."
        ),
    )

    control_flow = pd.DataFrame(
        [
            {
                "Step": "01",
                "Area": "Platform Health",
                "Question": (
                    "Is the Hospital 360 platform operational?"
                ),
                "Next Workspace": "Command Center",
            },
            {
                "Step": "02",
                "Area": "ETL Operations",
                "Question": (
                    "Did source data load successfully?"
                ),
                "Next Workspace": "ETL Operations",
            },
            {
                "Step": "03",
                "Area": "Data Quality",
                "Question": (
                    "Did validation identify bad or rejected records?"
                ),
                "Next Workspace": "Data Quality",
            },
            {
                "Step": "04",
                "Area": "Warehouse",
                "Question": (
                    "Is governed analytical data available?"
                ),
                "Next Workspace": "Database & Warehouse",
            },
            {
                "Step": "05",
                "Area": "Audit",
                "Question": (
                    "What administrative activity occurred?"
                ),
                "Next Workspace": "Audit & Governance",
            },
            {
                "Step": "06",
                "Area": "Distribution",
                "Question": (
                    "Which reports and BI deliverables are ready?"
                ),
                "Next Workspace": "Download Center",
            },
            {
                "Step": "07",
                "Area": "Administration",
                "Question": (
                    "Which safe platform controls can be executed?"
                ),
                "Next Workspace": "Admin Actions",
            },
        ]
    )

    dataframe(
        control_flow,
        height=340,
    )

# ============================================================
# TAB 2 — ETL OPERATIONS
# ============================================================

with tabs[1]:
    section_header(
        "ETL Operations",
        (
            "Operational command workspace for monitoring Hospital 360 "
            "data ingestion, pipeline execution, throughput, rejected "
            "records and batch-level failures."
        ),
    )

    if etl_batches.empty:
        st.warning(
            "ETL execution history is currently unavailable. "
            "Check the database connection and control.etl_batch."
        )

    else:
        etl_ops = etl_batches.copy()

        numeric_columns = [
            "records_received",
            "records_inserted",
            "records_updated",
            "records_rejected",
            "duration_seconds",
        ]

        for column in numeric_columns:
            if column in etl_ops.columns:
                etl_ops[column] = pd.to_numeric(
                    etl_ops[column],
                    errors="coerce",
                ).fillna(0)

        for column in [
            "start_time",
            "end_time",
            "created_at",
            "business_date",
        ]:
            if column in etl_ops.columns:
                etl_ops[column] = pd.to_datetime(
                    etl_ops[column],
                    errors="coerce",
                )

        etl_ops["normalized_status"] = (
            etl_ops["status"]
            .apply(normalize_status)
        )

        etl_ops["status_group"] = (
            etl_ops["normalized_status"]
            .apply(
                lambda value: (
                    "Successful"
                    if status_is_success(value)
                    else (
                        "Failed"
                        if status_is_failure(value)
                        else (
                            "Running"
                            if status_is_running(value)
                            else "Other"
                        )
                    )
                )
            )
        )

        total_received = int(
            etl_ops[
                "records_received"
            ].sum()
        )

        total_inserted = int(
            etl_ops[
                "records_inserted"
            ].sum()
        )

        total_updated = int(
            etl_ops[
                "records_updated"
            ].sum()
        )

        total_rejected = int(
            etl_ops[
                "records_rejected"
            ].sum()
        )

        successful_runs = int(
            (
                etl_ops[
                    "status_group"
                ]
                == "Successful"
            ).sum()
        )

        failed_runs = int(
            (
                etl_ops[
                    "status_group"
                ]
                == "Failed"
            ).sum()
        )

        running_runs = int(
            (
                etl_ops[
                    "status_group"
                ]
                == "Running"
            ).sum()
        )

        success_rate = (
            (
                successful_runs
                / len(etl_ops)
            )
            * 100
            if len(etl_ops)
            else 0
        )

        rejection_rate = (
            (
                total_rejected
                / total_received
            )
            * 100
            if total_received
            else 0
        )

        average_duration = (
            etl_ops[
                "duration_seconds"
            ].mean()
            if "duration_seconds"
            in etl_ops.columns
            else 0
        )

        latest_batch = (
            etl_ops.iloc[0]
            if not etl_ops.empty
            else None
        )


        # ====================================================
        # ETL CONTROL STATUS
        # ====================================================

        st.markdown("### Pipeline Control Status")

        metric_row(
            [
                (
                    "Latest Batch",
                    (
                        str(
                            latest_batch[
                                "batch_id"
                            ]
                        )
                        if latest_batch is not None
                        else "N/A"
                    ),
                ),
                (
                    "Latest Status",
                    (
                        normalize_status(
                            latest_batch[
                                "status"
                            ]
                        )
                        if latest_batch is not None
                        else "N/A"
                    ),
                ),
                (
                    "Successful Runs",
                    format_integer(
                        successful_runs
                    ),
                ),
                (
                    "Failed Runs",
                    format_integer(
                        failed_runs
                    ),
                ),
            ]
        )

        metric_row(
            [
                (
                    "Total Received",
                    format_integer(
                        total_received
                    ),
                ),
                (
                    "Inserted",
                    format_integer(
                        total_inserted
                    ),
                ),
                (
                    "Updated",
                    format_integer(
                        total_updated
                    ),
                ),
                (
                    "Rejected",
                    format_integer(
                        total_rejected
                    ),
                ),
            ]
        )

        metric_row(
            [
                (
                    "Pipeline Success",
                    f"{success_rate:,.1f}%",
                ),
                (
                    "Rejection Rate",
                    f"{rejection_rate:,.2f}%",
                ),
                (
                    "Avg Duration",
                    f"{average_duration:,.1f} sec",
                ),
                (
                    "Running / Pending",
                    format_integer(
                        running_runs
                    ),
                ),
            ]
        )


        # ====================================================
        # OPERATIONAL ASSESSMENT
        # ====================================================

        if failed_runs > 0:
            management_insight(
                (
                    f"{failed_runs:,} ETL execution(s) are classified as "
                    "failed in the available batch history. Review the "
                    "failure register, error messages and rejected records "
                    "before treating the latest warehouse refresh as fully "
                    "operational."
                ),
                label="ETL Operations Assessment",
            )

        elif total_rejected > 0:
            management_insight(
                (
                    f"Pipeline execution is operational, but "
                    f"{total_rejected:,} source records have been rejected "
                    "across the available ETL history. Review rejection "
                    "patterns and related data-quality rules."
                ),
                label="ETL Operations Assessment",
            )

        else:
            management_insight(
                (
                    "No failed ETL executions or rejected source records "
                    "are visible in the currently loaded pipeline history."
                ),
                label="ETL Operations Assessment",
            )


        # ====================================================
        # ETL FILTERS
        # ====================================================

        section_header(
            "Pipeline Explorer",
            (
                "Filter the ETL execution history by status, batch type "
                "and source system."
            ),
        )

        filter_one, filter_two, filter_three = st.columns(3)

        status_options = sorted(
            [
                value
                for value in (
                    etl_ops[
                        "normalized_status"
                    ]
                    .dropna()
                    .unique()
                    .tolist()
                )
                if value
            ]
        )

        batch_type_options = (
            sorted(
                etl_ops[
                    "batch_type"
                ]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
            if "batch_type"
            in etl_ops.columns
            else []
        )

        source_options = (
            sorted(
                etl_ops[
                    "source_name"
                ]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
            if "source_name"
            in etl_ops.columns
            else []
        )

        with filter_one:
            selected_status = st.multiselect(
                "Pipeline Status",
                options=status_options,
                default=[],
                key="control_tower_etl_status",
            )

        with filter_two:
            selected_batch_types = st.multiselect(
                "Batch Type",
                options=batch_type_options,
                default=[],
                key="control_tower_etl_batch_type",
            )

        with filter_three:
            selected_sources = st.multiselect(
                "Source",
                options=source_options,
                default=[],
                key="control_tower_etl_source",
            )

        filtered_etl = etl_ops.copy()

        if selected_status:
            filtered_etl = filtered_etl[
                filtered_etl[
                    "normalized_status"
                ].isin(
                    selected_status
                )
            ]

        if selected_batch_types:
            filtered_etl = filtered_etl[
                filtered_etl[
                    "batch_type"
                ]
                .astype(str)
                .isin(
                    selected_batch_types
                )
            ]

        if selected_sources:
            filtered_etl = filtered_etl[
                filtered_etl[
                    "source_name"
                ]
                .astype(str)
                .isin(
                    selected_sources
                )
            ]


        # ====================================================
        # STATUS DISTRIBUTION
        # ====================================================

        section_header(
            "Execution Status",
            (
                "Distribution of successful, failed, running and other "
                "pipeline executions."
            ),
        )

        status_summary = (
            etl_ops[
                "status_group"
            ]
            .value_counts()
            .rename_axis(
                "Status"
            )
            .reset_index(
                name="Runs"
            )
        )

        status_chart, status_table = st.columns(
            [1.1, 1]
        )

        with status_chart:
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
                title="Pipeline Runs"
            )

            st.plotly_chart(
                style_figure(
                    fig,
                    380,
                ),
                width="stretch",
            )

        with status_table:
            dataframe(
                status_summary,
                height=380,
            )


        # ====================================================
        # PIPELINE THROUGHPUT
        # ====================================================

        section_header(
            "Pipeline Throughput",
            (
                "Compare received, inserted, updated and rejected "
                "record volumes across recent ETL batches."
            ),
        )

        throughput_columns = [
            column
            for column in [
                "batch_id",
                "records_received",
                "records_inserted",
                "records_updated",
                "records_rejected",
            ]
            if column in etl_ops.columns
        ]

        throughput = (
            etl_ops[
                throughput_columns
            ]
            .head(30)
            .copy()
        )

        if (
            not throughput.empty
            and "batch_id"
            in throughput.columns
        ):
            throughput_long = (
                throughput.melt(
                    id_vars=[
                        "batch_id"
                    ],
                    value_vars=[
                        column
                        for column in [
                            "records_received",
                            "records_inserted",
                            "records_updated",
                            "records_rejected",
                        ]
                        if column
                        in throughput.columns
                    ],
                    var_name="Metric",
                    value_name="Records",
                )
            )

            throughput_long[
                "Metric"
            ] = (
                throughput_long[
                    "Metric"
                ]
                .str.replace(
                    "records_",
                    "",
                    regex=False,
                )
                .str.replace(
                    "_",
                    " ",
                    regex=False,
                )
                .str.title()
            )

            fig = px.bar(
                throughput_long,
                x="batch_id",
                y="Records",
                color="Metric",
                barmode="group",
                title="Record Movement by Recent Batch",
            )

            fig.update_xaxes(
                title="Batch ID",
                type="category",
            )

            fig.update_yaxes(
                title="Records"
            )

            st.plotly_chart(
                style_figure(
                    fig,
                    460,
                ),
                width="stretch",
            )

        else:
            st.info(
                "Pipeline throughput metrics are unavailable."
            )


        # ====================================================
        # BATCH DURATION
        # ====================================================

        section_header(
            "Pipeline Duration",
            (
                "Execution duration helps identify slow or abnormal "
                "pipeline runs."
            ),
        )

        duration_data = etl_ops[
            [
                column
                for column in [
                    "batch_id",
                    "batch_name",
                    "duration_seconds",
                    "status_group",
                ]
                if column in etl_ops.columns
            ]
        ].copy()

        if (
            not duration_data.empty
            and "duration_seconds"
            in duration_data.columns
            and "batch_id"
            in duration_data.columns
        ):
            duration_data = (
                duration_data[
                    duration_data[
                        "duration_seconds"
                    ]
                    >= 0
                ]
                .head(40)
            )

            fig = px.bar(
                duration_data,
                x="batch_id",
                y="duration_seconds",
                color="status_group",
                title="ETL Duration by Batch",
                hover_data=[
                    column
                    for column in [
                        "batch_name"
                    ]
                    if column
                    in duration_data.columns
                ],
            )

            fig.update_xaxes(
                title="Batch ID",
                type="category",
            )

            fig.update_yaxes(
                title="Duration (seconds)"
            )

            st.plotly_chart(
                style_figure(
                    fig,
                    420,
                ),
                width="stretch",
            )

        else:
            st.info(
                "Batch duration information is unavailable."
            )


        # ====================================================
        # SOURCE SYSTEM MONITORING
        # ====================================================

        section_header(
            "Source System Monitoring",
            (
                "Operational view of pipeline activity and rejected "
                "records by source."
            ),
        )

        if "source_name" in etl_ops.columns:
            source_summary = (
                etl_ops.groupby(
                    "source_name",
                    dropna=False,
                )
                .agg(
                    Runs=(
                        "batch_id",
                        "count",
                    ),
                    Received=(
                        "records_received",
                        "sum",
                    ),
                    Inserted=(
                        "records_inserted",
                        "sum",
                    ),
                    Updated=(
                        "records_updated",
                        "sum",
                    ),
                    Rejected=(
                        "records_rejected",
                        "sum",
                    ),
                    Avg_Duration_Seconds=(
                        "duration_seconds",
                        "mean",
                    ),
                )
                .reset_index()
            )

            source_summary[
                "source_name"
            ] = (
                source_summary[
                    "source_name"
                ]
                .fillna(
                    "Unknown"
                )
                .astype(str)
            )

            source_summary[
                "Avg_Duration_Seconds"
            ] = (
                source_summary[
                    "Avg_Duration_Seconds"
                ]
                .round(2)
            )

            source_left, source_right = st.columns(
                [1.15, 1]
            )

            with source_left:
                fig = px.bar(
                    source_summary.sort_values(
                        "Received",
                        ascending=False,
                    ),
                    x="source_name",
                    y="Received",
                    title="Records Received by Source",
                    text_auto=True,
                )

                fig.update_xaxes(
                    title=None
                )

                fig.update_yaxes(
                    title="Records Received"
                )

                st.plotly_chart(
                    style_figure(
                        fig,
                        410,
                    ),
                    width="stretch",
                )

            with source_right:
                dataframe(
                    source_summary,
                    height=410,
                )

        else:
            st.info(
                "Source-level ETL information is unavailable."
            )


        # ====================================================
        # REJECTION ANALYSIS
        # ====================================================

        section_header(
            "Pipeline Rejection Monitoring",
            (
                "Identify ETL batches contributing the largest number "
                "of rejected source records."
            ),
        )

        rejection_batches = (
            etl_ops[
                etl_ops[
                    "records_rejected"
                ]
                > 0
            ]
            .copy()
        )

        if rejection_batches.empty:
            st.success(
                "No rejected records are recorded against the "
                "available ETL batches."
            )

        else:
            rejection_display_columns = [
                column
                for column in [
                    "batch_id",
                    "batch_name",
                    "source_name",
                    "status",
                    "records_received",
                    "records_rejected",
                    "business_date",
                    "start_time",
                ]
                if column
                in rejection_batches.columns
            ]

            rejection_chart, rejection_table = st.columns(
                [1, 1.3]
            )

            with rejection_chart:
                rejection_plot = (
                    rejection_batches[
                        [
                            "batch_id",
                            "records_rejected",
                        ]
                    ]
                    .sort_values(
                        "records_rejected",
                        ascending=False,
                    )
                    .head(15)
                )

                fig = px.bar(
                    rejection_plot,
                    x="records_rejected",
                    y=rejection_plot[
                        "batch_id"
                    ].astype(str),
                    orientation="h",
                    title="Highest Rejection Batches",
                    text_auto=True,
                )

                fig.update_xaxes(
                    title="Rejected Records"
                )

                fig.update_yaxes(
                    title="Batch ID",
                    autorange="reversed",
                )

                st.plotly_chart(
                    style_figure(
                        fig,
                        430,
                    ),
                    width="stretch",
                )

            with rejection_table:
                dataframe(
                    rejection_batches[
                        rejection_display_columns
                    ]
                    .sort_values(
                        "records_rejected",
                        ascending=False,
                    )
                    .head(25),
                    height=430,
                )


        # ====================================================
        # FAILURE INVESTIGATION
        # ====================================================

        section_header(
            "Failure Investigation",
            (
                "Inspect pipeline executions classified as failed "
                "and review their recorded error messages."
            ),
        )

        failed_batches = etl_ops[
            etl_ops[
                "status_group"
            ]
            == "Failed"
        ].copy()

        if failed_batches.empty:
            st.success(
                "No failed ETL batches are visible in the "
                "current execution history."
            )

        else:
            failure_columns = [
                column
                for column in [
                    "batch_id",
                    "batch_name",
                    "batch_type",
                    "source_name",
                    "status",
                    "records_received",
                    "records_inserted",
                    "records_updated",
                    "records_rejected",
                    "duration_seconds",
                    "error_message",
                    "start_time",
                    "end_time",
                    "source_path",
                ]
                if column
                in failed_batches.columns
            ]

            dataframe(
                failed_batches[
                    failure_columns
                ],
                height=460,
            )


        # ====================================================
        # BATCH INSPECTOR
        # ====================================================

        section_header(
            "Batch Inspector",
            (
                "Select one pipeline batch to inspect its execution "
                "metadata, record movement and associated quality events."
            ),
        )

        available_batch_ids = (
            etl_ops[
                "batch_id"
            ]
            .dropna()
            .tolist()
        )

        if available_batch_ids:
            selected_batch_id = st.selectbox(
                "Select Batch",
                options=available_batch_ids,
                key="control_tower_batch_inspector",
            )

            selected_batch = (
                etl_ops[
                    etl_ops[
                        "batch_id"
                    ]
                    == selected_batch_id
                ]
                .head(1)
            )

            if not selected_batch.empty:
                batch_row = (
                    selected_batch.iloc[0]
                )

                metric_row(
                    [
                        (
                            "Batch ID",
                            str(
                                batch_row.get(
                                    "batch_id",
                                    "N/A",
                                )
                            ),
                        ),
                        (
                            "Status",
                            normalize_status(
                                batch_row.get(
                                    "status"
                                )
                            ),
                        ),
                        (
                            "Type",
                            str(
                                batch_row.get(
                                    "batch_type",
                                    "N/A",
                                )
                            ),
                        ),
                        (
                            "Source",
                            str(
                                batch_row.get(
                                    "source_name",
                                    "N/A",
                                )
                            ),
                        ),
                    ]
                )

                metric_row(
                    [
                        (
                            "Received",
                            format_integer(
                                safe_number(
                                    batch_row.get(
                                        "records_received"
                                    )
                                )
                            ),
                        ),
                        (
                            "Inserted",
                            format_integer(
                                safe_number(
                                    batch_row.get(
                                        "records_inserted"
                                    )
                                )
                            ),
                        ),
                        (
                            "Updated",
                            format_integer(
                                safe_number(
                                    batch_row.get(
                                        "records_updated"
                                    )
                                )
                            ),
                        ),
                        (
                            "Rejected",
                            format_integer(
                                safe_number(
                                    batch_row.get(
                                        "records_rejected"
                                    )
                                )
                            ),
                        ),
                    ]
                )

                inspector_data = pd.DataFrame(
                    [
                        {
                            "Field": column,
                            "Value": (
                                ""
                                if pd.isna(
                                    batch_row.get(
                                        column
                                    )
                                )
                                else str(
                                    batch_row.get(
                                        column
                                    )
                                )
                            ),
                        }
                        for column
                        in etl_ops.columns
                        if column
                        not in {
                            "normalized_status",
                            "status_group",
                        }
                    ]
                )

                dataframe(
                    inspector_data,
                    height=420,
                )

                if not quality_log.empty:
                    batch_quality = (
                        quality_log[
                            quality_log[
                                "batch_id"
                            ]
                            == selected_batch_id
                        ]
                        .copy()
                    )

                    st.markdown(
                        "#### Data Quality Events for Selected Batch"
                    )

                    if batch_quality.empty:
                        st.info(
                            "No data-quality events are linked to "
                            "the selected batch."
                        )

                    else:
                        quality_columns = [
                            column
                            for column in [
                                "quality_log_id",
                                "table_name",
                                "rule_name",
                                "rule_type",
                                "records_checked",
                                "failed_records",
                                "severity",
                                "status",
                                "details",
                                "checked_at",
                            ]
                            if column
                            in batch_quality.columns
                        ]

                        dataframe(
                            batch_quality[
                                quality_columns
                            ],
                            height=360,
                        )

                if not rejected_records.empty:
                    batch_rejections = (
                        rejected_records[
                            rejected_records[
                                "batch_id"
                            ]
                            == selected_batch_id
                        ]
                        .copy()
                    )

                    st.markdown(
                        "#### Rejected Records for Selected Batch"
                    )

                    if batch_rejections.empty:
                        st.info(
                            "No rejected-record entries are linked "
                            "to the selected batch."
                        )

                    else:
                        dataframe(
                            batch_rejections,
                            height=360,
                        )


        # ====================================================
        # COMPLETE EXECUTION REGISTER
        # ====================================================

        section_header(
            "ETL Execution Register",
            (
                "Complete filtered pipeline execution register for "
                "operational review."
            ),
        )

        display_columns = [
            column
            for column in [
                "batch_id",
                "batch_name",
                "batch_type",
                "source_name",
                "status",
                "records_received",
                "records_inserted",
                "records_updated",
                "records_rejected",
                "duration_seconds",
                "business_date",
                "start_time",
                "end_time",
                "source_batch_id",
                "source_path",
                "error_message",
            ]
            if column
            in filtered_etl.columns
        ]

        dataframe(
            filtered_etl[
                display_columns
            ],
            height=560,
        )


        # ====================================================
        # ETL OPERATING FLOW
        # ====================================================

        section_header(
            "ETL Operating Flow",
            (
                "Sequence used to understand how source data moves "
                "into governed Hospital 360 analytics."
            ),
        )

        etl_flow = pd.DataFrame(
            [
                {
                    "Stage": "01",
                    "Process": "Source Arrival",
                    "Control Question": (
                        "Did the expected source batch arrive?"
                    ),
                    "Evidence": (
                        "Source name, source path and source batch ID"
                    ),
                },
                {
                    "Stage": "02",
                    "Process": "Pipeline Execution",
                    "Control Question": (
                        "Did the ETL batch start and complete?"
                    ),
                    "Evidence": (
                        "Batch status, start time and end time"
                    ),
                },
                {
                    "Stage": "03",
                    "Process": "Record Processing",
                    "Control Question": (
                        "How many records were received and processed?"
                    ),
                    "Evidence": (
                        "Received, inserted and updated records"
                    ),
                },
                {
                    "Stage": "04",
                    "Process": "Quality Control",
                    "Control Question": (
                        "Which records failed validation?"
                    ),
                    "Evidence": (
                        "Data-quality log and failed-record count"
                    ),
                },
                {
                    "Stage": "05",
                    "Process": "Rejection Handling",
                    "Control Question": (
                        "Which records were rejected and why?"
                    ),
                    "Evidence": (
                        "Rejected-record register and rejection reason"
                    ),
                },
                {
                    "Stage": "06",
                    "Process": "Warehouse Availability",
                    "Control Question": (
                        "Is processed data available for analytics?"
                    ),
                    "Evidence": (
                        "Warehouse and semantic-layer inventory"
                    ),
                },
            ]
        )

        dataframe(
            etl_flow,
            height=330,
        )

    # ============================================================
# TAB 3 — DATA QUALITY
# ============================================================

with tabs[2]:
    section_header(
        "Data Quality Control",
        (
            "Enterprise quality monitoring for validation rules, failed "
            "records, severity, rejected data and batch-level exceptions."
        ),
    )

    if quality_log.empty:
        st.warning(
            "Data-quality history is currently unavailable. "
            "Check control.data_quality_log and database connectivity."
        )

    else:
        dq = quality_log.copy()

        for column in [
            "records_checked",
            "failed_records",
        ]:
            if column in dq.columns:
                dq[column] = pd.to_numeric(
                    dq[column],
                    errors="coerce",
                ).fillna(0)

        if "checked_at" in dq.columns:
            dq["checked_at"] = pd.to_datetime(
                dq["checked_at"],
                errors="coerce",
            )

        dq["severity_normalized"] = (
            dq["severity"]
            .fillna("UNKNOWN")
            .astype(str)
            .str.strip()
            .str.upper()
        )

        dq["status_normalized"] = (
            dq["status"]
            .fillna("UNKNOWN")
            .astype(str)
            .str.strip()
            .str.upper()
        )

        dq["has_failure"] = (
            dq["failed_records"] > 0
        )

        total_checks = len(dq)

        total_records_checked = int(
            dq["records_checked"].sum()
        )

        total_failed_records = int(
            dq["failed_records"].sum()
        )

        checks_with_failures = int(
            dq["has_failure"].sum()
        )

        clean_checks = (
            total_checks
            - checks_with_failures
        )

        check_pass_rate = (
            (
                clean_checks
                / total_checks
            )
            * 100
            if total_checks
            else 0
        )

        record_failure_rate = (
            (
                total_failed_records
                / total_records_checked
            )
            * 100
            if total_records_checked
            else 0
        )

        critical_failures = int(
            (
                (
                    dq[
                        "severity_normalized"
                    ]
                    == "CRITICAL"
                )
                & dq[
                    "has_failure"
                ]
            ).sum()
        )

        high_failures = int(
            (
                (
                    dq[
                        "severity_normalized"
                    ]
                    == "HIGH"
                )
                & dq[
                    "has_failure"
                ]
            ).sum()
        )


        # ====================================================
        # QUALITY SCORECARD
        # ====================================================

        st.markdown("### Quality Scorecard")

        metric_row(
            [
                (
                    "Quality Checks",
                    format_integer(
                        total_checks
                    ),
                ),
                (
                    "Clean Checks",
                    format_integer(
                        clean_checks
                    ),
                ),
                (
                    "Checks With Failures",
                    format_integer(
                        checks_with_failures
                    ),
                ),
                (
                    "Check Pass Rate",
                    f"{check_pass_rate:,.1f}%",
                ),
            ]
        )

        metric_row(
            [
                (
                    "Records Checked",
                    format_integer(
                        total_records_checked
                    ),
                ),
                (
                    "Failed Records",
                    format_integer(
                        total_failed_records
                    ),
                ),
                (
                    "Record Failure Rate",
                    f"{record_failure_rate:,.2f}%",
                ),
                (
                    "Rejected Register",
                    format_integer(
                        len(rejected_records)
                    ),
                ),
            ]
        )

        metric_row(
            [
                (
                    "Critical Failures",
                    format_integer(
                        critical_failures
                    ),
                ),
                (
                    "High Failures",
                    format_integer(
                        high_failures
                    ),
                ),
                (
                    "Tables Checked",
                    format_integer(
                        dq[
                            "table_name"
                        ].nunique()
                    ),
                ),
                (
                    "Rules Executed",
                    format_integer(
                        dq[
                            "rule_name"
                        ].nunique()
                    ),
                ),
            ]
        )


        # ====================================================
        # QUALITY ASSESSMENT
        # ====================================================

        if critical_failures > 0:
            management_insight(
                (
                    f"{critical_failures:,} critical data-quality "
                    "check(s) contain failed records. These exceptions "
                    "should be investigated before downstream reporting "
                    "outputs are treated as fully validated."
                ),
                label="Data Quality Assessment",
            )

        elif high_failures > 0:
            management_insight(
                (
                    f"{high_failures:,} high-severity quality check(s) "
                    "contain failed records. Review affected tables, rules "
                    "and rejected records before the next reporting cycle."
                ),
                label="Data Quality Assessment",
            )

        elif checks_with_failures > 0:
            management_insight(
                (
                    f"{checks_with_failures:,} quality check(s) contain "
                    f"{total_failed_records:,} failed records. No critical "
                    "severity failure is currently visible, but the "
                    "exceptions should still be reviewed."
                ),
                label="Data Quality Assessment",
            )

        else:
            management_insight(
                (
                    "No failed records are recorded across the currently "
                    "loaded data-quality checks."
                ),
                label="Data Quality Assessment",
            )


        # ====================================================
        # QUALITY FILTERS
        # ====================================================

        section_header(
            "Quality Explorer",
            (
                "Filter validation history by table, severity, rule type "
                "and quality status."
            ),
        )

        filter_one, filter_two = st.columns(2)
        filter_three, filter_four = st.columns(2)

        table_options = sorted(
            dq[
                "table_name"
            ]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        severity_options = sorted(
            dq[
                "severity_normalized"
            ]
            .dropna()
            .unique()
            .tolist()
        )

        rule_type_options = (
            sorted(
                dq[
                    "rule_type"
                ]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
            if "rule_type"
            in dq.columns
            else []
        )

        status_options = sorted(
            dq[
                "status_normalized"
            ]
            .dropna()
            .unique()
            .tolist()
        )

        with filter_one:
            selected_tables = st.multiselect(
                "Table",
                options=table_options,
                default=[],
                key="control_tower_dq_table",
            )

        with filter_two:
            selected_severity = st.multiselect(
                "Severity",
                options=severity_options,
                default=[],
                key="control_tower_dq_severity",
            )

        with filter_three:
            selected_rule_types = st.multiselect(
                "Rule Type",
                options=rule_type_options,
                default=[],
                key="control_tower_dq_rule_type",
            )

        with filter_four:
            selected_dq_status = st.multiselect(
                "Quality Status",
                options=status_options,
                default=[],
                key="control_tower_dq_status",
            )

        filtered_dq = dq.copy()

        if selected_tables:
            filtered_dq = filtered_dq[
                filtered_dq[
                    "table_name"
                ]
                .astype(str)
                .isin(
                    selected_tables
                )
            ]

        if selected_severity:
            filtered_dq = filtered_dq[
                filtered_dq[
                    "severity_normalized"
                ].isin(
                    selected_severity
                )
            ]

        if selected_rule_types:
            filtered_dq = filtered_dq[
                filtered_dq[
                    "rule_type"
                ]
                .astype(str)
                .isin(
                    selected_rule_types
                )
            ]

        if selected_dq_status:
            filtered_dq = filtered_dq[
                filtered_dq[
                    "status_normalized"
                ].isin(
                    selected_dq_status
                )
            ]


        # ====================================================
        # SEVERITY MATRIX
        # ====================================================

        section_header(
            "Severity Matrix",
            (
                "Understand where data-quality exceptions sit within "
                "the configured severity hierarchy."
            ),
        )

        severity_summary = (
            dq.groupby(
                "severity_normalized",
                as_index=False,
            )
            .agg(
                Checks=(
                    "quality_log_id",
                    "count",
                ),
                Records_Checked=(
                    "records_checked",
                    "sum",
                ),
                Failed_Records=(
                    "failed_records",
                    "sum",
                ),
            )
            .rename(
                columns={
                    "severity_normalized":
                        "Severity"
                }
            )
        )

        severity_summary[
            "Failure_Rate_Pct"
        ] = (
            (
                severity_summary[
                    "Failed_Records"
                ]
                / severity_summary[
                    "Records_Checked"
                ].replace(
                    0,
                    pd.NA,
                )
            )
            * 100
        ).fillna(0).round(2)

        severity_chart, severity_table = st.columns(
            [1.05, 1]
        )

        with severity_chart:
            fig = px.bar(
                severity_summary,
                x="Severity",
                y="Failed_Records",
                title="Failed Records by Severity",
                text_auto=True,
            )

            fig.update_xaxes(
                title=None
            )

            fig.update_yaxes(
                title="Failed Records"
            )

            st.plotly_chart(
                style_figure(
                    fig,
                    390,
                ),
                width="stretch",
            )

        with severity_table:
            dataframe(
                severity_summary,
                height=390,
            )


        # ====================================================
        # TABLE QUALITY HEALTH
        # ====================================================

        section_header(
            "Table Quality Health",
            (
                "Compare validation volume and failed records across "
                "warehouse and analytical data objects."
            ),
        )

        table_quality = (
            dq.groupby(
                "table_name",
                as_index=False,
            )
            .agg(
                Checks=(
                    "quality_log_id",
                    "count",
                ),
                Records_Checked=(
                    "records_checked",
                    "sum",
                ),
                Failed_Records=(
                    "failed_records",
                    "sum",
                ),
            )
        )

        table_quality[
            "Failure_Rate_Pct"
        ] = (
            (
                table_quality[
                    "Failed_Records"
                ]
                / table_quality[
                    "Records_Checked"
                ].replace(
                    0,
                    pd.NA,
                )
            )
            * 100
        ).fillna(0).round(2)

        table_quality = (
            table_quality.sort_values(
                by=[
                    "Failed_Records"
                ],
                ascending=[
                    False
                ],
            )
            .reset_index(
                drop=True
            )
        )

        table_chart, table_register = st.columns(
            [1.1, 1]
        )

        with table_chart:
            fig = px.bar(
                table_quality.head(20),
                x="Failed_Records",
                y="table_name",
                orientation="h",
                title="Failed Records by Table",
                text_auto=True,
            )

            fig.update_xaxes(
                title="Failed Records"
            )

            fig.update_yaxes(
                title=None,
                autorange="reversed",
            )

            st.plotly_chart(
                style_figure(
                    fig,
                    440,
                ),
                width="stretch",
            )

        with table_register:
            dataframe(
                table_quality,
                height=440,
            )


        # ====================================================
        # RULE FAILURE ANALYSIS
        # ====================================================

        section_header(
            "Rule Failure Analysis",
            (
                "Identify validation rules responsible for the largest "
                "number of failed records."
            ),
        )

        rule_summary = (
            dq.groupby(
                [
                    "rule_name",
                    "rule_type",
                ],
                dropna=False,
                as_index=False,
            )
            .agg(
                Executions=(
                    "quality_log_id",
                    "count",
                ),
                Records_Checked=(
                    "records_checked",
                    "sum",
                ),
                Failed_Records=(
                    "failed_records",
                    "sum",
                ),
            )
        )

        rule_summary[
            "Failure_Rate_Pct"
        ] = (
            (
                rule_summary[
                    "Failed_Records"
                ]
                / rule_summary[
                    "Records_Checked"
                ].replace(
                    0,
                    pd.NA,
                )
            )
            * 100
        ).fillna(0).round(2)

        rule_summary = (
            rule_summary.sort_values(
                by=[
                    "Failed_Records"
                ],
                ascending=[
                    False
                ],
            )
            .reset_index(
                drop=True
            )
        )

        rule_left, rule_right = st.columns(
            [1.05, 1]
        )

        with rule_left:
            rule_plot = (
                rule_summary[
                    rule_summary[
                        "Failed_Records"
                    ]
                    > 0
                ]
                .head(15)
            )

            if rule_plot.empty:
                st.success(
                    "No validation rule currently contains "
                    "failed records."
                )

            else:
                fig = px.bar(
                    rule_plot,
                    x="Failed_Records",
                    y="rule_name",
                    orientation="h",
                    title="Highest-Failure Quality Rules",
                    text_auto=True,
                )

                fig.update_xaxes(
                    title="Failed Records"
                )

                fig.update_yaxes(
                    title=None,
                    autorange="reversed",
                )

                st.plotly_chart(
                    style_figure(
                        fig,
                        450,
                    ),
                    width="stretch",
                )

        with rule_right:
            dataframe(
                rule_summary,
                height=450,
            )


        # ====================================================
        # QUALITY STATUS
        # ====================================================

        section_header(
            "Quality Check Status",
            (
                "Operational status distribution reported by the "
                "data-quality framework."
            ),
        )

        dq_status_summary = (
            dq[
                "status_normalized"
            ]
            .value_counts()
            .rename_axis(
                "Status"
            )
            .reset_index(
                name="Checks"
            )
        )

        status_left, status_right = st.columns(
            [1, 1]
        )

        with status_left:
            fig = px.bar(
                dq_status_summary,
                x="Status",
                y="Checks",
                title="Quality Checks by Status",
                text_auto=True,
            )

            fig.update_xaxes(
                title=None
            )

            fig.update_yaxes(
                title="Checks"
            )

            st.plotly_chart(
                style_figure(
                    fig,
                    360,
                ),
                width="stretch",
            )

        with status_right:
            dataframe(
                dq_status_summary,
                height=360,
            )


        # ====================================================
        # QUALITY TREND
        # ====================================================

        section_header(
            "Quality Trend",
            (
                "Observe failed-record volume over time using recorded "
                "quality-check timestamps."
            ),
        )

        if (
            "checked_at"
            in dq.columns
            and dq[
                "checked_at"
            ].notna().any()
        ):
            dq_trend = (
                dq[
                    dq[
                        "checked_at"
                    ].notna()
                ]
                .copy()
            )

            dq_trend[
                "Quality Date"
            ] = (
                dq_trend[
                    "checked_at"
                ]
                .dt.date
            )

            dq_trend = (
                dq_trend.groupby(
                    "Quality Date",
                    as_index=False,
                )
                .agg(
                    Checks=(
                        "quality_log_id",
                        "count",
                    ),
                    Failed_Records=(
                        "failed_records",
                        "sum",
                    ),
                )
                .sort_values(
                    "Quality Date"
                )
            )

            fig = px.line(
                dq_trend,
                x="Quality Date",
                y="Failed_Records",
                markers=True,
                title="Failed Records Over Time",
            )

            fig.update_xaxes(
                title=None
            )

            fig.update_yaxes(
                title="Failed Records"
            )

            st.plotly_chart(
                style_figure(
                    fig,
                    390,
                ),
                width="stretch",
            )

            dataframe(
                dq_trend.sort_values(
                    "Quality Date",
                    ascending=False,
                ),
                height=320,
            )

        else:
            st.info(
                "Quality trend cannot be calculated because "
                "valid check timestamps are unavailable."
            )


        # ====================================================
        # REJECTED DATA CONTROL
        # ====================================================

        section_header(
            "Rejected Data Control",
            (
                "Detailed exception register for records rejected during "
                "the Hospital 360 data pipeline."
            ),
        )

        if rejected_records.empty:
            st.success(
                "No rejected records are currently present in "
                "the rejection register."
            )

        else:
            rejected = (
                rejected_records.copy()
            )

            if "rejected_at" in rejected.columns:
                rejected[
                    "rejected_at"
                ] = pd.to_datetime(
                    rejected[
                        "rejected_at"
                    ],
                    errors="coerce",
                )

            metric_row(
                [
                    (
                        "Rejected Entries",
                        format_integer(
                            len(rejected)
                        ),
                    ),
                    (
                        "Affected Batches",
                        format_integer(
                            rejected[
                                "batch_id"
                            ].nunique()
                        ),
                    ),
                    (
                        "Affected Datasets",
                        format_integer(
                            rejected[
                                "dataset_name"
                            ].nunique()
                        ),
                    ),
                    (
                        "Rejection Rules",
                        format_integer(
                            rejected[
                                "rule_name"
                            ].nunique()
                        ),
                    ),
                ]
            )

            rejection_by_dataset = (
                rejected[
                    "dataset_name"
                ]
                .fillna(
                    "Unknown"
                )
                .astype(str)
                .value_counts()
                .rename_axis(
                    "Dataset"
                )
                .reset_index(
                    name="Rejected Records"
                )
            )

            rejection_by_rule = (
                rejected[
                    "rule_name"
                ]
                .fillna(
                    "Unknown"
                )
                .astype(str)
                .value_counts()
                .rename_axis(
                    "Rule"
                )
                .reset_index(
                    name="Rejected Records"
                )
            )

            reject_left, reject_right = st.columns(
                2
            )

            with reject_left:
                fig = px.bar(
                    rejection_by_dataset.head(
                        15
                    ),
                    x="Rejected Records",
                    y="Dataset",
                    orientation="h",
                    title="Rejections by Dataset",
                    text_auto=True,
                )

                fig.update_xaxes(
                    title="Rejected Records"
                )

                fig.update_yaxes(
                    title=None,
                    autorange="reversed",
                )

                st.plotly_chart(
                    style_figure(
                        fig,
                        420,
                    ),
                    width="stretch",
                )

            with reject_right:
                fig = px.bar(
                    rejection_by_rule.head(
                        15
                    ),
                    x="Rejected Records",
                    y="Rule",
                    orientation="h",
                    title="Rejections by Rule",
                    text_auto=True,
                )

                fig.update_xaxes(
                    title="Rejected Records"
                )

                fig.update_yaxes(
                    title=None,
                    autorange="reversed",
                )

                st.plotly_chart(
                    style_figure(
                        fig,
                        420,
                    ),
                    width="stretch",
                )


            # ================================================
            # REJECTION REASON ANALYSIS
            # ================================================

            st.markdown(
                "### Rejection Reason Analysis"
            )

            rejection_reasons = (
                rejected[
                    "rejection_reason"
                ]
                .fillna(
                    "No reason recorded"
                )
                .astype(str)
                .value_counts()
                .rename_axis(
                    "Rejection Reason"
                )
                .reset_index(
                    name="Records"
                )
            )

            dataframe(
                rejection_reasons,
                height=360,
            )


            # ================================================
            # REJECTION REGISTER
            # ================================================

            st.markdown(
                "### Rejected Record Register"
            )

            rejection_display_columns = [
                column
                for column in [
                    "rejection_id",
                    "batch_id",
                    "dataset_name",
                    "record_identifier",
                    "rule_name",
                    "rejection_reason",
                    "rejected_at",
                ]
                if column
                in rejected.columns
            ]

            dataframe(
                rejected[
                    rejection_display_columns
                ],
                height=500,
            )


        # ====================================================
        # BATCH QUALITY INSPECTOR
        # ====================================================

        section_header(
            "Batch Quality Inspector",
            (
                "Select one ETL batch to inspect its validation checks "
                "and rejected-record evidence."
            ),
        )

        dq_batch_options = (
            dq[
                "batch_id"
            ]
            .dropna()
            .unique()
            .tolist()
        )

        try:
            dq_batch_options = sorted(
                dq_batch_options,
                reverse=True,
            )

        except TypeError:
            dq_batch_options = list(
                dq_batch_options
            )

        if not dq_batch_options:
            st.info(
                "No batch identifiers are available in the "
                "data-quality history."
            )

        else:
            selected_dq_batch = st.selectbox(
                "Select Quality Batch",
                options=dq_batch_options,
                key="control_tower_dq_batch_inspector",
            )

            batch_dq = (
                dq[
                    dq[
                        "batch_id"
                    ]
                    == selected_dq_batch
                ]
                .copy()
            )

            batch_checked = int(
                batch_dq[
                    "records_checked"
                ].sum()
            )

            batch_failed = int(
                batch_dq[
                    "failed_records"
                ].sum()
            )

            batch_failed_checks = int(
                (
                    batch_dq[
                        "failed_records"
                    ]
                    > 0
                ).sum()
            )

            batch_rejected_count = 0

            if not rejected_records.empty:
                batch_rejected_count = len(
                    rejected_records[
                        rejected_records[
                            "batch_id"
                        ]
                        == selected_dq_batch
                    ]
                )

            metric_row(
                [
                    (
                        "Batch",
                        str(
                            selected_dq_batch
                        ),
                    ),
                    (
                        "Checks",
                        format_integer(
                            len(batch_dq)
                        ),
                    ),
                    (
                        "Failed Checks",
                        format_integer(
                            batch_failed_checks
                        ),
                    ),
                    (
                        "Rejected Entries",
                        format_integer(
                            batch_rejected_count
                        ),
                    ),
                ]
            )

            metric_row(
                [
                    (
                        "Records Checked",
                        format_integer(
                            batch_checked
                        ),
                    ),
                    (
                        "Failed Records",
                        format_integer(
                            batch_failed
                        ),
                    ),
                    (
                        "Tables",
                        format_integer(
                            batch_dq[
                                "table_name"
                            ].nunique()
                        ),
                    ),
                    (
                        "Rules",
                        format_integer(
                            batch_dq[
                                "rule_name"
                            ].nunique()
                        ),
                    ),
                ]
            )

            batch_quality_columns = [
                column
                for column in [
                    "quality_log_id",
                    "table_name",
                    "rule_name",
                    "rule_type",
                    "records_checked",
                    "failed_records",
                    "severity",
                    "status",
                    "details",
                    "checked_at",
                ]
                if column
                in batch_dq.columns
            ]

            dataframe(
                batch_dq[
                    batch_quality_columns
                ],
                height=430,
            )

            if not rejected_records.empty:
                selected_rejections = (
                    rejected_records[
                        rejected_records[
                            "batch_id"
                        ]
                        == selected_dq_batch
                    ]
                    .copy()
                )

                st.markdown(
                    "#### Rejected Records for Selected Batch"
                )

                if selected_rejections.empty:
                    st.info(
                        "No rejected-record entries are linked "
                        "to this batch."
                    )

                else:
                    dataframe(
                        selected_rejections,
                        height=350,
                    )


        # ====================================================
        # QUALITY EXCEPTION REGISTER
        # ====================================================

        section_header(
            "Quality Exception Register",
            (
                "Filtered register of validation events for detailed "
                "administrative investigation."
            ),
        )

        quality_display_columns = [
            column
            for column in [
                "quality_log_id",
                "batch_id",
                "table_name",
                "rule_name",
                "rule_type",
                "records_checked",
                "failed_records",
                "severity",
                "status",
                "details",
                "checked_at",
            ]
            if column
            in filtered_dq.columns
        ]

        dataframe(
            filtered_dq[
                quality_display_columns
            ],
            height=560,
        )


        # ====================================================
        # QUALITY CONTROL FLOW
        # ====================================================

        section_header(
            "Data Quality Control Flow",
            (
                "Sequence used to interpret validation results and "
                "resolve data exceptions."
            ),
        )

        dq_flow = pd.DataFrame(
            [
                {
                    "Stage": "01",
                    "Control": "Validation Execution",
                    "Question": (
                        "Which quality rules were executed?"
                    ),
                    "Evidence": (
                        "Rule name, type and records checked"
                    ),
                },
                {
                    "Stage": "02",
                    "Control": "Failure Detection",
                    "Question": (
                        "Which rules identified failed records?"
                    ),
                    "Evidence": (
                        "Failed-record count and quality status"
                    ),
                },
                {
                    "Stage": "03",
                    "Control": "Severity Review",
                    "Question": (
                        "How important is each exception?"
                    ),
                    "Evidence": (
                        "Configured severity"
                    ),
                },
                {
                    "Stage": "04",
                    "Control": "Table Impact",
                    "Question": (
                        "Which datasets are affected?"
                    ),
                    "Evidence": (
                        "Table-level quality summary"
                    ),
                },
                {
                    "Stage": "05",
                    "Control": "Record Rejection",
                    "Question": (
                        "Which individual records were rejected?"
                    ),
                    "Evidence": (
                        "Rejected-record register"
                    ),
                },
                {
                    "Stage": "06",
                    "Control": "Investigation",
                    "Question": (
                        "Why did validation fail?"
                    ),
                    "Evidence": (
                        "Rule details and rejection reason"
                    ),
                },
                {
                    "Stage": "07",
                    "Control": "Reporting Readiness",
                    "Question": (
                        "Can downstream analytics be trusted?"
                    ),
                    "Evidence": (
                        "Quality status, severity and unresolved exceptions"
                    ),
                },
            ]
        )

        dataframe(
            dq_flow,
            height=360,
        )

    # ============================================================
# TAB 4 — DATABASE & WAREHOUSE
# ============================================================

with tabs[3]:
    section_header(
        "Database & Warehouse",
        (
            "Administrative view of PostgreSQL connectivity, warehouse "
            "record volumes, analytical objects and the governed data "
            "estate supporting Hospital 360."
        ),
    )

    # ========================================================
    # DATABASE STATUS
    # ========================================================

    st.markdown("### Database Status")

    metric_row(
        [
            (
                "PostgreSQL",
                (
                    "Online"
                    if database_online
                    else "Unavailable"
                ),
            ),
            (
                "Warehouse Records",
                format_integer(
                    warehouse_total
                ),
            ),
            (
                "Warehouse Objects",
                format_integer(
                    len(warehouse_counts)
                ),
            ),
            (
                "Analytics Objects",
                format_integer(
                    analytics_count
                ),
            ),
        ]
    )

    if database_online:
        management_insight(
            (
                "The Hospital 360 PostgreSQL platform is reachable. "
                "Warehouse and analytical objects discovered during the "
                "current session are available for administrative review."
            ),
            label="Database Assessment",
        )
    else:
        management_insight(
            (
                "The Hospital 360 PostgreSQL platform could not be "
                "confirmed as available during the current session. "
                "Warehouse and analytical information shown below may "
                "therefore be incomplete."
            ),
            label="Database Assessment",
        )


    # ========================================================
    # DATABASE ARCHITECTURE
    # ========================================================

    section_header(
        "Data Platform Architecture",
        (
            "Understand how operational source data moves through the "
            "Hospital 360 governed analytics platform."
        ),
    )

    architecture = pd.DataFrame(
        [
            {
                "Layer": "01",
                "Platform Area": "Source Systems",
                "Purpose": (
                    "Operational hospital data enters the platform "
                    "through configured source feeds."
                ),
                "Primary Users": "Operational Systems",
            },
            {
                "Layer": "02",
                "Platform Area": "ETL Control",
                "Purpose": (
                    "Pipeline batches load, validate and govern "
                    "incoming source records."
                ),
                "Primary Users": "Data Engineering",
            },
            {
                "Layer": "03",
                "Platform Area": "Warehouse",
                "Purpose": (
                    "Dimensional facts and dimensions provide governed "
                    "analytical data structures."
                ),
                "Primary Users": "Analytics Platform",
            },
            {
                "Layer": "04",
                "Platform Area": "Analytics",
                "Purpose": (
                    "Semantic views expose management-friendly metrics "
                    "and reporting structures."
                ),
                "Primary Users": "Dashboards and AI",
            },
            {
                "Layer": "05",
                "Platform Area": "Reporting",
                "Purpose": (
                    "Streamlit, Power BI, Tableau and MIS outputs "
                    "consume governed analytical information."
                ),
                "Primary Users": "Management",
            },
        ]
    )

    dataframe(
        architecture,
        height=300,
    )


    # ========================================================
    # WAREHOUSE INVENTORY
    # ========================================================

    section_header(
        "Warehouse Inventory",
        (
            "Record volume across the Hospital 360 dimensional "
            "warehouse."
        ),
    )

    if warehouse_counts.empty:
        st.warning(
            "Warehouse inventory is currently unavailable."
        )

    else:
        warehouse_inventory = warehouse_counts.copy()

        if "row_count" in warehouse_inventory.columns:
            warehouse_inventory[
                "row_count"
            ] = pd.to_numeric(
                warehouse_inventory[
                    "row_count"
                ],
                errors="coerce",
            ).fillna(0)

        if "entity" in warehouse_inventory.columns:
            warehouse_inventory[
                "entity"
            ] = (
                warehouse_inventory[
                    "entity"
                ]
                .fillna(
                    "Unknown"
                )
                .astype(str)
            )

        largest_warehouse_object = "N/A"
        largest_warehouse_rows = 0

        if (
            "entity" in warehouse_inventory.columns
            and "row_count" in warehouse_inventory.columns
            and not warehouse_inventory.empty
        ):
            largest_row = (
                warehouse_inventory.sort_values(
                    by=["row_count"],
                    ascending=[False],
                )
                .iloc[0]
            )

            largest_warehouse_object = str(
                largest_row[
                    "entity"
                ]
            )

            largest_warehouse_rows = int(
                safe_number(
                    largest_row[
                        "row_count"
                    ]
                )
            )

        metric_row(
            [
                (
                    "Warehouse Objects",
                    format_integer(
                        len(
                            warehouse_inventory
                        )
                    ),
                ),
                (
                    "Total Records",
                    format_integer(
                        warehouse_inventory[
                            "row_count"
                        ].sum()
                        if "row_count"
                        in warehouse_inventory.columns
                        else 0
                    ),
                ),
                (
                    "Largest Object",
                    largest_warehouse_object,
                ),
                (
                    "Largest Object Rows",
                    format_integer(
                        largest_warehouse_rows
                    ),
                ),
            ]
        )

        if (
            "entity" in warehouse_inventory.columns
            and "row_count" in warehouse_inventory.columns
        ):
            warehouse_chart_data = (
                warehouse_inventory.sort_values(
                    by=["row_count"],
                    ascending=[True],
                )
                .copy()
            )

            fig = px.bar(
                warehouse_chart_data,
                x="row_count",
                y="entity",
                orientation="h",
                title="Warehouse Record Volume",
                text_auto=True,
            )

            fig.update_xaxes(
                title="Records"
            )

            fig.update_yaxes(
                title=None
            )

            st.plotly_chart(
                style_figure(
                    fig,
                    500,
                ),
                width="stretch",
            )

        dataframe(
            warehouse_inventory,
            height=430,
        )


    # ========================================================
    # WAREHOUSE CONCENTRATION
    # ========================================================

    section_header(
        "Warehouse Volume Distribution",
        (
            "Identify which warehouse objects contain the largest "
            "share of analytical records."
        ),
    )

    if (
        not warehouse_counts.empty
        and "entity" in warehouse_counts.columns
        and "row_count" in warehouse_counts.columns
    ):
        warehouse_distribution = (
            warehouse_counts[
                [
                    "entity",
                    "row_count",
                ]
            ]
            .copy()
        )

        warehouse_distribution[
            "row_count"
        ] = pd.to_numeric(
            warehouse_distribution[
                "row_count"
            ],
            errors="coerce",
        ).fillna(0)

        warehouse_distribution = (
            warehouse_distribution.sort_values(
                by=["row_count"],
                ascending=[False],
            )
            .reset_index(
                drop=True
            )
        )

        warehouse_distribution[
            "Share_Pct"
        ] = (
            (
                warehouse_distribution[
                    "row_count"
                ]
                / warehouse_distribution[
                    "row_count"
                ].sum()
            )
            * 100
            if warehouse_distribution[
                "row_count"
            ].sum()
            else 0
        )

        warehouse_distribution[
            "Share_Pct"
        ] = pd.to_numeric(
            warehouse_distribution[
                "Share_Pct"
            ],
            errors="coerce",
        ).fillna(0).round(2)

        distribution_left, distribution_right = st.columns(
            [1.1, 1]
        )

        with distribution_left:
            fig = px.bar(
                warehouse_distribution.head(
                    15
                ),
                x="entity",
                y="Share_Pct",
                title="Warehouse Record Share",
                text_auto=True,
            )

            fig.update_xaxes(
                title=None
            )

            fig.update_yaxes(
                title="Share of Warehouse Records (%)"
            )

            st.plotly_chart(
                style_figure(
                    fig,
                    410,
                ),
                width="stretch",
            )

        with distribution_right:
            dataframe(
                warehouse_distribution,
                height=410,
            )

    else:
        st.info(
            "Warehouse volume distribution cannot be calculated "
            "from the currently available inventory."
        )


    # ========================================================
    # ANALYTICS SEMANTIC LAYER
    # ========================================================

    section_header(
        "Analytics Semantic Layer",
        (
            "Governed analytical objects exposed to dashboards, "
            "reporting tools and the Hospital 360 AI analyst."
        ),
    )

    if analytics_objects.empty:
        st.warning(
            "Analytics semantic-layer inventory is currently unavailable."
        )

    else:
        semantic_objects = (
            analytics_objects.copy()
        )

        metric_row(
            [
                (
                    "Semantic Objects",
                    format_integer(
                        len(
                            semantic_objects
                        )
                    ),
                ),
                (
                    "Schema",
                    "analytics",
                ),
                (
                    "Consumption",
                    "Read Only",
                ),
                (
                    "Primary Purpose",
                    "Reporting",
                ),
            ]
        )

        object_type_column = None

        for candidate in [
            "object_type",
            "type",
            "relation_type",
            "table_type",
        ]:
            if candidate in semantic_objects.columns:
                object_type_column = candidate
                break

        if object_type_column:
            semantic_type_summary = (
                semantic_objects[
                    object_type_column
                ]
                .fillna(
                    "Unknown"
                )
                .astype(str)
                .value_counts()
                .rename_axis(
                    "Object Type"
                )
                .reset_index(
                    name="Objects"
                )
            )

            semantic_left, semantic_right = st.columns(
                [1, 1.2]
            )

            with semantic_left:
                fig = px.bar(
                    semantic_type_summary,
                    x="Object Type",
                    y="Objects",
                    title="Semantic Objects by Type",
                    text_auto=True,
                )

                fig.update_xaxes(
                    title=None
                )

                fig.update_yaxes(
                    title="Objects"
                )

                st.plotly_chart(
                    style_figure(
                        fig,
                        370,
                    ),
                    width="stretch",
                )

            with semantic_right:
                dataframe(
                    semantic_type_summary,
                    height=370,
                )

        dataframe(
            semantic_objects,
            height=470,
        )


    # ========================================================
    # RELATION EXPLORER
    # ========================================================

    section_header(
        "Data Object Explorer",
        (
            "Search the discovered warehouse and analytics estate "
            "without exposing unrestricted database access."
        ),
    )

    warehouse_relation_frame = pd.DataFrame()

    if not warehouse_counts.empty:
        warehouse_relation_frame = (
            warehouse_counts.copy()
        )

        warehouse_relation_frame[
            "Platform Layer"
        ] = "Warehouse"

        if "entity" in warehouse_relation_frame.columns:
            warehouse_relation_frame = (
                warehouse_relation_frame.rename(
                    columns={
                        "entity":
                            "Object"
                    }
                )
            )

    analytics_relation_frame = pd.DataFrame()

    if not analytics_objects.empty:
        analytics_relation_frame = (
            analytics_objects.copy()
        )

        analytics_relation_frame[
            "Platform Layer"
        ] = "Analytics"

        analytics_name_column = None

        for candidate in [
            "object_name",
            "relation_name",
            "table_name",
            "view_name",
            "name",
        ]:
            if candidate in analytics_relation_frame.columns:
                analytics_name_column = candidate
                break

        if analytics_name_column:
            analytics_relation_frame = (
                analytics_relation_frame.rename(
                    columns={
                        analytics_name_column:
                            "Object"
                    }
                )
            )

    relation_frames = []

    if (
        not warehouse_relation_frame.empty
        and "Object"
        in warehouse_relation_frame.columns
    ):
        relation_frames.append(
            warehouse_relation_frame
        )

    if (
        not analytics_relation_frame.empty
        and "Object"
        in analytics_relation_frame.columns
    ):
        relation_frames.append(
            analytics_relation_frame
        )

    if relation_frames:
        relation_inventory = pd.concat(
            relation_frames,
            ignore_index=True,
            sort=False,
        )

        relation_inventory[
            "Object"
        ] = (
            relation_inventory[
                "Object"
            ]
            .fillna(
                "Unknown"
            )
            .astype(str)
        )

        relation_search = st.text_input(
            "Search Data Object",
            placeholder=(
                "Example: admission, patient, department, revenue, claim"
            ),
            key="control_tower_relation_search",
        )

        relation_layer_options = sorted(
            relation_inventory[
                "Platform Layer"
            ]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        selected_relation_layers = st.multiselect(
            "Platform Layer",
            options=relation_layer_options,
            default=relation_layer_options,
            key="control_tower_relation_layer",
        )

        filtered_relations = (
            relation_inventory.copy()
        )

        if selected_relation_layers:
            filtered_relations = (
                filtered_relations[
                    filtered_relations[
                        "Platform Layer"
                    ]
                    .isin(
                        selected_relation_layers
                    )
                ]
            )

        if relation_search.strip():
            filtered_relations = (
                filtered_relations[
                    filtered_relations[
                        "Object"
                    ]
                    .str.contains(
                        relation_search.strip(),
                        case=False,
                        na=False,
                    )
                ]
            )

        metric_row(
            [
                (
                    "Matching Objects",
                    format_integer(
                        len(
                            filtered_relations
                        )
                    ),
                ),
                (
                    "Warehouse Matches",
                    format_integer(
                        (
                            filtered_relations[
                                "Platform Layer"
                            ]
                            == "Warehouse"
                        ).sum()
                    ),
                ),
                (
                    "Analytics Matches",
                    format_integer(
                        (
                            filtered_relations[
                                "Platform Layer"
                            ]
                            == "Analytics"
                        ).sum()
                    ),
                ),
                (
                    "Access Mode",
                    "Governed",
                ),
            ]
        )

        dataframe(
            filtered_relations,
            height=500,
        )

    else:
        st.info(
            "No warehouse or analytics objects are available "
            "for the relation explorer."
        )


    # ========================================================
    # DATABASE READINESS
    # ========================================================

    section_header(
        "Reporting Readiness",
        (
            "Administrative checks showing whether the governed "
            "data platform has the core components required for "
            "Hospital 360 reporting."
        ),
    )

    readiness_rows = []

    readiness_rows.append(
        {
            "Component": "PostgreSQL Connectivity",
            "Status": (
                "READY"
                if database_online
                else "NOT READY"
            ),
            "Evidence": (
                "Database connection available"
                if database_online
                else "Database connection unavailable"
            ),
        }
    )

    readiness_rows.append(
        {
            "Component": "Warehouse",
            "Status": (
                "READY"
                if warehouse_total > 0
                else "CHECK"
            ),
            "Evidence": (
                f"{warehouse_total:,} warehouse records discovered"
            ),
        }
    )

    readiness_rows.append(
        {
            "Component": "Analytics Semantic Layer",
            "Status": (
                "READY"
                if analytics_count > 0
                else "CHECK"
            ),
            "Evidence": (
                f"{analytics_count:,} analytical objects discovered"
            ),
        }
    )

    readiness_rows.append(
        {
            "Component": "ETL History",
            "Status": (
                "READY"
                if not etl_batches.empty
                else "CHECK"
            ),
            "Evidence": (
                f"{len(etl_batches):,} ETL executions available"
            ),
        }
    )

    readiness_rows.append(
        {
            "Component": "Data Quality",
            "Status": (
                "READY"
                if not quality_log.empty
                else "CHECK"
            ),
            "Evidence": (
                f"{len(quality_log):,} quality checks available"
            ),
        }
    )

    readiness_rows.append(
        {
            "Component": "Reporting Assets",
            "Status": (
                "READY"
                if not artifacts.empty
                else "CHECK"
            ),
            "Evidence": (
                f"{len(artifacts):,} reporting artifacts discovered"
            ),
        }
    )

    readiness = pd.DataFrame(
        readiness_rows
    )

    ready_count = int(
        (
            readiness[
                "Status"
            ]
            == "READY"
        ).sum()
    )

    readiness_pct = (
        (
            ready_count
            / len(readiness)
        )
        * 100
        if len(readiness)
        else 0
    )

    metric_row(
        [
            (
                "Readiness Checks",
                format_integer(
                    len(readiness)
                ),
            ),
            (
                "Ready",
                format_integer(
                    ready_count
                ),
            ),
            (
                "Needs Review",
                format_integer(
                    len(readiness)
                    - ready_count
                ),
            ),
            (
                "Readiness",
                f"{readiness_pct:,.1f}%",
            ),
        ]
    )

    dataframe(
        readiness,
        height=330,
    )


    # ========================================================
    # ADMINISTRATIVE DIAGNOSTICS
    # ========================================================

    section_header(
        "Database Diagnostics",
        (
            "Administrative loading exceptions affecting the database, "
            "warehouse or semantic-layer view."
        ),
    )

    database_error_keys = [
        key
        for key in load_errors.keys()
        if any(
            token in str(
                key
            ).lower()
            for token in [
                "database",
                "warehouse",
                "analytics",
                "schema",
                "postgres",
            ]
        )
    ]

    if not database_error_keys:
        st.success(
            "No database or warehouse loading exceptions are "
            "currently registered by the Control Tower."
        )

    else:
        database_diagnostics = pd.DataFrame(
            [
                {
                    "Component": key,
                    "Status": "Unavailable",
                    "Details": load_errors[
                        key
                    ],
                }
                for key in database_error_keys
            ]
        )

        dataframe(
            database_diagnostics,
            height=340,
        )


    # ========================================================
    # DATABASE GOVERNANCE
    # ========================================================

    section_header(
        "Database Governance",
        (
            "Control principles used by Hospital 360 to separate "
            "operational storage from governed analytical consumption."
        ),
    )

    governance = pd.DataFrame(
        [
            {
                "Control Area": "Warehouse Access",
                "Approach": "Governed",
                "Purpose": (
                    "Analytical workloads use approved warehouse "
                    "facts and dimensions."
                ),
            },
            {
                "Control Area": "Semantic Layer",
                "Approach": "Preferred",
                "Purpose": (
                    "Management reporting should prefer analytics "
                    "views when the required metric already exists."
                ),
            },
            {
                "Control Area": "AI Analytics",
                "Approach": "Read Only",
                "Purpose": (
                    "AI-generated database requests are restricted "
                    "to approved SELECT/WITH analytical queries."
                ),
            },
            {
                "Control Area": "Administrative Changes",
                "Approach": "Restricted",
                "Purpose": (
                    "Dashboard analytics must not directly modify "
                    "warehouse or analytical data."
                ),
            },
            {
                "Control Area": "System Schemas",
                "Approach": "Blocked for AI",
                "Purpose": (
                    "System catalog and unrestricted metadata access "
                    "are excluded from the AI analytical path."
                ),
            },
            {
                "Control Area": "Reporting Distribution",
                "Approach": "Centralized",
                "Purpose": (
                    "Downloadable reporting assets are distributed "
                    "through the administrative Control Tower."
                ),
            },
        ]
    )

    dataframe(
        governance,
        height=370,
    )


    # ========================================================
    # DATABASE FLOW
    # ========================================================

    section_header(
        "Database & Analytics Flow",
        (
            "End-to-end sequence explaining how Hospital 360 data "
            "becomes management information."
        ),
    )

    database_flow = pd.DataFrame(
        [
            {
                "Step": "01",
                "Stage": "Operational Data",
                "Description": (
                    "Hospital source systems produce operational records."
                ),
                "Output": "Source Data",
            },
            {
                "Step": "02",
                "Stage": "ETL Processing",
                "Description": (
                    "Data pipelines ingest and transform source records."
                ),
                "Output": "Processed Records",
            },
            {
                "Step": "03",
                "Stage": "Data Quality",
                "Description": (
                    "Validation rules identify failed and rejected records."
                ),
                "Output": "Validated Data",
            },
            {
                "Step": "04",
                "Stage": "Warehouse",
                "Description": (
                    "Validated information is organized into analytical "
                    "facts and dimensions."
                ),
                "Output": "Governed Warehouse",
            },
            {
                "Step": "05",
                "Stage": "Semantic Layer",
                "Description": (
                    "Analytics views expose business-friendly measures "
                    "and dimensions."
                ),
                "Output": "Analytics Views",
            },
            {
                "Step": "06",
                "Stage": "Consumption",
                "Description": (
                    "Streamlit, Power BI, Tableau, MIS and AI consume "
                    "governed analytical information."
                ),
                "Output": "Management Insight",
            },
        ]
    )

    dataframe(
        database_flow,
        height=350,
    )

    # ============================================================
# TAB 5 — AUDIT & GOVERNANCE
# ============================================================

with tabs[4]:
    section_header(
        "Audit & Governance",
        (
            "Administrative oversight of platform activity, audit events, "
            "user actions and governance controls across Hospital 360."
        ),
    )

    if audit_log.empty:
        st.warning(
            "Audit history is currently unavailable. "
            "Administrative activity monitoring cannot be displayed."
        )

    else:
        audit = audit_log.copy()

        timestamp_column = None

        for candidate in [
            "event_time",
            "event_timestamp",
            "created_at",
            "logged_at",
            "action_time",
            "timestamp",
            "audit_time",
        ]:
            if candidate in audit.columns:
                timestamp_column = candidate
                break

        if timestamp_column:
            audit[timestamp_column] = pd.to_datetime(
                audit[timestamp_column],
                errors="coerce",
            )

        user_column = None

        for candidate in [
            "username",
            "user_name",
            "user_id",
            "actor",
            "performed_by",
            "created_by",
        ]:
            if candidate in audit.columns:
                user_column = candidate
                break

        action_column = None

        for candidate in [
            "action",
            "action_name",
            "event_type",
            "activity",
            "operation",
        ]:
            if candidate in audit.columns:
                action_column = candidate
                break

        entity_column = None

        for candidate in [
            "entity_name",
            "object_name",
            "resource_name",
            "table_name",
            "module_name",
            "entity_type",
        ]:
            if candidate in audit.columns:
                entity_column = candidate
                break

        status_column = None

        for candidate in [
            "status",
            "result",
            "outcome",
            "event_status",
        ]:
            if candidate in audit.columns:
                status_column = candidate
                break

        category_column = None

        for candidate in [
            "category",
            "event_category",
            "action_category",
            "module",
        ]:
            if candidate in audit.columns:
                category_column = candidate
                break

        total_audit_events = len(audit)

        unique_users = (
            audit[user_column]
            .dropna()
            .astype(str)
            .nunique()
            if user_column
            else 0
        )

        unique_actions = (
            audit[action_column]
            .dropna()
            .astype(str)
            .nunique()
            if action_column
            else 0
        )

        unique_entities = (
            audit[entity_column]
            .dropna()
            .astype(str)
            .nunique()
            if entity_column
            else 0
        )


        # ====================================================
        # GOVERNANCE SCORECARD
        # ====================================================

        st.markdown("### Governance Scorecard")

        metric_row(
            [
                (
                    "Audit Events",
                    format_integer(
                        total_audit_events
                    ),
                ),
                (
                    "Recorded Users",
                    format_integer(
                        unique_users
                    ),
                ),
                (
                    "Action Types",
                    format_integer(
                        unique_actions
                    ),
                ),
                (
                    "Affected Objects",
                    format_integer(
                        unique_entities
                    ),
                ),
            ]
        )

        latest_audit_time = "N/A"

        if (
            timestamp_column
            and audit[
                timestamp_column
            ].notna().any()
        ):
            latest_timestamp = (
                audit[
                    timestamp_column
                ]
                .max()
            )

            latest_audit_time = (
                latest_timestamp.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )

        failed_audit_events = 0

        if status_column:
            normalized_audit_status = (
                audit[
                    status_column
                ]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.upper()
            )

            failed_audit_events = int(
                normalized_audit_status.isin(
                    [
                        "FAILED",
                        "FAILURE",
                        "ERROR",
                        "DENIED",
                        "REJECTED",
                        "BLOCKED",
                    ]
                ).sum()
            )

        metric_row(
            [
                (
                    "Latest Audit Event",
                    latest_audit_time,
                ),
                (
                    "Failed / Denied Events",
                    format_integer(
                        failed_audit_events
                    ),
                ),
                (
                    "Audit Register",
                    "Available",
                ),
                (
                    "Governance Mode",
                    "Centralized",
                ),
            ]
        )


        # ====================================================
        # GOVERNANCE ASSESSMENT
        # ====================================================

        if failed_audit_events > 0:
            management_insight(
                (
                    f"{failed_audit_events:,} audit event(s) are recorded "
                    "with failed, denied, rejected, blocked or error outcomes. "
                    "Review the event register and associated users or "
                    "platform objects before closing the administrative review."
                ),
                label="Governance Assessment",
            )

        else:
            management_insight(
                (
                    "No failed, denied, rejected, blocked or error outcomes "
                    "were identified from the available audit status field. "
                    "Continue reviewing the audit trail as part of normal "
                    "platform governance."
                ),
                label="Governance Assessment",
            )


        # ====================================================
        # AUDIT FILTERS
        # ====================================================

        section_header(
            "Audit Explorer",
            (
                "Filter the administrative activity register to investigate "
                "specific users, actions, objects and outcomes."
            ),
        )

        filter_one, filter_two = st.columns(2)
        filter_three, filter_four = st.columns(2)

        user_options = (
            sorted(
                audit[
                    user_column
                ]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
            if user_column
            else []
        )

        action_options = (
            sorted(
                audit[
                    action_column
                ]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
            if action_column
            else []
        )

        entity_options = (
            sorted(
                audit[
                    entity_column
                ]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
            if entity_column
            else []
        )

        status_options = (
            sorted(
                audit[
                    status_column
                ]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
            if status_column
            else []
        )

        with filter_one:
            selected_audit_users = st.multiselect(
                "User",
                options=user_options,
                default=[],
                key="control_tower_audit_users",
            )

        with filter_two:
            selected_audit_actions = st.multiselect(
                "Action",
                options=action_options,
                default=[],
                key="control_tower_audit_actions",
            )

        with filter_three:
            selected_audit_entities = st.multiselect(
                "Platform Object",
                options=entity_options,
                default=[],
                key="control_tower_audit_entities",
            )

        with filter_four:
            selected_audit_statuses = st.multiselect(
                "Outcome",
                options=status_options,
                default=[],
                key="control_tower_audit_status",
            )

        audit_search = st.text_input(
            "Search Audit Register",
            placeholder=(
                "Search across available audit fields"
            ),
            key="control_tower_audit_search",
        )

        filtered_audit = audit.copy()

        if (
            selected_audit_users
            and user_column
        ):
            filtered_audit = (
                filtered_audit[
                    filtered_audit[
                        user_column
                    ]
                    .astype(str)
                    .isin(
                        selected_audit_users
                    )
                ]
            )

        if (
            selected_audit_actions
            and action_column
        ):
            filtered_audit = (
                filtered_audit[
                    filtered_audit[
                        action_column
                    ]
                    .astype(str)
                    .isin(
                        selected_audit_actions
                    )
                ]
            )

        if (
            selected_audit_entities
            and entity_column
        ):
            filtered_audit = (
                filtered_audit[
                    filtered_audit[
                        entity_column
                    ]
                    .astype(str)
                    .isin(
                        selected_audit_entities
                    )
                ]
            )

        if (
            selected_audit_statuses
            and status_column
        ):
            filtered_audit = (
                filtered_audit[
                    filtered_audit[
                        status_column
                    ]
                    .astype(str)
                    .isin(
                        selected_audit_statuses
                    )
                ]
            )

        if audit_search.strip():
            search_text = (
                audit_search
                .strip()
                .lower()
            )

            search_mask = pd.Series(
                False,
                index=filtered_audit.index,
            )

            for column in filtered_audit.columns:
                search_mask = (
                    search_mask
                    | filtered_audit[
                        column
                    ]
                    .fillna("")
                    .astype(str)
                    .str.lower()
                    .str.contains(
                        search_text,
                        regex=False,
                    )
                )

            filtered_audit = (
                filtered_audit[
                    search_mask
                ]
            )

        metric_row(
            [
                (
                    "Matching Events",
                    format_integer(
                        len(
                            filtered_audit
                        )
                    ),
                ),
                (
                    "Total Events",
                    format_integer(
                        total_audit_events
                    ),
                ),
                (
                    "Filters",
                    "Active"
                    if (
                        selected_audit_users
                        or selected_audit_actions
                        or selected_audit_entities
                        or selected_audit_statuses
                        or audit_search.strip()
                    )
                    else "None",
                ),
                (
                    "Register",
                    "Read Only",
                ),
            ]
        )


        # ====================================================
        # ACTION ANALYSIS
        # ====================================================

        section_header(
            "Administrative Activity",
            (
                "Understand which administrative actions occur most "
                "frequently across the platform."
            ),
        )

        if action_column:
            action_summary = (
                audit[
                    action_column
                ]
                .fillna(
                    "Unknown"
                )
                .astype(str)
                .value_counts()
                .rename_axis(
                    "Action"
                )
                .reset_index(
                    name="Events"
                )
            )

            action_chart, action_table = st.columns(
                [1.1, 1]
            )

            with action_chart:
                fig = px.bar(
                    action_summary.head(
                        20
                    ),
                    x="Events",
                    y="Action",
                    orientation="h",
                    title="Most Frequent Administrative Actions",
                    text_auto=True,
                )

                fig.update_xaxes(
                    title="Audit Events"
                )

                fig.update_yaxes(
                    title=None,
                    autorange="reversed",
                )

                st.plotly_chart(
                    style_figure(
                        fig,
                        430,
                    ),
                    width="stretch",
                )

            with action_table:
                dataframe(
                    action_summary,
                    height=430,
                )

        else:
            st.info(
                "An action field was not discovered in the "
                "available audit register."
            )


        # ====================================================
        # USER ACTIVITY
        # ====================================================

        section_header(
            "User Activity",
            (
                "Review administrative activity volume by recorded "
                "platform user or actor."
            ),
        )

        if user_column:
            user_summary = (
                audit[
                    user_column
                ]
                .fillna(
                    "Unknown"
                )
                .astype(str)
                .value_counts()
                .rename_axis(
                    "User"
                )
                .reset_index(
                    name="Events"
                )
            )

            user_left, user_right = st.columns(
                [1.1, 1]
            )

            with user_left:
                fig = px.bar(
                    user_summary.head(
                        20
                    ),
                    x="Events",
                    y="User",
                    orientation="h",
                    title="Administrative Events by User",
                    text_auto=True,
                )

                fig.update_xaxes(
                    title="Audit Events"
                )

                fig.update_yaxes(
                    title=None,
                    autorange="reversed",
                )

                st.plotly_chart(
                    style_figure(
                        fig,
                        420,
                    ),
                    width="stretch",
                )

            with user_right:
                dataframe(
                    user_summary,
                    height=420,
                )

        else:
            st.info(
                "A user or actor field was not discovered in the "
                "available audit register."
            )


        # ====================================================
        # OBJECT ACTIVITY
        # ====================================================

        section_header(
            "Platform Object Activity",
            (
                "Identify which platform objects appear most frequently "
                "in administrative audit events."
            ),
        )

        if entity_column:
            entity_summary = (
                audit[
                    entity_column
                ]
                .fillna(
                    "Unknown"
                )
                .astype(str)
                .value_counts()
                .rename_axis(
                    "Platform Object"
                )
                .reset_index(
                    name="Events"
                )
            )

            entity_left, entity_right = st.columns(
                [1.1, 1]
            )

            with entity_left:
                fig = px.bar(
                    entity_summary.head(
                        20
                    ),
                    x="Events",
                    y="Platform Object",
                    orientation="h",
                    title="Audit Events by Platform Object",
                    text_auto=True,
                )

                fig.update_xaxes(
                    title="Audit Events"
                )

                fig.update_yaxes(
                    title=None,
                    autorange="reversed",
                )

                st.plotly_chart(
                    style_figure(
                        fig,
                        420,
                    ),
                    width="stretch",
                )

            with entity_right:
                dataframe(
                    entity_summary,
                    height=420,
                )

        else:
            st.info(
                "No platform-object field was discovered in the "
                "available audit register."
            )


        # ====================================================
        # OUTCOME ANALYSIS
        # ====================================================

        section_header(
            "Audit Outcomes",
            (
                "Review successful, failed, denied and other recorded "
                "administrative outcomes."
            ),
        )

        if status_column:
            outcome_summary = (
                audit[
                    status_column
                ]
                .fillna(
                    "Unknown"
                )
                .astype(str)
                .value_counts()
                .rename_axis(
                    "Outcome"
                )
                .reset_index(
                    name="Events"
                )
            )

            outcome_left, outcome_right = st.columns(
                [1, 1]
            )

            with outcome_left:
                fig = px.bar(
                    outcome_summary,
                    x="Outcome",
                    y="Events",
                    title="Administrative Outcomes",
                    text_auto=True,
                )

                fig.update_xaxes(
                    title=None
                )

                fig.update_yaxes(
                    title="Audit Events"
                )

                st.plotly_chart(
                    style_figure(
                        fig,
                        360,
                    ),
                    width="stretch",
                )

            with outcome_right:
                dataframe(
                    outcome_summary,
                    height=360,
                )

        else:
            st.info(
                "No outcome/status field was discovered in the "
                "available audit register."
            )


        # ====================================================
        # CATEGORY ANALYSIS
        # ====================================================

        section_header(
            "Governance Categories",
            (
                "Group audit activity by category or module when "
                "that information is available."
            ),
        )

        if category_column:
            category_summary = (
                audit[
                    category_column
                ]
                .fillna(
                    "Unknown"
                )
                .astype(str)
                .value_counts()
                .rename_axis(
                    "Category"
                )
                .reset_index(
                    name="Events"
                )
            )

            category_left, category_right = st.columns(
                [1, 1]
            )

            with category_left:
                fig = px.bar(
                    category_summary,
                    x="Category",
                    y="Events",
                    title="Audit Events by Category",
                    text_auto=True,
                )

                fig.update_xaxes(
                    title=None
                )

                fig.update_yaxes(
                    title="Audit Events"
                )

                st.plotly_chart(
                    style_figure(
                        fig,
                        370,
                    ),
                    width="stretch",
                )

            with category_right:
                dataframe(
                    category_summary,
                    height=370,
                )

        else:
            st.info(
                "No audit category or module field was discovered."
            )


        # ====================================================
        # AUDIT TREND
        # ====================================================

        section_header(
            "Audit Activity Trend",
            (
                "Track administrative activity over time when audit "
                "timestamps are available."
            ),
        )

        if (
            timestamp_column
            and audit[
                timestamp_column
            ].notna().any()
        ):
            audit_trend = (
                audit[
                    audit[
                        timestamp_column
                    ].notna()
                ]
                .copy()
            )

            audit_trend[
                "Audit Date"
            ] = (
                audit_trend[
                    timestamp_column
                ]
                .dt.date
            )

            audit_trend = (
                audit_trend.groupby(
                    "Audit Date",
                    as_index=False,
                )
                .size()
                .rename(
                    columns={
                        "size":
                            "Events"
                    }
                )
                .sort_values(
                    by=["Audit Date"],
                    ascending=[True],
                )
            )

            fig = px.line(
                audit_trend,
                x="Audit Date",
                y="Events",
                markers=True,
                title="Administrative Activity Over Time",
            )

            fig.update_xaxes(
                title=None
            )

            fig.update_yaxes(
                title="Audit Events"
            )

            st.plotly_chart(
                style_figure(
                    fig,
                    390,
                ),
                width="stretch",
            )

            dataframe(
                audit_trend.sort_values(
                    by=["Audit Date"],
                    ascending=[False],
                ),
                height=320,
            )

        else:
            st.info(
                "Audit activity trend cannot be calculated because "
                "a usable event timestamp was not discovered."
            )


        # ====================================================
        # GOVERNANCE CONTROL MATRIX
        # ====================================================

        section_header(
            "Governance Control Matrix",
            (
                "Administrative controls defining how Hospital 360 "
                "protects analytical operations and reporting."
            ),
        )

        governance_controls = pd.DataFrame(
            [
                {
                    "Control": "Database Analytics",
                    "Mode": "Read Only",
                    "Administrative Purpose": (
                        "Analytical consumption must not modify "
                        "warehouse data."
                    ),
                },
                {
                    "Control": "AI SQL Safety",
                    "Mode": "Restricted",
                    "Administrative Purpose": (
                        "Generated SQL is validated before database "
                        "execution."
                    ),
                },
                {
                    "Control": "Allowed Schemas",
                    "Mode": "Governed",
                    "Administrative Purpose": (
                        "AI analytical access is limited to approved "
                        "analytics and warehouse schemas."
                    ),
                },
                {
                    "Control": "System Metadata",
                    "Mode": "Blocked",
                    "Administrative Purpose": (
                        "System catalog access is excluded from the "
                        "AI analytical path."
                    ),
                },
                {
                    "Control": "ETL Monitoring",
                    "Mode": "Centralized",
                    "Administrative Purpose": (
                        "Pipeline execution history is reviewed from "
                        "the Control Tower."
                    ),
                },
                {
                    "Control": "Data Quality",
                    "Mode": "Monitored",
                    "Administrative Purpose": (
                        "Validation failures and rejected records are "
                        "centrally visible."
                    ),
                },
                {
                    "Control": "Audit Trail",
                    "Mode": "Recorded",
                    "Administrative Purpose": (
                        "Administrative activity is retained for "
                        "governance review."
                    ),
                },
                {
                    "Control": "Reporting Downloads",
                    "Mode": "Admin Controlled",
                    "Administrative Purpose": (
                        "Downloadable BI and MIS assets are distributed "
                        "through the Admin Control Tower."
                    ),
                },
                {
                    "Control": "Visualization Pages",
                    "Mode": "Presentation",
                    "Administrative Purpose": (
                        "Business pages focus on analysis and visual "
                        "interpretation rather than platform control."
                    ),
                },
            ]
        )

        dataframe(
            governance_controls,
            height=450,
        )


        # ====================================================
        # EVENT INSPECTOR
        # ====================================================

        section_header(
            "Audit Event Inspector",
            (
                "Inspect one administrative event without exposing "
                "editable platform controls."
            ),
        )

        if filtered_audit.empty:
            st.info(
                "No audit events match the current filters."
            )

        else:
            audit_id_column = None

            for candidate in [
                "audit_id",
                "audit_log_id",
                "event_id",
                "log_id",
                "id",
            ]:
                if candidate in filtered_audit.columns:
                    audit_id_column = candidate
                    break

            if audit_id_column:
                inspector_options = (
                    filtered_audit[
                        audit_id_column
                    ]
                    .dropna()
                    .tolist()
                )

                selected_audit_event = st.selectbox(
                    "Select Audit Event",
                    options=inspector_options,
                    key="control_tower_audit_event_inspector",
                )

                selected_event = (
                    filtered_audit[
                        filtered_audit[
                            audit_id_column
                        ]
                        == selected_audit_event
                    ]
                    .head(1)
                )

            else:
                inspector_options = (
                    filtered_audit.index
                    .tolist()
                )

                selected_audit_event = st.selectbox(
                    "Select Audit Event",
                    options=inspector_options,
                    format_func=lambda value: (
                        f"Audit Row {value}"
                    ),
                    key="control_tower_audit_event_inspector_index",
                )

                selected_event = (
                    filtered_audit.loc[
                        [
                            selected_audit_event
                        ]
                    ]
                )

            if not selected_event.empty:
                event_row = (
                    selected_event.iloc[0]
                )

                metric_row(
                    [
                        (
                            "User",
                            (
                                str(
                                    event_row.get(
                                        user_column,
                                        "N/A",
                                    )
                                )
                                if user_column
                                else "N/A"
                            ),
                        ),
                        (
                            "Action",
                            (
                                str(
                                    event_row.get(
                                        action_column,
                                        "N/A",
                                    )
                                )
                                if action_column
                                else "N/A"
                            ),
                        ),
                        (
                            "Object",
                            (
                                str(
                                    event_row.get(
                                        entity_column,
                                        "N/A",
                                    )
                                )
                                if entity_column
                                else "N/A"
                            ),
                        ),
                        (
                            "Outcome",
                            (
                                str(
                                    event_row.get(
                                        status_column,
                                        "N/A",
                                    )
                                )
                                if status_column
                                else "N/A"
                            ),
                        ),
                    ]
                )

                event_details = pd.DataFrame(
                    [
                        {
                            "Field": column,
                            "Value": (
                                ""
                                if pd.isna(
                                    event_row.get(
                                        column
                                    )
                                )
                                else str(
                                    event_row.get(
                                        column
                                    )
                                )
                            ),
                        }
                        for column in audit.columns
                    ]
                )

                dataframe(
                    event_details,
                    height=450,
                )


        # ====================================================
        # COMPLETE AUDIT REGISTER
        # ====================================================

        section_header(
            "Complete Audit Register",
            (
                "Read-only administrative event register after applying "
                "the selected governance filters."
            ),
        )

        audit_display = (
            filtered_audit.copy()
        )

        if timestamp_column:
            audit_display = (
                audit_display.sort_values(
                    by=[timestamp_column],
                    ascending=[False],
                    na_position="last",
                )
            )

        dataframe(
            audit_display,
            height=600,
        )


    # ========================================================
    # GOVERNANCE MODEL
    # ========================================================

    section_header(
        "Hospital 360 Governance Model",
        (
            "Clear separation of responsibilities across the "
            "analytics platform."
        ),
    )

    governance_model = pd.DataFrame(
        [
            {
                "Layer": "01",
                "Responsibility": "Business Pages",
                "Purpose": (
                    "Present KPIs, charts, trends and management "
                    "interpretation."
                ),
                "Control Level": "View",
            },
            {
                "Layer": "02",
                "Responsibility": "AI Analyst",
                "Purpose": (
                    "Answer governed analytical questions using "
                    "read-only database access."
                ),
                "Control Level": "Restricted",
            },
            {
                "Layer": "03",
                "Responsibility": "ETL Control",
                "Purpose": (
                    "Monitor source ingestion, processing and "
                    "pipeline execution."
                ),
                "Control Level": "Operational",
            },
            {
                "Layer": "04",
                "Responsibility": "Data Quality",
                "Purpose": (
                    "Monitor validation rules, failed records and "
                    "rejections."
                ),
                "Control Level": "Governed",
            },
            {
                "Layer": "05",
                "Responsibility": "Admin Control Tower",
                "Purpose": (
                    "Centralize administrative monitoring, downloads "
                    "and safe platform controls."
                ),
                "Control Level": "Administrative",
            },
        ]
    )

    dataframe(
        governance_model,
        height=330,
    )


    # ========================================================
    # AUDIT & GOVERNANCE FLOW
    # ========================================================

    section_header(
        "Audit & Governance Flow",
        (
            "Sequence administrators can follow when reviewing "
            "Hospital 360 platform activity."
        ),
    )

    audit_flow = pd.DataFrame(
        [
            {
                "Step": "01",
                "Stage": "Activity Occurs",
                "Question": (
                    "What action occurred on the platform?"
                ),
                "Evidence": "Audit Event",
            },
            {
                "Step": "02",
                "Stage": "Actor Review",
                "Question": (
                    "Who or what initiated the activity?"
                ),
                "Evidence": "User / Actor",
            },
            {
                "Step": "03",
                "Stage": "Object Review",
                "Question": (
                    "Which platform object was affected?"
                ),
                "Evidence": "Object / Resource",
            },
            {
                "Step": "04",
                "Stage": "Outcome Review",
                "Question": (
                    "Did the action complete successfully?"
                ),
                "Evidence": "Status / Outcome",
            },
            {
                "Step": "05",
                "Stage": "Exception Review",
                "Question": (
                    "Was the activity failed, blocked or denied?"
                ),
                "Evidence": "Audit Exception",
            },
            {
                "Step": "06",
                "Stage": "Governance Review",
                "Question": (
                    "Was the activity consistent with platform controls?"
                ),
                "Evidence": "Governance Matrix",
            },
            {
                "Step": "07",
                "Stage": "Administrative Record",
                "Question": (
                    "Can the event be traced later?"
                ),
                "Evidence": "Complete Audit Register",
            },
        ]
    )

    dataframe(
        audit_flow,
        height=360,
    )

    # ============================================================
# TAB 6 — DOWNLOAD CENTER
# ============================================================

with tabs[5]:
    section_header(
        "Enterprise Download Center",
        (
            "Central administrative distribution point for Hospital 360 "
            "Power BI, Tableau, MIS and other approved reporting assets."
        ),
    )

    management_insight(
        (
            "Reporting downloads are centralized in the Admin Control Tower. "
            "Business dashboard pages remain focused on KPIs, charts, trends "
            "and management interpretation, while distributable reporting "
            "assets are managed from this workspace."
        ),
        label="Distribution Policy",
    )


    # ========================================================
    # DOWNLOAD CENTER SCORECARD
    # ========================================================

    st.markdown("### Reporting Asset Estate")

    metric_row(
        [
            (
                "All Assets",
                format_integer(
                    len(artifacts)
                ),
            ),
            (
                "Power BI Assets",
                format_integer(
                    powerbi_count
                ),
            ),
            (
                "Tableau Assets",
                format_integer(
                    tableau_count
                ),
            ),
            (
                "MIS Reports",
                format_integer(
                    mis_count
                ),
            ),
        ]
    )

    total_artifact_bytes = 0

    if (
        not artifacts.empty
        and "Size Bytes" in artifacts.columns
    ):
        total_artifact_bytes = int(
            pd.to_numeric(
                artifacts[
                    "Size Bytes"
                ],
                errors="coerce",
            )
            .fillna(0)
            .sum()
        )

    metric_row(
        [
            (
                "Reporting Storage",
                format_bytes(
                    total_artifact_bytes
                ),
            ),
            (
                "Distribution",
                "Admin Controlled",
            ),
            (
                "Business Pages",
                "Visualization Only",
            ),
            (
                "Download Hub",
                "Control Tower",
            ),
        ]
    )


    # ========================================================
    # NO ASSETS
    # ========================================================

    if artifacts.empty:
        st.warning(
            "No downloadable reporting assets were discovered. "
            "Generate or place approved Power BI, Tableau, MIS or "
            "other reporting files in the configured reporting areas."
        )

    else:
        download_assets = artifacts.copy()

        for column in [
            "Artifact",
            "Category",
            "Type",
            "Size",
            "Path",
        ]:
            if column in download_assets.columns:
                download_assets[column] = (
                    download_assets[column]
                    .fillna("")
                    .astype(str)
                )

        if "Modified" in download_assets.columns:
            download_assets["Modified"] = pd.to_datetime(
                download_assets["Modified"],
                errors="coerce",
            )


        # ====================================================
        # CATEGORY OVERVIEW
        # ====================================================

        section_header(
            "Reporting Categories",
            (
                "Understand which business-intelligence and reporting "
                "deliverables are currently available."
            ),
        )

        if "Category" in download_assets.columns:
            category_summary = (
                download_assets[
                    "Category"
                ]
                .replace(
                    "",
                    "Other",
                )
                .value_counts()
                .rename_axis(
                    "Category"
                )
                .reset_index(
                    name="Assets"
                )
            )

            category_left, category_right = st.columns(
                [1.05, 1]
            )

            with category_left:
                fig = px.bar(
                    category_summary,
                    x="Category",
                    y="Assets",
                    title="Reporting Assets by Category",
                    text_auto=True,
                )

                fig.update_xaxes(
                    title=None
                )

                fig.update_yaxes(
                    title="Assets"
                )

                st.plotly_chart(
                    style_figure(
                        fig,
                        380,
                    ),
                    width="stretch",
                )

            with category_right:
                dataframe(
                    category_summary,
                    height=380,
                )


        # ====================================================
        # POWER BI CENTER
        # ====================================================

        section_header(
            "Power BI Dashboard Center",
            (
                "Dedicated administrative area for Hospital 360 "
                "Power BI dashboard files and supporting assets."
            ),
        )

        powerbi_assets = pd.DataFrame()

        if "Category" in download_assets.columns:
            powerbi_assets = (
                download_assets[
                    download_assets[
                        "Category"
                    ]
                    .str.contains(
                        "power bi|powerbi",
                        case=False,
                        na=False,
                        regex=True,
                    )
                ]
                .copy()
            )

        if powerbi_assets.empty:
            st.info(
                "No Power BI reporting assets are currently available. "
                "When Power BI deliverables are added to the configured "
                "reporting area, they will appear here automatically."
            )

        else:
            powerbi_total_bytes = (
                int(
                    pd.to_numeric(
                        powerbi_assets[
                            "Size Bytes"
                        ],
                        errors="coerce",
                    )
                    .fillna(0)
                    .sum()
                )
                if "Size Bytes"
                in powerbi_assets.columns
                else 0
            )

            metric_row(
                [
                    (
                        "Power BI Assets",
                        format_integer(
                            len(
                                powerbi_assets
                            )
                        ),
                    ),
                    (
                        "Storage",
                        format_bytes(
                            powerbi_total_bytes
                        ),
                    ),
                    (
                        "Distribution",
                        "Admin Only",
                    ),
                    (
                        "Purpose",
                        "BI Dashboard",
                    ),
                ]
            )

            powerbi_columns = [
                column
                for column in [
                    "Artifact",
                    "Type",
                    "Size",
                    "Modified",
                ]
                if column
                in powerbi_assets.columns
            ]

            dataframe(
                powerbi_assets[
                    powerbi_columns
                ],
                height=320,
            )

            st.markdown(
                "### Download Power BI Assets"
            )

            for index, row in powerbi_assets.reset_index(
                drop=True
            ).iterrows():
                artifact_number = int(str(index)) + 1
                artifact_name = str(
                    row.get(
                        "Artifact",
                        f"Power BI Asset {artifact_number}",
                    )
                )

                artifact_type = str(
                    row.get(
                        "Type",
                        "File",
                    )
                )

                artifact_size = str(
                    row.get(
                        "Size",
                        "",
                    )
                )

                artifact_modified = (
                    row.get(
                        "Modified"
                    )
                )

                artifact_path = str(
                    row.get(
                        "Path",
                        "",
                    )
                )

                with st.container(
                    border=True
                ):
                    name_col, detail_col = st.columns(
                        [1.5, 1]
                    )

                    with name_col:
                        st.markdown(
                            f"#### {artifact_name}"
                        )

                        st.write(
                            (
                                "Hospital 360 Power BI "
                                "reporting deliverable."
                            )
                        )

                    with detail_col:
                        st.write(
                            f"**Type:** {artifact_type}"
                        )

                        if artifact_size:
                            st.write(
                                f"**Size:** {artifact_size}"
                            )

                        if (
                            pd.notna(
                                artifact_modified
                            )
                        ):
                            try:
                                st.write(
                                    "**Modified:** "
                                    + artifact_modified.strftime(
                                        "%Y-%m-%d %H:%M"
                                    )
                                )
                            except Exception:
                                st.write(
                                    f"**Modified:** {artifact_modified}"
                                )

                    if (
                        artifact_path
                        and Path(
                            artifact_path
                        ).is_file()
                    ):
                        file_path = Path(
                            artifact_path
                        )

                        try:
                            file_bytes = (
                                file_path.read_bytes()
                            )

                            st.download_button(
                                label=(
                                    f"Download {artifact_name}"
                                ),
                                data=file_bytes,
                                file_name=file_path.name,
                                mime=(
                                    "application/octet-stream"
                                ),
                                width="stretch",
                                key=(
                                    f"powerbi_download_"
                                    f"{index}"
                                ),
                            )

                        except Exception as exc:
                            st.error(
                                (
                                    "This Power BI asset was discovered "
                                    "but could not be prepared for download. "
                                    f"{exc}"
                                )
                            )

                    else:
                        st.warning(
                            "The asset is listed in the reporting "
                            "inventory, but its physical file is not "
                            "currently available at the recorded path."
                        )


        # ====================================================
        # TABLEAU CENTER
        # ====================================================

        section_header(
            "Tableau Reporting Center",
            (
                "Administrative distribution area for Hospital 360 "
                "Tableau workbooks and supporting files."
            ),
        )

        tableau_assets = pd.DataFrame()

        if "Category" in download_assets.columns:
            tableau_assets = (
                download_assets[
                    download_assets[
                        "Category"
                    ]
                    .str.contains(
                        "tableau",
                        case=False,
                        na=False,
                    )
                ]
                .copy()
            )

        if tableau_assets.empty:
            st.info(
                "No Tableau reporting assets are currently available."
            )

        else:
            tableau_columns = [
                column
                for column in [
                    "Artifact",
                    "Type",
                    "Size",
                    "Modified",
                ]
                if column
                in tableau_assets.columns
            ]

            dataframe(
                tableau_assets[
                    tableau_columns
                ],
                height=300,
            )

            for artifact_index, (_, row) in enumerate(
                tableau_assets.iterrows(),
                start=1,
            ):
                artifact_number = artifact_index
                artifact_name = str(
                    row.get(
                        "Artifact",
                        f"Tableau Asset {artifact_number}",
                    )
                )

                artifact_path = str(
                    row.get(
                        "Path",
                        "",
                    )
                )

                with st.container(
                    border=True
                ):
                    st.markdown(
                        f"#### {artifact_name}"
                    )

                    st.write(
                        "Hospital 360 Tableau reporting deliverable."
                    )

                    if (
                        artifact_path
                        and Path(
                            artifact_path
                        ).is_file()
                    ):
                        file_path = Path(
                            artifact_path
                        )

                        try:
                            st.download_button(
                                label=(
                                    f"Download {artifact_name}"
                                ),
                                data=file_path.read_bytes(),
                                file_name=file_path.name,
                                mime=(
                                    "application/octet-stream"
                                ),
                                width="stretch",
                                key=(
                                    f"tableau_download_"
                                    f"{artifact_index}"
                                ),
                            )

                        except Exception as exc:
                            st.error(
                                (
                                    "The Tableau asset could not "
                                    f"be prepared for download. {exc}"
                                )
                            )

                    else:
                        st.warning(
                            "The physical Tableau file is unavailable "
                            "at the recorded path."
                        )


        # ====================================================
        # MIS REPORT CENTER
        # ====================================================

        section_header(
            "MIS Report Center",
            (
                "Central administrative distribution area for Hospital 360 "
                "management-information reports."
            ),
        )

        mis_assets = pd.DataFrame()

        if "Category" in download_assets.columns:
            mis_assets = (
                download_assets[
                    download_assets[
                        "Category"
                    ]
                    .str.contains(
                        "mis",
                        case=False,
                        na=False,
                    )
                ]
                .copy()
            )

        if mis_assets.empty:
            st.info(
                "No MIS reporting assets are currently available."
            )

        else:
            mis_columns = [
                column
                for column in [
                    "Artifact",
                    "Type",
                    "Size",
                    "Modified",
                ]
                if column
                in mis_assets.columns
            ]

            dataframe(
                mis_assets[
                    mis_columns
                ],
                height=300,
            )

            for index, row in enumerate(
                mis_assets.reset_index(drop=True).to_dict(
                    orient="records"
                ),
                start=1,
            ):
                report_index = index
                artifact_name = str(
                    row.get("Artifact")
                    if row.get("Artifact") is not None
                    else f"MIS Report {report_index}"
                )

                artifact_path = str(
                    row.get(
                        "Path",
                        "",
                    )
                )

                with st.container(
                    border=True
                ):
                    st.markdown(
                        f"#### {artifact_name}"
                    )

                    st.write(
                        "Hospital 360 management-information report."
                    )

                    if (
                        artifact_path
                        and Path(
                            artifact_path
                        ).is_file()
                    ):
                        file_path = Path(
                            artifact_path
                        )

                        try:
                            st.download_button(
                                label=(
                                    f"Download {artifact_name}"
                                ),
                                data=file_path.read_bytes(),
                                file_name=file_path.name,
                                mime=(
                                    "application/octet-stream"
                                ),
                                width="stretch",
                                key=(
                                    f"mis_download_"
                                    f"{index}"
                                ),
                            )

                        except Exception as exc:
                            st.error(
                                (
                                    "The MIS report could not "
                                    f"be prepared for download. {exc}"
                                )
                            )

                    else:
                        st.warning(
                            "The physical MIS file is unavailable "
                            "at the recorded path."
                        )


        # ====================================================
        # COMPLETE ASSET EXPLORER
        # ====================================================

        section_header(
            "Reporting Asset Explorer",
            (
                "Search and filter all reporting deliverables discovered "
                "by the Hospital 360 Control Tower."
            ),
        )

        search_col, category_col, type_col = st.columns(
            [1.4, 1, 1]
        )

        with search_col:
            artifact_search = st.text_input(
                "Search Reporting Assets",
                placeholder=(
                    "Search by report or dashboard name"
                ),
                key="control_tower_artifact_search",
            )

        category_options = (
            sorted(
                [
                    value
                    for value in download_assets[
                        "Category"
                    ]
                    .dropna()
                    .astype(str)
                    .unique()
                    .tolist()
                    if value
                ]
            )
            if "Category"
            in download_assets.columns
            else []
        )

        type_options = (
            sorted(
                [
                    value
                    for value in download_assets[
                        "Type"
                    ]
                    .dropna()
                    .astype(str)
                    .unique()
                    .tolist()
                    if value
                ]
            )
            if "Type"
            in download_assets.columns
            else []
        )

        with category_col:
            selected_artifact_categories = st.multiselect(
                "Category",
                options=category_options,
                default=[],
                key="control_tower_artifact_category",
            )

        with type_col:
            selected_artifact_types = st.multiselect(
                "File Type",
                options=type_options,
                default=[],
                key="control_tower_artifact_type",
            )

        filtered_assets = (
            download_assets.copy()
        )

        if artifact_search.strip():
            search_value = (
                artifact_search
                .strip()
                .lower()
            )

            asset_mask = pd.Series(
                False,
                index=filtered_assets.index,
            )

            for column in [
                "Artifact",
                "Category",
                "Type",
            ]:
                if column in filtered_assets.columns:
                    asset_mask = (
                        asset_mask
                        | filtered_assets[
                            column
                        ]
                        .fillna("")
                        .astype(str)
                        .str.lower()
                        .str.contains(
                            search_value,
                            regex=False,
                        )
                    )

            filtered_assets = (
                filtered_assets[
                    asset_mask
                ]
            )

        if selected_artifact_categories:
            filtered_assets = (
                filtered_assets[
                    filtered_assets[
                        "Category"
                    ]
                    .isin(
                        selected_artifact_categories
                    )
                ]
            )

        if selected_artifact_types:
            filtered_assets = (
                filtered_assets[
                    filtered_assets[
                        "Type"
                    ]
                    .isin(
                        selected_artifact_types
                    )
                ]
            )

        metric_row(
            [
                (
                    "Matching Assets",
                    format_integer(
                        len(
                            filtered_assets
                        )
                    ),
                ),
                (
                    "Categories",
                    format_integer(
                        filtered_assets[
                            "Category"
                        ].nunique()
                        if "Category"
                        in filtered_assets.columns
                        else 0
                    ),
                ),
                (
                    "File Types",
                    format_integer(
                        filtered_assets[
                            "Type"
                        ].nunique()
                        if "Type"
                        in filtered_assets.columns
                        else 0
                    ),
                ),
                (
                    "Distribution",
                    "Controlled",
                ),
            ]
        )

        explorer_columns = [
            column
            for column in [
                "Artifact",
                "Category",
                "Type",
                "Size",
                "Modified",
            ]
            if column
            in filtered_assets.columns
        ]

        dataframe(
            filtered_assets[
                explorer_columns
            ],
            height=450,
        )


        # ====================================================
        # ASSET INSPECTOR
        # ====================================================

        section_header(
            "Reporting Asset Inspector",
            (
                "Select one reporting deliverable to review its metadata "
                "and download the physical file."
            ),
        )

        if filtered_assets.empty:
            st.info(
                "No reporting assets match the current filters."
            )

        else:
            inspector_assets = (
                filtered_assets.reset_index(
                    drop=True
                )
            )

            selected_asset_index = st.selectbox(
                "Select Reporting Asset",
                options=list(
                    range(
                        len(
                            inspector_assets
                        )
                    )
                ),
                format_func=lambda index: str(
                    inspector_assets.iloc[
                        index
                    ].get(
                        "Artifact",
                        f"Asset {index + 1}",
                    )
                ),
                key="control_tower_asset_inspector",
            )

            selected_asset = (
                inspector_assets.iloc[
                    selected_asset_index
                ]
            )

            selected_name = str(
                selected_asset.get(
                    "Artifact",
                    "Reporting Asset",
                )
            )

            selected_category = str(
                selected_asset.get(
                    "Category",
                    "Other",
                )
            )

            selected_type = str(
                selected_asset.get(
                    "Type",
                    "File",
                )
            )

            selected_size = str(
                selected_asset.get(
                    "Size",
                    "",
                )
            )

            selected_path = str(
                selected_asset.get(
                    "Path",
                    "",
                )
            )

            metric_row(
                [
                    (
                        "Asset",
                        selected_name,
                    ),
                    (
                        "Category",
                        selected_category,
                    ),
                    (
                        "Type",
                        selected_type,
                    ),
                    (
                        "Size",
                        (
                            selected_size
                            if selected_size
                            else "N/A"
                        ),
                    ),
                ]
            )

            asset_details = pd.DataFrame(
                [
                    {
                        "Field": column,
                        "Value": (
                            ""
                            if pd.isna(
                                selected_asset.get(
                                    column
                                )
                            )
                            else str(
                                selected_asset.get(
                                    column
                                )
                            )
                        ),
                    }
                    for column
                    in inspector_assets.columns
                ]
            )

            dataframe(
                asset_details,
                height=350,
            )

            if (
                selected_path
                and Path(
                    selected_path
                ).is_file()
            ):
                selected_file_path = Path(
                    selected_path
                )

                try:
                    selected_file_bytes = (
                        selected_file_path.read_bytes()
                    )

                    st.download_button(
                        label=(
                            f"Download {selected_name}"
                        ),
                        data=selected_file_bytes,
                        file_name=(
                            selected_file_path.name
                        ),
                        mime=(
                            "application/octet-stream"
                        ),
                        width="stretch",
                        key="control_tower_selected_asset_download",
                    )

                except Exception as exc:
                    st.error(
                        (
                            "The selected asset exists but could not "
                            f"be prepared for download. {exc}"
                        )
                    )

            else:
                st.warning(
                    "The selected reporting asset does not currently "
                    "have an accessible physical file."
                )


        # ====================================================
        # COMPLETE REPORTING INVENTORY
        # ====================================================

        section_header(
            "Complete Reporting Inventory",
            (
                "Administrative inventory of all reporting artifacts "
                "discovered by Hospital 360."
            ),
        )

        complete_inventory_columns = [
            column
            for column in [
                "Artifact",
                "Category",
                "Type",
                "Size",
                "Modified",
                "Path",
            ]
            if column
            in download_assets.columns
        ]

        inventory_display = (
            download_assets[
                complete_inventory_columns
            ]
            .copy()
        )

        if "Modified" in inventory_display.columns:
            inventory_display = (
                inventory_display.sort_values(
                    by=["Modified"],
                    ascending=[False],
                    na_position="last",
                )
            )

        dataframe(
            inventory_display,
            height=550,
        )


    # ========================================================
    # DISTRIBUTION RESPONSIBILITIES
    # ========================================================

    section_header(
        "Reporting Distribution Model",
        (
            "Clear separation between analytical visualization "
            "and administrative file distribution."
        ),
    )

    distribution_model = pd.DataFrame(
        [
            {
                "Platform Area": "Executive Dashboard",
                "Primary Purpose": (
                    "Enterprise KPI interpretation"
                ),
                "Downloads": "No",
                "Owner": "Business Analytics",
            },
            {
                "Platform Area": "Patient Analytics",
                "Primary Purpose": (
                    "Patient utilization visualization"
                ),
                "Downloads": "No",
                "Owner": "Business Analytics",
            },
            {
                "Platform Area": "Financial Analytics",
                "Primary Purpose": (
                    "Revenue and financial visualization"
                ),
                "Downloads": "No",
                "Owner": "Business Analytics",
            },
            {
                "Platform Area": "Claims Analytics",
                "Primary Purpose": (
                    "Claims and payer visualization"
                ),
                "Downloads": "No",
                "Owner": "Business Analytics",
            },
            {
                "Platform Area": "Doctor Performance",
                "Primary Purpose": (
                    "Doctor performance visualization"
                ),
                "Downloads": "No",
                "Owner": "Business Analytics",
            },
            {
                "Platform Area": "AI Analyst",
                "Primary Purpose": (
                    "Governed analytical questions"
                ),
                "Downloads": "No",
                "Owner": "Analytics",
            },
            {
                "Platform Area": "Admin Control Tower",
                "Primary Purpose": (
                    "Reporting asset administration"
                ),
                "Downloads": "Yes",
                "Owner": "Administrator",
            },
        ]
    )

    dataframe(
        distribution_model,
        height=380,
    )


    # ========================================================
    # REPORTING DELIVERY FLOW
    # ========================================================

    section_header(
        "Reporting Delivery Flow",
        (
            "Sequence explaining how analytical information becomes "
            "a controlled reporting deliverable."
        ),
    )

    reporting_flow = pd.DataFrame(
        [
            {
                "Step": "01",
                "Stage": "Governed Data",
                "Question": (
                    "Is validated analytical data available?"
                ),
                "Output": "Warehouse Data",
            },
            {
                "Step": "02",
                "Stage": "Semantic Metrics",
                "Question": (
                    "Are management measures available?"
                ),
                "Output": "Analytics Views",
            },
            {
                "Step": "03",
                "Stage": "Visualization",
                "Question": (
                    "Can users understand performance?"
                ),
                "Output": "Streamlit Dashboards",
            },
            {
                "Step": "04",
                "Stage": "BI Production",
                "Question": (
                    "Has an external BI deliverable been created?"
                ),
                "Output": "Power BI / Tableau",
            },
            {
                "Step": "05",
                "Stage": "MIS Production",
                "Question": (
                    "Has a management report been produced?"
                ),
                "Output": "MIS Report",
            },
            {
                "Step": "06",
                "Stage": "Administrative Review",
                "Question": (
                    "Is the reporting asset ready for distribution?"
                ),
                "Output": "Approved Artifact",
            },
            {
                "Step": "07",
                "Stage": "Distribution",
                "Question": (
                    "Where should the file be downloaded?"
                ),
                "Output": "Admin Download Center",
            },
        ]
    )

    dataframe(
        reporting_flow,
        height=370,
    )

with tabs[6]:
    section_header(
        "Storage & Project Assets",
        (
            "Administrative view of Hospital 360 project storage, reporting "
            "files and data assets across the application."
        ),
    )

    if artifacts.empty:
        st.info(
            "No project or reporting assets are currently available "
            "for storage analysis."
        )

    else:
        storage = artifacts.copy()

        if "Size Bytes" in storage.columns:
            storage["Size Bytes"] = pd.to_numeric(
                storage["Size Bytes"],
                errors="coerce",
            ).fillna(0)
        else:
            storage["Size Bytes"] = 0

        total_files = len(storage)
        total_storage = int(storage["Size Bytes"].sum())

        largest_file = "N/A"
        largest_file_size = 0

        if not storage.empty:
            largest_row = storage.sort_values(
                by=["Size Bytes"],
                ascending=[False],
            ).iloc[0]

            largest_file = str(
                largest_row.get(
                    "Artifact",
                    "N/A",
                )
            )

            largest_file_size = int(
                largest_row.get(
                    "Size Bytes",
                    0,
                )
            )

        categories = (
            storage["Category"].nunique()
            if "Category" in storage.columns
            else 0
        )

        metric_row(
            [
                (
                    "Stored Assets",
                    format_integer(total_files),
                ),
                (
                    "Total Storage",
                    format_bytes(total_storage),
                ),
                (
                    "Asset Categories",
                    format_integer(categories),
                ),
                (
                    "Largest File",
                    format_bytes(largest_file_size),
                ),
            ]
        )

        management_insight(
            (
                f"The Control Tower currently tracks {total_files:,} "
                f"reporting or project assets using approximately "
                f"{format_bytes(total_storage)} of storage. "
                f"The largest discovered asset is {largest_file}."
            ),
            label="Storage Assessment",
        )

        section_header(
            "Storage by Category",
            (
                "Understand how discovered project storage is distributed "
                "across reporting categories."
            ),
        )

        if "Category" in storage.columns:
            storage["Category"] = (
                storage["Category"]
                .fillna("Other")
                .astype(str)
            )

            storage_summary = (
                storage.groupby(
                    "Category",
                    as_index=False,
                )
                .agg(
                    Files=("Category", "size"),
                    Storage_Bytes=("Size Bytes", "sum"),
                )
                .sort_values(
                    by=["Storage_Bytes"],
                    ascending=[False],
                )
            )

            storage_summary["Storage"] = (
                storage_summary["Storage_Bytes"]
                .apply(format_bytes)
            )

            storage_left, storage_right = st.columns(
                [1.1, 1]
            )

            with storage_left:
                fig = px.bar(
                    storage_summary,
                    x="Category",
                    y="Storage_Bytes",
                    title="Storage Consumption by Category",
                    text_auto=True,
                )

                fig.update_xaxes(
                    title=None
                )

                fig.update_yaxes(
                    title="Storage (Bytes)"
                )

                st.plotly_chart(
                    style_figure(
                        fig,
                        400,
                    ),
                    width="stretch",
                )

            with storage_right:
                dataframe(
                    storage_summary[
                        [
                            "Category",
                            "Files",
                            "Storage",
                        ]
                    ],
                    height=400,
                )

        section_header(
            "Largest Project Assets",
            (
                "Identify reporting files consuming the greatest amount "
                "of tracked project storage."
            ),
        )

        largest_assets = storage.sort_values(
            by=["Size Bytes"],
            ascending=[False],
        ).head(20).copy()

        largest_assets["Storage"] = (
            largest_assets["Size Bytes"]
            .apply(format_bytes)
        )

        largest_columns = [
            column
            for column in [
                "Artifact",
                "Category",
                "Type",
                "Storage",
                "Modified",
            ]
            if column in largest_assets.columns
        ]

        dataframe(
            largest_assets[
                largest_columns
            ],
            height=430,
        )

        section_header(
            "Storage Explorer",
            (
                "Search the project asset inventory without changing "
                "or deleting physical files."
            ),
        )

        storage_search = st.text_input(
            "Search Stored Assets",
            placeholder="Search by file, category or type",
            key="control_tower_storage_search",
        )

        storage_category_options = (
            sorted(
                storage["Category"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
            if "Category" in storage.columns
            else []
        )

        selected_storage_categories = st.multiselect(
            "Storage Category",
            options=storage_category_options,
            default=[],
            key="control_tower_storage_categories",
        )

        filtered_storage = storage.copy()

        if selected_storage_categories:
            filtered_storage = filtered_storage[
                filtered_storage["Category"].isin(
                    selected_storage_categories
                )
            ]

        if storage_search.strip():
            search_value = storage_search.strip().lower()

            mask = pd.Series(
                False,
                index=filtered_storage.index,
            )

            for column in [
                "Artifact",
                "Category",
                "Type",
                "Path",
            ]:
                if column in filtered_storage.columns:
                    mask = (
                        mask
                        | filtered_storage[column]
                        .fillna("")
                        .astype(str)
                        .str.lower()
                        .str.contains(
                            search_value,
                            regex=False,
                        )
                    )

            filtered_storage = filtered_storage[
                mask
            ]

        metric_row(
            [
                (
                    "Matching Assets",
                    format_integer(
                        len(filtered_storage)
                    ),
                ),
                (
                    "Matching Storage",
                    format_bytes(
                        int(
                            filtered_storage[
                                "Size Bytes"
                            ].sum()
                        )
                    ),
                ),
                (
                    "Access",
                    "Read Only",
                ),
                (
                    "Deletion",
                    "Disabled",
                ),
            ]
        )

        display_storage = filtered_storage.copy()

        display_storage["Storage"] = (
            display_storage["Size Bytes"]
            .apply(format_bytes)
        )

        storage_columns = [
            column
            for column in [
                "Artifact",
                "Category",
                "Type",
                "Storage",
                "Modified",
                "Path",
            ]
            if column in display_storage.columns
        ]

        dataframe(
            display_storage[
                storage_columns
            ],
            height=520,
        )

    section_header(
        "Hospital 360 Data Lifecycle",
        (
            "Complete project flow from operational source data to "
            "management reporting and controlled distribution."
        ),
    )

    lifecycle = pd.DataFrame(
        [
            {
                "Step": "01",
                "Layer": "Hospital Operations",
                "Purpose": "Operational records are generated",
                "Output": "Source Data",
            },
            {
                "Step": "02",
                "Layer": "ETL",
                "Purpose": "Source records are ingested and transformed",
                "Output": "Processed Data",
            },
            {
                "Step": "03",
                "Layer": "Data Quality",
                "Purpose": "Records are validated and exceptions identified",
                "Output": "Validated Data",
            },
            {
                "Step": "04",
                "Layer": "Warehouse",
                "Purpose": "Analytical facts and dimensions are maintained",
                "Output": "Governed Warehouse",
            },
            {
                "Step": "05",
                "Layer": "Analytics",
                "Purpose": "Business measures and semantic views are exposed",
                "Output": "Analytics Layer",
            },
            {
                "Step": "06",
                "Layer": "Streamlit",
                "Purpose": "Business users explore dashboards and insights",
                "Output": "Interactive Analytics",
            },
            {
                "Step": "07",
                "Layer": "AI Analyst",
                "Purpose": "Natural-language analytical questions are answered",
                "Output": "Governed AI Insight",
            },
            {
                "Step": "08",
                "Layer": "External BI",
                "Purpose": "Power BI and Tableau deliverables are produced",
                "Output": "BI Assets",
            },
            {
                "Step": "09",
                "Layer": "MIS",
                "Purpose": "Management reporting deliverables are produced",
                "Output": "MIS Reports",
            },
            {
                "Step": "10",
                "Layer": "Admin Control Tower",
                "Purpose": "Platform operations and downloads are centralized",
                "Output": "Governed Distribution",
            },
        ]
    )

    dataframe(
        lifecycle,
        height=500,
    )

    section_header(
        "Control Tower Responsibilities",
        (
            "Final administrative responsibility map for the Hospital 360 "
            "analytics platform."
        ),
    )

    responsibilities = pd.DataFrame(
        [
            {
                "Area": "Platform Health",
                "Admin Responsibility": "Monitor",
                "Business Pages": "View",
            },
            {
                "Area": "ETL Operations",
                "Admin Responsibility": "Control and Monitor",
                "Business Pages": "Not Exposed",
            },
            {
                "Area": "Data Quality",
                "Admin Responsibility": "Monitor",
                "Business Pages": "Summarized",
            },
            {
                "Area": "Database & Warehouse",
                "Admin Responsibility": "Govern",
                "Business Pages": "Consume Analytics",
            },
            {
                "Area": "Audit Trail",
                "Admin Responsibility": "Review",
                "Business Pages": "Not Exposed",
            },
            {
                "Area": "Power BI",
                "Admin Responsibility": "Distribute",
                "Business Pages": "No Download",
            },
            {
                "Area": "Tableau",
                "Admin Responsibility": "Distribute",
                "Business Pages": "No Download",
            },
            {
                "Area": "MIS Reports",
                "Admin Responsibility": "Distribute",
                "Business Pages": "No Download",
            },
            {
                "Area": "AI Analyst",
                "Admin Responsibility": "Govern",
                "Business Pages": "Analytical Use",
            },
            {
                "Area": "Project Storage",
                "Admin Responsibility": "Monitor",
                "Business Pages": "Not Exposed",
            },
        ]
    )

    dataframe(
        responsibilities,
        height=450,
    )

    section_header(
        "Control Tower Completion",
        (
            "The Admin Control Tower now provides the centralized "
            "administrative layer for the Hospital 360 project."
        ),
    )

    completion = pd.DataFrame(
        [
            {
                "Module": "Command Center",
                "Status": "Complete",
                "Purpose": "Overall platform health and administration",
            },
            {
                "Module": "ETL Operations",
                "Status": "Complete",
                "Purpose": "Pipeline monitoring and operational control",
            },
            {
                "Module": "Data Quality",
                "Status": "Complete",
                "Purpose": "Validation and exception monitoring",
            },
            {
                "Module": "Database & Warehouse",
                "Status": "Complete",
                "Purpose": "Data-platform visibility and governance",
            },
            {
                "Module": "Audit & Governance",
                "Status": "Complete",
                "Purpose": "Administrative traceability and controls",
            },
            {
                "Module": "Download Center",
                "Status": "Complete",
                "Purpose": "Power BI, Tableau and MIS distribution",
            },
            {
                "Module": "Storage",
                "Status": "Complete",
                "Purpose": "Project asset and storage visibility",
            },
        ]
    )

    dataframe(
        completion,
        height=370,
    )

    st.success(
        "Hospital 360 Admin Control Tower is ready as the centralized "
        "administrative, governance, monitoring and reporting-distribution "
        "workspace."
    )