---
name: flow-invocable-from-apex
description: "Author @InvocableMethod Apex classes that Flow can call as Actions. Design the input / output variable contract, bulk semantics (one list in, one list out), null handling, and error surfacing. Also covers the inverse direction: calling a flow from Apex via Flow.Interview. NOT for general Apex authoring (use apex-service-selector-domain). NOT for REST-exposed Apex (use apex-rest-resource-patterns)."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Security
  - Performance
tags:
  - flow
  - apex
  - invocable
  - integration
  - bulkification
triggers:
  - "invocable apex from flow"
  - "flow action apex parameters"
  - "@InvocableMethod input output design"
  - "call flow from apex"
  - "flow interview createinterview"
  - "invocable apex bulk semantics"
inputs:
  - Business work the invocable must perform
  - Flow-facing variable shape (primitives, sObject, sObject list, custom Apex DTO)
  - Whether the caller needs bulk behavior (typical) or single-record
outputs:
  - An @InvocableMethod class with input + output wrapper DTOs
  - Unit tests covering single-record, bulk, null, and exception cases
  - Contract documentation for Flow authors consuming the action
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# Flow ↔ Apex — Invocable Methods

## Core concept — Flow-to-Apex is a bulk contract

When a Flow calls an Invocable Apex method, **Flow does NOT call once per record**. It calls **once with a `List<T>`**.

```apex
// Wrong — treats input as if it were one record per call.
@InvocableMethod(label='Geocode Address')
public static Result geocode(String street) { ... }   // COMPILE ERROR

// Right — Flow passes a List even if the caller "looks" single-record.
@InvocableMethod(label='Geocode Address')
public static List<Result> geocode(List<Request> requests) { ... }
```

This is identical to the bulk contract of a trigger. Flow is responsible for bulking up the records; your invocable is responsible for handling the list.

### Consequence

- An invocable that does SOQL inside a per-request loop will hit the 100-query limit at ~50 records.
- An invocable that does DML inside a per-request loop will hit the 150-DML-statement limit at ~75 records.
- Always query once for the whole input list, DML once for the whole result list.

## The contract surface

An `@InvocableMethod` has six settable parameters. Treat them as a public API — changes break every flow consuming the action.

```apex
@InvocableMethod(
    label='Calculate Shipping Rate',
    description='Returns a shipping rate for each provided address.',
    category='Logistics',
    callout=false,        // true if you do HTTP callouts
    iconName='standard:shipment'
)
public static List<RateResult> calculateRates(List<RateRequest> requests) { ... }
```

Three more things Flow authors see:

- **Input wrapper class** — fields marked `@InvocableVariable(required=true label='...' description='...')`.
- **Output wrapper class** — same annotation; description appears in Flow's Output pane.
- **The wrapper class itself** — must be a top-level or nested public class; top-level is better for reuse.

## Recommended Workflow

1. **Confirm the routing** — this step is genuinely Apex (`automation-selection.md`), and inside a flow that should remain declarative.
2. **Design the bulk contract first** — input list shape, output list shape, one-to-one or one-to-many mapping.
3. **Author request + response DTOs** with `@InvocableVariable` annotations. Include `description` on every field — it shows up in Flow Builder.
4. **Implement the method bulk-safe** — bulk query, loop over inputs to assemble work, bulk DML at the end.
5. **Handle nulls explicitly** — Flow can pass null collections when the caller forgot to provide inputs; return an empty list, don't throw.
6. **Wire error surfacing** — either throw `AuraHandledException` (if the calling Flow should fault) or populate an `error` output field (if the flow should branch on failure).
7. **Write a test class** — single-record, bulk, null-collection, partial-failure, governor-stress (N=200).
8. **Document the action in a short markdown block** — Flow authors won't read your code; they need the contract.

## Key patterns

### Pattern 1 — Bulk-safe shipping calculator

```apex
public class ShippingInvocable {

    public class RateRequest {
        @InvocableVariable(required=true label='Postal Code')
        public String postalCode;

        @InvocableVariable(required=true label='Weight (kg)')
        public Decimal weightKg;
    }

    public class RateResult {
        @InvocableVariable(label='Rate (USD)')
        public Decimal rateUsd;

        @InvocableVariable(label='Carrier')
        public String carrier;

        @InvocableVariable(label='Error Message')
        public String error;
    }

    @InvocableMethod(
        label='Calculate Shipping Rate',
        description='Returns a shipping rate per postal code / weight.',
        category='Logistics',
        callout=false
    )
    public static List<RateResult> calculate(List<RateRequest> requests) {
        if (requests == null || requests.isEmpty()) {
            return new List<RateResult>();
        }

        // Bulk query — one SOQL regardless of input size.
        Set<String> codes = new Set<String>();
        for (RateRequest r : requests) codes.add(r.postalCode);
        Map<String, Shipping_Rate__mdt> rateMap =
            new Map<String, Shipping_Rate__mdt>();
        for (Shipping_Rate__mdt rate :
                [SELECT Postal_Code__c, Rate_Usd__c, Carrier__c
                 FROM Shipping_Rate__mdt
                 WHERE Postal_Code__c IN :codes]) {
            rateMap.put(rate.Postal_Code__c, rate);
        }

        List<RateResult> results = new List<RateResult>();
        for (RateRequest r : requests) {
            RateResult rr = new RateResult();
            Shipping_Rate__mdt rate = rateMap.get(r.postalCode);
            if (rate == null) {
                rr.error = 'No rate configured for ' + r.postalCode;
            } else {
                rr.rateUsd = rate.Rate_Usd__c * r.weightKg;
                rr.carrier = rate.Carrier__c;
            }
            results.add(rr);
        }
        return results;
    }
}
```

