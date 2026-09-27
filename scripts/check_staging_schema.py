from sqlalchemy import text

from database.connection import engine


EXPECTED = {

    "stg_doctors": [
        "staging_id",
        "batch_id",
        "doctor_id",
        "doctor_name",
        "gender",
        "specialization",
        "department_id",
        "qualification",
        "experience_years",
        "consultation_fee",
        "joining_date",
        "employment_status",
        "loaded_at",
    ],

    "stg_patients": [
        "staging_id",
        "batch_id",
        "patient_id",
        "first_name",
        "last_name",
        "gender",
        "date_of_birth",
        "blood_group",
        "city",
        "state",
        "insurance_status",
        "chronic_condition",
        "registration_date",
        "loaded_at",
    ],

    "stg_admissions": [
        "staging_id",
        "batch_id",
        "admission_id",
        "patient_id",
        "doctor_id",
        "department_id",
        "diagnosis_code",
        "admission_timestamp",
        "discharge_timestamp",
        "admission_type",
        "room_type",
        "bed_number",
        "length_of_stay",
        "icu_flag",
        "readmission_flag",
        "emergency_flag",
        "outcome",
        "loaded_at",
    ],

    "stg_billing": [
        "staging_id",
        "batch_id",
        "bill_id",
        "admission_id",
        "patient_id",
        "billing_date",
        "room_charge",
        "doctor_charge",
        "procedure_charge",
        "medication_charge",
        "lab_charge",
        "other_charge",
        "gross_amount",
        "discount_amount",
        "insurance_amount",
        "patient_amount",
        "tax_amount",
        "net_amount",
        "paid_amount",
        "outstanding_amount",
        "payment_status",
        "payment_method",
        "loaded_at",
    ],

    "stg_claims": [
        "staging_id",
        "batch_id",
        "claim_id",
        "bill_id",
        "patient_id",
        "insurer_id",
        "submission_date",
        "settlement_date",
        "claim_amount",
        "approved_amount",
        "rejected_amount",
        "claim_status",
        "rejection_reason",
        "processing_days",
        "loaded_at",
    ],

    "stg_labs": [
        "staging_id",
        "batch_id",
        "lab_test_id",
        "patient_id",
        "admission_id",
        "doctor_id",
        "test_date",
        "test_name",
        "test_category",
        "result_value",
        "result_unit",
        "result_status",
        "test_cost",
        "abnormal_flag",
        "loaded_at",
    ],

    "stg_medication_master": [
        "staging_id",
        "batch_id",
        "medication_id",
        "medication_name",
        "medication_category",
        "manufacturer",
        "unit_cost",
        "loaded_at",
    ],

    "stg_medication_events": [
        "staging_id",
        "batch_id",
        "medication_event_id",
        "patient_id",
        "admission_id",
        "medication_id",
        "prescribed_date",
        "quantity",
        "unit_price",
        "total_amount",
        "loaded_at",
    ],
}


def get_columns(
    connection,
    table_name,
):

    result = connection.execute(
        text(
            """
            SELECT column_name

            FROM information_schema.columns

            WHERE table_schema = 'staging'
              AND table_name = :table_name

            ORDER BY ordinal_position
            """
        ),
        {
            "table_name":
                table_name
        },
    )

    return [
        row[0]
        for row in result
    ]


def main():

    print()
    print("=" * 70)
    print(
        "HOSPITAL 360 — "
        "STAGING SCHEMA CHECK"
    )
    print("=" * 70)

    failures = []

    with engine.connect() as connection:

        for (
            table_name,
            expected_columns,
        ) in EXPECTED.items():

            actual_columns = get_columns(
                connection,
                table_name,
            )

            missing = [
                column
                for column
                in expected_columns
                if column
                not in actual_columns
            ]

            unexpected = [
                column
                for column
                in actual_columns
                if column
                not in expected_columns
            ]

            print()
            print(
                f"{table_name}"
            )

            print(
                f"  Columns : "
                f"{len(actual_columns)}"
            )

            if not actual_columns:

                print(
                    "  [FAIL] Table does not exist."
                )

                failures.append(
                    table_name
                )

                continue

            if missing:

                print(
                    "  [FAIL] Missing:"
                )

                for column in missing:

                    print(
                        f"         - {column}"
                    )

                failures.append(
                    table_name
                )

            if unexpected:

                print(
                    "  [WARN] Unexpected:"
                )

                for column in unexpected:

                    print(
                        f"         - {column}"
                    )

            if (
                not missing
                and actual_columns
            ):

                print(
                    "  [PASS] Schema aligned."
                )

    print()
    print("-" * 70)

    if failures:

        print(
            "STAGING SCHEMA CHECK FAILED"
        )

        print(
            "Tables requiring attention:"
        )

        for table_name in failures:

            print(
                f"  - {table_name}"
            )

        raise SystemExit(1)

    print(
        "STAGING SCHEMA CHECK PASSED"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()