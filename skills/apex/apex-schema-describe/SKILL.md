---
name: apex-schema-describe
description: "Apex Schema describe API patterns — `Schema.getGlobalDescribe()`, `SObjectType.getDescribe()`, `DescribeFieldResult`, `getPicklistValues()`, and the per-namespace describe cost. Covers the lazy-vs-eager describe pattern (cache the SObjectType reference, not the full describe), the `SObjectField.getDescribe()` overhead at scale, and the FLS / record-type metadata access patterns. NOT for SOQL injection prevention via Schema (use apex/dynamic-soql), NOT for the Tooling API metadata layer (use apex/tooling-api)."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-05
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

NOT for SOQL string-binding (`apex/dynamic-soql`); NOT for
Tooling API metadata work (`apex/tooling-api`).

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

## Core Concepts

### Static-vs-runtime SObjectType lookup

```apex
// Compile-time: zero describe cost
Schema.SObjectType t = Account.SObjectType;

// Runtime (string): one global-describe lookup
Schema.SObjectType t = Schema.getGlobalDescribe().get('Account');
```

`Schema.getGlobalDescribe()` is the expensive call — it materializes
the entire org's SObject inventory. Cache the result if you call
it more than once per transaction.

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

`static final` ensures the global describe runs once per class
load. Per-type field maps are lazy.

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

Inactive entries are still in the list — filter explicitly.

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

Removes inaccessible field values from the records — bulk-safe,
governor-cheap.

### Pattern C — Dynamic SObject creation by name

```apex
public static SObject create(String objName) {
    Schema.SObjectType t = Schema.getGlobalDescribe().get(objName);
    if (t == null) throw new IllegalArgumentException(objName);
    return t.newSObject();
}
```

Use `Schema.getGlobalDescribe().get(name)` — NOT `Type.forName(name)`.
Type.forName returns `System.Type`, not an SObject prototype.

---

## Decision Guidance

| Situation | Approach | Reason |
|---|---|---|
| Compile-time-known SObject type | `Account.SObjectType` directly | Zero describe cost |
| Runtime SObject name as string | `Schema.getGlobalDescribe().get(name)` | The only path for string-driven |
| Repeated describe in a loop | Cache as `static final` | Avoid per-iteration describe overhead |
| FLS check before bulk DML | `Security.stripInaccessible` | Bulk-safe; cleaner than per-field |
| FLS check on a single field | `getDescribe().isAccessible()` | Single-field is fine direct |
| List of active picklist values | `getPicklistValues()` + `isActive()` filter | Inactive entries still in the list |
| RecordType lookup by name | `getRecordTypeInfosByDeveloperName().get(name)` | Stable identifier across orgs |
| Schema query on managed-package object | Include namespace prefix | Required for cross-package access |

---

## Recommended Workflow

1. **Identify call frequency.** Loop body = cache. One-shot = anywhere.
2. **Use compile-time references when possible.** Skip describe entirely.
3. **For dynamic strings, cache `Schema.getGlobalDescribe()` once.**
4. **For FLS on bulk DML, use `Security.stripInaccessible`.**
5. **For picklist enumeration, filter `isActive()` explicitly.**
6. **Test the namespaced case** if managed packages are in scope.

---

## Review Checklist

- [ ] No `Schema.getGlobalDescribe()` inside loops.
- [ ] Per-type field map cached as `static final` when used in hot paths.
- [ ] FLS checks use `Security.stripInaccessible` for bulk DML.
- [ ] Picklist enumeration filters by `isActive()`.
- [ ] Dynamic SObject creation uses `Schema.getGlobalDescribe()` not `Type.forName`.
- [ ] Managed-package SObjects include namespace prefix.

---

## Salesforce-Specific Gotchas

1. **`Schema.getGlobalDescribe()` is expensive.** Cache. (See `references/gotchas.md` § 1.)
2. **`getDescribe()` on a field in a loop multiplies cost.** Cache the field map at class scope. (See `references/gotchas.md` § 2.)
3. **Inactive picklist entries appear in `getPicklistValues()`.** Filter. (See `references/gotchas.md` § 3.)
4. **`Type.forName` returns `System.Type`, not SObjectType.** Use `Schema.getGlobalDescribe().get()`. (See `references/gotchas.md` § 4.)
5. **Managed-package fields require the namespace prefix.** (See `references/gotchas.md` § 5.)

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
- `apex/dynamic-soql` — SOQL string binding (different concern: SOQL injection prevention).
- `apex/apex-switch-on-sobject` — when describe-driven dispatch fits a switch-on-SObject pattern.
- `security/field-level-security-design` — broader FLS architecture; this skill is the Apex-side enforcement.
