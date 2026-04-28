---
name: flow-apex-defined-types
description: "Design and use Apex-Defined Types as Flow variables for structured non-sObject data (HTTP callout payloads, External Service responses, complex configuration). Trigger keywords: apex-defined type, flow variable, @AuraEnabled class, flow http callout response. Does NOT cover building HTTP Callout Actions themselves, External Services schema, or raw Apex invocable methods."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-23
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

An Apex-Defined Type is a plain Apex class whose instance fields are all
`@AuraEnabled` and serialisable. Flow reflects those fields as accessible
Flow variable attributes.

```apex
public class InvoiceLine {
    @AuraEnabled public String productCode;
    @AuraEnabled public Decimal quantity;
    @AuraEnabled public Decimal unitPrice;
    @AuraEnabled public List<String> tags;
}
```

Rules:

- Every exposed field **must** be `@AuraEnabled`.
- No `static`, no private state, no constructor params.
- Types: primitives, `Date`, `Datetime`, another Apex-Defined Type, or a
  `List<>` of the above.
- No `Map<>`. Flow cannot bind a Map — model it as `List<KeyValue>` where
  `KeyValue` is itself an Apex-Defined Type.

## Recommended Workflow

1. Identify the smallest serialisable shape Flow actually needs. Do not
   mirror the whole upstream class.
2. Write the Apex class with `@AuraEnabled` fields and no logic.
3. Write a unit test that serialises and deserialises an instance to
   prove the class is JSON round-tripable.
4. Reference the class as the Flow variable type. Bind from the HTTP
   Callout / External Service / invocable return.
5. Document the class in `references/examples.md` so future changes go
   through a review step.
6. When adding a field, check for Flow consumers first — removing a
   field is a breaking change to callers.

## Official Sources Used

- Apex-Defined Data Types in Flow —
  https://help.salesforce.com/s/articleView?id=sf.flow_ref_resources_variable_apex.htm
- @AuraEnabled —
  https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_classes_annotation_AuraEnabled.htm
