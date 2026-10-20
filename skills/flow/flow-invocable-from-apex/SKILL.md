---
name: flow-invocable-from-apex
description: "Author @InvocableMethod Apex classes that Flow can call as Actions. Design the input / output variable contract, bulk semantics (one list in, one list out), null handling, and error surfacing. Also covers the inverse direction: calling a flow from Apex via Flow.Interview. NOT for wiring the action into Flow Builder and mapping flow variables — use flow/flow-action-framework. NOT for exposing the same Apex over REST — use apex/apex-rest-services."
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
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
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

- An invocable that does one SOQL query per input hits the 100-query synchronous limit at the 101st input (200 asynchronous, apexdev 264 L19747).
- An invocable that does one DML statement per input hits the 150-statement limit at the 151st input (apexdev 264 L19757).
- The guide ties the bulk contract to the platform: "the i-th Output entry must correspond to the i-th Input entry ... when your action is in bulkified execution, such as when an apex action is used in a record trigger flow" (apexdev 264 L5510-5512).
- Always query once for the whole input list, DML once for the whole result list.

## The contract surface

An `@InvocableMethod` has seven optional modifiers — `label`, `description`, `callout`, `capabilityType`, `category`, `configurationEditor`, `iconName` (apexdev 264 L5458-5470). Treat them as a public API — changes break every flow consuming the action.

```apex
@InvocableMethod(
    label='Calculate Shipping Rate',
    description='Returns a shipping rate for each provided address.',
    category='Logistics',
    callout=false,        // true if the method calls an external system
    iconName='standard:shipment'
)
public static List<RateResult> calculateRates(List<RateRequest> requests) { ... }
```

Three more things Flow authors see:

- **Input wrapper class** — fields marked `@InvocableVariable(required=true label='...' description='...')`.
- **Output wrapper class** — same annotation; description appears in Flow's Output pane.
- **The wrapper class itself** — a custom global or public Apex class with at least one `@InvocableVariable` member (apexdev 264 L5490-5492); the class holding the `@InvocableMethod` must be an outer class (L5475). Top-level wrappers are better for reuse.
- **Variable rules** — only global and public member variables qualify; a property, a static, a final or a protected/private variable cannot be an invocable variable (apexdev 264 L5773-5778). `defaultValue` with `required` throws an error (L5748). Starting in API version 66.0 the class used for an invocable action parameter must have a visible no-argument constructor (L5792-5794).

## Recommended Workflow

1. **Confirm the routing** — this step is genuinely Apex (`automation-selection.md`), and inside a flow that should remain declarative.
2. **Design the bulk contract first** — input list shape, output list shape, one-to-one or one-to-many mapping.
3. **Author request + response DTOs** with `@InvocableVariable` annotations. Include `description` on every field — it shows up in Flow Builder.
4. **Implement the method bulk-safe** — bulk query, loop over inputs to assemble work, bulk DML at the end.
5. **Handle nulls explicitly** — Flow can pass null collections when the caller forgot to provide inputs (UNVERIFIED (2026-10-20): not in the corpus; the guard is defensive); return an empty list, don't throw.
6. **Wire error surfacing** — populate an `error` output field (if the flow should branch on failure) or throw `AuraHandledException` (if the calling Flow should fault; see Error handling for what is unverified).
7. **Test and document the contract.** Write a test class (single-record, bulk, null-collection, partial-failure, governor-stress at N=200) and publish a short markdown block for Flow authors — input/output names, types, and fault behavior.

## Questions to Ask Before Configuring

