---
name: recursion-and-re-entry-prevention
description: "Use when a record-triggered Flow re-fires on the same record because its own DML (or a downstream Flow's DML) re-satisfies the entry criteria — causing CPU-limit failures, duplicated side effects, or 'Maximum Trigger Depth Exceeded' errors. Triggers: 'flow infinite loop', 'flow re-firing on same record', 'flow updates field then runs again', 'flow A and flow B keep updating each other', 'maximum trigger depth exceeded record-triggered flow', 'flow recursion limit hit'. NOT for Apex trigger recursion (use apex/recursive-trigger-prevention) or for Loop element design inside a single Flow run (use flow/flow-loop-element-patterns)."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
triggers:
  - "my record-triggered flow keeps firing on the same record"
  - "maximum trigger depth exceeded coming from a flow"
  - "flow A updates a field, flow B fires, then flow A runs again"
  - "after-save flow re-runs on its own update"
  - "before-save flow seems to re-execute and CPU times out"
  - "flow A flow B mutually triggering each other cascade"
tags:
  - flow
  - record-triggered-flow
  - recursion
  - re-entry
  - infinite-loop
  - bulkification
inputs:
  - "the record-triggered Flow(s) involved (which object, which entry criteria, before-save vs after-save)"
  - "what fields the Flow updates and whether those fields appear in any Flow's entry criteria"
  - "any downstream Apex triggers, Process Builder, Workflow Rules, or other Flows on the same object"
outputs:
  - "an entry-criteria refinement that prevents self-re-entry (record-state guard)"
  - "an idempotency marker pattern (boolean field, hash, or version field) when the entry criteria can't be tightened"
  - "a debug plan for diagnosing which automation is firing in which order"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# Flow Recursion and Re-Entry Prevention

Activate when a record-triggered Flow re-fires on the same record because its own DML — or a chain of DML through other automations on the same object — re-satisfies the Flow's entry criteria. Apex has the `static` Boolean idiom for breaking recursion; Flow does not. The skill produces entry-criteria refinements, idempotency markers, and diagnostic patterns specific to Flow's re-entry mechanics.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Which Flow is re-firing, and what's its trigger configuration?** Object, before-save vs after-save, "create only" vs "create or update" vs "update only," and the entry criteria (formula or "ISCHANGED" / "ISNEW" predicates). The diagnostic path forks sharply on whether the loop is *one Flow firing on its own DML*, or *Flow A → Flow B → Flow A*.
- **What fields does the Flow update, and which of those fields are referenced in any Flow's entry criteria on the same object?** This intersection is where re-entry happens. If the Flow updates `Status__c` and another Flow (or itself, on update) fires when `Status__c` changes, you have a loop.
- **What other automations exist on the object?** Apex triggers, Process Builder, Workflow Rules, other record-triggered Flows. The order of execution lists all of them (apexdev 264 L15643-15673); UNVERIFIED (2026-10-20): the corpus has no statement that Process Builder or Workflow Rules are deprecated, so check the org rather than assume they are gone. The order-of-execution governs which one fires first; loops often span this stack.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Which Flow re-fires, and is the loop one Flow or Flow A to Flow B? | The fix forks on self-loop, mutual loop and cascade (Gotcha 1). | The loop shape and the pattern it maps to. |
| Which fields does the Flow write that appear in any entry condition on the object? | That intersection is where re-entry happens (Gotcha 3). | A field list to build the state guard from. |
| Is the Flow before-save or after-save, and does it touch related records? | Before-save only edits its own record but re-runs in every cascade that saves that record again (Gotcha 4). | A cascade map across objects. |
| Which Apex triggers, Process Builder processes and Workflow Rules run on the same object? | They fire in the same save and can restart the Flow (Gotcha 5). | An automation inventory in order-of-execution order. |
| Is the trigger set to "only when a record is updated to meet the condition requirements"? | `doesRequireRecordChangedToMeetCriteria` is the platform's own guard (Pattern 1). | A yes/no and the entry condition it applies to. |
| Does the loop show up in a 200-record bulk update? | Stack depth is not a record count, and bulk makes the cost worse (Gotcha 6). | A bulk reproduction recipe. |
| What will prove the fix: Flow test, Apex test, or both? | Flow tests do not run the whole save chain (Gotcha 7). | A regression test scenario that previously hit the limit. |

A proper configuration adds a named guard, a documented lock or marker field and a bulk regression test; "just tightening a condition" leaves the next loop undiagnosed.


---

## Core Concepts

### Apex's `static` recursion guard does not work for Flow

