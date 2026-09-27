from __future__ import annotations

import pandas as pd


def format_value(
    value,
    unit: str,
) -> str:
    if pd.isna(value):
        return "N/A"

    if unit == "currency":
        return f"{float(value):,.2f}"

    if unit == "percent":
        return f"{float(value):.2f}%"

    if unit == "count":
        return f"{int(float(value)):,}"

    if unit == "days":
        return f"{float(value):.2f} days"

    return str(value)


def scorecard_dictionary(
    scorecard: pd.DataFrame,
) -> dict[str, dict]:
    required = {
        "kpi",
        "value",
        "unit",
    }

    missing = (
        required
        - set(scorecard.columns)
    )

    if missing:
        raise RuntimeError(
            "Executive scorecard missing columns: "
            + ", ".join(
                sorted(missing)
            )
        )

    return {
        row["kpi"]: {
            "value": row["value"],
            "unit": row["unit"],
        }
        for _, row
        in scorecard.iterrows()
    }


def build_management_summary(
    executive_scorecard: pd.DataFrame,
    executive_commentary: pd.DataFrame,
    management_exceptions: pd.DataFrame,
) -> pd.DataFrame:
    kpis = scorecard_dictionary(
        executive_scorecard
    )

    summary_rows = []

    for section, metric_names in {
        "Executive":
            [
                "Total Patients",
                "Total Admissions",
                "Average Length of Stay",
                "Readmission Rate",
            ],

        "Finance":
            [
                "Net Revenue",
                "Collected Amount",
                "Outstanding Amount",
                "Collection Efficiency",
                "Outstanding Rate",
            ],

        "Claims":
            [
                "Total Claims",
                "Claim Rejection Rate",
                "Rejected Claim Value",
                "Rejected Value Rate",
            ],
    }.items():

        for metric_name in metric_names:
            if metric_name not in kpis:
                continue

            item = kpis[
                metric_name
            ]

            summary_rows.append(
                {
                    "section": section,
                    "item_type": "KPI",
                    "subject": metric_name,
                    "detail":
                        format_value(
                            item["value"],
                            item["unit"],
                        ),
                }
            )

    if not executive_commentary.empty:
        for _, row in (
            executive_commentary.iterrows()
        ):
            summary_rows.append(
                {
                    "section":
                        row["domain"],
                    "item_type":
                        "Commentary",
                    "subject":
                        row["domain"],
                    "detail":
                        row["commentary"],
                }
            )

    if not management_exceptions.empty:
        for _, row in (
            management_exceptions.iterrows()
        ):
            summary_rows.append(
                {
                    "section":
                        row["domain"],
                    "item_type":
                        "Management Review",
                    "subject":
                        (
                            f"{row['entity_type']}: "
                            f"{row['entity_name']}"
                        ),
                    "detail":
                        (
                            f"{row['metric']} = "
                            f"{row['metric_value']}; "
                            f"{row['review_reason']}"
                        ),
                }
            )

    return pd.DataFrame(
        summary_rows,
        columns=[
            "section",
            "item_type",
            "subject",
            "detail",
        ],
    )