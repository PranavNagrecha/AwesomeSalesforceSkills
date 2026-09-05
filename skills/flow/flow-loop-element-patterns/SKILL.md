---
name: flow-loop-element-patterns
description: "Use when reviewing or authoring Flow logic that contains a Loop element — DML-in-loop / SOQL-in-loop refactors, the collect-then-DML idiom, nested loops, and loop-free alternatives (Collection Filter, Transform, Get-with-criteria). Triggers: 'DML inside flow loop', 'Get Records inside loop element', 'Update Records in loop blowing governor limits', 'nested loop in flow', 'Subflow in loop'. NOT for collection elements on their own — use flow/flow-collection-processing. NOT for whole-flow bulk redesign — use flow/flow-bulkification. Also covers: Loop metadata (FlowLoop collectionReference / iterationOrder / nextValueConnector / noMoreValuesConnector), Collection Filter, Sort and Map processors (FlowCollectionProcessor), collection Assignment operators (Add, AssignCount, RemoveAll, RemoveUncommon), and FLOW_LOOP_DETAIL debug-log analysis."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
triggers:
  - "DML inside a flow loop is throwing Too Many DML Statements: 151"
  - "Get Records inside a loop element exhausts SOQL queries"
  - "nested loop in screen flow exploding 2000-element execution limit"
  - "Update Records sits inside the loop iteration body"
  - "subflow called inside a loop and it does its own DML"
  - "loop iteration variable changes don't persist to the source records"
  - "should I use Collection Filter or a Loop with a Decision"
  - "DML inside flow loop element collect then update bulkification governor limit"
  - "refactor a nested flow loop into a Collection Filter element"
  - "stage records inside the loop then update once after the loop ends"
  - "write the Flow XML for a Loop element with iterationOrder and noMoreValuesConnector"
  - "count the items in a flow collection without building a counter loop"
  - "build a Map collection processor that outputs a new record collection"
  - "sort and limit a collection before the flow loop runs"
  - "read FLOW_LOOP_DETAIL in a debug log to count loop iterations"
  - "flow loop element deploys but the field edits never save"
tags:
  - flow-loop-element-patterns
  - bulkification
  - collection-processor
  - iteration-order
  - loop-element
  - dml-in-loop
  - soql-in-loop
inputs:
  - "Flow XML or design with one or more Loop elements"
  - "Source collection variable type (SObject Collection, primitive collection, Apex-defined collection)"
  - "What the loop body does (Assignment, DML, Get Records, Subflow, Decision)"
  - "Expected input volume per interview (1, 200, scheduled batch sizes)"
outputs:
  - "Identified loop anti-patterns (DML-in-loop, SOQL-in-loop, subflow-in-loop, nested loop) with concrete refactor"
  - "Collect-then-DML refactor instructions per loop"
  - "Recommendation to keep, replace with Collection Filter / Transform / Get-with-criteria, or escalate to invocable Apex"
  - "Worst-case element-execution and CPU-time estimate for the loop"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Flow Loop Element Patterns

Use this skill when a Flow contains a Loop element and you need to confirm the loop is safe, correct, and necessary. The Loop element is the most common source of governor-limit failures in Flow because anything placed inside its body executes once per iteration — and Salesforce's per-transaction limits (150 DML statements, 100 synchronous SOQL queries, 10,000 ms synchronous CPU time — `apexdev.txt` L19544–L19579) are shared across every iteration AND every other automation in the same transaction. There is no documented per-interview element ceiling: see `references/gotchas.md` Gotcha 3 for the search that establishes the negative.

This skill is the canonical reference for: (1) what Loop semantics actually are, (2) the four anti-patterns that the `flow-builder` and `flow-analyzer` agents must flag (DML-in-loop, SOQL-in-loop, subflow-with-DML-in-loop, nested loops), (3) the collect-then-DML refactor that fixes most of them, and (4) when a Loop should be deleted entirely in favour of a Filter, Sort or Map collection processor, a Transform, or a tighter Get Records. Deployable XML for all of it is in `references/metadata-examples.md`.

---

## Before Starting

Gather this context before reviewing or editing any Flow with a Loop element:

