---
name: activity-and-task-patterns
description: "Task and Event objects: polymorphic WhatId/WhoId, Activity object model, ActivityHistory vs OpenActivity, activity timeline customization, bulk task creation, Einstein Activity Capture boundaries. NOT for turning on EAC or calendar sync — use admin/einstein-activity-capture-setup. NOT for Email-to-Case — use admin/case-management-setup. Covers ActivitiesSettings metadata, enableActivities, shared Task/Event custom fields and FLS, TaskStatus value sets, Shared Activities and TaskRelation/EventRelation, recurring and child activities, and partial-success bulk DML on Task."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
tags:
  - task
  - event
  - activity
  - whatid
  - whoid
  - einstein-activity-capture
triggers:
  - "task whatid whoid polymorphic lookup soql"
  - "why are some activities missing from the record activity timeline"
  - "bulk create tasks from apex dml best practice"
  - "activityhistory openactivity difference"
  - "einstein activity capture data storage and reporting"
  - "custom fields on activity task event sharing"
  - "salesforce task whatid whoid polymorphic typeof"
  - "bulk task insert emailed every assignee an assignment notification"
  - "cannot enable shared activities by deploying activitiessettings"
  - "task subject or status filter is slow and cannot be custom indexed"
  - "update event failed only isreminderset allowed on child event"
  - "emailmessage activityid points at a deleted task"
  - "add a custom field to task but not event"
  - "activitiessettings metadata xml enablerecurringtasks enablegrouptasks"
  - "insert tasks with partial success instead of rolling back the batch"
inputs:
  - Objects requiring activity tracking
  - Volume of tasks/events generated per day
  - Einstein Activity Capture license status
  - Reporting requirements on activities
outputs:
  - Activity model decision (Task, Event, custom)
  - Polymorphic query patterns
  - Bulk creation pattern
  - Activity reporting approach
dependencies: []
version: 1.2.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Activity and Task Patterns

Activate when designing interactions with Salesforce Activities — Task and Event records that attach to other objects via polymorphic `WhatId` and `WhoId`. The Activity object model is unusual: `Activity` is a read-only abstract parent, `Task` and `Event` are concrete children, and `ActivityHistory` / `OpenActivity` are read-only related lists, not queryable in bulk.

## Before Starting

- **Understand the Activity object model.** `Activity` cannot be queried directly; query `Task` or `Event`. `ActivityHistory` and `OpenActivity` appear on related lists and subqueries only.
- **Know the polymorphic fields.** `WhatId` can reference any object enabled for activities; `WhoId` references Contact or Lead. Require `TYPEOF` or explicit type filters in SOQL.
- **Check Einstein Activity Capture.** EAC-captured emails/events are stored outside standard Task/Event and are not reportable the same way.

## Questions to Ask Before Configuring

Ask these before writing a line of Apex or opening Setup. Each one maps to a platform behaviour documented in `references/gotchas.md`; skipping them produces activity code that passes review and then misbehaves in production.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Is Shared Activities on in this org, and who turned it on?" | It cannot be enabled or disabled by a deploy — `allowUsersToRelateMultipleContactsToTasksAndEvents` has been read-only in every API version since v36.0 | Whether `TaskWhoIds`, `TaskRelation` and multi-contact relates exist at all, before code assumes them |
| "Who owns these activities, and should each one email its owner?" | Apex DML that creates or modifies a Task triggers the assignment notification by default | A decision to set `EmailHeader.triggerUserEmail`, and a backfill that doesn't mail thousands of people |
| "What is the read path — which field will the WHERE clause filter on?" | `Subject`, `TaskStatus` and `TaskPriority` are on the platform's can't-index list; `WhatId` / `OwnerId` / date ranges are not | Whether Task/Event survives the volume, or the design needs a custom `Interaction__c` |
| "Does this field make sense on both a Task and an Event?" | There is no Task-only custom field; Activity fields land on both children and share field-level security | The validation rule that scopes it, and the FLS entries for **both** objects in the same deploy |
| "Are any of these activities recurring, or occurrences of a series?" | Recurring Tasks can't be flipped after creation and reject `ActivityDate`/`Status` updates; child Events accept updates to `IsReminderSet` and `ReminderDateTime` only | A partition step before the bulk DML instead of a half-failed job |
| "Is Einstein Activity Capture on for anyone here?" | EAC-captured mail and events live outside the `Task`/`Event` tables, so reports and triggers silently miss them | An explicit source-of-truth statement in the data dictionary |
| "Can one bad row be allowed to fail on its own?" | The bare `insert` verb rolls the whole transaction back; `Database.insert(..., dmlOptions, ...)` does not | A partial-success write plus the `Database.SaveResult` loop that reports what didn't land |

