# Examples — Standard Object Quirks

## Example 1: Querying Contact Email from a Task Using Polymorphic TYPEOF

**Context:** A support team dashboard needs to display the email address of the Contact or Lead associated with each open Task. The developer writes a SOQL query using `Who.Email` expecting it to return the email for both Contacts and Leads.

**Problem:** `Who` is a polymorphic relationship — `WhoId` "represents a human such as a lead or a contact" and is documented as polymorphic (object_reference.txt L278448) — so the platform cannot determine at compile time whether the target is a Contact or a Lead, and dot-notation for a type-specific field does not resolve.

UNVERIFIED (2026-09-05): the exact error string *"No such column 'Email' on entity 'Name'"* and the `TYPEOF` grammar itself are SOQL/SOSL Reference Guide content — zero hits for `TYPEOF` in either the Object Reference or the Apex Developer Guide. The polymorphism is grounded above; the error text is reported behaviour. See `apex/apex-polymorphic-soql`.

**Solution:**

```apex
List<Task> openTasks = [
    SELECT Id, Subject, Status,
        TYPEOF Who
            WHEN Contact THEN FirstName, LastName, Email
            WHEN Lead THEN FirstName, LastName, Email, Company
        END
    FROM Task
    WHERE CompletedDateTime = null
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

Note the filter change from the naive version: `CompletedDateTime = null` rather than `Status != 'Completed'`. `CompletedDateTime` is set whenever a task is saved with a **Closed** status (object_reference.txt L277989–L277994), so it catches `Closed - No Action` and every other closed value the org has defined, which a string comparison against `'Completed'` does not.

---

## Example 2: PersonAccount Email Query Returning Null

**Context:** An integration pulls Account records to sync email addresses to a marketing platform. The query uses `SELECT Id, Name, Email FROM Account` and filters to PersonAccounts. The integration sends null emails for every PersonAccount.

**Problem:** Account has no bare `Email` field. Person account email lives in `PersonEmail`, whose description reads "Email address for this person account. **Label is Email**" (object_reference.txt L13770) — the UI label is the trap. These fields "are the subset of person account fields that are contained in the child person contact record of each person account"; when `IsPersonAccount` is false they are null and can't be modified, and person account fields only appear at all once the feature is enabled, which it is not by default (object_reference.txt L13677–L13683).

**Solution:**

```apex
List<Account> personAccounts = [
    SELECT Id, Name, FirstName, LastName,
           PersonEmail, PersonMailingStreet, PersonMailingCity
    FROM Account
    WHERE IsPersonAccount = true
    AND PersonEmail != null
];

