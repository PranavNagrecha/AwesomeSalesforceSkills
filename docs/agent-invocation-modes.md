# Agent Invocation Modes

**Audience:** anyone routing work to `agents/<id>/` — humans in Cursor / Claude
Code / VS Code, AI assistants wrapping this repo, MCP clients, CI, or custom
orchestrators.

**TL;DR:** The library exposes the same 48 active run-time agents through many
channels. **MCP is the canonical channel for production use** — it keeps agent
specs, skill library, probes, and live-org context in sync so agent outputs stay
grounded and citations stay resolvable. Other channels exist for sketching,
teaching, and delivery-team handoff.

**One caveat before you rely on that recommendation:** installing the SfSkills
plugin does **not** connect the MCP server. `.claude-plugin/plugin.json` declares
`skills` and `commands` and has no `mcpServers` key, so a user has to wire the
server up themselves. Channel 1 is the best channel; it is not the default one.

**This file is itself an MCP tool resource** — `get_invocation_modes` returns it
verbatim (`mcp/sfskills-mcp/src/sfskills_mcp/meta.py:205-225`). Agents read it,
so keep it accurate.

**Source:** this catalog was consolidated from an external review (Cursor,
2026-04-19) — see `feedback/FEEDBACK_LOG.md`, anchor
`2026-04-19-cursor-invocation-review`. Attributed and adopted; not every claim
landed verbatim.

Verified against this checkout on 2026-08-15.

---

## The channels

| # | Channel | Who uses it | Enforcement | Best for |
|---|---|---|---|---|
| 1 | **MCP server (`get_agent` / `list_agents`)** | AI assistants with MCP client | Canonical — stays in sync with repo, ships probes + skills + live-org tools together | Production agent invocations; anything that needs real-org grounding; multi-tool workflows |
| 2 | Authored happy path in `AGENT.md` | Humans / AI reading the spec directly | By discipline only | Highest-fidelity single run; good for routers and multi-mode designers |
| 3 | Slash commands (`/build-flow`, `/audit-router`, etc.) — 67 of them | IDE users | Command wrapper bakes in flags + paths | Repeatable team workflows; "same command, different org alias" |
| 4 | Queue + `orchestrator` (`BACKLOG.yaml`) | Library maintainers | Orchestrator reads the queue, routes builders | Skill-building and library-maintenance rows, **not** ad-hoc "fix this Flow" |
| 5 | Harness (`scripts/run_builder.py`) | CI / builder agents | Full 5-gate protocol — Gate A inputs, A.5 requirements, B ground, C build, D seal | Generated metadata that must compile in a target org |
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

Fourteen agent folders are deprecated stubs — `validation-rule-auditor`,
`sharing-audit-agent`, `picklist-governor`, `org-drift-detector` and ten more.
Every one of them redirects to `audit-router`; nine also keep a legacy slash
command alias in `commands/`. See [`docs/MIGRATION.md`](MIGRATION.md) for the
full mapping and the removal window.

---

## Why MCP is the canonical channel

We're doubling down on MCP because the other channels all share the same
structural failure mode: **context drift**. The agent reads an old version of
`AGENT.md`, or the skill it cited was since renamed, or the probe it wants to run
was never copied into the consuming project. Every non-MCP channel has its own
plumbing for this — bundle rewrites paths, MCP ships the library intact, informal
chat hopes for the best.

MCP wins because:

| Problem | How MCP handles it |
|---|---|
| Agent spec goes stale in consumer project | Server reads straight from the repo; every `get_agent` call is current |
| Probes dropped on the floor | `list_agents` / `get_agent` return the dependency graph; the caller can't skip them accidentally |
| Skill citations broken | Same server exposes `search_skill` / `get_skill`; no version skew between agent spec and the skill it cites |
| Live-org grounding is ad-hoc | `describe_org`, `tooling_query`, `probe_apex_references`, `validate_against_org` all ship with the agent surface |
| Consumer forgets persistence contract | `get_invocation_modes` returns this document as a tool resource |

**The MCP surface — 38 tools**, verified by counting `@mcp.tool` registrations in
`mcp/sfskills-mcp/src/sfskills_mcp/server.py` (the same derivation
`scripts/check_doc_counts.py` gates):

- **Agent discovery (3):** `list_agents` (filter `kind`: `runtime` / `build` /
  `deprecated` / `all`, or omit), `get_agent`, `suggest_agent` (free-text →
  ranked agents + decision-tree branches)
- **Skill discovery (2):** `search_skill`, `get_skill`
- **Knowledge search (5):** `search_agents`, `search_templates`,
  `search_decision_trees`, `get_template`, `get_decision_tree`
- **Org grounding — core (4):** `describe_org`, `list_custom_objects`,
  `list_flows_on_object`, `validate_against_org`
- **Org grounding — admin (7):** `list_validation_rules`, `list_permission_sets`,
  `describe_permission_set`, `list_record_types`, `list_named_credentials`,
  `list_approval_processes`, `tooling_query`
