# LLM Anti-Patterns — Standard Object Quirks

Common mistakes AI coding assistants make when generating or advising on Standard Object Quirks.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using Dot-Notation on Polymorphic Lookups

**What the LLM generates:**

```apex
SELECT Id, Subject, Who.Email, Who.Phone
FROM Task
WHERE OwnerId = :userId
```

**Why it happens:** LLMs treat polymorphic lookups (WhoId, WhatId) like standard lookups because training data contains many examples of regular lookup dot-notation. The LLM does not distinguish between a resolved-type relationship (e.g., Account.Name on Contact) and a polymorphic relationship that could resolve to multiple sObject types.

**Correct pattern:**

```apex
SELECT Id, Subject,
    TYPEOF Who
        WHEN Contact THEN Email, Phone
        WHEN Lead THEN Email, Phone, Company
    END
FROM Task
WHERE OwnerId = :userId
```

**Detection hint:** Look for `Who\.` or `What\.` followed by any field name other than `Name`, `Type`, or `Id` in a SOQL query on Task or Event.

---

## Anti-Pattern 2: Querying Email Instead of PersonEmail on Account

**What the LLM generates:**

```apex
List<Account> accounts = [SELECT Id, Name, Email FROM Account WHERE IsPersonAccount = true];
```

**Why it happens:** LLMs generalize from the Contact object, where `Email` is the correct API name. Since PersonAccounts are "like Contacts," the LLM assumes the same field name applies on the Account object. The `Person` prefix requirement is a Salesforce-specific naming convention that does not exist in training data for any other platform.

**Correct pattern:**

```apex
List<Account> accounts = [SELECT Id, Name, PersonEmail FROM Account WHERE IsPersonAccount = true];
```

**Detection hint:** Regex `FROM\s+Account.*\bEmail\b` where `Email` is not preceded by `Person`. Any bare `Email` field in an Account query when the context involves PersonAccounts is suspect.

---

## Anti-Pattern 3: Expecting Case Triggers to Fire on CaseComment DML

**What the LLM generates:**

```apex
// In Case after-update trigger:
// "This will fire when a CaseComment is added..."
trigger CaseTrigger on Case (after update) {
    for (Case c : Trigger.new) {
        if (c.LastModifiedDate > Trigger.oldMap.get(c.Id).LastModifiedDate) {
            // Handle new comment activity
        }
    }
}
```

**Why it happens:** LLMs assume that child-object DML propagates changes to the parent object, similar to how roll-up summary fields cause parent triggers to fire in master-detail relationships. In fact triggers are scoped per sObject, and CaseComment is explicitly one of the standard child objects that carries its own trigger context (apexdev.txt L14861-L14863). Nothing about CaseComment is special here — it is ordinary trigger scoping — but the *conclusion* is right even though the usual reasoning about master-detail is not: deleting a Case does cascade to its CaseComment, CaseHistory and CaseSolution records (apexdev.txt L8236-L8240), so "it's only a lookup" is not the explanation.

**Correct pattern:**

```apex
trigger CaseCommentTrigger on CaseComment (after insert) {
    Set<Id> caseIds = new Set<Id>();
    for (CaseComment cc : Trigger.new) {
        caseIds.add(cc.ParentId);
    }
    // Explicitly update parent Cases
    update [SELECT Id FROM Case WHERE Id IN :caseIds];
}
```

**Detection hint:** Any trigger on `Case` that references "comment" in comments or string literals, combined with the absence of a CaseComment trigger in the same codebase.

---

## Anti-Pattern 4: Assuming Lead Conversion Preserves All Fields Automatically

**What the LLM generates:**

```apex
Database.LeadConvert lc = new Database.LeadConvert();
lc.setLeadId(leadId);
lc.setConvertedStatus('Qualified');
Database.convertLead(lc);
// All Lead data is now on the Contact — query Contact to verify
Contact c = [SELECT Id, Custom_Score__c FROM Contact WHERE Id = :lc.getContactId()];
// Assumes Custom_Score__c was transferred from Lead
```

**Why it happens:** LLMs assume field-level data transfer is automatic during Lead conversion because the operation is described as "converting" the record. Training data rarely includes the nuance that only mapped fields transfer. The LLM confidently references custom fields on the converted Contact without verifying mapping.

**Correct pattern:**

