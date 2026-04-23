---
name: apex-flow-invocation-from-apex
description: "Use when invoking Autolaunched Flows from Apex via `Flow.Interview.createInterview`. Covers parameter typing, output retrieval, governor boundaries, and when to inline logic instead. NOT for Apex-from-Flow (`@InvocableMethod`), Process Builder, Screen Flow invocation, or Flow Orchestrator stages."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
  - Operational Excellence
triggers:
  - "call an Autolaunched Flow from Apex with input variables"
  - "Flow.Interview.createInterview is throwing on type mismatch"
  - "run a Flow from a trigger or Queueable"
  - "should this logic be in Apex or in a Flow I invoke from Apex"
  - "how do I read output variables from a Flow invoked in Apex"
tags:
  - apex-flow-invocation-from-apex
  - flow-interview
  - autolaunched-flow
  - orchestration
inputs:
  - "Flow developer name and its input/output variable declarations"
  - "Apex caller context (trigger, Queueable, batch)"
  - "the data being handed to the Flow"
outputs:
  - "correct `Flow.Interview.createInterview(name, params)` invocation with type-safe params"
  - "output variable retrieval pattern"
  - "guidance on when to inline the logic in Apex instead"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-23
---

# Apex Flow Invocation From Apex

Activates when Apex calls `Flow.Interview.createInterview` to run an Autolaunched Flow. Produces type-safe parameter maps, output retrieval, and clear guidance on the "Apex calls Flow" architectural choice.

---

## Before Starting

- Is the Flow **Autolaunched**? Only Autolaunched Flows can be started from Apex. Screen Flows cannot run headless and throw.
- Does the Flow's API name exactly match what you will pass? `Flow.Interview.createInterview` looks up by API name — a typo produces a `SObjectException` at runtime, not compile time.
- What is the **exact type** of each input variable in the Flow? Collections of SObjects, dates, currencies all have specific Apex types the Flow engine expects.
- Does the caller execute in a trigger context? Flow invocations count against SOQL, DML, and CPU governor limits of the *caller*.
- Is this a good architectural fit? If the only reason you're calling a Flow is "admin owns it," ensure the Flow's logic actually benefits from Flow's declarative shape. Plain Apex is usually simpler.

---

## Core Concepts

### The Parameter Map Must Match Flow Variable Types Exactly

`createInterview` accepts `Map<String, Object>`. The keys are Flow input-variable API names. The values are Apex primitives, SObjects, or `List<SObject>`. Mismatched types throw `Flow.FlowException` at runtime with messages like "Type mismatch: expected Decimal, got String".

Collections in Flows have two flavors — SObject collections and primitive collections. Passing `List<String>` where the Flow expects a "Collection of Text" generally works; passing `List<Opportunity>` where it expects a "Collection of SObject Records" requires the Flow's SObject type to match.

### Starting The Interview Runs The Flow

After `createInterview`, call `.start()`. This synchronously runs the Flow to completion (for Autolaunched Flows without pause elements). Long-running Flows — those with loops that create/update many records — count every action against the caller's governor limits.

### Output Variables Come Back By Name

After `.start()`, retrieve outputs with `interview.getVariableValue(name)`. The return type is `Object`; cast to the expected type. A typo in the output name returns `null` — no exception.

### Invocable Actions Are A Better Fit For Dynamic Invocation

If the caller doesn't know which Flow to run until runtime, consider registering the Flow as an Invocable Action and using the `Action` framework. This gives you discovery, validation of required parameters, and a better error surface than raw `Flow.Interview`.

---

## Common Patterns

### Pattern 1: Invoke An Autolaunched Flow With Typed Inputs And Outputs

**When to use:** Apex must delegate a calculated business rule that an admin maintains in Flow.

**How it works:**

```apex
public with sharing class TierAssignmentService {
    public static String assignTier(Account a, Decimal yearToDate) {
        Map<String, Object> params = new Map<String, Object>{
            'inputAccount'    => a,
            'yearToDateAmount'=> yearToDate
        };
        Flow.Interview i = Flow.Interview.createInterview('Assign_Account_Tier', params);
        i.start();
        return (String) i.getVariableValue('resultTier');
    }
}
```

