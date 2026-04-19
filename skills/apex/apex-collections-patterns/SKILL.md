---
name: apex-collections-patterns
description: "Use when designing, reviewing, or debugging Apex code that relies on List, Set, or Map collections in triggers, batch classes, or service layers — especially for bulkification, heap management, and safe null handling. Trigger keywords: 'Map<Id, SObject>', 'containsKey', 'retainAll', 'putAll', 'Set intersection', 'heap limit', 'collection in loop', 'unbounded accumulation'. NOT for SOQL query optimization (use soql-fundamentals), NOT for async job design (use apex-queueable-patterns or batch-apex-patterns), NOT for platform cache strategies (use platform-cache)."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Reliability
triggers:
  - "Map containsKey guard null pointer exception apex collections"
  - "retainAll mutates set apex bulkification pattern"
  - "unbounded list accumulation Database.Stateful batch heap limit"
  - "putAll list SObject null Id NullPointerException apex"
  - "nested loop performance Map lookup bulkified trigger"
tags:
  - apex-collections
  - bulkification
  - maps-and-sets
  - heap-management
  - triggers
  - batch-apex
inputs:
  - "Apex class or trigger body using List, Set, or Map"
  - "Whether the context is a trigger, batch, or service layer"
  - "Known governor limit pressure (heap, CPU, SOQL rows)"
outputs:
  - "Refactored collection usage with bulkified patterns"
  - "Heap and null-safety review findings"
  - "Decision guidance on Map vs Set vs List for the given scenario"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-18
---

# Apex Collections Patterns

Use this skill when reviewing or writing Apex code that uses List, Set, or Map to aggregate, de-duplicate, or look up SObject data in triggers, batch classes, or service layers. The skill covers safe null handling, heap-efficient accumulation patterns, and idiomatic bulkification using Map<Id, List<SObject>>.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is the code running in a trigger (200-record scope), a batch execute() chunk (configurable scope), or synchronous Apex? The heap pressure and loop patterns differ.
- Is the class implementing Database.Stateful? If so, any instance-level Map or List grows across every execute() chunk and can exhaust the 6 MB heap before the job finishes.
- Are Set intersection or subtraction operations needed? If so, confirm whether mutating the receiver is acceptable — `retainAll()` and `removeAll()` modify the Set in place.
- What is the maximum expected volume of records? A Map keyed on Id with one value per key is O(n); a Map<Id, List<SObject>> with unbounded inner lists can be O(n²) if records share the same key frequently.

---

## Core Concepts

### Collections Are Heap-Allocated Against the 6 MB Limit

Every List, Set, and Map in an Apex transaction contributes to the heap. A Map<Id, List<SObject>> is the standard bulkification container in trigger handlers: one SOQL returns all related records, and the Map groups them by parent Id. However, each inner List object also consumes heap. In a `Database.Stateful` batch job, instance-level Map or List fields persist across every `execute()` call — growing unboundedly until the job finishes or the 6 MB limit kills the transaction. The Apex Developer Guide states the heap limit as 6 MB for synchronous transactions and async transactions alike.

### Map.get() Returns null — Not an Exception

`Map.get(key)` returns `null` when the key is absent. This is different from Java's behavior and different from what many LLMs assume. Calling `.size()`, iterating, or performing any operation on a `null` return causes a `NullPointerException`. The correct guard is `Map.containsKey(key)` before `Map.get(key)`, or assigning to a variable and null-checking before use. This applies equally to `Trigger.oldMap.get(Id)` inside after-update triggers.

### Set Mutation — retainAll() and removeAll() Are In-Place

`Set.retainAll(otherCollection)` modifies the receiver Set to keep only elements present in both collections (intersection). `Set.removeAll(otherCollection)` removes all elements present in the argument (subtraction). Both are destructive to the original Set. If the original Set is needed after the operation, copy it first with `new Set<Id>(originalSet)` before calling `retainAll()` or `removeAll()`. Building a new Set manually in a loop instead of calling `retainAll()` is verbose, slower, and a frequent LLM anti-pattern.

