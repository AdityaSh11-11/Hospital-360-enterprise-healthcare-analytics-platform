from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd
from sqlalchemy import text


# ============================================================
# RESULT MODEL
# ============================================================

@dataclass
class ReferentialIssue:
    dataset: str
    record_id: str
    field: str
    value: str
    reason: str


@dataclass
class ReferentialValidationResult:
    issues: list[ReferentialIssue] = field(
        default_factory=list
    )

    @property
    def passed(self) -> bool:
        return len(self.issues) == 0

    @property
    def issue_count(self) -> int:
        return len(self.issues)

    def add(
        self,
        dataset: str,
        record_id: str,
        field: str,
        value: str,
        reason: str,
    ) -> None:

        self.issues.append(
            ReferentialIssue(
                dataset=dataset,
                record_id=str(record_id),
                field=field,
                value=str(value),
                reason=reason,
            )
        )


# ============================================================
# NORMALIZATION
# ============================================================

def normalize(value) -> str:

    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    return str(value).strip()


def dataframe_keys(
    dataframe: pd.DataFrame | None,
    column: str,
) -> set[str]:

    if dataframe is None:
        return set()

    if dataframe.empty:
        return set()

    if column not in dataframe.columns:
        return set()

    return {
        normalize(value)
        for value in dataframe[column]
        if normalize(value)
    }


# ============================================================
# DATABASE BUSINESS KEYS
# ============================================================

def fetch_keys(
    connection,
    sql: str,
) -> set[str]:

    result = connection.execute(
        text(sql)
    )

    return {
        normalize(row[0])
        for row in result
        if normalize(row[0])
    }


def warehouse_reference_keys(
    connection,
) -> dict[str, set[str]]:

    return {
        "patients": fetch_keys(
            connection,
            """
            SELECT patient_id
            FROM warehouse.dim_patient
            """,
        ),

        "doctors": fetch_keys(
            connection,
            """
            SELECT doctor_id
            FROM warehouse.dim_doctor
            """,
        ),

        "departments": fetch_keys(
            connection,
            """
            SELECT department_id
            FROM warehouse.dim_department
            """,
        ),

        "diagnoses": fetch_keys(
            connection,
            """
            SELECT diagnosis_code
            FROM warehouse.dim_diagnosis
            """,
        ),

        "insurers": fetch_keys(
            connection,
            """
            SELECT insurer_id
            FROM warehouse.dim_insurer
            """,
        ),

        "medications": fetch_keys(
            connection,
            """
            SELECT medication_id
            FROM warehouse.dim_medication
            """,
        ),

        "admissions": fetch_keys(
            connection,
            """
            SELECT admission_id
            FROM warehouse.fact_admission
            """,
        ),

        "billing": fetch_keys(
            connection,
            """
            SELECT bill_id
            FROM warehouse.fact_billing
            """,
        ),
    }


# ============================================================
# GENERIC REFERENCE CHECK
# ============================================================

def check_reference(
    *,
    result: ReferentialValidationResult,
    dataframe: pd.DataFrame,
    dataset: str,
    record_column: str,
    reference_column: str,
    valid_values: set[str],
    reason: str,
) -> None:

    if dataframe.empty:
        return

    if record_column not in dataframe.columns:
        return

    if reference_column not in dataframe.columns:
        return

    for _, row in dataframe.iterrows():

        record_id = normalize(
            row.get(record_column)
        )

        reference_value = normalize(
            row.get(reference_column)
        )

        if not reference_value:
            continue

        if reference_value not in valid_values:

            result.add(
                dataset=dataset,
                record_id=record_id,
                field=reference_column,
                value=reference_value,
                reason=reason,
            )


# ============================================================
# TEMPORAL PATIENT CHECK
# ============================================================

