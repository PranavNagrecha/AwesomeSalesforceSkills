# CLAUDE.md — Salesforce Skills Repository

Read this file completely before taking action in this repository.

## What This Repo Is

This is a Salesforce skill framework, not a traditional application.

The repo contains:
- human-authored skill packages under `skills/`
- generated machine-readable registry artifacts under `registry/`
- generated local retrieval artifacts under `vector_index/`
- repo-native authoring, sync, and validation tooling under `scripts/` and `pipelines/`

The goal is to keep new skill creation deterministic, searchable, and self-maintaining.

## Canonical Rules

- `SKILL.md` frontmatter is the canonical metadata source for each skill.
- Official Salesforce docs are the primary authority for behavior, APIs, limits, metadata semantics, and security requirements.
- Salesforce Architects content is the primary authority for architecture patterns and Well-Architected framing.
- Local knowledge sharpens guidance. It does not override official behavior claims unless the skill explicitly documents a nuance.
- Do not hand-edit generated files in `registry/`, `vector_index/`, or `docs/SKILLS.md`.

The repo-wide canonical workflow rules are in `AGENT_RULES.md`. Follow them exactly.

## Required Workflow For Skill Creation Or Skill Updates

Before creating or materially revising a skill:

1. Search local coverage first:
   - `python3 scripts/search_knowledge.py "<topic>"`
2. Run the semantic-duplicate audit so you don't ship the 927th near-clone:
   - `python3 scripts/audit_duplicates.py --domain <domain>`
   - Review the top of `docs/reports/duplicate-candidates.md`.
3. Read the relevant official Salesforce docs from `standards/official-salesforce-sources.md`.
4. Scaffold with `python3 scripts/new_skill.py <domain> <name> --strict` — `--strict` blocks scaffolding when the proposed name produces a near-duplicate.

After any skill add or skill update:

1. Run:
   - `python3 scripts/skill_sync.py --skill skills/<domain>/<skill-name>`
   - or `python3 scripts/skill_sync.py --all`
2. Run:
   - `python3 scripts/validate_repo.py`
3. Commit:
   - the skill changes
   - generated files in `registry/`
   - generated files in `vector_index/`
   - generated `docs/SKILLS.md`
   - generated `standards/validation-gates.md` (if validator source changed)
   - generated `docs/queue-progress.md` (if `BACKLOG.yaml` changed)

The full list of validator gates with file:line citations lives in
`standards/validation-gates.md` — read it instead of grepping validator code.

## Repository Structure

```text
/
├── AGENT_RULES.md
├── AGENTS.md
├── config/
├── knowledge/
├── registry/
├── vector_index/
├── pipelines/
├── scripts/
├── docs/
├── skills/
├── templates/
├── agents/
├── commands/
└── standards/
```

### Key Areas

- `skills/`: canonical human-authored skill packages
- `templates/`: shared, cross-skill canonical building blocks (Apex base classes, test factory, LWC skeleton, Flow fault paths, Agentforce action scaffold) — see `templates/README.md`
- `knowledge/`: repo-native local corpus and curated imports
- `registry/`: generated normalized skill records
- `vector_index/`: generated retrieval chunks, lexical index, optional embeddings
- `scripts/`: top-level CLI entrypoints used by agents and contributors
- `docs/reports/duplicate-candidates.md`: generated report of near-duplicate skills — regenerate with `python3 scripts/audit_duplicates.py`
- `standards/validation-gates.md`: generated index of every gate the validators enforce — read this when you want to know what `validate_repo.py` will check
- `BACKLOG.yaml`: machine-readable queue of pending / researched / blocked / duplicate skill entries (the row data formerly inside `MASTER_QUEUE.md`)
- `docs/queue-progress.md`: generated dashboard for `BACKLOG.yaml` — status counts, drift, next-pick

## Bootstrap

Install repo-level tooling dependencies if they are not already available:

```bash
python3 -m pip install -r requirements.txt
```

## Skill Package Standard

Every skill package stays in the existing shape:

```text
skills/<domain>/<skill-name>/
├── SKILL.md
├── references/
│   ├── examples.md
│   ├── gotchas.md
│   ├── well-architected.md
│   └── llm-anti-patterns.md
├── templates/
└── scripts/
```

