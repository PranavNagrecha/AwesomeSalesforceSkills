# Gotchas — Apex Schema Describe

---

## Gotcha 1: `Schema.getGlobalDescribe()` materializes the entire org schema

**What happens.** Returns a Map of every SObject API name → SObjectType
in the org. Heavy on first call; cached per-transaction after.

**How to avoid.** Cache as `static final` if you call it more than
once. Compile-time `Account.SObjectType` skips the call entirely.

---

## Gotcha 2: `getDescribe()` on a field per record multiplies cost

**What happens.** `Account.Name.getDescribe()` in a 200-record loop
runs the describe 200 times. Each call is small but cumulative.

**How to avoid.** Hoist to `static final` at class scope:

```apex
private static final Schema.DescribeFieldResult NAME_DESCRIBE =
    Account.Name.getDescribe();
```

---

## Gotcha 3: Inactive picklist entries appear in `getPicklistValues()`

**What happens.** `getPicklistValues()` returns ALL values
including deactivated ones. Code that expects only active values
sees stale ones.

**How to avoid.** Filter with `isActive()`.

---

## Gotcha 4: `Type.forName()` returns `System.Type`, not `SObjectType`

**What happens.** `Type.forName('Account')` returns a Type
object — not directly usable for SObject operations.

**How to avoid.** `Schema.getGlobalDescribe().get('Account')`
returns `SObjectType`. `t.newSObject()` produces a record.

---

## Gotcha 5: Managed-package fields require namespace prefix

**What happens.** `Schema.getGlobalDescribe().get('Custom__c')` returns
null when the field actually has namespace `pkg__Custom__c`.

**How to avoid.** Include namespace prefix when accessing managed-
package metadata.

---

## Gotcha 6: `getRecordTypeInfosByName()` uses LABEL (renameable)

**What happens.** Code uses `getRecordTypeInfosByName().get('Partner Account')`.
Admin renames the record type label; code breaks.

**How to avoid.** Use `getRecordTypeInfosByDeveloperName()` —
DeveloperName is stable.

---

## Gotcha 7: `isAccessible()` returns true for system fields user can't read

**What happens.** Some system fields (e.g. internal flags) report
`isAccessible() = true` even for non-admin users. The describe
result reflects metadata-level FLS, not contextual access.

**How to avoid.** For reliable read-access checks, use
`Security.stripInaccessible(AccessType.READABLE, records)` —
honors runtime context.

---

## Gotcha 8: `fields.getMap()` field names are LOWERCASE keys

**What happens.** `Account.SObjectType.getDescribe().fields.getMap().get('Name')`
returns null. The Map's keys are lowercased.

**How to avoid.** `getMap().get('name')` (lowercase) or use
`Account.Name` directly (compile-time reference).