What a proper configuration adds over just creating the records: the activity model matches the org's actual read path and volume, the shared Task/Event surface is deployed as one unit instead of half of it silently disabling FLS, and bulk writes fail one row at a time and quietly instead of rolling back a 200-record save while emailing everyone.

## Core Concepts

### Task vs Event

Task: to-do item with due date. Event: calendar appointment with start/end time. Both share the polymorphic `WhatId` / `WhoId` pattern and an IsTask discriminator on Activity queries.

### Polymorphic SOQL

```
SELECT Id, Subject, What.Type, TYPEOF What
  WHEN Account THEN Name, Industry
  WHEN Opportunity THEN Amount, StageName
END FROM Task
```

Without TYPEOF, only ID and Type are accessible via `What.Type`.

### ActivityHistory vs OpenActivity

`ActivityHistory`: closed activities (completed tasks, past events). `OpenActivity`: open activities (due, upcoming). Only queryable as subqueries from activity-enabled parents. Cannot create/update these objects directly.

### Einstein Activity Capture

EAC syncs emails and calendar events from Exchange/Gmail into Salesforce. Data lives in a separate EAC store — visible on timeline, but not in Task/Event tables. Reporting requires Activity Metrics or EAC-specific features.

## Common Patterns

### Pattern: Bulk task creation from trigger

```apex
List<Task> tasks = new List<Task>();
for (Opportunity o : Trigger.new) {
    tasks.add(new Task(WhatId = o.Id, Subject = 'Review',
                       ActivityDate = Date.today().addDays(7), OwnerId = o.OwnerId));
}

Database.DMLOptions dml = new Database.DMLOptions();
dml.optAllOrNone = false;                  // one bad WhoId must not roll back the save
dml.EmailHeader.triggerUserEmail = false;  // suppress "a task was assigned to you"

List<Database.SaveResult> results =
    Database.insert(tasks, dml, AccessLevel.SYSTEM_MODE);
```

Collect and write once — never loop-DML. The two `DMLOptions` lines are not optional polish: creating or modifying a Task is one of the events that fires `triggerUserEmail`, and the bare `insert` verb has nowhere to put either setting. Full version with result handling in `references/metadata-examples.md` section 5.

### Pattern: Custom Object for high-volume activity-like data

Past roughly 50k activities/day per object — UNVERIFIED (2026-09-05): a field heuristic, no activity-volume ceiling is published in the App Limits cheat sheet or the LDV guide — consider a custom `Interaction__c` with a real lookup instead of polymorphic Task. The grounded reason to switch is the read path, not the number: the LDV guide lists Activity `Subject`, `TaskStatus` and `TaskPriority` among the standard fields the platform can't index, so a query that must filter on any of them will not get selective on a large Task table.

### Pattern: Activity rollup via Lightning component or Apex

