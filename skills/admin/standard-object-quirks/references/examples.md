# Examples — Standard Object Quirks

## Example 1: Querying Contact Email from a Task Using Polymorphic TYPEOF

**Context:** A support team dashboard needs to display the email address of the Contact or Lead associated with each open Task. The developer writes a SOQL query using `Who.Email` expecting it to return the email for both Contacts and Leads.

**Problem:** `Who.Email` does not compile because `Who` is a polymorphic relationship — the platform cannot determine at compile time whether `Who` is a Contact (which has `Email`) or a Lead (which also has `Email` but is a different sObject). The query fails with: *"No such column 'Email' on entity 'Name'"*.

**Solution:**

```apex
List<Task> openTasks = [
    SELECT Id, Subject, Status,
        TYPEOF Who
            WHEN Contact THEN FirstName, LastName, Email
            WHEN Lead THEN FirstName, LastName, Email, Company
        END
    FROM Task
    WHERE Status != 'Completed'
    AND OwnerId = :UserInfo.getUserId()
];

for (Task t : openTasks) {
    String email;
    if (t.Who instanceof Contact) {
        email = ((Contact) t.Who).Email;
    } else if (t.Who instanceof Lead) {
        email = ((Lead) t.Who).Email;
    }
    System.debug('Task: ' + t.Subject + ' — Contact/Lead email: ' + email);
}
```

**Why it works:** The `TYPEOF` clause tells SOQL which fields to retrieve for each possible target type. At runtime, the polymorphic relationship resolves to the correct sObject, and the `instanceof` check lets you safely cast and access type-specific fields.

---

## Example 2: PersonAccount Email Query Returning Null

**Context:** An integration pulls Account records to sync email addresses to a marketing platform. The query uses `SELECT Id, Name, Email FROM Account` and filters to PersonAccounts. The integration sends null emails for every PersonAccount.

**Problem:** On the Account object, the `Email` field does not exist for PersonAccounts. PersonAccount email is stored in the `PersonEmail` field. Querying `Email` on Account either fails or returns null, depending on context. The UI shows the email on the Account page, so developers assume `Email` is the correct API name.

**Solution:**

```apex
List<Account> personAccounts = [
    SELECT Id, Name, PersonEmail, PersonMailingStreet, PersonMailingCity
    FROM Account
    WHERE IsPersonAccount = true
    AND PersonEmail != null
];

for (Account pa : personAccounts) {
    System.debug('PersonAccount: ' + pa.Name + ' — Email: ' + pa.PersonEmail);
}
```

**Why it works:** PersonAccounts expose Contact-equivalent fields on the Account object using the `Person` prefix. `PersonEmail` maps to the Contact's `Email` field on the implicit Contact record. Always use `IsPersonAccount = true` to filter, and always use Person-prefixed field names when querying Account for person-level data.

---

## Example 3: CaseComment Trigger Not Updating Parent Case Last Modified

**Context:** A service team wants the Case `LastModifiedDate` to update whenever an agent adds a CaseComment, so that reporting accurately reflects recent activity. They add logic to an existing Case after-update trigger, but adding CaseComments does not fire it.

**Problem:** DML on CaseComment does not trigger any Case triggers. CaseComment is a separate sObject with its own trigger context. The platform does not propagate CaseComment changes to the parent Case record unless you explicitly perform a DML update on the Case.

**Solution:**

```apex
trigger CaseCommentTrigger on CaseComment (after insert) {
    Set<Id> caseIds = new Set<Id>();
    for (CaseComment cc : Trigger.new) {
        caseIds.add(cc.ParentId);
    }

    // Touch the parent Cases to update LastModifiedDate
    List<Case> casesToUpdate = [SELECT Id FROM Case WHERE Id IN :caseIds];
    // Updating without field changes still bumps LastModifiedDate
    update casesToUpdate;
}
```

**Why it works:** By explicitly updating the parent Case records from a CaseComment trigger, you force the platform to recalculate `LastModifiedDate` on the Case. This also fires any Case triggers or Flows that should respond to "recent activity."

---

## Anti-Pattern: Assuming Account Deletion Cascades to Contacts

**What practitioners do:** Delete an Account record expecting all related Contacts to be deleted automatically, similar to how child records in a master-detail relationship are cascade-deleted.

**What goes wrong:** Contacts are not deleted. Instead, their `AccountId` is set to null, leaving orphaned Contact records with no parent Account. This creates data quality issues: Contacts without Accounts are invisible in many reports and list views that filter by Account.

**Correct approach:** Before deleting an Account, query all child Contacts and decide explicitly whether to delete them, reassign them to another Account, or leave them orphaned intentionally. Use a before-delete trigger on Account to enforce the desired behavior:

```apex
trigger AccountBeforeDelete on Account (before delete) {
    List<Contact> orphans = [SELECT Id FROM Contact WHERE AccountId IN :Trigger.oldMap.keySet()];
    if (!orphans.isEmpty()) {
        // Option A: block deletion
        for (Account a : Trigger.old) {
            a.addError('Cannot delete Account with active Contacts. Reassign or delete Contacts first.');
        }
        // Option B: cascade delete (uncomment if desired)
        // delete orphans;
    }
}
```
