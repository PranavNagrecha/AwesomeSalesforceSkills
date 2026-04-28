---
name: flow-loop-element-patterns
description: "Use when reviewing or authoring Flow logic that contains a Loop element — covers DML-in-loop / SOQL-in-loop refactors, the collect-then-DML idiom, nested loops, and loop-free alternatives (Collection Filter, Transform, Get-with-criteria). Triggers: 'DML inside flow loop', 'Get Records inside loop element', 'Update Records in loop blowing governor limits', 'nested loop in flow', 'Subflow in loop'. NOT for general collection processing semantics (see flow-collection-processing) and NOT for end-to-end bulkification redesign across an entire flow (see flow-bulkification)."
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
tags:
  - flow-loop-element-patterns
  - bulkification
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
  - "Element-count estimate against the 2,000-element interview limit"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-27
---

# Flow Loop Element Patterns

Use this skill when a Flow contains a Loop element and you need to confirm the loop is safe, correct, and necessary. The Loop element is the most common source of governor-limit failures in Flow because anything placed inside its body executes once per iteration — and Salesforce's per-transaction limits (150 DML statements, 100 SOQL queries, 2,000 Flow elements) are shared across every iteration AND every other automation in the same transaction.

This skill is the canonical reference for: (1) what Loop semantics actually are, (2) the four anti-patterns that the `flow-builder` and `flow-analyzer` agents must flag (DML-in-loop, SOQL-in-loop, subflow-with-DML-in-loop, nested loops), (3) the collect-then-DML refactor that fixes most of them, and (4) when a Loop should be deleted entirely in favour of Collection Filter, Transform, or a tighter Get Records.

---

## Before Starting

Gather this context before reviewing or editing any Flow with a Loop element:

- **The flow type and trigger** — record-triggered (which save phase), autolaunched, screen, scheduled. Record-triggered flows multiply the per-iteration cost by the trigger batch size (up to 200 in a single Bulk API chunk), and ALL iterations share one transaction.
- **The loop's input collection** — its source (Get Records output, manually built collection, prior loop's accumulator), its sObject type, and its expected size. A loop that worked at 5 records may fail at 200.
- **Every element inside the loop body** — flag any of: Create Records, Update Records, Delete Records, Get Records, Action (especially Apex invocable), Subflow. Loops containing only Assignment / Decision / formula evaluation are usually safe.
- **Whether the iteration variable is modified** — Flow's Loop iterator is a reference into the source SObject collection; a common practitioner assumption is that `Assignment: loopItem.Field__c = X` updates the source. It does not persist to the database; you must Add the modified item to a separate Update collection.
- **Existing fault paths** — an unhandled DML failure inside a loop rolls back the entire transaction (see `flow/fault-handling`), making the symptom appear at iteration 1 even when the bad data is at iteration 73.

---

## Core Concepts

### 1. Loop element semantics and iteration variable scope

A Loop element takes an **input collection** (SObject Collection or primitive collection) and exposes a **current item** variable on each pass. Iteration order matches the order of the source collection — Flow does not sort or dedupe. The current-item variable is scoped at the flow level, not the loop level: after the loop's End connector executes, the variable retains the LAST item processed (or remains null only if the input collection was empty). Practitioners frequently rely on this for "last record processed" logic, but it is also a foot-gun if a downstream element accidentally references it.

For SObject collections, the current item is a reference to the same SObject instance held in the source collection — not a copy. Mutating fields on the iteration variable visibly changes the in-memory source collection, but does NOT issue a DML to the database. To persist changes you must call Update Records on a collection (typically the source collection itself, or a separate collection you accumulated). This is the single biggest semantic surprise in Flow.

### 2. Why DML / SOQL / Subflow-with-DML inside a loop is a P0

Salesforce enforces per-transaction governor limits that are **shared across every flow, trigger, and Apex class in the same transaction**: 150 DML statements, 100 SOQL queries (synchronous), 50,000 records retrieved, 6 MB of Apex heap. A Loop iterating 200 records with one Update Records inside the body issues 200 DML statements in that transaction, busting the 150 limit on iteration 76 and rolling back the whole thing. Same math for Get Records inside a loop versus the 100-SOQL ceiling. The flow does not "release" budget between iterations — there is one transaction, one budget.

Subflow-in-loop is the same anti-pattern in disguise. If `LoopOverCases → Subflow_NotifyOwner` calls a subflow whose body contains an Update Records, every iteration executes that subflow's DML — the parent loop bulkifies-fails just as if the DML were inline. Reviewers must inspect every subflow called inside a loop body. Action elements that wrap Apex invocables are equally suspect; the Apex method runs once per iteration unless its `invocableMethod` declaration accepts a `List<>` and the flow passes a collection (the action's bulkified-input contract is what matters, not whether it "looks bulky").

