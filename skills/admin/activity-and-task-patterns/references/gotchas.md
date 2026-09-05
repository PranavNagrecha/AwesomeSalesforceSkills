# Gotchas — Activity and Task Patterns

Non-obvious Salesforce platform behaviors that cause real production
problems when working with Tasks, Events, and the Activity object model.
These are distinct from the high-level callouts in `SKILL.md` — each
gotcha here is something a practitioner won't see until the work hits
production data volume or a non-trivial user.

## Gotcha 1: ActivityHistory subqueries silently cap at 500 rows per parent

**What happens:** A subquery like
`(SELECT Id, Subject FROM ActivityHistories WHERE ActivityDate < LAST_N_YEARS:2)`
returns at most 500 rows per parent no matter how many matching
activities exist, and you cannot raise the ceiling with a larger
`LIMIT`. The truncation is silent — no system debug entry, no
row-count warning — so any total computed from the subquery is
capped at 500 on long-tenured parents.

**When it occurs:** Any subquery from a parent against
`ActivityHistories` or `OpenActivities` on accounts/opportunities
with high activity volume (>500 lifetime activities). Common
trigger: an Apex job rolling up "total activities last 12 months"
that produces wildly wrong numbers on the long-tenured customers.

**How to avoid:** For accurate counts or filtered scans on
high-volume parents, query `Task` and `Event` directly with the
`AccountId` (or `WhatId`) filter and a real `LIMIT`. Use the
subqueries only when the activity timeline UI is the consumer
and "recent 500" is acceptable.

---

## Gotcha 2: `Activity.IsClosed` and `Task.IsClosed` use different field semantics

**What happens:** Both `Task` and `Event` have an `IsClosed` field,
but they're driven by completely different rules. On `Task`,
`IsClosed` is computed from `Status` — when `Status.IsClosed = true`
(configured in Setup → Task Statuses), the platform sets
`Task.IsClosed = true`. On `Event`, `IsClosed` is computed from
`ActivityDateTime + DurationInMinutes` — an event is "closed" when
its end time is in the past, irrespective of any status. There is
no `Event.Status` controlling closure.

**When it occurs:** A report or formula that mixes Tasks and Events
using a unified "closed activity" filter. The Task side respects
the admin-configured status semantics; the Event side flips purely
on calendar time. Practitioners discover this when an admin updates
the Task Status picklist to add a new "Closed - No Action" entry,
sees Task rollups change, and then can't understand why Event
rollups didn't move.

**How to avoid:** For Task-focused work, filter on
`TaskStatus.IsClosed` (the metadata-driven field). For Event-focused
work, filter on `ActivityDateTime < NOW()` directly — don't rely on
`Event.IsClosed` if you want deterministic behavior across timezones,
because the platform evaluates it against the running user's timezone
at query time.

---

## Gotcha 3: `WhoId` accepts Contact OR Lead — but only the one matching the lookup record's RecordType

**What happens:** Setting `Task.WhoId = leadId` on a Task whose
`WhatId` already points at an Opportunity throws
`INVALID_FIELD_FOR_INSERT_UPDATE: Lead cannot be associated with
this record because the related record's type does not allow it`.
The error wording suggests a record-type issue, but the real cause
is that **Opportunities can't have Leads as their primary contact** —
once you convert a Lead, its activities are migrated to the Contact
created during conversion. Lead-pointed `WhoId` only works when
`WhatId` is null or points at an object that supports Lead
relationships (which is essentially none of the standard CRM objects
post-conversion).

**When it occurs:** Migrations that copy historical activity data
from a legacy system into Salesforce, mapping the legacy
"contact_id" field to `WhoId` without distinguishing Contact vs
Lead. Also: Apex code that assembles activities from a search
result containing both Contacts and Leads and tries to attach
them to an Opportunity in a single insert.

**How to avoid:** Validate upstream that `WhoId` is a Contact
when `WhatId` is set to an Opportunity, Account, or Case. If the
source data has Lead activities, either (a) leave `WhatId` null
and rely on `WhoId` alone, or (b) run lead conversion first and
remap to the resulting Contact. Defensive code: a single SOQL
`SELECT Id FROM Contact WHERE Id IN :whoIds` to confirm every
`WhoId` is a Contact before bulk-inserting Tasks with a non-null
`WhatId`.

---

## Gotcha 4: Einstein Activity Capture events are invisible to standard reports

