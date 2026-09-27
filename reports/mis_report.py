from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd

from analytics.data_loader import load_table


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_EXPORT_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "exports"
    / "mis"
)


@dataclass(frozen=True)
class MISReportPack:
    report_date: pd.Timestamp
    outputs: dict[str, pd.DataFrame]


def load_single_row_view(
    view_name: str,
) -> pd.Series:
    dataframe = load_table(
        "analytics",
        view_name,
    )

    if len(dataframe) != 1:
        raise RuntimeError(
            f"analytics.{view_name} must contain "
            f"exactly one row. Found {len(dataframe):,}."
        )

    return dataframe.iloc[0]


def build_executive_scorecard() -> pd.DataFrame:
    executive = load_single_row_view(
        "vw_executive_kpis"
    )

    finance = load_single_row_view(
        "vw_cfo_financial_scorecard"
    )

    rows = [
        {
            "domain": "Operations",
            "kpi": "Total Patients",
            "value": executive["total_patients"],
            "unit": "count",
        },
        {
            "domain": "Operations",
            "kpi": "Total Admissions",
            "value": executive["total_admissions"],
            "unit": "count",
        },
        {
            "domain": "Operations",
            "kpi": "Average Length of Stay",
            "value": executive[
                "average_length_of_stay"
            ],
            "unit": "days",
        },
        {
            "domain": "Operations",
            "kpi": "Readmission Rate",
            "value": executive[
                "readmission_rate_pct"
            ],
            "unit": "percent",
        },
        {
            "domain": "Finance",
            "kpi": "Net Revenue",
            "value": finance["net_revenue"],
            "unit": "currency",
        },
        {
            "domain": "Finance",
            "kpi": "Collected Amount",
            "value": finance["collected_amount"],
            "unit": "currency",
        },
        {
            "domain": "Finance",
            "kpi": "Outstanding Amount",
            "value": finance[
                "outstanding_amount"
            ],
            "unit": "currency",
        },
        {
            "domain": "Finance",
            "kpi": "Collection Efficiency",
            "value": finance[
                "collection_efficiency_pct"
            ],
            "unit": "percent",
        },
        {
            "domain": "Finance",
            "kpi": "Outstanding Rate",
            "value": finance[
                "outstanding_rate_pct"
            ],
            "unit": "percent",
        },
        {
            "domain": "Claims",
            "kpi": "Total Claims",
            "value": finance["total_claims"],
            "unit": "count",
        },
        {
            "domain": "Claims",
            "kpi": "Claim Rejection Rate",
            "value": finance[
                "claim_rejection_rate_pct"
            ],
            "unit": "percent",
        },
        {
            "domain": "Claims",
            "kpi": "Rejected Claim Value",
            "value": finance[
                "rejected_amount"
            ],
            "unit": "currency",
        },
        {
            "domain": "Claims",
            "kpi": "Rejected Value Rate",
            "value": finance[
                "rejected_value_rate_pct"
            ],
            "unit": "percent",
        },
    ]

    return pd.DataFrame(rows)


def build_monthly_mis() -> pd.DataFrame:
    finance = load_table(
        "analytics",
        "vw_monthly_cfo_performance",
    ).copy()

    operations = load_table(
        "analytics",
        "vw_monthly_operations_trend",
    ).copy()

    finance["month_start"] = pd.to_datetime(
        finance["month_start"],
        errors="coerce",
    )

    operations["month_start"] = pd.to_datetime(
        operations["month_start"],
        errors="coerce",
    )

    operation_columns = [
        column
        for column in [
            "month_start",
            "admissions",
            "admitted_patients",
            "average_length_of_stay",
            "emergency_admissions",
            "icu_admissions",
            "readmissions",
            "emergency_rate_pct",
            "icu_rate_pct",
            "readmission_rate_pct",
        ]
        if column in operations.columns
    ]

    operations = operations[
        operation_columns
    ]

    result = finance.merge(
        operations,
        on="month_start",
        how="left",
        validate="one_to_one",
    )

    return (
        result
        .sort_values("month_start")
        .reset_index(drop=True)
    )


