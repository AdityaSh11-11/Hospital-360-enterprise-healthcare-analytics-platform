from __future__ import annotations

import importlib.util
from pathlib import Path

from admin.service import (
    discover_incremental_batches,
    get_pending_batches,
)
from analytics.data_loader import load_table
from database.connection import get_engine


PROJECT_ROOT = Path(
    __file__
).resolve().parents[1]


REQUIRED_FILES = [
    "app.py",
    "utils/app_helpers.py",
    "admin/service.py",
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


REQUIRED_VIEWS = [
    "vw_executive_kpis",
    "vw_monthly_hospital_performance",
    "vw_department_performance",
    "vw_patient_demographics",
    "vw_operations_summary",
    "vw_department_operations",
    "vw_finance_summary",
    "vw_monthly_finance",
    "vw_claims_summary",
    "vw_insurer_claim_performance",
    "vw_doctor_analytics_summary",
    "vw_patient_risk",
    "vw_admission_risk",
    "vw_department_risk",
    "vw_bill_financial_risk",
    "vw_claim_risk",
]


def check_files() -> None:
    print("\n[1] Streamlit files")

    for relative in REQUIRED_FILES:
        path = PROJECT_ROOT / relative

        assert path.exists(), (
            f"Missing file: {relative}"
        )

        print(
            f"PASS  {relative}"
        )


def check_deprecations() -> None:
    print(
        "\n[2] Deprecated Streamlit arguments"
    )

    targets = [
        PROJECT_ROOT / "app.py",
        PROJECT_ROOT / "utils",
        PROJECT_ROOT / "pages",
    ]

    offenders = []

    for target in targets:
        paths = (
            [target]
            if target.is_file()
            else list(
                target.rglob("*.py")
            )
        )

        for path in paths:
            text = path.read_text(
                encoding="utf-8"
            )

            if "use_container_width" in text:
                offenders.append(
                    str(
                        path.relative_to(
                            PROJECT_ROOT
                        )
                    )
                )

    assert not offenders, (
        "Deprecated use_container_width "
        f"found in: {offenders}"
    )

    print(
        "PASS  no use_container_width references"
    )


def check_modules() -> None:
    print("\n[3] Operational modules")

    for module in [
        "scripts.generate_incremental_data",
        "scripts.run_incremental_etl",
        "scripts.check_warehouse",
        "scripts.run_mis_report",
        "scripts.check_anomaly_exports",
        "scripts.check_unified_risk_exports",
    ]:
        assert (
            importlib.util.find_spec(module)
            is not None
        ), f"Module not found: {module}"

        print(
            f"PASS  {module}"
        )


def check_views() -> None:
    print("\n[4] Analytics views")

    for view in REQUIRED_VIEWS:
        df = load_table(
            "analytics",
            view,
            limit=1,
        )

        assert len(df.columns) > 0, (
            f"No columns returned: {view}"
        )

        print(
            f"PASS  {view}"
        )


def check_warehouse() -> None:
    print("\n[5] Warehouse connectivity")

    engine = get_engine()

    with engine.connect() as connection:
        result = connection.exec_driver_sql(
            """
            SELECT
                (SELECT COUNT(*)
                 FROM warehouse.dim_patient)
                    AS patients,
                (SELECT COUNT(*)
                 FROM warehouse.fact_admission)
                    AS admissions,
                (SELECT COUNT(*)
                 FROM warehouse.fact_billing)
                    AS bills,
                (SELECT COUNT(*)
                 FROM warehouse.fact_claim)
                    AS claims
            """
        ).mappings().one()

    for key, value in result.items():
        assert int(value) > 0
        print(
            f"PASS  {key}: {int(value):,}"
        )


def check_batches() -> None:
    print("\n[6] Incremental batch state")

    batches = discover_incremental_batches()
    pending = get_pending_batches()

    print(
        f"Discovered batches: {len(batches):,}"
    )

    print(
        f"Pending batches: {len(pending):,}"
    )

    if not pending.empty:
        print(
            "Pending source IDs:"
        )

        for batch in pending[
            "source_batch_id"
        ].astype(str):
            print(
                f"  - {batch}"
            )

    print("PASS  batch discovery")


def main() -> None:
    print(
        "=" * 68
    )
    print(
        "HOSPITAL 360 - STREAMLIT FINAL VALIDATION"
    )
    print(
        "=" * 68
    )

    check_files()
    check_deprecations()
    check_modules()
    check_views()
    check_warehouse()
    check_batches()

    print(
        "\n"
        + "=" * 68
    )

    print(
        "STREAMLIT APPLICATION VALIDATION PASSED"
    )

    print(
        "=" * 68
    )


if __name__ == "__main__":
    main()