- **The flow type and trigger** — record-triggered (which save phase), autolaunched, screen, scheduled. Record-triggered flows multiply the per-iteration cost by the trigger batch size (up to 200 in a single Bulk API chunk), and ALL iterations share one transaction.
- **The loop's input collection** — its source (Get Records output, manually built collection, prior loop's accumulator), its sObject type, and its expected size. A loop that worked at 5 records may fail at 200.
- **Every element inside the loop body** — flag any of: Create Records, Update Records, Delete Records, Get Records, Action (especially Apex invocable), Subflow. Loops containing only Assignment / Decision / formula evaluation are usually safe.
- **Whether the loop variable is modified** — a common practitioner assumption is that `Assignment: loopItem.Field__c = X` updates the source records. It does not persist to the database; you must Add the modified item to a separate collection and DML that collection after the loop.
- **Existing fault paths** — an unhandled DML failure inside a loop rolls back the entire transaction (see `flow/fault-handling`), making the symptom appear at iteration 1 even when the bad data is at iteration 73.

---

## Questions to Ask Before Configuring

Ask these before opening the Loop element; the answers decide whether the loop should exist at all, and an LLM that skips them ships a flow that deploys, passes a five-record debug run, and drops every edit in production.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "How big is the input collection on the worst day, not the demo day?" | Iteration count is the only input to every other decision here; a loop that is fine at 5 is a CPU-time incident at 4,000 | The iteration budget, and whether a Sort + `limit` before the loop removes the problem outright (Gotcha 13) |
| "What does the loop body actually do — edit fields, write records, query, call a subflow, or just count?" | Each answer has a different loop-free replacement, and one of them (count) has no loop at all | The refactor target: staged collection, pre-loaded lookup, `AssignCount`, or Collection Filter (Gotchas 11, 15) |
| "Where do the edited records get written?" | Editing the loop variable persists nothing; the `Add` into a second collection is what carries the edit out | The staged collection variable and the single post-loop DML element (Gotcha 1) |
| "Is a second collection being iterated inside the first?" | Nested loops are `n × m` element executions with no DML to blame, so none of the bulkification advice catches them | A Filter processor whose formula references the outer loop variable, replacing `m` elements with one (Gotcha 8, `references/metadata-examples.md` §3) |
| "Does the order of iteration change the result?" | `iterationOrder` reverses the collection; it does not sort it, and an unsorted Get Records has no defined order | An explicit `sortField`/`sortOrder` on the Get Records, or a documented statement that order is irrelevant (Gotcha 8) |
| "What happens when the collection is empty?" | An empty collection reaches `noMoreValuesConnector` on the first evaluation, so everything in the loop body is skipped | Initialisation moved before the loop, and a wired After Last Item path (Gotcha 9) |
| "What is the flow's own `<apiVersion>`, and which subflows and actions does the loop body call?" | Version gates half the elements you would reach for, and a subflow hides its DML from the parent's XML | A version floor for Filter/Sort/Map and `limit`, plus the transitive review list (Gotchas 3, 5, 12) |

What a proper loop design adds over just dragging in a Loop element: the records the loop edits are actually saved, the iteration count is bounded before the loop rather than survived inside it, the empty and single-record paths behave, and the failure surface is one DML with a fault path instead of `n` silent ones.

---

## Core Concepts

### 1. Loop element semantics and iteration variable scope

`FlowLoop` has exactly five fields, and they are the whole element (`api_meta.txt` L70698–70716, API 30.0+):

| Field | What it does |
|---|---|
| `collectionReference` | "The collection being looped through" |
| `assignNextValueToReference` | "The variable that's assigned to the current value in the collection before navigating to the target of `nextValueConnector`" |
| `iterationOrder` | `Asc` — the order the values are listed, first to last; `Desc` — the reverse of that order, last to first. Not a sort |
| `nextValueConnector` | the loop body — "a reference to the next element in the collection" |
| `noMoreValuesConnector` | "the element to navigate to when all entries in the collection have been iterated through" |

Three things follow directly. There is no `faultConnector` — a Loop cannot fault, so fault handling belongs to the Get Records feeding it and the DML following it. There is no persistence field — the collection's value is assigned *into* a variable, and nothing described here writes back. And an empty collection has all zero entries iterated on the first evaluation, so it lands on `noMoreValuesConnector` immediately and every element in the body is skipped.

