import random
from datetime import date

import pandas as pd
from faker import Faker

from generator.config import CONFIG


fake = Faker("en_IN")


BLOOD_GROUPS = [
    "A+",
    "A-",
    "B+",
    "B-",
    "AB+",
    "AB-",
    "O+",
    "O-",
]


CHRONIC_CONDITIONS = [
    "Hypertension",
    "Type 2 Diabetes",
    "Asthma",
    "Coronary Artery Disease",
    "Chronic Kidney Disease",
    "Migraine",
]


STATES = [
    "Uttar Pradesh",
    "Delhi",
    "Haryana",
    "Rajasthan",
    "Uttarakhand",
    "Punjab",
    "Madhya Pradesh",
]


def generate_patients(
    count: int = CONFIG.patient_count,
    start_number: int = 1,
) -> pd.DataFrame:

    records = []

    today = date.today()

    for number in range(
        start_number,
        start_number + count,
    ):

        gender = random.choices(
            [
                "Male",
                "Female",
                "Other",
            ],
            weights=[
                50,
                49,
                1,
            ],
            k=1,
        )[0]

        dob = fake.date_of_birth(
            minimum_age=1,
            maximum_age=95,
        )

        age = (
            today.year
            - dob.year
            - (
                (today.month, today.day)
                <
                (dob.month, dob.day)
            )
        )

        chronic_probability = (
            0.15
            if age < 40
            else 0.35
            if age < 65
            else 0.60
        )

        chronic_condition = None

        if random.random() < chronic_probability:
            chronic_condition = random.choice(
                CHRONIC_CONDITIONS
            )

        insured = (
            random.random()
            <
            CONFIG.insurance_probability
        )

        records.append(
            {
                "patient_id":
                    f"PAT-{number:07d}",

                "first_name":
                    fake.first_name(),

                "last_name":
                    fake.last_name(),

                "gender":
                    gender,

                "date_of_birth":
                    dob,

                "blood_group":
                    random.choice(
                        BLOOD_GROUPS
                    ),

                "city":
                    fake.city(),

                "state":
                    random.choice(
                        STATES
                    ),

                "insurance_status":
                    (
                        "Insured"
                        if insured
                        else "Self Pay"
                    ),

                "chronic_condition":
                    chronic_condition,

                "registration_date":
                    fake.date_between(
                        start_date="-8y",
                        end_date="today",
                    ),
            }
        )

    return pd.DataFrame(records)