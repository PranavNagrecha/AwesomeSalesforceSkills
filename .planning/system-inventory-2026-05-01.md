# SfSkills System Inventory — 2026-05-01

A read-only audit of every validator, gate, generator, and workflow rule that
exists in the repo today. Goal: see the entire surface on one page so we can
decide what to keep, merge, or retire — *without* actually changing anything yet.

Counts at the time of this audit:

- **926** skills (`find skills -name SKILL.md`)
- **75** agent directories under `agents/` + 8 shared docs in `agents/_shared/`
- **68** slash commands under `commands/`
- **35** Python entrypoints in `scripts/` (10 are migration / one-shots)
- **3** GitHub Actions workflows
- **2** local git hooks
- **1** master queue file (`MASTER_QUEUE.md`, 1852 lines, 836 status rows)

---

## 1. Pain points the user named — what's actually true

| User feeling | What's actually true |
|---|---|
| "Too many skills built" | 926 skills exist. `MASTER_QUEUE.md` shows **670 DONE / 33 DUPLICATE / 41 RESEARCHED / 92 TODO** out of 836 tracked rows. There is also a separate "Total: 1097 planned, 687 done, 394 TODO" summary table at the top — these two numbers don't match each other or the actual skill count, which means the queue and the filesystem have drifted. |
| "Too many skills pending" | 92 explicit TODO + 41 RESEARCHED rows (~133 in flight). But the summary table claims 394 TODO. Either way the queue is the bottleneck — the build pipeline is fast, but the queue is much larger than any single session can drain. |
| "There is no duplicate check somehow" | **There is one — and it only catches exact-name collisions.** `validate_repo.py` lines 282–300 fail on duplicate `category/name` (skill_id) and duplicate `name`. There is also a *coverage warning* in `new_skill.py` (`_check_coverage`, line 102) that calls `search_knowledge.py` and prints "⚠ WARNING: Local knowledge already has coverage" — but it's a warning, not a gate, and it relies on lexical search which can miss synonyms / near-duplicates / overlapping scope. **There is no semantic / fuzzy / scope-overlap detector.** This is the real gap. |
| "Too many validations build over time, I have no idea" | 12+ distinct gates exist (catalogued in §3 below). The biggest source of opacity isn't the number of gates — it's that they live in 4 different places (`validators.py`, `agent_validators.py`, `validate_repo.py`, the `.githooks/` and `.github/workflows/` glue) and are not summarized in any single doc except `AGENT_RULES.md` (which describes the workflow, not the gates). |

---

## 2. Skill creation surface — what runs when an agent makes a new skill

Reading `AGENT_RULES.md` § "Required Workflow" + `MASTER_QUEUE.md` agent
instructions, the documented flow is:

1. `scripts/search_knowledge.py "<topic>" --domain <d>` — coverage check (advisory)
2. `scripts/new_skill.py <domain> <name>` — scaffold all files, pre-seed official sources
   - At line 487 it auto-runs the coverage check and prints a WARNING if `has_coverage: true`. **Does not block scaffolding.**
3. Author fills every TODO in the scaffold
4. `scripts/skill_sync.py --skill skills/<d>/<name>` — sync engine: validates, then writes to `registry/` and `vector_index/`
5. Add a query fixture to `vector_index/query-fixtures.json`
6. `scripts/validate_repo.py` — must exit 0
7. (Step 6 in AGENT_RULES) Decide which agents should cite the skill, run `patch_agent_skill.py`
8. Commit skill + `registry/` + `vector_index/` + `docs/SKILLS.md`

**Observation:** the only *enforced* duplicate gate at this stage is the
exact-name check inside `validate_repo.py` step 6. The coverage warning at
step 2 is honor-system. An agent that ignores the warning has no gate
preventing creation of a near-duplicate skill.

---

## 3. Validation surface — every gate, where it runs, what it catches

### 3a. Pre-commit hook (`.githooks/pre-commit`)

```sh
python3 scripts/skill_sync.py --changed-only
python3 scripts/validate_repo.py --changed-only
```

Runs on every commit. Targets only files in the current diff. Always runs the
generated-artifact drift check.

### 3b. Pre-push hook (`.githooks/pre-push`)

