---
name: flow-cross-object-updates
description: "Cross-object DML in Flow: updating parent from child or child from parent via Get/Update Records, lookup traversal in formulas, and bulkification. NOT for Apex cross-object updates — use flow/flow-loop-element-patterns. Trigger keywords: update parent record from child flow, fan a parent field to all children, roll-up summary vs flow, master-detail vs lookup for a flow, flow ping-pong recursion, orphan lookup null in flow."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Scalability
tags:
  - flow
  - cross-object
  - get-records
  - update-records
  - bulkification
triggers:
  - "flow update parent from child record trigger"
  - "flow rollup sum contacts update account field"
  - "flow record-triggered get related records update"
  - "flow update child records without loop bulkification"
  - "flow formula dot traversal parent field lookup"
  - "flow cross object update too many soql dml"
  - "stamp a field on the parent record when a child record changes"
  - "push a changed field from the parent down to all its child records"
  - "two flows keep re-triggering each other on parent and child"
  - "should this be a roll-up summary field or a flow"
  - "flow fails when the lookup to the parent is empty"
  - "why did my flow fire twice when the parent updated"
  - "does master-detail or lookup change how my flow has to be built"
inputs:
  - Parent/child object relationship (lookup or master-detail)
  - Trigger context (record-triggered, scheduled, platform event)
  - Bulk volume expected
  - Which side already has a flow, and what field each side writes
outputs:
  - Flow design using Get Records + Update Records (no per-record loop DML)
  - Dot-notation traversal where a Get Records is unneeded
  - Entry criteria on both sides that break the write cycle
  - Deployable flow-meta.xml, FlowTest, and the CustomField relationship definition
dependencies: []
version: 1.2.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Flow Cross Object Updates

Activate when a flow must read or write a record other than the one that triggered it. Getting the pattern right avoids SOQL-inside-loop disasters and preserves bulk behavior when 200 records arrive at once.

## Before Starting

- **Identify the relationship direction.** Child→parent (lookup traversal) and parent→child (Get Records for related list) behave differently.
- **Check bulk context.** A record-triggered flow starts one interview per record in the triggering DML, and all of them share one transaction budget — 100 SOQL, 150 DML, 10,000 DML rows, 10,000 ms CPU (`apexdev.txt` L19542–19579). UNVERIFIED (2026-09-05): the "200 records per batch" figure people quote is the API batch size, documented on help.salesforce.com, not a Flow limit in the Metadata API or Apex guides.
- **Prefer formulas for read-only parent fields.** `$Record.Account.Name` costs no Get Records element. The Metadata API guide's own samples use dotted parent traversal on `$Record` — `$Record.Account.SLA__c`, `$Record.Product2.Name` (`api_meta.txt` L102276–102289).
- **Find out what already writes to the other object.** Half the failures in this skill are two correct flows composing into a loop; you cannot see that from inside either one.

## Questions to Ask Before Configuring

Ask these before opening Flow Builder. Every row traces to a gotcha in `references/gotchas.md`; skipping the row is how you get that gotcha.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Is the relationship master-detail or lookup, and can I change it?" | Master-detail unlocks roll-up summaries, which delete the whole child→parent flow; lookup does not (`api_meta.txt` L43648–43650) | The decision on whether this skill is needed at all — or reduces to one `CustomField` |
| "Can a child exist with an empty parent lookup?" | `deleteConstraint` defaults to `SetNull`, so deleting a parent orphans children silently (`api_meta.txt` L43347–43357) | Whether the null-guard Decision is load-bearing or defensive, and which branch the test must cover |
| "What is already record-triggered on the *other* object, and what field does it write?" | The ping-pong loop needs two flows to exist; neither author can see it alone | The write graph, and the entry condition that has to be narrower than the other side's write |
| "Is the value I am writing to the parent an aggregate, or a derived state?" | Count/Sum/Min/Max on a master-detail child is a platform-maintained field; a derived string is not (`api_meta.txt` L43651–43666) | Roll-up summary, `flow/flow-collection-processing` Transform, or a flow — in that order |
| "How many children can one parent have, worst case, and how many parents change at once?" | The fan-out multiplies: parents-in-batch × children-each, against 10,000 DML rows (`apexdev.txt` L19556) | The `<limit>` on Get Records, and whether this belongs in a scheduled flow instead |
| "Does the flow need to respect the running user's access, or run as the platform?" | `runInMode` `DefaultMode` means "how the flow is launched determines" the context (`api_meta.txt` L68374–68378) — it is not a synonym for system mode | An explicit `runInMode`, plus the `writeRequiresMasterRead` consequence on master-detail children |
| "Which side gets activated first, and how will we tell it worked?" | Both flows Active in one deploy is how an untested cycle reaches production | The staged activation order and the `FLOW_CREATE_INTERVIEW_BEGIN` count that proves no second interview fired |

What a proper configuration adds over just doing it: entry criteria on **both** objects that are provably narrower than the field the other side writes, so the cross-object write terminates on the first pass instead of relying on the platform's stack-depth-16 backstop to stop it.

