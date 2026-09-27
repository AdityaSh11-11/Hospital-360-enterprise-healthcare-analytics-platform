from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from database.connection import engine
from etl.incremental import get_batch


# ============================================================
# DISPLAY HELPERS
# ============================================================

WIDTH = 90


def separator(char: str = "="):
    print(char * WIDTH)


def heading(title: str):
    print()
    separator()
    print(title)
    separator()


def subheading(title: str):
    print()
    print(title)
    print("-" * WIDTH)


def status(exists: bool) -> str:
    return "EXISTS" if exists else "MISSING"


# ============================================================
# CSV LOADING
# ============================================================

def load_csv(
    batch_path: Path,
    filename: str,
) -> pd.DataFrame:

    path = batch_path / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Required source file not found: {path}"
        )

    dataframe = pd.read_csv(
        path,
        dtype=str,
        keep_default_na=False,
    )

    return dataframe


def load_batch_sources(
    batch_path: Path,
) -> dict[str, pd.DataFrame]:

    return {
        "patients": load_csv(
            batch_path,
            "patients.csv",
        ),
        "admissions": load_csv(
            batch_path,
            "admissions.csv",
        ),
        "billing": load_csv(
            batch_path,
            "billing.csv",
        ),
        "claims": load_csv(
            batch_path,
            "claims.csv",
        ),
        "labs": load_csv(
            batch_path,
            "labs.csv",
        ),
        "medication_events": load_csv(
            batch_path,
            "medication_events.csv",
        ),
    }


# ============================================================
# DATABASE HELPERS
# ============================================================

def fetch_key_set(
    connection,
    sql_text: str,
) -> set[str]:

    result = connection.execute(
        text(sql_text)
    )

    return {
        str(row[0])
        for row in result
        if row[0] is not None
    }


def record_exists(
    connection,
    sql_text: str,
    parameter_name: str,
    value: str,
) -> bool:

    result = connection.execute(
        text(sql_text),
        {
            parameter_name: value,
        },
    )

    return bool(
        result.scalar()
    )


# ============================================================
# WAREHOUSE KEY SNAPSHOT
# ============================================================

def get_warehouse_keys(
    connection,
) -> dict[str, set[str]]:

    return {
        "patients": fetch_key_set(
            connection,
            """
            SELECT patient_id
            FROM warehouse.dim_patient
            """,
        ),

        "admissions": fetch_key_set(
            connection,
            """
            SELECT admission_id
            FROM warehouse.fact_admission
            """,
        ),

        "billing": fetch_key_set(
            connection,
            """
            SELECT bill_id
            FROM warehouse.fact_billing
            """,
        ),

        "claims": fetch_key_set(
            connection,
            """
            SELECT claim_id
            FROM warehouse.fact_claim
            """,
        ),

        "labs": fetch_key_set(
            connection,
            """
            SELECT lab_test_id
            FROM warehouse.fact_lab_test
            """,
        ),

        "medication_events": fetch_key_set(
            connection,
            """
            SELECT medication_event_id
            FROM warehouse.fact_medication
            """,
        ),
    }


# ============================================================
# SOURCE KEYS
# ============================================================

KEY_COLUMNS = {
    "patients": "patient_id",
    "admissions": "admission_id",
    "billing": "bill_id",
    "claims": "claim_id",
    "labs": "lab_test_id",
    "medication_events": "medication_event_id",
}


def source_key_set(
    dataframe: pd.DataFrame,
    key_column: str,
) -> set[str]:

    if key_column not in dataframe.columns:
        raise KeyError(
            f"Source dataframe is missing "
            f"required key column: {key_column}"
        )

    return {
        str(value).strip()
        for value in dataframe[key_column]
        if str(value).strip()
    }


# ============================================================
# MISSING KEY ANALYSIS
# ============================================================

def find_missing_keys(
    sources: dict[str, pd.DataFrame],
    warehouse_keys: dict[str, set[str]],
) -> dict[str, list[str]]:

    missing = {}

    for dataset_name, key_column in KEY_COLUMNS.items():

        source_keys = source_key_set(
            sources[dataset_name],
            key_column,
        )

        missing[dataset_name] = sorted(
            source_keys
            - warehouse_keys[dataset_name]
        )

    return missing


# ============================================================
# ROW LOOKUP
# ============================================================

def find_source_row(
    dataframe: pd.DataFrame,
    key_column: str,
    key_value: str,
) -> dict:

    matches = dataframe[
        dataframe[key_column]
        .astype(str)
        .str.strip()
        == str(key_value).strip()
    ]

    if matches.empty:
        return {}

    return matches.iloc[0].to_dict()


# ============================================================
# DEPENDENCY CHECKS
# ============================================================

