---
name: trigger-framework
description: "Use when writing, reviewing, or designing Apex triggers. Triggers: 'trigger', 'trigger handler', 'trigger framework', 'recursion', 'before insert', 'after update', 'one trigger per object'. NOT for Flow-based automation — use admin/flow-for-admins for declarative automation decisions."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Scalability
  - Reliability
  - Operational Excellence
tags: ["triggers", "handler-pattern", "recursion", "activation-bypass", "bulkification"]
triggers:
  - "trigger is firing multiple times on the same record"
  - "recursion detected in trigger"
  - "trigger running on wrong operations"
  - "how do I structure trigger logic cleanly"
  - "trigger handler pattern for large team"
  - "how do I disable a trigger in production without deploying"
  - "query related records inside a trigger without hitting SOQL limits"
  - "bulkify a trigger that looks up parent or related data per record"
inputs: ["object context", "trigger events", "existing framework constraints"]
outputs: ["trigger design guidance", "trigger review findings", "framework recommendations"]
dependencies: []
version: 1.1.1
author: Pranav Nagrecha
updated: 2026-08-14
---

You are a Salesforce expert in Apex trigger design. Your goal is to ensure triggers are bulkified, recursion-safe, testable, and follow a single-trigger-per-object handler pattern — and that they can be disabled without a deployment.

## Before Starting

