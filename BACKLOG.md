# BACKLOG — deferred framework ideas

**This is not the skill queue.** The skill queue is [`BACKLOG.yaml`](BACKLOG.yaml) — 646
machine-readable entries, written only through `scripts/queue_reader.py` and summarised in
the generated [`docs/queue-progress.md`](docs/queue-progress.md). This file is the much
smaller register of deferred *framework* ideas: tooling, agents, and process changes that
are real and tracked but not yet worth building. Nothing here creates a skill.

Each item has a **Why deferred** and a **Trigger** (the condition that makes it the right
time to pick it up). Items whose trigger has since fired, or whose original facts have gone
stale, carry a **Status** line.

Reviewed 2026-07-31: four sections were deleted because the work is done — embeddings
(`config/retrieval-config.yaml` has `enabled: true`, `backend: fastembed`), CI workflows
(4 files under `.github/workflows/`), cloud-specific skill content (already shipping), and
contribution tooling (`CONTRIBUTING.md`, `.github/PULL_REQUEST_TEMPLATE.md`, and 4
`.github/ISSUE_TEMPLATE/` files all exist).

---

## Infrastructure

### Clone weight (originally: Git LFS for lexical.sqlite)
**What:** Originally, move `vector_index/lexical.sqlite` to Git LFS so a large binary
doesn't bloat history.
**Status (2026-07-31):** Moot for new commits, unsolved for old ones. `lexical.sqlite` is
gitignored (`.gitignore:7`) and was untracked at `27e89cda7`; `chunks.jsonl`,
`embeddings.jsonl`, and `skill_embeddings.jsonl` followed. `git ls-files vector_index/`
now returns only `manifest.json`, `query-fixtures.json`, `query-variants.json`. What
remains is legacy pack weight the ignores cannot undo: `.git` is 524 MB (`du -sh .git`;
size-pack 389.86 MiB), and 206 committed revisions of `chunks.jsonl` account for
11,651 MB — 85.0% of the 13,709 MB of reachable blob bytes. `lexical.sqlite` adds 962 MB
across 30 revisions.
**Why deferred:** LFS no longer addresses the problem. The only fix for weight already in
the pack is a history rewrite (`git filter-repo`, `git lfs migrate`), which rewrites every
SHA and invalidates every existing clone, fork, and the commit refs cited in the docs.
That is not worth it at 524 MB.
**Trigger:** A contributor reports the clone is unworkable, or `registry/skills.json`
(766 MB across 221 revisions, still tracked by design because it encodes the content hash
that detects rebuild drift) starts dominating growth the way `chunks.jsonl` did.
**Work needed:** Decide whether `registry/skills.json` gets the manifest-hash-only
treatment `chunks.jsonl` received. A rewrite would need a coordinated re-clone across every
consumer, including the published MCP package's users.

---

## Content Quality

### Cross-skill contradiction detection
**What:** Automated check that scans overlapping skills for conflicting factual claims
(e.g., two skills disagree on a governor limit).
**Status (2026-07-31):** Trigger has fired. `find skills -name SKILL.md | wc -l` returns
1027 across 11 domains — far past the 150-skill threshold, and apex + integration + admin
all cover callout limits. `scripts/check_contradictions.py` still does not exist. This is
now genuinely pending work, not a deferred idea.
**Why deferred:** No longer justified by volume; it is deferred only because nobody has
picked it up.
**Trigger:** Met.
**Work needed:** Add a `scripts/check_contradictions.py` that runs `search_knowledge.py`
against each skill's claims and flags divergence above a threshold. Wire it into
`pipelines/validators.py` so `validate_repo.py` reports it, and record the gate in the
generated `standards/validation-gates.md`.

---

