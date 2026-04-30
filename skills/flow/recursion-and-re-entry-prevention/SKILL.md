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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-30
---

# Flow Recursion and Re-Entry Prevention

Activate when a record-triggered Flow re-fires on the same record because its own DML — or a chain of DML through other automations on the same object — re-satisfies the Flow's entry criteria. Apex has the `static` Boolean idiom for breaking recursion; Flow does not. The skill produces entry-criteria refinements, idempotency markers, and diagnostic patterns specific to Flow's re-entry mechanics.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Which Flow is re-firing, and what's its trigger configuration?** Object, before-save vs after-save, "create only" vs "create or update" vs "update only," and the entry criteria (formula or "ISCHANGED" / "ISNEW" predicates). The diagnostic path forks sharply on whether the loop is *one Flow firing on its own DML*, or *Flow A → Flow B → Flow A*.
- **What fields does the Flow update, and which of those fields are referenced in any Flow's entry criteria on the same object?** This intersection is where re-entry happens. If the Flow updates `Status__c` and another Flow (or itself, on update) fires when `Status__c` changes, you have a loop.
- **What other automations exist on the object?** Apex triggers, Process Builder (deprecated but lingering), Workflow Rules (deprecated but still firing), other record-triggered Flows. The order-of-execution governs which one fires first; loops often span this stack.

---

## Core Concepts

### Apex's `static` recursion guard does not work for Flow

In Apex, a `static Boolean alreadyRan` flag scoped to the trigger handler is the canonical recursion break. The `static` lasts the duration of the transaction. Flow has no equivalent: there is no per-transaction static state inside a Flow definition. If a record-triggered Flow's DML triggers itself again (directly or indirectly) within the same transaction, the platform's only protection is the global trigger-depth limit (default 16), which is not a recursion *prevention* mechanism — it's a recursion *failure* mechanism.

This is the single most important fact of this skill. Engineers transferring from Apex assume a Flow-level "run once per record per transaction" feature exists. It does not.

### The platform's only built-in recursion ceiling

Salesforce enforces a maximum trigger depth of 16 by default for record-triggered automation chains. After 16 nested updates on the same record (or a related cascade), the platform throws `System.LimitException: Maximum trigger depth exceeded`. This is a circuit breaker, not a fix. Reaching the limit means the design has a recursion bug; the limit just kept things from running forever.

Optimistically, before-save Flow updates that complete in the same DML statement can hit this limit faster than after-save: each before-save self-update consumes a depth slot, and a poorly designed entry condition that re-fires on every update can cascade to 16 in milliseconds.

### Re-entry vs. recursion vs. cascade

- **Self-re-entry:** Flow A fires on update of Account, sets `Status__c = 'Active'` (which IS an update), Flow A's "update" trigger fires again. Pure self-loop.
- **Mutual recursion:** Flow A fires when `Status__c` changes, sets `Last_Status_Change__c`. Flow B fires when `Last_Status_Change__c` changes, sets `Status_Audit__c`. If either flow's DML cascades back into the other's entry condition, you have a two-Flow loop.
- **Cascade:** Flow A on Account fires, updates a related Contact, which triggers Flow B on Contact, which updates the Account back. Cross-object loops are harder to spot because the entry criteria look unrelated until you trace the data flow.

The remediation differs per case. Self-re-entry is fixed by tightening the entry criteria. Mutual recursion sometimes needs a Boolean idempotency marker. Cascades often need a coordination point (e.g., a "Sync_In_Progress__c" guard owned by one of the parties).

### Before-save vs. after-save and re-entry

Before-save Flows mutate `$Record` directly, without a separate DML; the change appears in the same save. Even so, the platform fires the *next* save cycle — i.e., a before-save Flow that's configured to run on update can re-trigger if the user (or another automation) updates the record again. Self-re-entry within a single save is not possible for before-save Flows on the *same record* because there's no second save until the transaction completes — but the chain can still cascade if a before-save Flow updates a related record whose own automation updates back.

After-save Flows perform a true DML update after the originating save commits to memory. That DML is what triggers the next round of automations. After-save loops are by far the more common variety.

