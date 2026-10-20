---
name: apex-schema-describe
description: "Apex Schema describe API patterns — `Schema.getGlobalDescribe()`, `SObjectType.getDescribe()`, `DescribeFieldResult`, `getPicklistValues()`, the per-namespace describe cost, the lazy-vs-eager caching pattern, `SObjectField.getDescribe()` overhead at scale, and the FLS / record-type metadata access patterns. NOT for building dynamic SOQL or dynamic field get/put — use apex/dynamic-apex. NOT for the Tooling API metadata layer — use apex/tooling-api-patterns."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Security
triggers:
  - "schema getGlobalDescribe performance cost loop"
  - "describe field FLS check apex"
  - "SObjectType picklist values getPicklistValues"
  - "schema getsobjecttype dynamic apex"
  - "describe record type apex metadata"
  - "apex schema cache static final pattern"
  - "schema getGlobalDescribe loop hot path CPU describe"
tags:
  - schema
  - describe
  - sobject-type
  - field-level-security
  - dynamic-apex
inputs:
  - "What needs to be discovered: SObject type, field metadata, picklist values, record types"
  - "Whether the describe runs once per request or per record (loop hot path)"
  - "Whether the field is dynamic (string at runtime) or known at compile time"
outputs:
  - "Describe pattern with appropriate caching"
  - "FLS / sharing check using the right API"
  - "Picklist value enumeration with correct active-only filtering"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# Apex Schema Describe

Schema describe is one of the most-used and most-misused APIs in
Apex. `Schema.getGlobalDescribe()` looks free — it isn't. Calling
`SObjectField.getDescribe()` per record in a 200-record trigger
multiplies a small cost into a CPU-budget problem. FLS checks
against `DescribeFieldResult.isAccessible()` look correct — but
the API surface has subtle differences between
`Schema.SObjectType.newSObject()` describe and
`Schema.DescribeFieldResult` describe.

This skill covers the patterns that make Schema describe fast
and correct: caching, FLS checks, picklist enumeration, and the
loop-cost trap.

NOT for SOQL string-binding (`apex/apex-dynamic-soql-binding-safety`); NOT for
Tooling API metadata work (`apex/tooling-api-patterns`).

---

## Before Starting

- **Identify the call site.** One-shot at request start (cheap,
  any pattern works) vs in a loop (must cache).
- **Identify what you need.** SObjectType reference,
  DescribeSObjectResult, DescribeFieldResult, picklist values —
  each has a different API call.
- **Identify whether the input is static or dynamic.** Compile-time
  known type → use `MyObj__c.SObjectType` directly (no describe
  call). Runtime string → `Schema.getGlobalDescribe().get(name)`.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Does the describe run once per request or inside a per-record loop? | Gotchas 1–2: loop placement multiplies the call | Tells you whether a transaction-scoped `static` cache is required |
| Is the object/field known at compile time? | Gotcha 1: a token needs no global describe | Lets you drop `getGlobalDescribe()` entirely |
| Does the code run inside, or call into, a namespaced package? | Gotcha 5: map keys carry the running code's namespace | The exact key string to look up |
| Do you need inactive picklist values too? | Gotcha 3: `getPicklistValues()` returns active values only | Whether a different source (metadata) is needed |
| Is a record type looked up by label or DeveloperName? | Gotcha 6: labels are renameable | A lookup that survives an admin rename |
| Is the FLS check for one field or for a bulk DML list? | Gotcha 7: per-field checks do not strip values | Picks `isAccessible()` vs `stripInaccessible` |
| Is the field name a runtime string? | Gotcha 8: field-map keys are case-insensitive | Removes needless `toLowerCase()` normalising |

A proper configuration caches what the transaction reuses and checks the user's access once, where "just doing it" describes per record and trusts stale assumptions about the map.

---

## Core Concepts

### Static-vs-runtime SObjectType lookup

```apex
// Compile-time: zero describe cost
Schema.SObjectType t = Account.SObjectType;

// Runtime (string): one global-describe lookup
Schema.SObjectType t = Schema.getGlobalDescribe().get('Account');
```

