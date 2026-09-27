from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sqlalchemy import text


# ============================================================
# WAREHOUSE SNAPSHOT
# ============================================================

@dataclass
class WarehouseSnapshot:
    patients: int
    doctors: int
    medications: int
    admissions: int
    billing: int
    claims: int
    labs: int
    medication_events: int


# ============================================================
# BUSINESS KEY RECONCILIATION
# ============================================================

@dataclass
class BusinessKeyCheck:
    dataset: str
    source_count: int
    warehouse_count: int
    missing_count: int
    missing_keys: list[str]

    @property
    def passed(self) -> bool:
        return self.missing_count == 0


@dataclass
class ReconciliationResult:
    checks: list[BusinessKeyCheck]

    @property
    def passed(self) -> bool:
        return all(
            check.passed
            for check in self.checks
        )

    @property
    def total_missing(self) -> int:
        return sum(
            check.missing_count
            for check in self.checks
        )


# ============================================================
# WAREHOUSE TABLE MAP
# ============================================================

WAREHOUSE_TABLES = {
    "patients":
        "warehouse.dim_patient",

    "doctors":
        "warehouse.dim_doctor",

    "medications":
        "warehouse.dim_medication",

    "admissions":
        "warehouse.fact_admission",

    "billing":
        "warehouse.fact_billing",

    "claims":
        "warehouse.fact_claim",

    "labs":
        "warehouse.fact_lab_test",

    "medication_events":
        "warehouse.fact_medication",
}


# ============================================================
# BUSINESS KEY MAP
# ============================================================

BUSINESS_KEY_MAP = {
    "patients": {
        "source_column":
            "patient_id",

        "warehouse_table":
            "warehouse.dim_patient",

        "warehouse_column":
            "patient_id",
    },

    "doctors": {
        "source_column":
            "doctor_id",

        "warehouse_table":
            "warehouse.dim_doctor",

        "warehouse_column":
            "doctor_id",
    },

    "medication_master": {
        "source_column":
            "medication_id",

        "warehouse_table":
            "warehouse.dim_medication",

        "warehouse_column":
            "medication_id",
    },

    "admissions": {
        "source_column":
            "admission_id",

        "warehouse_table":
            "warehouse.fact_admission",

        "warehouse_column":
            "admission_id",
    },

    "billing": {
        "source_column":
            "bill_id",

        "warehouse_table":
            "warehouse.fact_billing",

        "warehouse_column":
            "bill_id",
    },

    "claims": {
        "source_column":
            "claim_id",

        "warehouse_table":
            "warehouse.fact_claim",

        "warehouse_column":
            "claim_id",
    },

    "labs": {
        "source_column":
            "lab_test_id",

        "warehouse_table":
            "warehouse.fact_lab_test",

        "warehouse_column":
            "lab_test_id",
    },

    "medication_events": {
        "source_column":
            "medication_event_id",

        "warehouse_table":
            "warehouse.fact_medication",

        "warehouse_column":
            "medication_event_id",
    },
}


# ============================================================
# COUNT TABLE
# ============================================================

def count_table(
    connection,
    table_name: str,
) -> int:

    if table_name not in (
        WAREHOUSE_TABLES.values()
    ):

        raise ValueError(
            f"Unsupported warehouse table: {table_name}"
        )

    result = connection.execute(
        text(
            f"""
            SELECT COUNT(*)
            FROM {table_name}
            """
        )
    )

    return int(
        result.scalar_one()
    )


# ============================================================
# SNAPSHOT
# ============================================================

def snapshot_warehouse(
    connection,
) -> WarehouseSnapshot:

    return WarehouseSnapshot(
        patients=count_table(
            connection,
            WAREHOUSE_TABLES[
                "patients"
            ],
        ),

        doctors=count_table(
            connection,
            WAREHOUSE_TABLES[
                "doctors"
            ],
        ),

        medications=count_table(
            connection,
            WAREHOUSE_TABLES[
                "medications"
            ],
        ),

        admissions=count_table(
            connection,
            WAREHOUSE_TABLES[
                "admissions"
            ],
        ),

        billing=count_table(
            connection,
            WAREHOUSE_TABLES[
                "billing"
            ],
        ),

        claims=count_table(
            connection,
            WAREHOUSE_TABLES[
                "claims"
            ],
        ),

        labs=count_table(
            connection,
            WAREHOUSE_TABLES[
                "labs"
            ],
        ),

        medication_events=count_table(
            connection,
            WAREHOUSE_TABLES[
                "medication_events"
            ],
        ),
    )


