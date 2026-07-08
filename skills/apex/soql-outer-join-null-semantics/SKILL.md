---
name: soql-outer-join-null-semantics
description: "Use when a SOQL child-to-parent relationship query returns more records than expected because relationship queries behave like an outer join — rows with a null foreign key still come back, `WHERE Parent.Field = null` returns children even when the parent record does not exist, Boolean fields compare as false instead of null, and ORDER BY / OR clauses keep the null-foreign-key rows. Also covers the base null-in-WHERE syntax: SOQL has no `IS NULL` / `IS NOT NULL` — filter with `= null` / `!= null` — and an explicit `!= null` guard helps query performance. Trigger keywords: soql outer join, null foreign key, WHERE Parent.Field = null, boolean field = null, relationship query returning null-parent rows, AccountId/WhatId is null, SOQL IS NULL / IS NOT NULL not supported, filter nulls for query performance. NOT for NULLS FIRST/NULLS LAST sort placement (use apex/soql-null-ordering-patterns), general relationship-query syntax and subqueries (use apex/apex-soql-relationship-queries), or SOQL injection / CRUD-FLS enforcement (use apex/soql-security)."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Security
triggers:
  - "why does my soql relationship query return records where the parent account is null"
  - "understand why WHERE Contact.LastName = null returns cases that have no contact"
  - "boolean field soql filter on null returns all the false rows instead of nothing"
  - "find records whose lookup is empty versus records that point at a deleted parent"
  - "getting a null pointer exception reading record.Account.Name after a relationship soql query"
  - "convert a SQL IS NULL / IS NOT NULL filter to the SOQL = null / != null form"
  - "improve soql query performance by filtering out null values in the where clause"
tags:
  - soql-outer-join-null-semantics
  - soql
  - null-semantics
  - relationship-query
  - foreign-key
  - boolean-null
inputs:
  - "The SOQL query (inline Apex, Database.query string, or .soql file) whose result set is larger or smaller than expected"
  - "The relationship being traversed (child sObject, foreign-key field, parent sObject/field)"
  - "Whether you need rows with an empty lookup, rows with a populated lookup, or a true/false boolean filter"
outputs:
  - "A corrected WHERE clause that isolates the intended rows (foreign-key filter vs parent-field filter, explicit true/false boolean comparison)"
  - "Apex that safely traverses the parent relationship after an outer-join query (null-guarded)"
  - "An explanation of why the original result set included null-foreign-key or parent-less rows"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-07-08
---

# SOQL Outer-Join & Null Semantics

This skill activates when a practitioner is surprised by a SOQL relationship query's result set: child records show up even though the lookup is empty, a `WHERE Parent.Field = null` filter returns rows whose parent record doesn't exist, a Boolean filter against `null` returns every "false" record, or Apex throws a `NullPointerException` while walking a parent relationship that came back on an outer-joined row. It explains the documented outer-join behavior of relationship queries and how to write filters that isolate the rows you actually want.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Confirm the query traverses a relationship.** Outer-join semantics apply to child-to-parent relationship queries (dot notation such as `Account.Name`, `Parent__r.Name`, `Contact.LastName`). A flat query over a single object's own fields does not exhibit them.
- **Name the exact goal for the filter.** "Records with an empty lookup," "records with a populated lookup," and "records whose parent field has a specific value" are three different result sets — and the naive filter usually returns a superset. Decide which one you need before writing the WHERE clause.
- **Beware the most common wrong assumption.** Practitioners assume a relationship query, an `ORDER BY` on a related field, or a `WHERE Parent.Field = null` acts like an *inner* join that drops rows with a null foreign key. It does not — the official reference states relationship queries return records "even if the relevant foreign key field has a null value, as with an outer join."
- **Remember Booleans are never null.** A Boolean field cannot hold `null`; the platform treats `null` as `false`. So `WHERE Flag__c = null` does not return "unset" rows — it returns every `false` row.
- **SOQL has no `IS NULL` / `IS NOT NULL`.** Filter null by comparing to the `null` keyword directly — `= null` for unset rows, `!= null` for populated ones (see Core Concepts for the operator list).

> Maturity note: the SOQL and SOSL Reference documents this as standard query-language behavior. It does **not** stamp the behavior with a GA / Beta / Pilot maturity level — do not assert one.

---

## Core Concepts

### SOQL filters null with `= null` / `!= null`, not `IS NULL`

SOQL has no `IS NULL` / `IS NOT NULL` operator. You compare a field to the `null` keyword directly:

```sql
SELECT Id FROM Event   WHERE ActivityDate != null   -- rows that have a value
SELECT Id FROM Account WHERE Test__c = null          -- rows where the field is unset
```

The Comparison Operators reference lists only `=`, `!=`, `<`, `<=`, `>`, `>=`, `LIKE`, `IN`, `NOT IN`, `INCLUDES`, and `EXCLUDES` — there is no `IS NULL` keyword, so a filter pasted in from SQL (`WHERE Field IS NULL`) is a query syntax error, not a working filter.

