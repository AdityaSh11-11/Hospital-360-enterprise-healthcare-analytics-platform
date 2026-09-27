from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from database.connection import engine
from utils.logger import get_logger


logger = get_logger(__name__)


# ============================================================
# CONFIGURATION
# ============================================================

SOURCE_BATCH_ID = "BATCH-20260924-003"

BATCH_DIR = (
    Path("data")
    / "incremental"
    / SOURCE_BATCH_ID
)

BACKUP_ROOT = (
    Path("data")
    / "recovery_backups"
)


# ============================================================
# FILES
# ============================================================

PATIENTS_FILE = (
    BATCH_DIR
    / "patients.csv"
)

ADMISSIONS_FILE = (
    BATCH_DIR
    / "admissions.csv"
)

BILLING_FILE = (
    BATCH_DIR
    / "billing.csv"
)

CLAIMS_FILE = (
    BATCH_DIR
    / "claims.csv"
)

LABS_FILE = (
    BATCH_DIR
    / "labs.csv"
)

MEDICATIONS_FILE = (
    BATCH_DIR
    / "medication_events.csv"
)


# ============================================================
# HELPERS
# ============================================================

def heading(
    text_value: str,
) -> None:

    print()
    print("=" * 90)
    print(text_value)
    print("=" * 90)


def load_csv(
    path: Path,
) -> pd.DataFrame:

    if not path.exists():

        raise FileNotFoundError(
            f"Required file not found: {path}"
        )

    return pd.read_csv(
        path
    )


def normalize_id(
    value,
) -> str:

    if pd.isna(value):
        return ""

    return str(
        value
    ).strip()


# ============================================================
# BACKUP
# ============================================================

def create_backup() -> Path:

    if not BATCH_DIR.exists():

        raise FileNotFoundError(
            f"Batch directory not found: {BATCH_DIR}"
        )

    BACKUP_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_directory = (
        BACKUP_ROOT
        / f"{SOURCE_BATCH_ID}_{timestamp}"
    )

    shutil.copytree(
        BATCH_DIR,
        backup_directory,
    )

    print(
        f"[OK] Backup created: "
        f"{backup_directory}"
    )

    return backup_directory


# ============================================================
# WAREHOUSE PATIENTS
# ============================================================

def load_warehouse_patients() -> pd.DataFrame:

    query = text(
        """
        SELECT
            patient_id,
            registration_date

        FROM warehouse.dim_patient

        WHERE is_active = TRUE
           OR is_active IS NULL

        ORDER BY patient_id
        """
    )

    with engine.connect() as connection:

        result = connection.execute(
            query
        )

        rows = result.fetchall()

        columns = list(
            result.keys()
        )

    return pd.DataFrame(
        rows,
        columns=columns,
    )


# ============================================================
# IDENTIFY INVALID ADMISSIONS
# ============================================================

def find_invalid_admissions(
    admissions: pd.DataFrame,
    warehouse_patients: pd.DataFrame,
    current_batch_patients: pd.DataFrame,
) -> pd.DataFrame:

    warehouse_ids = set(
        warehouse_patients[
            "patient_id"
        ]
        .astype(str)
        .str.strip()
    )

    current_ids = set(
        current_batch_patients[
            "patient_id"
        ]
        .astype(str)
        .str.strip()
    )

    valid_ids = (
        warehouse_ids
        |
        current_ids
    )

    invalid = admissions[
        ~admissions[
            "patient_id"
        ]
        .astype(str)
        .str.strip()
        .isin(
            valid_ids
        )
    ].copy()

    return invalid


# ============================================================
# SELECT REPLACEMENT PATIENT
# ============================================================

