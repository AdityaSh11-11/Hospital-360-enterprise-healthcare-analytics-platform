from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pandas as pd

from analytics.data_loader import (
    read_sql,
)
from scripts.run_statistical_analysis import (
    EXPORT_DIRECTORY,
)


EXPECTED_EXPORTS = [
    "finance_distribution.csv",
    "payment_status_statistics.csv",
    "department_finance_statistics.csv",
    "monthly_finance_statistics.csv",
    "doctor_revenue_concentration.csv",
    "department_revenue_concentration.csv",
    "los_statistics.csv",
    "department_operations_statistics.csv",
    "admission_type_statistics.csv",
    "day_of_week_statistics.csv",
    "monthly_operations_statistics.csv",
    "patient_age_statistics.csv",
    "patient_utilization_statistics.csv",
    "patient_utilization_segmentation.csv",
    "chronic_condition_statistics.csv",
    "insurance_statistics.csv",
]


def separator() -> None:
    print("=" * 108)


def small_separator() -> None:
    print("-" * 108)


def money(value) -> str:

    if value is None:
        return "0.00"

    return f"{Decimal(str(value)):,.2f}"


def load_export(
    filename: str,
) -> pd.DataFrame:

    path = (
        EXPORT_DIRECTORY
        / filename
    )

    if not path.exists():
        raise RuntimeError(
            f"Missing statistical export: {filename}"
        )

    return pd.read_csv(
        path
    )


def check_exports() -> None:

    print()
    print("STATISTICAL EXPORT FILES")
    small_separator()

    failed = []

    for filename in EXPECTED_EXPORTS:

        path = (
            EXPORT_DIRECTORY
            / filename
        )

        if not path.exists():

            print(
                f"{filename:<58}"
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
            f"{filename:<58}"
            f"{len(dataframe):>12,}"
            f" rows   PASS"
        )

    if failed:
        raise RuntimeError(
            "Missing statistical exports: "
            + ", ".join(failed)
        )


def reconcile_department_operations() -> None:

    dataframe = load_export(
        "department_operations_statistics.csv"
    )

    source = read_sql(
        """
        SELECT
            COUNT(*) AS admissions,
            COUNT(DISTINCT patient_key) AS patients,
            SUM(length_of_stay) AS inpatient_days,
            COUNT(*) FILTER (
                WHERE emergency_flag = TRUE
            ) AS emergency_admissions,
            COUNT(*) FILTER (
                WHERE icu_flag = TRUE
            ) AS icu_admissions,
            COUNT(*) FILTER (
                WHERE readmission_flag = TRUE
            ) AS readmissions

        FROM warehouse.fact_admission
        """
    ).iloc[0]

    python_metrics = {
        "admissions": int(
            dataframe[
                "admissions"
            ].sum()
        ),
        "inpatient_days": int(
            dataframe[
                "total_inpatient_days"
            ].sum()
        ),
        "emergency_admissions": int(
            dataframe[
                "emergency_admissions"
            ].sum()
        ),
        "icu_admissions": int(
            dataframe[
                "icu_admissions"
            ].sum()
        ),
        "readmissions": int(
            dataframe[
                "readmissions"
            ].sum()
        ),
    }

    print()
    print("OPERATIONS RECONCILIATION")
    small_separator()

    print(
        f"{'Metric':<38}"
        f"{'Warehouse':>22}"
        f"{'Python':>22}"
    )

    small_separator()

    metrics = [
        "admissions",
        "inpatient_days",
        "emergency_admissions",
        "icu_admissions",
        "readmissions",
    ]

    for metric in metrics:

        warehouse_value = int(
            source[metric]
        )

        python_value = int(
            python_metrics[metric]
        )

        print(
            f"{metric:<38}"
            f"{warehouse_value:>22,}"
            f"{python_value:>22,}"
        )

        if (
            warehouse_value
            != python_value
        ):
            raise RuntimeError(
                f"Operations reconciliation "
                f"failed for {metric}."
            )

    print()
    print(
        "[PASS] Operations reconciliation passed."
    )


