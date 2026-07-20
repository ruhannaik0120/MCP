"""Tests for the offline demo connector."""

from connectors.demo.connector import DemoConnector


# region Function: Test demo connector lists sample databases
def test_demo_connector_lists_sample_databases():
    connector = DemoConnector()
    payload = connector.list_databases()

    assert payload["count"] >= 1
    assert payload["databases"][0]["name"] == "qa_demo"
# endregion Function: Test demo connector lists sample databases


# region Function: Test demo connector executes health check query
def test_demo_connector_executes_health_check_query():
    connector = DemoConnector()
    payload = connector.execute_query("SELECT 1 AS health_check")

    assert payload["columns"] == ["health_check"]
    assert payload["rows"][0]["health_check"] == 1
# endregion Function: Test demo connector executes health check query


# region Function: Test demo connector describes sample table
def test_demo_connector_describes_sample_table():
    connector = DemoConnector()
    payload = connector.describe_table(database="qa_demo", table="demo_items")

    assert payload["column_count"] == 3
    assert payload["columns"][0]["COLUMN_NAME"] == "item_id"
# endregion Function: Test demo connector describes sample table
