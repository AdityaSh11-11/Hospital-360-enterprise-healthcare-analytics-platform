from __future__ import annotations

from decimal import Decimal

from sqlalchemy import text

from database.connection import engine


EXPECTED_VIEWS = [
    "vw_doctor_performance",
    "vw_doctor_workload",
    "vw_doctor_department_benchmark",
    "vw_doctor_analytics_summary",
    "vw_doctor_financial_contribution",
    "vw_monthly_doctor_performance",
    "vw_doctor_claim_performance",
    "vw_doctor_patient_utilization",
]


def separator() -> None:
    print("=" * 108)


def small_separator() -> None:
    print("-" * 108)


def money(value) -> str:

    if value is None:
        return "0.00"

    return f"{Decimal(value):,.2f}"


def get_views(connection) -> set[str]:

    return set(
        connection.execute(
            text(
                """
                SELECT table_name

                FROM information_schema.views

                WHERE table_schema = 'analytics'
                """
            )
        ).scalars().all()
    )


def get_count(
    connection,
    view_name: str,
) -> int:

    return int(
        connection.execute(
            text(
                f"""
                SELECT COUNT(*)
                FROM analytics.{view_name}
                """
            )
        ).scalar_one()
    )


def reconcile_doctors(connection) -> None:

    source = connection.execute(
        text(
            """
            SELECT
                COUNT(*) AS doctors

            FROM warehouse.dim_doctor
            """
        )
    ).mappings().one()

    analytics_row = connection.execute(
        text(
            """
            SELECT
                COUNT(*) AS doctors

            FROM analytics.vw_doctor_analytics_summary
            """
        )
    ).mappings().one()

    print()
    print("DOCTOR POPULATION RECONCILIATION")
    small_separator()

    print(
        f"{'Doctor dimension':<38}"
        f"{source['doctors']:>20,}"
        f"{analytics_row['doctors']:>20,}"
    )

    if (
        source["doctors"]
        != analytics_row["doctors"]
    ):
        raise RuntimeError(
            "Doctor population reconciliation failed."
        )

    print()
    print(
        "[PASS] Doctor population reconciliation passed."
    )


def reconcile_admissions(connection) -> None:

    source = connection.execute(
        text(
            """
            SELECT
                COUNT(*) AS admissions

            FROM warehouse.fact_admission
            """
        )
    ).mappings().one()

    analytics_row = connection.execute(
        text(
            """
            SELECT
                SUM(admissions) AS admissions

            FROM analytics.vw_doctor_analytics_summary
            """
        )
    ).mappings().one()

    print()
    print("DOCTOR ADMISSION RECONCILIATION")
    small_separator()

    print(
        f"{'Admissions':<38}"
        f"{source['admissions']:>20,}"
        f"{analytics_row['admissions']:>20,}"
    )

    if (
        source["admissions"]
        != analytics_row["admissions"]
    ):
        raise RuntimeError(
            "Doctor admission reconciliation failed."
        )

    print()
    print(
        "[PASS] Doctor admission reconciliation passed."
    )


