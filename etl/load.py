import json

import pandas as pd
from sqlalchemy import text

from utils.logger import get_logger


logger = get_logger(__name__)


# ============================================================
# HELPERS
# ============================================================

def none_if_na(value):

    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    if hasattr(value, "item"):

        try:
            return value.item()

        except Exception:
            pass

    return value


def records(
    dataframe: pd.DataFrame,
) -> list[dict]:

    result = []

    for row in dataframe.to_dict(
        orient="records"
    ):

        clean = {
            key: none_if_na(value)
            for key, value
            in row.items()
        }

        result.append(clean)

    return result


# ============================================================
# ETL CONTROL
# ============================================================

def source_already_loaded(
    connection,
    source_batch_id: str,
) -> bool:

    result = connection.execute(
        text(
            """
            SELECT EXISTS
            (
                SELECT 1

                FROM control.etl_batch

                WHERE source_batch_id =
                    :source_batch_id

                  AND status =
                    'SUCCESS'
            )
            """
        ),
        {
            "source_batch_id":
                source_batch_id
        },
    )

    return bool(
        result.scalar()
    )


def create_etl_batch(
    connection,
    batch_name: str,
    batch_type: str,
    source_batch_id: str,
    source_path: str,
    business_date=None,
) -> int:

    result = connection.execute(
        text(
            """
            INSERT INTO control.etl_batch
            (
                batch_name,
                batch_type,
                source_name,
                source_batch_id,
                source_path,
                business_date,
                status
            )

            VALUES
            (
                :batch_name,
                :batch_type,
                'Hospital360 Synthetic Source',
                :source_batch_id,
                :source_path,
                :business_date,
                'RUNNING'
            )

            RETURNING batch_id
            """
        ),
        {
            "batch_name":
                batch_name,

            "batch_type":
                batch_type,

            "source_batch_id":
                source_batch_id,

            "source_path":
                source_path,

            "business_date":
                business_date,
        },
    )

    batch_id = result.scalar_one()

    logger.info(
        "Created ETL batch_id=%s source=%s",
        batch_id,
        source_batch_id,
    )

    return batch_id


def complete_etl_batch(
    connection,
    batch_id: int,
    status: str,
    received: int,
    inserted: int,
    rejected: int,
    duration_seconds: float,
    error_message=None,
):

    connection.execute(
        text(
            """
            UPDATE control.etl_batch

            SET
                end_time =
                    CURRENT_TIMESTAMP,

                status =
                    :status,

                records_received =
                    :received,

                records_inserted =
                    :inserted,

                records_rejected =
                    :rejected,

                duration_seconds =
                    :duration,

                error_message =
                    :error

            WHERE batch_id =
                :batch_id
            """
        ),
        {
            "status":
                status,

            "received":
                int(received),

            "inserted":
                int(inserted),

            "rejected":
                int(rejected),

            "duration":
                round(
                    float(duration_seconds),
                    2,
                ),

            "error":
                error_message,

            "batch_id":
                batch_id,
        },
    )


# ============================================================
# REJECTED RECORDS
# ============================================================

def load_rejections(
    connection,
    batch_id: int,
    issues,
):

    if not issues:

        logger.info(
            "No rejected records for batch_id=%s",
            batch_id,
        )

        return

    payload = []

    for issue in issues:

        payload.append(
            {
                "batch_id":
                    batch_id,

                "dataset_name":
                    issue.dataset,

                "record_identifier":
                    issue.record_identifier,

                "rule_name":
                    issue.rule_name,

                "rejection_reason":
                    issue.reason,

                "record_data":
                    json.dumps(
                        issue.record_data,
                        default=str,
                    ),
            }
        )

    connection.execute(
        text(
            """
            INSERT INTO control.rejected_record
            (
                batch_id,
                dataset_name,
                record_identifier,
                rule_name,
                rejection_reason,
                record_data
            )

            VALUES
            (
                :batch_id,
                :dataset_name,
                :record_identifier,
                :rule_name,
                :rejection_reason,
                CAST(
                    :record_data
                    AS JSONB
                )
            )
            """
        ),
        payload,
    )

    logger.info(
        "Stored %s rejected records.",
        f"{len(payload):,}",
    )