- `SKILL.md` must include a `## Recommended Workflow` section with 3–7 numbered steps.
- `references/llm-anti-patterns.md` must list 5+ mistakes AI assistants commonly make in this domain.

Do not add machine-generated metadata files inside a skill folder.

Generated machine artifacts live outside the skill package.

## Required Skill Frontmatter

Every `SKILL.md` must include:

```yaml
---
name: skill-name
description: "When to use this skill. Trigger keywords. What it does NOT cover."
category: admin | apex | lwc | flow | omnistudio | agentforce | security | integration | data | devops | architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
tags:
  - tag-one
inputs:
  - input the skill needs
outputs:
  - artifact or guidance the skill produces
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: YYYY-MM-DD
---
```

## Retrieval Rules

- Lexical retrieval is mandatory and must work with no API keys.
- Embeddings are optional and controlled through `config/retrieval-config.yaml`.
- Use `python3 scripts/search_knowledge.py` before claiming a topic is uncovered.
- Retrieval artifacts are generated; do not edit them manually.

## Repo-Level Scripts

### Required

```bash
python3 scripts/skill_sync.py --all
python3 scripts/validate_repo.py
python3 scripts/search_knowledge.py "query"
```

### Optional / supporting

```bash
python3 scripts/build_registry.py
python3 scripts/build_knowledge.py
python3 scripts/build_index.py
python3 scripts/generate_docs.py
python3 scripts/import_knowledge.py --source /path/to/local/markdown
python3 scripts/install_hooks.py
```

## Agent Expectations

### `/new-skill` and skill-builder

Must:
- search local knowledge first
- check official docs
- scaffold a compliant skill package
- run `skill_sync.py`
- run `validate_repo.py`
- report generated artifact updates

### `/review`, `/assess-org`, and `/release-notes`

Must:
- use registry-driven skill discovery
- use `search_knowledge.py` to find relevant local guidance
- prefer skill-local validators where they exist
- avoid referencing nonexistent repo-level analysis scripts

### Run-time agents (56)

These are user-facing agents that USE the library to do real Salesforce work — they do not build the library. The full roster is documented in [`agents/_shared/RUNTIME_VS_BUILD.md`](./agents/_shared/RUNTIME_VS_BUILD.md) and source-mapped in [`agents/_shared/SKILL_MAP.md`](./agents/_shared/SKILL_MAP.md).

The roster:
- **Developer + architecture (17)** — `/refactor-apex`, `/consolidate-triggers`, `/gen-tests`, `/optimize-soql`, `/scan-security`, `/analyze-flow`, `/plan-bulk-migration`, `/build-lwc`, `/audit-lwc`, `/debug-lwc`, `/score-deployment`, `/build-agentforce-action`, `/detect-drift`, `/build-apex`, `/build-changeset`, `/design-flow-orchestrator`, `/automation-migration-router`.
- **Admin accelerators — Tier 1 (15)** — `/analyze-field-impact`, `/design-object`, `/architect-perms`, `/build-flow`, `/audit-validation-rules`, `/preflight-load`, `/design-duplicate-rule`, `/design-assignment-rules`, `/configure-business-hours`, `/author-config-workbook`, `/design-custom-metadata`, `/design-entitlements`, `/design-experience-cloud`, `/design-path`, `/map-process-flow`.
- **Strategic — Tier 2 (12)** — `/audit-sharing`, `/audit-record-page`, `/audit-record-types`, `/govern-picklists`, `/review-data-model`, `/catalog-integrations`, `/audit-reports`, `/map-csv-to-object`, `/modernize-email-templates`, `/audit-router`, `/run-fit-gap`, `/draft-stories`.
- **Vertical + governance — Tier 3 (12)** — `/design-omni-channel`, `/design-knowledge-taxonomy`, `/design-sales-stages`, `/design-lead-routing`, `/audit-case-escalation`, `/design-sandbox-strategy`, `/plan-release-train`, `/assess-waf`, `/review-agentforce-action`, `/govern-prompt-library`, `/migrate-profile-to-permset`, `/diff-users`.

