# Gotchas — Apex Hardcoded ID Elimination

Non-obvious behaviors that turn a "simple ID lookup" into a production bug.

---

## 1. `getRecordTypeInfosByName()` uses a translatable label

`getRecordTypeInfosByName()` returns the map keyed by the RecordType's MasterLabel. Labels are translatable and renamable in setup; DeveloperName is the API-stable identifier.

**Always use:**

```apex
Schema.SObjectType.Account.getRecordTypeInfosByDeveloperName().get('Partner');
```

Never:

```apex
Schema.SObjectType.Account.getRecordTypeInfosByName().get('Partner');  // breaks if label is renamed or translated
```

This applies to API version 31.0+. The describe-API approach replaces older patterns (`[SELECT Id FROM RecordType WHERE DeveloperName=...]`) which still work but cost a SOQL query.

---

## 2. `Profile.Name = 'System Administrator'` is not universally portable

Salesforce has historically used `Name = 'System Administrator'`, but some orgs (notably newer / certain editions) display "Standard System Administrator" or have localized names. The Profile object lacks a true DeveloperName field for standard profiles in older API versions, and querying by `Name` couples your code to one org's labeling.

**Mitigations (in preference order):**

1. Put the admin Profile's actual `Name` in a Custom Metadata Type entry. Code reads from CMDT; admin updates the value per org.
2. Use `PermissionSet` membership instead of Profile checks where possible — Permission Sets have a stable DeveloperName.
3. If you must hardcode the predicate, document the assumption explicitly and add a unit test that asserts the lookup returns a non-null Id.

---

## 3. Custom Metadata is the right home for config IDs in subscriber orgs

If your code is going into a managed package, hardcoded IDs are guaranteed to be wrong in every subscriber org. Custom Metadata Types are deployable, accessible via `CustomType__mdt.getInstance()`, and editable in setup without a code change.

**Use CMDT for:**

- Default record owner User
- Fallback Account / Contact for orphaned records
- Routing Queue per priority / region
- Integration target IDs

---

## 4. `Id`-as-`String` comparisons fail across the 15/18 boundary

Salesforce IDs exist in two forms:
- 15-char, **case-sensitive** (`0011x00000ABCDe`)
- 18-char, **case-insensitive** (`0011x00000ABCDeAAB`)

The 18-char form is the 15-char form plus a 3-char checksum suffix that encodes case. SOQL returns 18-char IDs. UI/URL bars often show 15-char.

**The trap:**

```apex
String hardcoded = '0011x00000ABCDe';      // stored as 15-char String
Account a = [SELECT Id FROM Account WHERE ...].iterator().next();
if (hardcoded == a.Id) { ... }              // a.Id is 18-char — comparison fails
```

**Fix:** declare with the `Id` type. Apex auto-normalizes to 18-char on assignment:

```apex
Id hardcoded = '0011x00000ABCDe';           // normalized
if (hardcoded == a.Id) { ... }              // works
```

Never store a Salesforce ID in a `String` field, variable, or Map key without an explicit reason.

---

## 5. Static-map cache survives the transaction, not the request

A static `Map<String, Id>` populated once is reused for the rest of the transaction (good — saves SOQL). It does NOT persist across transactions or across user sessions. Don't confuse it with Platform Cache. Each new Apex execution context starts cold.

---

## 6. Querying inside `for` loops (the SOQL-101 trap)

```apex
for (User u : users) {
    Id pid = [SELECT Id FROM Profile WHERE Name = :u.ProfileName].Id;  // 1 SOQL per iteration
}
```

Always batch upfront and cache:

```apex
Set<String> names = new Set<String>();
for (User u : users) names.add(u.ProfileName);
Map<String, Id> idByName = new Map<String, Id>();
for (Profile p : [SELECT Id, Name FROM Profile WHERE Name IN :names]) {
    idByName.put(p.Name, p.Id);
}
```

---

## 7. Test classes that hardcode IDs cannot run in scratch orgs

Scratch orgs are spun fresh per CI run; no record exists at any specific ID. Tests must `insert` seed data and use the returned `.Id`.