### putAll(List<SObject>) Keys on the SObject Id Field

`Map<Id, SObject>.putAll(List<SObject>)` inserts all records into the Map using each record's `Id` field as the key. Records with a null `Id` (unsaved records) will cause a `NullPointerException`. Records with duplicate Ids — possible in Trigger.new on update when the same record appears — will silently overwrite the prior entry. This is intentional behavior for trigger maps (most recent value wins) but can be surprising in other contexts.

---

## Common Patterns

### Map<Id, List<SObject>> for Bulkified Trigger Lookups

**When to use:** An after-insert or after-update trigger on a child object needs to group child records by their parent Id before performing a single DML or SOQL operation at the parent level.

**How it works:**
1. Query all relevant parent records using the set of parent Ids extracted from `Trigger.new`.
2. Build a `Map<Id, List<Child__c>>` by iterating the query results once, using `Map.containsKey()` guard before `Map.get()`.
3. Iterate `Trigger.new`, look up each record's parent group from the Map, and accumulate changes.
4. Perform a single bulkified DML call outside all loops.

Reference the `templates/apex/TriggerHandler.cls` scaffold for the handler structure. The collection building belongs in the handler's `afterInsert()` / `afterUpdate()` methods, not in a trigger body directly.

**Why not the alternative:** Querying inside a for loop over `Trigger.new` runs one SOQL per record, burning the 100-query limit on any bulk load of 100+ records.

### Safe Set Intersection With retainAll()

**When to use:** A service method needs to find the overlap between two Sets — for example, the set of record Ids that are both in a new batch and in an existing do-not-process exclusion list.

**How it works:**
1. Construct the first Set from the incoming Ids: `Set<Id> incoming = new Set<Id>(triggerIds);`
2. Construct or load the exclusion Set from a SOQL or Custom Metadata query.
3. Create a working copy if the original Set must be preserved: `Set<Id> overlap = new Set<Id>(incoming);`
4. Call `overlap.retainAll(exclusionIds);` — the result is the intersection in one platform operation.
5. Subtract from the working set to get records that are NOT excluded: `incoming.removeAll(exclusionIds);`