In Apex, a `static Boolean alreadyRan` flag scoped to the trigger handler is the canonical recursion break. The `static` lasts the duration of the transaction. Flow has no equivalent: there is no per-transaction static state inside a Flow definition. UNVERIFIED (2026-10-20): the corpus holds no Flow Builder guide, so "Flow has no static state" is not grounded here; the Apex idiom itself is documented (apexdev 264 L3751: a recursive trigger can use a static class variable to exit). If a record-triggered Flow's DML triggers itself again (directly or indirectly) within the same transaction, the only ceiling the corpus documents is the stack-depth limit of 16 (see next section), which is a recursion *failure* mechanism, not a *prevention* mechanism.

This is the single most important fact of this skill. Engineers transferring from Apex assume a Flow-level "run once per record per transaction" feature exists. It does not (UNVERIFIED 2026-10-20, see above); the nearest platform feature is the guard below.

The platform does ship one guard: `FlowStart.doesRequireRecordChangedToMeetCriteria` (API 50.0+) — when true, "conditions evaluate to true only if the record didn't meet the required conditions before the triggering update but now meets the conditions after the update" (api_meta 264 L75049-75052). Use it before building a field-based marker.

### The only documented recursion ceiling

The Apex Developer Guide limits "total stack depth for any Apex invocation that recursively fires triggers due to insert, update, or delete statements" to 16, the same value for synchronous and asynchronous Apex (apexdev 264 L19762). A recursive save also skips order-of-execution steps 9 (assignment rules) through 17 (grandparent roll-up) (apexdev 264 L15617). When a process or flow runs DML, the affected record goes through the save procedure again (apexdev 264 L15671). UNVERIFIED (2026-10-20): that a chain made only of Flow DML counts against the 16, that 16 is a "default", and the exact error text `Maximum trigger depth exceeded` are not in the corpus (grep of all 14 files). Treat the limit as a circuit breaker, not a fix; reaching it means the design has a recursion bug.

### Re-entry vs. recursion vs. cascade

- **Self-re-entry:** Flow A fires on update of Account, sets `Status__c = 'Active'` (which IS an update), Flow A's "update" trigger fires again. Pure self-loop.
- **Mutual recursion:** Flow A fires when `Status__c` changes, sets `Last_Status_Change__c`. Flow B fires when `Last_Status_Change__c` changes, sets `Status_Audit__c`. If either flow's DML cascades back into the other's entry condition, you have a two-Flow loop.
- **Cascade:** Flow A on Account fires, updates a related Contact, which triggers Flow B on Contact, which updates the Account back. Cross-object loops are harder to spot because the entry criteria look unrelated until you trace the data flow.

The remediation differs per case. Self-re-entry is fixed by tightening the entry criteria. Mutual recursion sometimes needs a Boolean idempotency marker. Cascades often need a coordination point (e.g., a "Sync_In_Progress__c" guard owned by one of the parties).

### Before-save vs. after-save and re-entry

Before-save Flows mutate `$Record` directly, without a separate DML; they run at step 3, before the before triggers (apexdev 264 L15643). A before-save Flow re-runs whenever another save of the same record starts — a user edit, or DML from an after trigger or after-save Flow (apexdev 264 L15671). A workflow-rule field update re-runs the before and after update triggers one more time but does not re-run flows (apexdev 264 L15654-15662). A before-save Flow exists "to make more updates to that record before it's saved" (api_meta 264 L75266-75268), so cross-object cascades start from after-save Flows, Apex or other DML; the before-save Flow still re-runs each time the cascade saves its record again.

After-save Flows run at step 14, after the record is saved to the database at step 7 but before the commit at step 19 (apexdev 264 L15673, L15650). Their DML sends the record back through the save procedure, which is what starts the next round. After-save loops are the more common variety.

---

## Common Patterns

### Pattern 1 — Tighten entry criteria with a record-state guard

**When to use:** A record-triggered Flow updates a field and you can characterize the "already done" state. The entry criteria currently fires on every update; tighten it so the Flow doesn't re-fire when the work is already done.

**How it works:** Replace a permissive entry condition like `ISCHANGED({!$Record.Status__c})` with a stricter one that excludes the post-update state. Common guards:

- `AND(ISCHANGED({!$Record.Status__c}), {!$Record.Status__c} <> 'Active')` — the Flow only fires when the status changes *to* something other than the value the Flow itself sets.
- `AND({!$Record.Needs_Sync__c} = TRUE, ISCHANGED({!$Record.Needs_Sync__c}))` — paired with the Flow setting `Needs_Sync__c = FALSE` at the end. The "needs sync" flag turns into a one-shot trigger that the Flow itself disables.

Alternatively set `doesRequireRecordChangedToMeetCriteria` to true on the Start element (api_meta 264 L75049-75052); it replaces the `ISCHANGED` pair below for conditions that describe a state the record enters.

