---
name: lookup-and-relationship-design
description: "Designing Lookup vs Master-Detail vs Hierarchical vs External relationships: cascade delete, roll-up summaries, ownership, sharing implications, polymorphic lookups, junction objects, relationship depth limits. NOT for restricting which records a lookup can pick — use admin/lookup-filter-cross-object-patterns. NOT for a roll-up across a plain lookup — use data/roll-up-summary-alternatives."
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
  - "master detail vs lookup relationship design tradeoffs"
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
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
status: stub
---

# Lookup and Relationship Design

Activate when designing a new parent-child relationship or reviewing an existing data model for correctness. The choice between Lookup, Master-Detail, Hierarchical, and External relationships has lasting implications for sharing, reporting, deletion cascades, and migration complexity — getting it wrong often requires costly rework.

## Before Starting

- **Clarify ownership semantics.** Does the child have its own owner, or does it inherit from parent? Master-detail forces inheritance; lookup allows independence.
- **Clarify deletion semantics.** Should deleting the parent delete the children? Master-detail: yes (cascade; object_reference 264 L3305). Lookup: configurable through `deleteConstraint` — `Cascade`, `Restrict`, or `SetNull`, the default (api_meta 264 L45591-L45597).
- **Inventory roll-up aggregates.** Roll-up summary fields require master-detail — `summaryForeignKey` is the "Master-detail field on the child" (api_meta 264 L45869-L45870); across a plain lookup use `data/roll-up-summary-alternatives`.
- **Count relationship fields per object.** "A custom object allows up to 40 relationships" (salesforce_app_limits_cheatsheet 264 L688-L689); a query may name at most 55 child-to-parent relationships (L687-L688).

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Will the child records ever need their own owner, a queue, or a sharing rule? | A detail-side custom object loses the Owner field and with it queues, manual sharing and sharing rules (Gotcha 1) | The relationship type decided by ownership, before roll-ups pull the design toward master-detail |
| What should happen to children when a parent is deleted or merged away? | A lookup deployed without `deleteConstraint` gets `SetNull` and blanks the child silently (Gotcha 2) | An explicit `Cascade`, `Restrict` or `SetNull` in the field metadata |
| Is this a junction object, and which parent should own its records? | `relationshipOrder` 0/1 decides ownership and delete behaviour (Gotcha 3) | Both master-detail fields deployed with an explicit primary |
| What is the deepest field path a report, query or component will read across this model? | SOQL stops at five child-to-parent levels and 55 relationships per query (Gotcha 4) | A read path drawn within the limits, or a flattening formula at the midpoint |
| Which users or integrations will reparent or change owners on the child? | Missing access to the parent fails the child change (Gotcha 5) | A permission plan for the automation user instead of a wider OWD |
| Does existing data have children with no parent value? | A conversion to master-detail needs a value on every row (Salesforce-Specific Gotchas item 2) | A cleanup query and backfill step scheduled before the conversion |
| Does the child need to point at more than one parent type? | Polymorphic fields are platform-defined; a custom polymorphic lookup is UNVERIFIED (2026-10-20) (Core Concepts: Polymorphic lookups) | Two lookups plus a validation rule, or a confirmed standard polymorphic field |

A relationship chosen from these answers fixes ownership, delete behaviour and query depth on purpose; a field picked from the type list alone tends to be discovered wrong only after roll-ups and automation depend on it.

## Core Concepts

### Master-Detail

Child record is owned by parent: inherits sharing (object_reference 264 L3309), cascade-deletes (L3305), allows roll-up summary fields on parent (api_meta 264 L45869-L45870). The master-detail field is required on the detail page layout (object_reference 264 L3310). Converting master-detail → lookup is possible only when no roll-ups reference the field — UNVERIFIED (2026-10-20): Setup/Help-only, not in the 264 corpus. A junction object carries two master-detail relationships (object_reference 264 L3341-L3343); "max 2 per object" as a ceiling is UNVERIFIED (2026-10-20): Setup/Help-only, not in the 264 corpus.

When an object carries two (the junction-object shape), the two parents are **not interchangeable**: one is primary and one is secondary, recorded in the field's Metadata API `relationshipOrder` (`0` = primary, `1` = secondary; always `0` on a non-junction master-detail). The `CustomField` reference states that designation "affects delete behavior and inheritance of look and feel, and record ownership for junction objects" (api_meta 264 L45809-L45818) — a design decision, not a cosmetic one. Settle which parent should govern the junction's ownership and deletion, and set `relationshipOrder` deliberately.

