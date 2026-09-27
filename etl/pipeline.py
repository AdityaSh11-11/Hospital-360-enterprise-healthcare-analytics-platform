from __future__ import annotations

import time
from pathlib import Path

from database.connection import engine

from etl.extract import (
    extract_initial,
    extract_incremental,
)

from etl.load import (
    complete_etl_batch,
    create_etl_batch,
    load_admissions,
    load_billing,
    load_claims,
    load_doctors,
    load_labs,
    load_medication_events,
    load_medication_master,
    load_patients,
    load_rejections,
    load_staging,
    log_quality,
    source_already_loaded,
)

from etl.reconciliation import (
    format_reconciliation,
    reconcile_business_keys,
)

from etl.referential import (
    format_referential_errors,
    validate_references,
)

from etl.transform import transform_all
from etl.validate import ValidationResult, validate_all
from utils.logger import get_logger


logger = get_logger(__name__)


# ============================================================
# EXTRACTION
# ============================================================

def extract_source(
    source_type: str,
    source_path: Path,
):

    source_type = (
        source_type
        .strip()
        .upper()
    )

    if source_type == "INITIAL":

        return extract_initial(
            source_path
        )

    if source_type == "INCREMENTAL":

        return extract_incremental(
            source_path
        )

    raise ValueError(
        f"Unsupported ETL source type: {source_type}"
    )


# ============================================================
# RECORD COUNTS
# ============================================================

def total_records(
    datasets,
) -> int:

    return sum(
        len(dataframe)
        for dataframe
        in datasets.values()
    )


# ============================================================
# VALIDATION COUNTS
# ============================================================

def validation_issue_count(
    validation_result: ValidationResult,
) -> int:

    return len(
        validation_result.issues
    )


def validation_valid_count(
    validation_result: ValidationResult,
) -> int:

    return total_records(
        validation_result.valid
    )


# ============================================================
# DATASET-LEVEL VALIDATION COUNTS
# ============================================================

def dataset_validation_counts(
    *,
    raw_datasets,
    validation_result: ValidationResult,
) -> dict[str, dict[str, int]]:
    """
    Return checked/failed counts for every dataset.

    ValidationResult.issues is one flat list, so failed rows
    are grouped by issue.dataset.
    """

    failed_by_dataset: dict[str, int] = {
        dataset_name: 0
        for dataset_name
        in raw_datasets
    }

    for issue in validation_result.issues:

        failed_by_dataset[
            issue.dataset
        ] = (
            failed_by_dataset.get(
                issue.dataset,
                0,
            )
            + 1
        )

    counts = {}

    for (
        dataset_name,
        dataframe,
    ) in raw_datasets.items():

        counts[
            dataset_name
        ] = {
            "checked":
                len(dataframe),

            "failed":
                failed_by_dataset.get(
                    dataset_name,
                    0,
                ),
        }

    return counts


# ============================================================
# STANDARD DATA QUALITY LOGGING
# ============================================================

def record_validation_results(
    *,
    connection,
    batch_id: int,
    raw_datasets,
    validation_result: ValidationResult,
) -> None:

    counts = dataset_validation_counts(
        raw_datasets=raw_datasets,
        validation_result=validation_result,
    )

    for (
        dataset_name,
        dataset_counts,
    ) in counts.items():

        log_quality(
            connection=connection,
            batch_id=batch_id,
            dataset_name=dataset_name,
            records_checked=(
                dataset_counts[
                    "checked"
                ]
            ),
            failed_records=(
                dataset_counts[
                    "failed"
                ]
            ),
        )


# ============================================================
# DIMENSION LOAD
# ============================================================

def load_dimensions(
    connection,
    datasets,
) -> None:

    patients = datasets.get(
        "patients"
    )

    doctors = datasets.get(
        "doctors"
    )

    medication_master = datasets.get(
        "medication_master"
    )

    if patients is not None:

        load_patients(
            connection,
            patients,
        )

    if doctors is not None:

        load_doctors(
            connection,
            doctors,
        )

    if medication_master is not None:

        load_medication_master(
            connection,
            medication_master,
        )


# ============================================================
# FACT LOAD
# ============================================================

def load_facts(
    connection,
    datasets,
) -> None:

    admissions = datasets.get(
        "admissions"
    )

    billing = datasets.get(
        "billing"
    )

    claims = datasets.get(
        "claims"
    )

    labs = datasets.get(
        "labs"
    )

    medication_events = datasets.get(
        "medication_events"
    )

    if admissions is not None:

        load_admissions(
            connection,
            admissions,
        )

    if billing is not None:

        load_billing(
            connection,
            billing,
        )

    if claims is not None:

        load_claims(
            connection,
            claims,
        )

    if labs is not None:

        load_labs(
            connection,
            labs,
        )

    if medication_events is not None:

        load_medication_events(
            connection,
            medication_events,
        )


