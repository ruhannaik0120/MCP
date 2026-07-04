# Local Testing And Evidence

## Automated Gate

```powershell
PowerShell -ExecutionPolicy Bypass -File .\clean_mcp\scripts\verify.ps1
```

The gate runs compilation, pytest, architecture rules, configuration validation, and an offline demo workflow.

## Live Connector Gate

For each configured profile:

1. Call `tool_list_connection_profiles` and capture the redacted output.
2. Ask for approval to switch.
3. Call `tool_switch_connection_profile` with the profile name and `confirm=true`.
4. Capture successful connection metadata.
5. Call `tool_list_tables` with the correct schema (`public`, `dbo`, or `PUBLIC`).
6. Execute `SELECT 1 AS health_check`.
7. Execute `DELETE FROM demo_table` and capture the structured rejection.
8. Capture the matching JSON artifact and log request ID.

Use read-only accounts and sanitized local data. Never capture `.env`, passwords, tokens, private account identifiers, or company data.

## Suggested Agent Prompt

```text
Use the MCP execution framework. List the configured connection profiles without exposing credentials. Ask me before every profile switch. After I approve, switch with confirm=true, verify connectivity, list accessible tables, run SELECT 1 AS health_check, and show the request ID. Do not execute writes or reveal configuration secrets.
```

## Evidence Record

For each backend record: profile name, date, tool, success, request ID, database/schema, and screenshot filename. A failed connection is valid engineering evidence when paired with the structured cause and rollback confirmation.
