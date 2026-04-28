# Examples — Apex stripInaccessible and FLS Enforcement

## Example 1: REST endpoint accepting JSON payload of Cases

**Context:** A `@RestResource` exposed at `/services/apexrest/cases/*` accepts an array of Case records as JSON. Community/portal users hitting it have a profile that cannot edit `Internal_Notes__c` or `Priority`, but a malicious client could include those fields in the body.

**Problem:** Without enforcement, `insert deserialized;` would write whatever the client sent — including fields the user lacks FLS Edit on. `with sharing` does NOT enforce field-level access; it enforces record-level access.

**Solution:**

```apex
@RestResource(urlMapping='/cases/*')
global with sharing class CaseRestEndpoint {

    @HttpPost
    global static List<Case> create() {
        RestRequest req = RestContext.request;
        List<Case> userSupplied =
            (List<Case>) JSON.deserialize(req.requestBody.toString(), List<Case>.class);

        SObjectAccessDecision decision =
            Security.stripInaccessible(AccessType.CREATABLE, userSupplied);

        if (!decision.getRemovedFields().isEmpty()) {
            ApplicationLogger.warn(
                'CaseRestEndpoint.create',
                'Stripped: ' + JSON.serialize(decision.getRemovedFields())
            );
        }

        List<Case> safe = (List<Case>) decision.getRecords();
        insert safe;          // NEVER `insert userSupplied;`
        return safe;
    }
}
```

**Why it works:** Every field the running user cannot create on Case is removed before `insert`. The audit log captures attempted privilege escalation. `with sharing` continues to handle record visibility separately.

---

## Example 2: Lightning Aura controller updating Opportunities

**Context:** An Aura controller `@AuraEnabled` method receives a `List<Opportunity>` from the client, edited inline in a custom UI. Some users can edit `Amount` but not `StageName`; others vice-versa.

**Problem:** Trusting `update opps;` lets the client mutate any field they could put on the wire. Server-side enforcement is mandatory — client-side disabled inputs are not security.

**Solution:**

```apex
public with sharing class OpportunityEditorController {

    @AuraEnabled
    public static List<Opportunity> saveEdits(List<Opportunity> userSupplied) {
        if (userSupplied == null || userSupplied.isEmpty()) { return userSupplied; }

        SObjectAccessDecision decision =
            Security.stripInaccessible(AccessType.UPDATABLE, userSupplied);

        Map<String, Set<String>> removed = decision.getRemovedFields();
        if (!removed.isEmpty()) {
            // Surface as soft warning so the client can re-enable / explain to user
            throw new AuraHandledException(
                'You are not permitted to edit: ' + JSON.serialize(removed)
            );
        }

        List<Opportunity> safe = (List<Opportunity>) decision.getRecords();
        update safe;
        return safe;
    }
}
```

**Why it works:** `AccessType.UPDATABLE` matches the `update` operation. Throwing rather than silently stripping gives the user immediate feedback rather than a confusing partial save.

---

## Example 3: Batch processing a user-supplied list of Leads

**Context:** A Batchable processes Lead records that need user-supplied enrichments applied. The batch executes as the user who invoked `Database.executeBatch`, so the running user's FLS still applies.

**Problem:** It's easy for a developer to assume batch always runs in system mode and skip enforcement. If the user uploaded modifications to fields they cannot edit, the batch would persist those edits.

**Solution:**

```apex
public class LeadEnrichmentBatch implements Database.Batchable<SObject> {

    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator(
            'SELECT Id, Status, Rating, Annual_Revenue_Estimate__c FROM Lead ' +
            'WHERE Pending_Enrichment__c = true WITH USER_MODE'
        );
    }

    public void execute(Database.BatchableContext bc, List<Lead> scope) {
        // Apply user-supplied modifications captured upstream
        for (Lead l : scope) {
            l.Rating = 'Hot';                       // mutation supplied by user CSV
            l.Annual_Revenue_Estimate__c = 5000000; // mutation supplied by user CSV
        }

        SObjectAccessDecision decision =
            Security.stripInaccessible(AccessType.UPDATABLE, scope);

        if (!decision.getRemovedFields().isEmpty()) {
            ApplicationLogger.warn(
                'LeadEnrichmentBatch.execute',
                JSON.serialize(decision.getRemovedFields())
            );
        }

        update decision.getRecords();
    }

    public void finish(Database.BatchableContext bc) {}
}
```

**Why it works:** `WITH USER_MODE` enforces FLS on the read; `stripInaccessible(UPDATABLE)` enforces FLS on the write. Each operation has its own enforcement gate.

---

## Anti-Pattern: DML on the original list after a strip call

**What practitioners do:**

```apex
SObjectAccessDecision decision =
    Security.stripInaccessible(AccessType.CREATABLE, userSupplied);
insert userSupplied;   // BUG — strip had zero effect
```

**What goes wrong:** The strip returned a NEW list inside the decision; the original argument is untouched. `insert userSupplied;` writes every field the client sent, including those the user cannot create. Functionally equivalent to no FLS enforcement at all — and worse, it gives a false sense of security to anyone reading the code.

**Correct approach:**

```apex
SObjectAccessDecision decision =
    Security.stripInaccessible(AccessType.CREATABLE, userSupplied);
insert decision.getRecords();   // operate on the decision's output
```

The repo's static checker `scripts/check_apex_stripinaccessible_and_fls_enforcement.py` flags this pattern as P0.