# ============================================================
# DATA QUALITY LOG
# ============================================================

def log_quality(
    connection,
    batch_id: int,
    dataset_name: str,
    records_checked: int,
    failed_records: int,
):

    status = (
        "PASS"
        if failed_records == 0
        else "PARTIAL"
    )

    severity = (
        "INFO"
        if failed_records == 0
        else "WARNING"
    )

    details = (
        f"{failed_records:,} of "
        f"{records_checked:,} records "
        "failed validation."
    )

    connection.execute(
        text(
            """
            INSERT INTO control.data_quality_log
            (
                batch_id,
                table_name,
                rule_name,
                rule_type,
                records_checked,
                failed_records,
                severity,
                status,
                details
            )

            VALUES
            (
                :batch_id,
                :table_name,
                'DATASET_VALIDATION',
                'ETL',
                :records_checked,
                :failed_records,
                :severity,
                :status,
                :details
            )
            """
        ),
        {
            "batch_id":
                batch_id,

            "table_name":
                dataset_name,

            "records_checked":
                int(records_checked),

            "failed_records":
                int(failed_records),

            "severity":
                severity,

            "status":
                status,

            "details":
                details,
        },
    )


# ============================================================
# STAGING
# ============================================================

STAGING_TABLES = {
    "doctors":
        "stg_doctors",

    "patients":
        "stg_patients",

    "admissions":
        "stg_admissions",

    "billing":
        "stg_billing",

    "claims":
        "stg_claims",

    "labs":
        "stg_labs",

    "medication_master":
        "stg_medication_master",

    "medication_events":
        "stg_medication_events",
}


def load_staging(
    connection,
    datasets: dict[str, pd.DataFrame],
    batch_id: int,
):

    for (
        dataset_name,
        dataframe,
    ) in datasets.items():

        if dataset_name not in STAGING_TABLES:

            raise KeyError(
                "No staging table configured "
                f"for dataset: {dataset_name}"
            )

        table_name = STAGING_TABLES[
            dataset_name
        ]

        if dataframe.empty:

            logger.info(
                "Skipping empty staging dataset=%s",
                dataset_name,
            )

            continue

        staged = dataframe.copy()

        # Incremental generator files already contain a textual
        # source batch_id. PostgreSQL staging.batch_id stores
        # the numeric ETL control batch ID instead.
        if "batch_id" in staged.columns:

            staged = staged.drop(
                columns=["batch_id"]
            )

        staged.insert(
            0,
            "batch_id",
            batch_id,
        )

        logger.info(
            (
                "Loading staging.%s | "
                "dataset=%s | rows=%s | columns=%s"
            ),
            table_name,
            dataset_name,
            f"{len(staged):,}",
            len(staged.columns),
        )

        staged.to_sql(
            name=table_name,
            con=connection,
            schema="staging",
            if_exists="append",
            index=False,
            chunksize=500,
            method=None,
        )

        logger.info(
            "Loaded %s rows into staging.%s",
            f"{len(staged):,}",
            table_name,
        )


# ============================================================
# PATIENT DIMENSION
# ============================================================

