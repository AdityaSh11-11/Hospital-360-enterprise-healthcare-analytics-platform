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
        "vw_bill_financial_risk": 52697,
        "vw_financial_risk_band_summary": 3,
        "vw_department_financial_risk": 10,
        "vw_claim_risk": 37658,
        "vw_insurer_claim_risk": 5,
        "vw_monthly_financial_risk": 46,
        "vw_financial_risk_factor_prevalence": 8,
    }

    print()
    print("FINANCIAL & CLAIM RISK VIEWS")
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
            f"{view_name:<54}"
            f"{actual_rows:>14,}"
            f"{status:>14}"
        )

        if actual_rows != expected_rows:
            raise RuntimeError(
                f"{view_name}: expected "
                f"{expected_rows:,} rows, "
                f"found {actual_rows:,}."
            )

    monthly_claim = load_table(
        "analytics",
        "vw_monthly_claim_risk",
    )

    if monthly_claim.empty:
        raise RuntimeError(
            "vw_monthly_claim_risk is empty."
        )

    print(
        f"{'vw_monthly_claim_risk':<54}"
        f"{len(monthly_claim):>14,}"
        f"{'PASS':>14}"
    )


def check_billing_reconciliation() -> None:
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

    risk = read_sql(
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

        FROM analytics.vw_bill_financial_risk
        """
    ).iloc[0]

    print()
    print("BILLING RISK RECONCILIATION")
    small_separator()

    assert_equal(
        "Bills",
        int(risk["bills"]),
        int(source["bills"]),
    )

    for field in [
        "net_revenue",
        "collected_amount",
        "outstanding_amount",
    ]:
        assert_close(
            field,
            float(risk[field]),
            float(source[field]),
        )

    print(
        f"{'Bills':<36}"
        f"{int(source['bills']):>24,}"
        f"{int(risk['bills']):>24,}"
    )

    print(
        f"{'Net revenue':<36}"
        f"{float(source['net_revenue']):>24,.2f}"
        f"{float(risk['net_revenue']):>24,.2f}"
    )

    print(
        f"{'Collected':<36}"
        f"{float(source['collected_amount']):>24,.2f}"
        f"{float(risk['collected_amount']):>24,.2f}"
    )

    print(
        f"{'Outstanding':<36}"
        f"{float(source['outstanding_amount']):>24,.2f}"
        f"{float(risk['outstanding_amount']):>24,.2f}"
    )

    print()
    print(
        "[PASS] Billing risk population reconciled."
    )


def check_claim_reconciliation() -> None:
    source = read_sql(
        """
        SELECT
            COUNT(*) AS claims,

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

    risk = read_sql(
        """
        SELECT
            COUNT(*) AS claims,

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

        FROM analytics.vw_claim_risk
        """
    ).iloc[0]

    print()
    print("CLAIM RISK RECONCILIATION")
    small_separator()

    assert_equal(
        "Claims",
        int(risk["claims"]),
        int(source["claims"]),
    )

    for field in [
        "claim_amount",
        "approved_amount",
        "rejected_amount",
    ]:
        assert_close(
            field,
            float(risk[field]),
            float(source[field]),
        )

    print(
        f"{'Claims':<36}"
        f"{int(source['claims']):>24,}"
        f"{int(risk['claims']):>24,}"
    )

    print(
        f"{'Claim amount':<36}"
        f"{float(source['claim_amount']):>24,.2f}"
        f"{float(risk['claim_amount']):>24,.2f}"
    )

    print(
        f"{'Approved amount':<36}"
        f"{float(source['approved_amount']):>24,.2f}"
        f"{float(risk['approved_amount']):>24,.2f}"
    )

    print(
        f"{'Rejected amount':<36}"
        f"{float(source['rejected_amount']):>24,.2f}"
        f"{float(risk['rejected_amount']):>24,.2f}"
    )

    print()
    print(
        "[PASS] Claim risk population reconciled."
    )


def check_financial_score_rules() -> None:
    dataframe = load_table(
        "analytics",
        "vw_bill_financial_risk",
    )

    expected = (
        dataframe[
            "outstanding_present_points"
        ]
        + dataframe[
            "outstanding_10k_points"
        ]
        + dataframe[
            "outstanding_25k_points"
        ]
        + dataframe[
            "outstanding_50k_points"
        ]
        + dataframe[
            "high_bill_points"
        ]
        + dataframe[
            "payment_status_points"
        ]
        + dataframe[
            "rejected_claim_points"
        ]
        + dataframe[
            "pending_claim_points"
        ]
    )

    mismatches = (
        expected
        != dataframe[
            "financial_risk_score"
        ]
    ).sum()

    if mismatches:
        raise RuntimeError(
            f"Financial score mismatch in "
            f"{mismatches:,} bills."
        )

    expected_band = pd.Series(
        "Low",
        index=dataframe.index,
    )

    expected_band.loc[
        dataframe[
            "financial_risk_score"
        ].between(
            25,
            49,
        )
    ] = "Medium"

    expected_band.loc[
        dataframe[
            "financial_risk_score"
        ] >= 50
    ] = "High"

    band_mismatches = (
        expected_band
        != dataframe[
            "financial_risk_band"
        ]
    ).sum()

    if band_mismatches:
        raise RuntimeError(
            f"Financial risk band mismatch in "
            f"{band_mismatches:,} bills."
        )

    minimum_score = int(
        dataframe[
            "financial_risk_score"
        ].min()
    )

    maximum_score = int(
        dataframe[
            "financial_risk_score"
        ].max()
    )

    if minimum_score < 0:
        raise RuntimeError(
            "Negative financial risk score."
        )

    if maximum_score > 95:
        raise RuntimeError(
            "Financial risk score exceeds 95."
        )

    print()
    print("FINANCIAL SCORE VALIDATION")
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
        "[PASS] Financial risk scoring validated."
    )