def choose_replacement_patient(
    admission_row: pd.Series,
    warehouse_patients: pd.DataFrame,
    current_batch_patients: pd.DataFrame,
) -> str:

    admission_timestamp = pd.to_datetime(
        admission_row[
            "admission_timestamp"
        ],
        errors="raise",
    )

    frames = []

    # --------------------------------------------------------
    # WAREHOUSE PATIENTS
    # --------------------------------------------------------

    warehouse = (
        warehouse_patients
        .copy()
    )

    warehouse[
        "registration_date"
    ] = pd.to_datetime(
        warehouse[
            "registration_date"
        ],
        errors="coerce",
    )

    warehouse = warehouse[
        warehouse[
            "registration_date"
        ].notna()
        &
        (
            warehouse[
                "registration_date"
            ]
            <= admission_timestamp
        )
    ].copy()

    frames.append(
        warehouse[
            [
                "patient_id",
                "registration_date",
            ]
        ]
    )

    # --------------------------------------------------------
    # CURRENT BATCH PATIENTS
    # --------------------------------------------------------

    current = (
        current_batch_patients
        .copy()
    )

    current[
        "registration_date"
    ] = pd.to_datetime(
        current[
            "registration_date"
        ],
        errors="coerce",
    )

    current = current[
        current[
            "registration_date"
        ].notna()
        &
        (
            current[
                "registration_date"
            ]
            <= admission_timestamp
        )
    ].copy()

    frames.append(
        current[
            [
                "patient_id",
                "registration_date",
            ]
        ]
    )

    eligible = pd.concat(
        frames,
        ignore_index=True,
    )

    eligible = (
        eligible
        .drop_duplicates(
            subset=[
                "patient_id"
            ],
            keep="last",
        )
        .sort_values(
            by=[
                "patient_id"
            ]
        )
        .reset_index(
            drop=True
        )
    )

    if eligible.empty:

        raise RuntimeError(
            (
                "No chronology-valid replacement "
                "patient is available for "
                f"admission "
                f"{admission_row['admission_id']}."
            )
        )

    # Deterministic mapping.
    #
    # We intentionally choose the first eligible business key
    # instead of a random patient so recovery is reproducible.

    return str(
        eligible.iloc[0][
            "patient_id"
        ]
    )


# ============================================================
# SYNCHRONIZE DEPENDENT DATASETS
# ============================================================

def synchronize_patient_reference(
    *,
    admission_id: str,
    old_patient_id: str,
    new_patient_id: str,
    admissions: pd.DataFrame,
    billing: pd.DataFrame,
    claims: pd.DataFrame,
    labs: pd.DataFrame,
    medications: pd.DataFrame,
) -> dict[str, int]:

    counts = {
        "admissions": 0,
        "billing": 0,
        "claims": 0,
        "labs": 0,
        "medication_events": 0,
    }

    # --------------------------------------------------------
    # ADMISSION
    # --------------------------------------------------------

    admission_mask = (
        admissions[
            "admission_id"
        ].astype(str)
        ==
        admission_id
    )

    counts[
        "admissions"
    ] = int(
        admission_mask.sum()
    )

    admissions.loc[
        admission_mask,
        "patient_id",
    ] = new_patient_id

    # --------------------------------------------------------
    # BILLING
    # --------------------------------------------------------

    bill_mask = (
        billing[
            "admission_id"
        ].astype(str)
        ==
        admission_id
    )

    affected_bill_ids = set(
        billing.loc[
            bill_mask,
            "bill_id",
        ]
        .astype(str)
        .tolist()
    )

    counts[
        "billing"
    ] = int(
        bill_mask.sum()
    )

    billing.loc[
        bill_mask,
        "patient_id",
    ] = new_patient_id

    # --------------------------------------------------------
    # CLAIMS
    #
    # Claims are linked to billing, so synchronize any claim
    # belonging to an affected bill.
    # --------------------------------------------------------

    if affected_bill_ids:

        claim_mask = (
            claims[
                "bill_id"
            ]
            .astype(str)
            .isin(
                affected_bill_ids
            )
        )

    else:

        claim_mask = pd.Series(
            False,
            index=claims.index,
        )

    counts[
        "claims"
    ] = int(
        claim_mask.sum()
    )

    claims.loc[
        claim_mask,
        "patient_id",
    ] = new_patient_id

    # --------------------------------------------------------
    # LABS
    # --------------------------------------------------------

    lab_mask = (
        labs[
            "admission_id"
        ].astype(str)
        ==
        admission_id
    )

    counts[
        "labs"
    ] = int(
        lab_mask.sum()
    )

    labs.loc[
        lab_mask,
        "patient_id",
    ] = new_patient_id

    # --------------------------------------------------------
    # MEDICATION EVENTS
    # --------------------------------------------------------

    medication_mask = (
        medications[
            "admission_id"
        ].astype(str)
        ==
        admission_id
    )

    counts[
        "medication_events"
    ] = int(
        medication_mask.sum()
    )

    medications.loc[
        medication_mask,
        "patient_id",
    ] = new_patient_id

    return counts


# ============================================================
# VERIFY SOURCE AFTER REPAIR
# ============================================================

