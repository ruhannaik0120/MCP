"""Verify that logs and request evidence stay under configured artifact paths."""

from pathlib import Path
import json

from artifact_manager import get_log_file_path, save_execution_artifact
from config import Config


# Persistence must produce parseable JSON at the request-scoped evidence path.
def test_execution_artifact_is_written_under_runtime_artifacts(tmp_path, monkeypatch):
    monkeypatch.setattr(Config, "OUTPUT_DIR", tmp_path / "artifacts", raising=False)
    monkeypatch.setattr(Config, "EXECUTION_ARTIFACTS_DIR", tmp_path / "artifacts" / "executions", raising=False)
    monkeypatch.setattr(Config, "LOG_ARTIFACTS_DIR", tmp_path / "artifacts" / "logs", raising=False)

    artifact_path = save_execution_artifact("req-123", {"tool": "execute_select_query", "status": "success"})

    assert artifact_path.parent == Config.EXECUTION_ARTIFACTS_DIR
    assert artifact_path.exists()
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["tool"] == "execute_select_query"
    assert payload["status"] == "success"


# Log path lookup also creates the dedicated directory when necessary.
def test_log_file_path_is_under_runtime_artifacts(tmp_path, monkeypatch):
    monkeypatch.setattr(Config, "OUTPUT_DIR", tmp_path / "artifacts", raising=False)
    monkeypatch.setattr(Config, "EXECUTION_ARTIFACTS_DIR", tmp_path / "artifacts" / "executions", raising=False)
    monkeypatch.setattr(Config, "LOG_ARTIFACTS_DIR", tmp_path / "artifacts" / "logs", raising=False)

    log_path = get_log_file_path()

    assert log_path.parent == Config.LOG_ARTIFACTS_DIR
    assert log_path.name == "mcp_execution_framework.log"
