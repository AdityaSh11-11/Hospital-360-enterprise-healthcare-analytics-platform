from __future__ import annotations

import numpy as np
import pandas as pd

from analytics.data_loader import read_sql
from analytics.risk_intelligence import (
    run_unified_risk_intelligence,
)


def separator() -> None:
    print("=" * 116)


def small_separator() -> None:
    print("-" * 116)


def assert_equal(
    label: str,
    actual: int,
    expected: int,
) -> None:
    if int(actual) != int(expected):
        raise RuntimeError(
            f"{label} failed: "
            f"{actual:,} != {expected:,}"
        )


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
            f"{actual} != {expected}"
        )


def kpi_value(
    dataframe: pd.DataFrame,
    name: str,
) -> float:
    matches = dataframe[
        dataframe["kpi"] == name
    ]

    if len(matches) != 1:
        raise RuntimeError(
            f"Expected exactly one KPI "
            f"named '{name}', found "
            f"{len(matches)}."
        )

    return float(
        matches.iloc[0]["value"]
    )


def check_output_structure(
    outputs: dict[str, pd.DataFrame],
) -> None:
    expected = {
        "enterprise_risk_kpis",
        "risk_domain_summary",
        "patient_priority_register",
        "financial_priority_register",
        "claim_priority_register",
        "department_risk_matrix",
        "insurer_risk_summary",
        "aggregate_review_signals",
        "risk_dashboard_feed",
        "enterprise_risk_insights",
    }

    missing = (
        expected
        - set(outputs.keys())
    )

    if missing:
        raise RuntimeError(
            "Missing unified risk outputs: "
            + ", ".join(
                sorted(missing)
            )
        )

    print()
    print("UNIFIED RISK OUTPUT STRUCTURE")
    small_separator()

    for name in sorted(expected):
        dataframe = outputs[name]

        print(
            f"{name:<50}"
            f"{len(dataframe):>14,}"
            f"{len(dataframe.columns):>14,}"
        )

    print()
    print(
        "[PASS] Unified risk output "
        "structure validated."
    )


def check_priority_populations(
    outputs: dict[str, pd.DataFrame],
) -> None:
    patient = outputs[
        "patient_priority_register"
    ]

    financial = outputs[
        "financial_priority_register"
    ]

    claims = outputs[
        "claim_priority_register"
    ]

    anomalies = outputs[
        "aggregate_review_signals"
    ]

    assert_equal(
        "High risk patient population",
        len(patient),
        2095,
    )

    assert_equal(
        "High financial risk bill population",
        len(financial),
        5488,
    )

    assert_equal(
        "High claim risk population",
        len(claims),
        2967,
    )

    assert_equal(
        "Aggregate anomaly population",
        len(anomalies),
        25,
    )

    print()
    print("PRIORITY POPULATIONS")
    small_separator()

    print(
        f"{'High risk patients':<42}"
        f"{len(patient):>16,}"
    )

    print(
        f"{'High financial risk bills':<42}"
        f"{len(financial):>16,}"
    )

    print(
        f"{'High risk claims':<42}"
        f"{len(claims):>16,}"
    )

    print(
        f"{'Aggregate review signals':<42}"
        f"{len(anomalies):>16,}"
    )

    print()
    print(
        "[PASS] Priority populations validated."
    )


def check_kpi_reconciliation(
    outputs: dict[str, pd.DataFrame],
) -> None:
    kpis = outputs[
        "enterprise_risk_kpis"
    ]

    source = read_sql(
        """
        SELECT
            (
                SELECT COUNT(*)
                FROM warehouse.fact_admission
            ) AS admissions,

            (
                SELECT COUNT(DISTINCT patient_key)
                FROM warehouse.fact_admission
            ) AS admitted_patients,

            (
                SELECT ROUND(
                    SUM(outstanding_amount)::numeric,
                    2
                )
                FROM warehouse.fact_billing
            ) AS outstanding_amount,

            (
                SELECT ROUND(
                    SUM(rejected_amount)::numeric,
                    2
                )
                FROM warehouse.fact_claim
            ) AS rejected_amount
        """
    ).iloc[0]

    assert_equal(
        "Admitted patients",
        int(
            kpi_value(
                kpis,
                "Admitted Patients Assessed",
            )
        ),
        int(
            source[
                "admitted_patients"
            ]
        ),
    )

    assert_close(
        "Total outstanding",
        kpi_value(
            kpis,
            "Total Recorded Outstanding",
        ),
        float(
            source[
                "outstanding_amount"
            ]
        ),
    )

    assert_close(
        "Rejected claim value",
        kpi_value(
            kpis,
            "Rejected Claim Value",
        ),
        float(
            source[
                "rejected_amount"
            ]
        ),
    )

    assert_equal(
        "High risk patients KPI",
        int(
            kpi_value(
                kpis,
                "High Risk Patients",
            )
        ),
        2095,
    )

    assert_equal(
        "High risk admissions KPI",
        int(
            kpi_value(
                kpis,
                "High Risk Admissions",
            )
        ),
        2437,
    )

    assert_equal(
        "High financial risk bills KPI",
        int(
            kpi_value(
                kpis,
                "High Financial Risk Bills",
            )
        ),
        5488,
    )

    assert_equal(
        "High risk claims KPI",
        int(
            kpi_value(
                kpis,
                "High Risk Claims",
            )
        ),
        2967,
    )

    print()
    print("ENTERPRISE KPI RECONCILIATION")
    small_separator()

    print(
        f"Admitted patients       : "
        f"{int(source['admitted_patients']):,}"
    )

    print(
        f"High risk patients      : "
        f"{int(kpi_value(kpis, 'High Risk Patients')):,}"
    )

    print(
        f"High risk admissions    : "
        f"{int(kpi_value(kpis, 'High Risk Admissions')):,}"
    )

    print(
        f"High financial bills    : "
        f"{int(kpi_value(kpis, 'High Financial Risk Bills')):,}"
    )

    print(
        f"High risk claims        : "
        f"{int(kpi_value(kpis, 'High Risk Claims')):,}"
    )

    print(
        f"Outstanding             : "
        f"{kpi_value(kpis, 'Total Recorded Outstanding'):,.2f}"
    )

    print(
        f"Rejected claim value    : "
        f"{kpi_value(kpis, 'Rejected Claim Value'):,.2f}"
    )

    print()
    print(
        "[PASS] Enterprise KPI reconciliation passed."
    )