def load_patients(
    connection,
    dataframe: pd.DataFrame,
):

    if dataframe.empty:
        return

    sql = text(
        """
        INSERT INTO warehouse.dim_patient
        (
            patient_id,
            first_name,
            last_name,
            gender,
            date_of_birth,
            blood_group,
            city,
            state,
            insurance_status,
            chronic_condition,
            registration_date
        )

        VALUES
        (
            :patient_id,
            :first_name,
            :last_name,
            :gender,
            :date_of_birth,
            :blood_group,
            :city,
            :state,
            :insurance_status,
            :chronic_condition,
            :registration_date
        )

        ON CONFLICT (patient_id)

        DO UPDATE SET

            first_name =
                EXCLUDED.first_name,

            last_name =
                EXCLUDED.last_name,

            gender =
                EXCLUDED.gender,

            date_of_birth =
                EXCLUDED.date_of_birth,

            blood_group =
                EXCLUDED.blood_group,

            city =
                EXCLUDED.city,

            state =
                EXCLUDED.state,

            insurance_status =
                EXCLUDED.insurance_status,

            chronic_condition =
                EXCLUDED.chronic_condition,

            registration_date =
                EXCLUDED.registration_date,

            updated_at =
                CURRENT_TIMESTAMP
        """
    )

    connection.execute(
        sql,
        records(dataframe),
    )

    logger.info(
        "Processed %s patient dimension rows.",
        f"{len(dataframe):,}",
    )


# ============================================================
# DOCTOR DIMENSION
# ============================================================

def load_doctors(
    connection,
    dataframe: pd.DataFrame,
):

    if dataframe.empty:
        return

    sql = text(
        """
        INSERT INTO warehouse.dim_doctor
        (
            doctor_id,
            doctor_name,
            gender,
            specialization,
            department_key,
            qualification,
            experience_years,
            consultation_fee,
            joining_date,
            employment_status
        )

        SELECT
            :doctor_id,
            :doctor_name,
            :gender,
            :specialization,
            department.department_key,
            :qualification,
            :experience_years,
            :consultation_fee,
            :joining_date,
            :employment_status

        FROM warehouse.dim_department
            AS department

        WHERE department.department_id =
            :department_id

        ON CONFLICT (doctor_id)

        DO UPDATE SET

            doctor_name =
                EXCLUDED.doctor_name,

            gender =
                EXCLUDED.gender,

            specialization =
                EXCLUDED.specialization,

            department_key =
                EXCLUDED.department_key,

            qualification =
                EXCLUDED.qualification,

            experience_years =
                EXCLUDED.experience_years,

            consultation_fee =
                EXCLUDED.consultation_fee,

            joining_date =
                EXCLUDED.joining_date,

            employment_status =
                EXCLUDED.employment_status
        """
    )

    connection.execute(
        sql,
        records(dataframe),
    )

    logger.info(
        "Processed %s doctor dimension rows.",
        f"{len(dataframe):,}",
    )


# ============================================================
# MEDICATION DIMENSION
# ============================================================

def load_medication_master(
    connection,
    dataframe: pd.DataFrame,
):

    if dataframe.empty:
        return

    sql = text(
        """
        INSERT INTO warehouse.dim_medication
        (
            medication_id,
            medication_name,
            medication_category,
            manufacturer,
            unit_cost
        )

        VALUES
        (
            :medication_id,
            :medication_name,
            :medication_category,
            :manufacturer,
            :unit_cost
        )

        ON CONFLICT (medication_id)

        DO UPDATE SET

            medication_name =
                EXCLUDED.medication_name,

            medication_category =
                EXCLUDED.medication_category,

            manufacturer =
                EXCLUDED.manufacturer,

            unit_cost =
                EXCLUDED.unit_cost
        """
    )

    connection.execute(
        sql,
        records(dataframe),
    )

    logger.info(
        "Processed %s medication dimension rows.",
        f"{len(dataframe):,}",
    )


# ============================================================
# ADMISSION FACT
# ============================================================

