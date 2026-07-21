# QA Automation Project

## Product Requirements and Design Document

| Document field | Value |
|---|---|
| Project | QA Automation |
| Document purpose | Complete project explanation, product requirements, architecture, setup, operation, and future development guide |
| Primary audience | New developers, QA engineers, technical leads, AI-agent operators, and project stakeholders |
| Agent context entry point | `Basic_Instructions.md` |
| Client workflow location | `skills/<clientname>_QA_workflow.md` |
| Unsupported-work fallback | `skills/fallback.md` |
| Database subsystem documentation | `docs/MCP.md` |
| Current delivery model | Human-approved, AI-assisted QA workflow |

## 2. Executive Summary

The QA Automation project turns the requirements in a Jira ticket into a controlled QA validation run.

An AI agent coordinates the process. It first reads the permanent project instructions, selects an exact client-specific workflow from `skills/`, and then performs only the ticket, approval, database, evidence, and reporting steps defined by that workflow. If the client or ticket type is unsupported or ambiguous, the agent follows the fallback instructions instead of inventing a process.

The project is deliberately divided into separate responsibilities:

- **Atlassian MCP** provides Jira ticket information.
- **The AI agent** coordinates the workflow and prepares QA artifacts.
- **Client workflow skills** define the exact procedure for supported clients and ticket types.
- **The fallback skill** stops and escalates unsupported or ambiguous work.
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
2. Collect supporting attachments and linked documents, including files behind credential-protected links.
3. Translate the complete available context into a QA plan.
4. Determine which database systems contain the relevant evidence.
5. Inspect database schemas and column names.
6. Write validation SQL.
7. Review the SQL for correctness and safety.
8. Run the SQL against the correct environment.
9. Compare actual results with expected results.
10. Save evidence and explain failures.
11. Produce a report that another person can understand.

When these steps are performed informally, important context can be lost. Queries may be executed against the wrong system, approval decisions may not be recorded, raw execution success may be mistaken for a passed QA check, and results may not be reproducible.

This project standardizes that process while keeping a human in control.

## 4. Product Vision

The final working QA Automation system should allow an authorized user to provide a Jira ticket key and guide an AI agent through a repeatable, auditable workflow that produces reliable QA evidence and a clear final report.

The finished system should:

- understand the available Jira requirement context;
- accept local copies of Jira attachments and linked documents that the agent cannot access directly;
- keep external source files separate from workflow-generated artifacts;
- create consistent ticket-scoped working files;
- require human approval at high-impact checkpoints;
- support multiple database systems through one MCP interface;
- keep credentials outside prompts and generated artifacts;
- preserve raw evidence separately from final reports;
- clearly distinguish query execution from QA validation;
- allow failed SQL to be corrected, reapproved, and selectively rerun;
- produce structured JSON evidence;
- optionally produce HTML and Excel reports;
- support future database connectors without redesigning the workflow;
- support different client procedures without changing the permanent project instructions; and
- remain understandable to a new developer or operator.

## 5. Product Goals

### 5.1 Primary goals

1. Convert Jira requirements into specific and reviewable QA checks.
2. Make database validation available to MCP-compatible AI agents.
3. Require explicit human approval before SQL execution and environment changes.
4. Store external ticket inputs and generated QA evidence in separate, stable locations.
5. Make credential-protected supporting content available through authorized local downloads without giving credentials to the agent.
6. Keep operational logs and final reports in clearly separate locations.
7. Support PostgreSQL, Snowflake, MySQL, SQL Server, and an offline demo system through one MCP tool interface.
8. Produce results that can be audited, evaluated, and shared.
9. Make the system extensible for future connectors and broader QA workflows.
10. Prevent unsupported tickets from being processed through an assumed or hallucinated workflow.

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

