# MCP Database Execution Framework

Reusable, AI-client-agnostic MCP server for executing approved SQL commands through named database profiles. It supports SQL Server, PostgreSQL, MySQL, Snowflake, and an offline demo connector through one stable tool and response contract.

## Responsibility Boundary

`clean_mcp` is only the database execution framework. It does not read Jira, interpret tickets, generate QA plans, manage approval logs, or write final PoC result files.

```text
Jira / requirements
        |
        v
AI agent: context, QA plan, SQL generation, approvals, run files
        |
        v
clean_mcp: profile selection, request validation, execution, response
        |
        v
SQL Server | PostgreSQL | MySQL | Snowflake | future connectors
```

The outer agent workflow owns `ticket_context.md`, `qa_plan.md`, `generated_queries.sql`, `approval_log.md`, `run_log.md`, and `execution_result.json` under `poc_runs/<ticket_id>/`.

## Capabilities

- Standard MCP `stdio` transport for compatible AI clients.
- Connector factory and stable `DatabaseConnector` extension contract.
- Approval-gated named profile switching with connection verification and rollback.
- Approved SQL command execution, including reads, writes, and DDL permitted by the database account.
- One-statement request validation, bounded returned rows, and timeouts.
- Structured responses, errors, request IDs, duration, profile metadata, and result data.
- Credential redaction in diagnostics and errors.
- Technical console logging only; no MCP-owned execution-result artifacts.
- Architecture tests that keep vendor drivers inside `connectors/`.

## MCP Tools

| Tool | Purpose |
|---|---|
| `tool_list_connection_profiles` | Lists profile names and safe metadata without credentials. |
| `tool_switch_connection_profile` | Requires `confirm=true`, verifies the target, and rolls back on failure. |
| `tool_config_diagnostics` | Returns redacted effective configuration. |
| `tool_test_connection` | Performs a real connection test and returns safe server metadata. |
| `tool_health` | Checks the active connector's operational status. |
| `tool_list_databases` | Lists visible databases. |
| `tool_list_tables` | Lists tables/views by database and schema. |
| `tool_describe_table` | Returns normalized column metadata. |
| `tool_execute_query` | Primary tool for one approved SQL command/query. |
| `tool_execute_select_query` | Deprecated compatibility alias for `tool_execute_query`. |

The deprecated alias uses the same generic execution path and does not impose different SQL behavior.

## Configuration

Copy the example and keep real credentials only in the ignored `.env` file:

```powershell
Copy-Item .\clean_mcp\.env.example .\clean_mcp\.env
```

Profiles are configured through `DB_PROFILES_JSON`. The AI works only with names such as `postgres-local`; profile listing returns credential-presence flags, never credential values.

```env
DB_TYPE=demo
DB_DATABASE=qa_demo
DB_TIMEOUT_SECONDS=30
DB_MAX_ROWS=500
DB_ACTIVE_PROFILE=demo-local
DB_PROFILES_JSON={"demo-local":{"db_type":"demo","database":"qa_demo"},"postgres-local":{"db_type":"postgresql","host":"localhost","database":"qa_demo","username":"qa_user","password":"qa_password","connection_options":{"port":5432}}}
```

## Setup And Verification

From the repository root:

```powershell
PowerShell -ExecutionPolicy Bypass -File .\clean_mcp\scripts\setup.ps1
PowerShell -ExecutionPolicy Bypass -File .\clean_mcp\scripts\verify.ps1
```

VS Code discovers the server through `.vscode/mcp.json`. Restart the MCP server after changing `.env`.

## Safety Model

- The agent must obtain human approval before execution and profile changes.
- The profile-switch tool requires the explicit `confirm=true` assertion.
- Use only sandbox/test databases and least-privilege profile credentials.
- Keep cloud/private databases reachable only through approved company network access.
- Database permissions remain the final authority for allowed commands.
- Returned rows cannot exceed `DB_MAX_ROWS`; request timeouts cannot exceed `DB_TIMEOUT_SECONDS`.
- Credentials, tokens, private keys, and connection strings are redacted from agent-visible diagnostics and errors.
- One tool call accepts one SQL statement; comments and multiple statements are rejected to keep requests unambiguous.

## Repository Map

```text
server.py         MCP registration and stdio entry point
config.py         Validated, redacted runtime configuration
connectors/       Common contract, factory, and vendor implementations
services/         Request orchestration and profile switching
tools/            Thin MCP-facing wrappers
validation/       Single-command structural validation
models/           Stable response and error contracts
tests/            Unit, behavior, and architecture tests
docs/             Integration, extension, and testing guides
scripts/          Setup and verification automation
```

See [ADDING_CONNECTORS.md](docs/ADDING_CONNECTORS.md) for the connector extension contract and required verification rules.
