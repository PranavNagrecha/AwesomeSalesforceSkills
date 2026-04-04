# Gotchas — Data Model Design Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Master-Detail Cascade Delete Has No Recycle Bin Recovery

**What happens:** When a master record is deleted, all associated detail records are immediately and permanently deleted — they do not go to the Recycle Bin. This applies recursively: if the detail object is itself a master to another object, grandchild records are also permanently deleted. There is no undo.

**When it occurs:** Any time a master record is deleted — manually by a user, via a data loader job, via Apex DML, or via an API call. The cascade is automatic and silent; there is no warning dialog in the standard UI. Bulk deletes (e.g., a data loader delete job on the parent object) trigger mass permanent deletion of all related children.

**How to avoid:**
- Before choosing master-detail, explicitly confirm with the business that cascade delete is the desired behavior in all scenarios.
- For junction objects, consider whether the business wants junction records to survive when one parent is deleted. If yes, use a lookup on that side instead of MDR.
- Implement a before-delete Apex trigger on the master object that counts related detail records and throws an exception if the count exceeds a configurable threshold, as a safety gate for bulk deletes.
- Enable Enhanced Transaction Security policies to alert administrators when bulk deletes occur above a record count threshold.

---

## Gotcha 2: Converting a Lookup to Master-Detail Requires All Children to Have a Non-Null Parent

**What happens:** If you try to convert an existing lookup relationship field to a master-detail relationship, Salesforce blocks the conversion if any child record has a null value in the lookup field. The conversion wizard surfaces an error and does not complete.

**When it occurs:** This is common when a lookup was initially marked optional (not required on page layout) and some records were created without a parent. Even a single null value in the entire object blocks the conversion.

**How to avoid:**
- Before requesting the conversion, run a SOQL query to find all records with a null parent field:
  ```soql
  SELECT Id FROM Child_Object__c WHERE Parent__c = null
  ```
- Populate the parent field on all returned records before attempting the conversion. You may need to assign a placeholder parent or perform a data migration.
- For large datasets, use Bulk API 2.0 to update the null records before the conversion.
- Document the decision: if even one record legitimately has no parent, the relationship semantics are lookup, not master-detail.

---

## Gotcha 3: Junction Object With Two Lookup Fields Cannot Use Rollup Summary on Either Parent

**What happens:** A junction object built with two lookup fields (instead of two master-detail fields) cannot support rollup summary fields on either parent object. Rollup summary fields are only available on the master side of a master-detail relationship. Lookup fields do not expose this capability regardless of field configuration.

**When it occurs:** Teams often build junction objects quickly with lookups because they are easier to add without data constraints. The rollup requirement surfaces later, after records already exist in the junction, making the fix a data migration rather than a simple field change.

**How to avoid:**
- Evaluate rollup summary requirements before creating the junction object — ask whether either parent needs to count, sum, min, or max any junction field.
- If rollup summaries are needed (now or likely in the future), build the junction with two master-detail fields from the start.
- If the junction already exists with lookup fields and rollup summaries are now required: create new MDR fields, populate them from the existing lookup values via a data loader job, make the old lookup fields non-required, then validate the rollup configuration. Delete the old lookup fields only after validating.

---

## Gotcha 4: Lookup Filters Do Not Create an Index on the Filtered Field

**What happens:** Adding a lookup filter to a relationship field (to restrict which parent records appear in the lookup search) does not create a database index on the filtered field. If the filter references a non-indexed field on the parent object, the lookup search dialog may perform slowly when the parent object has large record volumes.

**When it occurs:** Lookup filters that reference custom non-indexed fields on large parent objects (typically 100k+ records). The filter logic is evaluated at query time without index support, causing visible lag in the lookup search modal.

**How to avoid:**
- Prefer lookup filters that reference indexed fields on the parent (Id, Name, RecordTypeId, OwnerId, or fields with custom indexes).
- If filtering on a custom non-indexed field is a business requirement and the parent object is large, file a Salesforce Support case to request a custom index on that field.
- Consider filtering on a formula field alternative that combines indexed fields to achieve the same restriction without introducing a non-indexed filter.

---

## Gotcha 5: External ID Limit Is 25 Per Object, But Unique Index Behavior Differs by Field Type

**What happens:** Each object supports up to 25 external ID fields, all of which are indexed by default. However, uniqueness enforcement behavior differs: `Text` external ID fields enforce case-insensitive uniqueness by default when the Unique option is selected, while `Number` external ID fields are always case-independent (numeric). Inserting a record with a Text external ID value that differs only by case (e.g., `ABC123` vs `abc123`) from an existing record will fail the unique constraint, even if your integration treats them as different keys.

**When it occurs:** Integrations that use alphanumeric natural keys where the source system treats case as significant (e.g., `ORDER-001` and `order-001` are different orders in the ERP, but Salesforce treats them as the same external ID value).

**How to avoid:**
- Normalize external ID values to a consistent case in the integration layer before inserting into Salesforce.
- If the source system key is a pure numeric identifier, use a `Number` external ID field to avoid case ambiguity entirely.
- Document the case-sensitivity behavior in the integration spec so downstream consumers understand the constraint.

---

## Gotcha 6: Skinny Table Data May Lag After Large Bulk Loads

**What happens:** Skinny tables are denormalized projections of selected fields on a large object, maintained by Salesforce internally to speed up queries. After a large Bulk API data load (millions of records), the skinny table may not immediately reflect the newly inserted or updated data. Reports, SOQL queries, and list views that rely on the skinny table may return stale counts or missing rows for a period after the load completes.

**When it occurs:** Immediately after large bulk insert or update jobs on objects where a skinny table has been provisioned. The lag duration depends on load volume and platform conditions.

**How to avoid:**
- Schedule reports and SOQL-dependent processes with a buffer after bulk load jobs complete, rather than chaining them directly in the same automation sequence.
- Use Bulk API 2.0 job status polling to confirm the job has completed before triggering downstream processes; then allow a platform-defined settling period before running aggregate queries on the loaded object.
- Coordinate with Salesforce Support to understand the expected refresh lag for the specific skinny table configuration in your org.
