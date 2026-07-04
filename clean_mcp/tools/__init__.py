"""MCP tool implementations for the MCP execution framework.

This package contains only the callable MCP tool wrappers. It should not hold
connection logic, SQL validation, or response shaping.
"""

from tools.connection import health, test_connection
from tools.diagnostics import config_diagnostics
from tools.profiles import list_profiles, switch_profile
from tools.metadata import describe_table, list_databases, list_tables
from tools.query import execute_select_query
