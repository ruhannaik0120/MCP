"""Query-oriented MCP tools for the MCP server.

This wrapper exposes parameterized query execution while keeping validation and
connector handling in the service layer.
"""

from services import query_service


def execute_select_query(
    sql: str = "",
    query: str = "",
    database: str = "",
    schema: str = "",
    environment: str = "",
    timeout_seconds: int | None = None,
    max_rows: int | None = None,
    execution_mode: str = "",
) -> dict:
    """Execute a validated SQL statement against the selected database."""

    return query_service.execute_select_query(
        sql=sql,
        query=query,
        database=database,
        schema=schema,
        environment=environment,
        timeout_seconds=timeout_seconds,
        max_rows=max_rows,
        execution_mode=execution_mode,
    ).to_dict()


def execute_query(
    sql: str = "",
    query: str = "",
    database: str = "",
    schema: str = "",
    environment: str = "",
    timeout_seconds: int | None = None,
    max_rows: int | None = None,
    execution_mode: str = "",
) -> dict:
    """Execute a statement using the server's configured permission mode."""

    return query_service.execute_query(
        sql=sql,
        query=query,
        database=database,
        schema=schema,
        environment=environment,
        timeout_seconds=timeout_seconds,
        max_rows=max_rows,
        execution_mode=execution_mode,
    ).to_dict()
