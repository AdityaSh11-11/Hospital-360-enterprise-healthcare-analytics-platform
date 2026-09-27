import random
import time
from pathlib import Path

import pandas as pd

from generator.admissions import generate_admissions
from generator.batch_manager import (
    create_batch_directory,
    next_batch_id,
    save_manifest,
)
from generator.billing import generate_billing
from generator.claims import generate_claims
from generator.config import CONFIG
from generator.helpers import set_random_seed
from generator.id_manager import max_id_from_files
from generator.labs import generate_labs
from generator.medications import generate_medications
from generator.patients import generate_patients
from utils.logger import get_logger


# ============================================================
# LOGGER
# ============================================================

logger = get_logger(__name__)


# ============================================================
# DATA DIRECTORIES
# ============================================================

RAW = Path("data/raw")

INCREMENTAL = CONFIG.incremental_directory


# ============================================================
# INCREMENTAL FILE DISCOVERY
# ============================================================

def incremental_files(
    filename: str,
) -> list[Path]:
    """
    Return every existing incremental version of a dataset.

    IMPORTANT:
    This function intentionally does NOT apply business-date
    filtering.

    It is used for global ID discovery where every existing
    source file must be considered to prevent duplicate IDs.
    """

    if not INCREMENTAL.exists():
        return []

    return sorted(
        INCREMENTAL.glob(
            f"BATCH-*/{filename}"
        )
    )


# ============================================================
# BATCH BUSINESS DATE
# ============================================================

def batch_business_date(
    batch_directory: Path,
) -> pd.Timestamp | None:
    """
    Extract the business date from a directory such as:

        BATCH-20260924-003

    Returns a normalized pandas Timestamp.
    """

    name = batch_directory.name

    parts = name.split("-")

    if len(parts) != 3:
        return None

    if parts[0] != "BATCH":
        return None

    date_text = parts[1]

    if len(date_text) != 8:
        return None

    try:
        return pd.Timestamp(
            date_text
        ).normalize()

    except Exception:
        return None


# ============================================================
# ELIGIBLE PATIENT FILES
# ============================================================

def eligible_incremental_patient_files(
    business_day: pd.Timestamp,
) -> list[Path]:
    """
    Return incremental patient files that are eligible for
    admissions on the requested business date.

    Rule:

        source batch date <= target business date

    Future source batches are never included.

    Example:

        generating 2026-09-24

        allowed:
            BATCH-20260924-001
            BATCH-20260924-002

        blocked:
            BATCH-20260925-001
            BATCH-20260926-001
    """

    if not INCREMENTAL.exists():
        return []

    business_day = pd.Timestamp(
        business_day
    ).normalize()

    eligible = []

    for path in incremental_files(
        "patients.csv"
    ):

        source_day = batch_business_date(
            path.parent
        )

        if source_day is None:

            logger.warning(
                (
                    "Ignoring patient source with "
                    "unrecognized batch directory: %s"
                ),
                path.parent,
            )

            continue

        if source_day <= business_day:

            eligible.append(
                path
            )

    return sorted(
        eligible
    )


# ============================================================
# PATIENT ELIGIBILITY
# ============================================================

