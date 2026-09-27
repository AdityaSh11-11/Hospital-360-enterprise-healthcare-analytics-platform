from __future__ import annotations

from sqlalchemy import text

from database.connection import engine


EXPECTED_VIEWS = [
    "vw_diagnosis_performance",
    "vw_diagnosis_category_performance",
    "vw_monthly_diagnosis_trend",
    "vw_hospital_monthly_comparison",
    "vw_department_monthly_benchmark",
    "vw_doctor_department_benchmark",
]


EXPECTED_INDEXES = [
    "idx_fact_admission_patient_key",
    "idx_fact_admission_doctor_key",
    "idx_fact_admission_department_key",
    "idx_fact_admission_diagnosis_key",
    "idx_fact_admission_admission_date_key",
    "idx_fact_admission_department_date",
    "idx_fact_admission_doctor_date",
    "idx_fact_admission_diagnosis_date",
    "idx_fact_admission_patient_timestamp",
    "idx_fact_billing_admission_key",
    "idx_fact_billing_patient_key",
    "idx_fact_billing_date_key",
    "idx_fact_claim_billing_key",
    "idx_fact_claim_patient_key",
    "idx_fact_claim_insurer_key",
    "idx_fact_claim_submission_date_key",
    "idx_fact_claim_insurer_submission",
    "idx_fact_lab_patient_key",
    "idx_fact_lab_admission_key",
    "idx_fact_medication_patient_key",
    "idx_fact_medication_admission_key",
]


def separator() -> None:
    print("=" * 104)


def small_separator() -> None:
    print("-" * 104)


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


def get_indexes(connection) -> set[str]:

    return set(
        connection.execute(
            text(
                """
                SELECT indexname

                FROM pg_indexes

                WHERE schemaname = 'warehouse'
                """
            )
        ).scalars().all()
    )


