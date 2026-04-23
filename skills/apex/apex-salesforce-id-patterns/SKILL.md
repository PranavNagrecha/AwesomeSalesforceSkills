---
name: apex-salesforce-id-patterns
description: "Use when working with Salesforce Ids in Apex — validating Id format, detecting the target sObject type from a string Id, or safely handling 15 vs 18-character Ids. Trigger keywords: Id prefix, Id.valueOf, Id.getSobjectType, 15-char, 18-char, case-insensitive Id. NOT for: record access / sharing decisions (see apex-user-and-permission-checks), or bulk Id collection patterns (see apex-bulk-patterns)."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "How do I tell what object an Id belongs to in Apex?"
  - "A user pasted a 15-character Id and my code is comparing it to an 18-character Id from a SOQL result"
  - "I need to validate that a user-supplied string is a real Salesforce Id before querying with it"
tags:
  - apex-salesforce-id-patterns
  - apex-id-prefix
  - apex-id-validation
  - apex-schema-describe
inputs:
  - "The string being treated as an Id (raw, external-system, user-typed, or SOQL-returned)"
  - "The expected sObject type, if the caller has a constraint"
outputs:
  - "Guidance on safe Id handling, validation, and type detection"
  - "Checker findings for unsafe Id string usage"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-23
---

# Apex Salesforce Id Patterns

Activate this skill when Apex must reason about a Salesforce Id — validating it came from a real record, determining which sObject it points to, or comparing Ids across the 15/18-character boundary. It covers the difference between `String` and `Id` types, the prefix-based describe lookup, and case sensitivity of 15-character Ids.

---

## Before Starting

Gather this context before working on anything in this domain:

- Where does the Id come from? User input, external system, URL parameter, SOQL result, or trigger context?
- Is the Id expected to be one specific sObject, or could it be any of several?
- Do you need the **record**, or just the **sObject type**? Type detection is cheap (no SOQL). Fetching the record is not.
- Are both 15-char (case-sensitive) and 18-char (case-insensitive) versions potentially in play?

---

## Core Concepts

### 15 vs 18 Character Ids

- 15-char Ids are **case-sensitive**. `005A000000ABCdE` and `005A000000abcde` are different records.
- 18-char Ids append a 3-character checksum that makes them **case-insensitive** safe to compare as strings.
- The Apex `Id` type **normalizes to 18 characters** on assignment. Comparing `Id == Id` always works.
- Comparing **strings** across the boundary (e.g., a 15-char URL param to an 18-char SOQL result) will return `false` without warning.

### Apex `Id` Is A Typed Value, Not Just A String

- `Id` is a primitive type. Assigning an invalid string to `Id` throws `System.StringException`.
- `Id.valueOf(str)` validates format and sobject-type legitimacy — it throws if the prefix is not a known sObject.
- Prefer `Id` typing over `String` in method signatures when the parameter must be a Salesforce Id.

### Detecting sObject Type From An Id

Two mechanisms, same result:

1. `myId.getSobjectType()` — returns the `Schema.SObjectType` for a typed `Id`. Cheap, no SOQL.
2. `Schema.getGlobalDescribe().get(myId.substring(0,3))` — prefix lookup, but not all prefixes are unique (some managed packages overlap, and custom objects share the `a0*` range).

Rule: always prefer `getSobjectType()` on a typed `Id`. Fall back to prefix only if you have a `String` you cannot type yet.

### Key Prefixes To Recognize

| Prefix | sObject |
|---|---|
| `001` | Account |
| `003` | Contact |
| `005` | User |
| `006` | Opportunity |
| `00Q` | Lead |
| `500` | Case |
| `a0x–a0z, a0*` | Custom objects (prefix is org-specific) |
| `00D` | Organization |
| `0F0` | Folder |

Do NOT hardcode custom object prefixes. They are org-specific.

---

## Common Patterns

### Validate A User-Supplied Id Before Using It

**When to use:** A controller receives an `Id` from a URL, Experience Cloud form, or external integration.

**How it works:**

