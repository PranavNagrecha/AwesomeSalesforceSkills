---
name: apex-collections-patterns
description: "Use when designing, reviewing, or debugging Apex code that relies on List, Set, or Map collections in triggers, batch classes, or service layers — especially for bulkification, heap management, and safe null handling. Trigger keywords: 'Map<Id, SObject>', 'containsKey', 'retainAll', 'putAll', 'Set intersection', 'heap limit', 'collection in loop', 'unbounded accumulation', 'group by parent Id', 'Comparator', 'Comparable', 'equals and hashCode', 'keySet', 'Set<String> duplicates', '15 vs 18 character Id', 'modify collection while iterating', 'List index out of bounds'. NOT for SOQL query optimization — use apex/soql-fundamentals. NOT for async job design — use apex/apex-queueable-patterns or apex/batch-apex-patterns. NOT for Platform Cache strategies — use apex/platform-cache. NOT for wrapper/DTO class design — use apex/apex-wrapper-class-patterns. NOT for CPU-time tuning — use apex/apex-cpu-and-heap-optimization."
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
  - "group child records by parent Id in Apex"
  - "sort a list of sObjects by two fields in Apex"
  - "use a custom class as a Map key in Apex"
  - "why does my Set<String> contain the same record twice"
  - "remove entries from a map while iterating over it"
  - "replace a nested loop over two lists with a Map lookup"
  - "index a query result by Id without writing a loop"
  - "build a Map of String to List of records in Apex"
  - "list index out of bounds exception in an Apex trigger"
tags:
  - apex-collections
  - bulkification
  - maps-and-sets
  - heap-management
  - triggers
  - batch-apex
  - comparator
  - equals-and-hashcode
inputs:
  - "Apex class or trigger body using List, Set, or Map"
  - "Whether the context is a trigger, batch, or service layer"
  - "Known governor limit pressure (heap, CPU, SOQL rows)"
  - "The access pattern the collection has to serve — ordered, membership, or keyed lookup"
  - "Whether keys are record Ids, Strings derived from Ids, or a custom class"
outputs:
  - "Refactored collection usage with bulkified patterns"
  - "Heap and null-safety review findings"
  - "Decision guidance on Map vs Set vs List for the given scenario"
  - "A deployable CollectionUtils class, Comparator, and custom key class with tests"
  - "Checker findings from scripts/check_apex_collections_patterns.py"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Apex Collections Patterns

Use this skill when reviewing or writing Apex code that uses List, Set, or Map to aggregate, de-duplicate, or look up SObject data in triggers, batch classes, or service layers. The skill covers safe null handling, heap-efficient accumulation patterns, and idiomatic bulkification using Map<Id, List<SObject>>.

It owns the container decision and the key semantics: choosing List/Set/Map by access pattern, grouping and indexing idioms, sObject and custom-type equality as keys, sorting with `Comparable` vs `Comparator`, safe iteration and mutation, and testing collection logic with deterministic ordering. Adjacent skills own the rest: `apex/apex-wrapper-class-patterns` owns wrapper DTO design, `apex/apex-cpu-and-heap-optimization` owns CPU-time tuning once the algorithm shape is already right, `apex/apex-design-patterns` owns the layering these helpers live inside, and `apex/soql-fundamentals` owns the query that produces the list you are about to index.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is the code running in a trigger (200-record scope), a batch execute() chunk (configurable scope), or synchronous Apex? The heap pressure and loop patterns differ.
- Is the class implementing Database.Stateful? If so, any instance-level Map or List grows across every execute() chunk and can exhaust the heap before the job finishes.
- Are Set intersection or subtraction operations needed? If so, confirm whether mutating the receiver is acceptable — `retainAll()` and `removeAll()` modify the Set in place.
- What is the maximum expected volume of records? A Map keyed on Id with one value per key is O(n); a Map<Id, List<SObject>> with unbounded inner lists can be O(n²) if records share the same key frequently.

---

## Questions to Ask Before Configuring

