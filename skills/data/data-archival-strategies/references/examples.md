# Examples — Data Archival Strategies

## Example 1: Archiving 5-Year-Old Opportunity Records to a Big Object

**Context:** A financial services org has 8 million Opportunity records, with 3 million older than 5 years that are closed and no longer actively used in reports. Data storage is at 78% of the Enterprise allocation. The compliance team requires that these records remain queryable for audit purposes for 7 years from close date.

**Problem:** Deleting records would violate the 7-year retention policy. Leaving them in place is pushing the org toward the storage limit, and reports on the Opportunity object are slowing down. Standard archival to an external system would make the data unavailable to Salesforce auditors without custom integration.

**Solution:**

Step 1 — Define the Big Object to hold archived Opportunities:

```xml
<!-- ArchivedOpportunity__b.object (Metadata API) -->
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
  <deploymentStatus>Deployed</deploymentStatus>
  <fields>
    <fullName>AccountId__c</fullName>
    <label>Account</label>
    <referenceTo>Account</referenceTo>
    <relationshipName>ArchivedOpportunities</relationshipName>
    <required>true</required>
    <type>Lookup</type>
  </fields>
  <fields>
    <fullName>CloseDate__c</fullName>
    <label>Close Date</label>
    <required>true</required>
    <type>DateTime</type>
  </fields>
  <fields>
    <fullName>OriginalId__c</fullName>
    <label>Original Opportunity ID</label>
    <length>18</length>
    <required>false</required>
    <type>Text</type>
  </fields>
  <fields>
    <fullName>Amount__c</fullName>
    <label>Amount</label>
    <required>false</required>
    <type>Number</type>
    <precision>18</precision>
    <scale>2</scale>
  </fields>
  <fields>
    <fullName>StageName__c</fullName>
    <label>Stage</label>
    <length>40</length>
    <required>false</required>
    <type>Text</type>
  </fields>
  <indexes>
    <fullName>ArchivedOpportunityIndex</fullName>
    <label>Archived Opportunity Index</label>
    <fields>
      <name>AccountId__c</name>
      <sortDirection>ASC</sortDirection>
    </fields>
    <fields>
      <name>CloseDate__c</name>
      <sortDirection>DESC</sortDirection>
    </fields>
  </indexes>
  <label>Archived Opportunity</label>
  <pluralLabel>Archived Opportunities</pluralLabel>
</CustomObject>
```

Step 2 — Batch Apex archival job:

```apex
public class OpportunityArchivalBatch implements Database.Batchable<SObject> {
    private Date cutoffDate;

    public OpportunityArchivalBatch(Date cutoffDate) {
        this.cutoffDate = cutoffDate;
    }

    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator(
            'SELECT Id, AccountId, CloseDate, Amount, StageName ' +
            'FROM Opportunity ' +
            'WHERE CloseDate < :cutoffDate AND IsClosed = true'
        );
    }

    public void execute(Database.BatchableContext bc, List<Opportunity> scope) {
        List<ArchivedOpportunity__b> toArchive = new List<ArchivedOpportunity__b>();

        for (Opportunity opp : scope) {
            toArchive.add(new ArchivedOpportunity__b(
                AccountId__c = opp.AccountId,
                CloseDate__c = DateTime.newInstance(opp.CloseDate, Time.newInstance(0,0,0,0)),
                OriginalId__c = opp.Id,
                Amount__c = opp.Amount,
                StageName__c = opp.StageName
            ));
        }

        // Write to Big Object — idempotent, safe to retry
        List<Database.SaveResult> results = Database.insertImmediate(toArchive);

        // Only delete source records if all archive writes succeeded
        List<Id> successfullyArchived = new List<Id>();
        for (Integer i = 0; i < results.size(); i++) {
            if (results[i].isSuccess()) {
                successfullyArchived.add(scope[i].Id);
            }
        }

        if (!successfullyArchived.isEmpty()) {
            // Hard delete to bypass recycle bin and reclaim storage immediately
            List<Opportunity> toDelete = new List<Opportunity>();
            for (Id oppId : successfullyArchived) {
                toDelete.add(new Opportunity(Id = oppId));
            }
            Database.delete(toDelete, false);
            Database.emptyRecycleBin(toDelete);
        }
    }

    public void finish(Database.BatchableContext bc) {
        System.debug('Opportunity archival batch complete.');
    }
}
```

