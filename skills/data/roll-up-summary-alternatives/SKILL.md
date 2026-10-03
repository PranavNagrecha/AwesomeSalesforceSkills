---
name: roll-up-summary-alternatives
description: "Use when native Roll-Up Summary fields are not enough and the design needs Flow, Apex aggregate, or DLRS-style alternatives for lookup or advanced summary scenarios. Triggers: 'roll up summary on lookup', 'build a lookup rollup', 'count child records on a lookup'. NOT for ordinary master-detail roll-ups that fit native limits — use apex/cross-object-formula-and-rollup-performance."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Reliability
tags:
  - roll-up-summary
  - dlrs
  - aggregate-soql
  - lookup-rollup
  - parent-child-summary
triggers:
  - "how do I do a roll up summary on a lookup relationship"
  - "DLRS versus Flow versus Apex rollup"
  - "count child records on parent in Salesforce"
  - "native roll up summary limitations"
  - "aggregate trigger for parent totals"
  - "build a rollup count on a lookup relationship that stays correct after deletes and merges"
  - "replace DLRS with a flow or Apex rollup"
inputs:
  - "relationship type such as master-detail or lookup"
  - "summary type such as count, sum, min, max, or filtered total"
  - "data volume, real-time expectation, and allowed tooling"
outputs:
  - "summary-pattern recommendation"
  - "review findings for scale and maintenance risk"
  - "implementation sketch for Flow, Apex, or native summary"
dependencies: []
version: 1.0.2
author: Pranav Nagrecha
updated: 2026-10-03
---

# Roll Up Summary Alternatives

Use this skill when stakeholders say "just add a roll-up field" and the platform answer is "not natively, at least not that way." Native Roll-Up Summary fields work when the relationship is master-detail and the summary is a count, sum, min, or max. Lookup relationships, other calculations, and high-churn parents need a different implementation, and each one has its own failure modes.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is the relationship master-detail or lookup? A native summary's `summaryForeignKey` must be the master-detail field on the child.
- Which operation: count, sum, min, max, or something native summaries do not offer (average, count distinct, concatenate, first, last)?
- Does the total have to be right in the same transaction, or is eventual consistency acceptable?
- How many children can one parent have, and how many child rows change per load?
- Does anything merge, cascade-delete, or undelete these records? Those paths skip child triggers.
- Is the team comfortable with Apex, an installed package such as DLRS, or Flow only?

---

## Questions to Ask Before Configuring

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "Is the child related by master-detail or by lookup?" | Native summaries need the master-detail field as `summaryForeignKey` | Native field when possible; a custom pattern only when required | No custom code where a native field would do |
| "Do children get merged, cascade-deleted, or undeleted with a parent?" | Reparenting from a merge, cascaded deletes, and child undeletes do not fire child triggers | A scheduled recompute that repairs totals | Totals that recover from paths the trigger never sees |
| "Will this run as a Flow, and must it handle deletes?" | Record-triggered flows run on delete only before the record is deleted, and Flow has no undelete trigger | A recount that excludes the record being deleted, plus a repair job for undeletes | A Flow total that does not overcount by one on every delete |
| "How many children can one parent hold, and do loads arrive grouped by parent?" | Skewed parents and ungrouped loads concentrate locks on the same parent rows | Child loads sorted by parent, and a recompute batch size that fits | Fewer lock errors during loads |
| "Is SUM over many children going to run in one transaction?" | SUM, MIN, MAX, and AVG count every aggregated row toward query-row limits; COUNT counts one row per group | Scoped recomputes for very large parents | No query-row limit errors on big parents |
| "Will we ever replace a native roll-up with a custom field?" | Deleting a roll-up summary field through Metadata API purges it with no Recycle Bin | A backup of definitions and reports before the swap | A reversible migration plan |

What a proper configuration adds over a quick counter field: the total stays correct through deletes, merges, undeletes, and bulk loads, and there is a repair job when it does not.

---

## Core Concepts

### Native roll-up summary is the first choice

`CustomField` of type `Summary` supports `summaryOperation` values Count, Min, Max, and Sum, an optional `summarizedField`, `summaryFilterItems`, and `summaryForeignKey`, which "represents the master-detail field on the child" (Metadata API Developer Guide). The platform recalculates native summaries during the parent's save procedure: step 16 of the order of execution updates the parent, and step 17 updates a grandparent.

### Lookup roll-ups need an alternative