def check_patient_registration_dates(
    *,
    result: ReferentialValidationResult,
    admissions: pd.DataFrame,
    batch_patients: pd.DataFrame,
    business_date,
) -> None:

    if admissions.empty:
        return

    if batch_patients.empty:
        return

    if (
        "patient_id"
        not in batch_patients.columns
        or
        "registration_date"
        not in batch_patients.columns
    ):
        return

    registration_map = {}

    for _, row in batch_patients.iterrows():

        patient_id = normalize(
            row.get("patient_id")
        )

        registration_date_value = row.get("registration_date")

        if registration_date_value is None:
            continue

        registration_date = pd.to_datetime(
            registration_date_value,
            errors="coerce",
        )

        if (
            patient_id
            and
            not pd.isna(registration_date)
        ):
            registration_map[
                patient_id
            ] = registration_date

    business_timestamp = pd.to_datetime(
        business_date,
        errors="coerce",
    )

    for _, row in admissions.iterrows():

        patient_id = normalize(
            row.get("patient_id")
        )

        admission_id = normalize(
            row.get("admission_id")
        )

        registration_date = (
            registration_map.get(
                patient_id
            )
        )

        if registration_date is None:
            continue

        admission_value = row.get(
            "admission_timestamp"
        )
        admission_timestamp = pd.to_datetime(
            "" if admission_value is None else str(admission_value),
            errors="coerce",
        )

        if (
            not pd.isna(
                admission_timestamp
            )
            and
            registration_date
            >
            admission_timestamp
        ):

            result.add(
                dataset="admissions",
                record_id=admission_id,
                field="patient_id",
                value=patient_id,
                reason=(
                    "Patient registration date "
                    "is after admission timestamp."
                ),
            )

        if (
            not pd.isna(
                business_timestamp
            )
            and
            registration_date.normalize()
            >
            business_timestamp.normalize()
        ):

            result.add(
                dataset="admissions",
                record_id=admission_id,
                field="patient_id",
                value=patient_id,
                reason=(
                    "Patient registration date "
                    "is after ETL business date."
                ),
            )


# ============================================================
# MAIN VALIDATOR
# ============================================================