def build_department_scorecard() -> pd.DataFrame:
    finance = load_table(
        "analytics",
        "vw_department_cfo_performance",
    ).copy()

    operations = load_table(
        "analytics",
        "vw_department_operations",
    ).copy()

    operation_columns = [
        column
        for column in [
            "department_name",
            "admissions",
            "admitted_patients",
            "average_length_of_stay",
            "total_inpatient_days",
            "emergency_admissions",
            "icu_admissions",
            "readmissions",
            "emergency_rate_pct",
            "icu_rate_pct",
            "readmission_rate_pct",
        ]
        if column in operations.columns
    ]

    operations = operations[
        operation_columns
    ]

    result = finance.merge(
        operations,
        on="department_name",
        how="left",
        validate="one_to_one",
    )

    return (
        result
        .sort_values(
            [
                "revenue_rank",
                "department_name",
            ]
        )
        .reset_index(drop=True)
    )


def build_claims_mis() -> pd.DataFrame:
    return (
        load_table(
            "analytics",
            "vw_cfo_insurer_exposure",
        )
        .sort_values(
            [
                "rejected_value_rank",
                "insurer_name",
            ]
        )
        .reset_index(drop=True)
    )


def build_receivables_mis() -> pd.DataFrame:
    return (
        load_table(
            "analytics",
            "vw_cfo_receivable_exposure",
        )
        .sort_values("exposure_order")
        .reset_index(drop=True)
    )


def build_payer_mix_mis() -> pd.DataFrame:
    return (
        load_table(
            "analytics",
            "vw_cfo_payer_mix",
        )
        .sort_values(
            "net_revenue",
            ascending=False,
        )
        .reset_index(drop=True)
    )


def build_payment_mix_mis() -> pd.DataFrame:
    return (
        load_table(
            "analytics",
            "vw_cfo_payment_method_mix",
        )
        .sort_values(
            "collected_amount",
            ascending=False,
        )
        .reset_index(drop=True)
    )


def build_doctor_mis() -> pd.DataFrame:
    dataframe = load_table(
        "analytics",
        "vw_doctor_analytics_summary",
    ).copy()

    if "net_revenue" not in dataframe.columns:
        raise RuntimeError(
            "vw_doctor_analytics_summary is missing "
            "net_revenue."
        )

    return (
        dataframe
        .sort_values(
            "net_revenue",
            ascending=False,
        )
        .reset_index(drop=True)
    )