Ask these before the first `new Map<...>` is written. Each one maps to a documented behaviour in `references/gotchas.md` that silently produces wrong data rather than an exception.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "What is the access pattern — position, membership, or lookup by key?" | List is index-addressable, a Set is not ("you can't access a set element at a specific index", `apexdev` L1641), and a Map is the only one with O(1) keyed retrieval | The container, chosen once, instead of a List that later grows a `contains()` in a loop |
| "Where do the keys come from — record Ids, an external system's strings, or a composite?" | `Id` normalizes a 15-character value to 18 (`apexdev` L1255); `String` does not, and String keys are case-sensitive (`apexdev` L1697) | Whether `Set<Id>` or `Set<String>` is correct, and whether an integration payload will silently produce two entries per record |
| "Can any record in the list be unsaved when the map is built?" | A map key may hold null and a repeated key overwrites the earlier entry (`apexdev` L1694–L1696), so unsaved records collapse into one slot | Whether `new Map<Id, SObject>(list)` is safe or the map must be built with an explicit null check |
| "Is a custom class going to be a Map key or a Set element?" | Uniqueness of user-defined key types comes from `equals` and `hashCode` you write (`apexdev` L1700); without them the types compare by reference (`apexdev` L2135–L2138) | Whether the class needs both methods, and whether its fields must be immutable after insertion |
| "Does anything downstream depend on the order of this collection?" | Set and Map iteration order is deterministic per code path but is not insertion order (`apexdev` L1642, L1692), and default `List.sort()` on sObjects uses a fixed field sequence (`apexdev` L10245–L10258) | Whether a `Comparator` is required, and what the test should assert instead of "the list has 3 elements" |
| "Will the collection be edited while it is being iterated?" | "Modifying a collection's elements while iterating through that collection is not supported and causes an error" (`apexdev` L3182–L3183), and `keySet()` is a live view of the map (`apexrefguide` L222249) | The temporary collection the removals or additions have to go into |
| "What is the largest realistic volume this collection will hold in one transaction?" | There is no item-count limit on a collection, only the heap ceiling — 6 MB sync, 12 MB async (`apexdev` L1431, L19577) | The number the bulk test uses, and whether the design needs a per-chunk flush instead of accumulation |

What a proper configuration adds over just doing it: the container is chosen from the access pattern rather than from habit, key semantics are asserted in a test rather than assumed, and the failure modes that produce silently wrong data — a collapsed null key, a duplicated Id string, a mutable custom key — are caught by `scripts/check_apex_collections_patterns.py` before a reviewer has to notice them.

---

## Core Concepts

### Collections Are Bounded By Heap, Not By Item Count

The Apex Developer Guide is explicit: "There is no limit on the number of items a collection can hold. However, there is a general limit on heap size" (`apexdev` L1431). That ceiling is 6 MB for synchronous transactions and 12 MB for asynchronous ones (`apexdev` L19577). A Map<Id, List<SObject>> is the standard bulkification container in trigger handlers: one SOQL returns all related records, and the Map groups them by parent Id. Each inner List is a separate allocation on the same budget. In a `Database.Stateful` batch job, instance-level Map or List fields persist across every `execute()` call, so the accumulation grows against a ceiling that does not reset even though the per-chunk governor counters do (`apexdev` L19530–L19531).

### Map.get() Returns null — Not an Exception

`Map.get(key)` "Returns the value to which the specified key is mapped, or null if the map contains no value for this key" (`apexrefguide` L222556–L222557). Calling `.size()`, iterating, or dereferencing a field on that null causes a `NullPointerException` at the *use* site, not at the `get()`. Three correct guards, in increasing order of terseness: `containsKey()` before `get()`; assign to a local and null-check; or the safe navigation operator, which "short-circuits expressions that attempt to operate on a null value and returns null instead of throwing a NullPointerException" (`apexdev` L2353–L2355) — `accountsById.get(c.AccountId)?.Industry`.

### Set Mutation — retainAll() and removeAll() Are In-Place

`Set.retainAll(otherCollection)` "Retains only the elements in this set that are contained in the specified list", returning "true if the original set changed as a result of the call" (`apexrefguide` L230750–L230751, L230771). `Set.removeAll()` is the mirror image. Both are destructive to the receiver. If the original Set is needed after the operation, copy it first with `new Set<Id>(originalSet)`. `CollectionUtils.intersect()` and `subtract()` in `references/code-examples.md` §1 wrap exactly this.

### Key Semantics Differ By Key Type

