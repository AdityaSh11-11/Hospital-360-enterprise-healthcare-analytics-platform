from __future__ import annotations

import pandas as pd

from analytics.data_loader import read_sql

ALLOWED_SCHEMAS = ("analytics", "warehouse")


def load_schema_catalog() -> pd.DataFrame:
    """
    Discover the live Hospital 360 analytical schema.
    Only analytics + warehouse are exposed to the AI.
    """
    return read_sql(
        """
        SELECT
            c.table_schema,
            c.table_name,
            c.column_name,
            c.data_type,
            c.ordinal_position
        FROM information_schema.columns c
        WHERE c.table_schema IN ('analytics', 'warehouse')
        ORDER BY c.table_schema, c.table_name, c.ordinal_position
        """
    )

def schema_prompt(max_chars: int = 28000) -> str:
    df = load_schema_catalog()
    if df.empty:
        return "No schema metadata is available."

    chunks: list[str] = []
    for (schema, table), group in df.groupby(
        ["table_schema", "table_name"], sort=True
    ):
        columns = ", ".join(
            f"{row.column_name} {row.data_type}"
            for row in group.itertuples()
        )
        chunks.append(f"{schema}.{table}({columns})")

    text = "\n".join(chunks)
    return text[:max_chars]
