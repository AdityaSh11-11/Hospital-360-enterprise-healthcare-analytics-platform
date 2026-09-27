from __future__ import annotations

import html
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Literal, Sequence

import pandas as pd
import streamlit as st

from analytics.data_loader import read_sql


# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

APP_NAME = os.getenv("APP_NAME", "Hospital 360")
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
APP_ENV = os.getenv("APP_ENV", "development")

PROJECT_ROOT = Path(__file__).resolve().parents[1]

EXPORT_ROOT = PROJECT_ROOT / "data" / "exports"
REPORTS_ROOT = PROJECT_ROOT / "reports"
INCREMENTAL_ROOT = PROJECT_ROOT / "data" / "incremental"


# ============================================================
# DESIGN TOKENS
# ============================================================

BRAND_NAVY = "#071A2F"
BRAND_NAVY_2 = "#0B2745"
BRAND_BLUE = "#2563EB"
BRAND_BLUE_DARK = "#1D4ED8"
BRAND_CYAN = "#06B6D4"

SUCCESS = "#059669"
WARNING = "#D97706"
DANGER = "#DC2626"

TEXT_PRIMARY = "#0F172A"
TEXT_SECONDARY = "#475569"
TEXT_MUTED = "#64748B"

SURFACE = "#FFFFFF"
SURFACE_SOFT = "#F8FAFC"
APP_BACKGROUND = "#F3F7FC"
BORDER = "#DCE6F0"


# ============================================================
# GENERIC HELPERS
# ============================================================

def _escape(value: Any) -> str:
    if value is None:
        return ""
    return html.escape(str(value))


def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        if value is None:
            return default

        if pd.isna(value):
            return default

        return float(value)

    except (TypeError, ValueError):
        return default


def _safe_int(
    value: Any,
    default: int = 0,
) -> int:
    try:
        return int(
            round(
                _safe_float(
                    value,
                    default,
                )
            )
        )

    except (TypeError, ValueError):
        return default


def _normalize_metric_items(
    items: Sequence[Any],
) -> list[dict[str, Any]]:

    normalized: list[dict[str, Any]] = []

    for item in items:

        if isinstance(item, dict):

            normalized.append(
                {
                    "label": item.get(
                        "label",
                        item.get(
                            "title",
                            "Metric",
                        ),
                    ),
                    "value": item.get(
                        "value",
                        "—",
                    ),
                    "delta": item.get(
                        "delta"
                    ),
                    "help": item.get(
                        "help"
                    ),
                }
            )

            continue

        if isinstance(
            item,
            (list, tuple),
        ):

            if len(item) >= 2:

                normalized.append(
                    {
                        "label": item[0],
                        "value": item[1],
                        "delta": (
                            item[2]
                            if len(item) >= 3
                            else None
                        ),
                        "help": (
                            item[3]
                            if len(item) >= 4
                            else None
                        ),
                    }
                )

    return normalized


def _page_exists(
    relative_path: str,
) -> bool:

    try:
        return (
            PROJECT_ROOT
            / relative_path
        ).exists()

    except OSError:
        return False


# ============================================================
# STREAMLIT PAGE CONFIG
# ============================================================

def configure_page(
    title: str = APP_NAME,
    icon: str = "🏥",
    layout: Literal[
        "centered",
        "wide",
    ] = "wide",
):

    page_title = (
        APP_NAME
        if title == APP_NAME
        else f"{title} | {APP_NAME}"
    )

    st.set_page_config(
        page_title=page_title,
        page_icon=icon,
        layout=layout,
        initial_sidebar_state="expanded",
    )


# ============================================================
# ENTERPRISE DESIGN SYSTEM
# ============================================================

