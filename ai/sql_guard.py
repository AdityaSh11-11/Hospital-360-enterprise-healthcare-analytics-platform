from __future__ import annotations

import re
from dataclasses import dataclass

ALLOWED_SCHEMAS = {"analytics", "warehouse"}
MAX_ROWS = 500

BLOCKED_KEYWORDS = {
    "INSERT", "UPDATE", "DELETE", "MERGE", "UPSERT",
    "DROP", "ALTER", "TRUNCATE", "CREATE", "REPLACE",
    "GRANT", "REVOKE", "COPY", "CALL", "DO", "EXECUTE",
    "VACUUM", "ANALYZE", "REFRESH", "CLUSTER", "REINDEX",
    "COMMENT", "SECURITY", "SET", "RESET",
}

BLOCKED_PATTERNS = (
    r"\bpg_catalog\b",
    r"\binformation_schema\b",
    r"\bpg_sleep\s*\(",
    r"\bpg_read_file\s*\(",
    r"\bpg_ls_dir\s*\(",
    r"\blo_import\s*\(",
    r"\blo_export\s*\(",
    r"\bdblink\b",
    r"\bpostgres_fdw\b",
    r"\bcurrent_setting\s*\(",
)

@dataclass
class GuardResult:
    sql: str
    safe: bool
    reason: str = ""

def _strip_literals(sql: str) -> str:
    sql = re.sub(r"'(?:''|[^'])*'", "''", sql, flags=re.S)
    sql = re.sub(r'"(?:""|[^"])*"', '""', sql, flags=re.S)
    return sql

def _cte_names(sql: str) -> set[str]:
    cleaned = _strip_literals(sql)
    names = set(
        m.group(1).lower()
        for m in re.finditer(
            r"(?:\bWITH\b|,)\s*([A-Za-z_][A-Za-z0-9_]*)\s+AS\s*\(",
            cleaned,
            flags=re.I,
        )
    )
    return names

def validate_and_limit(sql: str, max_rows: int = MAX_ROWS) -> GuardResult:
    raw = (sql or "").strip()
    if not raw:
        return GuardResult("", False, "Empty SQL.")

    # Exactly one statement; a single trailing semicolon is okay.
    trimmed = raw[:-1].strip() if raw.endswith(";") else raw
    if ";" in trimmed:
        return GuardResult("", False, "Multiple SQL statements are blocked.")

    if "--" in trimmed or "/*" in trimmed or "*/" in trimmed:
        return GuardResult("", False, "SQL comments are blocked.")

    normalized = _strip_literals(trimmed)
    first = re.match(r"^\s*(SELECT|WITH)\b", normalized, flags=re.I)
    if not first:
        return GuardResult("", False, "Only SELECT/WITH queries are allowed.")

    upper = normalized.upper()
    for keyword in BLOCKED_KEYWORDS:
        if re.search(rf"\b{re.escape(keyword)}\b", upper):
            return GuardResult("", False, f"Blocked SQL keyword: {keyword}.")

    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, normalized, flags=re.I):
            return GuardResult("", False, "Blocked database/system access pattern.")

    # Every explicitly qualified schema must be allowlisted.
    qualified = re.findall(
        r"\b([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)\b",
        normalized,
    )
    for schema, _ in qualified:
        if schema.lower() not in ALLOWED_SCHEMAS:
            return GuardResult(
                "", False, f"Schema '{schema}' is not available to the AI."
            )

    # FROM/JOIN relations must be schema-qualified unless they are CTEs.
    ctes = _cte_names(normalized)
    relations = re.findall(
        r"\b(?:FROM|JOIN)\s+([A-Za-z_][A-Za-z0-9_\.]*)",
        normalized,
        flags=re.I,
    )
    for relation in relations:
        rel = relation.lower()
        if "." not in rel and rel not in ctes:
            return GuardResult(
                "", False,
                f"Relation '{relation}' must use analytics. or warehouse. schema."
            )
        if "." in rel:
            schema = rel.split(".", 1)[0]
            if schema not in ALLOWED_SCHEMAS:
                return GuardResult("", False, f"Schema '{schema}' is blocked.")

    # Prevent SELECT INTO even if it appears after WITH.
    if re.search(r"\bINTO\b", upper):
        return GuardResult("", False, "SELECT INTO is blocked.")

    # Cap result size. Existing smaller LIMITs are kept.
    limit_match = re.search(r"\bLIMIT\s+(\d+)\b", normalized, flags=re.I)
    final_sql = trimmed
    if limit_match:
        if int(limit_match.group(1)) > max_rows:
            final_sql = re.sub(
                r"\bLIMIT\s+\d+\b",
                f"LIMIT {max_rows}",
                final_sql,
                count=1,
                flags=re.I,
            )
    else:
        final_sql = f"{final_sql}\nLIMIT {max_rows}"

    return GuardResult(final_sql, True, "Read-only query approved.")
