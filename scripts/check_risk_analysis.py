from __future__ import annotations

import pandas as pd

from analytics.data_loader import (
    load_table,
    read_sql,
)


def separator() -> None:
    print("=" * 112)


def small_separator() -> None:
    print("-" * 112)


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


def check_view_counts() -> None:
    expectations = {
        "vw_admission_risk": 52697,
        "vw_patient_risk": 21706,
        "vw_risk_band_summary": 3,
        "vw_department_risk": 10,
        "vw_doctor_risk": 150,
        "vw_monthly_risk_trend": 45,
        "vw_risk_factor_prevalence": 7,
    }

    print()
    print("PATIENT RISK ANALYTICS VIEWS")
    small_separator()

    for (
        view_name,
        expected_rows,
    ) in expectations.items():

        dataframe = load_table(
            "analytics",
            view_name,
        )

        actual_rows = len(
            dataframe
        )

        status = (
            "PASS"
            if actual_rows == expected_rows
            else "FAIL"
        )

        print(
            f"{view_name:<52}"
            f"{actual_rows:>14,}"
            f"{status:>14}"
        )

        if actual_rows != expected_rows:
            raise RuntimeError(
                f"{view_name}: expected "
                f"{expected_rows:,} rows, "
                f"found {actual_rows:,}."
            )


def check_admission_reconciliation() -> None:
    source = read_sql(
        """
        SELECT
            COUNT(*) AS admissions,

            COUNT(
                DISTINCT patient_key
            ) AS patients,

            COUNT(*) FILTER (
                WHERE readmission_flag
            ) AS readmissions,

            COUNT(*) FILTER (
                WHERE emergency_flag
            ) AS emergency_admissions,

            COUNT(*) FILTER (
                WHERE icu_flag
            ) AS icu_admissions,

            SUM(
                length_of_stay
            ) AS inpatient_days

        FROM warehouse.fact_admission
        """
    ).iloc[0]

    risk = read_sql(
        """
        SELECT
            COUNT(*) AS admissions,

            COUNT(
                DISTINCT patient_key
            ) AS patients,

            COUNT(*) FILTER (
                WHERE readmission_flag
            ) AS readmissions,

            COUNT(*) FILTER (
                WHERE emergency_flag
            ) AS emergency_admissions,

            COUNT(*) FILTER (
                WHERE icu_flag
            ) AS icu_admissions,

            SUM(
                length_of_stay
            ) AS inpatient_days

        FROM analytics.vw_admission_risk
        """
    ).iloc[0]

    print()
    print("ADMISSION RISK RECONCILIATION")
    small_separator()

    fields = [
        "admissions",
        "patients",
        "readmissions",
        "emergency_admissions",
        "icu_admissions",
        "inpatient_days",
    ]

    for field in fields:
        expected = int(
            source[field]
        )

        actual = int(
            risk[field]
        )

        print(
            f"{field:<36}"
            f"{expected:>24,}"
            f"{actual:>24,}"
        )

        assert_equal(
            field,
            actual,
            expected,
        )

    print()
    print(
        "[PASS] Admission risk population reconciled."
    )


def check_outstanding_reconciliation() -> None:
    source = read_sql(
        """
        SELECT
            ROUND(
                SUM(outstanding_amount)::numeric,
                2
            ) AS outstanding_amount

        FROM warehouse.fact_billing
        """
    ).iloc[0]

    risk = read_sql(
        """
        SELECT
            ROUND(
                SUM(outstanding_amount)::numeric,
                2
            ) AS outstanding_amount

        FROM analytics.vw_admission_risk
        """
    ).iloc[0]

    expected = float(
        source[
            "outstanding_amount"
        ]
    )

    actual = float(
        risk[
            "outstanding_amount"
        ]
    )

    print()
    print("RISK FINANCIAL RECONCILIATION")
    small_separator()

    print(
        f"{'Outstanding amount':<36}"
        f"{expected:>24,.2f}"
        f"{actual:>24,.2f}"
    )

    assert_close(
        "Outstanding amount",
        actual,
        expected,
    )

    print()
    print(
        "[PASS] Risk financial exposure reconciled."
    )


