---
name: data-model-documentation
description: "Use when a BA or admin needs to document the Salesforce data model: creating field inventories, object relationship maps, ER diagrams, or analyzing field usage across objects. Triggers: 'data dictionary', 'document our data model', 'object relationship map', 'field inventory', 'ER diagram for Salesforce'. NOT for designing the data model (use object-creation-and-design or architect skills) or for optimizing queries against the model (use soql-query-optimization)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
triggers:
  - "how do I document the fields on my Salesforce objects"
  - "I need to create an ER diagram of our Salesforce data model"
  - "how do I produce a data dictionary for our Salesforce org"
  - "I need a field inventory for all custom objects"
  - "how do I see all the relationships between Salesforce objects"
tags:
  - data-model
  - field-inventory
  - er-diagram
  - schema-documentation
  - object-relationships
inputs:
  - "List of objects to document (standard, custom, or both)"
  - "Access to Salesforce org Setup or exported metadata (package.xml retrieve)"
  - "Any specific documentation format required (spreadsheet, diagram, narrative)"
outputs:
  - "Field inventory: object name, field label, API name, type, required, FLS, description"
  - "Object relationship map showing Lookup, Master-Detail, and Junction relationships"
  - "ER diagram draft suitable for stakeholder review or onboarding"
  - "Field usage analysis flagging blank Description fields or undocumented custom fields"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-03
---

# Data Model Documentation

Use this skill when you need to produce documentation artifacts describing an existing or new Salesforce data model: field inventories, ER diagrams, object relationship maps, or a data dictionary. This skill produces the documentation — it does not design or change the model.

---

## Before Starting

Gather this context before working:

- Which objects are in scope? Confirm whether the request covers standard objects, all custom objects, a specific functional area (e.g., Service objects, Sales objects), or the full org.
- Is access to the Salesforce org available (Setup → Object Manager, Schema Builder), or is this a metadata-only analysis (retrieved via Metadata API or SFDX)?
- What is the target audience and format? A developer data dictionary (API names, types, FLS) differs from a business ER diagram (labels, relationships, business descriptions).
- Are there objects with more than 800 fields? Each standard or custom object supports up to 800 custom fields total (limits vary by object type per the Object Reference). Document-only orgs that hit field limits often have undocumented or duplicated fields.

---

## Core Concepts

### Objects and Fields in Salesforce

Every record in Salesforce is an instance of an sObject. Standard objects (Account, Contact, Opportunity, Case) are provided by Salesforce. Custom objects have API names ending in `__c`. Fields on objects have an API name, a field type (Text, Number, Date, Lookup, etc.), a label visible to users, and metadata properties including Required, Unique, External ID, and Field-Level Security (FLS).

The Object Reference defines the field types, cardinality rules, and behavior of each relationship field type. Lookup fields create a loosely coupled many-to-one relationship; deleting the parent leaves the child intact (blank lookup). Master-Detail fields create a tightly coupled relationship; deleting the master deletes the child (cascade delete). Each object can have up to two Master-Detail relationships.

### Schema Builder

Schema Builder (Setup → Object Manager → Schema Builder) is Salesforce's built-in visual ER diagram tool. It allows you to view objects, fields, and relationships in a drag-and-drop canvas, filter by object, and export a visual representation. It is the fastest way to produce an ER diagram for a small to medium scope (10–30 objects). For large orgs with hundreds of custom objects, Schema Builder becomes slow and the export is limited — use Metadata API retrieval instead.

### Metadata API and SFDX Retrieval for Field Inventory

For complete field inventory across many objects, retrieve the metadata using Metadata API or the sf CLI. The `CustomObject` metadata type includes every field definition, validation rule, and relationship. Once retrieved as XML or SFDX source format, the field inventory can be parsed programmatically or inspected manually.

```bash
# Retrieve all custom objects via sf CLI
sf project retrieve start --metadata "CustomObject"
```

After retrieval, each object lives in `force-app/main/default/objects/<ObjectName__c>/` with individual `fields/` files per field. Standard object fields are returned as part of the `StandardValueSet` and standard object metadata.

### Field Description Quality

Every custom field has an optional Description property visible only in Setup and in the metadata — not to end users. A complete data dictionary requires every custom field to have a populated Description explaining what the field is used for, what values are valid, and who owns it. An org with blank field descriptions has undocumented schema debt.

---

## Common Patterns

### Pattern 1: Field Inventory Using Object Manager

**When to use:** You need a field-by-field inventory for one or a few objects and have live org access.

**How it works:**
1. Navigate to Setup → Object Manager → [Object Name] → Fields & Relationships.
2. The list view shows: Field Label, API Name, Data Type, Controlling Field (for dependent picklists), and whether the field is indexed.
3. Click each field to view the full Description, Required flag, Unique flag, and FLS settings.
4. Use the "Fields & Relationships" export via the Metadata API (see Pattern 2) for bulk extraction rather than manually clicking each field.
5. For FLS documentation, navigate to Setup → Profiles or Permission Sets and review field permissions per field.

