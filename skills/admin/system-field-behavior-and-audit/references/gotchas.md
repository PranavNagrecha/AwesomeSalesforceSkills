# Gotchas — System Field Behavior and Audit

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: SystemModstamp Updates on Cross-Object Formula Recalculations

**What happens:** A child record's SystemModstamp updates even though no user or process directly touched the child. This occurs when the child has a formula field that references a parent field, and the parent field value changes. The formula recalculation causes SystemModstamp to advance on the child.

**When it occurs:** Any object with cross-object formula fields (e.g., `Account.Industry` referenced in a Contact formula). Changing the parent triggers formula recalc on all children, updating each child's SystemModstamp.

**How to avoid:** Expect inflated delta sync volumes on objects with cross-object formulas. Factor this into ETL batch sizing. Do not treat a SystemModstamp change as proof that a user edited the record — cross-reference with LastModifiedDate if human attribution matters.

---

## Gotcha 2: Create Audit Fields Requires Both Org Permission and User Permission

**What happens:** A developer enables the org-level "Set Audit Fields upon Record Creation" setting but the insert still overwrites CreatedDate with the current timestamp. The migration appears to work but all dates are wrong.

**When it occurs:** The org setting is necessary but not sufficient. The user performing the insert must also have the "Set Audit Fields upon Record Creation" user permission assigned via a permission set. Without both layers, the platform silently ignores the provided audit field values.

**How to avoid:** After enabling the org setting, create a dedicated permission set with the "Set Audit Fields upon Record Creation" permission and assign it to the migration user. Test with a single record before running the full migration batch.

---

## Gotcha 3: ALL ROWS Returns Archived Records Too

**What happens:** A query intended to find only soft-deleted (Recycle Bin) records returns unexpected results that include archived records on objects with archiving enabled.

**When it occurs:** On objects where Salesforce archiving is configured (e.g., Task, Event, or custom objects with Big Object archival). The `ALL ROWS` keyword returns both `IsDeleted = true` records and archived records.

**How to avoid:** Always include an explicit `IsDeleted = true` filter when you only want Recycle Bin records. Do not rely on `ALL ROWS` alone as a proxy for "deleted records."

---

## Gotcha 4: Permanently Deleted Records Are Unqueryable

**What happens:** A team attempts to recover records deleted more than 15 days ago using `ALL ROWS` and finds nothing. Once the Recycle Bin retention period expires and records are permanently deleted (hard delete), they are removed from all query results including `ALL ROWS` and `queryAll`.

**When it occurs:** After the 15-day Recycle Bin window (or immediately if a user clicks "Empty Recycle Bin" or uses `Database.emptyRecycleBin()`). Also occurs if the Bulk API hard-delete feature was used.

**How to avoid:** Implement a scheduled job or integration that queries soft-deleted records on a regular cadence (e.g., daily) and backs them up to an external system before the 15-day window closes. Alert on unexpected bulk deletes.

---

## Gotcha 5: LastModifiedDate Is Not Indexed

**What happens:** A SOQL query filtering on `LastModifiedDate > :someTimestamp` runs slowly or times out on objects with millions of records, even though the same query structure with `SystemModstamp` returns instantly.

**When it occurs:** On any object with a large record count (typically > 100,000 rows). The platform does not maintain a standard index on LastModifiedDate, so the query results in a full table scan. SystemModstamp has a platform-maintained index.

**How to avoid:** Always use `SystemModstamp` instead of `LastModifiedDate` in SOQL WHERE clauses for date-range filtering. If you must filter on LastModifiedDate for business reasons, request a custom index from Salesforce Support.

---

## Gotcha 6: Create Audit Fields Only Works on Insert, Not Update

**What happens:** A developer attempts to correct a wrong CreatedDate on existing records by running a DML update with the Create Audit Fields permission. The update either silently ignores the value or throws a FIELD_NOT_UPDATEABLE error.

**When it occurs:** Any attempt to modify CreatedDate, CreatedById, LastModifiedDate, or LastModifiedById via update DML, regardless of permissions.

**How to avoid:** Plan audit field values before the initial insert. If historical dates were not set correctly during migration, the only remediation is to delete and re-insert the records (which resets relationships and may cascade deletes on child records) or to store the correct historical date in a separate custom field.
