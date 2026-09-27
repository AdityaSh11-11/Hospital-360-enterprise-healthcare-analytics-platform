import sys
from pathlib import Path

import pandas as pd


RAW = Path("data/raw")
INC = Path("data/incremental")


def latest_batch():

    batches = sorted(
        [
            path
            for path in INC.glob("BATCH-*")
            if path.is_dir()
        ]
    )

    if not batches:

        raise RuntimeError(
            "No incremental batches found."
        )

    return batches[-1]


def read_batch(
    batch,
    filename,
):

    return pd.read_csv(
        batch / filename
    )


def previous_files(
    current_batch,
    filename,
):

    files = []

    initial = RAW / filename

    if initial.exists():
        files.append(initial)

    for batch in sorted(
        INC.glob("BATCH-*")
    ):

        if batch == current_batch:
            continue

        path = batch / filename

        if path.exists():
            files.append(path)

    return files


def collect_ids(
    files,
    column,
):

    values = set()

    for path in files:

        df = pd.read_csv(
            path,
            usecols=[column],
        )

        values.update(
            df[column]
            .astype(str)
            .tolist()
        )

    return values


def main():

    batch = latest_batch()

    print()
    print("=" * 70)
    print(
        "HOSPITAL 360 — INCREMENTAL VALIDATION"
    )
    print("=" * 70)

    print(
        f"Validating: {batch.name}"
    )

    patients = read_batch(
        batch,
        "patients.csv",
    )

    admissions = read_batch(
        batch,
        "admissions.csv",
    )

    billing = read_batch(
        batch,
        "billing.csv",
    )

    claims = read_batch(
        batch,
        "claims.csv",
    )

    labs = read_batch(
        batch,
        "labs.csv",
    )

    medications = read_batch(
        batch,
        "medication_events.csv",
    )

    # ------------------------------------------------------
    # DUPLICATES WITHIN BATCH
    # ------------------------------------------------------

    tests = [
        (
            patients,
            "patient_id",
        ),
        (
            admissions,
            "admission_id",
        ),
        (
            billing,
            "bill_id",
        ),
        (
            claims,
            "claim_id",
        ),
        (
            labs,
            "lab_test_id",
        ),
        (
            medications,
            "medication_event_id",
        ),
    ]

    for dataframe, column in tests:

        assert not dataframe[
            column
        ].duplicated().any(), (
            f"Duplicate {column} "
            f"inside current batch."
        )

    print(
        "[PASS] No duplicates inside batch"
    )

    # ------------------------------------------------------
    # DUPLICATES AGAINST HISTORY
    # ------------------------------------------------------

    checks = [
        (
            "patients.csv",
            patients,
            "patient_id",
        ),
        (
            "admissions.csv",
            admissions,
            "admission_id",
        ),
        (
            "billing.csv",
            billing,
            "bill_id",
        ),
        (
            "claims.csv",
            claims,
            "claim_id",
        ),
        (
            "labs.csv",
            labs,
            "lab_test_id",
        ),
        (
            "medication_events.csv",
            medications,
            "medication_event_id",
        ),
    ]

    for (
        filename,
        dataframe,
        column,
    ) in checks:

        historical_ids = collect_ids(
            previous_files(
                batch,
                filename,
            ),
            column,
        )

        current_ids = set(
            dataframe[
                column
            ].astype(str)
        )

        collision = (
            current_ids
            &
            historical_ids
        )

        assert not collision, (
            f"{column} collisions "
            f"with historical data: "
            f"{list(collision)[:5]}"
        )

    print(
        "[PASS] No historical ID collisions"
    )

    # ------------------------------------------------------
    # BATCH ID
    # ------------------------------------------------------

    for dataframe in [
        patients,
        admissions,
        billing,
        claims,
        labs,
        medications,
    ]:

        assert (
            dataframe[
                "batch_id"
            ]
            == batch.name
        ).all()

    print(
        "[PASS] Batch IDs valid"
    )

    # ------------------------------------------------------
    # BILLING RELATIONSHIP
    # ------------------------------------------------------

    assert set(
        billing["admission_id"]
    ) == set(
        admissions["admission_id"]
    )

    print(
        "[PASS] Admission → Billing relationship"
    )

    # ------------------------------------------------------
    # CLAIM RELATIONSHIP
    # ------------------------------------------------------

    assert set(
        claims["bill_id"]
    ).issubset(
        set(
            billing["bill_id"]
        )
    )

    print(
        "[PASS] Billing → Claims relationship"
    )

    # ------------------------------------------------------
    # LAB RELATIONSHIP
    # ------------------------------------------------------

    assert set(
        labs["admission_id"]
    ).issubset(
        set(
            admissions[
                "admission_id"
            ]
        )
    )

    print(
        "[PASS] Admission → Labs relationship"
    )

    # ------------------------------------------------------
    # MEDICATION RELATIONSHIP
    # ------------------------------------------------------

    assert set(
        medications[
            "admission_id"
        ]
    ).issubset(
        set(
            admissions[
                "admission_id"
            ]
        )
    )

    print(
        "[PASS] Admission → Medication relationship"
    )

    # ------------------------------------------------------
    # FINANCE
    # ------------------------------------------------------

    financial_columns = [
        "gross_amount",
        "net_amount",
        "paid_amount",
        "outstanding_amount",
    ]

    for column in financial_columns:

        assert (
            billing[column] >= 0
        ).all()

    print(
        "[PASS] Financial values valid"
    )

    # ------------------------------------------------------
    # DATE LOGIC
    # ------------------------------------------------------

    admission_date = pd.to_datetime(
        admissions[
            "admission_timestamp"
        ]
    )

    discharge_date = pd.to_datetime(
        admissions[
            "discharge_timestamp"
        ]
    )

    assert (
        discharge_date
        >= admission_date
    ).all()

    print(
        "[PASS] Admission dates valid"
    )

    print()
    print("-" * 70)

    print(
        f"New patients          : "
        f"{len(patients):,}"
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
        "PHASE 3 INCREMENTAL VALIDATION PASSED"
    )
    print("=" * 70)


if __name__ == "__main__":

    try:
        main()

    except Exception as exc:

        print()
        print(
            f"[FAIL] {exc}"
        )

        sys.exit(1)