def build_management_exception_register(
    department_scorecard: pd.DataFrame,
    claims_mis: pd.DataFrame,
    receivables_mis: pd.DataFrame,
) -> pd.DataFrame:
    """
    Deterministic management exceptions.

    These are prioritization signals for management review,
    not clinical judgments or causal conclusions.
    """

    rows: list[dict] = []

    if not department_scorecard.empty:
        hospital_collection = (
            department_scorecard[
                "collected_amount"
            ].sum()
            / department_scorecard[
                "net_revenue"
            ].sum()
            * 100.0
        )

        hospital_outstanding = (
            department_scorecard[
                "outstanding_amount"
            ].sum()
            / department_scorecard[
                "net_revenue"
            ].sum()
            * 100.0
        )

        hospital_readmission = (
            (
                department_scorecard[
                    "readmissions"
                ].sum()
                / department_scorecard[
                    "admissions"
                ].sum()
                * 100.0
            )
            if (
                "readmissions"
                in department_scorecard.columns
                and "admissions"
                in department_scorecard.columns
            )
            else None
        )

        for _, row in (
            department_scorecard.iterrows()
        ):
            collection_rate = float(
                row[
                    "collection_efficiency_pct"
                ]
            )

            outstanding_rate = float(
                row["outstanding_rate_pct"]
            )

            if collection_rate < hospital_collection:
                rows.append(
                    {
                        "domain": "Finance",
                        "entity_type": "Department",
                        "entity_name": row[
                            "department_name"
                        ],
                        "metric":
                            "Collection Efficiency",
                        "metric_value":
                            collection_rate,
                        "benchmark_value":
                            round(
                                hospital_collection,
                                2,
                            ),
                        "variance":
                            round(
                                collection_rate
                                - hospital_collection,
                                2,
                            ),
                        "unit":
                            "percentage points",
                        "review_reason":
                            (
                                "Collection efficiency is "
                                "below the hospital aggregate."
                            ),
                    }
                )

            if outstanding_rate > hospital_outstanding:
                rows.append(
                    {
                        "domain": "Finance",
                        "entity_type": "Department",
                        "entity_name": row[
                            "department_name"
                        ],
                        "metric":
                            "Outstanding Rate",
                        "metric_value":
                            outstanding_rate,
                        "benchmark_value":
                            round(
                                hospital_outstanding,
                                2,
                            ),
                        "variance":
                            round(
                                outstanding_rate
                                - hospital_outstanding,
                                2,
                            ),
                        "unit":
                            "percentage points",
                        "review_reason":
                            (
                                "Outstanding rate is above "
                                "the hospital aggregate."
                            ),
                    }
                )

            if (
                hospital_readmission is not None
                and "readmission_rate_pct"
                in row.index
                and pd.notna(
                    row[
                        "readmission_rate_pct"
                    ]
                )
            ):
                readmission_rate = float(
                    row[
                        "readmission_rate_pct"
                    ]
                )

                if (
                    readmission_rate
                    > hospital_readmission
                ):
                    rows.append(
                        {
                            "domain": "Operations",
                            "entity_type": "Department",
                            "entity_name": row[
                                "department_name"
                            ],
                            "metric":
                                "Readmission Rate",
                            "metric_value":
                                readmission_rate,
                            "benchmark_value":
                                round(
                                    hospital_readmission,
                                    2,
                                ),
                            "variance":
                                round(
                                    readmission_rate
                                    - hospital_readmission,
                                    2,
                                ),
                            "unit":
                                "percentage points",
                            "review_reason":
                                (
                                    "Readmission rate is above "
                                    "the hospital aggregate."
                                ),
                        }
                    )

    if not claims_mis.empty:
        hospital_rejected_value_rate = (
            claims_mis[
                "rejected_amount"
            ].sum()
            / claims_mis[
                "claim_amount"
            ].sum()
            * 100.0
        )

        for _, row in claims_mis.iterrows():
            rate = float(
                row[
                    "rejected_value_rate_pct"
                ]
            )

            if rate > hospital_rejected_value_rate:
                rows.append(
                    {
                        "domain": "Claims",
                        "entity_type": "Insurer",
                        "entity_name": row[
                            "insurer_name"
                        ],
                        "metric":
                            "Rejected Value Rate",
                        "metric_value": rate,
                        "benchmark_value":
                            round(
                                hospital_rejected_value_rate,
                                2,
                            ),
                        "variance":
                            round(
                                rate
                                - hospital_rejected_value_rate,
                                2,
                            ),
                        "unit":
                            "percentage points",
                        "review_reason":
                            (
                                "Rejected claim value rate is "
                                "above the insurer aggregate."
                            ),
                    }
                )

    if not receivables_mis.empty:
        positive_exposure = (
            receivables_mis[
                receivables_mis[
                    "outstanding_amount"
                ] > 0
            ]
            .copy()
        )

        if not positive_exposure.empty:
            largest = (
                positive_exposure
                .sort_values(
                    "outstanding_amount",
                    ascending=False,
                )
                .iloc[0]
            )

            rows.append(
                {
                    "domain": "Receivables",
                    "entity_type":
                        "Exposure Band",
                    "entity_name":
                        largest[
                            "exposure_band"
                        ],
                    "metric":
                        "Outstanding Share",
                    "metric_value":
                        largest[
                            "outstanding_share_pct"
                        ],
                    "benchmark_value":
                        None,
                    "variance":
                        None,
                    "unit": "percent",
                    "review_reason":
                        (
                            "This exposure band contains the "
                            "largest recorded outstanding value."
                        ),
                }
            )

    columns = [
        "domain",
        "entity_type",
        "entity_name",
        "metric",
        "metric_value",
        "benchmark_value",
        "variance",
        "unit",
        "review_reason",
    ]

    result = pd.DataFrame(
        rows,
        columns=columns,
    )

    if result.empty:
        return result

    return (
        result
        .sort_values(
            [
                "domain",
                "entity_type",
                "entity_name",
                "metric",
            ]
        )
        .reset_index(drop=True)
    )


