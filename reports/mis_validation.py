from __future__ import annotations

import pandas as pd

from analytics.data_loader import read_sql
from reports.mis_report import MISReportPack


EXPECTED_MINIMUM_OUTPUTS = {
    "executive_scorecard",
    "monthly_mis",
    "department_scorecard",
    "claims_mis",
    "receivables_mis",
    "payer_mix",
    "payment_mix",
    "doctor_mis",
    "management_exceptions",
    "executive_commentary",
}


def assert_close(
    label: str,
    actual: float,
    expected: float,
    tolerance: float = 0.05,
) -> None:
    if abs(
        float(actual)
        - float(expected)
    ) > tolerance:
        raise RuntimeError(
            f"{label} failed: "
            f"actual={actual}, "
            f"expected={expected}"
        )


def validate_output_structure(
    report_pack: MISReportPack,
) -> None:
    missing = (
        EXPECTED_MINIMUM_OUTPUTS
        - set(
            report_pack.outputs.keys()
        )
    )

    if missing:
        raise RuntimeError(
            "MIS pack missing outputs: "
            + ", ".join(
                sorted(missing)
            )
        )


def validate_executive_scorecard(
    dataframe: pd.DataFrame,
) -> None:
    required_kpis = {
        "Total Patients",
        "Total Admissions",
        "Average Length of Stay",
        "Readmission Rate",
        "Net Revenue",
        "Collected Amount",
        "Outstanding Amount",
        "Collection Efficiency",
        "Outstanding Rate",
        "Total Claims",
        "Claim Rejection Rate",
        "Rejected Claim Value",
        "Rejected Value Rate",
    }

    actual_kpis = set(
        dataframe["kpi"]
    )

    missing = (
        required_kpis
        - actual_kpis
    )

    if missing:
        raise RuntimeError(
            "Executive scorecard missing KPIs: "
            + ", ".join(
                sorted(missing)
            )
        )


def validate_finance_reconciliation(
    report_pack: MISReportPack,
) -> None:
    department = (
        report_pack.outputs[
            "department_scorecard"
        ]
    )

    source = read_sql(
        """
        SELECT
            COUNT(*) AS bills,

            ROUND(
                SUM(net_amount)::numeric,
                2
            ) AS net_revenue,

            ROUND(
                SUM(paid_amount)::numeric,
                2
            ) AS collected_amount,

            ROUND(
                SUM(outstanding_amount)::numeric,
                2
            ) AS outstanding_amount

        FROM warehouse.fact_billing
        """
    ).iloc[0]

    if int(
        department["bills"].sum()
    ) != int(source["bills"]):
        raise RuntimeError(
            "MIS department bill count "
            "does not reconcile."
        )

    assert_close(
        "MIS department net revenue",
        department[
            "net_revenue"
        ].sum(),
        source[
            "net_revenue"
        ],
    )

    assert_close(
        "MIS department collections",
        department[
            "collected_amount"
        ].sum(),
        source[
            "collected_amount"
        ],
    )

    assert_close(
        "MIS department outstanding",
        department[
            "outstanding_amount"
        ].sum(),
        source[
            "outstanding_amount"
        ],
    )


def validate_operations_reconciliation(
    report_pack: MISReportPack,
) -> None:
    department = (
        report_pack.outputs[
            "department_scorecard"
        ]
    )

    source = read_sql(
        """
        SELECT
            COUNT(*) AS admissions,
            SUM(length_of_stay) AS inpatient_days,
            COUNT(*) FILTER (
                WHERE emergency_flag
            ) AS emergency_admissions,
            COUNT(*) FILTER (
                WHERE icu_flag
            ) AS icu_admissions,
            COUNT(*) FILTER (
                WHERE readmission_flag
            ) AS readmissions

        FROM warehouse.fact_admission
        """
    ).iloc[0]

    comparisons = {
        "admissions":
            int(source["admissions"]),

        "total_inpatient_days":
            int(source["inpatient_days"]),

        "emergency_admissions":
            int(
                source[
                    "emergency_admissions"
                ]
            ),

        "icu_admissions":
            int(
                source[
                    "icu_admissions"
                ]
            ),

        "readmissions":
            int(source["readmissions"]),
    }

    for column, expected in (
        comparisons.items()
    ):
        if column not in department.columns:
            raise RuntimeError(
                f"Department MIS missing {column}."
            )

        actual = int(
            department[column].sum()
        )

        if actual != expected:
            raise RuntimeError(
                f"{column} reconciliation failed: "
                f"{actual:,} != {expected:,}"
            )


def validate_claim_reconciliation(
    report_pack: MISReportPack,
) -> None:
    claims = (
        report_pack.outputs[
            "claims_mis"
        ]
    )

    source = read_sql(
        """
        SELECT
            COUNT(*) AS total_claims,

            ROUND(
                SUM(claim_amount)::numeric,
                2
            ) AS claim_amount,

            ROUND(
                SUM(rejected_amount)::numeric,
                2
            ) AS rejected_amount

        FROM warehouse.fact_claim
        """
    ).iloc[0]

    if int(
        claims["total_claims"].sum()
    ) != int(
        source["total_claims"]
    ):
        raise RuntimeError(
            "MIS claim count does not reconcile."
        )

    assert_close(
        "MIS claim amount",
        claims["claim_amount"].sum(),
        source["claim_amount"],
    )

    assert_close(
        "MIS rejected amount",
        claims[
            "rejected_amount"
        ].sum(),
        source[
            "rejected_amount"
        ],
    )


def validate_population_counts(
    report_pack: MISReportPack,
) -> None:
    department = (
        report_pack.outputs[
            "department_scorecard"
        ]
    )

    claims = (
        report_pack.outputs[
            "claims_mis"
        ]
    )

    doctor = (
        report_pack.outputs[
            "doctor_mis"
        ]
    )

    payer = (
        report_pack.outputs[
            "payer_mix"
        ]
    )

    payment = (
        report_pack.outputs[
            "payment_mix"
        ]
    )

    receivables = (
        report_pack.outputs[
            "receivables_mis"
        ]
    )

    monthly = (
        report_pack.outputs[
            "monthly_mis"
        ]
    )

    expectations = [
        (
            "departments",
            len(department),
            10,
        ),
        (
            "insurers",
            len(claims),
            5,
        ),
        (
            "doctors",
            len(doctor),
            150,
        ),
        (
            "payer groups",
            len(payer),
            2,
        ),
        (
            "payment methods",
            len(payment),
            4,
        ),
        (
            "receivable bands",
            len(receivables),
            5,
        ),
        (
            "billing months",
            len(monthly),
            46,
        ),
    ]

    for (
        label,
        actual,
        expected,
    ) in expectations:
        if actual != expected:
            raise RuntimeError(
                f"Expected {expected} {label}; "
                f"found {actual}."
            )


def validate_mis_report_pack(
    report_pack: MISReportPack,
) -> None:
    validate_output_structure(
        report_pack
    )

    validate_executive_scorecard(
        report_pack.outputs[
            "executive_scorecard"
        ]
    )

    validate_finance_reconciliation(
        report_pack
    )

    validate_operations_reconciliation(
        report_pack
    )

    validate_claim_reconciliation(
        report_pack
    )

    validate_population_counts(
        report_pack
    )