from __future__ import annotations

from pathlib import Path

from sqlalchemy import text

from database.connection import engine


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

SQL_FILE = (
    PROJECT_ROOT
    / "database"
    / "sql"
    / "19_cfo_finance_views.sql"
)


def main() -> None:
    print("=" * 96)

    print(
        "HOSPITAL 360 — "
        "PHASE 7.1 CFO FINANCE VIEW DEPLOYMENT"
    )

    print("=" * 96)

    if not SQL_FILE.exists():
        raise FileNotFoundError(
            f"SQL file not found: {SQL_FILE}"
        )

    sql = SQL_FILE.read_text(
        encoding="utf-8"
    )

    print()
    print(
        f"Applying: {SQL_FILE.name}"
    )

    with engine.begin() as connection:
        connection.execute(
            text(sql)
        )

    print()
    print(
        "[PASS] CFO finance views applied successfully."
    )

    print("=" * 96)


if __name__ == "__main__":
    main()