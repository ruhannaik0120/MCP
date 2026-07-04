"""Backend-specific configuration mapping tests that require no live secrets."""

from config import Config
from connectors.mysql.connector import MySQLConnector
from connectors.postgresql.connector import PostgreSQLConnector
from connectors.snowflake.connector import SnowflakeConnector


def _configure(monkeypatch, db_type: str, options: str = "{}") -> None:
    monkeypatch.setenv("DB_TYPE", db_type)
    monkeypatch.setenv("DB_HOST", "db.example.test")
    monkeypatch.setenv("DB_DATABASE", "qa_demo")
    monkeypatch.setenv("DB_USERNAME", "qa_user")
    monkeypatch.setenv("DB_PASSWORD", "qa_password")
    monkeypatch.setenv("DB_CONNECTION_OPTIONS", options)
    monkeypatch.setenv("DB_TIMEOUT_SECONDS", "12")
    monkeypatch.setenv("DB_MAX_ROWS", "100")
    monkeypatch.setenv("DB_EXECUTION_MODE", "read_only")
    Config.load()


def test_mysql_connection_arguments(monkeypatch):
    _configure(monkeypatch, "mysql", '{"port":3307,"ssl_disabled":true}')

    kwargs = MySQLConnector()._connection_kwargs(Config.connection_config(), "qa_demo")

    assert kwargs == {
        "host": "db.example.test",
        "port": 3307,
        "user": "qa_user",
        "password": "qa_password",
        "connection_timeout": 12,
        "database": "qa_demo",
        "ssl_disabled": True,
    }


def test_postgresql_connection_arguments(monkeypatch):
    _configure(monkeypatch, "postgresql", '{"port":5433,"sslmode":"require"}')

    kwargs = PostgreSQLConnector()._connection_kwargs(Config.connection_config(), "qa_demo")

    assert kwargs == {
        "host": "db.example.test",
        "port": 5433,
        "dbname": "qa_demo",
        "user": "qa_user",
        "password": "qa_password",
        "connect_timeout": 12,
        "sslmode": "require",
    }


def test_snowflake_connection_arguments(monkeypatch):
    _configure(
        monkeypatch,
        "snowflake",
        '{"warehouse":"COMPUTE_WH","schema":"PUBLIC","role":"QA_ROLE"}',
    )

    kwargs = SnowflakeConnector()._connection_kwargs(Config.connection_config(), "QA_DEMO")

    assert kwargs == {
        "account": "db.example.test",
        "user": "qa_user",
        "password": "qa_password",
        "login_timeout": 12,
        "database": "QA_DEMO",
        "schema": "PUBLIC",
        "warehouse": "COMPUTE_WH",
        "role": "QA_ROLE",
    }
