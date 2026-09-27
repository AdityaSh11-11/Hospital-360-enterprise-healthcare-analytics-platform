from __future__ import annotations

from pathlib import Path

from database.connection import engine


PROJECT_ROOT = Path(__file__).resolve().parents[1]

SQL_FILE = (
    PROJECT_ROOT
    / "database"
    / "sql"
    / "21_financial_claim_risk_views.sql"
)


def separator() -> None:
    print("=" * 108)


def main() -> None:
    separator()

    print(
        "HOSPITAL 360 — "
        "PHASE 8.2 FINANCIAL & CLAIMS RISK DEPLOYMENT"
    )

    separator()
    print()

    if not SQL_FILE.exists():
        raise FileNotFoundError(
            f"SQL file not found: {SQL_FILE}"
        )

    print(
        f"Applying: {SQL_FILE.name}"
    )

    sql = SQL_FILE.read_text(
        encoding="utf-8"
    )

    raw_connection = (
        engine.raw_connection()
    )

    try:
        cursor = raw_connection.cursor()

        try:
            cursor.execute(sql)

            raw_connection.commit()

        except Exception:
            raw_connection.rollback()
            raise

        finally:
            cursor.close()

    finally:
        raw_connection.close()

    print()
    print(
        "[PASS] Financial & claims risk views "
        "applied successfully."
    )

    separator()


if __name__ == "__main__":
    main()