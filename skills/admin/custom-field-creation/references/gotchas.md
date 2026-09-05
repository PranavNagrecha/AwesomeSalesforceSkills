# Gotchas — Custom Field Creation

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: New Fields Are Hidden for All Profiles in Enterprise and Unlimited Editions

**What happens:** After creating a custom field in an Enterprise or Unlimited edition org, users report they cannot see the field even after it was added to the page layout. The field appears on the layout canvas in Setup, but is invisible on the record page.

**When it occurs:** In Enterprise, Performance, and Unlimited editions, newly created custom fields default to no FLS access for all profiles. The field exists and holds data written via API, but the UI respects FLS — users with no FLS access see nothing. This includes System Administrators in some configurations if the "Modify All Data" permission is not granting implicit field access.

**How to avoid:** Always complete the "Establish Field-Level Security" step during field creation. After saving, also verify by navigating to Setup → Object Manager → [Object] → Fields & Relationships → [Field] → Set Field-Level Security. Confirm Read (and Edit if needed) is checked for every relevant profile. For permission-set-based orgs, also check the permission set's object settings for the field.

---

## Gotcha 2: Required Fields Break Existing Records and Integrations

**What happens:** An admin marks a previously optional custom field as Required at the field definition level. Shortly after, integration jobs start failing with errors like "REQUIRED_FIELD_MISSING: Required fields are missing: [Field_Name__c]". API clients that were not updated to supply the field cannot create or update records. Triggers that do not explicitly set the field also fail.

**When it occurs:** Whenever a field is made Required (not just Required on a page layout — Required at the field definition level), the Salesforce API enforces the constraint on all DML operations, including API calls, triggers, and bulk data jobs. If existing records have blank values in the field, those records are technically invalid until they have a value — though existing records are not retroactively rejected, any update to such a record via any channel that does not include the field will fail if the record does not already have a value.

**How to avoid:** Before marking a field Required, run a SOQL query to identify records with blank values: `SELECT Id FROM Object__c WHERE Field__c = null`. Backfill those records with a default value first. Coordinate with integration owners to update their payloads. Consider using a validation rule with a custom bypass (Custom Permission or Profile check) instead of the field-level Required setting — this gives more control over enforcement scope.

---

## Gotcha 3: Dynamic Forms Bypasses Classic Page Layouts for Field Display

**What happens:** A field is added to the classic page layout and FLS is correctly set, but users on Lightning experience still cannot see the field on the record page.

**When it occurs:** When a Lightning record page uses Dynamic Forms (configured in Lightning App Builder by clicking "Upgrade Now" on the layout section), the classic page layout is no longer used for field display. Dynamic Forms replaces the layout's field section with a Dynamic Form component where fields are added individually. Any field on the classic page layout that is not also added to the Dynamic Form component is invisible to Lightning users seeing that page.

**How to avoid:** Before adding a field to a classic page layout, check whether any Lightning record pages for that object use Dynamic Forms. In App Builder, look for a "Fields" component on the record page — if it says "Dynamic Form" rather than "Record Detail", the page is using Dynamic Forms. Add the field to the Dynamic Form component directly. Dynamic Forms also support field-level visibility rules (show/hide based on record values), which is a capability classic layouts do not have.

---

## Gotcha 4: Roll-Up Summary Fields Are Only Available on Master-Detail Relationships

**What happens:** An admin creates a Lookup Relationship between a child and parent object, then tries to create a Roll-Up Summary field on the parent. The Roll-Up Summary field type is greyed out or not shown in the field type selection.

**When it occurs:** Roll-Up Summary fields are exclusively supported on Master-Detail relationship parents. Lookup Relationships do not support this field type, regardless of how the objects are designed. If you already have a Lookup relationship and need roll-ups, you must convert it to Master-Detail (only possible if no child records have a blank parent value).

**How to avoid:** Decide before creating the relationship whether roll-up functionality will be needed. If aggregate totals, counts, min values, or max values from child records are needed on the parent, use Master-Detail from the start. Converting later requires verifying no child records have a null parent, and it makes the parent field required for all future child records.

---

## Gotcha 5: Classic Encrypted Text Fields Cannot Be Used in Formulas, Reports, or Workflow Criteria

**What happens:** An admin creates an Encrypted Text field (Classic Encryption, not Shield Platform Encryption) to store sensitive data such as a partial SSN or internal code. When they try to reference the field in a formula field, report filter, or workflow rule, they find the field is not available as an option.

**When it occurs:** Salesforce Classic Encryption uses a platform-managed symmetric key to mask field values. As a result, encrypted fields cannot be indexed, cannot be used in formula fields, cannot appear in workflow or process criteria, cannot be searched using SOQL WHERE clauses, and cannot be filtered in reports. The encryption model is not compatible with these platform features.