Runs `validate_repo.py --skills-only --shard 0..3/4 --skip-fixture-retrieval`
across all 4 shards. Same set of checks as CI's main job, locally, before push.
Bypassable with `--no-verify`.

### 3c. CI: `.github/workflows/validate.yml` (main gate)

Four jobs:

- **validate-skills** (4-shard matrix) — runs `validate_repo.py --skills-only --shard N/4 --skip-fixture-retrieval` per shard. ~40s wall-clock for 926 skills.
- **validate-agents** (ubuntu + macos matrix) — `validate_repo.py --agents` + frontmatter round-trip + probe/MCP tool tests.
- **export-parity-matrix** (ubuntu + macos) — `export_skills.py --check` to detect cross-OS hash drift in exports.
- **bench-orchestration** — `validate_repo_bench.py` with 500 synthetic skills, 30s threshold. Conditional on PR labels / title.

### 3d. CI: `.github/workflows/pr-lint.yml` (lightweight first-impression)

- Frontmatter schema round-trip (`tests.test_agent_frontmatter`)
- Export manifest parity (`export_skills.py --check` + `tests.test_export_parity`)

### 3e. CI: `.github/workflows/org-validation.yml` (manual / weekly cron)

NOT on every PR. Three optional layers, gated on `SFDX_AUTH_URL` secret:

- Probe SOQL correctness against a real org (`validate_probes_against_org.py`)
- Agent smoke tests (`smoke_test_agents.py`)
- Skill factuality sampling (`validate_skill_factuality.py --sample 200`)

### 3f. The actual checks inside `validate_repo.py` + `pipelines/validators.py`

This is the heart of the system. **Twelve distinct gates**, all wired into one
orchestrator:

| # | Gate | File:line | Level | What it catches |
|---|---|---|---|---|
| 1 | Required frontmatter keys | `pipelines/validators.py:139` | ERROR | Missing `name`, `description`, `category`, `salesforce-version`, `well-architected-pillars`, `tags`, `triggers`, `inputs`, `outputs`, `dependencies`, `version`, `author`, `updated`. |
| 2 | Category enum | `pipelines/validators.py:143` | ERROR | `category` not in the 11 allowed values. |
| 3 | Category ↔ folder | `pipelines/validators.py:155` | ERROR | `category` doesn't match parent domain folder. |
| 4 | Name ↔ folder | `pipelines/validators.py:151` | ERROR | `name` doesn't match the skill's folder name. |
| 5 | Description must say "NOT" | `pipelines/validators.py:163` | ERROR | Description missing scope exclusion ("NOT for ..."). |
| 6 | No unfilled TODOs | `pipelines/validators.py:167` + `:182` | ERROR | TODO markers in frontmatter or body. |
| 7 | Body word count ≥ 300 | `pipelines/validators.py:178` | ERROR | Stub bodies. |
| 8 | JSON-schema check on frontmatter | `pipelines/validators.py:187` | ERROR | Type / format / pattern violations. Has friendly enum-suggestion ("did you mean 'Performance'?"). |
| 9 | Required files exist | `pipelines/validators.py:244` | ERROR | `SKILL.md`, `references/{examples,gotchas,well-architected,llm-anti-patterns}.md`, non-empty `templates/`, non-empty `scripts/`. |
| 10 | Checker script not a stub | `pipelines/validators.py:193` | WARN | Scripts < 10 meaningful lines, no conditionals, no error path. |
| 11 | "Recommended Workflow" section present | `pipelines/validators.py:276` | WARN | Missing `## Recommended Workflow` heading in `SKILL.md`. |
| 12 | "Official Sources Used" section non-empty | `pipelines/validators.py:282` | ERROR | Heading missing or empty in `references/well-architected.md`. |
| 13 | Style: no `## When To Use` body | `pipelines/validators.py:332` | ERROR | Per `skill-authoring-style.md` § 6.1 — frontmatter description IS the trigger surface. |
| 14 | Style: no inline pillar mapping | `pipelines/validators.py:357` | ERROR | § 6.4 — pillar mapping belongs in `references/well-architected.md`. |
| 15 | Style: no verbatim paragraph dup | `pipelines/validators.py:391` | ERROR | § 6.6 — same paragraph in SKILL.md *and* `gotchas.md`. |
| 16 | Style: parallel-prose bullets | `pipelines/validators.py:443` | WARN | § 6.2 — runs of 4+ `- **X** — text` bullets should be tables. |
| 17 | **Duplicate skill_id** | `scripts/validate_repo.py:283` | **ERROR** | Two skills with same `category/name`. Exact match only. |
| 18 | **Duplicate skill name** | `scripts/validate_repo.py:292` | **ERROR** | Two skills with same `name`. Exact match only. |
| 19 | Knowledge sources schema | `validate_repo.py:303` | ERROR | `knowledge/sources.yaml` entries against schema. |
| 20 | Registry record schema | `validate_repo.py:309` | ERROR | Generated `registry/skills.json` records against schema. |
| 21 | Skill-local script `--help` | `validate_repo.py:319` | ERROR | Each `skills/*/*/scripts/*.py` must compile + respond to `--help`. |
| 22 | Query fixture coverage | `validate_repo.py:331` | ERROR | Every skill must have at least one entry in `query-fixtures.json`. |
| 23 | Query fixture retrieval | `validate_repo.py:346` | ERROR | The fixture's expected skill must appear in top-K of search. *Skipped in CI shard runs* (`--skip-fixture-retrieval`). |
| 24 | Generated-artifact drift | `validate_repo.py:362` | ERROR | `registry/`, `vector_index/`, `docs/SKILLS.md` are stale w.r.t. source skills. |
| 25 | Orphan skills | `validate_repo.py:375` | WARN | Skills not cited by any agent's `dependencies.skills:`. Soft — opt-out via `runtime_orphan: true`. |

