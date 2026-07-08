"""Generic runtime configuration for the MCP execution framework."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import ClassVar

from dotenv import load_dotenv

from connectors.factory import SUPPORTED_CONNECTORS

load_dotenv()

_SENSITIVE_OPTION_KEYS = frozenset(
    {
        "password",
        "secret",
        "token",
        "private_key",
        "private_key_passphrase",
        "access_token",
        "connection_string",
        "connectionstring",
    }
)


def _normalize_text(value: str | None, default: str = "") -> str:
    """Trim an optional string and substitute a default for blank values."""

    if value is None:
        return default
    return value.strip() or default


def _as_int(value: str | None, default: int) -> int:
    """Parse an integer environment value with a clear configuration error."""

    if value is None or not value.strip():
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ConfigError(f"Expected an integer value, got: {value!r}") from exc


def _as_dict(value: str | None) -> dict[str, object]:
    """Parse JSON connection options and require an object-shaped value."""

    if value is None or not value.strip():
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ConfigError("DB_CONNECTION_OPTIONS must be valid JSON.") from exc
    if not isinstance(parsed, dict):
        raise ConfigError("DB_CONNECTION_OPTIONS must decode to a JSON object.")
    return parsed


def _redact_connection_options(options: dict[str, object]) -> dict[str, object]:
    """Copy connection options while replacing recognized secret values."""

    # Diagnostics may be shown to an AI client, so secret-like option values
    # are replaced before configuration leaves the process boundary.
    redacted: dict[str, object] = {}
    for key, value in options.items():
        normalized_key = key.lower().replace("-", "_").replace(" ", "_")
        if normalized_key in _SENSITIVE_OPTION_KEYS:
            redacted[key] = "[REDACTED]"
        else:
            redacted[key] = value
    return redacted


class ConfigError(ValueError):
    """Raised when runtime configuration fails validation."""


@dataclass(frozen=True, slots=True)
class ConnectionConfig:
    """Resolved generic connection settings for the active database."""

    db_type: str
    host: str
    database: str
    username: str = ""
    password: str = ""
    connection_options: dict[str, object] | None = None
    timeout_seconds: int = 30
    max_rows: int = 500

    def safe_dict(self) -> dict[str, object]:
        """Return this connection profile in a form safe for agent responses."""

        return {
            "db_type": self.db_type,
            "host": "[CONFIGURED]" if self.host else "",
            "database": self.database,
            "username": "[CONFIGURED]" if self.username else "",
            "password": "",
            "connection_options": _redact_connection_options(self.connection_options or {}),
            "timeout_seconds": self.timeout_seconds,
            "max_rows": self.max_rows,
        }


class Config:
    """Central configuration surface for the MCP server."""

    DB_TYPE: ClassVar[str] = ""
    HOST: ClassVar[str] = ""
    DATABASE: ClassVar[str] = ""
    USERNAME: ClassVar[str] = ""
    PASSWORD: ClassVar[str] = ""
    CONNECTION_OPTIONS: ClassVar[dict[str, object]] = {}
    GLOBAL_MAX_ROWS: ClassVar[int] = 500
    GLOBAL_TIMEOUT_SECONDS: ClassVar[int] = 30
    LOG_LEVEL: ClassVar[str] = "INFO"

    @classmethod
    def load(cls) -> "Config":
        """Refresh process-wide settings from environment variables."""

        # All environment access is centralized here so connectors receive one
        # consistent snapshot instead of interpreting raw strings themselves.
        cls.DB_TYPE = _normalize_text(os.getenv("DB_TYPE")).lower()
        cls.HOST = _normalize_text(os.getenv("DB_HOST"))
        cls.DATABASE = _normalize_text(os.getenv("DB_DATABASE"))
        cls.USERNAME = _normalize_text(os.getenv("DB_USERNAME"))
        cls.PASSWORD = os.getenv("DB_PASSWORD", "")
        cls.CONNECTION_OPTIONS = _as_dict(os.getenv("DB_CONNECTION_OPTIONS"))
        cls.GLOBAL_MAX_ROWS = _as_int(os.getenv("DB_MAX_ROWS"), 500)
        cls.GLOBAL_TIMEOUT_SECONDS = _as_int(os.getenv("DB_TIMEOUT_SECONDS"), 30)
        cls.LOG_LEVEL = _normalize_text(os.getenv("LOG_LEVEL"), "INFO").upper()
        return cls

    @classmethod
    def validate(cls) -> "Config":
        """Load settings and reject all detected configuration problems."""

        cls.load()

        # Collect every problem and report them together. This makes setup much
        # faster than failing one environment variable at a time.
        errors: list[str] = []
        if not cls.DB_TYPE:
            errors.append("DB_TYPE is required.")
        elif cls.DB_TYPE not in SUPPORTED_CONNECTORS:
            supported = ", ".join(sorted(SUPPORTED_CONNECTORS))
            errors.append(f"DB_TYPE must be one of: {supported}.")

        if cls.DB_TYPE != "demo" and not cls.HOST:
            errors.append("DB_HOST is required for the selected connector.")

        if cls.LOG_LEVEL not in logging._nameToLevel:
            errors.append("LOG_LEVEL must be a valid logging level.")
        if cls.GLOBAL_MAX_ROWS <= 0:
            errors.append("DB_MAX_ROWS must be greater than zero.")
        elif cls.GLOBAL_MAX_ROWS > 10_000:
            errors.append("DB_MAX_ROWS must not exceed 10000.")
        if cls.GLOBAL_TIMEOUT_SECONDS <= 0:
            errors.append("DB_TIMEOUT_SECONDS must be greater than zero.")

        errors.extend(cls._validate_connection_options())
        errors.extend(cls._validate_connector_requirements())

        if errors:
            raise ConfigError("Configuration validation failed: " + " ".join(errors))

        return cls

    @classmethod
    def _validate_connection_options(cls) -> list[str]:
        """Validate generic options shared across connector implementations."""

        errors: list[str] = []
        port = cls.CONNECTION_OPTIONS.get("port")
        if port is not None:
            try:
                int(port)
            except (TypeError, ValueError):
                errors.append("DB_CONNECTION_OPTIONS.port must be an integer.")
        return errors

    @classmethod
    def _validate_connector_requirements(cls) -> list[str]:
        """Apply only the required fields that vary by selected backend."""

        errors: list[str] = []
        if cls.DB_TYPE == "sqlserver" and not cls.DATABASE:
            errors.append("DB_DATABASE is required for the SQL Server connector.")
        if cls.DB_TYPE == "snowflake" and not cls.USERNAME:
            errors.append("DB_USERNAME is required for the Snowflake connector.")
        if cls.DB_TYPE == "demo" and not cls.DATABASE:
            cls.DATABASE = "qa_demo"
        return errors

    @classmethod
    def connection_config(cls) -> ConnectionConfig:
        """Build the neutral configuration object consumed by connectors."""

        if not cls.DB_TYPE:
            cls.load()
        # Connectors receive one neutral profile instead of reading environment
        # variables independently, which keeps backend logic interchangeable.
        return ConnectionConfig(
            db_type=cls.DB_TYPE,
            host=cls.HOST,
            database=cls.DATABASE,
            username=cls.USERNAME,
            password=cls.PASSWORD,
            connection_options=dict(cls.CONNECTION_OPTIONS),
            timeout_seconds=cls.GLOBAL_TIMEOUT_SECONDS,
            max_rows=cls.GLOBAL_MAX_ROWS,
        )

    @classmethod
    def as_dict(cls) -> dict[str, object]:
        """Return redacted effective settings for internal structured output."""

        if not cls.DB_TYPE:
            cls.load()

        return {
            "db_type": cls.DB_TYPE,
            "host": "[CONFIGURED]" if cls.HOST else "",
            "database": cls.DATABASE,
            "username": "[CONFIGURED]" if cls.USERNAME else "",
            "password": "",
            "connection_options": _redact_connection_options(dict(cls.CONNECTION_OPTIONS)),
            "global_max_rows": cls.GLOBAL_MAX_ROWS,
            "global_timeout_seconds": cls.GLOBAL_TIMEOUT_SECONDS,
            "log_level": cls.LOG_LEVEL,
        }

    @classmethod
    def diagnostics(cls) -> dict[str, object]:
        """Return troubleshooting metadata without returning credential values."""

        if not cls.DB_TYPE:
            cls.load()

        return {
            "db_type": cls.DB_TYPE or "(not set)",
            "host_present": bool(cls.HOST),
            "database": cls.DATABASE,
            "username_present": bool(cls.USERNAME),
            "password_present": bool(cls.PASSWORD),
            "timeout_seconds": cls.GLOBAL_TIMEOUT_SECONDS,
            "max_rows": cls.GLOBAL_MAX_ROWS,
            "connection_options": _redact_connection_options(dict(cls.CONNECTION_OPTIONS)),
            "supported_connectors": sorted(SUPPORTED_CONNECTORS),
        }

    @classmethod
    def redact_text(cls, value: object) -> str:
        """Remove configured credential values from an external error message."""

        text = str(value)
        secrets = [cls.PASSWORD]
        for key, option_value in cls.CONNECTION_OPTIONS.items():
            normalized_key = key.lower().replace("-", "_").replace(" ", "_")
            if normalized_key in _SENSITIVE_OPTION_KEYS:
                secrets.append(str(option_value))
        for secret in secrets:
            if secret:
                text = text.replace(secret, "[REDACTED]")
        return text


# Load defaults at import time; startup validation still performs the strict gate.
Config.load()