def build_executive_commentary(
    executive_scorecard: pd.DataFrame,
    monthly_mis: pd.DataFrame,
    department_scorecard: pd.DataFrame,
    claims_mis: pd.DataFrame,
    receivables_mis: pd.DataFrame,
) -> pd.DataFrame:
    """
    Deterministic management commentary.

    This deliberately avoids pretending correlation is
    causation. Later Gemini can summarize these trusted
    aggregated outputs.
    """

    rows: list[dict] = []

    kpi = (
        executive_scorecard
        .set_index("kpi")["value"]
        .to_dict()
    )

    rows.append(
        {
            "sequence": 1,
            "domain": "Finance",
            "commentary":
                (
                    "Hospital net revenue is "
                    f"{float(kpi['Net Revenue']):,.2f}; "
                    "recorded collections are "
                    f"{float(kpi['Collected Amount']):,.2f}, "
                    "with collection efficiency of "
                    f"{float(kpi['Collection Efficiency']):.2f}%."
                ),
        }
    )

    rows.append(
        {
            "sequence": 2,
            "domain": "Receivables",
            "commentary":
                (
                    "Recorded outstanding balance is "
                    f"{float(kpi['Outstanding Amount']):,.2f}, "
                    "equal to "
                    f"{float(kpi['Outstanding Rate']):.2f}% "
                    "of net revenue."
                ),
        }
    )

    rows.append(
        {
            "sequence": 3,
            "domain": "Claims",
            "commentary":
                (
                    "Claim rejection rate is "
                    f"{float(kpi['Claim Rejection Rate']):.2f}% "
                    "by claim count, while rejected claim "
                    "value is "
                    f"{float(kpi['Rejected Claim Value']):,.2f}."
                ),
        }
    )

    if not monthly_mis.empty:
        monthly = (
            monthly_mis
            .sort_values("month_start")
            .reset_index(drop=True)
        )

        latest = monthly.iloc[-1]

        if pd.notna(
            latest.get(
                "net_revenue_mom_growth_pct"
            )
        ):
            rows.append(
                {
                    "sequence": 4,
                    "domain":
                        "Monthly Finance",
                    "commentary":
                        (
                            "Latest billing-month net revenue "
                            f"changed "
                            f"{float(latest['net_revenue_mom_growth_pct']):.2f}% "
                            "versus the previous billing month."
                        ),
                }
            )

    if not department_scorecard.empty:
        highest_revenue = (
            department_scorecard
            .sort_values(
                "net_revenue",
                ascending=False,
            )
            .iloc[0]
        )

        highest_outstanding = (
            department_scorecard
            .sort_values(
                "outstanding_amount",
                ascending=False,
            )
            .iloc[0]
        )

        rows.append(
            {
                "sequence": 5,
                "domain": "Department",
                "commentary":
                    (
                        f"{highest_revenue['department_name']} "
                        "has the highest department net revenue "
                        f"at "
                        f"{float(highest_revenue['net_revenue']):,.2f}."
                    ),
            }
        )

        rows.append(
            {
                "sequence": 6,
                "domain":
                    "Department Receivables",
                "commentary":
                    (
                        f"{highest_outstanding['department_name']} "
                        "has the largest department outstanding "
                        f"balance at "
                        f"{float(highest_outstanding['outstanding_amount']):,.2f}."
                    ),
            }
        )

    if not claims_mis.empty:
        highest_rejection = (
            claims_mis
            .sort_values(
                "rejected_amount",
                ascending=False,
            )
            .iloc[0]
        )

        rows.append(
            {
                "sequence": 7,
                "domain": "Insurer",
                "commentary":
                    (
                        f"{highest_rejection['insurer_name']} "
                        "has the largest rejected claim value "
                        f"at "
                        f"{float(highest_rejection['rejected_amount']):,.2f}."
                    ),
            }
        )

    if not receivables_mis.empty:
        positive = receivables_mis[
            receivables_mis[
                "outstanding_amount"
            ] > 0
        ]

        if not positive.empty:
            largest = (
                positive
                .sort_values(
                    "outstanding_amount",
                    ascending=False,
                )
                .iloc[0]
            )

            rows.append(
                {
                    "sequence": 8,
                    "domain":
                        "Receivable Exposure",
                    "commentary":
                        (
                            f"The {largest['exposure_band']} "
                            "band contains "
                            f"{float(largest['outstanding_share_pct']):.2f}% "
                            "of recorded outstanding value."
                        ),
                }
            )

    return (
        pd.DataFrame(rows)
        .sort_values("sequence")
        .reset_index(drop=True)
    )


