import random

import pandas as pd
from faker import Faker

from generator.config import CONFIG


fake = Faker("en_IN")


SPECIALIZATIONS = {
    "DEP001": [
        "Emergency Medicine",
        "Trauma Medicine",
    ],

    "DEP002": [
        "Cardiology",
        "Interventional Cardiology",
    ],

    "DEP003": [
        "Neurology",
        "Neurophysiology",
    ],

    "DEP004": [
        "Orthopedics",
        "Sports Medicine",
    ],

    "DEP005": [
        "Pediatrics",
        "Neonatology",
    ],

    "DEP006": [
        "Internal Medicine",
        "General Medicine",
    ],

    "DEP007": [
        "Medical Oncology",
        "Clinical Oncology",
    ],

    "DEP008": [
        "Gynecology",
        "Obstetrics",
    ],

    "DEP009": [
        "ENT",
        "Otolaryngology",
    ],

    "DEP010": [
        "Dermatology",
        "Clinical Dermatology",
    ],
}


QUALIFICATIONS = [
    "MBBS, MD",
    "MBBS, MS",
    "MBBS, DNB",
    "MBBS, MD, DM",
    "MBBS, MS, MCh",
]


def generate_doctors(
    count: int = CONFIG.doctor_count,
) -> pd.DataFrame:

    records = []

    department_ids = list(
        SPECIALIZATIONS.keys()
    )

    for number in range(
        1,
        count + 1,
    ):

        department_id = random.choice(
            department_ids
        )

        experience = random.randint(
            1,
            35,
        )

        consultation_fee = random.choice(
            [
                500,
                700,
                800,
                1000,
                1200,
                1500,
                1800,
                2000,
                2500,
            ]
        )

        gender = random.choices(
            ["Male", "Female"],
            weights=[55, 45],
            k=1,
        )[0]

        name = (
            fake.name_male()
            if gender == "Male"
            else fake.name_female()
        )

        records.append(
            {
                "doctor_id":
                    f"DOC-{number:05d}",

                "doctor_name":
                    f"Dr. {name}",

                "gender":
                    gender,

                "specialization":
                    random.choice(
                        SPECIALIZATIONS[
                            department_id
                        ]
                    ),

                "department_id":
                    department_id,

                "qualification":
                    random.choice(
                        QUALIFICATIONS
                    ),

                "experience_years":
                    experience,

                "consultation_fee":
                    consultation_fee,

                "joining_date":
                    fake.date_between(
                        start_date="-15y",
                        end_date="-30d",
                    ),

                "employment_status":
                    random.choices(
                        [
                            "Active",
                            "On Leave",
                        ],
                        weights=[97, 3],
                        k=1,
                    )[0],
            }
        )

    return pd.DataFrame(records)