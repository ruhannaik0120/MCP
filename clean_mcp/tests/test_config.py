"""Configuration tests for the MCP server."""

import pytest

from config import Config, ConfigError


def _configure_generic_settings(monkeypatch):
    """Install a valid baseline so each test isolates one configuration rule."""

    monkeypatch.setenv("DB_TYPE", "sqlserver")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_DATABASE", "devdb")
    monkeypatch.setenv("DB_USERNAME", "dev_user")
    monkeypatch.setenv("DB_PASSWORD", "dev_pass")
    monkeypatch.setenv("DB_CONNECTION_OPTIONS", '{"driver": "ODBC Driver 18 for SQL Server"}')
    monkeypatch.setenv("DB_TIMEOUT_SECONDS", "20")
    monkeypatch.setenv("DB_MAX_ROWS", "100")


def test_config_validation_passes_with_generic_settings(monkeypatch):
    _configure_generic_settings(monkeypatch)

    Config.load()
    Config.validate()

    profile = Config.connection_config()
    assert Config.DB_TYPE == "sqlserver"
    assert profile.db_type == "sqlserver"
    assert profile.host == "localhost"
    assert profile.database == "devdb"
    assert profile.connection_options == {"driver": "ODBC Driver 18 for SQL Server"}


def test_connection_config_has_no_execution_mode(monkeypatch):
    _configure_generic_settings(monkeypatch)

    Config.load()

    assert not hasattr(Config.connection_config(), "execution_mode")


def test_config_rejects_non_numeric_max_rows(monkeypatch):
    monkeypatch.setenv("DB_TYPE", "sqlserver")
    monkeypatch.setenv("DB_MAX_ROWS", "abc")

    with pytest.raises(ConfigError, match="Expected an integer value"):
        Config.load()


def test_invalid_connection_options_raise_structured_error(monkeypatch):
    monkeypatch.setenv("DB_TYPE", "sqlserver")
    monkeypatch.setenv("DB_CONNECTION_OPTIONS", "not-json")

    with pytest.raises(ConfigError, match="valid JSON"):
        Config.load()


def test_config_rejects_unsupported_db_type(monkeypatch):
    monkeypatch.setenv("DB_TYPE", "oracle")
    monkeypatch.setenv("DB_HOST", "localhost")

    Config.load()

    with pytest.raises(ConfigError, match="DB_TYPE must be one of"):
        Config.validate()


def test_config_allows_demo_without_host(monkeypatch):
    monkeypatch.setenv("DB_TYPE", "demo")
    monkeypatch.setenv("DB_HOST", "")
    monkeypatch.setenv("DB_DATABASE", "qa_demo")

    Config.load()
    Config.validate()

    assert Config.DB_TYPE == "demo"


def test_config_diagnostics_redacts_password(monkeypatch):
    monkeypatch.setenv("DB_TYPE", "postgresql")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PASSWORD", "secret-value")
    monkeypatch.setenv("DB_CONNECTION_OPTIONS", '{"port":5432,"password":"nested-secret"}')

    Config.load()
    diagnostics = Config.diagnostics()

    assert diagnostics["password_present"] is True
    assert "secret-value" not in str(diagnostics)
    assert diagnostics["connection_options"]["password"] == "[REDACTED]"
    assert "host" not in diagnostics


def test_diagnostics_redact_connection_strings_and_private_keys(monkeypatch):
    monkeypatch.setenv("DB_TYPE", "postgresql")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv(
        "DB_CONNECTION_OPTIONS",
        '{"connection_string":"Server=private","private_key":"key-material"}',
    )

    Config.load()
    diagnostics = Config.diagnostics()

    assert diagnostics["connection_options"]["connection_string"] == "[REDACTED]"
    assert diagnostics["connection_options"]["private_key"] == "[REDACTED]"
    assert "key-material" not in str(diagnostics)