| Key type | Uniqueness rule | Grounded at |
|---|---|---|
| `Id` | `==` is case-sensitive and does not distinguish 15- from 18-character forms; an `Id`-typed 15-character value is converted to 18 | `apexdev` L2135–L2136, L1255 |
| `String` | Case-sensitive as a Map key or Set element — two keys differing only by case are distinct entries | `apexdev` L1697–L1699; `apexrefguide` L230262–L230263 |
| `sObject` | Determined by comparing the objects' field values; changing the record after insertion breaks the mapping | `apexdev` L1700–L1704 |
| User-defined class | Determined by the `equals` and `hashCode` methods you provide | `apexdev` L1700, L7044–L7045 |
| `Decimal` | "Two Decimal objects that are numerically equivalent but differ in scale (such as 1.1 and 1.10) generally don't have the same hashcode" | `apexdev` L1245–L1247 |

### keySet() Is a View; values() Is a List

"With the keySet() method, the returned keySet is backed by the map and reflects any changes made to the map, and vice versa" (`apexrefguide` L222249–L222250, restated at L222682). So `for (Id k : m.keySet()) { m.remove(k); }` is the documented "modifying a collection while iterating" error, and `Set<Id> snapshot = new Set<Id>(m.keySet())` is the fix. `values()` is documented as returning "a list that contains all the values in the map" with deterministic order (`apexrefguide` L222901–L222915) and carries no backing note.

### Sorting Needs an Explicit Order

`List.sort()` on sObjects follows a fixed sequence: the sObject type label, then `Name`, then standard fields alphabetically excluding Id and Name, then custom fields alphabetically (`apexdev` L10245–L10258). Primitives sort ascending with nulls first (`apexrefguide` L221858–L221872). For anything else, "You can sort custom types (your Apex classes) if they implement the Comparable interface. Alternatively, a class implementing the Comparator interface can be passed as a parameter to the List.sort method" (`apexdev` L1537–L1539). The `Comparator` contract carries one hard obligation: "Your implementation must explicitly handle null inputs in the compare() method to avoid a null pointer exception" (`apexrefguide` L202283–L202284).

---

## Common Patterns

### Map<Id, List<SObject>> for Bulkified Trigger Lookups

**When to use:** An after-insert or after-update trigger on a child object needs to group child records by their parent Id before performing a single DML or SOQL operation at the parent level.

**How it works:**
1. Query all relevant parent records using the set of parent Ids extracted from `Trigger.new`.
2. Build a `Map<Id, List<Child__c>>` by iterating the query results once, using `Map.containsKey()` guard before `Map.get()`.
3. Iterate `Trigger.new`, look up each record's parent group from the Map, and accumulate changes.
4. Perform a single bulkified DML call outside all loops.

Reference the `templates/apex/TriggerHandler.cls` scaffold for the handler structure. The collection building belongs in the handler's `afterInsert()` / `afterUpdate()` methods, not in a trigger body directly — or in `CollectionUtils.groupByLookup()` from `references/code-examples.md` §1, which the handler then calls.

**Why not the alternative:** Querying inside a for loop over `Trigger.new` runs one SOQL per record, burning the 100-query synchronous limit (`apexdev` L19544) on any bulk load of 100+ records.

### Safe Set Intersection With retainAll()

**When to use:** A service method needs to find the overlap between two Sets — for example, the set of record Ids that are both in a new batch and in an existing do-not-process exclusion list.

**How it works:**
1. Construct the first Set from the incoming Ids: `Set<Id> incoming = new Set<Id>(triggerIds);`
2. Construct or load the exclusion Set from a SOQL or Custom Metadata query.
3. Create a working copy if the original Set must be preserved: `Set<Id> overlap = new Set<Id>(incoming);`
4. Call `overlap.retainAll(exclusionIds);` — the result is the intersection in one platform operation.
5. Subtract from the working set to get records that are NOT excluded: `incoming.removeAll(exclusionIds);`

**Why not the alternative:** Building a new Set by iterating and adding manually is O(n) extra code, allocates additional intermediate objects, and is more likely to introduce off-by-one bugs.

### A Composite Key Class Instead of a Nested Map

**When to use:** A roll-up is keyed on two or more dimensions — owner and stage, account and product family, region and month.

**How it works:** Write a small final-field class with `equals(Object)` and `hashCode()` and use it directly as the Map key. `Map<StageOwnerKey, Decimal>` replaces `Map<Id, Map<String, Decimal>>` and removes the inner containsKey guard entirely. See `references/code-examples.md` §3 for the class and the roll-up loop.