The variable named by `assignNextValueToReference` is a flow resource, not a block-scoped one: after the loop finishes it still holds the last item assigned (or nothing at all, if the collection was empty). That is a hazard downstream and a deliberate tool inside an in-loop Collection Filter formula, which is how the nested-loop refactor works.

To save an edit made inside a loop, the Assignment that sets the field must also `Add` the variable to a separate collection, and one Update Records after the loop must take that collection. See `references/gotchas.md` Gotcha 1 for the grounding and the one claim that is explicitly marked unverified.

### 2. Why DML / SOQL / Subflow-with-DML inside a loop is a P0

Salesforce enforces per-transaction governor limits that are **shared across every flow, trigger, and Apex class in the same transaction**: 150 DML statements, 100 synchronous SOQL queries (200 async), 50,000 records retrieved by SOQL, 6 MB heap (12 MB async), and 10,000 ms synchronous CPU time (60,000 ms async) — `apexdev.txt` L19544–L19579. A Loop iterating 200 records with one Update Records inside the body issues 200 DML statements in that transaction, busting the 150 limit on iteration 76 and rolling back the whole thing. Same math for Get Records inside a loop versus the 100-SOQL ceiling. The flow does not "release" budget between iterations — there is one transaction, one budget.

Subflow-in-loop is the same anti-pattern in disguise. If `LoopOverCases → Subflow_NotifyOwner` calls a subflow whose body contains an Update Records, every iteration executes that subflow's DML — the parent loop bulkifies-fails just as if the DML were inline. Reviewers must inspect every subflow called inside a loop body. Action elements that wrap Apex invocables are equally suspect; the Apex method runs once per iteration unless its `invocableMethod` declaration accepts a `List<>` and the flow passes a collection (the action's bulkified-input contract is what matters, not whether it "looks bulky").

### 3. Collection-based alternatives — collect-then-DML, Collection Filter, Transform, Get-with-criteria

The fix for DML-in-loop is the **collect-then-DML idiom**: inside the loop body use Assignment with the `Add` operator to append the current item (modified as needed) into a separate SObject Collection variable, then place a single Update / Create / Delete Records element AFTER the loop, operating on the accumulated collection. One DML statement, regardless of input size.

For pure filtering, sorting and per-item field mapping, the three `FlowCollectionProcessor` elements replace whole loop bodies with a single element each. `collectionProcessorType` accepts exactly three values (`api_meta.txt` L69934–69941):

| Builder element | `collectionProcessorType` | Version floor | Replaces |
|---|---|---|---|
| Sort | `SortCollectionProcessor` | API 50.0 | a loop that orders or takes top N (with `limit`, API 51.0) |
| Filter | `FilterCollectionProcessor` | API 53.0 | Loop → Decision → Assignment(Add) |
| Map | `RecommendationMapCollectionProcessor` | API 53.0 | Loop → Assignment(build record) → Assignment(Add) |

The Map element's enum keeps a `Recommendation` prefix from its Einstein origin; there is no `MapCollectionProcessor` value, and guessing it is the most common reason hand-authored Flow XML fails to deploy. Separately, the **Transform** element (`FlowTransform`, API 59.0 and later — `api_meta.txt` L72685–72688) handles typed source-to-target transformation. For "narrow this list to just the rows I care about," the cheapest fix is neither: push the filter into the upstream **Get Records** `filters`, `sortField`/`sortOrder`, or `limit` and have no loop at all.

---

## Common Patterns

### Pattern: Collect-Then-DML (the primary refactor)

**When to use:** Any time you have a Loop whose body needs to issue DML (Update / Create / Delete) on the iterated records or related records.

**How it works:**
1. Before the loop, initialize an empty SObject Collection variable, e.g. `accountsToUpdate`.
2. Inside the loop, use Assignment to set fields on the current item (or build a new SObject via constants/formulas).
3. In the same Assignment, add a row: `accountsToUpdate` `Add` `{!CurrentAccount}`.
4. After the loop ends, place ONE Update Records element with `accountsToUpdate` as the input.

