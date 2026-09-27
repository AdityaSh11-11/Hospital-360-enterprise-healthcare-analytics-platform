from pathlib import Path

import pandas as pd


RAW = Path("data/raw")


def load(name):
    return pd.read_csv(
        RAW / name
    )


def assert_unique(
    dataframe,
    column,
):
    duplicates = dataframe[
        column
    ].duplicated().sum()

    assert duplicates == 0, (
        f"{column} contains "
        f"{duplicates} duplicates."
    )


def main():

    print()
    print("=" * 70)
    print(
        "HOSPITAL 360 — GENERATED DATA VALIDATION"
    )
    print("=" * 70)

    doctors = load(
        "doctors.csv"
    )

    patients = load(
        "patients.csv"
    )

    admissions = load(
        "admissions.csv"
    )

    billing = load(
        "billing.csv"
    )

    claims = load(
        "claims.csv"
    )

    labs = load(
        "labs.csv"
    )

    medications = load(
        "medication_events.csv"
    )

    # --------------------------------------------------------
    # UNIQUE IDS
    # --------------------------------------------------------

    assert_unique(
        doctors,
        "doctor_id",
    )

    assert_unique(
        patients,
        "patient_id",
    )

    assert_unique(
        admissions,
        "admission_id",
    )

    assert_unique(
        billing,
        "bill_id",
    )

    assert_unique(
        claims,
        "claim_id",
    )

    assert_unique(
        labs,
        "lab_test_id",
    )

    assert_unique(
        medications,
        "medication_event_id",
    )

    print(
        "[PASS] Unique identifier checks"
    )

    # --------------------------------------------------------
    # REFERENTIAL INTEGRITY
    # --------------------------------------------------------

    invalid_patients = (
        ~admissions[
            "patient_id"
        ].isin(
            patients[
                "patient_id"
            ]
        )
    ).sum()

    assert invalid_patients == 0

    invalid_doctors = (
        ~admissions[
            "doctor_id"
        ].isin(
            doctors[
                "doctor_id"
            ]
        )
    ).sum()

    assert invalid_doctors == 0

    invalid_bills = (
        ~billing[
            "admission_id"
        ].isin(
            admissions[
                "admission_id"
            ]
        )
    ).sum()

    assert invalid_bills == 0

    invalid_claim_bills = (
        ~claims[
            "bill_id"
        ].isin(
            billing[
                "bill_id"
            ]
        )
    ).sum()

    assert invalid_claim_bills == 0

    print(
        "[PASS] Referential integrity checks"
    )

    # --------------------------------------------------------
    # FINANCIAL CHECKS
    # --------------------------------------------------------

    assert (
        billing["gross_amount"] >= 0
    ).all()

    assert (
        billing["net_amount"] >= 0
    ).all()

    assert (
        billing["outstanding_amount"] >= 0
    ).all()

    print(
        "[PASS] Financial validation"
    )

    # --------------------------------------------------------
    # DATE CHECKS
    # --------------------------------------------------------

    admission_dates = pd.to_datetime(
        admissions[
            "admission_timestamp"
        ]
    )

    discharge_dates = pd.to_datetime(
        admissions[
            "discharge_timestamp"
        ]
    )

    assert (
        discharge_dates
        >= admission_dates
    ).all()

    print(
        "[PASS] Admission date validation"
    )

    # --------------------------------------------------------
    # RELATIONAL COUNTS
    # --------------------------------------------------------

    assert len(billing) == len(
        admissions
    )

    print(
        "[PASS] One bill per admission"
    )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print()
    print("-" * 70)

    print(
        f"Patients              : "
        f"{len(patients):,}"
    )

    print(
        f"Doctors               : "
        f"{len(doctors):,}"
    )

    print(
        f"Admissions            : "
        f"{len(admissions):,}"
    )

    print(
        f"Bills                 : "
        f"{len(billing):,}"
    )

    print(
        f"Claims                : "
        f"{len(claims):,}"
    )

    print(
        f"Lab Tests             : "
        f"{len(labs):,}"
    )

    print(
        f"Medication Events     : "
        f"{len(medications):,}"
    )

    print()
    print("=" * 70)
    print(
        "PHASE 2 DATA VALIDATION PASSED"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()