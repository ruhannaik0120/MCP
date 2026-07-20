# QA Automation Project

## Product Requirements and Design Document

| Document field | Value |
|---|---|
| Project | QA Automation |
| Document purpose | Complete project explanation, product requirements, architecture, setup, operation, and future development guide |
| Primary audience | New developers, QA engineers, technical leads, AI-agent operators, and project stakeholders |
| Main workflow entry point | `Basic_Instructions.md` |
| Database subsystem documentation | `docs/MCP.md` |
| Current delivery model | Human-approved, AI-assisted QA workflow |

## 2. Executive Summary

The QA Automation project turns the requirements in a Jira ticket into a controlled QA validation run.

An AI agent coordinates the process. It retrieves Jira context through Atlassian MCP, organizes the requirements, creates a QA plan, proposes database validation SQL, pauses for human approval, executes approved SQL through the repository's database MCP server, evaluates the returned evidence, and creates an approved final report.

The project is deliberately divided into separate responsibilities:

- **Atlassian MCP** provides Jira ticket information.
- **The AI agent** coordinates the workflow and prepares QA artifacts.
- **The human operator** approves important decisions and execution steps.
- **The database MCP server in `MCP/`** provides controlled database access.
- **Database connectors** translate common MCP operations into database-specific operations.
- **Ticket storage** keeps working state and raw evidence for each ticket.
- **Root-level logs** record workflow and execution activity.
- **Root-level output** contains final HTML and Excel reports.

The system is not intended to give an AI unrestricted access to Jira or databases. Human approval, named database profiles, credential isolation, structured evidence, and database permissions are core design requirements.

## 3. The Problem Being Solved

Database-backed QA validation commonly involves several manual steps:

1. Read a Jira ticket and identify testable requirements.
2. Translate those requirements into a QA plan.
3. Determine which database systems contain the relevant evidence.
4. Inspect database schemas and column names.
5. Write validation SQL.
6. Review the SQL for correctness and safety.
7. Run the SQL against the correct environment.
8. Compare actual results with expected results.
9. Save evidence and explain failures.
10. Produce a report that another person can understand.

When these steps are performed informally, important context can be lost. Queries may be executed against the wrong system, approval decisions may not be recorded, raw execution success may be mistaken for a passed QA check, and results may not be reproducible.

This project standardizes that process while keeping a human in control.

## 4. Product Vision

The final working QA Automation system should allow an authorized user to provide a Jira ticket key and guide an AI agent through a repeatable, auditable workflow that produces reliable QA evidence and a clear final report.

The finished system should:

- understand the available Jira requirement context;
- create consistent ticket-scoped working files;
- require human approval at high-impact checkpoints;
- support multiple database systems through one MCP interface;
- keep credentials outside prompts and generated artifacts;
- preserve raw evidence separately from final reports;
- clearly distinguish query execution from QA validation;
- allow failed SQL to be corrected, reapproved, and selectively rerun;
- produce structured JSON evidence;
- optionally produce HTML and Excel reports;
- support future database connectors without redesigning the workflow; and
- remain understandable to a new developer or operator.

## 5. Product Goals

### 5.1 Primary goals

1. Convert Jira requirements into specific and reviewable QA checks.
2. Make database validation available to MCP-compatible AI agents.
3. Require explicit human approval before SQL execution and environment changes.
4. Store ticket evidence in a stable and predictable structure.
5. Keep operational logs and final reports in clearly separate locations.
6. Support PostgreSQL, Snowflake, MySQL, SQL Server, and an offline demo system through one MCP tool interface.
7. Produce results that can be audited, evaluated, and shared.
8. Make the system extensible for future connectors and broader QA workflows.

### 5.2 Non-goals

The current project is not intended to:

- replace human QA judgment;
- automatically approve its own SQL;
- bypass database permissions;
- store database credentials in the repository;
- embed Jira-specific logic inside the database MCP server;
- treat successful SQL execution as automatic proof that a requirement passed;
- provide a production web dashboard;
- act as a general-purpose database administration tool; or
- run destructive database operations without explicit explanation and approval.

## 6. Beginner Concepts

### 6.1 What is QA automation?

Quality assurance, or QA, is the process of checking whether a system behaves as required. QA automation uses software to perform repeatable checks and collect evidence.

In this project, automation assists with requirement interpretation, SQL preparation, database execution, evidence handling, and report generation. A human still reviews the context and approves important actions.

### 6.2 What is an AI agent?

An AI agent is an AI assistant that can use configured tools and work with files. In this project, the agent acts as the workflow coordinator.

