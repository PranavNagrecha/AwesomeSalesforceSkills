# Metadata Examples — Activity and Task Patterns

Deployable shapes for the metadata this skill actually produces: the org-level
`ActivitiesSettings`, the `enableActivities` flag that decides which objects can be
a `WhatId`, the shared Task/Event custom field, the `TaskStatus` standard value set
that drives `Task.IsClosed`, and the Apex that writes activities in bulk.

Element names, enum values, and the skeletons come from the Metadata API Developer
Guide (v62 PDF, `ActivitiesSettings`, `CustomObject`, `CustomField`,
`StandardValueSet` sections) and the Object Reference (`Task`, `Event`,
`TaskRelation`, `EventRelation`). The worked examples extend the guide's own sample
definitions to a realistic org.

Lint whatever you write with:

```bash
python3 skills/admin/activity-and-task-patterns/scripts/check_activity_and_task_patterns.py \
    --manifest-dir force-app/main/default
```

## Where the files live

| Type | package.xml `<name>` / `<members>` | File in a DX project |
|---|---|---|
| Org activity settings | `Settings` / `Activities` | `settings/Activities.settings-meta.xml` |
| Activity-enable a custom object | `CustomObject` / `Interaction__c` | `objects/Interaction__c/Interaction__c.object-meta.xml` |
| Custom field shared by Task and Event | `CustomField` / `Activity.Outcome__c` | `objects/Activity/fields/Outcome__c.field-meta.xml` |
| Task status picklist | `StandardValueSet` / `TaskStatus` | `standardValueSets/TaskStatus.standardValueSet-meta.xml` |
| Task field-level security | `Profile` or `PermissionSet` | see the Task **and** Event warning below |

`ActivitiesSettings` values are stored in the `Activities.settings` file in the
`settings` directory, and there is only one settings file per settings component
(api_meta.txt L109370–L109372). All org settings metadata types are addressed in
package.xml through the `Settings` name (api_meta.txt L109366).

## 1. Org activity settings

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ActivitiesSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <!-- Task behaviour -->
    <enableActivityReminders>true</enableActivityReminders>
    <enableGroupTasks>true</enableGroupTasks>
    <enableRecurringTasks>false</enableRecurringTasks>
    <enableSimpleTaskCreateUI>true</enableSimpleTaskCreateUI>
    <enableUNSTaskDelegatedToNotifications>true</enableUNSTaskDelegatedToNotifications>
    <enableFlowTaskNotifsViaApex>false</enableFlowTaskNotifsViaApex>

    <!-- Event behaviour -->
    <enableRecurringEvents>true</enableRecurringEvents>
    <enableMultidayEvents>true</enableMultidayEvents>
    <enableHideChildEventsPreference>true</enableHideChildEventsPreference>
    <autoRelateEventAttendees>true</autoRelateEventAttendees>

    <!-- Rollup and timeline -->
    <enableRollUpActivToContactsAcct>true</enableRollUpActivToContactsAcct>
    <enableTimelineCompDateSort>true</enableTimelineCompDateSort>
    <enableEmailTracking>true</enableEmailTracking>
    <enableLogNote>true</enableLogNote>

    <!-- Calendar UI (User Interface settings page, not Activity Settings) -->
    <enableCalendarHomeLWC>true</enableCalendarHomeLWC>
    <enableClickCreateEvents>true</enableClickCreateEvents>
    <enableDragAndDropScheduling>true</enableDragAndDropScheduling>
    <enableListViewScheduling>true</enableListViewScheduling>
    <enableUserListViewCalendars>true</enableUserListViewCalendars>
    <showEventDetailsMultiUserCalendar>true</showEventDetailsMultiUserCalendar>
