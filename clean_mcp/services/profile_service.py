"""Runtime connection-profile discovery and atomic switching."""

from __future__ import annotations

import json
import os
from threading import RLock
from typing import Any

from config import Config, ConfigError
from connectors.factory import SUPPORTED_CONNECTORS
from services.query_service import get_query_service, reset_query_service

_PROFILE_ENV_KEYS = {
    "db_type": "DB_TYPE",
    "host": "DB_HOST",
    "database": "DB_DATABASE",
    "username": "DB_USERNAME",
    "password": "DB_PASSWORD",
    "connection_options": "DB_CONNECTION_OPTIONS",
    "timeout_seconds": "DB_TIMEOUT_SECONDS",
    "max_rows": "DB_MAX_ROWS",
    "execution_mode": "DB_EXECUTION_MODE",
}
# A re-entrant lock prevents two agent requests from replacing process-wide
# connection settings at the same time.
_switch_lock = RLock()
_active_profile = os.getenv("DB_ACTIVE_PROFILE", "default").strip() or "default"


def _profiles() -> dict[str, dict[str, Any]]:
    """Parse named profiles from JSON without exposing them outside this module."""

    raw = os.getenv("DB_PROFILES_JSON", "").strip()
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ConfigError("DB_PROFILES_JSON must be valid JSON.") from exc
    if not isinstance(parsed, dict):
        raise ConfigError("DB_PROFILES_JSON must be a JSON object keyed by profile name.")

    profiles: dict[str, dict[str, Any]] = {}
    for name, value in parsed.items():
        normalized_name = str(name).strip().lower()
        if not normalized_name or not isinstance(value, dict):
            raise ConfigError("Every connection profile must have a name and JSON object value.")
        profiles[normalized_name] = value
    return profiles


def _safe_profile(name: str, profile: dict[str, Any]) -> dict[str, Any]:
    """Convert a profile into agent-safe metadata with no credential values."""

    # Return presence flags rather than credential values. The agent can reason
    # about available systems without ever receiving connection secrets.
    return {
        "name": name,
        "db_type": str(profile.get("db_type", "")).lower(),
        "host_present": bool(profile.get("host")),
        "database": str(profile.get("database", "")),
        "username_present": bool(profile.get("username")),
        "password_present": bool(profile.get("password")),
        "active": name == _active_profile,
    }


def list_connection_profiles() -> dict[str, Any]:
    """Return non-secret metadata for configured connection profiles."""

    profiles = _profiles()
    return {
        "active_profile": _active_profile,
        "count": len(profiles),
        "profiles": [_safe_profile(name, value) for name, value in sorted(profiles.items())],
        "supported_connectors": sorted(SUPPORTED_CONNECTORS),
    }


def _profile_environment(profile: dict[str, Any]) -> dict[str, str]:
    """Translate profile fields into the environment keys consumed by Config."""

    db_type = str(profile.get("db_type", "")).strip().lower()
    if db_type not in SUPPORTED_CONNECTORS:
        supported = ", ".join(sorted(SUPPORTED_CONNECTORS))
        raise ConfigError(f"Profile db_type must be one of: {supported}.")

    values: dict[str, str] = {}
    # Only fields explicitly present in the selected profile are transferred.
    for field, env_key in _PROFILE_ENV_KEYS.items():
        if field not in profile:
            continue
        value = profile[field]
        if field == "connection_options":
            if not isinstance(value, dict):
                raise ConfigError("connection_options must be a JSON object.")
            values[env_key] = json.dumps(value)
        else:
            values[env_key] = str(value)
    values["DB_TYPE"] = db_type
    return values


def switch_connection_profile(name: str, *, confirm: bool = False, test_connection: bool = True) -> dict[str, Any]:
    """Atomically switch the process to a named profile and optionally verify it."""

    global _active_profile
    normalized_name = name.strip().lower()
    if not confirm:
        raise ConfigError("Profile switch requires explicit user approval: call again with confirm=true.")

    profiles = _profiles()
    if normalized_name not in profiles:
        available = ", ".join(sorted(profiles)) or "none"
        raise ConfigError(f"Unknown connection profile {normalized_name!r}. Available profiles: {available}.")

    new_values = _profile_environment(profiles[normalized_name])
    affected_keys = set(_PROFILE_ENV_KEYS.values()) | {"DB_ACTIVE_PROFILE"}
    # Snapshot every affected value before mutation. This snapshot is the
    # transaction boundary used to restore a known-good profile on failure.
    previous = {key: os.environ.get(key) for key in affected_keys}
    previous_profile = _active_profile

    with _switch_lock:
        try:
            # Clear old fields first so omitted values cannot leak from the
            # previous backend into the newly selected connector.
            for key in _PROFILE_ENV_KEYS.values():
                os.environ.pop(key, None)
            os.environ.update(new_values)
            os.environ["DB_ACTIVE_PROFILE"] = normalized_name
            Config.validate()
            # QueryService owns a connector instance, so discarding the cached
            # service is what makes the next call build the selected backend.
            reset_query_service()

            connection_result: dict[str, Any] = {}
            if test_connection:
                # A switch is committed only after the target system proves it
                # is reachable. The resulting metadata is safe to show an agent.
                response = get_query_service().test_connection(database=Config.DATABASE).to_dict()
                if not response["success"]:
                    detail = response.get("error", {}).get("detail", "Connection test failed.")
                    raise ConfigError(detail)
                connection_result = {
                    "connection_status": response.get("connection_status", "connected"),
                    "server_information": response.get("server_information", {}),
                }

            _active_profile = normalized_name
            return {
                "switched": True,
                "active_profile": normalized_name,
                "db_type": Config.DB_TYPE,
                "database": Config.DATABASE,
                **connection_result,
            }
        except Exception:
            # Any validation, driver, authentication, or network failure rolls
            # back both environment state and the cached connector instance.
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
            _active_profile = previous_profile
            Config.load()
            reset_query_service()
            raise
