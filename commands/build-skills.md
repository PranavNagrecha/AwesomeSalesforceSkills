# /build-skills — Hermes-style agentic skill batch builder

End-to-end orchestrator that takes a count + optional topic hints and ships N production-grade skills with measurement-driven quality gates at every step.

This is the primary skill-creation entry point as of 2026-05-08, replacing the manual `/new-skill` flow for batch work. `/new-skill` remains for one-off authoring.

## Usage

```
/build-skills <N> [<topic-hint-1> <topic-hint-2> ...]
```

Examples:
- `/build-skills 5` — discover top 5 verified gaps, build them
- `/build-skills 10 agentforce data-cloud field-service` — bias discovery toward listed topic areas, build top 10
- `/build-skills 3 audit-driven` — pull candidates from the most recent audit's gap themes

## Hermes principles enforced

This command applies Hermes agentic-development principles:

1. **Evals over vibes** — every step has a measurable success criterion (HIGH/MED/LOW per rubric below).
2. **Self-improving** — every run appends metrics to `.planning/build-history/<date>.jsonl`. Each future run reads the last 5 runs' metrics to recalibrate (e.g. raise duplicate-rejection threshold if last runs had high false-positive rate).
3. **Composable primitives** — discover → screen → plan → build → wire → validate → commit are each runnable standalone (`scripts/`, `evals/measurement/`).
4. **Verifiable** — every claim is checked by an independent agent before commit (description URLs verified, search-screen verifies no duplicates, validate_repo enforces shape).
5. **Production-only commits** — per the repo's `.gitignore` and the "no session artifacts in main" rule, only product changes + reusable tooling get committed. Dated reports go to `.planning/build-history/` (gitignored).

---

## Step 0 — Pre-flight (no exceptions)

```bash
# Confirm clean working tree
git status --short
# Must be empty. If not, ask the user before proceeding — never start a build wave on dirty state.

# Pull latest
git pull --rebase origin main

# Confirm the harness is healthy
python3 scripts/validate_repo.py 2>&1 | tail -3
# Must show 0 errors. If errors, fix them before starting (this is a PRE-CONDITION not part of the build).
```

If pre-flight fails, **stop and report**. Do not paper over a broken baseline.

---

## Step 1 — Discover candidates (3N targets)

Goal: produce a candidate list of `~3 * N` proposed skill slugs that MIGHT be real gaps.

Sources, in priority order:

### 1a. Audit-driven (highest confidence)

If `evals/measurement/per_row.jsonl` exists from a prior audit run, mine zero-coverage and weak-coverage queries:

```bash
python3 << 'EOF'
import json
zeros = []
for line in open('evals/measurement/per_row.jsonl'):
    r = json.loads(line)
    if r.get('loop','').startswith('Loop 1'): continue   # baseline = author-curated
    if not r.get('has_coverage'): zeros.append(r)
# Group by topic, dedupe, output top candidates
EOF
```

### 1b. User hints

For each topic hint the user passed: search `scripts/search_knowledge.py "<hint>"` and identify clusters that score weakly (top-1 < 1.5). Generate proposed slugs in the form `<domain>/<descriptive-name>`.

### 1c. Roadmap-driven

Read `BACKLOG.yaml` for any entries with `status: planned` and `priority: high` — those are pre-vetted gaps from the user's backlog work.

### 1d. Competitive-driven (only if 1a-1c yield <3N)

Mine the most recent competitive research files in `/tmp/sf-session-*/competitive_*.md` if any exist locally. Topics that competitor tools cover but our screener flags as GAP are good candidates.

**Output:** write candidates to `.planning/build-history/<YYYY-MM-DD>-candidates.json`:

```json
[
  {"proposed_slug": "domain/skill-name", "topic_keywords": "search query for screening", "source": "audit|hint|roadmap|competitive", "priority": "high|medium|low"},
  ...
]
```

---

## Step 2 — Screen (mandatory dedup gate)

```bash
python3 evals/measurement/gap_candidate_screener.py \
    --candidates .planning/build-history/<YYYY-MM-DD>-candidates.json \
    --out .planning/build-history/<YYYY-MM-DD>-screening-report.md
```

Read the screening report. Categorize:

- **DUPLICATE** (top-1 score ≥ 3.0): drop. The library already covers it. Surface this list to the user as "what already exists" — it's value, not waste.
- **ADJACENT** (1.5 ≤ score < 3.0): partial coverage. NOT a new-skill candidate. Mark as a candidate for trigger-fix (see Step 7) instead.
- **GAP** (score < 1.5 or no result): real gap. These are the build candidates.

If `len(GAP) < N`, **do not pad with adjacent or duplicate candidates**. Tell the user: "Only K real gaps found from the candidate set. Build K, or expand topic hints?" Wait for direction.

