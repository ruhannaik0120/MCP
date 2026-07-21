# QA Workflow Fallback

## Purpose

Use this file when the AI agent cannot safely identify or apply an exact client-specific QA workflow. The fallback prevents the agent from inventing instructions or continuing into an unsupported process.

## Fallback Triggers

Stop the client workflow and use this fallback when:

- the client identity is unknown or cannot be verified;
- `skills/<clientname>_QA_workflow.md` does not exist;
- multiple client workflows appear applicable;
- the ticket type, keyword, request, database, or required output is not covered by the selected workflow;
- required ticket context or instructions are missing;
- instructions conflict or their authority is unclear; or
- the agent cannot prove the last approved workflow state after losing context.

## Required Action

1. Stop before generating client-specific plans or SQL, executing database operations, switching profiles, or creating final reports.
2. Do not select the closest-looking workflow and do not invent a missing procedure.
3. Preserve existing downloads, generated artifacts, logs, approvals, and output without overwriting or deleting them.
4. Tell the user which client, ticket type, keyword, instruction, or context could not be resolved.
5. Contact the project manager or designated QA workflow owner for the correct workflow or explicit direction.
6. Resume only after an authoritative workflow or instruction resolves the condition.

## Temporary Escalation Owner

Until the organization defines a more specific escalation route, contact the project manager or designated QA workflow owner.

This fallback does not authorize SQL execution, profile changes, report generation, MCP modification, or creation of a new client workflow by assumption.