def load_admissions(
    connection,
    dataframe: pd.DataFrame,
):

    if dataframe.empty:
        return

    sql = text(
        """
        INSERT INTO warehouse.fact_admission
        (
            admission_id,
            patient_key,
            doctor_key,
            department_key,
            diagnosis_key,
            admission_date_key,
            discharge_date_key,
            admission_timestamp,
            discharge_timestamp,
            admission_type,
            room_type,
            bed_number,
            length_of_stay,
            icu_flag,
            readmission_flag,
            emergency_flag,
            outcome
        )

        SELECT
            :admission_id,

            patient.patient_key,

            doctor.doctor_key,

            department.department_key,

            diagnosis.diagnosis_key,

            TO_CHAR(
                CAST(
                    :admission_timestamp
                    AS TIMESTAMP
                ),
                'YYYYMMDD'
            )::INTEGER,

            TO_CHAR(
                CAST(
                    :discharge_timestamp
                    AS TIMESTAMP
                ),
                'YYYYMMDD'
            )::INTEGER,

            CAST(
                :admission_timestamp
                AS TIMESTAMP
            ),

            CAST(
                :discharge_timestamp
                AS TIMESTAMP
            ),

            :admission_type,

            :room_type,

            :bed_number,

            :length_of_stay,

            :icu_flag,

            :readmission_flag,

            :emergency_flag,

            :outcome

        FROM warehouse.dim_patient
            AS patient

        JOIN warehouse.dim_doctor
            AS doctor

            ON doctor.doctor_id =
                :doctor_id

        JOIN warehouse.dim_department
            AS department

            ON department.department_id =
                :department_id

        JOIN warehouse.dim_diagnosis
            AS diagnosis

            ON diagnosis.diagnosis_code =
                :diagnosis_code

        WHERE patient.patient_id =
            :patient_id

        ON CONFLICT (admission_id)
        DO NOTHING
        """
    )

    connection.execute(
        sql,
        records(dataframe),
    )

    logger.info(
        "Processed %s admission fact rows.",
        f"{len(dataframe):,}",
    )


# ============================================================
# BILLING FACT
# ============================================================

def load_billing(
    connection,
    dataframe: pd.DataFrame,
):

    if dataframe.empty:
        return

    sql = text(
        """
        INSERT INTO warehouse.fact_billing
        (
            bill_id,
            admission_key,
            patient_key,
            billing_date_key,
            room_charge,
            doctor_charge,
            procedure_charge,
            medication_charge,
            lab_charge,
            other_charge,
            gross_amount,
            discount_amount,
            insurance_amount,
            patient_amount,
            tax_amount,
            net_amount,
            paid_amount,
            outstanding_amount,
            payment_status,
            payment_method
        )

        SELECT
            :bill_id,

            admission.admission_key,

            patient.patient_key,

            TO_CHAR(
                CAST(
                    :billing_date
                    AS TIMESTAMP
                ),
                'YYYYMMDD'
            )::INTEGER,

            :room_charge,
            :doctor_charge,
            :procedure_charge,
            :medication_charge,
            :lab_charge,
            :other_charge,
            :gross_amount,
            :discount_amount,
            :insurance_amount,
            :patient_amount,
            :tax_amount,
            :net_amount,
            :paid_amount,
            :outstanding_amount,
            :payment_status,
            :payment_method

        FROM warehouse.fact_admission
            AS admission

        JOIN warehouse.dim_patient
            AS patient

            ON patient.patient_id =
                :patient_id

        WHERE admission.admission_id =
            :admission_id

        ON CONFLICT (bill_id)
        DO NOTHING
        """
    )

    connection.execute(
        sql,
        records(dataframe),
    )

    logger.info(
        "Processed %s billing fact rows.",
        f"{len(dataframe):,}",
    )


# ============================================================
# CLAIM FACT
# ============================================================

