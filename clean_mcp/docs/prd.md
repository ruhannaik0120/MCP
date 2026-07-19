# MCP Database Execution Server Documentation

## 1. What Is MCP?

MCP stands for Model Context Protocol.

In simple terms, MCP is a standard way for an AI assistant to use external tools safely and consistently.

Normally, an AI model can only reason from the text it is given. It cannot automatically connect to a database, inspect tables, run a query, or check a live system unless some tool gives it that ability. MCP provides a structured protocol for exposing those tools to AI clients.

An MCP server is a small service that publishes capabilities. An AI client connects to the MCP server and sees a list of available tools. The AI can then call those tools with structured inputs and receive structured outputs.

For example, instead of giving an AI direct access to a database password, an MCP server can expose safe tools such as:

- list configured database profiles
- switch to an approved database profile
- test a database connection
- list tables
- describe a table
- execute one approved SQL statement
- return structured query results

The important idea is separation of responsibilities:

- The AI client decides what it needs to do.
- The MCP server controls what actions are available.
- The database connector performs the actual database operation.
- The database account permissions remain the final security boundary.

This project uses MCP to make database execution reusable and AI-client-agnostic. The same MCP server can be connected to different AI agents as long as they support MCP over standard input/output.

## 2. What This MCP Server Does

This MCP server is a reusable database execution framework.

The server lives in:

```text
clean_mcp/
```

Its job is to let an AI client safely work with configured database systems through named profiles. It does not contain Jira workflow logic, QA ticket logic, report generation logic, or business-specific test orchestration. Those belong outside the MCP server.

The MCP server focuses only on database operations:

1. Load and validate database profile configuration.
2. List available database profiles without exposing credentials.
3. Switch between profiles only after explicit approval.
4. Reload configuration after profile updates.
5. Test database connections.
6. List databases, tables, and columns.
7. Suggest similar column names when SQL references an incorrect column.
8. Execute one approved SQL statement per tool call.
9. Return structured results with request IDs, timing, profile metadata, rows, and errors.
10. Keep credentials, tokens, private keys, and connection strings out of agent-visible output.

The currently supported connector types are:

- `demo`
- `postgresql`
- `snowflake`
- `mysql`
- `sqlserver`

The server is designed so future connectors can be added without changing the MCP tool layer.

## 3. How This MCP Fits Into The Broader QA Project

The broader QA project may involve Jira tickets, test plans, generated SQL, approval checkpoints, result files, reports, dashboards, or other workflow artifacts.

This MCP server is only the database execution layer inside that larger system.

The broader workflow might look like this:

```text
Jira ticket / QA requirement
        |
        v
AI agent creates a QA plan and proposes SQL
        |
        v
Human approves the SQL and target database profile
        |
        v
AI agent calls this MCP server
        |
        v
MCP server switches profile, executes approved SQL, returns results
        |
        v
AI agent evaluates and reports the QA result
```

The MCP server does not know what Jira is. It does not know what a QA ticket is. It does not decide whether a test passed or failed. It only provides reliable, structured, safe database access.

That separation is intentional. It makes the MCP server reusable in other projects later.

## 4. Simple Workflow Diagram

This is the overall flow at a high level:

```text
                    +----------------------+
                    |      AI Client       |
                    |  Codex / Claude /    |
                    |  Cursor / other MCP  |
                    |      compatible app  |
                    +----------+-----------+
                               |
                               | MCP tool call
                               v
                    +----------------------+
                    |   clean_mcp Server   |
                    |  profile + safety +  |
                    |  execution framework |
                    +----------+-----------+
                               |
                    selects approved profile
                               |
          +--------------------+--------------------+
          |                    |                    |
          v                    v                    v
   +-------------+      +-------------+      +-------------+
   | PostgreSQL  |      | Snowflake   |      | SQL Server  |
   +-------------+      +-------------+      +-------------+
          |
          | also supports
          v
   +-------------+      +-------------+
   |   MySQL     |      |    Demo     |
   +-------------+      +-------------+
```

Plain-English version:

1. The AI client connects to `clean_mcp`.
2. The AI client asks what profiles are available.
3. A human approves the profile switch and SQL execution.
4. `clean_mcp` connects to the configured database.
5. `clean_mcp` executes the approved SQL.
6. `clean_mcp` returns a structured response.
7. The AI client uses the response for QA validation or other analysis.

## 5. Folder Overview

The MCP server is organized like this:

