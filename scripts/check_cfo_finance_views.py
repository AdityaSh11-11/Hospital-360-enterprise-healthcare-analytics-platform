from __future__ import annotations

from decimal import Decimal

from analytics.data_loader import (
    read_sql,
)


EXPECTED_VIEWS = {
    "vw_cfo_financial_scorecard": 1,
    "vw_monthly_cfo_performance": 46,
    "vw_department_cfo_performance": 10,
    "vw_cfo_payer_mix": 2,
    "vw_cfo_payment_method_mix": 4,
    "vw_cfo_receivable_exposure": 5,
    "vw_cfo_insurer_exposure": 5,
}


def separator() -> None:
    print("=" * 112)


def small_separator() -> None:
    print("-" * 112)


def money(value) -> str:
    if value is None:
        return "0.00"

    return (
        f"{Decimal(str(value)):,.2f}"
    )


def check_views() -> None:
    print()
    print("CFO ANALYTICS VIEWS")
    small_separator()

    for (
        view_name,
        expected_rows,
    ) in EXPECTED_VIEWS.items():

        result = read_sql(
            f"""
            SELECT
                COUNT(*) AS row_count
            FROM analytics.{view_name}
            """
        )

        actual_rows = int(
            result.iloc[0][
                "row_count"
            ]
        )

        status = (
            "PASS"
            if actual_rows
            == expected_rows
            else "FAIL"
        )

        print(
            f"{view_name:<48}"
            f"{actual_rows:>12,}"
            f"{status:>14}"
        )

        if actual_rows != expected_rows:
            raise RuntimeError(
                f"{view_name}: expected "
                f"{expected_rows:,} rows, "
                f"found {actual_rows:,}."
            )