def load_claims(
    connection,
    dataframe: pd.DataFrame,
):

    if dataframe.empty:
        return

    sql = text(
        """
        INSERT INTO warehouse.fact_claim
        (
            claim_id,
            billing_key,
            patient_key,
            insurer_key,
            submission_date_key,
            settlement_date_key,
            claim_amount,
            approved_amount,
            rejected_amount,
            claim_status,
            rejection_reason,
            processing_days
        )

        SELECT
            :claim_id,

            billing.billing_key,

            patient.patient_key,

            insurer.insurer_key,

            CASE
                WHEN :submission_date IS NULL
                THEN NULL

                ELSE TO_CHAR(
                    CAST(
                        :submission_date
                        AS TIMESTAMP
                    ),
                    'YYYYMMDD'
                )::INTEGER
            END,

            CASE
                WHEN :settlement_date IS NULL
                THEN NULL

                ELSE TO_CHAR(
                    CAST(
                        :settlement_date
                        AS TIMESTAMP
                    ),
                    'YYYYMMDD'
                )::INTEGER
            END,

            :claim_amount,
            :approved_amount,
            :rejected_amount,
            :claim_status,
            :rejection_reason,
            :processing_days

        FROM warehouse.fact_billing
            AS billing

        JOIN warehouse.dim_patient
            AS patient

            ON patient.patient_id =
                :patient_id

        JOIN warehouse.dim_insurer
            AS insurer

            ON insurer.insurer_id =
                :insurer_id

        WHERE billing.bill_id =
            :bill_id

        ON CONFLICT (claim_id)
        DO NOTHING
        """
    )

    connection.execute(
        sql,
        records(dataframe),
    )

    logger.info(
        "Processed %s claim fact rows.",
        f"{len(dataframe):,}",
    )


# ============================================================
# LAB FACT
# ============================================================

def load_labs(
    connection,
    dataframe: pd.DataFrame,
):

    if dataframe.empty:
        return

    sql = text(
        """
        INSERT INTO warehouse.fact_lab_test
        (
            lab_test_id,
            patient_key,
            admission_key,
            doctor_key,
            test_date_key,
            test_name,
            test_category,
            result_value,
            result_unit,
            result_status,
            test_cost,
            abnormal_flag
        )

        SELECT
            :lab_test_id,

            patient.patient_key,

            admission.admission_key,

            doctor.doctor_key,

            TO_CHAR(
                CAST(
                    :test_date
                    AS TIMESTAMP
                ),
                'YYYYMMDD'
            )::INTEGER,

            :test_name,
            :test_category,
            :result_value,
            :result_unit,
            :result_status,
            :test_cost,
            :abnormal_flag

        FROM warehouse.dim_patient
            AS patient

        JOIN warehouse.fact_admission
            AS admission

            ON admission.admission_id =
                :admission_id

        JOIN warehouse.dim_doctor
            AS doctor

            ON doctor.doctor_id =
                :doctor_id

        WHERE patient.patient_id =
            :patient_id

        ON CONFLICT (lab_test_id)
        DO NOTHING
        """
    )

    connection.execute(
        sql,
        records(dataframe),
    )

    logger.info(
        "Processed %s lab fact rows.",
        f"{len(dataframe):,}",
    )


# ============================================================
# MEDICATION FACT
# ============================================================

def load_medication_events(
    connection,
    dataframe: pd.DataFrame,
):

    if dataframe.empty:
        return

    sql = text(
        """
        INSERT INTO warehouse.fact_medication
        (
            medication_event_id,
            patient_key,
            admission_key,
            medication_key,
            prescribed_date_key,
            quantity,
            unit_price,
            total_amount
        )

        SELECT
            :medication_event_id,

            patient.patient_key,

            admission.admission_key,

            medication.medication_key,

            TO_CHAR(
                CAST(
                    :prescribed_date
                    AS TIMESTAMP
                ),
                'YYYYMMDD'
            )::INTEGER,

            :quantity,
            :unit_price,
            :total_amount

        FROM warehouse.dim_patient
            AS patient

        JOIN warehouse.fact_admission
            AS admission

            ON admission.admission_id =
                :admission_id

        JOIN warehouse.dim_medication
            AS medication

            ON medication.medication_id =
                :medication_id

        WHERE patient.patient_id =
            :patient_id

        ON CONFLICT (medication_event_id)
        DO NOTHING
        """
    )

    connection.execute(
        sql,
        records(dataframe),
    )

    logger.info(
        "Processed %s medication fact rows.",
        f"{len(dataframe):,}",
    )