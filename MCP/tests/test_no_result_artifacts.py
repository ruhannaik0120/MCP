"""Verify that MCP execution does not create persistent result artifacts."""

# region Imports and module setup
from config import Config
from services.query_service import QueryService
# endregion Imports and module setup


# region Class: Connector
class _Connector:
    """Return one deterministic query result without external infrastructure."""

    # region Function: Execute query
    def execute_query(self, query, *, database=None, timeout_seconds=None, max_rows=None):
        """Handle execute query."""
        return {"columns": ["value"], "rows": [{"value": 1}], "rows_affected": 1}
    # endregion Function: Execute query
# endregion Class: Connector


# region Function: Test execution does not write result artifacts
def test_execution_does_not_write_result_artifacts(tmp_path, monkeypatch):
    """Verify execution does not write result artifacts."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DB_TYPE", "demo")
    monkeypatch.setenv("DB_DATABASE", "qa_demo")
    Config.load()

    response = QueryService(_Connector()).execute_query(sql="SELECT 1").to_dict()

    assert response["success"] is True
    assert list(tmp_path.rglob("*.json")) == []
# endregion Function: Test execution does not write result artifacts
