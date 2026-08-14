---
name: apex-stripinaccessible-and-fls-enforcement
description: "Use Security.stripInaccessible to enforce CRUD/FLS on user-supplied records before DML, and to scrub query results before returning them to clients. Covers AccessType.READABLE/CREATABLE/UPDATABLE/UPSERTABLE, the SObjectAccessDecision API, when to prefer WITH USER_MODE on the SOQL itself, and integration with the SecurityUtils template. NOT for class-level sharing keyword choice (with sharing / without sharing / inherited sharing — see apex-sharing-keywords). NOT for managed sharing or Apex managed sharing recalculations (see sharing-selection decision tree)."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
tags:
  - apex
  - stripinaccessible
  - fls
  - crud
  - security
  - user-mode
  - sobjectaccessdecision
triggers:
  - "how do i enforce field level security before insert in apex"
  - "stripinaccessible vs with user_mode vs with security_enforced"
  - "user can edit fields they should not be able to edit via my rest endpoint"
  - "apex aura controller exposing fields the running user cannot read"
  - "sobjectaccessdecision getrecords getremovedfields how to use"
  - "should i call stripinaccessible after a user_mode soql query"
inputs:
  - User-supplied SObject records about to be inserted, updated, or upserted
  - Query results that will be returned to a less-privileged caller (LWC, REST, Aura)
  - Running user context (System.runAs target during tests)
  - AccessType the operation requires (READABLE / CREATABLE / UPDATABLE / UPSERTABLE)
outputs:
  - DML-safe sanitized record list with inaccessible fields stripped
  - Audit log of removed fields per record (via SObjectAccessDecision.getRemovedFields)
  - Test class proving FLS enforcement under a non-admin profile
  - "Decision: stripInaccessible vs WITH USER_MODE vs proactive describe checks"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# Apex stripInaccessible and FLS Enforcement

Activate when Apex code accepts records from a less-privileged context (LWC, Aura, REST, Visualforce) and writes them to the database, OR when query results need to be scrubbed of fields the running user cannot read. `Security.stripInaccessible(AccessType, records)` removes inaccessible fields from a record collection and returns an `SObjectAccessDecision` you must operate on instead of the original list.

---

## Before Starting