```text
clean_mcp/
|-- server.py
|-- config.py
|-- logger.py
|-- requirements.txt
|-- .env.example
|-- connectors/
|-- services/
|-- tools/
|-- validation/
|-- models/
|-- tests/
|-- scripts/
`-- docs/
```

### `server.py`

This is the MCP entry point.

It creates the FastMCP server and registers the MCP tools. It should stay thin. It should not contain database connector logic, SQL parsing, business workflow logic, or Jira-specific behavior.

### `config.py`

This loads and validates runtime configuration.

It handles:

- `DB_TYPE`
- host/database/username/password settings
- `DB_PROFILES_JSON`
- timeout and row-limit settings
- redaction of secrets in diagnostics and errors
- validation for placeholder hosts, quoted hosts, invalid Snowflake account identifiers, and unsafe connection option overrides

### `connectors/`

This folder contains the database-specific implementations.

Current connector folders:

```text
connectors/demo/
connectors/postgresql/
connectors/snowflake/
connectors/mysql/
connectors/sqlserver/
```

Every connector implements the same `DatabaseConnector` contract from:

```text
connectors/base.py
```

The connector factory is:

```text
connectors/factory.py
```

### `services/`

This folder contains the business logic for the MCP runtime.

Important files:

- `query_service.py`: orchestrates tool calls, validates SQL, calls connectors, and builds structured responses.
- `profile_service.py`: lists profiles, switches profiles, reloads config, and keeps profile output secret-safe.
- `runtime_state.py`: provides the runtime lock so profile switches and query execution do not collide.

### `tools/`

This folder contains thin wrappers used by `server.py`.

The wrappers call the service layer and return dictionaries. They should not contain connector logic.

### `validation/`

This contains SQL guardrails.

The current SQL guard keeps each tool call to one clear SQL statement and rejects comments or multiple statements.

### `models/`

This defines stable response and error objects.

The response shape is important because AI clients and workflow layers rely on consistent fields such as:

- `success`
- `tool`
- `request_id`
- `environment`
- `execution_time_ms`
- `data`
- `metadata`
- `error`

### `tests/`

This contains unit, connector, safety, architecture, and service tests.

These tests are important because the MCP server is intended to be reused and extended. A new connector should not break existing behavior.

### `scripts/`

This contains setup and verification scripts:

```text
scripts/setup.ps1
scripts/verify.ps1
```

Use these scripts for first-time setup and confidence checks.

## 6. MCP Tools Exposed By This Server

The server exposes these MCP tools:

| Tool | Purpose |
|---|---|
| `tool_list_connection_profiles` | Lists configured profile names and safe readiness metadata. Does not expose credentials. |
| `tool_switch_connection_profile` | Switches to a named profile after `confirm=true`, tests the connection, and rolls back on failure. |
| `tool_reload_configuration` | Reloads `.env` / profile configuration after `confirm=true` and resets cached connectors. |
| `tool_config_diagnostics` | Returns redacted configuration diagnostics for the active runtime. |
| `tool_test_connection` | Tests the active connector and returns safe server metadata. |
| `tool_health` | Runs a health check for the active connector. |
| `tool_list_databases` | Lists databases visible to the active profile. |
| `tool_list_tables` | Lists tables for a database and optional schema. |
| `tool_describe_table` | Returns column metadata for a table. |
| `tool_suggest_columns` | Suggests real column names similar to a missing/incorrect column. |
| `tool_execute_query` | Executes one approved SQL statement against the active profile. |
| `tool_execute_select_query` | Deprecated compatibility alias for `tool_execute_query`. |

The most important operational tools are:

1. `tool_list_connection_profiles`
2. `tool_switch_connection_profile`
3. `tool_execute_query`

In a normal QA workflow, the AI should list profiles, ask for approval to switch to the required database, then execute only approved SQL.

## 7. Safety Model

This server is designed to be safe for AI-assisted database work, but it is not a replacement for proper database permissions.

The safety model has several layers:

### Human approval

Profile switching requires:

```json
{"confirm": true}
```

This makes the approval explicit in the tool call.

SQL execution should also be approved by the human/operator before the AI sends it to the MCP server. The MCP server enforces structure, but the workflow layer is responsible for approval.

### Named profiles

The AI does not need raw credentials. It works with names such as:

```text
postgres-personal
snowflake-personal
sqlserver-test
```

The actual host, username, password, and connection options stay in `.env` or a secret-backed runtime environment.

### Credential redaction

Diagnostics do not expose credentials.

The server returns flags such as:

```json
"username_present": true,
"password_present": true
```

It does not return the actual values.

### One statement per call

The SQL guard blocks multiple statements and comments.

This makes each database operation auditable. One tool call should map to one clear statement.

### Row and timeout limits

Returned rows are capped by:

```text
DB_MAX_ROWS
```

Timeouts are capped by:

```text
DB_TIMEOUT_SECONDS
```

A tool call can request a lower limit, but it cannot exceed the configured cap.

### Database permissions

The database account is the final authority.

If the database account cannot run `DROP`, `DELETE`, or `UPDATE`, the MCP server cannot bypass that. For QA usage, use least-privilege test accounts.

## 8. Setup From Scratch

This section contains the complete first-time setup for the project. Follow it in order on a new machine. The commands assume the terminal is opened at the repository root unless a step says otherwise.

### 8.1 Prerequisites

The developer needs:

- access to the GitHub repository;
- Git;
- Python 3.12 recommended;
- VS Code;
- GitHub Copilot access if Copilot will be the MCP client;
- access to the required Atlassian Cloud site and Jira project;
- PowerShell on Windows;
- company VPN or network access if a live database requires it.

Install from the official sources:

- Git: https://git-scm.com/downloads
- Python: https://www.python.org/downloads/
- VS Code: https://code.visualstudio.com/download
- GitHub CLI, optional: https://cli.github.com/

SQL Server also requires Microsoft ODBC Driver 18 for SQL Server. The Python package alone is not enough:

- https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server

PostgreSQL, MySQL, and Snowflake use the Python drivers installed from this repository's requirements file. The offline demo connector requires no database, credentials, VPN, or external driver.

Confirm the main tools after installation:

```powershell
git --version
py -3.12 --version
code --version
```

If `py` is unavailable but `python --version` works, use `python` for the manual virtual-environment commands below.

### 8.2 Get access and clone the repository

For a private repository, the repository administrator must grant the developer access first. The developer must accept the GitHub invitation and verify that the repository opens in a browser while signed in to the correct GitHub account.

Use one of these clone methods.

#### HTTPS

Copy the current HTTPS URL from the repository's **Code** menu:

```powershell
git clone <repository-url>
cd <repository-folder>
```

If GitHub requests authentication, complete the browser or Git Credential Manager login. A GitHub account password is not used as a command-line Git password.

#### GitHub CLI

```powershell
gh auth login
gh auth status
gh repo clone <owner>/<repository>
cd <repository-folder>
```

During `gh auth login`, choose GitHub.com, HTTPS, and browser authentication.

#### SSH

Use this only when the developer's SSH key is already registered with GitHub:

```powershell
ssh -T git@github.com
git clone git@github.com:<owner>/<repository>.git
cd <repository-folder>
```

#### VS Code user interface

1. Open VS Code.
2. Select **Source Control: Clone Repository**.
3. Select **Clone from GitHub** or paste the repository URL.
4. Sign in with the GitHub account that has repository access.
5. Choose a local parent folder.
6. Open the cloned folder.

After any clone method, confirm the correct repository root:

```powershell
git status
git remote -v
Test-Path .\clean_mcp\server.py
Test-Path .\.vscode\mcp.json
```

Both `Test-Path` commands must return `True`. Open the repository root in VS Code, not the `clean_mcp` subfolder by itself:

```powershell
code .
```

Trust the workspace only after confirming that it is the expected repository.

### 8.3 Create the Python environment on Windows

From the repository root, run:

```powershell
PowerShell -ExecutionPolicy Bypass -File .\clean_mcp\scripts\setup.ps1
```

The script:

1. creates `.venv` at the repository root;
2. reuses it if its interpreter is healthy;
3. recreates it if the interpreter is broken;
4. upgrades pip to the minimum required by the project;
5. installs `clean_mcp/requirements.txt`;
6. installs the outer workflow dependencies from `requirements-e2e.txt`.

Expected final output:

```text
Environment ready: ...\.venv\Scripts\python.exe
```

Confirm that the installed dependency set is consistent:

```powershell
.\.venv\Scripts\python.exe -m pip check
```

To repair only the outer E2E/Excel dependency later, run:

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\requirements-e2e.txt
```