**Why not the alternative:** A nested map needs a guard at every level and a two-level iteration to read back. A concatenated string key (`ownerId + '|' + stage`) works but is case-sensitive, un-typed, and silently collides when a component value contains the separator.

### Grouping Without a Second Query — AggregateResult vs Map

**When to use:** You need counts or sums per parent.

**How it works:** `GROUP BY` returns `AggregateResult` objects; an aggregated field without an alias gets an implied alias of the form `expr0` (`apexdev` L9553–L9555). Read with `ar.get('expr0')` or alias the field. Note the caveat: "All aggregate functions other than COUNT() or COUNT(fieldname) include each row used by the aggregation as a query row" (`apexdev` L9558–L9560).

**Why not the alternative:** Grouping in Apex with `Map<Id, List<SObject>>` gives you the records as well as the count, which you need if the parent update depends on child field values. Use `AggregateResult` when only the aggregate matters; use the Map when you need the rows.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Group child records by parent in a trigger | `Map<Id, List<SObject>>` built outside loops | Single pass; avoids SOQL in loop |
| Check if a key exists before reading its value | `Map.containsKey(key)` guard, or `get(key)?.field` | `Map.get()` returns null — not an exception (`apexrefguide` L222557) |
| Find the overlap between two Id Sets | `Set.retainAll()` on a copy | One platform call; avoids manual loop |
| Convert a query result to a lookup map | `Map<Id, SObject> m = new Map<Id, SObject>(queryResult)` | The only list-populating Map constructor is `Map<ID,sObject>(recordList)` (`apexrefguide` L222322) |
| Build a map from records that may be unsaved | Explicit loop with an `Id != null` check | Null keys collapse; the last unsaved record wins (`apexdev` L1694–L1696) |
| Accumulate state across Batch execute() chunks | Write results to SObject records at end of each chunk; avoid growing instance-level Maps | Instance-level collections in Database.Stateful grow against a ceiling that does not reset |
| De-duplicate a List of Ids | `new Set<Id>(myList)` | Set construction removes duplicates in one step |
| De-duplicate Ids arriving as Strings | Convert to `Id` first, then `new Set<Id>(...)` | `Id` normalizes 15 to 18 characters (`apexdev` L1255); `String` does not |
| Sort a List of custom objects | Pass a `Comparator` to `List.sort()`, or implement `Comparable` | Platform-native sort; avoids hand-rolled comparison logic (`apexdev` L1537–L1539) |
| Remove entries while walking a Map | Collect keys in a temporary List, remove after the loop | `keySet()` is backed by the map (`apexrefguide` L222249) |
| Key a roll-up on two dimensions | Custom key class with `equals` + `hashCode` | One guard-free map instead of a nested one (`apexdev` L7044–L7045) |

---

## Recommended Workflow

1. Answer the seven rows in **Questions to Ask Before Configuring**; the container choice and the key type fall out of rows 1 and 2, and rows 6 and 7 set the bulk-test volume.
2. Read `references/code-examples.md` §0 and pick the container from the access-pattern table before writing any declaration. If a canonical scaffold already exists — `templates/apex/TriggerHandler.cls`, `templates/apex/BaseSelector.cls` — call it rather than restating it.
3. Copy `CollectionUtils`, and where the case needs them `OpportunitySortComparator` and `StageOwnerKey`, from `references/code-examples.md` §1–§3. Rename to the domain; do not inline the grouping logic into the handler.
4. Cross-check the design against `references/gotchas.md` — in particular the keySet view, the null-Id collapse, the `Set<String>` Id trap, and the mutable custom key — and against `references/llm-anti-patterns.md` if the code was AI-generated.
5. Run `python3 scripts/check_apex_collections_patterns.py --manifest-dir <apex source root> --strict`. Every ERROR is a defect; WARN and ADVISORY findings need a written reason to keep.
6. Adapt `CollectionUtilsTest` from `references/code-examples.md` §4: assert grouping counts, sort order across all keys including the null case, key-equality collapse, and heap headroom at 200 records inside `Test.startTest()`/`Test.stopTest()`.
7. Deploy and verify with §6–§7 — `sf project deploy start --manifest`, `sf apex run test --tests <YourTest>`, then the Tooling API query that confirms the classes are Active.

---

## Review Checklist