`Schema.getGlobalDescribe()` returns a map of every sObject name the
running user can see to its token (apexdev 264 L11244-11249); tokens are
the lightweight path (apexdev 264 L10919). That it is the expensive call
is UNVERIFIED (2026-10-20): the guide gives no cost figure. Cache the
result if you call it more than once per transaction. To describe several
runtime names at once, use `Schema.describeSObjects(List<String>)` (apexref 262
L229191); its `describeSObjects(types, SObjectDescribeOptions)` overload
documents `SObjectDescribeOptions.DEFERRED` (lazy) as its default
(apexref 262 L229225-229227).

### Caching describe results

```apex
public class SchemaCache {
    private static final Map<String, Schema.SObjectType> TYPES =
        Schema.getGlobalDescribe();
    private static final Map<String, Map<String, Schema.SObjectField>> FIELDS_BY_TYPE =
        new Map<String, Map<String, Schema.SObjectField>>();

    public static Schema.SObjectField field(String objName, String fieldName) {
        Map<String, Schema.SObjectField> fields = FIELDS_BY_TYPE.get(objName);
        if (fields == null) {
            Schema.SObjectType t = TYPES.get(objName);
            if (t == null) return null;
            fields = t.getDescribe().fields.getMap();
            FIELDS_BY_TYPE.put(objName, fields);
        }
        return fields.get(fieldName);
    }
}
```

`static final` ensures the global describe runs once per transaction
(a static is static only within the Apex transaction, apexdev 264 L3746).
Per-type field maps are lazy.

### FLS check via DescribeFieldResult

```apex
Schema.DescribeFieldResult dfr = Account.SSN__c.getDescribe();
if (!dfr.isAccessible()) {
    throw new SecurityException('No FLS read');
}
if (!dfr.isUpdateable()) {
    throw new SecurityException('No FLS update');
}
```

Modern alternative — `Security.stripInaccessible` (preferred for
DML) handles bulk records:

```apex
SObjectAccessDecision dec = Security.stripInaccessible(
    AccessType.UPDATABLE, records
);
update dec.getRecords();
```

### Picklist value enumeration

```apex
List<Schema.PicklistEntry> entries =
    Account.Industry.getDescribe().getPicklistValues();

List<String> activeValues = new List<String>();
for (Schema.PicklistEntry pe : entries) {
    if (pe.isActive()) {
        activeValues.add(pe.getValue());  // API name; use getLabel() for display
    }
}
```

Corrected 2026-10-20: `getPicklistValues()` returns active entries only
— "Only active picklist values are returned" (apexref 262 L190851). The
`isActive()` test above is a harmless no-op, not a required filter; the
earlier claim that inactive entries appear in the list was wrong.

---

## Common Patterns

### Pattern A — Hot-path describe with class-level cache

```apex
public class FieldValidator {
    private static final Map<String, Schema.SObjectField> FIELDS =
        Account.SObjectType.getDescribe().fields.getMap();

    public static Boolean isAccessible(String fieldName) {
        Schema.SObjectField f = FIELDS.get(fieldName);
        return f != null && f.getDescribe().isAccessible();
    }
}
```

`static final` + per-type field map = describe runs once per
class load.

### Pattern B — Bulk FLS via stripInaccessible

```apex
public static List<Account> readAccessible(List<Account> records) {
    SObjectAccessDecision dec = Security.stripInaccessible(
        AccessType.READABLE, records
    );
    return (List<Account>) dec.getRecords();
}
```

Strips fields the user cannot access (apexdev 264 L12281-12282) —
bulk-safe; "governor-cheap" is UNVERIFIED (2026-10-20), no cost figure in the guide.

### Pattern C — Dynamic SObject creation by name

```apex
public static SObject create(String objName) {
    Schema.SObjectType t = Schema.getGlobalDescribe().get(objName);
    if (t == null) throw new IllegalArgumentException(objName);
    return t.newSObject();
}
```

