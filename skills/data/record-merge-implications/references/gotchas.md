# Gotchas — Record Merge Implications

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

---

## Gotcha 1: Apex Database.merge() Does Not Copy Fields — Silent Data Loss

Unlike the UI merge which presents a field selection screen, `Database.merge()` in Apex silently keeps only the master record's current field values. Fields that are null on the master and non-null on losing records are permanently discarded after the merge with no error or warning.

This is the most common source of data loss in programmatic deduplication jobs. The only safe pattern is to explicitly query all losing records, compare field values, and update the master record with any values that should be preserved before calling `Database.merge()`.

---

## Gotcha 2: Merged Record IDs Are Permanently Deleted — No Rollback

Once a merge is executed, the losing records' IDs are deleted. Salesforce creates an EntityId redirect so API queries for the old ID return the master record's data — but this redirect is not guaranteed for all API versions or all third-party integrations. External systems (ERPs, data warehouses, marketing platforms) that stored the old IDs may fail to resolve them or create orphaned references.

Before bulk merging, export the mapping of losing record IDs to master record ID so external systems can be updated. There is no undo for a merge — the only recovery is a sandbox restore or a manual rebuild.

---

## Gotcha 3: Converted Leads Cannot Be Merged — Error at Runtime

Attempting to merge a Lead where `IsConverted = true` raises: `FIELD_INTEGRITY_EXCEPTION: Cannot merge a converted Lead`. This error is not surfaced in the UI's merge candidate list — the converted Lead simply does not appear as a merge option. But in Apex or when building merge automation, the code must explicitly filter out converted Leads:

```apex
List<Lead> mergeCandidates = [SELECT Id, IsConverted FROM Lead WHERE ... AND IsConverted = false];
```

Failing to filter will cause bulk merge jobs to fail on any batch containing a converted Lead.

---

## Gotcha 4: Campaign Member Deduplication Is Silent — One Member Is Kept, One Is Deleted

When two Contacts (or Leads) who are both Campaign Members of the same Campaign are merged, Salesforce deduplicates the Campaign Members — keeping one and deleting the other. The kept member is the one from the master record. The losing member's response data (e.g., `HasResponded`, `Status`) may differ and the losing member's response data is discarded.

If Campaign Member response history is important, review Campaign Member data across merge candidates before merging and consolidate response statuses manually if needed.

---

## Gotcha 5: Merge Fires Before/After Delete Triggers on Losing Records

The merge operation deletes the losing records. This fires `before delete` and `after delete` triggers on those records. If any trigger or Flow performs cleanup actions on delete (e.g., archiving related data, decrementing counters, sending notifications), those actions will run for each losing record during the merge.

In bulk merge jobs processing thousands of records, this can cause governor limit failures if the delete-triggered automation is not bulkified, or produce unexpected notifications/side effects. Always test bulk merges in a sandbox with production-scale data to surface delete-trigger interactions before running in production.