```text
Entry criteria (Flow Builder):
  Trigger: A record is updated
  Condition Requirements: Custom Condition Logic
    Condition 1: $Record.Sync_Required__c Equals True
    Condition 2: ISCHANGED({!$Record.Sync_Required__c})
  Logic: 1 AND 2
```

**Why not the alternative:** "Just exclude the user that the Flow updates as" — Flow doesn't have a clean "updated by automation" check the way Apex does. Modeling the guard as a record-field state is portable and self-documenting.

### Pattern 2 — Idempotency marker (boolean field that tracks "already processed in this transaction")

**When to use:** The entry criteria can't be tightened to characterize "done" state — e.g., the Flow makes a callout via an external service, and the act of receiving a response back into the record looks identical to a user-triggered update.

**How it works:** Add a custom field, e.g., `Last_Sync_Hash__c`. Compute a hash (or composite key) of the input fields the Flow uses. At the start of the Flow, compare the current hash to `Last_Sync_Hash__c`; if equal, exit. At the end of the Flow, store the new hash. Two Flow executions for the same logical state become a no-op the second time.

```text
Flow steps:
  1. Get Records: load this record (already in $Record).
  2. Assignment: computedHash = ...formula combining input fields...
  3. Decision: $Record.Last_Sync_Hash__c == computedHash?
       Yes → End (already processed).
       No  → continue.
  4. ... actual work ...
  5. Update Records: set $Record.Last_Sync_Hash__c = computedHash.
```

**Why not the alternative:** A simple Boolean "already ran" flag breaks across transactions — the second user edit *should* re-trigger the Flow, and a Boolean flag would block it. The hash approach lets the Flow re-run when something meaningful changed, but no-op when nothing did.

### Pattern 3 — Cross-Flow coordination via a shared lock field

**When to use:** Two Flows on related objects mutually re-trigger each other (Flow A on Account updates a Contact, Flow B on Contact updates the Account back, and Flow A re-fires).

**How it works:** Designate one of the records as the "lock owner." Add a `Sync_In_Progress__c` Boolean. Flow A sets it to `TRUE` before its updates; Flow B's entry criteria includes `Sync_In_Progress__c = FALSE` and so it does not run. Flow A unsets it at the end of its run.

```text
Flow A (Account, after-save):
  1. Update $Record.Sync_In_Progress__c = TRUE.
  2. Update related Contacts (this would normally fire Flow B,
     but Flow B's entry criteria filters out Sync_In_Progress__c = TRUE).
  3. Update $Record.Sync_In_Progress__c = FALSE.

Flow B (Contact, after-save):
  Entry criteria includes:
    AND(other conditions, $Record.Account.Sync_In_Progress__c = FALSE)
```

**Why not the alternative:** "Flow B should detect the loop and exit" — without a shared signal, Flow B doesn't have a clean way to distinguish "user edit on Contact" from "Flow A's DML cascading back." The lock field is the explicit signal.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single Flow re-firing on its own DML, "already done" state is characterizable | Pattern 1 — tighten entry criteria with record-state guard | Cleanest; no extra fields |
| Single Flow with no clean "done" state (callout-shaped logic) | Pattern 2 — hash-based idempotency marker | Re-fires on real changes, no-ops on duplicate triggers |
| Two Flows mutually re-triggering across related objects | Pattern 3 — shared lock field on the parent | Explicit coordination; one party owns the lock |
| Flow + Apex trigger combined recursion | Apex `static` flag handles Apex side; combine with Pattern 1 or 2 on the Flow side | Each automation needs its own guard |
| Flow firing on every save because entry criteria is "create or update" with no condition | Add an entry condition; bare "create or update" is rarely correct | The Flow shouldn't fire when nothing it cares about changed |

---

## Recommended Workflow

1. Reproduce the loop in a sandbox with debug logs. Identify the Flow(s), Apex triggers, and any Process Builder / Workflow Rules involved. The loop's shape (self / mutual / cascade) determines the fix.
2. Map the entry criteria of every record-triggered automation on the affected object(s). Look specifically for fields the loop's automations *write* that also appear in any automation's *entry condition*.
3. Pick the pattern: state guard (1), hash idempotency (2), or shared lock (3). When in doubt, prefer (1) — it's the simplest and survives refactors best.
4. Implement the guard. For Pattern 1, change entry criteria. For Pattern 2, add the hash field, the comparison Decision, and the post-run update. For Pattern 3, add the lock field and the entry-condition reference.
5. Add a regression test: a deterministic scenario that previously hit the depth-16 failure (apexdev 264 L19762) or that produced duplicate side effects, and verify it now runs to completion with the guard in place. Use Flow tests (where available) or an Apex test that performs the originating DML and inspects the result.
6. Document the guard inline. Future maintainers don't see the recursion risk; they need a one-line description of what the entry condition / hash field / lock field protects against.
7. Audit related objects for the same pattern. If you find the loop on Account, the next-most-likely place is Account → Opportunity → Contact, where related-list cascades mirror the original.

