from pathlib import Path

from sqlalchemy import text

from database.connection import engine
from utils.logger import get_logger


logger = get_logger(__name__)


SQL_DIRECTORY = Path("database/sql")


SQL_FILES = [
    "01_schemas.sql",
    "02_dimensions.sql",
    "03_facts.sql",
    "04_control.sql",
    "05_staging.sql",
    "06_indexes.sql",
    "07_views.sql",
    "08_seed.sql",
    "09_etl_upgrade.sql",
]


def read_sql_file(filename: str) -> str:

    path = SQL_DIRECTORY / filename

    return path.read_text(
        encoding="utf-8"
    )


def initialize_database():

    logger.info(
        "Starting Hospital 360 database initialization."
    )

    with engine.begin() as connection:

        for filename in SQL_FILES:

            logger.info(
                "Executing SQL file: %s",
                filename,
            )

            sql = read_sql_file(filename)

            connection.execute(
                text(sql)
            )

    logger.info(
        "Hospital 360 database initialization completed."
    )