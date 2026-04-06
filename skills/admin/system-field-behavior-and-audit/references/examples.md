# Examples — System Field Behavior and Audit

## Example 1: Incremental ETL Using SystemModstamp

**Context:** A Mulesoft integration syncs Account data from Salesforce to a data warehouse every 15 minutes. The team needs to pull only records changed since the last sync.

**Problem:** The initial implementation used `LastModifiedDate > :lastSync` as the filter. After go-live, the warehouse showed stale data for Accounts that were updated by a workflow rule that stamps `Account_Status__c` when a related Opportunity closes. The workflow updated the field, but LastModifiedDate did not change because no user or API call directly modified the Account.

**Solution:**

```sql
SELECT Id, Name, AccountNumber, Industry, Account_Status__c, SystemModstamp
FROM Account
WHERE SystemModstamp > :lastSyncTimestamp
ORDER BY SystemModstamp ASC
LIMIT 2000
```

Store the highest `SystemModstamp` value from the result set as the watermark for the next poll. If the batch is interrupted, re-query from the stored watermark.

**Why it works:** SystemModstamp captures every modification — user edits, API updates, workflow field updates, formula recalculations, and roll-up summary recalcs. It is also indexed, so the query uses a selective filter instead of a full table scan.

---

## Example 2: Data Migration with Preserved Audit Dates

**Context:** A company is migrating 500,000 Contact records from a legacy CRM into Salesforce. The compliance team requires that the original creation dates and creator IDs are preserved so that audit reports reflect the true record history.

**Problem:** Without Create Audit Fields enabled, Salesforce overwrites CreatedDate with the insert timestamp and CreatedById with the integration user, losing all historical attribution.

**Solution:**

1. Enable "Set Audit Fields upon Record Creation" at the org level (Setup > User Interface or via Salesforce Support case).
2. Assign the "Set Audit Fields upon Record Creation" user permission to the integration user via a permission set.
3. Include audit fields in the Data Loader CSV:

```csv
FirstName,LastName,Email,CreatedDate,CreatedById,LastModifiedDate,LastModifiedById
Jane,Doe,jane@example.com,2019-03-15T10:30:00Z,005xx000001Sv1eAAC,2024-11-22T14:15:00Z,005xx000001Sv1eAAC
```

4. Run the insert. Verify a sample record:

```sql
SELECT Id, FirstName, CreatedDate, CreatedById FROM Contact WHERE Email = 'jane@example.com'
```

**Why it works:** The Create Audit Fields permission tells the platform to accept the provided values for CreatedDate, CreatedById, LastModifiedDate, and LastModifiedById instead of auto-generating them. This only works on insert — the fields cannot be overridden on update.

---

## Example 3: Soft-Delete Recovery After Accidental Mass Delete

**Context:** A sales operations user accidentally mass-deleted 2,000 Leads using Data Loader. The team needs to identify exactly which records were deleted and recover them before the 15-day Recycle Bin window closes.

**Problem:** The standard Recycle Bin UI in Setup only shows 5,000 records across all objects and can be slow to search. The team needs a targeted query.

**Solution:**

```sql
SELECT Id, FirstName, LastName, Company, Email, LastModifiedDate, LastModifiedById
FROM Lead
WHERE IsDeleted = true
  AND SystemModstamp >= 2025-03-20T00:00:00Z
ALL ROWS
```

Then recover via Apex:

```apex
List<Lead> deletedLeads = [
    SELECT Id FROM Lead
    WHERE IsDeleted = true AND SystemModstamp >= 2025-03-20T00:00:00Z
    ALL ROWS
];
Database.UndeleteResult[] results = Database.undelete(deletedLeads, false);
for (Database.UndeleteResult r : results) {
    if (!r.isSuccess()) {
        System.debug('Failed to undelete: ' + r.getId() + ' — ' + r.getErrors()[0].getMessage());
    }
}
```

**Why it works:** The `ALL ROWS` keyword includes soft-deleted records in the query results. `Database.undelete()` restores records from the Recycle Bin, preserving all field values and relationships.

---

## Anti-Pattern: Using LastModifiedDate for Delta Sync

**What practitioners do:** Write integration queries with `WHERE LastModifiedDate > :lastSync` because LastModifiedDate is the more familiar field name.

**What goes wrong:** Any record modified by an automated process (workflow field update, process builder, formula field recalculation on a parent change) will have its SystemModstamp updated but LastModifiedDate unchanged. The integration misses these changes, causing silent data drift between Salesforce and the target system. The problem compounds over time and is difficult to diagnose because the records appear unchanged in standard Salesforce UI views.

**Correct approach:** Always use `SystemModstamp` for delta sync and incremental replication queries. Reserve `LastModifiedDate` for display purposes where only intentional human edits matter.
