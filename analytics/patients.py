from __future__ import annotations

import numpy as np
import pandas as pd

from analytics.data_loader import (
    load_admission_analysis_dataset,
    load_table,
)
from analytics.statistics import (
    distribution_summary,
    percentile_segment,
)


PATIENT_UTILIZATION_REQUIRED_COLUMNS = {
    "patient_key",
    "patient_id",
    "current_age",
    "insurance_status",
    "chronic_condition",
    "lifetime_admissions",
    "total_length_of_stay_days",
    "average_length_of_stay",
    "emergency_admissions",
    "icu_admissions",
    "readmissions",
    "lifetime_gross_revenue",
    "lifetime_net_revenue",
    "lifetime_paid_amount",
    "lifetime_outstanding_amount",
}


def load_patient_level_dataset() -> pd.DataFrame:
    """
    Load the patient-grain analytical view.

    Grain:
        One row per patient.

    Source:
        analytics.vw_patient_utilization
    """

    patients = load_table(
        "analytics",
        "vw_patient_utilization",
    )

    missing_columns = (
        PATIENT_UTILIZATION_REQUIRED_COLUMNS
        - set(patients.columns)
    )

    if missing_columns:
        raise RuntimeError(
            "analytics.vw_patient_utilization is missing "
            "required columns: "
            + ", ".join(
                sorted(missing_columns)
            )
        )

    date_columns = [
        "date_of_birth",
        "registration_date",
        "first_admission_timestamp",
        "latest_admission_timestamp",
    ]

    for column in date_columns:
        if column in patients.columns:
            patients[column] = pd.to_datetime(
                patients[column],
                errors="coerce",
            )

    return patients


def patient_age_statistics(
    admissions: pd.DataFrame,
) -> pd.DataFrame:
    """
    Admission-weighted patient age distribution.

    Age is calculated at the time of each admission,
    rather than using current_age.
    """

    working = admissions.copy()

    working[
        "date_of_birth"
    ] = pd.to_datetime(
        working["date_of_birth"],
        errors="coerce",
    )

    working[
        "admission_date"
    ] = pd.to_datetime(
        working["admission_date"],
        errors="coerce",
    )

    age_days = (
        working["admission_date"]
        - working["date_of_birth"]
    ).dt.days

    working[
        "patient_age_at_admission"
    ] = np.floor(
        age_days / 365.2425
    )

    working.loc[
        working[
            "patient_age_at_admission"
        ] < 0,
        "patient_age_at_admission",
    ] = np.nan

    return distribution_summary(
        working,
        [
            "patient_age_at_admission",
        ],
    )


def patient_utilization_statistics(
    patients: pd.DataFrame,
) -> pd.DataFrame:
    """
    Statistical distribution of lifetime patient
    utilization and financial measures.
    """

    columns = [
        "current_age",
        "lifetime_admissions",
        "total_length_of_stay_days",
        "average_length_of_stay",
        "emergency_admissions",
        "icu_admissions",
        "readmissions",
        "lifetime_gross_revenue",
        "lifetime_net_revenue",
        "lifetime_paid_amount",
        "lifetime_outstanding_amount",
    ]

    return distribution_summary(
        patients,
        columns,
    )


