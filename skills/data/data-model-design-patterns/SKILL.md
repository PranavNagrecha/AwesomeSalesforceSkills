---
name: data-model-design-patterns
description: "Use when designing, reviewing, or troubleshooting Salesforce object relationships and field type choices — lookup vs master-detail, junction object modeling, indexing strategy, and data model anti-patterns. NOT for drawing or diagramming the model — use architect/salesforce-erd-and-diagramming. NOT for the Setup steps to create the object itself — use admin/object-creation-and-design. NOT for hierarchical or external relationship types, polymorphic lookups, or the per-object relationship limits — use admin/lookup-and-relationship-design."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Scalability
  - Security
  - Performance
triggers:
  - "should I use a lookup or master-detail relationship for this child object"
  - "my SOQL queries are slow on a large object with millions of records"
  - "how do I model a many-to-many relationship between two objects in Salesforce"
  - "rollup summary field is not available on this relationship"
  - "cascade delete wiped related records I did not expect to lose"
  - "what field type should I use to store phone numbers or email addresses"
  - "section status JSON in a long text area is not reportable"
  - "pipeline lives on account instead of opportunity"
  - "lookup driven junction create duplicates"
  - "design a junction object between two objects so both sides get roll-up totals"
tags:
  - data-model
  - relationships
  - lookup
  - master-detail
  - junction-object
  - indexing
  - skinny-tables
  - external-id
  - field-types
inputs:
  - "List of objects involved and their approximate record volumes"
  - "Relationship cardinality requirements (one-to-many, many-to-many)"
  - "Whether rollup summaries or cascade delete are needed"
  - "Anticipated query patterns (fields used in WHERE, ORDER BY, GROUP BY)"
  - "Integration requirements (upsert via external ID, API access)"
outputs:
  - "Relationship type recommendation (lookup vs master-detail vs junction object) with rationale"
  - "Field type selection guidance for data integrity"
  - "Indexing strategy recommendation (standard, custom index, skinny table)"
  - "Data model anti-pattern findings with remediation steps"
  - "Completed data-model-design-patterns-template.md for the org"
dependencies: []
version: 1.1.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# Data Model Design Patterns

This skill activates when a practitioner needs to choose or review Salesforce object relationship types, field types, or indexing strategy. It covers the full decision surface from green-field modeling through production performance troubleshooting.

---

## Before Starting

Gather this context before working on anything in this domain:

| Context | What to confirm |
|---|---|
| Object list and volumes | Which objects are involved? Record counts now, in 1 year, in 3 years? |
| Query patterns | What fields appear in WHERE, ORDER BY, or GROUP BY in the most frequent SOQL queries? |
| Relationship requirements | Is cascade delete acceptable? Are rollup summaries needed? Can a child exist without a parent? |
| Integration requirements | Does any external system upsert records? If so, what is the natural key? |
| Common wrong assumption | Lookup relationships do NOT support rollup summary fields; only master-detail children do. |
| Key limits in play | A custom object allows up to 40 relationships (limits guide); External ID makes Auto Number, Email, Number, and Text fields indexed without a Support case; other custom indexes come from Customer Support. |

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "If the parent is deleted, should the children go too, and can any child ever block that?" | Master-detail deletes detail records, and the parent delete fails if any child can't be deleted (Gotcha 1) | A deliberate cascade decision and a guard for bulk deletes |
| "Can a child ever exist without a parent, or move to a different parent?" | Master-detail is required and reparenting is off unless `reparentableMasterDetail` is set (Gotcha 2) | Lookup where optional, or master-detail with reparenting decided up front |
| "Does either parent need totals across the children?" | Native roll-up summaries need the master-detail field as `summaryForeignKey` (Gotcha 3) | Master-detail legs where totals are needed, or a roll-up alternative chosen early |
| "Is either side of the junction one of the standard objects that can't be a master?" | BusinessHours, Idea, Lead, OrderItem, PriceBook2, Product2, QuoteLineItem, and User can't be the master (Gotcha 8) | A lookup on that leg and a non-native roll-up plan for it |
| "What is the source system's key, must it be unique, and is it case-sensitive?" | External ID, Unique, and case sensitivity are separate settings (Gotcha 5) | A key field whose flags match the source semantics |
| "How many relationships does the object already have?" | A custom object allows up to 40 relationships | A relationship budget before adding more lookups |
| "Should the child be editable by users who can only read the parent?" | `writeRequiresMasterRead` sets the parent access needed to create, edit, or delete detail records | A sharing behaviour chosen on purpose, not by default |

A proper model adds relationship types chosen against deletion, ownership, totals, and keys; "just adding a lookup" leaves orphan rows, missing totals, and keys that collide in the first integration.

---

## Core Concepts

### Lookup Relationships