Activity count / last-activity-date rollups: use formula-friendly patterns (e.g., Salesforce's Activity Metrics, EAC Insights, or DLRS).

## Decision Guidance

| Need | Approach |
|---|---|
| Standard to-do with reminders | Task |
| Calendar appointment with participants | Event |
| Query must filter on activity subject or status at volume | Custom `Interaction__c` with an indexed field |
| Email tracking without EAC | EmailMessage + Task linking |
| Reporting on email activity | Activity Metrics or EAC Insights |

## Recommended Workflow

1. **Establish what the org already does.** Retrieve `Settings:Activities` and check whether Shared Activities is on — it is a read-only field no deploy can change, and `TaskWhoIds` / `TaskRelation` / `EventRelation.IsParent` only exist when it is. Note whether Einstein Activity Capture is enabled for anyone (`admin/einstein-activity-capture-setup`).
2. **Decide Task/Event vs custom `Interaction__c`** using the Decision Guidance table above and the tradeoff table in `references/well-architected.md`. Drive the decision from the read path and the sharing requirement, not from record count alone.
3. **Write the metadata from `references/metadata-examples.md`** — `Activities.settings-meta.xml`, `enableActivities` on every object that must be a valid `WhatId`, the custom field under `Activity` (never under Task), the `TaskStatus` value set if `IsClosed` semantics are changing, and FLS entries for Task **and** Event in the same permission set.
4. **Write the read path with `TYPEOF` or a `What.Type` filter**, and the write path with `Database.insert(records, dmlOptions, accessLevel)` carrying `optAllOrNone = false` and `EmailHeader.triggerUserEmail = false`. Partition out recurring Tasks and child Events (`IsChild = true`) before any bulk update.
5. **Lint the working tree** with `python3 skills/admin/activity-and-task-patterns/scripts/check_activity_and_task_patterns.py --manifest-dir force-app/main/default`. It flags `FROM Activity`, DML on `ActivityHistory`/`OpenActivity`, loop-DML on Task/Event, `What.<field>` without `TYPEOF`, bare `insert`/`update` of Task collections, `ActivitiesSettings` files that try to set the read-only Shared Activities flag, and permission-set FLS that names one child object but not the other.
6. **Read `references/gotchas.md` end to end before deploying** — the ten entries are the failures this skill exists to prevent, and several of them (the 500-row subquery cap, shared FLS, the EmailMessage task swap) are invisible in a sandbox with test-sized data.
7. **Verify in the target org** using the three checks at the end of `references/metadata-examples.md`: a Task insert against the newly activity-enabled object, a `Status`/`IsClosed`/`CompletedDateTime` query, and a `FieldPermissions` query that must return a row for both `Task.<field>` and `Event.<field>`.

## Review Checklist

- [ ] Activity volume estimated and matched to object choice
- [ ] Polymorphic SOQL uses TYPEOF or explicit type filters
- [ ] Bulk DML used for task/event creation
- [ ] ActivityHistory / OpenActivity queries only in subquery form
- [ ] EAC data strategy documented
- [ ] Custom fields on Activity limited (they propagate to both Task and Event)
- [ ] Sharing model for activities understood (inherits from WhatId parent)
- [ ] FLS deployed for `Task.<field>` **and** `Event.<field>` — a missing entry disables, it does not preserve
- [ ] Bulk writes use `Database.insert(..., dmlOptions, accessLevel)` with `optAllOrNone = false`
- [ ] `EmailHeader.triggerUserEmail` set deliberately on any job that creates or modifies Tasks
- [ ] Recurring Tasks and `IsChild = true` Events partitioned out before bulk update
- [ ] Shared Activities state confirmed in the org, not assumed from a deploy
- [ ] `WHERE` clauses filter on an indexable field, not `Subject` / `Status` / `Priority` alone
- [ ] `scripts/check_activity_and_task_patterns.py --manifest-dir …` run clean

## Salesforce-Specific Gotchas

1. **Custom fields on `Activity` propagate to both Task and Event.** You cannot add a field only to Task — architect with this in mind.
2. **Activities inherit sharing from the `WhatId` parent.** No independent sharing rules.
3. **`OpenActivity` and `ActivityHistory` cannot be modified.** They are projections of Task/Event — the Object Reference lists `describeSObjects()` as their only supported call (object_reference.txt L23515–L23516, L191459–L191460).
4. **Shared Activities is not deployable.** Its `ActivitiesSettings` field has been read-only in every API version since v36.0; a deploy that sets it succeeds and changes nothing.
5. **`Task.IsClosed` is never written directly.** It is derived from the `Status` value's `closed` flag in the `TaskStatus` standard value set, and `Event` has no `Status` at all.

The ten platform behaviours behind these — with what happens, when, and how to avoid — are in `references/gotchas.md`.

## Output Artifacts

| Artifact | Description |
|---|---|
| Activity model decision | Task vs Event vs custom object |
| SOQL pattern library | Polymorphic queries with TYPEOF |
| Bulk creation template | Apex trigger / batch pattern |

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing the deployable XML — `ActivitiesSettings`, `enableActivities`, an Activity custom field and its FLS, `TaskStatus`, plus the bulk-safe Apex and the post-deploy verification queries |
| `references/gotchas.md` | Before deploying, and whenever activity behaviour differs between sandbox and production |
| `references/examples.md` | Two worked scenarios end to end: a polymorphic timeline query for an LWC, and bulk task generation from a record-triggered context |
| `references/llm-anti-patterns.md` | Reviewing AI-generated Apex or metadata that touches Task, Event or Activity |
| `references/well-architected.md` | Choosing between Task/Event and a custom `Interaction__c`, and citing the sources behind any claim in this skill |

---

## Related Skills

- `apex/apex-polymorphic-soql` — `TYPEOF`, `What.Type` and `instanceof` in depth
- `apex/apex-dml-patterns` — `Database.DMLOptions` beyond the email header, and partial-success result handling
- `apex/trigger-framework` — where activity-creating logic belongs in a handler
- `admin/einstein-activity-capture-setup` — EAC sync scope, and where EAC data actually lives
- `admin/case-management-setup` — case-related activity handling
- `admin/email-to-case-configuration` — the intake side of the `EmailMessage.ActivityId` task
- `admin/picklist-and-value-sets` — standard vs global value sets, for the `TaskStatus` change
- `admin/queues-and-public-groups` — `Task.OwnerId` accepts Groups of type Queue only
- `architect/large-data-volume-architecture` — when activity volume forces a custom object
- `data/data-archival-strategies` — what to do with `IsArchived` activities
