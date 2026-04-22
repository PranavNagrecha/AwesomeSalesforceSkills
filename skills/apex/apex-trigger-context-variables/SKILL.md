---
name: apex-trigger-context-variables
description: "Apex Trigger.new / Trigger.old / Trigger.newMap / Trigger.oldMap / Trigger.isInsert etc.: when each is populated, null-safety, recursion depth, trigger event matrix. NOT for trigger framework architecture (use apex-trigger-handler-framework). NOT for bulk patterns (use apex-bulkification-patterns)."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
tags:
  - apex
  - triggers
  - context-variables
  - trigger-new
  - trigger-old
triggers:
  - "why is trigger.oldmap null in before insert"
  - "trigger.new vs trigger.newmap performance difference"
  - "trigger context variable matrix insert update delete"
  - "trigger.isexecuting vs system.isbatch distinguish context"
  - "trigger.newmap nullpointerexception before insert"
  - "accessing old values in after update trigger"
inputs:
  - Trigger events in scope (before/after × insert/update/delete/undelete)
  - Whether Trigger.newMap/oldMap needed
  - Recursion-control requirement
outputs:
  - Correct context-variable usage per event
  - Null-safe access pattern
  - Event matrix documentation
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-21
---

# Apex Trigger Context Variables

Activate when writing or reviewing an Apex trigger or a trigger handler method that consumes Trigger context variables. Each variable (`Trigger.new`, `Trigger.old`, `Trigger.newMap`, `Trigger.oldMap`, `Trigger.isExecuting`, the event booleans) is populated only in specific events; using one in the wrong event causes `NullPointerException` or wrong semantics.

## Before Starting

- **Memorize the context matrix.** `Trigger.old` and `Trigger.oldMap` are null in `before insert` and `after insert`. `Trigger.newMap` is null in `before insert` (records have no Id yet).
- **Know the delete semantics.** In `before delete` / `after delete`, only `Trigger.old` and `Trigger.oldMap` are populated. `Trigger.new` is null.
- **Guard recursion.** Triggers can re-enter; a static `Set<Id> processedIds` or a framework flag is mandatory for trigger-causing-trigger scenarios.

## Core Concepts

### The event matrix

| Event | new | newMap | old | oldMap |
|---|---|---|---|---|
| before insert | ✓ | null (no Id) | null | null |
| after insert | ✓ | ✓ | null | null |
| before update | ✓ | ✓ | ✓ | ✓ |
| after update | ✓ | ✓ | ✓ | ✓ |
| before delete | null | null | ✓ | ✓ |
| after delete | null | null | ✓ | ✓ |
| after undelete | ✓ | ✓ | null | null |

### Modifying vs reading

`Trigger.new` records are **read-write** in `before` events (mutate fields directly). In `after` events, `Trigger.new` is read-only — attempts to modify throw. Updates in `after` require explicit DML on a separate list.

### Recursion and re-entry

Updating a record inside its own trigger re-fires the trigger. Guard with a framework-level static boolean or an ID set.

### `Trigger.size`

Scalar count — useful for bulk heuristics, but prefer `Trigger.new.size()`.

## Common Patterns

### Pattern: Before-update field stamping

```
for (Account a : Trigger.new) {
    Account oldA = Trigger.oldMap.get(a.Id);
    if (a.Industry != oldA.Industry) a.Industry_Changed_On__c = Datetime.now();
}
```

### Pattern: After-insert related-record creation

```
List<Contact> defaults = new List<Contact>();
for (Account a : Trigger.new) defaults.add(new Contact(AccountId = a.Id, LastName = 'Primary'));
insert defaults;
```

### Pattern: Before-delete gate

```
for (Account a : Trigger.old) {
    if (a.Is_Protected__c) a.addError('Cannot delete protected account');
}
```

## Decision Guidance

| Need | Access |
|---|---|
| Read new values, no Id needed | `Trigger.new` |
| Need Id (after insert and beyond) | `Trigger.newMap` |
| Compare old vs new | `Trigger.new` + `Trigger.oldMap.get(record.Id)` |
| Delete validation | `Trigger.old` / `Trigger.oldMap` |
| Determine context programmatically | `Trigger.isInsert`, `Trigger.isBefore`, etc. |

## Recommended Workflow

1. Decide trigger events (before/after × DML).
2. Consult the event matrix; confirm which context variables are populated.
3. Route each event to a dedicated handler method — never monolithic trigger body.
4. For before-update, pair `Trigger.new` iteration with `Trigger.oldMap.get(rec.Id)` lookup.
5. Add recursion guard via framework static flag.
6. Bulk-safe everything: no SOQL/DML in loops.
7. Unit test each event with `Test.startTest()` and explicit record setup.

## Review Checklist

- [ ] Correct context variable per event (not relying on null-populated ones)
- [ ] Null-safe access for oldMap in before-insert / after-insert
- [ ] Handler methods split by event
- [ ] Recursion guard in place
- [ ] Bulkified: no per-record SOQL/DML
- [ ] Before events mutate `Trigger.new`; after events use DML on new lists
- [ ] Tests cover each event with bulk collections (200+)

## Salesforce-Specific Gotchas

1. **`Trigger.newMap` is null in before-insert.** Records have no IDs yet; you cannot index by Id until after-insert.
2. **Modifying `Trigger.new` in after events throws.** Use a separate DML pass.
3. **`Trigger.old` is NOT populated in insert contexts.** Default to null checks for pre-existing state.

## Output Artifacts

| Artifact | Description |
|---|---|
| Event matrix reference | Quick-lookup table for which variable in which event |
| Handler template | Skeleton trigger + handler class |
| Recursion guard class | Framework static boolean |

## Related Skills

- `apex/apex-trigger-handler-framework` — framework architecture
- `apex/apex-bulkification-patterns` — bulk-safe DML
- `apex/apex-async-patterns` — async DML patterns when sync unsafe