# ============================================================
# SNAPSHOT DELTA
#
# Retained for diagnostics / reporting.
# Do NOT use this as the final retry-safety gate.
# ============================================================

def snapshot_delta(
    before: WarehouseSnapshot,
    after: WarehouseSnapshot,
) -> dict[str, int]:

    return {
        "patients":
            after.patients
            - before.patients,

        "doctors":
            after.doctors
            - before.doctors,

        "medications":
            after.medications
            - before.medications,

        "admissions":
            after.admissions
            - before.admissions,

        "billing":
            after.billing
            - before.billing,

        "claims":
            after.claims
            - before.claims,

        "labs":
            after.labs
            - before.labs,

        "medication_events":
            after.medication_events
            - before.medication_events,
    }


# ============================================================
# EXPECTED DELTA
#
# Retained so existing scripts importing this function
# continue to work.
# ============================================================

def expected_incremental_delta(
    datasets,
) -> dict[str, int]:

    return {
        "patients":
            len(
                datasets.get(
                    "patients",
                    pd.DataFrame(),
                )
            ),

        "doctors":
            len(
                datasets.get(
                    "doctors",
                    pd.DataFrame(),
                )
            ),

        "medications":
            len(
                datasets.get(
                    "medication_master",
                    pd.DataFrame(),
                )
            ),

        "admissions":
            len(
                datasets.get(
                    "admissions",
                    pd.DataFrame(),
                )
            ),

        "billing":
            len(
                datasets.get(
                    "billing",
                    pd.DataFrame(),
                )
            ),

        "claims":
            len(
                datasets.get(
                    "claims",
                    pd.DataFrame(),
                )
            ),

        "labs":
            len(
                datasets.get(
                    "labs",
                    pd.DataFrame(),
                )
            ),

        "medication_events":
            len(
                datasets.get(
                    "medication_events",
                    pd.DataFrame(),
                )
            ),
    }


# ============================================================
# DELTA COMPARISON
#
# Kept for old CLI compatibility.
# New ETL success logic must use reconcile_business_keys().
# ============================================================

def compare_deltas(
    expected: dict[str, int],
    actual: dict[str, int],
) -> dict[str, dict]:

    result = {}

    keys = sorted(
        set(expected)
        |
        set(actual)
    )

    for key in keys:

        expected_value = int(
            expected.get(
                key,
                0,
            )
        )

        actual_value = int(
            actual.get(
                key,
                0,
            )
        )

        difference = (
            actual_value
            - expected_value
        )

        result[key] = {
            "expected":
                expected_value,

            "actual":
                actual_value,

            "difference":
                difference,

            "passed":
                difference == 0,
        }

    return result


# ============================================================
# NORMALIZE BUSINESS KEYS
# ============================================================

def normalize_key(
    value,
) -> str | None:

    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    value = str(
        value
    ).strip()

    if not value:
        return None

    return value


def source_business_keys(
    dataframe: pd.DataFrame,
    column: str,
) -> set[str]:

    if dataframe.empty:
        return set()

    if column not in dataframe.columns:

        raise KeyError(
            (
                f"Source dataset does not contain "
                f"business key column '{column}'."
            )
        )

    keys = {
        normalized

        for value in dataframe[
            column
        ].tolist()

        if (
            normalized := normalize_key(
                value
            )
        ) is not None
    }

    return keys


# ============================================================
# FETCH WAREHOUSE BUSINESS KEYS
# ============================================================

def warehouse_business_keys(
    connection,
    table_name: str,
    column_name: str,
) -> set[str]:

    allowed_pairs = {
        (
            config[
                "warehouse_table"
            ],
            config[
                "warehouse_column"
            ],
        )
        for config
        in BUSINESS_KEY_MAP.values()
    }

    if (
        table_name,
        column_name,
    ) not in allowed_pairs:

        raise ValueError(
            (
                "Unsupported warehouse "
                "business-key lookup: "
                f"{table_name}.{column_name}"
            )
        )

    result = connection.execute(
        text(
            f"""
            SELECT {column_name}
            FROM {table_name}
            """
        )
    )

    return {
        normalized

        for value in result.scalars()

        if (
            normalized := normalize_key(
                value
            )
        ) is not None
    }


