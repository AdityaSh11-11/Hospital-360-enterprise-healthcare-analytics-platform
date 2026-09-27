import random

import pandas as pd

from generator.helpers import money


ROOM_DAILY_RATE = {
    "General": 2500,
    "Semi Private": 4500,
    "Private": 7000,
    "ICU": 15000,
}


def generate_billing(
    admissions: pd.DataFrame,
    doctors: pd.DataFrame,
    patients: pd.DataFrame,
    start_number: int = 1,
) -> pd.DataFrame:

    if admissions.empty:
        return pd.DataFrame()

    doctor_fee_map = (
        doctors
        .set_index(
            "doctor_id"
        )[
            "consultation_fee"
        ]
        .to_dict()
    )

    insurance_map = (
        patients
        .set_index(
            "patient_id"
        )[
            "insurance_status"
        ]
        .to_dict()
    )

    records = []

    for number, row in enumerate(
        admissions.itertuples(
            index=False
        ),
        start=start_number,
    ):

        los = max(
            int(
                float(
                    str(
                        row.length_of_stay
                    )
                )
            ),
            1,
        )

        room_rate = (
            ROOM_DAILY_RATE[
                str(row.room_type)
            ]
        )

        room_charge = (
            room_rate
            * los
        )

        doctor_fee = float(
            doctor_fee_map[
                row.doctor_id
            ]
        )

        doctor_charge = (
            doctor_fee
            *
            random.randint(
                1,
                los,
            )
        )

        procedure_charge = random.choice(
            [
                0,
                0,
                5000,
                8000,
                12000,
                25000,
                40000,
                75000,
            ]
        )

        if row.icu_flag:

            procedure_charge += (
                random.randint(
                    5000,
                    25000,
                )
            )

        medication_charge = (
            random.randint(
                1000,
                12000,
            )
        )

        if row.icu_flag:

            medication_charge *= 2

        lab_charge = random.randint(
            800,
            9000,
        )

        other_charge = random.randint(
            0,
            5000,
        )

        gross_amount = sum(
            [
                room_charge,
                doctor_charge,
                procedure_charge,
                medication_charge,
                lab_charge,
                other_charge,
            ]
        )

        discount_rate = random.choices(
            [
                0,
                0.02,
                0.05,
                0.10,
            ],
            weights=[
                50,
                20,
                20,
                10,
            ],
            k=1,
        )[0]

        discount_amount = (
            gross_amount
            * discount_rate
        )

        after_discount = (
            gross_amount
            - discount_amount
        )

        tax_amount = (
            after_discount
            * 0.05
        )

        net_amount = (
            after_discount
            + tax_amount
        )

        insured = (
            insurance_map.get(
                row.patient_id,
                "Self Pay",
            )
            == "Insured"
        )

        if insured:

            insurance_ratio = (
                random.uniform(
                    0.55,
                    0.85,
                )
            )

            insurance_amount = (
                net_amount
                * insurance_ratio
            )

        else:

            insurance_amount = 0.0

        patient_amount = (
            net_amount
            - insurance_amount
        )

        collection_ratio = random.choices(
            [
                1.0,
                0.75,
                0.50,
                0.0,
            ],
            weights=[
                72,
                12,
                10,
                6,
            ],
            k=1,
        )[0]

        paid_amount = (
            patient_amount
            * collection_ratio
        )

        outstanding_amount = max(
            patient_amount
            - paid_amount,
            0.0,
        )

        if outstanding_amount < 1:

            payment_status = "Paid"

        elif paid_amount > 0:

            payment_status = (
                "Partially Paid"
            )

        else:

            payment_status = (
                "Outstanding"
            )

        records.append(
            {
                "bill_id":
                    f"BILL-{number:08d}",

                "admission_id":
                    row.admission_id,

                "patient_id":
                    row.patient_id,

                "billing_date":
                    row.discharge_timestamp,

                "room_charge":
                    money(
                        room_charge
                    ),

                "doctor_charge":
                    money(
                        doctor_charge
                    ),

                "procedure_charge":
                    money(
                        procedure_charge
                    ),

                "medication_charge":
                    money(
                        medication_charge
                    ),

                "lab_charge":
                    money(
                        lab_charge
                    ),

                "other_charge":
                    money(
                        other_charge
                    ),

                "gross_amount":
                    money(
                        gross_amount
                    ),

                "discount_amount":
                    money(
                        discount_amount
                    ),

                "insurance_amount":
                    money(
                        insurance_amount
                    ),

                "patient_amount":
                    money(
                        patient_amount
                    ),

                "tax_amount":
                    money(
                        tax_amount
                    ),

                "net_amount":
                    money(
                        net_amount
                    ),

                "paid_amount":
                    money(
                        paid_amount
                    ),

                "outstanding_amount":
                    money(
                        outstanding_amount
                    ),

                "payment_status":
                    payment_status,

                "payment_method":
                    random.choice(
                        [
                            "Cash",
                            "Card",
                            "UPI",
                            "Bank Transfer",
                        ]
                    ),
            }
        )

    return pd.DataFrame(
        records
    )