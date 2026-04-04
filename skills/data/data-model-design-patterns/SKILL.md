---
name: data-model-design-patterns
description: "Use when designing, reviewing, or troubleshooting Salesforce object relationships and field type choices — lookup vs master-detail, junction object modeling, indexing strategy, and data model anti-patterns. NOT for object creation steps (use object-creation-and-design). NOT for bulk data loading operations."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Data Model Design Patterns

This skill activates when a practitioner needs to choose or review Salesforce object relationship types, field types, or indexing strategy. It covers the full decision surface from green-field modeling through production performance troubleshooting.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Object list and volumes**: Which objects are involved? How many records exist or are projected (now, 1 year, 3 years)?
- **Query patterns**: What fields appear in WHERE, ORDER BY, or GROUP BY clauses in the most frequent SOQL queries?
- **Relationship requirements**: Is cascade delete acceptable? Are rollup summaries needed? Can a child record exist without a parent?
- **Integration requirements**: Does any external system upsert records? If so, what is the natural key?
- **Common wrong assumption**: Practitioners assume lookup relationships support rollup summary fields — they do not. Only master-detail children support rollup summaries on the parent.
- **Key limits in play**: Max 2 master-detail relationships per child object; max 40 lookup relationships per object; max 25 external ID fields per object; custom indexes are requested via a Salesforce Support case, not self-serve.

---

## Core Concepts

### Lookup Relationships

A lookup relationship is a loosely coupled reference from a child object to a parent object. The child record can exist without a parent (the parent field is optional unless you mark it required on the page layout). Deleting the parent does not automatically delete child records — the lookup field is simply cleared (or you can configure it to restrict or cascade). Lookups do not support rollup summary fields on the parent.

Each object supports up to 40 lookup relationship fields. Standard relationship fields (OwnerId, CreatedById, LastModifiedById, RecordTypeId) are indexed by default and do not count toward the custom lookup limit.

**Use lookup when:** The child record has independent business meaning, the parent may be deleted without removing children, or you need more than 2 parent references on the same child.

### Master-Detail Relationships (MDR)

A master-detail relationship is a tightly coupled parent-child relationship. The parent field on the child is required — a child record cannot exist without a parent. Deleting the parent cascades and permanently deletes all detail records. Master-detail relationships enable rollup summary fields (COUNT, SUM, MIN, MAX) on the parent object.

Each child object supports a maximum of **2** master-detail relationships. You cannot convert a lookup to master-detail if records already exist with a blank parent field (all existing children must have a populated parent). MDR fields are indexed automatically.

**Cascade delete chain risk**: If Object A is the master of Object B, and Object B is the master of Object C, deleting an A record cascades through B into C. Chains deeper than two levels are a production risk — a single parent delete can remove thousands of grandchild records silently.

**Use master-detail when:** The child's entire existence depends on the parent (e.g., Order Line Item depends on Order), rollup summaries are required, and you are certain cascade delete is the desired behavior.

### Many-to-Many: Junction Objects

Salesforce does not support native many-to-many relationships. The standard pattern is a **junction object**: a custom object with two master-detail relationships, one to each side of the many-to-many. This gives you:

- Rollup summaries on both parent objects (if both sides are MDR)
- Cascade delete: deleting either parent deletes the junction records
- A place to store attributes about the relationship itself (e.g., a role, a quantity, a date)

If you model the junction with two **lookup** fields instead of two MDR fields, you lose rollup summary capability on both sides and the junction records survive even after one parent is deleted — which creates orphan records and referential integrity problems.

### Field Type Selection for Data Integrity

Choosing the wrong field type loses platform-enforced validation, formatting, and UI affordances:

| Data | Correct Type | Wrong Type | What You Lose |
|---|---|---|---|
| Phone number | Phone | Text(255) | Click-to-dial, mobile formatting |
| Email address | Email | Text(255) | Click-to-email, email validation |
| Percentage | Percent | Number | Automatic % display, decimal semantics |
| Currency amounts | Currency | Number | Multi-currency support, locale formatting |
| Long unformatted text | Long Text Area | Text(255) | Storage — Text truncates at 255 chars |
| Structured rich content | Rich Text Area | Long Text Area | Formatting, inline images |
| Unique record key | External ID (+ Unique) | Text | Indexed by default, available for upsert |
| True/False | Checkbox | Picklist | Compact storage, formula compatibility |

### Indexing Strategy

Salesforce automatically indexes a small set of standard fields on every object: `Id`, `Name`, `OwnerId`, `CreatedDate`, `SystemModstamp`, `RecordTypeId`, and all standard and custom relationship fields.

