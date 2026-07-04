# MCP Execution Framework Foundation

Production-oriented connector foundation for the controlled execution layer of an AI-driven QA automation system.

An AI orchestrator can retrieve requirements, draft validation instructions, and request approval. This framework owns the next boundary: selecting an approved enterprise connection, validating an approved read-only query, executing it through MCP, and returning structured, auditable evidence. The AI never receives database credentials and never connects directly to a data platform.

## System Position

```text
Jira / Requirements -> AI-Agnostic Orchestrator -> Human Approval
                                                   |
                                                   v
                                      MCP Execution Framework
                                      | tools and policy
                                      | service orchestration
                                      | connector factory
                                      v
                         SQL Server | PostgreSQL | MySQL | Snowflake
                                                   |
                                                   v
                                 JSON results, logs, artifacts
```

This repository is the reusable MCP execution-layer foundation intended to integrate into the larger system. Jira retrieval, AI reasoning, memory, and reporting remain separate components with explicit contracts.

## Capabilities

- AI-client agnostic MCP server using standard `stdio` transport.
- SQL Server, PostgreSQL, MySQL, Snowflake, and deterministic offline demo connectors.
- Named profile switching at runtime without restarting the MCP server.
- Mandatory `confirm=true` approval signal before a system transition.
- Atomic switch validation, connectivity test, and rollback on failure.
- Credentials remain in local environment configuration and are redacted from diagnostics.
- Read-only SQL policy, single-statement enforcement, bounded row limits, and timeouts.
- Stable JSON response envelopes, structured errors, request IDs, JSON logs, and per-request artifacts.
- Architecture tests preventing database-driver imports outside `connectors/`.

## MCP Tools

| Tool | Purpose |
|---|---|
| `tool_list_connection_profiles` | Lists safe profile metadata without credentials. |
| `tool_switch_connection_profile` | Switches after explicit approval, tests the target, and rolls back on failure. |
| `tool_config_diagnostics` | Returns redacted runtime diagnostics. |
| `tool_health` | Checks the active connector. |
| `tool_test_connection` | Verifies connectivity and server metadata. |
| `tool_list_databases` | Lists visible databases. |
| `tool_list_tables` | Lists tables by database/schema. |
| `tool_describe_table` | Returns column metadata. |
| `tool_execute_select_query` | Executes one approved read-only statement. |

## Runtime Switching

Define named profiles in `.env` through `DB_PROFILES_JSON`. Real passwords must exist only in `.env`, which is ignored by Git.

```env
DB_TYPE=demo
DB_DATABASE=qa_demo
DB_ACTIVE_PROFILE=demo-local
DB_PROFILES_JSON={"demo-local":{"db_type":"demo","database":"qa_demo"},"postgres-local":{"db_type":"postgresql","host":"localhost","database":"qa_demo","username":"qa_user","password":"secret","connection_options":{"port":5432}}}
```

Expected agent flow:

1. Call `tool_list_connection_profiles`.
2. Explain the requested source and ask the user for approval.
3. After approval, call `tool_switch_connection_profile(name="postgres-local", confirm=true)`.
4. The framework validates configuration, builds the connector, and tests connectivity.
5. On failure, the previous profile is restored automatically.

The connectivity check cannot be disabled through the MCP tool. A profile is
only made active after its configuration validates and its target responds.

## Setup

From the workspace root:

```powershell
PowerShell -ExecutionPolicy Bypass -File .\clean_mcp\scripts\setup.ps1
Copy-Item .\clean_mcp\.env.example .\clean_mcp\.env
```

Edit `.env`, then verify:

```powershell
PowerShell -ExecutionPolicy Bypass -File .\clean_mcp\scripts\verify.ps1
```

VS Code discovers the server through `.vscode/mcp.json`. Reload VS Code after setup, open an MCP-capable agent, and enable `mcp-execution-framework`.

## Safety Contract

- This version permits `read_only` execution only. Tool arguments cannot elevate access.
- Request row limits can reduce but never exceed the configured `DB_MAX_ROWS` ceiling (maximum 10,000).
- Request timeouts can reduce but never exceed the configured `DB_TIMEOUT_SECONDS` ceiling.
- The framework requires human approval before profile transitions.
- Profiles and diagnostics expose presence flags, never passwords or tokens.
- The MCP core accesses databases only through `ConnectorFactory -> DatabaseConnector`.
- External database permissions remain the final enforcement layer; use read-only database users.
- Every request produces a traceable ID, structured log, and execution artifact.

## Repository Map

```text
server.py                 MCP registration and stdio entry point
config.py                 Generic validated configuration
connectors/               Stable interface, factory, backend implementations
services/                 Orchestration and atomic profile switching
tools/                    Thin agent-facing wrappers
validation/               Read-only SQL policy
models/                   Stable response and error contracts
artifacts/                Generated logs and execution evidence
tests/                    Unit, policy, and architecture tests
docs/                     Extension, testing, and demo documentation
scripts/                  Reproducible setup and verification
```

To add SAP, Oracle, Databricks, or another system, follow [docs/ADDING_CONNECTORS.md](docs/ADDING_CONNECTORS.md). The tool, service, response, audit, and policy layers remain unchanged.

## Verified Versus Configured

The release gate currently passes **50 automated tests**. It also verifies all
**nine MCP tools**, the real `stdio` protocol handshake, profile approval,
successful switching, failed-switch rollback, read-only rejection, dependency
integrity, and backend-specific configuration mapping.

| Connector | Implemented | Automated-tested | Live-verified |
|---|---:|---:|---:|
| Offline demo | Yes | Yes | Yes (`stdio` MCP client) |
| SQL Server | Yes | Yes | Pending local SQL Server networking/authentication |
| PostgreSQL | Yes | Yes | Pending profile credentials and query execution |
| MySQL | Yes | Yes | Pending local server/profile configuration |
| Snowflake | Yes | Yes | Pending account profile and query execution |

A database connector is only called live-verified after `tool_test_connection`
and a safe query succeed against that platform. Record results using
[docs/LOCAL_TESTING.md](docs/LOCAL_TESTING.md); never imply external
connectivity that was not actually tested.
