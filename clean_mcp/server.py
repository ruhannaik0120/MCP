"""MCP server entry point for the database connector runtime.

This file should only register MCP tools and start the server. It should not
contain business logic, SQL validation, or direct connector code.
"""

import json

from mcp.server.fastmcp import FastMCP

from config import Config
from logger import logger
from tools import (
    config_diagnostics,
    describe_table,
    execute_query,
    execute_select_query,
    health,
    list_databases,
    list_profiles,
    list_tables,
    switch_profile,
    test_connection,
)

Config.validate()
# FastMCP owns the protocol transport; this module only publishes our tool surface.
mcp = FastMCP("mcp-execution-framework")
logger.info("MCP Server initialising...")


# Profile tools expose safe profile metadata and approval-gated switching.
@mcp.tool()
def tool_list_connection_profiles() -> str:
    """List configured connection profiles without exposing credentials."""

    return json.dumps(list_profiles(), indent=2, default=str)


@mcp.tool()
def tool_switch_connection_profile(name: str, confirm: bool = False) -> str:
    """Switch connectors after explicit approval and verify the new connection.

    First call with confirm=false to inspect the approval requirement. After the
    user approves the system transition, call with confirm=true.
    """

    # Tool errors are returned as JSON so an agent can explain failures without
    # exposing a Python traceback to the user.
    try:
        payload = switch_profile(name, confirm=confirm)
        return json.dumps({"success": True, "data": payload}, indent=2, default=str)
    except Exception as exc:
        return json.dumps({"success": False, "error": {"code": "PROFILE_SWITCH_FAILED", "message": str(exc)}}, indent=2)


@mcp.tool()
def tool_config_diagnostics() -> str:
    """Return a safe summary of the active runtime configuration."""

    return json.dumps(config_diagnostics(), indent=2, default=str)


# Connection and metadata tools let an agent inspect the active system without
# embedding any database-specific behavior in the MCP transport layer.
@mcp.tool()
def tool_test_connection(environment: str = "", database: str = "", timeout_seconds: int | None = None) -> str:
    """Verify database connectivity and return server metadata.

    Args:
        environment: Retained for compatibility; connector selection comes from DB_TYPE.
        database: Database used for the connection check.
        timeout_seconds: Optional command timeout override.

    Returns:
        JSON text containing the standard response envelope.
    """

    return json.dumps(test_connection(environment, database, timeout_seconds), indent=2, default=str)


@mcp.tool()
def tool_health(environment: str = "", timeout_seconds: int | None = None) -> str:
    """Return diagnostics for the selected database connector."""

    return json.dumps(health(environment, timeout_seconds), indent=2, default=str)


@mcp.tool()
def tool_list_databases(environment: str = "", timeout_seconds: int | None = None) -> str:
    """List databases for the selected connector."""

    return json.dumps(list_databases(environment, timeout_seconds), indent=2, default=str)


@mcp.tool()
def tool_list_tables(
    database: str = "",
    schema: str = "",
    environment: str = "",
    timeout_seconds: int | None = None,
) -> str:
    """List tables in a database, optionally filtered by schema."""

    return json.dumps(list_tables(database, schema, environment, timeout_seconds), indent=2, default=str)


@mcp.tool()
def tool_describe_table(
    database: str = "",
    table: str = "",
    schema: str = "",
    environment: str = "",
    timeout_seconds: int | None = None,
) -> str:
    """Return table metadata for a single table."""

    return json.dumps(describe_table(database, table, schema, environment, timeout_seconds), indent=2, default=str)


@mcp.tool()
def tool_execute_query(
    sql: str = "",
    query: str = "",
    database: str = "",
    schema: str = "",
    environment: str = "",
    timeout_seconds: int | None = None,
    max_rows: int | None = None,
    execution_mode: str = "",
) -> str:
    """Execute one SQL statement using the configured permission mode."""

    # The generic tool supports the server's configured permission mode. The
    # legacy select-named tool below remains available for existing clients.
    return json.dumps(
        execute_query(sql, query, database, schema, environment, timeout_seconds, max_rows, execution_mode),
        indent=2,
        default=str,
    )


@mcp.tool()
def tool_execute_select_query(
    sql: str = "",
    query: str = "",
    database: str = "",
    schema: str = "",
    environment: str = "",
    timeout_seconds: int | None = None,
    max_rows: int | None = None,
    execution_mode: str = "",
) -> str:
    """Execute a parameterized SQL statement against the selected database."""

    return json.dumps(
        execute_select_query(sql, query, database, schema, environment, timeout_seconds, max_rows, execution_mode),
        indent=2,
        default=str,
    )


if __name__ == "__main__":
    logger.info("MCP Server started. Waiting for connections...")
    mcp.run(transport="stdio")
