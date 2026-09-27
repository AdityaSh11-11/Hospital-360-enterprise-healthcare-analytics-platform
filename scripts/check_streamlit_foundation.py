from __future__ import annotations

from pathlib import Path

from utils.app_helpers import (
    PROJECT_ROOT,
    export_inventory,
    load_control_counts,
    load_data_freshness,
    load_etl_summary,
    load_system_health,
    load_warehouse_counts,
)


def separator() -> None:
    print("=" * 112)


def small_separator() -> None:
    print("-" * 112)


def assert_equal(
    label: str,
    actual: int,
    expected: int,
) -> None:
    if int(actual) != int(expected):
        raise RuntimeError(
            f"{label} failed: "
            f"{actual:,} != {expected:,}"
        )


def check_files() -> None:
    expected = [
        PROJECT_ROOT
        / "app.py",

        PROJECT_ROOT
        / "utils"
        / "app_helpers.py",

        PROJECT_ROOT
        / "pages"
        / "11_ETL_Control.py",

        PROJECT_ROOT
        / "pages"
        / "12_Admin.py",
    ]

    print()
    print("STREAMLIT FILES")
    small_separator()

    for path in expected:
        exists = path.exists()

        print(
            f"{str(path.relative_to(PROJECT_ROOT)):<52}"
            f"{'PASS' if exists else 'FAIL':>16}"
        )

        if not exists:
            raise RuntimeError(
                f"Missing Streamlit file: {path}"
            )


def check_database() -> None:
    health = load_system_health()

    if (
        health.get("status")
        != "ONLINE"
    ):
        raise RuntimeError(
            "Database health check failed."
        )

    print()
    print("DATABASE HEALTH")
    small_separator()

    print(
        f"Status               : "
        f"{health['status']}"
    )

    print(
        f"Database             : "
        f"{health['database_name']}"
    )

    print(
        f"User                 : "
        f"{health['database_user']}"
    )


def check_warehouse_counts() -> None:
    dataframe = load_warehouse_counts()

    count_map = dict(
        zip(
            dataframe["entity"],
            dataframe["row_count"],
        )
    )

    expectations = {
        "Patients": 25338,
        "Doctors": 150,
        "Departments": 10,
        "Admissions": 51317,
        "Bills": 51317,
        "Claims": 36650,
        "Lab Tests": 153688,
        "Medication Events": 179374,
    }

    print()
    print("WAREHOUSE COUNTS")
    small_separator()

    for entity, expected in expectations.items():
        actual = int(
            count_map.get(
                entity,
                -1,
            )
        )

        status = (
            "PASS"
            if actual == expected
            else "FAIL"
        )

        print(
            f"{entity:<34}"
            f"{actual:>18,}"
            f"{status:>14}"
        )

        assert_equal(
            entity,
            actual,
            expected,
        )


def check_freshness() -> None:
    dataframe = load_data_freshness()

    expected_datasets = {
        "Admissions",
        "Billing",
        "Claims Submitted",
        "Lab Tests",
        "Medication Events",
    }

    actual = set(
        dataframe[
            "dataset"
        ].astype(str)
    )

    missing = (
        expected_datasets
        - actual
    )

    if missing:
        raise RuntimeError(
            "Missing freshness datasets: "
            + ", ".join(
                sorted(missing)
            )
        )

    if dataframe[
        "latest_timestamp"
    ].isna().any():
        raise RuntimeError(
            "Null data freshness timestamp found."
        )

    print()
    print("DATA FRESHNESS")
    small_separator()

    print(
        dataframe.to_string(
            index=False
        )
    )

    print()
    print(
        "[PASS] Data freshness validated."
    )


def check_control_layer() -> None:
    control = load_control_counts()
    etl = load_etl_summary()

    if etl.empty:
        raise RuntimeError(
            "No ETL batch history found."
        )

    if control[
        "etl_batches"
    ] != len(etl):
        raise RuntimeError(
            "ETL control count does not "
            "match ETL history rows."
        )

    print()
    print("CONTROL LAYER")
    small_separator()

    print(
        f"ETL batches          : "
        f"{control['etl_batches']:,}"
    )

    print(
        f"Quality checks       : "
        f"{control['quality_checks']:,}"
    )

    print(
        f"Rejected records     : "
        f"{control['rejected_records']:,}"
    )

    print(
        f"Audit events         : "
        f"{control['audit_events']:,}"
    )

    print()
    print(
        "[PASS] Control layer validated."
    )


def check_exports() -> None:
    inventory = export_inventory()

    if inventory.empty:
        raise RuntimeError(
            "No analytical exports found."
        )

    required_categories = {
        "eda",
        "risk",
        "anomalies",
        "risk_intelligence",
    }

    categories = set(
        inventory[
            "category"
        ].astype(str)
    )

    missing = (
        required_categories
        - categories
    )

    if missing:
        raise RuntimeError(
            "Missing expected export "
            "categories: "
            + ", ".join(
                sorted(missing)
            )
        )

    print()
    print("EXPORT INVENTORY")
    small_separator()

    print(
        f"Files                : "
        f"{len(inventory):,}"
    )

    print(
        f"Categories           : "
        f"{inventory['category'].nunique():,}"
    )

    print(
        f"Total size KB        : "
        f"{inventory['size_kb'].sum():,.2f}"
    )

    print()
    print(
        "[PASS] Export inventory validated."
    )


def main() -> None:
    separator()

    print(
        "HOSPITAL 360 — "
        "PHASE 9.1 STREAMLIT FOUNDATION CHECK"
    )

    separator()

    check_files()

    check_database()

    check_warehouse_counts()

    check_freshness()

    check_control_layer()

    check_exports()

    print()
    separator()

    print(
        "PHASE 9.1 STREAMLIT "
        "FOUNDATION VALIDATION PASSED"
    )

    separator()


if __name__ == "__main__":
    main()