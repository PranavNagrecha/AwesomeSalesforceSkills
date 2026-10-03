# SfSkills documentation

**Who this is for:** everyone, as a map. Find your section, then follow one link.

This page is an index only. It links and classifies, it does not teach. The
sections run in the order a reader usually needs them: get it working,
understand what it is, see the build loop in action, look things up, install
it properly, run it day to day, and finally change it.

| Label | Means |
|---|---|
| `Consumer` | You are USING the library on a Salesforce project: searching skills, running agents, wiring the MCP server into your editor. You never edit this repo. |
| `Contributor` | You are CHANGING the library: adding or revising a skill, an agent, a template or the tooling. You run the sync and validation gates. |
| `Both` | Useful either way. |

---

## 1. Getting started

| Doc | Audience | What it answers |
|---|---|---|
| [../README.md](../README.md) | Both | What is this and why would I want it? |
| [getting-started.md](getting-started.md) | Consumer | Install to first useful answer, for the three real entry points: Claude Code checkout, MCP server, plain export to another tool. |
| [worked-example-trigger-consolidation.md](worked-example-trigger-consolidation.md) | Consumer | One complete Salesforce task, start to finish, with the real command output. |

## 2. Concepts

| Doc | Audience | What it answers |
|---|---|---|
| [architecture.md](architecture.md) | Both | How skills, agents, commands, templates, decision trees, registry, index, evals and the MCP server fit together, and which of the three retrieval mechanisms each accuracy figure describes. |
| [agent-invocation-modes.md](agent-invocation-modes.md) | Consumer | The ways to invoke an agent, and why MCP is the canonical channel for production use. |
| [glossary.md](glossary.md) | Both | This repo's own vocabulary: mechanism 1/2/3, gloss, roster, tier, coverage gate, envelope. |
| [../evals/measurement/README-model-routing.md](../evals/measurement/README-model-routing.md) | Both | How the shipped routing path is benchmarked, and the retraction of the "79.2% → 92.2% Hit@1" headline. Read before citing any routing number. |

## 3. The build loop

Asked to make a Salesforce change (a field, a flow, a rule, an integration, a
whole process) rather than answer a question? This is the path. The
"Two Ways In" section at the top of [../CLAUDE.md](../CLAUDE.md) says the same
to an AI session.

| Doc | Audience | What it answers |
|---|---|---|
| [build-loop.md](build-loop.md) | Consumer | **Start here.** The requirement-to-build loop told through the five worked examples, smallest first, with every number sourced. |
| [../examples/builds/README.md](../examples/builds/README.md) | Both | The five scenarios side by side, how each column was counted, every org refusal and where it lives now, and what validate-only could not see. |
| [../standards/build-orchestration.md](../standards/build-orchestration.md) | Both | The contract: stages, gates, the plan file, the sizing rule (§ 3.1), steps, acceptance tests, roles. The authority when anything else disagrees. |
| [../commands/build-from-requirements.md](../commands/build-from-requirements.md) | Consumer | The exact command sequence, gate by gate. |

The worked examples, each a folder with its own `README.md`:

| Example | Size, from its README | Read it for |
|---|---|---|
| [opp-amount-lock](../examples/builds/opp-amount-lock/README.md) | `ask` tier: one-line ask, 13 questions, 1 step, two gate decisions | The loop at its smallest; one rendered `RUN.md` read at both gates |
| [tier2-webhook](../examples/builds/tier2-webhook/README.md) | `feature` tier: integration, 45 questions, 5 steps, 13 validate-only runs | Why compile-only Apex evidence is not enough |
| [case-onboarding](../examples/builds/case-onboarding/README.md) | project: 97 clarifications, 5 milestones, 22 steps, 13 gates | The largest build; the org as the last reviewer |
| [northwind-sales](../examples/builds/northwind-sales/README.md) | project: 16 steps, 4 milestones, 9 gates, 16 runs reached the org, 14 org-taught facts | The broadest build: config, access, approvals, Apex, LWC, reporting |
| [cold-start-lead-source](../examples/builds/cold-start-lead-source/README.md) | no tier: the loop was never found | What a session that skipped the loop missed |
| [cold-start-case-escalation-email](../examples/builds/cold-start-case-escalation-email/README.md) | `feature` tier: 19 questions, 1 step | The same experiment after the fix: found, sized and driven to `done` |