def patient_exists(
    connection,
    patient_id: str,
) -> bool:

    return record_exists(
        connection,
        """
        SELECT EXISTS
        (
            SELECT 1
            FROM warehouse.dim_patient
            WHERE patient_id = :patient_id
        )
        """,
        "patient_id",
        patient_id,
    )


def doctor_exists(
    connection,
    doctor_id: str,
) -> bool:

    return record_exists(
        connection,
        """
        SELECT EXISTS
        (
            SELECT 1
            FROM warehouse.dim_doctor
            WHERE doctor_id = :doctor_id
        )
        """,
        "doctor_id",
        doctor_id,
    )


def department_exists(
    connection,
    department_id: str,
) -> bool:

    return record_exists(
        connection,
        """
        SELECT EXISTS
        (
            SELECT 1
            FROM warehouse.dim_department
            WHERE department_id = :department_id
        )
        """,
        "department_id",
        department_id,
    )


def diagnosis_exists(
    connection,
    diagnosis_code: str,
) -> bool:

    return record_exists(
        connection,
        """
        SELECT EXISTS
        (
            SELECT 1
            FROM warehouse.dim_diagnosis
            WHERE diagnosis_code = :diagnosis_code
        )
        """,
        "diagnosis_code",
        diagnosis_code,
    )


def admission_exists(
    connection,
    admission_id: str,
) -> bool:

    return record_exists(
        connection,
        """
        SELECT EXISTS
        (
            SELECT 1
            FROM warehouse.fact_admission
            WHERE admission_id = :admission_id
        )
        """,
        "admission_id",
        admission_id,
    )


def billing_exists(
    connection,
    bill_id: str,
) -> bool:

    return record_exists(
        connection,
        """
        SELECT EXISTS
        (
            SELECT 1
            FROM warehouse.fact_billing
            WHERE bill_id = :bill_id
        )
        """,
        "bill_id",
        bill_id,
    )


def medication_exists(
    connection,
    medication_id: str,
) -> bool:

    return record_exists(
        connection,
        """
        SELECT EXISTS
        (
            SELECT 1
            FROM warehouse.dim_medication
            WHERE medication_id = :medication_id
        )
        """,
        "medication_id",
        medication_id,
    )


def insurer_exists(
    connection,
    insurer_id: str,
) -> bool:

    return record_exists(
        connection,
        """
        SELECT EXISTS
        (
            SELECT 1
            FROM warehouse.dim_insurer
            WHERE insurer_id = :insurer_id
        )
        """,
        "insurer_id",
        insurer_id,
    )


# ============================================================
# ADMISSION DIAGNOSTICS
# ============================================================

def diagnose_missing_admissions(
    connection,
    dataframe: pd.DataFrame,
    missing_ids: list[str],
):

    subheading(
        "MISSING ADMISSIONS"
    )

    if not missing_ids:
        print("[PASS] No missing admissions.")
        return

    for admission_id in missing_ids:

        row = find_source_row(
            dataframe,
            "admission_id",
            admission_id,
        )

        print()
        print(
            f"Admission ID : {admission_id}"
        )

        if not row:
            print(
                "Source row could not be located."
            )
            continue

        patient_id = str(
            row.get(
                "patient_id",
                "",
            )
        )

        doctor_id = str(
            row.get(
                "doctor_id",
                "",
            )
        )

        department_id = str(
            row.get(
                "department_id",
                "",
            )
        )

        diagnosis_code = str(
            row.get(
                "diagnosis_code",
                "",
            )
        )

        print(
            f"Patient      : {patient_id}"
        )

        print(
            f"Doctor       : {doctor_id}"
        )

        print(
            f"Department   : {department_id}"
        )

        print(
            f"Diagnosis    : {diagnosis_code}"
        )

        print()
        print("Dependencies")

        print(
            f"  Patient    : "
            f"{status(patient_exists(connection, patient_id))}"
        )

        print(
            f"  Doctor     : "
            f"{status(doctor_exists(connection, doctor_id))}"
        )

        print(
            f"  Department : "
            f"{status(department_exists(connection, department_id))}"
        )

        print(
            f"  Diagnosis  : "
            f"{status(diagnosis_exists(connection, diagnosis_code))}"
        )


# ============================================================
# BILLING DIAGNOSTICS
# ============================================================

