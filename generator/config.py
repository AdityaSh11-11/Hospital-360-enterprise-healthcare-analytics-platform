from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GeneratorConfig:

    # ========================================================
    # RANDOMNESS
    # ========================================================

    random_seed: int = 42

    # ========================================================
    # INITIAL DATASET
    # ========================================================

    patient_count: int = 25_000

    doctor_count: int = 150

    admission_count: int = 50_000

    # ========================================================
    # PROBABILITIES
    # ========================================================

    insurance_probability: float = 0.72

    icu_probability: float = 0.12

    readmission_probability: float = 0.11

    emergency_probability: float = 0.28

    # ========================================================
    # LABS
    # ========================================================

    min_labs_per_admission: int = 1

    max_labs_per_admission: int = 5

    # ========================================================
    # MEDICATIONS
    # ========================================================

    min_medications_per_admission: int = 1

    max_medications_per_admission: int = 6

    # ========================================================
    # INITIAL HISTORICAL RANGE
    # ========================================================

    start_date: str = "2023-01-01"

    end_date: str = "2026-09-23"

    # ========================================================
    # INCREMENTAL GENERATION
    # ========================================================

    incremental_patient_min: int = 40

    incremental_patient_max: int = 100

    incremental_admission_min: int = 120

    incremental_admission_max: int = 300

    # ========================================================
    # STORAGE
    # ========================================================

    raw_directory: Path = Path(
        "data/raw"
    )

    incremental_directory: Path = Path(
        "data/incremental"
    )


CONFIG = GeneratorConfig()