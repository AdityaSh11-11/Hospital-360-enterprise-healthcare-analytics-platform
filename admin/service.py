from __future__ import annotations

import re
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import text

from database.connection import get_engine


PROJECT_ROOT = Path(__file__).resolve().parents[1]

# IMPORTANT:
# Incremental generator / ETL CLI uses:
# data/incremental/BATCH-YYYYMMDD-NNN
INCREMENTAL_ROOT = (
    PROJECT_ROOT
    / "data"
    / "incremental"
)

EXPORT_ROOT = (
    PROJECT_ROOT
    / "data"
    / "exports"
)

BATCH_PATTERN = re.compile(
    r"^BATCH-(\d{8})-(\d{3})$"
)


@dataclass
class AdminActionResult:
    action: str
    status: str
    message: str
    duration_seconds: float
    stdout: str = ""
    stderr: str = ""
    return_code: int | None = None

    @property
    def succeeded(self) -> bool:
        return self.status == "SUCCESS"


def record_audit_event(
    module: str,
    action: str,
    status: str,
    details: str = "",
    entity_type: str | None = None,
    entity_id: str | None = None,
    username: str = "streamlit_admin",
) -> None:
    engine = get_engine()

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO control.audit_log (
                    event_timestamp,
                    username,
                    module,
                    action,
                    entity_type,
                    entity_id,
                    status,
                    details
                )
                VALUES (
                    NOW(),
                    :username,
                    :module,
                    :action,
                    :entity_type,
                    :entity_id,
                    :status,
                    :details
                )
                """
            ),
            {
                "username": username,
                "module": module,
                "action": action,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "status": status,
                "details": details,
            },
        )


def get_audit_history(
    limit: int = 100,
    module: str | None = None,
    status: str | None = None,
) -> pd.DataFrame:
    limit = max(
        1,
        min(int(limit), 1000),
    )

    clauses: list[str] = []

    params: dict[str, Any] = {
        "limit": limit,
    }

    if module:
        clauses.append(
            "module = :module"
        )
        params["module"] = module

    if status:
        clauses.append(
            "status = :status"
        )
        params["status"] = status

    where_clause = (
        "WHERE " + " AND ".join(clauses)
        if clauses
        else ""
    )

    query = text(
        f"""
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
        {where_clause}
        ORDER BY audit_id DESC
        LIMIT :limit
        """
    )

    engine = get_engine()

    with engine.connect() as connection:
        return pd.read_sql(
            query,
            connection,
            params=params,
        )


def get_audit_filter_values() -> dict[str, list[str]]:
    engine = get_engine()

    with engine.connect() as connection:
        modules = connection.execute(
            text(
                """
                SELECT DISTINCT module
                FROM control.audit_log
                WHERE module IS NOT NULL
                ORDER BY module
                """
            )
        ).scalars().all()

        statuses = connection.execute(
            text(
                """
                SELECT DISTINCT status
                FROM control.audit_log
                WHERE status IS NOT NULL
                ORDER BY status
                """
            )
        ).scalars().all()

    return {
        "modules": [
            str(value)
            for value in modules
        ],
        "statuses": [
            str(value)
            for value in statuses
        ],
    }


def discover_incremental_batches() -> pd.DataFrame:
    """
    Discover incremental source batches from the exact
    source directory used by the generator / ETL CLI.

    Source:
        data/incremental/BATCH-YYYYMMDD-NNN

    ETL status is resolved from the latest control.etl_batch
    record for each source_batch_id.
    """

    columns = [
        "source_batch_id",
        "business_date",
        "sequence",
        "path",
        "etl_status",
        "etl_batch_id",
    ]

    if not INCREMENTAL_ROOT.exists():
        return pd.DataFrame(
            columns=columns
        )

    engine = get_engine()

    with engine.connect() as connection:
        loaded = pd.read_sql(
            text(
                """
                SELECT DISTINCT ON (source_batch_id)
                    source_batch_id,
                    batch_id AS etl_batch_id,
                    status AS etl_status
                FROM control.etl_batch
                WHERE source_batch_id IS NOT NULL
                ORDER BY
                    source_batch_id,
                    batch_id DESC
                """
            ),
            connection,
        )

    status_lookup: dict[
        str,
        dict[str, Any],
    ] = {}

    if not loaded.empty:
        for _, row in loaded.iterrows():
            source_batch_id = str(
                row["source_batch_id"]
            )

            status_lookup[
                source_batch_id
            ] = {
                "etl_status":
                    row["etl_status"],
                "etl_batch_id":
                    row["etl_batch_id"],
            }

    rows: list[dict[str, Any]] = []

    for path in sorted(
        INCREMENTAL_ROOT.iterdir()
    ):
        if not path.is_dir():
            continue

        match = BATCH_PATTERN.match(
            path.name
        )

        if not match:
            continue

        business_date = pd.to_datetime(
            match.group(1),
            format="%Y%m%d",
        ).date()

        sequence = int(
            match.group(2)
        )

        etl_info = status_lookup.get(
            path.name,
            {},
        )

        rows.append(
            {
                "source_batch_id":
                    path.name,

                "business_date":
                    business_date,

                "sequence":
                    sequence,

                "path":
                    str(
                        path.relative_to(
                            PROJECT_ROOT
                        )
                    ),

                "etl_status":
                    etl_info.get(
                        "etl_status",
                        "PENDING",
                    ),

                "etl_batch_id":
                    etl_info.get(
                        "etl_batch_id",
                    ),
            }
        )

    return pd.DataFrame(
        rows,
        columns=columns,
    )


def get_pending_batches() -> pd.DataFrame:
    """
    A source batch is pending unless its latest ETL attempt
    has SUCCESS status.
    """

    batches = discover_incremental_batches()

    if batches.empty:
        return batches

    successful = (
        batches["etl_status"]
        .astype(str)
        .str.upper()
        .eq("SUCCESS")
    )

    return (
        batches.loc[
            ~successful
        ]
        .sort_values(
            [
                "business_date",
                "sequence",
            ]
        )
        .reset_index(drop=True)
    )


def _run_python_module(
    *,
    action: str,
    module: str,
    arguments: list[str] | None = None,
    timeout_seconds: int = 900,
    entity_type: str | None = None,
    entity_id: str | None = None,
) -> AdminActionResult:
    arguments = arguments or []

    command = [
        sys.executable,
        "-m",
        module,
        *arguments,
    ]

    start = time.perf_counter()

    try:
        record_audit_event(
            module="Admin Service",
            action=action,
            status="STARTED",
            details=(
                "Executing: "
                + " ".join(command)
            ),
            entity_type=entity_type,
            entity_id=entity_id,
        )

        completed = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )

        duration = (
            time.perf_counter()
            - start
        )

        stdout = (
            completed.stdout
            or ""
        ).strip()

        stderr = (
            completed.stderr
            or ""
        ).strip()

        status = (
            "SUCCESS"
            if completed.returncode == 0
            else "FAILED"
        )

        if status == "SUCCESS":
            message = (
                f"{action} completed successfully."
            )
        else:
            message = (
                f"{action} failed with return "
                f"code {completed.returncode}."
            )

        audit_details = (
            f"Module: {module}\n"
            f"Arguments: "
            f"{' '.join(arguments) or 'none'}\n"
            f"Return code: "
            f"{completed.returncode}\n"
            f"Duration: "
            f"{duration:.2f}s"
        )

        if stdout:
            audit_details += (
                "\n\nSTDOUT:\n"
                + stdout[-5000:]
            )

        if stderr:
            audit_details += (
                "\n\nSTDERR:\n"
                + stderr[-5000:]
            )

        record_audit_event(
            module="Admin Service",
            action=action,
            status=status,
            details=audit_details,
            entity_type=entity_type,
            entity_id=entity_id,
        )

        return AdminActionResult(
            action=action,
            status=status,
            message=message,
            duration_seconds=duration,
            stdout=stdout,
            stderr=stderr,
            return_code=
                completed.returncode,
        )

    except subprocess.TimeoutExpired as exc:
        duration = (
            time.perf_counter()
            - start
        )

        message = (
            f"{action} exceeded the "
            f"{timeout_seconds}-second timeout."
        )

        record_audit_event(
            module="Admin Service",
            action=action,
            status="TIMEOUT",
            details=message,
            entity_type=entity_type,
            entity_id=entity_id,
        )

        return AdminActionResult(
            action=action,
            status="TIMEOUT",
            message=message,
            duration_seconds=duration,
            stdout=str(
                exc.stdout
                or ""
            ),
            stderr=str(
                exc.stderr
                or ""
            ),
        )

    except Exception as exc:
        duration = (
            time.perf_counter()
            - start
        )

        message = (
            f"{action} could not be executed: "
            f"{exc}"
        )

        try:
            record_audit_event(
                module="Admin Service",
                action=action,
                status="ERROR",
                details=message,
                entity_type=entity_type,
                entity_id=entity_id,
            )
        except Exception:
            pass

        return AdminActionResult(
            action=action,
            status="ERROR",
            message=message,
            duration_seconds=duration,
            stderr=str(exc),
        )


def generate_synthetic_batch(
    business_date: date,
) -> AdminActionResult:
    return _run_python_module(
        action="Generate Synthetic Batch",
        module=(
            "scripts.generate_incremental_data"
        ),
        arguments=[
            "--date",
            business_date.isoformat(),
        ],
        timeout_seconds=600,
        entity_type="BUSINESS_DATE",
        entity_id=
            business_date.isoformat(),
    )


def run_pending_incremental_etl(
) -> AdminActionResult:
    """
    Use the exact same ETL entry point that works from
    PowerShell:

        python -m scripts.run_incremental_etl --all-pending
    """

    pending = get_pending_batches()

    if pending.empty:
        return AdminActionResult(
            action="Run Pending Incremental ETL",
            status="SUCCESS",
            message=(
                "No incremental source batches "
                "are pending."
            ),
            duration_seconds=0.0,
            stdout=(
                "Pending queue is empty."
            ),
            return_code=0,
        )

    return _run_python_module(
        action="Run Pending Incremental ETL",
        module=(
            "scripts.run_incremental_etl"
        ),
        arguments=[
            "--all-pending",
        ],
        timeout_seconds=1200,
        entity_type="INCREMENTAL_BATCH_QUEUE",
        entity_id=str(
            len(pending)
        ),
    )


def run_data_quality_validation(
) -> AdminActionResult:
    return _run_python_module(
        action="Run Data Quality Validation",
        module="scripts.check_warehouse",
        timeout_seconds=300,
    )


def run_mis_generation(
) -> AdminActionResult:
    return _run_python_module(
        action="Generate MIS Reports",
        module="scripts.run_mis_report",
        timeout_seconds=600,
    )


def validate_analytical_exports(
) -> AdminActionResult:
    first = _run_python_module(
        action="Validate Anomaly Exports",
        module=(
            "scripts.check_anomaly_exports"
        ),
        timeout_seconds=300,
    )

    if not first.succeeded:
        return first

    second = _run_python_module(
        action=(
            "Validate Unified Risk Exports"
        ),
        module=(
            "scripts."
            "check_unified_risk_exports"
        ),
        timeout_seconds=300,
    )

    if not second.succeeded:
        return second

    return AdminActionResult(
        action="Validate Analytical Exports",
        status="SUCCESS",
        message=(
            "Analytical exports validated "
            "successfully."
        ),
        duration_seconds=(
            first.duration_seconds
            + second.duration_seconds
        ),
        stdout=(
            first.stdout
            + "\n\n"
            + second.stdout
        ).strip(),
        stderr=(
            first.stderr
            + "\n"
            + second.stderr
        ).strip(),
        return_code=0,
    )


def get_admin_capabilities() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "action":
                    "Generate Synthetic Batch",
                "enabled":
                    True,
                "risk_level":
                    "Controlled",
            },
            {
                "action":
                    "Run Pending ETL",
                "enabled":
                    True,
                "risk_level":
                    "Controlled",
            },
            {
                "action":
                    "Data Quality Validation",
                "enabled":
                    True,
                "risk_level":
                    "Read Only",
            },
            {
                "action":
                    "Generate MIS",
                "enabled":
                    True,
                "risk_level":
                    "Controlled",
            },
            {
                "action":
                    "Validate Exports",
                "enabled":
                    True,
                "risk_level":
                    "Read Only",
            },
            {
                "action":
                    "Delete Batch",
                "enabled":
                    False,
                "risk_level":
                    "Destructive",
            },
            {
                "action":
                    "Rebuild Environment",
                "enabled":
                    False,
                "risk_level":
                    "Destructive",
            },
            {
                "action":
                    "Gemini AI",
                "enabled":
                    False,
                "risk_level":
                    "Future Phase",
            },
        ]
    )


def get_export_status() -> pd.DataFrame:
    requirements = [
        (
            "Anomaly Intelligence",
            EXPORT_ROOT
            / "anomalies"
            / "aggregate_anomalies.csv",
        ),
        (
            "Enterprise Risk KPIs",
            EXPORT_ROOT
            / "risk_intelligence"
            / "enterprise_risk_kpis.csv",
        ),
        (
            "Risk Dashboard Feed",
            EXPORT_ROOT
            / "risk_intelligence"
            / "risk_dashboard_feed.csv",
        ),
    ]

    rows: list[dict[str, Any]] = []

    for asset, path in requirements:
        exists = path.exists()

        rows.append(
            {
                "asset":
                    asset,

                "exists":
                    exists,

                "size_kb":
                    (
                        round(
                            path.stat().st_size
                            / 1024,
                            2,
                        )
                        if exists
                        else 0
                    ),

                "path":
                    str(
                        path.relative_to(
                            PROJECT_ROOT
                        )
                    ),
            }
        )

    return pd.DataFrame(rows)


def get_operational_status() -> dict[str, Any]:
    engine = get_engine()

    with engine.connect() as connection:
        etl = connection.execute(
            text(
                """
                SELECT
                    COUNT(*) AS total_batches,

                    COUNT(*) FILTER (
                        WHERE status = 'SUCCESS'
                    ) AS successful_batches,

                    COUNT(*) FILTER (
                        WHERE status = 'FAILED'
                    ) AS failed_batches,

                    COUNT(*) FILTER (
                        WHERE status =
                        'RECONCILIATION_FAILED'
                    )
                    AS reconciliation_failed_batches,

                    MAX(end_time) FILTER (
                        WHERE status = 'SUCCESS'
                    )
                    AS latest_successful_etl

                FROM control.etl_batch
                """
            )
        ).mappings().one()

        audit = connection.execute(
            text(
                """
                SELECT
                    COUNT(*) AS audit_events,
                    MAX(event_timestamp)
                        AS latest_audit_event
                FROM control.audit_log
                """
            )
        ).mappings().one()

        quality = connection.execute(
            text(
                """
                SELECT
                    COUNT(*) AS quality_checks,

                    COALESCE(
                        SUM(failed_records),
                        0
                    ) AS failed_records

                FROM control.data_quality_log
                """
            )
        ).mappings().one()

    pending = get_pending_batches()

    return {
        "total_batches":
            int(
                etl["total_batches"]
                or 0
            ),

        "successful_batches":
            int(
                etl[
                    "successful_batches"
                ]
                or 0
            ),

        "failed_batches":
            int(
                etl[
                    "failed_batches"
                ]
                or 0
            ),

        "reconciliation_failed_batches":
            int(
                etl[
                    "reconciliation_failed_batches"
                ]
                or 0
            ),

        "latest_successful_etl":
            etl[
                "latest_successful_etl"
            ],

        "pending_source_batches":
            len(pending),

        "audit_events":
            int(
                audit[
                    "audit_events"
                ]
                or 0
            ),

        "latest_audit_event":
            audit[
                "latest_audit_event"
            ],

        "quality_checks":
            int(
                quality[
                    "quality_checks"
                ]
                or 0
            ),

        "failed_quality_records":
            int(
                quality[
                    "failed_records"
                ]
                or 0
            ),
    }