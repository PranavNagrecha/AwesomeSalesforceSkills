# Data Model Design Review — Output Template

Use this template to document data model decisions for a Salesforce org or project. Fill in each section during or after a design session. This document becomes the durable record of why specific relationship types, field types, and indexing choices were made.

---

## Review Metadata

| Field | Value |
|---|---|
| Org / Project | |
| Reviewer | |
| Review Date | |
| Skill Version | data-model-design-patterns 1.0.0 |
| Mode | Build from Scratch / Review / Troubleshoot |

---

## Objects In Scope

List each object being designed or reviewed.

| Object API Name | Label | Approx. Record Volume (current) | Projected Volume (3yr) | External System Writes? |
|---|---|---|---|---|
| | | | | Yes / No |
| | | | | Yes / No |
| | | | | Yes / No |

---

## Relationship Map

Document each relationship between the objects in scope.

| Child Object | Relationship Field | Type | Parent Object | Rollup Needed? | Cascade Delete Acceptable? | Decision Rationale |
|---|---|---|---|---|---|---|
| | | Lookup / MasterDetail | | Yes / No | Yes / No | |
| | | Lookup / MasterDetail | | Yes / No | Yes / No | |

### Many-to-Many Relationships

| Left Parent | Junction Object | Right Parent | Junction Field to Left | Junction Field to Right | MDR or Lookup (each side) |
|---|---|---|---|---|---|
| | | | | | MDR / Lookup |

---

## Field Type Decisions

Document field type choices for any field where the type was a deliberate decision (especially structured data types).

| Object | Field Label | Field API Name | Chosen Type | Why Not Text |
|---|---|---|---|---|
| | | | Phone | Click-to-dial, mobile formatting |
| | | | Email | Platform email validation |
| | | | Currency | Multi-currency, locale formatting |
| | | | External ID (Unique) | Upsert support, default index |
| | | | Long Text Area | Exceeds 255 char limit |

---

## External ID Fields

List all External ID fields across the objects in scope.

| Object | Field API Name | Field Type | Unique? | Source System Key Name | Integration Pattern |
|---|---|---|---|---|---|
| | | Text / Number | Yes / No | | Upsert / Insert-only |

---

## Indexing Plan

| Object | Field API Name | Currently Indexed? | Index Type | Action Required |
|---|---|---|---|---|
| | | Yes — standard | Standard (Id/Name/Owner) | None |
| | | Yes — MDR field | Automatic (MDR) | None |
| | | No | Custom index needed | File Support case |
| | | No — large object | Skinny table candidate | File Support case |

---

## Anti-Pattern Findings

Document any anti-patterns found during the review.

| Anti-Pattern | Object | Field(s) Affected | Severity | Recommended Fix |
|---|---|---|---|---|
| Junction object with two lookups | | | High / Medium / Low | Convert to MDR |
| Text field for Phone/Email data | | | Medium | Migrate to Phone/Email type |
| No External ID on integration object | | | High | Add External ID (Unique) field |
| MDR chain deeper than 2 levels | | | High | Review cascade delete scope |
| Missing custom index on large filter field | | | Medium | File Support case |

---

## MDR Chain Review

List any master-detail chains in the org to verify depth and cascade delete scope.

| Level 1 (Master) | Level 2 (Detail) | Level 3 (Detail-of-Detail) | Cascade Delete Risk Accepted? |
|---|---|---|---|
| | | N/A | — |
| | | (object name if exists) | Yes / No |

---

## Decisions and Rationale

Record the key decisions made during this review and why.

| Decision | Chosen Approach | Alternatives Considered | Rationale |
|---|---|---|---|
| | | | |
| | | | |

---

## Open Items

| Item | Owner | Due Date |
|---|---|---|
| | | |
| | | |

---

## Review Checklist

- [ ] All many-to-many relationships use junction objects with two MDR fields (unless rollup summaries are explicitly not required)
- [ ] No MDR chain is deeper than 2 levels
- [ ] All objects written by external systems have at least one External ID field (Unique)
- [ ] Phone, Email, Currency, and Percent data uses the correct platform field type
- [ ] Fields expected in large-volume WHERE clauses are either standard-indexed or have a custom index request filed
- [ ] Large objects (500k+ records) with narrow repeated query patterns have skinny table request evaluated
- [ ] This template is complete and reviewed with the stakeholder
