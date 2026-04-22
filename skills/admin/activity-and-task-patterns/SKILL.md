---
name: activity-and-task-patterns
description: "Task and Event objects: polymorphic WhatId/WhoId, Activity object model, ActivityHistory vs OpenActivity, activity timeline customization, bulk task creation, Einstein Activity Capture boundaries. NOT for Calendar sharing (use calendar-sharing-setup). NOT for Email-to-Case (use case-management-setup)."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-21
---

# Activity and Task Patterns

Activate when designing interactions with Salesforce Activities — Task and Event records that attach to other objects via polymorphic `WhatId` and `WhoId`. The Activity object model is unusual: `Activity` is a read-only abstract parent, `Task` and `Event` are concrete children, and `ActivityHistory` / `OpenActivity` are read-only related lists, not queryable in bulk.

## Before Starting

- **Understand the Activity object model.** `Activity` cannot be queried directly; query `Task` or `Event`. `ActivityHistory` and `OpenActivity` appear on related lists and subqueries only.
- **Know the polymorphic fields.** `WhatId` can reference any object enabled for activities; `WhoId` references Contact or Lead. Require `TYPEOF` or explicit type filters in SOQL.
- **Check Einstein Activity Capture.** EAC-captured emails/events are stored outside standard Task/Event and are not reportable the same way.

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

```
List<Task> tasks = new List<Task>();
for (Opportunity o : Trigger.new) {
    tasks.add(new Task(WhatId = o.Id, Subject = 'Review', ActivityDate = Date.today().addDays(7), OwnerId = o.OwnerId));
}
insert tasks;
```

Never loop-DML inside trigger; collect and insert once.

### Pattern: Custom Object for high-volume activity-like data

If volume exceeds ~50k activities/day per object, consider a custom `Interaction__c` object with lookup instead of polymorphic Task. Better indexing, custom sharing, no Task-UI overhead.

### Pattern: Activity rollup via Lightning component or Apex

Activity count / last-activity-date rollups: use formula-friendly patterns (e.g., Salesforce's Activity Metrics, EAC Insights, or DLRS).

## Decision Guidance

| Need | Approach |
|---|---|
| Standard to-do with reminders | Task |
| Calendar appointment with participants | Event |
| 100k+ interactions per day | Custom Interaction__c object |
| Email tracking without EAC | EmailMessage + Task linking |
| Reporting on email activity | Activity Metrics or EAC Insights |

## Recommended Workflow

1. Inventory activity-generating processes; estimate daily volume per object.
2. If volume is modest and UI integration matters, use Task/Event.
3. For polymorphic queries, use `TYPEOF` and index-friendly `WhatId` filters.
4. Bulk-insert from triggers; never single-DML in loops.
5. Customize Activity Timeline via LWC or Flow for business-specific views.
6. Decide EAC vs manual logging; document where activity data lives.
7. Build reports using Task/Event + Activity Metrics; avoid querying ActivityHistory outside subqueries.

## Review Checklist

- [ ] Activity volume estimated and matched to object choice
- [ ] Polymorphic SOQL uses TYPEOF or explicit type filters
- [ ] Bulk DML used for task/event creation
- [ ] ActivityHistory / OpenActivity queries only in subquery form
- [ ] EAC data strategy documented
- [ ] Custom fields on Activity limited (they propagate to both Task and Event)
- [ ] Sharing model for activities understood (inherits from WhatId parent)

## Salesforce-Specific Gotchas

1. **Custom fields on `Activity` propagate to both Task and Event.** You cannot add a field only to Task — architect with this in mind.
2. **Activities inherit sharing from the `WhatId` parent.** No independent sharing rules.
3. **`OpenActivity` and `ActivityHistory` cannot be modified.** They are projections of Task/Event.

## Output Artifacts

| Artifact | Description |
|---|---|
| Activity model decision | Task vs Event vs custom object |
| SOQL pattern library | Polymorphic queries with TYPEOF |
| Bulk creation template | Apex trigger / batch pattern |

## Related Skills

- `apex/apex-polymorphic-soql` — polymorphic query patterns in depth
- `admin/case-management-setup` — case-related activity handling
- `integration/einstein-activity-capture-integration` — EAC data flow
