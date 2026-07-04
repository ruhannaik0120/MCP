"""Tests for safe runtime connection-profile switching."""

import json

import pytest

from config import Config, ConfigError
from services import profile_service


@pytest.fixture
def profiles(monkeypatch):
    payload = {
        "demo-one": {"db_type": "demo", "database": "qa_demo"},
        "demo-two": {"db_type": "demo", "database": "sales"},
    }
    monkeypatch.setenv("DB_PROFILES_JSON", json.dumps(payload))
    monkeypatch.setenv("DB_TYPE", "demo")
    monkeypatch.setenv("DB_DATABASE", "qa_demo")
    monkeypatch.setattr(profile_service, "_active_profile", "default")
    Config.load()
    return payload


def test_list_profiles_never_returns_credentials(monkeypatch, profiles):
    profiles["demo-one"]["password"] = "top-secret"
    monkeypatch.setenv("DB_PROFILES_JSON", json.dumps(profiles))

    result = profile_service.list_connection_profiles()

    assert result["count"] == 2
    assert "top-secret" not in str(result)
    assert result["profiles"][0]["password_present"] is True


def test_switch_requires_explicit_confirmation(profiles):
    with pytest.raises(ConfigError, match="explicit user approval"):
        profile_service.switch_connection_profile("demo-two")


def test_switch_rebuilds_service_and_changes_active_database(profiles):
    result = profile_service.switch_connection_profile("demo-two", confirm=True)

    assert result["switched"] is True
    assert result["active_profile"] == "demo-two"
    assert result["database"] == "sales"
    assert result["connection_status"] == "connected"
    assert Config.DATABASE == "sales"


def test_failed_switch_restores_previous_configuration(monkeypatch, profiles):
    monkeypatch.setenv(
        "DB_PROFILES_JSON",
        json.dumps({**profiles, "broken": {"db_type": "postgresql", "database": "missing-host"}}),
    )

    with pytest.raises(ConfigError, match="DB_HOST"):
        profile_service.switch_connection_profile("broken", confirm=True)

    assert Config.DB_TYPE == "demo"
    assert Config.DATABASE == "qa_demo"
    assert profile_service.list_connection_profiles()["active_profile"] == "default"