def verify_repaired_source(
    admissions: pd.DataFrame,
    billing: pd.DataFrame,
    claims: pd.DataFrame,
    labs: pd.DataFrame,
    medications: pd.DataFrame,
    warehouse_patients: pd.DataFrame,
    current_batch_patients: pd.DataFrame,
) -> None:

    valid_patient_ids = set(
        warehouse_patients[
            "patient_id"
        ]
        .astype(str)
        .str.strip()
    )

    valid_patient_ids.update(
        current_batch_patients[
            "patient_id"
        ]
        .astype(str)
        .str.strip()
    )

    problems = []

    # --------------------------------------------------------
    # PATIENT REFERENCES
    # --------------------------------------------------------

    datasets = {
        "admissions":
            admissions,

        "billing":
            billing,

        "claims":
            claims,

        "labs":
            labs,

        "medication_events":
            medications,
    }

    for (
        dataset_name,
        dataframe,
    ) in datasets.items():

        if dataframe.empty:
            continue

        if "patient_id" not in dataframe.columns:
            continue

        invalid = dataframe[
            ~dataframe[
                "patient_id"
            ]
            .astype(str)
            .str.strip()
            .isin(
                valid_patient_ids
            )
        ]

        if not invalid.empty:

            problems.append(
                (
                    f"{dataset_name}: "
                    f"{len(invalid):,} invalid "
                    "patient reference(s)"
                )
            )

    # --------------------------------------------------------
    # BILLING → ADMISSION
    # --------------------------------------------------------

    admission_ids = set(
        admissions[
            "admission_id"
        ]
        .astype(str)
    )

    invalid_billing = billing[
        ~billing[
            "admission_id"
        ]
        .astype(str)
        .isin(
            admission_ids
        )
    ]

    if not invalid_billing.empty:

        problems.append(
            (
                "billing: "
                f"{len(invalid_billing):,} "
                "missing admission reference(s)"
            )
        )

    # --------------------------------------------------------
    # LAB → ADMISSION
    # --------------------------------------------------------

    invalid_labs = labs[
        ~labs[
            "admission_id"
        ]
        .astype(str)
        .isin(
            admission_ids
        )
    ]

    if not invalid_labs.empty:

        problems.append(
            (
                "labs: "
                f"{len(invalid_labs):,} "
                "missing admission reference(s)"
            )
        )

    # --------------------------------------------------------
    # MEDICATION → ADMISSION
    # --------------------------------------------------------

    invalid_medications = medications[
        ~medications[
            "admission_id"
        ]
        .astype(str)
        .isin(
            admission_ids
        )
    ]

    if not invalid_medications.empty:

        problems.append(
            (
                "medication_events: "
                f"{len(invalid_medications):,} "
                "missing admission reference(s)"
            )
        )

    if problems:

        raise RuntimeError(
            "Repair verification failed:\n"
            + "\n".join(
                problems
            )
        )


# ============================================================
# DATABASE STATUS RECOVERY
# ============================================================

def mark_previous_success_for_recovery() -> None:

    with engine.begin() as connection:

        rows = connection.execute(
            text(
                """
                SELECT
                    batch_id,
                    status

                FROM control.etl_batch

                WHERE source_batch_id =
                    :source_batch_id

                ORDER BY batch_id
                """
            ),
            {
                "source_batch_id":
                    SOURCE_BATCH_ID
            },
        ).fetchall()

        if not rows:

            raise RuntimeError(
                (
                    "No ETL control record found for "
                    f"{SOURCE_BATCH_ID}."
                )
            )

        success_rows = [
            row
            for row in rows
            if row.status == "SUCCESS"
        ]

        if len(success_rows) != 1:

            raise RuntimeError(
                (
                    "Expected exactly one SUCCESS "
                    f"ETL record for "
                    f"{SOURCE_BATCH_ID}, found "
                    f"{len(success_rows)}."
                )
            )

        failed_batch_id = (
            success_rows[0].batch_id
        )

        connection.execute(
            text(
                """
                UPDATE control.etl_batch

                SET
                    status =
                        'RECONCILIATION_FAILED',

                    error_message =
                        :error_message

                WHERE batch_id =
                    :batch_id
                """
            ),
            {
                "batch_id":
                    failed_batch_id,

                "error_message":
                    (
                        "Historical recovery: source "
                        "batch referenced a patient "
                        "registered in a future source "
                        "batch. Source repaired and "
                        "scheduled for idempotent retry."
                    ),
            },
        )

    print(
        (
            "[OK] ETL control batch "
            f"{failed_batch_id} changed from "
            "SUCCESS to RECONCILIATION_FAILED."
        )
    )


# ============================================================
# MAIN RECOVERY
# ============================================================

