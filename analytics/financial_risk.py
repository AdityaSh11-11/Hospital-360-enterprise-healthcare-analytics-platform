from __future__ import annotations

import pandas as pd

from analytics.data_loader import load_table


RISK_BAND_ORDER = {
    "Low": 1,
    "Medium": 2,
    "High": 3,
}


def load_bill_financial_risk() -> pd.DataFrame:
    return load_table(
        "analytics",
        "vw_bill_financial_risk",
    ).copy()


def load_financial_risk_band_summary() -> pd.DataFrame:
    dataframe = load_table(
        "analytics",
        "vw_financial_risk_band_summary",
    ).copy()

    dataframe["risk_band_order"] = (
        dataframe[
            "financial_risk_band"
        ].map(RISK_BAND_ORDER)
    )

    return (
        dataframe
        .sort_values("risk_band_order")
        .drop(columns=["risk_band_order"])
        .reset_index(drop=True)
    )


def load_department_financial_risk() -> pd.DataFrame:
    return (
        load_table(
            "analytics",
            "vw_department_financial_risk",
        )
        .sort_values(
            [
                "financial_risk_rank",
                "department_name",
            ]
        )
        .reset_index(drop=True)
    )


def load_claim_risk() -> pd.DataFrame:
    return load_table(
        "analytics",
        "vw_claim_risk",
    ).copy()


def load_insurer_claim_risk() -> pd.DataFrame:
    return (
        load_table(
            "analytics",
            "vw_insurer_claim_risk",
        )
        .sort_values(
            [
                "claim_risk_rank",
                "insurer_name",
            ]
        )
        .reset_index(drop=True)
    )


def load_monthly_financial_risk() -> pd.DataFrame:
    dataframe = load_table(
        "analytics",
        "vw_monthly_financial_risk",
    ).copy()

    dataframe["month_start"] = pd.to_datetime(
        dataframe["month_start"],
        errors="coerce",
    )

    return (
        dataframe
        .sort_values("month_start")
        .reset_index(drop=True)
    )


def load_monthly_claim_risk() -> pd.DataFrame:
    dataframe = load_table(
        "analytics",
        "vw_monthly_claim_risk",
    ).copy()

    dataframe["month_start"] = pd.to_datetime(
        dataframe["month_start"],
        errors="coerce",
    )

    return (
        dataframe
        .sort_values("month_start")
        .reset_index(drop=True)
    )


def load_financial_factor_prevalence() -> pd.DataFrame:
    return (
        load_table(
            "analytics",
            "vw_financial_risk_factor_prevalence",
        )
        .sort_values(
            [
                "prevalence_pct",
                "risk_factor",
            ],
            ascending=[
                False,
                True,
            ],
        )
        .reset_index(drop=True)
    )


def build_financial_risk_kpis(
    bills: pd.DataFrame,
    claims: pd.DataFrame,
) -> pd.DataFrame:
    total_bills = len(bills)

    high_risk_bills = int(
        (
            bills[
                "financial_risk_band"
            ]
            == "High"
        ).sum()
    )

    high_risk_claims = int(
        (
            claims[
                "claim_risk_band"
            ]
            == "High"
        ).sum()
    )

    total_claims = len(claims)

    return pd.DataFrame(
        [
            {
                "kpi": "Bills Scored",
                "value": total_bills,
                "unit": "count",
            },
            {
                "kpi": "Average Financial Risk Score",
                "value": round(
                    float(
                        bills[
                            "financial_risk_score"
                        ].mean()
                    ),
                    2,
                ),
                "unit": "score",
            },
            {
                "kpi": "High Risk Bills",
                "value": high_risk_bills,
                "unit": "count",
            },
            {
                "kpi": "High Risk Bill Rate",
                "value": round(
                    (
                        high_risk_bills
                        / total_bills
                        * 100.0
                    )
                    if total_bills
                    else 0.0,
                    2,
                ),
                "unit": "percent",
            },
            {
                "kpi": "Outstanding Exposure",
                "value": round(
                    float(
                        bills[
                            "outstanding_amount"
                        ].sum()
                    ),
                    2,
                ),
                "unit": "currency",
            },
            {
                "kpi": "Claims Scored",
                "value": total_claims,
                "unit": "count",
            },
            {
                "kpi": "Average Claim Risk Score",
                "value": round(
                    float(
                        claims[
                            "claim_risk_score"
                        ].mean()
                    ),
                    2,
                ),
                "unit": "score",
            },
            {
                "kpi": "High Risk Claims",
                "value": high_risk_claims,
                "unit": "count",
            },
            {
                "kpi": "High Risk Claim Rate",
                "value": round(
                    (
                        high_risk_claims
                        / total_claims
                        * 100.0
                    )
                    if total_claims
                    else 0.0,
                    2,
                ),
                "unit": "percent",
            },
            {
                "kpi": "Rejected Claim Value",
                "value": round(
                    float(
                        claims[
                            "rejected_amount"
                        ].sum()
                    ),
                    2,
                ),
                "unit": "currency",
            },
        ]
    )


def build_high_financial_risk_register(
    bills: pd.DataFrame,
) -> pd.DataFrame:
    result = bills[
        bills[
            "financial_risk_band"
        ] == "High"
    ].copy()

    return (
        result
        .sort_values(
            [
                "financial_risk_score",
                "outstanding_amount",
                "net_amount",
            ],
            ascending=[
                False,
                False,
                False,
            ],
        )
        .reset_index(drop=True)
    )