Must:
- follow `agents/_shared/AGENT_CONTRACT.md` — the 8-section AGENT.md shape, including the mandatory **Process Observations** block that flags healthy / concerning / ambiguous patterns seen while executing
- read every skill / template / decision tree cited in Mandatory Reads before producing output
- cite every skill id, template path, and decision-tree branch consulted in a Citations block
- NEVER deploy to an org, NEVER mutate files outside the user-supplied paths
- return a confidence score (HIGH/MEDIUM/LOW) and list ambiguities
- recommend (but never auto-chain to) other run-time agents

Must not:
- freestyle Apex/LWC/Flow/admin patterns when a template or decision tree exists
- recommend a technology without citing the matching decision-tree branch
- print secrets in output (always `[REDACTED]`)
- process more than one target per invocation
- invent a skill path — every citation must resolve to a real `skills/<domain>/<slug>/SKILL.md` (see `SKILL_MAP.md`)

## Python Tooling Rules

- Skill-local checker scripts in `skills/*/*/scripts/` remain stdlib-only unless explicitly documented otherwise.
- Repo-level framework scripts may use small documented dependencies from `requirements.txt`.
- Deterministic local tooling is preferred over hidden state or hosted services.

## Quality Gate

A skill or framework change is not complete unless:

- required frontmatter is present
- required package files exist
- `Official Sources Used` is present
- generated artifacts are current
- `python3 scripts/validate_repo.py` passes

## Decision Trees Layer

Cross-skill routing logic lives under `standards/decision-trees/`:

- `automation-selection.md` — Flow vs Apex vs Agentforce vs Approvals vs Platform Events
- `async-selection.md` — `@future` vs Queueable vs Batch vs Schedulable vs Platform Events
- `integration-pattern-selection.md` — REST vs Bulk API vs PE vs CDC vs Pub/Sub vs Salesforce Connect vs MuleSoft
- `sharing-selection.md` — OWD vs Role Hierarchy vs Sharing Rules vs Teams vs Manual vs Apex Managed vs Restriction

Rule: when a user query straddles more than one technology in a tree's
scope, read the tree before activating any skill. Cite the tree step that
resolved the choice. See `standards/decision-trees/README.md`.

## Golden Evals Layer

Output-quality checks for flagship skills live under `evals/golden/`.
Format is markdown-based (see `evals/framework.md`) and each flagship
skill has 3+ P0 cases with assertions, rubric, and reference answers.

Current coverage: 10 flagship skills × 3 cases = 30 P0 cases. Lint with
`python3 evals/scripts/run_evals.py --structure`.

Rule: when editing a flagship skill (see list in `evals/README.md`),
update its eval file in the same PR — reference answers should cite the
templates and decision trees the skill points to.

## Shared Templates Layer

Canonical, cross-skill building blocks live under `templates/`:

```text
templates/
├── apex/       TriggerHandler, TriggerControl, BaseDomain/Service/Selector,
│               ApplicationLogger, SecurityUtils, HttpClient, cmdt/, custom_objects/
├── apex/tests/ TestDataFactory, TestRecordBuilder, MockHttpResponseGenerator,
│               TestUserFactory, BulkTestPattern
├── lwc/        jest.config.js, component-skeleton/, patterns/
├── flow/       RecordTriggered_Skeleton, FaultPath_Template, Subflow_Pattern
└── agentforce/ AgentSkeleton.json, AgentActionSkeleton.cls, AgentTopic_Template.md
```

Rule for authors and agents:

- Before writing example code inside a skill, check `templates/<domain>/` for
  a canonical version and reference it by relative path.
- Skill-local templates in `skills/.../templates/` are fine for skill-specific
  placeholders. If a skill-local template starts being referenced by a second
  skill, promote it to `templates/<domain>/`.
- Do NOT hand-edit `templates/` artifacts downstream — copy and rename in the
  consuming project.

## Anti-Patterns

- Do not create a new skill without searching the local corpus first.
- Do not hand-edit generated registry or retrieval files.
- Do not add per-skill YAML metadata that duplicates frontmatter.
- Do not introduce hosted retrieval as a requirement for local authoring.
- Do not leave stale docs or registry artifacts after changing skills.
- Do not make factual Salesforce claims without official-source grounding.
- Do not reinvent an idiom that already exists under `templates/` — link to the template instead.
