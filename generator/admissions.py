import random
from datetime import datetime, timedelta

import pandas as pd

from generator.config import CONFIG
from generator.helpers import random_date


# ============================================================
# DIAGNOSIS → DEPARTMENT MAPPING
# ============================================================

DIAGNOSIS_MAP = {
    "DEP001": [
        "DX003",
        "DX005",
        "DX009",
    ],
    "DEP002": [
        "DX001",
        "DX007",
    ],
    "DEP003": [
        "DX006",
    ],
    "DEP004": [
        "DX005",
    ],
    "DEP005": [
        "DX003",
        "DX004",
        "DX010",
    ],
    "DEP006": [
        "DX001",
        "DX002",
        "DX003",
        "DX009",
        "DX010",
    ],
    "DEP007": [
        "DX010",
    ],
    "DEP008": [
        "DX010",
    ],
    "DEP009": [
        "DX003",
    ],
    "DEP010": [
        "DX004",
    ],
}


# ============================================================
# ADMISSION GENERATOR
# ============================================================

def generate_admissions(
    patients: pd.DataFrame,
    doctors: pd.DataFrame,
    count: int = CONFIG.admission_count,
    start_number: int = 1,
    generation_start=None,
    generation_end=None,
    clip_discharge_to_end: bool = True,
) -> pd.DataFrame:
    """
    Generate synthetic hospital admissions.

    Parameters
    ----------
    patients:
        Patient master dataframe.

    doctors:
        Doctor master dataframe.

    count:
        Number of admissions to generate.

    start_number:
        Starting numeric portion of admission_id.

        Example:
            start_number=50001

            produces:
            ADM-00050001

    generation_start:
        Earliest allowed admission timestamp.

        If None, CONFIG.start_date is used.

    generation_end:
        Latest allowed admission timestamp.

        If None, CONFIG.end_date is used.

    clip_discharge_to_end:
        When True, discharge timestamps cannot exceed
        generation_end.

        This is useful for the initial historical dataset.

        When False, admissions may discharge after the
        business date.

        This is useful for incremental daily simulation.
    """

    # --------------------------------------------------------
    # BASIC VALIDATION
    # --------------------------------------------------------

    if patients.empty:
        raise ValueError(
            "Patient dataframe cannot be empty."
        )

    if doctors.empty:
        raise ValueError(
            "Doctor dataframe cannot be empty."
        )

    if count <= 0:
        raise ValueError(
            "Admission count must be greater than zero."
        )

    if start_number <= 0:
        raise ValueError(
            "start_number must be greater than zero."
        )

    # --------------------------------------------------------
    # DATE WINDOW
    # --------------------------------------------------------

    if generation_start is not None:

        start = (
            pd.Timestamp(
                generation_start
            )
            .to_pydatetime()
        )

    else:

        start = datetime.fromisoformat(
            CONFIG.start_date
        )

    if generation_end is not None:

        end = (
            pd.Timestamp(
                generation_end
            )
            .to_pydatetime()
        )

    else:

        end = datetime.fromisoformat(
            CONFIG.end_date
        )

    if start > end:
        raise ValueError(
            "generation_start cannot be after "
            "generation_end."
        )

    # --------------------------------------------------------
    # PREPARE DOCTOR GROUPS
    # --------------------------------------------------------

    doctor_groups = {
        department_id:
            group.to_dict(
                "records"
            )

        for department_id, group
        in doctors.groupby(
            "department_id"
        )
    }

    # Make sure all required departments
    # actually have doctors.

    missing_departments = (
        set(
            DIAGNOSIS_MAP.keys()
        )
        -
        set(
            doctor_groups.keys()
        )
    )

    if missing_departments:

        raise ValueError(
            "No doctors available for departments: "
            f"{sorted(missing_departments)}"
        )

    # Convert once instead of repeatedly
    # converting inside the generation loop.

    patient_records = patients.to_dict(
        "records"
    )

    department_ids = list(
        DIAGNOSIS_MAP.keys()
    )

    records = []

    # --------------------------------------------------------
    # GENERATE ADMISSIONS
    # --------------------------------------------------------

    for number in range(
        start_number,
        start_number + count,
    ):

        # ----------------------------------------------------
        # PATIENT
        # ----------------------------------------------------

        patient = random.choice(
            patient_records
        )

        # ----------------------------------------------------
        # DEPARTMENT
        # ----------------------------------------------------

        department_id = random.choice(
            department_ids
        )

        # ----------------------------------------------------
        # DOCTOR
        # ----------------------------------------------------

        doctor = random.choice(
            doctor_groups[
                department_id
            ]
        )

        # ----------------------------------------------------
        # ADMISSION TIMESTAMP
        # ----------------------------------------------------

        admission_timestamp = random_date(
            start,
            end,
        )

        # ----------------------------------------------------
        # EMERGENCY LOGIC
        # ----------------------------------------------------

        emergency_flag = (
            random.random()
            <
            CONFIG.emergency_probability
        )

        if emergency_flag:

            admission_type = "Emergency"

        else:

            admission_type = random.choices(
                [
                    "Elective",
                    "Referral",
                ],
                weights=[
                    70,
                    30,
                ],
                k=1,
            )[0]

        # ----------------------------------------------------
        # ICU LOGIC
        # ----------------------------------------------------

        if emergency_flag:

            icu_probability = 0.25

        else:

            icu_probability = (
                CONFIG.icu_probability
            )

        icu_flag = (
            random.random()
            <
            icu_probability
        )

        # ----------------------------------------------------
        # LENGTH OF STAY
        # ----------------------------------------------------

        length_of_stay = random.randint(
            1,
            7,
        )

        # ICU admissions generally remain
        # in hospital longer.

        if icu_flag:

            length_of_stay += random.randint(
                2,
                8,
            )

        discharge_timestamp = (
            admission_timestamp
            + timedelta(
                days=length_of_stay
            )
        )

        # ----------------------------------------------------
        # HISTORICAL DATASET HORIZON
        # ----------------------------------------------------

        # During Phase 2 initial generation we do not
        # want discharge dates extending beyond the
        # historical dataset horizon.
        #
        # During Phase 3 incremental generation this
        # flag is False because a patient admitted today
        # may legitimately discharge several days later.

        if (
            clip_discharge_to_end
            and discharge_timestamp > end
        ):

            discharge_timestamp = end

            length_of_stay = max(
                0,
                (
                    discharge_timestamp.date()
                    -
                    admission_timestamp.date()
                ).days,
            )

        # ----------------------------------------------------
        # READMISSION RISK
        # ----------------------------------------------------

        readmission_probability = (
            CONFIG.readmission_probability
        )

        # Chronic patients have higher synthetic
        # readmission probability.

        chronic_condition = patient.get(
            "chronic_condition"
        )

        if (
            pd.notna(
                chronic_condition
            )
            and chronic_condition
        ):

            readmission_probability += 0.08

        # ICU patients also receive additional
        # readmission probability.

        if icu_flag:

            readmission_probability += 0.05

        # Safety ceiling.

        readmission_probability = min(
            readmission_probability,
            0.60,
        )

        readmission_flag = (
            random.random()
            <
            readmission_probability
        )

        # ----------------------------------------------------
        # OUTCOME
        # ----------------------------------------------------

        if icu_flag:

            outcome = random.choices(
                [
                    "Recovered",
                    "Improved",
                    "Transferred",
                    "Deceased",
                ],
                weights=[
                    40,
                    35,
                    12,
                    13,
                ],
                k=1,
            )[0]

        else:

            outcome = random.choices(
                [
                    "Recovered",
                    "Improved",
                    "Transferred",
                    "Deceased",
                ],
                weights=[
                    58,
                    32,
                    7,
                    3,
                ],
                k=1,
            )[0]

        # ----------------------------------------------------
        # ROOM
        # ----------------------------------------------------

        if icu_flag:

            room_type = "ICU"

        else:

            room_type = random.choice(
                [
                    "General",
                    "Semi Private",
                    "Private",
                ]
            )

        # ----------------------------------------------------
        # DIAGNOSIS
        # ----------------------------------------------------

        diagnosis_code = random.choice(
            DIAGNOSIS_MAP[
                department_id
            ]
        )

        # ----------------------------------------------------
        # CREATE RECORD
        # ----------------------------------------------------

        records.append(
            {
                "admission_id":
                    f"ADM-{number:08d}",

                "patient_id":
                    patient[
                        "patient_id"
                    ],

                "doctor_id":
                    doctor[
                        "doctor_id"
                    ],

                "department_id":
                    department_id,

                "diagnosis_code":
                    diagnosis_code,

                "admission_timestamp":
                    admission_timestamp,

                "discharge_timestamp":
                    discharge_timestamp,

                "admission_type":
                    admission_type,

                "room_type":
                    room_type,

                "bed_number":
                    (
                        f"BED-"
                        f"{random.randint(1, 500):03d}"
                    ),

                "length_of_stay":
                    length_of_stay,

                "icu_flag":
                    icu_flag,

                "readmission_flag":
                    readmission_flag,

                "emergency_flag":
                    emergency_flag,

                "outcome":
                    outcome,
            }
        )

    # --------------------------------------------------------
    # DATAFRAME
    # --------------------------------------------------------

    return pd.DataFrame(
        records
    )