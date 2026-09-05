---
name: data-model-documentation
description: "Use when a BA or admin needs to document the Salesforce data model: creating field inventories, object relationship maps, ER diagrams, or analyzing field usage across objects. Triggers: 'data dictionary', 'document our data model', 'object relationship map', 'field inventory', 'ER diagram for Salesforce'. NOT for designing the model or choosing lookup vs master-detail — use data/data-model-design-patterns. NOT for generating the Mermaid or PlantUML diagram — use architect/salesforce-erd-and-diagramming. More trigger keywords: field inventory CSV, describe API, getGlobalDescribe, DescribeFieldResult, sObject describe, schema snapshot, schema drift, blank field descriptions, undocumented fields, field ownership, data dictionary review cadence."
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
  - "generate a field inventory CSV from the org with Apex"
  - "export every field and its description out of Salesforce"
  - "our data dictionary is out of date and nobody knows which fields are still used"
  - "the describe call is missing fields that exist on the object"
  - "diff the data model between sandbox and production"
  - "which custom fields have no description and who owns them"
tags:
  - data-model
  - field-inventory
  - er-diagram
  - schema-documentation
  - data-dictionary
  - schema-describe
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
  - "Reviewed data dictionary record with owner, classification, record volume and review date per object"
  - "Repeatable generator scripts (Apex, REST, retrieve) plus a two-snapshot drift diff"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-04
---

# Data Model Documentation

Use this skill when you need to produce documentation artifacts describing an existing or new Salesforce data model: field inventories, ER diagrams, object relationship maps, or a data dictionary. This skill produces the documentation — it does not design or change the model.

---

## Before Starting

Gather this context before working:

- Which objects are in scope? Confirm whether the request covers standard objects, all custom objects, a specific functional area (e.g., Service objects, Sales objects), or the full org.
- Is access to the Salesforce org available (Setup → Object Manager, Schema Builder), or is this a metadata-only analysis (retrieved via Metadata API or SFDX)?
- What is the target audience and format? A developer data dictionary (API names, types, FLS) differs from a business ER diagram (labels, relationships, business descriptions).
- Are any objects near their custom-field ceiling? UNVERIFIED (2026-09-04): the per-object custom-field cap (commonly cited as 800) is not stated in any of the extracted Salesforce PDFs — confirm the current number for the org's edition and object type in the Object Reference or Setup before quoting it. What *is* documented and usually explains the surprise: a custom geolocation field "counts as three custom fields towards your organization's limits: one for latitude, one for longitude, and one for internal use" (Object Reference, Compound Field Considerations).
- **Who will run the extract?** Describe and retrieve both return only what the running user can see, with no error and no gap marker. Fix the account and the permission profile before the first snapshot, not after the diff looks wrong.

---

## Questions to Ask Before Configuring

Ask before writing a line of the dictionary. Each answer changes which generator you run and what the
artefact must carry; an agent that skips them produces a 400-row CSV nobody can act on.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "What decision will someone make from this document?" | Integration mapping, a deletion review, onboarding and an audit need different columns; only the audit needs FLS, only the deletion review needs `business_status` | The column set, and permission to omit the rest |
| "Who owns each object, by name?" | The platform models this as `businessOwnerUser` on the field itself, so the answer is deployable rather than a spreadsheet column that rots | A real owner per object and per sensitive field — the checker errors without one |
| "Which fields hold regulated or sensitive data?" | Drives `securityClassification` and `complianceGroup`, and decides whether FLS must be documented at all (a separate Profile/PermissionSet retrieve) | The classification per field, and whether the FLS retrieve is in scope |
| "Which account will run the extract, and with what permissions?" | Describe and retrieve are both scoped by the running user; two snapshots taken as different users diff as false drift | A single documentation user recorded in `generated_from.retrieved_as` |
| "Is this a one-off snapshot or a standing control?" | A one-off can be a CSV; a standing control needs the manifest, the snapshot directory and the diff job in source control | A review cadence and a `last_reviewed` owner, or an explicit decision not to have one |
| "Which objects are in scope, and do standard objects count?" | A `<members>*</members>` manifest retrieves no standard objects, so "all objects" and "the wildcard" are not the same request | An explicit object list, standard objects named individually |
| "What happens to fields marked as dead?" | `businessStatus: DeprecateCandidate` is a documentation state; deleting the field is a different job with a different blast radius | A hand-off to `/analyze-field-impact` rather than a delete list |