- permanent AI-agent orientation and repository-boundary instructions;
- a client workflow template based on the tested E2E procedure;
- explicit fallback instructions for unknown or unsupported work;
- Atlassian MCP workspace configuration;
- a reusable database MCP server;
- named database profile handling;
- demo, PostgreSQL, Snowflake, MySQL, and SQL Server connectors;
- connection, metadata, diagnostics, profile, and query tools;
- SQL structural guardrails;
- ticket-run folder initialization;
- safe ticket ID normalization;
- separate `downloads/` and `generated/` ticket workspaces;
- a local-file fallback for supporting Jira content the agent cannot access directly;
- stable generated-artifact paths;
- root-level workflow logs;
- structured execution-result storage;
- HTML and Excel report generation;
- sensitive-field redaction during report generation;
- HTML escaping and Excel formula-injection protection;
- unit and workflow helper tests; and
- an offline demo connector for verification without a live database.

### 7.2 Current operating model

The current system is AI-assisted rather than a single unattended application.

The AI agent reads `Basic_Instructions.md` to recover its role and understand the repository. It then identifies and reads the exact `skills/<clientname>_QA_workflow.md` for the current ticket. If no exact workflow applies, it must follow `skills/fallback.md`. The outer workflow modules initialize folders and export saved data, but they do not select workflows, retrieve Jira tickets, or execute database queries themselves.

### 7.3 Intended final development

The final working development should preserve the same boundaries while making the workflow consistently repeatable for every ticket. Regardless of the future AI client, user interface, scheduler, or deployment platform, the system should continue to enforce:

- one ticket-scoped working area per run;
- one explicitly selected and approved client workflow per run;
- controlled fallback instead of guessed behavior for unsupported work;
- a clear boundary between external source files and generated workflow artifacts;
- an authorized local-download fallback for inaccessible supporting content;
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
                    | reads project rules  |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    | Client workflow skill|
                    | or fallback/escalate |
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

ticket_runs/<ticket-id>/                 logs/<ticket-id>.log   output/<ticket-id>/
downloads/ + generated/ workspace          shared activity log    final reports
```

### 8.2 Responsibility boundaries

| Component | Responsible for | Not responsible for |
|---|---|---|
| Human operator | Confirming client identity where needed, reviewing context, downloading protected source files through an authorized session, and making approvals required by the client workflow | Giving credentials to the agent or manually implementing every database connector operation |
| AI agent | Recovering project context, selecting an exact client workflow, coordinating approved work, and using fallback when coverage is uncertain | Inventing workflow rules or bypassing approvals, credentials, and database permissions |
| Client workflow skill | Defining supported ticket types, exact QA steps, approvals, systems, evidence, and outputs for one client | Overriding project-wide security and folder boundaries |
| Task-specific agent skill | Teaching the agent how to perform a reusable specialized task or use a project capability | Selecting a client workflow or overriding its instructions |
| Fallback skill | Stopping and escalating unknown, ambiguous, conflicting, or unsupported work | Acting as permission to continue with a guessed workflow |
| Atlassian MCP | Retrieving Jira context available to the authenticated user | Database execution or report generation |
| Database MCP in `MCP/` | Profile operations, connection checks, metadata inspection, approved SQL execution | Jira interpretation, QA pass/fail decisions, or ticket report ownership |
| Database connector | Database-specific connections, metadata SQL, timeouts, row limits, and execution | Workflow orchestration |
| Workflow modules | Creating local ticket structure and exporting saved results | Calling Jira, MCP tools, or databases |
| Ticket `downloads/` | Preserving unmodified external files associated with the ticket | Holding AI-generated or workflow-generated artifacts |
| Ticket `generated/` | Preserving AI-generated workflow state and raw QA evidence | Holding external source documents, operational logs, or final reports |
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
|-- modules/
|   |-- __init__.py
|   |-- init_ticket_run.py
|   `-- export_results.py
|-- skills/
|   |-- QA_workflow_TEMPLATE.md
|   `-- fallback.md
|-- tests/
|   `-- test_e2e_helpers.py
|-- ticket_runs/
|-- requirements-e2e.txt
`-- ticket_run_config.json
```

### 9.1 Top-level files and folders

