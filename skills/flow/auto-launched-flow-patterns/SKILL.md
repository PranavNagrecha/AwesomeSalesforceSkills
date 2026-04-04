---
name: auto-launched-flow-patterns
description: "Use when invoking auto-launched Flows from Apex (Flow.Interview), from external systems via REST API, from Platform Events, or from other Flows (subflow element). Covers input/output variable mapping, bulkification patterns, and error/fault handling. NOT for record-triggered flows (use record-triggered-flow-patterns) or scheduled flows (use scheduled-flows)."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "How do I call a Flow from Apex and read its output variables?"
  - "How do I invoke an auto-launched Flow via the Salesforce REST API from an external system?"
  - "My auto-launched Flow called from Apex is hitting governor limits or not handling errors"
  - "How do I pass input variables into a Flow started by a Platform Event?"
  - "How do I call one Flow from another Flow using a subflow element?"
  - "Auto-launched flow returning null output — how to debug input/output variable mapping"
tags:
  - flow
  - auto-launched-flow
  - apex-flow-interview
  - rest-api
  - platform-events
  - bulkification
inputs:
  - "Flow API name (exact, case-sensitive)"
  - "Names and data types of Flow input and output variables"
  - "The invocation context: Apex, REST API, Platform Event trigger, or subflow"
  - "Bulk volume expectations (single record vs. batch context)"
outputs:
  - "Correct Apex Flow.Interview invocation pattern with variable mapping"
  - "REST API request structure for the Flows resource"
  - "Fault-handling guidance for auto-launched Flow invocations"
  - "Bulkification pattern for calling Flows in batch Apex context"
  - "Review checklist for existing auto-launched Flow configurations"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Auto-Launched Flow Patterns

This skill activates when a practitioner needs to invoke an auto-launched (no-UI) Flow from Apex code, an external system via the REST API, a Platform Event, or a parent Flow — and must correctly map variables, respect governor limits, and handle faults.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Flow API name:** Confirm the exact API name of the Flow from Setup > Flows. API names are case-sensitive in `Flow.Interview.createInterview()` calls; a mismatch throws a runtime exception.
- **Variable access settings:** Each Flow variable must have its Input/Output Type set to "Input and Output," "Input Only," or "Output Only" as appropriate. Variables marked "Private" cannot be accessed by the caller — this is the most common mapping failure.
- **Invocation context:** Know whether the caller is synchronous Apex, a batch Apex job, a Platform Event-triggered process, the REST API, or a parent Flow. Each context has different limit and bulkification implications.
- **Governor limit budget:** Auto-launched Flows invoked from Apex share the calling transaction's governor limits — every SOQL query and DML statement inside the Flow counts against the transaction's limits. A Flow that is fine in isolation may push a batch transaction over the limit.

---

## Core Concepts

### Concept 1: Flow.Interview — Apex-to-Flow Bridge

The `Flow.Interview` class is the Apex API for invoking auto-launched Flows. The standard pattern is:

1. Build a `Map<String, Object>` of input variable name → value pairs.
2. Call `Flow.Interview.createInterview('Flow_API_Name', inputMap)` to create an interview instance.
3. Call `interview.start()` to execute the Flow.
4. Call `interview.getVariableValue('outputVarName')` to read output variables after `start()` returns.

`createInterview` and `start()` are both synchronous. The Flow runs to completion (or fault) before `start()` returns. Any unhandled fault in the Flow causes `start()` to throw a `System.FlowException`, which must be caught in the Apex caller.

**Type mapping:** Apex types map to Flow types as follows — `String` → Text, `Boolean` → Boolean, `Integer`/`Long`/`Decimal`/`Double` → Number or Currency, `Date` → Date, `DateTime` → DateTime, `Id`/`SObject` → Record (use the SObject Id string when mapping). Collection variables map to `List<>` in Apex. If the types do not match, `start()` or `getVariableValue()` throws a runtime exception.

### Concept 2: REST API Invocation via the Flows Resource

External systems (integration middleware, Experience Cloud pages, third-party apps) can start an auto-launched Flow using the Salesforce REST API:

- **Endpoint:** `POST /services/data/vXX.X/actions/standard/flow` (Invocable Actions endpoint; see also the legacy `/services/data/vXX.X/process/rules` path for older Flows).
- For the dedicated Flows resource: `POST /services/data/vXX.X/actions/custom/flow/<FlowApiName>` where inputs are passed as a JSON body.
- The response body contains output variable values as JSON key-value pairs.

Authentication requires a valid OAuth access token with the `api` and `flow` scopes. The running user must have the "Run Flows" permission. If the Flow performs DML or SOQL, the user must also have the relevant object-level permissions.

### Concept 3: Platform Event as a Flow Trigger