def main() -> None:

    heading(
        "HOSPITAL 360 — BATCH 003 CONTROLLED RECOVERY"
    )

    print(
        f"Source batch: {SOURCE_BATCH_ID}"
    )

    # ========================================================
    # LOAD SOURCE FILES
    # ========================================================

    patients = load_csv(
        PATIENTS_FILE
    )

    admissions = load_csv(
        ADMISSIONS_FILE
    )

    billing = load_csv(
        BILLING_FILE
    )

    claims = load_csv(
        CLAIMS_FILE
    )

    labs = load_csv(
        LABS_FILE
    )

    medications = load_csv(
        MEDICATIONS_FILE
    )

    warehouse_patients = (
        load_warehouse_patients()
    )

    # ========================================================
    # FIND CORRUPTED REFERENCES
    # ========================================================

    invalid_admissions = (
        find_invalid_admissions(
            admissions=admissions,
            warehouse_patients=(
                warehouse_patients
            ),
            current_batch_patients=(
                patients
            ),
        )
    )

    heading(
        "INVALID ADMISSION REFERENCES"
    )

    if invalid_admissions.empty:

        print(
            "[INFO] No invalid admission patient "
            "references were found."
        )

        print(
            "No source files were changed."
        )

        return

    print(
        invalid_admissions[
            [
                "admission_id",
                "patient_id",
                "admission_timestamp",
            ]
        ].to_string(
            index=False
        )
    )

    print()
    print(
        "Invalid admissions:",
        len(
            invalid_admissions
        ),
    )

    # ========================================================
    # BACKUP BEFORE ANY WRITE
    # ========================================================

    heading(
        "BACKUP"
    )

    backup_directory = (
        create_backup()
    )

    # ========================================================
    # REPAIR
    # ========================================================

    heading(
        "SOURCE REPAIR"
    )

    recovery_rows = []

    for _, row in (
        invalid_admissions.iterrows()
    ):

        admission_id = normalize_id(
            row[
                "admission_id"
            ]
        )

        old_patient_id = normalize_id(
            row[
                "patient_id"
            ]
        )

        new_patient_id = (
            choose_replacement_patient(
                admission_row=row,
                warehouse_patients=(
                    warehouse_patients
                ),
                current_batch_patients=(
                    patients
                ),
            )
        )

        counts = (
            synchronize_patient_reference(
                admission_id=admission_id,
                old_patient_id=old_patient_id,
                new_patient_id=new_patient_id,
                admissions=admissions,
                billing=billing,
                claims=claims,
                labs=labs,
                medications=medications,
            )
        )

        recovery_rows.append(
            {
                "admission_id":
                    admission_id,

                "old_patient_id":
                    old_patient_id,

                "new_patient_id":
                    new_patient_id,

                **counts,
            }
        )

        print(
            (
                f"[REPAIR] {admission_id} | "
                f"{old_patient_id} -> "
                f"{new_patient_id}"
            )
        )

        print(
            (
                "         "
                f"admissions={counts['admissions']} | "
                f"billing={counts['billing']} | "
                f"claims={counts['claims']} | "
                f"labs={counts['labs']} | "
                "medication_events="
                f"{counts['medication_events']}"
            )
        )

    # ========================================================
    # VERIFY IN MEMORY BEFORE WRITING
    # ========================================================

    heading(
        "VERIFY REPAIRED SOURCE"
    )

    verify_repaired_source(
        admissions=admissions,
        billing=billing,
        claims=claims,
        labs=labs,
        medications=medications,
        warehouse_patients=(
            warehouse_patients
        ),
        current_batch_patients=(
            patients
        ),
    )

    print(
        "[PASS] Repaired source references are valid."
    )

    # ========================================================
    # WRITE REPAIRED FILES
    # ========================================================

    heading(
        "WRITE REPAIRED SOURCE"
    )

    admissions.to_csv(
        ADMISSIONS_FILE,
        index=False,
    )

    billing.to_csv(
        BILLING_FILE,
        index=False,
    )

    claims.to_csv(
        CLAIMS_FILE,
        index=False,
    )

    labs.to_csv(
        LABS_FILE,
        index=False,
    )

    medications.to_csv(
        MEDICATIONS_FILE,
        index=False,
    )

    recovery_log = pd.DataFrame(
        recovery_rows
    )

    recovery_log_path = (
        BATCH_DIR
        / "recovery_log.csv"
    )

    recovery_log.to_csv(
        recovery_log_path,
        index=False,
    )

    print(
        "[OK] Repaired source files written."
    )

    print(
        f"[OK] Recovery log: "
        f"{recovery_log_path}"
    )

    # ========================================================
    # CHANGE FALSE SUCCESS STATUS
    # ========================================================

    heading(
        "ETL CONTROL RECOVERY"
    )

    mark_previous_success_for_recovery()

    # ========================================================
    # COMPLETE
    # ========================================================

    heading(
        "RECOVERY COMPLETE"
    )

    print(
        f"Backup directory : {backup_directory}"
    )

    print(
        f"Repaired batch   : {BATCH_DIR}"
    )

    print(
        (
            "Database facts were NOT deleted or "
            "rewritten by this script."
        )
    )

    print(
        (
            "Existing valid fact rows remain intact. "
            "The next ETL retry can use ON CONFLICT "
            "DO NOTHING and insert only the previously "
            "missing chain."
        )
    )


if __name__ == "__main__":
    main()