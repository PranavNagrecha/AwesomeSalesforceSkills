---
name: sosl-external-object-search-limits
description: "Use when a SOSL search (or global search) against a Salesforce Connect external object misbehaves: it returns no records, rejects an operator/function/clause, or silently drops matches. Covers the query-level rules that apply only to external objects — searchable field types (text only), the mandatory RETURNING clause, the 100-character search-string cap, unsupported operators (INCLUDES / LIKE / EXCLUDES), unsupported functions (toLabel / convertCurrency), unsupported clauses (UPDATE TRACKING / UPDATE VIEWSTAT / WITH DATA CATEGORY / WITH), and adapter-scoped limits (OData logical operators in FIND; custom-adapter convertCurrency and WITH). NOT for enabling search in Setup (use admin/global-search-configuration), NOT for SOSL against standard/custom sObjects (use data/sosl-search-patterns), NOT for general Salesforce Connect / external-object setup (use integration/salesforce-connect-external-objects), and NOT for SOQL of external objects."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "searching a Salesforce Connect external object with SOSL returns no records even though rows exist"
  - "SOSL FIND with LIKE or INCLUDES throws an unsupported-operator error on an external object"
  - "external object rows are missing from global search or SOSL results after syncing the external data source"
  - "which field types on an external object can I actually search with SOSL"
  - "my external-object SOSL search string over 100 characters is being rejected"
tags:
  - sosl
  - external-objects
  - salesforce-connect
  - search
  - odata
inputs:
  - "A SOSL query (or global-search scenario) that targets a Salesforce Connect external object (an object whose API name ends in __x)"
  - "The external object's adapter type (OData 2.0/4.0 or a custom Apex Connector Framework adapter) and its searchable text fields"
outputs:
  - "A corrected, external-object-safe SOSL statement: explicit RETURNING, search string of 100 or fewer characters, no unsupported operators/functions/clauses"
  - "A diagnosis of why an external-object search returns no records or errors, plus the enablement or adapter-scoped fix"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-07-08
---

# SOSL External Object Search Results Limits

This skill activates when SOSL (or the global search box that runs on SOSL) is pointed at a
Salesforce Connect **external object** and behaves differently from a standard sObject search —
returning nothing, erroring on a normally valid operator, or dropping the external object from
the results. External objects (`__x`) map to data that lives outside the org through an OData
2.0/4.0 adapter or a custom Apex Connector Framework adapter, and the SOSL reference documents a
narrow set of extra constraints that only apply to them.

The primary authority is the SOQL and SOSL Reference page *SOSL Limits on External Object Search
Results*. That page carries **no GA/Beta/Pilot maturity label**; treat these as standard platform
behavior for external-object search and do not assert a maturity level the docs don't state.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Confirm it's actually an external object.** External objects end in `__x` and are backed by an
  external data source (Salesforce Connect). The rules here do **not** apply to standard or custom
  (`__c`) sObjects — those follow `data/sosl-search-patterns`.
- **Know the adapter type.** Three of the limits are adapter-scoped: OData 2.0/4.0 adapters reject
  logical operators in the FIND clause, and custom (Apex Connector Framework) adapters reject
  `convertCurrency()` and generic `WITH` clauses. Everything else applies to all external objects.
- **Verify search is enabled at both layers.** An external object is searchable only when search is
  enabled on **both** the external object and its external data source. This is the single most
  common cause of "returns no records."
- **Identify the searchable fields.** Only `Text`, `Text Area`, and `Text Area (Long)` fields on an
  external object are searchable. An object with zero searchable fields returns no records — with no
  error to tell you why.

---

## Core Concepts

### Concept 1: Search is enabled at two layers, and Sync overwrites the object layer

To surface an external object in SOSL and global search, enable search on **both** the external
object and the external data source. The trap: **syncing the external data source always overwrites
the external object's search status to match the data source's.** If the data source has search
off, every sync silently flips the object's search flag off again — so a search that worked
yesterday can stop working after a routine sync with no code or query change.

### Concept 2: Only text-type fields are searchable, and "no searchable fields" is silent

Only `Text`, `Text Area`, and `Text Area (Long)` fields on external objects can be searched. Number,
date, checkbox, picklist, and lookup fields are never part of the SOSL index for an external object.
If an external object has **no searchable fields at all**, searches on it **return no records** — the
platform does not raise an error. This reads to callers as "the data isn't there," when the real
cause is that nothing on the object is indexable.

