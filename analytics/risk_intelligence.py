from __future__ import annotations

import pandas as pd

from analytics.data_loader import load_table
from analytics.anomalies import run_anomaly_analysis


RISK_BAND_ORDER = {
    "Low": 1,
    "Medium": 2,
    "High": 3,
}


def load_patient_risk() -> pd.DataFrame:
    return load_table(
        "analytics",
        "vw_patient_risk",
    ).copy()


def load_admission_risk() -> pd.DataFrame:
    return load_table(
        "analytics",
        "vw_admission_risk",
    ).copy()


def load_bill_risk() -> pd.DataFrame:
    return load_table(
        "analytics",
        "vw_bill_financial_risk",
    ).copy()


def load_claim_risk() -> pd.DataFrame:
    return load_table(
        "analytics",
        "vw_claim_risk",
    ).copy()


def load_department_patient_risk() -> pd.DataFrame:
    return load_table(
        "analytics",
        "vw_department_risk",
    ).copy()


def load_department_financial_risk() -> pd.DataFrame:
    return load_table(
        "analytics",
        "vw_department_financial_risk",
    ).copy()


def load_insurer_claim_risk() -> pd.DataFrame:
    return load_table(
        "analytics",
        "vw_insurer_claim_risk",
    ).copy()


def build_enterprise_risk_kpis(
    patient_risk: pd.DataFrame,
    admission_risk: pd.DataFrame,
    bill_risk: pd.DataFrame,
    claim_risk: pd.DataFrame,
    aggregate_anomalies: pd.DataFrame,
) -> pd.DataFrame:
    high_risk_patients = int(
        (
            patient_risk[
                "maximum_risk_band"
            ]
            == "High"
        ).sum()
    )

    high_risk_admissions = int(
        (
            admission_risk[
                "risk_band"
            ]
            == "High"
        ).sum()
    )

    high_financial_bills = int(
        (
            bill_risk[
                "financial_risk_band"
            ]
            == "High"
        ).sum()
    )

    high_claims = int(
        (
            claim_risk[
                "claim_risk_band"
            ]
            == "High"
        ).sum()
    )

    high_bill_outstanding = float(
        bill_risk.loc[
            bill_risk[
                "financial_risk_band"
            ]
            == "High",
            "outstanding_amount",
        ].sum()
    )

    total_outstanding = float(
        bill_risk[
            "outstanding_amount"
        ].sum()
    )

    rejected_claim_value = float(
        claim_risk[
            "rejected_amount"
        ].sum()
    )

    high_anomalies = int(
        (
            aggregate_anomalies[
                "direction"
            ]
            == "High"
        ).sum()
    ) if not aggregate_anomalies.empty else 0

    low_anomalies = int(
        (
            aggregate_anomalies[
                "direction"
            ]
            == "Low"
        ).sum()
    ) if not aggregate_anomalies.empty else 0

    return pd.DataFrame(
        [
            {
                "kpi":
                    "Admitted Patients Assessed",
                "value":
                    len(patient_risk),
                "unit":
                    "count",
                "domain":
                    "Patient Risk",
            },
            {
                "kpi":
                    "High Risk Patients",
                "value":
                    high_risk_patients,
                "unit":
                    "count",
                "domain":
                    "Patient Risk",
            },
            {
                "kpi":
                    "High Risk Admissions",
                "value":
                    high_risk_admissions,
                "unit":
                    "count",
                "domain":
                    "Patient Risk",
            },
            {
                "kpi":
                    "High Financial Risk Bills",
                "value":
                    high_financial_bills,
                "unit":
                    "count",
                "domain":
                    "Financial Risk",
            },
            {
                "kpi":
                    "High Risk Bill Outstanding",
                "value":
                    round(
                        high_bill_outstanding,
                        2,
                    ),
                "unit":
                    "currency",
                "domain":
                    "Financial Risk",
            },
            {
                "kpi":
                    "Total Recorded Outstanding",
                "value":
                    round(
                        total_outstanding,
                        2,
                    ),
                "unit":
                    "currency",
                "domain":
                    "Financial Risk",
            },
            {
                "kpi":
                    "High Risk Claims",
                "value":
                    high_claims,
                "unit":
                    "count",
                "domain":
                    "Claims Risk",
            },
            {
                "kpi":
                    "Rejected Claim Value",
                "value":
                    round(
                        rejected_claim_value,
                        2,
                    ),
                "unit":
                    "currency",
                "domain":
                    "Claims Risk",
            },
            {
                "kpi":
                    "High Aggregate Anomalies",
                "value":
                    high_anomalies,
                "unit":
                    "count",
                "domain":
                    "Anomaly Detection",
            },
            {
                "kpi":
                    "Low Aggregate Anomalies",
                "value":
                    low_anomalies,
                "unit":
                    "count",
                "domain":
                    "Anomaly Detection",
            },
        ]
    )


