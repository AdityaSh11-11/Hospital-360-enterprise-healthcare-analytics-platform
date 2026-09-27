from __future__ import annotations

from decimal import Decimal

import pandas as pd

from analytics.data_loader import (
    read_sql,
)
from scripts.run_business_analysis import (
    EXPORT_DIRECTORY,
)


EXPECTED_EXPORTS = [
    "monthly_kpi_variance.csv",
    "department_benchmark.csv",
    "doctor_benchmark.csv",
    "finance_diagnostics.csv",
    "claim_diagnostics.csv",
    "operational_driver_analysis.csv",
    "management_insights.csv",
]


def separator() -> None:
    print("=" * 112)


def small_separator() -> None:
    print("-" * 112)


def money(value) -> str:
    return (
        f"{Decimal(str(value)):,.2f}"
    )


def load_export(
    filename: str,
) -> pd.DataFrame:
    path = (
        EXPORT_DIRECTORY
        / filename
    )

    if not path.exists():
        raise RuntimeError(
            f"Missing export: {filename}"
        )

    return pd.read_csv(
        path
    )


def check_exports() -> None:
    print()
    print("BUSINESS ANALYSIS EXPORTS")
    small_separator()

    failed = []

    for filename in EXPECTED_EXPORTS:
        path = (
            EXPORT_DIRECTORY
            / filename
        )

        if not path.exists():
            print(
                f"{filename:<60}"
                f"{'MISSING':>18}"
            )

            failed.append(
                filename
            )

            continue

        dataframe = pd.read_csv(
            path
        )

        print(
            f"{filename:<60}"
            f"{len(dataframe):>12,}"
            f" rows   PASS"
        )

    if failed:
        raise RuntimeError(
            "Missing exports: "
            + ", ".join(failed)
        )


def reconcile_department_benchmark() -> None:
    dataframe = load_export(
        "department_benchmark.csv"
    )

    source = read_sql(
        """
        SELECT
            COUNT(*) AS admissions,
            ROUND(
                SUM(b.net_amount)::numeric,
                2
            ) AS net_revenue

        FROM warehouse.fact_admission a

        INNER JOIN warehouse.fact_billing b
            ON b.admission_key =
               a.admission_key
        """
    ).iloc[0]

    python_admissions = int(
        dataframe[
            "admissions"
        ].sum()
    )

    python_revenue = round(
        float(
            dataframe[
                "net_revenue"
            ].sum()
        ),
        2,
    )

    print()
    print("DEPARTMENT BENCHMARK RECONCILIATION")
    small_separator()

    print(
        f"{'Metric':<40}"
        f"{'Warehouse':>28}"
        f"{'Python':>28}"
    )

    small_separator()

    print(
        f"{'Admissions':<40}"
        f"{int(source['admissions']):>28,}"
        f"{python_admissions:>28,}"
    )

    print(
        f"{'Net revenue':<40}"
        f"{money(source['net_revenue']):>28}"
        f"{money(python_revenue):>28}"
    )

    if (
        int(source["admissions"])
        != python_admissions
    ):
        raise RuntimeError(
            "Department admission reconciliation failed."
        )

    if abs(
        float(source["net_revenue"])
        - python_revenue
    ) > 0.05:
        raise RuntimeError(
            "Department revenue reconciliation failed."
        )

    print()
    print(
        "[PASS] Department benchmark reconciled."
    )


def reconcile_doctors() -> None:
    dataframe = load_export(
        "doctor_benchmark.csv"
    )

    source = read_sql(
        """
        SELECT
            COUNT(*) AS doctors

        FROM warehouse.dim_doctor
        """
    ).iloc[0]

    python_doctors = int(
        dataframe[
            "doctor_id"
        ].nunique()
    )

    print()
    print("DOCTOR BENCHMARK RECONCILIATION")
    small_separator()

    print(
        f"{'Warehouse doctors':<40}"
        f"{int(source['doctors']):>20,}"
    )

    print(
        f"{'Python doctors':<40}"
        f"{python_doctors:>20,}"
    )

    if (
        int(source["doctors"])
        != python_doctors
    ):
        raise RuntimeError(
            "Doctor benchmark reconciliation failed."
        )

    print()
    print(
        "[PASS] Doctor benchmark reconciled."
    )


