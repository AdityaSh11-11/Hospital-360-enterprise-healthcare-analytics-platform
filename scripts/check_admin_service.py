from __future__ import annotations

import importlib.util
from pathlib import Path

from admin.service import (
    PROJECT_ROOT,
    discover_incremental_batches,
    get_admin_capabilities,
    get_audit_history,
    get_export_status,
    get_operational_status,
    get_pending_batches,
    record_audit_event,
)
from analytics.data_loader import read_sql


def separator() -> None:
    print("=" * 116)


def small_separator() -> None:
    print("-" * 116)


def check_capabilities() -> None:
    dataframe = get_admin_capabilities()

    required = {
        "Generate Synthetic Batch",
        "Run Pending ETL",
        "Data Quality Validation",
        "Generate MIS",
        "Validate Exports",
        "Delete Batch",
        "Rebuild Environment",
        "Gemini AI",
    }

    missing = (
        required
        - set(
            dataframe[
                "action"
            ].astype(str)
        )
    )

    if missing:
        raise RuntimeError(
            "Missing capabilities: "
            + ", ".join(
                sorted(missing)
            )
        )

    destructive = dataframe[
        dataframe[
            "action"
        ].isin(
            [
                "Delete Batch",
                "Rebuild Environment",
            ]
        )
    ]

    if destructive[
        "enabled"
    ].astype(bool).any():
        raise RuntimeError(
            "Destructive capability enabled."
        )

    print()
    print("CAPABILITY MATRIX")
    small_separator()
    print(dataframe.to_string(index=False))
    print()
    print(
        "[PASS] Capability matrix validated."
    )


def check_generator_cli() -> None:
    module = (
        "scripts.generate_incremental_data"
    )

    spec = importlib.util.find_spec(
        module
    )

    print()
    print("GENERATOR CLI")
    small_separator()

    print(
        f"Expected module         : {module}"
    )

    print(
        f"Module discovered       : "
        f"{'YES' if spec else 'NO'}"
    )

    if spec is None:
        scripts = (
            PROJECT_ROOT
            / "scripts"
        )

        candidates = sorted(
            path.name
            for path in scripts.glob(
                "*incremental*.py"
            )
        )

        print(
            "Candidate files         : "
            + (
                ", ".join(candidates)
                if candidates
                else "none"
            )
        )

        raise RuntimeError(
            "Generator CLI module mismatch. "
            "Do not use the Generate button until "
            "admin.service is aligned with the "
            "actual generator script."
        )

    print()
    print(
        "[PASS] Generator CLI module discovered."
    )


def check_batches() -> None:
    all_batches = (
        discover_incremental_batches()
    )

    pending = get_pending_batches()

    print()
    print("INCREMENTAL BATCH DISCOVERY")
    small_separator()

    print(
        f"Source batches          : "
        f"{len(all_batches):,}"
    )

    print(
        f"Pending batches         : "
        f"{len(pending):,}"
    )

    if not all_batches.empty:
        if (
            all_batches[
                "source_batch_id"
            ].duplicated().any()
        ):
            raise RuntimeError(
                "Duplicate source batch IDs "
                "discovered."
            )

    print()
    print(
        "[PASS] Batch discovery validated."
    )


def check_operational_status() -> None:
    status = get_operational_status()

    required = {
        "total_batches",
        "successful_batches",
        "failed_batches",
        "reconciliation_failed_batches",
        "latest_successful_etl",
        "pending_source_batches",
        "audit_events",
        "latest_audit_event",
        "quality_checks",
        "failed_quality_records",
    }

    missing = (
        required
        - set(status)
    )

    if missing:
        raise RuntimeError(
            "Missing operational keys: "
            + ", ".join(
                sorted(missing)
            )
        )

    print()
    print("OPERATIONAL STATUS")
    small_separator()

    for key, value in status.items():
        print(
            f"{key:<38}: {value}"
        )

    print()
    print(
        "[PASS] Operational status validated."
    )


def check_exports() -> None:
    dataframe = get_export_status()

    print()
    print("REQUIRED ANALYTICAL ASSETS")
    small_separator()

    print(
        dataframe.to_string(
            index=False
        )
    )

    missing = dataframe[
        ~dataframe[
            "exists"
        ]
    ]

    if not missing.empty:
        raise RuntimeError(
            "Required analytical assets missing: "
            + ", ".join(
                missing[
                    "asset"
                ].astype(str)
            )
        )

    print()
    print(
        "[PASS] Required analytical assets found."
    )


def check_audit_cycle() -> None:
    before = int(
        read_sql(
            """
            SELECT COUNT(*) AS row_count
            FROM control.audit_log
            """
        ).iloc[0]["row_count"]
    )

    record_audit_event(
        module="Phase 9.3 Validator",
        action="Audit Write Test",
        status="SUCCESS",
        details=(
            "Synthetic audit event generated "
            "by Phase 9.3 validation."
        ),
        entity_type="VALIDATION",
        entity_id="PHASE-9.3",
        username="validator",
    )

    after = int(
        read_sql(
            """
            SELECT COUNT(*) AS row_count
            FROM control.audit_log
            """
        ).iloc[0]["row_count"]
    )

    if after != before + 1:
        raise RuntimeError(
            "Audit write count mismatch."
        )

    history = get_audit_history(
        limit=25,
        module="Phase 9.3 Validator",
        status="SUCCESS",
    )

    match = history[
        history[
            "entity_id"
        ]
        == "PHASE-9.3"
    ]

    if match.empty:
        raise RuntimeError(
            "Filtered audit retrieval failed."
        )

    print()
    print("AUDIT FILTER/WRITE TEST")
    small_separator()

    print(
        f"Before                : {before:,}"
    )

    print(
        f"After                 : {after:,}"
    )

    print()
    print(
        "[PASS] Audit write and filtering validated."
    )


def check_warehouse_safety() -> None:
    row = read_sql(
        """
        SELECT
            (
                SELECT COUNT(*)
                FROM warehouse.fact_admission
            ) AS admissions,
            (
                SELECT COUNT(*)
                FROM warehouse.fact_billing
            ) AS bills,
            (
                SELECT COUNT(*)
                FROM warehouse.fact_claim
            ) AS claims
        """
    ).iloc[0]

    expected = {
        "admissions": 52697,
        "bills": 52697,
        "claims": 37658,
    }

    print()
    print("WAREHOUSE SAFETY")
    small_separator()

    for column, target in expected.items():
        actual = int(
            row[column]
        )

        print(
            f"{column:<30}"
            f"{actual:>18,}"
        )

        if actual != target:
            raise RuntimeError(
                f"{column} unexpectedly changed: "
                f"{actual:,} != {target:,}"
            )

    print()
    print(
        "[PASS] Phase 9.3 validator made no "
        "warehouse fact changes."
    )


def main() -> None:
    separator()

    print(
        "HOSPITAL 360 â€” "
        "PHASE 9.3 ADMIN CONTROL VALIDATION"
    )

    separator()

    check_capabilities()
    check_generator_cli()
    check_batches()
    check_operational_status()
    check_exports()
    check_audit_cycle()
    check_warehouse_safety()

    print()
    separator()

    print(
        "PHASE 9.3 ADMIN CONTROL "
        "VALIDATION PASSED"
    )

    separator()


if __name__ == "__main__":
    main()

