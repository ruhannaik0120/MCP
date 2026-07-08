"""Backend-specific configuration mapping tests that require no live secrets."""

from contextlib import contextmanager

import pytest

from config import Config
from connectors.mysql.connector import MySQLConnector
from connectors.postgresql.connector import PostgreSQLConnector
from connectors.snowflake.connector import SnowflakeConnector


# Build profiles consistently so assertions focus on driver argument mapping.
def _configure(monkeypatch, db_type: str, options: str = "{}") -> None:
    monkeypatch.setenv("DB_TYPE", db_type)
    monkeypatch.setenv("DB_HOST", "db.example.test")
    monkeypatch.setenv("DB_DATABASE", "qa_demo")
    monkeypatch.setenv("DB_USERNAME", "qa_user")
    monkeypatch.setenv("DB_PASSWORD", "qa_password")
    monkeypatch.setenv("DB_CONNECTION_OPTIONS", options)
    monkeypatch.setenv("DB_TIMEOUT_SECONDS", "12")
    monkeypatch.setenv("DB_MAX_ROWS", "100")
    Config.load()


# Each backend receives the expected driver keywords, defaults, and options.
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


# Transaction doubles prove commit behavior without touching live databases.
class _WriteCursor:
    """Represent a write cursor with a deterministic affected-row count."""
    description = None
    rowcount = 2

    def execute(self, query):
        self.query = query

    def close(self):
        return None


class _WriteConnection:
    """Record whether a transactional connector commits an accepted write."""
    def __init__(self):
        self.cursor_object = _WriteCursor()
        self.committed = False

    def cursor(self):
        return self.cursor_object

    def commit(self):
        self.committed = True


@pytest.mark.parametrize(
    ("db_type", "connector_class"),
    [
        ("mysql", MySQLConnector),
        ("postgresql", PostgreSQLConnector),
        ("snowflake", SnowflakeConnector),
    ],
)
# MySQL, PostgreSQL, and Snowflake must commit successful write statements.
def test_transactional_connectors_commit_writes(monkeypatch, db_type, connector_class):
    _configure(monkeypatch, db_type)
    connector = connector_class()
    connection = _WriteConnection()

    @contextmanager
    def fake_connection(*args, **kwargs):
        yield connection

    monkeypatch.setattr(connector, "_connection", fake_connection)

    result = connector.execute_query(
        "UPDATE demo_items SET status = 'verified'",
    )

    assert connection.committed is True
    assert result["rows_affected"] == 2
