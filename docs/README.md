# SfSkills documentation

Every markdown document this repository ships as documentation, ordered by the
journey a reader actually takes. This page is an index only — it links and
classifies, it does not teach. Tutorials live in
[getting-started.md](getting-started.md); explanation lives in
[architecture.md](architecture.md).

## Audience legend

| Label | Means |
|---|---|
| `Consumer` | You are USING the library on a Salesforce project — searching skills, running agents, wiring the MCP server into your editor. You never edit this repo. |
| `Contributor` | You are CHANGING the library — adding or revising a skill, an agent, a template, or the tooling. You run the sync and validation gates. |
| `Both` | Useful either way. |

That split is the single most confusing thing about this repo's docs. Of the 36
rows below, 13 are consumer-facing, 12 are maintainer contracts and 11 serve
both — so a third of this index is written for people who maintain the library,
and reading those as a user is a waste of an afternoon.

---

## 1. Start here

| Doc | Audience | What it answers |
|---|---|---|
| [../README.md](../README.md) | Both | What is this and why would I want it? |
| [getting-started.md](getting-started.md) | Consumer | Install to first useful output, for the three real entry points. |
| [installing.md](installing.md) | Both | The canonical setup reference: one bootstrap command, every flag, what a clone does and does not contain, embeddings cost, MCP install paths, and the maintainer runbook for cutting a release. |
| [worked-example-trigger-consolidation.md](worked-example-trigger-consolidation.md) | Consumer | One complete Salesforce task, start to finish, with the real command output. |
| [glossary.md](glossary.md) | Both | What is a "skill", a "chunk", a "coverage gate", a "probe"? |
| [faq.md](faq.md) | Both | Do I need an org? Why is search slow? Why do the CLI and MCP disagree? |
| [troubleshooting.md](troubleshooting.md) | Both | Symptom to cause to fix, for the failure modes a fresh clone actually hits. |

## 2. Use the library

| Doc | Audience | What it answers |
|---|---|---|
| [../mcp/sfskills-mcp/docs/CONNECT.md](../mcp/sfskills-mcp/docs/CONNECT.md) | Consumer | MCP client config for Claude Code, Claude Desktop, Cursor, Windsurf, Zed, VS Code, Cline, Continue, Codex CLI, Gemini CLI, Goose. |
| [../mcp/sfskills-mcp/README.md](../mcp/sfskills-mcp/README.md) | Consumer | The 38 MCP tool schemas, annotations, and design notes. |
| [installing-the-plugin.md](installing-the-plugin.md) | Consumer | Install the library as a Claude Code plugin from the marketplace. |
| [installing-single-agents.md](installing-single-agents.md) | Consumer | Ship one agent into another project without dropping its skill and probe dependencies. |
| [agent-invocation-modes.md](agent-invocation-modes.md) | Consumer | The canonical short list of ways to invoke an agent. Start with this one. |
| [consumer-responsibilities.md](consumer-responsibilities.md) | Consumer | What a consuming tool MUST do when it runs a runtime agent (persist reports, honour the JSON envelope). |
| [multi-ai-parity.md](multi-ai-parity.md) | Consumer | Which export targets are first-class and what each one loses. |
| [../agents/_shared/RUNTIME_VS_BUILD.md](../agents/_shared/RUNTIME_VS_BUILD.md) | Consumer | The agent roster: which agents do Salesforce work vs maintain the library. |
| [../agents/_shared/SKILL_MAP.md](../agents/_shared/SKILL_MAP.md) | Consumer | Which agent cites which skills. |
| [../standards/decision-trees/README.md](../standards/decision-trees/README.md) | Consumer | Routing before technology choice, across seven trees: Flow vs Apex, flow pattern, Agentforce capability, async tier, integration pattern, sharing mechanism, performance tuning. |
| [../templates/README.md](../templates/README.md) | Consumer | The canonical Apex / LWC / Flow / Agentforce building blocks skills point at — 73 files. |

## 3. Understand it

| Doc | Audience | What it answers |
|---|---|---|
| [architecture.md](architecture.md) | Both | How skills, agents, commands, templates, decision trees, registry, index, evals and the MCP server fit together — and which of the three retrieval mechanisms each accuracy figure describes. |
| [validation/README.md](validation/README.md) | Both | How the library verifies itself against a live org (three re-runnable harnesses). The committed reports are dated April 2026; the harnesses are current. |
| [../evals/measurement/README-model-routing.md](../evals/measurement/README-model-routing.md) | Both | How the shipped routing path is benchmarked, and the retraction of the "79.2% → 92.2% Hit@1" headline. Read before citing any routing number. |
| [../agents/_shared/AGENT_CONTRACT.md](../agents/_shared/AGENT_CONTRACT.md) | Both | The 8-section shape every AGENT.md must have. |
| [../evals/README.md](../evals/README.md) | Both | Golden P0 output-quality cases for the flagship skills. |
| [../SECURITY.md](../SECURITY.md) | Both | Threat model, secret handling, and how to report a vulnerability. |

