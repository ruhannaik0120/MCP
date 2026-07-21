# Client QA Workflow Template

## Template Status

This file preserves the database-validation workflow proven during the initial end-to-end test. It is a template, not an active client workflow.

Before use:

1. Copy it to `skills/<clientname>_QA_workflow.md` using the approved client identifier.
2. Replace every template assumption with confirmed client requirements.
3. Define supported ticket types, keywords, systems, approvals, artifacts, and report expectations.
4. Have the project manager or designated QA workflow owner approve the client workflow.

The AI agent must never select this template for a live ticket. If no exact approved client workflow exists, it must follow `skills/fallback.md`.

## Client Definition

| Field | Required client-specific value |
|---|---|
| Client identifier | `<clientname>` |
| Supported Jira projects | Define before activation |
| Supported ticket types | Define before activation |
| Supported keywords or routing rules | Define before activation |
| Required database systems and profiles | Define before activation |
| Required approvals | Define before activation |
| Required final outputs | Define before activation |
| Workflow owner | Define before activation |

## Reference Workflow

The following procedure is the tested starting point. Customize it before activating the client workflow.

### 1. Initialize The Ticket Workspace

From the repository root, run:

```powershell
.\.venv\Scripts\python.exe .\modules\init_ticket_run.py <ticket-id>
```

Confirm that the ticket workspace contains `downloads/` and `generated/`, that its shared log is under root `logs/`, and that no ticket-local log or output folder was created.

### 2. Retrieve And Confirm Ticket Context

1. Use Atlassian MCP to retrieve the authorized Jira summary, description, acceptance criteria, comments, linked information, and other relevant context.
2. Identify relevant attachments and external supporting links.
3. If a credential-protected source cannot be accessed by the agent, ask an authorized user to download it into `ticket_runs/<ticket-id>/downloads/` without sharing credentials.
4. Inventory and inspect supported local source files. Record any file that cannot be safely read.
5. Save the combined context to `ticket_runs/<ticket-id>/generated/ticket_context.md`, citing relevant downloaded filenames.
6. Record non-secret retrieval and review activity in `logs/<ticket-id>.log`.
7. Ask the user to confirm that the context is complete enough for QA planning.
8. Stop until context approval is explicit, then record the decision in `generated/approvals/approval_log.md`.

### 3. Create The QA Plan

1. Translate approved requirements into stable, reviewable QA checks.
2. Define the expected outcome, required evidence, data needs, and target system for every check.
3. Save the plan to `ticket_runs/<ticket-id>/generated/qa_plan.md`.
4. Record the activity in `logs/<ticket-id>.log`.

### 4. Prepare Database Access

1. Use the existing database MCP server in `MCP/`.
2. Inspect safe named-profile information through MCP tools.
3. Ask the user to configure missing profiles through the approved secret process; never request credentials in chat.
4. Explain every required system, profile, or environment switch and obtain explicit approval before switching.
5. Record profile approvals under `generated/approvals/` and non-secret activity in the root ticket log.

### 5. Generate And Approve SQL

1. Generate the validation SQL required by the approved QA plan.
2. Prefer non-mutating queries. Explain any necessary DML or DDL separately.
3. Map every statement to a stable check ID.
4. Save proposed SQL to `ticket_runs/<ticket-id>/generated/generated_sql/generated_queries.sql`.
5. Present or reference each proposed statement and explain what it validates.
6. Obtain explicit approval before execution and record the decision.
7. If SQL changes after approval, request approval again for the changed statement.

### 6. Execute Approved SQL

1. Execute each approved SQL statement in a separate database MCP call.
2. Send only the exact approved statement, not organizational comments or a multi-statement file.
3. Associate every MCP response with its stable check ID.
4. Save structured responses to `ticket_runs/<ticket-id>/generated/execution_results/execution_result.json`.
5. Record the check ID, safe profile name, outcome, and timestamp in `logs/<ticket-id>.log`.
6. Never place credentials or secret-bearing connection details in evidence or logs.

### 7. Evaluate Results

1. Compare each actual result with the expected outcome in `generated/qa_plan.md`.
2. Record an explicit `validation_status`, such as `passed` or `failed`, in the execution result.
3. Keep execution status separate from QA status. A successful MCP call proves that SQL ran, not that the requirement passed.
4. Correct, reapprove, and rerun only affected failed checks when necessary.

### 8. Create Approved Output

Ask the user to choose and approve one supported export option:

- `json_only` keeps the structured JSON evidence only;
- `html` creates `output/<ticket-id>/report.html`;
- `excel` creates `output/<ticket-id>/report.xlsx`; or
- `both` creates both reports.

Record export approval under `generated/approvals/`, create reports only under root `output/<ticket-id>/`, and record export activity in the shared ticket log.

## Client Customization Checklist

Before renaming and activating this template, define:

- how the client is identified;
- which Jira projects and ticket types are supported;
- keywords that change routing or require fallback;
- mandatory source documents;
- database systems, environments, and profile-selection rules;
- client-specific QA checks and evidence standards;
- every human approval checkpoint;
- retry, correction, and selective-rerun rules;
- required report formats, recipients, and data-handling rules;
- escalation contacts and unsupported conditions; and
- the workflow owner and approval date.
