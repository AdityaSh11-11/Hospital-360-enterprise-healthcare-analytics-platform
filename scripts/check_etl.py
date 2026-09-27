from sqlalchemy import text

from database.connection import engine


QUERIES = {
    "Patients":
        """
        SELECT COUNT(*)
        FROM warehouse.dim_patient
        """,

    "Doctors":
        """
        SELECT COUNT(*)
        FROM warehouse.dim_doctor
        """,

    "Medications":
        """
        SELECT COUNT(*)
        FROM warehouse.dim_medication
        """,

    "Admissions":
        """
        SELECT COUNT(*)
        FROM warehouse.fact_admission
        """,

    "Billing":
        """
        SELECT COUNT(*)
        FROM warehouse.fact_billing
        """,

    "Claims":
        """
        SELECT COUNT(*)
        FROM warehouse.fact_claim
        """,

    "Lab Tests":
        """
        SELECT COUNT(*)
        FROM warehouse.fact_lab_test
        """,

    "Medication Events":
        """
        SELECT COUNT(*)
        FROM warehouse.fact_medication
        """,

    "ETL Batches":
        """
        SELECT COUNT(*)
        FROM control.etl_batch
        """,

    "Rejected Records":
        """
        SELECT COUNT(*)
        FROM control.rejected_record
        """,
}


def main():

    print()
    print("=" * 70)
    print(
        "HOSPITAL 360 — ETL VALIDATION"
    )
    print("=" * 70)

    with engine.connect() as connection:

        for label, query in QUERIES.items():

            count = connection.execute(
                text(query)
            ).scalar()

            print(
                f"{label:<25}: "
                f"{count:,}"
            )

        print()
        print("-" * 70)
        print("RECENT ETL BATCHES")
        print("-" * 70)

        batches = connection.execute(
            text(
                """
                SELECT
                    batch_id,
                    source_batch_id,
                    batch_type,
                    status,
                    records_received,
                    records_inserted,
                    records_rejected

                FROM control.etl_batch

                ORDER BY batch_id DESC

                LIMIT 10
                """
            )
        ).fetchall()

        for row in batches:

            print(
                " | ".join(
                    str(value)
                    for value in row
                )
            )

    print()
    print("=" * 70)


if __name__ == "__main__":
    main()