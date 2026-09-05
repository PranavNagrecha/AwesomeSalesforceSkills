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

---

## Gotcha 5: The Inventory You Get Depends on Who Runs It

**What happens:** Two admins run the same describe-based inventory against the same org an hour apart and
produce field counts that differ by dozens. Neither made a mistake. `Schema.DescribeFieldResult` exposes
`isAccessible()` — "Returns true if the current user can see this field, false otherwise" (Apex Reference
Guide, DescribeFieldResult Methods, apexrefguide.txt L190604) — and the object-level
`DescribeSObjectResult.isAccessible()` says the same for the object (L192206). A describe run under a
user with restricted field-level security returns a smaller picture, silently, with no error and no
indication that anything was withheld. The same is true of a Metadata API retrieve: it returns what the
retrieving user is entitled to retrieve.

**When it occurs:** Any inventory, ER map or snapshot diff produced without recording the identity and
permission profile of the account that produced it. It bites hardest on sandbox-vs-production diffs,
where the two integration users rarely have identical permission sets, so ordinary permission differences
read as schema drift.

**How to avoid:** Run every snapshot as a dedicated documentation user with View All Data / Modify All
Metadata-class access, and record that user in the artefact — `generated_from.retrieved_as` in
`templates/data-dictionary.yaml` exists for exactly this. When comparing two orgs, the two snapshots must
be taken under the same profile or the delta is uninterpretable. If a field appears in one snapshot and
not the other, rule out permissions before calling it drift.

---

## Gotcha 6: Describe Returns the Field's Shape, Never Its Documentation

**What happens:** An agent builds a "complete data dictionary" from `Schema.getGlobalDescribe()` plus
`Schema.describeSObjects()`, gets every type, length, required flag and relationship target, and ships it
with an empty or absent Description column — because there is no `getDescription()` method on
`Schema.DescribeFieldResult`. The full method list (Apex Reference Guide, apexrefguide.txt
L190542–L190672) has `getLabel()`, `getInlineHelpText()`, `getLength()`, `getPicklistValues()`,
`isCustom()`, `isCalculated()` and forty more — and no description accessor at all. The same omission
applies to the REST `/sobjects/<Object>/describe` payload, which mirrors `DescribeSObjectResult`.

**When it occurs:** Every time the inventory generator is a describe call and nobody notices the missing
column, because a 400-row CSV looks complete.

**How to avoid:** Treat describe as the *shape* source and the Metadata API retrieve as the
*documentation* source, and join them. `<description>`, `<inlineHelpText>`, `<businessOwnerUser>`,
`<businessStatus>` and `<securityClassification>` are all `CustomField` metadata elements (Metadata API
Developer Guide, CustomField field table, api_meta.txt L43308–L43622) and none of them are reachable from
a describe call. `references/worked-examples.md` sections 1 and 4 are the two halves; running only the
first is the failure.

---

## Gotcha 7: A Compound Field Is Three Fields in the Limit Count, One in the UI, and Neither in Schema Builder

**What happens:** An address or geolocation field is counted once by an admin reading the Setup field
list, expanded into its components by describe and by the Data Loader, and dropped entirely from Schema
Builder. Three tools, three answers, for the same field. The Object Reference states each part directly:
"custom geolocation fields count as three custom fields towards your organization's limits: one for
latitude, one for longitude, and one for internal use" (object_reference.txt L2874–L2876); "Compound
fields are accessible only through SOAP API, REST API, and Apex. The compound versions of fields aren't
accessible anywhere in the Salesforce user interface" (L2913–L2914); "Geolocation fields aren't available
in dashboards or Schema Builder" (L2954). And "If you select compound fields for export in the Data
Loader, they cause error messages. To export values, use individual field components" (L2931–L2932).

**When it occurs:** Any org using standard addresses, custom address fields, or geolocation fields — which
is most orgs with `Account`, `Contact`, `Lead` or `WorkOrder` in scope.

**How to avoid:** Document the compound field once, as a row, and list its components as sub-rows with the
`__latitude__s` / `__longitude__s` suffixes noted. Reconcile the field count deliberately: an org that
appears to be under a field limit by the Setup count may not be by the platform's count. Record which view
the count came from. One further trap from the same page: `isFilterable()` "erroneously returns true for
address fields" (L2950–L2951), so an inventory that derives "usable in a WHERE clause" from describe will
be wrong for every address field.

---

## Gotcha 8: The Relationship Name Is Not the Field Name, and a Polymorphic Field Has Several Parents

**What happens:** An ER map or integration spec labels an edge with the field API name and a downstream
developer writes a parent-to-child subquery against it, which fails. `DescribeFieldResult` carries the two
as separate accessors: `getRelationshipName()` "Returns the name of the child-to-parent relationship"
(apexrefguide.txt L190590) and `getName()` returns the field. `Account__c` and `Account__r` are different
strings, and the child-side relationship name — the one a subquery needs — is a third string configured
on the field and surfaced through `DescribeSObjectResult.getChildRelationships()` (L192140). Separately,
`getReferenceTo()` "Returns a list of Schema.sObjectType objects for the parent objects of this field. If
the isNamePointing method returns true, there is more than one entry in the list, otherwise there is only
one" (L190587–L190589) — so a generator that reads `getReferenceTo()[0]` silently records one parent for
`Task.WhoId` and `Task.WhatId`.