Do not copy another person's `.venv`. Virtual environments contain machine-specific paths and must be created locally.

#### Windows manual fallback

If the setup script cannot be used:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install "pip>=26.1.2"
.\.venv\Scripts\python.exe -m pip install -r .\clean_mcp\requirements.txt
.\.venv\Scripts\python.exe -m pip install -r .\requirements-e2e.txt
.\.venv\Scripts\python.exe -m pip check
```

Activation is optional because the commands use the virtual-environment Python directly. To activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, either continue using `.\.venv\Scripts\python.exe` directly or allow scripts only for the current terminal process:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 8.4 Create the Python environment on macOS or Linux

The supplied PowerShell setup script is Windows-specific. From the repository root, run:

```bash
python3.12 -m venv .venv
./.venv/bin/python -m pip install "pip>=26.1.2"
./.venv/bin/python -m pip install -r clean_mcp/requirements.txt
./.venv/bin/python -m pip install -r requirements-e2e.txt
./.venv/bin/python -m pip check
```

Activation is optional:

```bash
source .venv/bin/activate
```

If `python3.12` has a different command on the machine, use the command that starts the installed compatible Python 3 interpreter.

### 8.5 Create the local environment file

The real configuration file is local and ignored by Git. Create it only if it does not already exist.

Windows:

```powershell
if (-not (Test-Path .\clean_mcp\.env)) {
    Copy-Item .\clean_mcp\.env.example .\clean_mcp\.env
}
```

macOS/Linux:

```bash
test -f clean_mcp/.env || cp clean_mcp/.env.example clean_mcp/.env
```

Never commit `clean_mcp/.env`. Never put database passwords, tokens, private keys, or connection strings in `.vscode/mcp.json`, chat prompts, tickets, logs, or screenshots.

For the first run, keep the demo configuration:

```env
DB_TYPE=demo
DB_HOST=demo-local
DB_DATABASE=qa_demo
DB_USERNAME=
DB_PASSWORD=
DB_CONNECTION_OPTIONS={}
DB_TIMEOUT_SECONDS=30
DB_MAX_ROWS=500
DB_ACTIVE_PROFILE=demo-local
DB_PROFILES_JSON={"demo-local":{"db_type":"demo","host":"demo-local","database":"qa_demo"}}
LOG_LEVEL=INFO
```

This verifies the complete MCP path without contacting a live database. Configure real profiles only after the demo works. Database-specific examples are in Section 10.

### 8.6 Check the VS Code workspace files

The repository includes:

```text
.vscode/mcp.json
.vscode/settings.json
```

On Windows, `.vscode/mcp.json` should point to the repository's virtual-environment Python and server:

```json
{
  "servers": {
    "atlassian-mcp-server": {
      "type": "http",
      "url": "https://mcp.atlassian.com/v1/mcp/authv2"
    },
    "mcp-execution-framework": {
      "type": "stdio",
      "command": "${workspaceFolder}\\.venv\\Scripts\\python.exe",
      "args": ["${workspaceFolder}\\clean_mcp\\server.py"],
      "cwd": "${workspaceFolder}\\clean_mcp"
    }
  }
}
```

The Windows interpreter setting in `.vscode/settings.json` should be:

```json
"python.defaultInterpreterPath": "${workspaceFolder}\\.venv\\Scripts\\python.exe"
```

No Windows path change is needed when `.venv` was created at the repository root.

On macOS/Linux, use:

```json
{
  "servers": {
    "mcp-execution-framework": {
      "type": "stdio",
      "command": "${workspaceFolder}/.venv/bin/python",
      "args": ["${workspaceFolder}/clean_mcp/server.py"],
      "cwd": "${workspaceFolder}/clean_mcp"
    }
  }
}
```

And set:

```json
"python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python"
```

If a macOS/Linux developer changes the tracked Windows workspace files locally, review `git status` before committing. A user-level VS Code MCP configuration with absolute local paths can be used instead when the team does not want OS-specific workspace changes committed.

These files must not contain secrets.

### 8.7 Verify the installation

Windows database-MCP verification:

```powershell
PowerShell -ExecutionPolicy Bypass -File .\clean_mcp\scripts\verify.ps1
```

The script compiles the Python source, runs the `clean_mcp` tests, performs an offline demo smoke test, and runs the outer E2E helper tests. Expected final output:

```text
All verification gates passed.
```

To run only the outer E2E helper tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q .\tests
```

