import random
from typing import Any, cast

import pandas as pd

from generator.config import CONFIG
from generator.helpers import money


LAB_TESTS = [
    (
        "Complete Blood Count",
        "Hematology",
        650,
    ),
    (
        "Blood Glucose",
        "Biochemistry",
        300,
    ),
    (
        "Lipid Profile",
        "Biochemistry",
        900,
    ),
    (
        "Kidney Function Test",
        "Biochemistry",
        1100,
    ),
    (
        "Liver Function Test",
        "Biochemistry",
        1200,
    ),
    (
        "Thyroid Profile",
        "Endocrinology",
        1000,
    ),
    (
        "Urine Routine",
        "Pathology",
        350,
    ),
    (
        "Troponin",
        "Cardiac",
        1400,
    ),
]


def generate_labs(
    admissions: pd.DataFrame,
    start_number: int = 1,
) -> pd.DataFrame:

    records = []

    event_number = start_number

    for admission in admissions.itertuples(
        index=False
    ):

        number_of_tests = random.randint(
            CONFIG.min_labs_per_admission,
            CONFIG.max_labs_per_admission,
        )

        for _ in range(
            number_of_tests
        ):

            (
                test_name,
                category,
                base_cost,
            ) = random.choice(
                LAB_TESTS
            )

            abnormal_probability = (
                0.35
                if admission.icu_flag
                else 0.18
            )

            abnormal = (
                random.random()
                <
                abnormal_probability
            )

            admission_date = pd.Timestamp(
                cast(
                    Any,
                    admission.admission_timestamp,
                )
            )

            discharge_date = pd.Timestamp(
                cast(
                    Any,
                    admission.discharge_timestamp,
                )
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

            random_seconds = (
                random.randint(
                    0,
                    total_seconds,
                )
                if total_seconds > 0
                else 0
            )

            test_date = (
                admission_date
                + pd.Timedelta(
                    seconds=random_seconds
                )
            )

            records.append(
                {
                    "lab_test_id":
                        f"LAB-{event_number:09d}",

                    "patient_id":
                        admission.patient_id,

                    "admission_id":
                        admission.admission_id,

                    "doctor_id":
                        admission.doctor_id,

                    "test_date":
                        test_date,

                    "test_name":
                        test_name,

                    "test_category":
                        category,

                    "result_value":
                        (
                            "Abnormal"
                            if abnormal
                            else "Normal"
                        ),

                    "result_unit":
                        None,

                    "result_status":
                        (
                            "Abnormal"
                            if abnormal
                            else "Normal"
                        ),

                    "test_cost":
                        money(
                            base_cost
                            * random.uniform(
                                0.90,
                                1.20,
                            )
                        ),

                    "abnormal_flag":
                        abnormal,
                }
            )

            event_number += 1

    return pd.DataFrame(
        records
    )