**Why not export manually:** Object Manager UI does not have a CSV export button. Manual documentation from the UI works for < 20 fields. For more, use the Metadata API.

### Pattern 2: Bulk Field Inventory via Metadata API Retrieval

**When to use:** You need a complete field inventory across many objects, or you need to track changes over time.

**How it works:**
1. Create or reuse a `package.xml` that includes `CustomObject` for the target objects:
   ```xml
   <types>
     <members>Account</members>
     <members>Contact</members>
     <members>MyCustomObject__c</members>
     <name>CustomObject</name>
   </types>
   ```
2. Retrieve: `sf project retrieve start --manifest package.xml`
3. Each field is a separate file in `objects/<ObjectName>/fields/<FieldName>.field-meta.xml`.
4. Parse the XML to extract: `fullName`, `label`, `type`, `required`, `externalId`, `description`, `referenceTo` (for Lookups), `relationshipName`.
5. Load into a spreadsheet or documentation system.

**Output:** A flat field inventory with every property. The `description` field from metadata reveals whether fields are documented.

### Pattern 3: Relationship Map Using Schema Builder

**When to use:** You need a visual ER diagram showing object relationships for a stakeholder presentation or onboarding document.

**How it works:**
1. Open Setup → Object Manager → Schema Builder.
2. Click "Clear All" to deselect all objects, then add only the objects in scope.
3. Rearrange to group related objects. Master-Detail lines appear bold; Lookup lines appear thin.
4. Use "Show Elements" to toggle field names on/off.
5. Take a screenshot or export the diagram.

**Limitation:** Schema Builder does not distinguish polymorphic lookups (e.g., WhoId on Task which can point to Contact or Lead). Document these manually.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| 1–5 objects, live org access | Object Manager UI + Schema Builder | Fastest for small scope |
| 10+ objects or repeatable documentation | Metadata API retrieval + XML parse | Programmatic, version-trackable |
| Stakeholder ER diagram needed | Schema Builder export or draw.io from relationship map | Visual format; Schema Builder is built-in |
| Field description quality audit | Metadata API retrieval, check `<description>` tags | UI does not bulk-expose blank descriptions |
| Documentation needs to track drift over time | SFDX source format in Git + diff | Metadata in version control shows schema changes |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before delivering data model documentation:

- [ ] Every custom field has its API name, label, type, and description recorded
- [ ] Relationship fields (Lookup, Master-Detail) show both the parent object and the relationship name
- [ ] Junction objects for many-to-many relationships are called out explicitly
- [ ] Required fields and external ID fields are flagged in the inventory
- [ ] FLS (Field-Level Security) notes indicate which profiles/permission sets can read/edit sensitive fields, if relevant to scope
- [ ] Schema Builder ER diagram reviewed against the metadata inventory for completeness
- [ ] Any fields with blank Description values flagged as documentation debt
- [ ] Standard objects noted as "Salesforce-managed — subject to version changes"

---

## Salesforce-Specific Gotchas

1. **Schema Builder does not show all relationships** — Schema Builder only shows fields that exist on the objects you have added to the canvas. If you do not add a child object, its lookup relationship to a parent will not appear. Always cross-check with the Fields & Relationships list for each object.
2. **Standard fields are not in retrieved CustomObject metadata** — When you retrieve a `CustomObject`, Salesforce returns only the customizations (custom fields, validation rules, etc.), not the built-in standard fields. Standard fields like `Name`, `OwnerId`, `CreatedDate` must be documented separately from the Object Reference. They are not absent from the object — they just do not appear in the retrieved XML.
3. **Field-Level Security is not in the object metadata** — FLS is stored at the Profile or Permission Set level, not in the object's field metadata. To document which roles can see a field, you must retrieve Profile or PermissionSet metadata separately and cross-reference it. The `fieldPermissions` element in Profile XML maps `object.fieldName → readable/editable`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Field inventory spreadsheet | Columns: Object API Name, Field Label, Field API Name, Type, Required, External ID, Description, Owner/Team |
| Object relationship map | List or diagram showing: Object A → (Relationship Type) → Object B, plus relationship field API name |
| ER diagram | Visual Schema Builder export or equivalent diagram, annotated with cardinality |
| Documentation debt report | List of custom fields with blank Description values, grouped by object |

---

## Related Skills

- object-creation-and-design — use when you need to design or create new objects, not document existing ones
- custom-field-creation — use when creating new fields; populate Description at field creation time to avoid documentation debt
- data-model-design-patterns — use for architecture-level decisions about relationship types and indexing (data domain skill)
- requirements-gathering-for-sf — use before documentation to capture As-Is process and what objects support each process
