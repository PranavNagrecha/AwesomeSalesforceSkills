---
id: task-mapper
class: build
version: 1.0.0
status: stable
requires_org: false
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-16
dependencies:
  shared:
    - AGENT_RULES.md
---
# Task Mapper Agent

## What This Agent Does

Maps the complete task universe for a given Salesforce Cloud × Role cell. Researches official Salesforce docs and Trailhead to identify every distinct practitioner task that role performs in that cloud. Compares against existing skills. Files each confirmed gap as an ask in the release plan (`RELEASES.yaml`) with `python3 scripts/release_plan.py add`. Does NOT build skills — it only adds asks to the plan.

**Scope:** One Cloud × Role cell per invocation. Output is new release-plan asks, not skill content.

---

## Activation Triggers

- A maintainer asks for one Cloud × Role cell to be mapped (there is no slash command; point the AI at this file)

---

## Mandatory Reads Before Starting

1. `RELEASES.yaml` — header comment only (size vocabulary and slotting); read planned items through `python3 scripts/release_plan.py status`, never by parsing the file
2. `standards/source-hierarchy.md` — Tier 1 and Tier 2 sources to search
3. `AGENT_RULES.md` — skill naming and domain conventions

---

## Orchestration Plan

### Step 1 — Take the cell

From the maintainer's request, extract:
- Cloud (e.g. Sales Cloud, Service Cloud, Core Platform)
- Role (Admin, BA, Dev, Data, Architect)
- Any research instructions

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

- `has_coverage: true` → mark as DUPLICATE in working list. Do not add it to the plan.
- `has_coverage: false` → confirmed gap. File it in Step 5.

Also run `python3 scripts/release_plan.py status` and drop any gap that is already a planned item.

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

### Step 5 — File each gap in the release plan

Run `python3 scripts/release_plan.py add --help` once to confirm the flags, then, for each confirmed gap:

```bash
python3 scripts/release_plan.py add --size S --title "<domain>/<skill-name-kebab-case>" \
  "<one sentence: when to use + NOT for exclusion>"
```

Use `--size M` for a skill that needs a day of research; never `L` for a single skill.

Skill naming rules (from AGENT_RULES.md):
- All lowercase kebab-case: `case-assignment-rules-setup`
- Include cloud qualifier only if ambiguous: `sales-cloud-territory-management` not just `territory-management`
- Match domain conventions: `admin/`, `apex/`, etc.

### Step 6 — Check the plan and commit

```bash
python3 -m pytest tests/test_releases.py -q
git add RELEASES.yaml
git commit -m "research(<cloud>): map <Role> task universe

Identified N tasks. N_new confirmed gaps added to RELEASES.yaml.
N_existing already covered (DUPLICATE).
Cloud: <cloud>
Role: <role>

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Quality Rules for Task Mapping

- Every filed ask must name a skill that follows kebab-case and is unique in the repo
- Every filed ask must include "NOT for..." — without it, the skill builder cannot scope correctly
- Do not add tasks that are already planned items in `RELEASES.yaml`, even if not yet built
- Minimum 5 tasks per Cloud × Role cell for a major cloud (Sales, Service, Experience). If you find fewer than 5, the research was too shallow — go back to Step 2.
- Maximum reasonable tasks per cell: 20. If you find more than 20, group related tasks.

---

## Anti-Patterns

- Never add a task that is purely a feature description — every task is an action with an output
- Never add tasks that are too granular (setting one checkbox = not a skill)
- Never skip the coverage check — duplicate skills waste build time and confuse retrieval
- Never finish without committing `RELEASES.yaml` after the plan's tests pass
- Never research two cells in one invocation — one cell at a time, always