Ask these before writing the method. Each one maps to a gotcha in `references/gotchas.md`.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "How many records can reach this action in one transaction, and from which flow type?" | The input is a list and the output must match it in size and order (apexdev 264 L5510-5512); per-input SOQL or DML breaks at 101 or 151 inputs (gotchas 1, 2) | A tested batch size and an N=200 test |
| "Does the method call an external system?" | `callout=true` changes how a screen flow handles the transaction (apexdev 264 L27275-27285; gotcha 4) | The modifier set from the method body, not from memory |
| "What are the wrapper's field types and visibility?" | Only global or public member variables qualify, not properties, statics or finals (apexdev 264 L5773-5778; gotcha 3) | A wrapper reviewed against that list, with a no-argument constructor at API 66.0+ |
| "What does the flow author do on failure: branch, fault, or roll back?" | The error strategy decides the output shape (gotcha 9) | One of three strategies chosen per failure class |
| "What `apiVersion` is the class saved at, and is sharing declared?" | Default access mode and sharing flipped at 67.0 (apexdev 264 L11926-11937; gotcha 8) | The `.cls-meta.xml` version and an explicit sharing keyword |
| "Is any state kept in statics, and will two flows share a transaction?" | A static persists for the whole transaction (apexdev 264 L3746-3748; gotcha 6) | State held on the input wrapper or in local variables |
| "If Apex starts a flow, is it autolaunched, what is its API name, and which variables does Apex read?" | `start()` runs only autolaunched and user provisioning flows; a missing flow throws `TypeException` (apexref 262 L158128, L158169-158177; gotchas 5, 7) | The API name, flow type and the variable names, confirmed in Setup |

A proper configuration adds a contract that survives 200 inputs, a failure path the flow author chose, and a class version and sharing posture someone decided, none of which "just adding an `@InvocableMethod`" provides.

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
- Output list order matches input list order — the guide requires it for bulkified execution (apexdev 264 L5510-5512).
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

What `callout=true` does, in the guide's words: "screen flows use this modifier to determine whether the action can be executed safely in the current transaction" (apexdev 264 L27275-27276). When the modifier is true, the action's Transaction Control setting in a screen flow lets the flow decide, and the current transaction has uncommitted work, "the flow commits the current transaction, starts a new transaction, and makes the call" (L27278-27282). The flow runs the action in the current transaction when the modifier is false, when a non-screen flow runs it, or when there is no uncommitted work (L27283-27285, L27294).

That replaces the earlier claims that `callout=true` forces an asynchronous context (Scheduled Path or `Queueable`) and "reserves" a CPU limit. Neither appears in the corpus: the CPU limits are 10,000 ms synchronous and 60,000 ms asynchronous for every Apex transaction (apexdev 264 L19782), not a `callout` effect.

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

"SOQL and DML limits apply during flow execution" (apexref 262 L157938); see `flow/flow-transactional-boundaries`. `start()` works only for autolaunched and user provisioning flows (apexref 262 L158169-158177). `createInterview` takes the flow's API name and throws a `TypeException` when the flow does not exist in the org (apexref 262 L158101, L158128); the guide recommends it only when you must reuse a method or class, because a packaged class must have the flow added manually and deleting a flow is not checked against `createInterview()` references (apexref 262 L157941-157944). To enforce sharing, run the flow or Apex on API version 62.0 or later with the Apex class declared `with sharing` (apexref 262 L157958-157962).

## Bulk safety

- **Design every invocable as if it will receive 200 inputs**: "Any Apex code, whether a trigger, a class or an extension, may be invoked for 1 to 200 records" (apexdev 264 L40790).
- **Output list length must match input list length and order** (apexdev 264 L5510-5512). UNVERIFIED (2026-10-20): that Flow's Loop element walks them in parallel, and that drift causes silent data loss, is not stated in the corpus.
- **Keep state on the input wrapper, not in class-level statics.** "The value of a static variable persists within the context of a single transaction" (apexdev 264 L3746-3748), so two flows calling the same invocable in one transaction share it.
- **Never do SOQL / DML inside a per-request loop.** Query once, DML once.

## Error handling

Three strategies, in order of preference:

1. **Soft error via output field.** Populate `result.error = 'message'`; Flow branches on `{!Result.error != null}`. Best for business-rule failures that the admin should handle. The guide's own `@InvocableMethod` example catches the exception per input, sets a success flag on the result and keeps processing the other values (apexdev 264 L5388-5400).
2. **Flow Fault Path via thrown exception.** Throw `AuraHandledException` with a user-safe message; Flow's Fault connector captures it. Best for system failures that require admin logging / rollback. UNVERIFIED (2026-10-20): the Apex Reference describes `AuraHandledException` as "Returns a custom error message to a JavaScript controller" (apexref 262 L214924); that a Flow fault connector captures it is not in the corpus.
3. **Fatal exception.** Throw a plain `Exception`; Flow errors out and the transaction rolls back. Use only when the work MUST be atomic with the caller. UNVERIFIED (2026-10-20): the rollback behaviour of an unhandled invocable exception is not described in the corpus.

