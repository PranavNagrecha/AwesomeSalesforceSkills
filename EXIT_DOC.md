# Codex Exit Doc

Date: 2026-03-13

This document is the handoff summary for Claude or any other agent reviewing what Codex changed in this repository.

## Scope Completed

Codex took over a partially built Salesforce skills repo and completed four major tracks:

1. Finished and normalized the Admin skill set.
2. Added official Salesforce source discipline to the skill-authoring workflow.
3. Built a repo-native skill framework with local retrieval, generated registry artifacts, and deterministic validation.
4. Updated the human and agent instruction surfaces so future skill creation must follow the same workflow.

## Current Repo State

- Built skills: 21
- Domain counts:
  - `admin`: 15
  - `apex`: 3
  - `flow`: 1
  - `lwc`: 1
  - `omnistudio`: 1
- Retrieval mode: local lexical baseline
- Embeddings: optional, currently disabled
- Repo-level dependencies: `PyYAML`, `jsonschema`
- Git status: this workspace is not a git repository, so no commit was created here

## What Codex Changed

### 1. Admin skills completed and normalized

`ADM-001` through `ADM-015` were finished and aligned to the repo standard.

Work included:
- preserving strong existing content where it was already good
- standardizing `SKILL.md` frontmatter and package structure
- adding missing `scripts/` checkers
- normalizing examples and references
- updating backlog status to done

### 2. Official Salesforce documentation made mandatory

Codex added a central official-source map and enforced it across the repo.

Key additions:
- `standards/official-salesforce-sources.md`
- `## Official Sources Used` requirement in `references/well-architected.md`

Existing skills were backfilled so the current built set follows the policy.

### 3. Repo-native framework implemented

Codex added the framework layers below:

- `config/`
  - JSON schemas for frontmatter, registry records, knowledge sources, retrieval chunks, and retrieval results
  - retrieval configuration
- `knowledge/`
  - `sources.yaml` as the canonical manifest
  - repo-native knowledge topics
  - import area for curated markdown
- `registry/`
  - generated master skill registry
  - generated per-skill normalized records
  - generated knowledge map
- `vector_index/`
  - generated retrieval chunks
  - SQLite lexical index
  - retrieval manifest
  - optional embeddings slot
- `pipelines/`
  - frontmatter parsing
  - validation
  - registry building
  - knowledge discovery
  - chunking
  - lexical indexing
  - optional embeddings
  - ranking
  - docs generation
  - sync orchestration
- `scripts/`
  - `validate_repo.py`
  - `skill_sync.py`
  - `build_registry.py`
  - `build_knowledge.py`
  - `build_index.py`
  - `search_knowledge.py`
  - `generate_docs.py`
  - `import_knowledge.py`
  - `install_hooks.py`

### 4. All current skills retrofitted to the metadata contract

Every existing skill `SKILL.md` was updated so frontmatter now includes:

- `tags`
- `inputs`
- `outputs`
- `dependencies`

`SKILL.md` frontmatter is now the canonical human-authored metadata source.

### 5. All instruction surfaces updated

The following now reflect the enforced workflow:

- `AGENT_RULES.md`
- `AGENTS.md`
- `README.md`
- `CLAUDE.md`
- `SKILL-AUTHORING-STANDARD.md`
- `CONTRIBUTING.md`
- `commands/new-skill.md`
- `agents/skill-builder/AGENT.md`
- `agents/skill-builder/SKILL.md`
- `agents/code-reviewer/AGENT.md`
- `agents/org-assessor/AGENT.md`
- `agents/release-planner/AGENT.md`

The intended workflow is now:

1. search local coverage first
2. check official Salesforce docs
3. create or revise the skill package
4. run `skill_sync.py`
5. run `validate_repo.py`
6. never hand-edit generated artifacts

### 6. Cursor testing assets added

Codex added:

- `CURSOR_TEST_SCRIPT.md`

This gives a concrete way to test whether Cursor follows the repo workflow before and after a new skill is created.

### 7. Retrieval output bug fixed

Codex fixed an issue where `scripts/search_knowledge.py` was returning weak official source titles like `Overview` even though the canonical titles existed in `knowledge/sources.yaml`.

