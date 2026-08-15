---
name: flow-apex-defined-types
description: "Design and use Apex-Defined Types as Flow variables for structured non-sObject data (HTTP callout payloads, External Service responses, complex configuration). Trigger keywords: apex-defined type, flow variable. NOT for building HTTP Callout Actions themselves, External Services schema, or raw Apex  — use flow/flow-external-services."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - apex-defined type
  - flow variable shape
  - http callout response flow
  - external services response type
tags:
  - flow
  - apex-defined-type
  - http-callout
  - external-services
  - typed-variables
inputs:
  - Proposed non-primitive Flow variable shape
  - Upstream source (HTTP Callout / External Service / Invocable Apex return)
  - Consumers (screen display, loop, sub-flow)
outputs:
  - Apex-Defined Type class stub with @AuraEnabled fields
  - Flow variable binding guidance
  - Caller-contract checklist
dependencies:
  - flow/flow-http-callout-action
  - flow/flow-invocable-from-apex
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-08-14
---

# Flow Apex-Defined Types

## Adoption Signals

- Flow needs a typed, structured, non-sObject value (nested JSON, complex
  response, config object).
- HTTP Callout Action or External Service response cannot be modelled
  cleanly as primitives.
- An invocable Apex method must return a multi-field structure into Flow.

## When NOT To Use

- The shape is a real sObject — use the sObject variable.
- The shape is a flat list of primitives — a collection of primitives is
  lighter.
- The structure changes frequently — prefer JSON string + targeted parse
  to avoid churn on the Apex class.

## Contract

An Apex-Defined Type is a data-only Apex class whose fields Flow reflects as
variable attributes. The constraints are unusually tight, and **almost all of
them compile cleanly and fail in the flow at run time** — which is the defining
property of this domain.

| Requirement | Detail |
|---|---|
| Field types | Boolean, Integer, Long, Decimal, Double, Date, DateTime, String — single values and lists of each, plus lists of other supported Apex-defined types |
| Annotation | `@AuraEnabled` on every field Flow must see |
| Constructor | A no-argument constructor is **required** |
| Inner classes | **Not supported** |
| Outer class named the same as an inner class | Not supported |
| Class methods | Not supported |
| Getter methods for fields | Not supported |
| List of lists as a field | Not supported |
| Referential integrity | Not supported — modify or delete a field in the class and the flow fails |

```apex
// InvoiceLine.cls — top-level, in its own file.
public class InvoiceLine {
    @AuraEnabled public String  productCode;
    @AuraEnabled public Decimal quantity;
    @AuraEnabled public Decimal unitPrice;
    @AuraEnabled public List<String> tags;

    // Required: a no-argument constructor. Declared explicitly so that adding
    // a convenience constructor later does not silently remove it.
    public InvoiceLine() {}
}
```

**Two consequences people miss.** There is no `Map` on the supported type list —
model it as `List<KeyValue>` with `KeyValue` as its own **top-level** class. And
because inner classes are unsupported, a nested structure is built from separate
top-level classes, not from the nested-class shape every Apex developer reaches
for first.

## When NOT To Use

- The shape is a real sObject — use the sObject variable.
- The shape is a flat list of primitives — a collection of primitives is lighter.
- The structure changes faster than a deploy cycle — a JSON string plus a
  targeted parse avoids churning a class whose every field is a commitment.
- You need map semantics inside the flow. Flow has no map either, so a key
  lookup over a `List<KeyValue>` is a Loop with a Decision — O(n) per lookup,
  multiplied by the interview batch size. Resolve it in Apex and expose named
  fields.

## Recommended Workflow

1. **Identify the smallest shape Flow actually consumes.** Do not mirror the
   upstream schema — referential integrity is unsupported, so every exposed
   field is a name you have committed not to change without a caller inventory.
2. **Write each type as a top-level class in its own file,** with `@AuraEnabled`
   on every field, an explicit no-argument constructor, no methods, and no
   getters.
3. **Check every field type against the supported list.** No `Map`, no list of
   lists, no sObject fields.
4. **Write two tests:** one that JSON round-trips an instance (which also proves
   the no-argument constructor exists), and one that asserts the serialized
   field-name set, so a rename fails the build rather than the next scheduled
   batch.
5. **Bind the class as the Flow variable type** from the HTTP Callout, External
   Service, or invocable return. For invocables, take and return `List<>` so the
   flow can call once with a collection instead of once per record inside a loop.
6. **Treat the field names as a published interface.** Adding a field is safe;
   renaming or removing one is a breaking change with no compile-time signal, so
   inventory the consuming flows first.

## Official Sources Used

- Considerations for the Apex-Defined Data Type — https://help.salesforce.com/s/articleView?id=platform.flow_considerations_apex_data_type.htm&type=5
- Apex-Defined Data Type — https://help.salesforce.com/s/articleView?id=platform.flow_concepts_apex_type.htm&type=5
- Extend Flows with the Apex-Defined Data Type — https://help.salesforce.com/s/articleView?id=sf.flow_build_extend_apex_type.htm&type=5
- AuraEnabled Annotation — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_annotation_AuraEnabled.htm
- Supported Data Types in Flows (LWC Developer Guide) — https://developer.salesforce.com/docs/platform/lwc/guide/use-flow-data-types.html

The full annotated list is in `references/well-architected.md`.
