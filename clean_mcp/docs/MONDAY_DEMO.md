# Monday Manager Demo

## Narrative

1. Present the full vision: Jira context, AI-agnostic reasoning, human approval, controlled MCP execution, and structured evidence.
2. Position this repository as the reusable execution-layer foundation, not a disposable prototype.
3. Show one stable tool contract with isolated connector-specific code.
4. Demonstrate explicit approval before moving between systems.
5. Show successful execution, blocked writes, request IDs, logs, and artifacts.
6. Open `docs/ADDING_CONNECTORS.md` to demonstrate the handoff path for SAP or Oracle.

## Preflight

- Run `clean_mcp\scripts\verify.ps1` and capture the passing result.
- Confirm `.env` and credentials are not visible.
- Start with the offline `demo-local` profile.
- Verify each live profile separately and record only successful claims.
- Keep every database account read-only.
- Close unrelated windows and company-sensitive material.

## Screenshot Sequence

1. README architecture and capability list.
2. Passing automated verification.
3. MCP tool list in VS Code.
4. Redacted connection-profile list.
5. Agent asking permission to switch.
6. Successful switch response with connection metadata.
7. `SELECT 1 AS health_check` result and request ID.
8. Rejected `DELETE FROM demo_table` with `QUERY_BLOCKED`.
9. Matching execution artifact and JSON log entry.
10. Connector extension guide.

## Agent Prompt

```text
Use the MCP execution framework. List configured profiles without exposing credentials. Ask me for explicit approval before each profile switch. After approval, switch with confirm=true, verify connectivity, run SELECT 1 AS health_check, and report the request ID. Never execute writes and never reveal secrets.
```

## Honest Support Statement

Say “implemented and automated-tested” for packaged connectors. Say “live-verified” only for platforms successfully tested tonight. The offline demo profile is a resilience feature and must be identified as simulated.