**Why not the alternative:** Building a new Set by iterating and adding manually is O(n) extra code, allocates additional intermediate objects, and is more likely to introduce off-by-one bugs.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Group child records by parent in a trigger | `Map<Id, List<SObject>>` built outside loops | Single pass; avoids SOQL in loop |
| Check if a key exists before reading its value | `Map.containsKey(key)` guard before `Map.get(key)` | `Map.get()` returns null — not an exception |
| Find the overlap between two Id Sets | `Set.retainAll()` on a copy | One platform call; avoids manual loop |
| Convert a query result to a lookup map | `Map<Id, SObject> m = new Map<Id, SObject>(queryResult)` | Map constructor with List<SObject> — idiomatic and concise |
| Accumulate state across Batch execute() chunks | Write results to SObject records at end of each chunk; avoid growing instance-level Maps | Instance-level collections in Database.Stateful grow unboundedly and exhaust heap |
| De-duplicate a List of Ids | `new Set<Id>(myList)` | Set construction removes duplicates in one step |
| Sort a List of custom objects | Implement `Comparator<T>` interface (Spring '24+) | Platform-native sort; avoids hand-rolled comparison logic |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. Identify the Apex context — trigger, batch, or service — and note the scope size and whether `Database.Stateful` is involved.
2. Locate every collection declaration and flag any that are instance-level fields in a `Database.Stateful` class; these are candidates for heap exhaustion.
3. Find every `Map.get()` call and verify a `Map.containsKey()` guard or null-check precedes it; unguarded calls will throw `NullPointerException` when the key is absent.
4. Find every `Set.retainAll()` or `Set.removeAll()` call and confirm the caller does not expect the original Set to be unmodified; if it does, the Set must be copied first.
5. Verify that SOQL queries and DML statements are outside all for loops; collections should accumulate changes across the loop, with a single bulk operation after.
6. Run `python3 scripts/check_apex_collections_patterns.py --manifest-dir <path>` against the target metadata directory.
7. Review the output artifacts against the Review Checklist below before closing the task.

---

## Review Checklist

- [ ] All `Map.get()` calls are preceded by `Map.containsKey()` or the return value is null-checked before use.
- [ ] No `Database.Stateful` batch class accumulates unbounded Map or List values across `execute()` chunks.
- [ ] `Set.retainAll()` and `Set.removeAll()` are called on copies, not the original collection, when the original is needed afterward.
- [ ] No SOQL query or DML statement appears inside a for loop.
- [ ] `Map<Id, SObject>` construction from `List<SObject>` uses the Map constructor (`new Map<Id, SObject>(list)`) rather than a manual loop where possible.
- [ ] Inner Lists in `Map<Id, List<SObject>>` are initialized with `containsKey` guard (not overwriting an existing list).
- [ ] Any `putAll(List<SObject>)` call is used only on records with guaranteed non-null Ids.

---

## Salesforce-Specific Gotchas

1. **Map.get() returns null silently** — unlike Java's optional approach, Apex `Map.get()` returns `null` for a missing key with no exception. Code that chains `.size()` or iterates the result without a null guard will throw `NullPointerException` at runtime — not at compile time — and only on data paths where the key is absent.

2. **Database.Stateful instance collections grow across every execute() chunk** — if a `Database.Stateful` batch class declares a `Map<Id, List<SObject>>` or `List<SObject>` as an instance field, the collection grows with every chunk processed. For a 200-scope batch over 100,000 records, the collection accumulates data from 500 chunks before `finish()` runs. Heap exhaustion causes the entire job to fail with a `LimitException` and no partial rollback. The fix is to flush accumulated data to the database at the end of each `execute()` chunk and keep only lightweight counters in instance fields.

3. **putAll(List<SObject>) silently overwrites duplicate keys** — `Map.putAll(list)` uses each SObject's `Id` as the key. If two records in the list share an Id (possible in upsert scenarios or test data with re-used Ids), the later record silently replaces the earlier one. This produces data loss bugs that are difficult to reproduce in unit tests where each test record has a unique fake Id.

4. **retainAll() and removeAll() mutate the receiver** — calling `mySet.retainAll(otherSet)` changes `mySet` in place. Code that passes a Set to a helper method and then continues to use the Set after the helper called `retainAll()` internally will observe a mutated Set with no indication that mutation occurred. This is a silent logic bug, not an exception.

5. **Set construction from a List does not preserve order** — `new Set<String>(myList)` de-duplicates but does not guarantee insertion order. Code that converts a List to a Set for de-duplication and then iterates the Set expecting the original order will produce non-deterministic behavior across Salesforce releases.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Collection pattern review | Findings on Map null-guard coverage, Set mutation safety, heap accumulation risk, and DML/SOQL loop violations |
| Bulkified trigger handler skeleton | Map<Id, List<SObject>> pattern with null-safe get and single-pass DML, referencing templates/apex/TriggerHandler.cls |
| Batch heap remediation plan | Identifies unbounded instance-level collections in Database.Stateful classes and recommends flush-per-chunk pattern |

---

## Related Skills

- `apex/trigger-framework` — use when the handler structure around the collection patterns is the primary concern.
- `apex/batch-apex-patterns` — use when the broader batch design (scope, start/execute/finish, error handling) is the focus.
- `apex/governor-limits` — use when heap or CPU limits are being hit and broader limit strategy is needed.
- `apex/soql-fundamentals` — use when the underlying SOQL driving collection population needs optimization.
- `apex/exception-handling` — use when NullPointerException from unguarded Map.get() is part of a broader error handling review.