def reconcile_scorecard() -> None:
    source = read_sql(
        """
        SELECT
            COUNT(*) AS total_bills,

            ROUND(
                SUM(gross_amount)::numeric,
                2
            ) AS gross_revenue,

            ROUND(
                SUM(discount_amount)::numeric,
                2
            ) AS discount_amount,

            ROUND(
                SUM(net_amount)::numeric,
                2
            ) AS net_revenue,

            ROUND(
                SUM(insurance_amount)::numeric,
                2
            ) AS insurance_receivable,

            ROUND(
                SUM(patient_amount)::numeric,
                2
            ) AS patient_responsibility,

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

    analytics = read_sql(
        """
        SELECT *
        FROM analytics.vw_cfo_financial_scorecard
        """
    ).iloc[0]

    print()
    print("CFO SCORECARD RECONCILIATION")
    small_separator()

    print(
        f"{'Metric':<38}"
        f"{'Warehouse':>30}"
        f"{'CFO View':>30}"
    )

    small_separator()

    count_metrics = [
        "total_bills",
    ]

    money_metrics = [
        "gross_revenue",
        "discount_amount",
        "net_revenue",
        "insurance_receivable",
        "patient_responsibility",
        "collected_amount",
        "outstanding_amount",
    ]

    for metric in count_metrics:
        warehouse_value = int(
            source[metric]
        )

        view_value = int(
            analytics[metric]
        )

        print(
            f"{metric:<38}"
            f"{warehouse_value:>30,}"
            f"{view_value:>30,}"
        )

        if warehouse_value != view_value:
            raise RuntimeError(
                f"{metric} reconciliation failed."
            )

    for metric in money_metrics:
        warehouse_value = float(
            source[metric]
        )

        view_value = float(
            analytics[metric]
        )

        print(
            f"{metric:<38}"
            f"{money(warehouse_value):>30}"
            f"{money(view_value):>30}"
        )

        if abs(
            warehouse_value
            - view_value
        ) > 0.05:
            raise RuntimeError(
                f"{metric} reconciliation failed."
            )

    print()
    print(
        "[PASS] CFO scorecard reconciled."
    )


def reconcile_claims() -> None:
    source = read_sql(
        """
        SELECT
            COUNT(*) AS total_claims,

            ROUND(
                SUM(claim_amount)::numeric,
                2
            ) AS claim_amount,

            ROUND(
                SUM(approved_amount)::numeric,
                2
            ) AS approved_amount,

            ROUND(
                SUM(rejected_amount)::numeric,
                2
            ) AS rejected_amount

        FROM warehouse.fact_claim
        """
    ).iloc[0]

    analytics = read_sql(
        """
        SELECT *
        FROM analytics.vw_cfo_financial_scorecard
        """
    ).iloc[0]

    print()
    print("CLAIM FINANCIAL RECONCILIATION")
    small_separator()

    print(
        f"{'Claims':<38}"
        f"{int(source['total_claims']):>30,}"
        f"{int(analytics['total_claims']):>30,}"
    )

    if (
        int(source["total_claims"])
        != int(
            analytics[
                "total_claims"
            ]
        )
    ):
        raise RuntimeError(
            "Claim count reconciliation failed."
        )

    for metric in [
        "claim_amount",
        "approved_amount",
        "rejected_amount",
    ]:
        source_value = float(
            source[metric]
        )

        analytics_value = float(
            analytics[metric]
        )

        print(
            f"{metric:<38}"
            f"{money(source_value):>30}"
            f"{money(analytics_value):>30}"
        )

        if abs(
            source_value
            - analytics_value
        ) > 0.05:
            raise RuntimeError(
                f"{metric} reconciliation failed."
            )

    print()
    print(
        "[PASS] Claim finance reconciled."
    )


def reconcile_departments() -> None:
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

    analytics = read_sql(
        """
        SELECT
            SUM(bills) AS bills,

            ROUND(
                SUM(net_revenue)::numeric,
                2
            ) AS net_revenue,

            ROUND(
                SUM(collected_amount)::numeric,
                2
            ) AS collected_amount,

            ROUND(
                SUM(outstanding_amount)::numeric,
                2
            ) AS outstanding_amount

        FROM analytics.vw_department_cfo_performance
        """
    ).iloc[0]

    print()
    print("DEPARTMENT CFO RECONCILIATION")
    small_separator()

    metrics = [
        "bills",
        "net_revenue",
        "collected_amount",
        "outstanding_amount",
    ]

    for metric in metrics:
        if metric == "bills":
            source_value = int(
                source[metric]
            )

            analytics_value = int(
                analytics[metric]
            )

            print(
                f"{metric:<38}"
                f"{source_value:>30,}"
                f"{analytics_value:>30,}"
            )

            if (
                source_value
                != analytics_value
            ):
                raise RuntimeError(
                    "Department bill "
                    "reconciliation failed."
                )

        else:
            source_value = float(
                source[metric]
            )

            analytics_value = float(
                analytics[metric]
            )

            print(
                f"{metric:<38}"
                f"{money(source_value):>30}"
                f"{money(analytics_value):>30}"
            )

            if abs(
                source_value
                - analytics_value
            ) > 0.05:
                raise RuntimeError(
                    f"Department {metric} "
                    "reconciliation failed."
                )

    print()
    print(
        "[PASS] Department CFO totals reconciled."
    )


def reconcile_payer_mix() -> None:
    source = read_sql(
        """
        SELECT
            COUNT(*) AS bills,

            ROUND(
                SUM(net_amount)::numeric,
                2
            ) AS net_revenue

        FROM warehouse.fact_billing
        """
    ).iloc[0]

    analytics = read_sql(
        """
        SELECT
            SUM(bills) AS bills,

            ROUND(
                SUM(net_revenue)::numeric,
                2
            ) AS net_revenue,

            ROUND(
                SUM(revenue_mix_pct)::numeric,
                2
            ) AS revenue_mix_pct

        FROM analytics.vw_cfo_payer_mix
        """
    ).iloc[0]

    print()
    print("PAYER MIX RECONCILIATION")
    small_separator()

    print(
        f"{'Bills':<38}"
        f"{int(source['bills']):>30,}"
        f"{int(analytics['bills']):>30,}"
    )

    print(
        f"{'Net revenue':<38}"
        f"{money(source['net_revenue']):>30}"
        f"{money(analytics['net_revenue']):>30}"
    )

    print(
        f"{'Revenue mix %':<38}"
        f"{'100.00':>30}"
        f"{float(analytics['revenue_mix_pct']):>30.2f}"
    )

    if (
        int(source["bills"])
        != int(analytics["bills"])
    ):
        raise RuntimeError(
            "Payer bill reconciliation failed."
        )

    if abs(
        float(source["net_revenue"])
        - float(
            analytics[
                "net_revenue"
            ]
        )
    ) > 0.05:
        raise RuntimeError(
            "Payer revenue reconciliation failed."
        )

    if abs(
        float(
            analytics[
                "revenue_mix_pct"
            ]
        )
        - 100.0
    ) > 0.05:
        raise RuntimeError(
            "Payer revenue mix does not sum to 100%."
        )

    print()
    print(
        "[PASS] Payer mix reconciled."
    )


def show_scorecard() -> None:
    scorecard = read_sql(
        """
        SELECT *
        FROM analytics.vw_cfo_financial_scorecard
        """
    )

    print()
    print("CFO SCORECARD")
    small_separator()

    print(
        scorecard.to_string(
            index=False
        )
    )


def show_receivable_exposure() -> None:
    data = read_sql(
        """
        SELECT
            exposure_band,
            bills,
            patients,
            outstanding_amount,
            outstanding_share_pct

        FROM analytics.vw_cfo_receivable_exposure

        ORDER BY exposure_order
        """
    )

    print()
    print("RECEIVABLE EXPOSURE")
    small_separator()

    print(
        data.to_string(
            index=False
        )
    )


def show_insurer_exposure() -> None:
    data = read_sql(
        """
        SELECT
            insurer_name,
            total_claims,
            claim_amount,
            rejected_amount,
            claim_rejection_rate_pct,
            rejected_value_rate_pct,
            rejected_value_share_pct

        FROM analytics.vw_cfo_insurer_exposure

        ORDER BY rejected_value_rank
        """
    )

    print()
    print("INSURER FINANCIAL EXPOSURE")
    small_separator()

    print(
        data.to_string(
            index=False
        )
    )


def main() -> None:
    separator()

    print(
        "HOSPITAL 360 — "
        "PHASE 7.1 CFO FINANCE VALIDATION"
    )

    separator()

    check_views()

    reconcile_scorecard()

    reconcile_claims()

    reconcile_departments()

    reconcile_payer_mix()

    show_scorecard()

    show_receivable_exposure()

    show_insurer_exposure()

    print()
    separator()

    print(
        "PHASE 7.1 CFO FINANCE "
        "INTELLIGENCE VALIDATION PASSED"
    )

    separator()


if __name__ == "__main__":
    main()