An auto-launched Flow can be configured with a **Start element that listens for a Platform Event**. When the Platform Event fires, Salesforce starts one Flow interview per event message. This decouples the publisher (e.g., an Apex trigger) from the processing logic (the Flow). Key characteristics:

- The Flow runs asynchronously in a separate transaction from the event publisher.
- Because it is a separate transaction, governor limits reset — the Flow does not share limits with the publisher's Apex transaction.
- Flow variables cannot be pre-populated by the caller; the Flow reads fields directly from the `$Record` event payload variables.
- If the Flow faults, it logs to **Paused and Failed Flow Interviews** but does not propagate the exception back to the publisher.

### Concept 4: Calling an Auto-Launched Flow as a Subflow

A parent Flow can invoke another auto-launched Flow using the **Subflow** element. The parent maps its own variables to the child Flow's input variables and can receive output variables back. This enables modular, reusable logic packages. When the parent calls the subflow, the child Flow runs synchronously in the same transaction, sharing the same governor limit budget.

---

## Common Patterns

### Pattern 1: Apex Caller with Input/Output Variable Mapping

**When to use:** Business logic is managed in a Flow so admins can change it without a code deployment. Apex triggers the logic (e.g., during record save) and must read a result back.

**How it works:**

```apex
// In a trigger handler or service class
public static void applyPricingDiscount(List<Opportunity> opps) {
    for (Opportunity opp : opps) {
        Map<String, Object> inputs = new Map<String, Object>{
            'inputOpportunityId'  => opp.Id,
            'inputProductFamily'  => opp.Product_Family__c
        };

        Flow.Interview pricingFlow = Flow.Interview.createInterview(
            'Calculate_Opportunity_Discount',  // exact API name — case-sensitive
            inputs
        );

        try {
            pricingFlow.start();
        } catch (System.FlowException e) {
            // Unhandled Flow fault propagates as FlowException
            throw new AuraHandledException('Pricing flow failed: ' + e.getMessage());
        }

        Decimal discount = (Decimal) pricingFlow.getVariableValue('outputDiscountPercent');
        opp.Discount__c = discount;
    }
}
```

**Critical detail — calling in a loop:** The pattern above calls `start()` once per record inside a for-loop. This is acceptable only for small record sets. In a bulk context (200 records from a trigger), each `start()` call incurs separate SOQL and DML from inside the Flow. If the Flow issues one SOQL query, 200 records × 1 query = 200 SOQL calls against the 100-query limit. **Bulk pattern:** See Pattern 2.

**Why not plain Apex:** Pricing rules change frequently. By encoding them in Flow, an admin can update the logic without a code change or deployment window.

### Pattern 2: Bulkification — Collect Records, Invoke Once with a Collection Variable

**When to use:** The Flow logic must be applied to all records in a bulk trigger invocation without hitting the SOQL or DML governor limits.

**How it works:**

1. In the Flow, change the input variable type to **Collection of Record** (e.g., a collection of Opportunity records or a collection of SObject Ids as Text collection).
2. Inside the Flow, process the collection using a Loop element rather than relying on the Apex caller to loop.
3. In Apex, collect all records first, then call `start()` once passing the whole collection.

```apex
// Collect all records first
List<Opportunity> oppsToProcess = new List<Opportunity>(opps);

Map<String, Object> inputs = new Map<String, Object>{
    'inputOpportunities' => oppsToProcess
};

Flow.Interview bulkFlow = Flow.Interview.createInterview(
    'Bulk_Opportunity_Processor',
    inputs
);

try {
    bulkFlow.start();
} catch (System.FlowException e) {
    throw new AuraHandledException('Bulk flow failed: ' + e.getMessage());
}

List<SObject> results =
    (List<SObject>) bulkFlow.getVariableValue('outputProcessedRecords');
```

**Why it works:** A single `start()` call incurs the Flow's SOQL and DML once, regardless of collection size. The Flow's Loop element iterates internally without multiplying external API calls.

### Pattern 3: REST API Invocation from External System

**When to use:** An external system (middleware, portal, third-party app) needs to trigger Flow logic in Salesforce without direct Apex access.

**How it works:**

```http
POST /services/data/v62.0/actions/custom/flow/My_Auto_Launched_Flow
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "inputs": [
    {
      "inputAccountId": "001xx000003Gyb2",
      "inputRequestType": "Renewal"
    }
  ]
}
```

**Response:**

```json
[
  {
    "actionName": "My_Auto_Launched_Flow",
    "errors": null,
    "isSuccess": true,
    "outputValues": {
      "outputCaseId": "500xx000001CXeU",
      "outputStatus": "Created"
    }
  }
]
```

The `errors` array is populated if the Flow throws a fault or if input variables do not match. Always check `isSuccess` before reading `outputValues`.