**What happens:** A user with Einstein Activity Capture enabled
syncs 200 calendar events from Outlook. They appear correctly on
the Lightning record timeline. Reports built on the Events object
return zero of them. Activity Metrics shows the right counts but
can't be drilled into for individual event detail.

**When it occurs:** Any reporting / Apex query / Flow that
assumes Salesforce activity = `Task` or `Event` records. The
default architectural assumption breaks the moment EAC is turned
on for any user. The most painful version: a sales-ops dashboard
that was accurate for months silently goes stale when a single
manager enables EAC for their team.

**How to avoid:** Decide org-wide whether EAC is the source of
truth for emails/events, and if so, build reporting on the
Activity Metrics object set (`ActivityMetric`, `ActivityHistory`
via Activity Metrics) rather than `Task`/`Event` directly.
Document in the org's data dictionary that "Event" reports
exclude EAC-synced activities. For Apex automation that triggers
on activity creation, watch for the gap — EAC does NOT fire
record-triggered flows or Apex triggers on the destination Event
records.

---

## Gotcha 5: Activity field-level security is silently inherited from both Task AND Event

**What happens:** An admin adds a custom field `Outcome__c` on
Activity, then removes Read access for it on the
`Read_Only_Support` profile. The next time a support user opens a
case with related Events, they get no error — but their `Outcome__c`
on Events stays NULL even when the database has values, and they
have no way to know the field exists. The profile's FLS applies to
the *Activity* parent and projects onto both Task and Event,
but the UI doesn't distinguish them.

**When it occurs:** Any FLS tightening on Activity custom fields
combined with users who only interact with one of {Task, Event}.
The asymmetry between the two child objects' UI surfaces hides the
fact that FLS is shared.