def check_financial_exposure(
    outputs: dict[str, pd.DataFrame],
) -> None:
    financial = outputs[
        "financial_priority_register"
    ]

    source = read_sql(
        """
        SELECT
            ROUND(
                SUM(outstanding_amount)::numeric,
                2
            ) AS total_outstanding

        FROM analytics.vw_bill_financial_risk

        WHERE financial_risk_band = 'High'
        """
    ).iloc[0]

    actual = float(
        financial[
            "outstanding_amount"
        ].sum()
    )

    expected = float(
        source[
            "total_outstanding"
        ]
    )

    assert_close(
        "High-risk outstanding",
        actual,
        expected,
    )

    assert_close(
        "Known high-risk outstanding",
        actual,
        222542163.16,
    )

    print()
    print("HIGH FINANCIAL RISK EXPOSURE")
    small_separator()

    print(
        f"High-risk outstanding   : "
        f"{actual:,.2f}"
    )

    print()
    print(
        "[PASS] High-risk financial "
        "exposure reconciled."
    )


def check_department_matrix(
    outputs: dict[str, pd.DataFrame],
) -> None:
    dataframe = outputs[
        "department_risk_matrix"
    ]

    assert_equal(
        "Department matrix rows",
        len(dataframe),
        10,
    )

    if (
        dataframe[
            "department_key"
        ].duplicated().any()
    ):
        raise RuntimeError(
            "Duplicate department_key found "
            "in unified department matrix."
        )

    print()
    print("DEPARTMENT RISK MATRIX")
    small_separator()

    print(
        f"Departments             : "
        f"{len(dataframe):,}"
    )

    print(
        f"Unique department keys  : "
        f"{dataframe['department_key'].nunique():,}"
    )

    print()
    print(
        "[PASS] Department matrix grain validated."
    )


def check_no_overall_magic_score(
    outputs: dict[str, pd.DataFrame],
) -> None:
    forbidden = {
        "overall_risk_score",
        "enterprise_risk_score",
        "combined_risk_score",
        "master_risk_score",
    }

    for name, dataframe in outputs.items():
        overlap = (
            forbidden
            & set(dataframe.columns)
        )

        if overlap:
            raise RuntimeError(
                f"{name} contains prohibited "
                "synthetic overall risk score: "
                + ", ".join(
                    sorted(overlap)
                )
            )

    print()
    print(
        "[PASS] No synthetic enterprise-wide "
        "magic risk score created."
    )


def check_no_infinite_values(
    outputs: dict[str, pd.DataFrame],
) -> None:
    for name, dataframe in outputs.items():
        numeric = (
            dataframe
            .select_dtypes(
                include=["number"]
            )
        )

        if numeric.empty:
            continue

        array = numeric.to_numpy(
            dtype=float,
            na_value=np.nan,
        )

        if np.isinf(array).any():
            raise RuntimeError(
                f"Infinite numeric value "
                f"found in {name}."
            )

    print(
        "[PASS] No infinite numeric values "
        "found."
    )


def main() -> None:
    separator()

    print(
        "HOSPITAL 360 â€” "
        "PHASE 8.4 UNIFIED RISK VALIDATION"
    )

    separator()

    outputs = (
        run_unified_risk_intelligence()
    )

    check_output_structure(
        outputs
    )

    check_priority_populations(
        outputs
    )

    check_kpi_reconciliation(
        outputs
    )

    check_financial_exposure(
        outputs
    )

    check_department_matrix(
        outputs
    )

    check_no_overall_magic_score(
        outputs
    )

    check_no_infinite_values(
        outputs
    )

    print()
    separator()

    print(
        "PHASE 8.4 UNIFIED RISK "
        "INTELLIGENCE VALIDATION PASSED"
    )

    separator()


if __name__ == "__main__":
    main()