The fix included:
- better fallback behavior in `pipelines/chunker.py`
- canonical official-source normalization in `scripts/search_knowledge.py`

## Generated Artifacts That Should Exist

These are expected and current:

- `registry/skills.json`
- `registry/skills/*.json`
- `registry/knowledge-map.json`
- `docs/SKILLS.md`
- `vector_index/chunks.jsonl`
- `vector_index/lexical.sqlite`
- `vector_index/manifest.json`

Current retrieval manifest snapshot:

- `skill_count`: 21
- `knowledge_source_count`: 15
- `chunk_count`: 980
- `embeddings_enabled`: false

## Verification Already Run By Codex

The following were executed successfully:

```bash
python3 scripts/skill_sync.py --all
python3 scripts/validate_repo.py
python3 -m py_compile pipelines/*.py scripts/*.py
python3 scripts/search_knowledge.py "permission sets least privilege" --domain admin --json
python3 scripts/search_knowledge.py "renderedCallback memory leak" --domain lwc --json
python3 scripts/search_knowledge.py "fault connector rollback" --domain flow --json
python3 scripts/search_knowledge.py "with user mode stripinaccessible" --domain apex --json
python3 scripts/search_knowledge.py "integration http callout retries" --domain integration --json
```

Expected high-level results:

- repo validation passes with 0 issues
- admin permission-set query returns `admin/permission-sets-vs-profiles`
- LWC lifecycle query returns `lwc/lifecycle-hooks`
- flow fault query returns `flow/fault-handling`
- Apex security query returns `apex/soql-security`
- integration retry query returns no dedicated skill but canonical official sources

## What Claude Should Verify

Claude should independently verify these claims:

1. The framework exists and is wired into the repo.
2. `SKILL.md` frontmatter is the canonical metadata source.
3. The generated artifacts are current.
4. The instruction files all point to the same workflow.
5. `search_knowledge.py` returns canonical official source names.
6. The current skills pass validation under the new standard.

## Suggested Claude Verification Procedure

```bash
python3 -m pip install -r requirements.txt
python3 scripts/search_knowledge.py "integration http callout retries" --domain integration --json
python3 scripts/skill_sync.py --all
python3 scripts/validate_repo.py
```

Then Claude should spot-check:

- `AGENT_RULES.md`
- `CLAUDE.md`
- `SKILL-AUTHORING-STANDARD.md`
- `registry/skills.json`
- `docs/SKILLS.md`
- `vector_index/manifest.json`
- one admin skill
- one apex skill
- one non-code-heavy skill

Recommended spot checks:

- `skills/admin/permission-sets-vs-profiles/`
- `skills/apex/soql-security/`
- `skills/flow/fault-handling/`
- `skills/omnistudio/integration-procedures/`

## Known Constraints

- This repo is local-first. There is no hosted retrieval backend.
- Embeddings are optional and currently disabled in `config/retrieval-config.yaml`.
- The lexical index is the required baseline and must keep working without API keys.
- Empty domain directories exist for future coverage but do not yet contain built skills:
  - `skills/agentforce/`
  - `skills/data/`
  - `skills/devops/`
  - `skills/integration/`
  - `skills/security/`
- Because there is no `.git` directory here, Codex could not produce a commit history for review.

## If Claude Finds Drift

If Claude finds any mismatch between standards, generated artifacts, and behavior, the expected repair loop is:

```bash
python3 scripts/skill_sync.py --all
python3 scripts/validate_repo.py
```

If the issue is in search output or retrieval metadata, inspect:

- `knowledge/sources.yaml`
- `pipelines/chunker.py`
- `pipelines/ranking.py`
- `scripts/search_knowledge.py`

If the issue is in skill creation workflow, inspect:

- `AGENT_RULES.md`
- `CLAUDE.md`
- `SKILL-AUTHORING-STANDARD.md`
- `commands/new-skill.md`
- `agents/skill-builder/AGENT.md`
- `agents/skill-builder/SKILL.md`

## Bottom Line

Codex left the repo in a state where:

- the current 21 skills validate
- future skill creation is supposed to be deterministic
- local retrieval works without hosting
- official Salesforce docs are part of the required workflow
- generated registry/docs/index artifacts are part of the normal authoring loop
