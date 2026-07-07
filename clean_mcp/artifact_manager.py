"""Runtime helpers for execution artifacts and logs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from config import Config


def ensure_runtime_directories() -> None:
    """Create the configured artifact directories when they do not exist."""

    for path in (Config.OUTPUT_DIR, Config.EXECUTION_ARTIFACTS_DIR, Config.LOG_ARTIFACTS_DIR):
        path.mkdir(parents=True, exist_ok=True)


def get_log_file_path() -> Path:
    """Return the stable path used by the framework's file log handler."""

    ensure_runtime_directories()
    return Config.LOG_ARTIFACTS_DIR / "mcp_execution_framework.log"


def save_execution_artifact(request_id: str, payload: dict[str, Any]) -> Path:
    """Persist one structured MCP response as request-scoped JSON evidence."""

    ensure_runtime_directories()
    # Request IDs make each evidence file directly traceable to its response
    # and structured log entries during audits or demonstrations.
    artifact_path = Config.EXECUTION_ARTIFACTS_DIR / f"{request_id}.json"
    artifact_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return artifact_path
