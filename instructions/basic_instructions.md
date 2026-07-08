# End-to-End PoC Agent Instructions

## Primary Rule

This workflow is automated, but not fully autonomous. Proceed automatically only when the next step is clear. If there is uncertainty, ambiguity, missing information, a failed tool call, an unexpected result, or possible risk, stop and ask the user before continuing.

## Uncertainty Rule

Do not guess, assume, or continue silently when:

- The Jira ticket is unclear.
- The target database profile is unclear.
- The table name or schema is unclear.
- The SQL logic is uncertain.
- A query may affect data unexpectedly.
- A tool call fails.
- A profile switch is needed but not confirmed.
- A returned result looks unexpected.
- Required files or folders are missing.
- The ticket, generated SQL, and database structure do not agree.

## Workflow

1. Ask for the Jira ticket ID, or read it from `poc_run_config.json` when present.
2. Use Atlassian MCP to retrieve ticket context. Do not add Jira logic to `clean_mcp`.
3. Create `poc_runs/<ticket_id>/` and save the context as `ticket_context.md`.
4. Generate the QA plan and save it as `qa_plan.md`.
5. Stop and obtain user approval before generating SQL.
6. Generate SQL and save it as `generated_queries.sql`.
7. Stop and obtain user approval before database execution.
8. Use only MCP execution framework tools for database actions. Never use a direct driver, shell database client, or unrelated database tool.
9. Ask before switching profiles. Call the switch tool with `confirm=true` only after approval.
10. Save MCP results to `poc_runs/<ticket_id>/execution_result.json`.
11. Save approval decisions to `poc_runs/<ticket_id>/approval_log.md`.
12. Save major actions and pass/fail outcomes to `poc_runs/<ticket_id>/run_log.md`.
13. Never expose credentials, tokens, connection strings, or private keys.

The agent workflow owns all files under `poc_runs/`. The MCP server only switches configured profiles, executes approved commands, and returns structured responses.