Plus a separate set in `pipelines/agent_validators.py` (674 lines, not
catalogued here line-by-line) — the AGENT.md equivalent: 8-section structure,
citation gate (every cited skill / template / decision-tree must resolve to a
real file), MCP tool gate, slash-command gate, frontmatter schema.

**The takeaway for "too many validations":** the *count* is reasonable
(~25 skill checks + ~10 agent checks), but they're spread across 4 files and
there is no single place that lists them with rationale. That's what makes
the system feel opaque — not the number of checks, but the lack of an index.

---

## 4. Duplicate detection — what exists, what's missing

### What exists

1. **Exact `name` collision** — `validate_repo.py:283-300`. Hard ERROR.
2. **Exact `category/name` collision** — same place.
3. **Coverage warning at scaffold time** — `new_skill.py:487`. Calls `search_knowledge.py` (lexical). Soft WARN, does not block.
4. **Lexical retrieval ranking** — `query-fixtures.json` enforces that a known query returns the right skill in top-K. Indirectly catches a class of "two skills compete for the same query" bugs, but only for queries with fixtures.
5. **`scripts/skill_graph.py`** — exists, lets a human navigate related skills by tag/trigger overlap. Discovery tool, not a gate.
6. **`scripts/search_skills.py`** — context-aware search with synonym expansion, role / cloud boosting. Discovery tool, not a gate.

### What's missing (and would be high leverage)

- **Description-level near-duplicate detection.** Two skills with `description: ...`s that are 80%+ similar should be flagged at sync time. `difflib.SequenceMatcher` over normalized descriptions is one possible implementation.
- **Trigger-overlap detection.** Two skills declaring overlapping `triggers:` (the natural-language symptom phrases) compete for the same retrieval. Today nothing flags that.
- **Tag-overlap heuristic.** Two skills with ≥ N shared tags AND in the same category AND with similar descriptions should be inspected.
- **A "is this a duplicate of?" affordance in `new_skill.py`.** Today it warns but creates anyway. A blocking flag (e.g. `--allow-overlap`) would force the author to acknowledge.
- **Periodic full-corpus dedup report.** A script that ranks every pair of skills by similarity and surfaces the top 50 candidates for human review — run weekly, not per-commit.

---

## 5. Pending skills (`MASTER_QUEUE.md`)

