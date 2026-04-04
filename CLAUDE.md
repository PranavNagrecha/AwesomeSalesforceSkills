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
2. Read the relevant official Salesforce docs from `standards/official-salesforce-sources.md`.
3. Confirm the skill does not already exist or overlap too heavily.

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
├── agents/
├── commands/
└── standards/
```

### Key Areas

- `skills/`: canonical human-authored skill packages
- `knowledge/`: repo-native local corpus and curated imports
- `registry/`: generated normalized skill records
- `vector_index/`: generated retrieval chunks, lexical index, optional embeddings
- `scripts/`: top-level CLI entrypoints used by agents and contributors

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

## Anti-Patterns

- Do not create a new skill without searching the local corpus first.
- Do not hand-edit generated registry or retrieval files.
- Do not add per-skill YAML metadata that duplicates frontmatter.
- Do not introduce hosted retrieval as a requirement for local authoring.
- Do not leave stale docs or registry artifacts after changing skills.
- Do not make factual Salesforce claims without official-source grounding.
