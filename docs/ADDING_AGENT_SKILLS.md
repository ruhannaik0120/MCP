# Adding Agent Skills Manually

## Purpose

This guide explains how a developer can manually add a reusable Agent Skill from an external source to the QA Automation repository. It covers how to locate a skill package, review it, install it in the project structure, verify it independently, and make it available to an approved workflow.

The process is AI-agnostic. It does not depend on Copilot, VS Code, or any other specific AI product. Any compatible agent may use an installed skill when it can read the repository and follow the skill's instructions.

## Destination Structure

Every installed Agent Skill must have its own folder under `skills/agent_skills/`:

```text
skills/
`-- agent_skills/
    `-- <skill-name>/
        |-- SKILL.md
        `-- optional supporting files
```

`<skill-name>` is the skill's exact identifier. Do not place unrelated skills in the same folder or place a `SKILL.md` directly in `skills/agent_skills/`.

## Locating the Skill Package

External repositories may organize skills differently. Do not assume that an external repository uses this project's destination structure or provides the same supporting folders.

To locate a skill package:

1. Download or clone the source repository to an authorized local location.
2. Search the source repository for the desired `SKILL.md`.
3. Identify the folder that directly contains that `SKILL.md`.
4. Treat that folder as the complete skill package.
5. Inspect every file and subfolder in the package before copying it.

Possible source layouts include:

```text
repository/skills/<skill-name>/SKILL.md
repository/plugins/<skill-name>/skills/<skill-name>/SKILL.md
repository/<skill-name>/SKILL.md
```

These are examples only. The actual source layout may be different, so locate the package from its `SKILL.md` rather than assuming a fixed source path.

## Required and Optional Files

An Agent Skill package may contain:

| Path | General purpose | Requirement |
|---|---|---|
| `SKILL.md` | Skill metadata, instructions, activation guidance, and references to supporting files | Always required |
| `references/` | Supporting documentation or detailed reference material | Optional generally; required when the skill depends on it |
| `scripts/` | Executable shell, PowerShell, Python, JavaScript, or other helpers | Optional generally; required when the skill depends on it |
| `templates/` | Reusable input or output templates | Optional generally; required when the skill depends on it |
| `assets/` | Images, data, or other supporting resources | Optional generally; required when the skill depends on it |
| `examples/` | Sample inputs, outputs, or usage patterns | Optional generally; required when the skill depends on it |
| `README.md` | Human-facing package information | Generally optional for agent execution |

Supporting files are optional in the general Agent Skill structure, but a specific skill may require them when `SKILL.md` references or relies on them.

Use this installation rule:

> Copy the complete skill package initially. Keep all files referenced or required by `SKILL.md`. Remove optional files only after review and successful testing proves that the skill does not depend on them.

## Naming Contract

The following values must match exactly:

1. The checklist item's **Required Agent Skill** value.
2. The skill folder name.
3. The `name` field inside the `SKILL.md` metadata.

Example checklist value:

```text
qa-test-planner
```

Example destination folder:

```text
skills/agent_skills/qa-test-planner/
```

Example `SKILL.md` metadata:

```yaml
name: qa-test-planner
```

Skill names are exact identifiers, not approximate descriptions. Differences in spelling, capitalization, separators, or wording can prevent reliable resolution.

## Security Review

Treat every external skill as untrusted until it has been fully reviewed. Before installation, inspect:

- all instructions in `SKILL.md`;
- shell, PowerShell, Python, JavaScript, and other scripts;
- commands the skill asks an agent or developer to execute;
- external URLs and network destinations;
- required tools, packages, runtimes, and dependencies;
- files the skill may read, create, modify, move, or delete;
- credential, token, secret, and environment-variable handling;
- conflicts with `Basic_Instructions.md`;
- assumptions that are specific to a client or ticket; and
- assumptions that depend on a particular AI product.

Do not install the package until its behavior and required access are understood. An Agent Skill must not override permanent project rules, repository boundaries, safety requirements, approval requirements, or credential controls in `Basic_Instructions.md`.

## Manual Installation Procedure

1. Download or clone the source repository to an authorized local location.
2. Locate the desired skill package by finding its `SKILL.md`.
3. Read the complete `SKILL.md`, including its metadata and activation instructions.
4. Review every supporting file and subfolder in the package.
5. Confirm that the skill is appropriate for this project and does not conflict with permanent instructions.
6. Confirm the exact `name` in the `SKILL.md` metadata.
7. Copy the complete skill package, including all initially supplied supporting files.
8. Place the package under:

   ```text
   skills/agent_skills/<exact-skill-name>/
   ```

9. Confirm that the required file now exists at:

   ```text
   skills/agent_skills/<exact-skill-name>/SKILL.md
   ```

10. Confirm that every relative link and referenced supporting path in `SKILL.md` still resolves from its new project location.

There is no universal copy or clone command for this process. External repository layouts and local source locations vary, so repository-specific commands must be determined only after inspecting the source.

## Verification

Before referencing a newly installed skill from a workflow, verify it independently with an AI-agnostic prompt such as:

```text
Read and follow:

