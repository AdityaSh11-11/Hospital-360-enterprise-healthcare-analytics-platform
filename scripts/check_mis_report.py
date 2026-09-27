from __future__ import annotations

from pathlib import Path

import pandas as pd

from analytics.data_loader import read_sql
from reports.mis_report import (
    DEFAULT_EXPORT_DIRECTORY,
)


EXPECTED_FILES = {
    "executive_scorecard.csv": 13,
    "monthly_mis.csv": 46,
    "department_scorecard.csv": 10,
    "claims_mis.csv": 5,
    "receivables_mis.csv": 5,
    "payer_mix.csv": 2,
    "payment_mix.csv": 4,
    "doctor_mis.csv": 150,
    "executive_commentary.csv": 8,
}


def separator() -> None:
    print("=" * 112)


def small_separator() -> None:
    print("-" * 112)


def load_csv(
    filename: str,
) -> pd.DataFrame:
    path = (
        DEFAULT_EXPORT_DIRECTORY
        / filename
    )

    if not path.exists():
        raise RuntimeError(
            f"Missing MIS export: {path}"
        )

    return pd.read_csv(path)


def check_export_files() -> None:
    print()
    print("MIS EXPORT FILES")
    small_separator()

    for (
        filename,
        expected_rows,
    ) in EXPECTED_FILES.items():

        dataframe = load_csv(
            filename
        )

        actual_rows = len(
            dataframe
        )

        status = (
            "PASS"
            if actual_rows
            == expected_rows
            else "FAIL"
        )

        print(
            f"{filename:<52}"
            f"{actual_rows:>12,}"
            f"{status:>14}"
        )

        if actual_rows != expected_rows:
            raise RuntimeError(
                f"{filename}: expected "
                f"{expected_rows:,} rows, "
                f"found {actual_rows:,}."
            )

    additional_files = [
        "management_exceptions.csv",
        "management_summary.csv",
        "mis_manifest.csv",
    ]

    for filename in additional_files:
        path = (
            DEFAULT_EXPORT_DIRECTORY
            / filename
        )

        if not path.exists():
            raise RuntimeError(
                f"Missing MIS export: {filename}"
            )

        dataframe = pd.read_csv(
            path
        )

        print(
            f"{filename:<52}"
            f"{len(dataframe):>12,}"
            f"{'PASS':>14}"
        )


