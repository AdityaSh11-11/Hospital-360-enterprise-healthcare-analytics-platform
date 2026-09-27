from sqlalchemy import text

from config.settings import settings
from database.connection import get_db_connection
from utils.logger import get_logger


logger = get_logger(__name__)


def database_health() -> dict:
    try:
        with get_db_connection() as connection:

            result = connection.execute(
                text(
                    """
                    SELECT
                        current_database() AS database_name,
                        current_user AS database_user,
                        version() AS postgres_version,
                        NOW() AS server_time
                    """
                )
            )

            row = result.mappings().one()

        return {
            "status": "healthy",
            "database": row["database_name"],
            "user": row["database_user"],
            "server_time": str(row["server_time"]),
            "postgres_version": row["postgres_version"],
        }

    except Exception as exc:

        logger.exception(
            "Database health check failed."
        )

        return {
            "status": "unhealthy",
            "database": settings.db_name,
            "error": str(exc),
        }