The agent can:

- retrieve ticket information through Atlassian MCP;
- create and update local QA artifacts;
- call database tools through the database MCP server;
- compare expected and actual results; and
- generate reports from saved evidence.

The agent does not receive unrestricted database credentials. It works through approved MCP tools and named database profiles.

### 6.3 What is MCP?

MCP stands for Model Context Protocol. It is a standard way for an AI client to discover and call tools exposed by an external service.

An MCP server publishes tools with structured inputs and outputs. In this project:

- Atlassian provides an MCP server for Jira access.
- This repository contains a separate MCP server for database access.

The database MCP server is only one component of the complete QA Automation project. See [MCP.md](MCP.md) for its full implementation, setup, connector, and tool documentation.

### 6.4 What is a database profile?

A database profile is a named, locally configured set of connection settings. A profile identifies a database type, host, database, user, connection options, timeouts, and row limits.

The AI agent works with safe profile names such as:

```text
postgres-test
snowflake-qa
sqlserver-staging
```

Credentials remain in `MCP/.env` or an approved secret-management system. They must not be written into tickets, prompts, logs, reports, or committed files.

### 6.5 What is a ticket run?

A ticket run is one QA workflow associated with one Jira ticket or client QA request.

Every run uses a normalized ticket ID and stores its working state under:

```text
ticket_runs/<ticket-id>/
```

Examples:

```text
ticket_runs/KAN-6/
ticket_runs/ABC-123/
```

## 7. Current Implementation And Final Target

It is important to distinguish what exists now from what the complete product may become later.

### 7.1 Implemented now

The repository currently includes:

- mandatory human-in-the-loop workflow instructions;
- Atlassian MCP workspace configuration;
- a reusable database MCP server;
- named database profile handling;
- demo, PostgreSQL, Snowflake, MySQL, and SQL Server connectors;
- connection, metadata, diagnostics, profile, and query tools;
- SQL structural guardrails;
- ticket-run folder initialization;
- safe ticket ID normalization;
- stable ticket artifact paths;
- root-level workflow logs;
- structured execution-result storage;
- HTML and Excel report generation;
- sensitive-field redaction during report generation;
- HTML escaping and Excel formula-injection protection;
- unit and workflow helper tests; and
- an offline demo connector for verification without a live database.

### 7.2 Current operating model

The current system is AI-assisted rather than a single unattended application.

The AI agent reads `Basic_Instructions.md` and coordinates tools, approvals, files, and results. The helper scripts initialize folders and export saved data, but they do not retrieve Jira tickets or execute database queries themselves.

### 7.3 Intended final development

The final working development should preserve the same boundaries while making the workflow consistently repeatable for every ticket. Regardless of the future AI client, user interface, scheduler, or deployment platform, the system should continue to enforce:

- one ticket-scoped working area per run;
- centralized logs;
- centralized final output;
- explicit approval checkpoints;
- named database profiles;
- one approved SQL statement per database MCP call;
- structured evidence;
- expected-versus-actual evaluation; and
- separation between orchestration and database execution.

Future interfaces may automate more coordination, but they must not remove these controls without an approved product and security decision.

## 8. System Architecture

### 8.1 High-level architecture

```text
                    +----------------------+
                    |    Human Operator    |
                    | reviews and approves |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    |       AI Agent       |
                    | coordinates the run  |
                    +---+--------------+---+
                        |              |
            Jira context|              |database tools
                        v              v
              +---------+----+   +-----+-------------+
              | Atlassian MCP |   | Repository MCP   |
              | Jira access   |   | database access  |
              +--------------+   +-----+-------------+
                                        |
                       +----------------+----------------+
                       |                |                |
                       v                v                v
                  PostgreSQL        Snowflake       Other supported
                                                     databases

AI Agent also writes:

ticket_runs/<ticket-id>/   logs/<ticket-id>.log   output/<ticket-id>/
working state and evidence   shared activity log    final reports
```

### 8.2 Responsibility boundaries