## 4. Contribute to it

| Doc | Audience | What it answers |
|---|---|---|
| [../CONTRIBUTING.md](../CONTRIBUTING.md) | Contributor | Add a skill, fix a skill, report a gap, flag stale content. |
| [../CLAUDE.md](../CLAUDE.md) | Contributor | The rules an AI assistant must follow inside this repo. |
| [../AGENT_RULES.md](../AGENT_RULES.md) | Contributor | The full repo-wide workflow rules, in detail. |
| [../AGENTS.md](../AGENTS.md) | Contributor | The agent-facing entry point (the `AGENTS.md` convention). |
| [../standards/validation-gates.md](../standards/validation-gates.md) | Contributor | Every gate `validate_repo.py` enforces, with file and line citations. Generated. |
| [MIGRATION.md](MIGRATION.md) | Contributor | Which agents were deprecated in the Wave 3 consolidation and what replaced them. |
| [../CHANGELOG.md](../CHANGELOG.md) | Both | What changed, when. |

## 5. Reference

### 5a. Generated artifacts — never hand-edit

Regenerate instead, with the command named in the last column. Note the second
column of teeth: only some of these are actually gated.

| Doc | Audience | What it answers | Regenerate with | Drift gated? |
|---|---|---|---|---|
| [SKILLS.md](SKILLS.md) | Both | The full skill catalog. | `scripts/skill_sync.py --all` (via `scripts/generate_docs.py`) | Yes — `validate_repo.py` recomputes it (`pipelines/sync_engine.py`, `diff_state`) and errors on any difference. |
| [queue-progress.md](queue-progress.md) | Contributor | Backlog dashboard: status counts, drift, next pick. | `scripts/generate_queue_dashboard.py` | Yes, when `BACKLOG.yaml` produces a dashboard. |
| [reports/duplicate-candidates.md](reports/duplicate-candidates.md) | Contributor | Near-duplicate skill pairs above the similarity threshold. | `scripts/audit_duplicates.py` | **No.** It is absent from `diff_state` and from every workflow, so a stale copy passes CI. |

The same distinction applies outside `docs/`. `registry/`,
`vector_index/chunks.jsonl`, `vector_index/manifest.json` and
`standards/validation-gates.md` are drift-gated by `validate_repo.py`. The 121
plugin artifacts under `.claude/` (the 12 routers, 11 rosters and 48 agent
loaders) are generated by `scripts/build_plugin.py` and checked by
`scripts/build_plugin.py --check`, which no workflow or hook invokes — run it
yourself before committing a router change.

### 5b. Hand-authored queue sources

These are edited by hand. `queue-progress.md` above is derived from the first
of them.

| Doc | Audience | What it answers |
|---|---|---|
| [../BACKLOG.yaml](../BACKLOG.yaml) | Contributor | The machine-readable queue of pending / researched / blocked / duplicate skill entries. Edit this, then regenerate the dashboard. |
| [../MASTER_QUEUE.md](../MASTER_QUEUE.md) | Contributor | The queue workflow contract: how to claim an entry, the status key, and the `queue_reader.py` CLI. Row data lives in `BACKLOG.yaml`. |

---

## What this library is not

- Not a deployment tool. Nothing here pushes metadata to an org.
- Not an org scanner on its own. Org-reading requires the MCP server plus
  your own authenticated Salesforce CLI session.
- Not org-dependent for skills. Search, agents, templates and decision trees
  work with no Salesforce org at all.

## Files this index does not cover

`docs/reports/` holds working artifacts, not documentation, and only
`duplicate-candidates.md` above is indexed from it. The rest is two kinds of
output: per-agent directories written by runtime agents at execution time (the
`emit_envelope` convention, `docs/reports/<agent>/<run_id>.{json,md}`), and a
few dated one-off analyses — `checker-findings.md` (2026-05-05),
`parallel-prose-candidates.md`, `user-permission-comparison-jones-prior.md`.
All of them describe a tree that has since moved on.

`docs/SKILLS.md` is indexed in 5a but is not prose — it is the generated
catalog of all 1,027 packages.