def build_patient_priority_register(
    patient_risk: pd.DataFrame,
) -> pd.DataFrame:
    result = patient_risk[
        patient_risk[
            "maximum_risk_band"
        ]
        == "High"
    ].copy()

    sort_columns = []

    for candidate in [
        "maximum_risk_score",
        "latest_risk_score",
        "total_outstanding_amount",
        "lifetime_admissions",
    ]:
        if candidate in result.columns:
            sort_columns.append(
                candidate
            )

    if sort_columns:
        result = result.sort_values(
            sort_columns,
            ascending=[
                False
            ] * len(sort_columns),
        )

    return result.reset_index(
        drop=True
    )


def build_financial_priority_register(
    bill_risk: pd.DataFrame,
) -> pd.DataFrame:
    result = bill_risk[
        bill_risk[
            "financial_risk_band"
        ]
        == "High"
    ].copy()

    return (
        result
        .sort_values(
            [
                "financial_risk_score",
                "outstanding_amount",
                "net_amount",
            ],
            ascending=[
                False,
                False,
                False,
            ],
        )
        .reset_index(drop=True)
    )


def build_claim_priority_register(
    claim_risk: pd.DataFrame,
) -> pd.DataFrame:
    result = claim_risk[
        claim_risk[
            "claim_risk_band"
        ]
        == "High"
    ].copy()

    return (
        result
        .sort_values(
            [
                "claim_risk_score",
                "rejected_amount",
                "claim_amount",
            ],
            ascending=[
                False,
                False,
                False,
            ],
        )
        .reset_index(drop=True)
    )


def build_department_risk_matrix(
    patient_department: pd.DataFrame,
    financial_department: pd.DataFrame,
) -> pd.DataFrame:
    patient_columns = [
        "department_key",
        "department_id",
        "department_name",
        "admissions",
        "patients",
        "average_risk_score",
        "high_risk_admissions",
        "high_risk_admission_rate_pct",
        "readmission_rate_pct",
        "emergency_rate_pct",
        "icu_rate_pct",
        "average_length_of_stay",
    ]

    patient_columns = [
        column
        for column in patient_columns
        if column
        in patient_department.columns
    ]

    financial_columns = [
        "department_key",
        "bills",
        "net_revenue",
        "collected_amount",
        "outstanding_amount",
        "average_financial_risk_score",
        "high_risk_bills",
        "high_risk_bill_rate_pct",
        "outstanding_rate_pct",
        "outstanding_share_pct",
    ]

    financial_columns = [
        column
        for column in financial_columns
        if column
        in financial_department.columns
    ]

    patient = patient_department[
        patient_columns
    ].copy()

    financial = financial_department[
        financial_columns
    ].copy()

    result = patient.merge(
        financial,
        on="department_key",
        how="outer",
        validate="one_to_one",
    )

    if (
        "high_risk_admission_rate_pct"
        in result.columns
    ):
        result[
            "patient_risk_rank"
        ] = (
            result[
                "high_risk_admission_rate_pct"
            ]
            .rank(
                method="dense",
                ascending=False,
            )
            .astype("Int64")
        )

    if (
        "outstanding_amount"
        in result.columns
    ):
        result[
            "financial_exposure_rank"
        ] = (
            result[
                "outstanding_amount"
            ]
            .rank(
                method="dense",
                ascending=False,
            )
            .astype("Int64")
        )

    if (
        "high_risk_bill_rate_pct"
        in result.columns
    ):
        result[
            "financial_risk_rank"
        ] = (
            result[
                "high_risk_bill_rate_pct"
            ]
            .rank(
                method="dense",
                ascending=False,
            )
            .astype("Int64")
        )

    return (
        result
        .sort_values(
            "department_name"
        )
        .reset_index(drop=True)
    )