# ============================================================
# RECONCILE ONE DATASET
# ============================================================

def reconcile_dataset(
    connection,
    dataset_name: str,
    dataframe: pd.DataFrame,
) -> BusinessKeyCheck:

    if dataset_name not in BUSINESS_KEY_MAP:

        raise KeyError(
            (
                "No business-key reconciliation "
                f"configuration exists for "
                f"dataset '{dataset_name}'."
            )
        )

    config = BUSINESS_KEY_MAP[
        dataset_name
    ]

    source_keys = (
        source_business_keys(
            dataframe,
            config[
                "source_column"
            ],
        )
    )

    # Empty source dataset is automatically reconciled.
    if not source_keys:

        return BusinessKeyCheck(
            dataset=dataset_name,
            source_count=0,
            warehouse_count=0,
            missing_count=0,
            missing_keys=[],
        )

    warehouse_keys = (
        warehouse_business_keys(
            connection,
            config[
                "warehouse_table"
            ],
            config[
                "warehouse_column"
            ],
        )
    )

    present_keys = (
        source_keys
        &
        warehouse_keys
    )

    missing_keys = sorted(
        source_keys
        -
        warehouse_keys
    )

    return BusinessKeyCheck(
        dataset=dataset_name,
        source_count=len(
            source_keys
        ),
        warehouse_count=len(
            present_keys
        ),
        missing_count=len(
            missing_keys
        ),
        missing_keys=missing_keys,
    )


# ============================================================
# FULL BUSINESS-KEY RECONCILIATION
# ============================================================

def reconcile_business_keys(
    connection,
    datasets,
) -> ReconciliationResult:
    """
    Verify that every business key present in the source
    datasets exists in the target warehouse.

    This works for both:

        fresh ETL loads
        retries of partially loaded batches

    It does not depend on row-count deltas.
    """

    checks = []

    for dataset_name in (
        "patients",
        "doctors",
        "medication_master",
        "admissions",
        "billing",
        "claims",
        "labs",
        "medication_events",
    ):

        dataframe = datasets.get(
            dataset_name
        )

        if dataframe is None:
            continue

        check = reconcile_dataset(
            connection=connection,
            dataset_name=dataset_name,
            dataframe=dataframe,
        )

        checks.append(
            check
        )

    return ReconciliationResult(
        checks=checks
    )


# ============================================================
# FORMAT RECONCILIATION RESULT
# ============================================================

def format_reconciliation(
    result: ReconciliationResult,
    max_missing_examples: int = 10,
) -> str:

    lines = []

    lines.append(
        "BUSINESS-KEY RECONCILIATION"
    )

    lines.append(
        "-" * 72
    )

    for check in result.checks:

        status = (
            "PASS"
            if check.passed
            else "FAIL"
        )

        lines.append(
            (
                f"{check.dataset}: "
                f"source={check.source_count:,} | "
                f"present={check.warehouse_count:,} | "
                f"missing={check.missing_count:,} | "
                f"{status}"
            )
        )

        if check.missing_keys:

            examples = (
                check.missing_keys[
                    :max_missing_examples
                ]
            )

            lines.append(
                "  Missing examples: "
                + ", ".join(
                    examples
                )
            )

    lines.append(
        "-" * 72
    )

    lines.append(
        (
            "OVERALL: PASS"
            if result.passed
            else (
                "OVERALL: FAIL | "
                f"missing keys="
                f"{result.total_missing:,}"
            )
        )
    )

    return "\n".join(
        lines
    )


# ============================================================
# ASSERT RECONCILIATION
# ============================================================

def assert_business_key_reconciliation(
    connection,
    datasets,
) -> ReconciliationResult:

    result = reconcile_business_keys(
        connection=connection,
        datasets=datasets,
    )

    if not result.passed:

        raise RuntimeError(
            format_reconciliation(
                result,
                max_missing_examples=20,
            )
        )

    return result