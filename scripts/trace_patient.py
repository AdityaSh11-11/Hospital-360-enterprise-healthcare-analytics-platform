from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from database.connection import engine


RAW_PATIENTS = Path("data/raw/patients.csv")
INCREMENTAL_ROOT = Path("data/incremental")

WIDTH = 90


def separator(char: str = "="):
    print(char * WIDTH)


def heading(title: str):
    print()
    separator()
    print(title)
    separator()


def load_patient_matches(
    path: Path,
    patient_id: str,
) -> pd.DataFrame:

    if not path.exists():
        return pd.DataFrame()

    dataframe = pd.read_csv(
        path,
        dtype=str,
        keep_default_na=False,
    )

    if "patient_id" not in dataframe.columns:
        return pd.DataFrame()

    return dataframe[
        dataframe["patient_id"]
        .astype(str)
        .str.strip()
        == patient_id
    ].copy()


def find_patient_sources(
    patient_id: str,
) -> list[tuple[str, Path, pd.DataFrame]]:

    matches = []

    # --------------------------------------------------------
    # HISTORICAL RAW DATA
    # --------------------------------------------------------

    raw_matches = load_patient_matches(
        RAW_PATIENTS,
        patient_id,
    )

    if not raw_matches.empty:

        matches.append(
            (
                "HISTORICAL RAW",
                RAW_PATIENTS,
                raw_matches,
            )
        )

    # --------------------------------------------------------
    # INCREMENTAL DATA
    # --------------------------------------------------------

    if INCREMENTAL_ROOT.exists():

        batch_directories = sorted(
            path
            for path in INCREMENTAL_ROOT.iterdir()
            if path.is_dir()
            and path.name.startswith("BATCH-")
        )

        for batch_path in batch_directories:

            patient_file = (
                batch_path
                / "patients.csv"
            )

            batch_matches = load_patient_matches(
                patient_file,
                patient_id,
            )

            if not batch_matches.empty:

                matches.append(
                    (
                        batch_path.name,
                        patient_file,
                        batch_matches,
                    )
                )

    return matches


def find_admission_references(
    patient_id: str,
) -> list[tuple[str, Path, pd.DataFrame]]:

    matches = []

    # --------------------------------------------------------
    # HISTORICAL ADMISSIONS
    # --------------------------------------------------------

    raw_admissions = Path(
        "data/raw/admissions.csv"
    )

    if raw_admissions.exists():

        dataframe = pd.read_csv(
            raw_admissions,
            dtype=str,
            keep_default_na=False,
        )

        if "patient_id" in dataframe.columns:

            found = dataframe[
                dataframe["patient_id"]
                .astype(str)
                .str.strip()
                == patient_id
            ].copy()

            if not found.empty:

                matches.append(
                    (
                        "HISTORICAL RAW",
                        raw_admissions,
                        found,
                    )
                )

    # --------------------------------------------------------
    # INCREMENTAL ADMISSIONS
    # --------------------------------------------------------

    if INCREMENTAL_ROOT.exists():

        batch_directories = sorted(
            path
            for path in INCREMENTAL_ROOT.iterdir()
            if path.is_dir()
            and path.name.startswith("BATCH-")
        )

        for batch_path in batch_directories:

            admission_file = (
                batch_path
                / "admissions.csv"
            )

            if not admission_file.exists():
                continue

            dataframe = pd.read_csv(
                admission_file,
                dtype=str,
                keep_default_na=False,
            )

            if "patient_id" not in dataframe.columns:
                continue

            found = dataframe[
                dataframe["patient_id"]
                .astype(str)
                .str.strip()
                == patient_id
            ].copy()

            if not found.empty:

                matches.append(
                    (
                        batch_path.name,
                        admission_file,
                        found,
                    )
                )

    return matches


def check_warehouse(
    patient_id: str,
) -> dict:

    with engine.connect() as connection:

        patient = (
            connection.execute(
                text(
                    """
                    SELECT
                        patient_key,
                        patient_id,
                        first_name,
                        last_name,
                        registration_date,
                        is_active

                    FROM warehouse.dim_patient

                    WHERE patient_id = :patient_id
                    """
                ),
                {
                    "patient_id": patient_id,
                },
            )
            .mappings()
            .first()
        )

        staging_rows = (
            connection.execute(
                text(
                    """
                    SELECT
                        staging_id,
                        batch_id,
                        patient_id,
                        first_name,
                        last_name,
                        registration_date,
                        loaded_at

                    FROM staging.stg_patients

                    WHERE patient_id = :patient_id

                    ORDER BY staging_id
                    """
                ),
                {
                    "patient_id": patient_id,
                },
            )
            .mappings()
            .all()
        )

        return {
            "warehouse": patient,
            "staging": staging_rows,
        }


