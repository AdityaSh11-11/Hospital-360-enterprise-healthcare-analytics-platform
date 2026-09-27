from __future__ import annotations

from sqlalchemy import text

from database.connection import engine


EXPECTED_VIEWS = [
    "vw_operations_summary",
    "vw_admission_type_analysis",
    "vw_room_type_analysis",
    "vw_length_of_stay_bands",
    "vw_outcome_analysis",
    "vw_department_operations",
    "vw_doctor_workload",
    "vw_day_of_week_operations",
    "vw_monthly_operations_trend",
    "vw_patient_demographics",
    "vw_patient_age_analysis",
    "vw_patient_gender_analysis",
    "vw_patient_insurance_analysis",
    "vw_chronic_condition_analysis",
    "vw_patient_geography",
    "vw_patient_utilization_segments",
    "vw_patient_utilization_segment_summary",
    "vw_high_utilization_patients",
    "vw_monthly_patient_admission_cohort",
]


def separator() -> None:
    print("=" * 100)


def small_separator() -> None:
    print("-" * 100)


def get_views(connection) -> set[str]:

    rows = connection.execute(
        text(
            """
            SELECT table_name
            FROM information_schema.views
            WHERE table_schema = 'analytics'
            """
        )
    ).scalars().all()

    return set(rows)


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


def reconcile_operations(connection) -> None:

    source = connection.execute(
        text(
            """
            SELECT
                COUNT(*) AS admissions,
                COUNT(DISTINCT patient_key)
                    AS patients,
                SUM(length_of_stay)
                    AS inpatient_days

            FROM warehouse.fact_admission
            """
        )
    ).mappings().one()

    summary = connection.execute(
        text(
            """
            SELECT
                total_admissions,
                admitted_patients,
                total_inpatient_days

            FROM analytics.vw_operations_summary
            """
        )
    ).mappings().one()

    department = connection.execute(
        text(
            """
            SELECT
                SUM(admissions) AS admissions

            FROM analytics.vw_department_operations
            """
        )
    ).mappings().one()

    print()
    print("OPERATIONS RECONCILIATION")
    small_separator()

    print(
        f"{'Metric':<35}"
        f"{'Source':>20}"
        f"{'Analytics':>20}"
    )

    small_separator()

    print(
        f"{'Admissions':<35}"
        f"{source['admissions']:>20,}"
        f"{summary['total_admissions']:>20,}"
    )

    print(
        f"{'Distinct admitted patients':<35}"
        f"{source['patients']:>20,}"
        f"{summary['admitted_patients']:>20,}"
    )

    print(
        f"{'Inpatient days':<35}"
        f"{source['inpatient_days']:>20,}"
        f"{summary['total_inpatient_days']:>20,}"
    )

    print(
        f"{'Department admissions':<35}"
        f"{source['admissions']:>20,}"
        f"{department['admissions']:>20,}"
    )

    if source["admissions"] != summary["total_admissions"]:
        raise RuntimeError(
            "Operations admission reconciliation failed."
        )

    if source["patients"] != summary["admitted_patients"]:
        raise RuntimeError(
            "Admitted-patient reconciliation failed."
        )

    if (
        source["inpatient_days"]
        != summary["total_inpatient_days"]
    ):
        raise RuntimeError(
            "Inpatient-day reconciliation failed."
        )

    if source["admissions"] != department["admissions"]:
        raise RuntimeError(
            "Department admission reconciliation failed."
        )

    print()
    print(
        "[PASS] Operations reconciliation passed."
    )


def reconcile_patients(connection) -> None:

    source_patients = connection.execute(
        text(
            """
            SELECT COUNT(*)
            FROM warehouse.dim_patient
            """
        )
    ).scalar_one()

    demographic_patients = connection.execute(
        text(
            """
            SELECT COUNT(*)
            FROM analytics.vw_patient_demographics
            """
        )
    ).scalar_one()

    utilization_patients = connection.execute(
        text(
            """
            SELECT COUNT(*)
            FROM analytics.vw_patient_utilization_segments
            """
        )
    ).scalar_one()

    source_admitted = connection.execute(
        text(
            """
            SELECT COUNT(DISTINCT patient_key)
            FROM warehouse.fact_admission
            """
        )
    ).scalar_one()

    cohort_total = connection.execute(
        text(
            """
            SELECT
                COALESCE(
                    SUM(first_time_admitted_patients),
                    0
                )

            FROM analytics.vw_monthly_patient_admission_cohort
            """
        )
    ).scalar_one()

    print()
    print("PATIENT RECONCILIATION")
    small_separator()

    print(
        f"{'Metric':<35}"
        f"{'Source':>20}"
        f"{'Analytics':>20}"
    )

    small_separator()

    print(
        f"{'Patient dimension':<35}"
        f"{source_patients:>20,}"
        f"{demographic_patients:>20,}"
    )

    print(
        f"{'Active utilization population':<35}"
        f"{source_patients:>20,}"
        f"{utilization_patients:>20,}"
    )

    print(
        f"{'Ever-admitted patients':<35}"
        f"{source_admitted:>20,}"
        f"{cohort_total:>20,}"
    )

    if source_patients != demographic_patients:
        raise RuntimeError(
            "Patient demographic reconciliation failed."
        )

    active_source = connection.execute(
        text(
            """
            SELECT COUNT(*)
            FROM warehouse.dim_patient
            WHERE is_active = TRUE
            """
        )
    ).scalar_one()

    if active_source != utilization_patients:
        raise RuntimeError(
            "Active patient utilization reconciliation failed."
        )

    if source_admitted != cohort_total:
        raise RuntimeError(
            "Patient cohort reconciliation failed."
        )

    print()
    print(
        "[PASS] Patient reconciliation passed."
    )