```apex
public static Account fetchAccount(String rawId) {
    Id accountId;
    try {
        accountId = (Id) rawId;
    } catch (System.StringException e) {
        throw new AuraHandledException('Invalid Id format.');
    }
    if (accountId.getSobjectType() != Account.SObjectType) {
        throw new AuraHandledException('Id does not belong to an Account.');
    }
    return [SELECT Id, Name FROM Account WHERE Id = :accountId WITH USER_MODE LIMIT 1];
}
```

**Why not the alternative:** Querying directly with an unvalidated string either throws `QueryException` (wrong prefix) or a less helpful `StringException` with no caller guidance.

### Detect Type Across A Heterogeneous List Of Ids

**When to use:** An Apex method accepts `List<Id>` where entries may belong to different sObjects.

**How it works:**

```apex
Map<Schema.SObjectType, List<Id>> byType = new Map<Schema.SObjectType, List<Id>>();
for (Id idValue : inputIds) {
    Schema.SObjectType type = idValue.getSobjectType();
    if (!byType.containsKey(type)) byType.put(type, new List<Id>());
    byType.get(type).add(idValue);
}
// Issue one SOQL per type instead of per record.
```

### Normalize 15-Char Id To 18-Char For String Compare

**When to use:** Comparing an Id from an external system or CSV (often 15-char) with an Id from SOQL (always 18-char).

**How it works:** Cast through `Id`: `Id normalized = (Id) fifteenCharString;` — the typed Id is 18 chars and case-insensitive-safe for string compare.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Comparing two Ids you own | `Id == Id` | Apex normalizes to 18 chars automatically |
| Comparing strings from mixed sources | Cast both to `Id` first | 15 vs 18 char mismatch is silent |
| Detecting sObject from a typed Id | `id.getSobjectType()` | No SOQL, no describe overhead |
| Detecting sObject from a string when you cannot trust the prefix | `Id.valueOf(str).getSobjectType()` | Throws if not a legal Id |
| Validating external-system Ids | `try { (Id) str; } catch ...` | Give a helpful error, not a raw exception |
| Routing logic by object | Switch on `Schema.SObjectType` | Safer than hardcoded prefixes |

---

## Recommended Workflow

1. Identify every point the Id crosses a trust boundary — URL, DTO, CSV, external API response.
2. Type the parameter as `Id`, not `String`, everywhere possible.
3. Where the source is untrusted, wrap the cast in a `try/catch` and surface a clear error.
4. Before SOQL, confirm sObject with `getSobjectType()` (not a string prefix compare).
5. Add a negative test: pass an invalid string, an Id for the wrong object, and an empty string; each should fail cleanly.

---

## Review Checklist

- [ ] No hardcoded 3-character prefixes for custom objects.
- [ ] No `String.startsWith('001')` style type detection where an `Id` is available.
- [ ] All untrusted Id inputs are cast through `Id` or `Id.valueOf` with caught `StringException`.
- [ ] SOQL bind variables typed as `Id` or `Set<Id>`, not `String`.
- [ ] Tests cover: invalid format, wrong-type Id, empty/null.

---

## Salesforce-Specific Gotchas

1. **15-char strings do not equal 18-char strings** — always cast to `Id` before a string compare.
2. **Custom object prefixes are org-specific** — `a03` in one org is a different object in another.
3. **`Id.valueOf(null)` throws** — guard null separately.
4. **Some managed-package prefixes collide** with standard orgs — always prefer `getSobjectType()` over prefix lookup.
5. **Trigger `oldMap` keys are typed `Id`** — iterating as `String` loses the type info.
6. **`System.StringException` from `(Id) someString`** is the clue that a caller passed garbage; handle it with intent.
7. **`Id` cannot be deserialized from JSON with a typo** — `JSON.deserialize` silently becomes null on invalid strings, not throw.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `scripts/check_apex_salesforce_id_patterns.py` | Scans for string-prefix Id checks, 15/18 char string compares, and untyped Id parameters |
| `templates/apex-salesforce-id-patterns-template.md` | Work template for validating and typing Id inputs at trust boundaries |

---

## Related Skills

- `apex-user-and-permission-checks` — authorization once an Id has been validated
- `apex-with-user-mode` — enforcing FLS/CRUD on the SOQL that consumes the validated Id
- `apex-bulk-patterns` — when the Id is part of a bulkified collection
