---
name: apex-wrapper-class-patterns
description: "Use when designing wrapper or inner classes in Apex to combine SObjects with computed fields, shape data for LWC consumption, or sort collections with Comparable or Comparator. Trigger keywords: wrapper class, inner class, Comparable, Comparator, @AuraEnabled fields, @JsonAccess. NOT for JSON serialization mechanics — use apex-json-serialization. NOT for LWC data-binding patterns — use lwc-reactive-state-patterns or lwc-lightning-record-forms."
category: apex
salesforce-version: "Spring '24+"
well-architected-pillars:
  - Performance
  - Reliability
triggers:
  - "apex wrapper class SObject computed field combine rollup display LWC"
  - "sort apex list custom object Comparable Comparator multiple sort strategies"
  - "@AuraEnabled wrapper class LWC wire imperative result shape"
  - "inner class apex sharing mode system context outer class"
  - "@JsonAccess annotation REST deserialize wrapper"
tags:
  - apex-wrapper
  - inner-class
  - comparable
  - comparator
  - aura-enabled
  - json-access
inputs:
  - "SObject types and computed/aggregate fields that need to be combined in a single response object"
  - "Sort criteria (single or multiple) for a list of wrapper or custom objects"
  - "Target consumer: LWC component (needs @AuraEnabled), Apex REST endpoint (needs @JsonAccess), or internal Apex service"
outputs:
  - "Wrapper class definition with correct field annotations for the target consumer"
  - "Comparable or Comparator implementation for controlled list sorting"
  - "Guidance on inner-class sharing context and @JsonAccess requirements"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-19
---

# Apex Wrapper Class Patterns

