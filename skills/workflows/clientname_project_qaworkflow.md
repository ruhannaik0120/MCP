---
document_type: "qa_workflow_template"
template: true
executable: false
client_key: "<client-key>"
project_key: "<project-key>"
workflow_variant_key: null
workflow_key: "<unique-workflow-key>"
# Example required skill entry:
# required_skills:
#   - skill_key: qa-test-planner
#     workflow_stage: qa-planning
#     required: true
required_skills: []
optional_skills: []
created_by: "<creator-name-or-id>"
created_on: "<yyyy-mm-dd>"
last_edited_by: "<editor-name-or-id>"
last_edited_on: "<yyyy-mm-dd>"
version: "<version>"
status: "template"
workflow_owner: "<workflow-owner-name-or-id>"
approved_by: null
approved_on: null
---

# QA Workflow Template

## Purpose

- State the permanent business purpose of this client/project workflow and the outcome it is intended to coordinate.
- Explain why this workflow exists and how it differs from other workflows that may belong to the same client.
- Give the AI enough detail to understand the workflow's objective without relying on one example ticket.
- Define terms that could otherwise have more than one meaning, especially client-specific language and project-type terminology.
- Do not include ticket-specific requirements, values, decisions, or artifacts. This section must remain valid across all supported tickets routed to this workflow.

## Scope

- Identify the client represented by `client_key`, the supported project type represented by `project_key`, and the optional additional routing condition represented by `workflow_variant_key`.
- Describe the ticket categories, title indicators, requests, and boundaries that make this workflow applicable.
- Explain why each routing condition is necessary so the AI can distinguish this workflow from other workflows for the same client.
- Be precise enough that applicability can be decided from authoritative metadata without similarity guessing.
- State explicit exclusions and unsupported conditions. Do not describe the contents or expected outcome of one specific ticket.

## Prerequisites

- List the permanent information, authorization, access, source material, environment readiness, and human roles required before this workflow can begin.
- Explain why every prerequisite is needed and how the AI can verify readiness without exposing credentials or inventing missing context.
- Specify required detail such as authoritative source, acceptable format, responsible role, and readiness condition.
- Make blocking and non-blocking prerequisites unambiguous, including what the AI must do when a prerequisite is absent.
- Define reusable prerequisites only; ticket-specific inputs belong under `ticket_runs/<ticket-id>/downloads/` or `ticket_runs/<ticket-id>/generated/` as appropriate.
- Reference reusable Agent Skills by the exact `skill_key` declared in the YAML metadata. A skill key will later resolve to `skills/agent_skills/<skill-key>/SKILL.md`; skill resolution is not implemented by this template.

## Steps

- Define the permanent ordered stages for this client/project workflow. Add, remove, or repeat the skeleton below until the full workflow is represented.
- Explain why each step exists and how it advances the workflow, with enough detail for consistent execution across supported tickets.
- Make ordering, dependencies, decision rules, permissions, approvals, checkpoints, artifacts, and failure routing explicit.
- Do not assume a particular tool, database, protocol, design platform, export format, or previous proof-of-concept process unless this client/project workflow permanently requires it.
- Do not place ticket-specific content in the step definitions. Runtime ticket information and generated outputs belong in the ticket workspace.

1. **Step name:** `<stable-stage-name>`
   - **Objective:** `<permanent-outcome-this-step-must-achieve-and-why>`
   - **Entry conditions:** `<conditions-that-must-be-true-before-the-step-starts>`
   - **Required inputs:** `<authoritative-input-types-and-where-they-come-from>`
   - **Required skill key, if applicable:** `<exact-skill-name-or-none>`
   - **Permitted tools or systems:** `<explicitly-allowed-tools-systems-or-none>`
   - **Ordered agent actions:**
     1. `<first-unambiguous-action>`
     2. `<next-unambiguous-action>`
     3. `<additional-actions-as-required>`
   - **Human approval point:** `<approver-role-trigger-decision-needed-and-whether-blocking-or-none>`
   - **Expected checkpoint:** `<observable-state-that-proves-the-step-completed>`
   - **Generated or updated artifact:** `<artifact-path-purpose-and-update-rule-or-none>`
   - **Failure path:** `<stop-retry-escalation-or-routing-action-for-each-defined-failure>`

## Error Handling / Fallbacks

- Define permanent failure categories, unsupported conditions, retry limits, escalation paths, and safe stopping behavior for this workflow.
- Explain why each fallback exists and what information the AI must preserve or report when using it.
- Provide enough detail to distinguish recoverable errors, approval blockers, missing prerequisites, routing mismatches, and conditions requiring human ownership.
- Name the responsible role and the exact condition for resuming; do not use vague directions such as "handle appropriately" or "continue if possible."
- Keep fallback rules reusable across the client/project workflow. Do not include an actual ticket failure, approval decision, execution result, or evidence record.

## Constraints

- State all permanent client/project restrictions governing data handling, folder ownership, tool use, system access, approvals, generated artifacts, retention, and prohibited actions.
- Explain why each constraint exists so the AI can apply it correctly when multiple rules interact.
- Specify whether each constraint is mandatory, conditional, or advisory and define every condition precisely.
- Resolve potentially ambiguous terms and identify which authoritative role decides any permitted exception.
- Do not repeat one ticket's requirements or hardcode ticket context, QA plans, generated instructions, approvals, execution results, evidence, or reports.
- Keep external ticket documents under `ticket_runs/<ticket-id>/downloads/` and ticket-generated information under `ticket_runs/<ticket-id>/generated/`.
- Do not allow this workflow or a referenced Agent Skill to override permanent project-wide rules in `Basic_Instructions.md`.
