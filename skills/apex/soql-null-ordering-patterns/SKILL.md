---
name: soql-null-ordering-patterns
description: "Use when SOQL ORDER BY behavior with NULL values surprises a query — null records sorting before non-null, paginated results inconsistent across pages, NULLS FIRST/LAST clauses needed. Triggers: 'soql nulls first', 'soql null sort order', 'pagination missing records with null fields', 'order by skipping null records', 'consistent ordering with optional fields'. NOT for general SOQL optimization (use data/soql-query-optimization) or for ordering of relationship-traversed fields."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
triggers:
  - "soql null sort order is wrong"
  - "soql nulls first vs nulls last"
  - "pagination skips records with null fields"
  - "order by ascending puts nulls at the wrong end"
  - "deterministic ordering when sort field has nulls"
tags:
  - soql
  - apex
  - ordering
  - null-handling
  - pagination
inputs:
  - "the SOQL query and its ORDER BY clause"
  - "how the result is consumed (UI list, pagination, batch processing)"
  - "the percentage of records with null values in the sort field"
outputs:
  - "corrected ORDER BY with NULLS FIRST/LAST or composite tiebreaker"
  - "pagination key strategy for stable cursors"
  - "test data covering null-and-non-null mix"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-30
---

# SOQL NULL Ordering Patterns

Activate when a SOQL query's ORDER BY behaves unexpectedly because of NULL values — null records appearing first when they should appear last, paginated results dropping records, or the same query returning records in a different order on subsequent runs. The skill produces a corrected ORDER BY clause, a pagination-stable cursor, and test data that reproduces the original surprise.

---

## Before Starting

Gather this context before working on anything in this domain:

- The exact SOQL query and the field(s) in the ORDER BY clause. Note which are required vs. optional in the schema.
- How results are consumed: rendering in a UI list, paginating with OFFSET/LIMIT, batching across an Apex Batch, exporting to a downstream system. Pagination is the context where null ordering most often produces *missing* records, not just misplaced ones.
- Approximately what percentage of records have null in the sort field. With <1% null, the issue may surface only on one specific report; with 30% null, it's a daily complaint.

---

## Core Concepts

### Default null ordering in SOQL

SOQL's default ordering treatment of nulls is:

- `ORDER BY field ASC` → NULLS **FIRST** (nulls come before non-null values)
- `ORDER BY field DESC` → NULLS **LAST** (nulls come after non-null values)

The default was chosen for consistency with SQL's "nulls are smallest" convention but is the *opposite* of what most users expect for ASC ("blank should mean 'unknown', sort to end"). Salesforce supports an explicit `NULLS FIRST` and `NULLS LAST` clause to override the default.

### Composite tiebreakers

ORDER BY on a single field with duplicates produces non-deterministic intra-tie ordering. The same query rerun may return ties in a different order. This becomes a bug under pagination: if records A and B tie on the sort field and the page boundary lands between them, page 2 may start with A (shifted from page 1) or with B, causing record duplication or omission.

The fix is a composite tiebreaker on a guaranteed-unique field, almost always `Id`:

```soql
ORDER BY Last_Activity_Date__c DESC NULLS LAST, Id ASC
```

`Id` ASC is deterministic and effectively free at the index level.

### Pagination-stable cursors

OFFSET-based pagination breaks when the underlying data shifts between pages. Cursor-based pagination (filter on the last seen sort key + tiebreaker) is the only stable approach above a few thousand records:

```soql
WHERE (Last_Activity_Date__c < :cursorDate
       OR (Last_Activity_Date__c = :cursorDate AND Id > :cursorId))
ORDER BY Last_Activity_Date__c DESC NULLS LAST, Id ASC
LIMIT 200
```

The `cursorDate` may be null on the first page; the WHERE clause must handle that case explicitly (commonly, treat the first page as `LIMIT 200` with no WHERE).

---

## Common Patterns

### Pattern: ASC with nulls at the end

**When to use:** UI list "sort by Last Activity ascending" — users expect oldest activity first, blanks last.

**How it works:** `ORDER BY Last_Activity_Date__c ASC NULLS LAST, Id ASC`. The explicit `NULLS LAST` overrides SOQL's default.

