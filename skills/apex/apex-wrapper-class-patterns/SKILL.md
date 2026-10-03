---
name: apex-wrapper-class-patterns
description: "Use when designing wrapper or inner classes in Apex to combine SObjects with computed fields, shape data for LWC consumption, or sort collections with Comparable or Comparator. Trigger keywords: wrapper class, inner class, Comparable, Comparator, @AuraEnabled fields, @JsonAccess, return a wrapper list to LWC, sort a list of wrapper objects. NOT for JSON serialization mechanics — use apex/apex-json-serialization. NOT for LWC data-binding patterns — use lwc/lwc-reactive-state-patterns."
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
  - "return a list of wrapper objects from Apex to a Lightning web component"
  - "sort a list of custom Apex objects by two different fields"
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
  - "Top-level wrapper class, controller, comparator, and test class ready to deploy"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

# Apex Wrapper Class Patterns

Use this skill to design a wrapper class that combines sObject data with computed values, shapes results for a Lightning web component, an Aura component, or an Apex REST consumer, or sorts a list of custom objects. It covers where the wrapper class lives, which annotations each consumer needs, sharing behavior, and null-safe sorting.

---

## Before Starting

- **Who consumes the wrapper?** A Lightning web component or Aura component, an Apex REST endpoint, or only other Apex. The answer decides top-level vs inner class and which annotations are needed.
- **Is it a parameter, a return value, or both?** Custom classes passed in from a component need `@AuraEnabled` properties with getters and setters.
- **How many sort orders?** One natural order fits `Comparable`. Several caller-selected orders fit `Comparator<T>`.
- **Does the wrapper ever run its own SOQL or DML?** Then its sharing declaration matters; inner classes don't adopt the container's sharing mode.
- **Will another namespace serialize or deserialize it?** Only then does `@JsonAccess` need widening.

---

## Questions to Ask Before Configuring

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "Will a Lightning web component or Aura component receive or send this object?" | The LWC and Aura guides say an Apex inner class as a parameter or return value isn't supported | A top-level wrapper class instead of an inner class | A component contract that is supported, not one that works until it doesn't |
| "Which properties does the component read?" | Only public instance properties and methods annotated with `@AuraEnabled` are serialized | The exact list of annotated properties | Smaller payloads and no `undefined` values in the template |
| "Is the wrapper also passed back to Apex as a parameter?" | Custom-class parameters need `@AuraEnabled` on each property plus a getter and setter | `{get; set;}` on those properties | Round-trips that deserialize cleanly |
| "Does any wrapper method query or write records?" | Inner classes don't adopt the container's sharing mode; in API 67.0 and later a class without a declaration runs with sharing | An explicit sharing keyword on the class that touches data | Record access that is decided on purpose |
| "Can a sort key be null, or can the list contain null entries?" | The Comparable and Comparator references say implementations must handle nulls to avoid a null pointer exception | A null ordering rule (nulls first or last) | Sorts that never fail on real data |
| "Does code in another namespace or package serialize this class?" | From API 49.0 the default `@JsonAccess` for both directions is `sameNamespace` | `@JsonAccess` only where cross-namespace access is real | No over-broad `always` access on internal types |

What a proper design adds over "just add an inner class": the wrapper uses a supported component contract, exposes only what the client needs, sorts safely, and has a sharing and serialization posture someone chose.

---

## Core Concepts

### Where the class lives

| Consumer | Class placement | Annotations |
|---|---|---|
| Lightning web component or Aura component | Top-level class (not an inner class, no inheritance) | `@AuraEnabled` on each public property the client reads; getters and setters on properties received as parameters |
| Apex REST resource in the same namespace | Top-level or inner class | None required; `@JsonAccess` only to open access to another namespace or package |
| Internal Apex only | Inner class is fine | None |

Inner classes behave like static Java inner classes: they can have instance member variables, but there is no implicit pointer to an instance of the outer class. Inner classes have no static methods or variables.

### Two meanings of `@AuraEnabled`

On a static method it makes the method callable from a component. On instance properties and methods it makes them serializable when an instance is returned. The Aura guide says not to mix the two uses in the same Apex class, so keep the controller (static methods) and the wrapper (instance properties) in separate top-level classes.

### Sharing

You can declare a sharing mode on inner and outer classes, and inner classes don't adopt the container's mode. In API 67.0 and later, a class without an explicit declaration runs with sharing. In 66.0 and earlier, such a class that isn't an entry point takes the sharing mode of its caller. Wrappers that only hold values never reach this question; keep data access in the service or controller.

