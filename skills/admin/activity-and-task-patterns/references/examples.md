# Examples — Activity and Task Patterns

Two worked scenarios and one anti-pattern showing the shape this skill
produces. Each example assumes the practitioner has already decided to use
the standard Task/Event model (see `Decision Guidance` in SKILL.md for the
volume threshold that pushes to a custom `Interaction__c` instead).

---

## Example 1: Polymorphic timeline query for a custom related-list LWC

**Context:** A custom Account record page LWC needs to render the next
3 open tasks alongside the most recent closed event, with the related
record's `Name` displayed when the activity is on an Opportunity or Case
and the contact's full name when it's on a Contact.

**Problem:** A naive `SELECT What.Name FROM Task` compiles but returns
NULL for any `WhatId` that points at a polymorphic relationship the
practitioner didn't explicitly enumerate. Worse, querying `Activity`
directly fails compilation entirely — Activity is abstract.

**Solution:**

```apex
List<Task> openTasks = [
    SELECT Id, Subject, ActivityDate, WhoId, WhatId,
           TYPEOF What
             WHEN Account     THEN Name
             WHEN Opportunity THEN Name, StageName, Amount
             WHEN Case        THEN CaseNumber, Subject
             ELSE Id, Name
           END,
           TYPEOF Who
             WHEN Contact THEN FirstName, LastName, Email
             WHEN Lead    THEN FirstName, LastName, Company
           END
      FROM Task
     WHERE AccountId = :recordId
       AND IsClosed = false
     ORDER BY ActivityDate ASC
     LIMIT 3
];

List<Event> recentEvents = [
    SELECT Id, Subject, ActivityDateTime, DurationInMinutes,
           TYPEOF What
             WHEN Account     THEN Name
             WHEN Opportunity THEN Name, StageName
           END
      FROM Event
     WHERE AccountId = :recordId
       AND ActivityDateTime < :Datetime.now()
     ORDER BY ActivityDateTime DESC
     LIMIT 1
];
```

**Why it works:** `TYPEOF` is the only way to project polymorphic
parent fields beyond `Id` and `Type`. The `ELSE Id, Name` branch
catches every other object type that may be activity-enabled (e.g.,
custom objects with `Enable Activities = true`) so the LWC doesn't
explode when a user logs a task against an object the developer
forgot about. The `AccountId` filter on `Event` works because both
Task and Event maintain a denormalized `AccountId` that Salesforce
populates from the `WhatId` parent's account at insert.

---

## Example 2: Bulk task generation from a record-triggered context

**Context:** When an Opportunity moves to `Stage = 'Proposal/Price Quote'`,
a follow-up task should be created for the opportunity owner with a due
date 5 business days out. The trigger fires on bulk loads of up to
200 records.

**Problem:** Practitioners write loop-DML (`insert task` inside the
`for` loop), which fails the platform's 150-DML governor limit on
the second batch of 75 records and bricks the entire transaction.
The fix is bulk DML — but the practitioner must also handle the
case where `Stage` is being updated AND the OldMap shows it was
already at `Proposal/Price Quote` (a re-save), so duplicates aren't
inserted.

**Solution:**

```apex
public with sharing class OpportunityStageFollowupHandler {
    public static void createProposalFollowupTasks(
        List<Opportunity> newOpps,
        Map<Id, Opportunity> oldMap
    ) {
        List<Task> tasksToInsert = new List<Task>();
        for (Opportunity opp : newOpps) {
            Opportunity prior = oldMap?.get(opp.Id);
            Boolean isFreshlyInProposal =
                opp.StageName == 'Proposal/Price Quote'
                && (prior == null || prior.StageName != 'Proposal/Price Quote');
            if (!isFreshlyInProposal) continue;

            tasksToInsert.add(new Task(
                WhatId        = opp.Id,
                OwnerId       = opp.OwnerId,
                Subject       = 'Follow up on proposal',
                ActivityDate  = BusinessHours.add(
                                    BusinessHours.getDefaultBusinessHoursId(),
                                    Datetime.now(),
                                    5 * 24L * 60 * 60 * 1000
                                ).date(),
                Priority      = 'High',
                Status        = 'Not Started'
            ));
        }
        if (!tasksToInsert.isEmpty()) {
            insert tasksToInsert;
        }
    }
}
```

**Why it works:** Single `insert` call regardless of batch size keeps
the trigger inside the 150-DML envelope. The `isFreshlyInProposal`
gate prevents duplicates when a user re-saves an opportunity that
was already in the target stage. `BusinessHours.add` respects the
org's working calendar instead of naive `Date.today().addDays(5)`,
which would land on a Saturday roughly 2/7 of the time.

---

## Anti-Pattern: Querying ActivityHistory or OpenActivity outside a subquery

**What practitioners do:** Run a top-level SOQL like
`SELECT Id, Subject FROM ActivityHistory WHERE AccountId = :acctId`
expecting it to behave like Task.

**What goes wrong:** Compilation fails. `ActivityHistory` and
`OpenActivity` are *projection* objects — they exist only as
subqueries from an activity-enabled parent. They have no
queryable surface of their own, no DML, and no API endpoints.
Practitioners who hit this often pivot to "well, I'll query
Task and Event separately and union them" — which works but
forces them to deduplicate against the timeline the platform
already projects for free.

**Correct approach:**

```apex
List<Account> accts = [
    SELECT Id, Name,
           (SELECT Id, Subject, ActivityDate, Status
              FROM OpenActivities
             ORDER BY ActivityDate ASC LIMIT 5),
           (SELECT Id, Subject, ActivityDate, Status
              FROM ActivityHistories
             ORDER BY ActivityDate DESC LIMIT 5)
      FROM Account
     WHERE Id = :acctId
];
```

The relationship names are `OpenActivities` and `ActivityHistories`
(plural, capital `A`), and the platform handles Task/Event union
plus the open-vs-closed split internally. If you need to *modify*
one of these records, look up the underlying Task or Event by
`Id` and DML it directly — `ActivityHistory` and `OpenActivity`
are read-only.