def validate_references(
    connection,
    datasets: dict[str, pd.DataFrame],
    business_date=None,
) -> ReferentialValidationResult:

    result = (
        ReferentialValidationResult()
    )

    warehouse = (
        warehouse_reference_keys(
            connection
        )
    )

    # ========================================================
    # CURRENT BATCH BUSINESS KEYS
    # ========================================================

    batch_patients = datasets.get(
        "patients",
        pd.DataFrame(),
    )

    batch_doctors = datasets.get(
        "doctors",
        pd.DataFrame(),
    )

    batch_medications = datasets.get(
        "medication_master",
        pd.DataFrame(),
    )

    admissions = datasets.get(
        "admissions",
        pd.DataFrame(),
    )

    billing = datasets.get(
        "billing",
        pd.DataFrame(),
    )

    claims = datasets.get(
        "claims",
        pd.DataFrame(),
    )

    labs = datasets.get(
        "labs",
        pd.DataFrame(),
    )

    medication_events = datasets.get(
        "medication_events",
        pd.DataFrame(),
    )

    # ========================================================
    # COMBINED VALID REFERENCE SETS
    # ========================================================

    valid_patients = (
        warehouse["patients"]
        |
        dataframe_keys(
            batch_patients,
            "patient_id",
        )
    )

    valid_doctors = (
        warehouse["doctors"]
        |
        dataframe_keys(
            batch_doctors,
            "doctor_id",
        )
    )

    valid_medications = (
        warehouse["medications"]
        |
        dataframe_keys(
            batch_medications,
            "medication_id",
        )
    )

    valid_admissions = (
        warehouse["admissions"]
        |
        dataframe_keys(
            admissions,
            "admission_id",
        )
    )

    valid_billing = (
        warehouse["billing"]
        |
        dataframe_keys(
            billing,
            "bill_id",
        )
    )

    # ========================================================
    # ADMISSIONS
    # ========================================================

    check_reference(
        result=result,
        dataframe=admissions,
        dataset="admissions",
        record_column="admission_id",
        reference_column="patient_id",
        valid_values=valid_patients,
        reason=(
            "Patient does not exist in the "
            "warehouse or current ETL batch."
        ),
    )

    check_reference(
        result=result,
        dataframe=admissions,
        dataset="admissions",
        record_column="admission_id",
        reference_column="doctor_id",
        valid_values=valid_doctors,
        reason=(
            "Doctor does not exist in the "
            "warehouse or current ETL batch."
        ),
    )

    check_reference(
        result=result,
        dataframe=admissions,
        dataset="admissions",
        record_column="admission_id",
        reference_column="department_id",
        valid_values=warehouse[
            "departments"
        ],
        reason=(
            "Department does not exist "
            "in warehouse.dim_department."
        ),
    )

    check_reference(
        result=result,
        dataframe=admissions,
        dataset="admissions",
        record_column="admission_id",
        reference_column="diagnosis_code",
        valid_values=warehouse[
            "diagnoses"
        ],
        reason=(
            "Diagnosis does not exist "
            "in warehouse.dim_diagnosis."
        ),
    )

    # ========================================================
    # BILLING
    # ========================================================

    check_reference(
        result=result,
        dataframe=billing,
        dataset="billing",
        record_column="bill_id",
        reference_column="admission_id",
        valid_values=valid_admissions,
        reason=(
            "Admission does not exist in the "
            "warehouse or current ETL batch."
        ),
    )

    check_reference(
        result=result,
        dataframe=billing,
        dataset="billing",
        record_column="bill_id",
        reference_column="patient_id",
        valid_values=valid_patients,
        reason=(
            "Patient does not exist in the "
            "warehouse or current ETL batch."
        ),
    )

    # ========================================================
    # CLAIMS
    # ========================================================

    check_reference(
        result=result,
        dataframe=claims,
        dataset="claims",
        record_column="claim_id",
        reference_column="bill_id",
        valid_values=valid_billing,
        reason=(
            "Billing record does not exist in "
            "the warehouse or current ETL batch."
        ),
    )

    check_reference(
        result=result,
        dataframe=claims,
        dataset="claims",
        record_column="claim_id",
        reference_column="patient_id",
        valid_values=valid_patients,
        reason=(
            "Patient does not exist in the "
            "warehouse or current ETL batch."
        ),
    )

    check_reference(
        result=result,
        dataframe=claims,
        dataset="claims",
        record_column="claim_id",
        reference_column="insurer_id",
        valid_values=warehouse[
            "insurers"
        ],
        reason=(
            "Insurer does not exist "
            "in warehouse.dim_insurer."
        ),
    )

    # ========================================================
    # LABS
    # ========================================================

    check_reference(
        result=result,
        dataframe=labs,
        dataset="labs",
        record_column="lab_test_id",
        reference_column="patient_id",
        valid_values=valid_patients,
        reason=(
            "Patient does not exist in the "
            "warehouse or current ETL batch."
        ),
    )

    check_reference(
        result=result,
        dataframe=labs,
        dataset="labs",
        record_column="lab_test_id",
        reference_column="admission_id",
        valid_values=valid_admissions,
        reason=(
            "Admission does not exist in the "
            "warehouse or current ETL batch."
        ),
    )

    check_reference(
        result=result,
        dataframe=labs,
        dataset="labs",
        record_column="lab_test_id",
        reference_column="doctor_id",
        valid_values=valid_doctors,
        reason=(
            "Doctor does not exist in the "
            "warehouse or current ETL batch."
        ),
    )

    # ========================================================
    # MEDICATION EVENTS
    # ========================================================

    check_reference(
        result=result,
        dataframe=medication_events,
        dataset="medication_events",
        record_column=(
            "medication_event_id"
        ),
        reference_column="patient_id",
        valid_values=valid_patients,
        reason=(
            "Patient does not exist in the "
            "warehouse or current ETL batch."
        ),
    )

    check_reference(
        result=result,
        dataframe=medication_events,
        dataset="medication_events",
        record_column=(
            "medication_event_id"
        ),
        reference_column="admission_id",
        valid_values=valid_admissions,
        reason=(
            "Admission does not exist in the "
            "warehouse or current ETL batch."
        ),
    )

    check_reference(
        result=result,
        dataframe=medication_events,
        dataset="medication_events",
        record_column=(
            "medication_event_id"
        ),
        reference_column="medication_id",
        valid_values=valid_medications,
        reason=(
            "Medication does not exist in the "
            "warehouse or current ETL batch."
        ),
    )

    # ========================================================
    # TEMPORAL VALIDATION
    # ========================================================

    if business_date is not None:

        check_patient_registration_dates(
            result=result,
            admissions=admissions,
            batch_patients=batch_patients,
            business_date=business_date,
        )

    return result


# ============================================================
# FAILURE MESSAGE
# ============================================================

def format_referential_errors(
    result: ReferentialValidationResult,
    max_examples: int = 20,
) -> str:

    if result.passed:
        return (
            "Referential integrity validation "
            "passed."
        )

    lines = [
        (
            "Referential integrity validation "
            f"failed with {result.issue_count:,} "
            "issue(s)."
        ),
        "",
    ]

    for issue in result.issues[
        :max_examples
    ]:

        lines.append(
            (
                f"{issue.dataset} | "
                f"{issue.record_id} | "
                f"{issue.field}="
                f"{issue.value} | "
                f"{issue.reason}"
            )
        )

    remaining = (
        result.issue_count
        - max_examples
    )

    if remaining > 0:

        lines.append(
            ""
        )

        lines.append(
            f"... plus {remaining:,} "
            "additional issue(s)."
        )

    return "\n".join(
        lines
    )