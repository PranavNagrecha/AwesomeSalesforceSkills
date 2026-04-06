# Gotchas — Record Type Strategy At Scale

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Layout Assignments Deploy Per Profile, Not Per Object

**What happens:** When deploying record type changes, the layout assignment mapping is stored in the Profile metadata (specifically the `layoutAssignments` section of each `.profile-meta.xml`). If you deploy a new record type without also deploying updated profiles, the new record type gets no layout assignment for those profiles, and users on those profiles either see the default layout or receive an error. Conversely, deploying profiles without the record type causes deployment failures.

**When it occurs:** Any metadata deployment (change sets, Metadata API, SFDX) that includes new or modified record types but does not include the affected profiles in the same package. This is especially common when teams split deployments across workstreams.

**How to avoid:** Always include the affected Profile metadata in the same deployment package as the RecordType metadata. Use `sf project retrieve` to pull both the RecordType and Profile XML, verify the `layoutAssignments` entries, and deploy them together.

---

## Gotcha 2: Deleting a Record Type Silently Reassigns Records

**What happens:** When a record type is deleted, Salesforce reassigns all records that had that record type to the default record type of the record owner's profile. This happens automatically with no confirmation dialog beyond the initial deletion warning. If the default record type has different picklist values or a different business process (e.g., a different Sales Process on Opportunity), records may silently change stage picklist behavior, validation rule firing, and report categorization.

**When it occurs:** During record type consolidation or cleanup projects. Administrators delete the "old" record type expecting records to remain unchanged, but the reassignment changes the business process membership of those records.

**How to avoid:** Before deleting any record type, run a SOQL query to count affected records: `SELECT COUNT() FROM Account WHERE RecordTypeId = '...'`. Migrate those records to the target record type using Bulk API update of RecordTypeId before deleting the old record type. Verify downstream automation and reports after migration.

---

## Gotcha 3: Record Type Picklist Values Do Not Cascade from Global Value Sets

**What happens:** When a Global Value Set adds a new value, that value is not automatically included in any record type's picklist override. Record type picklist filtering is an allowlist — only explicitly included values appear for users on that record type. New global values are invisible to users until an administrator manually adds them to each record type's picklist value set.

**When it occurs:** Organizations that use Global Value Sets for consistency assume that adding a value to the global set propagates everywhere. It does for the field definition, but record type picklist overrides are a separate configuration layer that must be updated independently.

**How to avoid:** After adding values to a Global Value Set, audit every record type on every object that uses that picklist field and update the record type picklist overrides. Build this into the change management checklist. Consider using the Metadata API to script bulk updates to RecordType picklist values rather than clicking through Setup.

---

## Gotcha 4: Dynamic Forms Visibility Rules Do Not Apply in Reports or List Views

**What happens:** Dynamic Forms controls field visibility on Lightning record pages only. It does not affect which fields appear in reports, list views, or SOQL queries. A field hidden by a Dynamic Forms visibility rule is still fully accessible through reports, the API, and list view columns. Practitioners who assume Dynamic Forms provides data-level security are mistaken — it is a UI-layer control only.

**When it occurs:** When teams use Dynamic Forms as a substitute for field-level security (FLS). Users who should not see sensitive fields can still access them through reports or API queries even though the fields are hidden on the record page.

**How to avoid:** Use field-level security (FLS) on profiles or permission sets for actual data access control. Use Dynamic Forms only for UX optimization — showing relevant fields to the right users — not for security enforcement.