def reconcile_finance() -> None:

    dataframe = load_export(
        "department_finance_statistics.csv"
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

    python_bills = int(
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
    print("FINANCE RECONCILIATION")
    small_separator()

    print(
        f"{'Metric':<38}"
        f"{'Warehouse':>26}"
        f"{'Python':>26}"
    )

    small_separator()

    print(
        f"{'Bills':<38}"
        f"{int(source['bills']):>26,}"
        f"{python_bills:>26,}"
    )

    print(
        f"{'Net revenue':<38}"
        f"{money(source['net_revenue']):>26}"
        f"{money(python_revenue):>26}"
    )

    print(
        f"{'Collected amount':<38}"
        f"{money(source['collected_amount']):>26}"
        f"{money(python_collected):>26}"
    )

    print(
        f"{'Outstanding amount':<38}"
        f"{money(source['outstanding_amount']):>26}"
        f"{money(python_outstanding):>26}"
    )

    if (
        int(source["bills"])
        != python_bills
    ):
        raise RuntimeError(
            "Finance bill reconciliation failed."
        )

    tolerance = 0.05

    comparisons = [
        (
            "net_revenue",
            float(source["net_revenue"]),
            python_revenue,
        ),
        (
            "collected_amount",
            float(source["collected_amount"]),
            python_collected,
        ),
        (
            "outstanding_amount",
            float(source["outstanding_amount"]),
            python_outstanding,
        ),
    ]

    for (
        metric,
        warehouse_value,
        python_value,
    ) in comparisons:

        if abs(
            warehouse_value
            - python_value
        ) > tolerance:
            raise RuntimeError(
                f"Finance reconciliation "
                f"failed for {metric}."
            )

    print()
    print(
        "[PASS] Finance reconciliation passed."
    )


def reconcile_monthly_operations() -> None:

    dataframe = load_export(
        "monthly_operations_statistics.csv"
    )

    source = read_sql(
        """
        SELECT
            COUNT(DISTINCT date_trunc(
                'month',
                d.full_date
            )) AS months,

            COUNT(*) AS admissions

        FROM warehouse.fact_admission a

        INNER JOIN warehouse.dim_date d
            ON d.date_key =
               a.admission_date_key
        """
    ).iloc[0]

    python_months = len(
        dataframe
    )

    python_admissions = int(
        dataframe[
            "admissions"
        ].sum()
    )

    print()
    print("MONTHLY OPERATIONS RECONCILIATION")
    small_separator()

    print(
        f"{'Operational months':<38}"
        f"{int(source['months']):>22,}"
        f"{python_months:>22,}"
    )

    print(
        f"{'Admissions':<38}"
        f"{int(source['admissions']):>22,}"
        f"{python_admissions:>22,}"
    )

    if (
        int(source["months"])
        != python_months
    ):
        raise RuntimeError(
            "Operational month reconciliation failed."
        )

    if (
        int(source["admissions"])
        != python_admissions
    ):
        raise RuntimeError(
            "Monthly admission reconciliation failed."
        )

    print()
    print(
        "[PASS] Monthly operations reconciliation passed."
    )


def validate_statistical_outputs() -> None:

    finance_distribution = load_export(
        "finance_distribution.csv"
    )

    los_statistics = load_export(
        "los_statistics.csv"
    )

    department_operations = load_export(
        "department_operations_statistics.csv"
    )

    if finance_distribution.empty:
        raise RuntimeError(
            "Finance distribution is empty."
        )

    if los_statistics.empty:
        raise RuntimeError(
            "LOS statistics are empty."
        )

    if len(
        department_operations
    ) != 10:
        raise RuntimeError(
            "Expected 10 departments in "
            "department operations output."
        )

    if (
        department_operations[
            "admissions"
        ] < 0
    ).any():
        raise RuntimeError(
            "Negative admission count detected."
        )

    if (
        department_operations[
            "readmission_rate_pct"
        ] < 0
    ).any():
        raise RuntimeError(
            "Negative readmission rate detected."
        )

    if (
        department_operations[
            "readmission_rate_pct"
        ] > 100
    ).any():
        raise RuntimeError(
            "Readmission rate above 100% detected."
        )

    print()
    print("STATISTICAL SANITY CHECKS")
    small_separator()

    print(
        "[PASS] Finance distributions populated."
    )

    print(
        "[PASS] LOS distribution populated."
    )

    print(
        "[PASS] Department population = 10."
    )

    print(
        "[PASS] Operational rates within valid bounds."
    )


def main() -> None:

    separator()

    print(
        "HOSPITAL 360 — "
        "PHASE 6.2 STATISTICAL ANALYTICS VALIDATION"
    )

    separator()

    if not EXPORT_DIRECTORY.exists():
        raise RuntimeError(
            "Statistics export directory does not exist. "
            "Run scripts.run_statistical_analysis first."
        )

    check_exports()

    reconcile_operations = (
        reconcile_department_operations
    )

    reconcile_operations()

    reconcile_finance()

    reconcile_monthly_operations()

    validate_statistical_outputs()

    print()
    separator()

    print(
        "PHASE 6.2 STATISTICAL BUSINESS "
        "ANALYTICS VALIDATION PASSED"
    )

    separator()


if __name__ == "__main__":
    main()