### Lookup

Independent child record; keeps its own owner and sharing. Deletion behavior configurable: "Clear the value of this field" (default), "Don't allow deletion of the parent if a child exists" (restrict), or "Delete this record also" (cascade — requires specific config); the Setup labels are UNVERIFIED (2026-10-20): Setup/Help-only, not in the 264 corpus. The metadata values are `SetNull` (default), `Restrict`, `Cascade` (api_meta 264 L45591-L45597). No native roll-up summary.

### Hierarchical (User object only)

Self-referencing lookup on `User` for manager hierarchy; `Hierarchy` is a `FieldType` value (api_meta 264 L48143), and "User object only" is UNVERIFIED (2026-10-20): Setup/Help-only, not in the 264 corpus. Its documented use is approval routing: a standard or custom user hierarchy field can name the next automated approver (api_meta 264 L25502-L25505). It is not the role hierarchy. (Corrected 2026-10-20: earlier text said it "drives `CustomField__c` sharing and Role reporting"; nothing in the 264 corpus supports that, so it is no longer asserted.)

### External relationships

`External Lookup` (ExternalLookup), `Indirect Lookup` (IndirectLookup) — connect to External Objects via Salesforce Connect. Only lookup, external lookup, and indirect lookup relationships are available for external objects (object_reference 264 L3293-L3294), so no master-detail and no roll-ups.

### Polymorphic lookups

`Task.WhatId` and `Task.WhoId` reference multiple object types. To get type-dependent results, filter on the `Type` qualifier of the relationship name (`What.Type IN ('Account', 'Opportunity')`) or select with `TYPEOF What WHEN … END` (salesforce_apex_developer_guide 264 L9939-L9948). The `Owner` of a custom object is polymorphic too (User or Group, L9962-L9987). (Corrected 2026-10-20: earlier text said SOQL "requires" `TYPEOF` or `WhatId.Type` and that polymorphism is "only on select standard objects"; the qualifier is `What.Type`, neither form is required, and custom-object `Owner` is polymorphic.) Creating your own polymorphic custom lookup is not covered by the corpus — UNVERIFIED (2026-10-20): Setup/Help-only, not in the 264 corpus.

## Common Patterns

### Pattern: Master-detail for true parent-child

Opportunity → OpportunityLineItem: cascading delete and roll-up of revenue. Classic.

### Pattern: Lookup + restrict delete for loose coupling

Account → Asset: each has its own owner, but deleting an Account with open Assets should be blocked. Configure "Don't allow deletion of the parent." `deleteConstraint` is a `CustomField` element (api_meta 264 L45591), so this applies to a custom lookup; whether the standard `Asset.AccountId` exposes it is UNVERIFIED (2026-10-20): Setup/Help-only, not in the 264 corpus.

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
2. Count existing relationship fields on the child object (max 40 on a custom object, salesforce_app_limits_cheatsheet 264 L688-L689).
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
- [ ] On an object with two master-details, `relationshipOrder` names the intended parent as primary
- [ ] SOQL path depth under 5 levels for queries traversing this relationship
- [ ] Data model diagram updated

## Salesforce-Specific Gotchas

1. **Master-detail creates ownership inheritance.** A custom object on the detail side can't have sharing rules, manual sharing, or queues; sharing follows the parent (object_reference 264 L3306-L3309).
2. **Converting lookup → master-detail requires all rows have a value.** Orphans block conversion; cleanup comes first: a Metadata API deploy that converts a Lookup to a Master-Detail needs every detail record to reference a master record or be soft-deleted, and the deploy then permanently deletes the detail records in the Recycle Bin (api_meta 264 L4346-L4348).
3. **SOQL relationship queries cap at 5 levels.** Five child-to-parent levels per relationship; five parent-to-child levels from API 58.0, two at 57.0 and earlier (salesforce_app_limits_cheatsheet 264 L708-L719). Deep hierarchies require multiple queries or flattened references.

## Output Artifacts

| Artifact | Description |
|---|---|
| Relationship design doc | Type choice, rationale, sharing impact |
| Roll-up aggregation plan | Field list + declarative or Apex approach |
| Data model diagram | Parent-child graph with relationship types |

## Related Skills

- `data/data-model-design-patterns` — holistic data model strategy
- `admin/object-creation-and-design` — custom object design, including junction objects
- `data/roll-up-summary-alternatives` — Flow, Apex aggregate and DLRS-style rollups when master-detail is unavailable