def get_view_count(
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


def reconcile_diagnosis(
    connection,
) -> None:

    source = connection.execute(
        text(
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
        )
    ).mappings().one()

    analytics_row = connection.execute(
        text(
            """
            SELECT
                SUM(admissions) AS admissions,

                ROUND(
                    SUM(net_revenue)::numeric,
                    2
                ) AS net_revenue

            FROM analytics.vw_diagnosis_performance
            """
        )
    ).mappings().one()

    print()
    print("DIAGNOSIS RECONCILIATION")
    small_separator()

    print(
        f"{'Metric':<34}"
        f"{'Source':>24}"
        f"{'Analytics':>24}"
    )

    small_separator()

    print(
        f"{'Admissions':<34}"
        f"{source['admissions']:>24,}"
        f"{analytics_row['admissions']:>24,}"
    )

    print(
        f"{'Net revenue':<34}"
        f"{float(source['net_revenue']):>24,.2f}"
        f"{float(analytics_row['net_revenue']):>24,.2f}"
    )

    if (
        source["admissions"]
        != analytics_row["admissions"]
    ):
        raise RuntimeError(
            "Diagnosis admission reconciliation failed."
        )

    if (
        source["net_revenue"]
        != analytics_row["net_revenue"]
    ):
        raise RuntimeError(
            "Diagnosis revenue reconciliation failed."
        )

    print()
    print(
        "[PASS] Diagnosis reconciliation passed."
    )


def check_hospital_monthly(
    connection,
) -> None:

    source = connection.execute(
        text(
            """
            SELECT
                COUNT(*) AS months,
                SUM(admissions) AS admissions

            FROM analytics.vw_monthly_operations_trend
            """
        )
    ).mappings().one()

    comparison = connection.execute(
        text(
            """
            SELECT
                COUNT(*) AS months,
                SUM(admissions) AS admissions

            FROM analytics.vw_hospital_monthly_comparison
            """
        )
    ).mappings().one()

    print()
    print("MONTHLY TREND RECONCILIATION")
    small_separator()

    print(
        f"{'Operational months':<34}"
        f"{source['months']:>24,}"
        f"{comparison['months']:>24,}"
    )

    print(
        f"{'Admissions':<34}"
        f"{source['admissions']:>24,}"
        f"{comparison['admissions']:>24,}"
    )

    if source["months"] != comparison["months"]:
        raise RuntimeError(
            "Monthly comparison month-count mismatch."
        )

    if (
        source["admissions"]
        != comparison["admissions"]
    ):
        raise RuntimeError(
            "Monthly comparison admission mismatch."
        )

    print()
    print(
        "[PASS] Monthly trend reconciliation passed."
    )


def print_diagnoses(
    connection,
) -> None:

    rows = connection.execute(
        text(
            """
            SELECT
                diagnosis_code,
                diagnosis_name,
                diagnosis_category,
                admissions,
                average_length_of_stay,
                readmission_rate_pct,
                net_revenue,
                admission_volume_rank

            FROM analytics.vw_diagnosis_performance

            ORDER BY
                admission_volume_rank,
                diagnosis_code
            """
        )
    ).mappings().all()

    print()
    print("DIAGNOSIS PERFORMANCE")
    small_separator()

    print(
        f"{'Code':<10}"
        f"{'Diagnosis':<30}"
        f"{'Admissions':>12}"
        f"{'ALOS':>10}"
        f"{'Readmit %':>12}"
        f"{'Net Revenue':>20}"
        f"{'Rank':>8}"
    )

    small_separator()

    for row in rows:

        print(
            f"{row['diagnosis_code']:<10}"
            f"{row['diagnosis_name'][:28]:<30}"
            f"{row['admissions']:>12,}"
            f"{str(row['average_length_of_stay']):>10}"
            f"{str(row['readmission_rate_pct']):>12}"
            f"{float(row['net_revenue']):>20,.2f}"
            f"{row['admission_volume_rank']:>8}"
        )


def print_latest_hospital_trend(
    connection,
) -> None:

    rows = connection.execute(
        text(
            """
            SELECT
                month_start,
                admissions,
                admission_mom_growth_pct,
                net_revenue,
                revenue_mom_growth_pct,
                readmission_rate_pct,
                readmission_rate_change_pp

            FROM analytics.vw_hospital_monthly_comparison

            ORDER BY month_start DESC

            LIMIT 6
            """
        )
    ).mappings().all()

    print()
    print("LATEST HOSPITAL TREND")
    small_separator()

    print(
        f"{'Month':<14}"
        f"{'Admissions':>12}"
        f"{'Adm MoM %':>12}"
        f"{'Net Revenue':>20}"
        f"{'Rev MoM %':>12}"
        f"{'Readmit %':>12}"
        f"{'Change pp':>12}"
    )

    small_separator()

    for row in rows:

        print(
            f"{str(row['month_start']):<14}"
            f"{row['admissions']:>12,}"
            f"{str(row['admission_mom_growth_pct']):>12}"
            f"{float(row['net_revenue']):>20,.2f}"
            f"{str(row['revenue_mom_growth_pct']):>12}"
            f"{str(row['readmission_rate_pct']):>12}"
            f"{str(row['readmission_rate_change_pp']):>12}"
        )


def main() -> None:

    separator()

    print(
        "HOSPITAL 360 — "
        "PHASE 5.4 ADVANCED SQL VALIDATION"
    )

    separator()

    with engine.connect() as connection:

        views = get_views(
            connection
        )

        indexes = get_indexes(
            connection
        )

        failed = []

        print()
        print("ADVANCED ANALYTICS VIEWS")
        small_separator()

        for view_name in EXPECTED_VIEWS:

            if view_name not in views:

                print(
                    f"{view_name:<60}"
                    f"{'MISSING':>14}"
                )

                failed.append(
                    view_name
                )

                continue

            try:

                count = get_view_count(
                    connection,
                    view_name,
                )

                print(
                    f"{view_name:<60}"
                    f"{count:>14,}"
                    f"   PASS"
                )

            except Exception as exc:

                print(
                    f"{view_name:<60}"
                    f"{'ERROR':>14}"
                )

                print(
                    f"  -> {exc}"
                )

                failed.append(
                    view_name
                )

        print()
        print("PERFORMANCE INDEXES")
        small_separator()

        missing_indexes = []

        for index_name in EXPECTED_INDEXES:

            if index_name in indexes:

                print(
                    f"{index_name:<70}"
                    f"{'PASS':>12}"
                )

            else:

                print(
                    f"{index_name:<70}"
                    f"{'MISSING':>12}"
                )

                missing_indexes.append(
                    index_name
                )

        if missing_indexes:

            failed.extend(
                missing_indexes
            )

        if failed:

            raise RuntimeError(
                "Phase 5.4 validation failed: "
                + ", ".join(failed)
            )

        reconcile_diagnosis(
            connection
        )

        check_hospital_monthly(
            connection
        )

        print_diagnoses(
            connection
        )

        print_latest_hospital_trend(
            connection
        )

    print()
    separator()

    print(
        "PHASE 5.4 ADVANCED SQL + "
        "PERFORMANCE VALIDATION PASSED"
    )

    separator()


if __name__ == "__main__":
    main()