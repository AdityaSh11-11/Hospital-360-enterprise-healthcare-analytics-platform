from __future__ import annotations

from sqlalchemy import text

from database.connection import engine


def main() -> None:
    query = text(
        """
        SELECT
            ordinal_position,
            column_name,
            data_type

        FROM information_schema.columns

        WHERE table_schema = 'analytics'
          AND table_name = 'vw_patient_utilization'

        ORDER BY ordinal_position
        """
    )

    print("=" * 90)
    print("HOSPITAL 360 — vw_patient_utilization SCHEMA")
    print("=" * 90)

    with engine.connect() as connection:
        rows = connection.execute(
            query
        ).mappings().all()

    if not rows:
        raise RuntimeError(
            "analytics.vw_patient_utilization "
            "was not found or has no columns."
        )

    print()
    print(
        f"{'#':<6}"
        f"{'COLUMN NAME':<45}"
        f"{'DATA TYPE'}"
    )

    print("-" * 90)

    for row in rows:
        print(
            f"{row['ordinal_position']:<6}"
            f"{row['column_name']:<45}"
            f"{row['data_type']}"
        )

    print()
    print(f"Total columns: {len(rows)}")
    print("=" * 90)


if __name__ == "__main__":
    main()