**Why not the alternative:** Putting the DML directly inside the loop issues N DML statements (one per iteration) and bursts the 150-DML cap on any record-triggered flow processing a 200-record bulk insert.

### Pattern: Map-Lookup via Pre-Loaded Collection

**When to use:** You need to enrich each row of collection A with a value derived from collection B, and B is not bounded to A by a parent-child relationship (so you cannot use a single Get Records with a related-list traversal).

**How it works:**
1. Use ONE Get Records to load all of B's relevant rows into a collection variable (e.g. all active Owners for a list of OwnerIds you're about to encounter).
2. Loop over A. Inside the loop, use a Decision element that filters the B collection by the lookup key (Flow does not have a native `Map<Id, SObject>` — you compare against the in-memory collection by iterating it OR by using a second short loop that breaks after the first match).
3. Use Assignment to set the enriched field on the current A item, then Add to an output collection.
4. Single DML on the output collection after the loop.

**Why not the alternative:** Get Records inside the outer loop issues one SOQL per A row — 200 A rows means 200 SOQL queries against the 100 sync SOQL limit. The pre-load pattern is one SOQL query regardless of size.

### Pattern: Pre-Filter with Collection Filter Instead of Loop+Decision

**When to use:** You want to keep only rows of a collection that match a condition (no DML, no enrichment — pure filter).

**How it works:** Replace `Loop → Decision → Assignment(Add) → end loop` with a single **Collection Filter** element. The output is a new collection containing only the matching rows.

**Why not the alternative:** Loop+Decision+Assignment executes 3+ elements per iteration, so it burns roughly triple the CPU time of a single Collection Filter, is harder to read, and is one of the most common LLM-generated anti-patterns.

### Pattern: Map / Transform Instead of Loop+Build

**When to use:** Your loop body is constructing one output SObject per input SObject (typed conversion, e.g. Quote Line → Order Line). Use a Map processor (`RecommendationMapCollectionProcessor`, API 53.0+) when the target is a record collection you will then create; use `FlowTransform` (API 59.0+) when you need the Builder's Transform mapping surface.

**How it works:** Replace the loop with a single Transform element that maps source fields to target fields declaratively. Output is a target-type collection ready for Create Records.

**Why not the alternative:** Loop+Assignment(build new sObject)+Assignment(Add) consumes more elements, hides the field-mapping intent in two Assignment elements, and is harder to maintain when the target schema changes.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Update N records based on per-row logic | Loop → Assignment(set + Add to collection) → Update Records (after loop) | One DML statement; survives 200-record bulk loads |
| Filter a collection by a fixed criterion | Collection Filter element | Single declarative element vs Loop+Decision+Assignment; fewer elements counted |
| Convert a collection to a different sObject type | Map processor (`RecommendationMapCollectionProcessor`, API 53.0+) or `FlowTransform` (API 59.0+) | Replaces Loop+Assignment(build)+Assignment(Add); `outputSObjectType` + `mapItems` state the mapping declaratively |
| Need a sorted or top-N subset | Get Records `sortField`/`sortOrder` + `limit` (2–20,000, API 63.0+); or a Sort processor with `sortOptions` + `limit` (API 51.0+) | Push work to the database first, the processor second, the loop never — `limit` applies after the sort |
| Need to look up B-rows by key while iterating A | One Get Records of all B + Loop A + Decision against in-memory B | Avoids SOQL-in-loop; single query regardless of A size |
| Intersect or subtract two collections | Assignment with `RemoveUncommon` (keeps items in both) or `RemoveAll` (removes each item of the value collection) | API 43.0+; both are single elements where the instinct is a nested loop |
| Count how many items a collection holds | Assignment with `AssignCount` | One element, API 43.0+; a Loop that only increments a counter is a Loop that should not exist |
| Genuinely complex per-row logic with branching DML | Invocable Apex receiving `List<SObject>` | Apex map/set primitives, full bulkification, real unit tests |
| Two input collections joined many-to-many | Filter processor inside the outer Loop, its `formula` referencing the outer loop variable | One element per outer iteration instead of `m`; nested Loops are O(n*m) and the 10,000 ms sync CPU limit (`apexdev.txt` L19579) is what stops them |

