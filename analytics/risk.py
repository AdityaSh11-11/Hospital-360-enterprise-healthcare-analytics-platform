from __future__ import annotations

import pandas as pd

from analytics.data_loader import load_table


RISK_BAND_ORDER = {
    "Low": 1,
    "Medium": 2,
    "High": 3,
}


def load_admission_risk() -> pd.DataFrame:
    dataframe = load_table(
        "analytics",
        "vw_admission_risk",
    ).copy()

    required = {
        "admission_id",
        "patient_id",
        "department_name",
        "doctor_name",
        "risk_score",
        "risk_band",
        "risk_reasons",
    }

    missing = (
        required
        - set(dataframe.columns)
    )

    if missing:
        raise RuntimeError(
            "Admission risk view missing columns: "
            + ", ".join(
                sorted(missing)
            )
        )

    return dataframe


def load_patient_risk() -> pd.DataFrame:
    return load_table(
        "analytics",
        "vw_patient_risk",
    ).copy()


def load_risk_band_summary() -> pd.DataFrame:
    dataframe = load_table(
        "analytics",
        "vw_risk_band_summary",
    ).copy()

    dataframe["risk_band_order"] = (
        dataframe["risk_band"]
        .map(RISK_BAND_ORDER)
    )

    return (
        dataframe
        .sort_values("risk_band_order")
        .drop(
            columns=["risk_band_order"]
        )
        .reset_index(drop=True)
    )


def load_department_risk() -> pd.DataFrame:
    return (
        load_table(
            "analytics",
            "vw_department_risk",
        )
        .sort_values(
            [
                "high_risk_rate_rank",
                "department_name",
            ]
        )
        .reset_index(drop=True)
    )


def load_doctor_risk() -> pd.DataFrame:
    return (
        load_table(
            "analytics",
            "vw_doctor_risk",
        )
        .sort_values(
            [
                "hospital_risk_rank",
                "doctor_name",
            ]
        )
        .reset_index(drop=True)
    )


def load_monthly_risk_trend() -> pd.DataFrame:
    dataframe = load_table(
        "analytics",
        "vw_monthly_risk_trend",
    ).copy()

    dataframe["month_start"] = (
        pd.to_datetime(
            dataframe["month_start"],
            errors="coerce",
        )
    )

    return (
        dataframe
        .sort_values("month_start")
        .reset_index(drop=True)
    )


def load_risk_factor_prevalence() -> pd.DataFrame:
    return (
        load_table(
            "analytics",
            "vw_risk_factor_prevalence",
        )
        .sort_values(
            [
                "prevalence_pct",
                "risk_factor",
            ],
            ascending=[
                False,
                True,
            ],
        )
        .reset_index(drop=True)
    )


def build_risk_kpi_table(
    admission_risk: pd.DataFrame,
) -> pd.DataFrame:
    total_admissions = len(
        admission_risk
    )

    total_patients = (
        admission_risk[
            "patient_id"
        ].nunique()
    )

    high_risk_admissions = int(
        (
            admission_risk[
                "risk_band"
            ]
            == "High"
        ).sum()
    )

    medium_risk_admissions = int(
        (
            admission_risk[
                "risk_band"
            ]
            == "Medium"
        ).sum()
    )

    low_risk_admissions = int(
        (
            admission_risk[
                "risk_band"
            ]
            == "Low"
        ).sum()
    )

    high_risk_rate = (
        high_risk_admissions
        / total_admissions
        * 100.0
        if total_admissions
        else 0.0
    )

    return pd.DataFrame(
        [
            {
                "kpi":
                    "Admissions Scored",
                "value":
                    total_admissions,
                "unit":
                    "count",
            },
            {
                "kpi":
                    "Patients Represented",
                "value":
                    total_patients,
                "unit":
                    "count",
            },
            {
                "kpi":
                    "Average Risk Score",
                "value":
                    round(
                        float(
                            admission_risk[
                                "risk_score"
                            ].mean()
                        ),
                        2,
                    ),
                "unit":
                    "score",
            },
            {
                "kpi":
                    "High Risk Admissions",
                "value":
                    high_risk_admissions,
                "unit":
                    "count",
            },
            {
                "kpi":
                    "Medium Risk Admissions",
                "value":
                    medium_risk_admissions,
                "unit":
                    "count",
            },
            {
                "kpi":
                    "Low Risk Admissions",
                "value":
                    low_risk_admissions,
                "unit":
                    "count",
            },
            {
                "kpi":
                    "High Risk Admission Rate",
                "value":
                    round(
                        high_risk_rate,
                        2,
                    ),
                "unit":
                    "percent",
            },
            {
                "kpi":
                    "Maximum Risk Score",
                "value":
                    int(
                        admission_risk[
                            "risk_score"
                        ].max()
                    ),
                "unit":
                    "score",
            },
        ]
    )


def build_high_risk_patient_register(
    patient_risk: pd.DataFrame,
) -> pd.DataFrame:
    required = {
        "patient_id",
        "first_name",
        "last_name",
        "lifetime_admissions",
        "maximum_risk_score",
        "maximum_risk_band",
        "latest_risk_score",
        "latest_risk_band",
        "latest_risk_reasons",
        "latest_department_name",
        "latest_doctor_name",
        "lifetime_recorded_outstanding",
    }

    missing = (
        required
        - set(patient_risk.columns)
    )

    if missing:
        raise RuntimeError(
            "Patient risk view missing columns: "
            + ", ".join(
                sorted(missing)
            )
        )

    result = patient_risk[
        patient_risk[
            "maximum_risk_band"
        ] == "High"
    ].copy()

    return (
        result
        .sort_values(
            [
                "maximum_risk_score",
                "latest_risk_score",
                "lifetime_admissions",
            ],
            ascending=[
                False,
                False,
                False,
            ],
        )
        .reset_index(drop=True)
    )