# ============================================================
# CREATE DURABLE RUNNING BATCH
# ============================================================

def create_running_batch(
    *,
    source_type: str,
    source_path: Path,
    source_batch_id: str,
    business_date,
) -> int:
    """
    Create RUNNING audit record in its own committed
    transaction.

    If warehouse loading later fails, this control record
    remains available and can be updated to FAILED.
    """

    with engine.begin() as connection:

        batch_id = create_etl_batch(
            connection=connection,
            batch_name=source_batch_id,
            batch_type=source_type,
            source_batch_id=source_batch_id,
            source_path=str(
                source_path
            ),
            business_date=business_date,
        )

    logger.info(
        (
            "Created durable RUNNING ETL "
            "batch_id=%s for source=%s"
        ),
        batch_id,
        source_batch_id,
    )

    return batch_id


# ============================================================
# MARK SUCCESS
# ============================================================

def mark_batch_success(
    *,
    batch_id: int,
    received: int,
    inserted: int,
    rejected: int,
    duration_seconds: float,
) -> None:

    with engine.begin() as connection:

        complete_etl_batch(
            connection=connection,
            batch_id=batch_id,
            status="SUCCESS",
            received=received,
            inserted=inserted,
            rejected=rejected,
            duration_seconds=duration_seconds,
            error_message=None,
        )


# ============================================================
# MARK FAILED
# ============================================================

def mark_batch_failed(
    *,
    batch_id: int,
    received: int,
    rejected: int,
    duration_seconds: float,
    error_message: str,
) -> None:

    safe_error = str(
        error_message
    )

    if len(safe_error) > 4000:

        safe_error = (
            safe_error[:3997]
            + "..."
        )

    with engine.begin() as connection:

        complete_etl_batch(
            connection=connection,
            batch_id=batch_id,
            status="FAILED",
            received=received,
            inserted=0,
            rejected=rejected,
            duration_seconds=duration_seconds,
            error_message=safe_error,
        )


# ============================================================
# MAIN ETL PIPELINE
# ============================================================

