# Agent Invocation Modes

**Audience:** anyone routing work to `agents/<id>/` — humans in Cursor / Claude
Code / VS Code, AI assistants wrapping this repo, MCP clients, CI, or custom
orchestrators.

**TL;DR:** The library exposes the same active run-time agents (7 stable, 8 beta,
55 experimental — see
[`agents/_shared/RUNTIME_VS_BUILD.md`](../agents/_shared/RUNTIME_VS_BUILD.md))
through the fifteen channels below. The shipped default is the Claude Code
plugin: router skills plus slash commands (channel 3). The MCP server
(channel 1) adds live-org read tools, but the plugin does not connect it:
`.claude-plugin/plugin.json` declares `skills` and `commands` and has no
`mcpServers` key, so a user wires the server up themselves.

**This file is itself an MCP tool resource** — `get_invocation_modes` returns it
verbatim (`mcp/sfskills-mcp/src/sfskills_mcp/meta.py`). Agents read it, so keep
it accurate.

---

## The channels

| # | Channel | Who uses it | Enforcement | Best for |
|---|---|---|---|---|
| 1 | **MCP server (`get_agent` / `list_agents`)** | AI assistants with an MCP client | Server reads specs from the repo it runs against; ships skills, agent specs and read-only org tools together | Runs that need live-org reads; multi-tool workflows |
| 2 | Authored happy path in `AGENT.md` | Humans / AI reading the spec directly | By discipline only | A single careful run; routers and multi-mode designers |
| 3 | Slash commands (`/build-flow`, `/audit-router`, etc.) | IDE users | Command wrapper bakes in flags + paths | Repeatable team workflows; "same command, different org alias" |
| 4 | Release plan + `orchestrator` (`RELEASES.yaml`, `/start-building`) | Library maintainers | Orchestrator reads the plan through `scripts/release_plan.py` | Library-maintenance items, **not** ad-hoc "fix this Flow" |
| 5 | Harness (`scripts/run_builder.py`) | CI / builder agents | Gate protocol — inputs, requirements, grounding, build, seal | Generated metadata that must compile in a target org |
| 6 | Bundle export (`scripts/export_agent_bundle.py`) | Consumer projects / delivery teams | Rewritten paths + shipped probes + shipped skills | Drop a single agent into a customer repo without vendoring the monorepo |
| 7 | Informal `@folder` chat (`@agents/<id>/` + natural language) | Humans exploring | None — all on the model's diligence | Fast sketching only; see mitigations below |
| 8 | PR / branch review (`code-reviewer`, `security-scanner`, `soql-optimizer`) | Reviewers on a feature branch | Static scan; no org needed for the three above | "Review this branch" workflows |
| 9 | Pre-push developer habit | Individual devs | By discipline only | `security-scanner` + `soql-optimizer` + `lwc-auditor` before `git push` |
| 10 | Multi-agent pipelines (choreographed) | Orchestrating caller | Intermediate reports written to disk per `docs/consumer-responsibilities.md` | `object-designer` → `data-model-reviewer`; the build loop's Tier 4 agents |
| 11 | Advisory / pre-sales / architecture desk work | Consultants / architects | None — label as desk-level unless evidence attached | `org-assessor`, `waf-assessor`, `release-train-planner`, `sandbox-strategy-designer` |
| 12 | Delivery / change readiness | Release managers | Checklists + dependency ordering | `changeset-builder`, `data-loader-pre-flight`, `custom-metadata-and-settings-designer` |
| 13 | Incident / load / data-governance | On-call operators | "Go / no-go + questions" framing | `data-loader-pre-flight`, `duplicate-rule-designer`, `deployment-risk-scorer` |
| 14 | Training / onboarding (reading syllabus) | Juniors | AGENT.md + linked skills as curriculum | Introducing new hires to library conventions |
| 15 | Subagent / delegated tasks | Parent AI session dispatching to child | Parent enforces write-to-disk + envelope | Context isolation; parallel scans on different paths |

Most agents named above are `status: experimental` (ungraded). Check an agent's
status in `RUNTIME_VS_BUILD.md` before relying on its output.