## 4. Library reference

| Doc | Audience | What it answers |
|---|---|---|
| [SKILLS.md](SKILLS.md) | Both | The full skill catalog, by domain. Generated. |
| [agents.md](agents.md) | Both | Every agent package with its status and role. Generated. |
| [../agents/_shared/RUNTIME_VS_BUILD.md](../agents/_shared/RUNTIME_VS_BUILD.md) | Consumer | Which agents do Salesforce work and which maintain the library. |
| [../agents/_shared/SKILL_MAP.md](../agents/_shared/SKILL_MAP.md) | Consumer | Which agent cites which skills. |
| [../standards/decision-trees/README.md](../standards/decision-trees/README.md) | Consumer | Routing before technology choice, across seven trees: Flow vs Apex, flow pattern, Agentforce capability, async tier, integration pattern, sharing mechanism, performance tuning. |
| [../templates/README.md](../templates/README.md) | Consumer | The canonical Apex, LWC, Flow and Agentforce building blocks that skills point at. |

## 5. Installing

| Doc | Audience | What it answers |
|---|---|---|
| [installing.md](installing.md) | Both | The canonical setup reference for a clone: one bootstrap command, every flag, what a clone does and does not contain, embeddings cost, MCP install paths, and the maintainer runbook for cutting a release. |
| [installing-the-plugin.md](installing-the-plugin.md) | Consumer | Install the library as a Claude Code plugin from the marketplace, and what the plugin costs at session start. |
| [installing-single-agents.md](installing-single-agents.md) | Consumer | Ship one agent into another project without dropping its skill and probe dependencies. |
| [../mcp/sfskills-mcp/docs/CONNECT.md](../mcp/sfskills-mcp/docs/CONNECT.md) | Consumer | MCP client config for Claude Code, Claude Desktop, Cursor, Windsurf, Zed, VS Code, Cline, Continue, Codex CLI, Gemini CLI, Goose. |
| [../mcp/sfskills-mcp/README.md](../mcp/sfskills-mcp/README.md) | Consumer | The MCP tool schemas, annotations and design notes. |

## 6. Operating

| Doc | Audience | What it answers |
|---|---|---|
| [consumer-responsibilities.md](consumer-responsibilities.md) | Consumer | What a consuming tool MUST do when it runs a run-time agent: persist reports, honour the JSON envelope. |
| [multi-ai-parity.md](multi-ai-parity.md) | Consumer | Which export targets are first-class and what each one loses. |
| [troubleshooting.md](troubleshooting.md) | Both | Symptom to cause to fix, for the failure modes a fresh clone actually hits. |
| [faq.md](faq.md) | Both | Do I need an org? Why is search slow? Why do the CLI and MCP disagree? |
| [MIGRATION.md](MIGRATION.md) | Both | Which agents were retired in the Wave 3 consolidation, what replaced them, and the state of each redirect. |
| [validation/README.md](validation/README.md) | Both | How the library verifies itself against a live org: three re-runnable harnesses. The harnesses ship; their reports do not. |
| [../SECURITY.md](../SECURITY.md) | Both | Threat model, secret handling, and how to report a vulnerability. |
| [../CHANGELOG.md](../CHANGELOG.md) | Both | What changed, when. |

## 7. Contributing