def check_score_rules() -> None:
    dataframe = load_table(
        "analytics",
        "vw_admission_risk",
    )

    expected_score = (
        dataframe[
            "readmission_risk_points"
        ]
        + dataframe[
            "age_risk_points"
        ]
        + dataframe[
            "chronic_condition_risk_points"
        ]
        + dataframe[
            "icu_risk_points"
        ]
        + dataframe[
            "long_stay_risk_points"
        ]
        + dataframe[
            "outstanding_risk_points"
        ]
        + dataframe[
            "emergency_risk_points"
        ]
    )

    mismatches = (
        expected_score
        != dataframe[
            "risk_score"
        ]
    ).sum()

    if mismatches:
        raise RuntimeError(
            f"Risk score mismatch found in "
            f"{mismatches:,} admissions."
        )

    expected_band = pd.Series(
        "Low",
        index=dataframe.index,
    )

    expected_band.loc[
        dataframe[
            "risk_score"
        ].between(
            30,
            59,
        )
    ] = "Medium"

    expected_band.loc[
        dataframe[
            "risk_score"
        ] >= 60
    ] = "High"

    band_mismatches = (
        expected_band
        != dataframe[
            "risk_band"
        ]
    ).sum()

    if band_mismatches:
        raise RuntimeError(
            f"Risk band mismatch found in "
            f"{band_mismatches:,} admissions."
        )

    minimum_score = int(
        dataframe[
            "risk_score"
        ].min()
    )

    maximum_score = int(
        dataframe[
            "risk_score"
        ].max()
    )

    if minimum_score < 0:
        raise RuntimeError(
            "Negative risk score detected."
        )

    if maximum_score > 100:
        raise RuntimeError(
            "Risk score exceeds theoretical "
            "maximum of 100."
        )

    print()
    print("RISK SCORE RULE VALIDATION")
    small_separator()

    print(
        f"Minimum score : {minimum_score}"
    )

    print(
        f"Maximum score : {maximum_score}"
    )

    print(
        "Score mismatches: 0"
    )

    print(
        "Band mismatches : 0"
    )

    print()
    print(
        "[PASS] Risk score and band rules validated."
    )


def check_band_population() -> None:
    summary = load_table(
        "analytics",
        "vw_risk_band_summary",
    )

    total = int(
        summary[
            "admissions"
        ].sum()
    )

    share = float(
        summary[
            "admission_share_pct"
        ].sum()
    )

    print()
    print("RISK BAND POPULATION")
    small_separator()

    print(
        summary.to_string(
            index=False
        )
    )

    assert_equal(
        "Risk band admission population",
        total,
        52697,
    )

    assert_close(
        "Risk band share",
        share,
        100.0,
        tolerance=0.05,
    )

    print()
    print(
        "[PASS] Risk band population validated."
    )


def check_patient_population() -> None:
    source = read_sql(
        """
        SELECT
            COUNT(
                DISTINCT patient_key
            ) AS admitted_patients

        FROM warehouse.fact_admission
        """
    ).iloc[0]

    risk = read_sql(
        """
        SELECT
            COUNT(*) AS patients

        FROM analytics.vw_patient_risk
        """
    ).iloc[0]

    expected = int(
        source[
            "admitted_patients"
        ]
    )

    actual = int(
        risk[
            "patients"
        ]
    )

    print()
    print("PATIENT RISK POPULATION")
    small_separator()

    print(
        f"{'Admitted patients':<36}"
        f"{expected:>24,}"
        f"{actual:>24,}"
    )

    assert_equal(
        "Patient risk population",
        actual,
        expected,
    )

    print()
    print(
        "[PASS] Patient risk population reconciled."
    )


def main() -> None:
    separator()

    print(
        "HOSPITAL 360 â€” "
        "PHASE 8.1 PATIENT RISK VALIDATION"
    )

    separator()

    check_view_counts()

    check_admission_reconciliation()

    check_outstanding_reconciliation()

    check_score_rules()

    check_band_population()

    check_patient_population()

    print()
    separator()

    print(
        "PHASE 8.1 PATIENT RISK "
        "INTELLIGENCE VALIDATION PASSED"
    )

    separator()


if __name__ == "__main__":
    main()
