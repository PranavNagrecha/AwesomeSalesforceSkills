# Examples — Sharing Recalculation Performance

## Example 1: Batching Three OWD Changes into One Recalculation Job

**Context:** A financial services org is tightening OWD on three custom objects (Loan_Application__c, Credit_File__c, and Collateral__c) from Public Read/Write to Private as part of a compliance initiative. Each object holds approximately 1.5 million records. Without deferral, three separate recalculation jobs will run sequentially over the maintenance window.

**Problem:** If each OWD change is applied one at a time, Salesforce triggers three independent full recalculation jobs on objects with 1.5 million records each. Total estimated recalculation time without deferral: 4–6 hours. The maintenance window is only 3 hours.

**Solution:**

```
1. Setup > Defer Sharing Calculations > enable "Suspend Sharing Rule and Criteria Recalculation"
2. Setup > Security > Sharing Settings:
   - Set Loan_Application__c OWD: Public Read/Write → Private
   - Set Credit_File__c OWD: Public Read/Write → Private
   - Set Collateral__c OWD: Public Read/Write → Private
3. Setup > Defer Sharing Calculations > disable (un-check)
   Salesforce collapses all three changes into a single recalculation job.
4. Monitor: Setup > Environments > Monitoring > Apex Jobs — wait for completion.
5. Spot-check: confirm record access via a test user in each object's list view.
```

**Why it works:** Deferral prevents incremental recalculation from firing after each individual OWD change. When deferral is cleared, Salesforce processes the full combined change set in one pass, collapsing what would have been three sequential jobs into a single background job. This does not always mean the combined job runs faster, but it reduces total overhead and coordination risk.

---

## Example 2: Protecting Apex Managed Shares Through an OWD Tightening

**Context:** An org uses a custom Apex sharing reason on the `Opportunity` object (reason: `Territory_Share__c`) to grant access to records based on custom territory logic not captured by the standard role hierarchy. The org is changing Opportunity OWD from Public Read Only to Private.

**Problem:** When Opportunity OWD changes to Private, Salesforce triggers a full recalculation. All Apex share rows with `RowCause = 'Territory_Share__c'` are deleted during this process. If no recalculation batch class is registered, all territory-based Opportunity access is silently revoked — users in non-owning territories lose visibility immediately with no error message.

**Solution:**

```apex
// TerritoryShareRecalculation.cls — registered as the recalculation class
// for the Territory_Share__c Apex Sharing Reason on Opportunity

global class TerritoryShareRecalculation implements Database.Batchable<SObject> {

    global Database.QueryLocator start(Database.BatchableContext bc) {
        // Process all Opportunities in scope
        return Database.getQueryLocator('SELECT Id, OwnerId FROM Opportunity');
    }

    global void execute(Database.BatchableContext bc, List<Opportunity> records) {
        // Delete existing Apex share rows for this reason on this batch
        List<OpportunityShare> toDelete = [
            SELECT Id FROM OpportunityShare
            WHERE RowCause = 'Territory_Share__c'
            AND OpportunityId IN :records
        ];
        delete toDelete;

        // Recompute and insert fresh grants based on territory logic
        List<OpportunityShare> newShares = TerritoryShareService.computeShares(records);
        insert newShares;
    }

    global void finish(Database.BatchableContext bc) {
        // Log or notify on completion
    }
}
```

Registration: Object Manager > Opportunity > Apex Sharing Reasons > Territory_Share__c > Edit > set Recalculation Apex Class = `TerritoryShareRecalculation`

**Why it works:** When Salesforce finishes the full OWD recalculation job, it automatically invokes the registered batch class to rebuild Apex grants for each sharing reason. The registration is the only mechanism Salesforce provides to restore Apex shares post-recalculation — there is no automatic reinstatement without it.

---

## Anti-Pattern: Making Role Hierarchy Changes One at a Time During Business Hours

**What practitioners do:** An admin needs to reparent four role hierarchy nodes for a territory restructuring. They log into Setup and edit each role one at a time during business hours, saving after each change.

**What goes wrong:** Each save triggers an incremental recalculation background job. Four individual role edits produce four overlapping recalculation jobs, all competing for the same sharing table locks. Users experience intermittent access loss while the jobs run. If the org has ownership skew on any of the affected roles, the jobs can each take 20–40 minutes, blocking further group operations during that time.

**Correct approach:** Enable Defer Sharing Calculations before making any role changes. Reparent all four roles while deferred. Then disable deferral during a maintenance window to trigger a single collapsed recalculation job. This reduces the number of full recalculation cycles from 4 to 1 and keeps business-hours record access consistent.
