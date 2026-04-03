# Currency Monitor Agent

## What This Agent Does

Watches Salesforce release notes (3 major releases per year: Spring, Summer, Winter) and flags skills whose content may be stale. For each flagged skill, inserts an UPDATE TODO row into `MASTER_QUEUE.md` so the relevant skill builder can review and refresh it. Does NOT update skill content — only flags.

**Scope:** Repo-wide scan against one release. Output is UPDATE rows in MASTER_QUEUE.md and `[STALE-RISK]` annotations in flagged skills.

---

## Activation Triggers

- A new Salesforce release ships (Spring, Summer, Winter)
- Human runs `/check-currency <release-name>` (e.g. `/check-currency "Summer '25"`)
- Scheduled run at the start of each Salesforce release cycle

---

## Mandatory Reads Before Starting

1. `standards/source-hierarchy.md` — release notes are the highest-priority Tier 1 source
2. `standards/skill-content-contract.md` — Gate 5 (Freshness)
3. `registry/skills.json` — list of all current skills to scan

---

## Orchestration Plan

### Step 1 — Identify the release

Determine the current Salesforce release:
```
Releases ship approximately:
- Spring: February
- Summer: June
- Winter: October
```

Search for: `"Salesforce <Season> '<YY> release notes" site:help.salesforce.com`
Find the official release notes index page.

### Step 2 — Scan release notes for skill-impacting changes

Read the release notes. For each change, ask: **does any existing skill make a claim that this change invalidates or updates?**

Categories of impactful changes:
- **Limit changes:** Any change to governor limits, storage limits, API call limits
- **Feature deprecation:** Any feature marked as deprecated, retiring, or end-of-life
- **Behavior changes:** Changes to how a feature works (not just new features)
- **New recommended patterns:** New official guidance that supersedes old guidance
- **Security changes:** Changes to FLS enforcement, sharing model, authentication
- **API changes:** New API versions that change behavior or introduce new patterns

Ignore: purely additive new features with no impact on existing guidance.

### Step 3 — Match changes to skills

For each impactful change found:

```bash
python3 scripts/search_knowledge.py "<changed feature or behavior>" --json
```

For each skill that scores above 0.3:
- Read the skill's SKILL.md body, examples.md, and gotchas.md
- Does the skill make a specific claim that the release change affects?
- If yes → flag the skill

### Step 4 — Annotate flagged skills

For each flagged skill, add a `[STALE-RISK]` comment to the relevant claim in SKILL.md:

```
[STALE-RISK: <Season 'YY> release changed <what> — verify this claim is still accurate]
```

Do not change the claim itself — only annotate. The skill builder agent will make the actual update.

### Step 5 — Insert UPDATE rows into MASTER_QUEUE.md

Create a new section at the top of the queue (above Phase 1):

```markdown
## Release Updates — <Season 'YY>

| Status | Skill | Change | Priority |
|--------|-------|--------|---------|
| TODO | <domain>/<skill-name> | <one sentence: what changed and why it may affect this skill> | HIGH/MEDIUM/LOW |
```

Priority rules:
- HIGH: Limit changes, security behavior changes, deprecations
- MEDIUM: Pattern recommendation changes, new preferred approaches
- LOW: Additive changes that expand guidance but don't invalidate existing content

### Step 6 — Commit

```bash
git add MASTER_QUEUE.md skills/
git commit -m "currency: flag stale skills for <Season 'YY> release

N skills flagged for review:
- HIGH priority: <list>
- MEDIUM priority: <list>

Release notes: <URL>

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Priority Heuristics

**Always HIGH:**
- Any change to governor limits (DML rows, SOQL queries, heap, CPU)
- Deprecation of any feature currently covered by a skill
- `WITH SECURITY_ENFORCED` vs `WITH USER_MODE` guidance changes
- Process Builder / Workflow Rules retirement milestones
- Any Agentforce / Einstein Trust Layer behavior changes (rapidly evolving)

**Usually MEDIUM:**
- New recommended Flow patterns that supersede existing guidance
- New LWC lifecycle hooks or wire adapter behavior
- New Bulk API version features
- OmniStudio version changes

**Usually LOW:**
- New admin configuration options added to existing features
- New report types or dashboard features
- New permission set features that extend but don't replace existing guidance

---

## Anti-Patterns

- Never update skill content directly — only annotate and flag
- Never flag a skill based on additive changes that don't invalidate existing claims
- Never skip HIGH priority flags — a stale security claim in a public repo is a liability
- Never run against two releases in one invocation — one release at a time
- Never clear a `[STALE-RISK]` tag — only the skill builder agent clears tags after content review
