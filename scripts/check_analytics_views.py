from __future__ import annotations

from sqlalchemy import text

from database.connection import engine


# ============================================================
# EXPECTED VIEWS
# ============================================================

EXPECTED_VIEWS = [
    "vw_executive_kpis",
    "vw_monthly_hospital_performance",
    "vw_department_performance",
    "vw_doctor_performance",
    "vw_claim_performance",
    "vw_daily_operations",
    "vw_patient_utilization",
    "vw_monthly_department_performance",
]


# ============================================================
# PRINT HELPERS
# ============================================================

def separator() -> None:

    print(
        "=" * 78
    )


def small_separator() -> None:

    print(
        "-" * 78
    )


# ============================================================
# VIEW DISCOVERY
# ============================================================

def get_analytics_views(
    connection,
) -> list[str]:

    result = connection.execute(
        text(
            """
            SELECT table_name
            FROM information_schema.views
            WHERE table_schema = 'analytics'
            ORDER BY table_name
            """
        )
    )

    return [
        row[0]
        for row in result
    ]


# ============================================================
# ROW COUNT
# ============================================================

def get_view_count(
    connection,
    view_name: str,
) -> int:

    result = connection.execute(
        text(
            f"""
            SELECT COUNT(*)
            FROM analytics.{view_name}
            """
        )
    )

    return int(
        result.scalar_one()
    )


# ============================================================
# EXECUTIVE KPI CHECK
# ============================================================

def check_executive_kpis(
    connection,
) -> None:

    result = connection.execute(
        text(
            """
            SELECT
                total_patients,
                total_admissions,
                admitted_patients,
                average_length_of_stay,
                readmissions,
                readmission_rate_pct,
                net_revenue,
                collected_amount,
                outstanding_amount,
                collection_efficiency_pct,
                total_claims,
                rejected_claims,
                claim_rejection_rate_pct
            FROM analytics.vw_executive_kpis
            """
        )
    ).mappings().one()

    print()
    print(
        "EXECUTIVE KPI SAMPLE"
    )

    small_separator()

    for key, value in result.items():

        print(
            f"{key:<32}: {value}"
        )


# ============================================================
# MONTHLY TREND CHECK
# ============================================================

def check_monthly_trend(
    connection,
) -> None:

    rows = connection.execute(
        text(
            """
            SELECT
                month_start,
                admissions,
                net_revenue,
                collected_amount,
                outstanding_amount,
                revenue_mom_growth_pct
            FROM analytics.vw_monthly_hospital_performance
            ORDER BY month_start DESC
            LIMIT 6
            """
        )
    ).mappings().all()

    print()
    print(
        "LATEST MONTHLY PERFORMANCE"
    )

    small_separator()

    print(
        f"{'Month':<14}"
        f"{'Admissions':>12}"
        f"{'Net Revenue':>18}"
        f"{'Collected':>18}"
        f"{'Outstanding':>18}"
        f"{'MoM %':>12}"
    )

    small_separator()

    for row in rows:

        print(
            f"{str(row['month_start']):<14}"
            f"{row['admissions']:>12,}"
            f"{float(row['net_revenue']):>18,.2f}"
            f"{float(row['collected_amount']):>18,.2f}"
            f"{float(row['outstanding_amount']):>18,.2f}"
            f"{str(row['revenue_mom_growth_pct']):>12}"
        )


# ============================================================
# DEPARTMENT CHECK
# ============================================================

def check_departments(
    connection,
) -> None:

    rows = connection.execute(
        text(
            """
            SELECT
                department_name,
                admissions,
                net_revenue,
                readmission_rate_pct,
                revenue_rank
            FROM analytics.vw_department_performance
            ORDER BY revenue_rank, department_name
            LIMIT 10
            """
        )
    ).mappings().all()

    print()
    print(
        "DEPARTMENT PERFORMANCE"
    )

    small_separator()

    print(
        f"{'Department':<24}"
        f"{'Admissions':>12}"
        f"{'Net Revenue':>18}"
        f"{'Readmit %':>12}"
        f"{'Rank':>8}"
    )

    small_separator()

    for row in rows:

        print(
            f"{row['department_name']:<24}"
            f"{row['admissions']:>12,}"
            f"{float(row['net_revenue']):>18,.2f}"
            f"{str(row['readmission_rate_pct']):>12}"
            f"{row['revenue_rank']:>8}"
        )


# ============================================================
# DOCTOR CHECK
# ============================================================

def check_doctors(
    connection,
) -> None:

    rows = connection.execute(
        text(
            """
            SELECT
                doctor_name,
                department_name,
                admissions,
                net_revenue,
                hospital_revenue_rank
            FROM analytics.vw_doctor_performance
            ORDER BY hospital_revenue_rank, doctor_name
            LIMIT 10
            """
        )
    ).mappings().all()

    print()
    print(
        "TOP DOCTORS BY NET REVENUE"
    )

    small_separator()

    print(
        f"{'Doctor':<28}"
        f"{'Department':<22}"
        f"{'Admissions':>12}"
        f"{'Net Revenue':>18}"
        f"{'Rank':>8}"
    )

    small_separator()

    for row in rows:

        print(
            f"{row['doctor_name']:<28}"
            f"{row['department_name']:<22}"
            f"{row['admissions']:>12,}"
            f"{float(row['net_revenue']):>18,.2f}"
            f"{row['hospital_revenue_rank']:>8}"
        )


# ============================================================
# MAIN VALIDATION
# ============================================================

def main() -> None:

    separator()

    print(
        "HOSPITAL 360 — "
        "ANALYTICS VIEW VALIDATION"
    )

    separator()

    with engine.connect() as connection:

        existing_views = (
            get_analytics_views(
                connection
            )
        )

        print()
        print(
            "ANALYTICS VIEWS"
        )

        small_separator()

        failed = []

        for view_name in EXPECTED_VIEWS:

            exists = (
                view_name
                in existing_views
            )

            if not exists:

                print(
                    f"{view_name:<42}"
                    f"{'MISSING':>12}"
                )

                failed.append(
                    view_name
                )

                continue

            try:

                row_count = (
                    get_view_count(
                        connection,
                        view_name,
                    )
                )

                print(
                    f"{view_name:<42}"
                    f"{row_count:>12,}"
                    f"   PASS"
                )

            except Exception as exc:

                print(
                    f"{view_name:<42}"
                    f"{'ERROR':>12}"
                )

                print(
                    f"  -> {exc}"
                )

                failed.append(
                    view_name
                )

        if failed:

            print()

            separator()

            print(
                "[FAIL] Analytics validation failed."
            )

            print(
                "Problem views: "
                + ", ".join(
                    failed
                )
            )

            separator()

            raise SystemExit(1)

        # ----------------------------------------------------
        # CONTENT CHECKS
        # ----------------------------------------------------

        check_executive_kpis(
            connection
        )

        check_monthly_trend(
            connection
        )

        check_departments(
            connection
        )

        check_doctors(
            connection
        )

    print()

    separator()

    print(
        "PHASE 5.1 ANALYTICS "
        "VALIDATION PASSED"
    )

    separator()


if __name__ == "__main__":

    main()