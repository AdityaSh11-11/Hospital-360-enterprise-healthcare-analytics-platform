from __future__ import annotations

from pathlib import Path

from sqlalchemy import text

from database.connection import engine


PROJECT_ROOT = Path(__file__).resolve().parents[1]

SQL_FILE = (
    PROJECT_ROOT
    / "database"
    / "sql"
    / "18_doctor_views.sql"
)


def separator() -> None:
    print("=" * 92)


def main() -> None:

    separator()

    print(
        "HOSPITAL 360 — "
        "PHASE 5.5 DOCTOR ANALYTICS"
    )

    separator()

    if not SQL_FILE.exists():
        raise FileNotFoundError(
            f"SQL file not found: {SQL_FILE}"
        )

    sql = SQL_FILE.read_text(
        encoding="utf-8"
    )

    print()
    print(
        f"Applying : {SQL_FILE.name}"
    )

    with engine.begin() as connection:
        connection.execute(
            text(sql)
        )

    print(
        f"[PASS] {SQL_FILE.name}"
    )

    print()
    separator()

    print(
        "[PASS] Phase 5.5 doctor analytics "
        "applied successfully."
    )

    separator()


if __name__ == "__main__":
    main()