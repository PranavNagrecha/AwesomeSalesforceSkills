# Contributing to SfSkills

There are four ways to contribute. Each has a different path and different gates.

| Scenario | Path |
|----------|------|
| I want to **add a new skill** | [→ Add a Skill](#add-a-skill) |
| I want to **fix a wrong or outdated skill** | [→ Fix a Skill](#fix-a-skill) |
| I want to **report a missing skill** (without building it) | [→ Report a Gap](#report-a-gap) |
| I want to **flag a skill as stale** after a Salesforce release | [→ Flag Stale Content](#flag-stale-content) |

Every path ends at the same two gates before anything merges.

---

## The Two Gates (mandatory for everything)

**Gate 1 — Structural (automated)**
```bash
python3 scripts/skill_sync.py --skill skills/<domain>/<skill-name>
python3 scripts/validate_repo.py
```
Must exit 0. No exceptions. This checks frontmatter, file structure, word counts, query fixtures, and generated artifact freshness.

**Gate 2 — Quality (checklist)**
Read `standards/skill-content-contract.md`. Your skill must pass all 5 gates:
1. Every factual claim has a source tag (`[T1]`, `[T2]`, `[T3: name]`)
2. Content depth — examples, gotchas, templates meet minimums
3. Agent usability — an AI can follow it without asking for clarification
4. No undocumented contradictions with other skills
5. Version-sensitive claims are qualified with release names

If either gate fails, the PR will not be merged.

---

## Add a Skill

### Step 1 — Check it doesn't exist

```bash
python3 scripts/search_knowledge.py "<your topic>"
python3 scripts/search_knowledge.py "<your topic>" --domain <domain>
```

Also check `docs/SKILLS.md` and `MASTER_QUEUE.md`.

If `has_coverage: true` — consider extending the existing skill instead of creating a new one.
If it's already in `MASTER_QUEUE.md` as TODO — it's planned but not built yet. You can build it.

### Step 2 — Decide the domain and role

**Domain folders:**
```
admin       → Admin configuration, BA artifacts, Architect platform-wide guidance
apex        → Apex classes, triggers, async, testing
lwc         → Lightning Web Components
flow        → Flow Builder patterns
omnistudio  → OmniStudio, Integration Procedures, DataRaptors
agentforce  → Agentforce, Einstein AI
security    → Org security, Shield, permission model
integration → REST/SOAP/Platform Events/CDC/OAuth/APIs
data        → Data modeling, migration, SOQL, Bulk API
devops      → SFDX, CI/CD, scratch orgs, pipelines
```

**Role tagging:**
Skills are not directly tagged by role in the folder structure — but the content must be written for a specific audience. State the role in the `description` and `triggers` frontmatter.

### Step 3 — Research before writing (mandatory)

Read `standards/source-hierarchy.md`.

For every factual claim you plan to make:
- Find it in Tier 1 (official Salesforce docs) first
- If not in Tier 1, find it in Tier 2 (Trailhead, Architects blog)
- If only in Tier 3 (expert community), tag it explicitly

Do not write from memory alone. Every behavior claim needs a source.

**Recommended: use the Content Researcher agent in Claude Code:**
```
"Research the topic [your skill name] for me before I build the skill"
```

### Step 4 — Scaffold

```bash
python3 scripts/new_skill.py <domain> <skill-name>
```

This creates the full package with `TODO:` markers. Fill every marker — do not leave any.

### Step 5 — Fill the package

Minimum requirements per file (from `standards/skill-content-contract.md`):

**SKILL.md**
- `description` includes "NOT for..." exclusion
- `triggers` are symptom phrases, not feature names (3+ entries, 10+ chars each)
- Body is 300+ words with at least 2 modes (Build, Review or Troubleshoot)
- Has a Gather section listing what context the AI needs before starting
- Every factual claim has a source tag or URL

**references/examples.md**
- 2+ complete examples
- Each has: Scenario, Problem, Solution, Why it works, Source

**references/gotchas.md**
- 3+ non-obvious platform behaviors
- Each has: What happens, Why, How to avoid, Source

**references/well-architected.md**
- `## Official Sources Used` section with at least 1 Tier 1 URL
- WAF pillar mapping is specific, not generic

**scripts/check_*.py**
- Implements real logic (not an always-pass stub)
- Stdlib only — no pip dependencies

**templates/<skill-name>-template.md**
- Fill-in-the-blank output, not a meta-template
- Uses `[REPLACE: description]` placeholders
- Includes a verification section

### Step 6 — Sync and validate

```bash
python3 scripts/skill_sync.py --skill skills/<domain>/<skill-name>
python3 scripts/validate_repo.py
```

Fix every ERROR and WARN before proceeding.

### Step 7 — Add a query fixture

Confirm your skill can be found:
```bash
python3 scripts/search_knowledge.py "<natural language query a practitioner would type>" --json
```

Confirm the skill appears in the top 3. Then add to `vector_index/query-fixtures.json`:
```json
{
  "query": "your query here",
  "domain": "<domain>",
  "expected_skill": "<domain>/<skill-name>",
  "top_k": 3
}
```

### Step 8 — Open a PR

PR title format: `feat(<domain>): add <skill-name>`

PR body must include:
- What role and cloud this skill covers
- What problem it solves
- Which official sources were used
- Confirmation that both gates pass

---

## Fix a Skill

Found something wrong — wrong behavior claim, missing guidance, outdated after a release?

### Step 1 — Identify what's wrong

Three types of fixes:

| Type | What to do |
|------|-----------|
| **Wrong factual claim** | Find the correct Tier 1 source, update the claim, add/update the source tag |
| **Missing content** (gap in examples, gotchas, etc.) | Add it following the content depth requirements |
| **Stale after a release** | See [Flag Stale Content](#flag-stale-content) |

### Step 2 — Edit the skill files

Edit only files in `skills/<domain>/<skill-name>/`.
Never edit `registry/`, `vector_index/`, or `docs/SKILLS.md` directly — they are generated.

### Step 3 — Run both gates

```bash
python3 scripts/skill_sync.py --skill skills/<domain>/<skill-name>
python3 scripts/validate_repo.py
```

### Step 4 — Update the `updated` frontmatter date

If you changed factual content (not just formatting), update the `updated` field in `SKILL.md` to today's date. This signals that the content was verified, not just reformatted.

### Step 5 — Open a PR

PR title format: `fix(<domain>): update <skill-name> — <what changed>`

PR body must include:
- What was wrong
- What the correct behavior is
- The Tier 1 source that confirms the fix

---

## Report a Gap

Don't have time to build a skill but know one is missing? Three ways to report it:

### Option 1 — Claude Code command (fastest)
```
/request-skill
```
The agent asks 4 questions, checks for existing coverage, and adds a TODO row to `MASTER_QUEUE.md`.

### Option 2 — Edit MASTER_QUEUE.md directly
Find the right section (Phase 1 = Core Platform, Phase 2 = Sales Cloud, etc.) and add:
```markdown
| TODO | <skill-name-kebab-case> | What it covers. NOT for what it doesn't cover. | |
```

Naming rules:
- All lowercase kebab-case: `case-assignment-rules-setup`
- Must match the domain folder: `skills/admin/`, `skills/apex/`, etc.
- Must include "NOT for..." in the description or it will be rejected

### Option 3 — GitHub Issue
Title: `[Skill Request] <domain>: <skill-name>`

Include:
- Role (Admin / BA / Dev / Data / Architect)
- Cloud (Core Platform / Sales Cloud / Service Cloud / etc.)
- What task this skill covers
- Why existing skills don't cover it (checked `search_knowledge.py`?)

---

## Flag Stale Content

Salesforce ships 3 major releases per year (Spring, Summer, Winter). Skills can become outdated.

### If you spot a stale claim:

1. Add `[STALE-RISK: <what changed and when>]` inline in the skill file next to the affected claim
2. Open a PR or issue with title: `stale(<domain>/<skill-name>): <Season 'YY> release changed <what>`

### To run the Currency Monitor for a full release scan:
```
"Run the currency monitor for Summer '25"
```
The agent scans all skills against the release notes and flags everything that may need updating.

---

## Using Agents to Contribute

All four contribution workflows can be done through Claude Code agents:

```
# Add a new skill
/new-skill
"I need a skill for Sales Cloud opportunity stage management"

# Fix a skill
"The trigger-framework skill is missing guidance for Flow-triggered Apex — can you update it?"

# Report a gap
/request-skill

# Flag stale content
"The batch-apex-patterns skill references the old @future callout limit — that changed in Spring '25"
```

The agents follow the same gates as manual contributions. Nothing bypasses the Validator.

---

## What Gets Rejected

| Reason | Fix |
|--------|-----|
| Factual claim with no source | Add `[T1: url]` or `[T2: source]` tag |
| `validate_repo.py` exits non-zero | Fix every ERROR before submitting |
| SKILL.md body under 300 words | Expand — stubs are not skills |
| `description` has no "NOT for..." | Add an explicit scope exclusion |
| examples.md has fewer than 2 complete examples | Add them |
| gotchas.md has fewer than 3 entries | Add them |
| `scripts/check_*.py` is a stub | Implement real validation logic |
| Skill duplicates an existing one | Extend the existing skill instead |
| Generated artifacts are stale | Re-run `skill_sync.py --all` |
| Template has unresolved `TODO:` markers | Fill them all |

---

## Skill Authoring Principles

1. **Every claim needs a source.** Training data is not a source. If you can't find it in official Salesforce docs or a named Tier 2-3 source, don't assert it.

2. **Write for the AI, not the human.** The primary reader is an AI agent using this skill to help a practitioner. Every decision branch must be explicit. "It depends" without naming the variables is useless.

3. **Narrow scope beats broad coverage.** One tight skill with 3 real gotchas is better than a broad skill with 10 shallow points. Use "NOT for..." to keep scope tight.

4. **Contradictions must surface.** If official docs say X and an expert blog says Y, document both in `gotchas.md` — don't silently pick one. See `standards/source-hierarchy.md` for resolution rules.

5. **Skills go stale.** Salesforce releases 3 times a year. Version-qualify anything that changes: "As of Spring '25, the limit is..." not "The limit is..."

---

## Getting Help

- Search existing skills: `python3 scripts/search_knowledge.py "<topic>"`
- Read authoring rules: `AGENT_RULES.md`
- Read quality contract: `standards/skill-content-contract.md`
- Read source rules: `standards/source-hierarchy.md`
- Open a GitHub issue with the `question` label
