from pathlib import Path

from sqlalchemy import text

from database.connection import engine
from utils.logger import get_logger


logger = get_logger(__name__)


SQL_FILE = Path(
    "database/sql/10_staging_alignment.sql"
)


def main():

    print()
    print("=" * 70)
    print(
        "HOSPITAL 360 — "
        "PHASE 4.1 STAGING ALIGNMENT"
    )
    print("=" * 70)

    if not SQL_FILE.exists():

        raise FileNotFoundError(
            f"SQL migration not found: "
            f"{SQL_FILE}"
        )

    sql = SQL_FILE.read_text(
        encoding="utf-8"
    )

    print()
    print(
        f"Migration file : {SQL_FILE}"
    )

    print(
        "Applying staging schema alignment..."
    )

    try:

        with engine.begin() as connection:

            connection.execute(
                text(sql)
            )

        print()
        print(
            "[PASS] Staging schema alignment applied."
        )

    except Exception as exc:

        logger.exception(
            "Staging alignment failed."
        )

        print()
        print(
            "[FAIL] Migration failed."
        )

        print(
            f"Reason: {exc}"
        )

        raise

    print()
    print("=" * 70)
    print(
        "PHASE 4.1 STAGING ALIGNMENT COMPLETE"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()