| Component | Responsible for | Not responsible for |
|---|---|---|
| Human operator | Reviewing context, approving SQL, approving profile changes, choosing report format | Manually implementing every database connector operation |
| AI agent | Coordinating workflow, preparing artifacts, calling approved tools, evaluating evidence | Bypassing approvals or database permissions |
| Atlassian MCP | Retrieving Jira context available to the authenticated user | Database execution or report generation |
| Database MCP in `MCP/` | Profile operations, connection checks, metadata inspection, approved SQL execution | Jira interpretation, QA pass/fail decisions, or ticket report ownership |
| Database connector | Database-specific connections, metadata SQL, timeouts, row limits, and execution | Workflow orchestration |
| Helper scripts | Creating local ticket structure and exporting saved results | Calling Jira, MCP tools, or databases |
| Ticket storage | Preserving QA source artifacts and raw evidence | Holding operational logs or final HTML/Excel reports |
| Root `logs/` | Recording non-secret workflow and execution activity | Holding raw credentials |
| Root `output/` | Holding final approved reports | Acting as the source of truth for raw execution evidence |

## 9. Repository Structure

```text
qa_automation/
|-- .vscode/
|   `-- mcp.json
|-- Basic_Instructions.md
|-- docs/
|   |-- MCP.md
|   `-- qa_automation.md
|-- MCP/
|   |-- connectors/
|   |-- models/
|   |-- scripts/
|   |-- services/
|   |-- tests/
|   |-- tools/
|   |-- validation/
|   |-- .env.example
|   |-- config.py
|   |-- requirements.txt
|   `-- server.py
|-- logs/
|-- output/
|-- scripts/
|   |-- init_ticket_run.py
|   `-- export_results.py
|-- tests/
|   `-- test_e2e_helpers.py
|-- ticket_runs/
|-- requirements-e2e.txt
`-- ticket_run_config.json
```

### 9.1 Top-level files and folders

| Path | Purpose |
|---|---|
| `Basic_Instructions.md` | Mandatory operating rules and approval checkpoints for an AI agent running a ticket. |
| `docs/qa_automation.md` | This project-wide PRD and handoff document. |
| `docs/MCP.md` | Detailed documentation for the reusable database MCP subsystem. |
| `MCP/` | Database MCP implementation, connectors, services, tools, configuration, and tests. |
| `ticket_runs/` | Ticket-scoped working state and raw QA evidence. Generated ticket folders are not committed. |
| `logs/` | Shared workflow and execution logs, one file per ticket run. |
| `output/` | Final generated reports organized by ticket ID. |
| `scripts/` | Outer workflow helpers for run initialization and result export. |
| `tests/` | Tests for the outer workflow helpers. |
| `ticket_run_config.json` | Machine-readable workflow paths, statuses, formats, and approval checkpoint definitions. |
| `requirements-e2e.txt` | Outer workflow dependencies. It currently provides `openpyxl` for Excel export. |
| `.vscode/mcp.json` | Workspace configuration for Atlassian MCP and the local database MCP server. |

## 10. Ticket Artifact Model

### 10.1 Ticket naming convention

The standard path is:

```text
ticket_runs/<ticket-id>/
```

The helper normalizes ticket IDs to uppercase and permits safe letters, numbers, dots, underscores, and hyphens. Unsafe values are normalized with a deterministic hash when necessary to reduce naming collisions. Windows reserved filenames are also handled.

### 10.2 Stable ticket structure

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

No `logs/` or `output/` folder should be created inside a ticket directory.

### 10.3 Artifact definitions

| Artifact | Purpose | Created or updated by |
|---|---|---|
| `ticket_context.md` | Organized Jira summary, requirements, acceptance criteria, comments, links, and QA-relevant context | AI agent using Atlassian MCP |
| `qa_plan.md` | QA objectives, checks, expected outcomes, required systems, and profile needs | AI agent after context approval |
| `generated_sql/generated_queries.sql` | Proposed SQL mapped to stable QA check IDs | AI agent before SQL approval |
| `approvals/approval_log.md` | Human approval and rejection history for required checkpoints | AI agent recording user decisions |
| `execution_results/execution_result.json` | Structured raw database evidence and explicit QA evaluation | AI agent using database MCP responses |
| `logs/<ticket-id>.log` | Non-secret workflow, profile, execution, evaluation, and export activity | Initializer and AI agent |
| `output/<ticket-id>/report.html` | Final browser-readable report | Export helper after approval |
| `output/<ticket-id>/report.xlsx` | Final spreadsheet report | Export helper after approval |

### 10.4 Why raw evidence and final output are separate

`execution_result.json` is the source evidence. It contains the structured data needed to audit or regenerate a report.

HTML and Excel files are presentation outputs. They may summarize or format the evidence for a stakeholder. Keeping them under `output/<ticket-id>/` prevents a final report from being confused with source workflow state.

## 11. End-To-End Workflow

### 11.1 Workflow summary