</ActivitiesSettings>
```

How to read it:

- **`allowUsersToRelateMultipleContactsToTasksAndEvents` is deliberately absent.**
  That element is the Shared Activities switch, and beginning with API v36.0 it is
  read-only in *all* versions of the API — you cannot change its value through the
  Metadata API, and code in older API versions that tries to set it should be
  removed (api_meta.txt L109382–L109391). Shared Activities is a Setup-only,
  one-way org change. Everything below that depends on it — `TaskWhoIds`,
  `TaskRelation`, `EventRelation` with `IsParent`, `WhatCount` / `WhoCount` — is
  therefore gated by a decision no deployment can make for you.
- `autoRelateEventAttendees` relates an event to **up to 50 contacts or one lead**
  by matching an attendee's email address (api_meta.txt L109402–L109406). It only
  does anything once Shared Activities is on.
- `enableRecurringTasks` is set `false` here on purpose: once a task is created it
  cannot be changed from recurring to nonrecurring or back (object_reference.txt
  L278482), and `ActivityDate` and `Status` can't be set or updated on a recurring
  task (object_reference.txt L277937, L278319). Turn it on only if users, not
  automation, own the series.
- `enableFlowTaskNotifsViaApex` controls whether an email is sent when Apex invokes
  Process Builder to create a task (api_meta.txt L109436–L109437). It is *not* the same
  lever as `Database.DMLOptions.EmailHeader.triggerUserEmail` in section 5 — that
  one governs Apex DML directly.
- `enableRollUpActivToContactsAcct` rolls a contact's activities up onto the
  contact's primary account and defaults to `true` (api_meta.txt L109479–L109481);
  turning it off changes what an Account timeline shows without touching a record.
- `meetingRequestsLogo` and `showCustomLogoMeetingRequests` are omitted here because
  the logo value must name a document already uploaded to the target org
  (api_meta.txt L109510–L109513) — deploy the `Document` first or the settings file
  fails.

## 2. Activity-enabling an object (deciding what can be a `WhatId`)

`WhatId` is polymorphic over "objects enabled for activities", so this one boolean
is what puts a custom object into the Related To picker, onto the activity timeline,
and into a `TYPEOF What` branch.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <deploymentStatus>Deployed</deploymentStatus>
    <enableActivities>true</enableActivities>
    <enableFeeds>false</enableFeeds>
    <enableHistory>true</enableHistory>
    <enableReports>true</enableReports>
    <label>Interaction</label>
    <pluralLabel>Interactions</pluralLabel>
    <nameField>
        <label>Interaction Name</label>
        <type>AutoNumber</type>
        <displayFormat>INT-{00000000}</displayFormat>
    </nameField>
    <sharingModel>Private</sharingModel>
</CustomObject>
```

How to read it:

- `enableActivities` is a plain boolean on `CustomObject`, and it is **not available
  for external objects** (api_meta.txt L42009–L42012). The guide's own `CustomObject`
  samples show it both ways (`false` at api_meta.txt L43163, `true` at L44751).
- The EventRelation section states the reciprocal rule from the activity side: an
  event can be related to a custom object that has the `HasActivities` attribute set
  to `true` (object_reference.txt L130978). `enableActivities` in metadata is what
  sets that describe attribute. UNVERIFIED (2026-09-05): the guides name the
  metadata field and the describe attribute separately; neither states in one place
  that the former sets the latter — the mapping is inferred from the two sections.
- `sharingModel` is `Private` here because the whole point of a custom
  `Interaction__c` is an activity-like record with its **own** sharing. Tasks and
  Events do not get one; see `references/well-architected.md`.
- Turning `enableActivities` **off** on an object that already has activities is the
  risky direction — the timeline and the `WhatId` values behind it are what change.
  Retrieve and diff before you deploy an object file that flips this bit; the flag
  travels silently inside a whole-object retrieve.

## 3. A custom field on Activity (it lands on Task *and* Event)

There is no such thing as a Task-only custom field. Author it under `Activity` and
expect it on both children.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Outcome__c</fullName>
    <label>Outcome</label>
    <type>Picklist</type>
    <required>false</required>
    <trackHistory>false</trackHistory>
    <valueSet>
        <restricted>true</restricted>
        <valueSetDefinition>
            <sorted>false</sorted>
            <value>
                <fullName>Connected</fullName>
                <default>false</default>
                <label>Connected</label>
            </value>
            <value>
                <fullName>Left Voicemail</fullName>
                <default>false</default>
                <label>Left Voicemail</label>
            </value>
            <value>
                <fullName>No Answer</fullName>
                <default>false</default>
                <label>No Answer</label>
            </value>
            <value>
                <fullName>Rescheduled</fullName>
                <default>false</default>
                <label>Rescheduled</label>
            </value>
        </valueSetDefinition>
    </valueSet>
