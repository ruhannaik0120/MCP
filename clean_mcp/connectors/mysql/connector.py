"""MySQL implementation of the database connector interface."""

from __future__ import annotations

import contextlib
import re
from typing import Any

from config import Config, ConfigError, ConnectionConfig
from connectors.base import DatabaseConnector


class MySQLConnector(DatabaseConnector):
    """Connector implementation for MySQL via mysql-connector-python."""

    def _driver(self):
        # Import on first use so installations that do not need MySQL can still
        # start the shared MCP framework.
        try:
            import mysql.connector  # type: ignore
        except ImportError as exc:
            raise ConfigError("Install mysql-connector-python to use the MySQL connector.") from exc
        return mysql.connector

    def _profile(self) -> ConnectionConfig:
        profile = Config.connection_config()
        if not profile.host:
            raise ConfigError("DB_HOST is required for the MySQL connector.")
        return profile

    def _normalize_database(self, database: str | None, fallback: str) -> str:
        return (database or fallback or "").strip()

    def _connection_kwargs(self, profile: ConnectionConfig, database: str | None = None) -> dict[str, Any]:
        options = dict(profile.connection_options or {})
        port = int(options.pop("port", 3306))
        kwargs: dict[str, Any] = {
            "host": profile.host,
            "port": port,
            "user": profile.username,
            "password": profile.password,
            "connection_timeout": profile.timeout_seconds,
        }
        if database:
            kwargs["database"] = database
        kwargs.update(options)
        return kwargs

    def _row_limit_sql(self, sql: str, max_rows: int, execution_mode: str | None) -> str:
        normalized_sql = sql.strip().rstrip(";")
        if (execution_mode or "read_only").strip().lower() != "read_only":
            return normalized_sql
        # Respect an explicit LIMIT; otherwise enforce the framework-wide cap
        # using MySQL's native syntax.
        limit_match = re.search(r"\bLIMIT\s+(\d+)\b", normalized_sql, flags=re.I)
        if limit_match:
            safe_limit = min(int(limit_match.group(1)), max_rows)
            return normalized_sql[: limit_match.start(1)] + str(safe_limit) + normalized_sql[limit_match.end(1) :]
        return f"{normalized_sql} LIMIT {max_rows}"

    def _fetch_rows(self, cursor, max_rows: int | None = None) -> dict[str, Any]:
        columns = [column[0] for column in cursor.description] if cursor.description else []
        raw_rows = cursor.fetchmany(max_rows) if columns and max_rows and hasattr(cursor, "fetchmany") else cursor.fetchall() if columns else []
        rows = [dict(zip(columns, row)) for row in raw_rows[:max_rows] if columns] if max_rows else [dict(zip(columns, row)) for row in raw_rows]
        return {"columns": columns, "rows": rows}

    def connect(self, database: str | None = None, timeout_seconds: int | None = None) -> Any:
        profile = self._profile()
        target_database = self._normalize_database(database, profile.database)
        kwargs = self._connection_kwargs(profile, target_database or None)
        if timeout_seconds is not None:
            kwargs["connection_timeout"] = timeout_seconds
        return self._driver().connect(**kwargs)

    @contextlib.contextmanager
    def _connection(self, database: str | None = None, timeout_seconds: int | None = None):
        connection = self.connect(database=database, timeout_seconds=timeout_seconds)
        try:
            yield connection
        finally:
            connection.close()

    def test_connection(self, database: str | None = None, timeout_seconds: int | None = None) -> dict[str, Any]:
        profile = self._profile()
        target_database = self._normalize_database(database, profile.database)
        with self._connection(database=target_database or None, timeout_seconds=timeout_seconds) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    @@hostname AS server_name,
                    VERSION() AS version,
                    USER() AS logged_in_user,
                    UTC_TIMESTAMP() AS utc_time
                """
            )
            snapshot = self._fetch_rows(cursor)
            cursor.close()
        return {
            "connector_type": self.__class__.__name__,
            "db_type": profile.db_type,
            "database": target_database,
            "connection_status": "connected",
            "server_information": snapshot["rows"][0] if snapshot["rows"] else {},
        }

    def health_check(self, database: str | None = None, timeout_seconds: int | None = None) -> dict[str, Any]:
        return self.test_connection(database=database, timeout_seconds=timeout_seconds)

    def list_databases(self, timeout_seconds: int | None = None) -> dict[str, Any]:
        profile = self._profile()
        with self._connection(timeout_seconds=timeout_seconds) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT SCHEMA_NAME AS name
                FROM INFORMATION_SCHEMA.SCHEMATA
                WHERE SCHEMA_NAME NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys')
                ORDER BY SCHEMA_NAME
                """
            )
            payload = self._fetch_rows(cursor)
            cursor.close()
        return {"connector_type": self.__class__.__name__, "db_type": profile.db_type, "count": len(payload["rows"]), "databases": payload["rows"]}

    def list_tables(self, database: str | None = None, schema: str | None = None, timeout_seconds: int | None = None) -> dict[str, Any]:
        profile = self._profile()
        target_database = self._normalize_database(database, profile.database)
        if not target_database:
            raise ConfigError("Database name is required to list MySQL tables.")
        with self._connection(database=target_database, timeout_seconds=timeout_seconds) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_SCHEMA, TABLE_NAME
                """,
                (target_database,),
            )
            payload = self._fetch_rows(cursor)
            cursor.close()
        return {"connector_type": self.__class__.__name__, "db_type": profile.db_type, "database": target_database, "schema": schema or "", "count": len(payload["rows"]), "tables": payload["rows"]}

    def describe_table(self, database: str | None = None, table: str | None = None, schema: str | None = None, timeout_seconds: int | None = None) -> dict[str, Any]:
        if not table:
            raise ConfigError("Table name is required.")
        profile = self._profile()
        target_database = self._normalize_database(database, profile.database)
        if not target_database:
            raise ConfigError("Database name is required to describe a MySQL table.")
        with self._connection(database=target_database, timeout_seconds=timeout_seconds) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH, ORDINAL_POSITION
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                ORDER BY ORDINAL_POSITION
                """,
                (target_database, table),
            )
            payload = self._fetch_rows(cursor)
            cursor.close()
        return {"connector_type": self.__class__.__name__, "db_type": profile.db_type, "database": target_database, "schema": schema or target_database, "table": table, "column_count": len(payload["rows"]), "columns": payload["rows"]}

    def execute_query(self, query: str, *, database: str | None = None, timeout_seconds: int | None = None, max_rows: int | None = None, execution_mode: str | None = None) -> Any:
        profile = self._profile()
        target_database = self._normalize_database(database, profile.database)
        limited_query = self._row_limit_sql(query, max_rows or profile.max_rows, execution_mode or profile.execution_mode)
        with self._connection(database=target_database or None, timeout_seconds=timeout_seconds) as conn:
            cursor = conn.cursor()
            cursor.execute(limited_query)
            payload = self._fetch_rows(cursor, max_rows or profile.max_rows)
            cursor.close()
        return {"connector_type": self.__class__.__name__, "db_type": profile.db_type, "database": target_database, "columns": payload["columns"], "rows": payload["rows"]}

    def close(self) -> None:
        return None


Connector = MySQLConnector