def reconcile_finance() -> None:
    dataframe = load_export(
        "finance_diagnostics.csv"
    )

    source = read_sql(
        """
        SELECT
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

    python_revenue = round(
        float(
            dataframe[
                "net_revenue"
            ].sum()
        ),
        2,
    )

    python_collected = round(
        float(
            dataframe[
                "collected_amount"
            ].sum()
        ),
        2,
    )

    python_outstanding = round(
        float(
            dataframe[
                "outstanding_amount"
            ].sum()
        ),
        2,
    )

    print()
    print("FINANCE DIAGNOSTIC RECONCILIATION")
    small_separator()

    comparisons = [
        (
            "Net revenue",
            float(
                source[
                    "net_revenue"
                ]
            ),
            python_revenue,
        ),
        (
            "Collected amount",
            float(
                source[
                    "collected_amount"
                ]
            ),
            python_collected,
        ),
        (
            "Outstanding amount",
            float(
                source[
                    "outstanding_amount"
                ]
            ),
            python_outstanding,
        ),
    ]

    for (
        label,
        warehouse_value,
        python_value,
    ) in comparisons:
        print(
            f"{label:<40}"
            f"{money(warehouse_value):>28}"
            f"{money(python_value):>28}"
        )

        if abs(
            warehouse_value
            - python_value
        ) > 0.05:
            raise RuntimeError(
                f"{label} reconciliation failed."
            )

    print()
    print(
        "[PASS] Finance diagnostics reconciled."
    )


def reconcile_claims() -> None:
    dataframe = load_export(
        "claim_diagnostics.csv"
    )

    source = read_sql(
        """
        SELECT
            COUNT(*) AS claims,

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

    python_claims = int(
        dataframe[
            "total_claims"
        ].sum()
    )

    python_claim_amount = round(
        float(
            dataframe[
                "claim_amount"
            ].sum()
        ),
        2,
    )

    python_rejected_amount = round(
        float(
            dataframe[
                "rejected_amount"
            ].sum()
        ),
        2,
    )

    print()
    print("CLAIM DIAGNOSTIC RECONCILIATION")
    small_separator()

    print(
        f"{'Claims':<40}"
        f"{int(source['claims']):>28,}"
        f"{python_claims:>28,}"
    )

    print(
        f"{'Claim amount':<40}"
        f"{money(source['claim_amount']):>28}"
        f"{money(python_claim_amount):>28}"
    )

    print(
        f"{'Rejected amount':<40}"
        f"{money(source['rejected_amount']):>28}"
        f"{money(python_rejected_amount):>28}"
    )

    if (
        int(source["claims"])
        != python_claims
    ):
        raise RuntimeError(
            "Claim count reconciliation failed."
        )

    if abs(
        float(source["claim_amount"])
        - python_claim_amount
    ) > 0.05:
        raise RuntimeError(
            "Claim amount reconciliation failed."
        )

    if abs(
        float(source["rejected_amount"])
        - python_rejected_amount
    ) > 0.05:
        raise RuntimeError(
            "Rejected amount reconciliation failed."
        )

    print()
    print(
        "[PASS] Claim diagnostics reconciled."
    )


def reconcile_operational_drivers() -> None:
    dataframe = load_export(
        "operational_driver_analysis.csv"
    )

    all_admissions = dataframe.loc[
        dataframe["cohort"]
        == "All Admissions"
    ]

    if len(all_admissions) != 1:
        raise RuntimeError(
            "All Admissions cohort missing or duplicated."
        )

    python_admissions = int(
        all_admissions.iloc[0][
            "admissions"
        ]
    )

    source = read_sql(
        """
        SELECT
            COUNT(*) AS admissions
        FROM warehouse.fact_admission
        """
    ).iloc[0]

    print()
    print("OPERATIONAL DRIVER RECONCILIATION")
    small_separator()

    print(
        f"{'Warehouse admissions':<40}"
        f"{int(source['admissions']):>20,}"
    )

    print(
        f"{'Python All Admissions cohort':<40}"
        f"{python_admissions:>20,}"
    )

    if (
        int(source["admissions"])
        != python_admissions
    ):
        raise RuntimeError(
            "Operational driver reconciliation failed."
        )

    print()
    print(
        "[PASS] Operational driver analysis reconciled."
    )


def sanity_checks() -> None:
    departments = load_export(
        "department_benchmark.csv"
    )

    doctors = load_export(
        "doctor_benchmark.csv"
    )

    finance = load_export(
        "finance_diagnostics.csv"
    )

    claims = load_export(
        "claim_diagnostics.csv"
    )

    monthly = load_export(
        "monthly_kpi_variance.csv"
    )

    insights = load_export(
        "management_insights.csv"
    )

    if len(departments) != 10:
        raise RuntimeError(
            "Expected 10 departments."
        )

    if (
        doctors[
            "doctor_id"
        ].nunique()
        != 150
    ):
        raise RuntimeError(
            "Expected 150 doctors."
        )

    if len(finance) != 10:
        raise RuntimeError(
            "Expected 10 finance department rows."
        )

    if len(claims) != 5:
        raise RuntimeError(
            "Expected 5 insurer rows."
        )

    if len(monthly) != 45:
        raise RuntimeError(
            "Expected 45 operational months."
        )

    if insights.empty:
        raise RuntimeError(
            "Management insight table is empty."
        )

    rate_columns = [
        (
            finance,
            "collection_efficiency_pct_python",
        ),
        (
            finance,
            "outstanding_rate_pct_python",
        ),
        (
            claims,
            "rejected_amount_rate_pct",
        ),
    ]

    for dataframe, column in rate_columns:
        if column not in dataframe.columns:
            continue

        invalid = (
            dataframe[column].dropna()
            < 0
        )

        if invalid.any():
            raise RuntimeError(
                f"Negative rate detected: {column}"
            )

    print()
    print("BUSINESS ANALYSIS SANITY CHECKS")
    small_separator()

    print(
        "[PASS] Department population = 10."
    )

    print(
        "[PASS] Doctor population = 150."
    )

    print(
        "[PASS] Insurer population = 5."
    )

    print(
        "[PASS] Operational months = 45."
    )

    print(
        "[PASS] Management insight table populated."
    )

    print(
        "[PASS] Diagnostic rates passed basic bounds."
    )


def main() -> None:
    separator()

    print(
        "HOSPITAL 360 — "
        "PHASE 6.3 BUSINESS ANALYSIS VALIDATION"
    )

    separator()

    if not EXPORT_DIRECTORY.exists():
        raise RuntimeError(
            "Business analysis export directory "
            "does not exist. Run "
            "scripts.run_business_analysis first."
        )

    check_exports()

    reconcile_department_benchmark()

    reconcile_doctors()

    reconcile_finance()

    reconcile_claims()

    reconcile_operational_drivers()

    sanity_checks()

    print()
    separator()

    print(
        "PHASE 6.3 ADVANCED BUSINESS "
        "ANALYSIS VALIDATION PASSED"
    )

    separator()


if __name__ == "__main__":
    main()