"""Database connector abstraction used by the MCP runtime."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class DatabaseConnector(ABC):
    """Abstract interface for backend-specific database connectors."""

    @abstractmethod
    def connect(self, database: str | None = None, timeout_seconds: int | None = None) -> Any:
        """Open a connection to the target database."""

    @abstractmethod
    def test_connection(self, database: str | None = None, timeout_seconds: int | None = None) -> dict[str, Any]:
        """Run a lightweight connection check and return diagnostics."""

    @abstractmethod
    def health_check(self, database: str | None = None, timeout_seconds: int | None = None) -> dict[str, Any]:
        """Return a health/diagnostic summary for the connector."""

    @abstractmethod
    def list_databases(self, timeout_seconds: int | None = None) -> dict[str, Any]:
        """Return a list of available databases for the current connector."""

    @abstractmethod
    def list_tables(
        self,
        database: str | None = None,
        schema: str | None = None,
        timeout_seconds: int | None = None,
    ) -> dict[str, Any]:
        """Return the tables available in a database."""

    @abstractmethod
    def describe_table(
        self,
        database: str | None = None,
        table: str | None = None,
        schema: str | None = None,
        timeout_seconds: int | None = None,
    ) -> dict[str, Any]:
        """Return column metadata for a table."""

    @abstractmethod
    def execute_query(
        self,
        query: str,
        *,
        database: str | None = None,
        timeout_seconds: int | None = None,
        max_rows: int | None = None,
        execution_mode: str | None = None,
    ) -> Any:
        """Execute a database query and return the result payload."""

    @abstractmethod
    def close(self) -> None:
        """Close any open resources held by the connector."""
