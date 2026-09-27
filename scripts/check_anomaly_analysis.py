from __future__ import annotations

import numpy as np
import pandas as pd

from analytics.anomalies import (
    IQR_MULTIPLIER,
    ROBUST_Z_THRESHOLD,
    iqr_bounds,
    robust_z_scores,
    run_anomaly_analysis,
)
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
    tolerance: float = 0.0001,
) -> None:
    if abs(
        float(actual)
        - float(expected)
    ) > tolerance:
        raise RuntimeError(
            f"{label} failed: "
            f"{actual} != {expected}"
        )


def check_source_populations() -> None:
    expectations = {
        "vw_monthly_hospital_performance": 46,
        "vw_monthly_operations_trend": 45,
        "vw_monthly_claim_risk": 46,
        "vw_department_performance": 10,
        "vw_bill_financial_risk": 52697,
    }

    print()
    print("ANOMALY SOURCE POPULATIONS")
    small_separator()

    for view_name, expected in expectations.items():
        dataframe = load_table(
            "analytics",
            view_name,
        )

        actual = len(dataframe)

        status = (
            "PASS"
            if actual == expected
            else "FAIL"
        )

        print(
            f"{view_name:<54}"
            f"{actual:>14,}"
            f"{status:>14}"
        )

        assert_equal(
            view_name,
            actual,
            expected,
        )

    admission_count = int(
        read_sql(
            """
            SELECT
                COUNT(*) AS admissions
            FROM warehouse.fact_admission
            """
        ).iloc[0]["admissions"]
    )

    print(
        f"{'warehouse.fact_admission':<54}"
        f"{admission_count:>14,}"
        f"{'PASS' if admission_count == 52697 else 'FAIL':>14}"
    )

    assert_equal(
        "Admission source population",
        admission_count,
        52697,
    )


def check_robust_z_math() -> None:
    series = pd.Series(
        [
            10.0,
            11.0,
            12.0,
            13.0,
            100.0,
        ]
    )

    scores, statistics = robust_z_scores(
        series
    )

    assert_close(
        "Robust median",
        statistics.median,
        12.0,
    )

    assert_close(
        "Robust MAD",
        statistics.mad,
        1.0,
    )

    if not (
        scores.iloc[-1]
        > ROBUST_Z_THRESHOLD
    ):
        raise RuntimeError(
            "Synthetic robust-z test "
            "did not flag extreme value."
        )

    print()
    print("ROBUST Z-SCORE MATH")
    small_separator()

    print(
        f"Median             : "
        f"{statistics.median:.2f}"
    )

    print(
        f"MAD                : "
        f"{statistics.mad:.2f}"
    )

    print(
        f"Extreme robust z   : "
        f"{scores.iloc[-1]:.4f}"
    )

    print(
        f"Threshold          : "
        f"{ROBUST_Z_THRESHOLD:.2f}"
    )

    print()
    print(
        "[PASS] Robust-z calculation validated."
    )


def check_iqr_math() -> None:
    series = pd.Series(
        [
            10.0,
            11.0,
            12.0,
            13.0,
            14.0,
            100.0,
        ]
    )

    (
        q1,
        q3,
        lower,
        upper,
    ) = iqr_bounds(
        series
    )

    if not (
        100.0 > upper
    ):
        raise RuntimeError(
            "Synthetic IQR test did not "
            "flag extreme value."
        )

    print()
    print("IQR MATH")
    small_separator()

    print(
        f"Q1                 : {q1:.4f}"
    )

    print(
        f"Q3                 : {q3:.4f}"
    )

    print(
        f"Lower bound        : {lower:.4f}"
    )

    print(
        f"Upper bound        : {upper:.4f}"
    )

    print(
        f"IQR multiplier     : "
        f"{IQR_MULTIPLIER:.2f}"
    )

    print()
    print(
        "[PASS] IQR calculation validated."
    )


