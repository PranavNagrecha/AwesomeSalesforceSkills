# Examples — FLS in Async Contexts

## Example 1: Queueable that asserts originating user

**Context:** A Lightning component lets sales reps trigger a re-sync of high-value accounts. The work is enqueued as a Queueable so the controller returns immediately.

**Problem:** The Queueable does `[SELECT ... WITH USER_MODE]` and trusts that "Queueable runs as the enqueuing user." It does, today. Six months later, someone refactors the entry point to publish a Platform Event instead, and the same Queueable is enqueued from the PE handler — which runs as the Automated Process user. `WITH USER_MODE` now returns every field. No test catches it.

**Solution:**

```apex
public class HighValueAccountSyncQueueable implements Queueable {
    private final Id originatingUserId;
    private final Set<Id> accountIds;

    public HighValueAccountSyncQueueable(Set<Id> accountIds) {
        this.accountIds = accountIds;
        this.originatingUserId = UserInfo.getUserId();
    }

    public void execute(QueueableContext qc) {
        if (UserInfo.getUserId() != originatingUserId) {
            throw new SecurityException(
                'FLS context drift: enqueued as ' + originatingUserId
                + ' but executing as ' + UserInfo.getUserId()
                + '. WITH USER_MODE would evaluate against the wrong identity.'
            );
        }
        for (Account a : [
            SELECT Id, Name, AnnualRevenue, SSN__c
            FROM Account
            WHERE Id IN :accountIds
            WITH USER_MODE
        ]) {
            // safe to act
        }
    }
}
```

**Why it works:** The assertion is cheap (one ID comparison) and turns silent drift into a loud `SecurityException`. The PE-handler refactor still compiles, but throws on first execution and is caught immediately.

---

## Example 2: Scheduled Apex that re-applies a target user's FLS

**Context:** A nightly job exports a CSV of customer records to a finance system. The job runs as a sysadmin (the user who scheduled it). Compliance requires the export honor a specific service account's FLS — that account has no access to PII columns, and the export must respect that.

**Problem:** `WITH USER_MODE` honors the sysadmin's FLS (everything visible). `Security.stripInaccessible` does the same — both evaluate against `UserInfo.getUserId()`. There's no built-in "evaluate as user X" mode.

**Solution:**

```apex
public class FinanceExportSchedulable implements Schedulable {
    private static final Id SERVICE_ACCOUNT_USER_ID = ...;

    public void execute(SchedulableContext sc) {
        List<Account> rows = [SELECT Id, Name, AnnualRevenue, SSN__c FROM Account];
        List<Account> stripped = (List<Account>) FlsForUser.stripForUser(rows, SERVICE_ACCOUNT_USER_ID);
        // emit stripped to CSV
    }
}

public class FlsForUser {
    public static List<SObject> stripForUser(List<SObject> records, Id userId) {
        if (records.isEmpty()) return records;
        Schema.DescribeSObjectResult dsr = records[0].getSObjectType().getDescribe();
        Set<String> readable = readableFieldsForUser(dsr, userId);

        List<SObject> result = new List<SObject>();
        for (SObject src : records) {
            SObject copy = src.getSObjectType().newSObject(src.Id);
            for (String f : readable) {
                copy.put(f, src.get(f));
            }
            result.add(copy);
        }
        return result;
    }

    private static Set<String> readableFieldsForUser(
        Schema.DescribeSObjectResult dsr,
        Id userId
    ) {
        Set<String> readable = new Set<String>{ 'Id' };
        for (FieldPermissions fp : [
            SELECT Field, PermissionsRead
            FROM FieldPermissions
            WHERE SobjectType = :String.valueOf(dsr.getSObjectType())
              AND PermissionsRead = true
              AND ParentId IN (
                  SELECT PermissionSetId FROM PermissionSetAssignment WHERE AssigneeId = :userId
              )
        ]) {
            readable.add(fp.Field.substringAfter('.'));
        }
        return readable;
    }
}
```

**Why it works:** The check is anchored on `userId`, not `UserInfo.getUserId()`, so the running user is irrelevant. The cost is a SOQL query against `FieldPermissions` — typically negligible since it's once per job, not per record.

**Caveats:** This implementation reads PermissionSet-driven FLS. Profile FLS adds another query against `Profile` + the user's profile ID. Production-grade implementations should also account for muted permission sets and Permission Set Groups.

---

## Example 3: Filter at publish time (PE-triggered subscriber stays system-mode)

**Context:** A user-initiated action publishes a Platform Event that triggers downstream processing in a subscriber Apex trigger. FLS must reflect the *publishing user*, but the subscriber runs as Automated Process.

**Problem:** No FLS check inside the subscriber can match the publisher's user identity — the publisher isn't even in scope at subscribe time.

**Solution:** Strip on the publisher side and pass only safe fields into the event.

```apex
// Publisher (user context — runs as the user who clicked the button)
public class AccountSyncPublisher {
    public static void publishSync(Set<Id> accountIds) {
        List<Account> visible = (List<Account>) Security.stripInaccessible(
            AccessType.READABLE,
            [SELECT Id, Name, AnnualRevenue, SSN__c FROM Account WHERE Id IN :accountIds]
        ).getRecords();

        List<Account_Sync__e> events = new List<Account_Sync__e>();
        for (Account a : visible) {
            events.add(new Account_Sync__e(
                Originating_User_Id__c = UserInfo.getUserId(),
                Payload__c = JSON.serialize(a)
            ));
        }
        EventBus.publish(events);
    }
}

// Subscriber (runs as Automated Process — and that's fine, because the data is already filtered)
trigger AccountSyncSubscriber on Account_Sync__e (after insert) {
    for (Account_Sync__e e : Trigger.new) {
        Account a = (Account) JSON.deserialize(e.Payload__c, Account.class);
        // a only has fields the originating user could read
    }
}
```

**Why it works:** The asynchronous-channel boundary becomes the FLS boundary. Once data crosses it, no further enforcement is needed. The subscriber runs as Automated Process by platform design and that's fine, because every field in the payload is already safe.

---

## Anti-Pattern: trusting `WITH USER_MODE` in Scheduled Apex

**What practitioners do:**

```apex
public class NightlyExportSchedulable implements Schedulable {
    public void execute(SchedulableContext sc) {
        List<Account> rows = [
            SELECT Id, Name, SSN__c
            FROM Account
            WITH USER_MODE  // evaluates against the schedule creator, not the org's intent
        ];
        emitToFinance(rows);
    }
}
```

**What goes wrong:** The schedule was created two years ago by a sysadmin. `WITH USER_MODE` evaluates against that sysadmin's profile (still has access to everything). `SSN__c` ships to finance even though current org policy restricts that field to the legal team.

**Correct approach:** Either (a) explicitly run in system mode and document that as the contract, OR (b) re-apply a specific user's FLS via the cross-user helper, OR (c) refactor the job so the user identity comes from data in scope (a `Service_Account__mdt` referenced by the export config) rather than from `UserInfo.getUserId()`.