**Custom indexes** extend selective filtering to other fields. They are not self-serve — you request them via a Salesforce Support case. Conditions for a field to be eligible for a custom index:
- Must not be a formula field
- Must not be an encrypted field
- Must not be a multi-select picklist
- The query filter must be selective (typically, the filter must match fewer than 10% of total records, or fewer than 333,000 records for large objects)

**Skinny tables** are a Salesforce-managed performance optimization for large objects with frequent queries on a specific set of fields. A skinny table is a denormalized projection of selected fields, maintained internally. You request skinny tables via Salesforce Support. They are most useful when a single object has millions of records and a small fixed set of non-indexed fields is repeatedly queried together.

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

**Limit:** Each object supports up to 25 external ID fields. External ID fields indexed by default; standard text fields are not.

**Why not use Name as the key:** Name is not guaranteed unique and is not marked as an external ID, so the upsert API will not match on it.

### Pattern: Custom Index for Selective Filter on Non-Standard Field

**When to use:** A large object (500k+ records) is queried frequently with a WHERE filter on a field that is not a standard indexed field, and the query is timing out or performing full table scans.

**How it works:**
1. Confirm the filter is selective (the filtered result is less than ~10% of total records, or under 333k records).
2. Confirm the field is not a formula, encrypted, or multi-select picklist.
3. Open a Salesforce Support case requesting a custom index on the specific field and object.
4. After the index is created, re-run the query and confirm execution plan shows index use (use SOQL `EXPLAIN` via Tooling API or Developer Console).

**Why not just add an external ID:** External ID fields are indexed, but they carry uniqueness semantics. Use custom index requests for non-unique filter fields.

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
| Need to store more than 255 characters | Long Text Area | Text field hard-truncates at 255 characters |

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

- **Unexpected record deletion**: Check for MDR cascade delete chains. A deleted grandparent may have silently removed grandchildren.
- **Rollup summary not available**: The relationship is likely a lookup, not a master-detail. You cannot add rollup summaries to a lookup relationship.
- **SOQL timeout or governor limit on large object**: Check query execution plan. If a full table scan is occurring, identify the filter field and request a custom index if eligible.
- **Upsert matching not working**: Confirm the target field is marked as External ID. Upsert will not match on non-External-ID fields.
- **Missing data after parent delete**: Lookup relationship delete behavior may be set to "Clear" instead of "Cascade" — clarify expected behavior and update.
- **Text field values getting truncated**: The field is likely Text(255). Migrate to Long Text Area.

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

Non-obvious platform behaviors that cause real production problems:

1. **MDR cascade delete is silent and permanent** — Deleting a master record immediately and permanently deletes all detail records, including any detail-of-detail records two levels down. There is no recycle bin recovery for cascade-deleted records. A single accidental parent delete can wipe thousands of related records.

2. **Converting lookup to master-detail requires all children to have a parent** — You cannot convert an existing lookup field to master-detail if any child records have a null parent field. You must first populate the parent field on all records, then perform the conversion — which may require a data migration step on large datasets.

3. **Lookup filter conditions add to query cost, not reduce it** — Lookup filters restrict which records appear in the lookup search but do not create a database index. If the filter references a non-indexed field on the parent object, the lookup search itself may perform slowly at scale.

4. **External ID limit is 25 per object, but only 3 are indexed in older API versions** — While the current platform allows up to 25 external ID fields per object (all indexed), integrations using older API versions (pre-Spring '16) may only respect the first 3. Always verify API version compatibility when adding more than 3 external ID fields.

5. **Skinny tables are not updated in real time for all operations** — Skinny tables can lag during bulk data loads. If you run a report or query immediately after a large Bulk API job, the skinny table projection may not reflect the freshest data until the background refresh completes.

6. **Junction object with two lookups loses rollup summary on both sides** — This is the most common many-to-many modeling mistake. Once a junction is built with lookup fields and populated with data, converting to MDR requires clearing and repopulating those fields — a non-trivial data migration.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `data-model-design-patterns-template.md` | Fill-in-the-blank output document capturing relationship decisions, field type choices, indexing plan, and anti-pattern findings |
| `check_data_model.py` | stdlib Python checker that validates junction object MDR structure in exported Salesforce metadata |

---

## Related Skills

- `object-creation-and-design` — use for step-by-step object creation and page layout setup; this skill covers design decisions, not UI creation steps
- `large-data-volumes` — use when the primary concern is bulk data loading, archival, or Bulk API throughput at scale
- `soql-query-optimization` — use when the focus is query tuning, EXPLAIN plan analysis, or governor limit debugging on existing queries