**How to avoid:** Before choosing Classic Encrypted Text, confirm whether the use case actually requires encryption or just masking. If the field needs to be searchable, filterable, or used in formulas, Classic Encryption is the wrong choice. For true encryption with broader usability, evaluate Shield Platform Encryption, which encrypts at rest while preserving more platform functionality (though some limits still apply). For simple masking without platform limitations, a validation rule or a standard Text field may be sufficient.

---

## Gotcha 6: A Lossy Field Type Conversion Deletes List Views and Silently Drops the Lead Conversion Mapping

**What happens:** An admin converts an existing field — Text to Picklist, or anything to Number, Percent, or Currency — after exporting the column so the data can be restored. The data restore is planned; the collateral damage is not. List views built on that field are gone from the object, assignment and escalation rules that referenced it no longer behave as designed, and if the field was mapped for lead conversion the mapping has disappeared without any warning at conversion time.

**When it occurs:** Salesforce's guidance is to only convert custom fields for which no data exists, or you risk losing your data. When that data loss happens, "any list view based on the custom field will be deleted, and assignment and escalation rules may be affected." The lead mapping is a separate, unconditional consequence: "If you change the data type of any custom field that is used for lead conversion, that lead field mapping will be deleted." Note the shape of that rule — the conversion is *not* blocked, the mapping is simply removed. A field set as an External ID also stops acting as one if the new type is anything other than Text, Number, or Email. Only a narrow set of conversions is refused rather than degraded: a field referenced in Apex or on a Visualforce page cannot change type at all, and Formula and Classic Encrypted Text fields convert in neither direction.

**How to avoid:** Treat a type change as a migration, not an edit. Before converting: export the column; inventory the object's list views and record which ones reference the field so they can be rebuilt; check Setup → Object Manager → Lead → Fields & Relationships → Map Lead Fields for a mapping on this field and plan to recreate it; grep Apex and Visualforce for the API name, because the conversion will be rejected until those references are removed. Two length traps: Long Text Area → Email, Phone, Text, Text Area, or URL truncates every value to its first 255 characters, and Auto Number caps at 30 characters, so shorten any record over 30 characters before converting Text → Auto Number. If any of this is unacceptable, create a new field of the correct type, migrate the data, and deprecate the old field instead.

---

## Gotcha 7: Retrieving One Field Rewrites Every Profile and Permission Set in the Same Package

**What happens:** An admin retrieves a single new field to add it to source control. The `git diff` shows the one `.field-meta.xml` they expected — and also several hundred changed lines across `profiles/` and `permissionsets/`. Reviewed carelessly and merged, the next deploy strips FLS from fields nobody touched.

**When it occurs:** Every time. The Metadata API Developer Guide states it as a property of the type: "Retrieving a component of this metadata type in a project makes the component appear in any `Profile` and `PermissionSet` components that are retrieved in the same package" (api_meta.txt:43251–43252). Two related behaviours make the diff harder to read than it looks. First, a field with `required` `true` will not appear at all, because "in API version 30.0 and later, permissions for required fields can't be retrieved or deployed" (api_meta.txt:95020–95021) — write a `fieldPermissions` entry for a required field and the deploy fails. Second, an absent row is not evidence of no access: "if the View All Fields object permission is enabled for an object in the permission set, the individual fields aren't returned under `fieldPermissions`" (api_meta.txt:95027–95029).

**How to avoid:** Retrieve fields and permission sets in the same deliberate operation, then read the profile and permission-set diff line by line before staging it — that diff *is* the FLS change, not noise around it. Keep required fields out of `fieldPermissions` entirely. When auditing who can read a field, check `objectPermissions` → `viewAllFields` before concluding from an empty `fieldPermissions` list. See `references/metadata-examples.md` §9 for the deployable shape.

---

## Gotcha 8: A Lookup With No `deleteConstraint` Silently Blanks Itself When the Parent Is Deleted

**What happens:** Someone deletes a Contact. Weeks later an invoice run produces records with no billing contact, or a Flow that assumed the lookup was populated takes its else-branch on thousands of records. No error was raised at delete time and nothing in the audit trail points at the lookup.

**When it occurs:** Whenever `deleteConstraint` is omitted from a `Lookup` field. The default is not "block" — the guide lists three values and names the default: `Cascade` "deletes the lookup record as well as associated lookup fields"; `Restrict` "prevents the record from being deleted if it's in a lookup relationship"; `SetNull` "this value is the default. If the lookup record is deleted, the lookup field is cleared" (api_meta.txt:43348–43356). Field XML generated by an LLM or by the Setup UI's default path routinely omits the element, so the org inherits `SetNull` by accident rather than by decision.

