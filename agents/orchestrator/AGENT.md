# Orchestrator Agent

## What This Agent Does

Reads `MASTER_QUEUE.md`, finds the next actionable task, routes it to the correct specialized agent, tracks status, and commits progress. It does not build skills, write content, or do research. It is the single entry point for autonomous queue execution.

**Scope:** One task per invocation. Routes → waits → updates status → commits → stops.

---

## Activation Triggers

- Scheduled run (every hour via Claude Code scheduled task)
- Human runs `/run-queue` to manually advance the queue
- Human runs `/orchestrate` to trigger one cycle

---

## Mandatory Reads Before Starting

1. `MASTER_QUEUE.md` — the queue
2. `AGENT_RULES.md` — repo rules all agents follow
3. `CLAUDE.md` — repo context

---

## Routing Table

| Task Status | Task Type | Route To |
|-------------|-----------|----------|
| RESEARCH | Task Mapper cell | `agents/task-mapper/` |
| TODO | Admin or BA role | `agents/admin-skill-builder/` |
| TODO | Dev role (apex/lwc/flow/integration/devops) | `agents/dev-skill-builder/` |
| TODO | Data role | `agents/data-skill-builder/` |
| TODO | Architect role | `agents/architect-skill-builder/` |
| UPDATE | Any stale skill | Route to the same agent as the skill's original domain/role |
| BLOCKED | Any | Skip. Log. Surface to human. |

---

## Orchestration Plan

### Step 1 — Find the next task

```bash
# Find first RESEARCHED, TODO, or RESEARCH row in MASTER_QUEUE.md
grep -n "| RESEARCHED\|| TODO\|| RESEARCH\|| UPDATE" MASTER_QUEUE.md | head -1
```

Read that row completely: Status, Skill Name, Description, Cloud, Role.

**If no RESEARCHED/TODO/RESEARCH/UPDATE rows exist:**
Check `SKILLS_BACKLOG.md` for any remaining TODO items there.
If both queues are empty → print "ALL QUEUES COMPLETE" and stop.

**If only BLOCKED rows remain:**
Print a summary of blocked items for human review. Stop.

### Step 2 — Mark IN_PROGRESS

Edit MASTER_QUEUE.md: change the row status from TODO/RESEARCH/UPDATE → IN_PROGRESS.
Add timestamp: `IN_PROGRESS (2026-04-03T10:00Z)`.

```bash
git add MASTER_QUEUE.md
git commit -m "queue: start <task-name>"
```

### Step 3 — Route to the correct agent

Read the task's Role field and route:

**RESEARCH task → Task Mapper:**
Pass: Cloud, Role, research instructions from the row.
Task Mapper maps the task universe and inserts TODO rows.

**TODO/UPDATE task → Role Agent:**
Determine role from MASTER_QUEUE.md row.
Pass to the appropriate skill builder:
- Admin/BA → `agents/admin-skill-builder/`
- Dev → `agents/dev-skill-builder/` (note the domain: apex/lwc/flow/integration/devops)
- Data → `agents/data-skill-builder/`
- Architect → `agents/architect-skill-builder/`

The skill builder will call Content Researcher and Validator internally.
Wait for the skill builder to complete.

### Step 4 — Handle the result

**If skill builder returns SHIPPABLE:**
The Validator agent has already committed the skill.
Update MASTER_QUEUE.md: change IN_PROGRESS → DONE.
```bash
git add MASTER_QUEUE.md
git commit -m "queue: complete <skill-name>"
```

**If skill builder returns BLOCKED:**
Update MASTER_QUEUE.md: change IN_PROGRESS → BLOCKED.
Add the blocking reason in the Notes column.
```bash
git add MASTER_QUEUE.md
git commit -m "queue: block <skill-name> — <reason>"
```

**If skill builder returns DUPLICATE:**
Update MASTER_QUEUE.md: change IN_PROGRESS → DUPLICATE.
```bash
git add MASTER_QUEUE.md
git commit -m "queue: mark duplicate <skill-name> — covered by <existing-skill>"
```

### Step 5 — Update progress summary

Recalculate the Progress Summary table at the top of MASTER_QUEUE.md.
Update counts for the relevant Phase row.

### Step 6 — Stop

One task per invocation. The next scheduled run picks up the next task.

---

## Stuck-Task Recovery

IN_PROGRESS rows that never complete are detected and reset at the start of each run.

**Rule:** If a row has status `IN_PROGRESS` and its timestamp is older than 2 hours, it is stuck.

**Recovery procedure:**
1. At the start of Step 1, before finding the next task, scan for stuck rows:
   ```bash
   grep "IN_PROGRESS" MASTER_QUEUE.md
   ```
2. For each stuck row, check the timestamp: `IN_PROGRESS (YYYY-MM-DDTHH:MMZ)`.
3. If the timestamp is more than 2 hours ago (compare against current time):
   - Reset status to `TODO`
   - Clear the timestamp
   - Add a note: `[reset: was stuck IN_PROGRESS since <timestamp>]`
4. Commit the reset:
   ```bash
   git add MASTER_QUEUE.md && git commit -m "queue: reset stuck task <skill-name>"
   ```
5. Proceed with Step 1 normally — the reset task is now a valid TODO.

**If a task gets stuck 3 times in a row** (detected by 3 `[reset: ...]` notes on the same row):
- Change status to `BLOCKED`
- Note: "Stuck 3 times — infrastructure or content issue. Requires human review."
- Move to the next task.

---

## Escalation Rules

Some situations require human review before proceeding:

| Situation | Action |
|-----------|--------|
| 3+ consecutive BLOCKED tasks | Stop queue. Add note: "Manual review needed — N consecutive blocks." |
| Validator returns NEEDS REVIEW on a security skill | Stop. Flag for human. Do not auto-commit. |
| A RESEARCH task returns fewer than 5 tasks for a major cloud | Flag as shallow research. Request human to add known tasks manually. |
| `validate_repo.py` exits non-zero 3 times in a row | Stop queue. Infrastructure issue likely. Requires human diagnosis. |
| Currency Monitor flags a HIGH priority stale security skill | Do not defer. Route immediately ahead of queue order. |

---

## Queue Priority Order

Process rows in this order, overriding queue position when necessary:

1. **HIGH priority UPDATE rows** (security and limit changes from Currency Monitor)
2. **RESEARCHED rows** (pre-researched by Phase B — build these first, they have notes in the Notes column)
3. **RESEARCH rows** (must run before TODO rows for that cell can be built)
4. **TODO rows** (Phase 1 before Phase 2, Admin before BA before Dev before Data before Architect within each phase)
5. **MEDIUM/LOW UPDATE rows**

---

## What This Agent Does NOT Do

- It does not write skill content
- It does not make architectural decisions about skill scope
- It does not resolve contradictions — those go to the relevant skill builder
- It does not skip BLOCKED rows silently — every BLOCKED status gets a committed note
- It does not process more than one task per invocation