def print_dataframe(
    dataframe: pd.DataFrame,
):

    if dataframe.empty:
        print("No rows.")
        return

    with pd.option_context(
        "display.max_columns",
        None,
        "display.width",
        200,
        "display.max_colwidth",
        50,
    ):
        print(
            dataframe.to_string(
                index=False
            )
        )


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Trace a patient business key "
            "through Hospital 360 source, "
            "staging and warehouse layers."
        )
    )

    parser.add_argument(
        "--patient",
        required=True,
        type=str,
        help="Patient business ID.",
    )

    args = parser.parse_args()

    patient_id = (
        args.patient
        .strip()
        .upper()
    )

    heading(
        "HOSPITAL 360 — "
        f"PATIENT TRACE — {patient_id}"
    )

    # ========================================================
    # SOURCE PATIENT RECORDS
    # ========================================================

    source_matches = (
        find_patient_sources(
            patient_id
        )
    )

    heading(
        "PATIENT SOURCE RECORDS"
    )

    if not source_matches:

        print(
            "[FAIL] Patient does not exist "
            "in any patients.csv source file."
        )

    else:

        for (
            source_name,
            path,
            dataframe,
        ) in source_matches:

            print()
            print(
                f"Source : {source_name}"
            )

            print(
                f"File   : {path}"
            )

            print_dataframe(
                dataframe
            )

    # ========================================================
    # ADMISSION REFERENCES
    # ========================================================

    admission_matches = (
        find_admission_references(
            patient_id
        )
    )

    heading(
        "ADMISSION REFERENCES"
    )

    if not admission_matches:

        print(
            "No admissions reference "
            "this patient."
        )

    else:

        total_references = 0

        for (
            source_name,
            path,
            dataframe,
        ) in admission_matches:

            total_references += len(
                dataframe
            )

            print()
            print(
                f"Source : {source_name}"
            )

            print(
                f"File   : {path}"
            )

            columns = [
                column
                for column in (
                    "admission_id",
                    "patient_id",
                    "doctor_id",
                    "department_id",
                    "diagnosis_code",
                    "admission_timestamp",
                    "discharge_timestamp",
                )
                if column
                in dataframe.columns
            ]

            print_dataframe(
                dataframe[
                    columns
                ]
            )

        print()
        print(
            f"Total admission references: "
            f"{total_references:,}"
        )

    # ========================================================
    # DATABASE TRACE
    # ========================================================

    database = check_warehouse(
        patient_id
    )

    heading(
        "WAREHOUSE RECORD"
    )

    if database["warehouse"]:

        print(
            "[PASS] Patient exists "
            "in warehouse.dim_patient"
        )

        for key, value in (
            database["warehouse"]
            .items()
        ):

            print(
                f"{key:<20}: {value}"
            )

    else:

        print(
            "[FAIL] Patient does NOT exist "
            "in warehouse.dim_patient"
        )

    heading(
        "STAGING HISTORY"
    )

    staging_rows = (
        database["staging"]
    )

    if not staging_rows:

        print(
            "[FAIL] Patient does not exist "
            "in staging.stg_patients."
        )

    else:

        for row in staging_rows:

            print()

            for key, value in row.items():

                print(
                    f"{key:<20}: {value}"
                )

    # ========================================================
    # CONCLUSION
    # ========================================================

    heading(
        "TRACE SUMMARY"
    )

    print(
        f"Patient ID              : "
        f"{patient_id}"
    )

    print(
        f"Patient source records  : "
        f"{sum(len(x[2]) for x in source_matches):,}"
    )

    print(
        f"Admission references    : "
        f"{sum(len(x[2]) for x in admission_matches):,}"
    )

    print(
        f"Staging records         : "
        f"{len(staging_rows):,}"
    )

    print(
        "Warehouse record        : "
        + (
            "YES"
            if database["warehouse"]
            else "NO"
        )
    )

    print()
    print(
        "Read-only trace complete. "
        "No database changes were made."
    )


if __name__ == "__main__":
    main()