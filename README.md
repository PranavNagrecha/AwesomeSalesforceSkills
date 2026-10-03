# SfSkills: Salesforce skills for AI coding assistants

Grounded Salesforce skill packages, run-time agents, a requirement-to-build loop and an MCP server for Claude Code, Cursor, Codex and any MCP client.

[![validate](https://github.com/PranavNagrecha/AwesomeSalesforceSkills/actions/workflows/validate.yml/badge.svg)](https://github.com/PranavNagrecha/AwesomeSalesforceSkills/actions/workflows/validate.yml)
[![pr-lint](https://github.com/PranavNagrecha/AwesomeSalesforceSkills/actions/workflows/pr-lint.yml/badge.svg)](https://github.com/PranavNagrecha/AwesomeSalesforceSkills/actions/workflows/pr-lint.yml)
[![tests](https://github.com/PranavNagrecha/AwesomeSalesforceSkills/actions/workflows/tests.yml/badge.svg)](https://github.com/PranavNagrecha/AwesomeSalesforceSkills/actions/workflows/tests.yml)
[![PyPI: sfskills-mcp](https://img.shields.io/pypi/v/sfskills-mcp?label=sfskills-mcp)](https://pypi.org/project/sfskills-mcp/)
[![License: PolyForm Small Business 1.0.0](https://img.shields.io/badge/license-PolyForm_Small_Business_1.0.0-orange.svg)](./LICENSE)

SfSkills makes an AI coding assistant work on Salesforce the way a senior practitioner does. It is a
library of 1,040 skill packages covering Apex, LWC, Flow, Agentforce, OmniStudio, integration, data,
security, DevOps and declarative admin work; 70 run-time agents you call as slash commands in Claude
Code; a beta loop that turns one business requirement into a verified, deploy-ready build; and an MCP
server that gives any MCP client the same library plus read-only probes of your org. Nothing in this
repository deploys to an org.

## Contents

- [What this is](#what-this-is)
- [Sixty-second start](#sixty-second-start)
- [What a session looks like](#what-a-session-looks-like)
- [What's in it](#whats-in-it)
- [Why you can trust the output](#why-you-can-trust-the-output)
- [Limits](#limits)
- [Docs](#docs)
- [Contributing](#contributing)
- [License](#license)

## What this is

**1. A skill library.** Each package under `skills/<domain>/<name>/` is a `SKILL.md` (when to use it,
a recommended workflow, and in packages written or revised since 2026-09-04 the questions to ask
before configuring) plus four reference files and a checker script:

- `references/examples.md`: worked examples, with metadata XML where the topic has it
- `references/gotchas.md`: the platform's non-obvious failure modes
- `references/llm-anti-patterns.md`: the wrong code an LLM reliably writes in this area, why it
  writes it, and the correct pattern
  ([example](skills/apex/mixed-dml-and-setup-objects/references/llm-anti-patterns.md))
- `references/well-architected.md`: the Well-Architected mapping and the official Salesforce sources
  the package rests on
- `scripts/`: a standard-library Python checker for the package's known failure modes

An assistant that has read the package refuses the specific wrong pattern and can say which document
each claim comes from. In Claude Code only the 12 router skills, the slash commands and the agent
loaders load at session start, about 7,000 tokens, and the model opens the one package it needs; a
flat list of every skill description would cost about 149,000 (both estimated by
`python3 scripts/build_plugin.py --measure`).

**2. Run-time agents.** 70 playbooks under `agents/<name>/AGENT.md`, each behind a slash command:
`/refactor-apex`, `/build-lwc`, `/build-flow`, `/score-deployment`, `/why-cant-user` and 65 more. An
agent reads every skill on its Mandatory Reads list before writing anything, cites each skill,
template and decision-tree branch it used, returns a HIGH/MEDIUM/LOW confidence score and a Process
Observations block about your org, and never deploys or edits files outside the paths you give it
([`agents/_shared/AGENT_CONTRACT.md`](agents/_shared/AGENT_CONTRACT.md)).

**3. The requirement-to-build loop (beta).** One business ask goes through eight Tier-4 agents with a
human gate between stages. The clarifier asks every question the cited skills say must be asked, each
with a proposed default. The planner writes milestones and steps, and the verifier tries to refute
the plan. Then, step by step, a builder writes the metadata or code, a tester runs every cited
skill's checker, and a doc keeper updates the plan views and the decision log; a milestone verifier
writes the acceptance report the human signs against. Ceremony scales with the ask (`ask`, `feature`
or `project`; [`standards/build-orchestration.md`](standards/build-orchestration.md) § 3.1). A build lives in
`.sfskills/builds/<id>/` with `plan.json` as its only state and `scripts/build_plan.py` as its only
writer. The loop never deploys and never approves a gate.

Five end-to-end scenarios are committed under [`examples/builds/`](examples/builds/README.md). The
builds were exported from real runs, false starts and rebuilds included:

| Scenario | Tier | Questions | Steps | Gate records | Org dry runs |
|---|---|---|---|---|---|
| [`case-onboarding`](examples/builds/case-onboarding/) | project | 97 | 22 | 13 | 32 |
| [`tier2-webhook`](examples/builds/tier2-webhook/) | feature | 45 | 5 | 4 | 13 |
| [`northwind-sales`](examples/builds/northwind-sales/) | project | 65 | 16 | 9 | 16 |
| [`opp-amount-lock`](examples/builds/opp-amount-lock/) | ask | 13 | 1 | 3 | 0 |
| [`cold-start-case-escalation-email`](examples/builds/cold-start-case-escalation-email/) | feature | 19 | 1 | 3 | 0 |

Scenario 5 ran twice: in [`cold-start-lead-source`](examples/builds/cold-start-lead-source/) a fresh
session given one client sentence used the library correctly but never found the loop; after a
one-paragraph fix to `CLAUDE.md`, the second cold start found it and drove the build to `done`. All
builds are design-only, and every gate was signed by someone standing in for the requester.

**4. An MCP server.** [`sfskills-mcp`](mcp/sfskills-mcp/README.md) serves the library, the agents'
playbooks, the templates and the decision trees to any MCP client, plus read-only org probes through
your existing `sf` CLI login: describe an org or an object, list fields, flows, validation rules,
permission sets, Apex classes, triggers and LWC bundles, and run read-only Tooling API SOQL. The
validate-only deploy the loop uses is a repository script, `scripts/mock_deploy.py`, which always runs
`sf project deploy start --dry-run`.

## Sixty-second start

Pick one path. [`docs/getting-started.md`](docs/getting-started.md) gives each a verification step;
[`docs/installing.md`](docs/installing.md) has every flag, the bootstrap internals and the embeddings
option.

**Claude Code plugin** (plugin 1.3.0). Installs the 12 router skills and 92 slash commands. It does
not install the agent loaders or wire the MCP server
([`docs/installing-the-plugin.md`](docs/installing-the-plugin.md)).

```text
/plugin marketplace add PranavNagrecha/AwesomeSalesforceSkills
/plugin install sfskills@sfskills
```

**Clone.** Open the folder in Claude Code and ask a Salesforce question. The routers, their rosters
and the 70 agent loaders are committed, so that works with no build step. Bootstrap adds local keyword
search and installs the slash commands; restart Claude Code afterwards.

```bash
git clone https://github.com/PranavNagrecha/AwesomeSalesforceSkills.git
cd AwesomeSalesforceSkills
python3 -m pip install -r requirements.txt    # inside a venv if your Python is externally managed
python3 scripts/bootstrap.py
python3 scripts/search_knowledge.py "trigger recursion"   # top skill: apex/recursive-trigger-prevention
```

For Cursor, `python3 scripts/export_skills.py --target cursor` writes `exports/cursor/.cursor/` to
copy into your project; `--help` lists the Windsurf, Aider, Augment, Codex and cross-tool `agents`
targets.

**MCP server** (any MCP client). The org tools borrow the `sf` CLI's session; the server stores no
credentials.

```bash
pip install sfskills-mcp
sfskills-mcp-init                          # one-time download of the skill data to ~/.cache/sfskills-mcp/
claude mcp add sfskills -- sfskills-mcp    # other clients: mcp/sfskills-mcp/docs/CONNECT.md
sf org login web --alias my-dev            # optional; only the org tools need it
```

This repository is at sfskills-mcp 0.5.0 (`mcp/sfskills-mcp/pyproject.toml`); `python3 -m pip show
sfskills-mcp` tells you which release PyPI installed. Client recipes for Claude Desktop, Cursor,
Windsurf, Zed, VS Code, Cline, Continue, Codex CLI, Gemini CLI and Goose are in
[`mcp/sfskills-mcp/docs/CONNECT.md`](mcp/sfskills-mcp/docs/CONNECT.md).

## What a session looks like

The smallest worked example, [`examples/builds/opp-amount-lock`](examples/builds/opp-amount-lock/),
abbreviated and reconstructed from the build's own records (`reports/drivers-log.md`, `RUN.md`,
`plan.json`). The ask is one line from Sales Ops.

```text
you        /clarify-requirements "Add a validation rule so an Opportunity's Amount can't go
           down after the Opportunity is Closed Won."

clarifier  scale: ask (D=1 metadata type, S=1 skill with question table, O=1 object,
           integration=no; no override)
           13 questions from admin/validation-rules and admin/requirements-gathering-for-sf:
           7 blocking, written to CLARIFICATIONS.md; 6 pre-filled from their defaults

you        Q3 (who may still lower a Closed Won Amount?): Only the Sales Ops team (two people),
           via a custom permission checked by the rule, not a profile exemption.
           ...six more answers...
           python3 scripts/build_plan.py ingest-answers plan.json

planner    1 milestone, 1 step (M1-S01, metadata-builder), 4 acceptance tests
verifier   one round, three lenses pass, 10 warnings, 0 blockers -> verified

you        python3 scripts/build_plan.py gate plan.json go approve --by "Sales Ops" \
             --notes "Accepted knowingly: the step grants a bypass permission set to
                      Sales Ops only (W1); historical violations stay in place (W6)"

builder    objects/Opportunity/validationRules/Amount_Locked_After_Closed_Won.validationRule-meta.xml
             AND(
               NOT($Permission.Bypass_Opp_Amount_Lock),
               NOT(ISNEW()),
               NOT(ISBLANK(TEXT(StageName))),
               ISPICKVAL(StageName, "Closed Won"),
               Amount < PRIORVALUE(Amount)
             )
           + Bypass_Opp_Amount_Lock custom permission, Opp_Amount_Lock_Bypass permission set,
             package.xml (API 67.0), deploy-order.md

tester     check_validation_rules.py exit 0 · check_custom_permissions.py exit 0 · xml pass ·
           manifest pass
milestone  ready-with-findings, F-01..F-11

you        python3 scripts/build_plan.py gate plan.json accept approve --by "Sales Ops" \
             --notes "F-02: assigning the permission set is a post-deploy Setup action"

next       printed, never run:
           python3 scripts/mock_deploy.py plan.json --org-alias <alias> --milestone M1
```

One thing went wrong, and it shows what the loop is for. The plan's first blank guard,
`NOT(ISBLANK(StageName))`, was copied from the skill's own GOOD example and did not compile in the
operator's validate-only probe ("Field StageName is a picklist field"). `NOT(ISBLANK(TEXT(StageName)))`
did. The step was amended and rebuilt, and `admin/validation-rules` now carries checker rule
`VR-PICK-01`. The human made two gate decisions, read four distinct files, and spent about 20 minutes
of a run that took about 170 (`reports/drivers-log.md`).

## What's in it

**1,040 skills · 98 agents (70 run-time, 14 build-time, 14 deprecated redirect stubs) · 92 slash
commands · 50 MCP tools · 7 decision trees.**

### Skills by domain

| Domain | Packages and scope |
|---|---|
| Admin | 261 — objects, fields, record types, page layouts, permission sets, reports, the record-access model (OWD, role hierarchy, sharing rules), and the requirements work before them |
| Apex | 159 — triggers, governor limits, async processing, outbound HTTP callouts, security enforcement, test patterns |
| Architect | 106 — multi-org strategy, scalability limits, licensing, Well-Architected reviews, architecture decision records |
| Data | 101 — data model, migrations, bulk loads, query optimisation, deduplication at volume, archival, SOSL |
| LWC | 83 — reactivity, wire adapters, component communication, accessibility, performance, security, Jest |
| DevOps | 70 — source tracking, packaging, branching, CI/CD pipelines, environment strategy, deployment troubleshooting |
| Flow | 63 — record-triggered, screen, scheduled and orchestration flows, bulkification, fault handling, testing |
| Integration | 61 — REST and SOAP APIs, Bulk API 2.0, Platform Events, CDC, Pub/Sub, Named Credentials, middleware |
| Agentforce | 53 — agents, topics, actions, prompt templates, grounding, guardrails, evaluation |
| Security | 49 — org hardening, encryption, session policy, MFA, monitoring, incident response, record-access troubleshooting |
| OmniStudio | 34 — OmniScripts, FlexCards, DataRaptors, Integration Procedures, DataPack deployment |

**Skills** (`skills/`) — 1,040 structured guides; the full catalog is [`docs/SKILLS.md`](docs/SKILLS.md).
`templates/` holds the shared Apex, LWC, Flow and Agentforce building blocks the skills point at
(TriggerHandler, TestDataFactory, HttpClient, the LWC skeleton, the Flow fault path), and
`standards/decision-trees/` holds the routing trees an agent reads before choosing a technology:
automation, flow pattern, Agentforce capability, async, integration pattern, sharing, performance.

### Agents by tier

**Run-time (70)** agents do Salesforce work in your codebase or org. **Build-time (14)** agents
maintain the library. Fourteen more are deprecated stubs whose commands redirect to `/audit-router`.

| Tier | Example commands |
|---|---|
| Developer + architecture (28) | `/refactor-apex`, `/consolidate-triggers`, `/gen-tests`, `/optimize-soql`, `/scan-security`, `/build-lwc`, `/score-deployment`, `/why-cant-user` |
| Admin accelerators — Tier 1 (14) | `/design-object`, `/architect-perms`, `/build-flow`, `/preflight-load`, `/design-duplicate-rule`, `/design-path` |
| Strategic — Tier 2 (9) | `/review-data-model`, `/run-fit-gap`, `/draft-stories`, `/audit-router`, `/decide-salesforce`, `/learn-salesforce` |
| Vertical + governance — Tier 3 (11) | `/design-omni-channel`, `/design-sales-stages`, `/design-lead-routing`, `/plan-release-train`, `/assess-waf`, `/design-omnistudio` |
| Orchestration — Tier 4 (8, beta) | `/clarify-requirements`, `/plan-build`, `/verify-plan`, `/run-build-step`, `/test-build-step`, `/keep-build-docs`, `/verify-milestone`, `/build-metadata` |

`/build-from-requirements` walks the whole loop and `/run-build` walks one milestone. Every agent with
its command and output: [`docs/agents.md`](docs/agents.md).

### MCP tools

**sfskills-mcp** (`mcp/sfskills-mcp/`) — 50 tools across skill, agent, template and decision-tree
retrieval plus org probes. 23 run offline against the library and local files, 26 read from an org
through the `sf` CLI, and one, `emit_envelope`, writes an agent's report under `docs/reports/`. None
of them writes to your org. The list is long — the fifteen named here cover the usual paths:
`search_skill` (lexical search over the 1,040-skill SfSkills corpus), `get_skill`, `suggest_agent`,
`get_agent`, `describe_org`, `describe_object_full`, `list_custom_fields`, `list_flows_on_object`,
`list_validation_rules`, `list_permission_sets`, `list_apex_classes`, `list_apex_triggers`,
`tooling_query`, `validate_against_org` and `probe_automation_graph`. Credential-shaped strings in CLI output are
scrubbed to `[REDACTED]` (`mcp/sfskills-mcp/tests/test_sf_cli_redaction.py`).

### In this release

- [x] 1,040 skills across 11 domains, each with `SKILL.md`, four reference files and a checker script
- [x] 70 run-time agents, eight of them the beta requirement-to-build loop
- [x] Five end-to-end build scenarios under `examples/builds/`
- [x] Golden evals for 10 flagship skills (3 P0 cases each)
- [x] Claude Code plugin 1.3.0 and sfskills-mcp 0.5.0

## Why you can trust the output

- **Grounding.** Every package's `references/well-architected.md` has an `## Official Sources Used`
  section, and `pipelines/validators.py` fails the build when one is missing. Sources are ranked in
  four tiers by [`standards/source-hierarchy.md`](standards/source-hierarchy.md): official Salesforce
  documentation first, and a lower tier never overrides a higher one on platform behaviour. The
  official pages per domain are in
  [`standards/official-salesforce-sources.md`](standards/official-salesforce-sources.md). A claim
  that could not be checked against a fetched page carries an inline `UNVERIFIED (YYYY-MM-DD)` marker
  instead of passing as fact.
- **Checkers.** Every package ships a standard-library Python script under `scripts/`, usually
  `check_<name>.py`, that inspects a project's metadata or source for that package's failure modes.
  `scripts/validate_repo.py` compiles each one and runs its `--help`. The build loop runs the cited
  checkers verbatim against every step and records each exit code in `tests/<step>/results.json`.
- **Validators.** `python3 scripts/validate_repo.py` checks frontmatter, package shape, citations,
  agent contracts and the counts in this README (`scripts/check_doc_counts.py`); every gate is listed
  in [`standards/validation-gates.md`](standards/validation-gates.md). On every push and pull request
  to `main`, `validate.yml` runs it in four shards together with `build_plugin.py --check`,
  `export_skills.py --check` and `run_evals.py --structure`, and `tests.yml` runs the unit suites plus
  a CLI/MCP retrieval parity check over 154 held-out queries.
- **Golden evals.** `evals/golden/` holds 3 P0 cases (assertions, rubric, reference answer) for each
  of 10 flagship skills: apex 4, integration 3, lwc 2, flow 1. Lint them with
  `python3 evals/scripts/run_evals.py --structure`.
- **Org dry runs.** `scripts/mock_deploy.py` assembles a build's artefacts and runs
  `sf project deploy start --dry-run` against an org you name; it has no deploy option. The three
  larger worked examples made 61 validate-only runs (32, 13 and 16). Most platform refusals they hit
  are now checker rules, gotchas or `mock_deploy.py` fixes;
  [the org as teacher](examples/builds/README.md#the-org-as-teacher) lists each one, including the
  two not fixed yet.

## Limits

- **Lexical search has no stemming.** The FTS5 index uses the default tokenizer and prefix-matches
  query terms (`pipelines/lexical_index.py`): "trigger" finds "triggers", but "deleting" does not
  find "delete", so natural-language phrasing can miss. In Claude Code, which package opens is a
  model decision over router descriptions and rosters, and it can pick a neighbour. Name the domain
  ("this is a sharing question") or run `scripts/search_knowledge.py`.
- **Grounded, not fully verified.** Where an official page could not be fetched while authoring, the
  claim carries an `UNVERIFIED (YYYY-MM-DD)` marker; `grep -rl "UNVERIFIED" skills/` lists every
  file that has one. Check those claims before relying on them.
- **The build loop is beta.** All eight Tier-4 agents are `status: beta`. Every worked example is
  design-only, and its gates were signed by someone standing in for the requester.
- **Org access is read-only; mock deploy is always `--dry-run`.** Validate-only compiles and checks
  the build and runs the Apex tests you ask for. It cannot show runtime behaviour, run Jest or load
  data; [what the loop could not see](examples/builds/README.md#what-the-loop-could-not-see) lists
  each blind spot.
- **Golden evals are thin.** 10 of 1,040 packages have them, in 4 of 11 domains, and CI lints their
  structure without grading answers against the rubric.
- **PyPI can trail the repository.** The badge above shows the published release.

## Docs

- [`docs/README.md`](docs/README.md): the documentation index, ordered the way a reader needs it
- [`docs/getting-started.md`](docs/getting-started.md): the three entry points, each with a check
- [`docs/build-loop.md`](docs/build-loop.md): the requirement-to-build loop told through the five scenarios
- [`docs/installing.md`](docs/installing.md): bootstrap, every flag, embeddings, MCP install paths
- [`docs/installing-the-plugin.md`](docs/installing-the-plugin.md): the Claude Code plugin
- [`docs/SKILLS.md`](docs/SKILLS.md): the generated skill catalog
- [`docs/agents.md`](docs/agents.md): the generated agent roster
- [`examples/builds/README.md`](examples/builds/README.md): the five scenarios and how to run one
- [`standards/build-orchestration.md`](standards/build-orchestration.md): the build loop contract
- [`docs/architecture.md`](docs/architecture.md): how routing, search and the MCP server fit together
- [`docs/troubleshooting.md`](docs/troubleshooting.md): known failure modes and fixes
- [`mcp/sfskills-mcp/README.md`](mcp/sfskills-mcp/README.md): MCP tools, prompts and resources
- [`standards/decision-trees/README.md`](standards/decision-trees/README.md) and
  [`templates/README.md`](templates/README.md): routing trees and shared building blocks

A browsable catalog site is generated by `scripts/build_site.py` and published by the Pages workflow
(`.github/workflows/pages.yml`) when GitHub Pages is enabled for the repository.

## Contributing

[`CONTRIBUTING.md`](CONTRIBUTING.md) covers adding a skill, fixing one and reporting a gap. The short
version:

```bash
python3 scripts/search_knowledge.py "<topic>"                          # search before you write
python3 scripts/new_skill.py <domain> <name> --strict --agent <agent_id>
python3 scripts/skill_sync.py --skill skills/<domain>/<name>
python3 scripts/validate_repo.py
```

Please follow the [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md). To cite SfSkills, use
[`CITATION.cff`](CITATION.cff). Bugs and gaps go to
[Issues](https://github.com/PranavNagrecha/AwesomeSalesforceSkills/issues).

## License

SfSkills is source-available under the [PolyForm Small Business License 1.0.0](./LICENSE)
(`PolyForm-Small-Business-1.0.0`). It is not open source. Use is free when your organisation has
fewer than 100 people and under USD 1M in prior-year revenue, which covers individual developers,
freelancers and independent consultants, including on billable client work. Everyone else needs a
commercial license; [`LICENSING.md`](LICENSING.md) explains the thresholds and how to buy one.