def run_etl(
    source_type: str,
    source_path,
    source_batch_id: str,
    business_date=None,
):

    started_at = time.perf_counter()

    source_type = (
        source_type
        .strip()
        .upper()
    )

    source_path = Path(
        source_path
    )

    batch_id = None

    received_count = 0

    rejected_count = 0

    valid_count = 0

    logger.info(
        (
            "Starting ETL | "
            "source=%s | "
            "type=%s"
        ),
        source_batch_id,
        source_type,
    )

    # ========================================================
    # STEP 0 — EXTRACT
    # ========================================================

    raw_datasets = extract_source(
        source_type=source_type,
        source_path=source_path,
    )

    received_count = total_records(
        raw_datasets
    )

    logger.info(
        "Extracted %s source records.",
        f"{received_count:,}",
    )

    # ========================================================
    # IDEMPOTENCY CHECK
    # ========================================================

    with engine.connect() as connection:

        if source_already_loaded(
            connection,
            source_batch_id,
        ):

            logger.warning(
                (
                    "Source batch %s already has "
                    "a successful ETL load. "
                    "Skipping."
                ),
                source_batch_id,
            )

            return {
                "status":
                    "SKIPPED",

                "source_batch_id":
                    source_batch_id,

                "reason":
                    "Source batch already loaded.",
            }

    # ========================================================
    # DURABLE RUNNING AUDIT RECORD
    # ========================================================

    batch_id = create_running_batch(
        source_type=source_type,
        source_path=source_path,
        source_batch_id=source_batch_id,
        business_date=business_date,
    )

    try:

        # ====================================================
        # MAIN WAREHOUSE TRANSACTION
        # ====================================================

        with engine.begin() as connection:

            # ================================================
            # STEP 1 — STAGING
            # ================================================

            logger.info(
                "STEP 1/8 — Loading staging tables."
            )

            load_staging(
                connection=connection,
                datasets=raw_datasets,
                batch_id=batch_id,
            )

            # ================================================
            # STEP 2 — STANDARD VALIDATION
            # ================================================

            logger.info(
                (
                    "STEP 2/8 — Running standard "
                    "data quality validation."
                )
            )

            validation_result = validate_all(
                raw_datasets
            )

            rejected_count = (
                validation_issue_count(
                    validation_result
                )
            )

            valid_count = (
                validation_valid_count(
                    validation_result
                )
            )

            cleaned_datasets = (
                validation_result.valid
            )

            logger.info(
                (
                    "Validation complete | "
                    "valid=%s | "
                    "rejected=%s"
                ),
                f"{valid_count:,}",
                f"{rejected_count:,}",
            )

            # ================================================
            # STEP 3 — DQ LOG + REJECTIONS
            # ================================================

            logger.info(
                (
                    "STEP 3/8 — Recording data "
                    "quality results."
                )
            )

            record_validation_results(
                connection=connection,
                batch_id=batch_id,
                raw_datasets=raw_datasets,
                validation_result=(
                    validation_result
                ),
            )

            load_rejections(
                connection=connection,
                batch_id=batch_id,
                issues=(
                    validation_result.issues
                ),
            )

            if rejected_count > 0:

                logger.warning(
                    (
                        "Standard validation rejected "
                        "%s record(s)."
                    ),
                    f"{rejected_count:,}",
                )

            # ================================================
            # STEP 4 — TRANSFORM
            # ================================================

            logger.info(
                (
                    "STEP 4/8 — Transforming "
                    "validated datasets."
                )
            )

            transformed = transform_all(
                cleaned_datasets
            )

            # ================================================
            # STEP 5 — REFERENTIAL INTEGRITY
            # ================================================

            logger.info(
                (
                    "STEP 5/8 — Running "
                    "referential integrity validation."
                )
            )

            referential_result = (
                validate_references(
                    connection=connection,
                    datasets=transformed,
                    business_date=business_date,
                )
            )

            if not referential_result.passed:

                referential_message = (
                    format_referential_errors(
                        referential_result,
                        max_examples=20,
                    )
                )

                logger.error(
                    "%s",
                    referential_message,
                )

                raise RuntimeError(
                    referential_message
                )

            logger.info(
                (
                    "Referential integrity "
                    "validation passed."
                )
            )

            # ================================================
            # STEP 6 — DIMENSIONS
            # ================================================

            logger.info(
                "STEP 6/8 — Loading dimensions."
            )

            load_dimensions(
                connection=connection,
                datasets=transformed,
            )

            # ================================================
            # STEP 7 — FACTS
            # ================================================

            logger.info(
                "STEP 7/8 — Loading facts."
            )

            load_facts(
                connection=connection,
                datasets=transformed,
            )

            # ================================================
            # STEP 8 — BUSINESS-KEY RECONCILIATION
            #
            # Same transaction means PostgreSQL can see the
            # rows inserted by this ETL attempt before commit.
            #
            # Existing rows from a previous partial attempt
            # also count as present.
            # ================================================

            logger.info(
                (
                    "STEP 8/8 — Running "
                    "business-key reconciliation."
                )
            )

            reconciliation_result = (
                reconcile_business_keys(
                    connection=connection,
                    datasets=transformed,
                )
            )

            reconciliation_message = (
                format_reconciliation(
                    reconciliation_result,
                    max_missing_examples=20,
                )
            )

            logger.info(
                "\n%s",
                reconciliation_message,
            )

            if not reconciliation_result.passed:

                raise RuntimeError(
                    reconciliation_message
                )

            logger.info(
                (
                    "Business-key reconciliation "
                    "passed."
                )
            )

        # ====================================================
        # MAIN TRANSACTION COMMITTED
        # ====================================================

        duration_seconds = round(
            time.perf_counter()
            - started_at,
            2,
        )

        # ====================================================
        # SUCCESS AUDIT
        # ====================================================

        mark_batch_success(
            batch_id=batch_id,
            received=received_count,
            inserted=valid_count,
            rejected=rejected_count,
            duration_seconds=duration_seconds,
        )

        logger.info(
            (
                "ETL SUCCESS | "
                "batch_id=%s | "
                "source=%s | "
                "received=%s | "
                "valid=%s | "
                "rejected=%s | "
                "duration=%ss"
            ),
            batch_id,
            source_batch_id,
            f"{received_count:,}",
            f"{valid_count:,}",
            f"{rejected_count:,}",
            duration_seconds,
        )

        return {
            "status":
                "SUCCESS",

            "batch_id":
                batch_id,

            "source_batch_id":
                source_batch_id,

            "received":
                received_count,

            "valid":
                valid_count,

            "rejected":
                rejected_count,

            "duration_seconds":
                duration_seconds,
        }

    except Exception as exc:

        # ====================================================
        # MAIN TRANSACTION ROLLED BACK
        # ====================================================

        duration_seconds = round(
            time.perf_counter()
            - started_at,
            2,
        )

        logger.exception(
            (
                "ETL FAILED | "
                "batch_id=%s | "
                "source=%s"
            ),
            batch_id,
            source_batch_id,
        )

        # ====================================================
        # DURABLE FAILED AUDIT
        # ====================================================

        try:

            mark_batch_failed(
                batch_id=batch_id,
                received=received_count,
                rejected=rejected_count,
                duration_seconds=duration_seconds,
                error_message=str(
                    exc
                ),
            )

            logger.info(
                (
                    "ETL batch_id=%s permanently "
                    "recorded as FAILED."
                ),
                batch_id,
            )

        except Exception:

            logger.exception(
                (
                    "CRITICAL: ETL failed and the "
                    "FAILED audit status could not "
                    "be persisted for batch_id=%s."
                ),
                batch_id,
            )

        raise