### Concept 3: External objects are opt-in to results — RETURNING is mandatory

For standard objects, `FIND {term} IN ALL FIELDS` will surface matches across the searchable objects.
External objects are different: **an external object must be named explicitly in a `RETURNING` clause
or its matches never appear in the results.** A SOSL statement with no `RETURNING`, or a `RETURNING`
that lists only standard objects, will silently exclude the external object even when it matches.

### Concept 4: A specific set of operators, functions, and clauses is unsupported

Against external objects, SOSL rejects (for **all** external objects):

- **Operators:** `INCLUDES`, `LIKE`, `EXCLUDES`
- **Function:** `toLabel()`
- **Clauses:** `UPDATE TRACKING`, `UPDATE VIEWSTAT`, `WITH DATA CATEGORY`
- **Search-string length:** the search text must be **100 or fewer characters**

And two adapter-scoped groups:

- **OData 2.0/4.0 adapters only:** logical operators (`AND` / `OR` / `AND NOT`) in the FIND clause are
  not supported.
- **Custom (Apex Connector Framework) adapters only:** the `convertCurrency()` function and generic
  `WITH` clauses are not supported.

Getting the adapter scope right matters: `convertCurrency()` and `WITH` are a problem for custom
adapters, not for OData; logical operators in FIND are a problem for OData, not (by this rule) for
custom adapters. Don't flag them universally.

---

## Common Patterns

### Pattern: Write an external-object-safe SOSL statement

**When to use:** any SOSL that targets an external object, in Apex or the Query Editor.

**How it works:** name the external object explicitly in `RETURNING`, list only text fields you
searched, keep the FIND term at 100 characters or fewer, and use wildcards (`*`, `?`) instead of
`LIKE`.

```apex
List<List<SObject>> hits = [
    FIND 'Acme*'
    IN ALL FIELDS
    RETURNING Order__x(ExternalId__c, AccountName__c, Description__c)
];
List<Order__x> orders = (List<Order__x>) hits[0];
```

**Why not the alternative:** dropping the `RETURNING Order__x(...)` (or relying on `IN ALL FIELDS`
alone) makes the external object silently absent from results — the query "works" but returns nothing
from that object.

### Pattern: Diagnose "external object returns no records"

**When to use:** the search runs without error but yields nothing from the external object.

**How it works:** walk the four silent causes in order:

1. Is search enabled on **both** the external object **and** the external data source? (Re-check after
   any recent sync — sync overwrites the object flag.)
2. Does the object have at least one searchable **text** field?
3. Is the object named explicitly in the `RETURNING` clause?
4. Is the FIND term within 100 characters and free of unsupported operators?

**Why not the alternative:** treating it as a data-availability or connectivity problem sends you into
the adapter/endpoint when the fix is almost always one of these four query/enablement conditions.

### Pattern: Replace an unsupported operator, function, or clause

**When to use:** SOSL errors on the external object with an unsupported-feature message, or you're
porting a standard-object query.

**How it works:** substitute the supported equivalent:

| Unsupported on external object | Use instead |
|---|---|
| `LIKE 'Acme%'` | wildcard in FIND: `FIND 'Acme*'` |
| `INCLUDES` / `EXCLUDES` (multi-select semantics) | not available — filter in Apex after the search, or query the source system |
| `toLabel(field)` | return the raw field; translate in the client |
| `convertCurrency()` (custom adapter) | return the raw amount; convert in Apex |
| `WITH DATA CATEGORY` / `WITH ...` | remove the clause |

**Why not the alternative:** leaving the unsupported token in place fails the whole SOSL statement, not
just the external-object portion.

---

## Decision Guidance

| Symptom | Most likely cause | Fix |
|---|---|---|
| External object returns no records, no error | Search disabled on object or data source (often reset by a sync) | Re-enable search on both layers; re-verify after each sync |
| Still no records after enabling search | No searchable (text) field on the object | Add/mark a `Text`/`Text Area`/`Long Text Area` field as searchable |
| Object matches but is absent from results | External object not in `RETURNING` | Add `RETURNING <Object>__x(fields)` explicitly |
| `unsupported operator` on a normally valid query | `INCLUDES` / `LIKE` / `EXCLUDES` used | Use wildcards in FIND; post-filter in Apex |
| Query fails only on OData-backed object | Logical operators (`AND`/`OR`/`NOT`) in FIND | Split into separate searches; combine results in code |
| Query fails only on custom-adapter object | `convertCurrency()` or `WITH` used | Remove the function/clause; convert or filter in the client |
| Long search string rejected | FIND term exceeds 100 characters | Trim the term to ≤100 characters |