```apex
// Before conversion: verify field mapping exists or copy manually
Lead l = [SELECT Id, Custom_Score__c FROM Lead WHERE Id = :leadId];
Database.LeadConvert lc = new Database.LeadConvert();
lc.setLeadId(leadId);
lc.setConvertedStatus('Qualified');
Database.LeadConvertResult result = Database.convertLead(lc);

// Explicitly set unmapped fields on the converted Contact
Contact c = new Contact(Id = result.getContactId());
c.Custom_Score__c = l.Custom_Score__c;
update c;
```

**Detection hint:** `Database.convertLead` followed by a query on Contact or Account that references Lead custom fields, without any intermediate DML to transfer those values. A second, quieter form: a before-insert trigger on Contact or Opportunity presented as the conversion-time guard. Those before triggers "fire during lead conversion only if validation and triggers for lead conversion are enabled in the organization" (apexdev.txt L15548-L15551), which is not the default — so the guard runs for every path except the one it was written for. A third: code that expects conversion to overwrite an existing Contact's values. Only empty target fields are overwritten, `setOverwriteLeadSource` excepted (apexdev.txt L8356-L8360).

---

## Anti-Pattern 5: Using ActivityDate as Completion Date on Task

**What the LLM generates:**

```apex
// Find tasks completed this week
List<Task> completedThisWeek = [
    SELECT Id, Subject, ActivityDate
    FROM Task
    WHERE Status = 'Completed'
    AND ActivityDate >= :Date.today().toStartOfWeek()
];
```

**Why it happens:** The name `ActivityDate` sounds like "the date of the activity," which LLMs interpret as the completion date. In reality, `ActivityDate` is the due date. LLMs do not consistently know that `CompletedDateTime` is the correct field for when a Task was actually finished.

**Correct pattern:**

```apex
// Find tasks completed this week. No Status literal: CompletedDateTime is set
// whenever the task is saved with a *Closed* status, whatever that status is
// spelled in this org (object_reference.txt L277989-L278009).
List<Task> completedThisWeek = [
    SELECT Id, Subject, Status, CompletedDateTime
    FROM Task
    WHERE CompletedDateTime >= :Datetime.newInstance(Date.today().toStartOfWeek(), Time.newInstance(0,0,0,0))
];
```

**Detection hint:** Any SOQL query on Task that filters on `ActivityDate` for date-range logic, **or** that hard-codes `Status = 'Completed'` as a proxy for completion. The second is the subtler defect: an org with `Closed - No Action` flagged `closed` in its `TaskStatus` value set populates `CompletedDateTime` for that status too, so the literal undercounts. Prefer `CompletedDateTime != null`.

---

## Anti-Pattern 6: Asserting That Events Require EndDateTime

**What the LLM generates:**

```apex
Event e = new Event();
e.Subject = 'Discovery Call';
e.StartDateTime = DateTime.now();
e.DurationInMinutes = 60;
e.WhoId = contactId;
insert e; // LLM comment: "Throws: Required fields are missing: [EndDateTime]"
```

...followed by a "fix" that adds `EndDateTime` while leaving `DurationInMinutes` in place, often computed from a different variable.

**Why it happens:** This is folklore that reads like documentation. `EndDateTime` was genuinely required in API 12.0 and earlier (object_reference.txt L111589-L111592), and that sentence has outlived its version. Models reproduce the confident absolute rather than the conditional that replaced it.

**What the guide actually says** (object_reference.txt L111593-L111597, repeated verbatim under `EndDateTime` at L111637-L111641):

> "If IsAllDayEvent is false, a value must be supplied for either DurationInMinutes or EndDateTime. Supplying values in both fields is allowed if the values add up to the same amount of time."

So the snippet above **inserts successfully**. The generated fix is worse than the generated bug: adding a second, independently computed field is how the two come to disagree, and disagreement is the case the guide explicitly disallows.

**Correct pattern:**

```apex
// Either form is valid. Pick one per integration.
Event byDuration = new Event(
    Subject = 'Discovery Call',
    StartDateTime = DateTime.now(),
    DurationInMinutes = 60,      // sufficient on its own
    WhoId = contactId
);

Event byEndTime = new Event(
    Subject = 'Discovery Call',
    StartDateTime = start,
    EndDateTime = start.addMinutes(60),   // also sufficient on its own
    WhoId = contactId
);
```