```text
Jira ticket key
      |
      v
Retrieve Jira context through Atlassian MCP
      |
      v
Save ticket_context.md
      |
      v
HUMAN APPROVAL: context is complete
      |
      v
Create qa_plan.md and generated SQL
      |
      v
HUMAN APPROVAL: SQL is approved
      |
      v
HUMAN APPROVAL: target profile/system switch
      |
      v
Execute each approved statement through database MCP
      |
      v
Save and evaluate execution_result.json
      |
      v
HUMAN APPROVAL: final export format
      |
      v
Generate output/<ticket-id>/ reports
```

### 11.2 Step 1: Initialize the run

From the repository root:

```powershell
.\.venv\Scripts\python.exe .\scripts\init_ticket_run.py ABC-123
```

The initializer:

- normalizes the ticket ID;
- creates the ticket directory and standard subdirectories;
- creates missing template artifacts without overwriting existing files;
- creates `logs/<ticket-id>.log` if it does not exist;
- does not create a ticket-local logs folder;
- does not create a ticket-local output folder;
- does not contact Jira;
- does not contact an MCP server; and
- does not connect to a database.

The initializer is idempotent. Running it again does not overwrite completed work.

### 11.3 Step 2: Retrieve Jira context

The user supplies a Jira ticket key. The AI agent uses Atlassian MCP to retrieve the ticket information visible to the authenticated Atlassian account.

Relevant context can include:

- summary;
- description;
- acceptance criteria;
- comments;
- linked issues;
- labels and priority;
- available project context; and
- information needed to define QA checks.

The organized context is saved to `ticket_context.md`.

### 11.4 Step 3: Approve ticket context

The AI agent must stop and ask the user whether the saved context is complete enough for planning.

The user may approve it, add missing information, or ask the agent to retrieve the Jira ticket again. QA planning cannot begin until the context is explicitly approved.

The decision is recorded in `approvals/approval_log.md`.

### 11.5 Step 4: Create the QA plan

The AI agent converts the approved requirements into concrete checks.

Each check should identify:

- a stable check ID;
- the requirement being validated;
- the expected result;
- the evidence required;
- whether database validation is required;
- the required database system and named profile; and
- any important assumptions or limitations.

The plan is saved to `qa_plan.md`.

### 11.6 Step 5: Inspect metadata and prepare SQL

When schema details are uncertain, the agent should use database MCP metadata tools before writing SQL. It should inspect available databases, tables, and columns rather than guessing names.

Proposed SQL is saved to `generated_sql/generated_queries.sql`. Every statement must map to a stable check ID.

Validation queries should normally be non-mutating. If DML or DDL is genuinely required, the agent must explain the effect and obtain explicit approval for that statement.

### 11.7 Step 6: Approve SQL

The agent shows or references the proposed SQL and explains what every statement checks.

No SQL may be executed until the user approves it. If an approved statement changes, the changed statement must be approved again.

### 11.8 Step 7: Approve and switch database profiles

Every target database or environment is represented by a named profile.

Before switching profiles, the agent explains:

- which profile is required;
- which database system it represents;
- why the switch is necessary; and
- which checks will use it.

The user must approve every system, environment, or profile switch.

### 11.9 Step 8: Execute approved SQL

The agent sends one exact approved SQL statement per database MCP call.

It must not send:

- the complete organizational SQL file as one request;
- multiple statements in one call;
- comments used only to organize the SQL file; or
- changed SQL that has not been reapproved.

Each response is associated with its stable check ID and stored in `execution_result.json`.

### 11.10 Step 9: Evaluate expected versus actual

Database execution and QA evaluation are different states.

An MCP response with `success=true` means the database accepted and executed the SQL. It does not mean the business requirement passed.

The agent compares the actual result with the expected result and assigns an explicit validation status:

| Status | Meaning |
|---|---|
| `passed` | The actual evidence satisfies the expected outcome. |
| `failed` | The actual evidence does not satisfy the expected outcome. |
| `executed_not_evaluated` | SQL ran successfully, but expected-versus-actual evaluation is incomplete. |
| `execution_failed` | The SQL did not execute successfully. |

### 11.11 Step 10: Correct and selectively rerun failures

If a query fails because of incorrect SQL, schema names, or column names:

1. inspect the actual metadata;
2. correct only the affected query;
3. explain the correction;
4. ask for approval again;
5. rerun only the failed or changed check; and
6. update the structured evidence and logs.

A successful retry must not erase the history of the earlier failure from the operational log.

### 11.12 Step 11: Approve report output

The user chooses one format:

