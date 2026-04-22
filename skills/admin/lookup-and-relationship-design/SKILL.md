---
name: lookup-and-relationship-design
description: "Designing Lookup vs Master-Detail vs Hierarchical vs External relationships: cascade delete, roll-up summaries, ownership, sharing implications, polymorphic lookups, relationship depth limits. NOT for record-type strategy (use data-model-design-patterns). NOT for junction object patterns (use many-to-many-relationships)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Scalability
tags:
  - lookup
  - master-detail
  - relationships
  - data-model
  - sharing
triggers:
  - "should this field be a lookup or master-detail relationship"
  - "roll-up summary limit and master-detail requirement"
  - "cascade delete behavior on lookup vs master-detail"
  - "hierarchical relationship on user object use case"
  - "polymorphic lookup field like task.whatid"
  - "relationship field limit 40 per object and 5 levels of soql"
inputs:
  - Parent and child objects under design
  - Ownership and sharing requirements
  - Aggregation needs (sums, counts) from parent
  - Deletion semantics (cascade vs orphan)
outputs:
  - Relationship-type decision with rationale
  - Roll-up summary plan or Apex alternative
  - Sharing impact analysis
  - Relationship graph documentation
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-21
---

# Lookup and Relationship Design

Activate when designing a new parent-child relationship or reviewing an existing data model for correctness. The choice between Lookup, Master-Detail, Hierarchical, and External relationships has lasting implications for sharing, reporting, deletion cascades, and migration complexity — getting it wrong often requires costly rework.

## Before Starting

- **Clarify ownership semantics.** Does the child have its own owner, or does it inherit from parent? Master-detail forces inheritance; lookup allows independence.
- **Clarify deletion semantics.** Should deleting the parent delete the children? Master-detail: yes (cascade). Lookup: configurable (clear field or restrict or cascade).
- **Inventory roll-up aggregates.** Roll-up summary fields require master-detail (or use declarative Rollup on lookup via specific features/apps).
- **Count relationship fields per object.** Hard limit of 40 relationship fields; soft reporting limits lower.

## Core Concepts

### Master-Detail

Child record is owned by parent: inherits sharing, cascade-deletes, allows roll-up summary fields on parent. A child cannot exist without a parent. Converting master-detail → lookup is possible only when no orphans exist and no roll-ups reference the field. Max 2 master-detail relationships per object.

### Lookup

Independent child record; keeps its own owner and sharing. Deletion behavior configurable: "Clear the value of this field" (default), "Don't allow deletion of the parent if a child exists" (restrict), or "Delete this record also" (cascade — requires specific config). No native roll-up summary.

### Hierarchical (User object only)

Self-referencing lookup on `User` for manager hierarchy. Drives `CustomField__c` sharing and "Role" reporting, but not role hierarchy — that's a separate concept.

### External relationships

`External Lookup` (ExternalLookup), `Indirect Lookup` (IndirectLookup) — connect to External Objects via Salesforce Connect. Different SOQL semantics and no roll-ups.

### Polymorphic lookups

`Task.WhatId` and `Task.WhoId` reference multiple object types. SOQL requires `TYPEOF` or `WhatId.Type` filters. Only supported on select standard objects.

## Common Patterns

### Pattern: Master-detail for true parent-child

Opportunity → OpportunityLineItem: cascading delete and roll-up of revenue. Classic.

### Pattern: Lookup + restrict delete for loose coupling

Account → Asset: each has its own owner, but deleting an Account with open Assets should be blocked. Configure "Don't allow deletion of the parent."

### Pattern: Lookup + Apex roll-up for aggregation

When master-detail is not viable, use a trigger-framework-based rollup (e.g., Declarative Lookup Rollup Summaries app, or custom Apex).

## Decision Guidance

| Need | Relationship |
|---|---|
| Cascade delete + roll-up summary | Master-Detail |
| Child has independent owner/sharing | Lookup |
| User manager hierarchy | Hierarchical |
| Child in external system | External Lookup |
| Two possible parent object types | Polymorphic (if supported) or two lookups with validation |

## Recommended Workflow

1. Clarify the business semantics: ownership, deletion, aggregation.
2. Count existing relationship fields on the child object (max 40).
3. Pick the type from the decision table.
4. For master-detail, verify data quality: no orphans will exist post-deployment.
5. Plan the roll-up summary fields (or Apex rollup) if aggregation required.
6. Document sharing impact — master-detail children inherit from parent.
7. Add relationship to the data model diagram; review with architect.

## Review Checklist

- [ ] Ownership semantics documented and match chosen type
- [ ] Deletion behavior explicit (cascade / restrict / clear)
- [ ] Relationship field count under 40 on child object
- [ ] Roll-up summaries planned where needed
- [ ] Sharing impact analyzed (especially for master-detail)
- [ ] SOQL path depth under 5 levels for queries traversing this relationship
- [ ] Data model diagram updated

## Salesforce-Specific Gotchas

1. **Master-detail creates ownership inheritance.** Custom sharing rules on child objects with master-detail are limited; sharing follows parent.
2. **Converting lookup → master-detail requires all rows have a value.** Orphans block conversion; cleanup comes first.
3. **SOQL relationship queries cap at 5 levels.** Deep hierarchies require multiple queries or flattened references.

## Output Artifacts

| Artifact | Description |
|---|---|
| Relationship design doc | Type choice, rationale, sharing impact |
| Roll-up aggregation plan | Field list + declarative or Apex approach |
| Data model diagram | Parent-child graph with relationship types |

## Related Skills

- `data/data-model-design-patterns` — holistic data model strategy
- `admin/many-to-many-relationships` — junction objects
- `apex/apex-rollup-patterns` — Apex-based rollups when master-detail unavailable
