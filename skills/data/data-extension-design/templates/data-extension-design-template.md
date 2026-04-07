# Data Extension Design — Work Template

Use this template when designing, reviewing, or troubleshooting a Marketing Cloud Data Extension.

## Scope

**Skill:** `data-extension-design`

**Request summary:** (describe what the user is trying to build or fix)

---

## DE Purpose and Type

| Property | Value |
|---|---|
| DE Name | |
| Sendable (yes/no) | |
| Use case | (send audience / lookup table / staging / event tracking / other) |
| Domain / business function | |

---

## Context Gathered

- **Send Relationship required:** (yes if sendable — which field maps to SubscriberKey?)
- **Approximate row volume:** (hundreds / thousands / millions)
- **Import frequency and mode:** (daily upsert / weekly replace / event-driven)
- **Retention requirements:** (how long should rows persist? any compliance constraint?)
- **Query access patterns:** (which fields will appear in SQL WHERE or AMPscript Lookup?)

---

## Primary Key Design

| Field Name | Data Type | PK? | Notes |
|---|---|---|---|
| | | Yes/No | |
| | | Yes/No | |
| | | Yes/No | |

**PK composition rationale:** (why these fields uniquely identify a row)

PK checklist:
- [ ] No more than 3 PK fields
- [ ] No Date-only PK
- [ ] PK combination is guaranteed unique in all source data
- [ ] PK fields match the business key in the source system (enabling reliable upsert)
- [ ] PK design reviewed before DE creation (cannot change after creation)

---

## Field Schema

| Field Name | Data Type | Required | PK | Notes |
|---|---|---|---|---|
| SubscriberKey | Text(50) | Yes | (if sendable) | Stable subscriber identifier |
| EmailAddress | Email | Yes | No | Required for sendable DEs |
| | | | | |
| | | | | |

**Total column count:** ___  (flag for review if > 200)

---

## Send Relationship (Sendable DEs Only)

| Property | Value |
|---|---|
| DE field mapped | (e.g., SubscriberKey) |
| Maps to field in All Subscribers | (Subscriber Key — preferred; or Email Address) |
| Rationale for choice | |

- [ ] Send Relationship maps to Subscriber Key (preferred) or Email Address (document why)
- [ ] DE field used in Send Relationship is marked Required

---

## Data Retention Configuration

| Property | Value |
|---|---|
| Retention enabled | (yes / no) |
| Retention mode | (row-based / period-based) |
| Retention period | (e.g., 90 days) |
| ResetRetentionPeriodOnImport | (true / false — must be explicitly set) |
| Rationale | (why this setting matches the import pattern) |

**ResetRetentionPeriodOnImport decision:**
- Set to `true` if: DE receives regular upsert imports and rows should stay alive as long as they keep being imported.
- Set to `false` if: rows should expire from creation date regardless of whether they were recently imported (e.g., time-limited eligibility records).
- Never leave at default (false) without explicit review.

---

## Indexing Plan

| Field | Used in SQL WHERE or AMPscript Lookup? | Estimated Row Volume | Index Required? | Support Ticket Filed? |
|---|---|---|---|---|
| | | | | |
| | | | | |

- [ ] All non-PK fields used in queries identified
- [ ] Row volume assessed for each
- [ ] Support ticket submitted for indexes where volume > 100,000 rows
- [ ] Index approval received before go-live (allow 2+ weeks)

---

## Approach

Which pattern from SKILL.md applies?

- [ ] Sendable DE with SubscriberKey Send Relationship mapping
- [ ] Composite PK for transactional/event data with upsert
- [ ] Staging DE with time-bounded row retention
- [ ] Non-sendable lookup DE

Why this pattern was chosen: (brief rationale)

---

## Test Import Results

| Check | Result |
|---|---|
| Test file row count matches import count | Pass / Fail |
| Duplicate PK values rejected or merged correctly | Pass / Fail |
| Retention settings visible in DE properties | Pass / Fail |
| Send Relationship visible in DE properties (if sendable) | Pass / Fail |
| Test query activity completes within time limit | Pass / Fail |

---

## Review Checklist

Copy from SKILL.md and tick as complete:

- [ ] Sendable DEs have exactly one Send Relationship mapped to SubscriberKey or Email Address
- [ ] Primary key composition is finalized and confirmed immutable (no changes planned post-creation)
- [ ] No Date-only primary key is used
- [ ] Data retention mode is explicitly chosen; ResetRetentionPeriodOnImport is documented and set intentionally
- [ ] Column count is below 200 (or split strategy is documented)
- [ ] All field types are valid Marketing Cloud DE types (no raw SQL types)
- [ ] Non-PK fields used in queries have been assessed for indexing; Support ticket submitted if needed
- [ ] Test import completed and row count/PK enforcement verified

---

## Notes

(Record any deviations from the standard pattern, constraints imposed by the project, or decisions that may need to be revisited.)