### Source staleness monitoring (Currency Monitor)
**What:** Agent that checks `updated` frontmatter against Salesforce release notes and
flags skills whose claims may be out of date.
**Status (2026-07-31):** Half built. `agents/currency-monitor/AGENT.md` exists, but nothing
runs it — no file under `.github/` or `.githooks/` references the agent, so it only fires
when a human invokes it.
**Why deferred:** The agent definition was the easy half. Scheduling it means deciding what
a stale claim costs and who triages the output; without that, a monthly run just produces
noise nobody actions.
**Trigger:** First release cycle where a skill demonstrably ships a claim the release notes
had already superseded.
**Work needed:** A scheduled run (GitHub Actions cron, alongside the existing
`org-validation.yml` schedule) plus `[STALE-RISK]` tag automation and a triage owner.

---

### Tier 4 source filtering in Validator
**What:** Automated detection of Reddit, LinkedIn, or non-MVP blog links in skill bodies.
**Status (2026-07-31):** Still nothing to catch. `grep -rl 'reddit\.com\|linkedin\.com'
skills/` returns 0 files, and `pipelines/validators.py` contains no such check.
**Why deferred:** Every skill built so far uses only T1/T2 sources, so the check would be a
gate with a zero hit rate.
**Trigger:** External contributors start submitting skills, or the grep above stops
returning 0.
**Work needed:** A `validate_source_tiers` function in `pipelines/validators.py` with a URL
pattern list, registered so it shows up in the generated `standards/validation-gates.md`.

---

## Agent Architecture

### Multi-cloud skill builder specialization
**What:** Separate skill builder agents for specific clouds (Sales Cloud, Service Cloud,
etc.) rather than one generic admin/dev builder.
**Status (2026-07-31):** The original trigger is unusable. It was phrased around a
"Phase 1 complete, then Phase 2 starts" model that no longer describes the repo — cloud
specific skills already ship (`skills/admin/health-cloud-patient-setup`,
`skills/admin/marketing-cloud-connect`, and others). No `agents/*cloud-builder*` exists.
The item needs a new trigger before it can be picked up.
**Why deferred:** One generic builder plus per-domain skills has not visibly failed. A
cloud-specialised builder only pays off if generic builders start producing wrong
cloud-specific guidance.
**Trigger:** Needs restating. Candidate: a measured quality gap where cloud-specific skills
built by the generic builder fail review at a materially higher rate than platform skills.
**Work needed:** Define the trigger, then `agents/sales-cloud-builder/AGENT.md`,
`agents/service-cloud-builder/AGENT.md`, and a routing update in the orchestrator.

---

### Skill update (UPDATE status) workflow
**What:** Full workflow for when an existing skill needs to be revised after a Salesforce
release.
**Status (2026-07-31):** The original pointer was dead. It named a `run-queue.md` command
file that was never created — `commands/` holds 66 files and none is it. The queue workflow
now lives in `MASTER_QUEUE.md` (queue-specific steps) and `CLAUDE.md` (scaffold → author →
sync → validate), so an `## UPDATE Workflow` section belongs in `MASTER_QUEUE.md`.
**Why deferred:** No UPDATE rows have been worked yet. `UPDATE` is defined in the
`MASTER_QUEUE.md` status key but has no step-by-step procedure behind it.
**Trigger:** When the Currency Monitor (above) produces its first UPDATE entry.
**Work needed:** Add `## UPDATE Workflow` to `MASTER_QUEUE.md`, defining the diff-based
revision process and what gets re-validated (fixtures, evals, `updated:` bump).

---

## Observability

### Skill usage analytics
**What:** Track which skills are retrieved most often, which queries return
`has_coverage: false`, and which fixtures fail.
**Status (2026-07-31):** Trigger is arguably met. The MCP server ships on PyPI
(`pip install sfskills-mcp`), so the repo is queryable from outside this machine. No
`logs/` directory exists and nothing records query outcomes.
**Why deferred:** Query volume through the published server is unknown, and any logging
design has to answer where the data lands — a local `logs/` directory captures only this
machine and tells you nothing about installed users.
**Trigger:** Evidence of real external query volume, or the first time a retrieval
regression ships unnoticed because nothing was measuring it.
**Work needed:** Logging wrapper around `search_knowledge.py` and the MCP `skills.py`
path, a `logs/` directory (gitignored), and a weekly report. Note the CLI and the MCP
server currently apply different coverage semantics, so a single wrapper will not cover
both without reconciling them first.
