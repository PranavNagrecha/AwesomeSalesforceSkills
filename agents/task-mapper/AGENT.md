# Task Mapper Agent

## What This Agent Does

Maps the complete task universe for a given Salesforce Cloud × Role cell. Researches official Salesforce docs and Trailhead to identify every distinct practitioner task that role performs in that cloud. Compares against existing skills. Inserts confirmed-gap TODO rows into `MASTER_QUEUE.md`. Does NOT build skills — it only populates the queue.

**Scope:** One Cloud × Role cell per invocation. Output is new TODO rows in MASTER_QUEUE.md, not skill content.

---

## Activation Triggers

- Orchestrator finds a RESEARCH row in `MASTER_QUEUE.md`
- Human runs `/map-tasks <cloud> <role>` to populate a new cell

---

## Mandatory Reads Before Starting

1. `MASTER_QUEUE.md` — the queue to populate
2. `standards/source-hierarchy.md` — Tier 1 and Tier 2 sources to search
3. `AGENT_RULES.md` — skill naming and domain conventions

---

## Orchestration Plan

### Step 1 — Read the RESEARCH row

From MASTER_QUEUE.md, extract:
- Cloud (e.g. Sales Cloud, Service Cloud, Core Platform)
- Role (Admin, BA, Dev, Data, Architect)
- Research instructions from the row

Mark the row `IN_PROGRESS` in MASTER_QUEUE.md. Commit.

### Step 2 — Map the task universe (Tier 1 + Tier 2)

Search the following in order:

**Official docs for this cloud:**
```
Search: "Salesforce <Cloud> <Role> guide site:help.salesforce.com"
Search: "Salesforce <Cloud> developer site:developer.salesforce.com"
Search: "Salesforce <Cloud> <Role> trailhead.salesforce.com"
```

**For each search result, extract every distinct practitioner task:**
A task is something the role DOES — an action with a start, steps, and an output.

Examples of tasks (not features):
- "Configure case assignment rules for Service Cloud" ✓
- "Set up entitlements and milestones" ✓
- "Case assignment rules" ✗ (feature name, not a task)

**Task extraction rules:**
- One task = one skill. If a task is too broad (10+ sub-tasks), split it.
- If a task only takes 3 clicks and has no gotchas, it is too small for a skill — combine with a related task.
- Tasks must be role-appropriate: Admin tasks involve Setup UI; Dev tasks involve code; Data tasks involve loads; BA tasks involve documents; Architect tasks involve decisions.

### Step 3 — Check every task against existing skills

For each task identified:

```bash
python3 scripts/search_knowledge.py "<task description>" --domain <domain>
```

- `has_coverage: true` → mark as DUPLICATE in working list. Do not add to queue.
- `has_coverage: false` → confirmed gap. Add to queue.

Also check `SKILLS_BACKLOG.md` for any overlapping planned skills not yet built.

### Step 4 — Determine domain folder for each gap

Map role → domain folder:
```
Admin role → admin
BA role → admin (BA skills live in admin domain)
Dev role → most specific: apex / lwc / flow / integration / devops
Data role → data
Architect role → architect
```

For cloud-specific topics:
- OmniStudio tasks → omnistudio
- Agentforce tasks → agentforce
- Security tasks → security

### Step 5 — Insert TODO rows into MASTER_QUEUE.md

For each confirmed gap, add a row to the correct table:

```markdown
| TODO | <skill-name-kebab-case> | <one sentence: when to use + NOT for exclusion> | |
```

Skill naming rules (from AGENT_RULES.md):
- All lowercase kebab-case: `case-assignment-rules-setup`
- Include cloud qualifier only if ambiguous: `sales-cloud-territory-management` not just `territory-management`
- Match domain conventions: `admin/`, `apex/`, etc.

Batch the TODO rows under the correct `### <Cloud> × <Role> Role` section in MASTER_QUEUE.md.

### Step 6 — Update progress summary

Update the Progress Summary table at the top of MASTER_QUEUE.md:
- Change the Skills Planned count for this Cloud
- Change status from RESEARCH to the count

### Step 7 — Mark RESEARCH row DONE and commit

```bash
git add MASTER_QUEUE.md
git commit -m "research(<cloud>): map <Role> task universe

Identified N tasks. N_new confirmed gaps added as TODO rows.
N_existing already covered (DUPLICATE).
Cloud: <cloud>
Role: <role>

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Quality Rules for Task Mapping

- Every TODO row must have a skill name that follows kebab-case and is unique in the repo
- Every TODO row description must include "NOT for..." — without it, the skill builder cannot scope correctly
- Do not add tasks that are already covered by `SKILLS_BACKLOG.md` even if not yet built — check that file too
- Minimum 5 tasks per Cloud × Role cell for a major cloud (Sales, Service, Experience). If you find fewer than 5, the research was too shallow — go back to Step 2.
- Maximum reasonable tasks per cell: 20. If you find more than 20, group related tasks.

---

## Anti-Patterns

- Never add a task that is purely a feature description — every task is an action with an output
- Never add tasks that are too granular (setting one checkbox = not a skill)
- Never skip the coverage check — duplicate skills waste build time and confuse retrieval
- Never mark a RESEARCH row DONE without committing the new TODO rows
- Never research two cells in one invocation — one cell at a time, always
