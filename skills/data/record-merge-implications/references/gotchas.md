# Gotchas — Record Merge Implications

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

---

## Gotcha 1: Apex Database.merge() Does Not Copy Fields — Silent Data Loss

Unlike the UI merge which presents a field selection screen, `Database.merge()` in Apex silently keeps only the master record's current field values. Fields that are null on the master and non-null on losing records are permanently discarded after the merge with no error or warning ("if a field value on the main record is empty, the resulting field value remains empty", apexdev 264 L8349-8352).

This is the most common source of data loss in programmatic deduplication jobs. The only safe pattern is to explicitly query all losing records, compare field values, and update the master record with any values that should be preserved before calling `Database.merge()`.

---

## Gotcha 2: Merged Record IDs Are Deleted — Undelete Restores Them, Not the Re-Parenting

Once a merge is executed, the losing records are deleted and each keeps `MasterRecordId`, the Id of the record that was kept (object_reference 264 L12945-12952). An earlier version said Salesforce creates an EntityId redirect so API queries for the old ID return the master record's data; UNVERIFIED (2026-10-20): no corpus file describes a redirect. External systems (ERPs, data warehouses, marketing platforms) that stored the old IDs may fail to resolve them or create orphaned references.

Before bulk merging, export the mapping of losing record IDs to master record ID so external systems can be updated; afterwards `ALL ROWS` queries (apexdev 264 L8446) and REST `QueryAll` (api_rest 264 L17232) still return the deleted rows. The earlier claim that there is no undo and the only recovery is a sandbox restore was wrong: "You can undelete records that were deleted as the result of a merge. However, the merge reparents the child objects, and that reparenting can't be undone" (apexdev 264 L8444-8445). Undelete restores the losing record, not the original parentage of its children.

---

## Gotcha 3: Converted Leads Cannot Be Merged — Error at Runtime (UNVERIFIED (2026-10-20))

Attempting to merge a Lead where `IsConverted = true` raises: `FIELD_INTEGRITY_EXCEPTION: Cannot merge a converted Lead` (UNVERIFIED (2026-10-20): neither the restriction nor the error text is in the corpus). This error is not surfaced in the UI's merge candidate list — the converted Lead simply does not appear as a merge option. But in Apex or when building merge automation, the code must explicitly filter out converted Leads:

```apex
List<Lead> mergeCandidates = [SELECT Id, IsConverted FROM Lead WHERE ... AND IsConverted = false];
```

Failing to filter will cause bulk merge jobs to fail on any batch containing a converted Lead.

---

## Gotcha 4: Campaign Member Deduplication Is Silent — One Member Is Kept, One Is Deleted (UNVERIFIED (2026-10-20))

(UNVERIFIED (2026-10-20): this whole gotcha is Help-level; no corpus file describes Campaign Member handling in a merge.) When two Contacts (or Leads) who are both Campaign Members of the same Campaign are merged, Salesforce deduplicates the Campaign Members — keeping one and deleting the other. The kept member is the one from the master record. The losing member's response data (e.g., `HasResponded`, `Status`) may differ and the losing member's response data is discarded.

If Campaign Member response history is important, review Campaign Member data across merge candidates before merging and consolidate response statuses manually if needed.

---

## Gotcha 5: Merge Fires Before/After Delete Triggers on Losing Records

The merge operation deletes the losing records. This fires `before delete` and `after delete` triggers on those records (apexdev 264 L15559-15563, L15569-15572), as a single delete event for all of them, and `MasterRecordId` is set only in `after delete`. The winner gets one update event, and reparented child records fire no triggers (apexdev 264 L15564-15567). If any trigger or Flow performs cleanup actions on delete (e.g., archiving related data, decrementing counters, sending notifications), those actions will run for each losing record during the merge.

In bulk merge jobs processing thousands of records, this can cause governor limit failures if the delete-triggered automation is not bulkified, or produce unexpected notifications/side effects. Always test bulk merges in a sandbox with production-scale data to surface delete-trigger interactions before running in production.
