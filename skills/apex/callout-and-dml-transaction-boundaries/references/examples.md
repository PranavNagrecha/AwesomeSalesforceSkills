# Examples — Callout and DML Transaction Boundaries

## Example 1: Callout After Insert Throws Uncommitted Work Pending

**Context:** A controller method creates a Case record and then calls an external ticketing system to sync the case.

**Problem:** The insert creates uncommitted work. The subsequent callout throws `System.CalloutException: You have uncommitted work pending`.

**Solution:**

```apex
// Controller method — reorder to callout first
public void createAndSync(String subject, String description) {
    // 1. Call external system FIRST (no DML yet)
    HttpRequest req = new HttpRequest();
    req.setEndpoint('callout:Ticketing_System/api/tickets');
    req.setMethod('POST');
    req.setBody(JSON.serialize(new Map<String, String>{
        'subject' => subject,
        'description' => description
    }));
    req.setTimeout(10000);
    HttpResponse res = new Http().send(req);

    if (res.getStatusCode() != 201) {
        throw new CalloutException('Ticketing system returned ' + res.getStatusCode());
    }

    // 2. Parse external ID from response
    Map<String, Object> body = (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
    String externalTicketId = (String) body.get('ticketId');

    // 3. NOW do DML — safe because callout is already done
    insert new Case(
        Subject = subject,
        Description = description,
        External_Ticket_Id__c = externalTicketId
    );
}
```

**Why it works:** By moving the callout before the insert, there is no uncommitted DML when the HTTP request fires. The external ID is captured and written to the record in the subsequent DML.

---

## Example 2: Trigger Enqueues Queueable for Post-Commit Callout

**Context:** An after-insert trigger on Opportunity needs to notify an external ERP system whenever a new Opportunity is created. The trigger always has pending DML because the Opportunity record itself was just inserted.

**Problem:** Making a callout directly in the trigger throws `System.CalloutException` because the triggering DML is uncommitted.

**Solution:**

```apex
// Trigger handler — enqueue async callout
public class OpportunityTriggerHandler {
    public static void afterInsert(List<Opportunity> newOpps) {
        List<Id> oppIds = new List<Id>();
        for (Opportunity opp : newOpps) {
            if (opp.SyncToERP__c) {
                oppIds.add(opp.Id);
            }
        }
        if (!oppIds.isEmpty()) {
            System.enqueueJob(new ErpSyncQueueable(oppIds));
        }
    }
}

// Queueable — runs in its own transaction after commit
public class ErpSyncQueueable implements Queueable, Database.AllowsCallouts {
    private List<Id> opportunityIds;

    public ErpSyncQueueable(List<Id> opportunityIds) {
        this.opportunityIds = opportunityIds;
    }

    public void execute(QueueableContext ctx) {
        List<Opportunity> opps = [
            SELECT Id, Name, Amount, CloseDate
            FROM Opportunity
            WHERE Id IN :opportunityIds
        ];

        for (Opportunity opp : opps) {
            HttpRequest req = new HttpRequest();
            req.setEndpoint('callout:ERP_System/api/opportunities');
            req.setMethod('POST');
            req.setBody(JSON.serialize(opp));
            req.setTimeout(15000);

            HttpResponse res = new Http().send(req);
            if (res.getStatusCode() == 200) {
                opp.ERP_Sync_Status__c = 'Synced';
            } else {
                opp.ERP_Sync_Status__c = 'Failed: ' + res.getStatusCode();
            }
        }
        update opps;
    }
}
```

**Why it works:** The trigger enqueues the job but makes no callout itself. The Queueable runs in a fresh transaction with no prior DML, so the callout succeeds. Status tracking lets admins see which records synced.

---

## Example 3: Callout-DML-Callout Split With Chained Queueable

**Context:** A service class must validate an address via an external API, save the record with the validated address, and then register the record with a second external system.

**Problem:** Callout A (address validation) -> DML (save record) -> Callout B (registration) fails because the DML creates uncommitted work before Callout B.

**Solution:**

```apex
// Synchronous method handles callout A + DML
public class AddressRegistrationService {
    public static void validateAndRegister(Account acc) {
        // Callout A — before any DML
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:Address_Validator/api/validate');
        req.setMethod('POST');
        req.setBody(JSON.serialize(new Map<String, String>{
            'street' => acc.BillingStreet,
            'city' => acc.BillingCity
        }));
        req.setTimeout(10000);
        HttpResponse res = new Http().send(req);

        Map<String, Object> validated = (Map<String, Object>)
            JSON.deserializeUntyped(res.getBody());
        acc.BillingStreet = (String) validated.get('standardStreet');
        acc.Validation_Status__c = 'Validated';

        // DML — commits the validated address
        update acc;

        // Callout B must go async — DML just happened
        System.enqueueJob(new RegistrationQueueable(acc.Id));
    }
}

public class RegistrationQueueable implements Queueable, Database.AllowsCallouts {
    private Id accountId;

    public RegistrationQueueable(Id accountId) {
        this.accountId = accountId;
    }

    public void execute(QueueableContext ctx) {
        Account acc = [SELECT Id, Name, BillingStreet FROM Account WHERE Id = :accountId];
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:Registration_System/api/register');
        req.setMethod('POST');
        req.setBody(JSON.serialize(acc));
        req.setTimeout(10000);
        HttpResponse res = new Http().send(req);
        acc.Registration_Status__c = (res.getStatusCode() == 200) ? 'Registered' : 'Failed';
        update acc;
    }
}
```

**Why it works:** Callout A happens before any DML. The DML commits the validated data. Callout B runs in a Queueable with its own clean transaction. The three-step flow is split across two transaction boundaries.

---

## Anti-Pattern: Wrapping Callout in Try-Catch After DML

**What practitioners do:** They insert a record, then wrap the callout in a try-catch block, believing the catch will suppress the `CalloutException`.

**What goes wrong:** The exception is still thrown. The catch block fires, but the callout never executes. The developer may silently swallow the error, making the integration appear to work while no data reaches the external system.

**Correct approach:** Move the callout before DML or to an async boundary. Never rely on try-catch to work around the uncommitted-work-pending restriction — the callout simply does not execute.
