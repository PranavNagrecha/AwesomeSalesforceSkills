# LLM Anti-Patterns — Apex Hardcoded ID Elimination

Mistakes AI assistants commonly make when generating or refactoring Apex that handles record IDs.

---

## 1. Pasting a sandbox Profile ID as a String literal

LLMs frequently fabricate or echo back IDs like `'00e1x000000ABcD'` from training-data examples. These are environment-specific. Even worse, the LLM may type them as `String`, opening the 15/18-char comparison bug.

**Fix:** never emit a literal Salesforce ID in non-test Apex. Always emit a `Schema...getRecordTypeInfosByDeveloperName()` call, a cached SOQL helper, or a `CustomType__mdt.getInstance(...)` reference. If a literal would otherwise be needed, ask the user for the DeveloperName instead.

**Detection hint:** regex `['"][a-zA-Z0-9]{15}(?:[a-zA-Z0-9]{3})?['"]` in non-test Apex.

---

## 2. Comparing `String` to `Id` without normalizing

```apex
String stored = '0011x00000ABCDe';  // 15-char
if (stored == account.Id) { ... }   // account.Id is 18-char — never matches
```

Models generate this constantly because String feels like the "default" type. The result is intermittent equality failures that are nearly impossible to debug from logs.

**Fix:** declare ID-holding variables as `Id`. Apex normalizes to 18-char on assignment.

**Detection hint:** any `String` typed variable whose name ends with `Id` / `Ids`.

---

## 3. Assuming `Profile.Name = 'System Administrator'` works in every org

Documentation and older Stack Exchange answers use this string. It is not universally portable — some orgs use "Standard System Administrator" or localized names.

**Fix:** drive the predicate from a Custom Metadata Type entry, or check Permission Set membership instead.

**Detection hint:** literal `'System Administrator'` in a Profile WHERE clause.

---

## 4. Querying Profile / Group / Queue inside a `for` loop

```apex
for (User u : users) {
    Id pid = [SELECT Id FROM Profile WHERE Name = :u.ProfileName].Id;  // SOQL-101 trap
}
```

LLMs reach for the inline query because it reads "naturally" near the data. But SOQL-in-loop is the most common Apex governor-limit failure.

**Fix:** collect names upfront, single SOQL with `IN :set`, build a `Map<String, Id>`, look up in the loop.

**Detection hint:** `[SELECT ... FROM Profile|Group|UserRole ...]` whose enclosing block is a `for` loop.

---

## 5. Not caching describe results across calls

`Schema.SObjectType.X.getRecordTypeInfosByDeveloperName()` is cheap but not free. Repeating it for every record in a trigger handler wastes CPU.

**Fix:** assign once to a `static final Id` or a `static Map<String, Id>` populated lazily in a helper method.

**Detection hint:** `getRecordTypeInfosByDeveloperName` appearing on the inside of a `for` loop body.

---

## 6. Hardcoding test-record IDs in `@IsTest` classes

```apex
Case c = new Case(OwnerId = '00G3x000003abcD');  // hardcoded queue ID in a test
```

Tests must run in scratch orgs, refreshed sandboxes, and managed-package subscriber orgs. Hardcoded IDs guarantee test-class failure in CI.

**Fix:** insert seed data inside the test (`insert new Group(...)`), capture the returned `.Id`, use that.

**Detection hint:** ID literal inside a `@isTest` method, in a constructor argument or assignment.

---

## 7. Using `getRecordTypeInfosByName()` because it "reads more naturally"

LLMs sometimes prefer the `ByName` variant because the argument looks like a friendly label. But that label is translatable and renamable; the lookup will silently return null after a label change.

**Fix:** always use `getRecordTypeInfosByDeveloperName()`.

**Detection hint:** the substring `getRecordTypeInfosByName` anywhere in Apex.

---

## 8. Inventing a non-existent `Profile.DeveloperName` field

Standard `Profile` does NOT have a `DeveloperName` field exposed for query in the way `Group`, `UserRole`, and Custom Metadata do. LLMs occasionally hallucinate `WHERE DeveloperName = 'SysAdmin'` for Profile.

**Fix:** for Profile, use `Name`. For Group / UserRole / Queue / Custom Metadata, use `DeveloperName`.

**Detection hint:** `FROM Profile WHERE DeveloperName` substring.
