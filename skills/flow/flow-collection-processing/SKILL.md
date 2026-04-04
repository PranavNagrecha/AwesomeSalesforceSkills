---
name: flow-collection-processing
description: "Use when building or reviewing Flow logic that processes lists of records using Loop, Assignment, Collection Filter, Collection Sort, or Transform elements. Triggers: 'iterate over collection in flow', 'flow loop add to collection', 'collection filter element', 'transform element flow', 'update records from collection variable', 'collection sort flow'. NOT for individual single-record retrieval (use Get Records alone), NOT for Apex-based collection manipulation, NOT for flow bulkification performance analysis (see flow-bulkification)."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Scalability
  - Reliability
triggers:
  - "how do I iterate over a collection in a flow and modify each record"
  - "flow loop is causing DML inside loop or too many DML statements error"
  - "how do I filter a collection without using a loop in flow"
  - "how to sort records in a collection variable before displaying in a screen flow"
  - "how do I use the transform element to create related records from a collection"
tags:
  - flow-collections
  - loop-element
  - collection-filter
  - collection-sort
  - transform-element
  - bulk-dml
inputs:
  - "Flow type (record-triggered, autolaunched, screen flow)"
  - "Source collection: SObject Collection or primitive collection variable"
  - "Operations needed: filter, sort, transform, accumulate, or DML"
  - "Target SObject type if Transform is involved"
outputs:
  - "Correct element selection and configuration for the collection operation"
  - "Pattern for loop-and-accumulate vs. Collection Filter vs. Transform"
  - "DML strategy: single Update Records on collection vs. loop+individual DML"
  - "Review findings on anti-patterns in existing Flow logic"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Flow Collection Processing

Use this skill when a Flow must do more than retrieve a flat list — when it needs to iterate, filter, sort, remap, or write back a group of records as a unit. This skill covers the full suite of Flow collection elements: Loop, Assignment inside a loop, Collection Filter, Collection Sort, and Transform.

---

## Before Starting

Gather this context before working on anything in this domain:

- What SObject or data type is in the collection? SObject Collections and primitive collections (Text, Number, etc.) behave differently and support different elements.
- Is the goal to read-and-branch, filter-and-keep, remap fields to a different SObject type, or accumulate records for a single DML write?
- Is the Flow running in a record-triggered context (bulk-safe, up to 200 records per transaction) or an autolaunched context called directly (potentially single-record)?

---

## Core Concepts

### SObject Collection vs. Primitive Collection

Flow supports two collection types. An SObject Collection stores a list of full records (e.g., `Account[]`). A primitive collection stores a list of scalar values such as Text or Number. Most collection operations — Loop, Collection Filter, Collection Sort, and Transform — apply only to SObject Collections. Primitive collections can be looped over and appended to via Assignment, but they are not compatible with the newer declarative filter/sort/transform elements.

### Loop Element

The Loop element iterates over a collection one record at a time, exposing a "current item" variable for that iteration. Inside the loop, Assignment elements can read from and write to the current item, accumulate records into a separate output collection, or set flags for downstream branching. A Loop always has two exit paths: "For Each" (for each iteration) and "After Last" (when the collection is exhausted). Building up a result collection inside a loop by appending the current item to a separate collection variable is the foundational collection-building pattern in Flow.

### Collection Filter Element

Available from Spring '23 onward, the Collection Filter element removes records from a collection based on one or more conditions — entirely without a Loop. It accepts an SObject Collection as input and produces a filtered SObject Collection as output. It supports AND/OR condition logic and field-level comparisons against literal values or other Flow variables. This element should be the first choice whenever the goal is simply reducing a collection to a subset; using a Loop with a conditional assignment to achieve the same result is more verbose and harder to maintain.

### Collection Sort Element

The Collection Sort element reorders an SObject Collection by one or more fields, ascending or descending. It operates in place on the input collection and does not require a Loop. Sorting before passing a collection to a Screen Flow table or to a downstream subflow is a common use case.

### Transform Element

The Transform element maps fields from one SObject Collection to a different SObject Collection or to a primitive collection. A common use case is producing a list of `Task` or `Case` records from a list of `Lead` records, mapping field values declaratively. Transform is the correct tool when the goal is type conversion or field remapping across SObject types; doing this inside a Loop with manual field assignments is more error-prone.

### DML on Collections

`Update Records`, `Create Records`, and `Delete Records` all accept either a single record or a collection variable. Using a collection variable with a single DML element processes all records in one operation and consumes one DML statement and one DML row per record — exactly the same limits as a list DML in Apex. Placing a DML element inside a Loop converts that cost into N DML statements, which fails at scale.

---

## Common Patterns

### Loop-and-Accumulate to Build a Modified Collection

**When to use:** You need to modify a field on every record in a collection (e.g., set `Status__c` to "Processed") and then write the whole list back.

**How it works:**
1. Declare a second SObject Collection variable (the output collection, initially empty).
2. Add a Loop over the source collection.
3. Inside the loop, use an Assignment element to set the field on `{!Loop.currentItem}`, then add `{!Loop.currentItem}` to the output collection using the `Add` operator.
4. After the loop exits via "After Last", connect to a single `Update Records` element pointed at the output collection.