**Why not Apex REST custom endpoint:** Using the standard Flows REST resource avoids a custom Apex class, reducing the code surface area to maintain.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Apex needs to invoke Flow logic for a single record synchronously | `Flow.Interview.createInterview()` + `start()` in Apex | Direct, synchronous, output variables readable immediately |
| Apex trigger fires on up to 200 records and Flow does SOQL inside | Collect all records, pass as collection variable, single `start()` call | Prevents per-record SOQL multiplication against governor limits |
| External system needs to trigger a Flow via HTTP | REST Flows resource (`/actions/custom/flow/<ApiName>`) | No custom Apex endpoint needed; standard auth applies |
| Publisher needs to fire-and-forget async processing | Platform Event + Flow Start element listening on the event | Separate transaction; publisher does not block or share limits |
| A complex reusable logic block is needed across multiple Flows | Auto-launched Flow called as a Subflow element | Encapsulates logic; parent maps variables; runs in same transaction |
| Flow logic must be retried on failure with no data loss | Platform Event + Flow (with fault path that re-publishes or logs) | Async invocation decouples retries from the original transaction |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking auto-launched Flow invocation work complete:

- [ ] All Flow input/output variables have the correct Access setting (not "Private") and the Apex or API caller uses the exact variable API name with matching case
- [ ] Apex callers wrap `interview.start()` in a try/catch for `System.FlowException`; uncaught Flow faults cause unhandled exceptions in the caller
- [ ] The Flow has a Fault connector on every element that can fail (Get Records, Create Records, Update Records, Delete Records, external calls); the fault path terminates gracefully and logs the `{!$Flow.FaultMessage}` value
- [ ] In bulk Apex contexts (triggers, batch jobs), the invocation passes collection variables rather than calling `start()` once per record
- [ ] SOQL and DML counts inside the Flow have been estimated and verified to stay within the shared governor limit budget of the calling transaction
- [ ] For REST API invocations, the integration user has the "Run Flows" permission and the required object permissions for any DML the Flow performs
- [ ] The Flow API name used in Apex or the REST endpoint matches the Setup-visible API name exactly (including underscores and capitalisation)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Auto-launched Flows share the calling Apex transaction's governor limits** — SOQL queries, DML statements, CPU time, and heap space consumed inside the Flow all count against the same 100-SOQL/150-DML limits as the Apex caller. A Flow that is well within limits when called in isolation can push a batch trigger transaction into a LimitException. Always budget Flow resource usage when designing Apex-invoked Flows.

2. **`$Flow.FaultMessage` is only available on the Fault path** — If the Flow does not have a Fault connector on a failing element, the error propagates as an unhandled `System.FlowException` in the Apex caller. The fault message is not automatically logged. The best practice is to add a fault path on every DML/SOQL element that writes `{!$Flow.FaultMessage}` to a custom log object or sends an alert email. Without this, debugging production failures requires parsing generic exception messages.

3. **Flow API name is case-sensitive in Apex and REST calls** — `Flow.Interview.createInterview('my_flow', inputs)` and `Flow.Interview.createInterview('My_Flow', inputs)` are different references. Salesforce stores Flow API names exactly as entered. A mismatch causes a runtime exception. Always copy the API name from Setup > Flows rather than typing it by hand.

4. **Output variables are `null` if `start()` throws or if the variable is not reachable** — If the Flow execution path never assigns the output variable (e.g., the path was short-circuited by a Decision element), `getVariableValue()` returns `null`. Always null-check output values in Apex before casting or using them.

5. **Platform Event-triggered Flows run asynchronously with reset limits** — Unlike Apex-invoked Flows, Platform Event-triggered Flows run in a new transaction. This means they cannot be controlled or blocked by the publisher, and their failures do not affect the publisher's transaction. However, it also means that any record Ids passed in the event payload must be re-queried inside the Flow — the publisher's in-memory state is not shared.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Apex Flow.Interview invocation snippet | Copy-paste Apex pattern with correct variable mapping, start(), and exception handling |
| Bulk collection invocation pattern | Apex pattern for passing record collections to a Flow in a trigger or batch context |
| REST API request/response example | HTTP request structure for calling a Flow from an external system |
| Fault path design recommendation | Guidance for connecting fault paths and capturing `{!$Flow.FaultMessage}` |

---

## Related Skills

- `flow/record-triggered-flow-patterns` — use for Flows that start automatically when a record is created or updated; NOT invoked via Apex or REST
- `flow/scheduled-flows` — use for Flows that run on a time-based schedule; NOT invoked by external callers
- `flow/fault-handling` — deep-dive on Flow fault connector design, error logging, and recovery strategies
- `flow/flow-bulkification` — broader bulkification patterns covering loop-and-assignment anti-patterns inside Flows
- `flow/subflows-and-reusability` — use when designing modular Flows that call each other via the Subflow element
- `apex/invocable-methods` — use when Flows need to call Apex from inside the Flow (inverse of this skill)
