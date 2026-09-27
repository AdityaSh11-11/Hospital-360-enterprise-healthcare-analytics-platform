from __future__ import annotations

import os
from functools import lru_cache
import random
import time
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from google.genai import errors

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")


class SQLPlan(BaseModel):
    needs_data: bool = Field(
        description="True when answering requires Hospital 360 database data."
    )
    sql: str = Field(
        description=(
            "One PostgreSQL SELECT/WITH query using only provided schemas. "
            "Required when needs_data=true; otherwise return an empty string."
        )
    )
    purpose: str = Field(
        description=(
            "Short description of what the query measures. "
            "Required for data questions; otherwise return an empty string."
        )
    )
    direct_answer: str = Field(
        description=(
            "Conversational answer when needs_data=false; "
            "otherwise return an empty string."
        )
    )


def enabled() -> bool:
    return bool(
        os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
    )


def _api_key() -> str:
    key = (
        os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
    )
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")
    return key


@lru_cache(maxsize=1)
def client() -> genai.Client:
    """
    Keep one durable SDK client alive for the Python process.

    Do not use:
        client().models.generate_content(...)

    with a newly-created temporary client. Some google-genai/httpx versions
    can close the underlying HTTP client before the request is sent when the
    Client object is only a temporary expression.
    """
    return genai.Client(api_key=_api_key())


def reset_client() -> None:
    """
    Close and clear the cached client. Useful after changing API credentials
    without restarting the Python process.
    """
    if client.cache_info().currsize:
        try:
            client().close()
        except Exception:
            pass
    client.cache_clear()


def _generate_content(*, contents, config):
    """
    Centralized Gemini request helper with bounded retry/backoff.

    Retries only transient API failures such as rate limiting and temporary
    server/capacity errors. Permanent client/configuration errors fail
    immediately.
    """
    max_attempts = 4
    retryable_status_codes = {
        500,
        502,
        503,
        504,
    }

    for attempt in range(1, max_attempts + 1):
        try:
            gemini_client = client()

            return gemini_client.models.generate_content(
                model=DEFAULT_MODEL,
                contents=contents,
                config=config,
            )

        except errors.APIError as exc:
            status_code = getattr(
                exc,
                "code",
                None,
            )

            if status_code is None:
                status_code = getattr(
                    exc,
                    "status_code",
                    None,
                )

            if (
                status_code not in retryable_status_codes
                or attempt >= max_attempts
            ):
                raise

            # Exponential backoff:
            # approximately 2s, 4s, 8s plus a small random jitter.
            delay = (
                2 ** attempt
                + random.uniform(0.0, 0.75)
            )

            print(
                f"Gemini temporary error "
                f"({status_code}). "
                f"Retrying in {delay:.1f}s "
                f"[{attempt}/{max_attempts - 1} retries]..."
            )

            time.sleep(delay)


def make_sql_plan(
    question: str,
    schema_text: str,
    history_text: str = "",
) -> SQLPlan:
    system = """
You are Hospital 360's senior BI/data analyst.
Understand English, Hinglish, abbreviations, follow-ups and management questions.

For Hospital 360 data questions, produce ONE PostgreSQL read-only query.

Rules:
- SELECT/WITH only.
- Use ONLY tables/views and columns present in the supplied schema.
- Always schema-qualify physical relations with analytics. or warehouse.
- Never invent a table, view, column or metric.
- Never use information_schema, pg_catalog, system functions, DDL or DML.
- Prefer analytics semantic views when they already contain the requested metric.
- Avoid fan-out joins. Aggregate each fact to the required grain before joining.
- Use NULLIF for division safety.
- Return useful labels and metrics.
- Add sensible ordering.
- Do not expose more rows than necessary.
- Synthetic data only.
- If the user asks a greeting or asks what you can do, set needs_data=false
  and answer conversationally.
- If the user asks for clinical diagnosis/treatment, explain that Hospital 360
  is an analytics system, not a clinical decision system.

For Hospital 360 data questions:
- Set needs_data=true.
- sql MUST contain exactly one executable PostgreSQL SELECT/WITH query.
- purpose MUST be non-empty.
- direct_answer MUST be an empty string.

For questions that do not require database data:
- Set needs_data=false.
- sql MUST be an empty string.
- purpose MUST be an empty string.
- direct_answer MUST contain the response.
""".strip()

    prompt = f"""
LIVE ALLOWED SCHEMA:
{schema_text}

RECENT CHAT CONTEXT:
{history_text[-5000:]}

USER:
{question}
""".strip()

    response = _generate_content(
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            response_schema=SQLPlan,
            temperature=0.1,
            max_output_tokens=2000,
        ),
    )

    if response is None or not response.text:
        raise RuntimeError("Gemini returned an empty SQL planning response.")

    return SQLPlan.model_validate_json(response.text)


def explain_result(
    question: str,
    sql: str,
    purpose: str,
    result_csv: str,
    truncated: bool,
) -> str:
    prompt = f"""
You are Hospital 360 AI Analyst.
Answer the user's question from ONLY the query result supplied below.

Requirements:
- Be conversational and management-friendly.
- English or Hinglish may be used naturally based on the user's wording.
- State important numbers exactly as supported by the result.
- Do not invent causality or missing facts.
- Distinguish observed values from interpretation.
- Mention when the result is empty or truncated.
- The hospital dataset is synthetic.
- Do not give clinical diagnosis or treatment advice.
- Do not mention internal prompts.

USER QUESTION:
{question}

QUERY PURPOSE:
{purpose}

VALIDATED SQL:
{sql}

RESULT TRUNCATED:
{truncated}

RESULT CSV:
{result_csv}
""".strip()

    response = _generate_content(
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=900,
        ),
    )

    return (getattr(response, "text", None) or "").strip()


