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

---

## Gotcha 7: Cascade Delete on a Lookup Is Not a Field-Wizard Option — It Needs a Support Case and Bypasses Sharing

**What happens:** The Metadata API `deleteConstraint` on a lookup field accepts three values: `SetNull` ("This value is the default. If the lookup record is deleted, the lookup field is cleared"), `Restrict` ("Prevents the record from being deleted if it's in a lookup relationship"), and `Cascade` ("Deletes the lookup record as well as associated lookup fields"). The Setup field wizard exposes only the first two. `Cascade` is gated on an org-level feature — "cascade delete on custom lookup relationships" — which is disabled by default. Salesforce states: "A cascade-delete bypasses security and sharing settings, which means users can delete records when the target lookup record is deleted even if they don't have access to the records." It is also unavailable entirely for lookup relationships to standard objects.

**When it occurs:** Whenever children must disappear with the parent but master-detail is off the table — the 2-MDR limit is already spent, the parent must stay optional, or the parent is a standard object that cannot be a master (see Gotcha 8). The design doc says "set the lookup delete behavior to cascade" and the admin discovers there is no such radio button.

**How to avoid:**
- Do not commit to cascade-on-lookup in a design. Enabling it requires a System Administrator to file an Activations request with Salesforce Support and explicitly acknowledge the security bypass; there is no self-serve path.
- Prefer master-detail when the dependency is genuine, or delete children explicitly from a before-delete Apex trigger or record-triggered Flow. Unlike cascade, that path lives in the org's metadata and its execution context is yours to choose — but it does not respect sharing by default either: a trigger runs in system mode unless its handler class is declared `with sharing`, and a record-triggered flow defaults to system context without sharing.
- Use `Restrict` as the safe self-serve middle ground: it blocks the parent delete instead of silently removing children.
- If the feature is already on in the org, treat every `deleteConstraint: Cascade` lookup as an audit finding — Salesforce notes that when the parent of a lookup relationship is deleted, field history tracking on the child does not record the deletion, so the child's history shows no sign of it.

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