for (Account pa : personAccounts) {
    System.debug('PersonAccount: ' + pa.Name + ' — Email: ' + pa.PersonEmail);
}
```

**Why it works:** PersonAccounts expose person-contact fields on Account behind the `Person` prefix. `IsPersonAccount` is read-only (`Defaulted on create, Filter, Group, Sort` — object_reference.txt L13116–L13122), so it is safe as a filter and useless as an assignment target.

Two traps sit immediately behind this query. Building the field list dynamically with `Schema.Account.PersonEmail` throws: "Field tokens aren't available for person accounts… Instead, specify the field name as a string" (apexdev.txt L10866–L10867). And writing `Name` back on a synced record fails — for a person account "the `Name` field can't be modified with DML operations" (apexdev.txt L9029); write `FirstName` / `LastName` instead.

---

## Example 3: CaseComment Trigger Not Updating Parent Case Last Modified

**Context:** A service team wants the Case `LastModifiedDate` to update whenever an agent adds a CaseComment, so that reporting accurately reflects recent activity. They add logic to an existing Case after-update trigger, but adding CaseComments does not fire it.

**Problem:** Triggers are scoped per sObject, and CaseComment is one of the standard child objects that carries its own trigger context — "You can define triggers for top-level standard objects that support triggers, such as a Contact or an Account, some standard child objects, such as a CaseComment, and custom objects" (apexdev.txt L14861–L14863). Nothing propagates a CaseComment insert into a Case trigger.

**Solution:**

```apex
trigger CaseCommentTrigger on CaseComment (after insert) {
    Set<Id> caseIds = new Set<Id>();
    for (CaseComment cc : Trigger.new) {
        caseIds.add(cc.ParentId);   // ParentId is required and refers to Case
    }

    // Touch the parent Cases to update LastModifiedDate
    List<Case> casesToUpdate = [SELECT Id FROM Case WHERE Id IN :caseIds];
    update casesToUpdate;
}
```

**Why it works:** Explicitly updating the parent Case from the CaseComment context bumps `LastModifiedDate` and fires whatever Case-side automation should respond to "recent activity".

**What this design must not grow into:** an edit-comment feature. In the API a CaseComment "can't be modified after insertion unless the user has the 'Modify All Records' object-level permission for Cases or the 'Modify All Data' permission. If not, users can only update the `IsPublished` field, and can't delete CaseComment" (object_reference.txt L63045–L63049). Append a new comment instead. And never read `IsNotificationSelected` back to decide whether an email went out — "when this field is queried, it always returns null" (object_reference.txt L62994–L63000).

---

## Example 4: The Person-Account Trigger That Never Ran

**Context:** An org enables person accounts. A developer adds a guard to the existing Contact trigger so that person-account contacts skip the standalone-contact logic, and adds enrichment for person accounts in the same trigger. Nothing is enriched. The trigger has 90% coverage and its tests pass.

**Problem:** The Contact trigger never executes for these records. The Apex Developer Guide places the rule inside "Operations That Don't Invoke Triggers": *"Inserts, updates, and deletes on person accounts fire Account triggers, not Contact triggers"* (apexdev.txt L15521). Both halves of the change are dead code — the guard defends against an event that is never raised, and the enrichment sits on a code path the platform never enters. The passing tests prove only that a standalone Contact behaves correctly.

**Diagnostic first.** Before rewriting anything, establish which triggers exist and which object they are on:

```bash
sf data query --use-tooling-api --target-org myOrg --query \
  "SELECT Name, TableEnumOrId, Status FROM ApexTrigger WHERE TableEnumOrId IN ('Account','Contact')"
```

| Name | TableEnumOrId | Reads person-account DML? |
|---|---|---|
| `ContactTrigger` | Contact | **No** — person-account DML never reaches it |
| `AccountTrigger` | Account | Yes — this is the only entry point |
| *(none)* | Account | If this row is empty, the requirement is unimplemented |

**Solution:** move the enrichment to the Account trigger and delete the guard. The deployable handler and its test class are in `references/metadata-examples.md` § 1–2; the shape of the correction is:

```apex
// BEFORE — ContactTrigger: unreachable for person accounts.
if (accts.get(c.AccountId)?.IsPersonAccount == true) {
    continue;              // defends against an event that never fires
}