---

## Review Checklist

- [ ] The entry criteria of every record-triggered Flow on the object excludes the post-update state the Flow itself produces (or a hash/lock guard is in place)
- [ ] No "create or update" trigger fires unconditionally — every after-save Flow has at least one ISCHANGED, ISNEW, or formula condition
- [ ] Cross-object cascades have a shared lock or coordination point with one party as owner
- [ ] Apex triggers and Flows on the same object have been audited together; recursion guards exist on both sides where needed
- [ ] A regression test reproduces the original loop and confirms the fix
- [ ] The guard's purpose is documented inline (entry-condition comment, field description, or Flow description)
- [ ] Any Process Builder or Workflow Rules involved in the loop are migrated or excluded from re-triggering

---

## Salesforce-Specific Gotchas

1. **Flow has no per-transaction static state (UNVERIFIED 2026-10-20: not in the corpus)** — Engineers from Apex backgrounds reach for the `static Boolean alreadyRan` idiom and find no equivalent. The only ceiling the corpus documents is the stack-depth limit of 16 (apexdev 264 L19762), which is a failure mode, not a prevention mode. Always model recursion prevention as a record-field state, not a transient flag.
2. **A depth-limit failure doesn't tell you which Flow is the culprit** — UNVERIFIED (2026-10-20): the error text `Maximum trigger depth exceeded` and which component raises it are not in the corpus. Diagnose by enabling debug logs (Apex Code level up to FINER, api_meta 264 L13295) and examining the order-of-execution trace; the offending Flow is usually the one whose DML reappears at increasing depth.
3. **Before-save Flows run once per save, not once per transaction** — They fire again on every later save of the record, including a save an after trigger or after-save Flow performs in the same transaction (apexdev 264 L15643, L15671). Don't assume "before-save = safe from recursion." The save chain is what matters.
4. **`ISCHANGED()` is true even when the Flow's own DML is the cause of the change** — `ISCHANGED(Status__c)` returns true on the Flow's self-triggered re-entry just as it does on a user-driven change. The Flow can't distinguish "I just set this" from "the user just set this" from `ISCHANGED` alone — only a record-state guard or marker field can.
5. **Process Builder / Workflow Rules can resurrect old loops** — A Workflow Rule or Process Builder process on the same object still fires if it's "Active" (both appear in the order of execution, apexdev 264 L15654, L15666; UNVERIFIED 2026-10-20: "deprecated" is not stated in the corpus). A workflow field update re-runs triggers but not flows (apexdev 264 L15659-15662). Loops sometimes hide in this older automation that no one is reading. Migrate or deactivate.
6. **Flow tests don't cover all re-entry scenarios** — Flow tests fire the Flow against a fixture, but they don't simulate the full multi-automation save chain that produces real loops. Pair Flow tests with Apex tests that exercise the originating DML and observe the post-condition.
7. **The 16 is a stack depth, not a record count** — The limit counts nested trigger invocations (apexdev 264 L19762), so a bulk update of 200 records is one level per cascade step, not 200. UNVERIFIED (2026-10-20): whether each record's loop is counted independently is not documented; test with 200 records anyway, because every loop iteration multiplies DML and CPU against the per-transaction limits.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Refined entry-criteria expression | Formula or rule condition that excludes the post-update state |
| Idempotency hash field + Flow logic | Custom field plus the Decision/Update steps for Pattern 2 |
| Shared lock field + cross-Flow entry conditions | Custom field plus matched entry-condition references for Pattern 3 |
| Regression test scaffold | Apex test that reproduces the original loop and verifies the guard |
| Order-of-execution diagnosis notes | Documented trace showing which automations fired in which order during the loop |

---

## Related Skills

- `apex/recursive-trigger-prevention` — for the Apex-side `static`-flag idiom and trigger-handler patterns; pair with this skill when the loop spans Apex and Flow
- `apex/order-of-execution-deep-dive` — for the platform's overall save-and-trigger cascade order, which determines which automation fires first
- `flow/record-triggered-flow-patterns` — for the broader design vocabulary of record-triggered Flows; this skill plugs into that vocabulary at the entry-criteria step
- `flow/flow-record-save-order-interaction` — for the more specific question of how before-save vs after-save interact with Apex triggers in the save sequence
- `admin/process-automation-selection` — for the strategic question of "should this Flow be Apex instead?" when the recursion fight gets too costly