### 3. Collection-based alternatives — collect-then-DML, Collection Filter, Transform, Get-with-criteria

The fix for DML-in-loop is the **collect-then-DML idiom**: inside the loop body use Assignment with the `Add` operator to append the current item (modified as needed) into a separate SObject Collection variable, then place a single Update / Create / Delete Records element AFTER the loop, operating on the accumulated collection. One DML statement, regardless of input size.

For pure filtering, the **Collection Filter** element (GA since Winter '23) replaces a Loop+Decision+Add pattern with a single declarative element — fewer elements, fewer bugs, faster to read. For shape transformation between sObject types (e.g., Lead → Contact + Account + Opportunity), the **Transform** element (GA in Spring '24 for record-triggered/autolaunched flows) replaces a Loop that builds output records from input records. For "narrow this list to just the rows I care about," the cheapest fix is to push the filter into the upstream **Get Records** filter conditions or sort/limit clause — no loop at all.

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

**Why not the alternative:** Loop+Decision+Assignment uses 3+ elements per iteration (counted against the 2,000-element interview limit), is harder to read, and is one of the most common LLM-generated anti-patterns.

### Pattern: Transform Element Instead of Loop+Build

**When to use:** Your loop body is constructing one output SObject per input SObject (typed conversion, e.g. Quote Line → Order Line). Spring '24+ on record-triggered and autolaunched flows.

**How it works:** Replace the loop with a single Transform element that maps source fields to target fields declaratively. Output is a target-type collection ready for Create Records.

