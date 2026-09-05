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

---

## Gotcha 5: A Permission Set Can Grant Visibility But Can Never Grant a Default

**What happens:** An org migrates every persona off profiles onto permission set groups. Record type access moves to `recordTypeVisibilities` on the permission sets and the profiles are stripped back to a bare minimum. Users can still select every record type they could before, so the migration is signed off. Weeks later, picklist governance is quietly gone: users creating records without explicitly choosing a type are landing on the **Master** record type, which applies no picklist filtering, so validation rules keyed on `RecordType.DeveloperName` never match and reports bucket the new rows under a type nobody designed.

**When it occurs:** Any permission-set-first or PSG migration, on every object with record types, at the moment the profile's `recordTypeVisibilities` block is trimmed. `PermissionSetRecordTypeVisibility` has exactly two fields — `recordType` and `visible`. `ProfileRecordTypeVisibility` has four — `recordType`, `visible`, `default`, and `personAccountDefault`. There is no `default` on the permission set side to migrate to, so the setting is not moved, it is deleted. Salesforce raises nothing: the platform falls back to Master, which `Schema.RecordTypeInfo.isMaster()` documents as "the default record type that's used when a record has no custom record type associated with it".

**How to avoid:** Treat the `default` column of the assignment matrix as permanently profile-resident and audit it separately from everything else the migration moves. Before trimming any profile, run the describe audit in `metadata-examples.md` §5 as each persona: exactly one `isDefaultRecordTypeMapping() == true` per object, and it must not be the row where `isMaster() == true`. Re-run it after the PSG deploy, not only before. `admin/permission-sets-vs-profiles` covers the wider set of profile-only settings this belongs to.

---

## Gotcha 6: The Layout Assignment With No Record Type Is a Row in the Matrix, and Consolidation Deletes It

**What happens:** A consolidation removes two record types, and the generated profile diff removes every `layoutAssignments` entry naming them. It also removes the entry that named no record type at all, because the tooling grouped it with the object being cleaned up. Users on that profile now get whatever layout the platform picks when nothing matches, and the symptom is intermittent — it only shows on records created outside the record type flow, on rows created before record types existed, and on anything whose type was cleared.

**When it occurs:** Any scripted or LLM-generated prune of `layoutAssignments`. `ProfileLayoutAssignments` has a required `layout` and an **optional** `recordType`: "If the `recordType` of the record matches a layout assignment rule, it uses the specified layout." The entry without a `recordType` is the rule that applies when none matches, and it looks like an incomplete record to a filter that keys on record type name.

**How to avoid:** Count the rows before and after. Per profile, per object, the target count is (number of visible record types) + 1, not (number of visible record types). Write the fallback row explicitly into the matrix — the worked table in `metadata-examples.md` §1 has it as its own line — so a diff that drops it is visible in review. The checker in this package flags an active record type with no `layoutAssignment` anywhere; it cannot flag a missing fallback, because a missing fallback is indistinguishable from a profile that never had one.

---

## Gotcha 7: A Bulk `RecordTypeId` Update Runs Every Automation on the Object, Once Per Record

**What happens:** A migration moves 200,000 Opportunities onto a consolidated record type with a Bulk API 2.0 job. The team plans it as a metadata cutover and sizes it accordingly. The job takes far longer than expected, a five-figure number of rows come back in `failedResults`, and the failures are validation rules that have nothing to do with record types — rules that fire on every save and that these records have not been through since they were created years ago.

**When it occurs:** Every bulk record type reassignment. Bulk API 2.0's `update` is an ordinary update, so each row goes through the documented save order: before-save record-triggered flows (step 3), before triggers (4), **all custom validation rules** (5), duplicate rules (6 — a `block` action stops the row and no after trigger runs), after triggers (8), assignment rules (9), auto-response rules (10), workflow rules (11), escalation rules (12), and after-save flows (14). Validation rules written as `ISPICKVAL(RecordType.DeveloperName, ...)` guards for the *target* type now apply to records that were never authored against them.

**How to avoid:** Before the run, inventory the object's active validation rules, before-save flows, duplicate rules, and assignment rules, and decide per item whether it should fire for a migration row. Run a representative sample first — a few thousand rows in a full-copy sandbox — and read `failedResults`, not just the success count. If a rule must not fire, gate it on a migration flag rather than deactivating it for the whole org during the window. `admin/record-types-and-page-layouts` gotchas #1 covers the separate picklist-blanking risk on the same operation; do the value union first, then this analysis, then the load.

---

## Gotcha 8: Deactivating N Record Types Shrinks Every Profile File in One Commit

**What happens:** A consolidation deactivates six record types across three objects. The next retrieve produces a pull request that removes several hundred lines from twenty-odd profile and permission set files. Nothing in the diff says "these were deactivated" — the blocks are simply absent. A reviewer reads it as a mass revocation of access, or worse, approves it as noise because profile diffs are already assumed to be unreliable.

**When it occurs:** The first retrieve after any deactivation, and it compounds with the number of personas. `Profile.recordTypeVisibilities` "isn't retrieved or deployed for inactive record types" in API 29.0 and later; `PermissionSet.recordTypeVisibilities` "is never retrieved or deployed for inactive record types". At one record type the diff is a curiosity. At six record types × twenty carriers it is 120 vanished blocks landing as a single reviewable unit, and it is genuinely indistinguishable from someone having revoked them.

**How to avoid:** Commit the visibility snapshot *before* the deactivation deploy and reference that commit in the deactivation PR, so the review has something to diff against. Split the consolidation into the three deploys listed in `metadata-examples.md` §7 rather than one — the deactivation deploy then contains only deactivations and their consequences, and its size is expected rather than alarming. `admin/record-types-and-page-layouts` gotchas #8 has the single-record-type mechanics; this is what it looks like when the count is not one.

---

## Gotcha 9: `RecordType` Has No Wildcard, So a Wildcard Audit Reports a Clean Org

**What happens:** An architect builds an org-wide record type audit on a manifest using `<members>*</members>` for `CustomObject`, `Profile`, and `RecordType`. The retrieve succeeds, the objects and layouts arrive, and the audit reports zero record types found across the org. The conclusion drawn is that the org has no record type sprawl. It has 90 of them.

**When it occurs:** Any manifest-driven audit or backup of an org whose record type inventory is not already known. The guide states it flatly under `RecordType`: "This metadata type doesn't support the wildcard character `*` (asterisk) in the package.xml manifest file." The retrieve does not warn, error, or partially succeed — the type is simply not in the result, and every downstream count is zero.

**How to avoid:** Never let a record type manifest be hand-written or wildcarded. Generate the member list from `SELECT SobjectType, DeveloperName FROM RecordType` and fail the audit if the generated member count is zero — a zero here is far more likely to be this bug than an org with no record types. `metadata-examples.md` §6 has the generator. The same reasoning applies to any tool that claims to have "retrieved everything": check that its `RecordType` members are enumerated, not starred.
