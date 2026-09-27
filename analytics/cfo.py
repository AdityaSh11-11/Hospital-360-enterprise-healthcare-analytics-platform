from __future__ import annotations

import numpy as np
import pandas as pd

from analytics.data_loader import (
    load_table,
)


def load_cfo_scorecard() -> pd.DataFrame:
    return load_table(
        "analytics",
        "vw_cfo_financial_scorecard",
    )


def load_monthly_cfo() -> pd.DataFrame:
    dataframe = load_table(
        "analytics",
        "vw_monthly_cfo_performance",
    )

    if "month_start" in dataframe.columns:
        dataframe[
            "month_start"
        ] = pd.to_datetime(
            dataframe[
                "month_start"
            ],
            errors="coerce",
        )

    return dataframe


def load_department_cfo() -> pd.DataFrame:
    return load_table(
        "analytics",
        "vw_department_cfo_performance",
    )


def load_payer_mix() -> pd.DataFrame:
    return load_table(
        "analytics",
        "vw_cfo_payer_mix",
    )


def load_payment_method_mix() -> pd.DataFrame:
    return load_table(
        "analytics",
        "vw_cfo_payment_method_mix",
    )


def load_receivable_exposure() -> pd.DataFrame:
    return load_table(
        "analytics",
        "vw_cfo_receivable_exposure",
    )


def load_insurer_exposure() -> pd.DataFrame:
    return load_table(
        "analytics",
        "vw_cfo_insurer_exposure",
    )


def build_cfo_kpi_table() -> pd.DataFrame:
    scorecard = (
        load_cfo_scorecard()
    )

    if len(scorecard) != 1:
        raise RuntimeError(
            "CFO scorecard must contain exactly one row."
        )

    row = scorecard.iloc[0]

    metrics = [
        (
            "Net Revenue",
            row["net_revenue"],
            "currency",
        ),
        (
            "Collected Amount",
            row["collected_amount"],
            "currency",
        ),
        (
            "Outstanding Amount",
            row["outstanding_amount"],
            "currency",
        ),
        (
            "Collection Efficiency",
            row["collection_efficiency_pct"],
            "percent",
        ),
        (
            "Outstanding Rate",
            row["outstanding_rate_pct"],
            "percent",
        ),
        (
            "Discount Rate",
            row["discount_rate_pct"],
            "percent",
        ),
        (
            "Claim Rejection Rate",
            row["claim_rejection_rate_pct"],
            "percent",
        ),
        (
            "Rejected Claim Value",
            row["rejected_amount"],
            "currency",
        ),
        (
            "Rejected Value Rate",
            row["rejected_value_rate_pct"],
            "percent",
        ),
        (
            "Average Bill",
            row["average_bill"],
            "currency",
        ),
    ]

    return pd.DataFrame(
        [
            {
                "kpi": name,
                "value": value,
                "unit": unit,
            }
            for (
                name,
                value,
                unit,
            ) in metrics
        ]
    )


def build_monthly_variance_table() -> pd.DataFrame:
    data = (
        load_monthly_cfo()
        .copy()
    )

    if data.empty:
        return data

    data = (
        data
        .sort_values(
            "month_start"
        )
        .reset_index(
            drop=True
        )
    )

    for metric in [
        "net_revenue",
        "collected_amount",
        "outstanding_amount",
        "collection_efficiency_pct",
    ]:
        if metric not in data.columns:
            continue

        data[
            f"{metric}_previous_month"
        ] = data[
            metric
        ].shift(1)

        data[
            f"{metric}_absolute_variance"
        ] = (
            data[metric]
            - data[
                f"{metric}_previous_month"
            ]
        ).round(2)

        data[
            f"{metric}_variance_pct_python"
        ] = (
            data[metric]
            .pct_change(
                fill_method=None
            )
            .mul(100)
            .replace(
                [np.inf, -np.inf],
                np.nan,
            )
            .round(2)
        )

    return data


