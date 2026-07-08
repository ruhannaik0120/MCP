"""SQL validation tests for the MCP execution framework."""

from validation.sql_guard import validate_query


def test_validate_query_rejects_sql_comments():
    ok, reason = validate_query("SELECT 1 -- comment")
    assert ok is False
    assert "comments" in reason.lower()


def test_validate_query_allows_select():
    ok, reason = validate_query("SELECT name FROM sys.databases")
    assert ok is True
    assert reason == ""


def test_validator_accepts_approved_write_statement():
    ok, reason = validate_query("UPDATE users SET is_active = 1")
    assert ok is True
    assert reason == ""


def test_validate_query_rejects_multiple_statements():
    ok, reason = validate_query("UPDATE users SET is_active = 1; DELETE FROM users")
    assert ok is False
    assert "multiple statements" in reason.lower()


def test_validate_query_allows_cte():
    ok, reason = validate_query("WITH cte AS (SELECT 1 AS value) SELECT * FROM cte")
    assert ok is True
    assert reason == ""


def test_validate_query_allows_comment_tokens_inside_string_literals():
    ok, reason = validate_query("SELECT * FROM logs WHERE message = 'value--part'")
    assert ok is True
    assert reason == ""


def test_validate_query_allows_semicolon_inside_string_literal():
    ok, reason = validate_query("SELECT 'alpha;beta' AS value")
    assert ok is True
    assert reason == ""
