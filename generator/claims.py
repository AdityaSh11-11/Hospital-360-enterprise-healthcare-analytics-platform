import random
from datetime import timedelta
from typing import Any, cast

import pandas as pd

from generator.helpers import money


REJECTION_REASONS = [
    "Missing Documentation",
    "Policy Exclusion",
    "Pre-authorization Missing",
    "Coverage Limit Exceeded",
    "Incorrect Coding",
    "Duplicate Claim",
]


def generate_claims(
    billing: pd.DataFrame,
    start_number: int = 1,
) -> pd.DataFrame:

    eligible = billing[
        billing[
            "insurance_amount"
        ] > 0
    ].copy()

    insurer_ids = [
        "INS001",
        "INS002",
        "INS003",
        "INS004",
        "INS005",
    ]

    records = []

    for number, row in enumerate(
        eligible.itertuples(
            index=False
        ),
        start=start_number,
    ):

        submission_date = (
            pd.Timestamp(
                cast(
                    Any,
                    row.billing_date,
                )
            )
            + timedelta(
                days=random.randint(
                    1,
                    7,
                )
            )
        )

        status = random.choices(
            [
                "Approved",
                "Partially Approved",
                "Rejected",
                "Pending",
            ],
            weights=[
                68,
                15,
                9,
                8,
            ],
            k=1,
        )[0]

        claim_amount = float(
            cast(
                Any,
                row.insurance_amount,
            )
        )

        approved_amount = 0.0
        rejected_amount = 0.0

        rejection_reason = None
        settlement_date = None

        if status == "Approved":

            approved_amount = (
                claim_amount
            )

            settlement_date = (
                submission_date
                + timedelta(
                    days=random.randint(
                        5,
                        30,
                    )
                )
            )

        elif status == "Partially Approved":

            approved_amount = (
                claim_amount
                * random.uniform(
                    0.55,
                    0.90,
                )
            )

            rejected_amount = (
                claim_amount
                - approved_amount
            )

            rejection_reason = (
                random.choice(
                    REJECTION_REASONS
                )
            )

            settlement_date = (
                submission_date
                + timedelta(
                    days=random.randint(
                        10,
                        45,
                    )
                )
            )

        elif status == "Rejected":

            rejected_amount = (
                claim_amount
            )

            rejection_reason = (
                random.choice(
                    REJECTION_REASONS
                )
            )

            settlement_date = (
                submission_date
                + timedelta(
                    days=random.randint(
                        5,
                        25,
                    )
                )
            )

        processing_days = None

        if settlement_date is not None:

            processing_days = (
                settlement_date
                - submission_date
            ).days

        records.append(
            {
                "claim_id":
                    f"CLM-{number:08d}",

                "bill_id":
                    row.bill_id,

                "patient_id":
                    row.patient_id,

                "insurer_id":
                    random.choice(
                        insurer_ids
                    ),

                "submission_date":
                    submission_date,

                "settlement_date":
                    settlement_date,

                "claim_amount":
                    money(
                        claim_amount
                    ),

                "approved_amount":
                    money(
                        approved_amount
                    ),

                "rejected_amount":
                    money(
                        rejected_amount
                    ),

                "claim_status":
                    status,

                "rejection_reason":
                    rejection_reason,

                "processing_days":
                    processing_days,
            }
        )

    return pd.DataFrame(
        records
    )