// AFTER — AccountTrigger handler: the only context person-account DML enters.
for (Account a : (List<Account>) Trigger.new) {
    if (!a.IsPersonAccount) { continue; }
    enrich(a);             // FirstName/LastName/PersonEmail — never Name
}
```

**Why it works:** the logic now lives where the platform dispatches. Two adjacent rules keep it honest: `Name` can't be modified with DML on a person account (apexdev.txt L9029), and no update account trigger fires when a record type changes between business and person account in either direction (apexdev.txt L15545–L15546) — so record-type conversion needs a scheduled compensator rather than a trigger.

---

## Anti-Pattern: Adding EndDateTime "Because the API Requires It"

**What practitioners do:** Take an Event payload that already carries a duration and bolt on an `EndDateTime`, on the widely-repeated belief that the API mandates that specific field. Sometimes the two disagree.

**What goes wrong:** The rule is an either/or, not a requirement on one field: "If `IsAllDayEvent` is false, a value must be supplied for either `DurationInMinutes` or `EndDateTime`. Supplying values in both fields is allowed if the values add up to the same amount of time" (object_reference.txt L111593–L111597, repeated at L111637–L111641). Supplying both with values that *disagree* is what the guide disallows — so the "fix" introduces the defect. `EndDateTime` was mandatory only in API 12.0 and earlier; from 13.0 it is optional under the either/or rule (object_reference.txt L111589–L111592).

The failure is hard to trace because the error moves. For API 38.0 and earlier, errors always surface on `DurationInMinutes`; from 39.0 the reported field depends on which value is missing (object_reference.txt L111642–L111646). Two orgs on different API versions report the same defect differently.

**Correct approach:** pick one form per integration and validate it at the boundary. Only the payload carrying **neither** field is invalid:

| Payload | Valid? | Why |
|---|---|---|
| `StartDateTime` + `DurationInMinutes` | Yes | Duration alone satisfies the rule |
| `StartDateTime` + `EndDateTime` | Yes | End time alone satisfies the rule |
| Both, agreeing | Yes | Explicitly allowed |
| Both, disagreeing | No | Values must add up to the same amount of time |
| Neither (and `IsAllDayEvent` false) | No | The only genuinely missing-field case |

```apex
// Validate at the boundary rather than guessing which field the API wants.
private static void assertDurationContract(Event e) {
    if (e.IsAllDayEvent == true) { return; }

    Boolean hasDuration = e.DurationInMinutes != null;
    Boolean hasEnd      = e.EndDateTime != null;

    if (!hasDuration && !hasEnd) {
        throw new IllegalArgumentException(
            'Event needs either DurationInMinutes or EndDateTime.'
        );
    }
    if (hasDuration && hasEnd) {
        Long derived = (e.EndDateTime.getTime() - e.StartDateTime.getTime()) / 60000;
        if (derived != e.DurationInMinutes) {
            throw new IllegalArgumentException(
                'DurationInMinutes and EndDateTime disagree: ' +
                e.DurationInMinutes + ' vs ' + derived
            );
        }
    }
}
```

---

## Anti-Pattern: Assuming Account Deletion Cascades to Contacts

**What practitioners do:** Delete an Account record expecting all related Contacts to be deleted automatically, similar to how child records in a master-detail relationship are cascade-deleted.

**What goes wrong:** Cascading delete is documented as a parent/child behaviour — "if you delete a parent object, you delete its children automatically, as long as each child record can be deleted", the guide's example being a Case taking its CaseComment, CaseHistory and CaseSolution records with it (apexdev.txt L8236–L8240). `Contact.AccountId` is `Nillable` (object_reference.txt L71327–L71336), i.e. a lookup rather than a master-detail, so the Contact is not a cascade child of the Account.

UNVERIFIED (2026-09-05): the specific mechanism — that Account deletion sets `Contact.AccountId` to null and leaves the Contact in place — is not stated in the Object Reference or the Apex Developer Guide (`grep -n -i "orphan"` returns nothing relevant in either). It is a Salesforce Help topic that could not be fetched. Test it in a sandbox before designing around it.

**Correct approach:** Before deleting an Account, query all child Contacts and decide explicitly whether to delete them, reassign them, or leave them. Note the deletable-children rule cuts the other way too: an undeletable child blocks the parent delete outright, so a permissions failure on a child surfaces as an error naming the parent.

```apex
trigger AccountBeforeDelete on Account (before delete) {
    Map<Id, Integer> contactCount = new Map<Id, Integer>();
    for (AggregateResult ar : [
        SELECT AccountId aid, COUNT(Id) total
        FROM Contact
        WHERE AccountId IN :Trigger.oldMap.keySet()
        GROUP BY AccountId
    ]) {
        contactCount.put((Id) ar.get('aid'), (Integer) ar.get('total'));
    }

    for (Account a : Trigger.old) {
        Integer total = contactCount.get(a.Id);
        if (total != null && total > 0) {
            a.addError(
                'Cannot delete Account with ' + total +
                ' related Contact(s). Reassign or delete them first.'
            );
        }
    }
}
```

Records deleted this way are recoverable for a window: deleted records "are placed in the Recycle Bin for 15 days from where they can be restored" (apexdev.txt L8212, L8260).
