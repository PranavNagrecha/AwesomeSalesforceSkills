# LLM Anti-Patterns: Apex Wrapper Class Patterns

Common mistakes AI coding assistants make when generating Apex wrapper classes. These help the consuming agent self-check its own output.

---

## Anti-Pattern 1: Returning an inner class to a Lightning web component

**What the LLM generates:**

```apex
public with sharing class AccountController {
    public class Row { @AuraEnabled public String name; }
    @AuraEnabled(cacheable=true)
    public static List<Row> getRows() { /* ... */ }
}
```

**Why it happens:** Most blog examples nest the wrapper inside the controller, and it often appears to work.

**The correct pattern:** The LWC guide says an Apex inner class as a parameter or return value for a method called by a Lightning web component isn't supported. Put `Row` in its own top-level class file and keep the controller separate.

**Detection hint:** An `@AuraEnabled` method whose return type or parameter type names a class declared inside the same file.

---

## Anti-Pattern 2: Claiming inner classes always run in system mode

**What the LLM generates:** "Inner classes always execute in system mode, and Apex doesn't allow sharing keywords on inner classes."

**Why it happens:** The model half-remembers that inner classes don't inherit sharing. Version 1.0.0 of this skill stated it this way.

**The correct pattern:** You can declare a sharing mode on inner classes, and they don't adopt the container's mode. In API 67.0 and later, a class without an explicit declaration runs with sharing. In 66.0 and earlier, a non-entry-point class without one takes its caller's mode (Apex Developer Guide, sharing keywords and Versioned Behavior Changes).

**Detection hint:** "Inner class" and "system mode" in the same sentence with no API version.

---

## Anti-Pattern 3: Forgetting @AuraEnabled, or getters and setters, on wrapper properties

**What the LLM generates:** `@AuraEnabled` on the method only, or plain fields on a wrapper that the component sends back to Apex.

**Why it happens:** The model assumes the method annotation cascades.

**The correct pattern:** Only public instance properties annotated with `@AuraEnabled` are serialized. Properties of a custom-class parameter need `@AuraEnabled` plus `{ get; set; }`.

**Detection hint:** A class used as an `@AuraEnabled` return or parameter type with public properties that lack the annotation.

---

## Anti-Pattern 4: Adding @JsonAccess to every REST wrapper

**What the LLM generates:** "Add `@JsonAccess(serializable='always' deserializable='always')` or the REST endpoint throws `Type is not visible`."

**Why it happens:** The model links the annotation to REST rather than to namespaces. Version 1.0.0 of this skill made that claim.

**The correct pattern:** Since API 49.0 the default for both directions is `sameNamespace`, so same-namespace REST code needs no annotation. Use `@JsonAccess` with the narrowest value only when another namespace or package must serialize or deserialize the class. A restrictive setting throws `JSONException` at runtime.

**Detection hint:** `@JsonAccess(... 'always' ...)` on a class that no other namespace touches.

---

## Anti-Pattern 5: Comparators and compareTo() without null handling

**What the LLM generates:**

```apex
public Integer compare(Row a, Row b) {
    return a.amount > b.amount ? 1 : -1;
}
```

**Why it happens:** Happy-path code with no null rows or null keys.

**The correct pattern:** Check both arguments and both keys for null, return 0 for equal values, and choose nulls first or last. The Comparable and Comparator references require explicit null handling.

**Detection hint:** A `compare` or `compareTo` body with no `== null` check.

---

## Anti-Pattern 6: Queries inside wrapper constructors

**What the LLM generates:** A constructor that runs `[SELECT COUNT() FROM Opportunity WHERE AccountId = :acct.Id]` for each row.

**Why it happens:** It keeps the wrapper "self-contained."

**The correct pattern:** Query and aggregate once in the controller or service, then pass values into the constructor. One query per row multiplies SOQL against the 100-query synchronous limit (Apex Developer Guide, Per-Transaction Apex Limits).

**Detection hint:** SOQL or DML inside a constructor of a class built in a loop.

---

## Anti-Pattern 7: Stating a version for Comparator as fact

**What the LLM generates:** "Comparator requires API 60.0; fall back to Comparable below that."

**Why it happens:** The model recalls a release, not a documented rule.

**The correct pattern:** The 262 Apex Reference Guide documents `System.Comparator` and `List.sort(comparator)` without a minimum version. Check the class's API version against your own org (compile it) rather than citing a number. UNVERIFIED (2026-10-03): the introducing API version.

**Detection hint:** A Comparator version floor stated with no source.
