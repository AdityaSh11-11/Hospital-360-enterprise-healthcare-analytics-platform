from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from analytics.data_loader import read_sql
from ai.gemini_client import DEFAULT_MODEL, enabled, explain_result, make_sql_plan
from ai.schema_catalog import schema_prompt
from ai.sql_guard import validate_and_limit

MAX_CONTEXT_ROWS = 200

@dataclass
class AnalystResponse:
    answer: str
    dataframe: pd.DataFrame
    sql: str = ""
    purpose: str = ""
    model: str = DEFAULT_MODEL
    used_database: bool = False
    blocked: bool = False
    error: str = ""

def _history_text(messages: list[dict] | None) -> str:
    if not messages:
        return ""
    recent = messages[-8:]
    return "\n".join(
        f"{m.get('role', 'user')}: {m.get('content', '')}"
        for m in recent
    )

def ask(question: str, messages: list[dict] | None = None) -> AnalystResponse:
    if not enabled():
        return AnalystResponse(
            answer=(
                "Gemini is not configured. Add GEMINI_API_KEY to .env and "
                "restart Streamlit."
            ),
            dataframe=pd.DataFrame(),
            error="GEMINI_API_KEY missing",
        )

    try:
        plan = make_sql_plan(
            question=question,
            schema_text=schema_prompt(),
            history_text=_history_text(messages),
        )
    except Exception as exc:
        return AnalystResponse(
            answer="I couldn't build an analytical plan for that question.",
            dataframe=pd.DataFrame(),
            error=str(exc),
        )

    if not plan.needs_data:
        return AnalystResponse(
            answer=plan.direct_answer or "How can I help with Hospital 360?",
            dataframe=pd.DataFrame(),
            purpose=plan.purpose,
        )

    guard = validate_and_limit(plan.sql)
    if not guard.safe:
        return AnalystResponse(
            answer=(
                "I understood the question, but the generated database query "
                "was blocked by the read-only safety layer. Rephrase the "
                "question and I’ll try another analytical route."
            ),
            dataframe=pd.DataFrame(),
            sql=plan.sql,
            purpose=plan.purpose,
            blocked=True,
            error=guard.reason,
        )

    try:
        frame = read_sql(guard.sql)
    except Exception as exc:
        return AnalystResponse(
            answer=(
                "The query passed the safety layer but PostgreSQL couldn't "
                "execute it. Try rephrasing the question."
            ),
            dataframe=pd.DataFrame(),
            sql=guard.sql,
            purpose=plan.purpose,
            error=str(exc),
        )

    preview = frame.head(MAX_CONTEXT_ROWS)
    csv_text = preview.to_csv(index=False)
    truncated = len(frame) > MAX_CONTEXT_ROWS

    try:
        answer = explain_result(
            question=question,
            sql=guard.sql,
            purpose=plan.purpose,
            result_csv=csv_text,
            truncated=truncated,
        )
    except Exception:
        answer = (
            f"Query completed successfully and returned {len(frame):,} rows. "
            "The result table is shown below."
        )

    return AnalystResponse(
        answer=answer,
        dataframe=frame,
        sql=guard.sql,
        purpose=plan.purpose,
        used_database=True,
    )