---

## Recommended Workflow

Step-by-step for an AI agent or practitioner working an external-object SOSL task:

1. **Classify the target.** Confirm the object ends in `__x` and note its adapter type (OData 2.0/4.0
   vs custom Apex Connector Framework). If it's a `__c`/standard object, route to
   `data/sosl-search-patterns` instead.
2. **Confirm enablement.** Verify search is enabled on both the external object and the external data
   source, and that the object has at least one searchable text field. Flag that a data-source sync
   overwrites the object's search flag.
3. **Build the SOSL statement.** Name the external object explicitly in `RETURNING` with only text
   fields, keep the FIND term ≤100 characters, and use wildcards rather than `LIKE`.
4. **Strip unsupported tokens.** Remove `INCLUDES`/`EXCLUDES`, `toLabel()`, `UPDATE TRACKING`,
   `UPDATE VIEWSTAT`, `WITH DATA CATEGORY`. For OData remove logical operators from FIND; for custom
   adapters remove `convertCurrency()` and generic `WITH`.
5. **Lint it.** Run `scripts/check_sosl_external_object_search_limits.py` against the query or source
   tree to catch any remaining external-object violations, passing `--adapter odata` or
   `--adapter custom` when the adapter is known.
6. **Verify results.** Run the search; if it still returns nothing, walk the four silent causes from
   the diagnose pattern before touching the adapter/endpoint.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Search is enabled on **both** the external object and the external data source (re-verified after any recent sync)
- [ ] The object has at least one searchable `Text` / `Text Area` / `Long Text Area` field
- [ ] The external object is named explicitly in the `RETURNING` clause
- [ ] The FIND search string is 100 or fewer characters
- [ ] No `INCLUDES` / `LIKE` / `EXCLUDES` operator, `toLabel()`, `UPDATE TRACKING`, `UPDATE VIEWSTAT`, or `WITH DATA CATEGORY` against the external object
- [ ] For OData adapters: no logical operators (`AND`/`OR`/`AND NOT`) in the FIND clause
- [ ] For custom adapters: no `convertCurrency()` and no generic `WITH` clause
- [ ] No maturity claim (GA/Beta/Pilot) asserted beyond what the reference states

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Sync silently disables search** — syncing the external data source overwrites the external
   object's search status to match the data source's. A working search can break after a routine sync
   with no query change and no error.
2. **"No searchable fields" returns zero records, not an error** — if nothing on the object is a text
   field (or none are marked searchable), every search comes back empty, masquerading as a data or
   connectivity problem.
3. **External objects are excluded from results unless named in RETURNING** — `IN ALL FIELDS` does not
   pull an external object into the result set; it must appear explicitly in `RETURNING`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Corrected SOSL statement | An external-object-safe `FIND ... RETURNING <Object>__x(text fields)` with a ≤100-char term and no unsupported tokens |
| Diagnosis note | The identified silent cause (enablement, no searchable field, missing RETURNING, term length) and its fix |
| `scripts/check_sosl_external_object_search_limits.py` | Stdlib linter that flags external-object SOSL violations, adapter-aware |
| `templates/sosl-external-object-search-limits-template.md` | Review worksheet with a safe-SOSL skeleton and a restriction-compliance matrix |

---

## Related Skills

- `data/sosl-search-patterns` — general SOSL against standard/custom sObjects; the baseline this skill diverges from for external objects.
- `data/sosl-search-result-limits` — result-count / SOSL row limits that apply to searches generally (a different limit family than these external-object rules).
- `data/sosl-with-clauses` — the `WITH` clauses (SNIPPET, HIGHLIGHT, NETWORK, etc.) that custom-adapter external objects don't support.
- `integration/salesforce-connect-external-objects` — designing the external object, data source, and adapter this skill searches.
- `admin/global-search-configuration` — enabling search (the Allow Search toggles, index behavior) that must be on before any of this applies.