Step 3 — Schedule the batch:

```apex
// Archive opportunities closed more than 5 years ago
Date cutoff = Date.today().addYears(-5);
OpportunityArchivalBatch batch = new OpportunityArchivalBatch(cutoff);
Database.executeBatch(batch, 200);
```

**Why it works:** The Batch Apex job processes records in manageable chunks (200 per execute), writes to the Big Object before deleting from the source, and uses `Database.emptyRecycleBin()` to immediately reclaim storage without waiting 15 days. The Big Object's composite index on AccountId and CloseDate supports audit queries like "show me all archived opportunities for this account sorted by close date."

---

## Example 2: Soft-Delete Pattern for Case Records with Compliance Hold

**Context:** A regulated healthcare org must retain Case records for 7 years for compliance but cannot move them to a Big Object because the compliance team runs standard Salesforce reports against all Cases. The org has 4 million Case records and the operations team wants to hide cases older than 2 years from the standard Case list views and queues to reduce clutter and improve performance.

**Problem:** Hard-deleting the old Cases violates the retention policy. Moving them to a Big Object breaks standard reporting. Keeping them in the active view creates noise for agents and degrades list view performance.

**Solution:**

Step 1 — Add an IsArchived__c custom field to Case:

```
Field Type: Checkbox
Field Label: Is Archived
API Name: IsArchived__c
Default Value: Unchecked
```

Step 2 — Batch Apex to flag old Cases as archived:

```apex
public class CaseArchivalFlagBatch implements Database.Batchable<SObject> {

    public Database.QueryLocator start(Database.BatchableContext bc) {
        Date twoYearsAgo = Date.today().addYears(-2);
        return Database.getQueryLocator(
            'SELECT Id FROM Case ' +
            'WHERE CreatedDate < :twoYearsAgo ' +
            'AND IsArchived__c = false ' +
            'AND Status = \'Closed\''
        );
    }

    public void execute(Database.BatchableContext bc, List<Case> scope) {
        for (Case c : scope) {
            c.IsArchived__c = true;
        }
        update scope;
    }

    public void finish(Database.BatchableContext bc) {
        System.debug('Case archival flagging complete.');
    }
}
```

Step 3 — Update all standard list views, queues, and reports to add the filter `IsArchived__c = false`. This filter is most effective when a custom index is created on `IsArchived__c` — contact Salesforce Support to add this custom index for the Case object.

Step 4 — Compliance team creates a dedicated "Archived Cases" report type filtered to `IsArchived__c = true` for audit access.

**Why it works:** Records remain fully intact in the Case object, so standard reports work without modification (the compliance team just uses the archived report type). Active-case list views and queues get a significant performance boost because the selective `IsArchived__c = false` filter eliminates the majority of rows. No storage is reclaimed, but query performance and UX are significantly improved at zero compliance risk.

---

## Anti-Pattern: Exporting to CSV and Deleting Without Hard Delete

**What practitioners do:** Export old records using Data Loader to CSV files on a local drive, then delete records using Data Loader's standard delete operation (soft delete). Storage numbers do not decrease immediately, so the practitioner repeats the export and delete cycle, accumulating more records in the Recycle Bin.

**What goes wrong:** Soft-deleted records remain in the Recycle Bin for 15 days and continue to affect query optimizer selectivity, so query performance does not improve. Storage may not be reclaimed at the rate expected. The CSV files on a local drive create a compliance and audit risk (sensitive data outside the platform). If the CSV is lost, the data is unrecoverable once the Recycle Bin clears.

**Correct approach:** Use Bulk API 2.0 hard delete to bypass the Recycle Bin entirely, or use Batch Apex with `Database.emptyRecycleBin()` after each batch. Before deleting, archive records to a Big Object or an external store if retention is required. Never rely on local CSV files as the authoritative archive.
