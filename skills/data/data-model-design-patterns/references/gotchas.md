# Gotchas — Data Model Design Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Master-Detail Cascade Delete Is Automatic, and One Undeletable Child Blocks It

**What happens:** Deleting a master record deletes its detail records, and detail-of-detail records below them, with no prompt about the children. In the other direction, a parent delete fails outright when any one child can't be deleted.

**When it occurs:** The Object Reference: "When a record of the master object is deleted, its related detail records are also deleted." The Apex Developer Guide: deleting a parent deletes its children automatically "as long as each child record can be deleted," and if a child isn't deletable or is in use, the delete on the parent fails. Deleted records go to the Recycle Bin for 15 days; when purging, `Database.emptyRecycleBin` takes only the top-level record's Id and removes the related records with it.

**How to avoid:**
- Confirm with the business that cascade delete is right in every scenario before choosing master-detail.
- For a junction whose rows should survive one parent's deletion, use a lookup on that side.
- Add a before-delete check on the master that counts detail rows and blocks deletes above a threshold, as a safety gate for bulk deletes.
- Test restore in a sandbox (undelete the master within 15 days) before relying on it as a recovery plan.

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

**What happens:** Adding a lookup filter to a relationship field (to restrict which parent records appear in the lookup search) does not create a database index on the filtered field. If the filter references a non-indexed field on the parent object, the lookup search dialog may perform slowly when the parent object has large record volumes. UNVERIFIED (2026-10-19): lookup-filter query behaviour is not described in the local PDF corpus; treat the slowdown as a hypothesis to confirm with a query plan.

**When it occurs:** Lookup filters that reference custom non-indexed fields on large parent objects (typically 100k+ records). The filter logic is evaluated at query time without index support, causing visible lag in the lookup search modal.

**How to avoid:**
- Prefer lookup filters that reference indexed fields on the parent (Id, Name, RecordTypeId, OwnerId, or fields with custom indexes).
- If filtering on a custom non-indexed field is a business requirement and the parent object is large, file a Salesforce Support case to request a custom index on that field.

---

## Gotcha 5: External ID Indexes the Key; Unique and Case Sensitivity Are Separate Settings

**What happens:** An integration sends `ORDER-001` and `order-001` as different orders and Salesforce treats them as one, or the reverse; or duplicates slip in because External ID was assumed to be unique.

**When it occurs:** In `CustomField` metadata, `externalId`, `unique`, and `caseSensitive` are separate booleans; External ID is available on Auto Number, Email, Number, and Text fields. Upserts whose key matches more than one record fail with a 300 error, which shows duplicates can exist under External ID alone.

**How to avoid:**
- Set `unique` when the key must be unique, and set `caseSensitive` deliberately to match the source system's semantics.
- Normalize case in the integration layer when the source treats keys case-insensitively.
- For purely numeric keys, consider a Number field.

---

## Gotcha 6: Skinny Tables Only Help Queries That Use Nothing Outside Them

**What happens:** A skinny table is provisioned, and the report that motivated it stays slow because it also reads one field that isn't in the skinny table.

**When it occurs:** The LDV guide: skinny tables are kept in sync with their source tables, and read-only operations that reference only fields in the skinny table skip the join between the standard and custom field tables. They hold at most 200 columns, can't include fields from other objects, can be created on custom objects and on Account, Contact, Opportunity, Lead, and Case, and are copied only to Full sandboxes. Adding a field to the report means asking Support to change the skinny table.

**How to avoid:**
- Design report field sets so heavy reports stay inside the skinny table's fields.
- Route any change to those reports through a Support request to update the skinny table definition.
- Test in a Full sandbox; other sandbox types don't receive skinny tables.

---

## Gotcha 7: Lookup Delete Behaviour Is a Metadata Setting — Check Cascade Before Designing on It

**What happens:** A design says "set the lookup to delete its children," and the admin finds the option isn't available, or that its consequences for access weren't reviewed.

**When it occurs:** The Metadata API `deleteConstraint` on a lookup field accepts `SetNull` ("This value is the default. If the lookup record is deleted, the lookup field is cleared"), `Restrict` ("Prevents the record from being deleted if it's in a lookup relationship"), and `Cascade` ("Deletes the lookup record as well as associated lookup fields"). Whether `Cascade` can be chosen in a given org, and what it means for users who can't see the child records, is not described in the Metadata API guide.