**Why not the alternative:** Loop+Assignment(build new sObject)+Assignment(Add) consumes more elements, hides the field-mapping intent in two Assignment elements, and is harder to maintain when the target schema changes.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Update N records based on per-row logic | Loop → Assignment(set + Add to collection) → Update Records (after loop) | One DML statement; survives 200-record bulk loads |
| Filter a collection by a fixed criterion | Collection Filter element | Single declarative element vs Loop+Decision+Assignment; fewer elements counted |
| Convert a collection to a different sObject type | Transform element (Spring '24+) on record-triggered/autolaunched | Replaces Loop+Assignment(build)+Assignment(Add); declarative mapping |
| Need a sorted or top-N subset | Get Records with Sort Order + Number of Records to Store | Push work to the database; avoids any loop |
| Need to look up B-rows by key while iterating A | One Get Records of all B + Loop A + Decision against in-memory B | Avoids SOQL-in-loop; single query regardless of A size |
| Genuinely complex per-row logic with branching DML | Invocable Apex receiving `List<SObject>` | Apex map/set primitives, full bulkification, real unit tests |
| Two input collections joined many-to-many | Pre-loaded map collection + single outer Loop | Nested Loops are O(n*m) elements counted against the 2,000-element interview limit |

---

## Recommended Workflow

1. **Inventory every Loop element** in the flow (and every subflow it calls). Record the input collection variable, sObject type, and expected size.
2. **Classify each loop's body** by what elements it contains: Pure (Assignment / Decision only), DML-in-loop (Create / Update / Delete), SOQL-in-loop (Get Records), Action-in-loop (Apex invocable), Subflow-in-loop (recurse and re-classify).
3. **Refactor every DML-in-loop and SOQL-in-loop** using Collect-Then-DML or Map-Lookup. Subflow-in-loop is refactored by either inlining the subflow logic or re-shaping the subflow to accept and operate on a collection.
4. **Consider replacing the loop entirely** — could a Collection Filter, Transform, or sharper Get Records eliminate the loop? If yes, prefer the loop-free version.
5. **Validate against `flow-bulkification`** — verify the redesigned flow respects the 200-record save-trigger contract and stays inside the 2,000-element interview limit. For high-volume scenarios also consult `flow-large-data-volume-patterns` and `flow-governor-limits-deep-dive`.

---

## Review Checklist

- [ ] No Create / Update / Delete Records element appears inside any Loop body (direct or via subflow / action).
- [ ] No Get Records element appears inside any Loop body.
- [ ] Every loop with mutation has a corresponding Assignment-with-Add into a target collection AND a single post-loop DML.
- [ ] No nested loops unless the inner-collection size is hard-bounded to a small constant AND a Map-Lookup pattern was rejected with reason documented.
- [ ] Iteration-variable assignments are NOT relied on to persist to the database (a separate Update Records on a collection exists).
- [ ] Element-count estimate (loops counted as `body_elements * iterations`) stays under 2,000 per interview at expected volume.
- [ ] Pure-filter loops have been replaced with Collection Filter; pure-transform loops have been replaced with Transform where Spring '24+ permits.
- [ ] Subflows called inside a loop have been inspected for hidden DML / SOQL.

---

## Salesforce-Specific Gotchas

1. **Iteration variable for SObject collections is a reference, not a copy** — modifying `loopItem.Field__c` inside an Assignment changes the in-memory source collection, but does NOT persist to the database. Practitioners assume the change is saved and skip the post-loop Update Records. Result: silent data loss until QA notices.
2. **Iteration variable retains the last item after the loop ends** — the variable is flow-scoped, not loop-scoped. Downstream elements that reference it get the last record processed (or null if the input collection was empty). Convenient for "last item" logic, but a bug if accidentally referenced.
3. **Per-interview 2,000-element execution limit** — every element executed counts. A loop body of 4 elements iterating 200 records consumes 800 element-executions just from the body, before any pre/post work. Nested loops at 200×200 = 40,000+ element-executions, which Flow halts with `Number of executed elements has exceeded the maximum`.
4. **DML budget is per-transaction, shared across the whole call stack** — the 150-DML cap is shared with every other trigger, flow, and Apex class in the same transaction. A loop with one DML inside, called from a record-triggered context already running 50 other automations, busts the limit much earlier than 150 iterations.
5. **Subflow-in-loop hides the anti-pattern from a casual review** — `LoopOverContacts → Subflow_RefreshAccountSummary` looks innocuous. Open the subflow and it does Get Records + Update Records — congratulations, you have SOQL-in-loop AND DML-in-loop, just two screens away.
6. **Collection variables are NOT auto-deduped** — `Add` on Assignment appends every time, including duplicates. If a loop with branching paths can `Add` the same record from two branches, your post-loop Update Records will issue duplicate writes (one DML, but the same row updated twice in memory) — and worse, can hit the "duplicate id in collection" runtime error on Update.
7. **Loop iteration order is the source-collection order, not deterministic** — if the input came from Get Records without a Sort Order, ordering depends on the database's chosen index. Order-dependent loop logic is a bug waiting to happen across orgs.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Loop inventory table | One row per Loop element with input collection, body classification (pure / DML / SOQL / subflow / action), expected iteration count, and pass/fail verdict |
| Refactor diff per anti-pattern loop | Before/after element list showing the collect-then-DML conversion, plus the new collection variable to declare |
| Element-count estimate | Worst-case element-executions per interview, compared to the 2,000-element ceiling |
| Loop-free alternative recommendation | Per loop, a yes/no on whether Collection Filter / Transform / Get-with-criteria could eliminate it, with reason |
| Subflow inspection report | For every subflow called inside a loop body, a verdict on whether it contains hidden DML / SOQL |

---

## Related Skills

- `flow-bulkification` — the broader framing for designing flows that survive 200-record bulk save contexts. This skill is the loop-specific subset of that work.
- `flow-collection-processing` — full reference for Loop, Assignment-with-Add, Collection Filter, Collection Sort, and Transform semantics. Read this first for collection element selection.
- `flow-cross-object-updates` — when the loop body reaches into related records, the cross-object update patterns describe how to batch parent / child writes.
- `flow-get-records-optimization` — most SOQL-in-loop refactors collapse into a single optimized Get Records; this skill shows how to write that query.
- `flow-governor-limits-deep-dive` — exhaustive treatment of the 2,000-element / 150-DML / 100-SOQL ceilings the loop must respect.
- `flow-large-data-volume-patterns` — when the input collection itself is too big for a single transaction (move to scheduled-paths or invocable Apex).
- `fault-handling` — fault paths around the post-loop DML so a single bad row does not silently roll back the whole interview.
- `subflows-and-reusability` — when refactoring subflow-in-loop, the contract for bulk-safe subflow inputs.

---

## Official Sources Used

- Flow Loop element reference — https://help.salesforce.com/s/articleView?id=platform.flow_ref_elements_loop.htm&type=5
- Flow Builder Considerations and Limits — https://help.salesforce.com/s/articleView?id=sf.flow_considerations_limits_general.htm&type=5
- Flow Best Practices (avoid DML/SOQL inside loops) — https://help.salesforce.com/s/articleView?id=sf.flow_prep_bestpractices.htm&type=5
- Apex Governor Limits (per-transaction DML and SOQL ceilings the flow shares) — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_gov_limits.htm
- Collection Filter element — https://help.salesforce.com/s/articleView?id=platform.flow_ref_elements_collection_filter.htm&type=5
- Transform element — https://help.salesforce.com/s/articleView?id=platform.flow_ref_elements_transform.htm&type=5
