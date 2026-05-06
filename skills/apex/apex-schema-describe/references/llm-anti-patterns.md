# LLM Anti-Patterns — Apex Schema Describe

---

## Anti-Pattern 1: `Schema.getGlobalDescribe()` inline in loops

**What the LLM generates.**

```apex
for (SObject r : records) {
    Schema.SObjectType t = Schema.getGlobalDescribe().get('Account');
    // ...
}
```

**Correct pattern.** Hoist to `static final` or assign once before
the loop.

**Detection hint.** Any `getGlobalDescribe()` inside `for` / `while`
is suspect.

---

## Anti-Pattern 2: `Type.forName` to get SObjectType

**What the LLM generates.**

```apex
Type t = Type.forName('Account');
SObject r = (SObject) t.newInstance();
```

**Correct pattern.** `Schema.getGlobalDescribe().get('Account').newSObject()`.
Type.forName is for Apex types, not SObject prototypes.

**Detection hint.** Any `Type.forName` for an SObject API name
followed by cast to SObject is wrong.

---

## Anti-Pattern 3: Picklist enumeration without `isActive` filter

**What the LLM generates.**

```apex
List<Schema.PicklistEntry> entries = Account.Industry.getDescribe().getPicklistValues();
for (Schema.PicklistEntry pe : entries) {
    options.add(pe.getValue());  // includes inactive
}
```

**Correct pattern.** `if (pe.isActive()) options.add(pe.getValue());`.

**Detection hint.** Any picklist enumeration without `isActive` is
showing inactive values.

---

## Anti-Pattern 4: `getRecordTypeInfosByName` against a stable identifier

**What the LLM generates.**

```apex
Id rtId = Account.SObjectType.getDescribe()
    .getRecordTypeInfosByName().get('Partner Account').getRecordTypeId();
```

**Correct pattern.** `getRecordTypeInfosByDeveloperName().get('Partner_Account')`.
Labels can be renamed; DeveloperNames are stable.

**Detection hint.** Any `byName` on RecordTypeInfo with a literal
label is brittle to label renames.

---

## Anti-Pattern 5: Per-field `isAccessible()` for bulk DML

**What the LLM generates.**

```apex
for (Account a : records) {
    if (Account.SSN__c.getDescribe().isAccessible()) {
        // ...
    }
}
update records;
```

**Correct pattern.** `Security.stripInaccessible(AccessType.UPDATABLE,
records)` — bulk-safe and runtime-context-aware.

**Detection hint.** Any per-record FLS check before bulk DML
should be replaced with stripInaccessible.

---

## Anti-Pattern 6: Field-map keys treated as case-sensitive

**What the LLM generates.**

```apex
Schema.SObjectField f = Account.SObjectType.getDescribe()
    .fields.getMap().get('Name');  // returns null
```

**Correct pattern.** Field-map keys are lowercase: `.get('name')`.
Or use compile-time `Account.Name`.

**Detection hint.** Any `fields.getMap().get('CamelCaseName')` is
returning null silently.

---

## Anti-Pattern 7: Forgetting namespace prefix for managed-package fields

**What the LLM generates.**

```apex
Schema.SObjectField f = Schema.getGlobalDescribe()
    .get('Custom__c').getDescribe().fields.getMap().get('field_name__c');
```

**Correct pattern.** Include namespace if the package is namespaced:
`pkg__Custom__c`, `pkg__field_name__c`.

**Detection hint.** Any cross-package field reference without a
namespace prefix returns null when the field is managed.
