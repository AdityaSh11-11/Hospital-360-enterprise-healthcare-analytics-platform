from __future__ import annotations

from sqlalchemy import text

from database.connection import engine


EXPECTED_VIEWS = [
    "vw_finance_summary",
    "vw_monthly_finance",
    "vw_payment_status_analysis",
    "vw_payment_method_analysis",
    "vw_department_finance",
    "vw_monthly_department_finance",
    "vw_claims_summary",
    "vw_monthly_claim_performance",
    "vw_claim_status_analysis",
    "vw_claim_rejection_reasons",
    "vw_insurer_claim_performance",
    "vw_monthly_insurer_claim_performance",
    "vw_claim_processing_bands",
]


def separator() -> None:

    print(
        "=" * 92
    )


def small_separator() -> None:

    print(
        "-" * 92
    )


def get_views(
    connection,
) -> list[str]:

    return list(
        connection.execute(
            text(
                """
                SELECT table_name

                FROM information_schema.views

                WHERE table_schema = 'analytics'

                ORDER BY table_name
                """
            )
        ).scalars()
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


def check_source_reconciliation(
    connection,
) -> None:

    source = connection.execute(
        text(
            """
            SELECT
                COUNT(*) AS total_bills,
                ROUND(
                    SUM(net_amount)::numeric,
                    2
                ) AS net_revenue

            FROM warehouse.fact_billing
            """
        )
    ).mappings().one()

    view = connection.execute(
        text(
            """
            SELECT
                total_bills,
                net_revenue

            FROM analytics.vw_finance_summary
            """
        )
    ).mappings().one()

    claims_source = connection.execute(
        text(
            """
            SELECT
                COUNT(*) AS total_claims

            FROM warehouse.fact_claim
            """
        )
    ).scalar_one()

    claims_view = connection.execute(
        text(
            """
            SELECT total_claims

            FROM analytics.vw_claims_summary
            """
        )
    ).scalar_one()

    print()
    print(
        "SOURCE RECONCILIATION"
    )

    small_separator()

    print(
        f"{'Billing rows':<32}"
        f"{source['total_bills']:>15,}"
        f"{view['total_bills']:>15,}"
    )

    print(
        f"{'Net revenue':<32}"
        f"{float(source['net_revenue']):>15,.2f}"
        f"{float(view['net_revenue']):>15,.2f}"
    )

    print(
        f"{'Claim rows':<32}"
        f"{claims_source:>15,}"
        f"{claims_view:>15,}"
    )

    if (
        source["total_bills"]
        != view["total_bills"]
    ):

        raise RuntimeError(
            "Finance bill-count reconciliation failed."
        )

    if (
        source["net_revenue"]
        != view["net_revenue"]
    ):

        raise RuntimeError(
            "Finance revenue reconciliation failed."
        )

    if (
        claims_source
        != claims_view
    ):

        raise RuntimeError(
            "Claim-count reconciliation failed."
        )

    print()
    print(
        "[PASS] Source reconciliation passed."
    )


def print_finance_summary(
    connection,
) -> None:

    row = connection.execute(
        text(
            """
            SELECT *

            FROM analytics.vw_finance_summary
            """
        )
    ).mappings().one()

    print()
    print(
        "FINANCE SUMMARY"
    )

    small_separator()

    for key, value in row.items():

        print(
            f"{key:<36}: {value}"
        )


def print_claim_summary(
    connection,
) -> None:

    row = connection.execute(
        text(
            """
            SELECT *

            FROM analytics.vw_claims_summary
            """
        )
    ).mappings().one()

    print()
    print(
        "CLAIMS SUMMARY"
    )

    small_separator()

    for key, value in row.items():

        print(
            f"{key:<36}: {value}"
        )


def print_top_rejection_reasons(
    connection,
) -> None:

    rows = connection.execute(
        text(
            """
            SELECT
                rejection_reason,
                rejected_claims,
                rejected_amount,
                rejection_mix_pct

            FROM analytics.vw_claim_rejection_reasons

            ORDER BY
                frequency_rank,
                rejection_reason

            LIMIT 10
            """
        )
    ).mappings().all()

    print()
    print(
        "TOP CLAIM REJECTION REASONS"
    )

    small_separator()

    print(
        f"{'Reason':<36}"
        f"{'Claims':>12}"
        f"{'Rejected Amount':>22}"
        f"{'Mix %':>12}"
    )

    small_separator()

    for row in rows:

        print(
            f"{str(row['rejection_reason']):<36}"
            f"{row['rejected_claims']:>12,}"
            f"{float(row['rejected_amount']):>22,.2f}"
            f"{str(row['rejection_mix_pct']):>12}"
        )


def print_insurers(
    connection,
) -> None:

    rows = connection.execute(
        text(
            """
            SELECT
                insurer_name,
                total_claims,
                claim_amount,
                rejected_amount,
                rejection_rate_pct,
                average_processing_days

            FROM analytics.vw_insurer_claim_performance

            ORDER BY
                claim_value_rank,
                insurer_name
            """
        )
    ).mappings().all()

    print()
    print(
        "INSURER CLAIM PERFORMANCE"
    )

    small_separator()

    print(
        f"{'Insurer':<24}"
        f"{'Claims':>10}"
        f"{'Claim Amount':>18}"
        f"{'Rejected':>18}"
        f"{'Reject %':>12}"
        f"{'Avg Days':>12}"
    )

    small_separator()

    for row in rows:

        print(
            f"{row['insurer_name']:<24}"
            f"{row['total_claims']:>10,}"
            f"{float(row['claim_amount']):>18,.2f}"
            f"{float(row['rejected_amount']):>18,.2f}"
            f"{str(row['rejection_rate_pct']):>12}"
            f"{str(row['average_processing_days']):>12}"
        )


def main() -> None:

    separator()

    print(
        "HOSPITAL 360 — "
        "PHASE 5.2 VALIDATION"
    )

    separator()

    with engine.connect() as connection:

        existing_views = set(
            get_views(
                connection
            )
        )

        print()
        print(
            "FINANCE + CLAIM VIEWS"
        )

        small_separator()

        failed = []

        for view_name in EXPECTED_VIEWS:

            if view_name not in existing_views:

                print(
                    f"{view_name:<48}"
                    f"{'MISSING':>12}"
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
                    f"{view_name:<48}"
                    f"{count:>12,}"
                    f"   PASS"
                )

            except Exception as exc:

                print(
                    f"{view_name:<48}"
                    f"{'ERROR':>12}"
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
                + ", ".join(
                    failed
                )
            )

        check_source_reconciliation(
            connection
        )

        print_finance_summary(
            connection
        )

        print_claim_summary(
            connection
        )

        print_top_rejection_reasons(
            connection
        )

        print_insurers(
            connection
        )

    print()

    separator()

    print(
        "PHASE 5.2 FINANCE + CLAIMS "
        "VALIDATION PASSED"
    )

    separator()


if __name__ == "__main__":

    main()