from dataclasses import dataclass, field

import pandas as pd


@dataclass
class ValidationIssue:

    dataset: str

    rule_name: str

    reason: str

    record_identifier: str | None = None

    record_data: dict | None = None


@dataclass
class ValidationResult:

    valid: dict[str, pd.DataFrame] = field(
        default_factory=dict
    )

    issues: list[ValidationIssue] = field(
        default_factory=list
    )


PRIMARY_KEYS = {
    "doctors": "doctor_id",
    "patients": "patient_id",
    "admissions": "admission_id",
    "billing": "bill_id",
    "claims": "claim_id",
    "labs": "lab_test_id",
    "medication_master": "medication_id",
    "medication_events": "medication_event_id",
}


REQUIRED_COLUMNS = {
    "doctors": [
        "doctor_id",
        "doctor_name",
        "department_id",
    ],

    "patients": [
        "patient_id",
        "gender",
        "date_of_birth",
    ],

    "admissions": [
        "admission_id",
        "patient_id",
        "doctor_id",
        "department_id",
        "diagnosis_code",
        "admission_timestamp",
        "discharge_timestamp",
    ],

    "billing": [
        "bill_id",
        "admission_id",
        "patient_id",
        "gross_amount",
        "net_amount",
    ],

    "claims": [
        "claim_id",
        "bill_id",
        "patient_id",
        "insurer_id",
        "claim_amount",
    ],

    "labs": [
        "lab_test_id",
        "patient_id",
        "admission_id",
        "doctor_id",
        "test_date",
        "test_name",
    ],

    "medication_master": [
        "medication_id",
        "medication_name",
        "unit_cost",
    ],

    "medication_events": [
        "medication_event_id",
        "patient_id",
        "admission_id",
        "medication_id",
        "prescribed_date",
        "quantity",
    ],
}