Use `Schema.getGlobalDescribe().get(name)` + `newSObject()` — the
guide's documented dynamic-creation path (apexdev 264 L11795-11801).
`Type.forName('Account')` does resolve (it equals `Account.class`, apexref
262 L242043-242045) but returns `System.Type` whose `newInstance()` returns
`Object` (apexref 262 L242303); whether that yields a usable sObject is
UNVERIFIED (2026-10-20): the reference documents it for classes only.

---

## Decision Guidance

| Situation | Approach | Reason |
|---|---|---|
| Compile-time-known SObject type | `Account.SObjectType` directly | Zero describe cost |
| Runtime SObject name as string | `Schema.getGlobalDescribe().get(name)` | The only path for string-driven |
| Repeated describe in a loop | Cache as `static final` | Avoid per-iteration describe overhead |
| FLS check before bulk DML | `Security.stripInaccessible` | Bulk-safe; cleaner than per-field |
| FLS check on a single field | `getDescribe().isAccessible()` | Single-field is fine direct |
| List of active picklist values | `getPicklistValues()` | Returns active values only (apexref 262 L190851) |
| Several runtime type names at once | `Schema.describeSObjects(names)` | One call, many results (apexref 262 L229191) |
| RecordType lookup by name | `getRecordTypeInfosByDeveloperName().get(name)` | Labels are what `ByName` keys on (apexref 262 L192589) |
| Schema query on managed-package object | Include namespace prefix | Required for cross-package access |

---

## Recommended Workflow

1. **Identify call frequency.** Loop body = cache. One-shot = anywhere.
2. **Use compile-time references when possible.** Skip describe entirely.
3. **For dynamic strings, cache `Schema.getGlobalDescribe()` once.**
4. **For FLS on bulk DML, use `Security.stripInaccessible`.**
5. **For picklist enumeration, rely on `getPicklistValues()` returning active values only** (apexref 262 L190851).
6. **Test the namespaced case** if managed packages are in scope, then run `scripts/check_apex_schema_describe.py --manifest-dir force-app` (add `--strict` in CI).

---

## Review Checklist

- [ ] No `Schema.getGlobalDescribe()` inside loops.
- [ ] Per-type field map cached as `static final` when used in hot paths.
- [ ] FLS checks use `Security.stripInaccessible` for bulk DML.
- [ ] Picklist code does not assume inactive values are returned (they are not).
- [ ] Dynamic SObject creation uses `Schema.getGlobalDescribe().get(name).newSObject()`.
- [ ] Managed-package SObjects include namespace prefix.

---

## Salesforce-Specific Gotchas

1. **`Schema.getGlobalDescribe()` returns every visible sObject.** Cache it; its cost is UNVERIFIED (2026-10-20). (See `references/gotchas.md` § 1.)
2. **`getDescribe()` on a field in a loop multiplies cost.** Cache the field map at class scope. (See `references/gotchas.md` § 2.)
3. **`getPicklistValues()` returns active entries only** (apexref 262 L190851) — no inactive values to filter. (See `references/gotchas.md` § 3.)
4. **`Type.forName` returns `System.Type`, not SObjectType.** Use `Schema.getGlobalDescribe().get()`. (See `references/gotchas.md` § 4.)
5. **Managed-package fields require the namespace prefix.** (See `references/gotchas.md` § 5.)
6. **Field-map keys are case-insensitive** — "All field names are case insensitive" (apexdev 264 L11079). (See `references/gotchas.md` § 8.)

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Cached schema utility class | `static final` field maps; one place to evolve |
| FLS-aware DML helpers | `stripInaccessible`-based wrappers for bulk DML |
| Picklist enumeration helpers | Active-only value lists with label-vs-API distinction |

---

## Related Skills

- `apex/dynamic-apex` — broader dynamic-Apex patterns; this skill is the schema-describe slice.
- `apex/apex-dynamic-soql-binding-safety` — SOQL string binding (different concern: SOQL injection prevention).
- `apex/apex-switch-on-sobject` — when describe-driven dispatch fits a switch-on-SObject pattern.
- `apex/apex-stripinaccessible-and-fls-enforcement` — broader FLS enforcement; this skill is the describe slice.