def build_risk_management_insights(
    risk_band_summary: pd.DataFrame,
    department_risk: pd.DataFrame,
    doctor_risk: pd.DataFrame,
    monthly_risk: pd.DataFrame,
    factor_prevalence: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict] = []

    high_band = risk_band_summary[
        risk_band_summary[
            "risk_band"
        ] == "High"
    ]

    if not high_band.empty:
        row = high_band.iloc[0]

        rows.append(
            {
                "sequence": 1,
                "domain":
                    "Risk Population",
                "insight":
                    (
                        f"{int(row['admissions']):,} "
                        "admissions fall in the High "
                        "analytical risk band, representing "
                        f"{float(row['admission_share_pct']):.2f}% "
                        "of scored admissions."
                    ),
            }
        )

    if not department_risk.empty:
        row = (
            department_risk
            .sort_values(
                [
                    "high_risk_admission_rate_pct",
                    "average_risk_score",
                ],
                ascending=[
                    False,
                    False,
                ],
            )
            .iloc[0]
        )

        rows.append(
            {
                "sequence": 2,
                "domain":
                    "Department",
                "insight":
                    (
                        f"{row['department_name']} has the "
                        "highest observed High-risk admission "
                        "rate at "
                        f"{float(row['high_risk_admission_rate_pct']):.2f}%."
                    ),
            }
        )

    if not doctor_risk.empty:
        eligible = doctor_risk[
            doctor_risk[
                "admissions"
            ] >= 25
        ].copy()

        if not eligible.empty:
            row = (
                eligible
                .sort_values(
                    [
                        "high_risk_admission_rate_pct",
                        "average_risk_score",
                    ],
                    ascending=[
                        False,
                        False,
                    ],
                )
                .iloc[0]
            )

            rows.append(
                {
                    "sequence": 3,
                    "domain":
                        "Doctor Workload",
                    "insight":
                        (
                            f"{row['doctor_name']} has the "
                            "highest observed High-risk admission "
                            "rate among doctors with at least "
                            "25 admissions, at "
                            f"{float(row['high_risk_admission_rate_pct']):.2f}%."
                        ),
                }
            )

    if not factor_prevalence.empty:
        row = (
            factor_prevalence
            .sort_values(
                "prevalence_pct",
                ascending=False,
            )
            .iloc[0]
        )

        rows.append(
            {
                "sequence": 4,
                "domain":
                    "Risk Factors",
                "insight":
                    (
                        f"{row['risk_factor']} is the most "
                        "frequently triggered modeled factor, "
                        "appearing in "
                        f"{float(row['prevalence_pct']):.2f}% "
                        "of admissions."
                    ),
            }
        )

    if not monthly_risk.empty:
        latest = (
            monthly_risk
            .sort_values("month_start")
            .iloc[-1]
        )

        rows.append(
            {
                "sequence": 5,
                "domain":
                    "Monthly Trend",
                "insight":
                    (
                        "The latest admission month has an "
                        "average analytical risk score of "
                        f"{float(latest['average_risk_score']):.2f} "
                        "and a High-risk admission rate of "
                        f"{float(latest['high_risk_admission_rate_pct']):.2f}%."
                    ),
            }
        )

        if pd.notna(
            latest[
                "high_risk_rate_mom_change_pp"
            ]
        ):
            rows.append(
                {
                    "sequence": 6,
                    "domain":
                        "Monthly Trend",
                    "insight":
                        (
                            "The latest High-risk admission rate "
                            "changed by "
                            f"{float(latest['high_risk_rate_mom_change_pp']):+.2f} "
                            "percentage points versus the prior "
                            "admission month."
                        ),
                }
            )

    return (
        pd.DataFrame(rows)
        .sort_values("sequence")
        .reset_index(drop=True)
    )


def run_risk_analysis() -> dict[str, pd.DataFrame]:
    admission_risk = (
        load_admission_risk()
    )

    patient_risk = (
        load_patient_risk()
    )

    risk_band_summary = (
        load_risk_band_summary()
    )

    department_risk = (
        load_department_risk()
    )

    doctor_risk = (
        load_doctor_risk()
    )

    monthly_risk = (
        load_monthly_risk_trend()
    )

    factor_prevalence = (
        load_risk_factor_prevalence()
    )

    return {
        "risk_kpis":
            build_risk_kpi_table(
                admission_risk
            ),

        "risk_band_summary":
            risk_band_summary,

        "department_risk":
            department_risk,

        "doctor_risk":
            doctor_risk,

        "monthly_risk_trend":
            monthly_risk,

        "risk_factor_prevalence":
            factor_prevalence,

        "high_risk_patient_register":
            build_high_risk_patient_register(
                patient_risk
            ),

        "risk_management_insights":
            build_risk_management_insights(
                risk_band_summary=
                    risk_band_summary,

                department_risk=
                    department_risk,

                doctor_risk=
                    doctor_risk,

                monthly_risk=
                    monthly_risk,

                factor_prevalence=
                    factor_prevalence,
            ),
    }