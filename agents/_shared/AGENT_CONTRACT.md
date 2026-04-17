# Agent Contract

Every agent in this repo — build-time or run-time — follows the same contract. This file defines that contract.

---

## Two classes of agents

| Class | Purpose | Examples | Invoked by |
|---|---|---|---|
| **Build-time** | Produce and maintain the skill library itself | `orchestrator`, `task-mapper`, `content-researcher`, the 4 `*-skill-builder` agents, `validator`, `currency-monitor` | Repo maintainers via `/run-queue`, scheduled task |
| **Run-time** | Use the skill library to do real Salesforce work against a user's org / codebase | `apex-refactorer`, `trigger-consolidator`, `test-class-generator`, `soql-optimizer`, `security-scanner`, `flow-analyzer`, `bulk-migration-planner`, `lwc-auditor`, `deployment-risk-scorer`, `agentforce-builder`, `org-drift-detector` | End users via slash commands, direct AGENT.md read, or MCP `get_agent` tool |

See [`RUNTIME_VS_BUILD.md`](./RUNTIME_VS_BUILD.md) for the full roster.

---

## AGENT.md frontmatter (required)

Every `agents/<slug>/AGENT.md` MUST start with a YAML frontmatter block validated against [`schemas/agent-frontmatter.schema.json`](./schemas/agent-frontmatter.schema.json):

```yaml
---
id: field-impact-analyzer          # must match the folder name (kebab-case)
class: runtime                     # runtime | build
version: 1.0.0                     # semver
status: stable                     # stable | beta | deprecated
requires_org: true                 # true if the agent needs an sf org alias to function
modes: [single]                    # [single] or [design, audit] etc. — free list of mode names
owner: sfskills-core               # team or handle responsible for the agent
created: 2026-04-16                # ISO date of first commit
updated: 2026-04-16                # ISO date of last material change
---
```

The canonical list of frontmatter keys, enums, and constraints lives in the JSON Schema. Do not duplicate it here.

---

## What an AGENT.md must contain

The required section shape depends on the agent's `class`.

### Run-time agents (`class: runtime`)

MUST have — after the frontmatter — all eight sections, in this order:

1. **What This Agent Does** — one paragraph, plain English, ends with the scope boundary.
2. **Invocation** — the three invocation modes (direct read / slash command / MCP `get_agent`) and what args the agent expects.
3. **Mandatory Reads Before Starting** — the files and skills the agent MUST read first. Always includes `AGENT_RULES.md` + any domain-specific decision trees or templates.
4. **Inputs** — structured list of what the agent needs from the caller (file paths, object names, target org alias, etc.). Ask for missing inputs up front; never guess. The canonical schema for typed inputs lives alongside the agent at `agents/<slug>/inputs.schema.json` when present; the Inputs section in the markdown is the human-readable view of that schema.
5. **Plan** — numbered steps. Each step cites the skill, template, or decision tree it relies on. Steps use MCP tools where the agent needs live-org data. Where possible, steps reference a probe recipe from [`probes/`](./probes/) rather than inlining a SOQL snippet.
6. **Output Contract** — exactly what the agent returns. Every run-time agent returns an envelope conforming to [`schemas/output-envelope.schema.json`](./schemas/output-envelope.schema.json), including at minimum: a `summary`, a `confidence` score (HIGH/MEDIUM/LOW — see rubric below), a **Process Observations** block (see below), and `citations[]` listing every skill/template/decision-tree branch the agent consulted.
7. **Escalation / Refusal Rules** — conditions under which the agent stops and asks a human. Refusal reasons should use the canonical codes from [`REFUSAL_CODES.md`](./REFUSAL_CODES.md) so downstream tooling can aggregate them. At minimum every agent covers: missing org connection when one is required, ambiguous inputs, contradicting skills (resolved per `standards/source-hierarchy.md`).
8. **What This Agent Does NOT Do** — explicit non-goals. Prevents scope creep.

### Build-time agents (`class: build`)

Build-time agents don't take caller-supplied inputs and don't produce user-facing deliverables in the same way — they read queues, commit skills, route work. They MUST have:

1. **What This Agent Does**
2. **Invocation** (alias: `Activation Triggers`, `Triggers`)
3. **Mandatory Reads Before Starting**
4. **Plan** (alias: `Orchestration Plan`)
5. **What This Agent Does NOT Do** (alias: `Anti-Patterns`)

Build-time agents MAY include `Inputs`, `Output Contract` (alias: `Output Format`), and `Escalation / Refusal Rules` when those concepts apply.

### Accepted section aliases

| Canonical name | Also accepted as |
|---|---|
| Invocation | `Activation Triggers`, `Triggers` |
| Plan | `Orchestration Plan` |
| Output Contract | `Output Format` |
| Escalation / Refusal Rules | `Escalation Rules` |
| What This Agent Does NOT Do | `Anti-Patterns` |

### The Process Observations requirement

Every run-time agent's Output Contract MUST include a **Process Observations** section, separate from the direct deliverable. This is the agent reporting back what it noticed *about the org and the process* while executing the task — the kind of peripheral signal a senior consultant captures in their head during a one-hour engagement but a junior admin walks past.

Why this matters: we are not just building. We are building while analyzing. Every agent run is also a lightweight assessment of the org's health in the agent's domain. An admin asking "rename this field" should also learn "by the way, 12 fields on this object have never been populated" — because that's the formula a real architect runs in the background.

Process Observations must include at minimum:

- **What was healthy** — patterns the org already gets right that the agent noticed in passing.
- **What was concerning** — issues the agent saw that weren't part of the direct ask but warrant attention.
- **What was ambiguous** — things the agent couldn't resolve and the human should adjudicate.
- **Suggested follow-up agents** — one or two other run-time agents that would deepen the analysis, with a one-sentence "because…".

Each observation conforms to [`schemas/observation.schema.json`](./schemas/observation.schema.json) so every run contributes to a rollable org-health signal.

Rules:

- Process Observations are observations, not accusations. "Noticed X" not "You did Y wrong."
- Every observation cites what the agent was looking at when it made the call — a file path, an MCP probe result, a query count.
- Do not inflate. If the agent genuinely observed nothing notable beyond the deliverable, say "nothing notable outside the direct finding." Empty honesty beats padded signal.
- Process Observations do NOT cross the boundary into the deliverable. They enrich, they don't replace.

### The Confidence rubric

Every run-time agent reports a single overall confidence: **HIGH / MEDIUM / LOW**. Absent a domain-specific override in the agent's own Plan, use this default rubric:

| Score | Condition |
|---|---|
| **HIGH** | All mandatory inputs were supplied, all required MCP probes returned without pagination or truncation errors, every recommendation cites at least one skill or template that exists in the registry, and the repo scan (if any) ran over a complete codebase. |
| **MEDIUM** | One probe paginated, one recommendation freestyled (no matching skill), or one mandatory-but-soft input (e.g. `repo_path`) was missing and a sensible default was used. |
| **LOW** | Any of: the target org was unreachable; a required input was missing and substituted; a critical skill/template citation resolved to a TODO; the agent had to freestyle more than one recommendation. |

An agent MAY override or extend this rubric in its Plan, but MAY NOT omit the score.

### Citations

Citations are data, not prose. Every output ends with a `citations[]` block where each entry matches [`schemas/citation.schema.json`](./schemas/citation.schema.json):

```json
{
  "type": "skill",
  "id": "admin/permission-set-architecture",
  "path": "skills/admin/permission-set-architecture/SKILL.md",
  "used_for": "PSG composition per persona"
}
```

`type` is one of `skill`, `template`, `standard`, `decision_tree`, `mcp_tool`, `probe`. Every citation must resolve to a real path (or a real MCP tool name) at validation time.

---

## Rules every agent follows

1. **Skill-first, never freestyle.** If `search_skill` or `get_skill` returns a matching skill, the agent MUST use that skill's guidance. If no skill matches, the agent MAY freestyle but MUST flag `confidence: LOW` and suggest adding the missing skill via `/request-skill`.

2. **Templates are canonical.** When generating Apex / LWC / Flow / Agentforce scaffolds, reference the file under `templates/` — never inline a parallel implementation. If a template is incomplete for the use case, flag it in the report instead of freestyling.

3. **Decision trees route technology choices.** If the user's request involves picking between automation / async / integration / sharing mechanisms, the agent MUST consult the matching file under `standards/decision-trees/` and cite which branch it followed.

4. **Source hierarchy for contradictions.** When skills disagree, Tier 1 (official Salesforce docs) wins. Per `standards/source-hierarchy.md`.

5. **Org-aware where possible.** If an MCP target-org is connected, the agent SHOULD call `describe_org` / `list_custom_objects` / `list_flows_on_object` / `validate_against_org` to ground recommendations in reality. If no org is connected, the agent MUST say so in the output and continue in "library-only" mode.

6. **Shared probes over inline SOQL.** Where a probe recipe exists under [`probes/`](./probes/) for an Apex-reference scan, a Flow-metadata scan, a matching/duplicate-rule listing, etc., the agent MUST cite the probe rather than inline the SOQL. This is how we prevent the same false-positive-avoidance logic from being re-invented in every agent.

7. **No hidden side effects.** Run-time agents NEVER deploy to an org, NEVER run `sf project deploy`, NEVER mutate files outside the paths the user gave as input. They produce plans, patches, and reports — execution is the human's call.

8. **One agent per invocation.** No auto-chaining. If another agent would help, recommend it in the output; don't silently invoke it.

9. **Return a report the user can paste into a PR.** Every output ends with a "Citations" block listing every skill id, template path, probe id, and decision tree branch the agent consulted — structured per the Citations schema above.

---

## Anti-patterns

- Reading `skills/` by globbing. Use `search_skill` or `get_skill` — they respect the registry.
- Inlining Apex patterns from memory. Use `templates/apex/*.cls`.
- Recommending a technology without citing the decision tree.
- Returning "HIGH confidence" without at least one official Salesforce docs citation in the skill's `references/`.
- Running `sf project deploy`, `sf data upsert`, or any write operation against the org.
- Inlining SOQL that already exists as a probe recipe.
- Returning Process Observations that restate the deliverable instead of adding peripheral signal.

---

## Testing an agent

Before a new AGENT.md is merged, it must pass:

1. **Structural gate** — `python3 scripts/validate_repo.py --agents` passes. This enforces frontmatter schema, section order, citation resolution, MCP-tool-name resolution, slash-command resolution, and follow-up-agent resolution.
2. **Citation gate** — every skill / template / decision tree / probe the AGENT.md mentions must exist at the cited path. Enforced by the structural gate.
3. **Dry-run gate** — the maintainer runs the agent's plan against a sample input and checks that the output envelope is well-formed. See [`evals/agents/README.md`](../../evals/agents/README.md) for the snapshot-eval harness.

See [`commands/review.md`](../../commands/review.md) for the review flow.
