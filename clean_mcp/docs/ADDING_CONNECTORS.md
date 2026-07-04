# Adding A Connector

The extension boundary is deliberately narrow: a new backend implements `DatabaseConnector`, exports `Connector`, and receives one registry entry. MCP tools, orchestration, response models, logging, artifacts, profile switching, and approval behavior do not change.

## Contract

Create `connectors/<name>/connector.py` and implement:

```python
class ExampleConnector(DatabaseConnector):
    def connect(self, database=None, timeout_seconds=None): ...
    def test_connection(self, database=None, timeout_seconds=None): ...
    def health_check(self, database=None, timeout_seconds=None): ...
    def list_databases(self, timeout_seconds=None): ...
    def list_tables(self, database=None, schema=None, timeout_seconds=None): ...
    def describe_table(self, database=None, table=None, schema=None, timeout_seconds=None): ...
    def execute_query(self, query, *, database=None, timeout_seconds=None, max_rows=None, execution_mode=None): ...
    def close(self): ...

Connector = ExampleConnector
```

Then register only the module path in `SUPPORTED_CONNECTORS` inside `connectors/factory.py`.

## Rules

1. Import the vendor driver lazily and raise `ConfigError` with the exact package to install.
2. Read settings only through `Config.connection_config()`.
3. Keep credentials out of exceptions, logs, metadata, and responses.
4. Parameterize metadata filters such as schema/table names.
5. Enforce timeout and row-limit arguments using native driver features where possible.
6. Return dictionaries containing connector metadata plus stable keys expected by `QueryService`.
7. Close cursors and connections in `finally` blocks or context managers.
8. Never import vendor drivers from `server.py`, `tools/`, or `services/`.
9. Do not add connector-specific branches to MCP tools.
10. Add unit tests with fake driver objects and an opt-in integration test.

## Required Tests

- Factory creates the connector and rejects unknown names.
- Missing driver produces an actionable configuration error.
- Connection arguments map correctly without leaking secrets.
- Metadata methods shape rows consistently.
- Query row limiting is correct for the backend dialect.
- Connection and cursor close on success and failure.
- Profile switching selects the connector and rolls back after a failed health check.
- `tests/test_architecture.py` continues to pass.

## Definition Of Done

A connector is implemented when automated tests pass. It is verified for an environment only after the opt-in live check succeeds and the evidence contains no secrets. Update the support matrix with `implemented`, `automated-tested`, and `live-verified` as separate claims.