Activate this skill when you need to design a wrapper or inner class that combines SObject data with computed fields, shapes results for LWC or REST consumers, or applies custom sort logic to Apex collections. The skill covers the full anatomy of a wrapper class — field annotation, sharing context, sort interface selection, and JSON serialization requirements — grounded in official Apex Developer Guide and Apex Reference Guide sources.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Consumer target**: LWC component, Apex REST endpoint, or internal service? The answer determines which annotations are required (@AuraEnabled, @JsonAccess, or neither).
- **Sort requirements**: Does the wrapper need to be sortable in a single way (Comparable) or in multiple, caller-selected ways (Comparator, requires API v60+ / Spring '24+)?
- **Sharing context**: Is the outer class declared `with sharing` or `without sharing`? Inner classes do NOT inherit the outer class's sharing keywords — they always run in system mode unless the inner class itself is declared with a sharing keyword (which Apex does not allow on inner classes). The outer-class declaration is what governs.

---

## Core Concepts

### 1. Wrapper Class Anatomy

A wrapper class is a plain Apex class (or inner class) that exists solely in heap memory. It has no DML footprint, no `@isTest`-only lifecycle, and no schema metadata. Its only purpose is to bundle fields — SObject records, computed values, aggregated rollups — into a shape the consumer can traverse without additional queries.

Key anatomy points (Apex Developer Guide — Inner Classes):
- Inner classes cannot be declared `static` in Apex (unlike Java). Every inner-class instance implicitly holds a reference to an instance of the outer class.
- Inner classes can be `private`, `public`, or `global` — scope the visibility to the smallest required level.
- Inner classes inherit the governor context of the outer class transaction but execute in **system mode** regardless of the outer class's sharing declaration. The outer class's `with sharing` / `without sharing` declaration governs records the outer class itself fetches; inner class code running in that same transaction context is still in system mode for any DML or SOQL it independently executes.

### 2. Comparable vs Comparator

**Comparable interface** (`System.Comparable`, available all API versions):
- Implement `Integer compareTo(Object compareTo)` on the wrapper class itself.
- `List.sort()` uses this contract.
- The sort order is baked into the class — a single fixed strategy.
- `compareTo()` **must guard against null arguments**. Passing a null to `compareTo()` when Salesforce's sort internals invoke it throws `NullPointerException` at runtime and surfaces as a confusing limit error.

**Comparator interface** (`System.Comparator<T>`, API v60+ / Spring '24+):
- Implement `Integer compare(T o1, T o2)` on a separate comparator class.
- `List.sort(Comparator<T>)` accepts a comparator instance.
- Enables multiple interchangeable sort strategies (ascending, descending, by different fields) without modifying the wrapper class.
- Requires **API version 60.0 or higher** — do not use in classes saved at v59 or earlier.

**Decision rule:** use Comparable when there is exactly one natural ordering; use Comparator (Spring '24+) when multiple orderings are needed or when the wrapper class should stay annotation-free for its sort logic.

### 3. @AuraEnabled and LWC Consumption

To expose a wrapper class to LWC via `@wire` or imperative Apex:
- The **method** returning the wrapper must be `@AuraEnabled(cacheable=true)` (for wire) or `@AuraEnabled` (for imperative).
- **Every field** on the wrapper that LWC needs to read must also carry `@AuraEnabled`. Fields without the annotation are invisible to the Lightning Data Service and JavaScript client — they arrive as `undefined` in the component.
- `@AuraEnabled` cannot be placed on transient fields.
- Wrapper class instances returned from `@AuraEnabled` methods are serialized to JSON by the platform; no explicit JSON.serialize() call is needed.

### 4. @JsonAccess for Apex REST

When a wrapper class is used as the request body of an `@RestResource` method, Salesforce's JSON deserializer requires the class to carry `@JsonAccess(serializable='always' deserializable='always')` (or narrower variants). Without this annotation, deserialization throws `System.JSONException: Type is not visible` at runtime. Serialization (outbound only) requires `serializable='always'`. This annotation is class-level, not field-level.

---

## Common Patterns

### Pattern 1: Account + Computed Rollup Wrapper for LWC

**When to use:** A Lightning component needs to display Account records alongside a computed field (e.g., open opportunity count, total contract value) that cannot be expressed in a single SOQL query return type or a formula field.

**How it works:**
1. Define an inner class `AccountRow` on the Apex controller with `@AuraEnabled` on each field.
2. Query Accounts and aggregate data separately.
3. Combine into `AccountRow` instances and return the list.
4. LWC iterates the returned list; each property is directly accessible.

See `references/examples.md` — Example 1 for a full annotated code listing.

**Why not a plain SObject list:** SObjects cannot carry computed fields. Returning raw SObjects forces the component to do client-side arithmetic or triggers an additional wire call.

### Pattern 2: Multi-Strategy Sort with Comparator (Spring '24+)

**When to use:** A list of wrapper instances must be sortable in different ways depending on context (e.g., sort by name ascending, then separately by value descending) without baking the sort into the wrapper class.

**How it works:**
1. Define separate comparator classes implementing `Comparator<WrapperType>`.
2. Call `myList.sort(new NameAscComparator())` or `myList.sort(new ValueDescComparator())` at the call site.
3. The wrapper class itself remains annotation-free with respect to sort logic.

See `references/examples.md` — Example 2 for a full code listing.

**Why not Comparable:** Comparable hard-wires a single sort order and requires modifying the wrapper class when the order changes.

### Pattern 3: REST Request/Response Wrapper

**When to use:** An `@RestResource` Apex class accepts or returns a structured JSON payload that maps to a custom shape — not an SObject.

**How it works:**
1. Define a top-level (not inner) class with `@JsonAccess(serializable='always' deserializable='always')`.
2. Declare public fields matching the JSON key names.
3. Use `(MyWrapper) JSON.deserialize(RestContext.request.requestBody.toString(), MyWrapper.class)` or rely on automatic parameter binding.

**Why not Map<String,Object>:** Untyped maps require `instanceof` checks everywhere, produce verbose code, and cannot be validated by the compiler.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| LWC needs SObject + computed field | Wrapper inner class with `@AuraEnabled` on all fields | LWC cannot read unannotated fields; inner class keeps the controller self-contained |
| Single fixed sort order on wrapper list | Implement `Comparable` on the wrapper class | Simple, one contract, no extra class needed |
| Multiple sort strategies needed | Implement separate `Comparator<T>` classes (API v60+) | Wrapper stays clean; sort logic is swappable at call site |
| Apex REST endpoint needs typed request body | Top-level class with `@JsonAccess(serializable='always' deserializable='always')` | Platform JSON deserializer rejects classes without this annotation |
| Wrapper used only inside Apex service layer | Plain inner class, no annotations | Minimum surface area; no annotation overhead |
| Wrapper needs to be sorted AND exposed to LWC | Both `Comparable` and `@AuraEnabled` on fields | The two contracts are independent and can coexist |

---

## Recommended Workflow

1. **Identify the consumer and shape requirements.** Determine whether the wrapper is consumed by LWC (needs `@AuraEnabled` fields), an Apex REST endpoint (needs `@JsonAccess`), or only internal Apex. Note any sort requirements.
2. **Choose inner class vs top-level class.** Use an inner class when the wrapper is used only by its enclosing controller or service. Promote to a top-level class when (a) two or more unrelated classes share the wrapper, (b) it needs `@JsonAccess` for REST (which requires a top-level class in practice), or (c) it needs to be `global`.
3. **Declare fields with minimum required annotations.** Add `@AuraEnabled` only to fields the LWC client must read. Add `@JsonAccess` at class level if REST serde is required. Never annotate fields that should remain server-only.
4. **Implement sort interface(s).** If a single natural ordering exists, implement `Comparable` and write a null-safe `compareTo()`. If multiple orderings are needed and the org is on API v60+, create separate `Comparator<T>` classes instead.
5. **Write the population logic.** Query the required SObjects, compute derived values, and assemble wrapper instances. Avoid calling DML inside wrapper constructors — keep constructors as pure field assignment.
6. **Test sorting edge cases.** Write unit tests with null-field wrappers to confirm `compareTo()` / `compare()` handles nulls without throwing `NullPointerException`. Test both ascending and descending order.
7. **Review against the checklist below** before marking the work complete.

---

## Review Checklist

- [ ] Every field the LWC template reads carries `@AuraEnabled`
- [ ] `@JsonAccess` is present on any wrapper used for Apex REST deserialization
- [ ] `compareTo()` has a null guard (returns a defined integer, never dereferences the argument without null check)
- [ ] `Comparator<T>` usage is restricted to classes saved at API v60.0 or higher
- [ ] Inner class is not assumed to inherit outer-class sharing — sharing behavior verified
- [ ] No DML inside wrapper constructors
- [ ] Unit tests cover: null fields in sort, empty list, single-element list

---

## Salesforce-Specific Gotchas

1. **`compareTo()` null throws NullPointerException at sort time** — When `List.sort()` invokes `compareTo()` internally and the argument is null (e.g., a wrapper instance with a null sort key), any unguarded dereference throws `System.NullPointerException` at runtime. The stack trace points into the sort internals, making it hard to diagnose. Always null-check the argument before comparing field values.

2. **Inner classes run in system mode regardless of outer-class sharing** — A developer declares the outer class `with sharing` expecting the inner wrapper class to respect record-level security. The inner class itself always runs in system mode for any SOQL or DML it executes independently. Sharing enforcement comes only from the outer-class methods that perform the queries.

3. **@JsonAccess is required for Apex REST deserialization** — Omitting `@JsonAccess(deserializable='always')` causes `System.JSONException: Type is not visible` at runtime even though the class is `public`. This error is invisible at compile time and only surfaces when the REST endpoint is called.

4. **Comparator interface requires API v60+ (Spring '24+)** — Classes saved at API version 59 or earlier cannot reference `System.Comparator`. Deploying such a class to a target org that enforces API version minimums silently falls back to a runtime error. Check the API version of the class file before using Comparator.

5. **@AuraEnabled on method but not on wrapper fields** — The `@AuraEnabled` on the returning Apex method does not cascade to the wrapper's fields. Each field the LWC template binds to must independently carry `@AuraEnabled`. Missing annotation causes the property to be `undefined` in JavaScript with no compile-time error.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Wrapper class definition | Inner or top-level class with correct field annotations for the target consumer |
| Comparable implementation | `compareTo()` method with null guard for single-strategy list sorting |
| Comparator implementation | Separate comparator class(es) for multi-strategy sorting (API v60+) |
| @AuraEnabled controller method | Method returning the wrapper list, shaped for LWC wire or imperative use |
| @JsonAccess-annotated class | Top-level wrapper class ready for Apex REST request/response binding |

---

## Related Skills

- apex-json-serialization — for JSON.serialize / JSON.deserialize mechanics, custom serializers, and handling platform JSON limits
- lwc-reactive-state-patterns — for LWC reactive properties, wire adapters, and component state management after receiving wrapper results
- lwc-lightning-record-forms — for standard LWC record forms that do not need a custom wrapper class
- apex-soql-relationship-queries — for querying the SObject data that wrappers aggregate
- apex-aggregate-queries — for building the aggregate SOQL results that feed computed fields in wrappers
