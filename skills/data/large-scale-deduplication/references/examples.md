# Examples — Large Scale Deduplication

## Example 1: Batch Apex Merge for 50K Duplicate Account Pairs

**Context:** A company ran a CRM migration that imported 2 million Account records from a legacy system. Post-migration analysis identified approximately 50,000 duplicate Account pairs via an external matching script that compared Name + BillingPostalCode.

**Problem:** The UI merge handles one set of up to 3 records at a time. Even using the Salesforce Merge Accounts page, 50,000 pairs would take thousands of hours manually. Trying to run all merges in a single Apex transaction hits the 10-merge-calls-per-transaction governor limit immediately.

**Solution:**

1. Load the (master\_id, losing\_id) pair list into a custom object `Dedup_Pair__c` with fields `Master_Id__c`, `Losing_Id__c`, `Status__c` (Pending/Merged/Failed), `Error__c`.
2. Run the Batch Apex job with a batch size of 10 (to ensure the execute block never exceeds 10 merge calls per transaction):

```apex
global class AccountDedupBatch implements Database.Batchable<SObject>, Database.Stateful {
    global Integer processed = 0;
    global Integer failed    = 0;

    global Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator(
            'SELECT Id, Master_Id__c, Losing_Id__c FROM Dedup_Pair__c ' +
            'WHERE Status__c = \'Pending\' ORDER BY CreatedDate ASC'
        );
    }

    global void execute(Database.BatchableContext bc, List<Dedup_Pair__c> scope) {
        List<Dedup_Pair__c> toUpdate = new List<Dedup_Pair__c>();
        for (Dedup_Pair__c pair : scope) {
            Account master = new Account(Id = pair.Master_Id__c);
            Account loser  = new Account(Id = pair.Losing_Id__c);
            Database.MergeResult result = Database.merge(master, loser, false);
            pair.Status__c = result.isSuccess() ? 'Merged' : 'Failed';
            if (!result.isSuccess()) {
                pair.Error__c = result.getErrors()[0].getMessage();
                failed++;
            } else {
                processed++;
            }
            toUpdate.add(pair);
        }
        update toUpdate;
    }

    global void finish(Database.BatchableContext bc) {
        // Optional: send completion summary to admin
        Messaging.SingleEmailMessage mail = new Messaging.SingleEmailMessage();
        mail.setToAddresses(new String[]{'admin@company.com'});
        mail.setSubject('Dedup Batch Complete');
        mail.setPlainTextBody('Merged: ' + processed + ' | Failed: ' + failed);
        Messaging.sendEmail(new Messaging.SingleEmailMessage[]{mail});
    }
}
```

Execute with: `Database.executeBatch(new AccountDedupBatch(), 10);`

**Why it works:** Batch size of 10 ensures each `execute()` invocation processes exactly 10 merges — matching the 10-merge-calls-per-transaction governor limit. The `Database.Stateful` interface preserves the running counts across batch chunks.

---

## Example 2: Bulk API 2.0 Export for External Matching

**Context:** An org has 4 million Contact records. The data team suspects 300,000+ duplicates based on email and phone overlap. SOQL cannot perform a self-join to find duplicate pairs, and standard Duplicate Jobs time out at this volume.

**Problem:** There is no in-Salesforce mechanism to efficiently identify duplicate pairs across millions of records.

**Solution:**

Export all Contacts with key matching fields using a Bulk API 2.0 query job, then run matching logic externally:

```bash
# Step 1: Create a Bulk API 2.0 query job
curl -X POST https://yourinstance.salesforce.com/services/data/v61.0/jobs/query \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "query",
    "query": "SELECT Id, FirstName, LastName, Email, Phone, AccountId, CreatedDate FROM Contact",
    "contentType": "CSV",
    "columnDelimiter": "COMMA",
    "lineEnding": "LF"
  }'

# Step 2: Poll for job completion, then download results
# (standard Bulk API 2.0 polling pattern)
```

After export, a Python script groups records by normalized Email (lowercased, trimmed) and Phone (digits only) to identify duplicate clusters. The script then applies survivorship scoring (field completeness + oldest CreatedDate) to assign master and loser roles within each cluster.

**Why it works:** Bulk API 2.0 handles multi-million-row exports efficiently via chunked CSV retrieval. External matching can use full relational logic (self-joins, fuzzy string matching, weighted scoring) that is not possible within SOQL constraints.

---

## Anti-Pattern: Running Merges One at a Time in a Loop Without Batch Limits

**What practitioners do:** Write a simple for loop in an Execute Anonymous script or a non-batch Apex class that calls `Database.merge()` for each pair in a large list.

**What goes wrong:** The first 10 merge calls succeed. On the 11th call, Salesforce throws `System.LimitException: Too many DML statements: 11` (or equivalent merge limit exception). The transaction is rolled back — none of the merges in that transaction are committed. At scale, this pattern produces partial execution with unpredictable rollback scope.

**Correct approach:** Always use Batch Apex with a controlled batch size of 10 or fewer records per `execute()` block. Each `execute()` invocation runs in its own transaction, so governor limits reset between chunks.