Fourteen agent folders are deprecated stubs — `validation-rule-auditor`,
`sharing-audit-agent`, `picklist-governor`, `org-drift-detector` and ten more.
Every one of them redirects to `audit-router`; nine also keep a slash command
alias in `commands/`. The alias table is in
[`agents/_shared/RUNTIME_VS_BUILD.md`](../agents/_shared/RUNTIME_VS_BUILD.md#deprecated-slash-command-redirects).

---

## What the MCP server adds

| Problem | How the MCP server handles it |
|---|---|
| Agent spec goes stale in a consumer project | Server reads from the checkout or data bundle it runs against |
| Probes dropped on the floor | `list_agents` / `get_agent` return the dependency graph |
| Skill citations broken | Same server exposes `search_skill` / `get_skill` |
| Live-org grounding is ad-hoc | `describe_org`, `tooling_query`, `probe_apex_references`, `validate_against_org` ship with the agent surface |
| Consumer forgets persistence contract | `get_invocation_modes` returns this document; `emit_envelope` writes the report |

**The MCP surface — 50 tools**, counted from `@mcp.tool` registrations in
`mcp/sfskills-mcp/src/sfskills_mcp/server.py` (the same derivation
`scripts/check_doc_counts.py` gates). Every org call is a read through the `sf`
CLI; no tool performs DML, deploys, or runs Apex.

- **Agent discovery:** `list_agents`, `get_agent`, `suggest_agent`
- **Skill and knowledge search:** `search_skill`, `get_skill`, `search_agents`,
  `search_templates`, `search_decision_trees`, `get_template`, `get_decision_tree`
- **Org reads — core and admin:** `describe_org`, `list_orgs`,
  `list_custom_objects`, `list_flows_on_object`, `validate_against_org`,
  `list_validation_rules`, `list_permission_sets`, `describe_permission_set`,
  `list_record_types`, `list_named_credentials`, `list_approval_processes`,
  `tooling_query`
- **Org reads — developer:** `list_apex_classes`, `get_apex_class`,
  `list_apex_triggers`, `list_lwc_bundles`, `get_lwc_bundle`,
  `list_custom_fields`, `describe_object_full`
- **Probes:** `probe_apex_references`, `probe_flow_references`,
  `probe_matching_rules`, `probe_permset_shape`, `probe_automation_graph`
- **Evidence readers:** `get_deployment_result`, `get_apex_test_run`,
  `get_user_access_evidence`, `get_component_dependency_evidence`,
  `get_automation_inventory`, `get_flow_test_result`,
  `get_code_analysis_result`, `get_integration_config_summary`,
  `get_data_load_result`, `get_org_snapshot_manifest`,
  `get_agentforce_test_result`, `compare_org_snapshots`
- **Meta / persistence:** `list_deprecated_redirects`,
  `get_invocation_modes`, `emit_envelope`, `health`

`search_skill` needs a built index. `vector_index/` is gitignored, so a fresh
clone has nothing to search until `python3 scripts/bootstrap.py` runs; a PyPI
install downloads a lexical-only data bundle. See
[architecture.md](architecture.md).

Beyond tools the server also exposes:

- **Prompts** — every wrapper in `commands/*.md` registers as an MCP prompt
  (`prompts.register_all`). Clients render them as native slash commands.
- **Resources** — `sfskills://catalog`, `sfskills://skill/{id}`,
  `sfskills://agent/{name}`, `sfskills://decision-tree/{name}`,
  `sfskills://template/{path}`. Use the `domain__name` form for IDs that contain
  slashes.
- **Tool annotations** — every tool carries `readOnlyHint` /
  `destructiveHint` / `idempotentHint` / `openWorldHint`, drawn from three
  presets in `server.py`: `_ANN_REPO_ONLY` for pure repo reads, `_ANN_ORG_READ`
  for read-only `sf` CLI calls (open-world, don't cache), and `_ANN_ENVELOPE`
  for `emit_envelope`, the one tool that writes.

---

## Quick picker: which channel for your situation?

| You have… | Reach for… |
|---|---|
| The plugin installed, no MCP server | **Channel 3** (slash commands) plus the shipped router skills — no setup needed. |
| An AI assistant with MCP connected and a live org to read | Channel 1 (MCP). |
| An IDE with slash commands shipped | Channel 3 (slash). |
| Only Cursor chat and a vague sentence | Channel 7 (informal), but force the model to name **artifacts** (paths, Ids, domains) in the same message. |
| A CI pipeline that must compile metadata | Channel 5 (harness). |
| A customer repo that shouldn't vendor the monorepo | Channel 6 (bundle export) or Channel 1 if they can run MCP. |
| A PR to review | Channel 8 (PR review with static agents). |
| A library maintenance task | Channel 4 (release plan + orchestrator). |
| Pre-sales / architecture deck | Channel 11 (advisory). Label confidence; attach evidence. |

If you're an AI assistant reading this — use channel 1 when the MCP server is
connected and the task needs org reads; otherwise use channel 3 rather than
freestyling.

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
  --target-org <alias>` — one of the `--domain` values listed in
  [`commands/audit-router.md`](../commands/audit-router.md).

---

## Related docs

- [`agents/_shared/CAPABILITY_MATRIX.md`](../agents/_shared/CAPABILITY_MATRIX.md) — Advisory vs Harness per builder agent.
- [`agents/_shared/AGENT_DISAMBIGUATION.md`](../agents/_shared/AGENT_DISAMBIGUATION.md) — which agent for which intent (overlap pairs resolved).
- [`agents/_shared/RUNTIME_VS_BUILD.md`](../agents/_shared/RUNTIME_VS_BUILD.md) — the run-time / build-time / deprecated split, agent statuses, and the deprecated-command redirects.
- [`docs/installing-single-agents.md`](installing-single-agents.md) — MCP vs bundle export trade-offs.
- [`docs/consumer-responsibilities.md`](consumer-responsibilities.md) — what every consuming AI must do (persist + envelope + no silent dimension drops).
- [`docs/architecture.md`](architecture.md) — the retrieval mechanisms, and which of them actually ships.
