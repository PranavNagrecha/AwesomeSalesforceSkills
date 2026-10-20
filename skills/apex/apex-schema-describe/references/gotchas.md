# Gotchas — Apex Schema Describe

---

## Gotcha 1: `Schema.getGlobalDescribe()` maps every sObject the running user can see

**What happens.** Returns a Map of every SObject API name → SObjectType
the running user can see, generated at runtime (apexdev 264 L11244-11249).
"Heavy on first call; cached per-transaction after" is UNVERIFIED
(2026-10-20): the guide states no cost or platform caching.

**How to avoid.** Cache as `static final` if you call it more than
once. Compile-time `Account.SObjectType` skips the call entirely.

---

## Gotcha 2: `getDescribe()` on a field per record multiplies cost

**What happens.** `Account.Name.getDescribe()` in a 200-record loop
runs the describe 200 times. The guide warns describe results "would take
too many system resources" if materialised for every field (apexdev 264
L11074), which is why the field map holds tokens, not describes.

**How to avoid.** Hoist to `static final` at class scope:

```apex
private static final Schema.DescribeFieldResult NAME_DESCRIBE =
    Account.Name.getDescribe();
```

---

## Gotcha 3: `getPicklistValues()` returns active entries only

**What happens.** Corrected 2026-10-20 — the earlier text said it
returns ALL values including deactivated ones. The reference says
"Only active picklist values are returned" (apexref 262 L190851). Code
that expects to see retired values (e.g. to label historic data) gets
nothing for them.

**How to avoid.** Treat the list as active-only; an `isActive()` filter
is a harmless no-op. Source inactive values from metadata instead.

---

## Gotcha 4: `Type.forName()` returns `System.Type`, not `SObjectType`

**What happens.** `Type.forName('Account')` returns a `System.Type`
equal to `Account.class` (apexref 262 L242043-242045), not an
`SObjectType`; its `newInstance()` returns `Object` (apexref 262 L242303).

**How to avoid.** `Schema.getGlobalDescribe().get('Account')`
returns `SObjectType`. `t.newSObject()` produces a record.

---

## Gotcha 5: Managed-package fields require namespace prefix

**What happens.** `Schema.getGlobalDescribe().get('Custom__c')` returns
null when the object actually has namespace `pkg__Custom__c`. From Apex
saved at API 28.0+, keys are always prefixed with the running code's
namespace (apexdev 264 L11255-11257).

**How to avoid.** Include namespace prefix when accessing managed-
package metadata.

---

## Gotcha 6: `getRecordTypeInfosByName()` uses LABEL (renameable)

**What happens.** Code uses `getRecordTypeInfosByName().get('Partner Account')`.
Admin renames the record type label; code breaks.

**How to avoid.** Use `getRecordTypeInfosByDeveloperName()` —
DeveloperName is stable.

---

## Gotcha 7: `isAccessible()` answers for one field; it strips nothing

**What happens.** Corrected 2026-10-20 — the earlier text said the
describe reflects metadata-level FLS, not the user's access. The guide
says the `DescribeFieldResult` access methods check "the current user's
read, create, or update access for a field" (apexdev 264 L12473-12474).
The claim that some system fields report `true` for users who cannot
read them is UNVERIFIED (2026-10-20). The real limit: a boolean per field
does nothing to the records you then return or write.

**How to avoid.** For record lists, use
`Security.stripInaccessible(AccessType.READABLE, records)`, which strips
inaccessible fields (apexdev 264 L12281-12282).

---

## Gotcha 8: `fields.getMap()` keys are case-insensitive (not lowercase-only)

**What happens.** Corrected 2026-10-20 — the earlier text said
`getMap().get('Name')` returns null because keys are lowercased. The
guide says "All field names are case insensitive" (apexdev 264 L11079),
so `get('Name')` and `get('name')` both resolve. The real miss is a
custom field looked up without its namespace (L11080).

**How to avoid.** Do not `toLowerCase()` names defensively; include the
namespace for packaged fields, or use `Account.Name` directly.