| Path | Purpose |
|---|---|
| `Basic_Instructions.md` | Permanent AI-agent role, repository map, folder contract, workflow-selection logic, safety boundaries, and context-recovery instructions. |
| `docs/qa_automation.md` | This project-wide PRD and handoff document. |
| `docs/MCP.md` | Detailed documentation for the reusable database MCP subsystem. |
| `MCP/` | Database MCP implementation, connectors, services, tools, configuration, and tests. |
| `ticket_runs/` | Ticket-scoped workspaces containing external inputs under `downloads/` and workflow artifacts under `generated/`. Generated ticket folders are not committed. |
| `logs/` | Shared workflow and execution logs, one file per ticket run. |
| `output/` | Final generated reports organized by ticket ID. |
| `modules/` | Reusable outer-workflow Python modules for ticket initialization and result export. |
| `skills/` | Exact client workflows, reusable task-specific agent skills, a non-executable workflow template, and fallback instructions. |
| `tests/` | Tests for the outer workflow helpers. |
| `ticket_run_config.json` | Machine-readable shared paths, statuses, formats, and baseline control definitions. |
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
|-- downloads/
|   |-- requirements.pdf
|   |-- supporting-data.xlsx
|   `-- <other external ticket files>
`-- generated/
    |-- ticket_context.md
    |-- qa_plan.md
    |-- generated_sql/
    |   `-- generated_queries.sql
    |-- approvals/
    |   `-- approval_log.md
    `-- execution_results/
        `-- execution_result.json
```

The example files under `downloads/` are illustrative only. The initializer creates the empty folder but does not create fake external inputs.

No `logs/` or `output/` folder should be created inside a ticket directory. Operational logs remain under root `logs/`, and final reports remain under root `output/`.

### 10.3 Artifact definitions

| Artifact | Purpose | Created or updated by |
|---|---|---|
| `downloads/<source-file>` | Original external content associated with Jira, including attachments or local copies of protected linked documents | Authorized user or an agent that can legitimately access the source |
| `generated/ticket_context.md` | Organized Jira summary plus relevant context extracted from local downloaded files | AI agent using Atlassian MCP and `downloads/` |
| `generated/qa_plan.md` | QA objectives, checks, expected outcomes, required systems, and profile needs | AI agent after context approval |
| `generated/generated_sql/generated_queries.sql` | Proposed SQL mapped to stable QA check IDs | AI agent before SQL approval |
| `generated/approvals/approval_log.md` | Human approval and rejection history for required checkpoints | AI agent recording user decisions |
| `generated/execution_results/execution_result.json` | Structured raw database evidence and explicit QA evaluation | AI agent using database MCP responses |
| `logs/<ticket-id>.log` | Non-secret workflow, profile, execution, evaluation, and export activity | Initializer and AI agent |
| `output/<ticket-id>/report.html` | Final browser-readable report | Export helper after approval |
| `output/<ticket-id>/report.xlsx` | Final spreadsheet report | Export helper after approval |

### 10.4 Downloads are external inputs

`downloads/` exists because an AI agent may be unable to open a Jira attachment or linked document that requires a separate authenticated browser session, VPN, client portal, or other credential-protected access.

When that happens:

1. The agent identifies the inaccessible source and explains why it matters.
2. The authorized user opens the source using their own approved session.
3. The user downloads the file and places it in `ticket_runs/<ticket-id>/downloads/`.
4. The agent inventories and reads the supported local file.
5. Relevant information is incorporated into `generated/ticket_context.md`, with the source filename recorded for traceability.

The user must not give credentials, session cookies, access tokens, or private links containing secrets to the agent. Downloaded files should retain meaningful filenames where practical, must not be overwritten silently, and must be handled according to company data-classification and malware-scanning policy.

### 10.5 Generated contains workflow outputs

`generated/` contains only artifacts produced or maintained by the QA automation workflow. External PDFs, Word documents, spreadsheets, images, and similar source files do not belong there.

This separation makes it clear which material came from outside the system and which material represents the system's interpretation, plan, approvals, SQL, and evidence.

### 10.6 Why raw evidence and final output are separate

`generated/execution_results/execution_result.json` is the source evidence. It contains the structured data needed to audit or regenerate a report.

HTML and Excel files are presentation outputs. They may summarize or format the evidence for a stakeholder. Keeping them under `output/<ticket-id>/` prevents a final report from being confused with source workflow state.

## 11. Client-Selected QA Workflow

`Basic_Instructions.md` does not contain the exact ticket procedure. It tells the agent how to recover project context, understand folder ownership, and select the correct skill.

Every live run must use one exact, approved file named `skills/<clientname>_QA_workflow.md`. The repository's `skills/QA_workflow_TEMPLATE.md` preserves the initially tested E2E procedure as a customization starting point, but it is not an active workflow and must never be selected for a live ticket.

If the client cannot be identified, an exact client workflow is absent, the ticket type is unsupported, or instructions conflict, the agent must open `skills/fallback.md`, stop client-specific work, and escalate to the project manager or designated QA workflow owner.

### 11.1 Workflow summary

```text
Read Basic_Instructions.md
      |
      v
