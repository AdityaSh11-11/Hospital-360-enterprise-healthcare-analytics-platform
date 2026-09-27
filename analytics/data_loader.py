from __future__ import annotations

from typing import Iterable

import pandas as pd
from sqlalchemy import text

from database.connection import engine


ALLOWED_SCHEMAS = {
    "warehouse",
    "analytics",
    "control",
}


def _validate_identifier(value: str) -> str:
    """
    Allow only simple PostgreSQL identifiers.

    This protects helper functions that dynamically construct
    schema/table/view names.
    """

    if not value:
        raise ValueError("Identifier cannot be empty.")

    cleaned = value.replace("_", "")

    if not cleaned.isalnum():
        raise ValueError(
            f"Unsafe SQL identifier: {value}"
        )

    return value


def read_sql(
    query: str,
    params: dict | None = None,
) -> pd.DataFrame:
    """
    Execute a read-only SQL query and return a Pandas DataFrame.
    """

    query_text = query.strip()

    if not query_text:
        raise ValueError("Query cannot be empty.")

    first_keyword = (
        query_text
        .lstrip("(")
        .split(maxsplit=1)[0]
        .upper()
    )

    allowed_keywords = {
        "SELECT",
        "WITH",
    }

    if first_keyword not in allowed_keywords:
        raise ValueError(
            "EDA data loader accepts only SELECT/WITH queries."
        )

    with engine.connect() as connection:
        return pd.read_sql_query(
            text(query),
            connection,
            params=params,
        )


def load_table(
    schema_name: str,
    object_name: str,
    columns: Iterable[str] | None = None,
    limit: int | None = None,
) -> pd.DataFrame:
    """
    Load a warehouse or analytics object into Pandas.
    """

    schema_name = _validate_identifier(
        schema_name
    )

    object_name = _validate_identifier(
        object_name
    )

    if schema_name not in ALLOWED_SCHEMAS:
        raise ValueError(
            f"Schema not allowed: {schema_name}"
        )

    if columns:

        validated_columns = [
            _validate_identifier(column)
            for column in columns
        ]

        column_sql = ", ".join(
            f'"{column}"'
            for column in validated_columns
        )

    else:
        column_sql = "*"

    query = (
        f'SELECT {column_sql} '
        f'FROM "{schema_name}"."{object_name}"'
    )

    if limit is not None:

        if limit <= 0:
            raise ValueError(
                "limit must be greater than zero."
            )

        query += f" LIMIT {int(limit)}"

    return read_sql(query)


def load_executive_kpis() -> pd.DataFrame:
    return load_table(
        "analytics",
        "vw_executive_kpis",
    )


def load_operations_summary() -> pd.DataFrame:
    return load_table(
        "analytics",
        "vw_operations_summary",
    )


def load_finance_summary() -> pd.DataFrame:
    return load_table(
        "analytics",
        "vw_finance_summary",
    )


def load_claims_summary() -> pd.DataFrame:
    return load_table(
        "analytics",
        "vw_claims_summary",
    )


def load_department_performance() -> pd.DataFrame:
    return load_table(
        "analytics",
        "vw_department_performance",
    )


def load_doctor_performance() -> pd.DataFrame:
    return load_table(
        "analytics",
        "vw_doctor_analytics_summary",
    )


def load_patient_demographics() -> pd.DataFrame:
    return load_table(
        "analytics",
        "vw_patient_demographics",
    )


def load_monthly_hospital_performance() -> pd.DataFrame:
    return load_table(
        "analytics",
        "vw_hospital_monthly_comparison",
    )


def load_admission_analysis_dataset() -> pd.DataFrame:
    """
    Admission-level analytical dataset.

    Grain:
        One row per admission.

    Billing is joined one-to-one through admission_key.
    No lab/medication facts are joined here, preventing
    accidental row multiplication.
    """

    query = """
        SELECT
            a.admission_key,
            a.admission_id,

            a.patient_key,
            p.patient_id,
            p.gender AS patient_gender,
            p.date_of_birth,
            p.city,
            p.state,
            p.insurance_status,
            p.chronic_condition,

            a.doctor_key,
            d.doctor_id,
            d.doctor_name,
            d.specialization,

            a.department_key,
            dep.department_id,
            dep.department_name,
            dep.department_type,
            dep.bed_capacity,

            a.diagnosis_key,
            dx.diagnosis_code,
            dx.diagnosis_name,
            dx.diagnosis_category,
            dx.chronic_flag AS diagnosis_chronic_flag,

            ad.full_date AS admission_date,
            dd.full_date AS discharge_date,

            a.admission_timestamp,
            a.discharge_timestamp,

            a.admission_type,
            a.room_type,
            a.length_of_stay,

            a.icu_flag,
            a.readmission_flag,
            a.emergency_flag,
            a.outcome,

            b.billing_key,
            b.bill_id,
            bd.full_date AS billing_date,

            b.gross_amount,
            b.discount_amount,
            b.insurance_amount,
            b.patient_amount,
            b.tax_amount,
            b.net_amount,
            b.paid_amount,
            b.outstanding_amount,
            b.payment_status,
            b.payment_method

        FROM warehouse.fact_admission a

        INNER JOIN warehouse.dim_patient p
            ON p.patient_key = a.patient_key

        INNER JOIN warehouse.dim_doctor d
            ON d.doctor_key = a.doctor_key

        INNER JOIN warehouse.dim_department dep
            ON dep.department_key = a.department_key

        INNER JOIN warehouse.dim_diagnosis dx
            ON dx.diagnosis_key = a.diagnosis_key

        INNER JOIN warehouse.dim_date ad
            ON ad.date_key = a.admission_date_key

        LEFT JOIN warehouse.dim_date dd
            ON dd.date_key = a.discharge_date_key

        LEFT JOIN warehouse.fact_billing b
            ON b.admission_key = a.admission_key

        LEFT JOIN warehouse.dim_date bd
            ON bd.date_key = b.billing_date_key
    """

    dataframe = read_sql(query)

    date_columns = [
        "date_of_birth",
        "admission_date",
        "discharge_date",
        "admission_timestamp",
        "discharge_timestamp",
        "billing_date",
    ]

    for column in date_columns:
        if column in dataframe.columns:
            dataframe[column] = pd.to_datetime(
                dataframe[column],
                errors="coerce",
            )

    return dataframe