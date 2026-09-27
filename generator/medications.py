import random

import pandas as pd

from generator.config import CONFIG
from generator.helpers import money


MEDICATIONS = [
    (
        "MED001",
        "Paracetamol",
        "Analgesic",
        8.0,
    ),
    (
        "MED002",
        "Amoxicillin",
        "Antibiotic",
        18.0,
    ),
    (
        "MED003",
        "Metformin",
        "Antidiabetic",
        12.0,
    ),
    (
        "MED004",
        "Amlodipine",
        "Antihypertensive",
        10.0,
    ),
    (
        "MED005",
        "Atorvastatin",
        "Lipid Lowering",
        15.0,
    ),
    (
        "MED006",
        "Pantoprazole",
        "Gastrointestinal",
        9.0,
    ),
    (
        "MED007",
        "Azithromycin",
        "Antibiotic",
        25.0,
    ),
    (
        "MED008",
        "Aspirin",
        "Antiplatelet",
        5.0,
    ),
]


def medication_master() -> pd.DataFrame:

    records = []

    for (
        medication_id,
        medication_name,
        category,
        unit_cost,
    ) in MEDICATIONS:

        records.append(
            {
                "medication_id":
                    medication_id,

                "medication_name":
                    medication_name,

                "medication_category":
                    category,

                "manufacturer":
                    "Hospital 360 Pharma Demo",

                "unit_cost":
                    unit_cost,
            }
        )

    return pd.DataFrame(
        records
    )


def generate_medications(
    admissions: pd.DataFrame,
    start_number: int = 1,
) -> pd.DataFrame:

    records = []

    event_number = start_number

    for admission in admissions.itertuples(
        index=False
    ):

        event_count = random.randint(
            CONFIG.min_medications_per_admission,
            CONFIG.max_medications_per_admission,
        )

        admission_date = pd.Timestamp(
            str(admission.admission_timestamp)
        )

        discharge_date = pd.Timestamp(
            str(admission.discharge_timestamp)
        )

        total_seconds = max(
            int(
                (
                    discharge_date
                    - admission_date
                ).total_seconds()
            ),
            0,
        )

        for _ in range(
            event_count
        ):

            (
                medication_id,
                _,
                _,
                unit_cost,
            ) = random.choice(
                MEDICATIONS
            )

            quantity = random.randint(
                1,
                20,
            )

            random_seconds = (
                random.randint(
                    0,
                    total_seconds,
                )
                if total_seconds > 0
                else 0
            )

            prescribed_date = (
                admission_date
                + pd.Timedelta(
                    seconds=random_seconds
                )
            )

            records.append(
                {
                    "medication_event_id":
                        f"MEV-{event_number:09d}",

                    "patient_id":
                        admission.patient_id,

                    "admission_id":
                        admission.admission_id,

                    "medication_id":
                        medication_id,

                    "prescribed_date":
                        prescribed_date,

                    "quantity":
                        quantity,

                    "unit_price":
                        money(
                            unit_cost
                        ),

                    "total_amount":
                        money(
                            unit_cost
                            * quantity
                        ),
                }
            )

            event_number += 1

    return pd.DataFrame(
        records
    )