### Relationship queries are outer joins

A child-to-parent relationship query returns the child row **even when the foreign key is null**. Per the reference: "Relationship SOQL queries return records, even if the relevant foreign key field has a null value, as with an outer join." So this query returns every Case, including Cases with no `AccountId`, and the parent columns come back null for those rows:

```sql
SELECT Id, CaseNumber, Account.Id, Account.Name
FROM Case
ORDER BY Account.Name
```

`ORDER BY` on a relationship field does not filter — "the record is returned even if the foreign key value in a record is null." A Case with an empty `AccountId` still appears when ordering by `Account.Name`.

### A parent-field null check does not mean "no parent"

Testing a parent field for null returns the child row **even if the parent record does not exist**:

```sql
SELECT Id FROM Case WHERE Contact.LastName = null
```

The reference is explicit: "In a WHERE clause that checks for a value in a parent field, the record is returned even if the parent does not exist." That means this filter returns Cases whose `ContactId` is empty **and** Cases whose Contact was deleted or is otherwise unresolvable. You cannot use it to isolate one from the other.

To reliably select rows whose lookup is **unset**, filter the foreign-key field itself (a real field on the base object), not the traversed parent field:

```sql
-- Rows with an empty lookup:
SELECT Id FROM Case WHERE ContactId = null
-- Rows with a populated lookup:
SELECT Id FROM Case WHERE ContactId != null
```

### Boolean fields coerce null to false

Boolean fields don't store `null` — per the reference, on a Boolean field "null matches FALSE values." When a Boolean lives on the outer-joined (parent) side and no matching record exists, it is treated as false. Consequently, comparing a Boolean to `null` is the same as comparing it to a literal:

- `WHERE Flag__c = null` is equivalent to `WHERE Flag__c = false`
- `WHERE Flag__c != null` is equivalent to `WHERE Flag__c = true`

So a Boolean null check never returns an empty set — it returns all the `false` (or all the `true`) rows. Always compare Boolean fields to `true` / `false` explicitly so the intent is unambiguous.

### OR keeps the null-foreign-key rows

In a `WHERE` clause that uses `OR`, a row is returned if it satisfies **any** branch — even if the foreign key is null:

```sql
SELECT Id FROM Contact WHERE LastName = 'Young' OR Account.Name = 'Quarry'
```

A Contact with `LastName = 'Young'` but a null `AccountId` is still returned, because it matches the first branch. The relationship branch does not silently exclude parent-less rows.

---

## Common Patterns

### Isolate records with an empty lookup — filter the foreign key, not the parent field

**When to use:** you want "all Cases with no Account," "all Contacts not linked to an Account," etc.

**How it works:** filter the foreign-key Id column directly: `WHERE AccountId = null` (empty) or `WHERE AccountId != null` (populated). The FK is a scalar field on the base object, so its null test means exactly "unset."

**Why not the alternative:** `WHERE Account.Name = null` traverses the relationship and returns rows even when the parent doesn't exist, mixing "no lookup" with "unresolvable parent." It is a superset of what you asked for.

### Filter Boolean fields with an explicit true/false, never null

**When to use:** any filter on a checkbox / Boolean field, especially one reached through a relationship.

**How it works:** write `WHERE Active__c = false` (or `= true`). This reads as intended and is exactly what the platform evaluates.

**Why not the alternative:** `WHERE Active__c = null` looks like an "unset" filter but is evaluated as `= false`, so it silently returns every inactive row. Reviewers and future maintainers misread it, and on an outer-joined parent Boolean the `false`-coercion widens the set further.

### Add an explicit `!= null` guard to help query performance

**When to use:** a WHERE clause that already constrains a field (an equality or bind-variable match) where null rows are not wanted — especially a selective lookup filter.

**How it works:** pair the value predicate with an explicit not-null term. The Apex Developer Guide states that "explicitly filtering out null values in the WHERE clause allows Salesforce to improve query performance," and its own example combines a bind-variable equality check with a not-null guard:

```sql
SELECT Id FROM MyObject__c WHERE Thread__c = :threadId AND Thread__c != null
```

**Why not the alternative:** returning null rows and dropping them in Apex forces the query to scan and return rows you immediately discard, and passes up the optimizer's chance to skip them. Filter them out in the WHERE clause rather than client-side.

### Guard the parent relationship in Apex after an outer-join query

**When to use:** you iterate query results in Apex and read a parent field (`c.Account.Name`, `child.Parent__r.Name`).

**How it works:** because the query is an outer join, rows with a null foreign key come back with the parent relationship object set to `null`. Null-check the relationship before dereferencing it:

```apex
for (Case c : [SELECT Id, Account.Name FROM Case]) {
    String acctName = (c.Account != null) ? c.Account.Name : '(no account)';
    // ... use acctName
}
```