macOS/Linux verification:

```bash
cd clean_mcp
../.venv/bin/python -m compileall -q .
../.venv/bin/python -m pytest -q
DB_TYPE=demo DB_HOST=demo-local DB_DATABASE=qa_demo DB_USERNAME= DB_PASSWORD= DB_CONNECTION_OPTIONS='{}' DB_ACTIVE_PROFILE=demo-local ../.venv/bin/python tests/smoke_test.py
cd ..
./.venv/bin/python -m pytest -q tests
```

Do not continue to a live database until the offline verification passes.

### 8.8 Sign in to GitHub Copilot in VS Code

GitHub Copilot is the AI client in this setup. It is separate from Git repository authentication.

1. Open the repository root in VS Code.
2. Select the Copilot icon in the status bar.
3. Select **Use AI Features** or **Sign in to use Copilot**.
4. Complete the GitHub browser login.
5. Use the GitHub account that has Copilot access.
6. Open Copilot Chat.
7. Select **Agent** mode when MCP tools are needed.

If Copilot is not visible, update VS Code and install or enable the official GitHub Copilot and GitHub Copilot Chat extensions. If the wrong account is active, sign out through the VS Code Accounts menu and sign in again.

### 8.9 Connect Atlassian Rovo MCP in VS Code

The tracked `.vscode/mcp.json` includes the shared Atlassian Rovo MCP endpoint. Authentication is completed separately by each developer and is not stored in Git.

1. Press `Ctrl+Shift+P`.
2. Run **MCP: List Servers**.
3. Select `atlassian-mcp-server`.
4. Select **Start Server**.
5. Complete the Atlassian browser authorization.
6. Sign in with the Atlassian account that can access the required Jira site.
7. Approve only the access required by the workflow and organization policy.
8. Return to VS Code and confirm the server shows as running.
9. Open Copilot Chat in Agent mode and confirm the Atlassian tools are available.

If the server is not listed, run **MCP: Add Server**, choose **HTTP**, enter `https://mcp.atlassian.com/v1/mcp/authv2`, and name it `atlassian-mcp-server`. Save it to the workspace only if the tracked `.vscode/mcp.json` entry is genuinely missing.

For a connection check, ask Copilot Agent mode to show the current Atlassian user and accessible Atlassian resources. Confirm the expected Jira site is returned before requesting a ticket. Atlassian permissions remain limited to what the signed-in account and organization allow.

Official setup reference: https://support.atlassian.com/atlassian-rovo-mcp-server/docs/setting-up-ides/

### 8.10 Start the local database MCP server in VS Code

1. Press `Ctrl+Shift+P`.
2. Run **MCP: List Servers**.
3. Select `mcp-execution-framework`.
4. Select **Start Server**.
5. Review the command and paths in `.vscode/mcp.json`.
6. Trust the server only when it points to this repository's `.venv` and `clean_mcp/server.py`.
7. Open Copilot Chat in Agent mode.
8. Open the tools selector and confirm the MCP tools are available.

Expected tools include:

```text
tool_list_connection_profiles
tool_switch_connection_profile
tool_reload_configuration
tool_config_diagnostics
tool_test_connection
tool_health
tool_list_databases
tool_list_tables
tool_describe_table
tool_suggest_columns
tool_execute_query
```

If startup fails, use **MCP: List Servers**, select the server, and choose **Show Output**.

A manual startup check is:

```powershell
.\.venv\Scripts\python.exe .\clean_mcp\server.py
```

The process normally waits for stdio input. Press `Ctrl+C` to stop the manual check before starting it through VS Code.

### 8.11 Verify the database MCP connection with the demo profile

In Copilot Chat Agent mode, ask:

```text
Use the mcp-execution-framework tools. List the configured connection profiles,
show redacted configuration diagnostics, test the active demo connection, list
the tables in qa_demo, and describe public.demo_items. Do not use a live
database and do not change files.
```