| Option | Runs when | Strengths | Watch out for |
|---|---|---|---|
| Apex trigger plus aggregate SOQL | After insert, update, delete, undelete on the child | Full control, bulk-safe, testable | Merge reparenting, cascaded deletes, and child undeletes skip child triggers |
| Record-triggered Flow | After save for create and update; before delete for delete | Declarative ownership | No after-delete or undelete trigger; a before-delete recount still sees the deleted row |
| DLRS (open-source package) | Realtime, Scheduled, or Developer API modes | Declarative; adds Average, Count Distinct, Concatenate, First, Last | A package to install, upgrade, and monitor |
| Scheduled recompute (Batch Apex or scheduled Flow) | On a schedule | Repairs drift from any path | Totals are stale between runs |

### Triggers do not see every change

The Apex Developer Guide lists operations that don't invoke triggers, including cascading deletes ("only records that initiate a delete cause trigger evaluation") and cascading updates of child records reparented by a merge. After undelete runs only on top-level objects: undeleting an Account restores its Opportunities, but only the Account trigger runs. Any trigger-maintained total needs a recompute path.

### Aggregate queries still cost query rows

All aggregate functions other than COUNT() and COUNT(fieldname) count each aggregated row as a query row. COUNT counts one row, or one per group with GROUP BY.

---

## Common Patterns

### Native roll-up on master-detail

Use the platform field. Worked XML in `references/metadata-examples.md`.

### Apex recompute-from-source

Collect affected parent IDs from `Trigger.new` and `Trigger.old` (both old and new parents on reparent), run one aggregate query, write only parents whose value changed, and schedule the same method as a repair batch. Full trigger, service, batch, and test class in `references/examples.md`.

### Flow-maintained summary

Use after-save flows for create and update. For delete, use a before-delete flow whose recount filters out `$Record.Id`. Pair it with a scheduled recompute for undeletes and merges.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Master-detail and count, sum, min, or max | Native roll-up summary | Platform recalculates in the save procedure |
| Lookup, moderate volume, admin-owned | Flow (create and update after save, delete before delete) plus a scheduled recompute | Flow has no after-delete or undelete trigger |
| Lookup, high volume or complex filters | Apex trigger with aggregate SOQL plus a repair batch | Bulk control and testability |
| Needs average, count distinct, concatenate, first, or last | DLRS or Apex | Native summaries offer only Count, Min, Max, Sum |
| Records are merged or cascade-deleted | Add a scheduled recompute to any trigger or Flow approach | Those paths skip child triggers |
| Replacing a native field with a custom one | Back up first | Metadata API purges deleted roll-up summary fields |

---

## Recommended Workflow

1. **Classify the relationship and operation.** Master-detail plus count, sum, min, or max goes native; stop there.
2. **List every path that changes a child.** Insert, update (including reparent), delete, undelete, merge, cascade delete, bulk loads.
3. **Pick the engine.** Use the option table above; size it against parent skew and daily load volume.
4. **Build recompute-from-source.** One aggregate per transaction, write only changed parents, and a scheduled repair job. Start from `references/examples.md`.
5. **Test the paths.** 200-row inserts, reparent, delete, undelete, and a repair run; then run `python3 scripts/check_roll_up_summary_alternatives.py --manifest-dir force-app`.
6. **Assign an owner.** Name who watches repair-job results and who answers "why is this total wrong."

---

## Review Checklist

- [ ] Native roll-up was rejected for a real reason (lookup relationship or unsupported operation)
- [ ] Every child-change path is handled, including reparent, delete, and undelete
- [ ] A scheduled recompute repairs merge, cascade-delete, and undelete drift
- [ ] No aggregate SOQL inside a loop
- [ ] Before-delete flow recounts exclude the record being deleted
- [ ] Child loads are grouped by parent
- [ ] An owner is named for repair results

---

## Salesforce-Specific Gotchas

See `references/gotchas.md`. The two most often missed: merges and cascaded deletes change children without firing child triggers, and a before-delete flow still counts the record it is deleting.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Summary decision | Native, Flow, Apex, or DLRS, with the reason |
| Rollup implementation | Trigger, service, repair batch, and tests, or the Flow pair |
| Path coverage table | Each child-change path and what keeps the total right |

---

## Related Skills

- `apex/cross-object-formula-and-rollup-performance`: ordinary master-detail roll-ups that fit native limits
- `apex/trigger-framework`: when the rollup implementation is becoming trigger-architecture work
- `apex/recursive-trigger-prevention`: when parent-summary writes are causing re-entry problems
- `data/multi-currency-and-advanced-currency-management`: when the rollup depends on currency conversion
