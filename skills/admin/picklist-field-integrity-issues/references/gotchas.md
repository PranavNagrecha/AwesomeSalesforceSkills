# Gotchas — Picklist Field Integrity Issues

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Unrestricted Picklists Silently Accept Any Value via API

**What happens:** When a record is created or updated via REST API, Bulk API, or Data Loader with a value not in the picklist definition, Salesforce saves the record without error. The unknown value appears in the field and may even be added as an inactive entry in the picklist metadata.

**When it occurs:** Any time data enters through a non-UI channel (API, Data Loader, Bulk API, middleware, Apex DML) on an unrestricted picklist field.

**How to avoid:** Convert critical picklist fields to Restricted. For fields that cannot be restricted (e.g., legacy integrations depend on dynamic values), add a before-trigger or validation rule that checks incoming values against `Schema.DescribeFieldResult.getPicklistValues()`.

---

## Gotcha 2: Dependent Picklist Enforcement Is UI-Only

**What happens:** The controlling-dependent picklist matrix is enforced only in the Lightning and Classic UI. API, Data Loader, Bulk API, Apex DML, and Flows running in system context completely bypass the dependent filtering. Records can be saved with any combination of controlling and dependent values.

**When it occurs:** Any non-UI data entry channel. This is especially dangerous during data migrations and integration loads where thousands of records may have invalid dependent values.

**How to avoid:** Deploy a validation rule or Apex before-trigger that explicitly validates the controlling-dependent combination. The UI filtering is a convenience feature, not a data integrity mechanism.

---

## Gotcha 3: Restricted Picklist Known Issue — Inactive Values via Metadata Deploy

**What happens:** There is a known Salesforce issue where inactive picklist values for restricted picklists can be inserted through certain Metadata API deploy paths. The restriction is bypassed when the value exists in the metadata XML but is marked inactive.

**When it occurs:** During metadata deployments that include picklist value definitions with `<isActive>false</isActive>` entries. The platform may accept records with these inactive values via API despite the field being restricted.

**How to avoid:** After any metadata deployment that touches picklist definitions, run an audit query to verify no inactive values have been written to records. Monitor the Salesforce Known Issues site for updates on this behavior.

---

## Gotcha 4: Record Type Picklist Mapping Is Not Automatic for New Values

**What happens:** Adding a new value to a picklist (or Global Value Set) does NOT automatically add it to existing record types. Only brand-new record types receive all master picklist values. Users on existing record types cannot see the new value until an admin explicitly maps it.

**When it occurs:** Every time a picklist value is added to a field that has record types. This is the most common source of "why can't users see the new value?" support tickets.

**How to avoid:** Include record type picklist mapping as a mandatory step in every picklist change deployment checklist. Use the Metadata API `RecordType` XML to audit which values are mapped to which record types.

---

## Gotcha 5: Picklist Label Rename Does Not Update Stored Data

**What happens:** Renaming a picklist value's label (display name) does not change the API name stored on existing records. If reports, formulas, or automation reference the new label text, they find zero matches because the underlying stored value is the original API name.

**When it occurs:** When an admin renames a picklist value label in Setup. The stored API value on records remains the original text (for fields created before API names were separate from labels) or the original API name.

**How to avoid:** When renaming is needed, either: (a) use the Replace functionality to create a new value, migrate records, then deactivate the old value, or (b) verify that all formulas, reports, and automation reference the API name, not the label.