def normalize_nulls(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:

    df = dataframe.copy()

    df = df.replace(
        {
            "": pd.NA,
            "NULL": pd.NA,
            "null": pd.NA,
            "None": pd.NA,
            "nan": pd.NA,
        }
    )

    return df


def validate_required_columns(
    dataset: str,
    dataframe: pd.DataFrame,
):

    expected = REQUIRED_COLUMNS[
        dataset
    ]

    missing = [
        column
        for column in expected
        if column not in dataframe.columns
    ]

    if missing:

        raise ValueError(
            f"{dataset}: missing required "
            f"columns {missing}"
        )


def reject_mask(
    dataset: str,
    dataframe: pd.DataFrame,
    mask: pd.Series,
    rule_name: str,
    reason: str,
    issues: list[ValidationIssue],
) -> pd.DataFrame:

    rejected = dataframe[
        mask
    ]

    key = PRIMARY_KEYS[
        dataset
    ]

    for _, row in rejected.iterrows():

        identifier = row.get(
            key
        )

        issues.append(
            ValidationIssue(
                dataset=dataset,
                rule_name=rule_name,
                reason=reason,
                record_identifier=(
                    None
                    if pd.isna(identifier)
                    else str(identifier)
                ),
                record_data={
                    str(k): (
                        None
                        if pd.isna(v)
                        else str(v)
                    )
                    for k, v
                    in row.to_dict().items()
                },
            )
        )

    return dataframe[
        ~mask
    ].copy()


def validate_dataset(
    dataset: str,
    dataframe: pd.DataFrame,
    issues: list[ValidationIssue],
) -> pd.DataFrame:

    validate_required_columns(
        dataset,
        dataframe,
    )

    df = normalize_nulls(
        dataframe
    )

    key = PRIMARY_KEYS[
        dataset
    ]

    # --------------------------------------------------------
    # PRIMARY ID REQUIRED
    # --------------------------------------------------------

    mask = df[key].isna()

    df = reject_mask(
        dataset,
        df,
        mask,
        "PRIMARY_KEY_NOT_NULL",
        f"{key} cannot be null.",
        issues,
    )

    # --------------------------------------------------------
    # DUPLICATE IDS
    # --------------------------------------------------------

    mask = df[
        key
    ].duplicated(
        keep="first"
    )

    df = reject_mask(
        dataset,
        df,
        mask,
        "DUPLICATE_BUSINESS_KEY",
        f"Duplicate {key}.",
        issues,
    )

    # --------------------------------------------------------
    # DATASET SPECIFIC RULES
    # --------------------------------------------------------

    if dataset == "patients":

        valid_gender = [
            "Male",
            "Female",
            "Other",
        ]

        mask = (
            df["gender"].notna()
            &
            ~df["gender"].isin(
                valid_gender
            )
        )

        df = reject_mask(
            dataset,
            df,
            mask,
            "VALID_GENDER",
            "Invalid patient gender.",
            issues,
        )

        dob = pd.to_datetime(
            df["date_of_birth"],
            errors="coerce",
        )

        mask = dob.isna()

        df = reject_mask(
            dataset,
            df,
            mask,
            "VALID_DATE_OF_BIRTH",
            "Invalid date of birth.",
            issues,
        )

    elif dataset == "admissions":

        admission = pd.to_datetime(
            df["admission_timestamp"],
            errors="coerce",
        )

        discharge = pd.to_datetime(
            df["discharge_timestamp"],
            errors="coerce",
        )

        mask = (
            admission.isna()
            |
            discharge.isna()
            |
            (discharge < admission)
        )

        df = reject_mask(
            dataset,
            df,
            mask,
            "VALID_ADMISSION_DATES",
            (
                "Admission/discharge timestamps "
                "are invalid."
            ),
            issues,
        )

    elif dataset == "billing":

        financial_columns = [
            "gross_amount",
            "discount_amount",
            "insurance_amount",
            "patient_amount",
            "tax_amount",
            "net_amount",
            "paid_amount",
            "outstanding_amount",
        ]

        invalid = pd.Series(
            False,
            index=df.index,
        )

        for column in financial_columns:

            values = pd.to_numeric(
                df[column],
                errors="coerce",
            )

            invalid = (
                invalid
                |
                values.isna()
                |
                (values < 0)
            )

        df = reject_mask(
            dataset,
            df,
            invalid,
            "NON_NEGATIVE_FINANCIALS",
            "Billing contains invalid financial values.",
            issues,
        )

    elif dataset == "claims":

        claim = pd.to_numeric(
            df["claim_amount"],
            errors="coerce",
        )

        approved = pd.to_numeric(
            df["approved_amount"],
            errors="coerce",
        )

        rejected = pd.to_numeric(
            df["rejected_amount"],
            errors="coerce",
        )

        mask = (
            claim.isna()
            |
            approved.isna()
            |
            rejected.isna()
            |
            (claim < 0)
            |
            (approved < 0)
            |
            (rejected < 0)
            |
            (approved > claim)
            |
            (rejected > claim)
        )

        df = reject_mask(
            dataset,
            df,
            mask,
            "VALID_CLAIM_AMOUNTS",
            "Invalid insurance claim amounts.",
            issues,
        )

    elif dataset == "labs":

        cost = pd.to_numeric(
            df["test_cost"],
            errors="coerce",
        )

        mask = (
            cost.isna()
            |
            (cost < 0)
        )

        df = reject_mask(
            dataset,
            df,
            mask,
            "VALID_LAB_COST",
            "Invalid laboratory test cost.",
            issues,
        )

    elif dataset == "medication_events":

        quantity = pd.to_numeric(
            df["quantity"],
            errors="coerce",
        )

        total = pd.to_numeric(
            df["total_amount"],
            errors="coerce",
        )

        mask = (
            quantity.isna()
            |
            total.isna()
            |
            (quantity <= 0)
            |
            (total < 0)
        )

        df = reject_mask(
            dataset,
            df,
            mask,
            "VALID_MEDICATION_VALUES",
            "Invalid medication quantity or amount.",
            issues,
        )

    return df


def validate_all(
    datasets: dict[str, pd.DataFrame],
) -> ValidationResult:

    result = ValidationResult()

    for dataset, dataframe in datasets.items():

        result.valid[
            dataset
        ] = validate_dataset(
            dataset,
            dataframe,
            result.issues,
        )

    return result