---

## Recommended Workflow

1. **Answer the seven questions above**, then inventory every `<loops>` node in the flow XML and every subflow it calls. For each, record `collectionReference`, `assignNextValueToReference`, `iterationOrder`, and whether `noMoreValuesConnector` is wired. Run `python3 scripts/check_flow_loop_element_patterns.py --manifest-dir <source-dir>` to get that inventory mechanically, including the checks a reader skips.
2. **Classify each loop body** as Pure (Assignment / Decision only), DML-in-loop, SOQL-in-loop, Action-in-loop, or Subflow-in-loop — recursing into every subflow, because the parent's XML does not show what the child does (`references/gotchas.md` Gotcha 5).
3. **Try to delete the loop before fixing it.** Work down the cost ladder in `references/metadata-examples.md`: Get Records `filters` + `sortField`/`sortOrder` + `limit` → a Sort / Filter / Map `collectionProcessors` element → `AssignCount`, `RemoveUncommon` or `RemoveAll` for counting and set arithmetic → only then a Loop. A nested loop over a second collection becomes a Filter processor whose `formula` references the outer loop variable (§3).
4. **For the loops that survive, apply the staged-collection shape** in `references/metadata-examples.md` §2: one Assignment that sets fields on the loop variable *and* `Add`s it to a separate collection, one `recordUpdates` after the loop, `faultConnector` on the Get Records and on the DML. §1 is the deployable negative case to diff against.
5. **Pin the behaviour with a `FlowTest`** (§4). Test points attach only to `Start` and `Finish`, so assert on the flow-scoped variables the loop left behind — the staged collection is non-empty, the `AssignCount` total is above zero, the post-loop DML has no error.
6. **Verify against a real run**, not a design review: the SOQL count-by-stage query in `references/metadata-examples.md` § Verification, then the debug log at Workflow `FINER` for `FLOW_LOOP_DETAIL` (actual iteration count), `FLOW_BULK_ELEMENT_DETAIL` (records per DML) and `FLOW_INTERVIEW_FINISHED_LIMIT_USAGE` (CPU time against the 10,000 ms ceiling).
7. **Hand off what this skill does not own** — bulk-transaction redesign to `flow/flow-bulkification`, the fault-path interior to `flow/fault-handling`, collection-element selection generally to `flow/flow-collection-processing`, and anything that no longer fits one transaction to `flow/flow-large-data-volume-patterns`.

---

## Review Checklist

- [ ] No Create / Update / Delete Records element appears inside any Loop body (direct or via subflow / action).
- [ ] No Get Records element appears inside any Loop body.
- [ ] Every loop with mutation has a corresponding Assignment-with-Add into a target collection AND a single post-loop DML.
- [ ] No nested loops unless the inner-collection size is hard-bounded to a small constant AND a Map-Lookup pattern was rejected with reason documented.
- [ ] Loop-variable assignments are NOT relied on to persist (each is paired with an `Add` into a separate collection and a single post-loop DML).
- [ ] Every `<loops>` node has a wired `noMoreValuesConnector`, and nothing the post-loop path needs is initialised inside the loop body.
- [ ] `iterationOrder` is not being used as a sort; ordering lives on the upstream Get Records or a Sort processor.
- [ ] The `body_elements * iterations` estimate has been read against the 10,000 ms synchronous CPU budget — not against a 2,000-element ceiling, which no developer guide documents.
- [ ] `faultConnector` is present on the Get Records feeding the loop and on the DML following it (a `FlowLoop` has no fault path of its own).
- [ ] Pure-filter loops have been replaced with a `FilterCollectionProcessor`; build-a-record loops with a Map processor; counter loops with `AssignCount`; two-collection comparisons with `RemoveUncommon` / `RemoveAll`.
- [ ] Any `collectionProcessors` element carries exactly one of `formula` or `conditions`, consistent with its `conditionLogic`, and a Map processor names an `assignNextValueToReference`.
- [ ] `python3 scripts/check_flow_loop_element_patterns.py --manifest-dir <dir>` reports no findings.
- [ ] Subflows called inside a loop have been inspected for hidden DML / SOQL.

---

## Salesforce-Specific Gotchas