Expected results:

- `demo-local` is active;
- the connection test succeeds;
- `qa_demo` is available;
- `demo_items` and `validation_results` are listed;
- diagnostics do not expose passwords.

After that, test an approved demo query through `tool_execute_query`:

```sql
SELECT * FROM demo_items
```

The demo connector returns deterministic sample rows without a network connection.

### 8.12 Configure a live database only after the demo passes

1. Add the approved named profile to `DB_PROFILES_JSON` in `clean_mcp/.env`.
2. Keep the JSON on one line and validate its syntax.
3. Start or restart the MCP server, or call `tool_reload_configuration(confirm=true)` after approval.
4. Call `tool_list_connection_profiles`.
5. Resolve every `ready=false` issue.
6. Obtain approval before switching profiles.
7. Call `tool_switch_connection_profile(name, confirm=true)`.
8. Confirm `tool_test_connection` succeeds.
9. Use metadata tools before generating SQL.
10. Execute only one approved SQL statement per tool call.

The detailed profile formats for demo, PostgreSQL, Snowflake, MySQL, and SQL Server are in Section 10. General connection and query troubleshooting is in Section 13.

## 9. Connecting The MCP Server To AI Agents

Different AI clients have different settings screens, but the idea is the same:

1. Tell the AI client there is an MCP server.
2. Give it the command that starts the server.
3. Give it the working directory.
4. Restart or reload the AI client.
5. Confirm that the MCP tools appear.

### Generic MCP stdio configuration

Use this shape as the starting point for any MCP-compatible client:

```json
{
  "mcpServers": {
    "mcp-execution-framework": {
      "command": "C:\\path\\to\\MCP\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\path\\to\\MCP\\clean_mcp\\server.py"
      ],
      "cwd": "C:\\path\\to\\MCP\\clean_mcp"
    }
  }
}
```

For another machine, replace the paths with that machine's project path.

### VS Code / local MCP config

If the client supports a workspace MCP config, add the server using the same command, args, and cwd idea.

Example shape:

```json
{
  "servers": {
    "mcp-execution-framework": {
      "type": "stdio",
      "command": ".\\.venv\\Scripts\\python.exe",
      "args": [".\\clean_mcp\\server.py"]
    }
  }
}
```

Exact field names may vary by client, but the required information is always:

- server name
- transport type: `stdio`
- Python executable path
- `clean_mcp/server.py` path
- working directory

### Claude Desktop style configuration

For clients that use a global JSON MCP config, use an absolute-path configuration:

```json
{
  "mcpServers": {
    "mcp-execution-framework": {
      "command": "C:\\path\\to\\MCP\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\path\\to\\MCP\\clean_mcp\\server.py"
      ]
    }
  }
}
```

After saving the config, restart the AI client.

### How to confirm the AI client is connected

Ask the AI client to list available MCP tools.

You should see tools like:

```text
tool_list_connection_profiles
tool_switch_connection_profile
tool_reload_configuration
tool_config_diagnostics
tool_test_connection
tool_list_databases
tool_list_tables
tool_describe_table
tool_suggest_columns
tool_execute_query
```

Then call:

```text
tool_list_connection_profiles
```

You should receive safe profile metadata without secrets.

## 10. Configuring Database Systems

This MCP server supports multiple systems through named profiles.

Profiles are stored in:

```text
DB_PROFILES_JSON
```

Each profile has a name. The AI switches by name, not by raw credentials.

Important rule:

Do not paste real credentials into chat, tickets, logs, or generated artifacts. Put them in `.env` locally or in the approved secret/configuration mechanism for the environment.

### Common profile fields

Most profiles use:

```json
{
  "db_type": "postgresql",
  "host": "localhost",
  "database": "qa_demo",
  "username": "qa_user",
  "password": "qa_password",
  "connection_options": {},
  "timeout_seconds": 30,
  "max_rows": 500
}
```

Field meaning:

| Field | Meaning |
|---|---|
| `db_type` | Connector type: `demo`, `postgresql`, `snowflake`, `mysql`, or `sqlserver`. |
| `host` | Server host, account identifier, or demo host value depending on connector. |
| `database` | Default database for the profile. |
| `username` | Database username, if required. |
| `password` | Database password, if required. |
| `connection_options` | Connector-specific settings such as port, schema, warehouse, role, or driver. |
| `timeout_seconds` | Optional per-profile timeout cap. |
| `max_rows` | Optional per-profile returned-row cap. |

### Demo profile

Use this to test the MCP server without a real database:

```json
"demo-local": {
  "db_type": "demo",
  "host": "demo-local",
  "database": "qa_demo"
}
```

### PostgreSQL profile

Example:

```json
"postgres-local": {
  "db_type": "postgresql",
  "host": "localhost",
  "database": "qa_demo",
  "username": "qa_user",
  "password": "qa_password",
  "connection_options": {
    "port": 5432
  }
}
```

Notes:

- `host` should be a real hostname or IP address, not `"<localhost>"`.
- Do not wrap host values in literal quotes inside JSON values.
- Use `connection_options.port` for the port.

### Snowflake profile

Example:

```json
"snowflake-test": {
  "db_type": "snowflake",
  "host": "MYACCOUNT",
  "database": "QA_TEST_DB",
  "username": "QA_USER",
  "password": "qa_password",
  "connection_options": {
    "warehouse": "QA_WH",
    "role": "QA_ROLE",
    "schema": "PUBLIC"
  }
}
```

