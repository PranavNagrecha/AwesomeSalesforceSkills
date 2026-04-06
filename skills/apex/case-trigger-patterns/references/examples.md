# Examples — Case Trigger Patterns

## Example 1: Inserting Cases from a Batch Job with Assignment Rule Invocation

**Context:** A nightly Batch Apex job imports cases from an external ticketing system. Each case must be routed by the active case assignment rule so it lands in the correct queue for the support tier.

**Problem:** The initial implementation used `insert caseList;` directly. Cases were created but all landed in the default queue — assignment rules were never evaluated. The silent failure went unnoticed for days.

**Solution:**

```apex
public class CaseImportBatch implements Database.Batchable<SObject> {

    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator(
            'SELECT Id FROM External_Ticket__c WHERE Imported__c = false'
        );
    }

    public void execute(Database.BatchableContext bc, List<External_Ticket__c> tickets) {
        List<Case> casesToInsert = new List<Case>();
        for (External_Ticket__c t : tickets) {
            casesToInsert.add(new Case(
                Subject        = t.Subject__c,
                Description    = t.Body__c,
                Priority       = t.Priority__c,
                Origin         = 'Web'
            ));
        }

        // Use Database.DmlOptions to invoke the active assignment rule
        Database.DmlOptions opts = new Database.DmlOptions();
        opts.assignmentRuleHeader.useDefaultRule = true;

        // Database.insert() accepts DmlOptions; the insert keyword does not
        List<Database.SaveResult> results = Database.insert(casesToInsert, opts);

        // Handle errors without aborting the entire batch
        for (Integer i = 0; i < results.size(); i++) {
            if (!results[i].isSuccess()) {
                Database.Error err = results[i].getErrors()[0];
                System.debug('Case insert failed: ' + err.getMessage()
                    + ' | Source ticket: ' + tickets[i].Id);
            }
        }
    }

    public void finish(Database.BatchableContext bc) {}
}
```

**Why it works:** `Database.DmlOptions.assignmentRuleHeader.useDefaultRule = true` signals the platform to evaluate the active assignment rule for each inserted case, replicating the behavior a user gets when checking "Assign using active assignment rule" on the record form.

---

## Example 2: Before Insert Entitlement Auto-Association Using EntitlementContact

**Context:** A telecom company sells support entitlements to specific named contacts on an account (not to the account as a whole). Cases created via API must automatically receive the correct entitlement so the entitlement process starts.

**Problem:** Without a trigger, cases created via the API arrive with no `EntitlementId`. The entitlement process never starts, milestones are never created, and SLA timers do not run.

**Solution:**

```apex
trigger CaseTrigger on Case (before insert, before update, after update, before delete, after delete) {
    if (Trigger.isBefore && Trigger.isInsert) {
        CaseTriggerHandler.associateEntitlements(Trigger.new);
    }
    if (Trigger.isBefore && Trigger.isUpdate) {
        // Re-associate if ContactId changes and no entitlement is set
        CaseTriggerHandler.associateEntitlementsOnUpdate(Trigger.new, Trigger.oldMap);
    }
    if (Trigger.isAfter && Trigger.isUpdate) {
        CaseTriggerHandler.completeMilestonesOnClose(Trigger.new, Trigger.oldMap);
    }
    if (Trigger.isBefore && Trigger.isDelete) {
        CaseTriggerHandler.onBeforeDelete(Trigger.old);
    }
}
```

```apex
public with sharing class CaseTriggerHandler {

    public static void associateEntitlements(List<Case> newCases) {
        Set<Id> contactIds = new Set<Id>();
        for (Case c : newCases) {
            if (c.ContactId != null && c.EntitlementId == null) {
                contactIds.add(c.ContactId);
            }
        }
        if (contactIds.isEmpty()) return;

        // EntitlementContact links a specific contact to an entitlement
        Map<Id, Id> contactToEntitlement = new Map<Id, Id>();
        for (EntitlementContact ec : [
            SELECT ContactId, EntitlementId
            FROM EntitlementContact
            WHERE ContactId IN :contactIds
              AND Entitlement.Status = 'Active'
              AND Entitlement.EndDate >= TODAY
            ORDER BY Entitlement.StartDate DESC  // prefer the most recently started entitlement
        ]) {
            if (!contactToEntitlement.containsKey(ec.ContactId)) {
                contactToEntitlement.put(ec.ContactId, ec.EntitlementId);
            }
        }

        for (Case c : newCases) {
            if (c.EntitlementId == null && contactToEntitlement.containsKey(c.ContactId)) {
                c.EntitlementId = contactToEntitlement.get(c.ContactId);
            }
        }
    }

    public static void associateEntitlementsOnUpdate(
            List<Case> newCases, Map<Id, Case> oldMap) {
        List<Case> needsAssociation = new List<Case>();
        for (Case c : newCases) {
            Boolean contactChanged = c.ContactId != oldMap.get(c.Id).ContactId;
            if (contactChanged && c.EntitlementId == null) {
                needsAssociation.add(c);
            }
        }
        if (!needsAssociation.isEmpty()) {
            associateEntitlements(needsAssociation);
        }
    }

    public static void completeMilestonesOnClose(
            List<Case> newCases, Map<Id, Case> oldMap) {
        Set<Id> closingIds = new Set<Id>();
        for (Case c : newCases) {
            if (c.IsClosed && !oldMap.get(c.Id).IsClosed) {
                closingIds.add(c.Id);
            }
        }
        if (closingIds.isEmpty()) return;

        List<CaseMilestone> open = [
            SELECT Id, CompletionDate
            FROM CaseMilestone
            WHERE CaseId IN :closingIds
              AND IsCompleted = false
        ];
        if (open.isEmpty()) return;

        Datetime now = Datetime.now();
        for (CaseMilestone cm : open) {
            cm.CompletionDate = now;
        }
        update open;
    }

    public static void onBeforeDelete(List<Case> oldCases) {
        for (Case c : oldCases) {
            if (c.MasterRecordId != null) {
                // Merge delete: c is being absorbed into MasterRecordId
                // Place merge-specific pre-processing here (e.g., re-parent child records)
                System.debug('Case merge detected. Losing: ' + c.Id
                    + ' | Master: ' + c.MasterRecordId);
            }
            // For true deletes (MasterRecordId == null), place permanent-delete logic here
        }
    }
}
```

**Why it works:** The `Before Insert` context allows direct field assignment on `Trigger.new` records without an extra DML statement. The `EntitlementContact` junction query respects contact-specific coverage and prefers the most recently started active entitlement when a contact has multiple.

---

## Anti-Pattern: Using `insert` Keyword When Assignment Rules Must Fire

**What practitioners do:** Write `insert caseList;` in a service method or trigger handler, assuming the platform evaluates assignment rules the same way it does when a user saves via the UI.

**What goes wrong:** The platform silently skips assignment rule evaluation for all programmatic DML. All inserted cases land with the default owner (typically the running user or a queue configured as the default). No error is thrown. The failure is discovered in production when support managers notice cases bypassing routing.

**Correct approach:** Replace `insert caseList;` with `Database.insert(caseList, opts)` where `opts` is a `Database.DmlOptions` instance with `assignmentRuleHeader.useDefaultRule = true`. This is a one-line change with no other impact on the insert behavior.

```apex
// Wrong — silently skips assignment rules
insert caseList;

// Correct — assignment rules evaluated
Database.DmlOptions opts = new Database.DmlOptions();
opts.assignmentRuleHeader.useDefaultRule = true;
Database.insert(caseList, opts);
```