def patient_utilization_segmentation(
    patients: pd.DataFrame,
) -> pd.DataFrame:
    """
    Create a Python percentile-based utilization
    segmentation using lifetime admission count.

    This is descriptive segmentation only.
    It is not a clinical risk classification.
    """

    working = patients.copy()

    working[
        "python_utilization_segment"
    ] = percentile_segment(
        working[
            "lifetime_admissions"
        ],
        labels=(
            "Lower Utilization",
            "Moderate Utilization",
            "High Utilization",
            "Very High Utilization",
        ),
    )

    result = (
        working
        .groupby(
            "python_utilization_segment",
            dropna=False,
        )
        .agg(
            patients=(
                "patient_id",
                "count",
            ),
            admitted_patients=(
                "lifetime_admissions",
                lambda series: int(
                    (
                        series > 0
                    ).sum()
                ),
            ),
            total_admissions=(
                "lifetime_admissions",
                "sum",
            ),
            average_admissions=(
                "lifetime_admissions",
                "mean",
            ),
            median_admissions=(
                "lifetime_admissions",
                "median",
            ),
            maximum_admissions=(
                "lifetime_admissions",
                "max",
            ),
            total_inpatient_days=(
                "total_length_of_stay_days",
                "sum",
            ),
            average_inpatient_days=(
                "total_length_of_stay_days",
                "mean",
            ),
            emergency_admissions=(
                "emergency_admissions",
                "sum",
            ),
            icu_admissions=(
                "icu_admissions",
                "sum",
            ),
            readmissions=(
                "readmissions",
                "sum",
            ),
            lifetime_net_revenue=(
                "lifetime_net_revenue",
                "sum",
            ),
            lifetime_paid_amount=(
                "lifetime_paid_amount",
                "sum",
            ),
            lifetime_outstanding_amount=(
                "lifetime_outstanding_amount",
                "sum",
            ),
        )
        .reset_index()
    )

    result[
        "patient_share_pct"
    ] = (
        100.0
        * result["patients"]
        / result["patients"].sum()
    ).round(2)

    result[
        "admission_share_pct"
    ] = (
        100.0
        * result["total_admissions"]
        / result[
            "total_admissions"
        ].sum()
    ).round(2)

    result[
        "readmission_rate_pct"
    ] = (
        100.0
        * result["readmissions"]
        / result[
            "total_admissions"
        ].replace(
            0,
            np.nan,
        )
    ).round(2)

    result[
        "emergency_rate_pct"
    ] = (
        100.0
        * result[
            "emergency_admissions"
        ]
        / result[
            "total_admissions"
        ].replace(
            0,
            np.nan,
        )
    ).round(2)

    result[
        "icu_rate_pct"
    ] = (
        100.0
        * result[
            "icu_admissions"
        ]
        / result[
            "total_admissions"
        ].replace(
            0,
            np.nan,
        )
    ).round(2)

    result[
        "collection_efficiency_pct"
    ] = (
        100.0
        * result[
            "lifetime_paid_amount"
        ]
        / result[
            "lifetime_net_revenue"
        ].replace(
            0,
            np.nan,
        )
    ).round(2)

    round_columns = [
        "average_admissions",
        "median_admissions",
        "average_inpatient_days",
        "lifetime_net_revenue",
        "lifetime_paid_amount",
        "lifetime_outstanding_amount",
    ]

    result[
        round_columns
    ] = result[
        round_columns
    ].round(2)

    segment_order = {
        "Lower Utilization": 1,
        "Moderate Utilization": 2,
        "High Utilization": 3,
        "Very High Utilization": 4,
    }

    result[
        "_segment_order"
    ] = result[
        "python_utilization_segment"
    ].map(
        segment_order
    )

    result = (
        result
        .sort_values(
            "_segment_order"
        )
        .drop(
            columns=[
                "_segment_order",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    return result


def chronic_condition_statistics(
    admissions: pd.DataFrame,
) -> pd.DataFrame:
    """
    Admission-level operational and financial
    statistics by patient chronic condition.
    """

    result = (
        admissions
        .groupby(
            "chronic_condition",
            dropna=False,
        )
        .agg(
            admissions=(
                "admission_id",
                "count",
            ),
            unique_patients=(
                "patient_id",
                "nunique",
            ),
            average_length_of_stay=(
                "length_of_stay",
                "mean",
            ),
            emergency_admissions=(
                "emergency_flag",
                "sum",
            ),
            icu_admissions=(
                "icu_flag",
                "sum",
            ),
            readmissions=(
                "readmission_flag",
                "sum",
            ),
            net_revenue=(
                "net_amount",
                "sum",
            ),
        )
        .reset_index()
    )

    result[
        "readmission_rate_pct"
    ] = (
        100.0
        * result["readmissions"]
        / result["admissions"].replace(
            0,
            np.nan,
        )
    ).round(2)

    result[
        "emergency_rate_pct"
    ] = (
        100.0
        * result[
            "emergency_admissions"
        ]
        / result["admissions"].replace(
            0,
            np.nan,
        )
    ).round(2)

    result[
        "icu_rate_pct"
    ] = (
        100.0
        * result["icu_admissions"]
        / result["admissions"].replace(
            0,
            np.nan,
        )
    ).round(2)

    result[
        "average_length_of_stay"
    ] = result[
        "average_length_of_stay"
    ].round(2)

    result[
        "net_revenue"
    ] = result[
        "net_revenue"
    ].round(2)

    return result.sort_values(
        "admissions",
        ascending=False,
    ).reset_index(
        drop=True
    )


def insurance_statistics(
    admissions: pd.DataFrame,
) -> pd.DataFrame:
    """
    Compare admission and financial behaviour
    across patient insurance status.
    """

    result = (
        admissions
        .groupby(
            "insurance_status",
            dropna=False,
        )
        .agg(
            admissions=(
                "admission_id",
                "count",
            ),
            unique_patients=(
                "patient_id",
                "nunique",
            ),
            average_length_of_stay=(
                "length_of_stay",
                "mean",
            ),
            readmissions=(
                "readmission_flag",
                "sum",
            ),
            net_revenue=(
                "net_amount",
                "sum",
            ),
            insurance_amount=(
                "insurance_amount",
                "sum",
            ),
            patient_amount=(
                "patient_amount",
                "sum",
            ),
            collected_amount=(
                "paid_amount",
                "sum",
            ),
            outstanding_amount=(
                "outstanding_amount",
                "sum",
            ),
        )
        .reset_index()
    )

    result[
        "readmission_rate_pct"
    ] = (
        100.0
        * result["readmissions"]
        / result["admissions"].replace(
            0,
            np.nan,
        )
    ).round(2)

    result[
        "collection_efficiency_pct"
    ] = (
        100.0
        * result[
            "collected_amount"
        ]
        / result["net_revenue"].replace(
            0,
            np.nan,
        )
    ).round(2)

    result[
        "outstanding_rate_pct"
    ] = (
        100.0
        * result[
            "outstanding_amount"
        ]
        / result["net_revenue"].replace(
            0,
            np.nan,
        )
    ).round(2)

    result[
        "average_length_of_stay"
    ] = result[
        "average_length_of_stay"
    ].round(2)

    money_columns = [
        "net_revenue",
        "insurance_amount",
        "patient_amount",
        "collected_amount",
        "outstanding_amount",
    ]

    result[
        money_columns
    ] = result[
        money_columns
    ].round(2)

    return result.sort_values(
        "admissions",
        ascending=False,
    ).reset_index(
        drop=True
    )


def patient_population_reconciliation(
    patients: pd.DataFrame,
) -> pd.DataFrame:
    """
    Produce patient-grain totals that can be
    reconciled against warehouse facts.
    """

    return pd.DataFrame(
        [
            {
                "patients": int(
                    len(patients)
                ),
                "patients_with_admissions": int(
                    (
                        patients[
                            "lifetime_admissions"
                        ] > 0
                    ).sum()
                ),
                "lifetime_admissions": int(
                    patients[
                        "lifetime_admissions"
                    ].sum()
                ),
                "total_length_of_stay_days": int(
                    patients[
                        "total_length_of_stay_days"
                    ].sum()
                ),
                "emergency_admissions": int(
                    patients[
                        "emergency_admissions"
                    ].sum()
                ),
                "icu_admissions": int(
                    patients[
                        "icu_admissions"
                    ].sum()
                ),
                "readmissions": int(
                    patients[
                        "readmissions"
                    ].sum()
                ),
                "lifetime_net_revenue": round(
                    float(
                        patients[
                            "lifetime_net_revenue"
                        ].sum()
                    ),
                    2,
                ),
                "lifetime_paid_amount": round(
                    float(
                        patients[
                            "lifetime_paid_amount"
                        ].sum()
                    ),
                    2,
                ),
                "lifetime_outstanding_amount": round(
                    float(
                        patients[
                            "lifetime_outstanding_amount"
                        ].sum()
                    ),
                    2,
                ),
            }
        ]
    )


def run_patient_analysis(
    admissions: pd.DataFrame | None = None,
) -> dict[str, pd.DataFrame]:

    if admissions is None:
        admissions = (
            load_admission_analysis_dataset()
        )

    patient_level = (
        load_patient_level_dataset()
    )

    return {
        "patient_age_statistics":
            patient_age_statistics(
                admissions
            ),

        "patient_utilization_statistics":
            patient_utilization_statistics(
                patient_level
            ),

        "patient_utilization_segmentation":
            patient_utilization_segmentation(
                patient_level
            ),

        "chronic_condition_statistics":
            chronic_condition_statistics(
                admissions
            ),

        "insurance_statistics":
            insurance_statistics(
                admissions
            ),

        "patient_population_reconciliation":
            patient_population_reconciliation(
                patient_level
            ),
    }