Notes:

- For this connector, `host` is the Snowflake account identifier.
- The current validation expects only letters, digits, `_`, and `-`.
- Do not put dots or slashes in the account identifier for this connector version.
- Put warehouse, role, and schema in `connection_options`.

### MySQL profile

Example:

```json
"mysql-local": {
  "db_type": "mysql",
  "host": "localhost",
  "database": "qa_demo",
  "username": "qa_user",
  "password": "qa_password",
  "connection_options": {
    "port": 3306
  }
}
```

### SQL Server profile

Example:

```json
"sqlserver-test": {
  "db_type": "sqlserver",
  "host": "localhost",
  "database": "qa_demo",
  "username": "qa_user",
  "password": "qa_password",
  "connection_options": {
    "driver": "ODBC Driver 18 for SQL Server",
    "TrustServerCertificate": "yes"
  }
}
```

Notes:

- Windows must have the Microsoft ODBC Driver installed.
- SQL Server profiles require a database.
- Username and password must either both be set or both be empty.

### Full multi-profile `.env` example

This is one-line JSON because `.env` files are easier to parse that way:

```env
DB_TYPE=demo
DB_HOST=demo-local
DB_DATABASE=qa_demo
DB_USERNAME=
DB_PASSWORD=
DB_CONNECTION_OPTIONS={}
DB_TIMEOUT_SECONDS=30
DB_MAX_ROWS=500
DB_ACTIVE_PROFILE=demo-local
DB_PROFILES_JSON={"demo-local":{"db_type":"demo","host":"demo-local","database":"qa_demo"},"postgres-local":{"db_type":"postgresql","host":"localhost","database":"qa_demo","username":"qa_user","password":"qa_password","connection_options":{"port":5432}},"snowflake-test":{"db_type":"snowflake","host":"MYACCOUNT","database":"QA_TEST_DB","username":"QA_USER","password":"qa_password","connection_options":{"warehouse":"QA_WH","role":"QA_ROLE","schema":"PUBLIC"}}}
LOG_LEVEL=INFO
```

### After changing `.env`

If the MCP server is already running, call:

```text
tool_reload_configuration(confirm=true)
```

If your deployment injects config through a cloud secret manager or environment variables, restart the MCP process after changing config.

## 11. Normal Operating Workflow

A safe normal workflow looks like this:

### Step 1: List profiles

Call:

```text
tool_list_connection_profiles
```

Check:

- profile names
- `ready`
- `issues`
- active profile
- connector type

### Step 2: Switch profile

First call without confirmation to expose the approval requirement:

```json
{
  "name": "postgres-local",
  "confirm": false
}
```

Then, after human approval:

```json
{
  "name": "postgres-local",
  "confirm": true
}
```

The switch will:

1. validate the profile
2. apply environment settings
3. reset the cached connector
4. test the target connection
5. commit the switch only if the connection succeeds
6. roll back if anything fails

### Step 3: Inspect metadata

Useful calls:

```text
tool_list_databases
tool_list_tables
tool_describe_table
```

Use metadata before writing SQL if column names are unknown.

### Step 4: Execute approved SQL

Call:

```text
tool_execute_query
```

Important rules:

- send one statement per call
- do not include comments
- do not send a file containing multiple SQL statements
- qualify schema/database names when needed
- switch profiles before targeting a different database system

### Step 5: Use structured results

The tool response includes:

- success/failure
- request ID
- execution time
- active profile metadata
- columns
- rows
- structured error if failed

## 12. Adding A New Connector

This is the most important extension guide.

A new connector should be added without changing how AI clients call the MCP server.

The ideal outcome:

- same MCP tools
- same response format
- same profile switching behavior
- new backend hidden behind the existing connector interface

### Connector architecture

The connector contract is:

```text
connectors/base.py
```

The factory registry is:

```text
connectors/factory.py
```

Existing connector examples:

```text
connectors/postgresql/connector.py
connectors/snowflake/connector.py
connectors/mysql/connector.py
connectors/sqlserver/connector.py
connectors/demo/connector.py
```

### Step 1: Choose the connector name

Pick a lowercase connector name.

Examples:

```text
oracle
bigquery
redshift
databricks
sqlite
```

This name becomes the `db_type` value used in profiles.

Example:

```json
{
  "db_type": "redshift"
}
```

### Step 2: Create the connector folder

Create:

```text
clean_mcp/connectors/<connector_name>/
```

Example:

```text
clean_mcp/connectors/redshift/
```

Add:

```text
__init__.py
connector.py
```

### Step 3: Implement `DatabaseConnector`

Your connector class must implement all abstract methods:

```python
from typing import Any

from config import Config, ConfigError, ConnectionConfig
from connectors.base import DatabaseConnector


class RedshiftConnector(DatabaseConnector):
    def connect(self, database: str | None = None, timeout_seconds: int | None = None) -> Any:
        ...

    def test_connection(self, database: str | None = None, timeout_seconds: int | None = None) -> dict[str, Any]:
        ...

    def health_check(self, database: str | None = None, timeout_seconds: int | None = None) -> dict[str, Any]:
        ...

    def list_databases(self, timeout_seconds: int | None = None) -> dict[str, Any]:
        ...

    def list_tables(
        self,
        database: str | None = None,
        schema: str | None = None,
        timeout_seconds: int | None = None,
    ) -> dict[str, Any]:
        ...

    def describe_table(
        self,
        database: str | None = None,
        table: str | None = None,
        schema: str | None = None,
        timeout_seconds: int | None = None,
    ) -> dict[str, Any]:
        ...

    def execute_query(
        self,
        query: str,
        *,
        database: str | None = None,
        timeout_seconds: int | None = None,
        max_rows: int | None = None,
    ) -> Any:
        ...

    def close(self) -> None:
        return None


Connector = RedshiftConnector
```

