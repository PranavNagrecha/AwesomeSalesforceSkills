# /run-queue — Autonomous Skill Queue Runner

Runs the next task from `MASTER_QUEUE.md` end-to-end with no human input.
Reads the queue, finds the first incomplete task, executes it fully, marks it done, commits, and exits.
The next invocation picks up the next task automatically.

---

## Step 0 — Configure git push (run once at session start)

The CCR environment proxies git through a local service that may block pushes.
Before doing any work, reconfigure the remote to use the authenticated HTTPS URL:

```bash
git remote set-url origin https://github.com/PranavNagrecha/AwesomeSalesforceSkills.git
git config user.email "agent@sfskills.ai"
git config user.name "SfSkills Agent"
```

Then verify push works:
```bash
git push origin main --dry-run 2>&1
```

If the dry-run fails with 403, the environment does not have write credentials.
In that case: commit locally, then use the GitHub MCP `push_files` tool to upload
only the **text files** that changed (skip binary files: `*.sqlite`, `*.pyc`, `__pycache__/`).
The `chunks.jsonl` and `lexical.sqlite` in `vector_index/` will be regenerated on the
next run via `python3 scripts/skill_sync.py --all` — do not attempt to push them via MCP.

**Note:** `lexical.sqlite` is listed in `.gitignore` (file size grows past GitHub's 50 MB limit).
If the local index is missing or stale, regenerate it before running any search:
```bash
python3 scripts/skill_sync.py --all
```

---

## Step 1 — Read the Queue

```bash
cat MASTER_QUEUE.md
```

Find the **first row** where Status is `TODO` or `RESEARCH`.
Read the entire row: Status, Skill Name (or Research Task), Description, Cloud, Role, Domain.

If no TODO or RESEARCH rows exist → the queue is complete. Print "QUEUE COMPLETE" and stop.

---

## Step 2 — Branch on Task Type

### If the task is RESEARCH

Goal: populate the empty skill rows for a Cloud × Role cell.

**2a. Mark in-progress**
Edit MASTER_QUEUE.md: change `RESEARCH` → `IN_PROGRESS` on that row. Add timestamp.

**2b. Web search — ground everything in official docs**
Search for: `"Salesforce <Cloud> <Role> tasks site:help.salesforce.com OR site:developer.salesforce.com OR site:trailhead.salesforce.com"`

Also search: `"Salesforce <Cloud> <Role> Trailhead trail"`

Read the top results. Extract every distinct practitioner task the Role performs in that Cloud.

**2c. Check existing coverage**
For each task identified, run:
```bash
cd /Users/pranavnagrecha/VS\ Code/Personal/SfSkills && python3 scripts/search_knowledge.py "<task>" 2>/dev/null
```
If `has_coverage: true` → skip it (mark DUPLICATE in your working list).
If `has_coverage: false` → it is a confirmed gap.

**2d. Insert TODO rows**
For each confirmed gap, insert a new row into the correct table in MASTER_QUEUE.md:
```
| TODO | <skill-name-kebab-case> | <one-line description. Must include "NOT for ..."> | |
```
Use the domain folder that matches the Role:
- Admin → `admin`
- BA → `admin` (BA skills live in admin domain)
- Dev → use the most specific domain: `apex`, `lwc`, `flow`, `integration`, `devops`
- Data → `data`
- Architect → `architect` (skills live in `skills/architect/` with `category: architect`)

**2e. Mark DONE**
Edit MASTER_QUEUE.md: change `IN_PROGRESS` → `DONE` on the research row.

**2f. Commit and push**
```bash
git add MASTER_QUEUE.md
git commit -m "research: map <Cloud> × <Role> task universe

Identified N confirmed gaps. Added TODO rows for:
- <skill-1>
- <skill-2>
...

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

Then push — try `git push` first; if it returns a non-zero exit code or 403, use `gh`:
```bash
git push origin main || gh repo sync PranavNagrecha/AwesomeSalesforceSkills --source main --force
```

**Stop. The next invocation will pick up the first TODO row.**

---

### If the task is TODO

Goal: build a complete, validated skill package.

**2a. Mark in-progress**
Edit MASTER_QUEUE.md: change `TODO` → `IN_PROGRESS` on that row. Add timestamp.
```bash
git add MASTER_QUEUE.md && git commit -m "wip: start <skill-name>"
git push origin main || gh repo sync PranavNagrecha/AwesomeSalesforceSkills --source main --force
```

**2b. Check coverage and load local documentation (mandatory — do not skip)**

First check if the skill already exists:
```bash
python3 scripts/search_knowledge.py "<skill-name>" 2>/dev/null
```
If `has_coverage: true` and top result matches this skill exactly → mark DUPLICATE, commit, stop.

If `has_coverage: false` or results are unrelated → proceed.

Then search local official documentation before any web search:
```bash
python3 scripts/search_knowledge.py "<skill-topic>" 2>/dev/null
python3 scripts/search_knowledge.py "<key-term-from-skill>" 2>/dev/null
```

Read every chunk with score > 1.0. These are Tier 1 sources stored in `knowledge/imports/` — always accessible, never blocked. Use them as the primary research input. Only search the web for gaps not covered locally.

**2c. Read official sources**
```bash
cat standards/official-salesforce-sources.md
```
Identify the official Salesforce docs for this skill's domain and cloud.
These are the ONLY sources you may use for factual claims. Do not use training data alone.

**2d. Web search for current official content**
Search: `"Salesforce <skill topic> site:help.salesforce.com OR site:developer.salesforce.com"`
Read the top 2-3 results. Extract:
- Exact platform behavior (with version if available)
- Known limits and restrictions
- Non-obvious gotchas
- Common mistakes

**2e. Scaffold the skill package**
```bash
cd /Users/pranavnagrecha/VS\ Code/Personal/SfSkills
python3 scripts/new_skill.py <domain> <skill-name>
```
This creates the full package structure with TODO markers. Do not write files manually.

**2f. Fill every TODO marker — this is the core work**

Fill in order:

**SKILL.md**
- `description`: One sentence covering when to use this skill, 3+ trigger keywords, and at least one "NOT for ..." exclusion.
- `salesforce-version`: Use "Spring '25+" unless the skill is version-specific.
- `well-architected-pillars`: Choose from Security, Reliability, Scalability, Operational Excellence, User Experience.
- `tags`: 4-6 lowercase kebab-case tags.
- `triggers`: 3+ natural-language phrases a practitioner would actually type (10+ chars each). Write them as symptoms, not feature names. E.g. "how do I add a new field to an object" not "custom field".
- `inputs`: What the agent/user needs to provide before this skill can execute.
- `outputs`: What artifact or guidance this skill produces.
- Body (300+ words): Structure as Mode 1 (build from scratch), Mode 2 (review/audit), Mode 3 (troubleshoot) where applicable. Include step-by-step guidance an AI can follow without asking the user for clarification. Every factual claim must be traceable to an official source.
- `## Recommended Workflow`: 3–7 numbered steps that an AI agent or practitioner should follow when this skill activates. Write as directives ("Verify the sharing model", "Run the checker script"), not explanations. This section tells the consuming agent what to DO, not what to KNOW.

**references/examples.md**
- 2+ real examples. Each must have: Scenario, Problem, Solution, Why it works.
- No placeholder scenarios. Use realistic Salesforce org situations.

**references/gotchas.md**
- 3+ non-obvious platform behaviors that catch practitioners off guard.
- Each must be grounded in official docs or known platform behavior.
- Format: What happens → Why → How to avoid.

**references/well-architected.md**
- Map the skill to Well-Architected pillars.
- `## Official Sources Used` section must list at least one real official Salesforce URL.
- Do not delete the pre-seeded sources. Add usage context to them.

**references/llm-anti-patterns.md**
- 5+ mistakes AI coding assistants commonly make in this skill's domain.
- Each entry must have: What the LLM generates wrong, Why it happens (e.g. Java bleed, hallucinated API, training data bias), Correct pattern with code, Detection hint (regex or keyword).
- Think about what Claude, Copilot, or Cursor would get wrong when generating code or config for this topic. Common categories: hallucinated methods/APIs, wrong syntax from adjacent languages, missing security enforcement, incorrect governor limit assumptions, outdated API versions.

**scripts/check_*.py**
- Implement actual validation logic. stdlib only — no pip dependencies.
- Must be runnable: `python3 scripts/check_<noun>.py`
- Check for the most common mistake this skill prevents.

**templates/<skill-name>-template.md**
- A fill-in-the-blank output template the AI produces for the user.
- Must be immediately usable — not a meta-template with instructions to the author.

**2g. Sync and validate**
```bash
cd /Users/pranavnagrecha/VS\ Code/Personal/SfSkills
python3 scripts/skill_sync.py --skill skills/<domain>/<skill-name>
```
Fix every ERROR reported. Do not use `--skip-validation`. Re-run until clean.

**2h. Add query fixture**
```bash
python3 scripts/search_knowledge.py "<natural language query>" --json 2>/dev/null
```
Confirm the skill appears in top 3 results for a query a real practitioner would type.
Then add to `vector_index/query-fixtures.json`:
```json
{
  "query": "<the query you tested>",
  "domain": "<domain>",
  "expected_skill": "<domain>/<skill-name>",
  "top_k": 3
}
```

**2i. Final validation**
```bash
python3 scripts/validate_repo.py
```
Must exit 0. If not, fix all errors and re-run. Do not proceed until this passes.

**2j. Mark DONE and update Progress Summary**
Edit the skill row: change `IN_PROGRESS` → `DONE`.

Then update the Progress Summary table at the top of MASTER_QUEUE.md:
- Increment **Skills Done** by 1
- Decrement **TODO** by 1
for the matching Phase row.

```bash
# Quick count to verify your numbers are correct
grep -c "^| DONE" MASTER_QUEUE.md
grep -c "^| TODO" MASTER_QUEUE.md
```

Also update README.md:
- Count total skills: `find skills/ -name "SKILL.md" | wc -l`
- Update the "**N skills built**" line with the new total
- Update the domain count in the Covered Skills table for the domain you just added to

**2k. Commit and push everything**
```bash
git add skills/<domain>/<skill-name>/ registry/ vector_index/ docs/SKILLS.md MASTER_QUEUE.md
git commit -m "feat(<domain>): add <skill-name> skill [<Cloud> × <Role>]

<one sentence describing what the skill covers>

Official sources: <primary doc URL>

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
git push origin main || gh repo sync PranavNagrecha/AwesomeSalesforceSkills --source main --force
```

**Stop. The next invocation picks up the next task.**

---

## Error Handling

**If `new_skill.py` fails:**
Read the error. Fix the input (domain name or skill name) and retry once.
If it fails again, mark the row BLOCKED with a note and move on.

**If `skill_sync.py` exits non-zero:**
Read every ERROR line. Fix each one in the skill files. Re-run.
Do not mark DONE until sync exits clean.

**If `validate_repo.py` exits non-zero:**
Only ERRORs cause a non-zero exit. Read every ERROR line, fix each one, re-run.
WARNs are advisory — they print but do not block. You do not need to fix WARNs before committing.
Do not commit until this exits 0 (zero ERRORs).

**If `git push` returns 403 or non-zero:**
```bash
gh repo sync PranavNagrecha/AwesomeSalesforceSkills --source main --force
```
`gh` is available in this environment and bypasses the local proxy. Use it as the fallback for every push.

**If web search returns no useful official docs:**
Do not write the skill from training data alone.
Mark the row BLOCKED with note: "No official source found for <topic>. Manual research needed."
Commit the BLOCKED status and move to next task.

**If a skill overlaps heavily with an existing skill:**
Mark the row DUPLICATE. Add a note: "Covered by skills/<domain>/<existing-skill>."
Do not create a duplicate.

---

## Parallel Mode (Multiple Skills Per Run)

Each skill takes ~8 minutes to build. Builds run in parallel so wall clock time is ~8 min (longest build) + ~2 min per skill for sequential sync. 10 skills = ~28 min total — well within the 60 min window. Use parallel mode to fill that window instead of building one skill and sitting idle.

**Core model: builds are parallel, syncs are sequential.**
- **Build phase**: multiple skills built simultaneously — each builder only touches its own `skills/<domain>/<skill>/` folder, so there are no write conflicts between builders in different domains.
- **Sync phase**: `skill_sync.py` writes to shared `registry/` and `vector_index/` — must run one skill at a time, in sequence.

**Safety rule: only run builders in parallel for tasks from DIFFERENT domains.**
Two admin skills, two apex skills, etc. must be built sequentially within their domain (their `skills/<domain>/` folder is shared). Skills from different domains are safe to build in parallel.

### How to run parallel

**Step P1 — Claim up to 6 tasks**
```bash
grep "^| TODO" MASTER_QUEUE.md | head -30
```
Select up to 6 TODO tasks. Group them by domain:
- Pick at most 1 task per domain for the parallel build phase.
- If you need more than 1 from the same domain, queue them as a sequential second pass after the first batch syncs.

Mark all selected tasks IN_PROGRESS in one commit:
```bash
git add MASTER_QUEUE.md && git commit -m "queue: start parallel batch — <skill1>, <skill2>, ..."
git push origin main || gh repo sync PranavNagrecha/AwesomeSalesforceSkills --source main --force
```

**Step P2 — Build all skills concurrently**
Launch each skill builder as an independent sub-agent simultaneously.
Each sub-agent runs Steps 2b–2f (research → scaffold → fill content) for its skill only.
Do NOT run skill_sync.py yet — that happens in Step P3.

**Step P3 — Sync each completed skill sequentially**
For each skill that completed successfully, run sync one at a time:
```bash
python3 scripts/skill_sync.py --skill skills/<domain1>/<skill1>
python3 scripts/skill_sync.py --skill skills/<domain2>/<skill2>
# ... continue for each completed skill
```
Then validate once across all:
```bash
python3 scripts/validate_repo.py
```
Must exit 0 before proceeding.

**Step P4 — Handle partial failures**
If one or more builders failed (BLOCKED, no official source, scaffold error):
- Sync and commit only the skills that completed successfully.
- Update MASTER_QUEUE.md: mark completed skills DONE, failed skills BLOCKED (with reason).
- Do not hold back completed skills waiting for failed ones.
```bash
git add skills/<domain-that-succeeded>/ registry/ vector_index/ docs/SKILLS.md MASTER_QUEUE.md
git commit -m "feat: partial batch — <completed-skill1>, <completed-skill2> [BLOCKED: <failed-skill>]"
```

**Step P5 — Commit all successful skills, update queue**
```bash
git add skills/ registry/ vector_index/ docs/SKILLS.md MASTER_QUEUE.md
git commit -m "feat: parallel batch — <skill1>, <skill2>, ... [<Cloud>]

<one sentence per skill describing what it covers>

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
git push origin main || gh repo sync PranavNagrecha/AwesomeSalesforceSkills --source main --force
```

Mark completed rows DONE. Update the Progress Summary table (increment Skills Done by N, decrement TODO by N).

**When NOT to use parallel mode:**
- Fewer than 3 TODO tasks remain in the queue
- All remaining TODOs are in the same domain (build them sequentially instead)
- A task depends on output from another task in the same batch (e.g., a foundational skill that the others reference — build it first, then run a new parallel batch)

---

## What This Command Does NOT Do

- It does not ask the user for input. It is fully autonomous.
- It does not skip `validate_repo.py`. There are no shortcuts.
- It does not hand-edit `registry/`, `vector_index/`, or `docs/SKILLS.md`.
- It does not write content from memory alone. Every factual claim needs an official source.
- It does not process more than one task per invocation unless explicitly using Parallel Mode.
