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

**Correct pattern.** `Schema.getGlobalDescribe().get('Account').newSObject()`,
the guide's documented path (apexdev 264 L11795-11801). `Type.forName('Account')`
resolves to `Account.class` (apexref 262 L242043-242045), but `newInstance()`
is documented for classes; that it builds a usable sObject is UNVERIFIED (2026-10-20).

**Detection hint.** `Type.forName` for an SObject API name followed by
a cast to SObject — replace with the documented `newSObject()` path.

---

## Anti-Pattern 3: Claiming `getPicklistValues()` returns inactive values

**What the LLM generates.**

```apex
List<Schema.PicklistEntry> entries = Account.Industry.getDescribe().getPicklistValues();
for (Schema.PicklistEntry pe : entries) {
    options.add(pe.getValue());  // "includes inactive" — false
}
```

**Correct pattern.** Corrected 2026-10-20 (this anti-pattern previously
told you to add an `isActive()` filter): "Only active picklist values are
returned" (apexref 262 L190851). The loop above is already active-only;
code that needs retired values must read them from metadata.

**Detection hint.** A comment or review note saying the list "includes
inactive" values, or logic that relies on seeing retired values.

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
records)` — strips the fields the user cannot access (apexdev 264
L12281-12282) instead of only testing one boolean.

**Detection hint.** Any per-record FLS check before bulk DML
should be replaced with stripInaccessible.

---

## Anti-Pattern 6: Claiming field-map keys are lowercase-only

**What the LLM generates.**

```apex
Schema.SObjectField f = Account.SObjectType.getDescribe()
    .fields.getMap().get('Name'.toLowerCase());  // "get('Name') returns null" — false
```

**Correct pattern.** Corrected 2026-10-20 (this entry previously said the
keys are lowercase and `get('Name')` returns null): "All field names are
case insensitive" (apexdev 264 L11079). `get('Name')` works; the miss that
does return null is a packaged field without its namespace (L11080).

**Detection hint.** Defensive `toLowerCase()` before `getMap().get(...)`,
or a review comment asserting lowercase keys.

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
