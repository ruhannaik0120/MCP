"""Business and orchestration logic for MCP tools."""

from __future__ import annotations
from datetime import datetime, timezone
from time import perf_counter
from uuid import uuid4

from artifact_manager import save_execution_artifact
from config import Config, ConfigError
from connectors.factory import ConnectorFactory
from logger import logger, reset_environment, reset_request_id, set_environment, set_request_id
from models.errors import ErrorCode, StructuredError
from models.responses import ToolResponse
from validation.sql_guard import validate_query


class QueryService:
    """Service layer that orchestrates tool requests and formats responses."""

    def __init__(self, sql_connector=None):
        if sql_connector is None:
            Config.load()
            self.connector = ConnectorFactory.create()
        else:
            self.connector = sql_connector

    def _request_id(self) -> str:
        return uuid4().hex[:12]

    def _effective_timeout(self, timeout_seconds: int | None) -> int:
        """Return a positive timeout that cannot exceed the configured ceiling."""

        if timeout_seconds is not None and timeout_seconds <= 0:
            raise ConfigError("timeout_seconds must be greater than zero.")
        return min(timeout_seconds or Config.GLOBAL_TIMEOUT_SECONDS, Config.GLOBAL_TIMEOUT_SECONDS)

    def _begin_request(self, tool: str) -> tuple[str, object, object, float, str]:
        # Context variables attach the same request ID and active backend to
        # every log emitted while this tool call is being processed.
        request_id = self._request_id()
        request_token = set_request_id(request_id)
        environment_name = (Config.DB_TYPE or "database").strip().upper() or "DATABASE"
        environment_token = set_environment(environment_name)
        start_time = perf_counter()
        logger.info(
            f"Starting {tool}.",
            extra={
                "tool": tool,
                "environment": environment_name,
                "db_type": Config.DB_TYPE,
                "success": None,
                "execution_time_ms": 0,
                "event": "request_received",
            },
        )
        return request_id, request_token, environment_token, start_time, environment_name

    def _response(
        self,
        *,
        tool: str,
        environment: str,
        success: bool,
        request_id: str,
        start_time: float,
        data: dict | None = None,
        metadata: dict | None = None,
        error: StructuredError | None = None,
    ) -> ToolResponse:
        # Timing and envelope construction are centralized so every MCP tool
        # returns the same contract regardless of the selected connector.
        execution_time_ms = int((perf_counter() - start_time) * 1000)
        return ToolResponse(
            success=success,
            tool=tool,
            request_id=request_id,
            environment=environment,
            execution_time_ms=execution_time_ms,
            data=data or {},
            metadata=metadata or {},
            error=error,
        )

    def _error(
        self,
        *,
        tool: str,
        environment: str,
        code: str,
        message: str,
        request_id: str,
        start_time: float,
        detail: str | None = None,
        hint: str | None = None,
        retryable: bool = False,
        context: dict | None = None,
        data: dict | None = None,
        metadata: dict | None = None,
    ) -> ToolResponse:
        return self._response(
            tool=tool,
            environment=environment,
            success=False,
            request_id=request_id,
            start_time=start_time,
            data=data,
            metadata=metadata,
            error=StructuredError(
                code=code,
                message=message,
                request_id=request_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
                detail=detail,
                hint=hint,
                retryable=retryable,
                context=context or {},
            ),
        )

    def _end_request(self, tool: str, environment: str, request_id: str, response: ToolResponse) -> None:
        success = response.success
        log_message = f"{tool} {'succeeded' if success else 'failed'}."
        log_method = logger.info if success else logger.error
        log_method(
            log_message,
            extra={
                "tool": tool,
                "environment": environment,
                "db_type": Config.DB_TYPE,
                "success": success,
                "execution_time_ms": response.execution_time_ms,
                "event": "request_completed",
                "error_code": getattr(response.error, "code", None) if response.error else None,
            },
        )

    def _save_execution_artifact(
        self,
        tool: str,
        request_id: str,
        environment: str,
        database: str | None,
        schema: str | None,
        query: str | None,
        response: ToolResponse,
    ) -> None:
        artifact = {
            "request_id": request_id,
            "timestamp": response.timestamp,
            "tool": tool,
            "environment": environment,
            "database": database or "",
            "schema": schema or "",
            "query": query or "",
            "execution_time_ms": response.execution_time_ms,
            "status": "success" if response.success else "failed",
            "rows_returned": len(response.data.get("rows", [])) if isinstance(response.data.get("rows", []), list) else 0,
            "result": response.data,
            "metadata": response.metadata,
            "error": response.error.to_dict() if response.error is not None else None,
        }

        try:
            save_execution_artifact(request_id, artifact)
            logger.info(
                "Execution artifact saved.",
                extra={
                    "tool": tool,
                    "environment": environment,
                    "db_type": Config.DB_TYPE,
                    "request_id": request_id,
                    "event": "execution_artifact_saved",
                    "execution_time_ms": response.execution_time_ms,
                    "status": artifact["status"],
                },
            )
        except OSError as exc:
            logger.error(
                "Failed to save execution artifact.",
                extra={
                    "tool": tool,
                    "environment": environment,
                    "db_type": Config.DB_TYPE,
                    "request_id": request_id,
                    "event": "execution_artifact_failed",
                    "execution_time_ms": response.execution_time_ms,
                    "error_code": "ARTIFACT_SAVE_FAILED",
                },
            )
            logger.debug(str(exc))

    def _finalize_request(
        self,
        response: ToolResponse,
        tool: str,
        environment: str,
        request_id: str,
        database: str | None = None,
        schema: str | None = None,
        query: str | None = None,
    ) -> ToolResponse:
        # Finalization is shared by success and failure paths, guaranteeing that
        # rejected queries and connection errors are auditable too.
        self._save_execution_artifact(tool, request_id, environment, database, schema, query, response)
        self._end_request(tool, environment, request_id, response)
        return response

    def _handle_connector_error(
        self,
        *,
        tool: str,
        requested_environment: str,
        request_id: str,
        start_time: float,
        error: Exception,
        data: dict | None = None,
        retryable: bool = True,
        code: str = ErrorCode.DATABASE_ERROR,
        message: str,
        hint: str | None = None,
    ) -> ToolResponse:
        # Configuration mistakes are non-retryable; network/database errors may
        # be retried by an upstream orchestrator after user intervention.
        if isinstance(error, ConfigError):
            code = ErrorCode.CONFIG_INVALID
            retryable = False
        return self._error(
            tool=tool,
            environment=requested_environment,
            code=code,
            message=message,
            request_id=request_id,
            start_time=start_time,
            detail=str(error),
            hint=hint,
            retryable=retryable,
            data=data,
        )

    def test_connection(
        self,
        environment: str | None = None,
        database: str | None = None,
        timeout_seconds: int | None = None,
    ) -> ToolResponse:
        request_id, request_token, environment_token, start_time, requested_environment = self._begin_request("test_connection")
        try:
            snapshot = self.connector.test_connection(
                database=database or Config.DATABASE,
                timeout_seconds=self._effective_timeout(timeout_seconds),
            )
            response = self._response(
                tool="test_connection",
                environment=Config.DB_TYPE.upper(),
                success=True,
                request_id=request_id,
                start_time=start_time,
                data={
                    "current_environment": Config.DB_TYPE.upper(),
                    "database": database or Config.DATABASE,
                    "connection_status": snapshot.get("connection_status", "connected"),
                    "server_information": snapshot.get("server_information", snapshot),
                },
                metadata={
                    "db_type": Config.DB_TYPE,
                    "connector_type": snapshot.get("connector_type", self.connector.__class__.__name__),
                },
            )
            return self._finalize_request(
                response,
                tool="test_connection",
                environment=Config.DB_TYPE.upper(),
                request_id=request_id,
                database=database or Config.DATABASE,
                schema="",
                query="",
            )
        except Exception as exc:
            response = self._handle_connector_error(
                tool="test_connection",
                requested_environment=requested_environment,
                request_id=request_id,
                start_time=start_time,
                error=exc,
                data={"current_environment": requested_environment, "connection_status": "failed"},
                message="Unable to establish a database connection.",
                hint="Check DB_TYPE and the generic connection settings for the selected connector.",
            )
            return self._finalize_request(
                response,
                tool="test_connection",
                environment=requested_environment,
                request_id=request_id,
                database=database or Config.DATABASE,
                schema="",
                query="",
            )
        finally:
            reset_request_id(request_token)
            reset_environment(environment_token)

    def health(
        self,
        environment: str | None = None,
        timeout_seconds: int | None = None,
    ) -> ToolResponse:
        request_id, request_token, environment_token, start_time, requested_environment = self._begin_request("health")
        try:
            snapshot = self.connector.health_check(
                database=Config.DATABASE,
                timeout_seconds=self._effective_timeout(timeout_seconds),
            )
            response = self._response(
                tool="health",
                environment=Config.DB_TYPE.upper(),
                success=True,
                request_id=request_id,
                start_time=start_time,
                data={
                    "current_environment": Config.DB_TYPE.upper(),
                    "connection_status": snapshot.get("connection_status", "connected"),
                    "server_information": snapshot.get("server_information", snapshot),
                    "environment_details": Config.connection_config().safe_dict(),
                },
                metadata={
                    "db_type": Config.DB_TYPE,
                    "connector_type": snapshot.get("connector_type", self.connector.__class__.__name__),
                },
            )
            return self._finalize_request(
                response,
                tool="health",
                environment=Config.DB_TYPE.upper(),
                request_id=request_id,
                database=Config.DATABASE,
                schema="",
                query="",
            )
        except Exception as exc:
            response = self._handle_connector_error(
                tool="health",
                requested_environment=requested_environment,
                request_id=request_id,
                start_time=start_time,
                error=exc,
                data={
                    "current_environment": requested_environment,
                    "connection_status": "failed",
                    "server_information": {},
                },
                message="Health check failed.",
                hint="Check DB_TYPE and the generic connection settings for the selected connector.",
            )
            return self._finalize_request(
                response,
                tool="health",
                environment=requested_environment,
                request_id=request_id,
                database=Config.DATABASE,
                schema="",
                query="",
            )
        finally:
            reset_request_id(request_token)
            reset_environment(environment_token)

    def list_databases(
        self,
        environment: str | None = None,
        timeout_seconds: int | None = None,
    ) -> ToolResponse:
        request_id, request_token, environment_token, start_time, requested_environment = self._begin_request("list_databases")
        try:
            payload = self.connector.list_databases(timeout_seconds=self._effective_timeout(timeout_seconds))
            response = self._response(
                tool="list_databases",
                environment=Config.DB_TYPE.upper(),
                success=True,
                request_id=request_id,
                start_time=start_time,
                data={
                    "current_environment": Config.DB_TYPE.upper(),
                    "count": payload.get("count", len(payload.get("databases", []))),
                    "databases": payload.get("databases", []),
                },
                metadata={"db_type": Config.DB_TYPE},
            )
            return self._finalize_request(
                response,
                tool="list_databases",
                environment=Config.DB_TYPE.upper(),
                request_id=request_id,
                database=Config.DATABASE,
                schema="",
                query="",
            )
        except Exception as exc:
            response = self._handle_connector_error(
                tool="list_databases",
                requested_environment=requested_environment,
                request_id=request_id,
                start_time=start_time,
                error=exc,
                message="Failed to list databases.",
            )
            return self._finalize_request(
                response,
                tool="list_databases",
                environment=requested_environment,
                request_id=request_id,
                database=Config.DATABASE,
                schema="",
                query="",
            )
        finally:
            reset_request_id(request_token)
            reset_environment(environment_token)

    def list_tables(
        self,
        database: str | None = None,
        schema: str | None = None,
        environment: str | None = None,
        timeout_seconds: int | None = None,
    ) -> ToolResponse:
        request_id, request_token, environment_token, start_time, requested_environment = self._begin_request("list_tables")
        try:
            target_database = database or Config.DATABASE
            payload = self.connector.list_tables(
                database=target_database,
                schema=schema,
                timeout_seconds=self._effective_timeout(timeout_seconds),
            )
            response = self._response(
                tool="list_tables",
                environment=Config.DB_TYPE.upper(),
                success=True,
                request_id=request_id,
                start_time=start_time,
                data={
                    "current_environment": Config.DB_TYPE.upper(),
                    "database": target_database,
                    "schema": schema or "",
                    "count": payload.get("count", len(payload.get("tables", []))),
                    "tables": payload.get("tables", []),
                },
                metadata={"db_type": Config.DB_TYPE},
            )
            return self._finalize_request(
                response,
                tool="list_tables",
                environment=Config.DB_TYPE.upper(),
                request_id=request_id,
                database=target_database,
                schema=schema or "",
                query="",
            )
        except Exception as exc:
            response = self._handle_connector_error(
                tool="list_tables",
                requested_environment=requested_environment,
                request_id=request_id,
                start_time=start_time,
                error=exc,
                message="Failed to list tables.",
            )
            return self._finalize_request(
                response,
                tool="list_tables",
                environment=requested_environment,
                request_id=request_id,
                database=database or Config.DATABASE,
                schema=schema or "",
                query="",
            )
        finally:
            reset_request_id(request_token)
            reset_environment(environment_token)

    def describe_table(
        self,
        database: str | None = None,
        table: str | None = None,
        schema: str | None = None,
        environment: str | None = None,
        timeout_seconds: int | None = None,
    ) -> ToolResponse:
        request_id, request_token, environment_token, start_time, requested_environment = self._begin_request("describe_table")
        try:
            payload = self.connector.describe_table(
                database=database or Config.DATABASE,
                table=table,
                schema=schema,
                timeout_seconds=self._effective_timeout(timeout_seconds),
            )

            if not payload.get("columns"):
                response = self._error(
                    tool="describe_table",
                    environment=Config.DB_TYPE.upper(),
                    code=ErrorCode.VALIDATION_FAILED,
                    message=f"Table {table!r} was not found in {payload.get('database', database or Config.DATABASE)!r}.",
                    request_id=request_id,
                    start_time=start_time,
                    retryable=False,
                    data={
                        "current_environment": Config.DB_TYPE.upper(),
                        "database": payload.get("database", database or Config.DATABASE),
                        "schema": payload.get("schema", schema or ""),
                        "table": table or "",
                        "column_count": 0,
                        "columns": [],
                    },
                )
                return self._finalize_request(
                    response,
                    tool="describe_table",
                    environment=Config.DB_TYPE.upper(),
                    request_id=request_id,
                    database=payload.get("database", database or Config.DATABASE),
                    schema=payload.get("schema", schema or ""),
                    query="",
                )

            response = self._response(
                tool="describe_table",
                environment=Config.DB_TYPE.upper(),
                success=True,
                request_id=request_id,
                start_time=start_time,
                data={
                    "current_environment": Config.DB_TYPE.upper(),
                    "database": payload.get("database", database or Config.DATABASE),
                    "schema": payload.get("schema", schema or ""),
                    "table": payload.get("table", table or ""),
                    "column_count": payload.get("column_count", len(payload.get("columns", []))),
                    "columns": payload.get("columns", []),
                },
                metadata={"db_type": Config.DB_TYPE},
            )
            return self._finalize_request(
                response,
                tool="describe_table",
                environment=Config.DB_TYPE.upper(),
                request_id=request_id,
                database=payload.get("database", database or Config.DATABASE),
                schema=payload.get("schema", schema or ""),
                query="",
            )
        except Exception as exc:
            response = self._handle_connector_error(
                tool="describe_table",
                requested_environment=requested_environment,
                request_id=request_id,
                start_time=start_time,
                error=exc,
                message="Failed to describe table.",
            )
            return self._finalize_request(
                response,
                tool="describe_table",
                environment=requested_environment,
                request_id=request_id,
                database=database or Config.DATABASE,
                schema=schema or "",
                query="",
            )
        finally:
            reset_request_id(request_token)
            reset_environment(environment_token)

    def execute_select_query(
        self,
        sql: str = "",
        query: str = "",
        database: str | None = None,
        schema: str | None = None,
        environment: str | None = None,
        timeout_seconds: int | None = None,
        max_rows: int | None = None,
        execution_mode: str = "",
    ) -> ToolResponse:
        request_id, request_token, environment_token, start_time, requested_environment = self._begin_request("execute_select_query")
        statement = sql or query
        try:
            effective_execution_mode = (execution_mode or Config.GLOBAL_EXECUTION_MODE).strip().lower() or Config.GLOBAL_EXECUTION_MODE
            if effective_execution_mode != "read_only":
                raise ConfigError("Only read_only execution is enabled. Agent requests cannot elevate execution mode.")
            if max_rows is not None and max_rows <= 0:
                raise ConfigError("max_rows must be greater than zero.")
            # Per-request limits may reduce, but never raise, the configured cap.
            row_limit = min(max_rows or Config.GLOBAL_MAX_ROWS, Config.GLOBAL_MAX_ROWS)
            # Policy validation happens before connector dispatch, so unsafe SQL
            # never reaches a database driver regardless of backend.
            valid, reason = validate_query(statement, execution_mode=effective_execution_mode)
            if not valid:
                response = self._error(
                    tool="execute_select_query",
                    environment=Config.DB_TYPE.upper(),
                    code=ErrorCode.QUERY_BLOCKED,
                    message=reason,
                    request_id=request_id,
                    start_time=start_time,
                    retryable=False,
                    data={
                        "current_environment": Config.DB_TYPE.upper(),
                        "row_count": 0,
                        "rows": [],
                    },
                )
                return self._finalize_request(
                    response,
                    tool="execute_select_query",
                    environment=Config.DB_TYPE.upper(),
                    request_id=request_id,
                    database=database or Config.DATABASE,
                    schema=schema or "",
                    query=statement,
                )

            target_database = database or Config.DATABASE
            payload = self.connector.execute_query(
                statement,
                database=target_database,
                timeout_seconds=self._effective_timeout(timeout_seconds),
                max_rows=row_limit,
                execution_mode=effective_execution_mode,
            )
            columns = payload.get("columns", [])
            rows = payload.get("rows", [])
            response = self._response(
                tool="execute_select_query",
                environment=Config.DB_TYPE.upper(),
                success=True,
                request_id=request_id,
                start_time=start_time,
                data={
                    "current_environment": Config.DB_TYPE.upper(),
                    "database": target_database,
                    "schema": schema or "",
                    "execution_mode": effective_execution_mode,
                    "row_limit": row_limit,
                    "row_count": len(rows),
                    "columns": columns,
                    "rows": rows,
                },
                metadata={
                    "db_type": Config.DB_TYPE,
                    "row_limit": row_limit,
                    "execution_mode": effective_execution_mode,
                },
            )
            return self._finalize_request(
                response,
                tool="execute_select_query",
                environment=Config.DB_TYPE.upper(),
                request_id=request_id,
                database=target_database,
                schema=schema or "",
                query=statement,
            )
        except Exception as exc:
            response = self._handle_connector_error(
                tool="execute_select_query",
                requested_environment=requested_environment,
                request_id=request_id,
                start_time=start_time,
                error=exc,
                message="Query execution failed.",
            )
            return self._finalize_request(
                response,
                tool="execute_select_query",
                environment=requested_environment,
                request_id=request_id,
                database=database or Config.DATABASE,
                schema=schema or "",
                query=statement,
            )
        finally:
            reset_request_id(request_token)
            reset_environment(environment_token)

    def config_diagnostics(self) -> ToolResponse:
        request_id, request_token, environment_token, start_time, requested_environment = self._begin_request("config_diagnostics")
        try:
            response = self._response(
                tool="config_diagnostics",
                environment=Config.DB_TYPE.upper() if Config.DB_TYPE else "UNCONFIGURED",
                success=True,
                request_id=request_id,
                start_time=start_time,
                data={
                    "current_environment": Config.DB_TYPE.upper() if Config.DB_TYPE else "UNCONFIGURED",
                    "configuration": Config.diagnostics(),
                },
                metadata={"db_type": Config.DB_TYPE},
            )
            return self._finalize_request(
                response,
                tool="config_diagnostics",
                environment=Config.DB_TYPE.upper() if Config.DB_TYPE else "UNCONFIGURED",
                request_id=request_id,
                database=Config.DATABASE,
                schema="",
                query="",
            )
        except Exception as exc:
            response = self._handle_connector_error(
                tool="config_diagnostics",
                requested_environment=requested_environment,
                request_id=request_id,
                start_time=start_time,
                error=exc,
                message="Configuration diagnostics failed.",
            )
            return self._finalize_request(
                response,
                tool="config_diagnostics",
                environment=requested_environment,
                request_id=request_id,
                database=Config.DATABASE,
                schema="",
                query="",
            )
        finally:
            reset_request_id(request_token)
            reset_environment(environment_token)


_QUERY_SERVICE: QueryService | None = None


def get_query_service() -> QueryService:
    global _QUERY_SERVICE
    # The service is reused during normal operation and explicitly discarded
    # by profile switching when a different connector is required.
    if _QUERY_SERVICE is None:
        _QUERY_SERVICE = QueryService()
    return _QUERY_SERVICE


def reset_query_service() -> None:
    """Close and discard the cached service after a configuration change."""

    global _QUERY_SERVICE
    if _QUERY_SERVICE is not None:
        _QUERY_SERVICE.connector.close()
    _QUERY_SERVICE = None
