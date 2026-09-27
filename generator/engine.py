import time

from generator.admissions import generate_admissions
from generator.billing import generate_billing
from generator.claims import generate_claims
from generator.config import CONFIG
from generator.doctors import generate_doctors
from generator.exporter import export_dataframe
from generator.helpers import set_random_seed
from generator.labs import generate_labs
from generator.medications import (
    generate_medications,
    medication_master,
)
from generator.patients import generate_patients

from utils.logger import get_logger


logger = get_logger(__name__)


def generate_initial_dataset():

    start_time = time.perf_counter()

    logger.info(
        "Hospital 360 initial dataset generation started."
    )

    set_random_seed()

    print("Generating doctors...")
    doctors = generate_doctors()

    print("Generating patients...")
    patients = generate_patients()

    print("Generating admissions...")
    admissions = generate_admissions(
        patients=patients,
        doctors=doctors,
    )

    print("Generating billing...")
    billing = generate_billing(
        admissions=admissions,
        doctors=doctors,
        patients=patients,
    )

    print("Generating insurance claims...")
    claims = generate_claims(
        billing=billing,
    )

    print("Generating laboratory events...")
    labs = generate_labs(
        admissions=admissions,
    )

    print("Generating medication master...")
    medications_master = medication_master()

    print("Generating medication events...")
    medication_events = generate_medications(
        admissions=admissions,
    )

    datasets = {
        "doctors.csv":
            doctors,

        "patients.csv":
            patients,

        "admissions.csv":
            admissions,

        "billing.csv":
            billing,

        "claims.csv":
            claims,

        "labs.csv":
            labs,

        "medication_master.csv":
            medications_master,

        "medication_events.csv":
            medication_events,
    }

    print()
    print("Exporting raw datasets...")

    for filename, dataframe in datasets.items():

        export_dataframe(
            dataframe,
            filename,
        )

    duration = (
        time.perf_counter()
        - start_time
    )

    logger.info(
        "Dataset generation completed in %.2f seconds.",
        duration,
    )

    return datasets