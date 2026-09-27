from sqlalchemy import text

from database.connection import engine


def print_section(title):

    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def main():

    with engine.connect() as connection:

        print_section(
            "HOSPITAL 360 — WAREHOUSE INSPECTION"
        )

        tables = connection.execute(
            text(
                """
                SELECT
                    table_schema,
                    table_name

                FROM information_schema.tables

                WHERE table_schema IN (
                    'staging',
                    'warehouse',
                    'control'
                )

                ORDER BY
                    table_schema,
                    table_name;
                """
            )
        ).fetchall()

        for schema, table in tables:

            print(
                f"{schema:<12} | {table}"
            )

        print_section(
            "MASTER DATA COUNTS"
        )

        queries = {
            "Dates":
                "SELECT COUNT(*) FROM warehouse.dim_date",

            "Departments":
                "SELECT COUNT(*) FROM warehouse.dim_department",

            "Insurers":
                "SELECT COUNT(*) FROM warehouse.dim_insurer",

            "Diagnoses":
                "SELECT COUNT(*) FROM warehouse.dim_diagnosis",
        }

        for label, query in queries.items():

            count = connection.execute(
                text(query)
            ).scalar()

            print(
                f"{label:<20}: {count:,}"
            )

        print_section(
            "FACT TABLE COUNTS"
        )

        fact_tables = [
            "fact_admission",
            "fact_billing",
            "fact_claim",
            "fact_lab_test",
            "fact_medication",
        ]

        for table in fact_tables:

            count = connection.execute(
                text(
                    f"""
                    SELECT COUNT(*)
                    FROM warehouse.{table}
                    """
                )
            ).scalar()

            print(
                f"{table:<25}: {count:,}"
            )


if __name__ == "__main__":
    main()