Why this shape:
- One SOQL for any input size.
- Output list order matches input list order — Flow's Loop element relies on this invariant.
- Errors go in an `error` field so the Flow can branch on it; no exception is thrown.

### Pattern 2 — Action with a callout

```apex
@InvocableMethod(
    label='Geocode Address',
    description='Calls the geocoding vendor and returns lat/lng.',
    category='Address Hygiene',
    callout=true     // CRITICAL: required for callout actions
)
public static List<GeoResult> geocode(List<GeoRequest> requests) { ... }
```

Setting `callout=true` does two things:
- Forces the calling Flow to be called from an async context (Scheduled Path or autolaunched called from `Queueable`).
- Reserves the 10-second vs 60-second CPU limit appropriately.

### Pattern 3 — Calling Flow from Apex

The inverse direction: Apex needs to run a flow.

```apex
Map<String, Object> inputs = new Map<String, Object>{
    'recordId' => oppId,
    'stageName' => 'Negotiation'
};
Flow.Interview.MyFlow interview = new Flow.Interview.MyFlow(inputs);
interview.start();

Object out = interview.getVariableValue('outputStatus');
```

Or the generic form when the flow name is dynamic:

```apex
Flow.Interview flow = Flow.Interview.createInterview('MyFlowName', inputs);
flow.start();
```

Both forms run the flow in the current transaction and share governor limits (see `flow-transactional-boundaries`).

## Bulk safety

- **Design every invocable as if it will receive 200 inputs**, because a trigger-initiated flow batch can route that many through a single action call.
- **Output list length must match input list length.** Flow's Loop element walks inputs and outputs in parallel; drift causes silent data loss.
- **Keep state on the input wrapper, not in class-level statics.** Two flows using the same invocable can run in the same transaction; static caches leak data across calls.
- **Never do SOQL / DML inside a per-request loop.** Query once, DML once.

## Error handling

Three strategies, in order of preference:

1. **Soft error via output field.** Populate `result.error = 'message'`; Flow branches on `{!Result.error != null}`. Best for business-rule failures that the admin should handle.
2. **Flow Fault Path via thrown exception.** Throw `AuraHandledException` with a user-safe message; Flow's Fault connector captures it. Best for system failures that require admin logging / rollback.
3. **Fatal exception.** Throw a plain `Exception`; Flow errors out and the transaction rolls back. Use only when the work MUST be atomic with the caller.

**Never catch-and-swallow** in an invocable. Admins debugging flows can't see Apex logs; swallowed errors become silent data corruption.

## Well-Architected mapping

- **Reliability** — bulk-safe contracts make invocables survive under load without mysterious `LimitException`s. Null-input handling avoids `NullPointerException`s when flows pass empty collections.
- **Security** — invocables run with the `with sharing` posture declared on the class; default is inherited. Use `with sharing` unless you have a specific reason. Enforce FLS via `Schema.DescribeFieldResult.isAccessible()` or `WITH SECURITY_ENFORCED` in SOQL.
- **Performance** — a well-bulked invocable is cheaper per record than equivalent Flow logic because Apex can batch SOQL/DML more aggressively than Flow elements.

## Testing

Every invocable must have tests covering:

1. **Happy path, single record** — one input, one output, fields set as expected.
2. **Happy path, bulk (N=200)** — 200 inputs, 200 outputs, no governor limits hit, order preserved.
3. **Null input collection** — `calculate(null)` returns `[]` without throwing.
4. **Empty input collection** — `calculate(new List<Request>())` returns `[]`.
5. **Partial failure** — some inputs resolve, others populate the `error` field.
6. **Sharing context** — run the test as a non-admin to verify `with sharing` respects record-level access.

See `skills/apex/apex-testing-patterns` for test factory patterns.

## Gotchas

See `references/gotchas.md`.

## Official Sources Used

- Salesforce Developer — `@InvocableMethod` Annotation: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_classes_annotation_InvocableMethod.htm
- Salesforce Developer — `@InvocableVariable` Annotation: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_classes_annotation_InvocableVariable.htm
- Salesforce Developer — Flow.Interview Class: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_Flow_Interview.htm
- Salesforce Help — Customize Flow Behavior with Apex: https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_apex.htm
- Salesforce Architects — Well-Architected Framework: https://architect.salesforce.com/design/architecture-framework/well-architected