</CustomField>
```

How to read it:

- `valueSet` has either a `valueSetDefinition` or a `valueName`, **never both**
  (api_meta.txt L43704–L43711); `restricted` limits values to those the admin
  defined, and `valueSetDefinition` carries `sorted` plus the `value` list
  (api_meta.txt L45839–L45870).
- "Rescheduled" is meaningless on a Task and "Left Voicemail" is meaningless on an
  Event, and you get both on both. Constrain per-child with a validation rule on
  `IsTask` / the child object, not by trying to scope the field.
- **The FLS half of this deploy is the part that bites.** Metadata deployments for
  the Task object should always include the field-level security for the Event
  object, because the two share FLS: if it is enabled for one it is enabled for
  both, if disabled for one it is disabled for both, and *a missing entry in the
  metadata is treated as field-level security being disabled*
  (object_reference.txt L278589–L278598). So a `Profile` or `PermissionSet` file
  that lists `Activity.Outcome__c` for Task but omits Event can silently strip
  access on the object you didn't mention.

```xml
<!-- Both entries, always. Omitting one is not "leave it alone"; it is "disable it". -->
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <fieldPermissions>
        <field>Task.Outcome__c</field>
        <editable>true</editable>
        <readable>true</readable>
    </fieldPermissions>
    <fieldPermissions>
        <field>Event.Outcome__c</field>
        <editable>true</editable>
        <readable>true</readable>
    </fieldPermissions>
    <label>Activity Outcome Capture</label>
</PermissionSet>
```

## 4. Task statuses — the metadata behind `Task.IsClosed`

`Task.IsClosed` is read-only and "is only set indirectly via the `Status` picklist"
(object_reference.txt L278059–L278063). `Status` values live in the `TaskStatus`
standard value set (api_meta.txt L143095), and the `closed` flag on each value is
what the platform reads.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<StandardValueSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <sorted>false</sorted>
    <standardValue>
        <fullName>Not Started</fullName>
        <default>true</default>
        <label>Not Started</label>
        <closed>false</closed>
    </standardValue>
    <standardValue>
        <fullName>In Progress</fullName>
        <default>false</default>
        <label>In Progress</label>
        <closed>false</closed>
    </standardValue>
    <standardValue>
        <fullName>Waiting on someone else</fullName>
        <default>false</default>
        <label>Waiting on someone else</label>
        <closed>false</closed>
    </standardValue>
    <standardValue>
        <fullName>Completed</fullName>
        <default>false</default>
        <label>Completed</label>
        <closed>true</closed>
    </standardValue>
    <standardValue>
        <fullName>Closed - No Action</fullName>
        <default>false</default>
        <label>Closed - No Action</label>
        <closed>true</closed>
    </standardValue>
</StandardValueSet>
```

How to read it:

- `closed` "indicates whether this value is associated with a closed status" and is
  "only relevant for the standard `Status` field in cases and tasks" (api_meta.txt
  L47542–L47547). The guide adds that the field is available in API version 16.0 up
  to 36.0, and in 37.0 it moved to `GlobalPicklistValue`; retrieved
  `TaskStatus.standardValueSet-meta.xml` files still carry `<closed>` in practice.
  UNVERIFIED (2026-09-05): the guide's version note and the observed retrieval shape
  disagree — retrieve the value set from your own org before hand-writing it.
- A deployed StandardValueSet must contain at least one picklist value or the deploy
  errors (api_meta.txt L130769–L130775), and this type does **not** support the `*`
  wildcard in package.xml (api_meta.txt L130826–L130828).
- Adding `Closed - No Action` with `closed=true` changes `Task.IsClosed` for every
  future task saved with it — and changes nothing about `Event`, which has no
  `Status` at all. `CompletedDateTime` follows the same picklist: it is set when the
  task is saved with a Closed status, reset to NULL on a new non-closed status, and
  unchanged when the status is re-saved as the same closed value. "The status is a
  dynamic enum. If the Closed mapping is changed it won't cause an update of
  existing tasks. Only new insert/update operations are affected."
  (object_reference.txt L277994–L278015).