**How to avoid:** Write `deleteConstraint` explicitly on every `Lookup` field, including when `SetNull` is what you want — the element's presence is the record that somebody chose. Pick `Restrict` when downstream automation cannot cope with a blank parent, and `Cascade` only when the child has no meaning without the parent (`Cascade` on a Lookup gives you delete propagation without the sharing and roll-up commitments of a Master-Detail). The skill's checker flags lookups with no `deleteConstraint`.

---

## Gotcha 9: An External ID That Is Not Unique Fails Upserts at Runtime, Not at Deploy

**What happens:** A nightly integration that has been upserting cleanly for months starts returning `300` on a handful of records. Those records are neither created nor updated, so the source system believes the sync succeeded while Salesforce quietly diverges.

**When it occurs:** `externalId` and `unique` are two independent booleans on `CustomField` (api_meta.txt:43402–43405, 43702). Setting `externalId` `true` alone makes the field a legal upsert key without preventing duplicate values in it. The REST API's documented behaviour: "If the external ID is matched multiple times, then a `300` error is reported, and the record isn't created or updated" (api_rest.txt:2963–2966), where `300` is "the value returned when an external ID exists in more than one record" (api_rest.txt:1134–1135). Bulk API 2.0 has the same dependency — "upserting records requires an external ID field on the object involved in the job. Bulk API 2.0 uses the external ID field to determine whether a record is used to update an existing record or create a record" (api_asynch.txt:889–891). The duplicate usually enters through a manual edit or a one-off data load months after the field was created, so nothing correlates the failure with the field definition.

**How to avoid:** Set `unique` `true` on every field marked `externalId` unless you can state why duplicates are acceptable. Decide `caseSensitive` in the same breath (api_meta.txt:43328–43333): case-insensitive uniqueness will reject `ACME01` when `acme01` exists, which is correct for a case-folding source system and wrong for one that treats them as different customers. Note the second effect of the flag — "a custom field is indexed if its External ID field is selected" (api_asynch.txt:1509–1510), which is what makes `Parent__r.External_Code__c` legal as a Bulk API CSV column header (api_asynch.txt:1503–1522). The skill's checker warns on `externalId` without `unique`.

---

## Gotcha 10: On a Junction Object, `relationshipOrder` Decides Ownership — and Getting It Wrong Is Invisible Until a Delete

**What happens:** A junction object is built with two master-detail fields. Records look fine for months. Then someone deletes a record on what they assumed was the secondary parent and the junction rows vanish, or a sharing review finds junction rows owned by the wrong user with the wrong page look and feel.

**When it occurs:** The guide is explicit about how much rides on this integer: "A junction object has two master-detail relationships… Junction objects must define one parent object as primary (`0`), the other as secondary (`1`). The definition of primary or secondary affects delete behavior and inheritance of look and feel, and record ownership for junction objects. `0` or `1` are the only valid values, and `0` is always the value for objects that aren't junction objects" (api_meta.txt:43582–43592). Because both fields deploy and both relationships work, an inverted assignment produces a working org with the wrong semantics. Compounding it, `reparentableMasterDetail` "indicates whether the child records in a master-detail relationship on a custom object can be reparented to different parent records. The default value is `false`" (api_meta.txt:43593–43597) — so once a row is attached to the wrong parent, the only fix is delete and recreate, which loses the Id and everything referencing it.

**How to avoid:** Before writing either master-detail field, answer one question out loud: which parent should own these rows and lend them its sharing? That parent is `relationshipOrder` `0`. Write the element on both fields even though `0` is the default for non-junctions, so the pairing is auditable in one diff. Set `reparentableMasterDetail` `true` unless the business genuinely forbids moving a child — the default costs you the ability to correct a data-entry mistake. Relationship *design* is `admin/lookup-and-relationship-design`; this is about the two elements the XML forgets.

---

## Gotcha 11: `writeRequiresMasterRead` Defaults to the Restrictive Setting, and on a Junction the Stricter Parent Wins

**What happens:** Users who can see a parent record cannot create child records under it and get an insufficient-privileges error. The admin grants more object permissions on the child, which changes nothing, because the block is coming from the parent's sharing.

**When it occurs:** The element is on the master-detail field, not on the child object's permissions. Its documented semantics: `true` "allows users with Read access to the primary record permission to create, edit, or delete child records. This setting makes sharing less restrictive"; `false` "allows users with Read/Write access to the primary record permission to create, edit, or delete child records. This setting is more restrictive than `true`, and is the default value" (api_meta.txt:43725–43742). On a junction object there is a second trap in the same paragraph: "For junction objects, the most restrictive access from the two parents is enforced. For example, if you set to `true` on both master-detail fields, but users have Read access to one primary record and Read/Write access to the other primary record, users aren't able to create, edit, or delete child records" (api_meta.txt:43738–43742). Flipping the flag on one of the two fields therefore has no observable effect and looks like the setting is broken.

