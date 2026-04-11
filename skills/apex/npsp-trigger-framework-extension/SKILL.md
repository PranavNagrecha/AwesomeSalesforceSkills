---
name: npsp-trigger-framework-extension
description: "Use when extending the NPSP Trigger-Driven Trigger Management (TDTM) framework with custom Apex handler classes — covering class authorship, DmlWrapper return patterns, Trigger_Handler__c registration, load order, recursion guards, and test isolation. NOT for standard Apex triggers outside of NPSP, general trigger-handler framework design, or Nonprofit Cloud (NPC) which replaced NPSP in new orgs."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
tags:
  - npsp
  - tdtm
  - trigger-framework
  - apex
  - nonprofit
  - custom-handler
  - dml-wrapper
inputs:
  - NPSP version installed in target org (determines available npsp.TDTM_Runnable API surface)
  - Business requirement driving the custom handler (object and trigger actions needed)
  - Whether the org already has custom TDTM handlers (for load order planning)
  - "Deployment method: managed vs unmanaged metadata"
outputs:
  - A deployable Apex class extending npsp.TDTM_Runnable with correct run() signature
  - A npsp__Trigger_Handler__c record definition (custom metadata or DML in test setup) for registration
  - A test class using npsp.TDTM_Global_API.setTdtmConfig() for isolated, repeatable test runs
  - Recursion guard pattern using a static Set<Id>
triggers:
  - "custom Apex logic needed on NPSP object without breaking NPSP trigger handlers"
  - "NPSP upgrade deleted custom trigger handler after deployment"
  - "DML inside TDTM run method causing recursion or NPSP conflicts"
  - "npsp__Trigger_Handler__c registration not firing on expected object events"
  - "test class not isolating NPSP trigger handlers for unit testing"
dependencies:
  - apex/trigger-framework
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-11
---

# NPSP Trigger Framework Extension (TDTM)

This skill activates when a practitioner needs to add custom Apex logic that participates in NPSP's Trigger-Driven Trigger Management (TDTM) pipeline — the built-in trigger framework used by the Nonprofit Success Pack managed package. It covers the complete lifecycle: authoring a handler class, returning results via DmlWrapper instead of issuing direct DML, registering the handler via Trigger_Handler__c records, controlling execution order, guarding against recursion with static state, and isolating tests from the packaged handler chain.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the org has NPSP installed and identify the namespace prefix in use (`npsp` for production orgs, potentially different in sandboxes cloned from scratch orgs).
- Determine which sObject the new handler targets and which trigger actions are required (BeforeInsert, AfterInsert, AfterUpdate, etc.).
- List existing custom Trigger_Handler__c records on the same object — use the highest `npsp__Load_Order__c` value among them as the baseline for your new handler's load order to avoid silent ordering conflicts.
- Confirm whether this is a managed-package deployment context or an unmanaged metadata deployment. The `npsp__Owned_by_Namespace__c` field behavior differs between contexts.
- The most common wrong assumption practitioners make: assuming TDTM works like a standard Apex trigger handler, where you can issue DML directly and return void. TDTM requires all DML to be batched into a `DmlWrapper` return value — direct DML inside `run()` causes double-trigger recursion and governor limit problems.

---

## Core Concepts

### TDTM_Runnable Contract

Every NPSP custom trigger handler must extend `npsp.TDTM_Runnable` and override the `run()` method with this exact signature:

```apex
public override npsp.TDTM_Runnable.DmlWrapper run(
    List<SObject> newlist,
    List<SObject> oldlist,
    npsp.TDTM_Runnable.Action triggerAction,
    Schema.DescribeSObjectResult objResult
) {
    npsp.TDTM_Runnable.DmlWrapper wrapper = new npsp.TDTM_Runnable.DmlWrapper();
    // Add records to wrapper.objectsToInsert, objectsToUpdate, objectsToDelete
    return wrapper;
}
```

NPSP's dispatcher calls all registered handlers in load order and accumulates each handler's DmlWrapper into a single, batched DML operation after all handlers have run. This design ensures that custom handler DML participates in the same transaction as package DML and respects the single-trigger-per-object Salesforce best practice enforced by NPSP.