## Core Concepts

### Child → Parent read: dot-notation traversal

In a Contact-triggered flow, `{!$Record.Account.Industry}` resolves the lookup without a Get Records element. UNVERIFIED (2026-09-05): the "up to 5 levels" ceiling quoted for Flow traversal is documented for SOQL child-to-parent relationships (`salesforce_app_limits_cheatsheet.txt` L1143–1146), not for Flow; help.salesforce.com is the only source for the Flow figure.

### Child → Parent write: single Update Records

```
Update Records:
  Object: Subscription__c              ← FlowRecordUpdate.object is Required
  Filter: Id = {!$Record.Subscription__c}
  Fields to set: Line_Health__c = "Attention: Cancelled Line"
```

`FlowRecordUpdate` has exactly two ways to name the target: `filters` + `inputAssignments` (shown above) or `inputReference` pointing at a record variable (`api_meta.txt` L71264–71292). Full XML for both in `references/metadata-examples.md` § 1.

### Parent → Child: Get Records then Update Records

```
Get Records:  Subscription_Line__c where Subscription__c = {!$Record.Id}
              AND Region__c != {!$Record.Region__c}     ← drops rows already correct
Loop:         Assignment only — set the field, add to `linesToUpdate`
Update Records (outside the loop): input collection `linesToUpdate`
```

The Update sits outside the Loop; `flow/flow-bulkification` owns that rule and its arithmetic. What belongs to *this* skill is the second filter: excluding children that already carry the value is what stops the fan-out from waking the child-side flow.

### Aggregates: roll-up summary before flow

`summaryForeignKey` is "the **master-detail** field on the child that defines the relationship between the parent and the child" (`api_meta.txt` L43648–43650) — one sentence that decides the design. Master-detail: use a `Summary` `CustomField`. Lookup: `flow/flow-collection-processing` (Transform / collection processors, no Loop). Loop-plus-`Add`-operator is the last resort, not the first.

## Common Patterns

### Pattern: child→parent stamp with a null guard

Line-triggered on `Line_Status__c` transition → Decision on `$Record.Subscription__c IsNull` → one Update Records on the parent. The guard is not paranoia: with `deleteConstraint` at its `SetNull` default, deleting a parent leaves children pointing at nothing.

### Pattern: parent→child fan-out that writes nothing on a re-run

Parent `Region__c` changes → Get children `WHERE Region__c != $Record.Region__c` → Loop stages → one Update. On a second pass the Get returns zero rows, the `IsEmpty` Decision short-circuits, and no DML is issued — so the child flow never wakes.

### Pattern: break the cycle at the entry condition, not in the flow body

`doesRequireRecordChangedToMeetCriteria` makes conditions "evaluate to true only if the record didn't meet the required conditions before the triggering update but now meets the conditions after the update" (`api_meta.txt` L72322–72326). Set it on **both** sides and make each side's criteria watch a field the other side never writes.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Read parent field for a decision | Dot-notation `$Record.Parent__r.Field__c` in `filterFormula` or a Decision | No Get Records element needed |
| Stamp one field on the parent | Update Records in filter mode, no Loop | The flow already holds the parent Id; a Get adds nothing |
| Count / Sum / Min / Max of master-detail children | `Summary` `CustomField` | Platform-maintained; no interview, no recursion surface |
| Same aggregate over a **lookup** relationship | `flow/flow-collection-processing` Transform or collection processor | Roll-ups require master-detail |
| Update many children from a parent change | Get (filtered to exclude correct rows) → Loop assign → Update outside loop | One DML; and a re-run writes nothing |
| Read a grandparent field | `$Record.Parent__r.GrandParent__r.Field__c` in the entry formula | One expression instead of two Get Records |
| **Write** to a grandparent | Separate Get + Update against the grandparent | Traversal reads; it does not chain writes |
| Two flows on the two objects, both Active | Narrow both entry conditions first, then activate one side at a time | Stack depth 16 is a backstop, not a design (`apexdev.txt` L19559) |

## Recommended Workflow

1. **Establish the write graph.** List every Active record-triggered flow on both objects and the fields each one writes. If the child flow writes a field the parent flow's entry criteria watch (or vice versa), you have a cycle before you build anything.
2. **Choose the relationship, then re-ask whether you need a flow.** Read `references/metadata-examples.md` § 5. Master-detail plus a `Summary` `CustomField` (§ 5.3) removes the child→parent flow entirely; `deleteConstraint` (§ 5.2) decides whether the null guard is load-bearing.
3. **Build the child→parent stamp from § 1** — entry criteria with `doesRequireRecordChangedToMeetCriteria`, the `IsNull` Decision on the lookup, one `recordUpdates`, a `faultConnector` on it. No Loop, no Get.
4. **Build the parent→child fan-out from § 3** — one `recordLookups` with both filters and a `<limit>`, a Loop whose `nextValueConnector` reaches only an `assignments` element, an `IsEmpty` Decision, one `recordUpdates` with `inputReference`.
5. **Run the checker over the source tree with both flows present:** `python3 scripts/check_flow_cross_object_updates.py --manifest-dir force-app/main/default --strict`. The ping-pong rule needs both files to fire.
6. **Deploy in the § 9 order, activating one side at a time.** Deploy the two `FlowTest` components (§ 6, § 7) with the flows and run them before activation.
7. **Verify with § 10:** the SOQL parent-plus-subquery check, then a debug log at Workflow FINE — `FLOW_CREATE_INTERVIEW_BEGIN` must not carry the other flow's definition ID, and `LIMIT_USAGE_FOR_NS` must be flat between a 1-record and a bulk load.