def check_claim_score_rules() -> None:
    dataframe = load_table(
        "analytics",
        "vw_claim_risk",
    )

    expected = (
        dataframe[
            "rejected_status_points"
        ]
        + dataframe[
            "pending_status_points"
        ]
        + dataframe[
            "partial_approval_points"
        ]
        + dataframe[
            "rejected_value_points"
        ]
        + dataframe[
            "high_claim_value_points"
        ]
        + dataframe[
            "long_processing_points"
        ]
    )

    mismatches = (
        expected
        != dataframe[
            "claim_risk_score"
        ]
    ).sum()

    if mismatches:
        raise RuntimeError(
            f"Claim score mismatch in "
            f"{mismatches:,} claims."
        )

    expected_band = pd.Series(
        "Low",
        index=dataframe.index,
    )

    expected_band.loc[
        dataframe[
            "claim_risk_score"
        ].between(
            20,
            39,
        )
    ] = "Medium"

    expected_band.loc[
        dataframe[
            "claim_risk_score"
        ] >= 40
    ] = "High"

    band_mismatches = (
        expected_band
        != dataframe[
            "claim_risk_band"
        ]
    ).sum()

    if band_mismatches:
        raise RuntimeError(
            f"Claim risk band mismatch in "
            f"{band_mismatches:,} claims."
        )

    minimum_score = int(
        dataframe[
            "claim_risk_score"
        ].min()
    )

    maximum_score = int(
        dataframe[
            "claim_risk_score"
        ].max()
    )

    if minimum_score < 0:
        raise RuntimeError(
            "Negative claim risk score."
        )

    if maximum_score > 75:
        raise RuntimeError(
            "Claim risk score exceeds 75."
        )

    print()
    print("CLAIM SCORE VALIDATION")
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
        "[PASS] Claim risk scoring validated."
    )


def check_band_reconciliation() -> None:
    summary = load_table(
        "analytics",
        "vw_financial_risk_band_summary",
    )

    total_bills = int(
        summary["bills"].sum()
    )

    total_outstanding = float(
        summary[
            "outstanding_amount"
        ].sum()
    )

    source = read_sql(
        """
        SELECT
            COUNT(*) AS bills,

            ROUND(
                SUM(outstanding_amount)::numeric,
                2
            ) AS outstanding_amount

        FROM warehouse.fact_billing
        """
    ).iloc[0]

    assert_equal(
        "Band bills",
        total_bills,
        int(source["bills"]),
    )

    assert_close(
        "Band outstanding",
        total_outstanding,
        float(
            source[
                "outstanding_amount"
            ]
        ),
    )

    share = float(
        summary[
            "bill_share_pct"
        ].sum()
    )

    assert_close(
        "Bill share",
        share,
        100.0,
        tolerance=0.05,
    )

    print()
    print("FINANCIAL RISK BAND SUMMARY")
    small_separator()

    print(
        summary.to_string(
            index=False
        )
    )

    print()
    print(
        "[PASS] Financial risk bands reconciled."
    )


def main() -> None:
    separator()

    print(
        "HOSPITAL 360 â€” "
        "PHASE 8.2 FINANCIAL & CLAIMS RISK VALIDATION"
    )

    separator()

    check_view_counts()

    check_billing_reconciliation()

    check_claim_reconciliation()

    check_financial_score_rules()

    check_claim_score_rules()

    check_band_reconciliation()

    print()
    separator()

    print(
        "PHASE 8.2 FINANCIAL & CLAIMS "
        "RISK INTELLIGENCE VALIDATION PASSED"
    )

    separator()


if __name__ == "__main__":
    main()
