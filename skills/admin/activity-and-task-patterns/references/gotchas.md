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