---

## Step 3 — Plan (user checkpoint, single Q)

Present the GAP list to the user with:
- Proposed slug
- One-line scope summary
- Suggested owning agent (or `runtime-orphan` with reason)
- Estimated authoring effort (lines, expected references)

Ask: "Build all K, or subset?" Wait for explicit approval. Hermes principle: never silently choose direction at a branch point.

---

## Step 4 — Build (parallel sub-agent batches)

For each approved gap, in parallel batches of 5:

### 4a. Scaffold

```bash
echo y | python3 scripts/new_skill.py <domain> <skill-name> --strict --agent <agent-id>
# OR
echo y | python3 scripts/new_skill.py <domain> <skill-name> --strict --runtime-orphan --orphan-reason "<why>"
```

### 4b. Dispatch sub-agent to author content

Use `Agent` tool with `subagent_type: general-purpose`. Prompt template:

```
Author the FULL content for skill skills/<domain>/<skill-name>/.
The directory was scaffolded by new_skill.py with TODO markers.

Quality bar: match skills/devops/isv-license-management-and-trialforce/ for depth and tone.
Read it before writing. Each reference file should be 80-300 lines, the SKILL.md
should be 200-400 lines, the check script should be 150-300 lines.

CRITICAL CONSTRAINTS:
- Cite ONLY real Salesforce docs at developer.salesforce.com / help.salesforce.com /
  architect.salesforce.com. If you cannot verify a URL, OMIT IT — do not fabricate.
- Cite the relevant subset of standards/official-salesforce-sources.md.
- Apex / SOQL / metadata field names must be real. Verify against
  knowledge/imports/ before writing example code.
- All 6 deliverable files must end with TODO=0 (no unfilled TODO markers).
- DO NOT run skill_sync — that's the orchestrator's job.

Deliverables (all in skills/<domain>/<skill-name>/):
1. SKILL.md  (frontmatter with NOT-for clauses + 6+ triggers + Recommended Workflow)
2. references/examples.md  (4-6 concrete worked examples)
3. references/gotchas.md  (5-8 specific platform behaviors)
4. references/well-architected.md  (pillars + tradeoffs + anti-patterns + Official Sources Used)
5. references/llm-anti-patterns.md  (5-7 LLM mistakes specific to this domain)
6. scripts/check_<noun>.py  (stdlib-only checker)

Report on completion: file paths + line counts.
```

Run 5 agents in parallel via a single message with multiple `Agent` tool uses.

### 4c. Verify each agent's output

For each completed agent:
```bash
# Verify TODO=0 across all files
for f in skills/<domain>/<skill-name>/SKILL.md skills/<domain>/<skill-name>/references/*.md; do
    grep -c "TODO" "$f"
done
# All should print 0. If any prints > 0, the agent failed — move skill to .planning/scaffolds-pending/
# and skip it from this batch.
```

If an agent reports DUPLICATE (existing skill found at score > 2.0), do not author. Log to metrics as `duplicate_caught`.

If an agent fails with TODOs left, log as `agent_partial_fail` and move scaffold to `.planning/scaffolds-pending/<slug>/`.

---

## Step 5 — Auto-fix common agent issues

Agents historically produce these recoverable issues. Auto-fix before validate:

- **Pillar name** — Replace `Performance Efficiency` with `Performance` (AWS-WAF naming leaks):
  ```bash
  for f in skills/<domain>/<slug>/SKILL.md; do
      sed -i '' 's/Performance Efficiency/Performance/g' "$f"
  done
  ```
- **Missing tags block** — If the frontmatter has triggers but no tags, insert a tags block. Tags should match the skill's slug + 3-5 related concepts.
- **Missing template file** — If `templates/` is empty, create a minimal `<slug>-template.md` with a starter pattern.
- **`runtime_orphan_reason` field** — The schema doesn't accept this field. If `--runtime-orphan --orphan-reason` was used, the reason is recorded in `MASTER_QUEUE` notes; remove the field from the SKILL.md frontmatter.
- **Missing query fixture** — Add a fixture entry to `vector_index/query-fixtures.json` with the strongest natural-language phrasing for the skill.

---

## Step 6 — Sync + validate

```bash
python3 scripts/skill_sync.py --all 2>&1 | tail -3
python3 scripts/validate_repo.py 2>&1 | tail -3
```

If validate reports errors:
- Errors on the new skills → fix or move that skill to `.planning/scaffolds-pending/<slug>/`. Do not commit a broken skill.
- Errors on existing skills (regression caused by trigger-fix or registry refresh) → diagnose and fix. Roll back the trigger-fix if needed.