**Why not the alternative:** Placing `Update Records` inside the loop issues one DML statement per record and fails when the transaction processes more than the DML statement limit allows.

### Collection Filter for Subset Selection

**When to use:** You need to pass a subset of a retrieved collection to a downstream element — for example, only the Opportunities with `StageName = 'Closed Won'` from a larger query result.

**How it works:**
1. Add a Collection Filter element after `Get Records`.
2. Set the source collection to the query result variable.
3. Define filter conditions (field, operator, value).
4. Store the result in a new SObject Collection variable.
5. Pass that filtered collection to the next element.

**Why not the alternative:** A Loop with an `if/then` branch and a conditional accumulation achieves the same result but takes four to six elements instead of one and is harder to read during review.

### Transform to Produce a Related-Record Collection

**When to use:** You have a collection of parent records and need to create child records — for example, creating follow-up `Task` records from a collection of `Case` records.

**How it works:**
1. Add a Transform element after the source collection is available.
2. Set the source collection (e.g., `{!CaseCollection}`) and the target SObject type (`Task`).
3. Map fields: `WhatId` from `Case.Id`, `Subject` from a template or literal, etc.
4. The output is a Task Collection variable.
5. Pass that collection to a single `Create Records` element.

**Why not the alternative:** Building the Task collection inside a Loop with manual Assignment and `Add` operations is verbose, difficult to maintain, and does not communicate intent as clearly as a dedicated Transform element.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Filter records from a collection to a subset | Collection Filter element | Single element, no loop required, conditions are explicit |
| Sort a collection before display or downstream use | Collection Sort element | Declarative, operates on the collection in place |
| Remap fields from one SObject type to another | Transform element | Designed for type conversion; avoids manual loop-based field assignment |
| Modify a field on all records and write back | Loop + Assignment + single Update Records | No declarative element covers in-place field mutation; accumulate then commit |
| Write N records created from a collection | Single Create Records on a collection variable | One DML statement regardless of N, versus N DML statements inside a loop |
| Filter AND sort AND then create related records | Collection Filter → Collection Sort → Transform → Create Records | Chain declarative elements; no loop needed |
| Conditional logic per record during iteration | Loop with branching inside | Only the Loop pattern supports per-record conditional branching |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

- [ ] No `Create Records`, `Update Records`, or `Delete Records` element sits inside a Loop without an explicit justified exception documented in the flow description.
- [ ] Collection Filter is used instead of a Loop-with-conditional-accumulation wherever the only goal is subset selection.
- [ ] Collection Sort is used instead of a sorting loop for ordering.
- [ ] Transform is used instead of a manual-assignment loop for SObject type conversion.
- [ ] SObject Collection variables have a defined SObject type — untyped collections cannot be used with Filter, Sort, or Transform.
- [ ] The "After Last" path of every Loop reaches the next meaningful element; unreachable paths cause silent flow termination.
- [ ] DML elements reference collection variables (not single-record variables) when operating on multiple records.
- [ ] The flow has been tested with an empty collection input to confirm it does not fault on the Loop's "After Last" path.

---

## Salesforce-Specific Gotchas

1. **Collection Filter and Collection Sort require typed SObject Collections** — if the collection variable does not have a specific SObject type set, the Filter and Sort elements cannot reference its fields and the configuration UI will be incomplete. This is easy to miss when variables are created ad hoc.
2. **Adding the current item to a new collection inside a loop mutates the shared object reference** — if you modify a field on `{!Loop.currentItem}` and then add it to the output collection, the modification is captured. But if you forget to modify before adding, you accumulate the original unmodified values silently.
3. **Transform does not support formula expressions in its field mappings** — you can map a source field to a target field, or a literal value, but you cannot write a formula inline. If logic is needed during the mapping (e.g., concatenating two fields), a Loop-based approach with an Assignment formula is required instead.
4. **An empty collection passed to a Loop does not fault — it exits immediately via "After Last"** — this is safe, but downstream elements must handle the resulting empty output collection correctly (e.g., a `Create Records` on an empty collection creates nothing and does not fault, while some subflows may expect a non-empty input).
5. **Collection Sort is stable but sorts the original collection variable in place** — there is no copy; the source variable is modified. If you need both the original and the sorted order, copy the collection into a second variable before sorting.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Element selection guidance | Recommendation for which collection element (Filter, Sort, Transform, or Loop) is correct for the scenario |
| Loop-and-accumulate pattern | Step-by-step design for in-loop field mutation and single-DML commit |
| Review findings | List of loops containing DML, missing typed collections, or manual patterns that should use declarative elements |
| Transform field mapping plan | Source-to-target field mapping table for producing a related-record collection |

---

## Related Skills

- `flow/flow-bulkification` — use when the primary concern is governor limit safety under high record volume, not collection element selection.
- `flow/record-triggered-flow-patterns` — use when the question is which trigger event, entry criteria, or save behavior to use, not how to process the resulting collection.
- `flow/subflows-and-reusability` — use when a collection-processing pattern should be extracted into a reusable subflow called from multiple parent flows.