**Why not the alternative:** `ORDER BY ... ASC` alone places null records at the top of the list, confusing users.

### Pattern: pagination over a nullable sort field

**When to use:** Batch processing 200k records sorted by `Last_Activity_Date__c`.

**How it works:** Cursor-based pagination keyed by `(sortField, Id)`. First page fetches `LIMIT 200`; subsequent pages filter with `WHERE` clause referencing the last seen `(sortField, Id)`.

**Why not the alternative:** OFFSET/LIMIT is bounded at 2,000 in SOQL and produces unstable results when records are inserted/updated mid-pagination.

### Pattern: composite sort with mixed null behavior

**When to use:** Sort by region (required, ASC) then by score (nullable, DESC nulls last).

**How it works:** `ORDER BY Region__c ASC, Score__c DESC NULLS LAST, Id ASC`. Each field gets its own NULLS clause as needed.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single-field ASC with nullable field | `... ASC NULLS LAST, Id ASC` | Matches user mental model for blanks |
| Single-field DESC with nullable field | `... DESC NULLS LAST, Id ASC` | DESC default already places nulls last; tiebreaker still needed for pagination |
| Pagination over a nullable field | Cursor pagination, never OFFSET | OFFSET breaks when data shifts |
| Sort by relationship field (`Account.Name`) | Treat the same way; relationship fields can be null too | Same NULLS clause grammar |
| Streaming export sorted by date | Cursor on `(date, Id)` | Stable across the multi-hour export window |

---

## Recommended Workflow

1. Identify the sort field(s) and check schema for `required=false` or formula fields that may emit null.
2. Decide where nulls should appear given the user/consumer mental model. Default SOQL behavior is rarely what users want for ASC.
3. Add explicit `NULLS FIRST` / `NULLS LAST` to every nullable-field ORDER BY clause.
4. Add `Id` (or another guaranteed-unique field) as the final tiebreaker — always.
5. If pagination is in scope, switch from OFFSET to cursor-based pagination keyed on `(sortField, Id)`. The first-page cursor handles the null-cursor case.
6. Build a test dataset with mixed null and non-null values; verify pagination across a page boundary that splits ties.
7. Document the ordering contract (NULLS LAST, tiebreaker by Id) in the data layer's interface so future readers don't reinvent.

---

## Review Checklist

- [ ] Every nullable field in ORDER BY has explicit NULLS FIRST/LAST
- [ ] Every ORDER BY has `Id` (or unique field) as final tiebreaker
- [ ] No OFFSET above ~500 records — switch to cursor pagination
- [ ] First-page cursor case handled (typically a no-WHERE first call)
- [ ] Tests cover mixed null/non-null data and tie-on-boundary pagination
- [ ] Ordering contract documented in selector/repository class

---

## Salesforce-Specific Gotchas

1. **Default null position flips with direction** — ASC defaults to NULLS FIRST; DESC defaults to NULLS LAST. Many bugs come from assuming a single default.
2. **OFFSET caps at 2,000** — Beyond that, SOQL throws. Cursor pagination is the only path for large result sets.
3. **Formula fields can be null even with non-null inputs** — A formula's null-handling (`BLANKVALUE`, `IF(ISBLANK(...))`) determines whether the formula emits null. Sorting on a formula needs the same NULLS clause discipline.
4. **Indexes don't include nulls by default** — Sorting on a high-null-percentage field can full-scan even when the field is custom-indexed. Custom indexes can be configured with null-inclusion via Support.
5. **`NULLS LAST` is a keyword pair, not a function** — `NULLS_LAST`, `NULLSLAST`, or `NULLS-LAST` are syntax errors.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Corrected ORDER BY clause | With NULLS FIRST/LAST and Id tiebreaker |
| Pagination cursor pattern | If pagination in scope, the cursor-based replacement |
| Test data factory | Apex factory producing mixed null/non-null records |
| Data-layer ordering contract | Documented in the selector class header |

---

## Related Skills

- data/soql-query-optimization — for the broader query plan and indexing concerns
- apex/soql-fundamentals — for foundational SOQL grammar
- apex/test-data-factory-patterns — for building the mixed null/non-null test fixtures
