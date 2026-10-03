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
        // insertImmediate() does not throw on failure; it returns SaveResults.
        List<Database.SaveResult> results = Database.insertImmediate(archives);
        Integer failures = 0;
        for (Database.SaveResult r : results) {
            if (!r.isSuccess()) { failures++; }
        }
        if (failures > 0) {
            // Persist the failure count for this scope; the hard-delete batch
            // must refuse to run while any scope has failures.
            System.debug(LoggingLevel.ERROR, 'Archive failures in scope: ' + failures);
        }
    }

    public void finish(Database.BatchableContext bc) {
        // Chain hard-delete batch after validation
    }
}
```

**Why it works:** Moving 6M historical records to a Big Object reduces the active Opportunity table to 2M rows. Queries become selective by default, storage pressure drops, and the Big Object retains the data for index-ordered SOQL lookups, batch analytics, and compliance queries. (Earlier versions of this example said Async SOQL; the current Big Objects guide documents synchronous SOQL along the index.) Remember the archive carries no record-level sharing and stores encrypted fields in clear text.

---

## Anti-Pattern: Using Soft Delete Instead of Archival

**What practitioners do:** Mark old Opportunities as "Archived" with a checkbox field and exclude them via report filters or list view conditions, believing this reduces query load.

**What goes wrong:** Soft-deleted records still exist in the table. Every SOQL query, sharing calculation, and batch job processes them unless every single query explicitly filters on the checkbox. A single missed filter reintroduces the full-table performance hit. Storage consumption is unchanged.

**Correct approach:** Archive to Big Objects and hard-delete the originals. If users need quick UI lookups for archived records, maintain a lightweight summary custom object with key fields (Account, Amount, CloseDate) populated during the archival batch.

---

## Example 3: Skew Queries and an Archival Decision Record

**Context:** A distributor's org holds 6.2 million Opportunities and 1.1 million Accounts with a Private Opportunity sharing model and territory-based visibility. `Amount` is encrypted with Shield Platform Encryption. Leadership wants old deals "out of the way" before a territory realignment.

**Step 1: find the skew.** Run in a full sandbox first; aggregate queries on multi-million-row tables can time out, so filter by date range if needed.

```soql
-- Q1. Owners above the 10,000-record guideline (LDV guide, Best Practices > General)
SELECT OwnerId, COUNT(Id) owned
FROM Opportunity
GROUP BY OwnerId
HAVING COUNT(Id) > 10000

-- Q2. Parents above the 10,000-child guideline
SELECT AccountId, COUNT(Id) children
FROM Opportunity
GROUP BY AccountId
HAVING COUNT(Id) > 10000

-- Q3. Archive candidates and the custom-index threshold for the filter
--     6.2M rows: custom index threshold = 100,000 + 5% of 5.2M = 360,000
SELECT COUNT() FROM Opportunity
WHERE IsClosed = true AND CloseDate < LAST_N_YEARS:3
```

**Step 2: the decision record** at `docs/adr/0092-opportunity-archive-big-object.md`. It names the metadata the build deploys: the big object (`CustomObject`, `Archived_Opportunity__b`, defined through Metadata API), the summary object (`CustomObject`, `Archived_Opportunity__c`), and the permission set limiting archive access (`PermissionSet`).

```markdown
# ADR-0092: Archive closed Opportunities older than 3 years to a big object

## Status
Accepted (2026-10-03), Data Architecture Board

## Context
- Q1: one integration user owns 2.4M Opportunities (guideline: 10,000).
- Q2: three catch-all Accounts each exceed 10,000 child Opportunities.
- Q3: 4.1M closed Opportunities older than 3 years.
- Big objects support SOQL only along the index, no aggregates, no
  record-level sharing, and store encrypted source data as clear text
  (Big Objects Implementation Guide v66.0).
- Amount is Shield-encrypted.

## Decision
1. Before archiving: reassign the integration user's open Opportunities
   to territory queues in parent-sorted batches with deferred sharing
   calculation; split the three catch-all Accounts.
2. Archive to Archived_Opportunity__b, index (Account__c, Close_Date__c,
   Opportunity_Id__c). Amount is NOT archived; Amount_Band__c (a
   non-sensitive range) is archived instead.
3. Archive access: permission set "Archive Reader" for Finance and
   Compliance only. Reps use Archived_Opportunity__c (summary object,
   Private sharing, owner preserved).
4. Hard delete runs per scope only when that scope's insertImmediate
   SaveResults show zero failures and a batch count matches.

## Consequences
### Positive
- Active table drops from 6.2M to 2.1M rows; realignment touches less.
### Negative
- Exact historical amounts leave Salesforce; finance reads them from the
  ERP. Agreed with the CFO on 2026-09-30.
- Archive counts need batch Apex; there is no COUNT() on big objects.
- Two archive objects to maintain.

## Alternatives Considered
### Checkbox "Archived" with filtered reports
Rejected: rows stay in every query, sharing calculation, and skew count.
### Export to an external data lake only
Rejected: auditors need in-org lookups by Account and date.

## Date
2026-10-03
```

**Why it works:** the skew and threshold numbers are measured, the big object's documented limits (index-only SOQL, no sharing, clear-text storage) each produce an explicit design line, and the destructive step is gated.