def print_operations_summary(connection) -> None:

    row = connection.execute(
        text(
            """
            SELECT *
            FROM analytics.vw_operations_summary
            """
        )
    ).mappings().one()

    print()
    print("OPERATIONS SUMMARY")
    small_separator()

    for key, value in row.items():
        print(
            f"{key:<36}: {value}"
        )


def print_departments(connection) -> None:

    rows = connection.execute(
        text(
            """
            SELECT
                department_name,
                admissions,
                average_length_of_stay,
                emergency_admissions,
                icu_admissions,
                readmission_rate_pct,
                admission_volume_rank

            FROM analytics.vw_department_operations

            ORDER BY
                admission_volume_rank,
                department_name
            """
        )
    ).mappings().all()

    print()
    print("DEPARTMENT OPERATIONS")
    small_separator()

    print(
        f"{'Department':<24}"
        f"{'Admissions':>12}"
        f"{'ALOS':>10}"
        f"{'Emergency':>12}"
        f"{'ICU':>10}"
        f"{'Readmit %':>12}"
        f"{'Rank':>8}"
    )

    small_separator()

    for row in rows:

        print(
            f"{row['department_name']:<24}"
            f"{row['admissions']:>12,}"
            f"{str(row['average_length_of_stay']):>10}"
            f"{row['emergency_admissions']:>12,}"
            f"{row['icu_admissions']:>10,}"
            f"{str(row['readmission_rate_pct']):>12}"
            f"{row['admission_volume_rank']:>8}"
        )


def print_utilization_segments(connection) -> None:

    rows = connection.execute(
        text(
            """
            SELECT
                utilization_segment,
                patients,
                admissions,
                inpatient_days,
                emergency_admissions,
                readmissions,
                patient_mix_pct

            FROM analytics.vw_patient_utilization_segment_summary

            ORDER BY
                utilization_segment_order
            """
        )
    ).mappings().all()

    print()
    print("PATIENT UTILIZATION SEGMENTS")
    small_separator()

    print(
        f"{'Segment':<24}"
        f"{'Patients':>12}"
        f"{'Admissions':>14}"
        f"{'IP Days':>14}"
        f"{'Emergency':>12}"
        f"{'Readmits':>12}"
        f"{'Mix %':>10}"
    )

    small_separator()

    for row in rows:

        print(
            f"{row['utilization_segment']:<24}"
            f"{row['patients']:>12,}"
            f"{row['admissions']:>14,}"
            f"{row['inpatient_days']:>14,}"
            f"{row['emergency_admissions']:>12,}"
            f"{row['readmissions']:>12,}"
            f"{str(row['patient_mix_pct']):>10}"
        )


def main() -> None:

    separator()

    print(
        "HOSPITAL 360 — "
        "PHASE 5.3 OPERATIONS + PATIENT VALIDATION"
    )

    separator()

    with engine.connect() as connection:

        existing_views = get_views(
            connection
        )

        print()
        print("OPERATIONS + PATIENT VIEWS")
        small_separator()

        failed = []

        for view_name in EXPECTED_VIEWS:

            if view_name not in existing_views:

                print(
                    f"{view_name:<58}"
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
                    f"{view_name:<58}"
                    f"{count:>14,}"
                    f"   PASS"
                )

            except Exception as exc:

                print(
                    f"{view_name:<58}"
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
                "Problem views: "
                + ", ".join(failed)
            )

        reconcile_operations(
            connection
        )

        reconcile_patients(
            connection
        )

        print_operations_summary(
            connection
        )

        print_departments(
            connection
        )

        print_utilization_segments(
            connection
        )

    print()
    separator()

    print(
        "PHASE 5.3 OPERATIONS + PATIENT "
        "VALIDATION PASSED"
    )

    separator()


if __name__ == "__main__":
    main()