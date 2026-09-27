from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv(
    dotenv_path=Path.cwd() / ".env",
    override=False,
)

from ai.analyst import ask
from ai.gemini_client import DEFAULT_MODEL
from utils.app_helpers import (
    bootstrap_page,
    dataframe,
    render_page_footer,
    section_header,
)


bootstrap_page(
    title="AI Analyst Assistant",
    subtitle=(
        "Ask Hospital 360 questions in natural language and receive "
        "governed, read-only answers from the analytical warehouse."
    ),
    icon="🤖",
)


if "ai_messages" not in st.session_state:
    st.session_state.ai_messages = []

if "ai_last_result" not in st.session_state:
    st.session_state.ai_last_result = None

if "ai_question_input" not in st.session_state:
    st.session_state.ai_question_input = ""


st.markdown(
    """
    <style>
    .ai-overview-card {
        background: linear-gradient(135deg, #f7fbff 0%, #edf6ff 100%);
        border: 1px solid #cfe3f8;
        border-radius: 18px;
        padding: 1.35rem 1.45rem;
        margin: 0.4rem 0 1.4rem 0;
        box-shadow: 0 6px 20px rgba(31, 78, 121, 0.06);
    }

    .ai-overview-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #163b65;
        margin-bottom: 0.45rem;
    }

    .ai-overview-text {
        color: #4b6075;
        line-height: 1.65;
        font-size: 0.94rem;
    }

    .ai-flow-card {
        background: #ffffff;
        border: 1px solid #dce8f3;
        border-radius: 16px;
        padding: 1rem 1.05rem;
        min-height: 145px;
        box-shadow: 0 4px 14px rgba(31, 78, 121, 0.05);
    }

    .ai-flow-number {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: #e8f2ff;
        color: #145da0;
        font-weight: 800;
        margin-bottom: 0.7rem;
    }

    .ai-flow-title {
        color: #163b65;
        font-size: 0.95rem;
        font-weight: 700;
        margin-bottom: 0.35rem;
    }

    .ai-flow-text {
        color: #607286;
        font-size: 0.84rem;
        line-height: 1.5;
    }

    .ai-status-card {
        background: #ffffff;
        border: 1px solid #dce8f3;
        border-radius: 14px;
        padding: 1rem 1.1rem;
        min-height: 112px;
        box-shadow: 0 4px 12px rgba(31, 78, 121, 0.04);
    }

    .ai-status-label {
        color: #6b7e91;
        font-size: 0.76rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.35rem;
    }

    .ai-status-value {
        color: #173b63;
        font-size: 1rem;
        font-weight: 750;
        margin-bottom: 0.25rem;
    }

    .ai-status-note {
        color: #718295;
        font-size: 0.79rem;
        line-height: 1.4;
    }

    .ai-question-card {
        background: #f7fbff;
        border: 1px solid #d4e6f7;
        border-left: 5px solid #2f80c9;
        border-radius: 14px;
        padding: 1rem 1.15rem;
        margin: 0.65rem 0;
    }

    .ai-question-label {
        color: #2f6595;
        font-size: 0.76rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.35rem;
    }

    .ai-question-text {
        color: #24384b;
        font-size: 0.94rem;
        line-height: 1.55;
    }

    .ai-answer-card {
        background: #ffffff;
        border: 1px solid #d8e6f1;
        border-left: 5px solid #1769aa;
        border-radius: 14px;
        padding: 1.1rem 1.2rem;
        margin: 0.65rem 0 1rem 0;
        box-shadow: 0 4px 14px rgba(31, 78, 121, 0.04);
    }

    .ai-answer-label {
        color: #1769aa;
        font-size: 0.76rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.45rem;
    }

    .ai-answer-text {
        color: #263b4e;
        font-size: 0.95rem;
        line-height: 1.65;
        white-space: pre-wrap;
    }

    .ai-note-card {
        background: #fffdf7;
        border: 1px solid #eee1b7;
        border-radius: 14px;
        padding: 1rem 1.1rem;
        color: #685b32;
        line-height: 1.55;
        font-size: 0.88rem;
    }

    .ai-safety-card {
        background: #f7fbff;
        border: 1px solid #d5e6f5;
        border-radius: 16px;
        padding: 1.1rem 1.2rem;
        margin-bottom: 0.8rem;
    }

    .ai-safety-title {
        color: #173f68;
        font-weight: 750;
        margin-bottom: 0.4rem;
    }

    .ai-safety-text {
        color: #617487;
        font-size: 0.87rem;
        line-height: 1.55;
    }

    div[data-testid="stTextArea"] textarea {
        border-radius: 12px;
        border: 1px solid #cbdceb;
        background: #ffffff;
        font-size: 0.95rem;
    }

    div[data-testid="stTextArea"] textarea:focus {
        border-color: #3b82c4;
        box-shadow: 0 0 0 1px #3b82c4;
    }

    div[data-testid="stButton"] button {
        border-radius: 10px;
        font-weight: 650;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


section_header(
    "01 · AI Analyst Workspace",
    (
        "A controlled natural-language interface for exploring Hospital 360 "
        "management, operational, financial, claims, physician and risk data."
    ),
)

st.markdown(
    """
    <div class="ai-overview-card">
        <div class="ai-overview-title">
            Ask the hospital data in plain language
        </div>
        <div class="ai-overview-text">
            You do not need to write SQL. Enter a management or analytical
            question, and Hospital 360 will interpret the request, create a
            read-only analytical query, validate it through the SQL safety
            layer, retrieve approved warehouse data and explain the result
            in business-friendly language.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


section_header(
    "02 · How Your Question Is Processed",
    (
        "Every analytical request follows a visible governed path before "
        "a database result is returned."
    ),
)

flow1, flow2, flow3, flow4, flow5 = st.columns(5)

with flow1:
    st.markdown(
        """
        <div class="ai-flow-card">
            <div class="ai-flow-number">1</div>
            <div class="ai-flow-title">Ask</div>
            <div class="ai-flow-text">
                Enter a natural-language Hospital 360 question.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with flow2:
    st.markdown(
        """
        <div class="ai-flow-card">
            <div class="ai-flow-number">2</div>
            <div class="ai-flow-title">Interpret</div>
            <div class="ai-flow-text">
                Gemini identifies the analytical intent and required data.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with flow3:
    st.markdown(
        """
        <div class="ai-flow-card">
            <div class="ai-flow-number">3</div>
            <div class="ai-flow-title">Validate</div>
            <div class="ai-flow-text">
                Generated SQL must pass the Hospital 360 read-only guard.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with flow4:
    st.markdown(
        """
        <div class="ai-flow-card">
            <div class="ai-flow-number">4</div>
            <div class="ai-flow-title">Retrieve</div>
            <div class="ai-flow-text">
                PostgreSQL returns only the approved analytical result.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with flow5:
    st.markdown(
        """
        <div class="ai-flow-card">
            <div class="ai-flow-number">5</div>
            <div class="ai-flow-title">Explain</div>
            <div class="ai-flow-text">
                The result is converted into a clear management answer.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


section_header(
    "03 · AI & Data Connection Status",
    (
        "Confirm that the analytical assistant is ready before submitting "
        "questions."
    ),
)

import os

api_key = os.getenv("GEMINI_API_KEY", "").strip()
api_ready = bool(api_key)
database_mode = "Read-only governed access"
model_name = DEFAULT_MODEL

status1, status2, status3, status4 = st.columns(4)

with status1:
    st.markdown(
        f"""
        <div class="ai-status-card">
            <div class="ai-status-label">Gemini Connection</div>
            <div class="ai-status-value">
                {"Ready" if api_ready else "Not Configured"}
            </div>
            <div class="ai-status-note">
                {"API credentials are available." if api_ready else "Configure GEMINI_API_KEY in the environment."}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with status2:
    st.markdown(
        f"""
        <div class="ai-status-card">
            <div class="ai-status-label">AI Model</div>
            <div class="ai-status-value">{model_name}</div>
            <div class="ai-status-note">
                Model configured for Hospital 360 analytical requests.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with status3:
    st.markdown(
        f"""
        <div class="ai-status-card">
            <div class="ai-status-label">Database Access</div>
            <div class="ai-status-value">Read Only</div>
            <div class="ai-status-note">
                {database_mode}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with status4:
    st.markdown(
        """
        <div class="ai-status-card">
            <div class="ai-status-label">Dataset</div>
            <div class="ai-status-value">Synthetic</div>
            <div class="ai-status-note">
                Portfolio healthcare data only. No real patient PHI.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


section_header(
    "04 · Questions You Can Ask",
    (
        "Use these examples to understand the types of management questions "
        "supported by the analytical assistant."
    ),
)

example1, example2, example3 = st.columns(3)

with example1:
    st.info(
        """
**Operations**

Which department has the highest admissions?

Which department has the longest average length of stay?

How are admissions trending over time?
        """
    )

with example2:
    st.info(
        """
**Finance & Claims**

Which department has the highest outstanding amount?

Which insurer has the highest rejected claim amount?

How is hospital revenue trending?
        """
    )

with example3:
    st.info(
        """
**Risk & Management**

How many admitted patients are high risk?

Which departments have the highest readmission rate?

Which doctors have the highest admission workload?
        """
    )

example4, example5, example6 = st.columns(3)

with example4:
    st.info(
        """
**Patient Analytics**

How many patients are in the warehouse?

Which age group has the most admissions?

Which patients have repeated admissions?
        """
    )

with example5:
    st.info(
        """
**Doctor Analytics**

Which doctor has the highest admissions?

Which specialization has the highest workload?

Which doctors have the highest attributed billing?
        """
    )

with example6:
    st.info(
        """
**Executive Analytics**

Give me a hospital performance overview.

Which department generates the most revenue?

What are the largest outstanding balances?
        """
    )


section_header(
    "05 · Ask Hospital 360 AI",
    (
        "Enter one clear analytical question. The assistant will determine "
        "whether warehouse data is required."
    ),
)

question = st.text_area(
    "Your analytical question",
    value=st.session_state.ai_question_input,
    height=120,
    placeholder=(
        "Example: Which department has the highest outstanding amount?"
    ),
    key="ai_question_box",
)

ask_col, clear_col, space_col = st.columns([1.3, 1.1, 5])

with ask_col:
    submit = st.button(
        "Ask AI Analyst",
        type="primary",
        width="stretch",
        disabled=not api_ready,
    )

with clear_col:
    clear = st.button(
        "Clear Conversation",
        width="stretch",
    )

if clear:
    st.session_state.ai_messages = []
    st.session_state.ai_last_result = None
    st.session_state.ai_question_input = ""
    st.rerun()

if not api_ready:
    st.warning(
        "Gemini is not currently configured. Add GEMINI_API_KEY to the "
        "project environment and restart the Streamlit application."
    )

if submit:
    clean_question = (question or "").strip()

    if not clean_question:
        st.warning("Enter a question before running the AI Analyst.")
    else:
        history_for_model = [
            {
                "role": item["role"],
                "content": item["content"],
            }
            for item in st.session_state.ai_messages[-8:]
            if item.get("role") in {"user", "assistant"}
        ]

        st.session_state.ai_messages.append(
            {
                "role": "user",
                "content": clean_question,
            }
        )

        with st.spinner(
            "Hospital 360 is interpreting the question, validating the "
            "analytical route and retrieving the result..."
        ):
            result = ask(
                clean_question,
                messages=history_for_model,
            )

        st.session_state.ai_last_result = result

        st.session_state.ai_messages.append(
            {
                "role": "assistant",
                "content": result.answer,
            }
        )


result = st.session_state.ai_last_result


section_header(
    "06 · Current Analytical Response",
    (
        "The latest question and answer are separated from the technical "
        "execution details so the result remains easy to understand."
    ),
)

if result is None:
    st.markdown(
        """
        <div class="ai-note-card">
            No question has been submitted yet. Choose one of the example
            questions above or enter your own Hospital 360 analytical
            question.
        </div>
        """,
        unsafe_allow_html=True,
    )

else:
    latest_user_question = ""

    for message in reversed(st.session_state.ai_messages):
        if message.get("role") == "user":
            latest_user_question = message.get("content", "")
            break

    st.markdown(
        f"""
        <div class="ai-question-card">
            <div class="ai-question-label">Your Question</div>
            <div class="ai-question-text">{latest_user_question}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if result.blocked:
        st.error(
            "The requested database query was blocked by the Hospital 360 "
            "SQL safety layer. No unsafe database operation was executed."
        )
    elif result.error and not result.used_database:
        error_lower = result.error.lower()

        if "429" in error_lower or "resource_exhausted" in error_lower:
            st.warning(
                "Gemini has reached its current API quota. Hospital 360 "
                "did not execute an unvalidated database query. Try again "
                "after the Gemini quota becomes available."
            )
        elif "503" in error_lower or "unavailable" in error_lower:
            st.warning(
                "Gemini is temporarily unavailable because of provider "
                "capacity. No unvalidated database query was executed. "
                "Please retry shortly."
            )
        else:
            st.warning(
                "The AI planning step could not be completed. No unsafe "
                "database action was performed."
            )

    st.markdown(
        f"""
        <div class="ai-answer-card">
            <div class="ai-answer-label">Hospital 360 AI Answer</div>
            <div class="ai-answer-text">{result.answer}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    response1, response2, response3, response4 = st.columns(4)

    with response1:
        st.metric(
            "Database Used",
            "Yes" if result.used_database else "No",
        )

    with response2:
        st.metric(
            "SQL Safety",
            "Blocked" if result.blocked else (
                "Approved" if result.sql else "Not Required"
            ),
        )

    with response3:
        st.metric(
            "Rows Returned",
            f"{len(result.dataframe):,}"
            if result.used_database
            else "—",
        )

    with response4:
        st.metric(
            "Model",
            result.model or DEFAULT_MODEL,
        )


section_header(
    "07 · Database Result",
    (
        "When the question requires Hospital 360 data, the exact rows "
        "returned by the approved query are displayed here."
    ),
)

if result is None:
    st.info(
        "Database results will appear here after a data-backed question "
        "is successfully processed."
    )

elif result.used_database:
    if result.dataframe.empty:
        st.info(
            "The approved query completed successfully but returned no rows."
        )
    else:
        dataframe(
            result.dataframe,
            height=min(
                520,
                max(
                    180,
                    38 * (len(result.dataframe) + 1),
                ),
            ),
        )

        st.caption(
            f"Returned rows: {len(result.dataframe):,} · "
            f"Returned columns: {len(result.dataframe.columns):,}"
        )

else:
    st.info(
        "This response did not require a database result, or the analytical "
        "planning stage did not complete."
    )


section_header(
    "08 · Analytical Execution Details",
    (
        "Technical transparency for users who want to understand how the "
        "answer was produced."
    ),
)

if result is None:
    st.info(
        "Execution details will become available after an AI request."
    )

else:
    detail1, detail2 = st.columns([1.3, 2])

    with detail1:
        st.markdown("#### Analytical Purpose")

        if result.purpose:
            st.write(result.purpose)
        else:
            st.caption(
                "No database analytical purpose was required or returned."
            )

        st.markdown("#### Execution Status")

        execution_status = pd.DataFrame(
            [
                {
                    "Stage": "Gemini planning",
                    "Status": (
                        "Completed"
                        if not result.error or result.used_database
                        else "Unavailable"
                    ),
                },
                {
                    "Stage": "SQL safety validation",
                    "Status": (
                        "Blocked"
                        if result.blocked
                        else (
                            "Approved"
                            if result.sql
                            else "Not required"
                        )
                    ),
                },
                {
                    "Stage": "Database retrieval",
                    "Status": (
                        "Completed"
                        if result.used_database
                        else "Not used"
                    ),
                },
                {
                    "Stage": "Management answer",
                    "Status": (
                        "Available"
                        if result.answer
                        else "Unavailable"
                    ),
                },
            ]
        )

        dataframe(
            execution_status,
            height=220,
        )

    with detail2:
        st.markdown("#### Validated SQL")

        if result.sql:
            st.code(
                result.sql,
                language="sql",
            )
        else:
            st.caption(
                "No SQL was executed for this response."
            )

        if result.error:
            with st.expander(
                "Technical error details",
                expanded=False,
            ):
                st.code(
                    result.error,
                    language="text",
                )


section_header(
    "09 · Conversation",
    (
        "Review the questions and answers from the current AI Analyst "
        "session."
    ),
)

if not st.session_state.ai_messages:
    st.info(
        "The conversation is empty. Submit a question to begin."
    )

else:
    for index, message in enumerate(
        st.session_state.ai_messages,
        start=1,
    ):
        role = message.get("role", "")
        content = message.get("content", "")

        if role == "user":
            st.markdown(
                f"""
                <div class="ai-question-card">
                    <div class="ai-question-label">
                        Question {((index + 1) // 2)}
                    </div>
                    <div class="ai-question-text">{content}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div class="ai-answer-card">
                    <div class="ai-answer-label">
                        AI Analyst Response
                    </div>
                    <div class="ai-answer-text">{content}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


section_header(
    "10 · Safety & Governance",
    (
        "Hospital 360 AI is intentionally restricted to governed analytical "
        "use rather than unrestricted database access."
    ),
)

safe1, safe2 = st.columns(2)

with safe1:
    st.markdown(
        """
        <div class="ai-safety-card">
            <div class="ai-safety-title">
                Read-Only SQL Control
            </div>
            <div class="ai-safety-text">
                The AI can only proceed with SELECT or WITH analytical
                queries. Database modification operations such as INSERT,
                UPDATE, DELETE, DROP, ALTER, CREATE and TRUNCATE are blocked.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="ai-safety-card">
            <div class="ai-safety-title">
                Approved Database Scope
            </div>
            <div class="ai-safety-text">
                Analytical access is restricted to Hospital 360 approved
                analytics and warehouse schemas. System catalogs and
                unrestricted database metadata access are blocked.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with safe2:
    st.markdown(
        """
        <div class="ai-safety-card">
            <div class="ai-safety-title">
                Synthetic Healthcare Data
            </div>
            <div class="ai-safety-text">
                Hospital 360 is a portfolio analytics environment built on
                synthetic healthcare records. The assistant is not operating
                on real patient PHI.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="ai-safety-card">
            <div class="ai-safety-title">
                Analytics, Not Clinical Decision Support
            </div>
            <div class="ai-safety-text">
                The AI Analyst supports management and analytical questions.
                It must not be treated as a system for clinical diagnosis,
                treatment decisions or patient-care recommendations.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


section_header(
    "11 · Understanding AI Availability",
    (
        "External AI services can occasionally be rate-limited or "
        "temporarily unavailable."
    ),
)

availability = pd.DataFrame(
    [
        {
            "Situation": "Normal response",
            "Meaning": (
                "Gemini interpreted the question and Hospital 360 completed "
                "the governed analytical flow."
            ),
            "Action": "Review the answer and database result.",
        },
        {
            "Situation": "429 quota limit",
            "Meaning": (
                "The configured Gemini API quota is temporarily exhausted."
            ),
            "Action": "Wait for quota availability and retry.",
        },
        {
            "Situation": "503 unavailable",
            "Meaning": (
                "The Gemini model is temporarily experiencing provider "
                "capacity or availability issues."
            ),
            "Action": "Retry the question shortly.",
        },
        {
            "Situation": "SQL blocked",
            "Meaning": (
                "The generated query did not satisfy Hospital 360's "
                "read-only safety rules."
            ),
            "Action": "Rephrase the analytical question.",
        },
        {
            "Situation": "No database required",
            "Meaning": (
                "The request was conversational or did not require a "
                "Hospital 360 warehouse query."
            ),
            "Action": "No database execution is necessary.",
        },
    ]
)

dataframe(
    availability,
    height=300,
)


section_header(
    "12 · Workspace Responsibility",
    (
        "The AI Analyst is a consumption and exploration workspace. "
        "Administrative generation and distribution remain centralized."
    ),
)

responsibility1, responsibility2, responsibility3 = st.columns(3)

with responsibility1:
    st.success(
        """
**AI Analyst**

Ask questions

Explore hospital data

Review governed answers

Inspect validated SQL
        """
    )

with responsibility2:
    st.info(
        """
**Analytics Pages**

View dashboards

Explore charts

Apply analytical filters

Understand domain performance
        """
    )

with responsibility3:
    st.warning(
        """
**Admin Control Center**

Generate deliverables

Run controlled processes

Download MIS outputs

Download BI assets

Manage platform operations
        """
    )


st.info(
    "Hospital 360 AI Analyst provides governed analytical assistance over "
    "synthetic healthcare data. Answers depend on the available warehouse "
    "data and the configured Gemini service. Generated SQL is validated by "
    "the read-only safety layer before database execution."
)


render_page_footer(
    (
        "AI Analyst Assistant · Hospital 360 Enterprise Intelligence "
        "Platform · Governed natural-language analytics · Synthetic data"
    )
)