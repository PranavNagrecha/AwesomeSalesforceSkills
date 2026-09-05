---
name: recursive-trigger-prevention
description: "Use when debugging or preventing recursive Apex trigger behavior — self-DML, static guard flaws, Set<Id>-based deduplication, and legitimate re-entry. Triggers: 'trigger recursion', 'static boolean guard', 'recursive update', 'self DML', 'trigger firing multiple times'. NOT for how to structure the trigger handler itself — use apex/trigger-framework. NOT for switching a trigger off for a data load — use apex/apex-trigger-bypass-and-killswitch-patterns. Also: 'maximum trigger depth exceeded', 'stack depth 16', 'hasRun flag', 'processed Id set', 'apex flow loop', 'workflow field update refires trigger', 'guard skipped records over 200'."
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
  - "trigger recursion isn't working"
  - "maximum trigger depth exceeded error on save"
  - "stop an apex trigger and a flow updating each other in a loop"
  - "my hasRun flag skipped half the records in a 400 row load"
  - "write a test that proves a recursion guard survives bulk chunking"
  - "count how many times a trigger fired in the debug log"
  - "turn a trigger off for a data migration without commenting out code"
  - "why does my trigger fire again after a workflow field update"
  - "guard the trigger by record id instead of a boolean"
inputs:
  - "object and trigger events involved"
  - "whether recursion comes from self-DML, workflow/flow updates, or cross-object writes"
  - "whether some re-entry is legitimate and should not be blocked globally"
  - "row count of the DML that spawns the re-entry (above or below 200)"
outputs:
  - "recursion prevention recommendation"
  - "review findings for overbroad or missing guards"
  - "guard pattern for trigger handlers and services"
  - "deployable RecursionGuard class, TriggerHandler subclass, trigger, and 400-record test class"
  - "package.xml, deploy order, and debug-log verification procedure"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

Use this skill when trigger behavior is correct once and wrong on the second pass. The objective is to prevent accidental recursion without suppressing legitimate processing. In Salesforce, recursion often comes from self-DML, after-save updates, or surrounding automation, and the classic static-boolean fix is usually too blunt.

## Before Starting

- What actually causes the second execution: self-update, related-object update, Flow/workflow field update, or integration callback?
- Is every repeated execution bad, or is some re-entry valid under certain records or transitions?
- Do you have record-level identity available to guard by ID instead of suppressing the whole transaction globally?

## Questions to Ask Before Configuring

Ask these before you write a guard. A `hasRun` Boolean is the answer to none of them, and every one of
these questions maps to a documented platform behaviour that a Boolean gets wrong.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "How many rows does the DML that re-enters the trigger carry?" | Over 200 rows, "the trigger is invoked for each batch" and `Trigger.size` counts only the current batch (`apexdev` L15029–15033), while a static "persists across these trigger invocations" (`apexdev` L3738–3740). One flag is spent on batch one. | The guard's key: a record-Id set instead of a Boolean, and a test at 400 records instead of 5 |
| "Which of the repeated passes do you actually want suppressed?" | A workflow field update re-runs before-update and after-update triggers "one more time (and only one more time)" (`apexdev` L15455–15460) — bounded, and carrying values the handler usually still needs | The distinction between an echo of our own DML and a real second change, i.e. whether the guard needs a field fingerprint |
| "Is the loop inside one object, or between two?" | Cross-object ping-pong is a mutual loop: "When a process or flow executes a DML operation, the affected record goes through the save procedure" (`apexdev` L15468). The debug-log counts move in lockstep (`references/examples.md`, Example 3) | Where the guard goes. A self-DML guard installed on the wrong side of a mutual loop suppresses nothing |
| "Is the DML all-or-none, or partial success?" | With partial success "triggers are fired during the first attempt and are fired again during subsequent attempts… static class variables that are accessed by the trigger aren't reset" (`apexdev` L15499–15501), for up to three attempts (`apexdev` L9070–9076) | Whether the guard must survive a retry — record-keyed guards do, Booleans reset to a duplicate-work failure |
| "Which fields does the handler actually read?" | The fingerprint is only correct over the watched fields. Widen it and every unrelated update in the transaction reads as new work; narrow it wrongly and a real change is swallowed | The exact field list in `fingerprintOf()`, written down before the code |
| "Is this a data load, or is this business automation?" | A load wants the handler off, not smarter. `TriggerControl` reads `Trigger_Setting__mdt` and the `TriggerControl_BypassAll` Custom Permission (`templates/apex/TriggerControl.cls`) | The bypass route (per-user permission for a Data Loader run; CMDT record for a deployment window) instead of a guard that has to be reasoned about later |
| "How will the fix be verified in the org, not just in a test?" | `CODE_UNIT_STARTED` and `CODE_UNIT_FINISHED` delimit units of code and a trigger is one unit (`apexdev` L38178–38190). The stack-depth ceiling is 16 (`apexdev` L19559), and it arrives as an uncatchable `LimitException` (`apexdev` L17856) | A before/after invocation count from a real save, so "it's fixed" is a number rather than an impression |

