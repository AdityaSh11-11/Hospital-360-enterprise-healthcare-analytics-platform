from generator.engine import generate_initial_dataset


def main():

    print()
    print("=" * 70)
    print(
        "HOSPITAL 360 — INITIAL DATA GENERATOR"
    )
    print("=" * 70)
    print()

    datasets = generate_initial_dataset()

    print()
    print("=" * 70)
    print("GENERATION SUMMARY")
    print("=" * 70)

    total = 0

    for filename, dataframe in datasets.items():

        rows = len(dataframe)

        total += rows

        print(
            f"{filename:<30}"
            f"{rows:>12,} rows"
        )

    print("-" * 70)

    print(
        f"{'TOTAL':<30}"
        f"{total:>12,} rows"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()