- Confirm the records are user-supplied. Internal trusted-context data (e.g., trigger handler reading from the trigger context with `without sharing`) does not need stripInaccessible.
- Decide the AccessType: are you reading, creating, updating, or upserting? The wrong enum will silently strip the wrong fields.
- Confirm the calling class's sharing keyword. `with sharing` enforces record visibility; stripInaccessible enforces FIELD visibility. Both are needed for full enforcement.
- Read the `apiVersion` in the class's `.cls-meta.xml` before judging what the surrounding code already enforces — that value is the gate, not the org's release. At 67.0+ (Summer '26) SOQL, SOSL, DML and `Database` methods default to user mode and a class with no sharing keyword runs `with sharing`; at 66.0 and earlier both defaulted the other way, so a class pinned to 58.0 in a Summer '26 org keeps the old behaviour. Canonical table: [`agents/_shared/AGENT_CONTRACT.md` → Apex security idiom by API version](../../../agents/_shared/AGENT_CONTRACT.md#apex-security-idiom-by-api-version). Either way `Security.stripInaccessible` is unaffected — it evaluates the running user's FLS at every version.
- Apex **triggers** are the exception at every API version: a trigger body runs in system mode, cannot declare a sharing or access mode, and bypasses sharing, FLS and object permissions. The 67.0 default-user-mode change does not reach it. Delegate to a handler class where the keyword and access level can be set.
- If the SOQL itself is fetching records to return to a less-privileged caller, prefer `WITH USER_MODE` (Spring '23 / API 57.0+) on the query and skip a redundant strip pass.

---

## Core Concepts

### The four AccessType enum values

`AccessType` is the first argument to `Security.stripInaccessible`. Each value evaluates a different permission:

| Enum | What it strips | When to use |
|---|---|---|
| `AccessType.READABLE` | Fields the user cannot read. | AFTER a SOQL query whose results you'll return to a less-privileged caller. |
| `AccessType.CREATABLE` | Fields the user cannot create. | BEFORE `insert`. |
| `AccessType.UPDATABLE` | Fields the user cannot update. | BEFORE `update`. |
| `AccessType.UPSERTABLE` | Fields the user cannot create OR update (strict intersection — a field must be both creatable AND updatable to survive). | BEFORE `upsert`. |

Picking the wrong AccessType is a real bug. `READABLE` before an `update` will leave create-only or update-only fields in the payload that the user could not have set themselves.

### SObjectAccessDecision — getRecords, getRemovedFields, getModifiedRecords

`Security.stripInaccessible(...)` returns an immutable `SObjectAccessDecision`. You cannot mutate the original list and call it safe — you must operate on the decision's outputs:

- **`getRecords()`** — the sanitized list with inaccessible fields removed. Always DML on this, never on the original argument.
- **`getRemovedFields()`** — a `Map<String, Set<String>>` keyed by SObject API name, value is the set of removed field API names. Useful for logging/audit and for surfacing soft warnings.
- **`getModifiedRecords()`** — a `Map<Id, SObject>` of records that had at least one field stripped (post-DML id only — useful when re-fetching).

### Canonical pattern wrapping DML

```
public void createCases(List<Case> userSupplied) {
    SObjectAccessDecision decision =
        Security.stripInaccessible(AccessType.CREATABLE, userSupplied);

    if (!decision.getRemovedFields().isEmpty()) {
        ApplicationLogger.warn('createCases',
            JSON.serialize(decision.getRemovedFields()));
    }

    insert decision.getRecords();   // NEVER `insert userSupplied;`
}
```

The single most common bug is calling `insert userSupplied;` after the strip — the strip then has zero effect.

### When stripInaccessible is the right choice vs WITH USER_MODE

| Goal | Prefer |
|---|---|
| Querying records to return/manipulate as the running user | `WITH USER_MODE` on the SOQL itself |
| DML on records assembled from user input (e.g., REST body) | `stripInaccessible(CREATABLE/UPDATABLE/UPSERTABLE, ...)` |
| Apex constructed records, no SOQL involved | `stripInaccessible` |
| Class pinned to API 47 or earlier | `WITH SECURITY_ENFORCED` (legacy — removed in 67.0, does not compile there) |
| Need granular per-field reporting (which fields were removed) | `stripInaccessible` (USER_MODE throws, doesn't strip) |

Rule of thumb: `WITH USER_MODE` is THROW-on-inaccessible, `stripInaccessible` is REMOVE-and-continue. Pick based on whether silent partial success is acceptable.

### Performance — per-record FLS evaluation

`stripInaccessible` evaluates FLS for every field on every record. For large lists (10k+) it consumes CPU. It does NOT count against SOQL/DML governor limits, but it does count against the 10-second sync CPU limit. Profile before strip-then-DML on huge collections; consider chunking.

### Relationship handling: subquery children ARE stripped; re-queried records are not

Get this the right way round — the common belief that `stripInaccessible` ignores everything below the top level is wrong, and coding around a limitation that does not exist wastes effort.

**What it does cover.** The Apex Developer Guide's worked example passes a collection queried as `SELECT Name, (SELECT LastName, Phone FROM Contacts) FROM Account` and shows the child `Contact.Phone` field stripped from the subquery results when the running user lacks read access to it. Child records returned *inside* the collection you pass are evaluated. The guide also states the method "checks the source records for lookup or master-detail relationship fields to which the current user doesn't have access" and removes those.

**What it does not cover.** `stripInaccessible` sanitises the sObject collection you hand it, and nothing else. Records fetched by a *separate* query, or traversed by code after the strip, are untouched — the decision object has no reach into them. The supported nesting depth for relationship traversal is not stated in the documentation; do not assume a specific depth in either direction. Verify against your own org with `System.runAs` if a design depends on it.

Practical rule: strip each collection at the point you query it, rather than assuming one strip covers records you obtained elsewhere.

```apex
// Children returned inside the queried collection: ONE strip covers them.
List<Account> accts = [SELECT Name, (SELECT LastName, Phone FROM Contacts) FROM Account];
SObjectAccessDecision d = Security.stripInaccessible(AccessType.READABLE, accts);
// d.getRecords() has Phone removed from the child Contact rows too.

// Records from a SEPARATE query: strip them at their own query site.
List<Contact> extra = [SELECT LastName, Phone FROM Contact WHERE AccountId IN :ids];
SObjectAccessDecision d2 = Security.stripInaccessible(AccessType.UPDATABLE, extra);
update d2.getRecords();
```

### Interaction with Schema.SObjectField.isCreateable / isUpdateable / isAccessible

`Schema.DescribeFieldResult.isCreateable()` is a CHEAP proactive check — use it to fail fast before assembling a payload. `stripInaccessible` is an EXPENSIVE post-hoc scrub — use it as the enforcement gate. They are complementary, not redundant.

```
if (!Schema.sObjectType.Account.fields.AnnualRevenue.isCreateable()) {
    throw new AuraHandledException('You cannot set AnnualRevenue.');
}
// later, still call stripInaccessible before insert as defense-in-depth.
```

### Testing with System.runAs

Without `runAs`, test code runs as whoever is running the test — normally an admin holding every field permission — so the strip returns the input unchanged and the test passes for the wrong reason. (Below API 67.0 the class also ran in system mode by default; at 67.0+ database operations default to user mode. Neither changes `stripInaccessible`, which evaluates the running user's FLS either way.) To prove it actually strips, create a non-admin user with limited permissions and wrap the assertion in `System.runAs(testUser)`.

---

## Common Patterns

### Pattern: REST endpoint — strip before DML

**When to use:** `@RestResource` accepting a JSON body of records.

**How it works:** Deserialize, strip with the appropriate AccessType, log removed fields for audit, DML on the stripped result.

**Why not the alternative:** Trusting the JSON payload assumes the running user can set every field they sent — they often cannot.

### Pattern: Aura/LWC controller — strip on the way out

**When to use:** `@AuraEnabled` method returning records to the client.

**How it works:** Query with `WITH USER_MODE` (preferred) OR strip the result with `AccessType.READABLE` before returning. Returning unscrubbed records lets the client see fields the user cannot read in the UI.

### Pattern: Defense-in-depth with WITH USER_MODE + stripInaccessible

**When to use:** The query already uses USER_MODE, but you also need to write back updates from a partially user-controlled object.

**How it works:** USER_MODE protects the read; stripInaccessible(UPDATABLE) protects the write. Each guards a different operation — do not collapse them.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| REST/LWC inserts user-supplied records | `stripInaccessible(CREATABLE, ...)` then DML on `getRecords()` | Records originate from a less-trusted client |
| Aura controller returns records | `WITH USER_MODE` on the SOQL | Throws on inaccessible read, no silent strip |
| Upsert from a user-supplied list | `stripInaccessible(UPSERTABLE, ...)` | Intersects creatable AND updatable |
| Internal trigger handler updating fields the running user can edit anyway | Skip — not user-supplied | stripInaccessible cost not justified |
| Need to know WHICH fields got removed for audit | `stripInaccessible` + `getRemovedFields()` | USER_MODE throws, gives no per-field detail |
| Class pinned below API 48 | `WITH SECURITY_ENFORCED` | `stripInaccessible` needs 48.0+, `WITH USER_MODE` needs 57.0+. Never emit `WITH SECURITY_ENFORCED` into a 67.0+ class — it was removed and fails to compile |

---

## Recommended Workflow

1. Identify entry points where records cross from less-privileged caller (LWC, Aura, REST, Visualforce) into Apex. Mark every parameter.
2. For each entry point, pick the correct `AccessType` based on the DML you'll perform (CREATABLE for insert, UPDATABLE for update, UPSERTABLE for upsert, READABLE for outbound payloads).
3. Replace the raw DML on the input list with DML on `Security.stripInaccessible(type, input).getRecords()`. Capture the decision in a local variable so you can also call `getRemovedFields()`.
4. Strip child collections separately if relationships are populated — parent strip does NOT recurse.
5. Log `getRemovedFields()` (or surface as a warning to the caller) so silent stripping is observable.
6. Add a test under `System.runAs(nonAdminUser)` that proves a restricted field IS stripped. The same test with no `runAs` — running as the privileged test user — should be a no-op.
7. Run `python3 scripts/check_apex_stripinaccessible_and_fls_enforcement.py` over the changed `.cls` files to catch the "stripped-then-DML-on-original" mistake.

---

## Review Checklist

- [ ] Every user-supplied record list passes through `Security.stripInaccessible` before DML
- [ ] DML targets `decision.getRecords()`, never the original argument
- [ ] `AccessType` matches the DML operation (CREATABLE/UPDATABLE/UPSERTABLE)
- [ ] Outbound query results either use `WITH USER_MODE` or `AccessType.READABLE` strip
- [ ] Child collections are stripped independently when relationships are populated
- [ ] `getRemovedFields()` is logged or surfaced; silent stripping is forbidden
- [ ] Test class uses `System.runAs(nonAdminUser)` and asserts a restricted field was removed
- [ ] No double-enforcement (USER_MODE in SOQL AND READABLE strip on the same path)

---

## Salesforce-Specific Gotchas

1. **DML on the original list silently bypasses the strip.** `stripInaccessible(...).getRecords()` returns a NEW list. Calling `insert userSupplied;` after the strip line does nothing — the strip's effect is in `getRecords()`.
2. **Subquery child records ARE stripped — separately queried records are not.** The documented worked example strips `Contact.Phone` from the child rows of `SELECT Name, (SELECT LastName, Phone FROM Contacts) FROM Account`, so a strip on the parent collection does cover children returned inside it. What it cannot cover is any record obtained by a *different* query or traversal; strip those at their own query site. The supported traversal depth is not documented — do not design around an assumed limit.
3. **Tests pass regardless of FLS unless you supply a restricted user.** Without `System.runAs(nonAdminUser)` the running user is the admin executing the test, so every field is accessible and your strip call is a no-op — the test proves nothing. Unchanged at 67.0+, where user mode still enforces that same unrestricted user's permissions.
4. **`AccessType.UPSERTABLE` is the intersection of CREATABLE and UPDATABLE.** A field accessible for create but not update gets stripped on UPSERTABLE — this is correct behavior for upsert but surprising if you expected union semantics.
5. **`SObjectAccessDecision` is immutable.** You cannot mutate `getRecords()` results and have those changes reflect anywhere; call DML directly on the returned list.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Sanitized DML payload | `decision.getRecords()` — the only safe input to `insert`/`update`/`upsert` |
| Removed-fields audit | `decision.getRemovedFields()` map for logging or warnings |
| FLS enforcement test | Test under `System.runAs(nonAdmin)` proving restricted field stripped |
| AccessType decision note | Documented choice of CREATABLE / UPDATABLE / UPSERTABLE / READABLE per entry point |

---

## Related Skills

- `apex/apex-with-user-mode-soql` — when to prefer USER_MODE on the SOQL itself
- `apex/apex-sharing-keywords` — class-level `with sharing` / `without sharing` / `inherited sharing` (record visibility, complements FLS)
- `apex/apex-security-utils` — using the shared `templates/apex/SecurityUtils.cls` helpers
- `security/security-fls-crud-enforcement` — broader CRUD/FLS strategy across the org