The final line is required:

```python
Connector = RedshiftConnector
```

The factory expects every connector module to export `Connector`.

### Step 4: Import the driver lazily

Do not import database drivers at the top of `server.py`, `tools/`, or `services/`.

Do this inside the connector:

```python
def _driver(self):
    try:
        import vendor_driver
    except ImportError as exc:
        raise ConfigError("Install vendor_driver_package to use the Redshift connector.") from exc
    return vendor_driver
```

Reason:

- using PostgreSQL should not require Snowflake packages
- using demo should not require any database package
- architecture tests enforce this boundary

### Step 5: Read config only through `Config.connection_config()`

Inside the connector:

```python
profile = Config.connection_config()
```

Do not read raw environment variables directly in the connector.

The `profile` object contains:

```text
db_type
host
database
username
password
connection_options
timeout_seconds
max_rows
```

### Step 6: Validate connector-specific requirements

Add connector-specific validation in the connector's `_profile()` helper, or in `Config._validate_connector_requirements()` if it is a generic startup/profile rule.

Example:

```python
def _profile(self) -> ConnectionConfig:
    profile = Config.connection_config()
    if not profile.host:
        raise ConfigError("DB_HOST is required for the Redshift connector.")
    if not profile.username:
        raise ConfigError("DB_USERNAME is required for the Redshift connector.")
    return profile
```

Use clear errors. The AI client and user should understand what to fix.

### Step 7: Create connection kwargs safely

Translate the neutral profile into the vendor driver's expected arguments.

Example:

```python
def _connection_kwargs(self, profile: ConnectionConfig, database: str) -> dict[str, Any]:
    options = dict(profile.connection_options or {})
    kwargs = {
        "host": profile.host,
        "database": database,
        "user": profile.username or None,
        "password": profile.password or None,
        "connect_timeout": profile.timeout_seconds,
    }
    kwargs.update(options)
    return {key: value for key, value in kwargs.items() if value is not None}
```

Do not return this dictionary in diagnostics. It may contain secrets.

### Step 8: Implement `test_connection`

This should run a lightweight query and return safe metadata.

Example shape:

```python
return {
    "connector_type": self.__class__.__name__,
    "db_type": profile.db_type,
    "database": target_database,
    "connection_status": "connected",
    "server_information": {
        "server_name": "...",
        "version": "...",
        "logged_in_user": "...",
        "utc_time": "..."
    }
}
```

Do not include passwords, tokens, connection strings, private keys, or full secret-bearing DSNs.

### Step 9: Implement metadata methods

Implement:

```text
list_databases
list_tables
describe_table
```

Use the database's information schema or system catalog.

Important:

- parameterize metadata filters where the driver supports parameters
- do not build unsafe string SQL from user input
- return normalized dictionaries
- keep field names stable where possible

Example table metadata response:

```python
{
    "connector_type": "RedshiftConnector",
    "db_type": "redshift",
    "database": "qa",
    "schema": "public",
    "table": "orders",
    "column_count": 3,
    "columns": [
        {"COLUMN_NAME": "order_id", "DATA_TYPE": "integer", "IS_NULLABLE": "NO"},
        {"COLUMN_NAME": "customer_id", "DATA_TYPE": "integer", "IS_NULLABLE": "NO"},
        {"COLUMN_NAME": "order_status", "DATA_TYPE": "varchar", "IS_NULLABLE": "YES"}
    ]
}
```

### Step 10: Implement query execution

Your connector's `execute_query` receives SQL that has already passed the shared MCP guardrails.

The connector still owns database-specific details:

- applying row limits
- applying timeouts
- executing through the driver
- fetching rows
- committing successful data-changing statements if the driver uses transactions
- closing cursors/connections

Example return shape:

```python
{
    "connector_type": "RedshiftConnector",
    "db_type": "redshift",
    "database": target_database,
    "columns": ["order_id", "order_status"],
    "rows": [
        {"order_id": 1, "order_status": "completed"}
    ],
    "rows_affected": 1
}
```

### Step 11: Apply row limits

For row-returning statements, respect:

```text
max_rows
```

Most connectors currently append or adjust `LIMIT` / `FETCH` depending on dialect.

If the query already has a limit greater than `max_rows`, reduce it.

If the query does not have a limit, add one for `SELECT` queries.

### Step 12: Apply timeouts

Use the driver's native timeout options where possible.

Examples:

- connection timeout
- login timeout
- statement timeout
- query timeout

The MCP service already caps requested timeouts, but the connector should pass the effective timeout into the driver.

### Step 13: Close resources

Always close cursors and connections.

Preferred pattern:

```python
with self._connection(database=target_database, timeout_seconds=timeout_seconds) as conn:
    cursor = conn.cursor()
    try:
        ...
    finally:
        cursor.close()
```

