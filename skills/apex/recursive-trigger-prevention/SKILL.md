---
name: recursive-trigger-prevention
description: "Use when debugging or preventing recursive Apex trigger behavior, especially around self-DML, static guard flaws, Set<Id>-based deduplication, and legitimate re-entry scenarios. Triggers: 'trigger recursion', 'static boolean guard', 'recursive update', 'self DML', 'trigger firing multiple times'. NOT for general trigger-framework structure unless recursion is the actual design problem."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Scalability
  - Operational Excellence
tags:
  - trigger-recursion
  - static-boolean
  - set-of-id
  - self-dml
  - recursion-guard
triggers:
  - "how do I prevent recursive Apex triggers"
  - "static boolean recursion guard problem"
  - "trigger updates same object again"
  - "after update trigger firing repeatedly"
  - "Set<Id> recursion guard pattern"
  - "trigger running twice"
  - "trigger firing multiple times"
inputs:
  - "object and trigger events involved"
  - "whether recursion comes from self-DML, workflow/flow updates, or cross-object writes"
  - "whether some re-entry is legitimate and should not be blocked globally"
outputs:
  - "recursion prevention recommendation"
  - "review findings for overbroad or missing guards"
  - "guard pattern for trigger handlers and services"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-13
---

Use this skill when trigger behavior is correct once and wrong on the second pass. The objective is to prevent accidental recursion without suppressing legitimate processing. In Salesforce, recursion often comes from self-DML, after-save updates, or surrounding automation, and the classic static-boolean fix is usually too blunt.

## Before Starting

- What actually causes the second execution: self-update, related-object update, Flow/workflow field update, or integration callback?
- Is every repeated execution bad, or is some re-entry valid under certain records or transitions?
- Do you have record-level identity available to guard by ID instead of suppressing the whole transaction globally?

## Core Concepts

### Static Boolean Guards Are Usually Overbroad

A single static Boolean often stops more than recursion. It can suppress valid processing for later records in the same transaction or later phases that should still run. This is why backlog guidance explicitly calls out the flaw: it does not scale well to multi-record or multi-phase behavior.

### Record-Aware Guards Are Safer

Set-based or map-based guards keyed by record ID or operation context are usually more precise. They let the system prevent duplicate processing for the same logical work item without globally silencing the handler.

### Guard Logic Must Match The Actual Recursion Source

If the real issue is after-save self-DML, the guard should sit before that DML path. If the issue is a legitimate second pass only when a field truly changes, old/new delta checks may be more important than a static flag.

### Some Re-Entry Is Legitimate

Not every second pass is a bug. Reparenting, staged enrichment, or chained updates can involve intended re-entry. Good recursion prevention blocks accidental loops, not all repeated execution.

## Common Patterns

### Set<Id>-Based Guard

**When to use:** The same record should not be processed twice for the same logical step in one transaction.

**How it works:** Store processed IDs in a static set and check membership before performing self-triggering work.

**Why not the alternative:** A single static Boolean suppresses unrelated records too.

### Delta-Based Guard Clause

**When to use:** Recursion should happen only if a meaningful field transition occurs.

**How it works:** Compare `Trigger.oldMap` to `Trigger.new` and exit unless the relevant state actually changed.

### Framework-Level Guard Service

**When to use:** The org already uses a trigger framework and needs consistent recursion rules.

**How it works:** Centralize guard management so every handler does not reinvent incompatible static state.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Self-DML on the same records is causing repeated after-update work | Set<Id>-based or context-aware guard | More precise than a global Boolean |
| Processing should happen only on meaningful status changes | Delta check using old/new values | Often removes the need for broad static guards |
| Org already has a trigger framework | Framework-level recursion service | Consistency and lower duplication |
| Re-entry is partly legitimate | Narrow guard by record and condition | Avoid suppressing valid behavior |


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

- [ ] The actual recursion source is identified before choosing a guard.
- [ ] Static Boolean guards are challenged and replaced when too broad.
- [ ] Old/new delta checks exist where field transitions matter.
- [ ] Guard state is record-aware when multiple records may be processed.
- [ ] Legitimate re-entry scenarios are not accidentally blocked.
- [ ] Recursion logic is centralized where the trigger framework allows it.

## Salesforce-Specific Gotchas

1. **A static Boolean can suppress valid work for later records in the same transaction** — it is rarely the safest long-term pattern.
2. **After-save self-DML is the classic recursion source** — the guard must sit before that path, not after it.
3. **Surrounding automation can re-enter Apex too** — recursion is not always caused by trigger code alone.
4. **A guard that is too broad becomes a data-loss bug** — silent skipped processing is still failure.

## Output Artifacts

| Artifact | Description |
|---|---|
| Recursion review | Findings on recursion source, guard precision, and skipped-processing risk |
| Guard recommendation | Choice of set-based, delta-based, or framework-level recursion prevention |
| Trigger remediation pattern | Concrete guard placement guidance for self-DML or re-entry scenarios |

## Related Skills

- `apex/trigger-framework` — use when recursion issues are inseparable from the broader handler architecture.
- `apex/exception-handling` — use when recursive behavior is surfacing as transaction rollbacks or swallowed failures.
- `apex/governor-limits` — use when recursion is also multiplying SOQL, DML, or CPU consumption.