### Sorting

`Comparable.compareTo(Object)` gives one natural order for `List.sort()`. `Comparator<T>.compare(T, T)` is passed to `List.sort(comparator)` to choose an order at the call site. Both references require explicit null handling. For locale-sensitive order use `Collator`, and avoid it in triggers because results depend on the running user. UNVERIFIED (2026-10-03): the API version that introduced `System.Comparator`; version 1.0.0 of this skill stated 60.0, and the 262 references give no version.

### `@JsonAccess`

`@JsonAccess(serializable=... deserializable=...)` sits at class level and accepts `never`, `sameNamespace`, `samePackage`, or `always`. If it restricts the operation, a runtime `JSONException` is thrown. In API 49.0 and later the default for both is `sameNamespace`. A subclass doesn't inherit the annotation.

---

## Common Patterns

### Pattern 1: Account plus computed count for a component

A top-level `AccountRow` class with `@AuraEnabled` properties, a separate `with sharing` controller that queries, aggregates, and builds rows, and a test class. Full deployable listing in `references/code-examples.md`.

### Pattern 2: Several sort orders with `Comparator<T>`

One comparator class per order, each null-safe, selected at the call site. The wrapper class stays unchanged when a new order is added.

### Pattern 3: REST request and response wrapper

A typed class deserialized with `(MyRequest) JSON.deserialize(RestContext.request.requestBody.toString(), MyRequest.class)`. Add `@JsonAccess` only if a managed package or another namespace must serialize or deserialize it.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Component needs sObject plus computed fields | Top-level wrapper class with `@AuraEnabled` properties | Inner classes as parameters or return values aren't supported |
| Component sends the wrapper back to Apex | Add `{get; set;}` to each `@AuraEnabled` property | Required for custom-class parameters |
| One fixed sort order | `Comparable` on the wrapper | One contract, no extra class |
| Several sort orders | `Comparator<T>` classes | Order chosen at the call site |
| REST payload in the same namespace | Typed class, no `@JsonAccess` | Default `sameNamespace` already allows it |
| Payload crosses a namespace or package | `@JsonAccess` with the narrowest value that works | Restrictive access throws `JSONException` |
| Wrapper used only inside a service | Inner class, no annotations | Smallest surface |

---

## Recommended Workflow

1. **Name the consumer and direction.** Component return, component parameter, REST, or internal.
2. **Place the class.** Top-level for components; inner is fine for internal use.
3. **Annotate the minimum.** `@AuraEnabled` on properties the client reads; getters and setters where the client sends data; `@JsonAccess` only for cross-namespace serialization.
4. **Add sorting.** `Comparable` or `Comparator<T>`, with an explicit null rule.
5. **Keep data access out of the wrapper.** Query and aggregate in a `with sharing` controller or service; the wrapper constructor assigns fields.
6. **Test.** 200-row build, null sort keys, null list entries, empty list; then run `python3 scripts/check_apex_wrapper_class_patterns.py --manifest-dir force-app/main/default/classes`.

---

## Review Checklist

- [ ] No inner class is a parameter or return type of an `@AuraEnabled` method
- [ ] Controller (static `@AuraEnabled` methods) and wrapper (`@AuraEnabled` properties) are separate classes
- [ ] Every property the template reads carries `@AuraEnabled`
- [ ] Properties received from a component have getters and setters
- [ ] `compareTo()` and `compare()` handle null arguments and null keys
- [ ] Any class that queries or writes records declares its sharing mode
- [ ] `@JsonAccess` appears only where another namespace or package needs it
- [ ] Tests cover null sort keys, null entries, empty list, and 200 rows

---

## Salesforce-Specific Gotchas

See `references/gotchas.md`. The one that breaks the most components: returning an inner class from an `@AuraEnabled` method, which the LWC guide lists as unsupported.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Wrapper class | Top-level class with `@AuraEnabled` properties, or an inner class for internal use |
| Controller | `with sharing` class with static `@AuraEnabled` methods |
| Comparator classes | Null-safe sort orders |
| Test class | Bulk and null-case coverage |

---

## Related Skills

- `apex/apex-json-serialization`: `JSON.serialize` and `JSON.deserialize` mechanics and custom serializers
- `lwc/lwc-reactive-state-patterns`: component state after receiving wrapper results
- `lwc/lwc-lightning-record-forms`: standard record forms that need no custom wrapper
- `apex/apex-soql-relationship-queries`: querying the sObject data wrappers combine
- `apex/apex-aggregate-queries`: aggregate SOQL that feeds computed wrapper fields