**Detection hint:** Any comment or prose claiming `EndDateTime` is required for Event, and any `new Event()` where both `DurationInMinutes` and `EndDateTime` are assigned from separately computed expressions rather than derived from one another. Flag the *claim*, not just the code — the claim is what propagates into the next design.

---

## Anti-Pattern 7: Guarding a Contact Trigger Against Person Accounts

**What the LLM generates:**

```apex
trigger ContactTrigger on Contact (before update) {
    Map<Id, Account> accts = new Map<Id, Account>([
        SELECT Id, IsPersonAccount FROM Account WHERE Id IN :accountIds
    ]);
    for (Contact c : Trigger.new) {
        if (accts.get(c.AccountId)?.IsPersonAccount == true) {
            continue; // "Skip the implicit Contact of a PersonAccount"
        }
        // ...
    }
}
```

**Why it happens:** The premise — that person-account DML fires Contact triggers as well as Account triggers — is stated widely enough on forums and blogs to dominate the training distribution. It is wrong, and the Apex Developer Guide is unambiguous (apexdev.txt L15521):

> "Inserts, updates, and deletes on person accounts fire Account triggers, not Contact triggers."

The guard is doubly harmful. It costs a query per transaction to defend against an event that never occurs, and it signals to the next reader that person accounts were considered — when in fact the Account-side implementation that should exist does not.

**Correct pattern:**

```apex
// AccountTrigger.trigger — the only context person-account DML enters.
trigger AccountTrigger on Account (before insert, before update) {
    new AccountQuirkHandler().run();
}

// AccountQuirkHandler: branch, do not filter.
for (Account a : (List<Account>) Trigger.new) {
    if (a.IsPersonAccount) {
        // person path: FirstName / LastName / PersonEmail. Never Name.
    } else {
        // business path
    }
}
```

**Detection hint:** `IsPersonAccount` referenced anywhere inside a trigger or handler whose sObject is `Contact`. Treat every hit as an unimplemented Account-side requirement, not as a code-style issue. A second signal: prose in the same PR asserting that person-account DML "fires both triggers".

---

## Anti-Pattern 8: Merging More Than Three Records, or Reading MasterRecordId Too Early

**What the LLM generates:**

```apex
// Merge all duplicates into the master in one call
Database.merge(master, duplicateList, false);   // duplicateList.size() == 8

// ...and detect the losers here:
trigger AccountAudit on Account (before delete) {
    for (Account a : Trigger.old) {
        if (a.MasterRecordId != null) { log(a); }   // always null
    }
}
```

**Why it happens:** `Database.merge` accepts a `List<sObject>`, so the signature invites an unbounded list; nothing in the type system encodes the cap. And `before delete` is the intuitive place to inspect a record about to disappear.

Both are wrong for documented reasons. "You can pass a main record and up to two additional sObject records to a single merge method" (apexdev.txt L8202); the API side gives the same cap and the workaround — "Up to three records can be merged in a single request, including the master record... To merge more than 3 records, do a successive merge" (salesforce_app_limits_cheatsheet.txt L977-L982). And "the MasterRecordId field is only set in after delete trigger events" (apexdev.txt L15358-L15359), so the `before delete` check reads null on every row.

**Correct pattern:**

```apex
// Successive merges of at most two losers per call.
for (Integer i = 0; i < duplicates.size(); i += 2) {
    List<Account> slice = new List<Account>();
    for (Integer j = i; j < Math.min(i + 2, duplicates.size()); j++) {
        slice.add(duplicates[j]);
    }
    for (Database.MergeResult r : Database.merge(master, slice, false)) {
        if (!r.isSuccess()) { handle(r.getErrors()); }
    }
}

// Detection belongs in AFTER delete.
trigger AccountMergeAudit on Account (after delete) {
    for (Account a : Trigger.old) {
        if (a.MasterRecordId != null) { log(a); }
    }
}
```

**Detection hint:** any `merge` or `Database.merge` call whose second argument is a list variable with no size guard, or a list literal holding three or more elements; and any `MasterRecordId` reference inside a `before delete` block. A third signal: code expecting one trigger invocation per merged record — a merge fires a single delete event for all losers and a single update event for the winner, and reparented children fire nothing (apexdev.txt L15354-L15366).
