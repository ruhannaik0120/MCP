"""Structured logging for the MCP execution framework.

This module owns request-scoped log context, JSON formatting, and handler
registration. It should not know anything about SQL semantics or MCP tools.
"""

from __future__ import annotations

import contextvars
import json
import logging
from pathlib import Path

from artifact_manager import get_log_file_path
from config import Config

Config.load()

LOG_DIR = Config.LOG_ARTIFACTS_DIR
LOG_DIR.mkdir(parents=True, exist_ok=True)

_request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")
_environment_var: contextvars.ContextVar[str] = contextvars.ContextVar("environment", default="-")


class _RequestContextFilter(logging.Filter):
    """Populate request-scoped context on every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        # Libraries may emit logs without our custom fields; defaults keep every
        # record valid JSON while request-scoped calls receive correlation data.
        if not hasattr(record, "request_id"):
            record.request_id = _request_id_var.get()
        if not hasattr(record, "environment"):
            record.environment = _environment_var.get()
        if not hasattr(record, "success"):
            record.success = None
        if not hasattr(record, "execution_time_ms"):
            record.execution_time_ms = None
        return True


class _JsonFormatter(logging.Formatter):
    """Emit machine-readable logs with the fields useful for audit trails."""

    def format(self, record: logging.LogRecord) -> str:
        # JSON logs can be searched, correlated, or ingested by a reporting
        # platform without parsing human-formatted text.
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "module": record.module,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
            "environment": getattr(record, "environment", "-"),
            "success": getattr(record, "success", None),
            "execution_time_ms": getattr(record, "execution_time_ms", None),
        }

        for key in ("tool", "database", "status", "event", "error_code"):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value

        return json.dumps(payload, default=str)


logger = logging.getLogger("mcp_execution_framework")
logger.setLevel(getattr(logging, Config.LOG_LEVEL, logging.INFO))
logger.propagate = False

if not logger.handlers:
    formatter = _JsonFormatter()

    file_handler = logging.FileHandler(get_log_file_path(), encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.addFilter(_RequestContextFilter())

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.addFilter(_RequestContextFilter())

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


def set_request_id(request_id: str) -> contextvars.Token[str]:
    return _request_id_var.set(request_id)


def reset_request_id(token: contextvars.Token[str]) -> None:
    _request_id_var.reset(token)


def set_environment(environment: str) -> contextvars.Token[str]:
    return _environment_var.set(environment)


def reset_environment(token: contextvars.Token[str]) -> None:
    _environment_var.reset(token)