def build_high_claim_risk_register(
    claims: pd.DataFrame,
) -> pd.DataFrame:
    result = claims[
        claims[
            "claim_risk_band"
        ] == "High"
    ].copy()

    return (
        result
        .sort_values(
            [
                "claim_risk_score",
                "rejected_amount",
                "claim_amount",
            ],
            ascending=[
                False,
                False,
                False,
            ],
        )
        .reset_index(drop=True)
    )


def build_financial_risk_insights(
    band_summary: pd.DataFrame,
    department_risk: pd.DataFrame,
    insurer_risk: pd.DataFrame,
    monthly_financial: pd.DataFrame,
    monthly_claim: pd.DataFrame,
    factor_prevalence: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict] = []

    high = band_summary[
        band_summary[
            "financial_risk_band"
        ] == "High"
    ]

    if not high.empty:
        row = high.iloc[0]

        rows.append(
            {
                "sequence": 1,
                "domain": "Financial Exposure",
                "insight":
                    (
                        f"{int(row['bills']):,} bills fall in "
                        "the High analytical financial-risk "
                        "band, representing "
                        f"{float(row['bill_share_pct']):.2f}% "
                        "of bills and "
                        f"{float(row['outstanding_share_pct']):.2f}% "
                        "of recorded outstanding value."
                    ),
            }
        )

    if not department_risk.empty:
        row = (
            department_risk
            .sort_values(
                "outstanding_amount",
                ascending=False,
            )
            .iloc[0]
        )

        rows.append(
            {
                "sequence": 2,
                "domain": "Department Exposure",
                "insight":
                    (
                        f"{row['department_name']} has the "
                        "largest recorded department outstanding "
                        "exposure at "
                        f"{float(row['outstanding_amount']):,.2f}, "
                        "representing "
                        f"{float(row['outstanding_share_pct']):.2f}% "
                        "of hospital outstanding value."
                    ),
            }
        )

    if not insurer_risk.empty:
        row = (
            insurer_risk
            .sort_values(
                "rejected_amount",
                ascending=False,
            )
            .iloc[0]
        )

        rows.append(
            {
                "sequence": 3,
                "domain": "Insurer Exposure",
                "insight":
                    (
                        f"{row['insurer_name']} has the largest "
                        "rejected claim value at "
                        f"{float(row['rejected_amount']):,.2f}, "
                        "with a rejected-value rate of "
                        f"{float(row['rejected_value_rate_pct']):.2f}%."
                    ),
            }
        )

    if not factor_prevalence.empty:
        row = (
            factor_prevalence
            .sort_values(
                "prevalence_pct",
                ascending=False,
            )
            .iloc[0]
        )

        rows.append(
            {
                "sequence": 4,
                "domain": "Financial Risk Factors",
                "insight":
                    (
                        f"{row['risk_factor']} is the most "
                        "frequently triggered modeled financial "
                        "factor, appearing in "
                        f"{float(row['prevalence_pct']):.2f}% "
                        "of bills."
                    ),
            }
        )

    if not monthly_financial.empty:
        latest = (
            monthly_financial
            .sort_values("month_start")
            .iloc[-1]
        )

        rows.append(
            {
                "sequence": 5,
                "domain": "Monthly Financial Risk",
                "insight":
                    (
                        "The latest billing month has a High-risk "
                        "bill rate of "
                        f"{float(latest['high_risk_bill_rate_pct']):.2f}% "
                        "and an outstanding rate of "
                        f"{float(latest['outstanding_rate_pct']):.2f}%."
                    ),
            }
        )

    if not monthly_claim.empty:
        latest = (
            monthly_claim
            .sort_values("month_start")
            .iloc[-1]
        )

        rows.append(
            {
                "sequence": 6,
                "domain": "Monthly Claim Risk",
                "insight":
                    (
                        "The latest claim-submission month has a "
                        "High-risk claim rate of "
                        f"{float(latest['high_risk_claim_rate_pct']):.2f}% "
                        "and rejected-value rate of "
                        f"{float(latest['rejected_value_rate_pct']):.2f}%."
                    ),
            }
        )

    return (
        pd.DataFrame(rows)
        .sort_values("sequence")
        .reset_index(drop=True)
    )


def run_financial_risk_analysis() -> dict[str, pd.DataFrame]:
    bills = load_bill_financial_risk()

    band_summary = (
        load_financial_risk_band_summary()
    )

    department_risk = (
        load_department_financial_risk()
    )

    claims = load_claim_risk()

    insurer_risk = (
        load_insurer_claim_risk()
    )

    monthly_financial = (
        load_monthly_financial_risk()
    )

    monthly_claim = (
        load_monthly_claim_risk()
    )

    factor_prevalence = (
        load_financial_factor_prevalence()
    )

    return {
        "financial_risk_kpis":
            build_financial_risk_kpis(
                bills=bills,
                claims=claims,
            ),

        "financial_risk_band_summary":
            band_summary,

        "department_financial_risk":
            department_risk,

        "insurer_claim_risk":
            insurer_risk,

        "monthly_financial_risk":
            monthly_financial,

        "monthly_claim_risk":
            monthly_claim,

        "financial_risk_factor_prevalence":
            factor_prevalence,

        "high_financial_risk_register":
            build_high_financial_risk_register(
                bills
            ),

        "high_claim_risk_register":
            build_high_claim_risk_register(
                claims
            ),

        "financial_risk_insights":
            build_financial_risk_insights(
                band_summary=band_summary,
                department_risk=department_risk,
                insurer_risk=insurer_risk,
                monthly_financial=
                    monthly_financial,
                monthly_claim=
                    monthly_claim,
                factor_prevalence=
                    factor_prevalence,
            ),
    }