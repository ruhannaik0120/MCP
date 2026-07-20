# Basic E2E PoC Instructions

This is the first file an AI agent must read before starting an E2E QA run. Do not begin the workflow by modifying `MCP/`; it is the existing database MCP server and should be used as-is unless a separate MCP change is explicitly requested.

## Purpose

The E2E workflow combines two separate MCP systems:

- **Atlassian MCP** retrieves Jira ticket context.
- **The database MCP server in `MCP/`** manages database profiles and executes approved SQL.

The workflow instructions and generated run artifacts stay outside `MCP/`. The database MCP remains a reusable database execution service and does not contain Jira-specific workflow logic.

## Required Order And Approval Gates

1. Use **Atlassian MCP first** to retrieve Jira context.
2. Save `ticket_context.md` outside the MCP and stop for human review and approval.
3. Create the QA plan and proposed SQL only after the context is approved.
4. Stop again for human approval before executing SQL.
5. Use the existing **database MCP second** to execute only the approved SQL.
6. Stop for human approval before every database system, profile, or environment switch.
7. Ask the user to choose and approve the final export format before generating reports.

Ticket-specific workflow state and evidence belong under `ticket_runs/<ticket-id>/`, never inside `MCP/`. All workflow and execution logging belongs in the shared root-level `logs/` folder. Final HTML and Excel reports belong under `output/<ticket-id>/`.

## Before Starting

1. The user logs in to Atlassian separately and makes the Atlassian MCP available to the agent.
2. The agent reads this entire file.
3. The user provides only the Jira ticket key, for example `QA-123`.
4. The agent uses the normalized ticket key as the run folder name, for example `ticket_runs/KAN-6/`. It must reject or safely normalize characters that cannot be used in a folder name.

## E2E Workflow

### 1. Retrieve And Confirm Jira Context

1. Use Atlassian MCP to retrieve the Jira ticket's available summary, description, acceptance criteria, comments, linked information, and other relevant QA context.
2. Create `ticket_runs/<ticket-id>/` and its standard artifact subfolders.
3. Save the retrieved, organized context to `ticket_runs/<ticket-id>/ticket_context.md`.
4. Record the retrieval activity in `logs/<ticket-id>.log`. Do not record authentication data, tokens, or credentials.
5. Ask the user to review `ticket_context.md` and confirm that it contains enough information for QA planning.
6. **Stop here until the user explicitly confirms that the ticket context is complete.**

If information is missing, the user may:

- add the missing details manually; or
- ask the agent to fetch or check the ticket again through Atlassian MCP.

After any update, ask the user to review the context again. Record the user's approval in `ticket_runs/<ticket-id>/approvals/approval_log.md` without storing sensitive information.

### 2. Create The QA Plan

1. After ticket-context approval, translate the confirmed requirements into specific QA checks.
2. Identify which checks require database validation and which database system or systems are needed.
3. Save the checks, expected outcomes, required data, and required database systems to `qa_plan.md`.
4. Record this activity in `logs/<ticket-id>.log`.

### 3. Prepare Database Access

1. Connect to the existing database MCP server in `MCP/`.
2. Inspect the available named database profiles through the database MCP tools.
3. If a required profile is not configured, ask the user to configure it through the approved `.env` or company secret-management process. Never ask the user to paste credentials into chat or a prompt.
4. Credentials must remain in the database MCP's approved secret/configuration mechanism. Never write them to a generated run file.
5. If the QA plan requires multiple databases, systems, or profiles, configure a named profile for each target, explain the reason for each switch, and request explicit approval before switching.
6. Record profile-switch approvals in `ticket_runs/<ticket-id>/approvals/approval_log.md` and record non-secret switch activity in `logs/<ticket-id>.log`.

### 4. Generate And Approve SQL

1. Generate the SQL validation queries required by the approved QA plan.
2. Prefer non-mutating validation queries. If DML or DDL is genuinely required, explain its impact separately and obtain explicit approval for that statement.
3. Save all proposed SQL to `ticket_runs/<ticket-id>/generated_sql/generated_queries.sql`, with a stable check ID and clear comments showing which QA check each query supports.
4. Show or reference the generated SQL and explain what each query checks.
5. Ask the user for explicit approval before execution.
6. **Do not execute any SQL until the user approves it.**
7. Record the approval or rejection in `ticket_runs/<ticket-id>/approvals/approval_log.md`.

If SQL changes after approval, request approval again for the changed SQL before executing it.

### 5. Execute Approved SQL And Save Evidence

1. Execute each approved SQL statement in a separate database MCP call. Do not send the whole `generated_sql/generated_queries.sql` file, its organizational comments, or multiple statements in one call.
2. Send the exact approved statement text and associate the MCP response with its stable check ID.
3. Use the database MCP only for database profile selection, connection checks, metadata inspection, and query execution.
4. Save structured execution responses to `ticket_runs/<ticket-id>/execution_results/execution_result.json`.
5. Record each execution action, query reference, selected non-secret profile name, outcome, and timestamp in `logs/<ticket-id>.log`.
6. Never copy credentials, connection strings, tokens, or other secrets into the results or logs.

### 6. Evaluate The QA Results

1. For every check, compare the actual database result with the expected outcome in `qa_plan.md`.
2. Record an explicit `validation_status` such as `passed` or `failed` in `ticket_runs/<ticket-id>/execution_results/execution_result.json`.
3. Keep database execution status separate from QA status: MCP `success=true` means the SQL executed, not that the requirement passed.
4. Leave a successfully executed check as `executed_not_evaluated` until expected-versus-actual evaluation is complete.
5. Record the evaluation activity in `logs/<ticket-id>.log`.

### 7. Create The Requested Output

At the end of the run, ask the user to choose and explicitly approve one export option:

- `json_only`: keep the structured JSON result only.
- `html`: create `output/<ticket-id>/report.html`.
- `excel`: create `output/<ticket-id>/report.xlsx`.
- `both`: create both HTML and Excel reports.

Do not generate an HTML or Excel report until the user makes this choice. Record the export approval in `ticket_runs/<ticket-id>/approvals/approval_log.md`. Place generated reports under `output/<ticket-id>/` and record the selected format and report-generation activity in `logs/<ticket-id>.log`.

## Required Run Files

Each completed run folder should contain:

```text
ticket_runs/<ticket-id>/
|-- ticket_context.md
|-- qa_plan.md
|-- generated_sql/
|   `-- generated_queries.sql
|-- approvals/
|   `-- approval_log.md
`-- execution_results/
    `-- execution_result.json
```

The corresponding shared log is `logs/<ticket-id>.log`. Requested final reports are written only to `output/<ticket-id>/`.

## Mandatory Safety And Boundary Rules

- Do not hardcode credentials, tokens, connection strings, or other secrets.
- Do not store credentials or secrets in any generated run file.
- Do not place Jira or Atlassian workflow logic inside `MCP/`.
- Do not place E2E run artifacts inside `MCP/`.
- Do not create a `logs/`, `run_log.md`, or `output/` location inside a ticket folder.
- Use Atlassian MCP only for retrieving Jira context.
- Use the database MCP only for database/profile/query operations.
- Do not continue past the ticket-context checkpoint without user approval.
- Do not execute SQL without user approval.
- Do not switch database systems or profiles without user approval.
- Do not generate final HTML or Excel reports before the user approves the export format.
- Treat the database account's permissions as the final execution boundary and use approved test environments and least-privilege access.
