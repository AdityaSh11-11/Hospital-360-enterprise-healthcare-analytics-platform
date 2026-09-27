from __future__ import annotations

import json
import re

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from sqlalchemy import text

from database.connection import engine
from utils.logger import get_logger


logger = get_logger(__name__)


# ============================================================
# PATHS
# ============================================================

INCREMENTAL_ROOT = Path(
    "data/incremental"
)


# ============================================================
# REQUIRED FILES
# ============================================================

REQUIRED_FILES = (
    "patients.csv",
    "admissions.csv",
    "billing.csv",
    "claims.csv",
    "labs.csv",
    "medication_events.csv",
)


# ============================================================
# BATCH NAME FORMAT
# ============================================================

BATCH_PATTERN = re.compile(
    r"^BATCH-(\d{8})-(\d{3})$"
)


# ============================================================
# DATA CLASS
# ============================================================

@dataclass(frozen=True)
class IncrementalBatch:

    batch_id: str
    path: Path
    business_date: date
    sequence: int


# ============================================================
# PARSE BATCH NAME
# ============================================================

def parse_batch_name(
    batch_name: str,
) -> tuple[date, int]:

    match = BATCH_PATTERN.match(
        batch_name
    )

    if not match:

        raise ValueError(
            "Invalid incremental batch name: "
            f"{batch_name}. Expected format "
            "BATCH-YYYYMMDD-NNN"
        )

    date_text = match.group(1)

    sequence = int(
        match.group(2)
    )

    business_date = date(
        year=int(date_text[0:4]),
        month=int(date_text[4:6]),
        day=int(date_text[6:8]),
    )

    return (
        business_date,
        sequence,
    )


# ============================================================
# MANIFEST
# ============================================================

def read_manifest(
    batch_path: Path,
) -> dict:

    manifest_path = (
        batch_path
        / "manifest.json"
    )

    if not manifest_path.exists():

        return {}

    try:

        return json.loads(
            manifest_path.read_text(
                encoding="utf-8"
            )
        )

    except json.JSONDecodeError as exc:

        raise ValueError(
            "Invalid JSON in manifest: "
            f"{manifest_path}"
        ) from exc


# ============================================================
# BATCH STRUCTURE VALIDATION
# ============================================================

def validate_batch_directory(
    batch_path: Path,
):

    if not batch_path.exists():

        raise FileNotFoundError(
            f"Batch directory does not exist: "
            f"{batch_path}"
        )

    if not batch_path.is_dir():

        raise NotADirectoryError(
            f"Batch path is not a directory: "
            f"{batch_path}"
        )

    missing_files = [
        filename
        for filename
        in REQUIRED_FILES
        if not (
            batch_path
            / filename
        ).exists()
    ]

    if missing_files:

        formatted = ", ".join(
            missing_files
        )

        raise FileNotFoundError(
            f"Batch {batch_path.name} "
            f"is incomplete. Missing: "
            f"{formatted}"
        )


# ============================================================
# DISCOVER BATCHES
# ============================================================

def discover_batches(
    root: Path = INCREMENTAL_ROOT,
) -> list[IncrementalBatch]:

    if not root.exists():

        logger.warning(
            "Incremental directory does not exist: %s",
            root,
        )

        return []

    batches = []

    for path in root.iterdir():

        if not path.is_dir():
            continue

        if not BATCH_PATTERN.match(
            path.name
        ):
            continue

        business_date, sequence = (
            parse_batch_name(
                path.name
            )
        )

        batches.append(
            IncrementalBatch(
                batch_id=path.name,
                path=path,
                business_date=business_date,
                sequence=sequence,
            )
        )

    batches.sort(
        key=lambda item: (
            item.business_date,
            item.sequence,
        )
    )

    return batches


# ============================================================
# SUCCESSFUL SOURCE BATCHES
# ============================================================

def get_successful_source_batches() -> set[str]:

    with engine.connect() as connection:

        result = connection.execute(
            text(
                """
                SELECT source_batch_id

                FROM control.etl_batch

                WHERE status = 'SUCCESS'
                  AND source_batch_id IS NOT NULL
                """
            )
        )

        return {
            row[0]
            for row in result
            if row[0]
        }


# ============================================================
# PENDING BATCHES
# ============================================================

def get_pending_batches(
    root: Path = INCREMENTAL_ROOT,
) -> list[IncrementalBatch]:

    discovered = discover_batches(
        root
    )

    successful = (
        get_successful_source_batches()
    )

    return [
        batch
        for batch
        in discovered
        if batch.batch_id
        not in successful
    ]


# ============================================================
# GET SPECIFIC BATCH
# ============================================================

def get_batch(
    batch_name: str,
    root: Path = INCREMENTAL_ROOT,
) -> IncrementalBatch:

    batch_name = (
        batch_name
        .strip()
        .upper()
    )

    batch_path = (
        root
        / batch_name
    )

    business_date, sequence = (
        parse_batch_name(
            batch_name
        )
    )

    validate_batch_directory(
        batch_path
    )

    return IncrementalBatch(
        batch_id=batch_name,
        path=batch_path,
        business_date=business_date,
        sequence=sequence,
    )