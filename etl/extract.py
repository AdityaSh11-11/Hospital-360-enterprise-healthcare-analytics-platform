from pathlib import Path

import pandas as pd

from utils.logger import get_logger


logger = get_logger(__name__)


INITIAL_FILES = {
    "doctors": "doctors.csv",
    "patients": "patients.csv",
    "admissions": "admissions.csv",
    "billing": "billing.csv",
    "claims": "claims.csv",
    "labs": "labs.csv",
    "medication_master": "medication_master.csv",
    "medication_events": "medication_events.csv",
}


INCREMENTAL_FILES = {
    "patients": "patients.csv",
    "admissions": "admissions.csv",
    "billing": "billing.csv",
    "claims": "claims.csv",
    "labs": "labs.csv",
    "medication_events": "medication_events.csv",
}


def read_csv_file(
    path: Path,
) -> pd.DataFrame:

    if not path.exists():
        raise FileNotFoundError(
            f"Source file not found: {path}"
        )

    logger.info(
        "Extracting %s",
        path,
    )

    return pd.read_csv(
        path,
        low_memory=False,
    )


def extract_initial(
    directory: Path = Path("data/raw"),
) -> dict[str, pd.DataFrame]:

    datasets = {}

    for dataset, filename in INITIAL_FILES.items():

        datasets[dataset] = read_csv_file(
            directory / filename
        )

    return datasets


def extract_incremental(
    batch_directory: Path,
) -> dict[str, pd.DataFrame]:

    datasets = {}

    for dataset, filename in INCREMENTAL_FILES.items():

        datasets[dataset] = read_csv_file(
            batch_directory / filename
        )

    return datasets