from __future__ import annotations

from pathlib import Path

from sqlalchemy import text

from database.connection import engine


PROJECT_ROOT = Path(
    __file__
).resolve().parents[1]


SQL_FILES = [
    PROJECT_ROOT
    / "database"
    / "sql"
    / "12_finance_views.sql",

    PROJECT_ROOT
    / "database"
    / "sql"
    / "13_claims_views.sql",
]


def separator() -> None:

    print(
        "=" * 78
    )


def apply_sql_file(
    sql_file: Path,
) -> None:

    if not sql_file.exists():

        raise FileNotFoundError(
            f"SQL file not found: {sql_file}"
        )

    sql = sql_file.read_text(
        encoding="utf-8"
    )

    print()
    print(
        f"Applying : {sql_file.name}"
    )

    with engine.begin() as connection:

        connection.execute(
            text(sql)
        )

    print(
        f"[PASS] {sql_file.name}"
    )


def main() -> None:

    separator()

    print(
        "HOSPITAL 360 — "
        "PHASE 5.2 FINANCE + CLAIMS"
    )

    separator()

    for sql_file in SQL_FILES:

        apply_sql_file(
            sql_file
        )

    print()

    separator()

    print(
        "[PASS] Phase 5.2 SQL "
        "applied successfully."
    )

    separator()


if __name__ == "__main__":

    main()