from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central application configuration.

    Values are loaded from environment variables
    and the local .env file.
    """

    app_name: str = "Hospital 360"
    app_env: str = "development"
    app_version: str = "0.1.0"

    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "hospital360"
    db_user: str = "postgres"
    db_password: str = "postgres"

    admin_username: str = "admin"
    admin_password: str = "change_this_password"

    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://"
            f"{self.db_user}:"
            f"{self.db_password}@"
            f"{self.db_host}:"
            f"{self.db_port}/"
            f"{self.db_name}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()