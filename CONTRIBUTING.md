# Contributing to SfSkills

Four ways to contribute. Each has a different path; all end at the same gates.

| Scenario | Path |
|----------|------|
| I want to **add a new skill** | [→ Add a Skill](#add-a-skill) |
| I want to **fix a wrong or outdated skill** | [→ Fix a Skill](#fix-a-skill) |
| I want to **report a missing skill** (without building it) | [→ Report a Gap](#report-a-gap) |
| I want to **flag a skill as stale** after a Salesforce release | [→ Flag Stale Content](#flag-stale-content) |

---

## Setup — do this first

```bash
python3 -m pip install -r requirements.txt
python3 scripts/bootstrap.py
```

`git clone` alone does not give you a working library. The retrieval corpus
(`vector_index/chunks.jsonl`) and the FTS5 index (`vector_index/lexical.sqlite`)
are gitignored and must be built locally, and `.claude/commands/` is not
committed either. Without the index, `scripts/search_knowledge.py` reports no
coverage for every query **and still exits 0** — so step 1 of the add-a-skill
flow silently passes when it should not.

`python3 scripts/bootstrap.py --verify-only` re-checks in under a second and
prints whether retrieval and the slash commands are live. Bootstrap writes
no tracked files and makes no network calls.

Optional but recommended:

```bash
python3 scripts/install_hooks.py
```

Installs a fast `pre-commit` (changed-only sync + validate) and a `pre-push`
that runs the full four-shard skill sweep. **The pre-push hook takes several
minutes**: each shard takes minutes on the full corpus, and the hook runs four
sequentially. Use `git push --no-verify` on WIP branches; CI still gates merge.

---

## The Two Gates (mandatory for everything)

**Gate 1 — Structural (automated)**

```bash
python3 scripts/skill_sync.py --skill skills/<domain>/<skill-name> --skip-embeddings
python3 scripts/validate_repo.py
```

`validate_repo.py` must exit 0. It exits non-zero on **ERROR** only. WARNs
print and do not block — the corpus carries hundreds of them by design. Read them, decide, move on; do not treat "zero warnings"
as the bar, because nobody can hit it.

The complete gate list, with severity and a link to the source line for each,
is generated at [`standards/validation-gates.md`](standards/validation-gates.md).
Read that instead of grepping validator code.
Do not hand-edit it.

**Gate 2 — Quality (checklist)**

Read `standards/skill-content-contract.md`. Your skill must pass all five
gates:

1. Every factual claim is sourced the way the corpus does it (see
   [Sourcing](#sourcing) below): a corpus line citation, an official URL in
   `## Official Sources Used`, or an inline `UNVERIFIED` marker
2. Content depth — examples, gotchas, templates meet the per-file minimums
3. Agent usability — an AI can follow it without asking for clarification
4. No undocumented contradictions with other skills
5. Version-sensitive claims are qualified with release names

Gate 2 is human review. No script checks it.

---

## Add a Skill

### Step 1 — Check it doesn't already exist

```bash
python3 scripts/search_knowledge.py "<your topic>"
python3 scripts/search_knowledge.py "<your topic>" --domain <domain>
```

If `has_coverage: true`, extend the existing skill rather than adding a new
one. Empty results on a fresh clone mean "no index", not "no coverage" — see
Setup.

Then run the semantic-duplicate audit, which compares against every skill's
description, tags, and triggers rather than lexical retrieval alone:

```bash
python3 scripts/audit_duplicates.py --domain <domain>
```

It writes `docs/reports/duplicate-candidates.md`; add `--json` to inspect
without rewriting the report. The threshold lives in
`config/retrieval-config.yaml` → `duplicate_threshold.score` (0.50 today).

Also check what is built (`docs/SKILLS.md`) and what is planned
(`RELEASES.yaml`, read through the script):

```bash
python3 scripts/release_plan.py status
```

If your topic is a planned item that nobody has started, you can build it.
`BACKLOG.yaml` is a frozen skill-request queue kept for history; do not add
to it.

### Step 2 — Pick the domain

There are 11 domain folders, and `category:` in frontmatter must match the
parent folder exactly — the validator ERRORs otherwise
(`pipelines/validators.py:176`).

```
admin       → Declarative configuration, BA artifacts, reports, sharing model
apex        → Apex classes, triggers, async, SOQL from code, testing
architect   → Solution/platform architecture, ADRs, Well-Architected, LDV strategy
lwc         → Lightning Web Components
flow        → Flow Builder patterns
omnistudio  → OmniStudio, Integration Procedures, DataRaptors
agentforce  → Agentforce, Einstein AI
security    → Org security, Shield, encryption, monitoring, incident response
integration → Inbound APIs, Platform Events, CDC, Pub/Sub, OAuth, middleware
data        → Data modelling, migration, bulk load, dedup at volume, archival
devops      → SFDX, CI/CD, scratch orgs, packaging, release
```

Architect skills go in `skills/architect/`, **not** `skills/admin/`.

Roles are not encoded in the folder structure. State the audience in the
`description` and `triggers` frontmatter instead.

### Step 3 — Research before writing (mandatory)

Read `standards/source-hierarchy.md`. Do not write from memory. Every
behavior claim needs a source.

#### Sourcing

This is what the corpus actually does. `standards/skill-content-contract.md`
describes `[T1]`-style source tags; shipped skills almost never use them.

- **Official Sources Used.** `references/well-architected.md` carries a
  `## Official Sources Used` section listing the official Salesforce pages
  the package relies on. The validator ERRORs when it is missing or empty.
- **Corpus line citations.** A specific claim (a limit, an API name, a
  metadata element) cites the official guide it came from by short name,
  release and line in the text extracted from Salesforce's release PDF, for
  example `` `apexdev 264 L19780` ``. `standards/skill-writer-brief.md` lists
  the guides and how to fetch them.
- **Inline `UNVERIFIED` markers.** A claim you could not ground in a fetched
  official page carries `UNVERIFIED (YYYY-MM-DD): <why>` written beside the
  claim itself, not in a footnote or another file.

Older skills that were never claims-audited have none of the last two, and
some of their claims are wrong. Do not treat an unmarked claim as checked.

### Step 4 — Scaffold

```bash
python3 scripts/new_skill.py <domain> <skill-name> --strict --agent <agent-id>
```

`--strict` blocks the scaffold when the proposed name is a near-duplicate of an
existing skill. `--agent` records which run-time agent will cite the skill and
wires it into that agent's `dependencies.skills:` and Mandatory Reads; repeat
for several. If no agent honestly needs it, use
`--runtime-orphan --orphan-reason "<why>"` instead. The two are mutually
exclusive, and one of them is required outside a TTY. In scripted runs add
`--assume-yes` so the coverage prompt does not EOF-crash.

Being uncited is a **WARN**, not a failure. Wire a skill to an agent only when
that agent's output would be wrong without it; a citation nobody reads spends
the agent's context and buys nothing.

### Step 5 — Fill the package

Per-file minimums, from `standards/skill-content-contract.md`:

**SKILL.md**
- `description` includes a "NOT for..." exclusion — ERROR without it
- `triggers`: 3+ symptom phrases a practitioner would type, 10+ chars each
- `inputs` / `outputs`: concrete, at least one each
- Body 300+ words — ERROR under
- At least 2 operational modes (Build / Review / Troubleshoot)
- A Gather section listing what context the AI needs before starting
- A `## Recommended Workflow` section, 3–7 numbered directive steps (WARN if
  absent)
- Body references `references/gotchas.md` at least once
- Every factual claim carries a corpus line citation or URL, or an inline
  `UNVERIFIED` marker

**references/examples.md**
- 2+ complete examples: Scenario, Problem, Solution, Why it works, Source
- At least one shows what goes wrong when applied incorrectly, and the recovery
- At least one fenced block — a worked artifact, not prose (WARN if none)

**references/gotchas.md**
- 3+ non-obvious behaviors: What happens, Why, How to avoid, Source
- Source disagreements surface here, not in SKILL.md
- Release-sensitive items carry `[STALE-RISK: what to check]`

**references/well-architected.md**
- `## Official Sources Used` with at least 1 Tier 1 URL — ERROR if the heading
  is missing or the section is empty
- Pillar mapping is specific, not "this skill touches Security"
- Do not delete the sources `new_skill.py` pre-seeded; add usage context

**references/llm-anti-patterns.md**
- Must exist with no unfilled TODOs — ERROR
- 5+ entries (WARN under). Each: what the LLM generates wrong, why, the correct
  pattern, a detection hint

**scripts/check_*.py**
- Real logic, not an always-pass stub. A WARN catches very short checkers;
  review must catch the rest — stub checkers have shipped before
- Stdlib only, Python 3.8+, exit 0 pass / 1 fail with a readable message

**templates/\<skill-name\>-template.md**
- Fill-in-the-blank output, not a meta-template
- `[REPLACE: description]` placeholders
- Includes a verification section

**Apex in any of these files:** copy identifiers from `templates/apex/`, do not
write them from memory. There is no `stripInaccessibleFields`. The real API is
`Security.stripInaccessible(AccessType, records)`, which returns an
`SObjectAccessDecision`; you operate on `.getRecords()`. DML on the original
list is unenforced.

### Step 6 — Sync and validate

```bash
python3 scripts/skill_sync.py --skill skills/<domain>/<skill-name> --skip-embeddings
python3 scripts/validate_repo.py
```

Fix every **ERROR**. Read the WARNs and decide.

For a repo-wide rebuild use `--all --skip-embeddings`. `embeddings.enabled` is
`true` in `config/retrieval-config.yaml`, so a bare `--all` attempts a
chunk-level encode — the config records ~2:20 for a first build on an M-series
CPU, and `.githooks/pre-commit` records ~3 hours when the cache is cold.
Rebuild embeddings deliberately with `python3 scripts/build_index.py`; it and
`scripts/generate_docs.py` start that pass even when given `--help`.

### Step 7 — Add a query fixture

Confirm the skill is findable:

```bash
python3 scripts/search_knowledge.py "<query a practitioner would type>" --json
```

Confirm it appears in the top 3, then add to `vector_index/query-fixtures.json`
(this file is tracked and hand-edited, unlike the rest of `vector_index/`):

```json
{
  "query": "your query here",
  "domain": "<domain>",
  "expected_skill": "<domain>/<skill-name>",
  "top_k": 3
}
```

Both halves are ERRORs: a skill with no fixture, and a fixture whose query does
not return the skill in the top *k*.

### Step 8 — If you changed any description or triggers, check the shipped gloss

Only `.claude/skills/salesforce-<domain>/references/skill-index.md` ships to a
plugin install — no FTS5 index, no embeddings. Vocabulary that lives in a skill
body but not in its 220-character gloss reaches nobody, and nothing errors.

```bash
python3 scripts/check_gloss_coverage.py <term> --domain <domain>
```

Exits 1 when packages mention the term but do not route on it.

### Step 9 — Open a PR

Title: `feat(<domain>): add <skill-name>`

`.github/PULL_REQUEST_TEMPLATE.md` will prompt you for the rest. Its pre-flight
list is the binding one:

- `python3 scripts/validate_repo.py` exits 0
- If you touched `mcp/sfskills-mcp/`:
  `python3 -m unittest discover -s mcp/sfskills-mcp/tests` exits 0
- `skill_sync.py --skill … --skip-embeddings` ran clean and the registry diff is included
- No `/Users/<author>/` paths or other identifying information
- Frontmatter complete on every new SKILL.md / AGENT.md

Also say which official sources you used and what the skill's scope exclusion
is.

---

## Fix a Skill

### Step 1 — Identify what's wrong

| Type | What to do |
|------|-----------|
| **Wrong factual claim** | Find the correct official source, update the claim, and cite it (see [Sourcing](#sourcing)) |
| **Missing content** | Add it following the content-depth requirements above |
| **Stale after a release** | See [Flag Stale Content](#flag-stale-content) |

### Step 2 — Edit the skill files

Edit only files under `skills/<domain>/<skill-name>/`. Never hand-edit
`registry/`, `docs/SKILLS.md`, `docs/agents.md`,
`standards/validation-gates.md`, `.claude/skills/**/references/skill-index.md`,
or the gitignored artifacts in `vector_index/` — they are generated.
`vector_index/query-fixtures.json` is the one tracked, hand-edited exception.

### Step 3 — Run both gates

```bash
python3 scripts/skill_sync.py --skill skills/<domain>/<skill-name> --skip-embeddings
python3 scripts/validate_repo.py
```

### Step 4 — Update `updated` and bump `version`

If you changed content (not just formatting), set `updated:` to today and bump
`version` by one patch level (`1.0.0` → `1.0.1`). `updated:` records an edit;
it is not evidence that anything was verified. Bump the version with it:
`validate_repo.py` treats a skill at `version: 1.0.0` with `updated:` on or
after 2026-10-19 as a new skill and holds it to the new-skill depth bar
(`pipelines/validators.py`, `DEPTH_NEW_SKILL_CUTOFF`).

### Step 5 — Open a PR

Title: `fix(<domain>): update <skill-name> — <what changed>`

Say what was wrong, what the correct behavior is, and the official source that
confirms the fix.

---

## Report a Gap

You know a skill is missing but do not want to build it. Two reliable routes:

### Option 1 — GitHub issue (recommended)

Use the **📚 Skill request** template. Blank issues are disabled
(`.github/ISSUE_TEMPLATE/config.yml`), so pick that template rather than
composing a title by hand — it applies the
`[Skill Request] <domain>: <skill-name>` title and the `skill-request` /
`triage` labels for you.

Include the role, the cloud, the task the skill covers, and why existing skills
do not cover it (say what `search_knowledge.py` returned).

### Option 2 — Add it to the release plan

In Claude Code:

```
/add-to-backlog <one sentence: the task the skill covers and who it is for>
```

Without Claude Code, the same thing from a shell (`--help` lists the flags):

```bash
python3 scripts/release_plan.py add --size S "<ask>"
```

Both size the ask (S, M or L) and slot it into a release in `RELEASES.yaml`.

Naming rules for the proposed skill:

- lowercase kebab-case: `case-assignment-rules-setup`
- must belong to one of the 11 domain folders
- the description must include "NOT for..." or it will be rejected downstream

---

## Flag Stale Content

Salesforce ships three major releases a year (Spring, Summer, Winter). Skills
go stale.

If you spot a stale claim:

1. Add `[STALE-RISK: <what changed and when>]` inline next to the affected
   claim, in `references/gotchas.md` where the depth belongs.
2. Open a PR or issue titled
   `stale(<domain>/<skill-name>): <Season 'YY> release changed <what>`.

There is a `currency-monitor` build-time agent
(`agents/currency-monitor/AGENT.md`) that scans skills against release notes
and files each stale candidate into the release plan with
`python3 scripts/release_plan.py add`.

---

## Using Agents to Contribute

The add and fix flows can run through Claude Code:

```
/new-skill
"I need a skill for Sales Cloud opportunity stage management"

"The trigger-framework skill is missing guidance for Flow-triggered Apex —
 can you update it?"
```

Agents run the same gates as manual contributions. Nothing bypasses
`validate_repo.py`.

---

## What Gets Rejected

| Reason | Fix |
|--------|-----|
| Factual claim with no source | Cite it (see [Sourcing](#sourcing)) or mark it `UNVERIFIED` inline |
| `validate_repo.py` exits non-zero | Fix every ERROR |
| SKILL.md body under 300 words | Expand — stubs are not skills |
| `description` has no "NOT for..." | Add an explicit scope exclusion |
| `category` does not match the folder | Move the skill or fix the frontmatter |
| `## Official Sources Used` missing or empty | Add at least one Tier 1 source |
| `llm-anti-patterns.md` missing or still has TODOs | Write it |
| No query fixture, or the fixture misses the top *k* | Add or retune it |
| examples.md has fewer than 2 complete examples | Add them |
| gotchas.md has fewer than 3 entries | Add them |
| `scripts/check_*.py` is a stub (review catches this; no gate does reliably) | Implement real validation logic |
| Skill duplicates an existing one | Extend the existing skill instead |
| Generated artifacts are stale | `skill_sync.py --all --skip-embeddings` |
| Any unresolved `TODO:` marker | Fill them all |
| A fabricated Apex identifier | Copy it from `templates/apex/` |

---

## Skill Authoring Principles

1. **Every claim needs a source.** Training data is not a source. If you cannot
   find it in official Salesforce docs, do not assert it, or mark it
   `UNVERIFIED` beside the claim.

2. **Write for the AI, not the human.** The primary reader is an AI agent using
   this skill to help a practitioner. Every decision branch must be explicit.
   "It depends" without naming the variables is useless.

3. **Narrow scope beats broad coverage.** One tight skill with 3 real gotchas
   beats a broad skill with 10 shallow points. Use "NOT for..." to hold the
   line.

4. **Contradictions must surface.** If official docs say X and an expert blog
   says Y, document both in `gotchas.md`. Do not silently pick one. See
   `standards/source-hierarchy.md` for resolution rules.

5. **Skills go stale.** Version-qualify anything that changes: "As of Spring
   '25, the limit is..." not "The limit is...".

---

## Licensing of Contributions

SfSkills is source-available under the
[PolyForm Small Business License 1.0.0](./LICENSE) — free below 100 people and
USD 1M prior-year revenue, commercially licensed above it. See
[`LICENSING.md`](./LICENSING.md).

**By opening a pull request you agree that your contribution is licensed to the
project under those same terms**, and that you have the right to grant that
licence — i.e. the work is yours, or your employer has cleared it.

Two practical consequences:

- **Write original prose.** Author from the official Salesforce documentation
  in your own words. Do not paste text out of another repository, a blog post,
  Stack Exchange, or vendor material, even when its licence looks permissive —
  attribution obligations attach to it and follow the file forever.
- **Say so if you are adapting something.** If a contribution is derived from
  an external source, flag it in the PR description with the source and its
  licence. Permissive sources can usually be adapted with attribution; anything
  else needs a clean-room rewrite. `/onboard-source` handles this properly.

## Getting Help

- Search existing skills: `python3 scripts/search_knowledge.py "<topic>"`
- Authoring rules: [`AGENT_RULES.md`](AGENT_RULES.md)
- Quality contract: `standards/skill-content-contract.md`
- Source rules: `standards/source-hierarchy.md`
- Every validator gate with its severity:
  [`standards/validation-gates.md`](standards/validation-gates.md)
- Usage questions and "how do I…":
  [GitHub Discussions](https://github.com/PranavNagrecha/AwesomeSalesforceSkills/discussions)
  — the issue tracker takes bugs, skill requests, and MCP tool requests via
  their templates