The `triggerAction` parameter maps to `npsp.TDTM_Runnable.Action` enum values: `BeforeInsert`, `BeforeUpdate`, `BeforeDelete`, `AfterInsert`, `AfterUpdate`, `AfterDelete`, `AfterUndelete`.

### Trigger_Handler__c Registration

A custom handler is invisible to NPSP until a corresponding `npsp__Trigger_Handler__c` record exists. The critical fields are:

| Field | Purpose | Notes |
|---|---|---|
| `npsp__Class__c` | Fully-qualified class name | Do not include `npsp.` prefix — this is your class name only |
| `npsp__Object__c` | API name of the sObject | e.g. `Contact`, `npe01__OppPayment__c` |
| `npsp__Trigger_Action__c` | Semicolon-delimited list of actions | e.g. `AfterInsert;AfterUpdate` |
| `npsp__Load_Order__c` | Integer execution order | Use values higher than packaged handlers; leave gaps of 10+ between custom handlers |
| `npsp__Owned_by_Namespace__c` | Protects the record from NPSP upgrades | Set to your namespace or leave blank — **never** set to `npsp` unless you intend the package to manage it |
| `npsp__Active__c` | Toggles the handler on/off | Default true; useful for debugging |

Packaged NPSP handlers typically use load orders in the 1–50 range. Start custom handlers at 100 or higher to ensure they run after packaged logic has established relationship state.

### Recursion Guard with Static State

NPSP does not expose a public recursion flag API for custom code. Custom handlers cannot add flags to the internal `TDTM_ProcessControl.flag` enum. The correct recursion guard is a static `Set<Id>` declared in the handler class:

```apex
private static Set<Id> processedIds = new Set<Id>();
```

Check and populate `processedIds` at the start of each relevant record iteration inside `run()`. Reset it only in test setup, never in production flow.

### Test Isolation via setTdtmConfig

NPSP's test isolation requirement is non-obvious: test classes must call `npsp.TDTM_Global_API.setTdtmConfig()` to replace the full packaged handler chain with a minimal or custom-only chain. Do **not** call `getTdtmConfig()` before `setTdtmConfig()` — as of the versions covered by this skill, `getTdtmConfig()` populates a static cache, and when `setTdtmConfig()` then tries to override it, the cache entry for your custom handler is dropped, causing it to silently never run during tests. The correct pattern is to pass a pre-built list directly to `setTdtmConfig()`.

---

## Common Patterns

### Pattern 1: Custom Handler Reacting to Opportunity Closure

**When to use:** When you need to create, update, or stamp related records whenever an Opportunity moves to Closed Won — after NPSP's own payment and rollup handlers have already fired.

**How it works:**
1. Set `npsp__Load_Order__c` to a value above the highest packaged handler on Opportunity (check the NPSP Setup tab or query `npsp__Trigger_Handler__c` for Opportunity records).
2. In `run()`, filter `newlist` where `StageName == 'Closed Won'` and `triggerAction == npsp.TDTM_Runnable.Action.AfterUpdate`.
3. Build the related records and add them to `wrapper.objectsToInsert`.
4. Return the wrapper; NPSP batches the insert after all handlers complete.

**Why not direct DML:** Issuing `insert` inside `run()` fires that object's trigger chain immediately and within the same call stack, risking recursive TDTM dispatch and consuming governor limits before the rest of the handler chain has run.

### Pattern 2: Conditional Handler Toggle via Active Flag

**When to use:** During rollout, debugging, or environment-specific deployments where the handler should be off in certain sandboxes.