def determine_report_date(
    monthly_mis: pd.DataFrame,
) -> pd.Timestamp:
    valid_dates = (
        monthly_mis["month_start"]
        .dropna()
    )

    if valid_dates.empty:
        return pd.Timestamp(
            datetime.now().date()
        )

    return pd.Timestamp(
        valid_dates.max()
    )


def build_mis_report_pack() -> MISReportPack:
    executive_scorecard = (
        build_executive_scorecard()
    )

    monthly_mis = (
        build_monthly_mis()
    )

    department_scorecard = (
        build_department_scorecard()
    )

    claims_mis = (
        build_claims_mis()
    )

    receivables_mis = (
        build_receivables_mis()
    )

    payer_mix = (
        build_payer_mix_mis()
    )

    payment_mix = (
        build_payment_mix_mis()
    )

    doctor_mis = (
        build_doctor_mis()
    )

    exception_register = (
        build_management_exception_register(
            department_scorecard=
                department_scorecard,
            claims_mis=
                claims_mis,
            receivables_mis=
                receivables_mis,
        )
    )

    executive_commentary = (
        build_executive_commentary(
            executive_scorecard=
                executive_scorecard,
            monthly_mis=
                monthly_mis,
            department_scorecard=
                department_scorecard,
            claims_mis=
                claims_mis,
            receivables_mis=
                receivables_mis,
        )
    )

    outputs = {
        "executive_scorecard":
            executive_scorecard,

        "monthly_mis":
            monthly_mis,

        "department_scorecard":
            department_scorecard,

        "claims_mis":
            claims_mis,

        "receivables_mis":
            receivables_mis,

        "payer_mix":
            payer_mix,

        "payment_mix":
            payment_mix,

        "doctor_mis":
            doctor_mis,

        "management_exceptions":
            exception_register,

        "executive_commentary":
            executive_commentary,
    }

    report_date = determine_report_date(
        monthly_mis
    )

    return MISReportPack(
        report_date=report_date,
        outputs=outputs,
    )


def export_mis_report_pack(
    report_pack: MISReportPack,
    export_directory: Path | None = None,
) -> Path:
    target = (
        export_directory
        if export_directory is not None
        else DEFAULT_EXPORT_DIRECTORY
    )

    target.mkdir(
        parents=True,
        exist_ok=True,
    )

    for name, dataframe in (
        report_pack.outputs.items()
    ):
        dataframe.to_csv(
            target / f"{name}.csv",
            index=False,
        )

    manifest = pd.DataFrame(
        [
            {
                "report_date":
                    report_pack.report_date.date(),
                "generated_at":
                    datetime.now(),
                "dataset":
                    name,
                "rows":
                    len(dataframe),
                "columns":
                    len(dataframe.columns),
            }
            for name, dataframe
            in report_pack.outputs.items()
        ]
    )

    manifest.to_csv(
        target / "mis_manifest.csv",
        index=False,
    )

    return target