What a proper documentation pass adds over exporting the field list: the artefact names an owner for every
object, carries a purpose for every field that describe cannot supply, records who and when it was
generated so the next diff is interpretable, and has a review date that makes it falsifiable.

---

## Core Concepts

### Objects and Fields in Salesforce

Every record in Salesforce is an instance of an sObject. Standard objects (Account, Contact, Opportunity, Case) are provided by Salesforce. Custom objects have API names ending in `__c`. Fields on objects have an API name, a field type (Text, Number, Date, Lookup, etc.), a label visible to users, and metadata properties including Required, Unique, External ID, and Field-Level Security (FLS).

The Object Reference defines the field types, cardinality rules, and behavior of each relationship field type. Lookup fields create a loosely coupled many-to-one relationship; deleting the parent leaves the child intact (blank lookup). Master-Detail fields create a tightly coupled relationship; deleting the master deletes the child (cascade delete). A junction object for a many-to-many relationship is "a custom junction object with two master-detail relationship fields, each linking to the objects that you want to relate" (Object Reference, Custom Objects — supported in API version 11.0 and later).

### Schema Builder

Schema Builder (Setup → Object Manager → Schema Builder) is Salesforce's built-in visual ER diagram tool. It allows you to view objects, fields, and relationships in a drag-and-drop canvas, filter by object, and export a visual representation. It is the fastest way to produce an ER diagram for a small to medium scope (10–30 objects). For large orgs with hundreds of custom objects, Schema Builder becomes slow and the export is limited — use Metadata API retrieval instead.

### Two Views of the Schema, and Why They Disagree

The org exposes its schema through two independent surfaces, and a data dictionary needs both.

| | Runtime view (describe) | Source view (retrieve) |
|---|---|---|
| Reached by | `Schema.getGlobalDescribe()`, `Schema.describeSObjects()`, REST `/sobjects/<Object>/describe` | Metadata API `retrieve` of `CustomObject` |
| Gives you | type, length, required, unique, external ID, formula flag, `referenceTo`, `relationshipName`, `relationshipOrder`, help text, picklist values | `description`, `inlineHelpText`, `businessOwnerUser`, `businessStatus`, `securityClassification`, `complianceGroup`, formula text, validation rules |
| Cannot give you | the field's **description** — `Schema.DescribeFieldResult` has no `getDescription()` method | anything the retrieving user is not entitled to retrieve; non-customisable standard fields |
| Scoped by | the running user's FLS (`isAccessible()`) | the retrieving user's permissions |
| Wildcard behaviour | n/a — enumerate with `getGlobalDescribe()` | `<members>*</members>` returns all *custom* objects and no standard ones |

The dictionary is the **join**. Running only describe produces a shape catalogue with an empty purpose
column; running only retrieve misses the runtime cardinality that the ER map needs. Both generators, and
the join, are in `references/worked-examples.md`.

### Metadata API and SFDX Retrieval for Field Inventory

For complete field inventory across many objects, retrieve the metadata using Metadata API or the sf CLI. The `CustomObject` metadata type includes every field definition, validation rule, and relationship. Once retrieved as XML or SFDX source format, the field inventory can be parsed programmatically or inspected manually.

```bash
# Retrieve all CUSTOM objects via sf CLI. This returns no standard objects — see gotcha 11.
sf project retrieve start --metadata "CustomObject"
```

After retrieval in source format, each object lives in `force-app/main/default/objects/<ObjectName>/` with individual `fields/*.field-meta.xml` files. Naming a standard object explicitly (`CustomObject:Account`) returns its customisations plus the standard fields that are customisable; system fields such as `CreatedById` and `LastModifiedDate` and autonumber fields are excluded (Metadata API guide, Sample package.xml Manifest Files → Standard Objects). Standard picklists are a separate type: "In API version 38.0 and later, the `StandardValueSet` type represents standard picklists. Picklists are no longer represented by fields as in earlier versions" — so `Account.Industry` values come from a `StandardValueSet` member named `Industry`, not from the object retrieve.