| Format | Result |
|---|---|
| `json_only` | Keep `execution_result.json`; create no HTML or Excel report. |
| `html` | Create `output/<ticket-id>/report.html`. |
| `excel` | Create `output/<ticket-id>/report.xlsx`. |
| `both` | Create both final report files. |

HTML or Excel generation must not occur before the user chooses the format.

### 11.13 Step 12: Export the report

Examples:

```powershell
.\.venv\Scripts\python.exe .\scripts\export_results.py ABC-123 --format json_only
.\.venv\Scripts\python.exe .\scripts\export_results.py ABC-123 --format html
.\.venv\Scripts\python.exe .\scripts\export_results.py ABC-123 --format excel
.\.venv\Scripts\python.exe .\scripts\export_results.py ABC-123 --format both
```

The exporter reads the saved JSON evidence. It does not call Jira, an MCP server, or a database.

## 12. Human Approval Requirements

Human approval is a product requirement, not an optional conversational preference.

| Checkpoint | Required before | Evidence location |
|---|---|---|
| Ticket context approval | QA planning | `approvals/approval_log.md` |
| SQL approval | Executing each new or changed SQL statement | `approvals/approval_log.md` |
| Profile or environment approval | Every database profile/system switch | `approvals/approval_log.md` |
| Export approval | Creating final HTML or Excel reports | `approvals/approval_log.md` |

The agent must pause at these checkpoints. A previous approval does not automatically approve later changes.

## 13. Database MCP Subsystem

### 13.1 Role in the project

The `MCP/` folder contains the reusable database execution subsystem. It gives MCP-compatible AI clients one stable tool interface across multiple database systems.

It is intentionally independent from Jira and ticket orchestration.

### 13.2 Supported connectors

The current connector registry supports:

- `demo`;
- `postgresql`;
- `snowflake`;
- `mysql`; and
- `sqlserver`.

The demo connector supports offline setup and testing without database credentials.

### 13.3 Main MCP capabilities

The MCP server exposes tools for:

- listing safe database profile information;
- reloading configuration;
- switching profiles with confirmation;
- returning redacted diagnostics;
- testing connections;
- checking connector health;
- listing databases;
- listing tables;
- describing table columns;
- suggesting likely column names;
- executing one approved SQL statement; and
- returning structured results and errors.

The exact tool names, response contracts, profile configuration, AI-client setup, and connector extension process are documented in [MCP.md](MCP.md).

### 13.4 MCP boundary rules

- Jira logic must stay outside `MCP/`.
- Ticket artifacts must stay outside `MCP/`.
- Reports and workflow logs must stay outside `MCP/`.
- Database drivers must remain inside their connector boundary.
- Credentials must not be included in MCP tool output.
- Database permissions remain the final execution boundary.

## 14. Execution Result Contract

The recommended `execution_result.json` structure is:

```json
{
  "schema_version": "1.0",
  "ticket_id": "ABC-123",
  "summary": {
    "status": "validation_passed"
  },
  "query_results": [
    {
      "check_id": "CHECK-1",
      "execution_success": true,
      "validation_status": "passed",
      "expected": "No duplicate active records",
      "actual": "0 duplicate records",
      "metadata": {
        "profile": "postgres-test"
      },
      "row_count": 1,
      "rows": [
        {
          "duplicate_count": 0
        }
      ]
    }
  ],
  "errors": []
}
```

The exporter also accepts supported raw MCP response shapes, but raw execution success is reported as `executed_not_evaluated` until an explicit QA evaluation is added.

The result must not contain credentials, tokens, private keys, or secret-bearing connection strings.

## 15. Report Generation

### 15.1 HTML reports

HTML reports are generated with Python standard-library functionality. Dynamic content is HTML-escaped before it is written.

### 15.2 Excel reports

Excel reports use `openpyxl`, declared separately in `requirements-e2e.txt` because spreadsheet reporting belongs to the outer QA workflow rather than the database MCP server.

Excel output protects against formula injection and removes invalid control characters from cell content.

### 15.3 Report validation and safety

Before creating a report, the exporter:

- confirms the execution-result file exists;
- confirms the file contains valid JSON;
- verifies a declared ticket ID matches the requested run;
- rejects unfinished empty evidence for HTML or Excel output;
- redacts credential-like keys and values;
- builds QA summary counts from actual result statuses; and
- writes generated output under `output/<ticket-id>/`.

## 16. Logging And Auditability

All workflow and execution activity is recorded under the single root-level logs folder:

```text
logs/<ticket-id>.log
```