- The sibling flag on `TaskPriority` is `highPriority`, which drives the derived
  `Task.IsHighPriority` field (api_meta.txt L47588–L47592; object_reference.txt
  L278066–L278071).

## 5. Bulk-safe Apex: polymorphic read, partial-success write, no mail storm

```apex
public with sharing class ProposalFollowupTaskService {

    private static final String PROPOSAL_STAGE = 'Proposal/Price Quote';

    /**
     * Reads the related-to parent polymorphically and writes follow-up tasks with
     * partial success, so one bad row cannot roll back a 200-record save.
     */
    public static List<Database.SaveResult> createFollowups(
        List<Opportunity> newOpps,
        Map<Id, Opportunity> oldMap
    ) {
        List<Task> toInsert = new List<Task>();

        for (Opportunity opp : newOpps) {
            Opportunity prior = (oldMap == null) ? null : oldMap.get(opp.Id);
            Boolean enteredProposal =
                opp.StageName == PROPOSAL_STAGE
                && (prior == null || prior.StageName != PROPOSAL_STAGE);
            if (!enteredProposal) {
                continue;
            }
            toInsert.add(new Task(
                WhatId       = opp.Id,          // polymorphic: Opportunity here
                OwnerId      = opp.OwnerId,
                Subject      = 'Follow up on proposal',
                Status       = 'Not Started',   // drives IsClosed via TaskStatus
                Priority     = 'High',          // drives IsHighPriority via TaskPriority
                TaskSubtype  = 'Task',          // set on create only; can't be updated
                ActivityDate = Date.today().addDays(5)
            ));
        }

        if (toInsert.isEmpty()) {
            return new List<Database.SaveResult>();
        }

        Database.DMLOptions dml = new Database.DMLOptions();
        dml.optAllOrNone = false;                  // partial success
        dml.EmailHeader.triggerUserEmail = false;  // no "a task was assigned to you" mail

        List<Database.SaveResult> results =
            Database.insert(toInsert, dml, AccessLevel.SYSTEM_MODE);

        for (Integer i = 0; i < results.size(); i++) {
            if (!results[i].isSuccess()) {
                for (Database.Error err : results[i].getErrors()) {
                    System.debug(LoggingLevel.ERROR,
                        'Task failed for WhatId ' + toInsert[i].WhatId + ': '
                        + err.getStatusCode() + ' ' + err.getMessage()
                        + ' fields=' + err.getFields());
                }
            }
        }
        return results;
    }
}
```

How to read it:

- One `Database.insert` for the whole batch. `optAllOrNone = false` means "if a
  record fails, the remainder of the DML operation can still succeed" and you must
  iterate the results to see which rows landed (apexrefguide.txt L148100–L148104;
  apexdev.txt L7566–L7586). With the bare `insert` DML verb one bad `WhoId` throws
  and takes all 200 opportunities down with it.
- `EmailHeader.triggerUserEmail` "indicates whether to trigger email that is sent to
  users in the organization", and the guide lists **creating or modifying a task**
  among the events that trigger it (apexdev.txt L8612–L8617). Leave it at its
  default and a 5,000-row backfill sends 5,000 assignment emails. The setting takes
  effect only for DML carried out in Apex code (apexdev.txt L8621–L8622).
- The three-argument form is
  `insert(List<SObject> recordsToInsert, Database.DMLOptions dmlOptions,
  System.AccessLevel accessLevel)`; **user mode is the default** when `accessLevel`
  is omitted (apexrefguide.txt L207936–L207953). Pass it explicitly so the mode is a
  decision, not an accident — `SYSTEM_MODE` here because the trigger owner, not the
  saving user, must be able to write the task.
- `TaskSubtype` is `Create, Filter, Group, Nillable, Restricted picklist, Sort` — no
  `Update` — so it is settable on insert and immutable afterwards; its values are
  `Task`, `Email`, `LinkedIn`, `ListEmail`, `Cadence`, `Call`, and `Cadence` is an
  internal Sales Engagement value that can't be set manually (object_reference.txt
  L278328–L278344).