**How to avoid:**
- Ask the org's admin whether lookup `Cascade` is available before putting it in a design, and review its effect on access with security.
- Prefer master-detail when the dependency is genuine, or delete children from before-delete automation whose sharing mode you choose explicitly (an Apex class declared `with sharing`, for example).
- Use `Restrict` as the safe middle ground: it blocks the parent delete instead of removing children.

---

## Gotcha 8: Eight Standard Objects Can Never Be the Master, and No Standard Object Can Be the Detail of a Custom Object

**What happens:** The Object Reference states: "you can't create a master-detail relationship where these standard objects are the primary object. BusinessHours, Idea, Lead, OrderItem, PriceBook2, Product2, QuoteLineItem, User". Separately: "the standard object can't be on the detail side of a relationship with a custom object." Those objects are simply not offered in the Related To list once you pick Master-Detail Relationship in the field wizard. The permanent consequence is that no native rollup summary field can ever exist on any of those eight objects.

**When it occurs:** Most often in junction design — the canonical broken recipe is `Account_Product__c` with a master-detail to Account plus a master-detail to Product2. The second leg is impossible. It also surfaces on requests like "roll up open pipeline onto the Lead", "count assigned cases per User", or "sum line quantities onto PriceBook2".

**How to avoid:**
- Check the blocklist before promising a rollup. If either parent is on it, that leg must be a lookup — and the rollup on that parent must come from a record-triggered Flow, an Apex trigger, or DLRS writing to a plain Number field.
- For a junction where one side is blocked, use master-detail to the eligible (usually custom) parent and lookup to the blocked one. The junction still inherits sharing and cascade delete from the master side, and rollups still work on that side.
- Never propose converting a standard object into the detail of a custom object; the platform offers no path for it, so a "make Contact a detail of Household__c" design has to be rewritten as a lookup, with record access handled by sharing rules or programmatically created Share records instead of inherited from the parent.

---

## Gotcha 9: Funnel or Wizard State in a Long Text Area JSON Is Invisible

**What happens:** Navigation status (`not started` / `in progress` / `completed` per section) is stored as one JSON string in a Long Text Area. That field cannot be filtered in SOQL, grouped in reports, referenced by formulas, or rolled up. Operations cannot answer "how many drafts are stuck on Income" **while the record is still alive**. After a purge, the JSON is gone.

**When it occurs:** Multi-step Experience Cloud / OmniScript applications that treat Salesforce as intake, not system of record.

**How to avoid:**
- Custom metadata can declare controlling-question → reopen-dependent-section rules. That is the reusable navigation idea — do not put the **instance** state in an LTA.
- Prefer child rows or Platform Events: section, timestamp, status, **no PII**. Measurement then survives both the wizard and the purge.
- A single "last visited section" text field is last-write-wins, not a funnel.

---

## Gotcha 10: Process on the Wrong Standard Object

**What happens:** The pipeline lives on **Account** (or Case, or Campaign) because Opportunity was skipped. Stage, amount, close date, and "deal team" are custom fields on a party object. Reports, forecasts, Path, and every sales skill assume Opportunity. Integrations and AppExchange expect Opportunity.

**When it occurs:** PE / search-fund / professional-services orgs that "didn't need Opportunity." Also: using Contact as the employee record.

**How to avoid:** If the noun is a deal, use Opportunity (or a custom object whose API name and report types say deal). Account is a party. Retrofitting Opportunity later means migrating stage history that never existed. Document the deviation in an ADR; do not pretend Account *is* Opportunity in reports.

---

## Gotcha 11: Lookup-Driven Junction Create Without an Existence Check

**What happens:** A Flow sees Lookup A and Lookup B populated and **Creates** a junction row every time. No Get Records for the pair. Save-edit-save duplicates the junction. Reports count relationships twice.

**When it occurs:** After-save Flows that "link the related company / contact / campaign when the lookup is filled."

**How to avoid:** Get existing junction on `(ParentA, ParentB)` (or an External Id on the pair) before Create. Prefer a unique matching rule / duplicate rule on the junction. Idempotent create, not fire-and-forget.
