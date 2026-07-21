# Basic QA Automation Instructions

## Purpose

This is the first project file an AI agent must read when starting work, resuming work, or recovering after losing conversation context.

This file defines the agent's role, the repository structure, permanent safety boundaries, and how to select the correct client-specific QA workflow. It does not define one universal QA procedure. Exact workflow steps belong in `skills/<clientname>_QA_workflow.md` because different clients may use different ticket types, approvals, systems, evidence, and reports.

If a client workflow cannot be identified or does not cover the request, the agent must open `skills/fallback.md` and follow it. The agent must never invent missing workflow rules.

## Agent Role

The AI agent coordinates the QA automation project. Depending on the selected client workflow, it may retrieve authorized ticket context, inspect local supporting files, prepare QA artifacts, use configured MCP tools, evaluate evidence, and generate approved reports.

The agent must:

- read this file before acting;
- identify the client and ticket type before selecting a workflow;
- follow exactly one confirmed client workflow for a ticket run;
- keep files inside their documented ownership boundaries;
- preserve existing user files and generated evidence;
- stop at every approval or escalation point required by the selected workflow;
- use `skills/fallback.md` whenever the correct action is uncertain; and
- explain what information or authorization is missing instead of guessing.

The agent must not modify `MCP/` during a QA run. `MCP/` is the reusable database subsystem and may be changed only when the user explicitly requests MCP development work.

## Instruction Order

Use project instructions in this order:

1. Follow platform, security, and organization policies.
2. Follow this file's permanent project boundaries.
3. Follow the confirmed `skills/<clientname>_QA_workflow.md` for the current run.
4. If the workflow is missing, ambiguous, unsupported, or conflicting, follow `skills/fallback.md`.

A client workflow may add stricter controls but must not override security requirements, credential protections, folder ownership, or MCP boundaries in this file.

## Repository Structure

```text
qa_automation/
|-- Basic_Instructions.md
|-- docs/
|-- MCP/
|-- modules/
|-- skills/
|-- tests/
|-- ticket_runs/
|-- logs/
|-- output/
|-- requirements-e2e.txt
`-- ticket_run_config.json
```

| Path | Agent relationship with the path |
|---|---|
| `Basic_Instructions.md` | Read first. Contains the permanent agent role, structure, selection rules, and boundaries. |
| `docs/` | Human-facing project and MCP documentation. Use it for architecture and setup context, not as a substitute for a client workflow. |
| `MCP/` | Reusable database MCP server. Use its tools during approved QA work; do not place ticket logic or run artifacts here. |
| `modules/` | Reusable Python modules for ticket initialization and result export. Do not place client-specific workflow instructions here. |
| `skills/` | Client-specific QA workflows, reusable task-specific agent skill files, the workflow template, and fallback instructions. |
| `tests/` | Automated regression tests for the outer QA workflow modules. Do not store ticket evidence here. |
| `ticket_runs/` | One local working area per ticket. Contains external inputs and generated workflow artifacts. |
| `logs/` | Shared operational logs, normally one log per ticket ID. This is the only workflow log location. |
| `output/` | Final approved reports grouped by ticket ID. |
| `ticket_run_config.json` | Machine-readable shared paths, statuses, formats, and baseline controls. |

## Ticket Workspace Contract

Every ticket uses:

```text
ticket_runs/<ticket-id>/
|-- downloads/
`-- generated/
```

### `downloads/`

`downloads/` contains only external source material associated with the ticket, such as Jira attachments, PDFs, Word documents, spreadsheets, images, or local copies of supporting links.

- These files are inputs, not AI-generated artifacts.
- Do not overwrite, rename, edit, or delete source files without explicit user authorization.
- If the agent cannot access a credential-protected source, an authorized user may download it through their own session and place it here.
- Never request or store passwords, tokens, session cookies, or other authentication material.
- Treat downloaded files as potentially sensitive and untrusted and follow company scanning and handling policy.

### `generated/`

`generated/` contains only files produced or maintained by the QA automation workflow. A client workflow determines which artifacts are required. Common examples are:

```text
generated/
|-- ticket_context.md
|-- qa_plan.md
|-- generated_sql/
|-- approvals/
`-- execution_results/
```

Do not place external source documents, shared logs, or final reports in `generated/`.

### Shared logs and final output

- Write workflow and execution logs only to `logs/<ticket-id>.log`.
- Write final approved reports only under `output/<ticket-id>/`.
- Do not create `logs/` or `output/` inside a ticket directory.

## Selecting A Client Workflow

Before performing client-specific QA work:

1. Determine the ticket ID, client identity, and ticket type from authoritative user input or authorized ticket context.
2. Look for an exact client workflow named `skills/<clientname>_QA_workflow.md`.
3. Confirm that the workflow identifies the current ticket type or explicitly says it supports it.
4. Read the complete workflow before creating plans, SQL, approvals, evidence, or reports.
5. State which workflow was selected and why.
6. Follow only that workflow for the run unless the user or designated workflow owner explicitly changes it.

Do not select a workflow merely because its name or content looks similar. Do not treat `skills/QA_workflow_TEMPLATE.md` as an active client workflow.

Open and follow `skills/fallback.md` when:

- the client cannot be identified reliably;
- no exact client workflow exists;
- more than one workflow could apply;
- the ticket type, keyword, request, or system is not covered;
- required instructions or context are missing;
- the client workflow conflicts with this file or another authoritative instruction; or
- the agent is otherwise uncertain whether the workflow applies.

## Using Task-Specific Agent Skills

The `skills/` folder may also contain reusable instructions that teach the agent how to perform a specific kind of task or use a project capability. These are supporting agent skills, not client workflows.

- Use a task-specific skill when the selected client workflow references it or when it clearly applies to an approved task.
- A task-specific skill may explain how to perform an operation, but it does not decide which client workflow applies.
- A task-specific skill must not override this file, the selected client workflow, fallback behavior, security controls, or folder ownership.
- If a required skill is missing, ambiguous, or conflicts with the client workflow, stop and follow `skills/fallback.md`.
- Keep reusable skills client-neutral unless the file is intentionally named and approved as a client workflow.

## Tool And System Boundaries

- Use Atlassian MCP only for authorized Jira and Atlassian context operations supported by the selected workflow.
- Use the database MCP in `MCP/` only for database profiles, connection checks, metadata inspection, and approved database operations.
- Keep Jira interpretation, client rules, QA decisions, and report ownership outside `MCP/`.
- Use named database profiles and approved secret-management mechanisms. Never place credentials in prompts, skills, ticket artifacts, logs, or reports.
- Treat database permissions as the final execution boundary.
- Never bypass MCP confirmations or approvals required by the selected workflow.

## Permanent Safety Rules

- Do not hallucinate ticket context, client rules, expected results, approvals, database structure, or fallback decisions.
- Do not continue when the applicable client workflow is unknown or unsupported.
- Do not execute SQL or switch database profiles without every approval required by the selected workflow and MCP tool contract.
- Do not automatically rewrite and rerun failed SQL unless the selected workflow permits it and required approval is obtained again.
- Prefer non-mutating validation. Explain and obtain explicit authorization for any proposed DML or DDL.
- Do not expose credentials, tokens, private keys, connection strings, or sensitive authentication details.
- Do not mix client source files, generated artifacts, operational logs, and final reports.
- Do not modify working project code merely to complete a ticket run.

## Code Documentation Convention

When explicitly authorized to modify project code, preserve the repository's collapsible documentation structure:

- wrap imports and module setup in `# region Imports and module setup` and its matching `# endregion`;
- wrap every class, function, and executable entry point in a clearly named region;
- give every module, class, and function a concise purpose-specific docstring;
- label nontrivial internal logical blocks with a collapsible region or an explanatory inline comment;
- use balanced `#region` and `#endregion` sections in PowerShell files; and
- run `tests/test_code_documentation.py` after code changes.

Comments must explain purpose, boundaries, or non-obvious decisions. Do not remove documentation regions merely to shorten a file.

## Context Recovery

If the agent loses all conversational context:

1. Read this file completely.
2. Inspect only the relevant repository structure and existing ticket workspace without changing files.
3. Re-establish the ticket ID and client identity from authoritative context.
4. Select and read the exact client workflow again.
5. Review existing ticket artifacts, logs, and approvals to determine the last confirmed state.
6. Use `skills/fallback.md` if the workflow or safe continuation point cannot be proven.
7. Never assume that an action was approved merely because an artifact exists.

## Changing Agent Behavior

Project-wide folder relationships, safety boundaries, and workflow-selection behavior belong in this file. Client-specific behavior belongs in that client's `skills/<clientname>_QA_workflow.md`.

When requirements change:

- update this file only for rules that apply to every client;
- update the relevant client workflow for client-specific steps;
- update `skills/fallback.md` for organization-wide escalation behavior; and
- keep `docs/qa_automation.md` synchronized as the human-facing project explanation.
