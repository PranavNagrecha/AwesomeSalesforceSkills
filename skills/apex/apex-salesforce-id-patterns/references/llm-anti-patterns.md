# LLM Anti-Patterns — Apex Salesforce Id Patterns

## Anti-Pattern 1: Prefix-String Type Detection

**What the LLM generates:**

```apex
if (recordId.startsWith('001')) {
    // treat as Account
}
```

**Why it happens:** LLMs learned the common standard-object prefixes and use them as convenient type-tags. They do not know custom prefixes are org-specific.

**Correct pattern:**

```apex
Id id = (Id) recordId;
if (id.getSobjectType() == Account.SObjectType) { /* ... */ }
```

**Detection hint:** `.startsWith('001'|'003'|'005'|'a0')` on an Id-like string.

---

## Anti-Pattern 2: Treating `Id` And `String` As Interchangeable

**What the LLM generates:**

```apex
public static void process(String recordId) {
    // no validation, straight to SOQL
    Account a = [SELECT Id FROM Account WHERE Id = :recordId];
}
```

**Why it happens:** LLMs carry over JS/TS habits where everything is a string. The Apex `Id` type carries validation semantics the LLM ignores.

**Correct pattern:** Type the parameter as `Id` (or `Id.valueOf(recordId)` with a try/catch at the boundary).

**Detection hint:** Method signatures taking `String recordId` that are then used as Id binds.

---

## Anti-Pattern 3: Mixing 15-Char And 18-Char Ids In String Sets

**What the LLM generates:**

```apex
Set<String> processedIds = new Set<String>();
for (String id : incomingIds) {
    processedIds.add(id);
}
if (processedIds.contains(someAccount.Id)) { /* never true for 15-char inputs */ }
```

**Why it happens:** LLMs don't model the 15/18 distinction; they treat all Ids as opaque strings.

**Correct pattern:** Use `Set<Id>`, or cast both sides through `Id` before comparison.

**Detection hint:** `Set<String>` being populated with Id values and compared to SObject `.Id` fields.

---

## Anti-Pattern 4: Catching The Wrong Exception

**What the LLM generates:**

```apex
try {
    Id i = Id.valueOf(untrustedStr);
} catch (IllegalArgumentException e) {
    // never catches — Apex throws System.StringException
}
```

**Why it happens:** Java bleed. `IllegalArgumentException` is the standard Java pattern for invalid inputs.

**Correct pattern:** `catch (System.StringException e)` or a broader `catch (Exception e)`.

**Detection hint:** `IllegalArgumentException` near `Id.valueOf`.

---

## Anti-Pattern 5: Using `Schema.getGlobalDescribe()` In Hot Paths

**What the LLM generates:**

```apex
for (Id i : ids) {
    String type = Schema.getGlobalDescribe().get(((String)i).substring(0,3))
                    .getDescribe().getName();
}
```

**Why it happens:** LLMs reach for `Schema.getGlobalDescribe()` because it's the most documented describe entry point — and they call it inside a loop.

**Correct pattern:** `i.getSobjectType().getDescribe().getName()` — no global describe needed for a typed Id.

**Detection hint:** `Schema.getGlobalDescribe()` inside any `for` loop, or called more than once per transaction.

---

## Anti-Pattern 6: Forgetting Null Before `getSobjectType()`

**What the LLM generates:**

```apex
for (Task t : tasks) {
    if (t.WhoId.getSobjectType() == Contact.SObjectType) { /* NPE when WhoId is null */ }
}
```

**Why it happens:** LLMs don't distinguish required from optional lookup fields, or forget that polymorphic Ids can be null.

**Correct pattern:** `if (t.WhoId != null && t.WhoId.getSobjectType() == Contact.SObjectType) { ... }`.

**Detection hint:** `.getSobjectType()` on a polymorphic or optional Id field without null guard.

---

## Anti-Pattern 7: Hardcoding 18-Char Id Literals In Tests

**What the LLM generates:**

```apex
@IsTest static void testWithMockId() {
    Id fakeId = '001000000000000AAA';
    MyHandler.handle(fakeId);
}
```

**Why it happens:** LLMs generate valid-looking Id strings for unit tests instead of using `Test.createStubApi()` or inserting real records.

**Correct pattern:** Create a test record with `TestDataFactory` and use its real Id, or use `Schema.SObjectType.Account.getKeyPrefix()` with a counter for synthetic Ids.

**Detection hint:** String literals matching `/00[0-9A-Z]{15}/` inside test classes.

---

## Anti-Pattern 8: Using `String.isBlank` On `Id` Type

**What the LLM generates:**

```apex
if (String.isBlank(accountId)) { /* accountId is Id, not String */ }
```

**Why it happens:** LLMs use `String.isBlank` reflexively as a null/empty check.

**Correct pattern:** `if (accountId == null)` — `Id` cannot be empty string, only null.

**Detection hint:** `String.isBlank(` followed by an argument typed `Id`.