def check_output_structure(
    outputs: dict[str, pd.DataFrame],
) -> None:
    expected = {
        "monthly_hospital_anomalies",
        "monthly_operations_anomalies",
        "monthly_claim_anomalies",
        "department_anomalies",
        "aggregate_anomalies",
        "bill_value_anomalies",
        "los_anomalies",
        "anomaly_summary",
        "anomaly_management_insights",
    }

    missing = (
        expected
        - set(outputs.keys())
    )

    if missing:
        raise RuntimeError(
            "Missing anomaly outputs: "
            + ", ".join(
                sorted(missing)
            )
        )

    print()
    print("ANOMALY OUTPUT STRUCTURE")
    small_separator()

    for name in sorted(expected):
        dataframe = outputs[name]

        print(
            f"{name:<48}"
            f"{len(dataframe):>14,}"
            f"{len(dataframe.columns):>14,}"
        )

    print()
    print(
        "[PASS] Anomaly output structure validated."
    )


def check_aggregate_thresholds(
    aggregate: pd.DataFrame,
) -> None:
    if aggregate.empty:
        print()
        print(
            "[PASS] No aggregate anomalies "
            "to threshold-check."
        )
        return

    invalid = aggregate[
        aggregate[
            "absolute_robust_z_score"
        ] < ROBUST_Z_THRESHOLD
    ]

    if not invalid.empty:
        raise RuntimeError(
            "Aggregate anomaly output contains "
            "observations below the configured "
            "robust-z threshold."
        )

    if aggregate[
        "robust_z_score"
    ].isna().any():
        raise RuntimeError(
            "Null robust-z score found in "
            "aggregate anomaly output."
        )

    print()
    print("AGGREGATE ANOMALY THRESHOLDS")
    small_separator()

    print(
        f"Aggregate anomalies : "
        f"{len(aggregate):,}"
    )

    print(
        f"Minimum |robust z|  : "
        f"{aggregate['absolute_robust_z_score'].min():.4f}"
    )

    print(
        f"Configured threshold: "
        f"{ROBUST_Z_THRESHOLD:.4f}"
    )

    print()
    print(
        "[PASS] Aggregate anomaly thresholds validated."
    )


def check_bill_anomaly_bounds(
    bills: pd.DataFrame,
) -> None:
    if bills.empty:
        print()
        print(
            "[PASS] No bill anomalies "
            "to bound-check."
        )
        return

    invalid = bills[
        ~(
            (
                bills[
                    "observed_value"
                ]
                < bills[
                    "lower_bound"
                ]
            )
            |
            (
                bills[
                    "observed_value"
                ]
                > bills[
                    "upper_bound"
                ]
            )
        )
    ]

    if not invalid.empty:
        raise RuntimeError(
            "Bill anomaly output contains "
            "values inside IQR bounds."
        )

    print()
    print("BILL ANOMALY BOUNDS")
    small_separator()

    print(
        f"Bill anomaly rows   : "
        f"{len(bills):,}"
    )

    print()
    print(
        "[PASS] Bill anomaly bounds validated."
    )


def check_los_anomaly_bounds(
    los: pd.DataFrame,
) -> None:
    if los.empty:
        print()
        print(
            "[PASS] No LOS anomalies "
            "to bound-check."
        )
        return

    invalid = los[
        ~(
            (
                los[
                    "length_of_stay"
                ]
                < los[
                    "lower_bound"
                ]
            )
            |
            (
                los[
                    "length_of_stay"
                ]
                > los[
                    "upper_bound"
                ]
            )
        )
    ]

    if not invalid.empty:
        raise RuntimeError(
            "LOS anomaly output contains "
            "values inside IQR bounds."
        )

    print()
    print("LOS ANOMALY BOUNDS")
    small_separator()

    print(
        f"LOS anomaly rows    : "
        f"{len(los):,}"
    )

    print()
    print(
        "[PASS] LOS anomaly bounds validated."
    )