- [ ] All `Map.get()` calls are preceded by `Map.containsKey()`, null-checked, or reached through `?.`.
- [ ] No `Database.Stateful` batch class accumulates unbounded Map or List values across `execute()` chunks.
- [ ] `Set.retainAll()` and `Set.removeAll()` are called on copies, not the original collection, when the original is needed afterward.
- [ ] No SOQL query or DML statement appears inside a for loop.
- [ ] `Map<Id, SObject>` construction from `List<SObject>` uses the Map constructor (`new Map<Id, SObject>(list)`) rather than a manual loop where possible — and only when every record is persisted.
- [ ] Inner Lists in `Map<Id, List<SObject>>` are initialized with a `containsKey` guard (not overwriting an existing list).
- [ ] No collection is added to, removed from, or cleared inside a loop that is iterating it, and no `keySet()` is iterated while its map is edited.
- [ ] Every user-defined class used as a Map key or Set element defines both `equals(Object)` and `hashCode()`, and its key fields are `final`.
- [ ] Record Ids are held as `Id`, not `String`, wherever they are used as keys or set elements.
- [ ] Any `List.sort()` whose intended order is not the platform default is passed a `Comparator` that handles null inputs.

---

## Salesforce-Specific Gotchas

Full write-ups, each with **What happens / When it occurs / How to avoid**, are in `references/gotchas.md`. The short list:

1. `Map.get()` returns null for an absent key, so the `NullPointerException` surfaces at the field access, not the lookup.
2. `retainAll()` and `removeAll()` mutate the receiver, silently, with no exception.
3. A map key may be null and a repeated key overwrites the earlier entry, so unsaved records are never safe to key on — see gotcha 3 for what the guide does and does not document.
4. `Set<SObject>` and sObject map keys compare field values, not identity — and mutating the record breaks the mapping.
5. Instance collections in a `Database.Stateful` batch grow against a heap ceiling that does not reset between chunks.
6. `keySet()` is a live view of the map, not a snapshot.
7. `Set<String>` holding record Ids treats the 15- and 18-character forms as two distinct elements.
8. `List.sort()` on sObjects uses a documented default field sequence that is almost never the business order.
9. Modifying any collection while iterating it is documented as unsupported, including through a `keySet()` view.
10. `Decimal` keys that are numerically equal but differ in scale generally hash differently.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Collection pattern review | Findings on Map null-guard coverage, Set mutation safety, key-type correctness, heap accumulation risk, and DML/SOQL loop violations |
| `CollectionUtils` + `Comparator` + custom key class | Deployable classes from `references/code-examples.md` §1–§3, with `-meta.xml`, package.xml, and deploy order |
| Semantics test class | `CollectionUtilsTest` — asserts grouping, sort stability, key equality, Id-vs-String behaviour, and 200-record heap headroom |
| Checker report | Output of `scripts/check_apex_collections_patterns.py`, ERROR / WARN / ADVISORY |
| Batch heap remediation plan | Identifies unbounded instance-level collections in Database.Stateful classes and recommends the flush-per-chunk pattern |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/code-examples.md` | You are about to write the class — container choice table, `CollectionUtils`, the multi-key `Comparator`, the custom key class, the test class, package.xml, deploy and verify |
| `references/gotchas.md` | A collection is producing wrong data rather than an exception, or you are reviewing someone else's collection code |
| `references/examples.md` | You want the worked trigger and service scenarios end to end, including the Stateful batch anti-pattern |
| `references/llm-anti-patterns.md` | The code under review was AI-generated, or you are prompting an assistant to write collection logic |
| `references/well-architected.md` | You need the pillar framing, the architectural trade-offs, or the official sources behind a claim |

---

## Related Skills

- `apex/trigger-framework` — use when the handler structure around the collection patterns is the primary concern.
- `apex/batch-apex-patterns` — use when the broader batch design (scope, start/execute/finish, error handling) is the focus.
- `apex/apex-cpu-and-heap-optimization` — use when the algorithm shape is already right and the transaction still exceeds CPU or heap.
- `apex/apex-wrapper-class-patterns` — use when the thing being collected is a wrapper or DTO and its shape is the question.
- `apex/apex-design-patterns` — use when the question is which layer the grouping logic belongs in.
- `apex/governor-limits` — use when heap or CPU limits are being hit and broader limit strategy is needed.
- `apex/soql-fundamentals` — use when the underlying SOQL driving collection population needs optimization.
- `apex/exception-handling` — use when NullPointerException from unguarded Map.get() is part of a broader error handling review.
