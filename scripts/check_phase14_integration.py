from __future__ import annotations

import compileall
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PAGES = [
    "pages/01_Executive_Command_Center.py",
    "pages/02_Patient_Analytics_Dashboard.py",
    "pages/03_Operations_Analytics_Dashboard.py",
    "pages/04_Finance_Analytics_Dashboard.py",
    "pages/05_Risk_Analytics_Dashboard.py",
    "pages/06_Claims_Analytics_Dashboard.py",
    "pages/07_Doctor_Performance_Dashboard.py",
    "pages/08_AI_Analyst_Assistant.py",
    "pages/09_Data_Explorer.py",
    "pages/10_MIS_Reports_Center.py",
    "pages/11_ETL_Control_Center.py",
    "pages/12_Admin_Control_Center.py",
]

OLD_PAGE_REFS = [
    "pages/02_Patient_Analytics.py",
    "pages/03_Operations.py",
    "pages/04_Finance.py",
    "pages/05_Risk.py",
    "pages/06_Claims.py",
    "pages/07_Doctor_Performance.py",
    "pages/08_AI_Analyst.py",
    "pages/10_MIS_Reports.py",
    "pages/11_ETL_Control.py",
    "pages/12_Admin.py",
]

def main() -> None:
    print("=" * 72)
    print("HOSPITAL 360 - PHASE 14 INTEGRATION CHECK")
    print("=" * 72)

    required = ["app.py", "utils/app_helpers.py", "ai/gemini_client.py", *PAGES]
    for rel in required:
        assert (ROOT / rel).exists(), f"Missing required file: {rel}"
    print(f"PASS  required UI files: {len(required)}")

    ok = compileall.compile_dir(str(ROOT), quiet=1)
    assert ok, "Python compilation failed."
    print("PASS  Python compilation")

    helper = (ROOT / "utils/app_helpers.py").read_text(encoding="utf-8")
    for rel in PAGES:
        assert rel in helper, f"Global navigation missing: {rel}"
    print("PASS  global top-right navigation targets")

    py_files = [ROOT / "app.py", *ROOT.joinpath("pages").glob("*.py"),
                *ROOT.joinpath("utils").glob("*.py")]
    corpus = "\n".join(p.read_text(encoding="utf-8") for p in py_files)
    for old in OLD_PAGE_REFS:
        assert old not in corpus, f"Stale page reference remains: {old}"
    print("PASS  no stale page links")

    assert "use_container_width" not in corpus, "Deprecated use_container_width remains."
    print("PASS  Streamlit width API")

    assert "st.exception" not in corpus, "Raw Streamlit traceback rendering remains."
    print("PASS  production-friendly UI errors")

    gemini = (ROOT / "ai/gemini_client.py").read_text(encoding="utf-8")
    assert 'gemini-3.6-flash' in gemini, "Expected Gemini fallback model not configured."
    assert "@lru_cache" in gemini and "def client()" in gemini, "Durable Gemini client missing."
    print("PASS  Gemini durable-client configuration")

    admin = (ROOT / "pages/12_Admin_Control_Center.py").read_text(encoding="utf-8")
    assert "Tableau Assets" not in admin, "Skipped Tableau section is still visible."
    print("PASS  Tableau removed from final Admin deliverables")

    print("=" * 72)
    print("PHASE 14 STATIC INTEGRATION CHECK PASSED")
    print("=" * 72)

if __name__ == "__main__":
    main()
