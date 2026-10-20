# Examples — System Field Behavior and Audit

## Example 1: Incremental ETL Using SystemModstamp

**Context:** A Mulesoft integration syncs Account data from Salesforce to a data warehouse every 15 minutes. The team needs to pull only records changed since the last sync.

**Problem:** The initial implementation used `LastModifiedDate > :lastSync` as the filter. After go-live, the warehouse showed stale data for Accounts that were updated by a workflow rule that stamps `Account_Status__c` when a related Opportunity closes. The team's diagnosis was that the workflow updated the field without moving LastModifiedDate, because no user modified the Account. UNVERIFIED (2026-10-20): that a workflow field update leaves LastModifiedDate unchanged — the Object Reference only defines LastModifiedDate as a user's modification (object_reference 264 L2563) and SystemModstamp as a user's or automated process's (L2566).

**Solution:**

```sql
SELECT Id, Name, AccountNumber, Industry, Account_Status__c, SystemModstamp
FROM Account
WHERE SystemModstamp > :lastSyncTimestamp
ORDER BY SystemModstamp ASC
LIMIT 2000
```

Store the highest `SystemModstamp` value from the result set as the watermark for the next poll. If the batch is interrupted, re-query from the stored watermark.

**Why it works:** SystemModstamp covers modifications by a user or an automated process (object_reference 264 L2566) and is on the default index list (large_data_volumes_bp 264 L404). It is not a complete change log: a value one object retrieves from another moves only the source object's SystemModstamp (L2581-2583).

---

## Example 2: Data Migration with Preserved Audit Dates

**Context:** A company is migrating 500,000 Contact records from a legacy CRM into Salesforce. The compliance team requires that the original creation dates and creator IDs are preserved so that audit reports reflect the true record history.

**Problem:** Without Create Audit Fields enabled, Salesforce overwrites CreatedDate with the insert timestamp and CreatedById with the integration user, losing all historical attribution.

**Solution:**

1. Enable "Set Audit Fields upon Record Creation" in Setup > User Interface (object_reference 264 L2599-2601); no Support case is needed.
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

**Problem:** The Recycle Bin UI is slow to search for one mass delete (UNVERIFIED (2026-10-20): the earlier "shows only 5,000 records" figure has no corpus line). The team needs a targeted query.

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

**What goes wrong:** A record modified by an automated process can have its SystemModstamp updated without a user modification, which is the scope difference in object_reference 264 L2563 vs L2566. UNVERIFIED (2026-10-20): the named examples (workflow field update, Process Builder, parent-driven formula recalculation). The integration misses these changes, causing silent data drift between Salesforce and the target system. The problem compounds over time and is difficult to diagnose because the records appear unchanged in standard Salesforce UI views.

**Correct approach:** Always use `SystemModstamp` for delta sync and incremental replication queries. Reserve `LastModifiedDate` for display purposes where only intentional human edits matter.