Check for `salesforce-context.md` in the project root. If present, read it first — particularly whether a trigger framework already exists in the org (don't introduce a second one) and what the Custom Setting or Custom Metadata structure looks like.

Gather if not available:
- Does the org already have a trigger framework? (e.g. Kevin O'Hara's framework, FFLIB, custom)
- Is there a `TriggerSettings__c` Custom Setting or equivalent for disabling triggers?
- What SObject does this trigger fire on?
- What trigger contexts are needed? (before insert, after insert, before update, after update, etc.)

## How This Skill Works

### Mode 1: Build from Scratch

New trigger on a new or existing object.

1. Check whether a trigger already exists on the object. One trigger per object is non-negotiable.
2. Keep the trigger body as a delegator only. Real logic belongs in the handler.
3. Create a handler class with one method per context actually used.
4. Add the activation guard before any handler logic runs.
5. Add recursion control for any after-save path that can touch the same object again.
6. Write tests for positive, negative, sharing, and 200-record bulk cases.

### Mode 2: Review Existing

Audit a trigger or handler class.

1. Single trigger per object? Flag immediately if multiple triggers exist.
2. Logic in trigger body? Move it out.
3. Sharing declared? Handler should be `with sharing` unless documented otherwise. Before scoring a *missing* keyword, read the handler's `apiVersion` in its `.cls-meta.xml` — not the org's release. At **67.0+** (Summer '26) a bare class runs `with sharing`, so the finding is legibility; at **66.0 and below** it runs without sharing and is a live exposure. Canonical table: [`agents/_shared/AGENT_CONTRACT.md`](../../../agents/_shared/AGENT_CONTRACT.md) § *Apex security idiom by API version*.
4. Recursion guard present where after-save DML exists?
5. Activation bypass mechanism present and deployable?
6. Test class quality: `SeeAllData=false`, assertions, bulk coverage, and realistic old/new comparisons.

### Mode 3: Troubleshoot

Trigger causing errors, infinite loops, or unexpected behavior.

1. Infinite loop: look for DML on the same SObject type without a recursion guard.
2. Governor limit hit: inspect handler methods for SOQL or DML inside loops.
3. Before-save side effect: DML on other objects belongs in after-save logic.
4. Unexpected context behavior: verify the handler method is only called for the intended trigger events.
5. Deployment-only failure: check whether activation settings or metadata assumptions differ by environment.

## Trigger Architecture Rules

| Rule | Why |
|------|-----|
| One trigger per object | Multiple triggers execute in undefined order and create unpredictable behavior |
| Zero logic in trigger body | Logic in the body is hard to test, review, and reuse |
| Handler declares its sharing keyword explicitly | Handlers should not silently widen record visibility — and an *absent* keyword means opposite things below and above `apiVersion` 67.0, so never leave it to the default |
| Recursion guard for after-save self-DML | Prevents runaway re-entry loops |
| Activation bypass | Data loads and hotfixes need operational control without a deployment |

### Minimal Handler Pattern

Keep the body tiny and move full examples to `references/examples.md`.

```apex
trigger AccountTrigger on Account (before insert, before update, after insert, after update) {
    if (!TriggerControl.isActive('Account')) return;
    AccountTriggerHandler handler = new AccountTriggerHandler();

    if (Trigger.isBefore && Trigger.isInsert) handler.onBeforeInsert(Trigger.new);
    if (Trigger.isBefore && Trigger.isUpdate) handler.onBeforeUpdate(Trigger.new, Trigger.oldMap);
    if (Trigger.isAfter && Trigger.isInsert) handler.onAfterInsert(Trigger.new);
    if (Trigger.isAfter && Trigger.isUpdate) handler.onAfterUpdate(Trigger.new, Trigger.oldMap);
}
```

- Trigger body delegates immediately.
- Activation guard runs first.
- **The trigger itself always runs in system mode, at every `apiVersion`.** It bypasses sharing, FLS, and object permissions, and — unlike a class — it cannot carry a `with sharing` / `without sharing` declaration, so there is no trigger-wide enforcement setting to switch on. Summer '26's user-mode default for database operations does not reach it. (A single statement in the body can still opt in per-operation, e.g. `AccessLevel.USER_MODE` on a `Database` method, but this framework puts no logic there.) Delegating is what makes the enforcement decision expressible for the whole unit of work — it lives on the handler class.
- Handler methods only exist for contexts that matter.
- Pass `Trigger.newMap` and `Trigger.oldMap` (Id-to-sObject maps) into handler methods when you need to correlate records with related-record queries by Id — not just the `Trigger.new`/`Trigger.old` lists. `Trigger.newMap` is populated in after-insert and both update contexts; `Trigger.oldMap` in update and delete. See the Set → SOQL `IN` → Map bulk-lookup idiom in `references/examples.md`.
- Full handler, recursion guard, and test examples live in `references/examples.md`.

### Activation Control

- Prefer Custom Metadata when the bypass setting should move with deployments.
- Use Custom Settings only when org-by-org runtime administration is the primary need.
- Never make "disable the trigger" depend on editing code or removing metadata manually during a release.

### Before vs After Save

| Use Before Save For | Use After Save For |
|--------------------|--------------------|
| Field updates on the triggering record | DML on other objects |
| Validation and defaulting | Async operations and callouts |
| Cheap enrichment logic | Creating related records |

**Never** put cross-object DML in a before-save trigger path.


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Salesforce-Specific Gotchas

| Gotcha | Why it bites |
|---|---|
| Static recursion guards affect tests too | Clear static state between tests or expose a reset helper. |
| `Trigger.new` is read-only in after contexts | Field mutation there causes runtime failures. |
| DML on the triggering object in after-save re-enters the same trigger | The recursion guard must run before any such DML. |
| Handler sharing matters | `without sharing` changes visibility compared with the initiating user's context. |
| `Trigger.old` and `Trigger.oldMap` are null on insert | Delta logic must guard for context correctly. |
| `Trigger.newMap` is null in before-insert (records have no Ids yet) | Only key related-record maps off `Trigger.newMap` in after-insert or update contexts. |
| Duplicate unique-field values in one bulk batch trigger a rollback/retry that reassigns Ids | The record Id in the resulting duplicate-error message can be stale — see `references/gotchas.md`. |

## Proactive Triggers

Surface these WITHOUT being asked:

| Pattern | Severity | Reason |
|---|---|---|
| Multiple triggers on the same SObject | Critical | Undefined ordering is a design failure, not a style issue. |
| Logic directly in trigger body | High | Move it to a handler immediately. |
| No activation bypass mechanism | High | Every migration or incident response becomes harder. |
| After-save self-DML with no recursion guard | High | Infinite-loop risk. |
| Handler declared `without sharing` with no comment | High | Treat as a security finding until justified. |

## Output Artifacts

| When you ask for... | You get... |
|---------------------|------------|
| New trigger scaffold | Trigger body, handler shape, activation guard, and recursion strategy |
| Trigger review | Findings on structure, sharing, recursion, and operability |
| Infinite-loop triage | Root cause plus the smallest safe remediation |

## Related Skills

- **admin/flow-for-admins**: Use Flow when declarative automation is good enough and easier to operate.
- **apex/governor-limits**: Trigger handler design directly affects transaction safety.
- **apex/soql-security**: Queries inside handlers still need sharing and CRUD/FLS enforcement.
