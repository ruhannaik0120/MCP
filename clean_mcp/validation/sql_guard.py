"""SQL validation guardrails for the MCP execution framework.

This module keeps the validation lightweight and readable. It should not parse
SQL fully or take on connector responsibilities.
"""

from __future__ import annotations

import re

from logger import logger

def _strip_string_literals(sql: str) -> str:
    """Replace string literal contents with a safe placeholder for scanning."""

    return re.sub(r"N?'(?:''|[^'])*'", "''", sql)


def normalize_query(sql: str) -> str:
    """Normalize whitespace and trailing delimiters for validation."""

    return sql.strip().rstrip(";").strip()


def validate_query(sql: str) -> tuple[bool, str]:
    """Validate that an approved request contains one unambiguous statement."""

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

    return True, ""
