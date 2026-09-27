import argparse

from generator.incremental import (
    generate_incremental_batch,
)


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Generate an incremental "
            "Hospital 360 data batch."
        )
    )

    parser.add_argument(
        "--date",
        required=True,
        help="Business date YYYY-MM-DD",
    )

    parser.add_argument(
        "--patients",
        type=int,
        default=None,
        help="Optional patient count",
    )

    parser.add_argument(
        "--admissions",
        type=int,
        default=None,
        help="Optional admission count",
    )

    args = parser.parse_args()

    print()
    print("=" * 70)
    print(
        "HOSPITAL 360 — INCREMENTAL GENERATOR"
    )
    print("=" * 70)

    (
        batch_id,
        batch_directory,
        datasets,
        manifest,
    ) = generate_incremental_batch(
        business_date=args.date,
        patient_count=args.patients,
        admission_count=args.admissions,
    )

    print()
    print(
        f"Batch: {batch_id}"
    )

    print(
        f"Location: {batch_directory}"
    )

    print()
    print("-" * 70)

    total = 0

    for filename, dataframe in datasets.items():

        count = len(dataframe)

        total += count

        print(
            f"{filename:<30}"
            f"{count:>12,}"
        )

    print("-" * 70)

    print(
        f"{'TOTAL':<30}"
        f"{total:>12,}"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()