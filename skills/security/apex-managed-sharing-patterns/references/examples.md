# Examples — Apex Managed Sharing Patterns

Apex managed sharing is the narrowest of the sharing mechanisms and the easiest
to get subtly wrong. Every example below is grounded in the *Understanding Apex
Managed Sharing* chapter of the Apex Developer Guide (Summer '26, API 67.0).

Read the platform constraint first, because it eliminates roughly half of the
designs people arrive with:

> "Apex sharing reasons and Apex managed sharing recalculation are only available
> for custom objects."
> — Apex Developer Guide, *Understanding Sharing*

That single sentence means there is no such thing as Apex *managed* sharing on
Opportunity, Account, Case, or Contact. You can still write rows into
`OpportunityShare` from Apex, but those rows are **user managed (manual) shares**
with `RowCause = 'Manual'`, and the platform deletes them when the record owner
changes. Examples 1 and 2 show both halves of that split.

---

## Example 1: Share a custom object with the users named on it (real Apex managed sharing)

**Context:** A recruiting app has a `Job__c` custom object with two User lookups,
`Recruiter__c` and `Hiring_Manager__c`. Org-wide default for `Job__c` is Private.
The recruiter needs Edit; the hiring manager needs Read. Access must survive an
owner change, because jobs are reassigned between regional owners every quarter.

**Problem:** A criteria-based sharing rule can't help — sharing rules grant access
to a *group* based on the record's field values, not to the specific user whose Id
sits in a lookup on that record. Manual sharing would work for a day and then
evaporate: manual shares are removed when the record owner changes.

**Solution — step 1, create the Apex sharing reasons.**

Apex sharing reasons live on the custom object, not in a permission set:

```text
Setup → Object Manager → Job → Apex Sharing Reasons → New
    Label: Recruiter          Name: Recruiter
    Label: Hiring Manager     Name: Hiring_Manager
```

Two constraints on that screen that cost people an afternoon:

- The **Apex Sharing Reasons related list is not rendered in Lightning
  Experience.** The Apex Developer Guide is explicit: "Apex sharing reasons aren't
  available in Lightning Experience. Use Salesforce Classic to create sharing
  reasons within the UI." Switch to Classic, or deploy a `SharingReason` component
  through the Metadata API.
- The **Name** can contain only underscores and alphanumerics, must be unique in
  the org, must begin with a letter, must not end with an underscore, and must not
  contain two consecutive underscores.

The equivalent Metadata API source, which is what you actually want in version
control:

```xml
<!-- force-app/main/default/objects/Job__c/sharingReasons/Recruiter.sharingReason-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<SharingReason xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Recruiter</label>
</SharingReason>
```

**Solution — step 2, the trigger.** This is the Apex Developer Guide's own sample,
adapted into a handler and kept bulk-safe:

```apex
public with sharing class JobShareService {

    // Reason names resolve at compile time. If the sharing reason has not been
    // deployed, this class will not save — which is the failure mode you want.
    private static final String REASON_RECRUITER =
        Schema.Job__Share.RowCause.Recruiter__c;
    private static final String REASON_HIRING_MGR =
        Schema.Job__Share.RowCause.Hiring_Manager__c;

    /**
     * The entry point. Grant and revoke are ONE operation, not two optional
     * halves: revoke first (scoped to this application's own RowCause values),
     * then re-grant from the current field values. That single ordering makes
     * the method idempotent, handles re-assignment (A -> B) in one transaction,
     * and revokes when a lookup is cleared. Calling `grantForJobs` alone leaves
     * the previous user's share row in place forever.
     */
    public static void reconcileForJobs(List<Job__c> jobs) {
        revokeForJobs(new Map<Id, Job__c>(jobs).keySet());
        grantForJobs(jobs);
    }

    /**
     * Delete only the rows this application owns. The RowCause filter is what
     * stops this from destroying Owner, Rule, Team, or end-user Manual shares.
     */
    public static void revokeForJobs(Set<Id> jobIds) {
        if (jobIds == null || jobIds.isEmpty()) {
            return;
        }
        delete as system [
            SELECT Id
            FROM Job__Share
            WHERE ParentId IN :jobIds
              AND RowCause IN (:REASON_RECRUITER, :REASON_HIRING_MGR)
        ];
    }

    public static void grantForJobs(List<Job__c> jobs) {
        List<Job__Share> shares = new List<Job__Share>();

        for (Job__c job : jobs) {
            if (job.Recruiter__c != null) {
                shares.add(new Job__Share(
                    ParentId      = job.Id,
                    UserOrGroupId = job.Recruiter__c,
                    AccessLevel   = 'Edit',
                    RowCause      = REASON_RECRUITER
                ));
            }
            if (job.Hiring_Manager__c != null) {
                shares.add(new Job__Share(
                    ParentId      = job.Id,
                    UserOrGroupId = job.Hiring_Manager__c,
                    AccessLevel   = 'Read',
                    RowCause      = REASON_HIRING_MGR
                ));
            }
        }
        if (shares.isEmpty()) {
            return;
        }

        // allOrNone = false: one bad row must not roll back the whole insert.
        List<Database.SaveResult> results =
            Database.insert(shares, false, AccessLevel.SYSTEM_MODE);

        for (Integer i = 0; i < results.size(); i++) {
            Database.SaveResult sr = results[i];
            if (sr.isSuccess()) {
                continue;
            }
            Database.Error err = sr.getErrors()[0];

            // Expected and harmless: the requested AccessLevel is not more
            // permissive than the object's org-wide default, so the row is
            // redundant and the platform rejects it.
            Boolean trivialAccess =
                err.getStatusCode() == StatusCode.FIELD_FILTER_VALIDATION_EXCEPTION
                && err.getMessage().contains('AccessLevel');

            if (!trivialAccess) {
                ApplicationLogger.error('JobShareService', err.getMessage());
            }
        }
    }
}
```

```apex
trigger JobTrigger on Job__c (after insert, after update) {
    if (Trigger.isAfter && (Trigger.isInsert || Trigger.isUpdate)) {
        // reconcile, NOT grant. A grant-only trigger passes every positive
        // test and never removes access when a lookup changes or is cleared.
        JobShareService.reconcileForJobs(Trigger.new);
    }
}
```

**Why it works:**

- The insert runs in an `after` context, so `job.Id` is populated. `ParentId` is
  not updateable, so a `before insert` handler has nothing to point at.
- `reconcileForJobs` revokes before it grants. Without the revoke half, changing
  `Recruiter__c` from user A to user B leaves A's `Job__Share` row untouched — A
  keeps Edit access permanently — and re-running the grant on an unchanged record
  attempts a duplicate row, so every subsequent save logs an error. The revoke is
  scoped by `RowCause`, so it never touches Owner, Rule, Team, or Manual shares.
- `AccessLevel.SYSTEM_MODE` is used because the docs state "Only users with
  'Modify All Data' permission can add or change Apex managed sharing on a
  record." Ordinary end users do not have that permission; running the DML in
  system mode is the mechanism that lets a recruiter-assignment save succeed for
  a normal sales user. (The Apex Developer Guide's own snippet uses
  `AccessLevel.USER_MODE`, which is correct only when the running user actually
  holds Modify All Data — see Gotcha 4 in `gotchas.md`.)
- Because the `RowCause` is an Apex sharing reason, "Apex managed sharing is
  maintained when the record owner changes or is deactivated." That is the whole
  reason for the ceremony.

---

## Example 2: The same requirement on a *standard* object — and why the usual answer is wrong

**Context:** Deal desk wants every user listed on a `Deal_Team_Member__c` junction
to see the parent Opportunity. OWD on Opportunity is Private.

### WRONG — this does not compile, and the design is not available

```apex
// DOES NOT COMPILE.
// Schema.OpportunityShare.RowCause has no member Deal_Team__c, because Apex
// sharing reasons cannot be created on standard objects at all.
public with sharing class DealTeamShareService {
    public static void grant(Id opptyId, Id userOrGroupId) {
        OpportunityShare s = new OpportunityShare(
            OpportunityId          = opptyId,
            UserOrGroupId          = userOrGroupId,
            OpportunityAccessLevel = 'Read',
            RowCause = Schema.OpportunityShare.RowCause.Deal_Team__c   // <-- invalid
        );
        Database.insert(s, false);
    }
}
```

This is the single most common LLM-generated Salesforce sharing bug. It reads
correctly, matches the pattern from every Apex-managed-sharing blog post, and
fails at save time with a compile error on the `RowCause` member.

### RIGHT — option A: use the built-in Opportunity Team

Opportunity Team membership writes `OpportunityShare` rows with
`RowCause = 'Team'`, which the platform maintains. If the requirement is
"named users on the deal can see it," `OpportunityTeamMember` is the answer and
no Apex is needed:

```apex
public with sharing class DealTeamService {
    public static void syncTeam(List<Deal_Team_Member__c> members) {
        List<OpportunityTeamMember> team = new List<OpportunityTeamMember>();
        for (Deal_Team_Member__c m : members) {
            team.add(new OpportunityTeamMember(
                OpportunityId       = m.Opportunity__c,
                UserId              = m.User__c,
                TeamMemberRole      = m.Role__c,
                OpportunityAccessLevel = 'Read'
            ));
        }
        insert as system team;
    }
}
```

### RIGHT — option B: a manual share, with eyes open about the lifecycle

If the access level or the population can't be expressed with a team, you can
still write an `OpportunityShare` row from Apex. It will be a manual share:

```apex
public with sharing class DealTeamShareService {

    public static void grant(List<Deal_Team_Member__c> members) {
        List<OpportunityShare> shares = new List<OpportunityShare>();
        for (Deal_Team_Member__c m : members) {
            shares.add(new OpportunityShare(
                OpportunityId          = m.Opportunity__c,
                UserOrGroupId          = m.User__c,
                OpportunityAccessLevel = 'Read'
                // RowCause omitted: 'Manual' is the default for share objects.
            ));
        }
        Database.insert(shares, false, AccessLevel.SYSTEM_MODE);
    }

    /**
     * Manual shares are removed when the Opportunity owner changes. Re-grant
     * from the junction after an owner transfer, or access silently disappears.
     */
    public static void reconcileAfterOwnerChange(Set<Id> opportunityIds) {
        grant([SELECT Opportunity__c, User__c
               FROM Deal_Team_Member__c
               WHERE Opportunity__c IN :opportunityIds]);
    }
}
```

**Why the distinction matters:** the Apex Developer Guide states that manual
shares written from Apex "contain `RowCause="Manual"` by default. Only shares
with this condition are removed when ownership changes." An owner transfer
therefore silently revokes every row this class wrote — which is exactly the
behaviour Apex managed sharing exists to avoid, and exactly why it is
custom-object-only.

---

## Example 3: The recalculation class the platform runs for you

**Context:** `Job__c` shares were written by a trigger. During a bulk load, a
record-locking error caused some `Job__Share` inserts to fail. Access is now
inconsistent with the lookups on the record.

**Problem:** There is no way to "re-run the trigger" over existing records without
touching every row. And when an admin later changes the `Job__c` org-wide default,
the platform wipes and rebuilds sharing — anything the trigger inserted is gone
unless something rebuilds it.

**Solution:** register a `Database.Batchable` recalculation class against the
object. The platform then calls it automatically:

> "Every time a custom object's organization-wide sharing default access level is
> updated, any Apex recalculation classes defined for associated custom object are
> also executed."
> — Apex Developer Guide, *Recalculating Apex Managed Sharing*

and, more broadly, from the Salesforce Security Guide:

> "When sharing is recalculated, Salesforce also runs all Apex sharing
> recalculations."

```apex
global with sharing class JobShareRecalculation implements Database.Batchable<sObject> {

    global Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator(
            'SELECT Id, Recruiter__c, Hiring_Manager__c FROM Job__c'
        );
    }

    global void execute(Database.BatchableContext bc, List<Job__c> scope) {
        Set<Id> jobIds = new Map<Id, Job__c>(scope).keySet();

        // Delete only the rows this application owns. Filtering on RowCause is
        // what stops the batch from destroying Owner, Rule, or Manual shares.
        delete as system [
            SELECT Id
            FROM Job__Share
            WHERE ParentId IN :jobIds
              AND RowCause IN (:Schema.Job__Share.RowCause.Recruiter__c,
                               :Schema.Job__Share.RowCause.Hiring_Manager__c)
        ];

        JobShareService.grantForJobs(scope);
    }

    global void finish(Database.BatchableContext bc) {
        AsyncApexJob job = [SELECT Status, NumberOfErrors, JobItemsProcessed
                            FROM AsyncApexJob WHERE Id = :bc.getJobId()];
        ApplicationLogger.info('JobShareRecalculation',
            'Status=' + job.Status + ' errors=' + job.NumberOfErrors);
    }
}
```

Register it:

```text
Setup → Object Manager → Job → Apex Sharing Recalculation → New
    Apex Class: JobShareRecalculation
```

(Also Classic-only, and the class must implement `Database.Batchable`. You cannot
associate the same Apex class more than once with the same custom object.)

Run it on demand with `Database.executeBatch(new JobShareRecalculation(), 200);`
and monitor under **Setup → Apex Jobs**.

**Why it works:** the delete is scoped by `RowCause`, so it is idempotent and
non-destructive; the platform-triggered execution closes the gap between "an admin
changed the OWD" and "application-defined access is correct again."

---

## Example 4: A test that actually proves access, not just row count

Counting `__Share` rows proves nothing — the row can exist and still not grant
visibility if the access level is not more permissive than the OWD. Assert on
what a real user can query.

```apex
@IsTest
private class JobShareServiceTest {

    @IsTest
    static void recruiterSeesJobAndLosesItWhenUnassigned() {
        User recruiter = TestUserFactory.createUser('Standard User', null);
        User owner     = TestUserFactory.createUser('Standard User', null);

        Job__c job;
        System.runAs(owner) {
            job = new Job__c(Name = 'Staff Engineer', Recruiter__c = recruiter.Id);
            insert job;
        }

        // Positive: the recruiter can see the record.
        System.runAs(recruiter) {
            Assert.areEqual(1,
                [SELECT COUNT() FROM Job__c WHERE Id = :job.Id],
                'Recruiter should see the job through the Apex managed share');
        }

        // The share carries the application's own RowCause, not Manual.
        Job__Share share = [SELECT AccessLevel, RowCause
                            FROM Job__Share
                            WHERE ParentId = :job.Id
                              AND UserOrGroupId = :recruiter.Id];
        Assert.areEqual('Edit', share.AccessLevel);
        Assert.areEqual(Schema.Job__Share.RowCause.Recruiter__c, share.RowCause);

        // Negative: unassigning must revoke. A grant-only implementation passes
        // every positive test and still leaks access forever.
        System.runAs(owner) {
            job.Recruiter__c = null;
            update job;
        }
        System.runAs(recruiter) {
            Assert.areEqual(0,
                [SELECT COUNT() FROM Job__c WHERE Id = :job.Id],
                'Access must be revoked when the recruiter lookup is cleared');
        }
    }
}
```

`TestUserFactory` is the shared factory at
[`templates/apex/tests/TestUserFactory.cls`](../../../../templates/apex/tests/TestUserFactory.cls).

**Why it works:** `System.runAs` re-evaluates record-level access, so a `COUNT()`
inside the block is a direct assertion about sharing. The negative half is the
half that finds real bugs — the revoke path is the one people forget, and it is
the one that turns into a compliance finding.

---

## Anti-Pattern: writing `__Share` rows from a `before insert` trigger

**What practitioners do:** put the share logic in `before insert` "to save a DML
statement."

**What goes wrong:** in `before insert` the record has no Id yet, so `ParentId` is
null and the insert fails with `REQUIRED_FIELD_MISSING`. If the developer works
around it by moving to `before update`, they now write shares for a record whose
transaction can still roll back, leaving the `__Share` table and the record out of
sync. `ParentId` and `RowCause` are both documented as not updateable, so there is
no repair path other than delete-and-reinsert.

**Correct approach:** always `after insert` / `after update`. If the volume is
large enough that the DML matters, move the work to a Queueable keyed on record
Ids rather than moving it earlier in the trigger order.