def inject_app_css():

    st.markdown(
        """
<style>

/* ==========================================================
   HOSPITAL 360
   ENTERPRISE HEALTHCARE INTELLIGENCE DESIGN SYSTEM
   ========================================================== */

:root {

    --h360-navy-950: #061525;
    --h360-navy-900: #071a2f;
    --h360-navy-850: #0a2038;
    --h360-navy-800: #0b2745;

    --h360-blue-700: #1d4ed8;
    --h360-blue-600: #2563eb;
    --h360-blue-500: #3b82f6;
    --h360-blue-100: #dbeafe;
    --h360-blue-50: #eff6ff;

    --h360-cyan-500: #06b6d4;

    --h360-success: #059669;
    --h360-warning: #d97706;
    --h360-danger: #dc2626;

    --h360-text: #0f172a;
    --h360-text-secondary: #475569;
    --h360-muted: #64748b;

    --h360-background: #f3f7fc;
    --h360-surface: #ffffff;
    --h360-surface-soft: #f8fafc;

    --h360-border: #dce6f0;
    --h360-border-strong: #cbd9e8;

    --h360-shadow-xs:
        0 1px 2px rgba(15, 23, 42, 0.03);

    --h360-shadow-sm:
        0 3px 10px rgba(15, 42, 70, 0.05);

    --h360-shadow-md:
        0 8px 24px rgba(15, 42, 70, 0.07);

    --h360-shadow-lg:
        0 18px 50px rgba(15, 42, 70, 0.10);

}


/* ==========================================================
   GLOBAL
   ========================================================== */

html,
body,
[class*="css"] {

    font-family:
        Inter,
        "Segoe UI",
        Roboto,
        Helvetica,
        Arial,
        sans-serif;

    color: var(--h360-text);

}


.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {

    background:
        linear-gradient(
            180deg,
            #f8fbff 0px,
            var(--h360-background) 330px
        ) !important;

    color: var(--h360-text) !important;

}


[data-testid="stMainBlockContainer"] {

    max-width: 1600px;

    padding-top: 1.4rem;
    padding-left: 2.35rem;
    padding-right: 2.35rem;
    padding-bottom: 5rem;

}


.block-container {

    max-width: 1600px;

}


/* ==========================================================
   STREAMLIT TOP BAR
   ========================================================== */

header[data-testid="stHeader"] {

    background:
        rgba(
            248,
            251,
            255,
            0.92
        ) !important;

    border-bottom:
        1px solid
        rgba(
            203,
            217,
            232,
            0.75
        );

    backdrop-filter:
        blur(18px);

    -webkit-backdrop-filter:
        blur(18px);

}


/* ==========================================================
   TYPOGRAPHY
   ========================================================== */

h1,
h2,
h3,
h4,
h5,
h6 {

    color:
        var(--h360-navy-900)
        !important;

    letter-spacing:
        -0.025em;

}


h1 {

    font-weight:
        800 !important;

}


h2,
h3 {

    font-weight:
        750 !important;

}


p,
li,
label {

    color:
        var(--h360-text);

}


[data-testid="stMarkdownContainer"] p {

    line-height:
        1.62;

}


[data-testid="stCaptionContainer"],
.stCaption {

    color:
        var(--h360-muted)
        !important;

}


hr {

    border:
        0 !important;

    border-top:
        1px solid
        var(--h360-border)
        !important;

    margin:
        1.45rem 0 !important;

}


/* ==========================================================
   SIDEBAR
   ========================================================== */

section[data-testid="stSidebar"] {

    background:
        linear-gradient(
            180deg,
            var(--h360-navy-950) 0%,
            var(--h360-navy-900) 45%,
            var(--h360-navy-800) 100%
        )
        !important;

    border-right:
        1px solid
        rgba(
            255,
            255,
            255,
            0.08
        )
        !important;

    box-shadow:
        8px 0 30px
        rgba(
            7,
            26,
            47,
            0.12
        );

}


section[data-testid="stSidebar"] > div {

    background:
        transparent
        !important;

}


section[data-testid="stSidebar"] * {

    color:
        #ffffff;

}


section[data-testid="stSidebar"]
[data-testid="stCaptionContainer"] {

    color:
        #a9c4df
        !important;

}


/* Sidebar navigation */

section[data-testid="stSidebarNav"] {

    padding-top:
        0.35rem;

}


section[data-testid="stSidebarNav"] a {

    border-radius:
        10px;

    margin:
        0.14rem
        0.35rem;

    min-height:
        2.65rem;

    transition:
        all
        0.16s
        ease;

    border:
        1px solid
        transparent;

}


section[data-testid="stSidebarNav"] a:hover {

    background:
        rgba(
            255,
            255,
            255,
            0.08
        )
        !important;

    border-color:
        rgba(
            255,
            255,
            255,
            0.08
        );

    transform:
        translateX(2px);

}


/* Sidebar metric */

section[data-testid="stSidebar"]
[data-testid="stMetric"] {

    background:
        rgba(
            255,
            255,
            255,
            0.065
        )
        !important;

    border:
        1px solid
        rgba(
            255,
            255,
            255,
            0.10
        )
        !important;

    box-shadow:
        none
        !important;

}


section[data-testid="stSidebar"]
[data-testid="stMetric"]::before {

    display:
        none;

}


section[data-testid="stSidebar"]
[data-testid="stMetricLabel"] p {

    color:
        #9ebbd7
        !important;

}


section[data-testid="stSidebar"]
[data-testid="stMetricValue"] {

    color:
        #ffffff
        !important;

}


/* Sidebar alerts */

section[data-testid="stSidebar"]
[data-testid="stAlert"] {

    background:
        rgba(
            255,
            255,
            255,
            0.065
        )
        !important;

    border:
        1px solid
        rgba(
            255,
            255,
            255,
            0.11
        )
        !important;

}


section[data-testid="stSidebar"]
[data-testid="stAlert"] * {

    color:
        #ffffff
        !important;

}


/* ==========================================================
   BORDERED CONTAINERS / CARDS
   ========================================================== */

[data-testid="stVerticalBlockBorderWrapper"] {

    background:
        var(--h360-surface);

    border-radius:
        16px !important;

    border-color:
        var(--h360-border)
        !important;

    box-shadow:
        var(--h360-shadow-sm);

}


/* ==========================================================
   KPI CARDS
   ========================================================== */

[data-testid="stMetric"] {

    position:
        relative;

    min-height:
        126px;

    padding:
        1.08rem
        1.15rem
        1.08rem
        1.22rem
        !important;

    background:
        linear-gradient(
            145deg,
            #ffffff 0%,
            #fbfdff 100%
        )
        !important;

    border:
        1px solid
        var(--h360-border)
        !important;

    border-radius:
        15px
        !important;

    box-shadow:
        var(--h360-shadow-md)
        !important;

    overflow:
        hidden;

    transition:
        transform
        0.16s
        ease,
        box-shadow
        0.16s
        ease,
        border-color
        0.16s
        ease;

}


[data-testid="stMetric"]:hover {

    transform:
        translateY(-2px);

    border-color:
        #bfd4ea
        !important;

    box-shadow:
        var(--h360-shadow-lg)
        !important;

}


[data-testid="stMetric"]::before {

    content:
        "";

    position:
        absolute;

    left:
        0;

    top:
        17px;

    bottom:
        17px;

    width:
        4px;

    border-radius:
        0
        4px
        4px
        0;

    background:
        linear-gradient(
            180deg,
            var(--h360-blue-600),
            var(--h360-cyan-500)
        );

}


[data-testid="stMetricLabel"] {

    overflow:
        visible
        !important;

}


[data-testid="stMetricLabel"] p {

    color:
        #64788d
        !important;

    font-size:
        0.74rem
        !important;

    font-weight:
        750
        !important;

    letter-spacing:
        0.025em;

    text-transform:
        uppercase;

    line-height:
        1.35
        !important;

    white-space:
        normal
        !important;

    overflow:
        visible
        !important;

    text-overflow:
        clip
        !important;

}


[data-testid="stMetricValue"] {

    color:
        var(--h360-navy-900)
        !important;

    font-size:
        clamp(
            1.45rem,
            1.8vw,
            2rem
        )
        !important;

    font-weight:
        800
        !important;

    letter-spacing:
        -0.045em
        !important;

    line-height:
        1.16
        !important;

    white-space:
        normal
        !important;

    overflow:
        visible
        !important;

    text-overflow:
        clip
        !important;

}


[data-testid="stMetricDelta"] div {

    font-size:
        0.78rem
        !important;

    font-weight:
        700
        !important;

}


/* ==========================================================
   BUTTONS
   ========================================================== */

.stButton > button,
.stDownloadButton > button,
[data-testid="stBaseButton-secondary"] {

    min-height:
        2.7rem
        !important;

    border-radius:
        9px
        !important;

    border:
        1px solid
        #c8d9ea
        !important;

    background:
        #ffffff
        !important;

    color:
        #234f76
        !important;

    font-weight:
        700
        !important;

    box-shadow:
        var(--h360-shadow-xs)
        !important;

    transition:
        all
        0.15s
        ease;

}


.stButton > button p,
.stDownloadButton > button p {

    color:
        inherit
        !important;

}


.stButton > button:hover,
.stDownloadButton > button:hover {

    border-color:
        #8dbcf2
        !important;

    background:
        var(--h360-blue-50)
        !important;

    color:
        var(--h360-blue-700)
        !important;

    transform:
        translateY(-1px);

    box-shadow:
        var(--h360-shadow-sm)
        !important;

}


[data-testid="stBaseButton-primary"],
.stButton > button[kind="primary"] {

    background:
        linear-gradient(
            135deg,
            var(--h360-blue-600),
            var(--h360-blue-700)
        )
        !important;

    color:
        #ffffff
        !important;

    border-color:
        var(--h360-blue-600)
        !important;

    box-shadow:
        0 5px 14px
        rgba(
            37,
            99,
            235,
            0.20
        )
        !important;

}


[data-testid="stBaseButton-primary"]:hover {

    background:
        linear-gradient(
            135deg,
            #1d4ed8,
            #1e40af
        )
        !important;

    color:
        #ffffff
        !important;

}


/* ==========================================================
   PAGE LINKS / WORKSPACE NAV
   ========================================================== */

[data-testid="stPageLink"] a {

    min-height:
        2.5rem;

    border:
        1px solid
        var(--h360-border);

    border-radius:
        9px;

    padding:
        0.35rem
        0.5rem;

    justify-content:
        center;

    background:
        rgba(
            255,
            255,
            255,
            0.92
        );

    color:
        #315c83
        !important;

    font-size:
        0.82rem;

    font-weight:
        700;

    transition:
        all
        0.15s
        ease;

}


[data-testid="stPageLink"] a p {

    color:
        inherit
        !important;

}


[data-testid="stPageLink"] a:hover {

    transform:
        translateY(-1px);

    border-color:
        #8dbcf2;

    background:
        #ffffff;

    color:
        var(--h360-blue-700)
        !important;

    box-shadow:
        var(--h360-shadow-sm);

}


/* ==========================================================
   TABS
   ========================================================== */

[data-testid="stTabs"] {

    margin-top:
        0.7rem;

    margin-bottom:
        1.15rem;

}


[data-testid="stTabs"]
[data-baseweb="tab-list"] {

    gap:
        0.2rem;

    padding:
        0.3rem;

    background:
        #eaf1f8
        !important;

    border:
        1px solid
        var(--h360-border)
        !important;

    border-radius:
        11px
        !important;

    overflow-x:
        auto;

}


[data-testid="stTabs"] button {

    min-height:
        2.45rem;

    padding:
        0.4rem
        0.9rem
        !important;

    border-radius:
        7px
        !important;

    color:
        #607489
        !important;

    font-size:
        0.84rem;

    font-weight:
        700
        !important;

    white-space:
        nowrap;

}


[data-testid="stTabs"] button p {

    color:
        inherit
        !important;

}


[data-testid="stTabs"]
button[aria-selected="true"] {

    background:
        #ffffff
        !important;

    color:
        var(--h360-blue-700)
        !important;

    box-shadow:
        0 2px 7px
        rgba(
            15,
            42,
            70,
            0.08
        );

}


[data-testid="stTabs"]
[data-baseweb="tab-highlight"],
[data-testid="stTabs"]
[data-baseweb="tab-border"] {

    display:
        none
        !important;

}


/* ==========================================================
   PLOTLY CHART CONTAINERS
   ========================================================== */

[data-testid="stPlotlyChart"] {

    width:
        100%
        !important;

    max-width:
        100%
        !important;

    background:
        #ffffff
        !important;

    border:
        1px solid
        var(--h360-border)
        !important;

    border-radius:
        15px
        !important;

    padding:
        0
        !important;

    margin:
        0.4rem
        0
        1.25rem
        !important;

    box-shadow:
        var(--h360-shadow-md)
        !important;

    overflow:
        hidden
        !important;

}


[data-testid="stPlotlyChart"] > div,
[data-testid="stPlotlyChart"] .js-plotly-plot,
[data-testid="stPlotlyChart"] .plot-container,
[data-testid="stPlotlyChart"] .svg-container {

    width:
        100%
        !important;

    max-width:
        100%
        !important;

    margin:
        0
        !important;

    padding:
        0
        !important;

}


[data-testid="stPlotlyChart"] .modebar {

    background:
        rgba(
            255,
            255,
            255,
            0.94
        )
        !important;

    border:
        1px solid
        #e2e8f0;

    border-radius:
        7px;

    padding:
        2px
        !important;

    box-shadow:
        var(--h360-shadow-xs);

}


[data-testid="stPlotlyChart"]
.modebar-btn path {

    fill:
        #64748b
        !important;

}


[data-testid="stPlotlyChart"]
.modebar-btn:hover path {

    fill:
        var(--h360-blue-600)
        !important;

}


/* ==========================================================
   DATAFRAMES
   ========================================================== */

[data-testid="stDataFrame"] {

    background:
        #ffffff;

    border:
        1px solid
        var(--h360-border);

    border-radius:
        13px;

    overflow:
        hidden;

    box-shadow:
        var(--h360-shadow-sm);

}


/* ==========================================================
   EXPANDERS
   ========================================================== */

[data-testid="stExpander"] {

    background:
        #ffffff
        !important;

    border:
        1px solid
        var(--h360-border)
        !important;

    border-radius:
        11px
        !important;

    overflow:
        hidden;

    margin-bottom:
        0.75rem;

    box-shadow:
        var(--h360-shadow-xs);

}


[data-testid="stExpander"] summary {

    font-weight:
        700;

    color:
        var(--h360-navy-900);

}


/* ==========================================================
   ALERTS
   ========================================================== */

[data-testid="stAlert"] {

    border-radius:
        11px
        !important;

    border-width:
        1px
        !important;

    box-shadow:
        var(--h360-shadow-xs);

}


[data-testid="stAlert"] p,
[data-testid="stAlert"] div,
[data-testid="stAlert"] span {

    color:
        #26384a
        !important;

}


/* ==========================================================
   INPUTS
   ========================================================== */

[data-baseweb="select"] > div,
[data-baseweb="input"] > div,
[data-testid="stDateInput"] > div > div,
[data-testid="stNumberInput"] > div > div {

    background:
        #ffffff
        !important;

    border-color:
        #c8d9e8
        !important;

    border-radius:
        9px
        !important;

    color:
        var(--h360-text)
        !important;

    min-height:
        2.6rem;

}


[data-baseweb="select"] > div:hover,
[data-baseweb="input"] > div:hover {

    border-color:
        #8dbcf2
        !important;

}


[data-testid="stWidgetLabel"] p {

    color:
        #334155
        !important;

    font-size:
        0.81rem;

    font-weight:
        700
        !important;

}


/* ==========================================================
   COLUMN / BLOCK SPACING
   ========================================================== */

[data-testid="stHorizontalBlock"] {

    gap:
        1rem;

}


[data-testid="stVerticalBlock"] {

    gap:
        0.72rem;

}


/* ==========================================================
   TOOLTIP
   ========================================================== */

[data-baseweb="tooltip"] {

    font-size:
        0.78rem
        !important;

}


/* ==========================================================
   MOBILE / TABLET
   ========================================================== */

@media (
    max-width: 900px
) {

    [data-testid="stMainBlockContainer"],
    .block-container {

        padding-left:
            1rem;

        padding-right:
            1rem;

    }


    [data-testid="stMetric"] {

        min-height:
            112px;

    }


    [data-testid="stMetricValue"] {

        font-size:
            1.45rem
            !important;

    }

}


/* ==========================================================
   PRINT / BOARD PACK
   ========================================================== */

@media print {

    [data-testid="stSidebar"],
    [data-testid="stToolbar"],
    .stButton,
    .stDownloadButton {

        display:
            none
            !important;

    }


    .stApp {

        background:
            #ffffff
            !important;

    }


    [data-testid="stMetric"],
    [data-testid="stPlotlyChart"],
    [data-testid="stDataFrame"] {

        box-shadow:
            none
            !important;

        break-inside:
            avoid;

    }

}

</style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# PAGE HEADER
# ============================================================

def render_page_header(
    title: str,
    subtitle: str = "",
    icon: str = "🏥",
    eyebrow: str = "Hospital 360 Intelligence Platform",
):

    with st.container(
        border=True
    ):

        top_left, top_right = st.columns(
            [5, 1.35],
            vertical_alignment="center",
        )

        with top_left:

            st.caption(
                eyebrow.upper()
            )

            heading = (
                f"{icon} {title}".strip()
            )

            st.title(
                heading
            )

            if subtitle:

                st.markdown(
                    subtitle
                )

        with top_right:

            st.caption(
                "PLATFORM STATUS"
            )

            st.markdown(
                "**Enterprise Analytics**"
            )

            st.caption(
                f"{APP_ENV.title()} · v{APP_VERSION}"
            )

        st.caption(
            "Hospital 360  •  Healthcare Operations  •  "
            "Financial Intelligence  •  Clinical Analytics  •  "
            "Synthetic Data Environment"
        )


# ============================================================
# TOP WORKSPACE NAVIGATION
# ============================================================

def render_page_actions(
    key: str = "page",
):

    nav_items = [

        (
            "app.py",
            "Home",
        ),

        (
            "pages/01_Executive_Command_Center.py",
            "Executive",
        ),

        (
            "pages/02_Patient_Analytics.py",
            "Patients",
        ),

        (
            "pages/03_Operations.py",
            "Operations",
        ),

        (
            "pages/04_Finance.py",
            "Finance",
        ),

        (
            "pages/05_Risk.py",
            "Risk",
        ),

        (
            "pages/06_Claims.py",
            "Claims",
        ),

        (
            "pages/07_Doctor_Performance.py",
            "Doctors",
        ),

        (
            "pages/07_Doctor_Performance_Dashboard.py",
            "Doctors",
        ),

        (
            "pages/08_AI_Analyst.py",
            "AI",
        ),

        (
            "pages/09_Data_Explorer.py",
            "Explorer",
        ),

        (
            "pages/10_MIS_Reports.py",
            "MIS",
        ),

        (
            "pages/11_ETL_Control.py",
            "ETL",
        ),

        (
            "pages/11_ETL_Control_Center.py",
            "ETL",
        ),

        (
            "pages/12_Admin.py",
            "Admin",
        ),

    ]

    seen: set[str] = set()

    available: list[
        tuple[str, str]
    ] = []

    for path, label in nav_items:

        if label in seen:

            continue

        if not _page_exists(
            path
        ):

            continue

        seen.add(
            label
        )

        available.append(
            (
                path,
                label,
            )
        )

    if not available:

        return

    st.caption(
        "WORKSPACES"
    )

    columns = st.columns(
        len(available),
        gap="small",
    )

    for (
        column,
        (
            path,
            label,
        ),
    ) in zip(
        columns,
        available,
    ):

        with column:

            st.page_link(
                path,
                label=label,
                width="stretch",
            )


# ============================================================
# BOOTSTRAP PAGE
# ============================================================

def bootstrap_page(
    title: str,
    subtitle: str = "",
    icon: str = "🏥",
    show_sidebar: bool = True,
    show_actions: bool = True,
):

    configure_page(
        title=title,
        icon=icon,
    )

    inject_app_css()

    if show_sidebar:

        render_sidebar_status()

    render_page_header(
        title=title,
        subtitle=subtitle,
        icon=icon,
    )

    if show_actions:

        render_page_actions(
            key=(
                title
                .lower()
                .replace(
                    " ",
                    "_",
                )
                .replace(
                    "&",
                    "and",
                )
            )
        )


# ============================================================
# SECTION HEADERS
# ============================================================

def section_header(
    title: str,
    subtitle: str = "",
    number: int | str | None = None,
    kicker: str | None = None,
):

    st.markdown(
        "---"
    )

    if kicker:

        st.caption(
            str(
                kicker
            ).upper()
        )

    display = (
        f"{number}. {title}"
        if number is not None
        else title
    )

    st.subheader(
        display
    )

    if subtitle:

        st.caption(
            subtitle
        )


def subsection_header(
    title: str,
    subtitle: str = "",
):

    st.markdown(
        f"#### {title}"
    )

    if subtitle:

        st.caption(
            subtitle
        )


# ============================================================
# MANAGEMENT INSIGHT
# ============================================================

def management_insight(
    text: str,
    label: str = "Management Insight",
):

    st.info(
        f"**{label}**\n\n{text}"
    )


# ============================================================
# STATUS PANEL
# ============================================================

def status_panel(
    title: str,
    body: str,
    status: str = "info",
):

    message = (
        f"**{title}**\n\n"
        f"{body}"
    )

    normalized = (
        str(
            status
        )
        .strip()
        .lower()
    )

    if normalized == "success":

        st.success(
            message
        )

    elif normalized == "warning":

        st.warning(
            message
        )

    elif normalized in {
        "danger",
        "error",
    }:

        st.error(
            message
        )

    else:

        st.info(
            message
        )


# ============================================================
# INFORMATION CARD
# ============================================================

def info_card(
    title: str,
    value: Any,
    body: str = "",
):

    with st.container(
        border=True
    ):

        st.caption(
            str(
                title
            ).upper()
        )

        st.markdown(
            f"### {value}"
        )

        if body:

            st.caption(
                body
            )


# ============================================================
# KPI / METRIC ROW
# ============================================================

def metric_row(
    items: Sequence[Any],
    columns: int | None = None,
):

    normalized = (
        _normalize_metric_items(
            items
        )
    )

    if not normalized:

        return

    count = (
        columns
        or len(
            normalized
        )
    )

    count = max(
        1,
        min(
            int(
                count
            ),
            len(
                normalized
            ),
        ),
    )

    for start in range(
        0,
        len(
            normalized
        ),
        count,
    ):

        batch = (
            normalized[
                start:
                start + count
            ]
        )

        metric_columns = (
            st.columns(
                len(
                    batch
                ),
                gap="medium",
            )
        )

        for (
            column,
            item,
        ) in zip(
            metric_columns,
            batch,
        ):

            with column:

                st.metric(
                    label=str(
                        item[
                            "label"
                        ]
                    ),
                    value=str(
                        item[
                            "value"
                        ]
                    ),
                    delta=(
                        None
                        if item[
                            "delta"
                        ] is None
                        else str(
                            item[
                                "delta"
                            ]
                        )
                    ),
                    help=item[
                        "help"
                    ],
                )


# ============================================================
# DATAFRAME
# ============================================================

def dataframe(
    frame: pd.DataFrame,
    height: int = 420,
    hide_index: bool = True,
):

    if frame is None:

        st.info(
            "No data is available."
        )

        return

    if not isinstance(
        frame,
        pd.DataFrame,
    ):

        frame = pd.DataFrame(
            frame
        )

    if frame.empty:

        st.info(
            "No records match the current selection."
        )

        return

    st.dataframe(
        frame,
        width="stretch",
        height=height,
        hide_index=hide_index,
    )


# ============================================================
# PLOTLY ENTERPRISE THEME
# ============================================================

def style_figure(
    figure,
    *,
    height: int = 390,
    unified_hover: bool = False,
    show_legend: bool | None = None,
):

    """
    Central Hospital 360 Plotly design system.

    Use this instead of defining local style_figure()
    functions inside individual pages.
    """

    figure.update_layout(

        height=height,

        paper_bgcolor="#FFFFFF",

        plot_bgcolor="#FFFFFF",

        font=dict(
            family=(
                "Inter, Segoe UI, "
                "Roboto, Arial, sans-serif"
            ),
            color="#334155",
            size=12,
        ),

        title=dict(
            font=dict(
                color="#0B2745",
                size=16,
                family=(
                    "Inter, Segoe UI, "
                    "Roboto, Arial, sans-serif"
                ),
            ),
            x=0.02,
            xanchor="left",
        ),

        margin=dict(
            l=24,
            r=24,
            t=58,
            b=32,
            pad=0,
        ),

        legend=dict(
            title_text="",
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(
                color="#475569",
                size=11,
            ),
            bgcolor="rgba(0,0,0,0)",
        ),

        hoverlabel=dict(
            bgcolor="#071A2F",
            bordercolor="#071A2F",
            font=dict(
                color="#FFFFFF",
                size=12,
            ),
        ),

        hovermode=(
            "x unified"
            if unified_hover
            else "closest"
        ),

        colorway=[
            "#2563EB",
            "#06B6D4",
            "#059669",
            "#F59E0B",
            "#7C3AED",
            "#E11D48",
            "#0EA5E9",
            "#14B8A6",
        ],

        bargap=0.28,

        transition=dict(
            duration=250,
        ),

    )

    if show_legend is not None:

        figure.update_layout(
            showlegend=show_legend
        )

    figure.update_xaxes(

        showgrid=False,

        zeroline=False,

        automargin=True,

        tickfont=dict(
            color="#64748B",
            size=11,
        ),

        title_font=dict(
            color="#475569",
            size=12,
        ),

        linecolor="#DCE6F0",

        tickcolor="#CBD5E1",

    )

    figure.update_yaxes(

        showgrid=True,

        gridcolor="rgba(148,163,184,0.16)",

        gridwidth=1,

        zeroline=False,

        automargin=True,

        tickfont=dict(
            color="#64748B",
            size=11,
        ),

        title_font=dict(
            color="#475569",
            size=12,
        ),

        linecolor="#DCE6F0",

    )

    figure.update_traces(

        hoverlabel=dict(
            font_size=12,
        )

    )

    # Better visual weight for line charts.
    try:

        figure.update_traces(
            line=dict(
                width=3,
            ),
            marker=dict(
                size=7,
            ),
            selector=dict(
                type="scatter"
            ),
        )

    except Exception:

        pass

    return figure


def render_plotly_chart(
    figure,
    *,
    height: int = 390,
    unified_hover: bool = False,
    show_legend: bool | None = None,
    key: str | None = None,
):

    figure = style_figure(
        figure,
        height=height,
        unified_hover=unified_hover,
        show_legend=show_legend,
    )

    st.plotly_chart(
        figure,
        width="stretch",
        config={
            "displaylogo": False,
            "responsive": True,
            "scrollZoom": False,
            "modeBarButtonsToRemove": [
                "lasso2d",
                "select2d",
            ],
            "toImageButtonOptions": {
                "format": "png",
                "filename": (
                    "hospital_360_chart"
                ),
                "height": height,
                "scale": 2,
            },
        },
        key=key,
    )


def chart_context(
    title: str,
    subtitle: str = "",
):

    st.markdown(
        f"#### {title}"
    )

    if subtitle:

        st.caption(
            subtitle
        )


# ============================================================
# FORMATTING
# ============================================================

def format_integer(
    value: Any,
) -> str:

    return (
        f"{_safe_int(value):,}"
    )


def format_currency(
    value: Any,
    decimals: int = 2,
    symbol: str = "₹",
) -> str:

    number = (
        _safe_float(
            value
        )
    )

    return (
        f"{symbol}"
        f"{number:,.{decimals}f}"
    )


def format_currency_compact(
    value: Any,
    symbol: str = "₹",
) -> str:

    number = (
        _safe_float(
            value
        )
    )

    absolute = abs(
        number
    )

    if absolute >= 1_000_000_000:

        return (
            f"{symbol}"
            f"{number / 1_000_000_000:,.2f}B"
        )

    if absolute >= 1_000_000:

        return (
            f"{symbol}"
            f"{number / 1_000_000:,.2f}M"
        )

    if absolute >= 1_000:

        return (
            f"{symbol}"
            f"{number / 1_000:,.2f}K"
        )

    return (
        f"{symbol}"
        f"{number:,.2f}"
    )


def format_percentage(
    value: Any,
    decimals: int = 2,
) -> str:

    return (
        f"{_safe_float(value):,.{decimals}f}%"
    )


def safe_scalar(
    frame: pd.DataFrame,
    column: str,
    default: Any = 0,
):

    if frame is None:

        return default

    if frame.empty:

        return default

    if column not in frame.columns:

        return default

    value: Any = frame.iloc[
        0,
        frame.columns.get_loc(
            column
        ),
    ]

    if pd.isna(
        value
    ):

        return default

    return value


# ============================================================
# SYSTEM HEALTH
# ============================================================

@st.cache_data(
    ttl=30,
    show_spinner=False,
)
def load_system_health() -> dict[str, Any]:

    try:

        result = read_sql(
            """
            SELECT
                current_database() AS database_name,
                current_user AS database_user,
                current_timestamp AS database_time,
                version() AS database_version,
                current_setting('TimeZone') AS server_timezone
            """
        )

        if result.empty:

            raise RuntimeError(
                "Database health query returned no rows."
            )

        row = result.iloc[0]

        return {

            "status":
                "ONLINE",

            "database_online":
                True,

            "database_name":
                row.get(
                    "database_name"
                ),

            "database_user":
                row.get(
                    "database_user"
                ),

            "database_time":
                row.get(
                    "database_time"
                ),

            "database_version":
                row.get(
                    "database_version"
                ),

            "server_timezone":
                row.get(
                    "server_timezone"
                ),

        }

    except Exception as exc:

        return {

            "status":
                "OFFLINE",

            "database_online":
                False,

            "database_name":
                None,

            "database_user":
                None,

            "database_time":
                None,

            "database_version":
                None,

            "server_timezone":
                None,

            "error":
                str(
                    exc
                ),

        }


# ============================================================
# WAREHOUSE COUNTS
# ============================================================

@st.cache_data(
    ttl=60,
    show_spinner=False,
)
def load_warehouse_counts() -> pd.DataFrame:

    return read_sql(
        """
        SELECT
            'Patients' AS entity,
            COUNT(*)::BIGINT AS row_count
        FROM warehouse.dim_patient

        UNION ALL

        SELECT
            'Doctors',
            COUNT(*)::BIGINT
        FROM warehouse.dim_doctor

        UNION ALL

        SELECT
            'Departments',
            COUNT(*)::BIGINT
        FROM warehouse.dim_department

        UNION ALL

        SELECT
            'Admissions',
            COUNT(*)::BIGINT
        FROM warehouse.fact_admission

        UNION ALL

        SELECT
            'Bills',
            COUNT(*)::BIGINT
        FROM warehouse.fact_billing

        UNION ALL

        SELECT
            'Claims',
            COUNT(*)::BIGINT
        FROM warehouse.fact_claim

        UNION ALL

        SELECT
            'Lab Tests',
            COUNT(*)::BIGINT
        FROM warehouse.fact_lab_test

        UNION ALL

        SELECT
            'Medication Events',
            COUNT(*)::BIGINT
        FROM warehouse.fact_medication
        """
    )


# ============================================================
# DATA FRESHNESS
# ============================================================

@st.cache_data(
    ttl=60,
    show_spinner=False,
)
def load_data_freshness() -> pd.DataFrame:

    return read_sql(
        """
        SELECT
            'Admissions' AS dataset,
            MAX(admission_timestamp) AS latest_timestamp
        FROM warehouse.fact_admission

        UNION ALL

        SELECT
            'Billing',
            MAX(d.full_date)::timestamp
        FROM warehouse.fact_billing b
        LEFT JOIN warehouse.dim_date d
            ON d.date_key = b.billing_date_key

        UNION ALL

        SELECT
            'Claims Submitted',
            MAX(d.full_date)::timestamp
        FROM warehouse.fact_claim c
        LEFT JOIN warehouse.dim_date d
            ON d.date_key = c.submission_date_key
        """
    )


# ============================================================
# ETL SUMMARY
# ============================================================

@st.cache_data(
    ttl=30,
    show_spinner=False,
)
def load_etl_summary():

    return read_sql(
        """
        SELECT
            status,
            COUNT(*)::BIGINT AS batch_count,

            COALESCE(
                SUM(records_received),
                0
            )::BIGINT AS records_received,

            COALESCE(
                SUM(records_inserted),
                0
            )::BIGINT AS records_inserted,

            COALESCE(
                SUM(records_updated),
                0
            )::BIGINT AS records_updated,

            COALESCE(
                SUM(records_rejected),
                0
            )::BIGINT AS records_rejected

        FROM control.etl_batch

        GROUP BY
            status

        ORDER BY
            status
        """
    )


# ============================================================
# DATA QUALITY
# ============================================================

@st.cache_data(
    ttl=30,
    show_spinner=False,
)
def load_data_quality_summary():

    return read_sql(
        """
        SELECT
            severity,
            status,

            COUNT(*)::BIGINT
                AS check_count,

            COALESCE(
                SUM(records_checked),
                0
            )::BIGINT
                AS records_checked,

            COALESCE(
                SUM(failed_records),
                0
            )::BIGINT
                AS failed_records

        FROM control.data_quality_log

        GROUP BY
            severity,
            status

        ORDER BY
            severity,
            status
        """
    )


# ============================================================
# REJECTED RECORDS
# ============================================================

@st.cache_data(
    ttl=30,
    show_spinner=False,
)
def load_rejected_records(
    limit: int = 500,
):

    safe_limit = max(
        1,
        min(
            int(
                limit
            ),
            5000,
        ),
    )

    return read_sql(
        f"""
        SELECT
            rejection_id,
            batch_id,
            dataset_name,
            record_identifier,
            rule_name,
            rejection_reason,
            rejected_at

        FROM control.rejected_record

        ORDER BY
            rejected_at DESC,
            rejection_id DESC

        LIMIT {safe_limit}
        """
    )


# ============================================================
# LATEST ETL STATUS
# ============================================================

@st.cache_data(
    ttl=30,
    show_spinner=False,
)
def load_latest_etl_status() -> dict[str, Any]:

    result = read_sql(
        """
        SELECT
            batch_id,
            batch_name,
            batch_type,
            source_name,
            start_time,
            end_time,
            status,
            records_received,
            records_inserted,
            records_updated,
            records_rejected,
            error_message,
            created_at,
            source_batch_id,
            business_date,
            duration_seconds,
            source_path

        FROM control.etl_batch

        ORDER BY
            batch_id DESC

        LIMIT 1
        """
    )

    if result.empty:

        return {
            "status":
                "NO RUNS"
        }

    return {
        str(k): v
        for k, v
        in result.iloc[
            0
        ].to_dict().items()
    }


# ============================================================
# CONTROL COUNTS
# ============================================================

@st.cache_data(
    ttl=30,
    show_spinner=False,
)
def load_control_counts() -> dict[str, int]:

    result = read_sql(
        """
        SELECT

            (
                SELECT COUNT(*)
                FROM control.etl_batch
            )::BIGINT
                AS etl_batches,

            (
                SELECT COUNT(*)
                FROM control.data_quality_log
            )::BIGINT
                AS quality_checks,

            (
                SELECT COUNT(*)
                FROM control.rejected_record
            )::BIGINT
                AS rejected_records,

            (
                SELECT COUNT(*)
                FROM control.audit_log
            )::BIGINT
                AS audit_events
        """
    )

    if result.empty:

        return {
            "etl_batches": 0,
            "quality_checks": 0,
            "rejected_records": 0,
            "audit_events": 0,
        }

    row = result.iloc[0]

    return {

        key: int(
            row.get(
                key,
                0,
            )
            or 0
        )

        for key in [
            "etl_batches",
            "quality_checks",
            "rejected_records",
            "audit_events",
        ]

    }


# ============================================================
# EXPORT / BI ARTIFACT INVENTORY
# ============================================================

def export_inventory() -> pd.DataFrame:

    roots = [

        (
            EXPORT_ROOT,
            "Exports",
        ),

        (
            REPORTS_ROOT,
            "Reports",
        ),

        (
            PROJECT_ROOT
            / "powerbi",
            "Power BI",
        ),

        (
            PROJECT_ROOT
            / "PowerBI",
            "Power BI",
        ),

        (
            PROJECT_ROOT
            / "tableau",
            "Tableau",
        ),

        (
            PROJECT_ROOT
            / "Tableau",
            "Tableau",
        ),

        (
            PROJECT_ROOT
            / "dashboards",
            "Dashboards",
        ),

        (
            PROJECT_ROOT
            / "bi",
            "BI",
        ),

    ]

    allowed = {
        ".csv",
        ".xlsx",
        ".xls",
        ".pdf",
        ".pbix",
        ".pbit",
        ".twb",
        ".twbx",
        ".hyper",
        ".json",
    }

    rows: list[
        dict[str, Any]
    ] = []

    seen: set[str] = set()

    for (
        root,
        root_category,
    ) in roots:

        if not root.exists():

            continue

        try:

            paths = root.rglob(
                "*"
            )

        except OSError:

            continue

        for path in paths:

            try:

                if (
                    not path.is_file()
                    or path.suffix.lower()
                    not in allowed
                ):

                    continue

                resolved = (
                    path.resolve()
                )

                identity = (
                    str(
                        resolved
                    ).lower()
                )

                if identity in seen:

                    continue

                seen.add(
                    identity
                )

                stat = (
                    resolved.stat()
                )

                try:

                    relative = (
                        resolved.relative_to(
                            PROJECT_ROOT
                        )
                    )

                except ValueError:

                    relative = (
                        resolved
                    )

                category = (
                    root_category
                )

                if (
                    root_category
                    in {
                        "Exports",
                        "Reports",
                    }
                    and resolved.parent
                    != root
                ):

                    category = (
                        resolved.parent.name
                        or root_category
                    )

                rows.append(
                    {
                        "category":
                            category,

                        "file_name":
                            resolved.name,

                        "file_type":
                            resolved
                            .suffix
                            .lstrip(".")
                            .upper(),

                        "size_kb":
                            round(
                                stat.st_size
                                / 1024,
                                2,
                            ),

                        "size_bytes":
                            stat.st_size,

                        "modified_at":
                            datetime.fromtimestamp(
                                stat.st_mtime
                            ),

                        "relative_path":
                            str(
                                relative
                            ),

                        "path":
                            str(
                                resolved
                            ),
                    }
                )

            except OSError:

                continue

    columns = [
        "category",
        "file_name",
        "file_type",
        "size_kb",
        "size_bytes",
        "modified_at",
        "relative_path",
        "path",
    ]

    if not rows:

        return pd.DataFrame(
            columns=columns
        )

    return (
        pd.DataFrame(
            rows,
            columns=columns,
        )
        .sort_values(
            "modified_at",
            ascending=False,
        )
        .reset_index(
            drop=True
        )
    )


# ============================================================
# CACHE CONTROL
# ============================================================

def clear_application_cache():

    st.cache_data.clear()


# ============================================================
# SIDEBAR ENTERPRISE STATUS
# ============================================================

def render_sidebar_status():

    with st.sidebar:

        st.markdown(
            """
### 🏥 Hospital 360
**Healthcare Intelligence Platform**
            """
        )

        st.caption(
            "ENTERPRISE ANALYTICS"
        )

        st.divider()

        health = (
            load_system_health()
        )

        if health.get(
            "database_online"
        ):

            st.success(
                "● PostgreSQL Connected"
            )

        else:

            st.error(
                "● Database Unavailable"
            )

        try:

            latest = (
                load_latest_etl_status()
            )

            if latest:

                status = str(
                    latest.get(
                        "status",
                        "Unknown",
                    )
                )

                batch = str(
                    latest.get(
                        "batch_name"
                    )
                    or latest.get(
                        "batch_id"
                    )
                    or "—"
                )

                st.caption(
                    "LATEST DATA PIPELINE"
                )

                st.markdown(
                    f"**{status}**"
                )

                st.caption(
                    batch
                )

        except Exception:

            pass

        st.divider()

        try:

            counts = (
                load_control_counts()
            )

            c1, c2 = st.columns(
                2
            )

            with c1:

                st.metric(
                    "ETL Runs",
                    format_integer(
                        counts.get(
                            "etl_batches",
                            0,
                        )
                    ),
                )

            with c2:

                st.metric(
                    "DQ Checks",
                    format_integer(
                        counts.get(
                            "quality_checks",
                            0,
                        )
                    ),
                )

            c3, c4 = st.columns(
                2
            )

            with c3:

                st.metric(
                    "Rejected",
                    format_integer(
                        counts.get(
                            "rejected_records",
                            0,
                        )
                    ),
                )

            with c4:

                st.metric(
                    "Audit",
                    format_integer(
                        counts.get(
                            "audit_events",
                            0,
                        )
                    ),
                )

        except Exception:

            pass

        st.divider()

        st.caption(
            "SYSTEM"
        )

        st.caption(
            f"Environment · {APP_ENV.title()}"
        )

        st.caption(
            f"Release · {APP_VERSION}"
        )

        if health.get(
            "database_name"
        ):

            st.caption(
                "Database · "
                + str(
                    health.get(
                        "database_name"
                    )
                )
            )

        st.caption(
            "Synthetic healthcare data"
        )


# ============================================================
# REFRESH
# ============================================================

def render_refresh_button(
    key: str = "refresh",
    label: str = "Refresh Data",
    clear_cached_data: bool = True,
):

    if st.button(
        f"↻ {label}",
        key=key,
        width="stretch",
    ):

        if clear_cached_data:

            st.cache_data.clear()

        st.rerun()


# ============================================================
# DOWNLOAD HELPERS
# ============================================================

def csv_download_button(
    frame: pd.DataFrame,
    file_name: str,
    label: str = "Download CSV",
    key: str | None = None,
):

    if frame is None:

        return

    if frame.empty:

        st.button(
            label,
            disabled=True,
            width="stretch",
            key=(
                f"{key}_disabled"
                if key
                else None
            ),
        )

        return

    data = (
        frame
        .to_csv(
            index=False
        )
        .encode(
            "utf-8"
        )
    )

    st.download_button(
        label=label,
        data=data,
        file_name=file_name,
        mime="text/csv",
        width="stretch",
        key=key,
    )


def bytes_download_button(
    data: bytes,
    file_name: str,
    label: str = "Download",
    mime: str = "application/octet-stream",
    key: str | None = None,
):

    st.download_button(
        label=label,
        data=data,
        file_name=file_name,
        mime=mime,
        width="stretch",
        key=key,
    )


# ============================================================
# FILTER HELPERS
# ============================================================

def multiselect_filter(
    frame: pd.DataFrame,
    column: str,
    label: str | None = None,
    key: str | None = None,
):

    if (
        frame is None
        or frame.empty
        or column not in frame.columns
    ):

        return []

    options = sorted(
        frame[
            column
        ]
        .dropna()
        .astype(
            str
        )
        .unique()
        .tolist()
    )

    return st.multiselect(
        label
        or column,
        options,
        key=key,
    )


def apply_multiselect_filter(
    frame: pd.DataFrame,
    column: str,
    values: Iterable[str],
):

    values = list(
        values
    )

    if not values:

        return frame

    if column not in frame.columns:

        return frame

    return frame[
        frame[
            column
        ]
        .astype(
            str
        )
        .isin(
            values
        )
    ]


# ============================================================
# EMPTY STATE
# ============================================================

def empty_state(
    title: str = "No data available",
    message: str = (
        "No records match the current selection."
    ),
):

    status_panel(
        title=title,
        body=message,
        status="info",
    )


# ============================================================
# PAGE FOOTER
# ============================================================

def render_page_footer(
    text: str | None = None,
):

    st.divider()

    left, right = st.columns(
        [5, 1],
        vertical_alignment="center",
    )

    with left:

        st.caption(
            text
            or (
                "Hospital 360 · "
                "Enterprise Healthcare Intelligence · "
                "Synthetic Healthcare Data · "
                f"v{APP_VERSION}"
            )
        )

    with right:

        render_refresh_button(
            key=(
                "footer_refresh_"
                + str(
                    abs(
                        hash(
                            text
                            or "hospital360"
                        )
                    )
                )
            ),
            label="Refresh",
        )