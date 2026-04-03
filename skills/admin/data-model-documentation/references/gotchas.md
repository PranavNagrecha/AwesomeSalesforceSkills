# Gotchas — Data Model Documentation

Non-obvious Salesforce platform behaviors that cause real problems when documenting the data model.

## Gotcha 1: Standard Object Fields Are Not Returned by CustomObject Metadata Retrieval

**What happens:** When you retrieve `CustomObject:Account` via Metadata API or sf CLI, the returned XML contains only the customizations made to Account — custom fields, validation rules, search layouts, and similar. Standard fields like `Name`, `Phone`, `BillingAddress`, `OwnerId`, and `CreatedDate` do not appear in the retrieved metadata XML. This causes admins to create a field inventory that appears to show Account has only 12 fields when it actually has 60+.

**When it occurs:** Any time you build a field inventory from a Metadata API retrieve without cross-referencing the Object Reference documentation for standard fields.

**How to avoid:** For each standard object in scope, manually add the standard fields from the Salesforce Object Reference (developer.salesforce.com/docs/atlas.en-us.object_reference.meta). The Object Reference lists every field on every standard object including type, label, and behavior. Document standard fields in a separate section of the inventory marked "Salesforce-managed — do not modify API names."

---

## Gotcha 2: Field-Level Security Lives in Profile/PermissionSet Metadata, Not on the Field

**What happens:** A practitioner documents a field as "sensitive — restricted to Finance team" based on what they were told, but the field inventory does not capture which profiles or permission sets actually enforce that restriction. When the org is audited or a new profile is created, the FLS restriction is invisible to anyone reading the field documentation alone.

**When it occurs:** Any time FLS documentation is written from memory or verbal confirmation rather than from Profile or PermissionSet metadata.

**How to avoid:** To document FLS accurately, retrieve Profile or PermissionSet metadata and look for `<fieldPermissions>` elements that reference the field:
```xml
<fieldPermissions>
  <editable>false</editable>
  <field>Account.ERP_Customer_ID__c</field>
  <readable>true</readable>
</fieldPermissions>
```
List in the field inventory which permission sets grant read access and which grant edit access. This requires a separate retrieve targeting the Profile or PermissionSet metadata types — it cannot be inferred from the object metadata alone.

---

## Gotcha 3: Schema Builder Silently Omits Polymorphic Lookups

**What happens:** Some standard fields in Salesforce are polymorphic lookups — they can point to more than one object type. The most common examples are `Task.WhoId` (Contact or Lead), `Task.WhatId` (Account, Opportunity, Case, etc.), and `Event.WhoId`. Schema Builder displays these fields as single relationship lines to only one of the target objects, or omits them entirely. An ER diagram built solely from Schema Builder will misrepresent how Activity data relates to the rest of the model.

**When it occurs:** Any time Task, Event, or other activity objects are included in a relationship diagram built only from Schema Builder.

**How to avoid:** Document polymorphic lookups separately. Note in the ER diagram that `WhoId` and `WhatId` are multi-target lookups and list their valid target objects from the Object Reference. These relationships cannot be fully represented with a standard ER notation line — use a note annotation explaining the polymorphic behavior.

---

## Gotcha 4: Object Manager Field List Does Not Export Natively

**What happens:** Admins expect to find a "Export to CSV" button in Setup → Object Manager → Fields & Relationships. No such button exists. Attempting to manually copy-paste the field list from the UI into a spreadsheet produces incomplete results (pagination limits, missing metadata properties).

**When it occurs:** Any time someone tries to create a field inventory using only the Setup UI.

**How to avoid:** Use the Metadata API or the Data Export approach via the `EntityDefinition` and `FieldDefinition` Tooling API objects. The Tooling API's `FieldDefinition` SOQL returns field metadata without a full metadata retrieve:
```
SELECT QualifiedApiName, Label, DataType, IsRequired, Description 
FROM FieldDefinition 
WHERE EntityDefinition.QualifiedApiName = 'Account'
```
This query runs in Developer Console (Query Editor → Use Tooling API checkbox) or via the Tooling API REST endpoint, and the results can be exported to CSV.