**How to avoid:** When the symptom is "user can see the parent but cannot add children", check the master-detail field's `writeRequiresMasterRead` before touching object permissions or sharing rules. On a junction, evaluate both master-detail fields together and confirm the user's access to *both* parents — the effective answer is the minimum of the two. Record the choice in the field's `description`, because nothing in the child object's Setup page reveals it.

---

## Gotcha 12: `CustomField` Takes No Wildcard, So a `*` Manifest Ships Zero Fields Without Failing

**What happens:** A release manifest lists `<members>*</members>` under `<name>CustomField</name>`. The retrieve or deploy completes successfully and the fields are simply not in it. The gap is discovered in the target org, after the release window.

**When it occurs:** The guide states it in one line at the end of the `CustomField` section: "This metadata type doesn't support the wildcard character `*` (asterisk) in the package.xml manifest file" (api_meta.txt:43983–43985). Most metadata types on either side of it in the same document *do* support the wildcard — `CustomObject` immediately above it does (api_meta.txt:43200–43201) — so the habit transfers and the exception does not announce itself.

**How to avoid:** Enumerate every field as `Object.Field__c`, exactly as the guide's own manifest example does (api_meta.txt:43261–43266). When you want every field on an object, request the `CustomObject` instead: "when you retrieve a custom or standard object, you return everything associated with the object, except for standard fields that aren't customizable" (api_meta.txt:43256–43257) — which also pulls layouts, record types, and validation rules, so scope the release accordingly. Diff the retrieved tree against the manifest before packaging; a manifest that names nine fields should produce nine files.

---

## Gotcha 13: `trackHistory`, `trackFeedHistory`, and `trackTrending` Fail to Deploy Unless the Object Was Enabled First

**What happens:** A field deploys cleanly to a scratch org and fails in the release pipeline against a sandbox or production, with an error about history tracking. Nothing in the field XML changed between the two runs.

**When it occurs:** These three booleans have an object-level prerequisite that lives in a different file. "To set `trackHistory` to `true`, the `enableHistory` field on the associated standard or custom object must also be `true`" (api_meta.txt:43675–43683). The Chatter equivalent: "to set this field to `true`, the `enableFeeds` field on the associated `CustomObject` must also be `true`" (api_meta.txt:43668–43674). `trackTrending` inverts the dependency — "an object is enabled for historical trending if this attribute is `true` for at least one field" (api_meta.txt:43684–43692) — so the first field to set it changes an object-level setting as a side effect. A scratch org built from a definition file that already enables history hides the problem; the target org that never had it enabled does not.

**How to avoid:** When adding a tracked field to an object that has never had tracking, put the object change in the same deploy — a `CustomObject` component with `enableHistory` `true`. Order the manifest so the object precedes the fields. Field history retention and querying is `admin/system-field-behavior-and-audit`; the point here is only that the field XML alone is not deployable. Also note the reverse asymmetry on `trackTrending`: setting it on one field quietly enables historical trending for the whole object, which is not a change most reviewers expect from a field-level diff.

---

## Gotcha 14: `precision` Is the Total Digit Count, Not the Digits Left of the Decimal Point

**What happens:** An admin designs a Number field in Setup as "Length 18, Decimal Places 2", then hand-writes or generates the XML as `<precision>18</precision><scale>2</scale>`. The deployed field holds 16 integer digits, not 18. A data load of values with 17 or 18 digits left of the point fails, or worse, the field was meant to hold a 16-digit account number and now silently cannot.

**When it occurs:** The two guide definitions use the same example number and settle it: "Precision is the number of digits in a number. For example, the number `256.99` has a precision value of `5`" (api_meta.txt:43563–43566) and "Scale is the number of digits to the right of the decimal point in a number. For example, the number `256.99` has a scale of `2`" (api_meta.txt:43610–43612). `256.99` is precision 5 and scale 2, so the integer part is precision minus scale. The Setup UI asks the question the other way round — its "Length" is the integer digits — so transcribing the two Setup numbers straight into the XML shrinks the field by `scale` digits every time. It deploys without complaint.

**How to avoid:** Convert deliberately: `precision` = Setup Length + Setup Decimal Places. Verify after deploy rather than trusting the XML — `sf sobject describe` returns `precision` and `scale` as the platform stored them, and `Schema.DescribeFieldResult.getPrecision()` / `getScale()` do the same from Apex (apexrefguide.txt:190862–190968). One related note the guide adds: a `Number` custom field is "internally represented as a field of type double. Setting the scale of the Number field to `0` gives you a double that behaves like an int" (api_meta.txt:45766–45768) — there is no true integer column behind a Number field.
