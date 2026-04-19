# Agent Invocation Modes

**Audience:** anyone routing work to `agents/<id>/` — humans in Cursor / Claude Code / VS Code, AI assistants wrapping this repo, MCP clients, CI, or custom orchestrators.

**TL;DR:** The library exposes the same agents through many channels. **MCP is the canonical channel for production use** — it keeps agent specs, skill library, probes, and live-org context in sync so agent outputs stay grounded and citations stay resolvable. Other channels exist for sketching, teaching, and delivery-team handoff.

**Source:** this catalog was consolidated from an external review (Cursor, 2026-04-19) — see `feedback/FEEDBACK_LOG.md#2026-04-19-cursor-invocation-review`. Attributed and adopted; not every claim landed verbatim.

---

## The channels

| # | Channel | Who uses it | Enforcement | Best for |
|---|---|---|---|---|
| 1 | **MCP server (`get_agent` / `list_agents`)** | AI assistants with MCP client | Canonical — stays in sync with repo, ships probes + skills + live-org tools together | Production agent invocations; anything that needs real-org grounding; multi-tool workflows |
| 2 | Authored happy path in `AGENT.md` | Humans / AI reading the spec directly | By discipline only | Highest-fidelity single run; good for routers and multi-mode designers |
| 3 | Slash commands (`/build-flow`, `/audit-*`, etc.) | IDE users | Command wrapper bakes in flags + paths | Repeatable team workflows; "same command, different org alias" |
| 4 | Queue + `orchestrator` (`MASTER_QUEUE.md`) | Library maintainers | Orchestrator reads queue, routes builders | Skill-building and library-maintenance rows, **not** ad-hoc "fix this Flow" |
| 5 | Harness (`scripts/run_builder.py`) | CI / builder agents | Full 5-gate protocol (input → requirements → ground → build → seal) | Generated metadata that must compile in a target org |
| 6 | Bundle export (`scripts/export_agent_bundle.py`) | Consumer projects / delivery teams | Rewritten paths + shipped probes + shipped skills | Drop a single agent into a customer repo without vendoring the monorepo |
| 7 | Informal `@folder` chat (`@agents/<id>/` + natural language) | Humans exploring | None — all on the model's diligence | Fast sketching; **not** production; see mitigations below |
| 8 | PR / branch review (`code-reviewer`, `security-scanner`, `soql-optimizer`) | Reviewers on a feature branch | Static scan; no org needed for the three above | "Review this branch" workflows |
| 9 | Pre-push developer habit | Individual devs | By discipline only | `security-scanner` + `soql-optimizer` + `lwc-auditor` before `git push` |
| 10 | Multi-agent pipelines (choreographed) | Orchestrating caller | Intermediate reports written to disk per `docs/consumer-responsibilities.md` | `content-researcher` → `*-skill-builder` → `validator`; `object-designer` → `data-model-reviewer` |
| 11 | Advisory / pre-sales / architecture desk work | Consultants / architects | None — label as desk-level unless evidence attached | `org-assessor`, `waf-assessor`, `release-train-planner`, `sandbox-strategy-designer` |
| 12 | Delivery / change readiness | Release managers | Checklists + dependency ordering | `changeset-builder`, `data-loader-pre-flight`, `custom-metadata-and-settings-designer` |
| 13 | Incident / load / data-governance | On-call operators | "Go / no-go + questions" framing | `data-loader-pre-flight`, `duplicate-rule-designer`, `deployment-risk-scorer` |
| 14 | Training / onboarding (reading syllabus) | Juniors | AGENT.md + linked skills as curriculum | Grounding new hires in library conventions |
| 15 | Subagent / delegated tasks | Parent AI session dispatching to child | Parent enforces write-to-disk + envelope | Context isolation; parallel scans on different paths |

The deprecated folders (`validation-rule-auditor`, `workflow-rule-to-flow-migrator`, `sharing-audit-agent`, etc.) remain discoverable by muscle memory but **redirect** to routers — see `docs/MIGRATION.md`.

---

## Why MCP is the canonical channel

We're doubling down on MCP because the other channels all share the same structural failure mode: **context drift**. The agent reads an old version of `AGENT.md`, or the skill it cited was since renamed, or the probe it wants to run was never copied into the consuming project. Every non-MCP channel has its own plumbing for this — bundle rewrites paths, MCP ships the library intact, informal chat hopes for the best.

MCP wins because:

