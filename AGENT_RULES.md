# Agent Rules

Canonical rulebook for any coding agent working in this repository, including
Claude, Codex, and GPT-based tooling.

## Core Rule

No new skill or skill update is complete until the repository metadata,
retrieval artifacts, and generated docs are synchronized — and
`validate_repo.py` exits 0.

Exit code is the contract. `validate_repo.py` exits non-zero on **ERROR** only.
WARNs print and do not fail the build; the corpus carries hundreds of them by
design (176 in shard 0 of 4 as of this writing). "Fix every warning" is not a
shippable instruction here — read the WARN, decide, and move on.

## Authoritative Sources

- `SKILL.md` frontmatter is the canonical metadata source for every skill.
- `standards/skill-content-contract.md` defines **what** a skill must say
  (factual claims, depth, source grounding).
- `standards/skill-authoring-style.md` defines **how** a skill should say it
  (voice, structural patterns, when to use code vs. tables vs. prose).
- `standards/official-salesforce-sources.md` is the canonical official-doc
  source map.
- `knowledge/sources.yaml` is the canonical retrieval source manifest.
- `standards/validation-gates.md` is the generated index of every gate the
  validators emit, with file:line links. Read it instead of grepping validator
  source. Do not hand-edit it.
- `registry/` is generated. So are `vector_index/chunks.jsonl`,
  `vector_index/lexical.sqlite`, and the `*embeddings.jsonl` files — all
  gitignored. `vector_index/query-fixtures.json`, `query-variants.json`, and
  `manifest.json` are the only tracked files in that directory; you edit
  `query-fixtures.json` by hand (step 5 below).

## Prerequisite — build the retrieval index once per clone

```bash
python3 scripts/bootstrap.py
```

The FTS5 index is gitignored. Without it, `search_index()` returns `[]` and
`search_knowledge.py` reports no coverage for every query while exiting 0. Step
1 below is worthless until this has run. Verify cheaply with
`python3 scripts/bootstrap.py --verify-only`.

## Required Workflow For Any New Skill

### Step 1 — Check coverage first (mandatory)

```bash
python3 scripts/search_knowledge.py "<topic>" --domain <domain>
```

If `has_coverage: true` is returned, a skill already exists. Extend it — do not
create a duplicate.

For a stronger check that compares against every skill's description, tags, and
triggers (not just lexical retrieval):

```bash
python3 scripts/audit_duplicates.py --domain <domain>
```

This writes `docs/reports/duplicate-candidates.md` with every pair above the
configured similarity threshold (`config/retrieval-config.yaml` →
`duplicate_threshold.score`, currently `0.50`, weighted description 0.5 / tags
0.25 / triggers 0.25). Add `--json` to inspect without rewriting the report.
Review before adding a skill that scores near an existing one.

### Step 2 — Scaffold (never write from scratch)

```bash
python3 scripts/new_skill.py <domain> <skill-name> --strict --agent <agent_id>
```

`--strict` exits non-zero if the proposed name scores at or above the
similarity threshold against any existing skill, so an agent cannot silently
create an overlapping package.

`--agent` records which run-time agent will cite the new skill; repeat it for
several. If no agent honestly owns the topic, use
`--runtime-orphan --orphan-reason "<why>"` instead. The two are mutually
exclusive, and in a non-TTY run you must pass one of them. Add `--assume-yes`
in pipelines: without it the coverage-warning prompt reads stdin and
EOF-crashes. `--assume-yes` does not bypass `--strict`.

The scaffold creates the full package with pre-filled TODO markers and
pre-seeded official sources. You fill the TODOs; you do not design the
structure.