- **Org grounding — developer (8):** `list_apex_classes`, `get_apex_class`,
  `list_apex_triggers`, `list_lwc_bundles`, `get_lwc_bundle`,
  `list_custom_fields`, `describe_object_full` (composite), `list_orgs`
- **Probes (5):** `probe_apex_references`, `probe_flow_references`,
  `probe_matching_rules`, `probe_permset_shape`, `probe_automation_graph`. Four
  of the five emit `notifications/progress` so clients render real-time status —
  all except `probe_permset_shape`.
- **Meta / persistence (4):** `list_deprecated_redirects`,
  `get_invocation_modes`, `emit_envelope`, `health`

`search_skill` is subject to the same install caveat as everything else in
mechanism 2: it needs a built index. `vector_index/` is gitignored
(`git ls-files vector_index` returns three fixture/metadata files), so a fresh
clone or a PyPI install has nothing to search until `python3
scripts/bootstrap.py` runs. See [architecture.md](architecture.md).

Beyond Tools the server also exposes:

- **Prompts** — every wrapper in `commands/*.md` registers as an MCP prompt, **67
  of them** (`prompts.register_all`, `prompts.py:112`). Clients render them as
  native slash commands.
- **Resources** — `sfskills://catalog`, `sfskills://skill/{id}`,
  `sfskills://agent/{name}`, `sfskills://decision-tree/{name}`,
  `sfskills://template/{path}`. Use the `domain__name` form for IDs that contain
  slashes.
- **Tool annotations** — **all 38** tools carry `readOnlyHint` /
  `destructiveHint` / `idempotentHint` / `openWorldHint`, drawn from three honest
  presets (`server.py:84-101`): `_ANN_REPO_ONLY` for pure repo reads,
  `_ANN_ORG_READ` for read-only `sf` CLI calls (open-world, don't cache), and
  `_ANN_ENVELOPE` for `emit_envelope`, the one tool that writes. MCP-aware
  clients can auto-approve safely.

---

## Quick picker: which channel for your situation?

| You have… | Reach for… |
|---|---|
| An AI assistant with MCP connected | **Channel 1 (MCP)**. Default. |
| The plugin installed but no MCP server | Channel 3 (slash commands) plus the shipped router skills — that combination needs no setup at all. |
| An IDE with slash commands shipped | Channel 3 (slash). |
| Only Cursor chat and a vague sentence | Channel 7 (informal), but force the model to name **artifacts** (paths, Ids, domains) in the same message. |
| A CI pipeline that must compile metadata | Channel 5 (harness). |
| A customer repo that shouldn't vendor the monorepo | Channel 6 (bundle export) or Channel 1 if they can run MCP. |
| A PR to review | Channel 8 (PR review with static agents). |
| A library maintenance task | Channel 4 (queue + orchestrator). |
| Pre-sales / architecture deck | Channel 11 (advisory). Label confidence; attach evidence. |

If you're an AI assistant reading this — **default to channel 1 unless you have a
specific reason to use another**, and fall back to channel 3 rather than
freestyling when the MCP server is not connected.

---

## What informal chat can't fix

- **Org-complete inventory without a read path.** You cannot honestly enumerate
  active flows, deployed permission sets, or existing integration endpoints from
  a vibe. MCP + live org, or pasted exports, or label outputs as desk-level.
- **Builder-vs-runtime agent confusion.** `@admin-skill-builder` writes a skill
  doc. It does not fix permissions in your org. See
  `agents/_shared/AGENT_DISAMBIGUATION.md`.
- **Deprecated-name muscle memory.** Typing `@validation-rule-auditor` lands on a
  stub. Use `/audit-router --domain validation_rule --object <ApiName>
  --target-org <alias>` — one of 15 supported `--domain` values listed in
  [`commands/audit-router.md`](../commands/audit-router.md).

---

## Related canonical docs

- [`agents/_shared/CAPABILITY_MATRIX.md`](../agents/_shared/CAPABILITY_MATRIX.md) — Advisory vs Harness per builder agent.
- [`agents/_shared/AGENT_DISAMBIGUATION.md`](../agents/_shared/AGENT_DISAMBIGUATION.md) — which agent for which intent (overlap pairs resolved).
- [`agents/_shared/RUNTIME_VS_BUILD.md`](../agents/_shared/RUNTIME_VS_BUILD.md) — the 48 / 14 / 14 split.
- [`docs/installing-single-agents.md`](installing-single-agents.md) — MCP vs bundle export trade-offs.
- [`docs/consumer-responsibilities.md`](consumer-responsibilities.md) — what every consuming AI MUST do (persist + envelope + no silent dimension drops).
- [`docs/architecture.md`](architecture.md) — the three retrieval mechanisms, and which of them actually ships.
- [`docs/MIGRATION.md`](MIGRATION.md) — routers vs retired agents.

---

## Provenance

The 15-channel catalog, the Quick Picker framing, and the informal-vs-happy-path
distinction in this doc were adopted from an external Cursor-authored review
(2026-04-19, written when the roster stood at 75 agents). Triage, MCP-first
framing, and the list of what MCP is missing are this repo's own. See
`feedback/FEEDBACK_LOG.md`, anchor `2026-04-19-cursor-invocation-review`.
