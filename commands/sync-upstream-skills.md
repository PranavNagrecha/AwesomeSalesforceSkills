# /sync-upstream-skills — Weekly Upstream Radar (clean-room)

Runs the clean-room discovery radar over [`forcedotcom/sf-skills`](https://github.com/forcedotcom/sf-skills)
and queues any genuinely-new topics for authoring **from official Salesforce docs**.

## ⚠️ Licensing — read first

`forcedotcom/sf-skills` is licensed **CC BY-NC 4.0**. This repo is **Apache-2.0**. They are
**incompatible for copying.** Treat upstream purely as a *discovery radar*: it tells us *what
topics exist*, nothing more.

- **Never** fetch, copy, paraphrase, or closely translate upstream `SKILL.md` / `README` prose.
- Author every new skill yourself from **official Salesforce documentation** (the primary
  authority per `CLAUDE.md`). Facts, APIs, and topic names are not copyrightable; their
  expression is.
- The radar script (`scripts/upstream_radar.py`) only reads upstream **file paths + blob
  SHAs** via the GitHub API — never file contents.

## Usage

```
/sync-upstream-skills
```

## Cadence

Intended weekly (Mondays). Operational state — the manifest of upstream slugs + blob SHAs —
is committed at `config/upstream-sources/sf-skills.manifest.json` (a lockfile-style artifact).
Dated triage output stays **out of `main`** (per the no-session-artifacts rule); only the
manifest, the tooling, and any authored skills get committed.

## What happens

### Step 1 — Run the radar (deterministic)

```bash
# Weekly delta: classify only skills new/changed since the committed manifest
python3 scripts/upstream_radar.py --json

# Periodic full audit: re-classify every upstream skill against our index
python3 scripts/upstream_radar.py --full --json --dry-run
```

The radar diffs the upstream latest release against the committed manifest, then classifies
each new/changed slug against our catalog via `scripts/search_knowledge.py`:

- `NET_NEW` — top local score `< 3.0`: likely a genuine gap.
- `ENRICH` — `3.0–5.0`: partial coverage worth extending.
- `COVERED` — `≥ 5.0`: already covered; skip.

> ⚠️ **The radar over-flags.** Its query is a noun-stripped lexical proxy, so it routinely
> marks covered topics (e.g. `generating-apex`, `querying-soql`) as actionable. It **proposes;
> a human/agent disposes.** Do not trust `auto_scaffold` to drive scaffolding directly.

### Step 2 — Verify each candidate (grounded, mandatory)

For every `NET_NEW`/`ENRICH` candidate, before authoring:

1. Run `python3 scripts/search_knowledge.py "<good Salesforce-noun query>"` and **read the
   verbatim top results.** Confirm we truly lack it (never trust a fabricated "no skill found"
   — require the actual output; see memory `feedback_dont_delegate_gap_analysis`).
2. Confirm the topic is a **distinct, current** Salesforce capability via official docs
   (`standards/official-salesforce-sources.md`, help/developer/architect.salesforce.com,
   release notes). Capture the official source URLs and the GA/Beta status (don't assert a
   maturity the docs don't state).
3. Drop anything the search shows we already cover. The catalog is saturated
   (see `project_skill_coverage_gaps`) — the bar for a new skill is high.

### Step 3 — Author (clean-room, from official docs)

For confirmed gaps, follow `/new-skill`:

```bash
python3 scripts/audit_duplicates.py --domain <domain>
python3 scripts/new_skill.py <domain> <name> --strict --agent <agent_id>
# fill SKILL.md + references from OFFICIAL DOCS only
python3 scripts/skill_sync.py --skill skills/<domain>/<name>
python3 scripts/validate_repo.py
```

Collapse related upstream slugs into **one** well-cross-referenced skill where the underlying
mechanics already exist (e.g. don't mirror 11 `ui-bundle-*` slugs as 11 skills).

### Step 4 — Commit the manifest + open a DRAFT PR

- Commit the refreshed `config/upstream-sources/sf-skills.manifest.json` (the radar writes it
  unless `--dry-run`).
- Open a **draft** PR with the authored skills + generated artifacts. **Never auto-merge.**
- In the PR body, cite the official sources used and explicitly note "clean-room authored from
  official docs; no upstream prose copied."

## Related

- `scripts/upstream_radar.py` — the deterministic radar (see its module docstring for flags).
- `commands/new-skill.md` — the authoring workflow each confirmed gap follows.
- Memory: `project_upstream_sf_skills_sync` (the clean-room decision), `feedback_no_session_artifacts_in_main`.
