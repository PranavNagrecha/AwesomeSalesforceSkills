# Gotchas — Apex Wrapper Class Patterns

Non-obvious Salesforce platform behaviors that cause real production problems when working with Apex wrapper and inner classes.

---

## Gotcha 1: Comparable.compareTo() Without Null Guard Throws NullPointerException at Sort Time

**What happens:** `List.sort()` invokes `compareTo(Object compareTo)` on each element during the sort. If the argument or a field on the argument is null and the implementation dereferences it without checking, the sort throws `System.NullPointerException`. The stack trace points into internal sort machinery, making it very difficult to trace back to the wrapper's `compareTo()` method.

**When it occurs:** Any time `List.sort()` is called on a list of wrappers where at least one instance has a null value in the sort-key field, or where a null wrapper instance itself is present in the list. This is common when wrappers are built from query results that include records with optional fields (e.g., Opportunity.Amount can be null).

**How to avoid:** Always null-check the incoming argument in `compareTo()` before accessing any field. A safe pattern:

```apex
public Integer compareTo(Object compareTo) {
    if (compareTo == null) return 1; // nulls sort last
    OpportunityWrapper other = (OpportunityWrapper) compareTo;
    Decimal thisAmt  = this.amount  == null ? -1 : this.amount;
    Decimal otherAmt = other.amount == null ? -1 : other.amount;
    if (thisAmt > otherAmt) return 1;
    if (thisAmt < otherAmt) return -1;
    return 0;
}
```

---

## Gotcha 2: Inner Classes Always Run in System Mode

**What happens:** A developer declares the outer class `with sharing` and assumes the inner wrapper class will also respect user record visibility. In reality, Apex inner classes always execute in system mode — they see all records regardless of the outer class's sharing declaration. Only SOQL and DML in the **outer class's own methods** are constrained by the outer class's sharing keyword.

**When it occurs:** When an inner class independently queries or modifies records (e.g., a heavy constructor that issues a SOQL query). The inner class bypasses record-level security even if the outer class is `with sharing`.

**How to avoid:** Do not issue SOQL or DML inside inner class constructors or methods. Perform all data access in the outer class (where `with sharing` is enforced) and pass results into the wrapper constructor as plain field values.

---

## Gotcha 3: @JsonAccess Is Required for Apex REST Deserialization

**What happens:** An `@RestResource` Apex class uses a custom wrapper as a typed parameter or deserializes the request body via `JSON.deserialize()`. At runtime the platform throws `System.JSONException: Type is not visible` even though the wrapper class is `public`.

**When it occurs:** Any time the Apex JSON deserializer encounters a class that lacks the `@JsonAccess` annotation. This is a compile-time-silent, runtime-fatal error — the code deploys successfully but fails on the first real HTTP call.

**How to avoid:** Add `@JsonAccess(serializable='always' deserializable='always')` at the class level on any wrapper used for Apex REST request or response binding. Use narrower variants (`serializable='never'`, `deserializable='samePackage'`, etc.) if the security policy requires tighter control. Inner classes cannot carry `@JsonAccess` — REST-bound wrappers must be top-level classes.

---

## Gotcha 4: Comparator Interface Requires API Version 60.0+ (Spring '24+)

**What happens:** A developer references `Comparator<T>` in an Apex class saved at API version 59 or earlier. The class fails to compile or deploys but throws a runtime error when `List.sort(Comparator)` is called.

**When it occurs:** In orgs or scratch org definitions that have not yet updated class-level API versions, or in packages that ship classes at a lower API version floor. The Comparator interface was introduced in Spring '24 (API v60.0); it does not exist at lower API versions.

**How to avoid:** Before using `Comparator<T>`, confirm the class file's API version is 60.0 or higher. In package development, set the minimum API version in `sfdx-project.json`. If the org is on an older release, fall back to `Comparable` with a flag-based sort direction.

---

## Gotcha 5: @AuraEnabled on Method Does Not Propagate to Wrapper Fields

**What happens:** The developer places `@AuraEnabled` on the Apex controller method that returns the wrapper list but forgets to annotate the fields on the wrapper class. The LWC component receives an array of objects where every custom property is `undefined`. The component renders empty rows with no JavaScript error in strict mode until a template binding tries to call a method on `undefined`.

**When it occurs:** Every time a wrapper class is introduced or a new field is added to an existing wrapper that will be consumed by a Lightning component. This is the single most common wrapper class mistake in LWC development.

**How to avoid:** As part of the wrapper class review checklist, enumerate every property the LWC HTML template references and confirm each has `@AuraEnabled`. Properties used only server-side should be left unannotated to minimize the JSON payload size.