| Doc | Audience | What it answers |
|---|---|---|
| [../CONTRIBUTING.md](../CONTRIBUTING.md) | Contributor | Add a skill, fix a skill, report a gap, flag stale content. |
| [../AGENT_RULES.md](../AGENT_RULES.md) | Contributor | The full repo-wide workflow rules. |
| [../CLAUDE.md](../CLAUDE.md) | Contributor | The rules an AI assistant follows inside this repo. |
| [../AGENTS.md](../AGENTS.md) | Contributor | The agent-facing entry point (the `AGENTS.md` convention). |
| [../standards/skill-authoring-style.md](../standards/skill-authoring-style.md) | Contributor | How a skill package is written: voice, section shapes, Questions to Ask Before Configuring. |
| [../standards/validation-gates.md](../standards/validation-gates.md) | Contributor | Every gate `validate_repo.py` enforces, with file and line citations. Generated. |
| [../standards/official-salesforce-sources.md](../standards/official-salesforce-sources.md) | Contributor | The official Salesforce documentation a skill's claims must be grounded in. |
| [../agents/_shared/AGENT_CONTRACT.md](../agents/_shared/AGENT_CONTRACT.md) | Contributor | The 8-section shape every AGENT.md must have. |
| [../evals/README.md](../evals/README.md) | Contributor | Golden P0 output-quality cases for the flagship skills. |
| [../commands/onboard-source.md](../commands/onboard-source.md) and [source-integrations/README.md](source-integrations/README.md) | Contributor | Onboarding an external skill source, and the licence and chain-of-title record each one leaves. |

### Generated artifacts: never hand-edit

Regenerate with the command in the third column. Only some of these are gated.

| Doc | What it is | Regenerate with | Drift gated? |
|---|---|---|---|
| [SKILLS.md](SKILLS.md) | The skill catalog | `scripts/skill_sync.py --all` (via `scripts/generate_docs.py`) | Yes. `validate_repo.py` recomputes it through `pipelines/sync_engine.py` and errors on any difference. |
| [agents.md](agents.md) | The agent roster | `scripts/generate_agent_roster.py` | Only by hand: `--check` exists, and no workflow or hook runs it. |
| [queue-progress.md](queue-progress.md) | Backlog dashboard: status counts, drift, next pick | `scripts/generate_queue_dashboard.py` | Yes, when `BACKLOG.yaml` produces a dashboard. |
| `docs/reports/duplicate-candidates.md` | Near-duplicate skill pairs | `scripts/audit_duplicates.py` | No. `docs/reports/` is gitignored, so it exists only after you run the script. |

Outside `docs/`, `registry/`, `vector_index/chunks.jsonl`,
`vector_index/manifest.json` and `standards/validation-gates.md` are written by
the sync engine and drift-gated by `validate_repo.py`. The plugin artifacts
under `.claude/` (routers, rosters, agent loaders) are generated by
`scripts/build_plugin.py` and checked in CI by `scripts/build_plugin.py --check`
(`.github/workflows/validate.yml`).

The queue itself is hand-authored: [../BACKLOG.yaml](../BACKLOG.yaml) holds the
rows, and [../MASTER_QUEUE.md](../MASTER_QUEUE.md) is the workflow contract for
claiming one. `queue-progress.md` is derived from the first.

---

## What this library is not

- Not a deployment tool. Nothing here pushes metadata to an org, and the build
  loop stops at a validate-only command a human runs.
- Not an org scanner on its own. Reading an org needs the MCP server plus your
  own authenticated Salesforce CLI session.
- Not org-dependent for skills. Search, agents, templates and decision trees
  work with no Salesforce org at all.

## Not indexed

- `docs/product-v2/` and `docs/source-integrations/2026-09-01-public-skill-source-audit.md`
  are historical: dated records of earlier work sessions, kept for provenance,
  not maintained as documentation.
- `docs/reports/` and everything under `docs/validation/` except its README are
  gitignored run output: per-agent reports, validation runs, dated one-off
  analyses. They describe the tree as it was when they ran.
