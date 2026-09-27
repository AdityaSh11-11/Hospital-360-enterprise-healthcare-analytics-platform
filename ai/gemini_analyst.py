from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

try:
    from google import genai
    from google.genai import types
except ImportError:  # graceful fallback when optional SDK is not installed
    genai = None
    types = None


DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

APPROVED_OPERATION_NAMES = (
    "executive_overview",
    "revenue_trend",
    "department_activity",
    "department_finance",
    "claims_overview",
    "patient_utilization",
    "operational_trend",
)

OPERATION_QUESTIONS = {
    "executive_overview": "Give me an enterprise performance overview",
    "revenue_trend": "How is monthly revenue trending?",
    "department_activity": "Which department has the largest admission workload?",
    "department_finance": "Which departments have the largest financial exposure?",
    "claims_overview": "What is happening with insurance claims and payers?",
    "patient_utilization": "Which patients show higher utilization?",
    "operational_trend": "What does the daily operations trend look like?",
}

SYSTEM_INSTRUCTION = """
You are the governed intent layer for Hospital 360, a synthetic healthcare
analytics portfolio application.

You are NOT a SQL generator and you have no database access.
You may only request the single approved tool `run_approved_analytics`.
Choose exactly one approved operation only when the user's question can be
answered by that operation. Never invent an operation, table, field, patient
fact, clinical recommendation, diagnosis, treatment recommendation, or
database query.

Approved operation meanings:
- executive_overview: enterprise KPIs and management scorecard.
- revenue_trend: monthly hospital revenue trend.
- department_activity: department admission workload and activity.
- department_finance: department revenue/outstanding financial exposure.
- claims_overview: insurance claims, payer performance and rejection metrics.
- patient_utilization: repeat/frequent admission and patient utilization.
- operational_trend: daily admissions and hospital operating trend.

If the request is outside this catalog, ambiguous, asks for clinical advice,
asks for arbitrary SQL, requests record modification/deletion, requests
secrets, or requests unrestricted data extraction, do not call the tool.
Respond briefly that the request is outside the approved analytics catalog.
""".strip()


@dataclass
class GeminiRoute:
    enabled: bool
    model: str
    operation: str | None = None
    approved_question: str | None = None
    message: str = ""
    raw_text: str = ""
    error: str = ""


def sdk_available() -> bool:
    return genai is not None and types is not None


def api_key_configured() -> bool:
    return bool(
        os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
    )


def gemini_enabled() -> bool:
    return sdk_available() and api_key_configured()


def status() -> dict[str, Any]:
    return {
        "sdk_available": sdk_available(),
        "api_key_configured": api_key_configured(),
        "enabled": gemini_enabled(),
        "model": DEFAULT_MODEL,
    }


def _client():
    if not sdk_available():
        raise RuntimeError(
            "google-genai is not installed. Install project requirements first."
        )

    api_key = (
        os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
    )

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )

    return genai.Client(api_key=api_key)


def _tool_declaration():
    return types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="run_approved_analytics",
                description=(
                    "Select exactly one governed Hospital 360 read-only "
                    "analytics operation. This tool does not accept SQL."
                ),
                parameters={
                    "type": "OBJECT",
                    "properties": {
                        "operation": {
                            "type": "STRING",
                            "enum": list(APPROVED_OPERATION_NAMES),
                            "description": "Approved analytics operation.",
                        }
                    },
                    "required": ["operation"],
                },
            )
        ]
    )


def route_with_gemini(question: str) -> GeminiRoute:
    question = (question or "").strip()

    if not question:
        return GeminiRoute(
            enabled=gemini_enabled(),
            model=DEFAULT_MODEL,
            message="Enter a question first.",
        )

    if not gemini_enabled():
        return GeminiRoute(
            enabled=False,
            model=DEFAULT_MODEL,
            message="Gemini is not configured; deterministic fallback is active.",
        )

    try:
        client = _client()

        response = client.models.generate_content(
            model=DEFAULT_MODEL,
            contents=question,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                tools=[_tool_declaration()],
                automatic_function_calling=types.AutomaticFunctionCallingConfig(
                    disable=True
                ),
                temperature=0,
                max_output_tokens=250,
            ),
        )

        function_calls = getattr(response, "function_calls", None) or []

        if function_calls:
            call = function_calls[0]

            if call.name != "run_approved_analytics":
                return GeminiRoute(
                    enabled=True,
                    model=DEFAULT_MODEL,
                    message="Gemini requested a non-approved tool; request blocked.",
                )

            args = dict(call.args or {})
            operation = args.get("operation")

            if operation not in APPROVED_OPERATION_NAMES:
                return GeminiRoute(
                    enabled=True,
                    model=DEFAULT_MODEL,
                    message="Gemini requested an unknown operation; request blocked.",
                )

            return GeminiRoute(
                enabled=True,
                model=DEFAULT_MODEL,
                operation=operation,
                approved_question=OPERATION_QUESTIONS[operation],
                message="Approved Gemini function call received.",
            )

        raw_text = (getattr(response, "text", "") or "").strip()

        return GeminiRoute(
            enabled=True,
            model=DEFAULT_MODEL,
            message=(
                raw_text
                or "This request is outside the approved analytics catalog."
            ),
            raw_text=raw_text,
        )

    except Exception as exc:
        return GeminiRoute(
            enabled=True,
            model=DEFAULT_MODEL,
            message=(
                "Gemini routing was unavailable. Deterministic fallback can "
                "still handle approved Hospital 360 questions."
            ),
            error=str(exc),
        )


def synthesize_answer(
    user_question: str,
    operation: str,
    deterministic_answer: str,
    note: str = "",
) -> str | None:
    """
    Optional narrative synthesis. Only already-computed governed analytics
    text is sent to Gemini; Gemini never receives SQL credentials or a query
    execution interface.
    """
    if not gemini_enabled():
        return None

    if operation not in APPROVED_OPERATION_NAMES:
        return None

    payload = {
        "user_question": user_question,
        "approved_operation": operation,
        "governed_analytics_answer": deterministic_answer,
        "note": note,
    }

    prompt = (
        "Using only the governed Hospital 360 analytics result below, write "
        "a concise management answer. Do not add facts, clinical advice, "
        "causal claims, forecasts, or numbers that are not present. Preserve "
        "important caveats. The data is synthetic.\n\n"
        + json.dumps(payload, default=str)
    )

    try:
        client = _client()
        response = client.models.generate_content(
            model=DEFAULT_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=500,
            ),
        )
        text = (getattr(response, "text", "") or "").strip()
        return text or None
    except Exception:
        return None
