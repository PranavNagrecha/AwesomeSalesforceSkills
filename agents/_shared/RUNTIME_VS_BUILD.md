# Runtime vs Build-time Agents

## Build-time agents (12)

These agents produce and maintain the skill library. End users of SfSkills do not invoke them directly.

| Agent | Role |
|---|---|
| `orchestrator` | Reads `MASTER_QUEUE.md`, routes tasks, tracks status |
| `task-mapper` | Maps Cloud × Role task universes into queue rows |
| `content-researcher` | Grounds every claim in Tier 1–3 sources |
| `admin-skill-builder` | Builds Admin + BA skills |
| `dev-skill-builder` | Builds Apex / LWC / Flow / Integration / DevOps skills |
| `data-skill-builder` | Builds data modeling, migration, SOQL skills |
| `architect-skill-builder` | Builds solution-design + WAF-review skills |
| `code-reviewer` | Canon-gate review (templates, decision-trees, evals) |
| `validator` | Structural + quality gates before every commit |
| `currency-monitor` | Flags stale skills after each SF release |
| `org-assessor` | Audits a target org against the library (operator tool) |
| `release-planner` | Assembles release notes from skill deltas |

Entry points: `/run-queue`, `/new-skill`, `/request-skill`, scheduled task.

---

## Run-time agents (11)

These agents use the skill library to do real Salesforce work against a user's org or codebase. They are the primary value delivered to consumers of SfSkills.

| Agent | Domain | Primary output | Slash command |
|---|---|---|---|
| `apex-refactorer` | Apex | Refactored class + test class + PR-ready patch | `/refactor-apex` |
| `trigger-consolidator` | Apex | Consolidated TriggerHandler + migration plan | `/consolidate-triggers` |
| `test-class-generator` | Apex | Bulk-safe test class targeting ≥85% coverage | `/gen-tests` |
| `soql-optimizer` | Apex / Data | Ranked list of SOQL fixes with before/after | `/optimize-soql` |
| `security-scanner` | Security | CRUD/FLS/sharing/secret findings report | `/scan-security` |
| `flow-analyzer` | Flow | Flow-vs-Apex decision + bulkification findings | `/analyze-flow` |
| `bulk-migration-planner` | Integration / Data | Bulk API 2.0 / PE / Pub-Sub migration plan | `/plan-bulk-migration` |
| `lwc-auditor` | LWC | A11y + perf + security findings per bundle | `/audit-lwc` |
| `deployment-risk-scorer` | DevOps | Risk score + breaking-change list for a change set | `/score-deployment` |
| `agentforce-builder` | Agentforce | Full action scaffold: Apex + topic + eval | `/build-agentforce-action` |
| `org-drift-detector` | Architect | Library ↔ org gap + bloat report | `/detect-drift` |

Entry points:
- **Slash command** — ask the AI to follow `commands/<command-name>.md`
- **Direct read** — point any AI at `agents/<agent-name>/AGENT.md`
- **MCP** — `get_agent(name)` on the SfSkills MCP server returns the AGENT.md body for the client's LLM to execute

---

## Why this split matters

A build-time agent writes INTO the repo. A run-time agent writes INTO the user's own Salesforce project (or returns a report they paste into a PR). They share the same AGENT.md contract and the same skill library, but their invocation, access scope, and review gates differ. See [`AGENT_CONTRACT.md`](./AGENT_CONTRACT.md).