def diagnose_missing_billing(
    connection,
    dataframe: pd.DataFrame,
    missing_ids: list[str],
):

    subheading(
        "MISSING BILLING"
    )

    if not missing_ids:
        print("[PASS] No missing billing rows.")
        return

    for bill_id in missing_ids:

        row = find_source_row(
            dataframe,
            "bill_id",
            bill_id,
        )

        print()
        print(
            f"Bill ID      : {bill_id}"
        )

        if not row:
            print(
                "Source row could not be located."
            )
            continue

        admission_id = str(
            row.get(
                "admission_id",
                "",
            )
        )

        patient_id = str(
            row.get(
                "patient_id",
                "",
            )
        )

        print(
            f"Admission    : {admission_id}"
        )

        print(
            f"Patient      : {patient_id}"
        )

        print()
        print("Dependencies")

        print(
            f"  Admission  : "
            f"{status(admission_exists(connection, admission_id))}"
        )

        print(
            f"  Patient    : "
            f"{status(patient_exists(connection, patient_id))}"
        )


# ============================================================
# CLAIM DIAGNOSTICS
# ============================================================

def diagnose_missing_claims(
    connection,
    dataframe: pd.DataFrame,
    missing_ids: list[str],
):

    subheading(
        "MISSING CLAIMS"
    )

    if not missing_ids:
        print("[PASS] No missing claims.")
        return

    for claim_id in missing_ids:

        row = find_source_row(
            dataframe,
            "claim_id",
            claim_id,
        )

        print()
        print(
            f"Claim ID     : {claim_id}"
        )

        if not row:
            print(
                "Source row could not be located."
            )
            continue

        bill_id = str(
            row.get(
                "bill_id",
                "",
            )
        )

        patient_id = str(
            row.get(
                "patient_id",
                "",
            )
        )

        insurer_id = str(
            row.get(
                "insurer_id",
                "",
            )
        )

        print(
            f"Bill         : {bill_id}"
        )

        print(
            f"Patient      : {patient_id}"
        )

        print(
            f"Insurer      : {insurer_id}"
        )

        print()
        print("Dependencies")

        print(
            f"  Billing    : "
            f"{status(billing_exists(connection, bill_id))}"
        )

        print(
            f"  Patient    : "
            f"{status(patient_exists(connection, patient_id))}"
        )

        print(
            f"  Insurer    : "
            f"{status(insurer_exists(connection, insurer_id))}"
        )


# ============================================================
# LAB DIAGNOSTICS
# ============================================================

def diagnose_missing_labs(
    connection,
    dataframe: pd.DataFrame,
    missing_ids: list[str],
):

    subheading(
        "MISSING LAB TESTS"
    )

    if not missing_ids:
        print("[PASS] No missing lab tests.")
        return

    for lab_test_id in missing_ids:

        row = find_source_row(
            dataframe,
            "lab_test_id",
            lab_test_id,
        )

        print()
        print(
            f"Lab Test ID  : {lab_test_id}"
        )

        if not row:
            print(
                "Source row could not be located."
            )
            continue

        admission_id = str(
            row.get(
                "admission_id",
                "",
            )
        )

        patient_id = str(
            row.get(
                "patient_id",
                "",
            )
        )

        doctor_id = str(
            row.get(
                "doctor_id",
                "",
            )
        )

        print(
            f"Admission    : {admission_id}"
        )

        print(
            f"Patient      : {patient_id}"
        )

        print(
            f"Doctor       : {doctor_id}"
        )

        print()
        print("Dependencies")

        print(
            f"  Admission  : "
            f"{status(admission_exists(connection, admission_id))}"
        )

        print(
            f"  Patient    : "
            f"{status(patient_exists(connection, patient_id))}"
        )

        print(
            f"  Doctor     : "
            f"{status(doctor_exists(connection, doctor_id))}"
        )


# ============================================================
# MEDICATION EVENT DIAGNOSTICS
# ============================================================

def diagnose_missing_medications(
    connection,
    dataframe: pd.DataFrame,
    missing_ids: list[str],
):

    subheading(
        "MISSING MEDICATION EVENTS"
    )

    if not missing_ids:
        print(
            "[PASS] No missing medication events."
        )
        return

    for event_id in missing_ids:

        row = find_source_row(
            dataframe,
            "medication_event_id",
            event_id,
        )

        print()
        print(
            f"Event ID     : {event_id}"
        )

        if not row:
            print(
                "Source row could not be located."
            )
            continue

        admission_id = str(
            row.get(
                "admission_id",
                "",
            )
        )

        patient_id = str(
            row.get(
                "patient_id",
                "",
            )
        )

        medication_id = str(
            row.get(
                "medication_id",
                "",
            )
        )

        print(
            f"Admission    : {admission_id}"
        )

        print(
            f"Patient      : {patient_id}"
        )

        print(
            f"Medication   : {medication_id}"
        )

        print()
        print("Dependencies")

        print(
            f"  Admission  : "
            f"{status(admission_exists(connection, admission_id))}"
        )

        print(
            f"  Patient    : "
            f"{status(patient_exists(connection, patient_id))}"
        )

        print(
            f"  Medication : "
            f"{status(medication_exists(connection, medication_id))}"
        )


