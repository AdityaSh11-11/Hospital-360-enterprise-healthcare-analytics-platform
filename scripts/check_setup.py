import sys

from config.settings import settings
from database.health import database_health


def main():

    print("=" * 60)
    print("HOSPITAL 360 — PHASE 0 SYSTEM CHECK")
    print("=" * 60)

    print()
    print("Application")
    print("-" * 60)

    print(f"Name        : {settings.app_name}")
    print(f"Environment : {settings.app_env}")
    print(f"Version     : {settings.app_version}")
    print(f"Python      : {sys.version.split()[0]}")

    print()
    print("Database")
    print("-" * 60)

    health = database_health()

    if health["status"] == "healthy":

        print("Status      : CONNECTED")
        print(
            f"Database    : {health['database']}"
        )
        print(
            f"User        : {health['user']}"
        )
        print(
            f"Server Time : {health['server_time']}"
        )

    else:

        print("Status      : FAILED")
        print(
            f"Error       : {health['error']}"
        )

        raise SystemExit(1)

    print()
    print("=" * 60)
    print("PHASE 0 CHECK PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()