def build_risk_domain_summary(
    patient_risk: pd.DataFrame,
    admission_risk: pd.DataFrame,
    bill_risk: pd.DataFrame,
    claim_risk: pd.DataFrame,
    aggregate_anomalies: pd.DataFrame,
) -> pd.DataFrame:
    patient_high = int(
        (
            patient_risk[
                "maximum_risk_band"
            ]
            == "High"
        ).sum()
    )

    admission_high = int(
        (
            admission_risk[
                "risk_band"
            ]
            == "High"
        ).sum()
    )

    bill_high = int(
        (
            bill_risk[
                "financial_risk_band"
            ]
            == "High"
        ).sum()
    )

    claim_high = int(
        (
            claim_risk[
                "claim_risk_band"
            ]
            == "High"
        ).sum()
    )

    anomaly_count = len(
        aggregate_anomalies
    )

    rows = [
        {
            "risk_domain":
                "Patient",
            "population":
                len(patient_risk),
            "priority_signals":
                patient_high,
            "priority_rate_pct":
                round(
                    100.0
                    * patient_high
                    / len(patient_risk),
                    2,
                )
                if len(patient_risk)
                else 0.0,
            "interpretation":
                (
                    "Patients whose maximum observed "
                    "admission-level analytical risk "
                    "band is High."
                ),
        },
        {
            "risk_domain":
                "Admission",
            "population":
                len(admission_risk),
            "priority_signals":
                admission_high,
            "priority_rate_pct":
                round(
                    100.0
                    * admission_high
                    / len(admission_risk),
                    2,
                )
                if len(admission_risk)
                else 0.0,
            "interpretation":
                (
                    "Admissions in the High analytical "
                    "patient-risk band."
                ),
        },
        {
            "risk_domain":
                "Financial",
            "population":
                len(bill_risk),
            "priority_signals":
                bill_high,
            "priority_rate_pct":
                round(
                    100.0
                    * bill_high
                    / len(bill_risk),
                    2,
                )
                if len(bill_risk)
                else 0.0,
            "interpretation":
                (
                    "Bills in the High analytical "
                    "financial-risk band."
                ),
        },
        {
            "risk_domain":
                "Claims",
            "population":
                len(claim_risk),
            "priority_signals":
                claim_high,
            "priority_rate_pct":
                round(
                    100.0
                    * claim_high
                    / len(claim_risk),
                    2,
                )
                if len(claim_risk)
                else 0.0,
            "interpretation":
                (
                    "Claims in the High analytical "
                    "claim-risk band."
                ),
        },
        {
            "risk_domain":
                "Aggregate Anomalies",
            "population":
                anomaly_count,
            "priority_signals":
                anomaly_count,
            "priority_rate_pct":
                100.0
                if anomaly_count
                else 0.0,
            "interpretation":
                (
                    "Statistically unusual aggregate "
                    "observations crossing the configured "
                    "robust-z threshold."
                ),
        },
    ]

    return pd.DataFrame(
        rows
    )