### Field Description Quality

Every custom field has an optional Description property visible only in Setup and in the metadata — not to end users. A complete data dictionary requires every custom field to have a populated Description explaining what the field is used for, what values are valid, and who owns it. An org with blank field descriptions has undocumented schema debt. `scripts/check_data_model_documentation.py --manifest-dir <retrieve-root>` enumerates it from the retrieved `.field-meta.xml` files and reports it as WARNs rather than errors, so the debt is listed and routed to owners instead of blocking the delivery.

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
| Whole-org inventory, hundreds of objects | `Schema.getGlobalDescribe()` to enumerate, then batched `describeSObjects()` | Schema Builder degrades; `describeSObjects()` caps at 100 objects returned per call |
| Nightly drift check on a few objects | REST `/describe` with `If-Modified-Since` | A `304 Not Modified` with no body is the "no drift" answer; cheaper than a full retrieve |
| Owner and PII classification per field | Metadata API `CustomField` — `businessOwnerUser`, `securityClassification`, `complianceGroup` | These are native, deployable metadata; see `security/data-classification-labels` |
| ER map that must survive polymorphic lookups | `getReferenceTo()` per field, one edge per entry | Schema Builder collapses or omits them; `getReferenceTo()` returns every parent |
| Sandbox vs production comparison | Two retrieves under the *same* user, then a field-level diff | Permission differences otherwise read as schema drift; see `devops/metadata-diff-between-sandboxes` |

---


## Recommended Workflow

1. **Answer the questions above and fix the scope.** Write the object list explicitly — standard objects
   by name, because a wildcard manifest returns none of them — and name the account the extract will run
   as. Record both in `generated_from` in the dictionary.
2. **Take the runtime snapshot.** Run the Apex inventory script (`references/worked-examples.md` §1) or
   the REST equivalent (§2), batching the object list; `describeSObjects()` returns a maximum of 100
   objects per call. This gives shape, not purpose.
3. **Take the source snapshot.** Retrieve `CustomObject` for the same object list with the package.xml in
   §4 and flatten the `.field-meta.xml` files. This is the only path to `description`,
   `businessOwnerUser`, `businessStatus` and `securityClassification`.
4. **Join the two into the dictionary record.** Fill `templates/data-dictionary.yaml` — one entry per
   object with `owner`, `classification`, `record_volume` (`SELECT COUNT() FROM <Object>`) and
   `last_reviewed`; one row per field with `type` and `description`. Worked version: §5.
5. **Derive the ER map from the same snapshot**, not by hand: emit one edge per `getReferenceTo()` entry
   with cardinality from `isNillable()` and `isCascadeDelete()` (§3). Hand the edge list to
   `architect/salesforce-erd-and-diagramming` for notation and layout.
6. **Lint before delivering.**
   `python3 scripts/check_data_model_documentation.py --file <dictionary.yaml> --manifest-dir <retrieve-root>`
   — errors block delivery (missing owner, unknown classification, field row with no type); WARNs are the
   documentation-debt list to route to owners, not to suppress.
7. **Make it falsifiable.** Commit the manifest, both snapshots and the dictionary, then schedule the
   two-org diff in §6 so the next drift shows up as a diff rather than as a surprise in a project.

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
- [ ] `python3 scripts/check_data_model_documentation.py --file <dictionary.yaml>` exits 0
- [ ] Every object entry carries an owner, a classification, a record volume and a `last_reviewed` date
- [ ] The account and permission profile the snapshot was taken as is recorded in `generated_from`
- [ ] Polymorphic fields show every entry in `referenceTo`, not just the first
- [ ] Compound (address / geolocation) fields are reconciled between the Setup count and the platform count

---

## Salesforce-Specific Gotchas

Eleven in full, with grounding, in `references/gotchas.md`. The ones that most often invalidate a
finished document:

| Gotcha | One-line shape |
|---|---|
| 1. Standard fields absent from a retrieve | A `CustomObject` retrieve returns customisations only; `Name`, `OwnerId`, `CreatedDate` come from the Object Reference |
| 2. FLS lives in Profile/PermissionSet | `<fieldPermissions>` is retrieved separately and cross-referenced; it is not on the field |
| 3. Schema Builder omits polymorphic lookups | `Task.WhoId` / `WhatId` render as one line or none |
| 4. No CSV export in Object Manager | Use the retrieve, or Tooling `FieldDefinition` — see gotcha 10 for its two mandatory constraints |
| 5. The inventory depends on who ran it | `isAccessible()` filters silently; record the extracting user |
| 6. Describe has no `getDescription()` | The purpose column can only come from the Metadata API |
| 7. Compound fields count three, show one, diagram zero | Geolocation counts as three custom fields and is absent from Schema Builder |
| 8. Relationship name ≠ field name | Four separate columns: field, `referenceTo`, `relationshipName`, `relationshipOrder` |
| 9. Namespaces appear or vanish by context | Populate from `getName()`, never `getLocalName()` |
| 10. `FieldDefinition` is Tooling, not Object Reference | Requires the `EntityDefinition.QualifiedApiName` filter; several obvious columns do not exist |
| 11. A wildcard manifest retrieves no standard objects | Name every standard object individually |

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Field inventory spreadsheet | Columns: Object API Name, Field Label, Field API Name, Type, Required, External ID, Description, Owner/Team |
| Object relationship map | List or diagram showing: Object A → (Relationship Type) → Object B, plus relationship field API name |
| ER diagram | Visual Schema Builder export or equivalent diagram, annotated with cardinality |
| Documentation debt report | List of custom fields with blank Description values, grouped by object |
| Data dictionary record | `templates/data-dictionary.yaml` filled in: owner, classification, record volume, review date per object; type + description per field |
| Generator scripts | The Apex / REST / retrieve extractors, committed so the next snapshot is a re-run rather than a re-derivation |
| Drift diff | Field-level delta between two same-manifest snapshots, both taken under the same user |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/worked-examples.md` | You are about to generate anything — the six generators (Apex CSV, REST + flatten, Mermaid ER map, retrieve inventory, dictionary record, two-snapshot diff), filled in |
| `references/gotchas.md` | An inventory, map or diff disagrees with what you expected, or before you trust a describe-only export |
| `references/well-architected.md` | Scoping the effort, arguing for living documentation over a snapshot, or citing sources |
| `references/llm-anti-patterns.md` | Reviewing AI-generated data model documentation, or self-checking your own output |
| `templates/data-model-documentation-template.md` | Producing the human-facing document — scope, object inventory, relationship map, FLS summary, delivery checklist |
| `templates/data-dictionary.yaml` | Producing the machine-lintable record the checker validates |
| `scripts/check_data_model_documentation.py` | Before delivering — lints the dictionary (`--file`) and the source metadata for description debt (`--manifest-dir`) |

---

## Related Skills

- `admin/object-creation-and-design` — use when you need to design or create new objects, not document existing ones
- `admin/custom-field-creation` — use when creating new fields; populate Description at field creation time to avoid documentation debt
- `admin/lookup-and-relationship-design` — use when the relationship map raises a design question rather than a documentation one
- `admin/system-field-behavior-and-audit` — use for the standard system fields (`CreatedDate`, `SystemModstamp`, `IsDeleted`) that no retrieve returns
- `admin/salesforce-object-queryability` — use when an object or field is missing from the inventory and you need to distinguish "does not exist" from "not visible to this user"
- `admin/requirements-gathering-for-sf` — use before documentation to capture As-Is process and what objects support each process
- `data/data-model-design-patterns` — use for architecture-level decisions about relationship types and indexing
- `architect/salesforce-erd-and-diagramming` — hand the extracted edge list here for diagram notation, layout and the PlantUML variant
- `security/data-classification-labels` — owns the `SecurityClassification` / `ComplianceGroup` / `BusinessOwnerId` / `BusinessStatus` value sets this skill consumes as dictionary columns
- `devops/metadata-diff-between-sandboxes` — owns interpretation of a two-org delta: which side is authoritative, and destructive-changes manifests