**When it occurs:** Any generated ER map, and any inventory whose relationship column is populated from a
single describe accessor rather than from three.

**How to avoid:** Carry four separate columns — field API name, `referenceTo` (all entries, joined),
`relationshipName`, and `relationshipOrder` — and emit one ER edge per `referenceTo` entry tagged as
polymorphic, as the emitter in `references/worked-examples.md` section 3 does. Never collapse a
polymorphic field to a single line; a reader who sees one line concludes the field has one parent.

---

## Gotcha 9: Managed-Package Fields Carry a Namespace, and Describe Sometimes Hides It

**What happens:** An inventory produced from inside a managed package's own namespace lists fields under
bare names, and the same inventory produced from a subscriber org lists them as `ns__Field__c`. The two
files diff as if every packaged field was renamed. `DescribeFieldResult.getLocalName()` documents the
behaviour: "Returns the name of the field, similar to the getName method. However, if the field is part of
the current namespace, the namespace portion of the name is omitted" (apexrefguide.txt L190566–L190567).

**When it occurs:** Any org with installed managed packages — and the effect is invisible until two
snapshots taken from different namespace contexts are compared, or until an integration built from the
documentation sends the un-namespaced API name and gets `INVALID_FIELD`.

**How to avoid:** Populate the inventory from `getName()`, never `getLocalName()`, and add an explicit
namespace column so packaged fields are visibly out of scope for modification. Packaged fields are also
the boundary of this skill: their descriptions are set by the package publisher and cannot be edited in the
subscriber org, so they are not documentation debt and must not appear in the debt list.

---

## Gotcha 10: FieldDefinition and EntityDefinition Are Tooling Objects, Not Documented in the Object Reference

**What happens:** A practitioner or agent looks up `FieldDefinition` in the Salesforce Object Reference to
confirm its columns, finds nothing, and concludes the object does not exist — or worse, invents column
names. Searching the Object Reference for `FieldDefinition` and `EntityDefinition` returns only incidental
foreign-key references from other objects (`ListViewColumn.FieldDefinitionId`,
`RelatedListColumnDefinition`, `ParentEntityDefinitionId` — object_reference.txt L245921–L246136,
L256273–L256281). Neither object has its own entry, because both are Tooling API objects and belong to the
Tooling API Developer Guide.

**When it occurs:** Any time the SOQL inventory route in Gotcha 4 is checked against the wrong guide, or an
agent asked to "cite the source" for a `FieldDefinition` query reaches for the Object Reference.

**How to avoid:** Query them with the Tooling API explicitly — `sf data query --use-tooling-api`, or the
Developer Console's Use Tooling API checkbox — and cite the Tooling API Developer Guide, not the Object
Reference. Two constraints that catch every first attempt: `FieldDefinition` requires a
`WHERE EntityDefinition.QualifiedApiName = '<Object>'` filter, and its `QualifiedApiName` is the bare field
name (`My_Field__c`), not `Account.My_Field__c`. `Custom`, `InlineHelpText`, `ExternalId` and `Unique` are
not `FieldDefinition` columns — selecting them fails the whole query with `No such column` rather than
returning null. `agents/field-impact-analyzer/AGENT.md` Step 1 documents the exact working projection;
reuse it rather than re-deriving it.

---

## Gotcha 11: A Wildcard Manifest Retrieves No Standard Objects

**What happens:** An agent writes `<members>*</members>` under `<name>CustomObject</name>`, retrieves, and
reports a complete inventory. Every custom field on `Account`, `Contact`, `Case` and `Opportunity` is
missing from it. The Metadata API guide is explicit that this manifest "can be used to retrieve or deploy
all custom objects, but not all standard objects", and that "you can't use an asterisk wildcard to work
with all standard objects; each standard object must be specified by name" (api_meta.txt L2178–L2179 and L2193).
Compounding it, retrieving a standard object "includes all custom and standard fields except for standard
fields that aren't customizable... Other standard fields aren't supported, including system fields (such as
CreatedById or LastModifiedDate) and autonumber fields" (L2162–L2167).

**When it occurs:** Every first attempt at a whole-org inventory, and every CI snapshot job whose manifest
was written once and never revisited as standard objects were customised.

**How to avoid:** Enumerate standard objects by name in the manifest — `sf sobject list --sobject standard`
gives the list to filter — and document system fields from `admin/system-field-behavior-and-audit` rather
than expecting them in the retrieve. One further effect of the same manifest worth knowing: "Retrieving a
component of this metadata type in a project makes the component appear in any Profile and PermissionSet
components that are retrieved in the same package" (api_meta.txt L41920–L41921) — which is how you get FLS
into the same snapshot as the fields, and also why a CustomObject-plus-Profile retrieve is much larger than
expected.