Logs should record:

- timestamps;
- ticket initialization;
- Jira retrieval activity;
- context updates;
- approval outcomes;
- profile switches using non-secret profile names;
- executed check IDs;
- execution outcomes;
- evaluation activity;
- corrections and retries; and
- report export activity.

Logs must not record:

- passwords;
- access tokens;
- private keys;
- secret connection strings;
- full credential configuration; or
- sensitive values that are not required for auditing the QA workflow.

## 17. Security Requirements

### 17.1 Credential handling

- Store local database credentials only in ignored `MCP/.env` configuration or an approved secret manager.
- Never commit `MCP/.env`.
- Never request that a user paste credentials into chat.
- Never store credentials in ticket artifacts, logs, JSON results, or reports.
- Keep OAuth and Atlassian authentication outside committed files.

### 17.2 Least privilege

Every database profile should use the least privilege required for its QA checks. Validation should normally use approved test or staging environments.

Database account permissions are the final authority. The MCP server cannot bypass permissions denied by the database.

### 17.3 SQL safety

- Prefer read-only validation SQL.
- Require approval before execution.
- Execute one statement per MCP call.
- Explain any DML or DDL separately.
- Do not automatically rewrite and rerun failed SQL without approval.
- Apply configured timeout and row limits.

### 17.4 Output safety

Reports can contain sensitive business data even when credentials are removed. Users must review outputs before sharing them outside the approved audience.

## 18. Functional Requirements

| ID | Requirement |
|---|---|
| FR-01 | The system shall accept a Jira ticket key or equivalent run identifier. |
| FR-02 | The system shall create a stable, safely normalized ticket-run path. |
| FR-03 | The agent shall retrieve Jira context through Atlassian MCP. |
| FR-04 | The system shall preserve organized ticket context in `ticket_context.md`. |
| FR-05 | The workflow shall require context approval before QA planning. |
| FR-06 | The agent shall create a QA plan containing checks and expected outcomes. |
| FR-07 | Proposed SQL shall map to stable check IDs. |
| FR-08 | The workflow shall require approval before every new or changed SQL execution. |
| FR-09 | The workflow shall require approval before every database profile or environment switch. |
| FR-10 | Database operations shall be performed through the database MCP server. |
| FR-11 | Each MCP query call shall contain one approved SQL statement. |
| FR-12 | Execution evidence shall be stored as structured JSON. |
| FR-13 | Execution success and QA validation status shall remain separate. |
| FR-14 | Failed or corrected checks shall support selective rerun after reapproval. |
| FR-15 | All operational logs shall be stored under root `logs/`. |
| FR-16 | Ticket folders shall not contain logs or final report output. |
| FR-17 | Final reports shall be stored under `output/<ticket-id>/`. |
| FR-18 | HTML and Excel export shall require an explicit user format choice. |
| FR-19 | Report generation shall redact credential-like values. |
| FR-20 | The database layer shall support extension through additional connectors. |

## 19. Non-Functional Requirements

### 19.1 Safety

The system must fail clearly when configuration, paths, SQL structure, evidence, or dependencies are invalid. It must not silently continue past required approval gates.

### 19.2 Auditability

Every check should be traceable from requirement to QA plan, proposed SQL, approval, MCP response, validation status, and final report.

### 19.3 Maintainability

Workflow logic, report helpers, MCP tools, services, validation, and database connectors must remain separated. A new connector should not require a new outer workflow.

### 19.4 Portability

The database server uses MCP over standard input/output and can be used by different compatible AI clients. Files use relative repository structure rather than developer-specific committed paths.

### 19.5 Reliability

Ticket initialization must be idempotent. Report generation must validate its input, and temporary report files must not replace final files until writing succeeds.

### 19.6 Testability

Normal automated tests should not require live Jira access or a live external database. Live connectivity tests should remain explicit and opt-in.

## 20. First-Time Setup

### 20.1 Prerequisites

The operator or developer needs:

- repository access;
- Git;
- Python 3.12 or another compatible Python 3 version;
- PowerShell for the provided Windows scripts;
- VS Code or another MCP-compatible AI client;
- permission to use the required Atlassian site;
- database access for any live profiles; and
- required operating-system database drivers, such as Microsoft ODBC Driver 18 for SQL Server.

### 20.2 Clone and open the complete project

Clone the repository and open its root, not only the `MCP/` subfolder:

```powershell
git clone <repository-url>
cd <repository-folder>
code .
```

### 20.3 Create the Python environment

From the repository root:

```powershell
PowerShell -ExecutionPolicy Bypass -File .\MCP\scripts\setup.ps1
```

The setup script creates or repairs the root `.venv`, installs database MCP dependencies from `MCP/requirements.txt`, and installs report dependencies from `requirements-e2e.txt`.

### 20.4 Create local MCP configuration

Create `MCP/.env` from the safe example if it does not already exist:

```powershell
if (-not (Test-Path .\MCP\.env)) {
    Copy-Item .\MCP\.env.example .\MCP\.env
}
```

Start with the offline demo profile. Configure live named profiles only through the approved local or managed-secret process.

### 20.5 Confirm MCP workspace configuration

`.vscode/mcp.json` defines:

- the remote Atlassian MCP endpoint; and
- the local database MCP command using `.venv\Scripts\python.exe`, `MCP\server.py`, and `MCP` as its working directory.

After changing MCP configuration, restart or reload the AI client so it rediscovers the tools.

### 20.6 Authenticate Atlassian

Start the Atlassian MCP server from the AI client and complete the browser authentication flow using the account authorized for the required Jira site.

OAuth tokens must not be placed in the repository.

### 20.7 Verify the installation

Run:

```powershell
PowerShell -ExecutionPolicy Bypass -File .\MCP\scripts\verify.ps1
```

The verification pipeline compiles tracked Python files, runs MCP tests, runs an offline demo smoke test, and runs outer workflow helper tests.

## 21. Normal Operating Procedure

1. Read `Basic_Instructions.md` completely.
2. Confirm Atlassian MCP and the database MCP server are available.
3. Obtain the Jira ticket key.
4. Initialize the ticket run.
5. Retrieve and save Jira context.
6. Stop for context approval.
7. Create the QA plan and proposed SQL.
8. Stop for SQL approval.
9. Confirm and approve the required database profile.
10. Inspect metadata where needed.
11. Execute one approved statement at a time.
12. Save each response and evaluate expected versus actual.
13. Correct and reapprove only failed queries where necessary.
14. Ask the user to choose the export format.
15. Generate the approved report.
16. Confirm source evidence, log, and output are stored in their correct locations.

## 22. Error Handling And Recovery

### 22.1 Atlassian tools are unavailable

- Confirm the Atlassian server is running in the AI client.
- Confirm browser login completed successfully.
- Restart or reload the AI client if the server was added after the session started.
- Do not invent missing Jira context.

### 22.2 Database MCP tools are unavailable

- Confirm `.vscode/mcp.json` points to the correct `.venv` and `MCP/server.py`.
- Confirm the working directory is `MCP`.
- Run the verification script.
- Restart the MCP server and AI client.

### 22.3 A profile is not ready

- List profiles and inspect safe readiness issues.
- Correct `MCP/.env` without exposing credentials.
- Reload MCP configuration with confirmation or restart the MCP process.
- Test the connection before running QA SQL.

### 22.4 A query references an incorrect column

- Describe the real table through MCP metadata tools.
- Use column suggestions when appropriate.
- Correct only the failed SQL.
- Ask for approval again.
- Rerun only affected checks.

### 22.5 A report cannot be generated

- Confirm `execution_results/execution_result.json` exists and contains valid JSON.
- Confirm the ticket ID matches the requested export.
- Confirm execution evidence or errors are present.
- Install `requirements-e2e.txt` for Excel output.
- Confirm the target output file is not locked by another application.

## 23. Testing And Quality Gates

### 23.1 Outer workflow tests

`tests/test_e2e_helpers.py` verifies:

- ticket ID normalization and collision resistance;
- idempotent ticket initialization;
- stable artifact locations;
- absence of ticket-local logs and output;
- QA status calculation;
- evidence validation;
- recursive sensitive-value redaction;
- HTML escaping;
- Excel formula protection;
- HTML and Excel output generation; and
- the end-to-end helper flow using temporary test directories.

### 23.2 MCP tests

`MCP/tests/` verifies configuration, connectors, connector registration, service behavior, profile switching, SQL guardrails, response models, architecture boundaries, tool wrappers, limits, diagnostics, and demo behavior.

### 23.3 Live system testing

Normal automated tests should use mocks or the demo connector. Live Jira and database tests require explicit credentials, network access, approved environments, and operator intent.

## 24. Extensibility

### 24.1 Adding a database connector

New database systems are added inside `MCP/connectors/` by implementing the shared connector interface, registering the connector, adding its driver, adding tests, and documenting profile requirements.