### Step 14: Register the connector

Edit:

```text
connectors/factory.py
```

Add the new connector:

```python
SUPPORTED_CONNECTORS: dict[str, str] = {
    "demo": "connectors.demo.connector",
    "sqlserver": "connectors.sqlserver.connector",
    "mysql": "connectors.mysql.connector",
    "postgresql": "connectors.postgresql.connector",
    "snowflake": "connectors.snowflake.connector",
    "redshift": "connectors.redshift.connector",
}
```

After this, profiles can use:

```json
{"db_type": "redshift"}
```

### Step 15: Add dependency

Add the vendor package to:

```text
requirements.txt
```

Example:

```text
redshift-connector>=2.0.0
```

If the driver requires OS-level installation, document that clearly.

### Step 16: Add tests

At minimum, add tests for:

1. factory registration
2. missing driver error
3. connection kwargs creation without exposing secrets
4. row limit behavior
5. metadata response shape
6. query response shape
7. architecture rule that driver imports stay inside `connectors/`

Use fake drivers/mocks for unit tests. Do not require a real external database in normal CI.

### Step 17: Add optional live smoke testing

Live database tests should be opt-in.

Use environment flags such as:

```env
DB_SMOKE_TEST_CONNECT=true
```

Do not make normal unit tests depend on external database availability.

### Step 18: Run verification

From repository root:

```powershell
PowerShell -ExecutionPolicy Bypass -File .\clean_mcp\scripts\verify.ps1
```

Or run tests directly:

```powershell
.\.venv\Scripts\python.exe -m pytest clean_mcp\tests
```

The connector is not ready to merge unless existing tests and new connector tests pass.

## 13. Common Troubleshooting

### MCP tools do not appear in the AI client

Check:

1. Is the MCP client configured with the correct Python path?
2. Is the `server.py` path correct?
3. Is the working directory correct?
4. Did you restart the AI client after editing MCP config?
5. Does the server start manually?

Manual check:

```powershell
.\.venv\Scripts\python.exe .\clean_mcp\server.py
```

### Profile appears but is not ready

Call:

```text
tool_list_connection_profiles
```

Look at:

```text
ready
issues
host_format_valid
snowflake_account_format_valid
```

Common issues:

- host is missing
- host still contains `<placeholder>`
- host is wrapped in literal quotes
- Snowflake account identifier contains invalid characters
- SQL Server username/password are only partially configured

### `.env` was changed but MCP still uses old config

Call:

```text
tool_reload_configuration(confirm=true)
```

If that fails or the deployment does not use local `.env`, restart the MCP server process.

### Query failed because a column does not exist

Use:

```text
tool_describe_table
tool_suggest_columns
```

Example:

```json
{
  "table": "mcp_test_orders",
  "missing_column": "status",
  "schema": "public"
}
```

The server can suggest similar real columns, but it should not automatically rewrite SQL. The human/operator should approve corrected SQL before rerun.

### Query blocked by SQL guard

The SQL guard blocks:

- empty queries
- comments
- multiple statements

Fix:

- send one statement only
- remove comments
- execute each approved statement in a separate tool call

### Connection works outside MCP but not inside MCP

Check:

1. Is the MCP server using the same `.env` file?
2. Did you call `tool_reload_configuration(confirm=true)`?
3. Is the AI client launching the right project path?
4. Is the virtual environment correct?
5. Are required database drivers installed in that virtual environment?
6. Are company VPN/network rules active for the MCP process?

## 14. Delivery Notes

This MCP server is the deliverable database execution layer.

It is intentionally separate from:

- Jira ticket retrieval
- QA plan generation
- approval logs
- report generation
- E2E run folders
- project-specific workflow artifacts

Those can use the MCP server, but they should not be built into it.

The server is ready to be reused by a broader QA automation project because it provides:

- stable MCP tool names
- named database profiles
- approval-gated switching
- multiple database connectors
- safe diagnostics
- structured responses
- connector extension contract
- test coverage

## 15. Quick Start Checklist

Use this checklist when giving the server to someone new.

1. Clone the repository.
2. Run `clean_mcp/scripts/setup.ps1`.
3. Copy `clean_mcp/.env.example` to `clean_mcp/.env`.
4. Configure `DB_PROFILES_JSON`.
5. Keep real credentials out of Git.
6. Run `clean_mcp/scripts/verify.ps1`.
7. Add the MCP server command to the AI client's MCP config.
8. Restart the AI client.
9. Call `tool_list_connection_profiles`.
10. Fix any `ready=false` profile issues.
11. Switch profile with `confirm=true` after approval.
12. Use metadata tools to inspect database structure.
13. Execute one approved SQL statement per call with `tool_execute_query`.
14. Use returned structured results for QA validation.

## 16. What To Say In A Presentation

Short explanation:

This project delivers a reusable MCP database execution server for AI-assisted QA. It lets an AI agent safely connect to approved database profiles, inspect metadata, execute approved SQL, and return structured results without exposing credentials. The server is connector-based, so PostgreSQL, Snowflake, MySQL, SQL Server, and future systems can be accessed through one stable MCP tool interface.

Key value:

- AI clients do not need custom database code.
- Credentials stay in configuration, not in prompts.
- Profile switches are explicit and approval-gated.
- Results are structured and auditable.
- New database backends can be added by implementing one connector contract.