def build_cfo_management_insights() -> pd.DataFrame:
    scorecard = (
        load_cfo_scorecard()
    ).iloc[0]

    departments = (
        load_department_cfo()
    )

    insurers = (
        load_insurer_exposure()
    )

    receivables = (
        load_receivable_exposure()
    )

    monthly = (
        load_monthly_cfo()
    )

    insights = []

    insights.append(
        {
            "domain": "Collections",
            "subject": "Hospital",
            "metric":
                "collection_efficiency_pct",
            "value":
                scorecard[
                    "collection_efficiency_pct"
                ],
            "observation":
                (
                    "Collected amount represents "
                    f"{scorecard['collection_efficiency_pct']:.2f}% "
                    "of net revenue."
                ),
        }
    )

    insights.append(
        {
            "domain": "Receivables",
            "subject": "Hospital",
            "metric":
                "outstanding_amount",
            "value":
                scorecard[
                    "outstanding_amount"
                ],
            "observation":
                (
                    "Total recorded outstanding balance is "
                    f"{scorecard['outstanding_amount']:,.2f}."
                ),
        }
    )

    if not departments.empty:
        row = (
            departments
            .sort_values(
                "outstanding_amount",
                ascending=False,
            )
            .iloc[0]
        )

        insights.append(
            {
                "domain": "Department Receivables",
                "subject":
                    row[
                        "department_name"
                    ],
                "metric":
                    "outstanding_amount",
                "value":
                    row[
                        "outstanding_amount"
                    ],
                "observation":
                    (
                        f"{row['department_name']} has the "
                        "largest department outstanding balance "
                        f"at {row['outstanding_amount']:,.2f}, "
                        f"representing "
                        f"{row['outstanding_share_pct']:.2f}% "
                        "of hospital outstanding balances."
                    ),
            }
        )

    if not insurers.empty:
        row = (
            insurers
            .sort_values(
                "rejected_amount",
                ascending=False,
            )
            .iloc[0]
        )

        insights.append(
            {
                "domain": "Claims",
                "subject":
                    row[
                        "insurer_name"
                    ],
                "metric":
                    "rejected_amount",
                "value":
                    row[
                        "rejected_amount"
                    ],
                "observation":
                    (
                        f"{row['insurer_name']} has the largest "
                        "rejected claim value at "
                        f"{row['rejected_amount']:,.2f}, "
                        f"representing "
                        f"{row['rejected_value_share_pct']:.2f}% "
                        "of rejected claim value."
                    ),
            }
        )

    if not receivables.empty:
        positive = (
            receivables[
                receivables[
                    "outstanding_amount"
                ] > 0
            ]
            .sort_values(
                "outstanding_amount",
                ascending=False,
            )
        )

        if not positive.empty:
            row = positive.iloc[0]

            insights.append(
                {
                    "domain":
                        "Receivable Exposure",
                    "subject":
                        row[
                            "exposure_band"
                        ],
                    "metric":
                        "outstanding_amount",
                    "value":
                        row[
                            "outstanding_amount"
                        ],
                    "observation":
                        (
                            f"The {row['exposure_band']} "
                            "exposure band contains the largest "
                            "recorded outstanding value at "
                            f"{row['outstanding_amount']:,.2f}."
                        ),
                }
            )

    if not monthly.empty:
        latest = (
            monthly
            .sort_values(
                "month_start"
            )
            .iloc[-1]
        )

        if pd.notna(
            latest[
                "net_revenue_mom_growth_pct"
            ]
        ):
            insights.append(
                {
                    "domain": "Monthly Finance",
                    "subject":
                        latest[
                            "month_start"
                        ],
                    "metric":
                        "net_revenue_mom_growth_pct",
                    "value":
                        latest[
                            "net_revenue_mom_growth_pct"
                        ],
                    "observation":
                        (
                            "Latest billing-month net revenue "
                            f"changed "
                            f"{latest['net_revenue_mom_growth_pct']:.2f}% "
                            "versus the previous billing month."
                        ),
                }
            )

    return pd.DataFrame(
        insights
    )


def run_cfo_analysis() -> dict[str, pd.DataFrame]:
    return {
        "cfo_kpis":
            build_cfo_kpi_table(),

        "monthly_cfo_variance":
            build_monthly_variance_table(),

        "department_cfo":
            load_department_cfo(),

        "payer_mix":
            load_payer_mix(),

        "payment_method_mix":
            load_payment_method_mix(),

        "receivable_exposure":
            load_receivable_exposure(),

        "insurer_exposure":
            load_insurer_exposure(),

        "cfo_management_insights":
            build_cfo_management_insights(),
    }