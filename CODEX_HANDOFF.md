# CODEX_HANDOFF.md
# Codex Agent Briefing — SfSkills Repository

**Read this document completely before doing any work.**
**Then read AGENT_RULES.md. Then read SKILLS_BACKLOG.md.**
**Do not touch a single file until you have read all three.**

---

## What This Repo Is

This is a Salesforce skill framework. You are building a structured, searchable library of Salesforce practitioner skills. Each skill is a directory under `skills/<domain>/<skill-name>/` containing:

- `SKILL.md` — canonical skill content and metadata (frontmatter)
- `references/examples.md` — real-world examples
- `references/gotchas.md` — non-obvious platform behaviors
- `references/well-architected.md` — WAF framing + **official sources** (pre-seeded)
- `templates/` — at least one reusable template file
- `scripts/` — at least one stdlib-only Python checker

When you finish a skill, the system generates machine-readable registry and retrieval artifacts automatically. You never touch files in `registry/`, `vector_index/`, or `docs/` directly.

---

## Your Job

1. Pick the next TODO item from `SKILLS_BACKLOG.md`
2. Build it completely and correctly
3. Mark it done
4. Repeat

You are not designing the system. You are filling in the skills. The system is built. Follow the process exactly.

---

## Non-Negotiable Rules

### Rule 1: Always scaffold. Never write from scratch.

```bash
python3 scripts/new_skill.py <domain> <skill-name>
```

This creates all required files with the correct structure. You fill the TODOs. If you write files from scratch instead, you will miss required sections, get frontmatter wrong, and waste cycles fixing validation failures.

### Rule 2: Sync validates first. Fix errors before moving on.

```bash
python3 scripts/skill_sync.py --skill skills/<domain>/<skill-name>
```

This runs validation before writing any artifact. If it reports ERRORs, you **must** fix every one before syncing succeeds. Do not use `--skip-validation`. Do not move to the next skill until this passes.

### Rule 3: Validate the whole repo after each skill.

```bash
python3 scripts/validate_repo.py
```

This checks your skill, all fixtures, and artifact freshness. It must exit 0. If it exits 1, fix every issue before committing.

### Rule 4: Read official docs. Every time. No exceptions.

**Your local RAG can be wrong. It can be outdated. It can be incomplete.**

Before writing any content for a skill, you MUST read the official Salesforce documentation listed in the skill's `official-docs:` field in `SKILLS_BACKLOG.md`. These are real URLs to the authoritative source. Open them. Read the relevant sections.

Every factual claim about Salesforce platform behavior, limits, APIs, or security must be grounded in official documentation. The official sources for your domain are also pre-seeded in `references/well-architected.md` when you scaffold — that is your starting point, not your ending point.

**Do not invent governor limits, API capabilities, or security behaviors. If you don't know the official answer, say so in the skill's content rather than guessing.**

Where to find official Salesforce documentation:
- Apex, SOQL, REST API, Bulk API, Platform Events: https://developer.salesforce.com/docs
- Help articles (Flow, Security, Admin): https://help.salesforce.com
- Architecture and WAF: https://architect.salesforce.com/docs
- LWC, Agentforce, OmniStudio: https://developer.salesforce.com/docs
- All source URLs by domain: see `## Official Salesforce Documentation Index` in SKILLS_BACKLOG.md

### Rule 5: No duplicate skills.

Before scaffolding, run:

```bash
python3 scripts/search_knowledge.py "<topic>" --domain <domain>
```

If `has_coverage: true` is returned, read the existing skill before creating a new one. The backlog notes fields already flag overlaps between skills (e.g. `apex-security-patterns` must NOT duplicate `soql-security`). Read those notes.

### Rule 6: Fill every TODO before syncing.

The scaffold generates files with `TODO:` markers throughout. Every single one must be replaced with real content. If you submit a sync with TODOs remaining, it will fail with explicit errors per unfilled marker. This is intentional. The validator counts them.

---

## Step-by-Step Workflow

### Step 1 — Claim the skill

Open `SKILLS_BACKLOG.md`. Find the first item with `status: TODO`.

Change it to:
```yaml
status:      IN_PROGRESS
agent:       Codex
started:     <ISO timestamp>
```

Commit this claim before starting:
```bash
git add SKILLS_BACKLOG.md
git commit -m "chore: claim <skill-name> IN_PROGRESS"
```

### Step 2 — Check coverage

```bash
python3 scripts/search_knowledge.py "<topic>" --domain <domain>
```

Read the output. If `has_coverage: true`, read the existing skill at the returned path. Understand what it covers and what it doesn't. The backlog notes tell you the intended differentiation. If you're satisfied the new skill is genuinely distinct, proceed.

### Step 3 — Scaffold

```bash
python3 scripts/new_skill.py <domain> <skill-name>
```