- File is **1852 lines**, **684 KB**. Read-only authoring discipline at this size is nearly impossible; the file is past the threshold where any agent will read it cover-to-cover before picking work.
- Rows by status: **670 DONE / 92 TODO / 41 RESEARCHED / 33 DUPLICATE**. Total tracked: 836.
- Summary table at the top claims 1097 planned / 687 done / 394 TODO — different numbers than the rows below it, indicating drift between the manual summary and the row data.
- Filesystem has 926 skills; queue tracks 670 DONE + 33 DUPLICATE + 41 RESEARCHED + 92 TODO = 836. **~90 skills exist on disk that aren't in the queue at all** (or the queue counts and disk counts use different definitions of "skill"). Worth verifying before trusting either number.

**Implication:** the queue is a workflow document that has slowly become a
dashboard, and is now neither. Splitting it into (a) one machine-readable
backlog file and (b) a generated progress dashboard would dissolve a lot of
the "too many pending" confusion.

---

## 6. Agents

### Inventory

- **75** agent directories under `agents/` (per `ls`).
- AGENT_RULES.md says: 14 build-time + 56 run-time = 70. The CLAUDE.md says "56 run-time agents" matching the 56 number. The discrepancy between 70 and 75 is small but real — likely 5 agents added since the doc was last updated, or 5 directories that aren't agents (e.g. demos, archives).
- Each agent dir typically has: `AGENT.md`, `GATES.md`, `REQUIREMENTS_TEMPLATE.md`, `inputs.schema.json`. Some have more.
- `agents/_shared/` holds the contract: `AGENT_CONTRACT.md`, `RUNTIME_VS_BUILD.md`, `SKILL_MAP.md`, `CAPABILITY_MATRIX.md`, `DELIVERABLE_CONTRACT.md`, `REFUSAL_CODES.md`, `AGENT_DISAMBIGUATION.md`, `SKILL_BUILDER_CORE.md` + `harnesses/`, `lib/`, `probes/`, `schemas/`.

### Agent gates (in `pipelines/agent_validators.py`)

- 8-section structural gate (run-time) / 5-section gate (build-time)
- Section aliasing (e.g. "Activation Triggers" counts as "Invocation")
- Citation gate — every skill/template/decision-tree cited must resolve to a real file
- MCP tool gate — agent's referenced MCP tools must exist in the server
- Slash-command gate — agent's slash command must exist in `commands/`
- Frontmatter JSON-schema validation

### Same problem as skills

- No semantic-overlap check between agents.
- 68 slash commands ↔ ~56 run-time agents — close but not 1:1. Worth verifying that mismatch is intentional.
- `SKILL_MAP.md` is hand-maintained — there is no "every agent's `dependencies.skills:` matches `SKILL_MAP.md`" gate.

---

## 7. Likely-stale tooling (candidates for retirement)

These are scripts whose names indicate one-shot migrations that probably ran
once and are now dead weight. **Recommend reading each, confirming, then
moving to `scripts/_archive/`** rather than deleting outright.

| Script | Last touched | Likely status |
|---|---|---|
| `scripts/migrate_agent_dependencies.py` | 2026-04-17 | One-shot — agent dependency format migration. |
| `scripts/migrate_deliverable_contract.py` | 2026-04-17 | One-shot — deliverable contract refactor. |
| `scripts/migrate_multidim_dimensions.py` | 2026-04-17 | One-shot — frontmatter dimension cleanup. |
| `scripts/backfill_agent_frontmatter.py` | 2026-04-16 | One-shot — agent frontmatter backfill. |
| `scripts/backfill_inputs_schema_descriptions.py` | 2026-04-21 | One-shot — schema description backfill. |
| `scripts/baseline_agent_envelope.py` | 2026-04-27 | Possibly still used — re-baselines agent envelope. Verify before retiring. |
| `scripts/_migrations/detect_parallel_prose.py` | (already archived) | Already lives under `_migrations/`. ✓ |
| `scripts/_migrations/strip_style_guide_duplications.py` | (already archived) | Already lives under `_migrations/`. ✓ |
| `scripts/skill_forge.py` | 2026-04-23 | 533 lines, similar role to `new_skill.py` — verify there isn't redundant scaffolding here. |
| `scripts/run_builder.py` + `builder_plugins/` | 2026-04-17 | The "one big builder" path. Probably still used by build-time agents but worth confirming. |