**Why not the alternative:** `c.Account.Name` on a Case with an empty `AccountId` throws a `System.NullPointerException` at run time — the row exists, but the parent object does not.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Want child rows whose lookup is empty | `WHERE ForeignKeyId = null` (e.g. `AccountId = null`) | FK is a scalar field; its null test means "unset" precisely |
| Want child rows whose lookup is populated | `WHERE ForeignKeyId != null` | Symmetric to the above; does not depend on parent field values |
| Want rows where a parent field has a value | `WHERE Parent.Field = 'x'` | Fine — but know parent-less rows are already excluded by the value match, not by the join |
| Tempted to use `WHERE Parent.Field = null` for "no parent" | Filter the FK Id instead | Parent-field null check also returns rows where the parent doesn't exist |
| Filtering a Boolean / checkbox field | `WHERE Flag__c = true` or `= false` | Booleans are never null; `= null` is read as `= false` |
| Reading a parent field in Apex after the query | Null-guard the relationship (`rec.Parent != null`) | Outer join returns null-FK rows; the parent object is null on those rows |
| Tempted to paste `WHERE Field IS NULL` from SQL | Rewrite as `WHERE Field = null` (or `!= null`) | SOQL has no `IS NULL` / `IS NOT NULL`; compare to the `null` keyword directly |
| Selective equality filter where null rows aren't wanted | Add `AND Field != null` alongside the value predicate | Explicitly filtering nulls in the WHERE clause lets Salesforce improve query performance |
| Need sort placement of null rows (first/last) | Use `apex/soql-null-ordering-patterns` (`NULLS FIRST/LAST`) | That is ordering, not filtering; different concern |

---

## Recommended Workflow

1. **Classify the query.** Confirm it is a child-to-parent relationship query (dot notation) and note every foreign key and parent field it touches.
2. **State the intended result set.** Decide precisely which rows you want — empty lookup, populated lookup, a specific parent value, a true/false flag — before touching the WHERE clause.
3. **Map each filter to the right column.** For "no/has lookup," filter the foreign-key Id (`AccountId`), not the parent field (`Account.Name`). For Boolean intent, write an explicit `= true` / `= false`.
4. **Account for OR and ORDER BY.** Verify that OR branches and ordering on a related field are not silently pulling in null-foreign-key rows you meant to exclude; add an explicit FK filter if they are.
5. **Null-guard the Apex traversal.** Wherever the code reads a parent field, guard the relationship object (`rec.Parent != null`) so outer-joined null-FK rows don't throw a `NullPointerException`.
6. **Verify against data.** Run the query (and the FK-filtered variant) against a sandbox or scratch org with known parent-less rows and confirm the counts match the intended result set.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Null filters use `= null` / `!= null` — no SQL-style `IS NULL` / `IS NOT NULL`
- [ ] "No lookup" / "has lookup" filters test the foreign-key Id field, not a traversed parent field
- [ ] No `WHERE Parent.Field = null` is being used to mean "the parent doesn't exist"
- [ ] Selective equality filters that shouldn't return null rows include an explicit `!= null` guard
- [ ] Every Boolean filter compares to an explicit `true` / `false`, not `null`
- [ ] OR clauses and `ORDER BY` on a related field don't silently include null-foreign-key rows
- [ ] Apex that reads a parent field null-guards the relationship object first
- [ ] The expected row count was confirmed against data that actually contains parent-less rows

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **`WHERE Parent.Field = null` can't tell "no lookup" from "deleted parent"** — it returns the child row in both cases, so it silently over-selects when you meant "records with an empty lookup." Filter the foreign-key Id instead.
2. **A Boolean `= null` filter returns all the `false` rows, not none** — Boolean fields never hold null, so `Flag__c = null` is evaluated as `Flag__c = false`. Teams expecting an empty result set instead get every inactive record.
3. **Reading a parent field in Apex after a relationship query can throw `NullPointerException`** — the outer join returns rows whose foreign key is null, and on those rows the parent relationship object is `null`; `rec.Account.Name` blows up unless you guard it.
4. **SOQL has no `IS NULL` / `IS NOT NULL`** — a null filter pasted in from SQL fails to parse. Compare to the `null` keyword directly with `= null` / `!= null`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Corrected WHERE clause | Filters the foreign-key field (not the parent field) and uses explicit `true`/`false` for Booleans |
| Null-guarded Apex traversal | Loop that checks `rec.Parent != null` before dereferencing parent fields |
| Null-semantics review worksheet | `templates/soql-outer-join-null-semantics-template.md` — walks a query's outer-join and null behavior |
| Static check output | `scripts/check_soql_outer_join_null_semantics.py` findings for risky relationship/Boolean null checks |

---

## Related Skills

- `apex/apex-soql-relationship-queries` — the mechanics of child-to-parent dot notation and parent-to-child subqueries this skill reasons about the null behavior of.
- `apex/soql-null-ordering-patterns` — `NULLS FIRST` / `NULLS LAST` sort *placement* of null rows; complementary to this skill's focus on which rows are *returned*.
- `apex/soql-fundamentals` — general SELECT / WHERE / ORDER BY syntax if the query itself needs building, not just its null handling.
- `apex/soql-security` — enforce CRUD/FLS and prevent injection when the corrected filter is assembled dynamically.