| Problem | How MCP handles it |
|---|---|
| Agent spec goes stale in consumer project | Server reads straight from the repo; every `get_agent` call is current |
| Probes dropped on the floor | `list_agents` / `get_agent` return dependency graph; caller can't skip them accidentally |
| Skill citations broken | Same server exposes `search_skill` / `get_skill`; no version skew between agent spec and skill it cites |
| Live-org grounding is ad-hoc | `describe_org`, `tooling_query`, `probe_apex_references`, `validate_against_org` all ship with the agent surface |
| Consumer forgets persistence contract | Server can surface `docs/consumer-responsibilities.md` as a tool resource |

**The tools MCP currently exposes** (as of 2026-04-19):

- **Agent discovery:** `list_agents`, `get_agent`
- **Skill discovery:** `search_skill`, `get_skill`
- **Org grounding:** `describe_org`, `list_custom_objects`, `list_flows_on_object`, `list_validation_rules`, `list_permission_sets`, `describe_permission_set`, `list_record_types`, `list_named_credentials`, `list_approval_processes`, `tooling_query`, `validate_against_org`
- **Probes:** `probe_apex_references`, `probe_flow_references`, `probe_matching_rules`, `probe_permset_shape`

**What MCP is missing** (tracked in `feedback/FEEDBACK_LOG.md` as ACCEPT-queued):

- A `list_deprecated_redirects` tool so clients asking for `validation-rule-auditor` get routed to `audit-router --domain=validation_rule` automatically, not a dead stub.
- A `get_invocation_modes` tool exposing this doc so clients can surface the right channel for the task.
- An `automation_graph_for_sobject` probe tool (the recipe already exists at `agents/_shared/probes/automation-graph-for-sobject.md` — needs to be lifted into the server).
- An `emit_envelope` helper that writes the final envelope + paired markdown to `docs/reports/<agent>/<run_id>.{json,md}` per `docs/consumer-responsibilities.md`, so consumers don't have to implement persistence themselves.

---

## Quick picker: which channel for your situation?

| You have… | Reach for… |
|---|---|
| An AI assistant with MCP connected | **Channel 1 (MCP)**. Default. |
| An IDE with slash commands shipped | Channel 3 (slash). |
| Only Cursor chat and a vague sentence | Channel 7 (informal), but force the model to name **artifacts** (paths, Ids, domains) in the same message. |
| A CI pipeline that must compile metadata | Channel 5 (harness). |
| A customer repo that shouldn't vendor the monorepo | Channel 6 (bundle export) or Channel 1 if they can run MCP. |
| A PR to review | Channel 8 (PR review with static agents). |
| A library maintenance task | Channel 4 (queue + orchestrator). |
| Pre-sales / architecture deck | Channel 11 (advisory). Label confidence; attach evidence. |

If you're an AI assistant reading this — **default to channel 1 unless you have a specific reason to use another**.

---

## What informal chat can't fix

- **Org-complete inventory without a read path.** You cannot honestly enumerate active flows, deployed permission sets, or existing integration endpoints from a vibe. MCP + live org, or pasted exports, or label outputs as desk-level.
- **Builder-vs-runtime agent confusion.** `@admin-skill-builder` writes a skill doc. It does not fix permissions in your org. See `agents/_shared/AGENT_DISAMBIGUATION.md`.
- **Deprecated-name muscle memory.** Typing `@validation-rule-auditor` lands on a stub. Use `audit-router --domain=validation_rule`.

---

## Related canonical docs

- [`agents/_shared/CAPABILITY_MATRIX.md`](../agents/_shared/CAPABILITY_MATRIX.md) — Advisory vs Harness per builder agent.
- [`agents/_shared/AGENT_DISAMBIGUATION.md`](../agents/_shared/AGENT_DISAMBIGUATION.md) — which agent for which intent (overlap pairs resolved).
- [`docs/installing-single-agents.md`](installing-single-agents.md) — MCP vs bundle export trade-offs.
- [`docs/consumer-responsibilities.md`](consumer-responsibilities.md) — what every consuming AI MUST do (persist + envelope + no silent dimension drops).
- [`docs/MIGRATION.md`](MIGRATION.md) — routers vs retired agents.

---

## Provenance

The 15-channel catalog, the Quick Picker framing, and the informal-vs-happy-path distinction in this doc were adopted from an external Cursor-authored review (`agent-informal-invocation-analysis.md`, 2026-04-19). Triage, MCP-first framing, and the list of what MCP is missing are this repo's own. See `feedback/FEEDBACK_LOG.md#2026-04-19-cursor-invocation-review`.