def filter_patients_by_registration_date(
    patients: pd.DataFrame,
    business_day: pd.Timestamp,
) -> pd.DataFrame:
    """
    Keep only patients registered on or before business_day.

    This is the second temporal safety layer.

    Even if a patient file belongs to an eligible source batch,
    the patient record itself must still satisfy:

        registration_date <= business date
    """

    if patients.empty:
        return patients.copy()

    if "registration_date" not in patients.columns:

        raise KeyError(
            "Patient dataset is missing "
            "'registration_date'."
        )

    filtered = patients.copy()

    registration_dates = pd.to_datetime(
        filtered["registration_date"],
        errors="coerce",
    )

    invalid_dates = registration_dates.isna()

    if invalid_dates.any():

        invalid_count = int(
            invalid_dates.sum()
        )

        logger.warning(
            (
                "Excluding %s patient record(s) "
                "with invalid registration_date."
            ),
            f"{invalid_count:,}",
        )

    eligible_mask = (
        registration_dates.notna()
        &
        (
            registration_dates.dt.normalize()
            <= business_day.normalize()
        )
    )

    filtered = (
        filtered.loc[
            eligible_mask
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )

    return filtered


# ============================================================
# LOAD ELIGIBLE PATIENTS
# ============================================================

def load_eligible_patients(
    business_day: pd.Timestamp,
) -> pd.DataFrame:
    """
    Build the patient population eligible for admissions on
    business_day.

    Sources:

        1. Phase 2 historical patient master
        2. Incremental patient files whose source business date
           is <= business_day

    Then enforce registration_date <= business_day.

    Future patients are therefore impossible to select.
    """

    business_day = pd.Timestamp(
        business_day
    ).normalize()

    frames = []

    # --------------------------------------------------------
    # INITIAL PATIENT MASTER
    # --------------------------------------------------------

    initial = (
        RAW
        / "patients.csv"
    )

    if initial.exists():

        initial_patients = pd.read_csv(
            initial
        )

        frames.append(
            initial_patients
        )

    # --------------------------------------------------------
    # ELIGIBLE INCREMENTAL PATIENT SOURCES
    # --------------------------------------------------------

    eligible_files = (
        eligible_incremental_patient_files(
            business_day
        )
    )

    for path in eligible_files:

        frame = pd.read_csv(
            path
        )

        frames.append(
            frame
        )

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not frames:

        raise RuntimeError(
            "No patient data exists. "
            "Run Phase 2 initial generation first."
        )

    # --------------------------------------------------------
    # UNION
    # --------------------------------------------------------

    patients = pd.concat(
        frames,
        ignore_index=True,
    )

    # --------------------------------------------------------
    # REMOVE DUPLICATE BUSINESS KEYS
    # --------------------------------------------------------

    patients = (
        patients
        .drop_duplicates(
            subset=[
                "patient_id"
            ],
            keep="last",
        )
        .reset_index(
            drop=True
        )
    )

    # --------------------------------------------------------
    # TEMPORAL ELIGIBILITY
    # --------------------------------------------------------

    patients = (
        filter_patients_by_registration_date(
            patients,
            business_day,
        )
    )

    if patients.empty:

        raise RuntimeError(
            (
                "No patients are eligible for "
                f"business date "
                f"{business_day.date()}."
            )
        )

    logger.info(
        (
            "Eligible historical patients=%s | "
            "business_date=%s | "
            "incremental patient files=%s"
        ),
        f"{len(patients):,}",
        business_day.strftime(
            "%Y-%m-%d"
        ),
        len(eligible_files),
    )

    return patients


# ============================================================
# LOAD DOCTOR MASTER
# ============================================================

def load_doctors() -> pd.DataFrame:
    """
    Doctors remain master data during Phase 3.

    Doctor hiring/resignation/SCD logic will be handled in a
    later phase.
    """

    path = (
        RAW
        / "doctors.csv"
    )

    if not path.exists():

        raise RuntimeError(
            "data/raw/doctors.csv was not found. "
            "Run Phase 2 initial generation first."
        )

    doctors = pd.read_csv(
        path
    )

    if doctors.empty:

        raise RuntimeError(
            "Doctor master is empty."
        )

    return doctors


# ============================================================
# CURRENT MAXIMUM ID
# ============================================================

def current_max_id(
    initial_filename: str,
    incremental_filename: str,
    column: str,
) -> int:
    """
    Determine the maximum numeric identifier across:

        Phase 2 initial data
        +
        EVERY existing Phase 3 batch

    IMPORTANT:

    Unlike patient eligibility, ID generation MUST remain
    global.

    Even future-dated/backdated batch folders must be included
    here so a newly generated batch never reuses an existing
    business ID.
    """

    paths = [
        RAW
        / initial_filename
    ]

    paths.extend(
        incremental_files(
            incremental_filename
        )
    )

    return max_id_from_files(
        paths,
        column,
    )


# ============================================================
# DATASET EXPORT
# ============================================================

def export_batch_dataset(
    dataframe: pd.DataFrame,
    path: Path,
) -> None:
    """
    Export one batch dataframe to CSV.
    """

    dataframe.to_csv(
        path,
        index=False,
    )

    logger.info(
        "Exported %s rows to %s",
        len(dataframe),
        path,
    )


# ============================================================
# TEMPORAL SOURCE VALIDATION
# ============================================================

def validate_generated_patient_references(
    admissions: pd.DataFrame,
    patient_population: pd.DataFrame,
    business_day: pd.Timestamp,
) -> None:
    """
    Final generator-side safety gate.

    Every admission patient must:

        1. exist in the eligible patient population
        2. have registration_date <= admission timestamp
        3. have registration_date <= batch business date

    The batch is not exported if this validation fails.
    """

    if admissions.empty:
        return

    patient_reference = (
        patient_population[
            [
                "patient_id",
                "registration_date",
            ]
        ]
        .drop_duplicates(
            subset=[
                "patient_id"
            ],
            keep="last",
        )
        .copy()
    )

    patient_reference[
        "registration_date"
    ] = pd.to_datetime(
        patient_reference[
            "registration_date"
        ],
        errors="coerce",
    )

    admission_check = admissions[
        [
            "admission_id",
            "patient_id",
            "admission_timestamp",
        ]
    ].copy()

    admission_check[
        "admission_timestamp"
    ] = pd.to_datetime(
        admission_check[
            "admission_timestamp"
        ],
        errors="coerce",
    )

    check = admission_check.merge(
        patient_reference,
        on="patient_id",
        how="left",
        validate="many_to_one",
    )

    missing_patient = (
        check[
            "registration_date"
        ].isna()
    )

    after_admission = (
        check[
            "registration_date"
        ].notna()
        &
        check[
            "admission_timestamp"
        ].notna()
        &
        (
            check[
                "registration_date"
            ]
            >
            check[
                "admission_timestamp"
            ]
        )
    )

    after_business_day = (
        check[
            "registration_date"
        ].notna()
        &
        (
            check[
                "registration_date"
            ].dt.normalize()
            >
            business_day.normalize()
        )
    )

    invalid_mask = (
        missing_patient
        |
        after_admission
        |
        after_business_day
    )

    if invalid_mask.any():

        invalid = check.loc[
            invalid_mask,
            [
                "admission_id",
                "patient_id",
                "admission_timestamp",
                "registration_date",
            ],
        ]

        examples = (
            invalid
            .head(10)
            .to_dict(
                orient="records"
            )
        )

        raise RuntimeError(
            (
                "Generated batch failed patient "
                "temporal integrity validation. "
                f"Invalid admissions="
                f"{len(invalid):,}. "
                f"Examples={examples}"
            )
        )

    logger.info(
        (
            "Patient temporal integrity passed "
            "for %s admission(s)."
        ),
        f"{len(admissions):,}",
    )


# ============================================================
# MAIN INCREMENTAL GENERATOR
# ============================================================

def generate_incremental_batch(
    business_date: str,
    patient_count: int | None = None,
    admission_count: int | None = None,
):
    """
    Generate one incremental hospital batch.

    The batch contains:

        new patients
        admissions
        billing
        insurance claims
        laboratory tests
        medication events

    Existing source data is never overwritten.

    Patient chronology rule:

        admissions on business date D can only reference
        patients registered on or before D.
    """

    start_clock = (
        time.perf_counter()
    )

    # --------------------------------------------------------
    # BUSINESS DATE
    # --------------------------------------------------------

    try:

        business_day = pd.Timestamp(
            business_date
        )

    except Exception as exc:

        raise ValueError(
            "business_date must be a valid "
            "date such as 2026-09-24."
        ) from exc

    business_day = (
        business_day
        .normalize()
    )

    # --------------------------------------------------------
    # BASE RANDOM SEED
    # --------------------------------------------------------

    set_random_seed()

    date_seed = int(
        business_day.strftime(
            "%Y%m%d"
        )
    )

    random.seed(
        CONFIG.random_seed
        + date_seed
    )

    # --------------------------------------------------------
    # COUNTS
    # --------------------------------------------------------

    if patient_count is None:

        patient_count = random.randint(
            CONFIG.incremental_patient_min,
            CONFIG.incremental_patient_max,
        )

    if admission_count is None:

        admission_count = random.randint(
            CONFIG.incremental_admission_min,
            CONFIG.incremental_admission_max,
        )

    if patient_count < 0:

        raise ValueError(
            "patient_count cannot be negative."
        )

    if admission_count <= 0:

        raise ValueError(
            "admission_count must be greater than zero."
        )

    # --------------------------------------------------------
    # BATCH ID
    # --------------------------------------------------------

    batch_id = next_batch_id(
        business_day.strftime(
            "%Y-%m-%d"
        )
    )

    logger.info(
        "Starting incremental batch %s",
        batch_id,
    )

    # --------------------------------------------------------
    # NEXT IDS
    #
    # IMPORTANT:
    # These remain GLOBAL across every existing source file.
    # --------------------------------------------------------

    patient_start = (
        current_max_id(
            initial_filename="patients.csv",
            incremental_filename="patients.csv",
            column="patient_id",
        )
        + 1
    )

    admission_start = (
        current_max_id(
            initial_filename="admissions.csv",
            incremental_filename="admissions.csv",
            column="admission_id",
        )
        + 1
    )

    bill_start = (
        current_max_id(
            initial_filename="billing.csv",
            incremental_filename="billing.csv",
            column="bill_id",
        )
        + 1
    )

    claim_start = (
        current_max_id(
            initial_filename="claims.csv",
            incremental_filename="claims.csv",
            column="claim_id",
        )
        + 1
    )

    lab_start = (
        current_max_id(
            initial_filename="labs.csv",
            incremental_filename="labs.csv",
            column="lab_test_id",
        )
        + 1
    )

    medication_start = (
        current_max_id(
            initial_filename="medication_events.csv",
            incremental_filename="medication_events.csv",
            column="medication_event_id",
        )
        + 1
    )

    logger.info(
        (
            "Next IDs | "
            "patient=%s | "
            "admission=%s | "
            "bill=%s | "
            "claim=%s | "
            "lab=%s | "
            "medication=%s"
        ),
        patient_start,
        admission_start,
        bill_start,
        claim_start,
        lab_start,
        medication_start,
    )

    # ========================================================
    # PATIENT GENERATION
    # ========================================================

    print(
        "Generating new patients..."
    )

    new_patients = generate_patients(
        count=patient_count,
        start_number=patient_start,
    )

    if not new_patients.empty:

        new_patients[
            "registration_date"
        ] = business_day.date()

    # ========================================================
    # ELIGIBLE HISTORICAL PATIENT POPULATION
    # ========================================================

    historical_patients = (
        load_eligible_patients(
            business_day
        )
    )

    # Admissions may reference:
    #
    #   eligible historical patients
    #   OR
    #   patients registered in this batch.

    patient_population = pd.concat(
        [
            historical_patients,
            new_patients,
        ],
        ignore_index=True,
    )

    patient_population = (
        patient_population
        .drop_duplicates(
            subset=[
                "patient_id"
            ],
            keep="last",
        )
        .reset_index(
            drop=True
        )
    )

    # Defensive second filter.
    patient_population = (
        filter_patients_by_registration_date(
            patient_population,
            business_day,
        )
    )

    logger.info(
        (
            "Final eligible patient population=%s | "
            "new patients=%s"
        ),
        f"{len(patient_population):,}",
        f"{len(new_patients):,}",
    )

    # ========================================================
    # DOCTOR MASTER
    # ========================================================

    doctors = load_doctors()

    # ========================================================
    # ADMISSION WINDOW
    # ========================================================

    day_start = (
        business_day
        .normalize()
    )

    day_end = (
        day_start
        + pd.Timedelta(
            hours=23,
            minutes=59,
            seconds=59,
        )
    )

    # ========================================================
    # ADMISSIONS
    # ========================================================

    print(
        "Generating admissions..."
    )

    admissions = generate_admissions(
        patients=patient_population,
        doctors=doctors,
        count=admission_count,
        start_number=admission_start,
        generation_start=day_start,
        generation_end=day_end,
        clip_discharge_to_end=False,
    )

    # --------------------------------------------------------
    # HARD TEMPORAL INTEGRITY GATE
    # --------------------------------------------------------

    validate_generated_patient_references(
        admissions=admissions,
        patient_population=patient_population,
        business_day=business_day,
    )

    # ========================================================
    # BILLING
    # ========================================================

    print(
        "Generating billing..."
    )

    billing = generate_billing(
        admissions=admissions,
        doctors=doctors,
        patients=patient_population,
        start_number=bill_start,
    )

    # ========================================================
    # CLAIMS
    # ========================================================

    print(
        "Generating insurance claims..."
    )

    claims = generate_claims(
        billing=billing,
        start_number=claim_start,
    )

    # ========================================================
    # LAB TESTS
    # ========================================================

    print(
        "Generating laboratory tests..."
    )

    labs = generate_labs(
        admissions=admissions,
        start_number=lab_start,
    )

    # ========================================================
    # MEDICATION EVENTS
    # ========================================================

    print(
        "Generating medication events..."
    )

    medications = generate_medications(
        admissions=admissions,
        start_number=medication_start,
    )

    # ========================================================
    # ADD SOURCE BATCH ID
    # ========================================================

    datasets_to_tag = [
        new_patients,
        admissions,
        billing,
        claims,
        labs,
        medications,
    ]

    for dataframe in datasets_to_tag:

        dataframe.insert(
            0,
            "batch_id",
            batch_id,
        )

    # ========================================================
    # CREATE BATCH DIRECTORY
    # ========================================================

    batch_directory = (
        create_batch_directory(
            batch_id
        )
    )

    # ========================================================
    # DATASET MAP
    # ========================================================

    datasets = {
        "patients.csv":
            new_patients,

        "admissions.csv":
            admissions,

        "billing.csv":
            billing,

        "claims.csv":
            claims,

        "labs.csv":
            labs,

        "medication_events.csv":
            medications,
    }

    # ========================================================
    # EXPORT FILES
    # ========================================================

    print(
        "Exporting batch files..."
    )

    for (
        filename,
        dataframe,
    ) in datasets.items():

        export_batch_dataset(
            dataframe,
            batch_directory
            / filename,
        )

    # ========================================================
    # CALCULATE DURATION
    # ========================================================

    duration = (
        time.perf_counter()
        - start_clock
    )

    # ========================================================
    # MANIFEST
    # ========================================================

    manifest = {
        "batch_id":
            batch_id,

        "business_date":
            business_day.strftime(
                "%Y-%m-%d"
            ),

        "status":
            "GENERATED",

        "duration_seconds":
            round(
                duration,
                2,
            ),

        "chronology_controls": {
            "future_patients_allowed":
                False,

            "patient_registration_cutoff":
                business_day.strftime(
                    "%Y-%m-%d"
                ),

            "eligible_historical_patients":
                int(
                    len(
                        historical_patients
                    )
                ),

            "final_patient_population":
                int(
                    len(
                        patient_population
                    )
                ),
        },

        "record_counts": {
            filename:
                int(
                    len(dataframe)
                )

            for (
                filename,
                dataframe,
            ) in datasets.items()
        },

        "id_ranges": {
            "patient_start":
                patient_start,

            "patient_end":
                (
                    patient_start
                    + len(new_patients)
                    - 1

                    if len(new_patients) > 0

                    else None
                ),

            "admission_start":
                admission_start,

            "admission_end":
                (
                    admission_start
                    + len(admissions)
                    - 1
                ),

            "bill_start":
                bill_start,

            "bill_end":
                (
                    bill_start
                    + len(billing)
                    - 1
                ),

            "claim_start":
                claim_start,

            "claim_end":
                (
                    claim_start
                    + len(claims)
                    - 1

                    if len(claims) > 0

                    else None
                ),

            "lab_start":
                lab_start,

            "lab_end":
                (
                    lab_start
                    + len(labs)
                    - 1

                    if len(labs) > 0

                    else None
                ),

            "medication_start":
                medication_start,

            "medication_end":
                (
                    medication_start
                    + len(medications)
                    - 1

                    if len(medications) > 0

                    else None
                ),
        },
    }

    # ========================================================
    # SAVE MANIFEST
    # ========================================================

    save_manifest(
        batch_directory,
        manifest,
    )

    # ========================================================
    # SUCCESS
    # ========================================================

    logger.info(
        (
            "Incremental batch %s completed "
            "successfully in %.2f seconds."
        ),
        batch_id,
        duration,
    )

    return (
        batch_id,
        batch_directory,
        datasets,
        manifest,
    )