Identify client and ticket type
      |
      v
Exact approved client workflow available and applicable?
      | Yes                         | No or uncertain
      v                             v
Read complete client skill    Read skills/fallback.md
      |                             |
      v                             v
Initialize ticket run         Stop and escalate
      |
      v
Retrieve authorized Jira context through Atlassian MCP
      |
      v
Identify Jira attachments and supporting links
      |
      v
Agent cannot access a protected source? User downloads it to downloads/
      |
      v
Review local source files and save generated/ticket_context.md
      |
      v
HUMAN APPROVAL: context is complete
      |
      v
Create generated/qa_plan.md and generated SQL
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
Save and evaluate generated/execution_results/execution_result.json
      |
      v
HUMAN APPROVAL: final export format
      |
      v
Generate output/<ticket-id>/ reports
```

The steps below document the tested reference process represented by `skills/QA_workflow_TEMPLATE.md`. An activated client workflow may add, remove, or refine workflow steps, but it cannot override the permanent security, credential, MCP, and folder boundaries in `Basic_Instructions.md`.

### 11.2 Step 1: Initialize the run

From the repository root:

```powershell
.\.venv\Scripts\python.exe .\modules\init_ticket_run.py ABC-123
```

The initializer:

- normalizes the ticket ID;
- creates the ticket directory with primary `downloads/` and `generated/` subdirectories;
- creates missing template artifacts without overwriting existing files;
- leaves `downloads/` empty until real external ticket files are added;
- creates `logs/<ticket-id>.log` if it does not exist;
- does not create a ticket-local logs folder;
- does not create a ticket-local output folder;
- does not contact Jira;
- does not contact an MCP server; and
- does not connect to a database.

The initializer is idempotent. Running it again does not overwrite completed work.

### 11.3 Step 2: Retrieve Jira and supporting context

The user supplies a Jira ticket key. The AI agent uses Atlassian MCP to retrieve the ticket information visible to the authenticated Atlassian account.

Relevant context can include:

- summary;
- description;
- acceptance criteria;
- comments;
- linked issues;
- attachments and linked supporting documents;
- labels and priority;
- available project context; and
- information needed to define QA checks.

If the agent cannot access a credential-protected link or attachment, it asks the authorized user to download the file through their own session and place it under `ticket_runs/<ticket-id>/downloads/`. The agent must not ask for the user's credentials, tokens, or session data.

The agent inventories supported files in `downloads/`, extracts relevant context, and notes any file it cannot safely read. The combined organized context is saved to `generated/ticket_context.md`, with downloaded filenames referenced where they support a requirement.

### 11.4 Step 3: Approve ticket context

The AI agent must stop and ask the user whether the saved context is complete enough for planning.

The user may approve it, add missing information, ask the agent to retrieve the Jira ticket again, or place additional protected source files in `downloads/`. QA planning cannot begin until the context is explicitly approved.

The decision is recorded in `generated/approvals/approval_log.md`.

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

The plan is saved to `generated/qa_plan.md`.

### 11.6 Step 5: Inspect metadata and prepare SQL

When schema details are uncertain, the agent should use database MCP metadata tools before writing SQL. It should inspect available databases, tables, and columns rather than guessing names.

Proposed SQL is saved to `generated/generated_sql/generated_queries.sql`. Every statement must map to a stable check ID.

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

Each response is associated with its stable check ID and stored in `generated/execution_results/execution_result.json`.

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
| `json_only` | Keep `generated/execution_results/execution_result.json`; create no HTML or Excel report. |
| `html` | Create `output/<ticket-id>/report.html`. |
| `excel` | Create `output/<ticket-id>/report.xlsx`. |
| `both` | Create both final report files. |

HTML or Excel generation must not occur before the user chooses the format.

### 11.13 Step 12: Export the report

Examples:

```powershell
.\.venv\Scripts\python.exe .\modules\export_results.py ABC-123 --format json_only
.\.venv\Scripts\python.exe .\modules\export_results.py ABC-123 --format html
.\.venv\Scripts\python.exe .\modules\export_results.py ABC-123 --format excel
.\.venv\Scripts\python.exe .\modules\export_results.py ABC-123 --format both
```

The exporter reads the saved JSON evidence. It does not call Jira, an MCP server, or a database.

## 12. Reference Human Approval Requirements

Each active client workflow must declare its exact approval checkpoints. The tested reference workflow in `skills/QA_workflow_TEMPLATE.md` uses the checkpoints below. A client workflow may add or refine checkpoints, but it cannot bypass MCP confirmations, database permissions, or permanent safety controls.

| Checkpoint | Required before | Evidence location |
|---|---|---|
| Ticket context approval | QA planning | `generated/approvals/approval_log.md` |
| SQL approval | Executing each new or changed SQL statement | `generated/approvals/approval_log.md` |
| Profile or environment approval | Every database profile/system switch | `generated/approvals/approval_log.md` |
| Export approval | Creating final HTML or Excel reports | `generated/approvals/approval_log.md` |

When these checkpoints apply, the agent must pause. A previous approval does not automatically approve later changes.

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

The recommended structure for `ticket_runs/<ticket-id>/generated/execution_results/execution_result.json` is:

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

### 17.2 Downloaded source files

- Do not ask users to share credentials, tokens, cookies, or authenticated URLs with the AI agent.
- Ask an authorized user to download inaccessible Jira-linked content through their own approved session.
- Store the resulting source file only under the ticket's `downloads/` folder.
- Treat downloaded files as untrusted until they satisfy company malware-scanning and data-handling policy.
- Preserve source files without silently overwriting or modifying them.
- Do not commit ticket downloads to Git.

### 17.3 Least privilege

Every database profile should use the least privilege required for its QA checks. Validation should normally use approved test or staging environments.

Database account permissions are the final authority. The MCP server cannot bypass permissions denied by the database.

### 17.4 SQL safety

- Prefer read-only validation SQL.
- Require approval before execution.
- Execute one statement per MCP call.
- Explain any DML or DDL separately.
- Do not automatically rewrite and rerun failed SQL without approval.
- Apply configured timeout and row limits.

### 17.5 Output safety

Reports can contain sensitive business data even when credentials are removed. Users must review outputs before sharing them outside the approved audience.

## 18. Functional Requirements

| ID | Requirement |
|---|---|
| FR-01 | The system shall accept a Jira ticket key or equivalent run identifier. |
| FR-02 | The system shall create a stable, safely normalized ticket-run path with `downloads/` and `generated/` as its primary subfolders. |
| FR-03 | The system shall support authorized Jira context retrieval through Atlassian MCP when required by the selected client workflow. |
| FR-04 | The workflow shall support authorized local copies of inaccessible Jira attachments and links under `downloads/` without collecting user credentials. |
| FR-05 | The workflow shall keep external source files in `downloads/` and system-produced artifacts in `generated/`. |
| FR-06 | The system shall support organized ticket context in `generated/ticket_context.md` when required by the selected client workflow. |
| FR-07 | Each client workflow shall define its required context review and approval behavior. |
| FR-08 | Each client workflow shall define its required QA plan, checks, and expected outcomes. |
| FR-09 | Proposed SQL shall map to stable check IDs whenever database validation applies. |
| FR-10 | The workflow shall require approval before every new or changed SQL execution. |
| FR-11 | Database profile or environment switches shall satisfy both the selected client workflow and MCP confirmation requirements. |
| FR-12 | Database operations shall be performed through the database MCP server. |
| FR-13 | Each MCP query call shall contain one approved SQL statement. |
| FR-14 | Database execution evidence shall be stored as structured JSON under `generated/` whenever database validation applies. |
| FR-15 | Execution success and QA validation status shall remain separate. |
| FR-16 | Client workflows using database validation shall define correction, reapproval, and selective-rerun behavior. |
| FR-17 | All operational logs shall be stored under root `logs/`. |
| FR-18 | Ticket folders shall not contain logs or final report output. |
| FR-19 | Final reports shall be stored under `output/<ticket-id>/`. |
| FR-20 | Each client workflow shall define allowed report formats and required export approval. |
| FR-21 | Report generation shall redact credential-like values. |
| FR-22 | The database layer shall support extension through additional connectors. |
| FR-23 | The agent shall read `Basic_Instructions.md` when starting, resuming, or recovering context. |
| FR-24 | Every active client workflow shall be stored as `skills/<clientname>_QA_workflow.md`. |
| FR-25 | The agent shall confirm that the selected client workflow covers the current ticket type before performing client-specific work. |
| FR-26 | The agent shall follow `skills/fallback.md` when workflow selection or coverage is missing, ambiguous, conflicting, or unsupported. |
| FR-27 | `skills/QA_workflow_TEMPLATE.md` shall remain a non-executable template until customized, renamed, and approved for a client. |
| FR-28 | The `skills/` folder shall support reusable task-specific agent skills that remain subordinate to the permanent instructions and selected client workflow. |

## 19. Non-Functional Requirements

### 19.1 Safety

The system must fail clearly when client workflow selection, ticket coverage, configuration, paths, SQL structure, evidence, or dependencies are invalid. It must not silently continue past required approval gates or improvise an unsupported process.

### 19.2 Auditability

Every check should be traceable from requirement to QA plan, proposed SQL, approval, MCP response, validation status, and final report.

### 19.3 Maintainability

Permanent agent instructions, client workflow skills, fallback behavior, workflow modules, MCP tools, services, validation, and database connectors must remain separated. Client workflow changes should not require MCP changes, and a new connector should not require rewriting the permanent agent instructions.

Every source file must preserve the collapsible code-documentation convention: labeled module setup, class, function, entry-point, and nontrivial internal sections; purpose-specific module/class/function docstrings; and balanced regions. `tests/test_code_documentation.py` enforces the structural parts of this convention.

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

### 20.8 Add an approved client workflow

The repository intentionally ships with a non-executable template rather than an assumed client procedure. Before a live run:

1. Copy `skills/QA_workflow_TEMPLATE.md` to `skills/<clientname>_QA_workflow.md`.
2. Replace the template fields and reference steps with confirmed client requirements.
3. Define supported ticket types and every condition that must route to fallback.
4. Obtain approval from the project manager or designated QA workflow owner.
5. Test both a supported ticket and an unsupported ticket before using live systems.

Do not rename the template itself or use it directly for a live ticket.

## 21. Normal Operating Procedure

1. Read `Basic_Instructions.md` completely.
2. Establish the ticket ID, client identity, and ticket type from authoritative information.
3. Find an exact `skills/<clientname>_QA_workflow.md` and verify that it covers the ticket type.
4. If selection or coverage is uncertain, open `skills/fallback.md`, stop, and escalate.
5. Read the selected client workflow completely and state which workflow is active.
6. Confirm the tools and systems required by that workflow are available.
7. Initialize and use the ticket workspace according to the shared folder contract.
8. Follow the selected client workflow's exact context, planning, approval, execution, evaluation, and output steps.
9. Keep external inputs, generated artifacts, logs, and final reports in their assigned locations.
10. On context loss, repeat workflow selection and verify the last approved state before continuing.

## 22. Error Handling And Recovery

### 22.1 The client workflow is unknown or unsupported

- Open `skills/fallback.md`.
- Stop before client-specific planning, SQL generation or execution, profile switching, and final report generation.
- Identify the unresolved client, ticket type, keyword, conflict, or missing context.
- Contact the project manager or designated QA workflow owner.
- Do not use the closest-looking workflow or the workflow template as a substitute.

### 22.2 Atlassian tools are unavailable

- Confirm the Atlassian server is running in the AI client.
- Confirm browser login completed successfully.
- Restart or reload the AI client if the server was added after the session started.
- Do not invent missing Jira context.

### 22.3 A Jira attachment or supporting link is inaccessible

- Do not ask for or store the user's credentials, session cookie, token, or authenticated URL.
- Ask an authorized user to download the source through their approved browser session.
- Place the original file under `ticket_runs/<ticket-id>/downloads/` using a meaningful filename.
- Apply company malware-scanning and data-handling requirements before opening it.
- Review the local file and cite its filename in `generated/ticket_context.md`.
- Record any file that cannot be safely or reliably read; do not invent its contents.

### 22.4 Database MCP tools are unavailable

- Confirm `.vscode/mcp.json` points to the correct `.venv` and `MCP/server.py`.
- Confirm the working directory is `MCP`.
- Run the verification script.
- Restart the MCP server and AI client.

### 22.5 A profile is not ready

- List profiles and inspect safe readiness issues.
- Correct `MCP/.env` without exposing credentials.
- Reload MCP configuration with confirmation or restart the MCP process.
- Test the connection before running QA SQL.

### 22.6 A query references an incorrect column

- Describe the real table through MCP metadata tools.
- Use column suggestions when appropriate.
- Correct only the failed SQL.
- Ask for approval again.
- Rerun only affected checks.

### 22.7 A report cannot be generated

- Confirm `ticket_runs/<ticket-id>/generated/execution_results/execution_result.json` exists and contains valid JSON.
- Confirm the ticket ID matches the requested export.
- Confirm execution evidence or errors are present.
- Install `requirements-e2e.txt` for Excel output.
- Confirm the target output file is not locked by another application.

## 23. Testing And Quality Gates

### 23.1 Outer workflow tests

`tests/test_e2e_helpers.py` verifies:

- ticket ID normalization and collision resistance;
- idempotent ticket initialization;
- creation of the two primary ticket folders, `downloads/` and `generated/`;
- stable generated-artifact locations;
- preservation of an empty input-only `downloads/` folder until real sources are added;
- absence of ticket-local logs and output;
- QA status calculation;
- evidence validation;
- recursive sensitive-value redaction;
- HTML escaping;
- Excel formula protection;
- HTML and Excel output generation; and
- the end-to-end helper flow using temporary test directories.

`tests/test_code_documentation.py` verifies module docstrings, class and function docstrings, collapsible region coverage, and balanced Python and PowerShell regions across the repository.

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

### 24.5 Adding a client workflow

To onboard a client:

1. Copy `skills/QA_workflow_TEMPLATE.md` to `skills/<clientname>_QA_workflow.md` using the approved client identifier.
2. Define authoritative client-identification rules, supported Jira projects, ticket types, and routing keywords.
3. Replace template assumptions with the client's required context, systems, checks, approvals, evidence, reports, and escalation contacts.
4. Confirm that the workflow respects `Basic_Instructions.md` and does not embed client logic inside `MCP/` or `modules/`.
5. Have the project manager or designated QA workflow owner approve the workflow before activation.
6. Test the client workflow against representative non-production tickets, including at least one unsupported case that must route to `skills/fallback.md`.

Never make the template itself active, and never create a client workflow by guessing from one ticket.

## 25. Known Boundaries And Limitations

- The AI agent currently coordinates the workflow; there is no standalone workflow dashboard.
- Client workflow selection currently depends on authoritative user or ticket context; there is no central client-routing service.
- The repository contains a workflow template but no active client workflow until an approved `<clientname>_QA_workflow.md` is added.
- The fallback escalation owner is temporarily the project manager or designated QA workflow owner and may be refined later.
- Jira retrieval depends on Atlassian authentication and account permissions.
- The agent may be unable to open credential-protected external links referenced by Jira. An authorized user must download that content to the ticket's `downloads/` folder when it is needed for the run.
- Live database execution depends on network access, drivers, profile configuration, and database permissions.
- The workflow modules do not call Jira or databases directly.
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
6. `Basic_Instructions.md` can restore the agent's project role and folder relationships without prescribing one client's exact procedure.
7. An exact approved client workflow can be identified and verified against the current ticket type.
8. Unknown, ambiguous, conflicting, and unsupported work routes to `skills/fallback.md` without client-specific execution.
9. A ticket ID creates `ticket_runs/<ticket-id>/downloads/` and `ticket_runs/<ticket-id>/generated/` with the documented generated-artifact structure.
10. Inaccessible supporting sources can be supplied through an authorized local download without exposing credentials to the agent.
11. External source files remain under `downloads/`, and all workflow-produced ticket artifacts remain under `generated/`.
12. No logs or final report folders are created inside the ticket directory.
13. The agent stops at every approval checkpoint required by the selected client workflow.
14. SQL execution and profile changes follow the selected workflow and MCP confirmation contract.
15. Raw evidence records execution success separately from validation status where database validation applies.
16. Shared activity is written to `logs/<ticket-id>.log`.
17. Approved reports are written to `output/<ticket-id>/` when required by the client workflow.
18. Credentials are absent from committed files, artifacts, skills, logs, reports, and downloads.
19. Outer workflow and MCP tests pass.
20. MCP implementation remains reusable and independent from client-specific workflow logic.

## 27. Handoff Checklist

Before handing the project to another developer or team:

1. Confirm the repository contains no real `.env` or secret files.
2. Confirm `MCP/.env.example` uses only safe demo values.
3. Run `MCP/scripts/verify.ps1`.
4. Confirm `.vscode/mcp.json` uses repository-relative paths.
5. Confirm `Basic_Instructions.md` describes permanent agent behavior and does not contain one client's detailed procedure.
6. Confirm every active client file follows `skills/<clientname>_QA_workflow.md`, declares supported ticket types, and has an approved workflow owner.
7. Confirm `skills/QA_workflow_TEMPLATE.md` is clearly marked non-executable and `skills/fallback.md` names the current escalation route.
8. Confirm `ticket_run_config.json` matches the documented shared artifact paths and baseline controls.
9. Confirm generated ticket runs, logs, and outputs are not committed.
10. Give the recipient this document for the project overview.
11. Give the recipient `MCP.md` for database subsystem setup and extension details.
12. Demonstrate workflow selection, one fallback case, and one offline MCP demo before connecting to live systems.

## 28. Glossary

| Term | Meaning |
|---|---|
| AI agent | The AI client coordinating the QA workflow and using MCP tools. |
| Approval checkpoint | A required pause where a human authorizes the next action. |
| Artifact | A file produced or updated during a ticket run. |
| Agent skill | Reusable instructions for performing a specific task or using a project capability; it does not select or replace a client workflow. |
| Client workflow | An approved `skills/<clientname>_QA_workflow.md` defining the exact supported QA procedure for one client. |
| Connector | Database-specific implementation behind the common MCP interface. |
| Downloads | External source files associated with a ticket, including authorized local copies of inaccessible attachments or linked documents. |
| Execution success | Confirmation that a SQL statement ran, not that the QA expectation passed. |
| Fallback | A controlled stop-and-escalate procedure used when workflow selection or coverage is uncertain. |
| Generated artifacts | Ticket-scoped files produced by the AI agent, initializer, or QA workflow. |
| Jira context | Ticket information used to understand and plan QA validation. |
| MCP | Model Context Protocol, used by AI clients to discover and call tools. |
| Named profile | A safe name referring to locally configured database connection settings. |
| QA plan | Document describing checks, expected outcomes, systems, and evidence requirements. |
| Ticket run | One complete QA workflow for one ticket or client request. |
| Validation status | Explicit expected-versus-actual QA result such as passed or failed. |

## 29. Documentation Map

Use the project documentation in this order:

1. **`docs/qa_automation.md`** - understand the complete product, architecture, requirements, setup, and design.
2. **`Basic_Instructions.md`** - restore the agent's role, repository relationships, permanent boundaries, and workflow-selection behavior.
3. **`skills/<clientname>_QA_workflow.md`** - follow the exact approved procedure for the identified client and supported ticket type.
4. **`skills/fallback.md`** - stop and escalate when the workflow is missing, ambiguous, conflicting, or unsupported.
5. **`skills/QA_workflow_TEMPLATE.md`** - create and approve a new client workflow; never use the template directly for a live run.
6. **`docs/MCP.md`** - configure, operate, troubleshoot, and extend the database MCP subsystem.
7. **`ticket_run_config.json`** - inspect the machine-readable shared paths, statuses, formats, and baseline controls.
