from pathlib import Path

from etl.pipeline import run_etl


def main():

    print()
    print("=" * 70)
    print(
        "HOSPITAL 360 — INITIAL WAREHOUSE ETL"
    )
    print("=" * 70)

    result = run_etl(
        source_type="INITIAL",
        source_path=Path(
            "data/raw"
        ),
        source_batch_id=
            "INITIAL-HISTORICAL-001",
    )

    print()

    for key, value in result.items():

        print(
            f"{key:<25}: {value}"
        )

    print("=" * 70)


if __name__ == "__main__":
    main()