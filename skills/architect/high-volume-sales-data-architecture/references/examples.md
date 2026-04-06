# Examples — High Volume Sales Data Architecture

## Example 1: Detecting and Fixing Account Ownership Skew

**Context:** A mid-market SaaS company has 2 million Accounts. An integration user that syncs records from an external CRM owns 400,000 of them. Sharing rule recalculation takes over 6 hours and blocks deployments.

**Problem:** Without redistributing ownership, every sharing rule change or role hierarchy update triggers a multi-hour recalculation. Territory reassignment jobs queue behind the recalculation and time out.

**Solution:**

```sql
-- Step 1: Identify the skew
SELECT OwnerId, Owner.Name, COUNT(Id) cnt
FROM Account
GROUP BY OwnerId, Owner.Name
ORDER BY COUNT(Id) DESC
LIMIT 20
```

```apex
// Step 2: Batch redistribute to territory queues
public class AccountOwnerRebalanceBatch implements Database.Batchable<SObject> {
    private Id integrationUserId;
    private Map<String, Id> territoryQueueMap; // region -> queue Id

    public AccountOwnerRebalanceBatch(Id intUserId, Map<String, Id> queueMap) {
        this.integrationUserId = intUserId;
        this.territoryQueueMap = queueMap;
    }

    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator(
            'SELECT Id, BillingState FROM Account WHERE OwnerId = :integrationUserId'
        );
    }

    public void execute(Database.BatchableContext bc, List<Account> scope) {
        for (Account a : scope) {
            String region = deriveRegion(a.BillingState);
            if (territoryQueueMap.containsKey(region)) {
                a.OwnerId = territoryQueueMap.get(region);
            }
        }
        Database.update(scope, false); // partial success for lock contention
    }

    public void finish(Database.BatchableContext bc) {
        // Log completion, notify admin
    }

    private String deriveRegion(String state) {
        // Map state to sales region
        if (state == null) return 'DEFAULT';
        // simplified example
        return 'WEST';
    }
}
```

**Why it works:** Moving 400K records from one owner to territory-aligned queues drops the per-owner count below 10K. Sharing recalculation goes from 6 hours to under 20 minutes because the platform processes each owner's set independently.

---

## Example 2: Archiving Historical Opportunities to a Big Object

**Context:** An enterprise org has 8 million Opportunity records. 6 million are Closed Won/Lost with CloseDates older than 3 years. Storage costs are climbing and Opportunity queries in Apex are hitting non-selective query exceptions.

**Problem:** Without archival, every SOQL query against Opportunity must contend with 8M rows. Even indexed queries pay I/O overhead scanning past historical records. Storage approaches the org limit.

**Solution:**

```apex
// Big Object definition (deployed via metadata)
// Archived_Opportunity__b with index on Account__c, Close_Date__c, Opportunity_Id__c

public class OpportunityArchivalBatch implements Database.Batchable<SObject> {
    private Date archivalCutoff;

    public OpportunityArchivalBatch(Date cutoff) {
        this.archivalCutoff = cutoff;
    }

    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator(
            'SELECT Id, AccountId, Name, Amount, CloseDate, StageName, OwnerId ' +
            'FROM Opportunity ' +
            'WHERE IsClosed = true AND CloseDate < :archivalCutoff'
        );
    }

    public void execute(Database.BatchableContext bc, List<Opportunity> scope) {
        List<Archived_Opportunity__b> archives = new List<Archived_Opportunity__b>();
        for (Opportunity opp : scope) {
            archives.add(new Archived_Opportunity__b(
                Account__c = opp.AccountId,
                Close_Date__c = opp.CloseDate,
                Opportunity_Id__c = opp.Id,
                Name__c = opp.Name,
                Amount__c = opp.Amount,
                Stage__c = opp.StageName,
                Owner__c = opp.OwnerId
            ));
        }
        Database.insertImmediate(archives);
    }

    public void finish(Database.BatchableContext bc) {
        // Chain hard-delete batch after validation
    }
}
```

**Why it works:** Moving 6M historical records to a Big Object reduces the active Opportunity table to 2M rows. Queries become selective by default, storage pressure drops, and the Big Object retains the data for Async SOQL analytics or compliance queries.

---

## Anti-Pattern: Using Soft Delete Instead of Archival

**What practitioners do:** Mark old Opportunities as "Archived" with a checkbox field and exclude them via report filters or list view conditions, believing this reduces query load.

**What goes wrong:** Soft-deleted records still exist in the table. Every SOQL query, sharing calculation, and batch job processes them unless every single query explicitly filters on the checkbox. A single missed filter reintroduces the full-table performance hit. Storage consumption is unchanged.

**Correct approach:** Archive to Big Objects and hard-delete the originals. If users need quick UI lookups for archived records, maintain a lightweight summary custom object with key fields (Account, Amount, CloseDate) populated during the archival batch.