**How to avoid:** When designing custom Activity fields, document
that FLS applies to both children. For permission-set design, treat
"Activity Outcome__c read" as a single permission, not a per-object
one. In bulk FLS-audit scripts, query the
`FieldPermissions` entity for `SobjectType = 'Activity'` (not
`'Task'` or `'Event'` — those rows don't exist for shared fields).

---

## Gotcha 6: Every Apex-created Task emails its assignee unless you turn the header off

**What happens:** A backfill class inserts 40,000 follow-up tasks
overnight. Each one triggers the "a task was assigned to you"
notification, and the org's users wake up to a mailbox full of
them. Nothing in the Apex says "send email"; the platform does it
because `Database.DMLOptions.EmailHeader.triggerUserEmail` defaults
to on. The Apex Developer Guide lists the trigger events for that
header explicitly: "resetting a password, creating a new user, or
creating or modifying a task" (apexdev.txt L8612–L8617).

**When it occurs:** Any Apex DML that creates or modifies Tasks
whose `OwnerId` is not the running user — data migrations,
scheduled hygiene jobs, trigger-created follow-ups, a Queueable
that reassigns overdue tasks. The bare `insert tasks;` DML verb
has no place to put the option, so this is invisible until it
fires. The DMLOptions settings for `emailHeader` take effect only
for DML carried out in Apex code (apexdev.txt L8621–L8622), which
is why a Data Loader run of the same rows behaves differently and
gives false confidence.

**How to avoid:** Build the option object before the write and pass
it to the `Database` method:
`dml.EmailHeader.triggerUserEmail = false;` then
`Database.insert(tasks, dml, AccessLevel.SYSTEM_MODE);` — see
`references/metadata-examples.md` section 5. Group events need the
same care: sending a group event invitation to a *user* respects
`triggerUserEmail`, sending one to a *lead or contact* respects
`triggerOtherEmail`, and updating or deleting a group event
respects both (apexdev.txt L8641–L8647).

---

## Gotcha 7: `Task.Subject`, `Status` and `Priority` cannot be custom-indexed

**What happens:** A "find every open task with subject 'Renewal
Check' " query on a multi-million-row Task table full-scans and
times out, and Salesforce Support declines to add a custom index.
The Large Data Volumes guide lists, among the standard fields with
special functionality that the platform can't index, "Activity:
Subject, TaskStatus, TaskPriority" (ldv.txt L498–L511) — the three
fields practitioners reach for first when filtering activities.

**When it occurs:** Reporting and cleanup jobs on long-tenured orgs,
where the natural filter is a subject string or an open/closed
status. It surfaces late because the query is fast in a sandbox
with 40,000 tasks and fails only past the selectivity thresholds
(a standard index is used only when the filter matches less than
30% of the first million records and less than 15% of additional
records; a custom index, less than 10% and 5%; ldv.txt
L461–L469).

**How to avoid:** Filter on something the platform *can* index —
`WhatId`, `WhoId`, `OwnerId`, `AccountId`, or a date range on
`ActivityDate` / `CreatedDate` — and treat `Subject`/`Status` as a
secondary narrowing in the same `WHERE`. If subject text is the
real access path, that is the signal to move the data to a custom
`Interaction__c` with an indexed custom field (see
`architect/large-data-volume-architecture`). UNVERIFIED
(2026-09-05): the LDV guide presents this list inside a discussion
of formula-field determinism, so its scope beyond formula fields is
inferred, not stated.

---

## Gotcha 8: You cannot enable Shared Activities by deploying metadata

**What happens:** The design calls for one task related to several
contacts, so the deploy sets
`allowUsersToRelateMultipleContactsToTasksAndEvents` to `true` in
`Activities.settings-meta.xml`. The deploy succeeds. Nothing
changes: `TaskWhoIds` still rejects a list, `TaskRelation` returns
nothing, and `WhoCount` stays null. Beginning with API v36.0 that
field is read-only in *all* versions of the API and its value
cannot be changed (api_meta.txt L109382–L109391).

**When it occurs:** Any org-setup automation, scratch-org
definition, or CI pipeline that assumes activity settings are
fully deployable because the rest of the `ActivitiesSettings` file
is. The failure is silent — a successful deploy that changed one
boolean the platform ignored — so downstream Apex written against
`TaskWhoIds` compiles and then behaves as if every task has one
contact.

**How to avoid:** Treat Shared Activities as a Setup-only,
org-lifetime decision made by a human before any of this code is
written, and assert it at runtime rather than assuming it:
`Task.TaskWhoIds` and the `TaskWhoRelations` child relationship it is linked to only
exist when it is on (object_reference.txt L278346–L278356). The
capability it unlocks is bounded too: a task can be related to one
lead **or up to 50 contacts**, plus one account, asset, campaign,
case, contract, opportunity, product, solution, or custom object
(object_reference.txt L278701–L278704).

---

## Gotcha 9: A child event accepts updates to exactly two fields

**What happens:** A bulk job that rewrites `Subject` or `WhatId`
across a date range succeeds on standalone events and fails on the
occurrences of a recurring or group series. Child events — rows
where `IsChild` is `true` — allow updates to `IsReminderSet` and
`ReminderDateTime` only; they can be queried and deleted, but not
otherwise edited (object_reference.txt L111715–L111720).

**When it occurs:** Any `List<Event>` update built from a plain
date-range query, because `IsChild` is not in the `SELECT` and
nothing in the query result hints that some rows are occurrences.
It also bites the timeline: `EventRelation` cannot be created for
a child event, and child events don't include the invitee related
list (object_reference.txt L111430, L131000).

**How to avoid:** Select `IsChild` and partition the list before
the DML — edit the series parent, delete-and-recreate occurrences,
or skip children outright. Pair that with partial-success DML so
the rows you *can* update still commit. On the Task side the
equivalent trap is recurrence: a task can never be flipped between
recurring and nonrecurring after creation, and `ActivityDate` and
`Status` are not updatable while `IsRecurrence` is true
(object_reference.txt L277937, L278319, L278482).

---

## Gotcha 10: The Task behind an EmailMessage is replaced, not updated

**What happens:** Automation stores `EmailMessage.ActivityId` to
point back at the task the platform created for an inbound case
email, then later reads that stored Id and gets
`ENTITY_IS_DELETED`. The Object Reference states the behaviour
plainly: "If an EmailMessage has a related task, and fields on the
email record are updated, we may delete the related task and create
a new related task" (object_reference.txt L104019–L104020).

**When it occurs:** Email-to-Case orgs where anything edits the
EmailMessage after arrival — a Flow stamping a custom field, an
Apex classifier writing a category, a user changing the status.
The stored Task Id was valid at capture time and is dangling after.
The same field is one-directional in another way: `ActivityId` can
only be *specified* for emails on cases; it is auto-created for
other entities (object_reference.txt L104017–L104018).

**How to avoid:** Never persist an activity Id derived from an
EmailMessage as a durable key. Re-read `EmailMessage.ActivityId`
at the moment you need it, or key off the EmailMessage itself and
navigate to the task. If a custom field must survive, put it on the
EmailMessage, not on the task the platform owns. See
`admin/email-to-case-configuration` for the intake side.