The validator's near-duplicate WARNINGS on the new skills are expected if the new skill is in a domain with siblings. They are NOT errors and do not block commit. They are noted in the metrics.

---

## Step 7 — Trigger-fix wave (free leverage)

While the orchestrator is here, also process the ADJACENT candidates from Step 2:

For each adjacent candidate (existing skill that nearly covers the gap):
1. Read the existing skill's `triggers:` list
2. Add 3-5 conversational trigger phrasings that better match the natural-language query that flagged the gap
3. Run `python3 scripts/skill_sync.py --skill skills/<domain>/<slug>` to refresh

Cap this at 5 trigger-fixes per build run to avoid scope creep.

---

## Step 8 — Commit (production-only)

```bash
git status --short
# Should show ONLY:
#   - skills/* (the new skills)
#   - registry/* (regenerated)
#   - vector_index/manifest.json + query-fixtures.json
#   - docs/SKILLS.md + docs/queue-progress.md (regenerated)
#   - agents/<agent-id>/AGENT.md (skill wirings)
# NOT:
#   - .planning/* (stays local)
#   - evals/measurement/REPORT.md or any session artifact
#   - /tmp/* archives
```

If anything in the staging area matches a pattern in `.gitignore`'s "Session artifacts" section, **STOP AND ASK** — do not commit it.

Commit message format:

```
skills: ship N new A++ skills [+ M trigger-fixes if any]

## N new skills (~<TOTAL_LINES> lines)

<bulleted list of <domain>/<slug>>

## Trigger-fixes on existing skills (if applicable)

<bulleted list>

## Verification

- gap-screener result: <DUP_COUNT> dup, <ADJ_COUNT> adjacent, <GAP_COUNT> gap
- agent failure rate: <FAIL_RATE>% (M agents partial / N dispatched)
- duplicates caught: <COUNT>

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
```

---

## Step 9 — Self-eval and metric capture

Append run metrics to `.planning/build-history/<YYYY-MM-DD>-build.json`:

```json
{
  "date": "2026-05-08",
  "command": "/build-skills 10 agentforce data-cloud",
  "duration_minutes": 47,
  "candidates_proposed": 30,
  "candidates_screened": {"DUPLICATE": 18, "ADJACENT": 8, "GAP": 4},
  "skills_shipped": 4,
  "skills_partial_pending": 0,
  "trigger_fixes_shipped": 5,
  "agent_failure_rate": 0.10,
  "duplicates_caught_in_screen": 18,
  "duplicates_caught_in_authoring": 0,
  "validate_warnings": 5,
  "validate_errors": 0,
  "lessons_for_next_run": [
    "agentforce candidate generation produced too many duplicates (12/15 DUP) — narrow with subdomain hints next time",
    "1 agent missed tags block (auto-fixed) — add explicit tags reminder to author prompt"
  ]
}
```

Then output a summary to the user:

```
✅ /build-skills run complete

Requested: <N>
Shipped: <K>  (clean commit on main, ready to push)
Trigger-fixes: <M>
Skipped (duplicates): <DUP>
Partial pending: <P>  (in .planning/scaffolds-pending/)

Quality gates:
- Validate: 0 errors, <W> warnings
- All agents reported with cited official sources
- Push: <pending|done>

Lessons captured for next run in .planning/build-history/
```

---

## When this command DOES NOT apply

- **Single skill, well-known scope** — use `/new-skill` for one-off authoring.
- **Bug fix on existing skill** — edit directly + `skill_sync --skill <path>`.
- **Trigger-fix only** — use the inline pattern in Step 7 standalone (no scaffolding needed).
- **Documentation update** — direct edit, no orchestrator needed.

## Failure modes and recovery

- **Pre-flight fails** — repo isn't clean; do not auto-fix; tell the user what's dirty and let them decide.
- **All candidates are DUPLICATE** — library is saturated for the topic area. Tell the user; suggest trigger-fixes instead.
- **All authoring agents fail** — likely a schema or scaffold issue; pause and read the most recent agent's output to diagnose.
- **Validate fails after auto-fix attempts** — move the offending skill to `.planning/scaffolds-pending/` and continue with the rest. Do not block the whole commit on one bad skill.
- **Commit hook rejects** — read the hook's error, NOT a generic "fix or skip." Common causes: missing query fixture, runtime_orphan_reason field, missing tags. Re-run the auto-fix pass (Step 5).

## Improvements from prior runs

This command was authored 2026-05-08 from session lessons documented in `.planning/build-history/`. Each run should:
1. Read the last 5 entries in `.planning/build-history/`
2. If any "lessons_for_next_run" entry repeats across 3+ runs, propose a permanent fix to this command (not a band-aid in the run)
3. Surface the proposed fix to the user at session end

This is the self-improvement loop. The command IS NOT static.
