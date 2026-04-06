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

**Why it happens:** LLMs assume that child-object DML propagates changes to the parent object, similar to how roll-up summary fields cause parent triggers to fire in master-detail relationships. CaseComment-to-Case is a lookup, not master-detail, and the platform does not touch the Case record when a CaseComment is inserted.

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

**Detection hint:** `Database.convertLead` followed by a query on Contact or Account that references Lead custom fields, without any intermediate DML to transfer those values.

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
// Find tasks completed this week
List<Task> completedThisWeek = [
    SELECT Id, Subject, CompletedDateTime
    FROM Task
    WHERE Status = 'Completed'
    AND CompletedDateTime >= :Datetime.newInstance(Date.today().toStartOfWeek(), Time.newInstance(0,0,0,0))
];
```

**Detection hint:** Any SOQL query on Task with `Status = 'Completed'` that filters on `ActivityDate` instead of `CompletedDateTime` for date-range logic.

---

## Anti-Pattern 6: Omitting EndDateTime When Creating Events Programmatically

**What the LLM generates:**

```apex
Event e = new Event();
e.Subject = 'Discovery Call';
e.StartDateTime = DateTime.now();
e.DurationInMinutes = 60;
e.WhoId = contactId;
insert e; // Throws: Required fields are missing: [EndDateTime]
```

**Why it happens:** The Salesforce UI allows creating Events by specifying only a start time and duration — the UI calculates EndDateTime. LLMs learn from UI-centric documentation and tutorials that describe "start time and duration" as the required inputs, then generate Apex that mirrors the UI pattern instead of the API contract.

**Correct pattern:**

```apex
Event e = new Event();
e.Subject = 'Discovery Call';
e.StartDateTime = DateTime.now();
e.EndDateTime = DateTime.now().addMinutes(60);
e.WhoId = contactId;
insert e;
```

**Detection hint:** `new Event()` followed by `insert` where `DurationInMinutes` is set but `EndDateTime` is absent.
