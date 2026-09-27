import pandas as pd


def clean_string_columns(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:

    df = dataframe.copy()

    for column in df.columns:

        if df[column].dtype == "object":

            df[column] = (
                df[column]
                .astype("string")
                .str.strip()
            )

    return df


def transform_patients(
    df: pd.DataFrame,
) -> pd.DataFrame:

    df = clean_string_columns(
        df
    )

    df["date_of_birth"] = pd.to_datetime(
        df["date_of_birth"],
        errors="coerce",
    ).dt.date

    df["registration_date"] = pd.to_datetime(
        df["registration_date"],
        errors="coerce",
    ).dt.date

    return df


def transform_doctors(
    df: pd.DataFrame,
) -> pd.DataFrame:

    df = clean_string_columns(
        df
    )

    df["experience_years"] = pd.to_numeric(
        df["experience_years"],
        errors="coerce",
    )

    df["consultation_fee"] = pd.to_numeric(
        df["consultation_fee"],
        errors="coerce",
    )

    df["joining_date"] = pd.to_datetime(
        df["joining_date"],
        errors="coerce",
    ).dt.date

    return df


def transform_admissions(
    df: pd.DataFrame,
) -> pd.DataFrame:

    df = clean_string_columns(
        df
    )

    df["admission_timestamp"] = pd.to_datetime(
        df["admission_timestamp"]
    )

    df["discharge_timestamp"] = pd.to_datetime(
        df["discharge_timestamp"]
    )

    df["length_of_stay"] = pd.to_numeric(
        df["length_of_stay"],
        errors="coerce",
    )

    for column in [
        "icu_flag",
        "readmission_flag",
        "emergency_flag",
    ]:

        df[column] = (
            df[column]
            .astype(str)
            .str.lower()
            .map(
                {
                    "true": True,
                    "false": False,
                    "1": True,
                    "0": False,
                }
            )
        )

    return df


def transform_billing(
    df: pd.DataFrame,
) -> pd.DataFrame:

    df = clean_string_columns(
        df
    )

    df["billing_date"] = pd.to_datetime(
        df["billing_date"]
    )

    financial_columns = [
        "room_charge",
        "doctor_charge",
        "procedure_charge",
        "medication_charge",
        "lab_charge",
        "other_charge",
        "gross_amount",
        "discount_amount",
        "insurance_amount",
        "patient_amount",
        "tax_amount",
        "net_amount",
        "paid_amount",
        "outstanding_amount",
    ]

    for column in financial_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    return df


def transform_claims(
    df: pd.DataFrame,
) -> pd.DataFrame:

    df = clean_string_columns(
        df
    )

    df["submission_date"] = pd.to_datetime(
        df["submission_date"],
        errors="coerce",
    )

    df["settlement_date"] = pd.to_datetime(
        df["settlement_date"],
        errors="coerce",
    )

    for column in [
        "claim_amount",
        "approved_amount",
        "rejected_amount",
        "processing_days",
    ]:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    return df


def transform_labs(
    df: pd.DataFrame,
) -> pd.DataFrame:

    df = clean_string_columns(
        df
    )

    df["test_date"] = pd.to_datetime(
        df["test_date"]
    )

    df["test_cost"] = pd.to_numeric(
        df["test_cost"],
        errors="coerce",
    )

    df["abnormal_flag"] = (
        df["abnormal_flag"]
        .astype(str)
        .str.lower()
        .map(
            {
                "true": True,
                "false": False,
                "1": True,
                "0": False,
            }
        )
    )

    return df


def transform_medication_master(
    df: pd.DataFrame,
) -> pd.DataFrame:

    df = clean_string_columns(
        df
    )

    df["unit_cost"] = pd.to_numeric(
        df["unit_cost"],
        errors="coerce",
    )

    return df


def transform_medication_events(
    df: pd.DataFrame,
) -> pd.DataFrame:

    df = clean_string_columns(
        df
    )

    df["prescribed_date"] = pd.to_datetime(
        df["prescribed_date"]
    )

    df["quantity"] = pd.to_numeric(
        df["quantity"],
        errors="coerce",
    )

    df["unit_price"] = pd.to_numeric(
        df["unit_price"],
        errors="coerce",
    )

    df["total_amount"] = pd.to_numeric(
        df["total_amount"],
        errors="coerce",
    )

    return df


TRANSFORMERS = {
    "patients":
        transform_patients,

    "doctors":
        transform_doctors,

    "admissions":
        transform_admissions,

    "billing":
        transform_billing,

    "claims":
        transform_claims,

    "labs":
        transform_labs,

    "medication_master":
        transform_medication_master,

    "medication_events":
        transform_medication_events,
}


def transform_all(
    datasets: dict[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:

    transformed = {}

    for name, dataframe in datasets.items():

        transformed[name] = (
            TRANSFORMERS[name](
                dataframe
            )
        )

    return transformed