def reconcile_finance(connection) -> None:

    source = connection.execute(
        text(
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
        )
    ).mappings().one()

    analytics_row = connection.execute(
        text(
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

            FROM analytics.vw_doctor_analytics_summary
            """
        )
    ).mappings().one()

    print()
    print("DOCTOR FINANCE RECONCILIATION")
    small_separator()

    print(
        f"{'Metric':<38}"
        f"{'Source':>24}"
        f"{'Doctor Analytics':>24}"
    )

    small_separator()

    print(
        f"{'Bills':<38}"
        f"{source['bills']:>24,}"
        f"{analytics_row['bills']:>24,}"
    )

    print(
        f"{'Net revenue':<38}"
        f"{money(source['net_revenue']):>24}"
        f"{money(analytics_row['net_revenue']):>24}"
    )

    print(
        f"{'Collected amount':<38}"
        f"{money(source['collected_amount']):>24}"
        f"{money(analytics_row['collected_amount']):>24}"
    )

    print(
        f"{'Outstanding amount':<38}"
        f"{money(source['outstanding_amount']):>24}"
        f"{money(analytics_row['outstanding_amount']):>24}"
    )

    if source["bills"] != analytics_row["bills"]:
        raise RuntimeError(
            "Doctor bill reconciliation failed."
        )

    if (
        source["net_revenue"]
        != analytics_row["net_revenue"]
    ):
        raise RuntimeError(
            "Doctor net-revenue reconciliation failed."
        )

    if (
        source["collected_amount"]
        != analytics_row["collected_amount"]
    ):
        raise RuntimeError(
            "Doctor collection reconciliation failed."
        )

    if (
        source["outstanding_amount"]
        != analytics_row["outstanding_amount"]
    ):
        raise RuntimeError(
            "Doctor outstanding reconciliation failed."
        )

    print()
    print(
        "[PASS] Doctor finance reconciliation passed."
    )


def reconcile_claims(connection) -> None:

    source = connection.execute(
        text(
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
        )
    ).mappings().one()

    analytics_row = connection.execute(
        text(
            """
            SELECT
                SUM(total_claims) AS claims,

                ROUND(
                    SUM(total_claim_amount)::numeric,
                    2
                ) AS claim_amount,

                ROUND(
                    SUM(rejected_amount)::numeric,
                    2
                ) AS rejected_amount

            FROM analytics.vw_doctor_claim_performance
            """
        )
    ).mappings().one()

    print()
    print("DOCTOR CLAIM RECONCILIATION")
    small_separator()

    print(
        f"{'Metric':<38}"
        f"{'Source':>24}"
        f"{'Doctor Analytics':>24}"
    )

    small_separator()

    print(
        f"{'Claims':<38}"
        f"{source['claims']:>24,}"
        f"{analytics_row['claims']:>24,}"
    )

    print(
        f"{'Claim amount':<38}"
        f"{money(source['claim_amount']):>24}"
        f"{money(analytics_row['claim_amount']):>24}"
    )

    print(
        f"{'Rejected amount':<38}"
        f"{money(source['rejected_amount']):>24}"
        f"{money(analytics_row['rejected_amount']):>24}"
    )

    if source["claims"] != analytics_row["claims"]:
        raise RuntimeError(
            "Doctor claim-count reconciliation failed."
        )

    if (
        source["claim_amount"]
        != analytics_row["claim_amount"]
    ):
        raise RuntimeError(
            "Doctor claim-amount reconciliation failed."
        )

    if (
        source["rejected_amount"]
        != analytics_row["rejected_amount"]
    ):
        raise RuntimeError(
            "Doctor rejected-amount reconciliation failed."
        )

    print()
    print(
        "[PASS] Doctor claim reconciliation passed."
    )


def check_claim_statuses(connection) -> None:

    rows = connection.execute(
        text(
            """
            SELECT
                claim_status,
                COUNT(*) AS claims

            FROM warehouse.fact_claim

            GROUP BY
                claim_status

            ORDER BY
                claim_status
            """
        )
    ).mappings().all()

    print()
    print("SOURCE CLAIM STATUSES")
    small_separator()

    total = 0

    for row in rows:

        print(
            f"{str(row['claim_status']):<40}"
            f"{row['claims']:>15,}"
        )

        total += row["claims"]

    source_total = connection.execute(
        text(
            """
            SELECT COUNT(*)
            FROM warehouse.fact_claim
            """
        )
    ).scalar_one()

    if total != source_total:
        raise RuntimeError(
            "Claim-status count reconciliation failed."
        )

    print()
    print(
        "[PASS] Claim-status distribution reconciled."
    )


def print_top_doctors(connection) -> None:

    rows = connection.execute(
        text(
            """
            SELECT
                doctor_id,
                doctor_name,
                department_name,
                admissions,
                unique_patients,
                net_revenue,
                hospital_revenue_contribution_pct,
                hospital_revenue_rank

            FROM analytics.vw_doctor_analytics_summary

            ORDER BY
                hospital_revenue_rank,
                doctor_id

            LIMIT 10
            """
        )
    ).mappings().all()

    print()
    print("TOP DOCTORS BY NET REVENUE")
    small_separator()

    print(
        f"{'ID':<10}"
        f"{'Doctor':<28}"
        f"{'Department':<22}"
        f"{'Admissions':>12}"
        f"{'Patients':>12}"
        f"{'Net Revenue':>20}"
        f"{'Share %':>10}"
        f"{'Rank':>8}"
    )

    small_separator()

    for row in rows:

        print(
            f"{row['doctor_id']:<10}"
            f"{row['doctor_name'][:26]:<28}"
            f"{str(row['department_name'])[:20]:<22}"
            f"{row['admissions']:>12,}"
            f"{row['unique_patients']:>12,}"
            f"{money(row['net_revenue']):>20}"
            f"{str(row['hospital_revenue_contribution_pct']):>10}"
            f"{row['hospital_revenue_rank']:>8}"
        )


def print_department_summary(connection) -> None:

    rows = connection.execute(
        text(
            """
            SELECT
                department_name,

                COUNT(*) AS doctors,

                SUM(admissions) AS admissions,

                ROUND(
                    SUM(net_revenue)::numeric,
                    2
                ) AS net_revenue,

                ROUND(
                    AVG(
                        revenue_per_admission
                    )::numeric,
                    2
                ) AS avg_doctor_revenue_per_admission

            FROM analytics.vw_doctor_analytics_summary

            GROUP BY
                department_name

            ORDER BY
                net_revenue DESC
            """
        )
    ).mappings().all()

    print()
    print("DOCTOR ANALYTICS BY DEPARTMENT")
    small_separator()

    print(
        f"{'Department':<26}"
        f"{'Doctors':>10}"
        f"{'Admissions':>14}"
        f"{'Net Revenue':>22}"
        f"{'Avg Rev/Adm':>18}"
    )

    small_separator()

    for row in rows:

        print(
            f"{str(row['department_name'])[:24]:<26}"
            f"{row['doctors']:>10,}"
            f"{row['admissions']:>14,}"
            f"{money(row['net_revenue']):>22}"
            f"{money(row['avg_doctor_revenue_per_admission']):>18}"
        )


def main() -> None:

    separator()

    print(
        "HOSPITAL 360 — "
        "PHASE 5.5 DOCTOR ANALYTICS VALIDATION"
    )

    separator()

    with engine.connect() as connection:

        existing_views = get_views(
            connection
        )

        failed = []

        print()
        print("DOCTOR ANALYTICS VIEWS")
        small_separator()

        for view_name in EXPECTED_VIEWS:

            if view_name not in existing_views:

                print(
                    f"{view_name:<66}"
                    f"{'MISSING':>14}"
                )

                failed.append(
                    view_name
                )

                continue

            try:

                count = get_count(
                    connection,
                    view_name,
                )

                print(
                    f"{view_name:<66}"
                    f"{count:>14,}"
                    f"   PASS"
                )

            except Exception as exc:

                print(
                    f"{view_name:<66}"
                    f"{'ERROR':>14}"
                )

                print(
                    f"  -> {exc}"
                )

                failed.append(
                    view_name
                )

        if failed:
            raise RuntimeError(
                "Problem doctor views: "
                + ", ".join(failed)
            )

        reconcile_doctors(
            connection
        )

        reconcile_admissions(
            connection
        )

        reconcile_finance(
            connection
        )

        reconcile_claims(
            connection
        )

        check_claim_statuses(
            connection
        )

        print_top_doctors(
            connection
        )

        print_department_summary(
            connection
        )

    print()
    separator()

    print(
        "PHASE 5.5 DOCTOR ANALYTICS "
        "VALIDATION PASSED"
    )

    separator()


if __name__ == "__main__":
    main()