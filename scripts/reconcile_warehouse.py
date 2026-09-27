from sqlalchemy import text

from database.connection import engine

from etl.reconciliation import (
    snapshot_warehouse,
)


# ============================================================
# PRINT HELPERS
# ============================================================

def separator():

    print(
        "=" * 78
    )


def small_separator():

    print(
        "-" * 78
    )


# ============================================================
# MAIN
# ============================================================

def main():

    separator()

    print(
        "HOSPITAL 360 — "
        "WAREHOUSE RECONCILIATION"
    )

    separator()

    with engine.connect() as connection:

        snapshot = snapshot_warehouse(
            connection
        )

        successful_batches = (
            connection.execute(
                text(
                    """
                    SELECT
                        batch_id,
                        source_batch_id,
                        batch_type,
                        business_date,
                        status,
                        records_received,
                        records_inserted,
                        records_rejected,
                        duration_seconds

                    FROM control.etl_batch

                    WHERE status = 'SUCCESS'

                    ORDER BY batch_id
                    """
                )
            )
            .mappings()
            .all()
        )

        rejected_count = (
            connection.execute(
                text(
                    """
                    SELECT COUNT(*)

                    FROM control.rejected_record
                    """
                )
            )
            .scalar_one()
        )

    # ========================================================
    # WAREHOUSE COUNTS
    # ========================================================

    print()
    print(
        "WAREHOUSE COUNTS"
    )

    small_separator()

    labels = {
        "patients":
            "Patients",

        "doctors":
            "Doctors",

        "medications":
            "Medications",

        "admissions":
            "Admissions",

        "billing":
            "Billing",

        "claims":
            "Claims",

        "labs":
            "Lab Tests",

        "medication_events":
            "Medication Events",
    }

    for (
        key,
        value,
    ) in snapshot.as_dict().items():

        print(
            f"{labels[key]:<28}"
            f"{value:>15,}"
        )

    # ========================================================
    # ETL HISTORY
    # ========================================================

    print()
    print(
        "SUCCESSFUL ETL HISTORY"
    )

    small_separator()

    if not successful_batches:

        print(
            "No successful ETL batches."
        )

    else:

        for row in successful_batches:

            print(
                f"{row['batch_id']:>4}"
                f" | "
                f"{str(row['source_batch_id']):<24}"
                f" | "
                f"{str(row['batch_type']):<12}"
                f" | "
                f"{str(row['business_date']):<12}"
                f" | "
                f"{row['status']}"
            )

    # ========================================================
    # QUALITY
    # ========================================================

    print()
    print(
        "DATA QUALITY"
    )

    small_separator()

    print(
        f"Rejected records : "
        f"{rejected_count:,}"
    )

    print()

    separator()


if __name__ == "__main__":

    main()