---

## Common Patterns

### Pattern 1 — Tighten entry criteria with a record-state guard

**When to use:** A record-triggered Flow updates a field and you can characterize the "already done" state. The entry criteria currently fires on every update; tighten it so the Flow doesn't re-fire when the work is already done.

**How it works:** Replace a permissive entry condition like `ISCHANGED({!$Record.Status__c})` with a stricter one that excludes the post-update state. Common guards:

- `AND(ISCHANGED({!$Record.Status__c}), {!$Record.Status__c} <> 'Active')` — the Flow only fires when the status changes *to* something other than the value the Flow itself sets.
- `AND({!$Record.Needs_Sync__c} = TRUE, ISCHANGED({!$Record.Needs_Sync__c}))` — paired with the Flow setting `Needs_Sync__c = FALSE` at the end. The "needs sync" flag turns into a one-shot trigger that the Flow itself disables.

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

1. Reproduce the loop in a sandbox with debug logs. Identify the Flow(s), Apex triggers, and any deprecated Process Builder / Workflow Rules involved. The loop's shape (self / mutual / cascade) determines the fix.
2. Map the entry criteria of every record-triggered automation on the affected object(s). Look specifically for fields the loop's automations *write* that also appear in any automation's *entry condition*.
3. Pick the pattern: state guard (1), hash idempotency (2), or shared lock (3). When in doubt, prefer (1) — it's the simplest and survives refactors best.
4. Implement the guard. For Pattern 1, change entry criteria. For Pattern 2, add the hash field, the comparison Decision, and the post-run update. For Pattern 3, add the lock field and the entry-condition reference.
5. Add a regression test: a deterministic scenario that previously hit "Maximum Trigger Depth Exceeded" or that produced duplicate side effects, and verify it now runs to completion with the guard in place. Use Flow tests (where available) or an Apex test that performs the originating DML and inspects the result.
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
- [ ] Any deprecated Process Builder or Workflow Rules involved in the loop are migrated or excluded from re-triggering

---

## Salesforce-Specific Gotchas

1. **Flow has no per-transaction static state** — Engineers from Apex backgrounds reach for the `static Boolean alreadyRan` idiom and find no equivalent. The platform's *only* recursion ceiling is the trigger-depth limit (default 16), which is a failure mode, not a prevention mode. Always model recursion prevention as a record-field state, not a transient flag.
2. **"Maximum trigger depth exceeded" doesn't tell you which Flow is the culprit** — The error fires from the platform-level cascade detector, not from a specific Flow node. Diagnose by enabling Flow + Apex debug logs and examining the order-of-execution trace; the offending Flow is usually the one whose DML reappears in the trace at depth 14, 15, 16.
3. **Before-save Flows don't re-trigger themselves within the same save** — But they DO fire again on the *next* update, including any update an after-save Flow performs in response to the same originating save. Don't assume "before-save = safe from recursion." The save chain is what matters.
4. **`ISCHANGED()` is true even when the Flow's own DML is the cause of the change** — `ISCHANGED(Status__c)` returns true on the Flow's self-triggered re-entry just as it does on a user-driven change. The Flow can't distinguish "I just set this" from "the user just set this" from `ISCHANGED` alone — only a record-state guard or marker field can.
5. **Process Builder / Workflow Rules can resurrect deprecated loops** — A long-deprecated Workflow Rule or Process Builder process on the same object will still fire if it's "Active." Loops sometimes hide in this older automation that no one is reading. Migrate or deactivate.
6. **Flow tests don't cover all re-entry scenarios** — Flow tests fire the Flow against a fixture, but they don't simulate the full multi-automation save chain that produces real loops. Pair Flow tests with Apex tests that exercise the originating DML and observe the post-condition.
7. **The 16-depth limit is per-record, not per-transaction** — A bulk update of 200 records can each hit the limit independently. Don't assume "one record's loop won't tip the transaction." Bulk operations make the risk worse, not better.

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
- `architect/automation-migration-router` — for the strategic question of "should this Flow be Apex instead?" when the recursion fight gets too costly