Summary only — `references/gotchas.md` carries the grounding, the line citations, and the three claims explicitly marked unverified.

| # | Gotcha | One-line shape |
|---|---|---|
| 1 | Editing the loop variable saves nothing | The `Add` into a second collection is what carries the edit out of the loop |
| 2 | Loop variables are flow-scoped | They still hold the last item after the loop, and null when the collection was empty |
| 3 | No 2,000-element ceiling is documented | Absent from `api_meta.txt`, `apexdev.txt` and the App Limits Cheat Sheet; CPU time is the real ceiling |
| 4 | DML / SOQL budgets are transaction-wide | A "safe" 100-DML loop fails because four other automations already spent 60 |
| 5 | Subflow-in-loop hides its own DML | The parent's XML looks clean; review is transitive or it is nothing |
| 6 | Post-loop DML on an empty collection is harmless | The defensive emptiness Decision is dead code |
| 7 | `Add` never deduplicates | Two branches that both append put the same record in the collection twice |
| 8 | `iterationOrder` reverses, it does not sort | And an unsorted Get Records has no order to reverse |
| 9 | Empty collection goes straight to `noMoreValuesConnector` | So the body is skipped, and a missing connector strands the interview |
| 10 | `Add` means arithmetic, append, or concatenation by target type | And is illegal on `boolean`, `dateTime` and `sObject` |
| 11 | `conditionLogic` picks `formula` or `conditions` | An element carrying both reads one way and runs the other |
| 12 | The Map element's enum is `RecommendationMapCollectionProcessor` | `MapCollectionProcessor` does not exist and does not deploy |
| 13 | `limit` applies after the sort, and has no default | Two different `limit` shapes: bare `int` on a processor, `numberValue` on Get Records |
| 14 | `RemoveUncommon` keeps the intersection | The name reads like it removes it; `RemoveAll` is the difference |
| 15 | A counter loop is one `AssignCount` | The collection goes in `value`, the Number variable in `assignToReference` |
| 16 | `storeOutputAutomatically` decides what the loop can reference | And a single-record Get Records under a Loop iterates one item without complaint |
| 17 | A Loop has no `faultConnector` | The fault path belongs to the Get Records before it and the DML after it |

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Loop inventory table | One row per Loop element with input collection, body classification (pure / DML / SOQL / subflow / action), expected iteration count, and pass/fail verdict |
| Refactor diff per anti-pattern loop | Before/after element list showing the collect-then-DML conversion, plus the new collection variable to declare |
| Element-count estimate | Worst-case element-executions per interview, read as a CPU-time proxy against 10,000 ms sync / 60,000 ms async (`apexdev.txt` L19579). Report the flow's own `<apiVersion>` alongside it, since version gates Filter/Sort/Map and `limit` — not because a 2,000-element ceiling is documented anywhere |
| Loop-free alternative recommendation | Per loop, a yes/no on whether a Get Records filter/sort/limit, a Filter / Sort / Map processor, `AssignCount`, or `RemoveUncommon` / `RemoveAll` could eliminate it, with reason |
| Deployable refactor XML | The corrected `*.flow-meta.xml` plus its `FlowTest`, shaped from `references/metadata-examples.md` §2–§4, with `package.xml` and deploy order |
| Checker output | `scripts/check_flow_loop_element_patterns.py --manifest-dir <dir>` findings, cleared or explained per finding |
| Subflow inspection report | For every subflow called inside a loop body, a verdict on whether it contains hidden DML / SOQL |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | You are writing or reviewing actual `*.flow-meta.xml` — the deployable anti-pattern, the staged-collection correction, the Filter-replaces-nested-loop and Map flows, a `FlowTest`, `package.xml`, deploy order, and the SOQL + debug-log verification |
| `references/gotchas.md` | A loop behaves in a way the design does not explain — 17 platform behaviours with `grep -n` citations, including the three claims marked UNVERIFIED |
| `references/llm-anti-patterns.md` | You are reviewing AI-generated Flow design or XML — the specific ways models get loops wrong, each with a mechanical detection hint |
| `references/well-architected.md` | You need the pillar framing, the loop-vs-loop-free tradeoff table, or the source list with the claim each source supports |
| `templates/flow-loop-element-patterns-template.md` | You are starting a loop review and want the worksheet the checklist and the checker fill in |
| `scripts/check_flow_loop_element_patterns.py` | Before any deploy — six stdlib checks over `*.flow-meta.xml` in a `--manifest-dir` |