What a proper configuration adds over just doing it: the guard suppresses only the pass that is an echo
of your own DML, every record in a 400-row load still gets its work, a partial-success retry is served
exactly once, the data-load case is handled by a switch that leaves an audit trail instead of by a flag
somebody has to remember, and the fix is demonstrated by a falling `CODE_UNIT_STARTED` count rather than
by the absence of complaints.

## Core Concepts

### Static Boolean Guards Are Usually Overbroad

A single static Boolean often stops more than recursion. It can suppress valid processing for later records in the same transaction or later phases that should still run. This is why backlog guidance explicitly calls out the flaw: it does not scale well to multi-record or multi-phase behavior.

The platform reason is specific rather than stylistic. A static variable "is static only within the scope
of the Apex transaction… if an Apex DML request causes a trigger to fire multiple times, the static
variables persist across these trigger invocations" (`apexdev` L3738–3740), and a DML over 200 rows fires
the trigger once per batch (`apexdev` L15029–15033). One bit of state, many invocations.

### Record-Aware Guards Are Safer

Set-based or map-based guards keyed by record ID or operation context are usually more precise. They let the system prevent duplicate processing for the same logical work item without globally silencing the handler.

Scope the key by `Trigger.operationType` as well as by Id. It returns a `System.TriggerOperation` enum
with values `BEFORE_INSERT`, `BEFORE_UPDATE`, `BEFORE_DELETE`, `AFTER_INSERT`, `AFTER_UPDATE`,
`AFTER_DELETE`, `AFTER_UNDELETE` (`apexdev` L15023–15026); without it, a before-update guard silences the
after-update work on the same record.

### Guard Logic Must Match The Actual Recursion Source

If the real issue is after-save self-DML, the guard should sit before that DML path. If the issue is a legitimate second pass only when a field truly changes, old/new delta checks may be more important than a static flag.

### Some Re-Entry Is Legitimate

Not every second pass is a bug. Reparenting, staged enrichment, or chained updates can involve intended re-entry. Good recursion prevention blocks accidental loops, not all repeated execution.

### Three Layers, Not One Flag

`templates/apex/` already separates the concerns; keep them separate in your own code.

| Layer | Canonical implementation | Question it answers |
|---|---|---|
| Activation | `templates/apex/TriggerControl.cls` (CMDT + Custom Permission) | Should this handler run at all, for this user, right now? |
| Circuit breaker | `templates/apex/TriggerHandler.cls` `MAX_DEPTH` | Has this become a runaway loop that must fail loudly? |
| Re-entry guard | `RecursionGuard` (`references/code-examples.md`) | Have I already done this work for this record with these values? |

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

### Fingerprinted Re-Entry Guard

**When to use:** The record legitimately comes back with different values — a workflow field update, an
after-save flow, a partial-success retry — and the handler must serve that pass but not an identical echo.

**How it works:** Store a string built from the watched fields alongside the record Id. Re-entry with the
same fingerprint is suppressed; re-entry with a different one is served.

**Why not the alternative:** An Id-only set cannot tell the two apart and silences the legitimate pass.

### Bypass, Not Guard, For Data Loads

**When to use:** A migration or Data Loader run should not fire the handler at all.

**How it works:** Assign `TriggerControl_BypassAll` to the load user, or deactivate the
`Trigger_Setting__mdt` record for the window.

**Why not the alternative:** A guard makes the automation look enabled while doing nothing, and nobody can
tell afterwards whether it ran.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Self-DML on the same records is causing repeated after-update work | Set<Id>-based or context-aware guard | More precise than a global Boolean |
| Processing should happen only on meaningful status changes | Delta check using old/new values | Often removes the need for broad static guards |
| Org already has a trigger framework | Framework-level recursion service | Consistency and lower duplication |
| Re-entry is partly legitimate | Narrow guard by record and condition | Avoid suppressing valid behavior |
| The DML that re-enters carries more than 200 rows | Record-keyed guard; never `skipOnce`, never a Boolean | The trigger is invoked once per batch (`apexdev` L15029–15033) and a one-shot skip is consumed by batch one |
| A workflow field update or after-save flow re-fires the trigger | Fingerprinted guard, not suppression | That pass is bounded at one and carries values you usually need (`apexdev` L15455–15460) |
| A data migration must not fire the handler | `TriggerControl` bypass | Stops the work outright and leaves a record of the decision |
| Two objects update each other in a cycle | Guard on both sides, plus `doesRequireRecordChangedToMeetCriteria` on the flow | The flow's DML re-enters the save procedure (`apexdev` L15468); the Flow-side entry condition is `api_meta` L72322–72325 |

## Recommended Workflow

1. **Count before you guard.** Reproduce the save with `sf apex tail log` and count
   `CODE_UNIT_STARTED … trigger event <Event>` lines per trigger — the pipeline is in
   `references/examples.md`, Example 3. A count of 2 is a workflow re-fire, not a loop; counts moving in
   lockstep across two triggers are a mutual loop, which changes where the guard goes.
2. **Answer the Questions table above**, in particular the row count of the re-entering DML and which
   fields the handler reads. Record the answers in `templates/recursive-trigger-prevention-template.md`.
