# Integration Guide

## Boundary

The AI-agnostic orchestrator owns requirement interpretation, query generation, and approval conversation. This MCP framework owns approved system selection, policy validation, execution, structured responses, and audit evidence. The integration contract is MCP tools in and stable JSON envelopes out. Credentials never cross that boundary.

## Multi-System Flow

1. The orchestrator lists safe profile metadata.
2. It identifies the required source and asks the user to approve the transition.
3. It switches using `confirm=true`.
4. The framework validates the profile, creates the connector, and tests connectivity.
5. Failure restores the previous connector; success makes the new profile active.
6. The orchestrator submits approved statements within the active profile's permission mode.
7. The framework returns results and writes correlated evidence.

This allows one MCP workspace and one stable tool surface to move among SQL Server, PostgreSQL, MySQL, Snowflake, and future systems.

## Production Rules

- Run the MCP process under a dedicated OS identity.
- Use least-privilege database users with only the reads and writes required by the workflow.
- Inject secrets from an approved secret manager or environment, never source control.
- Keep approval state upstream; `confirm=true` is the execution-boundary assertion.
- Correlate reports using `request_id`.
- Treat profile names as logical systems rather than raw credentials.
- Add named deployment environments when the company deployment model is confirmed.

## Maturity Statement

This is a framework foundation with implemented connectors, automated offline tests, controlled switching, and audit contracts. Live verification is environment-specific and recorded separately for each connection. Jira ingestion, report generation, durable AI memory, and secret-manager adapters are integration layers, not connector responsibilities.

See `docs/ADDING_CONNECTORS.md`, `docs/LOCAL_TESTING.md`, and `docs/MONDAY_DEMO.md`.