> **Known defect (report, don't route around):** `scripts/new_skill.py` accepts
> `experience` and `servicecloud` as domains, but `ALLOWED_CATEGORIES` in
> `pipelines/validators.py` has only the 11 real domains. A skill scaffolded
> into either will fail validation with `invalid category`. The 11 valid
> domains are `admin`, `agentforce`, `apex`, `architect`, `data`, `devops`,
> `flow`, `integration`, `lwc`, `omnistudio`, `security`.

### Step 3 — Fill all TODOs

Every scaffolded file contains `TODO:` markers. Every one must be replaced
before sync succeeds:

- `SKILL.md` — description (must include "NOT for ..."), triggers (3+,
  natural-language symptom phrases, 10+ chars each), tags, inputs, outputs,
  well-architected-pillars, body (300+ words), `## Recommended Workflow`
  section (3–7 numbered steps an AI agent should follow when this skill
  activates)
- `references/examples.md` — real examples with context, problem, solution
- `references/gotchas.md` — non-obvious platform behaviors
- `references/well-architected.md` — WAF notes; official sources are
  pre-seeded, add usage context
- `references/llm-anti-patterns.md` — 5+ mistakes AI coding assistants commonly
  make in this skill's domain. Each entry: what the LLM generates wrong, why it
  happens, the correct pattern, and a detection hint
- `scripts/check_<noun>.py` — implement actual checks, stdlib only

### Step 4 — Sync (validates first, hard stop on errors)

```bash
python3 scripts/skill_sync.py --skill skills/<domain>/<skill-name>
```

Validation runs before any artifact is written. Sync will not produce artifacts
from a broken skill. Do not use `--skip-validation`.

For a repo-wide rebuild, use `--all --skip-embeddings`. `embeddings.enabled` is
`true` in `config/retrieval-config.yaml`, so a bare `--all` attempts a
chunk-level encode — the config records ~2:20 for a first-time build on an
M-series CPU, and `.githooks/pre-commit` records ~3 hours when the content-hash
cache is cold. Rebuild embeddings deliberately with
`python3 scripts/build_index.py`, not as a side effect of syncing.

### Step 5 — Add a query fixture and validate

Add an entry to `vector_index/query-fixtures.json` (tracked, hand-edited):

```json
{
  "query": "natural-language query a practitioner would type",
  "domain": "<domain>",
  "expected_skill": "<domain>/<skill-name>",
  "top_k": 3
}
```

Then:

```bash
python3 scripts/validate_repo.py
```

Two separate gates apply, both **ERROR**:
`skill '<id>' has no query fixture — add at least one entry`
(`validate_repo.py:363`), and `query '<q>' did not return '<skill>' in top <k>`
(`validate_repo.py:383`). The fixture must pass retrieval, not merely exist.

**Validator flags:**

| Flag | What it does | When to use |
|---|---|---|
| `--skills-only` | Skill validation only. The default when no class flag is set. | Normal skill work. |
| `--agents` | AGENT.md structural + citation gate only. Measured 0.4 s for all 76 agents. | After editing an `AGENT.md`. |
| `--all` | Both. | Pre-release sweep. |
| `--changed-only` | Only skills/agents in the current git diff (staged + unstaged + untracked); drift check still runs. | Pre-commit hook. Fastest path on small changes. |
| `--shard N/M` | The N-th bucket of skills partitioned by stable hash mod M (0-indexed). | CI matrix jobs (`.github/workflows/validate.yml`). |
| `--domain <name>` | Restrict to `skills/<name>/`. Composable with `--shard` and `--changed-only`. | Local work on one domain. |
| `--skip-drift` | Skip the generated-artifact freshness check. | Only when sync_engine is deliberately mid-rebuild. |
| `--skip-fixture-retrieval` | Skip the per-fixture retrieval-quality assertion; fixture *coverage* still runs. | When the lexical index is intentionally absent (synthetic benches, CI shard warm-up). |
| `--skip-similarity` | Skip the semantic-duplicate WARN gate. | The orchestration bench, where synthetic skills share tags by construction. |

Expect roughly 2 minutes per quarter-shard on the current corpus with
`--skip-fixture-retrieval`; a full unsharded run is longer, and the
per-fixture retrieval gate adds several minutes more.

**Benchmarking the validator:** `python3 scripts/validate_repo_bench.py
--count 500` spins up a throwaway temp repo with 500 synthetic skills and
asserts validation stays under a 30-second threshold (both tunable via
`--count` / `--threshold`). Run it before merging changes to
`scripts/validate_repo.py` or `pipelines/agent_validators.py`.

### Step 6 — Decide whether any agent should cite this skill

This is a **judgment** step, not a sweep. Walk the run-time roster and decide
which agents — if any — would meaningfully use this skill. Forcing a skill into
an agent that does not need it dilutes that agent's Mandatory Reads with noise,
which is worse than leaving the skill uncited.

The bar: an agent should cite a skill only when reading it would change the
agent's output for a real invocation. If you cannot name the scenario in which
the agent would be wrong without this skill, the skill does not belong there.

1. **Walk the roster.** Read `agents/_shared/RUNTIME_VS_BUILD.md` (full list)
   and `agents/_shared/SKILL_MAP.md` (existing citations). Generate 3–6
   candidates whose domain overlaps. For each, name the concrete scenario where
   citing this skill would matter. Drop any candidate without one.

2. **Patch only the candidates that pass.**

   ```bash
   python3 scripts/patch_agent_skill.py <agent-id> <skill-id> "<section-heading>" "<short description>"
   ```

   The helper inserts the skill into YAML `dependencies.skills:` alphabetically
   and appends a numbered bullet under the named Mandatory Reads section,
   renumbering subsequent items. Use `*end*` for flat numbered lists.
   Idempotent.

3. **Update `agents/_shared/SKILL_MAP.md`** when the wired agent has an entry
   there (Wave A/B/C tier agents). Developer-tier agents (apex-refactorer,
   lwc-builder, soql-optimizer, and so on) are tracked only in their own
   AGENT.md.

**What the validator actually enforces here — read this carefully.**
An uncited skill is a **WARN**, not an error. `_check_orphan_skills`
(`validate_repo.py:474`) is advisory, and its docstring explains why: it used
to be an ERROR whose message handed the reader a ready-to-paste citation
command, "which made mass-citation the cheapest route to a green build — and
produced 555 machine-generated citations whose description was just the slug
title-cased."

What carries ERROR severity is citation **quality**:
`_check_agent_citation_quality` (`validate_repo.py:602`) errors, per line, when
a Mandatory Reads description is an exact echo of the slug
("fsl-mobile-app-setup" → "Fsl mobile app setup"). One appended word clears it.
That is deliberate — it is a regression guard against the machine-generated
stub wave, not a judge of whether the justification is any good. Three further
WARNs cover reads with no description, reads that echo the slug behind a
bucketing label, and any agent over `MAX_AGENT_SKILL_READS = 40` numbered skill
reads anywhere in the file.

So: leaving a skill uncited does **not** block the commit. Recording the
decision is still the rule — wire it, or set `runtime_orphan: true` plus
`runtime_orphan_reason:` — but flipping orphan flags in bulk to silence the
WARN is the same gaming pattern under a different label. The WARN is cheap to
leave standing.

### Step 7 — Commit

Commit all of:

- the skill package under `skills/`
- generated files in `registry/`
- `vector_index/query-fixtures.json` and `manifest.json` (the other files there
  are gitignored)
- generated `docs/SKILLS.md`
- generated `docs/queue-progress.md` if `BACKLOG.yaml` changed
- generated `standards/validation-gates.md` if validator source changed
- modified files under `agents/` and `agents/_shared/SKILL_MAP.md` from step 6

---

## Architect Domain

Architect skills live in `skills/architect/` with `category: architect`. They
do NOT go in `skills/admin/`.

- Domain folder: `architect`
- `category` frontmatter: `architect`
- Scaffold: `python3 scripts/new_skill.py architect <skill-name> --strict --agent <agent_id>`

Enforced by `validate_repo.py`: `category` must match the parent folder name
(`pipelines/validators.py:176`, ERROR).

---

## Supporting Scripts (these exist — verified via `--help`)

| Script | Purpose | Usage |
|--------|---------|-------|
| `scripts/bootstrap.py` | One-command setup for a fresh clone: builds `chunks.jsonl` + `lexical.sqlite`, installs `commands/*.md` into `.claude/commands/`, then verifies. Writes no tracked files. | `python3 scripts/bootstrap.py` |
| `scripts/skill_graph.py` | Related-skill navigator — skills connected by shared tags, domain, or explicit deps | `python3 scripts/skill_graph.py <domain/skill-name>` |
| `scripts/search_skills.py` | Registry-level search with synonym expansion and role/cloud boosting (faster than knowledge search for skill-ID lookups) | `python3 scripts/search_skills.py "<query>" --role dev` |
| `scripts/check_gloss_coverage.py` | Does a term reach the shipped roster? Only `.claude/skills/salesforce-<domain>/references/skill-index.md` ships; a term in a body but not in the 220-char gloss reaches nobody. Exits 1 on misses. | `python3 scripts/check_gloss_coverage.py <term> --domain <domain>` |
| `scripts/check_doc_counts.py` | Derives canonical skill / agent / MCP-tool counts from `registry/skills.json` and `AGENT.md` frontmatter and asserts every quoted number in the docs matches. `--fix` rewrites drifted counts. | `python3 scripts/check_doc_counts.py` |
| `scripts/export_skills.py` | Exports skills to platform-native formats. Targets: `claude`, `cursor`, `mcp`, `windsurf`, `aider`, `augment`, `codex`, `agents`. | `python3 scripts/export_skills.py --target cursor` or `--all` |

Use `skill_graph.py` when writing cross-skill references in
`references/well-architected.md`. Use `search_skills.py` for duplicate checking
before scaffold. Run `check_gloss_coverage.py` after any wave that touches
skill descriptions or triggers.

---

## Shared Templates

Canonical cross-skill code scaffolds live under `templates/` at the repo root
(73 files):

- `templates/apex/` — `TriggerHandler`, `TriggerControl`, `BaseDomain`,
  `BaseService`, `BaseSelector`, `ApplicationLogger`, `SecurityUtils`,
  `HttpClient`, plus supporting CMDT and custom objects
- `templates/apex/tests/` — `TestDataFactory`, `TestRecordBuilder`,
  `MockHttpResponseGenerator`, `TestUserFactory`, `BulkTestPattern`
- `templates/lwc/` — Jest config, component skeleton with tests,
  wire/imperative/LDS patterns
- `templates/flow/` — record-triggered skeleton, fault-path runbook, subflow
  contract rules
- `templates/agentforce/` — agent spec, invocable action skeleton, topic
  template

**Rule for skill authors:** when a skill needs example code for a well-known
idiom (trigger handler, test factory, wire pattern, fault path, invocable
action), do NOT re-invent it inline. Reference the canonical template by
relative path and mark what must be renamed or specialized.

**Rule for agents during `/new-skill` and `/review`:**

- Read `templates/README.md` for the layout.
- Use a template path (e.g. `templates/apex/TriggerHandler.cls`) instead of
  pasting a reimplementation into `references/examples.md`.
- If a needed idiom is missing from `templates/`, flag it as a gap rather than
  writing a one-off in the skill.
- Copy Apex identifiers from the template file; never write one from memory.
  `AGENT_CONTRACT.md` lists the fabricated names that reached shipped agents —
  `stripInaccessibleFields`, `SecurityUtils.requireUpdateable`,
  `TestDataFactory.accounts(200)` — none of which exist. The real API is
  `Security.stripInaccessible(AccessType, records)`, which returns an
  `SObjectAccessDecision` you call `.getRecords()` on.

---

## Decision Trees

Cross-skill routing logic lives under `standards/decision-trees/`. There are
**seven** trees; `standards/decision-trees/README.md` is the authoritative
table of which tree routes what, and what to read it before.

- `automation-selection.md` — Flow vs Apex vs Agentforce vs Approvals vs
  Platform Events vs Batch
- `flow-pattern-selector.md` — which *kind* of Flow, once
  automation-selection has resolved to Flow
- `agentforce-capability-selector.md` — Agentforce Agent vs Prompt Builder vs
  Next Best Action vs Model Builder / BYOLLM vs Einstein Discovery vs Einstein
  Bots
- `async-selection.md` — `@future` vs Queueable vs Batch vs Schedulable vs
  Platform Events vs Scheduled Flow
- `integration-pattern-selection.md` — REST vs Bulk API vs Platform Events vs
  CDC vs Pub/Sub vs Salesforce Connect vs Named Credentials vs MuleSoft
- `sharing-selection.md` — OWD vs Role Hierarchy vs Sharing Rules vs Teams vs
  Manual vs Apex Managed vs Restriction / Scoping
- `performance-tuning.md` — where the time is going: Apex CPU/heap vs
  SOQL/index vs sharing recalc vs LDV vs cache vs LWC render

**Rule for agents:**

- If the user's request straddles more than one technology in a tree's scope,
  read the tree top-to-bottom **before** activating any skill.
- Cite the tree step that resolved the choice (e.g. "per
  `automation-selection.md` Q3, this needs a callout, so Apex — not Flow").
- When two skills score close in retrieval, the tree's recommended skill wins.
- If a scenario falls outside the existing trees, flag it as a gap; do not
  force-fit.

**Rule for skill authors:**

- Skills must **link** to the relevant decision tree from their `## Related`
  section, not duplicate its logic.
- A skill body that re-answers a tree's decision is a smell — delete the
  re-answer and link to the tree.

Tree structure is validated: `[unreachable-question]` WARNs fire when a
question is defined but no branch routes to it. Several stand today in
`async-selection.md`, `performance-tuning.md`, and `sharing-selection.md`.

---

## Golden Evals

Output-quality checks live under `evals/golden/<category>__<slug>.md` — 10
files, 3 P0 cases each. Retrieval fixtures (which skill gets picked) live
separately in `vector_index/query-fixtures.json`; do not duplicate.

**Rule for agents:**

- When you change a flagship skill, update its eval file in the same PR.
  "Flagship" means the 10 skills listed in `evals/README.md`.
- Before concluding a session that edited a flagship skill, run
  `python3 evals/scripts/run_evals.py --structure`.

**Rule for skill authors:**

- When adding a skill you consider flagship (high retrieval volume, or a
  high-blast-radius wrong answer), add an eval file using `evals/framework.md`
  as the schema source.
- Reference answers should cite `templates/…` and
  `standards/decision-trees/…` — evals are where those artifacts get
  exercised.

---

## Run-time Agents

76 `AGENT.md` files live under `agents/`, in three classes. The class and
status come from frontmatter (`class:`, `status:`), which is the canonical
source — `scripts/check_doc_counts.py` derives every quoted count from it.

1. **Build-time (14)** — `orchestrator`, `task-mapper`, `content-researcher`,
   the 6 skill-builders (`admin`, `dev`, `devops`, `data`, `architect`,
   `security`), `code-reviewer`, `validator`, `currency-monitor`,
   `org-assessor`, `release-planner`. These produce the library.

   > There is no `/run-queue` command. `commands/run-queue.md` was deleted on
   > 2026-05-08 in commit `014a069b3` ("infra: P0 FTS5 sanitizer fix + remove 6
   > deprecated commands"). `agents/_shared/AGENT_CONTRACT.md`,
   > `agents/_shared/RUNTIME_VS_BUILD.md`, and `agents/orchestrator/AGENT.md`
   > still name it as an entry point — that is wrong. Invoke build agents by
   > reading their `AGENT.md` directly, or via `/new-skill` and `/add-skill`.

2. **Run-time (48)** — four tiers:
   - **Developer + architecture (16):** `apex-refactorer`,
     `trigger-consolidator`, `test-class-generator`, `soql-optimizer`,
     `security-scanner`, `flow-analyzer`, `bulk-migration-planner`,
     `lwc-builder`, `lwc-auditor`, `lwc-debugger`, `deployment-risk-scorer`,
     `agentforce-builder`, `apex-builder`, `changeset-builder`,
     `flow-orchestrator-designer`, `automation-migration-router`.
   - **Admin accelerators — Tier 1 (14):** `field-impact-analyzer`,
     `object-designer`, `permission-set-architect`, `flow-builder`,
     `data-loader-pre-flight`, `duplicate-rule-designer`,
     `assignment-and-auto-response-rules-designer`,
     `business-hours-and-holidays-configurator`, `config-workbook-author`,
     `custom-metadata-and-settings-designer`,
     `entitlement-and-milestone-designer`, `experience-cloud-admin-designer`,
     `path-designer`, `process-flow-mapper`.
   - **Strategic — Tier 2 (7):** `data-model-reviewer`,
     `integration-catalog-builder`, `csv-to-object-mapper`,
     `email-template-modernizer`, `audit-router`, `fit-gap-analyzer`,
     `story-drafter`.
   - **Vertical + governance — Tier 3 (11):** `omni-channel-routing-designer`,
     `knowledge-article-taxonomy-agent`, `sales-stage-designer`,
     `lead-routing-rules-designer`, `sandbox-strategy-designer`,
     `release-train-planner`, `waf-assessor`, `agentforce-action-reviewer`,
     `profile-to-permset-migrator`, `user-access-diff`, `omnistudio-designer`.

   These USE the library to do real Salesforce work. Invoked via the matching
   `commands/<name>.md`, a direct AGENT.md read, or the MCP `get_agent` tool.
   Every active run-time agent must have a matching slash command — enforced
   as an ERROR at `pipelines/agent_validators.py:661`.

3. **Deprecated (14)** — single-mode auditors and governors consolidated into
   `audit-router` during Wave 3b. Their AGENT.md files remain for reference:
   `case-escalation-auditor`,
   `field-audit-trail-and-history-tracking-governor`,
   `lightning-record-page-auditor`, `list-view-and-search-layout-auditor`,
   `my-domain-and-session-security-auditor`, `org-drift-detector`,
   `picklist-governor`, `prompt-library-governor`,
   `quick-action-and-global-action-auditor`, `record-type-and-layout-auditor`,
   `report-and-dashboard-auditor`,
   `reports-and-dashboards-folder-sharing-auditor`, `sharing-audit-agent`,
   `validation-rule-auditor`. Nine of their slash-command aliases still ship;
   see `docs/MIGRATION.md` for which.

The single source of truth for what an AGENT.md must contain is
`agents/_shared/AGENT_CONTRACT.md`. The full roster lives in
`agents/_shared/RUNTIME_VS_BUILD.md`. The authoring reference mapping every
agent to its verified source skills, templates, and decision trees is
`agents/_shared/SKILL_MAP.md`.

**Rules for any agent (build-time or run-time):**

- Section requirements differ by class, and
  `pipelines/agent_validators.py:216` enforces the **order**, not just
  presence:
  - `class: runtime` — 8 sections: What This Agent Does, Invocation, Mandatory
    Reads Before Starting, Inputs, Plan, Output Contract, Escalation / Refusal
    Rules, What This Agent Does NOT Do.
  - `class: build` — 5 sections: What This Agent Does, Invocation, Mandatory
    Reads Before Starting, Plan, What This Agent Does NOT Do.
  - Deprecated stubs need only Plan and What This Agent Does NOT Do.
  - Aliases are accepted (`SECTION_ALIASES`): Invocation ↔ Activation Triggers
    ↔ Triggers; Plan ↔ Orchestration Plan; Output Contract ↔ Output Format;
    Escalation / Refusal Rules ↔ Escalation Rules; What This Agent Does NOT Do
    ↔ Anti-Patterns.
- Every agent MUST list in Mandatory Reads the specific skill ids, templates,
  and decision trees it consumes. "Follow the skills" is not sufficient.
- Every run-time agent MUST include a **Process Observations** subsection in
  its Output Contract (healthy / concerning / ambiguous / suggested
  follow-ups), per `AGENT_CONTRACT.md`.
- Every run-time agent MUST return a Citations block enumerating every skill,
  template, and decision-tree branch used. No citations means the agent ran
  blind.
- No agent may bypass `standards/source-hierarchy.md` when skills disagree.
- No agent may cite an invented path. `_validate_citations`
  (`pipelines/agent_validators.py:279–377`) ERRORs when a cited
  `skills/…`, `templates/…`, `standards/…`, `agents/_shared/probes/…`,
  `agents/…`, slash command, or MCP tool name does not resolve.
- No run-time agent may write to an org, call `sf project deploy`, or mutate
  files outside the paths the user supplied as input. This is a written rule
  (`AGENT_CONTRACT.md` rule 7), **not** a mechanical gate: the validator checks
  that the "What This Agent Does NOT Do" section exists and is in the right
  place, and does not inspect its wording.
- No agent may auto-chain to another agent. Recommending a follow-up in the
  output is fine; silently invoking one is not.

**Contract vs. reality — `search_skill`:**
`AGENT_CONTRACT.md` line 132 requires skill resolution through the MCP
`search_skill` tool. That is not what the shipped path does.
`.claude-plugin/plugin.json` declares `skills` and `commands` and no
`mcpServers`, and there is no `.mcp.json`, so a plugin install has no MCP
server. Only `audit-router`, `automation-migration-router`, and
`release-planner` mention `search_skill` at all, and the two routers gate a
`REFUSAL_NEEDS_HUMAN_REVIEW` on it — a refusal a plugin-only caller cannot
evaluate. Citation resolution is already enforced statically at PR time by
`_validate_citations`; prefer that as the real guarantee, and do not write new
runtime gates that assume MCP.

**Rules for the MCP server (38 tools):**

- The MCP server never executes an agent. Tools that expose agent context
  (`list_agents`, `get_agent`, `suggest_agent`) return instructions and the
  caller's model executes them. Same posture for `get_skill`, `get_template`,
  `get_decision_tree` — text in, text out, no side effects on the org.
- Run-time agent classification is read from each AGENT.md's frontmatter at
  server start: `class: runtime` plus optional `status: deprecated`. No
  hardcoded roster — adding a run-time agent needs only the frontmatter.
  Deprecated stubs surface under `kind="deprecated"` and resolve via
  `list_deprecated_redirects`.
- Counts in tool descriptions and `SERVER_INSTRUCTIONS` come from the registry
  and agents directory at runtime, never hand-edited.
  `mcp/sfskills-mcp/tests/test_meta_freshness.py` scans `src/` for stale
  literals (`686+`, `twenty-three tools`, `registers twenty-three`,
  `_RUNTIME_AGENTS`) to keep them extinct.
- Every tool carries `mcp.types.ToolAnnotations`. Today: 13 `_ANN_REPO_ONLY`,
  24 `_ANN_ORG_READ`, 1 `_ANN_ENVELOPE`. `readOnlyHint=True` on everything
  except `emit_envelope` (which writes paired JSON+MD into
  `docs/reports/<agent>/<run_id>`); `destructiveHint=False` on all;
  `openWorldHint=True` for org-touching tools and `False` for repo-only ones.
  A new tool MUST pick one of the three profiles in `server.py`.
- Org-touching tools — every `_ANN_ORG_READ` tool, which is all the
  `list_*` / `describe_*` / `get_apex_*` / `get_lwc_*` org readers,
  `tooling_query`, `validate_against_org`, and every `probe_*` — are strictly
  read-only. `tooling_query` refuses anything that does not start with
  `SELECT`, refuses DML statement tokens (`INSERT`, `UPDATE`, `DELETE`,
  `UPSERT`, `MERGE`) and `;`, and bounds rows at `MAX_TOOLING_QUERY_ROWS`.
  Adding a probe MUST keep that blocklist intact and validate object / field /
  permission-set names through `_shared._validate_api_name` (re-exported from
  `admin`).
- Default `sf` subprocess timeout is 90 s (`sf_cli._default_timeout`).
  Deployers raise it with `SFSKILLS_TIMEOUT_SECONDS`. The four heavy probes
  (`probe_apex_references`, `probe_flow_references`, `probe_matching_rules`,
  `probe_automation_graph`) call `ctx.report_progress` so clients render
  real-time status.

---

## Retrieval Rules

- Always run `python3 scripts/search_knowledge.py "<query>"` before claiming a
  new skill does not already exist or that a topic has no local coverage.
- Lexical retrieval is the required baseline and must remain functional with no
  API keys or cloud services. It does require a **locally built** index — see
  the bootstrap prerequisite above. An empty result on a fresh clone means "no
  index", not "no coverage".
- Embeddings are optional and must never be required for authoring, validation,
  or review. They are enabled by default in `config/retrieval-config.yaml`; the
  no-vector path degrades to lexical-only rather than failing.

### Interpreting search results

`search_knowledge.py --json` returns `chunks`, `skills`, `official_sources`,
`domain_filter`, `query`, and a `has_coverage` boolean.

- **`has_coverage: true`** — at least one skill scored above the confidence
  threshold. Use the top skill(s) to guide your response.
- **`has_coverage: false`** — no skill is confident enough. Do NOT present
  low-scoring skills as answers. Instead:
  1. Confirm the index exists (`bootstrap.py --verify-only`) before concluding
     anything about coverage.
  2. Tell the user the repo has no skill for this topic yet.
  3. Surface `official_sources` from the result — these are returned regardless
     of coverage.
  4. If this came up during a `/new-skill` flow, treat it as a confirmed gap
     and proceed.

Never present a skill to the user when `has_coverage` is false. The threshold
exists precisely to prevent confidently wrong answers.

---

## Skill Identity Rules

Enforced by `validate_repo.py` and `skill_sync.py` as **ERRORs** (hard
failure), with the gate line in `standards/validation-gates.md`:

- `name` frontmatter **must exactly match** the folder name
  (`validators.py:171`).
- `category` **must exactly match** the parent domain folder
  (`validators.py:176`).
- `description` **must include an explicit scope exclusion** — at least one
  "NOT for ..." clause (`validators.py:182`). This is what stops the skill
  activating on unrelated queries.
- SKILL.md body must be 300+ words (`validators.py:198`). No stub skills.
- No unfilled `TODO:` markers in frontmatter or body
  (`validators.py:188/192/203`).
- `## Official Sources Used` must exist in `references/well-architected.md`
  **and** list at least one source (`validators.py:351` and `:357`). Sources
  are pre-seeded by `new_skill.py`; do not delete them.
- `references/llm-anti-patterns.md` must exist (`validators.py:283`) and
  contain no unfilled TODOs (`validators.py:288`).
- Every required package file must exist; `templates/` must hold at least one
  file and `scripts/` at least one Python file (`validators.py:267–274`).

Validated as **WARNs** (advisory, do not fail the exit code):

- Fewer than 5 anti-patterns in `llm-anti-patterns.md` (`validators.py:297`),
  or a file under the byte-depth floor (`:311`).
- No `## Recommended Workflow` section in SKILL.md (`validators.py:345`). When
  present it should hold 3–7 numbered steps an AI agent follows when the skill
  activates — directives ("do this"), not explanations.
- `examples.md` with no fenced block (`validators.py:332`).
- Near-duplicate of another skill (`validators.py:701`).
- An `## Official Sources Used` block byte-identical to other skills in the
  same domain (`validators.py:781`) — a shared per-domain list is not grounding
  for this skill.
- Skill-local checker scripts that look like always-pass stubs
  (`validators.py:232/248/254`).

---

## Rejection Conditions

Do not sync, do not commit, if any of the following is true:

- frontmatter is missing required keys
- `name` does not match the folder name
- `category` does not match the parent domain folder
- `description` has no scope exclusion ("NOT for ...")
- SKILL.md body is under 300 words
- required package files are missing
- `## Official Sources Used` is absent or empty
- `references/llm-anti-patterns.md` is missing or still has TODOs
- generated registry/docs/index outputs are stale
- the skill has no query fixture, or its fixture does not return the skill in
  the top *k*
- the skill duplicates an existing skill without a clear disambiguation
- skill-local checker scripts require pip dependencies without explicit
  documentation
- `skill_sync.py` exits non-zero for this skill

---

## Official Sources Policy

Every skill must be grounded in official Salesforce documentation.

1. Check `standards/official-salesforce-sources.md` for authoritative sources
   in the skill's domain.
2. Domain sources are pre-seeded into `references/well-architected.md` by
   `new_skill.py`.
3. Do not make factual claims about Salesforce behavior, limits, or APIs
   without an official source.
4. Local knowledge sharpens guidance; it does not override official behavior
   claims.
5. When `has_coverage: false`, surface `official_sources` from the search
   result before saying there is no guidance.

---

## Rules For Editing Generated Artifacts

- Do not hand-edit `registry/`, `docs/SKILLS.md`, `docs/queue-progress.md`,
  `standards/validation-gates.md`, `.claude/skills/**/references/skill-index.md`,
  or the gitignored retrieval artifacts in `vector_index/`.
- Regenerate through `python3 scripts/skill_sync.py --all --skip-embeddings`.
- `vector_index/query-fixtures.json` is the exception: tracked and
  hand-maintained.

---

## Rules For Repo-Wide Changes

When changing standards, retrieval behavior, or authoring workflow:

1. Update the relevant source docs: `AGENT_RULES.md`, `CLAUDE.md`,
   `CONTRIBUTING.md`, `commands/new-skill.md`, and the affected agent
   definitions.
2. `python3 scripts/skill_sync.py --all --skip-embeddings`
3. `python3 scripts/validate_repo.py`
4. `python3 scripts/check_doc_counts.py` — any count you quoted must match the
   machine-derived value.

---

## Rule Of Simplicity

Prefer deterministic local scripts, generated JSON, and committed artifacts
over hidden state, cloud dependencies, or one-off manual exceptions.