3. **Build on the canonical framework, not beside it.** Read `templates/apex/TriggerHandler.cls` and
   `templates/apex/TriggerControl.cls`, then subclass the first. Copy `RecursionGuard` and the handler
   from `references/code-examples.md` and replace `fingerprintOf()` with your watched fields.
4. **Prove it at 400 records.** Port `AccountRecursionGuardTest` from `references/code-examples.md`. The
   chunking test must show every record processed once, not 200 of them; the re-entry test must show an
   identical second pass suppressed and a changed one served.
5. **Run the checker over the source tree**:
   `python3 scripts/check_recursive_trigger_prevention.py --manifest-dir force-app` (add `--strict` in
   CI to fail on WARN). It flags never-reset `hasRun` Booleans, second triggers on one sObject, logic in
   the trigger body, same-object DML with no guard, and a missing `@TestVisible` reset.
6. **Re-count in the org.** Deploy, repeat step 1, and record the before/after invocation counts. If the
   count did not fall, the guard is on the wrong side of the loop — go back to step 1 rather than
   widening it.
7. **Read `references/gotchas.md` before switching the DML to `allOrNone = false`,** adding a savepoint,
   or shipping anything that will be loaded through Bulk API. Each of those changes the guard's
   correctness in a way that no test at default settings will catch.

---

## Review Checklist

- [ ] The actual recursion source is identified before choosing a guard.
- [ ] Static Boolean guards are challenged and replaced when too broad.
- [ ] Old/new delta checks exist where field transitions matter.
- [ ] Guard state is record-aware when multiple records may be processed.
- [ ] Legitimate re-entry scenarios are not accidentally blocked.
- [ ] Recursion logic is centralized where the trigger framework allows it.
- [ ] The guard is keyed by `Trigger.operationType` as well as by record Id.
- [ ] A bulk test at 400+ records asserts every record was processed exactly once.
- [ ] The data-load case is handled by `TriggerControl`, not by the guard.
- [ ] Before/after `CODE_UNIT_STARTED` counts from a real save are recorded.

## Salesforce-Specific Gotchas

1. **A static Boolean can suppress valid work for later records in the same transaction** — it is rarely the safest long-term pattern.
2. **After-save self-DML is the classic recursion source** — the guard must sit before that path, not after it.
3. **Surrounding automation can re-enter Apex too** — recursion is not always caused by trigger code alone.
4. **A guard that is too broad becomes a data-loss bug** — silent skipped processing is still failure.
5. **A static declared in the `.trigger` file is not the same variable in the next context** — put guards in a class (`apexdev` L3761–3763).
6. **A rollback does not roll back the guard** — statics survive `Database.rollback` (`apexdev` L8692–8693).

The full set with citations is in `references/gotchas.md`.

## Output Artifacts

| Artifact | Description |
|---|---|
| Recursion review | Findings on recursion source, guard precision, and skipped-processing risk |
| Guard recommendation | Choice of set-based, delta-based, fingerprinted, or framework-level recursion prevention |
| Trigger remediation pattern | Concrete guard placement guidance for self-DML or re-entry scenarios |
| Deployable package | `RecursionGuard`, a `TriggerHandler` subclass, the trigger, a 400-record test class, and `package.xml` |
| Verification record | Before/after `CODE_UNIT_STARTED` counts and the `sf apex run test` result |

## Reference Files

| File | Read it when |
|---|---|
| `references/code-examples.md` | You are writing the code — full `RecursionGuard`, `TriggerHandler` subclass, trigger, 400-record test class, CMDT bypass record, `package.xml`, deploy order, and the debug-log verification |
| `references/gotchas.md` | Something behaves unexpectedly under bulk, partial success, rollback, Bulk API, workflow re-fire, or a second trigger on the object |
| `references/examples.md` | You want the shape of a guard or the debug-log pipeline that identifies the loop before you write one |
| `references/llm-anti-patterns.md` | You are reviewing generated code, or about to write a `hasRun` flag, a `finally` reset, or a `skipOnce` before a large DML |
| `references/well-architected.md` | You need the pillar framing, the tradeoff list, or the exact official-source line for a claim |
| `templates/recursive-trigger-prevention-template.md` | You are recording the recursion source and guard decision for review |

## Related Skills

- `apex/trigger-framework` — use when recursion issues are inseparable from the broader handler architecture.
- `apex/apex-trigger-bypass-and-killswitch-patterns` — use when the requirement is to switch the handler off (data load, incident) rather than to shape its re-entry.
- `apex/trigger-and-flow-coexistence` — use when the loop involves a record-triggered Flow writing back and you need the automation inventory.
- `flow/flow-record-save-order-interaction` — use when you need the save-order step list and the Flow side of the re-entry.
- `apex/order-of-execution-deep-dive` — use when the question is which step of the save fired what.
- `apex/exception-handling` — use when recursive behavior is surfacing as transaction rollbacks, partial-success retries, or swallowed failures.
- `apex/governor-limits` — use when recursion is also multiplying SOQL, DML, or CPU consumption.
- `apex/apex-trigger-context-variables` — use when the guard's correctness depends on which context variables are populated.