The complete connector procedure is in [MCP.md](MCP.md).

### 24.2 Adding a report format

A new report format should:

- read the same structured execution evidence;
- preserve sensitive-value redaction;
- validate ticket ownership and evidence completeness;
- write only under `output/<ticket-id>/`;
- require explicit user approval; and
- include focused tests.

### 24.3 Adding another requirement source

A future source such as another ticketing system may be added to the outer workflow. It must not be embedded inside the database MCP server. The source adapter should produce the same organized ticket-context artifact expected by the planning stage.

### 24.4 Adding another AI client

Any client that supports the required MCP transports can use the project if it can:

- connect to Atlassian MCP;
- launch the local database MCP server;
- read and write repository files;
- stop for user approvals; and
- preserve the documented artifact contract.

## 25. Known Boundaries And Limitations

- The AI agent currently coordinates the workflow; there is no standalone workflow dashboard.
- Jira retrieval depends on Atlassian authentication and account permissions.
- Live database execution depends on network access, drivers, profile configuration, and database permissions.
- The helper scripts do not call Jira or databases directly.
- Human approvals are workflow rules coordinated by the agent and recorded in files.
- JSON evidence must be evaluated explicitly before a successful query can be called a passed QA check.
- Generated reports may contain sensitive business data and require review before distribution.
- Root logs are local text evidence rather than a centralized enterprise observability platform.

These boundaries do not prevent future expansion, but future development should preserve the security and responsibility model unless it is deliberately redesigned and approved.

## 26. Final Acceptance Criteria

The complete project is considered ready for a controlled ticket run when:

1. A new developer can set up the environment from documented steps.
2. Atlassian MCP authentication can retrieve an authorized Jira ticket.
3. The database MCP server starts and exposes its expected tools.
4. The demo connector passes without live credentials.
5. Required live database profiles report ready before use.
6. A ticket ID creates the documented ticket-run structure.
7. No logs or final report folders are created inside the ticket directory.
8. The agent stops at every required approval checkpoint.
9. SQL is executed one approved statement at a time.
10. Raw evidence records execution success separately from validation status.
11. Failed SQL can be corrected, reapproved, and selectively rerun.
12. Shared activity is written to `logs/<ticket-id>.log`.
13. Approved reports are written to `output/<ticket-id>/`.
14. Credentials are absent from committed files, artifacts, logs, and reports.
15. Outer workflow and MCP tests pass.
16. MCP implementation remains reusable and independent from Jira-specific workflow logic.

## 27. Handoff Checklist

Before handing the project to another developer or team:

1. Confirm the repository contains no real `.env` or secret files.
2. Confirm `MCP/.env.example` uses only safe demo values.
3. Run `MCP/scripts/verify.ps1`.
4. Confirm `.vscode/mcp.json` uses repository-relative paths.
5. Confirm `Basic_Instructions.md` matches the current workflow.
6. Confirm `ticket_run_config.json` matches the documented artifact paths.
7. Confirm generated ticket runs, logs, and outputs are not committed.
8. Give the recipient this document for the project overview.
9. Give the recipient `MCP.md` for database subsystem setup and extension details.
10. Demonstrate one offline demo run before connecting to live systems.

## 28. Glossary

| Term | Meaning |
|---|---|
| AI agent | The AI client coordinating the QA workflow and using MCP tools. |
| Approval checkpoint | A required pause where a human authorizes the next action. |
| Artifact | A file produced or updated during a ticket run. |
| Connector | Database-specific implementation behind the common MCP interface. |
| Execution success | Confirmation that a SQL statement ran, not that the QA expectation passed. |
| Jira context | Ticket information used to understand and plan QA validation. |
| MCP | Model Context Protocol, used by AI clients to discover and call tools. |
| Named profile | A safe name referring to locally configured database connection settings. |
| QA plan | Document describing checks, expected outcomes, systems, and evidence requirements. |
| Ticket run | One complete QA workflow for one ticket or client request. |
| Validation status | Explicit expected-versus-actual QA result such as passed or failed. |

## 29. Documentation Map

Use the project documentation in this order:

1. **`docs/qa_automation.md`** - understand the complete product, architecture, requirements, setup, workflow, and final design.
2. **`Basic_Instructions.md`** - follow the mandatory operating sequence and approval rules during an actual ticket run.
3. **`docs/MCP.md`** - configure, operate, troubleshoot, and extend the database MCP subsystem.
4. **`ticket_run_config.json`** - inspect the machine-readable workflow paths, statuses, formats, and approval checkpoints.