def build_enterprise_risk_insights(
    patient_risk: pd.DataFrame,
    admission_risk: pd.DataFrame,
    bill_risk: pd.DataFrame,
    claim_risk: pd.DataFrame,
    department_matrix: pd.DataFrame,
    insurer_risk: pd.DataFrame,
    aggregate_anomalies: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict] = []

    high_patients = int(
        (
            patient_risk[
                "maximum_risk_band"
            ]
            == "High"
        ).sum()
    )

    rows.append(
        {
            "sequence": 1,
            "domain":
                "Patient Risk",
            "insight":
                (
                    f"{high_patients:,} admitted patients "
                    "have reached the High analytical "
                    "patient-risk band on at least one "
                    "observed admission."
                ),
        }
    )

    high_admissions = int(
        (
            admission_risk[
                "risk_band"
            ]
            == "High"
        ).sum()
    )

    rows.append(
        {
            "sequence": 2,
            "domain":
                "Admission Risk",
            "insight":
                (
                    f"{high_admissions:,} admissions are "
                    "classified in the High analytical "
                    "admission-risk band."
                ),
        }
    )

    high_bills = bill_risk[
        bill_risk[
            "financial_risk_band"
        ]
        == "High"
    ]

    high_outstanding = float(
        high_bills[
            "outstanding_amount"
        ].sum()
    )

    total_outstanding = float(
        bill_risk[
            "outstanding_amount"
        ].sum()
    )

    share = (
        high_outstanding
        / total_outstanding
        * 100.0
        if total_outstanding
        else 0.0
    )

    rows.append(
        {
            "sequence": 3,
            "domain":
                "Financial Risk",
            "insight":
                (
                    f"{len(high_bills):,} High financial-risk "
                    "bills contain "
                    f"{high_outstanding:,.2f} of recorded "
                    "outstanding value, representing "
                    f"{share:.2f}% of total recorded "
                    "outstanding exposure."
                ),
        }
    )

    high_claims = claim_risk[
        claim_risk[
            "claim_risk_band"
        ]
        == "High"
    ]

    rows.append(
        {
            "sequence": 4,
            "domain":
                "Claims Risk",
            "insight":
                (
                    f"{len(high_claims):,} claims are in the "
                    "High analytical claim-risk band. "
                    "This is an exposure-prioritization "
                    "signal, not a rejection prediction."
                ),
        }
    )

    if (
        not department_matrix.empty
        and "outstanding_amount"
        in department_matrix.columns
    ):
        department = (
            department_matrix
            .sort_values(
                "outstanding_amount",
                ascending=False,
            )
            .iloc[0]
        )

        rows.append(
            {
                "sequence": 5,
                "domain":
                    "Department Exposure",
                "insight":
                    (
                        f"{department['department_name']} "
                        "has the largest recorded department "
                        "outstanding exposure at "
                        f"{float(department['outstanding_amount']):,.2f}."
                    ),
            }
        )

    if not insurer_risk.empty:
        insurer = (
            insurer_risk
            .sort_values(
                "rejected_amount",
                ascending=False,
            )
            .iloc[0]
        )

        rows.append(
            {
                "sequence": 6,
                "domain":
                    "Insurer Exposure",
                "insight":
                    (
                        f"{insurer['insurer_name']} has the "
                        "largest observed rejected claim "
                        "value at "
                        f"{float(insurer['rejected_amount']):,.2f}."
                    ),
            }
        )

    if not aggregate_anomalies.empty:
        strongest = (
            aggregate_anomalies
            .sort_values(
                "absolute_robust_z_score",
                ascending=False,
            )
            .iloc[0]
        )

        rows.append(
            {
                "sequence": 7,
                "domain":
                    "Statistical Anomaly",
                "insight":
                    (
                        "The strongest aggregate review "
                        f"signal is {strongest['metric']} "
                        f"for {strongest['entity_id']} "
                        "with a robust z-score of "
                        f"{float(strongest['robust_z_score']):+.2f}. "
                        "Anomaly status indicates unusual "
                        "behavior, not error or misconduct."
                    ),
            }
        )

    return (
        pd.DataFrame(
            rows
        )
        .sort_values("sequence")
        .reset_index(drop=True)
    )