**How it works:** The `npsp__Active__c` field on `npsp__Trigger_Handler__c` acts as a runtime toggle. A scratch org or sandbox deployment script can set it to false for that environment without code changes. Test classes that call `setTdtmConfig()` with a handler list control activation programmatically.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need logic after NPSP payment creation on Opportunity | Register handler on Opportunity AfterUpdate at load order 100+ | Ensures NPSP payment handler (typically order 1-10) has already fired |
| Need to create related records from handler logic | Add to DmlWrapper.objectsToInsert | Avoids re-entrant TDTM dispatch from direct DML |
| Need to prevent double-processing in a batch context | Static Set<Id> recursion guard | TDTM_ProcessControl enum is package-private; static Set is the only extensible option |
| Handler silently not firing in tests | Use setTdtmConfig() with explicit handler list | getTdtmConfig() cache bug causes silent drops |
| Handler deleted after NPSP upgrade | Set npsp__Owned_by_Namespace__c to non-npsp value | Package upgrade routine only deletes records owned by 'npsp' namespace |
| Org migrating from NPSP to Nonprofit Cloud (NPC) | Evaluate NPC trigger extensibility approach | TDTM does not exist in NPC; this skill does not apply |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Gather context** — Confirm NPSP is installed, identify the target sObject and trigger actions, query `npsp__Trigger_Handler__c` to find the highest existing load order for that object, and note any existing custom handlers.
2. **Author the handler class** — Extend `npsp.TDTM_Runnable`, override `run()` with the correct four-parameter signature, add a static `Set<Id>` recursion guard, and batch all related-record DML into `DmlWrapper` (never direct DML).
3. **Register the handler** — Create the `npsp__Trigger_Handler__c` record with `npsp__Class__c`, `npsp__Object__c`, `npsp__Trigger_Action__c` (semicolon-delimited), `npsp__Load_Order__c` (start at 100+), and `npsp__Owned_by_Namespace__c` set to your org namespace or a custom value — never `npsp`.
4. **Write isolated tests** — Call `npsp.TDTM_Global_API.setTdtmConfig()` first with an explicit handler list containing only your custom handler; do **not** call `getTdtmConfig()` beforehand. Use `System.runAs` where context matters and assert on DML outcomes, not on internal state.
5. **Validate execution order** — In a sandbox, verify the handler fires by inserting/updating the target records and checking logs or results. Confirm load order does not conflict with packaged handlers by reviewing the full `npsp__Trigger_Handler__c` list.
6. **Deploy** — Include the Apex class, test class, and the `npsp__Trigger_Handler__c` record as part of the deployment package. Verify `npsp__Owned_by_Namespace__c` is set to protect the record from upgrade deletion.
7. **Post-deploy check** — After the next NPSP upgrade cycle, confirm the handler record still exists and is still active. Set up a monitoring query or validation script to catch silent deletions.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Handler class extends `npsp.TDTM_Runnable` and overrides `run()` with the exact four-parameter signature
- [ ] All related-record DML is added to `DmlWrapper` fields — no direct `insert`, `update`, or `delete` calls inside `run()`
- [ ] `npsp__Trigger_Handler__c` record has `npsp__Owned_by_Namespace__c` set to a non-`npsp` value
- [ ] `npsp__Load_Order__c` is set above the highest packaged handler for that object (confirm by querying existing records)
- [ ] Test class uses `npsp.TDTM_Global_API.setTdtmConfig()` without a prior `getTdtmConfig()` call
- [ ] Static recursion guard (`Set<Id>`) is in place for any handler that could be triggered by its own DML wrapper output
- [ ] Handler is verified in sandbox before production deployment

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **NPSP Upgrade Silently Deletes Unprotected Custom Handler Records** — If `npsp__Owned_by_Namespace__c` is blank or set to `npsp`, the NPSP package upgrade routine treats the record as package-owned and may delete it. The handler disappears silently with no deploy error or warning. Always set this field to your org's namespace or a custom sentinel value.
2. **getTdtmConfig() Cache Bug Drops Custom Handlers in Tests** — Calling `getTdtmConfig()` before `setTdtmConfig()` in a test causes a static cache to be populated. When `setTdtmConfig()` then tries to register the custom handler, the cache entry for that class is already set to the packaged state, causing the custom handler to be silently skipped during the test run. Tests pass but the handler is never actually tested.
3. **Direct DML Inside run() Triggers Recursive TDTM Dispatch** — Any `insert`, `update`, or `delete` statement inside `run()` fires that object's full trigger pipeline again, including all NPSP handlers. This doubles governor limit consumption, risks an infinite recursion in some configurations, and violates NPSP's design contract. Use `DmlWrapper` exclusively.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Custom TDTM handler class | Apex class extending npsp.TDTM_Runnable, ready to deploy |
| Trigger_Handler__c record | Registration record for the custom handler, protected from upgrade deletion |
| Test class | Isolated test using setTdtmConfig() with assertions on DML outcomes |

---

## Related Skills

- apex/trigger-framework — general trigger handler framework design for orgs not using NPSP TDTM