A lookup relationship is a loosely coupled reference from a child object to a parent object. The child record can exist without a parent (the parent field is optional unless you mark it required on the page layout). Deleting the parent does not delete child records by default — the lookup field is cleared (Metadata API `deleteConstraint: SetNull`, the default). `Restrict` blocks the parent delete instead. `Cascade` also exists in the metadata; confirm it is available in the org and review its access implications before designing on it (see `references/gotchas.md`). Lookups can't drive native roll-up summary fields.

The limits guide notes a custom object allows up to 40 relationships. Lookup and master-detail fields are foreign keys, which are indexed by default.

**Use lookup when:** The child record has independent business meaning, the parent may be deleted without removing children, or you need more than 2 parent references on the same child.

### Master-Detail Relationships (MDR)

A master-detail relationship is a tightly coupled parent-child relationship. The master-detail field is required on the detail record, the detail record takes its owner and sharing from the master, and deleting the master deletes its detail records (the parent delete fails if any child can't be deleted). Master-detail relationships enable roll-up summary fields on the parent.

A junction object carries two master-detail fields. Records can't be reparented unless `reparentableMasterDetail` is true, and `writeRequiresMasterRead` controls whether Read access on the master is enough to create, edit, or delete detail records. Converting a lookup to master-detail needs a parent on every existing child (see Gotcha 2).

**Cascade delete chain risk**: If Object A is the master of Object B, and Object B is the master of Object C, deleting an A record cascades through B into C. A single parent delete can remove thousands of grandchild records.

**Use master-detail when:** The child's entire existence depends on the parent (e.g., Order Line Item depends on Order), rollup summaries are required, and you are certain cascade delete is the desired behavior.

### Many-to-Many: Junction Objects

Salesforce does not support native many-to-many relationships. The standard pattern is a **junction object**: a custom object with two master-detail relationships, one to each side of the many-to-many. This gives you:

- Rollup summaries on both parent objects (if both sides are MDR)
- Cascade delete: deleting either parent deletes the junction records
- A place to store attributes about the relationship itself (e.g., a role, a quantity, a date)

**Both legs must be legal.** Eight standard objects can never be the master: BusinessHours, Idea, Lead, OrderItem, PriceBook2, Product2, QuoteLineItem, User. A junction to any of them must use a lookup on that leg, which means no native rollup on that parent — `Account_Product__c` with a master-detail to Product2 is not buildable. No standard object can be the detail of a custom object either.

If you model the junction with two **lookup** fields instead of two MDR fields, you lose rollup summary capability on both sides and the junction records survive even after one parent is deleted — which creates orphan records and referential integrity problems.

### Field Type Selection for Data Integrity

Choosing the wrong field type loses platform-enforced validation, formatting, and UI affordances:

| Data | Correct Type | Wrong Type | What You Lose |
|---|---|---|---|
| Phone number | Phone | Text(255) | Click-to-dial, mobile formatting |
| Email address | Email | Text(255) | Click-to-email, email validation |
| Percentage | Percent | Number | Automatic % display, decimal semantics |
| Currency amounts | Currency | Number | Multi-currency support, locale formatting |
| Long unformatted text | Long Text Area | Text(255) | Capacity — Text holds at most 255 chars, and a longer value fails the save unless truncation is requested (Apex Developer Guide L8519-8521) |
| Structured rich content | Rich Text Area | Long Text Area | Formatting, inline images |
| Unique record key | External ID (+ Unique) | Text | Indexed by default, available for upsert |
| True/False | Checkbox | Picklist | Compact storage, formula compatibility |

### Indexing Strategy

Salesforce automatically indexes a small set of standard fields on every object: `Id`, `Name`, `OwnerId`, `CreatedDate`, `SystemModstamp`, `RecordTypeId`, and all standard and custom relationship fields.

**Custom indexes** extend selective filtering to other fields. External ID or Unique on an Auto Number, Email, Number, or Text field creates one without a case; for other fields, Customer Support creates them. Constraints:
- Not available on long or rich text areas, encrypted text, multi-select picklists, currency fields in a multicurrency org, or non-deterministic formulas (deterministic formulas can be indexed)
- The optimizer uses a custom index only when the filter matches less than 10% of the first million rows and 5% of rows beyond (5M rows → 300,000)

**Skinny tables** hold selected standard and custom fields together so read-only queries that use only those fields skip a join. Customer Support creates them; they stay in sync with the source table, hold up to 200 columns, and are copied to Full sandboxes only.

---

## Common Patterns

### Pattern: Junction Object for Many-to-Many with MDR Fields

**When to use:** Two objects need a many-to-many relationship and you need rollup summaries or tight referential integrity.

**How it works:**
1. Create a custom junction object (e.g., `Contact_Campaign__c` to link Contact and Campaign).
2. Add a master-detail field to the first parent (e.g., `Contact__c` MDR to Contact).
3. Add a second master-detail field to the second parent (e.g., `Campaign__c` MDR to Campaign).
4. Add any relationship-attribute fields to the junction (e.g., `Role__c`, `Response_Date__c`).
5. Optionally add rollup summary fields on each parent to aggregate junction data.

**Why not two lookups:** Lookup-based junction objects cannot have rollup summary fields on either parent, and orphan junction records accumulate when parents are deleted.

### Pattern: External ID for Integration Upsert

**When to use:** An external system needs to create or update Salesforce records without knowing the Salesforce `Id`, using a natural key from the source system.

**How it works:**
1. Create a custom field with type `Text` (or `Number`), mark it as `External ID` and `Unique`.
2. The field becomes indexed automatically — no Support case required.
3. Use the REST API `upsert` endpoint or Bulk API 2.0 upsert with the external ID field as the key.
4. Salesforce matches on the external ID value: if found, updates; if not found, inserts.

**Note:** External ID makes the field indexed and usable as the upsert key; Unique is what rejects duplicate values, and `caseSensitive` decides whether `ABC` and `abc` are the same key.

**Why not use Name as the key:** Name is not guaranteed unique and is not marked as an external ID, so the upsert API will not match on it.

### Pattern: Custom Index for Selective Filter on Non-Standard Field

**When to use:** A large object (500k+ records) is queried frequently with a WHERE filter on a field that is not a standard indexed field, and the query is timing out or performing full table scans.

**How it works:**
1. Confirm the filter is under the custom-index threshold for the object's row count (10% of the first million rows plus 5% of the rest).
2. Confirm the field type can be indexed (not long or rich text, encrypted text, multi-select picklist, or a non-deterministic formula).
3. Open a Salesforce Support case requesting a custom index on the specific field and object.
4. After the index is created, capture the plan with Developer Console Query Plan or the REST `?explain=` parameter and confirm `leadingOperationType: Index`.

**Why not just add an external ID:** External ID only applies to Auto Number, Email, Number, and Text fields, and it turns the field into an upsert key. For picklists, dates, and other filter fields, ask Support for the index.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Child record must not exist without a parent | Master-Detail | Parent field is required; enforce referential integrity at the platform level |
| Rollup summary needed on parent | Master-Detail | Rollup summary fields only work on MDR parent objects |
| Child record has independent meaning; parent may be deleted | Lookup | Child survives parent deletion; parent field is optional |
| Many-to-many relationship required | Junction object with two MDR fields | Enables rollup summaries and cascade delete on both sides |
| Many-to-many but rollup not needed and orphan records are acceptable | Junction object with two Lookups | Looser coupling; junction survives parent deletion |
| Phone or email data to display in UI | Phone / Email field type | Platform formatting, click-to-dial/email, mobile display |
| Integration upsert with a source-system natural key | External ID field (Unique) | Automatically indexed; supported by upsert API endpoints |
| Large object with slow non-indexed filter queries | Custom index (via Support case) | Selective index on the filter field reduces full-table scans |
| Very large object, small set of repeatedly queried fields | Skinny table (via Support) | Denormalized projection eliminates wide-row scans |
| Need to store more than 255 characters | Long Text Area | A Text field holds at most 255 characters; longer values fail the save |

---

## Mode 1: Build from Scratch

Use this mode when modeling a new set of objects or relationships before any data exists.

1. **Map entities and cardinality**: For each entity pair, determine whether the relationship is one-to-one, one-to-many, or many-to-many.
2. **Select relationship type**: Apply the Decision Guidance table above. Default to lookup unless cascade delete + rollup summaries are needed, or until you are certain the child's existence is fully dependent on the parent.
3. **Select field types**: For each attribute, choose the most semantically specific field type (Phone over Text, Currency over Number, etc.).
4. **Plan external IDs**: For every object that an external system will write to, identify the natural key and create an External ID field.
5. **Identify index candidates early**: List fields likely to appear in WHERE clauses. Standard fields are already indexed. Flag any custom fields for a future Support case if the object is expected to grow past 500k records.
6. **Document the model**: Fill in the `data-model-design-patterns-template.md` with the decisions made and their rationale.

## Mode 2: Review an Existing Model

Use this mode when auditing an org's data model for quality or before a major integration or migration project.

1. Run `scripts/check_data_model.py` against the exported metadata to detect structural anti-patterns automatically.
2. Check all junction objects: do they use two MDR fields or two lookups? Flag lookup-based junctions.
3. Check for Text fields storing phone or email data by inspecting field labels and common values.
4. Check external ID coverage: does each object integrated with an external system have an External ID field?
5. Check for MDR chains deeper than 2 levels — these create hidden cascade delete risk.
6. Check the SOQL query log (from Debug Logs or Event Monitoring) for queries performing full table scans on large objects. Cross-reference against available indexes.
7. Fill the Review Checklist below and report findings using the template.

## Mode 3: Troubleshoot

Use this mode when a production issue traces back to the data model.

| Symptom | Likely cause / next step |
|---|---|
| Unexpected record deletion | Check for MDR cascade delete chains. A deleted grandparent may have silently removed grandchildren. |
| Rollup summary not available | Relationship is likely a lookup, not a master-detail. Rollups require master-detail. |
| SOQL timeout or governor limit on large object | Check query execution plan. If full table scan, identify filter field and request a custom index if eligible. |
| Upsert matching not working | Confirm the target field is marked External ID. Upsert won't match on non-External-ID fields. |
| Orphaned children after a lookup parent delete | Lookup delete behaviour is `SetNull` (clears the field) by default. Use `Restrict`, master-detail, or before-delete automation; check `Cascade` availability in the org before relying on it. |
| Saves fail on long text values, or values arrive cut off (a client using `allowFieldTruncation`) | Field is likely Text(255). Migrate to Long Text Area. |

---


## Recommended Workflow

1. List entities, volumes, query filters, and integration keys in `templates/data-model-design-patterns-template.md`.
2. Choose each relationship with the Questions table and Decision Guidance; write the field metadata (example below) with `deleteConstraint`, `reparentableMasterDetail`, and `writeRequiresMasterRead` set on purpose.
3. Run `python3 skills/data/data-model-design-patterns/scripts/check_data_model.py --manifest-dir force-app/main/default` and fix every ERROR (for example, a master-detail to a standard object that can't be a master); review WARN lines (lookup-only junctions, relationship counts near 40).
4. For filter fields on large objects, do the threshold arithmetic and either set External ID or file a Support request (`data/custom-index-requests`).
5. Deploy to a sandbox, load sample data, and capture plans for the main queries; record decisions in the template. `references/metadata-examples.md` shows junction legs, a Restrict lookup, and a key field with every decision attribute set.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- objects/Enrollment__c/fields/Course__c.field-meta.xml: one master-detail leg of a junction -->
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Course__c</fullName>
    <label>Course</label>
    <type>MasterDetail</type>
    <referenceTo>Course__c</referenceTo>
    <relationshipName>Enrollments</relationshipName>
    <relationshipOrder>0</relationshipOrder>
    <reparentableMasterDetail>false</reparentableMasterDetail>
    <writeRequiresMasterRead>false</writeRequiresMasterRead>
</CustomField>
```

---

## Review Checklist

Run through these before marking data model work complete:

- [ ] All many-to-many relationships are modeled with junction objects using two MDR fields (not two lookups) unless rollup summaries are explicitly not required
- [ ] No MDR chain is deeper than 2 levels (master → detail → detail-of-detail)
- [ ] All objects integrated with external systems have at least one External ID field (Unique)
- [ ] Phone, Email, Currency, and Percent data uses the correct platform field type (not Text)
- [ ] Fields expected to appear in large-volume WHERE clauses are either standard-indexed or have a custom index request filed
- [ ] Large objects (500k+ records) with narrow repeated query patterns have a skinny table request evaluated
- [ ] The data model template is filled and reviewed with the stakeholder

---

## Salesforce-Specific Gotchas

Full write-ups are in `references/gotchas.md`:

| # | Gotcha |
|---|---|
| 1 | Master-detail cascade delete is automatic, and one undeletable child blocks it |
| 2 | Converting a lookup to master-detail needs a parent on every child |
| 3 | Lookup-only junctions can't carry native roll-ups |
| 4 | Lookup filters don't index anything |
| 5 | External ID, Unique, and case sensitivity are separate settings |
| 6 | Skinny tables help only queries that use nothing outside them |
| 7 | Check lookup `Cascade` availability before designing on it |
| 8 | Eight standard objects can never be the master |
| 9 | Wizard state in a long text JSON blob is invisible to reports |
| 10 | Processes built on the wrong standard object |
| 11 | Lookup-driven junction creates need an existence check |

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `data-model-design-patterns-template.md` | Fill-in-the-blank output document capturing relationship decisions, field type choices, indexing plan, and anti-pattern findings |
| `scripts/check_data_model.py` | stdlib checker for relationship metadata: never-master targets, lookup-only junctions, relationship counts |

---

## Related Skills

- `admin/object-creation-and-design` — creating the object and its page layouts in Setup
- `admin/lookup-and-relationship-design` — hierarchical, external, and polymorphic relationship types and per-object limits
- `architect/salesforce-erd-and-diagramming` — drawing the model
- `data/custom-index-requests` — getting the index or skinny table the model needs
- `data/roll-up-summary-alternatives` — totals over lookup relationships
- `data/soql-query-optimization` — tuning the queries the model must serve
- `architect/large-data-volume-architecture` — objects expected to reach tens of millions of rows
