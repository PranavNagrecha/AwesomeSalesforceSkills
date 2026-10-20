# Gotchas — Apex Hardcoded ID Elimination

Non-obvious behaviors that turn a "simple ID lookup" into a production bug.

---

## 1. `getRecordTypeInfosByName()` uses a translatable label

`getRecordTypeInfosByName()` returns the map keyed by the record type label (apexref 262 L192589), and the label "can be translated into any language that Salesforce supports" (L193789); `getRecordTypeInfosByDeveloperName()` returns a map by developer name (L192556-192558).

**Always use:**

```apex
Schema.SObjectType.Account.getRecordTypeInfosByDeveloperName().get('Partner');
```

Never:

```apex
Schema.SObjectType.Account.getRecordTypeInfosByName().get('Partner');  // breaks if label is renamed or translated
```

UNVERIFIED (2026-10-20): the "API version 31.0+" availability. The describe-API approach replaces older patterns (`[SELECT Id FROM RecordType WHERE DeveloperName=...]`) which still work; a SOQL statement counts against the 100-query limit (apex dev guide 264 L19747).

---

## 2. `Profile.Name = 'System Administrator'` is not universally portable

Salesforce has historically used `Name = 'System Administrator'`; UNVERIFIED (2026-10-20): that some orgs display "Standard System Administrator" or localized names. The Profile field list has `Name` and no `DeveloperName` at all (object_reference 264 L234799-234887) — the earlier "for standard profiles in older API versions" qualifier is dropped — so querying by `Name` couples your code to one org's labeling.

**Mitigations (in preference order):**

1. Put the admin Profile's actual `Name` in a Custom Metadata Type entry. Code reads from CMDT; admin updates the value per org.
2. Use `PermissionSet` membership instead of Profile checks where possible — a PermissionSet has `Name` and `Label` fields (object_reference 264 L219421-219444), not a `DeveloperName`; UNVERIFIED (2026-10-20): that `Name` is stable across orgs.
3. If you must hardcode the predicate, document the assumption explicitly and add a unit test that asserts the lookup returns a non-null Id.

---

## 3. Custom Metadata is the right home for config IDs in subscriber orgs

If your code is going into a managed package, hardcoded IDs are guaranteed to be wrong in every subscriber org. Custom Metadata Types are accessible via `CustomType__mdt.getInstance()` (apexref 262 L204587-204629); UNVERIFIED (2026-10-20): that they are editable in Setup without a code change and deployable in packages.

**Use CMDT for:**

- Default record owner User
- Fallback Account / Contact for orphaned records
- Routing Queue per priority / region
- Integration target IDs

---

## 4. `Id`-as-`String` comparisons fail across the 15/18 boundary

Salesforce IDs exist in two forms:
- 15-char (`0011x00000ABCDe`)
- 18-char (`0011x00000ABCDeAAB`)

Apex "converts the value to its 18-character representation" when you set an `ID` to a 15-character value (apex dev guide 264 L1254-1255). UNVERIFIED (2026-10-20): the case-sensitivity of each form, the checksum suffix, that SOQL returns 18-char IDs and that UI bars show 15-char.

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

A static `Map<String, Id>` populated once is reused for the rest of the transaction (good — saves SOQL): a static variable is "static only within the scope of the Apex transaction" and "reset across transaction boundaries" (apex dev guide 264 L3746-3748). It does NOT persist across transactions or across user sessions. Don't confuse it with Platform Cache. Each new Apex execution context starts cold.

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

---

## Checker Ignores Comments And String Literals

**What happens:** The skill checker flags a keyword that appears only in a comment or a string literal (for example a note that `WITH SECURITY_ENFORCED` is not used, or an assertion message that mentions `EventBus.publish`).

**When it occurs:** Before the checker blanked `//` line comments, `/* … */` block comments, and `'…'` string literals to spaces (same length, newlines preserved) for code-pattern rules.

**How to avoid:** Trust the checker on executable code only. Mentions inside comments and string literals are ignored for pattern matches; rules that intentionally read comments (for example a `// reason:` search) still read the original text.