def build_risk_dashboard_feed(
    patient_risk: pd.DataFrame,
    admission_risk: pd.DataFrame,
    bill_risk: pd.DataFrame,
    claim_risk: pd.DataFrame,
    aggregate_anomalies: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict] = []

    patient_high = int(
        (
            patient_risk[
                "maximum_risk_band"
            ]
            == "High"
        ).sum()
    )

    admission_high = int(
        (
            admission_risk[
                "risk_band"
            ]
            == "High"
        ).sum()
    )

    bill_high = int(
        (
            bill_risk[
                "financial_risk_band"
            ]
            == "High"
        ).sum()
    )

    claim_high = int(
        (
            claim_risk[
                "claim_risk_band"
            ]
            == "High"
        ).sum()
    )

    outstanding_high = float(
        bill_risk.loc[
            bill_risk[
                "financial_risk_band"
            ]
            == "High",
            "outstanding_amount",
        ].sum()
    )

    rejected_value = float(
        claim_risk[
            "rejected_amount"
        ].sum()
    )

    rows.extend(
        [
            {
                "display_order": 1,
                "section":
                    "Patient Risk",
                "metric":
                    "High Risk Patients",
                "value":
                    patient_high,
                "unit":
                    "count",
            },
            {
                "display_order": 2,
                "section":
                    "Patient Risk",
                "metric":
                    "High Risk Admissions",
                "value":
                    admission_high,
                "unit":
                    "count",
            },
            {
                "display_order": 3,
                "section":
                    "Financial Risk",
                "metric":
                    "High Risk Bills",
                "value":
                    bill_high,
                "unit":
                    "count",
            },
            {
                "display_order": 4,
                "section":
                    "Financial Risk",
                "metric":
                    "High Risk Outstanding",
                "value":
                    round(
                        outstanding_high,
                        2,
                    ),
                "unit":
                    "currency",
            },
            {
                "display_order": 5,
                "section":
                    "Claims Risk",
                "metric":
                    "High Risk Claims",
                "value":
                    claim_high,
                "unit":
                    "count",
            },
            {
                "display_order": 6,
                "section":
                    "Claims Risk",
                "metric":
                    "Rejected Claim Value",
                "value":
                    round(
                        rejected_value,
                        2,
                    ),
                "unit":
                    "currency",
            },
            {
                "display_order": 7,
                "section":
                    "Anomaly Detection",
                "metric":
                    "Aggregate Review Signals",
                "value":
                    len(
                        aggregate_anomalies
                    ),
                "unit":
                    "count",
            },
        ]
    )

    return pd.DataFrame(
        rows
    )


def run_unified_risk_intelligence(
) -> dict[str, pd.DataFrame]:
    patient_risk = (
        load_patient_risk()
    )

    admission_risk = (
        load_admission_risk()
    )

    bill_risk = (
        load_bill_risk()
    )

    claim_risk = (
        load_claim_risk()
    )

    department_patient = (
        load_department_patient_risk()
    )

    department_financial = (
        load_department_financial_risk()
    )

    insurer_risk = (
        load_insurer_claim_risk()
    )

    anomaly_outputs = (
        run_anomaly_analysis()
    )

    aggregate_anomalies = (
        anomaly_outputs[
            "aggregate_anomalies"
        ]
    )

    department_matrix = (
        build_department_risk_matrix(
            patient_department=
                department_patient,
            financial_department=
                department_financial,
        )
    )

    return {
        "enterprise_risk_kpis":
            build_enterprise_risk_kpis(
                patient_risk=
                    patient_risk,
                admission_risk=
                    admission_risk,
                bill_risk=
                    bill_risk,
                claim_risk=
                    claim_risk,
                aggregate_anomalies=
                    aggregate_anomalies,
            ),

        "risk_domain_summary":
            build_risk_domain_summary(
                patient_risk=
                    patient_risk,
                admission_risk=
                    admission_risk,
                bill_risk=
                    bill_risk,
                claim_risk=
                    claim_risk,
                aggregate_anomalies=
                    aggregate_anomalies,
            ),

        "patient_priority_register":
            build_patient_priority_register(
                patient_risk
            ),

        "financial_priority_register":
            build_financial_priority_register(
                bill_risk
            ),

        "claim_priority_register":
            build_claim_priority_register(
                claim_risk
            ),

        "department_risk_matrix":
            department_matrix,

        "insurer_risk_summary":
            insurer_risk,

        "aggregate_review_signals":
            aggregate_anomalies,

        "risk_dashboard_feed":
            build_risk_dashboard_feed(
                patient_risk=
                    patient_risk,
                admission_risk=
                    admission_risk,
                bill_risk=
                    bill_risk,
                claim_risk=
                    claim_risk,
                aggregate_anomalies=
                    aggregate_anomalies,
            ),

        "enterprise_risk_insights":
            build_enterprise_risk_insights(
                patient_risk=
                    patient_risk,
                admission_risk=
                    admission_risk,
                bill_risk=
                    bill_risk,
                claim_risk=
                    claim_risk,
                department_matrix=
                    department_matrix,
                insurer_risk=
                    insurer_risk,
                aggregate_anomalies=
                    aggregate_anomalies,
            ),
    }