Reading a polymorphic parent needs `TYPEOF` or a `What.Type` filter. Both forms are
in the Apex Developer Guide (apexdev.txt L9770–L9787):

```apex
// Filter form — cheapest when you only need to narrow the rows
List<Event> events = [
    SELECT Id, Subject, DurationInMinutes
      FROM Event
     WHERE What.Type IN ('Account', 'Opportunity')
];

// Projection form — the only way to read parent fields beyond Id and Type
List<Task> tasks = [
    SELECT Id, Subject, Status, IsClosed,
           TYPEOF What
             WHEN Account     THEN Name, Industry
             WHEN Opportunity THEN Amount, StageName
             ELSE Id
           END
      FROM Task
     WHERE IsClosed = false
     LIMIT 200
];

// Runtime narrowing, for when the branch matters in code rather than in the query
for (Task t : tasks) {
    if (t.What instanceof Opportunity) {
        Opportunity o = (Opportunity) t.What;
        System.debug(o.Amount);
    }
}
```

## package.xml and CLI

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Activities</members>
        <name>Settings</name>
    </types>
    <types>
        <members>Activity.Outcome__c</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>TaskStatus</members>
        <members>TaskPriority</members>
        <name>StandardValueSet</name>
    </types>
    <types>
        <members>Interaction__c</members>
        <name>CustomObject</name>
    </types>
    <version>62.0</version>
</Package>
```

The guide's own manifest sample for activity settings is exactly the `Settings` /
`Activities` pair above (api_meta.txt L109545–L109552); it shows `<version>28.0</version>`
because `ActivitiesSettings` is available in API 28.0 and later — use your project's
sourceApiVersion instead. The `*` wildcard in package.xml **does not apply to feature
settings metadata types**; it applies only when retrieving all settings, never an
individual one (api_meta.txt L109589–L109592). `StandardValueSet` does not support
the wildcard either (api_meta.txt L130826–L130828).

```bash
# 1. Pull the org's current state before editing anything
sf project retrieve start \
   --metadata "Settings:Activities" "StandardValueSet:TaskStatus" "CustomField:Activity.Outcome__c" \
   --target-org my-sandbox

# 2. Lint the working tree
python3 skills/admin/activity-and-task-patterns/scripts/check_activity_and_task_patterns.py \
   --manifest-dir force-app/main/default

# 3. Validate without deploying
sf project deploy validate --manifest manifest/package.xml --target-org my-sandbox

# 4. Deploy the object/field/value-set first, the Profile/PermissionSet FLS second
sf project deploy start --manifest manifest/package.xml --target-org my-sandbox
```

## Verification after deploy

Settings and describe-level flags do not show up in a record query, so verify each
layer separately.

```bash
# Did enableActivities actually take on the custom object? WhatId only accepts
# activity-enabled objects, so a successful Task insert IS the proof.
sf data create record --sobject Task \
   --values "Subject='Deploy smoke test' Status='Not Started' Priority='Normal' WhatId=<an Interaction__c Id>" \
   --target-org my-sandbox

# Did the TaskStatus change land? IsClosed is derived, never written directly.
sf data query --target-org my-sandbox \
   --query "SELECT Status, IsClosed, CompletedDateTime FROM Task WHERE Subject = 'Deploy smoke test'"

# Is the shared field readable on BOTH children? Two rows expected, not one.
sf data query --target-org my-sandbox --use-tooling-api \
   --query "SELECT Field, PermissionsRead, PermissionsEdit, Parent.Label FROM FieldPermissions WHERE Field IN ('Task.Outcome__c','Event.Outcome__c')"
```

Then check Setup → Activity Settings and Setup → User Interface by eye: the
`ActivitiesSettings` fields are split across those two pages, and the guide's field
table says which lever lives where (api_meta.txt L109379–L109532). If
`allowUsersToRelateMultipleContactsToTasksAndEvents` is what you needed, no deploy
will have moved it — see section 1.

## Related reading

- `references/gotchas.md` — the platform behaviours these files trip over
- `references/examples.md` — two worked scenarios end to end
- `apex/apex-dml-patterns` — `Database.DMLOptions` beyond the email header
- `admin/picklist-and-value-sets` — standard vs global value sets in general