This creates:
```
skills/<domain>/<skill-name>/
├── SKILL.md                         ← pre-filled, all TODOs to replace
├── references/
│   ├── examples.md                  ← TODO structure
│   ├── gotchas.md                   ← TODO structure
│   └── well-architected.md          ← official sources PRE-SEEDED for domain
├── templates/<skill-name>-template.md
└── scripts/check_<noun>.py
```

The scaffold command will print a box of official doc URLs for the domain. **Do not skip reading them.**

### Step 3.5 — READ THE OFFICIAL DOCS (mandatory hard stop before writing)

This is not optional. This is not a suggestion. **Stop here before writing a single word of skill content.**

1. Find the `official-docs:` field for your skill in `SKILLS_BACKLOG.md`.
2. Open each URL in a browser or fetch it.
3. Read the sections relevant to your skill's scope.
4. Also check `## Official Salesforce Documentation Index` in SKILLS_BACKLOG.md for your domain.

**Why this matters:** Your local RAG can have wrong or outdated information. Official docs have the accurate governor limits, exact API signatures, and current platform behavior. A skill with wrong Salesforce facts is worse than no skill.

If a doc URL is broken or inaccessible, search https://developer.salesforce.com/docs or https://help.salesforce.com for the correct current URL.

### Step 4 — Check for SEEDED content

If the backlog item says `rag-source: SEEDED`, clone:

```bash
git clone https://github.com/PranavNagrecha/Salesforce-RAG /tmp/sf-rag
```

Browse the content relevant to your skill. Use it as a starting point for examples, gotchas, and well-architected notes. Do not copy it verbatim — adapt it to the skill's specific scope and add WAF framing.

### Step 5 — Fill SKILL.md

Open `skills/<domain>/<skill-name>/SKILL.md`. Every field in the frontmatter has a TODO. Replace them all:

**Frontmatter checklist:**
- `description` — one sentence, must include "NOT for ..." scope exclusion
- `well-architected-pillars` — pick from: Security, Performance, Scalability, Reliability, User Experience, Operational Excellence
- `triggers` — 3 to 6 natural-language symptom phrases (10+ chars each) that a practitioner would actually type when they need this skill. These are critical for retrieval routing.
- `tags` — 3 to 6 lowercase hyphenated keywords
- `inputs` — what context/info the skill needs to work
- `outputs` — what the skill produces (guidance, code, review findings, etc.)

**Body checklist (300+ words required):**
- Activation summary — 1-2 sentences on when this skill activates
- Before Starting — 2-3 context questions to answer first
- Core Concepts — 2-4 real Salesforce concepts, platform-specific, not generic
- Common Patterns — 2-3 patterns that solve the most frequent problems
- Decision Guidance — decision table with at least 3 rows
- Review Checklist — 5-7 verification steps
- Salesforce-Specific Gotchas — 3+ non-obvious platform behaviors
- Output Artifacts — table of what this skill produces
- Related Skills — links to complementary skills in this repo

### Step 6 — Fill references/