# ============================================================
# SOURCE REGISTRATION CHECK
# ============================================================

def diagnose_patient_registration(
    sources: dict[str, pd.DataFrame],
):

    subheading(
        "PATIENT REGISTRATION VS ADMISSION CHECK"
    )

    patients = sources["patients"].copy()
    admissions = sources["admissions"].copy()

    if patients.empty or admissions.empty:
        print(
            "No source rows available."
        )
        return

    patients[
        "registration_date"
    ] = pd.to_datetime(
        patients["registration_date"],
        errors="coerce",
    )

    admissions[
        "admission_timestamp"
    ] = pd.to_datetime(
        admissions["admission_timestamp"],
        errors="coerce",
    )

    joined = admissions.merge(
        patients[
            [
                "patient_id",
                "registration_date",
            ]
        ],
        on="patient_id",
        how="inner",
    )

    invalid = joined[
        joined["registration_date"]
        >
        joined["admission_timestamp"]
    ]

    if invalid.empty:

        print(
            "[PASS] No newly generated patient "
            "was admitted before registration."
        )

        return

    print(
        f"[WARN] Found {len(invalid):,} "
        "admission(s) where the new patient's "
        "registration date is after admission."
    )

    for _, row in invalid.head(
        20
    ).iterrows():

        print(
            f"  {row['admission_id']} | "
            f"{row['patient_id']} | "
            f"registration="
            f"{row['registration_date']} | "
            f"admission="
            f"{row['admission_timestamp']}"
        )


# ============================================================
# SUMMARY
# ============================================================

def print_summary(
    sources,
    missing,
):

    heading(
        "SOURCE → WAREHOUSE BUSINESS KEY SUMMARY"
    )

    print(
        f"{'Dataset':<24}"
        f"{'Source':>12}"
        f"{'Missing':>12}"
        f"{'Status':>12}"
    )

    print(
        "-" * WIDTH
    )

    for dataset_name, key_column in KEY_COLUMNS.items():

        source_count = len(
            source_key_set(
                sources[dataset_name],
                key_column,
            )
        )

        missing_count = len(
            missing[dataset_name]
        )

        row_status = (
            "PASS"
            if missing_count == 0
            else "FAIL"
        )

        print(
            f"{dataset_name:<24}"
            f"{source_count:>12,}"
            f"{missing_count:>12,}"
            f"{row_status:>12}"
        )


# ============================================================
# MAIN DIAGNOSTIC
# ============================================================

def diagnose(
    batch_name: str,
):

    batch = get_batch(
        batch_name
    )

    heading(
        "HOSPITAL 360 — "
        f"BATCH DIAGNOSTIC — {batch.batch_id}"
    )

    print(
        f"Business date : {batch.business_date}"
    )

    print(
        f"Source path   : {batch.path}"
    )

    sources = load_batch_sources(
        batch.path
    )

    with engine.connect() as connection:

        warehouse_keys = (
            get_warehouse_keys(
                connection
            )
        )

        missing = find_missing_keys(
            sources,
            warehouse_keys,
        )

        print_summary(
            sources,
            missing,
        )

        diagnose_missing_admissions(
            connection,
            sources["admissions"],
            missing["admissions"],
        )

        diagnose_missing_billing(
            connection,
            sources["billing"],
            missing["billing"],
        )

        diagnose_missing_claims(
            connection,
            sources["claims"],
            missing["claims"],
        )

        diagnose_missing_labs(
            connection,
            sources["labs"],
            missing["labs"],
        )

        diagnose_missing_medications(
            connection,
            sources[
                "medication_events"
            ],
            missing[
                "medication_events"
            ],
        )

    diagnose_patient_registration(
        sources
    )

    heading(
        "DIAGNOSTIC COMPLETE"
    )

    total_missing = sum(
        len(values)
        for dataset_name, values
        in missing.items()
        if dataset_name != "patients"
    )

    if total_missing == 0:

        print(
            "[PASS] All source business keys "
            "exist in the warehouse."
        )

    else:

        print(
            f"[FAIL] {total_missing:,} source "
            "business key(s) are missing from "
            "the warehouse."
        )

        print()
        print(
            "No database changes were made."
        )


# ============================================================
# CLI
# ============================================================

def build_parser():

    parser = argparse.ArgumentParser(
        description=(
            "Diagnose source-to-warehouse "
            "row loss for one Hospital 360 "
            "incremental batch."
        )
    )

    parser.add_argument(
        "--batch",
        required=True,
        type=str,
        help=(
            "Batch name, for example "
            "BATCH-20260924-003"
        ),
    )

    return parser


def main():

    parser = build_parser()

    args = parser.parse_args()

    diagnose(
        args.batch
    )


if __name__ == "__main__":
    main()