---

## Related Skills

- `flow/flow-bulkification` — the broader framing for designing flows that survive 200-record bulk save contexts. This skill is the loop-specific subset of that work; it owns DML-in-loop and collection staging as a *transaction* problem.
- `flow/flow-collection-processing` — collection element selection generally: which of Loop, Filter, Sort, Map, Transform, or an Assignment operator fits the job.
- `flow/flow-cross-object-updates` — when the loop body reaches into related records, the cross-object update patterns describe how to batch parent / child writes.
- `flow/flow-get-records-optimization` — most SOQL-in-loop refactors collapse into a single optimized Get Records; this skill shows how to write that query.
- `flow/flow-governor-limits-deep-dive` — exhaustive treatment of the CPU-time / 150-DML / 100-SOQL ceilings the loop must respect.
- `flow/flow-large-data-volume-patterns` — when the input collection itself is too big for a single transaction (move to scheduled paths or invocable Apex).
- `flow/fault-handling` — the interior of the fault path this skill only insists must exist.
- `flow/subflows-and-reusability` — when refactoring subflow-in-loop, the contract for bulk-safe subflow inputs.
- `flow/flow-testing` — the wider `FlowTest` and debug-run practice around the single test in §4.

---

## Official Sources Used

- Metadata API Developer Guide, `FlowLoop` (`api_meta.txt` L70698–70716) — the five-field element, `iterationOrder` `Asc`/`Desc` semantics, `nextValueConnector` / `noMoreValuesConnector`, and the absence of any `faultConnector` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide, `FlowAssignmentOperator` (`api_meta.txt` L69767–69880) — `Add` by target type, `AssignCount`, `RemoveAll`, `RemoveUncommon`, `RemoveFirst`, `RemovePosition`, and the API 43.0 floor — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide, `FlowCollectionProcessor` / `FlowCollectionSortOption` / `FlowCollectionMapItem` (`api_meta.txt` L69927–69996, L70161–70172) — the three `collectionProcessorType` values and their version floors, `conditionLogic` `Formula`, `limit` after sort, `mapItems` and `outputSObjectType` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide, `FlowRecordLookup` and `FlowRecordUpdate` (`api_meta.txt` L71091–71292) — "records aren't returned in any particular order" without a sort, `storeOutputAutomatically` vs `outputReference`, the 2–20,000 `limit` (API 63.0+), and both `faultConnector` fields — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide, `FlowTest` and subtypes (`api_meta.txt` L73960–74340) — `.flowtest` suffix, API 55.0 floor, test points limited to `Start` and `Finish`, `testType` `WithAssertion`, `HasError` and `IsEmpty` operators, and the sample XML this skill's test is shaped from — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Apex Developer Guide, "Execution Governors and Limits" (`apexdev.txt` L19535–19585) — 100 sync / 200 async SOQL, 150 DML, 50,000 rows, 6 MB / 12 MB heap, 10,000 ms / 60,000 ms CPU, all per transaction — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Apex Developer Guide, "Debug Log Levels" Workflow events (`apexdev.txt` L38715–38900) — `FLOW_LOOP_DETAIL`, `FLOW_BULK_ELEMENT_DETAIL`, `FLOW_INTERVIEW_FINISHED_LIMIT_USAGE`, and the absence of any executed-element event — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Salesforce KB "Flow Error 'Number of Iterations Exceeded'" — the only source in either direction for the retired 2,000-element limit and its removal in API 57.0; not a developer guide, and not corroborated by any of the above — https://help.salesforce.com/s/articleView?id=000382258&language=en_US&type=1
- Flow Loop element reference — https://help.salesforce.com/s/articleView?id=platform.flow_ref_elements_loop.htm&type=5
- Flow Best Practices (avoid DML/SOQL inside loops) — https://help.salesforce.com/s/articleView?id=sf.flow_prep_bestpractices.htm&type=5