skills/agent_skills/<skill-name>/SKILL.md

Before performing the task, confirm:

- the exact skill path;
- the skill name from its metadata;
- its activation instructions, when defined;
- any supporting files used.

Perform a small fictional task appropriate to the skill.

Do not modify existing project files during this test.
```

A successful test shows that the agent can locate the exact path, read the skill metadata and instructions, access required supporting files, and apply the skill to an appropriate task. It does not by itself approve the skill for production use or authorize changes to an active workflow.

## Workflow Integration

After standalone verification and the required review, an approved client/project workflow may reference the skill directly inside the checklist item that needs it:

```text
1. **Checklist item:** `qa-planning`
   - **Required Agent Skill:** `qa-test-planner`
```

The checklist value resolves to:

```text
skills/agent_skills/qa-test-planner/SKILL.md
```

The workflow uses the skill only for that checklist item and remains responsible for the client/project procedure. Control returns to the workflow checklist when the skill finishes. Agent Skills are not declared in workflow YAML metadata, and the skill does not select the workflow. No native discovery configuration for a particular AI product is required or defined by this project structure.

## Updating or Replacing a Skill

Before updating or replacing an installed skill:

1. Review the complete new version as untrusted external content.
2. Compare changes to `SKILL.md` and every supporting file.
3. Recheck scripts, commands, external URLs, tools, and dependencies.
4. Confirm that the metadata `name` has not changed unexpectedly.
5. Repeat the standalone skill verification with a small fictional task.
6. Confirm that existing checklist items still use the correct exact **Required Agent Skill** value.

Do not overwrite an approved skill package without review. Preserve the current approved version until the replacement has passed review and testing according to the project's change-control requirements.

## Troubleshooting

| Problem | What to check |
|---|---|
| The wrong repository root is open | Confirm the active repository contains this project's `Basic_Instructions.md`, `skills/`, and `ticket_runs/` paths. |
| The skill was copied into the wrong `skills` folder | Confirm the destination begins at this repository's `skills/agent_skills/`. |
| `SKILL.md` is missing or incorrectly named | Confirm the filename is exactly `SKILL.md` and is directly inside the skill folder. |
| The folder name does not match the metadata name | Compare the checklist item's **Required Agent Skill** value, folder name, and `SKILL.md` metadata `name` character for character. |
| Referenced supporting files were not copied | Review every relative reference in `SKILL.md` and restore the required files from the reviewed source package. |
| Relative paths are broken | Confirm the copied package preserved its internal folder relationships and path capitalization. |
| The skill requires explicit invocation | Read its activation instructions and invoke it exactly as documented. |
| Scripts require unavailable tools | Review the declared runtimes and dependencies; do not install or execute them without authorization. |
| The skill conflicts with project-wide instructions | Stop using the skill. `Basic_Instructions.md` takes precedence, and an authorized owner must resolve the conflict. |
| The agent reports only a filename | Require confirmation of the complete project path: `skills/agent_skills/<skill-name>/SKILL.md`. |
