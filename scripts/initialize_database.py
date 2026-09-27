from database.initializer import initialize_database


def main():

    print()
    print("=" * 60)
    print("HOSPITAL 360 — DATABASE INITIALIZATION")
    print("=" * 60)

    initialize_database()

    print()
    print("Database initialized successfully.")
    print("=" * 60)


if __name__ == "__main__":
    main()