def check_bill_source_reconciliation() -> None:
    source = read_sql(
        """
        SELECT
            COUNT(*) AS bills,

            ROUND(
                SUM(net_amount)::numeric,
                2
            ) AS net_amount,

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
            COUNT(*) AS bills,

            ROUND(
                SUM(net_amount)::numeric,
                2
            ) AS net_amount,

            ROUND(
                SUM(outstanding_amount)::numeric,
                2
            ) AS outstanding_amount

        FROM analytics.vw_bill_financial_risk
        """
    ).iloc[0]

    assert_equal(
        "Bill source rows",
        int(analytics["bills"]),
        int(source["bills"]),
    )

    assert_close(
        "Bill source net amount",
        float(
            analytics[
                "net_amount"
            ]
        ),
        float(
            source[
                "net_amount"
            ]
        ),
        tolerance=0.05,
    )

    assert_close(
        "Bill source outstanding",
        float(
            analytics[
                "outstanding_amount"
            ]
        ),
        float(
            source[
                "outstanding_amount"
            ]
        ),
        tolerance=0.05,
    )

    print()
    print("BILL SOURCE RECONCILIATION")
    small_separator()

    print(
        f"{'Bills':<34}"
        f"{int(source['bills']):>22,}"
        f"{int(analytics['bills']):>22,}"
    )

    print(
        f"{'Net amount':<34}"
        f"{float(source['net_amount']):>22,.2f}"
        f"{float(analytics['net_amount']):>22,.2f}"
    )

    print(
        f"{'Outstanding':<34}"
        f"{float(source['outstanding_amount']):>22,.2f}"
        f"{float(analytics['outstanding_amount']):>22,.2f}"
    )

    print()
    print(
        "[PASS] Bill anomaly source reconciled."
    )


def check_admission_source_reconciliation() -> None:
    source = read_sql(
        """
        SELECT
            COUNT(*) AS admissions,

            SUM(
                length_of_stay
            ) AS inpatient_days

        FROM warehouse.fact_admission
        """
    ).iloc[0]

    admissions = int(
        source["admissions"]
    )

    inpatient_days = int(
        source["inpatient_days"]
    )

    assert_equal(
        "Admission source rows",
        admissions,
        52697,
    )

    assert_equal(
        "Admission inpatient days",
        inpatient_days,
        249562,
    )

    print()
    print("ADMISSION SOURCE RECONCILIATION")
    small_separator()

    print(
        f"Admissions           : "
        f"{admissions:,}"
    )

    print(
        f"Inpatient days       : "
        f"{inpatient_days:,}"
    )

    print()
    print(
        "[PASS] Admission anomaly source reconciled."
    )


def check_no_infinite_numbers(
    outputs: dict[str, pd.DataFrame],
) -> None:
    for name, dataframe in outputs.items():
        numeric = dataframe.select_dtypes(
            include=["number"]
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

    print()
    print(
        "[PASS] No infinite numeric values "
        "found in anomaly outputs."
    )


def main() -> None:
    separator()

    print(
        "HOSPITAL 360 â€” "
        "PHASE 8.3 ANOMALY VALIDATION"
    )

    separator()

    check_source_populations()

    check_robust_z_math()

    check_iqr_math()

    outputs = run_anomaly_analysis()

    check_output_structure(
        outputs
    )

    check_aggregate_thresholds(
        outputs[
            "aggregate_anomalies"
        ]
    )

    check_bill_anomaly_bounds(
        outputs[
            "bill_value_anomalies"
        ]
    )

    check_los_anomaly_bounds(
        outputs[
            "los_anomalies"
        ]
    )

    check_bill_source_reconciliation()

    check_admission_source_reconciliation()

    check_no_infinite_numbers(
        outputs
    )

    print()
    separator()

    print(
        "PHASE 8.3 STATISTICAL "
        "ANOMALY VALIDATION PASSED"
    )

    separator()


if __name__ == "__main__":
    main()