**Never catch-and-swallow** in an invocable. Admins debugging flows can't see Apex logs; swallowed errors become silent data corruption. UNVERIFIED (2026-10-20): both statements are advice, not corpus claims.

## Well-Architected mapping

- **Reliability** — bulk-safe contracts make invocables survive under load without mysterious `LimitException`s. Null-input handling avoids `NullPointerException`s when flows pass empty collections.
- **Security** — invocables run with the sharing posture declared on the class. For API 67.0 and later, "classes without an explicit sharing declaration run in with sharing mode"; at 66.0 and earlier an undeclared class is `with sharing` when a class in its inheritance chain is saved at 67.0 or later or when it is an Aura controller, takes its caller's mode when it is not an entry point, and is otherwise `without sharing` (apexdev 264 L11930-11937). Declare it explicitly and use `with sharing` unless you have a specific reason. Enforce FLS on reads with `WITH USER_MODE` and on writes with `Security.stripInaccessible(AccessType.CREATABLE, records).getRecords()` (apexdev 264 L11913-11915 for `stripInaccessible`, L11926-11927 for `WITH USER_MODE`). UNVERIFIED (2026-10-20): the "API 57.0+" floor for `WITH USER_MODE` is not in the corpus (the `accessLevel` parameter of `Database.query` is 55.0+, apexdev 264 L11609). The default flipped by API version: "In API version 67.0 and later, Apex runs in user context by default ... In API version 66.0 and earlier, system mode is the default" (apexdev 264 L11928-11929), and "In API version 67.0 and later, you can't use the WITH SECURITY_ENFORCED clause in SOQL SELECT queries in Apex code" (L11926). So `WITH SECURITY_ENFORCED` is available only to classes saved below API 67.0. The gate is the `apiVersion` in the class's `.cls-meta.xml`, not the org's release (apexdev 264 L11926-11929, listed under Versioned Behavior Changes).
- **Performance** — a well-bulked invocable is cheaper per record than equivalent Flow logic because Apex can batch SOQL/DML more aggressively than Flow elements.

## Testing

Every invocable must have tests covering:

1. **Happy path, single record** — one input, one output, fields set as expected.
2. **Happy path, bulk (N=200)** — 200 inputs, 200 outputs, no governor limits hit, order preserved.
3. **Null input collection** — `calculate(null)` returns `[]` without throwing.
4. **Empty input collection** — `calculate(new List<Request>())` returns `[]`.
5. **Partial failure** — some inputs resolve, others populate the `error` field.
6. **Sharing context** — run the test as a non-admin to verify `with sharing` respects record-level access.

See `skills/apex/test-class-standards` for test class standards and `skills/apex/test-data-factory-patterns` for test factory patterns.

## `@IntegrationTest` for live Agentforce / Data 360 callouts (Developer Preview)

Standard `@IsTest` methods mock callouts and roll back all DML — they cannot assert on real Agentforce or Data 360 responses. Summer '26 adds **`@IntegrationTest`** (class or method, apexdev 264 L5207) plus **`@TearDown`** cleanup methods (L6343). Integration tests may perform live callouts and commit mid-transaction via `IntegrationTest.commitTestOnly()`.

Constraints as documented in the developer guide: **Developer Preview** in scratch orgs, Summer '26 (API version 67.0) (apexdev 264 L5209-5210); feature **`ApexIntegrationTests`** in the scratch org definition (L42711-42713); tests are **asynchronous only, one concurrent execution per org** (L42703-42704). UNVERIFIED (2026-10-20): that they run through Tooling `runTestsAsynchronous` specifically is not in the corpus (L41625 names that endpoint for tests generally). Use for invocable actions that call Agentforce or Data 360 in ways `@IsTest` cannot simulate — not as a replacement for bulk-safe unit tests of the invocable contract itself.

## Gotchas

See `references/gotchas.md`.

## Official Sources Used

- Salesforce Developer — `@InvocableMethod` Annotation: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_classes_annotation_InvocableMethod.htm
- Salesforce Developer — `@InvocableVariable` Annotation: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_classes_annotation_InvocableVariable.htm
- Salesforce Developer — Flow.Interview Class: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_Flow_Interview.htm
- Salesforce Help — Customize Flow Behavior with Apex: https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_apex.htm
- Salesforce Architects — Well-Architected Framework: https://architect.salesforce.com/design/architecture-framework/well-architected