**Why not the alternative:** Hardcoding the tier logic in Apex forces deploys for admin-owned tweaks. Calling the Flow preserves declarative ownership while giving Apex a clean call site.

### Pattern 2: Bulk-Safe Flow Invocation

**When to use:** A trigger fires for 200 records and each needs the Flow's logic.

**How it works:**

```apex
public with sharing class BulkTierAssignment {
    public static void assignAll(List<Account> accounts, Map<Id, Decimal> ytdById) {
        Map<String, Object> params = new Map<String, Object>{
            'inputAccounts' => accounts,
            'ytdMap'        => ytdById
        };
        Flow.Interview i = Flow.Interview.createInterview('Bulk_Assign_Tier', params);
        i.start();
    }
}
```

**Why not the alternative:** Calling `createInterview` in a per-record loop multiplies CPU consumption and makes failure isolation harder. Design the Flow to accept a collection and iterate internally.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Admin-owned decision table (tier, routing) | Apex calls Flow | Admin maintains, Apex integrates |
| Hot-path computation in a trigger | Inline Apex | Flow adds overhead for simple math |
| Dynamic flow selection at runtime | Invocable Action framework | Adds discovery, validation, error surface |
| Flow with screen elements | Do not invoke from Apex | Screen Flows cannot run headless |
| Long-running orchestration with waits | Flow Orchestrator, not direct Apex call | Orchestrator handles waits; Flow.Interview does not |

---

## Recommended Workflow

1. Confirm the Flow is **Autolaunched** (Flow Builder → Start element → "Autolaunched Flow").
2. Read the Flow's input and output variable API names and their Apex-equivalent types.
3. Build a `Map<String, Object>` with typed keys/values.
4. Call `Flow.Interview.createInterview('Flow_API_Name', params)` — confirm exact API name.
5. Wrap `.start()` in try/catch for `Flow.FlowException` (flow-internal failures) and `DmlException` (for governor exhaustion).
6. Read outputs via `getVariableValue(name)` with a cast.
7. Add a test with `@IsTest` that arranges realistic input and asserts the output; the Apex wrapper still needs its own coverage.

---

## Review Checklist

- [ ] Flow is Autolaunched, confirmed in Setup.
- [ ] Parameter map keys match Flow variable API names exactly (case-sensitive).
- [ ] Parameter value types match Flow variable types exactly.
- [ ] `createInterview` + `start()` are wrapped in try/catch.
- [ ] Output retrieval casts to the expected Apex type.
- [ ] Invocation is NOT in a per-record loop over 200 records; Flow accepts a collection.
- [ ] Unit test covers the Apex side end-to-end.

---

## Salesforce-Specific Gotchas

See `references/gotchas.md` for the full list.

1. **Screen Flows fail at runtime** — only Autolaunched Flows start from Apex.
2. **Typo in Flow API name throws at runtime**, not compile time.
3. **Governor limits are charged to the calling transaction**, not reset by the Flow boundary.
4. **Output variable typo returns `null`** silently.
5. **Picklist values must match Flow's expected internal value**, not the label.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `references/examples.md` | Autolaunched Flow invocation, bulk-safe collection pattern |
| `references/gotchas.md` | Screen Flow failures, governor-limit sharing |
| `references/llm-anti-patterns.md` | Common LLM mistakes: hardcoded per-record loops, wrong parameter types |
| `references/well-architected.md` | Ops framing: admin ownership vs deploy cadence |
| `scripts/check_apex_flow_invocation_from_apex.py` | Stdlib lint for per-record invocation and missing try/catch |

---

## Related Skills

- **apex-invocable-method** — the inverse: exposing Apex to Flow
- **apex-trigger-architecture** — where to put the Flow invocation
- **apex-async-architecture** — when to enqueue instead of inline-invoking
