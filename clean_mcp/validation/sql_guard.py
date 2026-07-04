"""SQL validation guardrails for the MCP execution framework.

This module keeps the validation lightweight and readable. It should not parse
SQL fully or take on connector responsibilities.
"""

from __future__ import annotations

import re

from logger import logger

FORBIDDEN_KEYWORDS = [
    r"\bINSERT\b",
    r"\bUPDATE\b",
    r"\bDELETE\b",
    r"\bDROP\b",
    r"\bTRUNCATE\b",
    r"\bALTER\b",
    r"\bCREATE\b",
    r"\bEXEC\b",
    r"\bEXECUTE\b",
    r"\bMERGE\b",
    r"\bGRANT\b",
    r"\bREVOKE\b",
    r"\bBACKUP\b",
    r"\bRESTORE\b",
    r"\bDBCC\b",
    r"\bINTO\b",
    r"\bSP_\w+",
    r"\bXP_\w+",
]


def _strip_string_literals(sql: str) -> str:
    """Replace string literal contents with a safe placeholder for scanning."""

    return re.sub(r"N?'(?:''|[^'])*'", "''", sql)


def normalize_query(sql: str) -> str:
    """Normalize whitespace and trailing delimiters for validation."""

    return sql.strip().rstrip(";").strip()


def validate_query(sql: str, execution_mode: str = "read_only") -> tuple[bool, str]:
    """Validate whether a SQL statement is safe for the configured execution mode."""

    if not sql or not sql.strip():
        return False, "Empty query is not allowed."

    normalized = normalize_query(sql)
    if not normalized:
        return False, "Empty query is not allowed."

    # Strip quoted text before scanning so values such as 'value--part' do not
    # look like SQL comments or forbidden commands.
    stripped_for_comments = _strip_string_literals(normalized)
    if re.search(r"--|/\*|\*/", stripped_for_comments):
        logger.warning("Blocked query containing SQL comments.")
        return False, "Query blocked - SQL comments are not permitted."

    # One tool invocation maps to one auditable statement. Multiple statements
    # could hide a write operation behind an otherwise valid SELECT.
    statement_count = len([statement for statement in stripped_for_comments.split(";") if statement.strip()])
    if statement_count > 1:
        logger.warning("Blocked query containing multiple statements.")
        return False, "Query blocked - multiple statements are not permitted."

    stripped = stripped_for_comments.upper()
    if execution_mode not in {"read_only", "read_write"}:
        return False, "Execution mode must be read_only or read_write."

    # In read-write mode the database user's own permissions are authoritative.
    # The framework still requires one unambiguous statement per tool call.
    if execution_mode == "read_write":
        return True, ""

    if not (stripped.startswith("SELECT") or stripped.startswith("WITH")):
        return False, "Only SELECT statements are permitted."

    if re.search(r"\bSELECT\b\s+.*?\bINTO\b", stripped, flags=re.S):
        logger.warning("Blocked query containing SELECT INTO.")
        return False, "Query blocked - SELECT INTO is not permitted."

    for pattern in FORBIDDEN_KEYWORDS:
        if re.search(pattern, stripped):
            keyword = pattern.replace(r"\b", "").replace(r"\w+", "*")
            logger.warning(f"Blocked query containing forbidden keyword: {keyword}")
            return False, f"Query blocked - forbidden keyword detected: {keyword}"

    return True, ""
