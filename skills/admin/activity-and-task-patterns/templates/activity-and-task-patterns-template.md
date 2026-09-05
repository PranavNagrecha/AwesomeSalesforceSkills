# Activity And Task Patterns — Work Template

Copy this file into the working notes for an activity/task design or review.
Every prompt below maps to a section of `SKILL.md` or `references/gotchas.md`.

## Scope

**Skill:** `activity-and-task-patterns`

**Request summary:** _(what the requester asked for, in their words)_

**Target org / sandbox:** _(alias)_

**One target per pass.** If the request spans two objects or two automations,
split it.

## Context Gathered

Answers to `## Questions to Ask Before Configuring` in `SKILL.md`.

| Question | Answer | Consequence for this design |
|---|---|---|
| Shared Activities on? Who enabled it? | | `TaskWhoIds` / `TaskRelation` / `EventRelation.IsParent` available or not |
| Who owns these activities; should each one email its owner? | | `EmailHeader.triggerUserEmail` setting |
| Which field will the `WHERE` clause filter on? | | Task/Event survives the volume, or `Interaction__c` |
| Does the field make sense on both Task and Event? | | Validation-rule scoping + both FLS entries |
| Any recurring Tasks or child Events in scope? | | Partition step before bulk DML |
| Einstein Activity Capture on for anyone? | | Source-of-truth statement for reporting |
| Can one bad row fail on its own? | | `optAllOrNone` value |

**Volume estimate:** _(activities/day per object, and lifetime rows on the
largest parent — the 500-row `ActivityHistories` subquery cap bites above that)_

**Existing consumers:** _(reports, dashboards, Flows, triggers, LWCs, and
integrations that read Task/Event today)_

## Approach

**Object choice:** Task / Event / custom `Interaction__c` — and the reason,
taken from the tradeoff table in `references/well-architected.md`.

**Metadata to write** (shapes in `references/metadata-examples.md`):

- [ ] `settings/Activities.settings-meta.xml`
- [ ] `enableActivities` on: _(objects)_
- [ ] Custom field under `objects/Activity/fields/`: _(name, type)_
- [ ] FLS for `Task.<field>` **and** `Event.<field>`
- [ ] `standardValueSets/TaskStatus.standardValueSet-meta.xml`
- [ ] Apex: _(class / trigger)_

**Read path:** `TYPEOF` branches needed, or a `What.Type` filter — list the
object types the query must handle, including the `ELSE` case.

**Write path:** `Database.insert(records, dmlOptions, accessLevel)` with
`optAllOrNone` = ____ and `EmailHeader.triggerUserEmail` = ____.

## Checklist

From `## Review Checklist` in `SKILL.md`.

- [ ] Activity volume estimated and matched to object choice
- [ ] Polymorphic SOQL uses `TYPEOF` or explicit type filters
- [ ] Bulk DML used for task/event creation
- [ ] `ActivityHistory` / `OpenActivity` queried only in subquery form
- [ ] EAC data strategy documented
- [ ] Custom fields on Activity limited (they propagate to both Task and Event)
- [ ] Sharing model understood (activities inherit from the `WhatId` parent)
- [ ] FLS deployed for `Task.<field>` **and** `Event.<field>`
- [ ] Bulk writes use `Database.insert(..., dmlOptions, accessLevel)` with `optAllOrNone = false`
- [ ] `EmailHeader.triggerUserEmail` set deliberately
- [ ] Recurring Tasks and `IsChild = true` Events partitioned out before bulk update
- [ ] Shared Activities state confirmed in the org, not assumed from a deploy
- [ ] `WHERE` clauses filter on an indexable field
- [ ] `scripts/check_activity_and_task_patterns.py --manifest-dir …` run clean

## Verification

Post-deploy checks from the end of `references/metadata-examples.md`:

- [ ] Task insert against the newly activity-enabled object succeeds
- [ ] `Status` / `IsClosed` / `CompletedDateTime` query returns the expected shape
- [ ] `FieldPermissions` query returns a row for **both** `Task.<field>` and `Event.<field>`

## Notes

**Deviations from the standard pattern, and why:**

**Ambiguities left open for the requester:**

**Confidence:** HIGH / MEDIUM / LOW