**examples.md** — at least 2 real examples. Each must have:
- A named scenario (not "Example 1")
- Context (what org state, what code, what requirement)
- Problem (what goes wrong without this skill's guidance)
- Solution (concrete code or config — no pseudocode)
- Why it works (the key insight)
- At least 1 anti-pattern with explanation

**gotchas.md** — at least 3 gotchas. Each must have:
- A specific name (not "Gotcha 1")
- What happens (the unexpected behavior)
- When it occurs (conditions that trigger it)
- How to avoid it (specific fix or prevention)

**well-architected.md** — official sources are pre-seeded. Add:
- Which WAF pillars apply and why (specific to this skill, not generic)
- Architectural tradeoffs practitioners face
- 2-3 anti-patterns this skill helps avoid

### Step 7 — Implement scripts/check_<noun>.py

The scaffold creates a stub. Replace the TODO with actual checks relevant to this skill. The script must:
- Be stdlib only (no pip dependencies)
- Accept `--help` and exit 0
- Accept `--manifest-dir` pointing to a metadata directory
- Parse relevant XML/JSON files and report real issues
- Return exit code 1 if issues found, 0 if clean

If the skill doesn't lend itself to static metadata checks, implement a configuration review script that validates common settings.

### Step 8 — Fill templates/

The scaffold creates a work template. Expand it to be actually useful for a practitioner applying this skill. Include:
- Relevant configuration sections
- Common code patterns (for code-based skills)
- Decision sections filled with guidance from SKILL.md

### Step 9 — Sync

```bash
python3 scripts/skill_sync.py --skill skills/<domain>/<skill-name>
```

Read every ERROR. Fix every ERROR. Re-run until it passes with 0 errors.

Common errors you will see:
- `description contains TODO marker` — you forgot to fill the description
- `triggers contains TODO marker` — replace placeholder trigger phrases with real ones
- `body contains N unfilled TODO marker(s)` — grep for "TODO:" in the body and replace them all
- `SKILL.md body has N words; minimum is 300` — add more substantive content
- `Official Sources Used section is empty` — the sources are pre-seeded but you may have deleted them; restore from `knowledge/sources.yaml`

### Step 10 — Add query fixture

Open `vector_index/query-fixtures.json`. Add an entry:

```json
{
  "query": "natural language query a practitioner would type",
  "domain": "<domain>",
  "expected_skill": "<domain>/<skill-name>",
  "top_k": 3
}
```

Verify it works:
```bash
python3 scripts/search_knowledge.py "<your query>" --domain <domain>
```

The skill must appear in the top 3 results. If it doesn't, try a different query or check if your triggers and tags are indexing the right terms.

### Step 11 — Full validation

```bash
python3 scripts/validate_repo.py
```

Must exit 0. Fix everything. This is the quality gate.

### Step 12 — Mark done and commit

Update `SKILLS_BACKLOG.md`:
```yaml
status:      DONE
completed:   <ISO date>
files:       <count of files in skill directory>
notes:       <one line describing what was built and any notable decisions>
```

Update the Progress Summary table at the top of SKILLS_BACKLOG.md.

Add a row to the Agent Handoff Log.

Commit everything:
```bash
git add skills/<domain>/<skill-name>/
git add registry/ vector_index/ docs/SKILLS.md
git add SKILLS_BACKLOG.md vector_index/query-fixtures.json
git commit -m "feat(<domain>): complete <skill-name> skill"
```

### Step 13 — Pick the next TODO and repeat

---

## Quality Bar

A skill is complete when:

- [ ] `validate_repo.py` exits 0
- [ ] No TODOs remain in any file in the skill directory
- [ ] SKILL.md body is 300+ real words (not counting TODO markers)
- [ ] At least 3 triggers are defined as real symptom phrases
- [ ] `references/well-architected.md` has official sources and real WAF content
- [ ] `scripts/check_<noun>.py` implements actual checks, not just the stub
- [ ] `templates/` file is useful to a practitioner (not just scaffold placeholders)
- [ ] `examples.md` has at least 2 named, concrete examples
- [ ] `gotchas.md` has at least 3 named, specific gotchas
- [ ] A query fixture exists and passes retrieval
- [ ] SKILLS_BACKLOG.md is updated to DONE with timestamp

---

## What Good Looks Like

Read `skills/apex/soql-security/` before starting. That skill is the quality benchmark:
- Specific, actionable content (not generic Salesforce advice)
- Real code patterns (not pseudocode)
- Named gotchas with precise platform behavior
- Decision table with real scenarios
- Official sources grounding every claim

Match that quality level. If your output would embarrass a senior Salesforce developer, rewrite it.

---

## What Will Get You Rejected

The validator enforces these. Fix them before committing:

- Any `TODO:` remaining in any file
- `description` missing "NOT for ..." clause
- `triggers` with fewer than 3 entries or entries under 10 chars
- SKILL.md body under 300 words
- `## Official Sources Used` absent or empty
- `scripts/check_<noun>.py` fails `--help` or has syntax errors
- `validate_repo.py` exits non-zero

---

## Domain Priority Order

Work in this order. P0 first, then P1, then P2.

1. **Apex** — APX-004 through APX-019 (P0 first)
2. **Security** — SEC-001 through SEC-012 (P0 first)
3. **Integration** — INT-001 through INT-013 (P0 first)
4. **LWC** — LWC-002 through LWC-014
5. **Flow** — FLW-002 through FLW-013 (P0 first)
6. **AgentForce** — AGT-001 through AGT-014 (P0 first)
7. **Data** — DAT-001 through DAT-013 (P0 first)
8. **OmniStudio** — OMS-002 through OMS-009
9. **DevOps** — DEV-001 through DEV-009
10. **Experience Cloud** — EXP-001 through EXP-007 (P0 first — guest user security is critical)
11. **Service Cloud** — SVC-001 through SVC-006 (P0 first)
12. **Admin** — ADM-016 through ADM-024

---

## If You Get Stuck

If you cannot complete a skill:

1. Mark it `BLOCKED` in SKILLS_BACKLOG.md with a specific note explaining where you stopped
2. Commit the partial work with `wip(<domain>): partial <skill-name> — blocked on <reason>`
3. Move to the next TODO item

Do not leave a skill in IN_PROGRESS without notes. The next agent needs to understand where you stopped.

---

## Final Note

The retrieval system built on top of these skills will be used by real practitioners to get real Salesforce guidance. Wrong information is worse than no information. The `has_coverage: false` signal exists precisely so the system can say "I don't know" rather than confidently giving bad advice.

Build accurate skills. Verify against official docs. The quality of this library is the quality of the product.

---

*Last updated: 2026-03-13 | Maintained by: Pranav Nagrecha | For questions, update this file.*