def reconcile_executive_scorecard() -> None:
    scorecard = load_csv(
        "executive_scorecard.csv"
    )

    kpis = (
        scorecard
        .set_index("kpi")["value"]
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

    print()
    print(
        "EXECUTIVE SCORECARD FINANCE RECONCILIATION"
    )

    small_separator()

    comparisons = [
        (
            "Net Revenue",
            float(
                source[
                    "net_revenue"
                ]
            ),
        ),
        (
            "Collected Amount",
            float(
                source[
                    "collected_amount"
                ]
            ),
        ),
        (
            "Outstanding Amount",
            float(
                source[
                    "outstanding_amount"
                ]
            ),
        ),
    ]

    for (
        metric,
        expected,
    ) in comparisons:
        actual = float(
            kpis.loc[metric]
        )

        print(
            f"{metric:<40}"
            f"{expected:>30,.2f}"
            f"{actual:>30,.2f}"
        )

        if abs(
            actual
            - expected
        ) > 0.05:
            raise RuntimeError(
                f"{metric} reconciliation failed."
            )

    print()
    print(
        "[PASS] Executive finance KPIs reconciled."
    )


def reconcile_department_scorecard() -> None:
    department = load_csv(
        "department_scorecard.csv"
    )

    source = read_sql(
        """
        SELECT
            COUNT(*) AS admissions,

            SUM(
                length_of_stay
            ) AS inpatient_days,

            COUNT(*) FILTER (
                WHERE emergency_flag
            ) AS emergency_admissions,

            COUNT(*) FILTER (
                WHERE icu_flag
            ) AS icu_admissions,

            COUNT(*) FILTER (
                WHERE readmission_flag
            ) AS readmissions

        FROM warehouse.fact_admission
        """
    ).iloc[0]

    print()
    print(
        "DEPARTMENT OPERATIONS RECONCILIATION"
    )

    small_separator()

    comparisons = [
        (
            "Admissions",
            "admissions",
            "admissions",
        ),
        (
            "Inpatient days",
            "total_inpatient_days",
            "inpatient_days",
        ),
        (
            "Emergency admissions",
            "emergency_admissions",
            "emergency_admissions",
        ),
        (
            "ICU admissions",
            "icu_admissions",
            "icu_admissions",
        ),
        (
            "Readmissions",
            "readmissions",
            "readmissions",
        ),
    ]

    for (
        label,
        dataframe_column,
        source_column,
    ) in comparisons:
        actual = int(
            department[
                dataframe_column
            ].sum()
        )

        expected = int(
            source[
                source_column
            ]
        )

        print(
            f"{label:<40}"
            f"{expected:>24,}"
            f"{actual:>24,}"
        )

        if actual != expected:
            raise RuntimeError(
                f"{label} reconciliation failed."
            )

    print()
    print(
        "[PASS] Department operations reconciled."
    )


def reconcile_claims() -> None:
    claims = load_csv(
        "claims_mis.csv"
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

    actual_claims = int(
        claims[
            "total_claims"
        ].sum()
    )

    actual_claim_amount = float(
        claims[
            "claim_amount"
        ].sum()
    )

    actual_rejected_amount = float(
        claims[
            "rejected_amount"
        ].sum()
    )

    print()
    print("CLAIMS MIS RECONCILIATION")
    small_separator()

    print(
        f"{'Claims':<40}"
        f"{int(source['claims']):>24,}"
        f"{actual_claims:>24,}"
    )

    print(
        f"{'Claim amount':<40}"
        f"{float(source['claim_amount']):>24,.2f}"
        f"{actual_claim_amount:>24,.2f}"
    )

    print(
        f"{'Rejected amount':<40}"
        f"{float(source['rejected_amount']):>24,.2f}"
        f"{actual_rejected_amount:>24,.2f}"
    )

    if (
        actual_claims
        != int(source["claims"])
    ):
        raise RuntimeError(
            "Claim count reconciliation failed."
        )

    if abs(
        actual_claim_amount
        - float(
            source[
                "claim_amount"
            ]
        )
    ) > 0.05:
        raise RuntimeError(
            "Claim amount reconciliation failed."
        )

    if abs(
        actual_rejected_amount
        - float(
            source[
                "rejected_amount"
            ]
        )
    ) > 0.05:
        raise RuntimeError(
            "Rejected amount reconciliation failed."
        )

    print()
    print(
        "[PASS] Claims MIS reconciled."
    )


def check_manifest() -> None:
    manifest = load_csv(
        "mis_manifest.csv"
    )

    expected_datasets = {
        "executive_scorecard",
        "monthly_mis",
        "department_scorecard",
        "claims_mis",
        "receivables_mis",
        "payer_mix",
        "payment_mix",
        "doctor_mis",
        "management_exceptions",
        "executive_commentary",
        "management_summary",
    }

    actual_datasets = set(
        manifest[
            "dataset"
        ]
    )

    missing = (
        expected_datasets
        - actual_datasets
    )

    if missing:
        raise RuntimeError(
            "MIS manifest missing datasets: "
            + ", ".join(
                sorted(missing)
            )
        )

    print()
    print("MIS MANIFEST")
    small_separator()

    print(
        f"Datasets recorded : "
        f"{len(actual_datasets):,}"
    )

    print(
        "[PASS] MIS manifest is complete."
    )


def main() -> None:
    separator()

    print(
        "HOSPITAL 360 — "
        "PHASE 7.2 MIS VALIDATION"
    )

    separator()

    if not Path(
        DEFAULT_EXPORT_DIRECTORY
    ).exists():
        raise RuntimeError(
            "MIS export directory does not exist. "
            "Run scripts.run_mis_report first."
        )

    check_export_files()

    reconcile_executive_scorecard()

    reconcile_department_scorecard()

    reconcile_claims()

    check_manifest()

    print()
    separator()

    print(
        "PHASE 7.2 MIS & MANAGEMENT "
        "REPORTING VALIDATION PASSED"
    )

    separator()


if __name__ == "__main__":
    main()