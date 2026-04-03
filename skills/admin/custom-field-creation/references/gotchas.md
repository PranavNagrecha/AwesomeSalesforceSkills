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
