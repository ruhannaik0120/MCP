"""Cross-dialect tests for the framework's hard row ceiling."""

from connectors.mysql.connector import MySQLConnector
from connectors.postgresql.connector import PostgreSQLConnector
from connectors.snowflake.connector import SnowflakeConnector
from connectors.sqlserver.connector import SQLServerConnector


# LIMIT-based dialects must reduce explicit limits above the global ceiling.
def test_limit_dialects_clamp_oversized_explicit_limit():
    query = "SELECT * FROM items LIMIT 5000"

    assert MySQLConnector()._row_limit_sql(query, 100, "read_only").endswith("LIMIT 100")
    assert PostgreSQLConnector()._row_limit_sql(query, 100, "read_only").endswith("LIMIT 100")
    assert SnowflakeConnector()._row_limit_sql(query, 100, "read_only").endswith("LIMIT 100")


# SQL Server's TOP syntax receives the same global ceiling guarantee.
def test_sqlserver_clamps_oversized_top():
    query = "SELECT TOP 5000 * FROM items"

    assert SQLServerConnector()._row_limit_sql(query, 100, "read_only") == "SELECT TOP 100 * FROM items"


# Complex CTE text remains untouched and relies on the fetch-layer backstop.
def test_sqlserver_cte_relies_on_fetch_cap_without_rewriting():
    query = "WITH items AS (SELECT 1 AS value) SELECT * FROM items"

    assert SQLServerConnector()._row_limit_sql(query, 100, "read_only") == query


# Fetch limiting is the final defense when SQL cannot be safely rewritten.
class _Cursor:
    """Record the maximum number of rows requested from a driver cursor."""
    description = [("value",)]

    def __init__(self):
        self.fetchmany_size = None

    def fetchmany(self, size):
        self.fetchmany_size = size
        return [(number,) for number in range(size)]


# The cursor fetch itself must never exceed the configured maximum.
def test_fetch_layer_enforces_cap_even_when_query_cannot_be_rewritten():
    cursor = _Cursor()

    payload = SQLServerConnector()._fetch_rows(cursor, max_rows=3)

    assert cursor.fetchmany_size == 3
    assert len(payload["rows"]) == 3