`scripts/_migrations/` is the right pattern for stash-and-keep — already used
twice. Recommend extending it for the rest.

---

## 8. Recommended next steps (prioritized)

In order of leverage. Each is independent — you can do any one without doing
the others.

### A. (Highest leverage) Add semantic-duplicate detection

A new validator gate, runs at sync time. Two flavors:

1. **Per-skill check at scaffold** — `new_skill.py --strict` blocks creation if description / triggers overlap > threshold with any existing skill. Today's coverage warning becomes a hard gate behind a flag.
2. **Full-corpus pairwise report** — new `scripts/audit_duplicates.py` that runs in O(N²) over all 926 skills, ranks pairs by combined description+tag+trigger similarity, and writes top 50 to `docs/reports/duplicate-candidates.md`. Run on demand, not in CI.

This directly addresses the "no duplicate check" complaint and is small
(~150 lines, stdlib `difflib`).

### B. Single index of every gate

One markdown file under `standards/` (e.g. `standards/validation-gates.md`)
that lists every gate from §3f above, the file:line where it lives, the level
(ERROR/WARN), and one sentence on intent. Generated, not hand-maintained —
one script that walks the validator files and extracts the `ValidationIssue(...)`
calls + their preceding context. Rebuild on commit.

This kills "I have no idea what's validating" in one document.

### C. Split MASTER_QUEUE.md

- `BACKLOG.yaml` (or similar) — machine-readable, one row per pending skill, columns: `domain, name, status, owner, notes, researched_at, started_at`.
- `docs/queue-progress.md` — generated dashboard. Counts by status, drift between queue and disk, oldest TODO, etc.
- `MASTER_QUEUE.md` keeps the prose intro + agent instructions but loses the 1500 rows.

This dissolves the 684 KB cliff and removes the manual-summary-vs-row drift.

### D. Reconcile skill counts

Run a one-off:

```
filesystem skills - queue DONE rows = ?
queue DONE rows - filesystem skills = ?
```

If non-zero, fix the queue rows or the skills. Add a CI gate that this
remains zero going forward.

### E. Agent inventory reconciliation

Resolve the 70 vs 75 vs 56 vs 68 mismatch (build agents + run-time agents +
slash commands). Update `RUNTIME_VS_BUILD.md` to match reality. Add a
generated count summary to that file so future drift is obvious.

### F. (Lowest leverage but easy) Retire stale migration scripts

Move the scripts in §7 to `scripts/_migrations/` (or delete). Removes ~10
files from `scripts/` root, makes the active surface easier to navigate.

---

## Appendix — script inventory by purpose

Active / regularly-used:

- `validate_repo.py`, `validate_repo_bench.py` — validation
- `skill_sync.py` + `pipelines/sync_engine.py` — sync engine
- `build_registry.py`, `build_index.py`, `build_knowledge.py`, `generate_docs.py` — generators (called by sync)
- `search_knowledge.py`, `search_skills.py`, `skill_graph.py` — discovery
- `new_skill.py`, `new_agent.py` — scaffolding
- `patch_agent_skill.py` — wires a skill into an agent
- `export_skills.py`, `export_agent_bundle.py` — IDE / consumer exports
- `install_hooks.py` — installs `.githooks/`
- `queue_reader.py` — parses `MASTER_QUEUE.md`
- `ship_skills.py` — release / ship flow
- `skill_forge.py` — *unclear, verify*
- `run_builder.py` + `builder_plugins/` — multi-skill build orchestrator
- `validate_probes_against_org.py`, `smoke_test_agents.py`, `validate_skill_factuality.py` — live-org gates
- `execute_agent_fixture.py`, `generate_agent_inputs_schemas.py`, `test_checkers.py` — agent + checker tooling

One-shot / migration / backfill (candidates for retirement, see §7):

- `migrate_agent_dependencies.py`, `migrate_deliverable_contract.py`, `migrate_multidim_dimensions.py`
- `backfill_agent_frontmatter.py`, `backfill_inputs_schema_descriptions.py`
- `baseline_agent_envelope.py` (verify first)
- `scripts/_migrations/*` (already archived ✓)