## Review Checklist

- [ ] No Update/Create Records reachable from a Loop's `nextValueConnector`
- [ ] Dot-notation used where a Get Records is unneeded
- [ ] `doesRequireRecordChangedToMeetCriteria` set on both objects' flows
- [ ] Each side's entry criteria watch a field the other side does not write
- [ ] Null guard on the parent lookup before any traversal or parent write
- [ ] Roll-up summary considered and rejected in writing, if the relationship is master-detail
- [ ] Get Records on children filtered by the parent Id *and* bounded by `<limit>`
- [ ] Fault paths present on every data element
- [ ] Bulk test executed in a sandbox; SOQL and DML counts flat, row count bounded
- [ ] Debug log shows no second `FLOW_CREATE_INTERVIEW_BEGIN` for the other flow

## Salesforce-Specific Gotchas

Full treatment with **What happens / When it occurs / How to avoid** in `references/gotchas.md`. Headlines:

1. **DML reachable from a Loop body** — silent under a one-record debug run, fatal at 150 DML statements (`apexdev.txt` L19550).
2. **Traversal through an empty lookup yields nothing** — and `deleteConstraint` defaults to `SetNull`, so orphans are the normal case, not the edge case.
3. **A flow's parent update re-enters the parent's save order** — "when a process or flow executes a DML operation, the affected record goes through the save procedure" (`apexdev.txt` L15468).
4. **Roll-up recalculation is step 16, and a recursive save skips steps 9 through 17** (`apexdev.txt` L15414–15415, L15471–15477) — a flow inside a recursive save cannot trust the roll-up.
5. **Bulk child inserts contend on the parent lock** — the Bulk API guide's own example is a child record whose parent "is locked during the transaction" (`api_asynch.txt` L2701–2707).
6. **`runInMode` `DefaultMode` is not system mode** — it means the launch decides (`api_meta.txt` L68374–68378).

## Output Artifacts

| Artifact | Description |
|---|---|
| Child→parent stamp flow | `references/metadata-examples.md` § 1 — entry criteria, null guard, one DML, fault path |
| Parent→child fan-out flow | § 3 — one Get with an exclusion filter, staging Loop, one Update |
| `CustomField` relationship pair | § 5 — MasterDetail vs Lookup with `deleteConstraint`, plus the roll-up summary alternative |
| Two `FlowTest` components | § 6, § 7 — the transition each flow's entry criteria depend on |
| `package.xml` + deploy order | § 8, § 9 — including the MasterDetail↔Lookup `checkOnly` caveat |
| Checker | `scripts/check_flow_cross_object_updates.py` — DML-in-loop, ping-pong pair, missing null guard, roll-up-instead-of-loop, unbounded child Get, `SetNull` assumption |

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | You are building: deployable flow XML both directions, the `CustomField` pair, `FlowTest`, `package.xml`, deploy order, verification |
| `references/gotchas.md` | A cross-object flow behaves in a way the design does not explain — recursion, orphans, locks, roll-up timing |
| `references/examples.md` | You want the two scenarios narrated end to end, plus the anti-pattern and how it fails |
| `references/llm-anti-patterns.md` | Reviewing generated Flow metadata, or writing the review prompt |
| `references/well-architected.md` | Choosing Flow vs Apex for the cross-object write, or defending the choice; also the source list |

## Related Skills

- `flow/flow-bulkification` — why the Update sits outside the Loop, and the staging collection
- `flow/flow-collection-processing` — Transform and collection processors for aggregates over a lookup
- `flow/flow-record-save-order-interaction` — what a flow's cross-object DML re-enters, step by step
- `flow/recursion-and-re-entry-prevention` — re-entry guards beyond entry criteria
- `flow/record-triggered-flow-patterns` — before-save vs after-save, `triggerOrder`, scheduled paths
- `flow/flow-record-locking-and-contention` — parent lock contention during bulk child DML
- `flow/flow-testing` — `FlowTest` coverage and what it cannot reach
- `admin/lookup-and-relationship-design` — choosing master-detail vs lookup in the first place
- `apex/cross-object-formula-and-rollup-performance` — when the declarative roll-up itself becomes the cost
- `apex/recursive-trigger-prevention` — the Apex side of an Apex↔Flow ping-pong
