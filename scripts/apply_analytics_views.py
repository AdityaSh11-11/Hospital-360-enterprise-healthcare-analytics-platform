from __future__ import annotations

from pathlib import Path

from sqlalchemy import text

from database.connection import engine


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(
    __file__
).resolve().parents[1]


SQL_FILE = (
    PROJECT_ROOT
    / "database"
    / "sql"
    / "11_analytics_views.sql"
)


# ============================================================
# PRINT HELPERS
# ============================================================

def separator() -> None:

    print(
        "=" * 78
    )


# ============================================================
# LOAD SQL
# ============================================================

def load_sql() -> str:

    if not SQL_FILE.exists():

        raise FileNotFoundError(
            f"SQL file not found: {SQL_FILE}"
        )

    return SQL_FILE.read_text(
        encoding="utf-8"
    )


# ============================================================
# APPLY
# ============================================================

def apply_analytics_views() -> None:

    sql = load_sql()

    separator()

    print(
        "HOSPITAL 360 — "
        "PHASE 5.1 ANALYTICS VIEWS"
    )

    separator()

    print(
        f"SQL file : {SQL_FILE}"
    )

    print()

    print(
        "Applying analytics schema "
        "and semantic views..."
    )

    with engine.begin() as connection:

        connection.execute(
            text(sql)
        )

    print()

    print(
        "[PASS] Analytics views "
        "applied successfully."
    )

    separator()


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    apply_analytics_views()


if __name__ == "__main__":

    main()