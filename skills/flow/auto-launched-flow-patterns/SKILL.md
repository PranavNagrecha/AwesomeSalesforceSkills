---
name: auto-launched-flow-patterns
description: "Use when invoking auto-launched Flows from Apex (Flow.Interview), from external systems via REST API, from Platform Events, or from other Flows (subflow element). Covers input/output variable mapping, bulkification patterns, and error/fault handling. NOT for record-triggered flows — use flow/record-triggered-flow-patterns. NOT for schedule-triggered flows — use flow/scheduled-flows."
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
  - "Flow API name (exact, copied from Setup)"
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
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# Auto-Launched Flow Patterns

This skill activates when a practitioner needs to invoke an auto-launched (no-UI) Flow from Apex code, an external system via the REST API, a Platform Event, or a parent Flow — and must correctly map variables, respect governor limits, and handle faults.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Flow API name:** Confirm the exact API name of the Flow from Setup > Flows. "If the flow doesn't exist in the current org, a TypeException is thrown" (apexref 262 L158086). UNVERIFIED (2026-10-20): that API names are case-sensitive in `createInterview()`; neither corpus says so, so copy the name exactly.
- **Variable access settings:** Each Flow variable must have its Input/Output Type set to "Input and Output," "Input Only," or "Output Only" as appropriate. In Metadata API terms these are `isInput` and `isOutput`, both false by default for variables created in API 25.0+ (api_meta 264 L75629-75658), so a new variable is Private until you change it. UNVERIFIED (2026-10-20): that this is "the most common mapping failure".
- **Invocation context:** Know whether the caller is synchronous Apex, a batch Apex job, a Platform Event-triggered process, the REST API, or a parent Flow. Each context has different limit and bulkification implications.
- **Governor limit budget:** "SOQL and DML limits apply during flow execution" (apexref 262 L157938), so every SOQL query and DML statement inside an Apex-invoked Flow counts against the synchronous limits of 100 queries and 150 DML statements (apexdev 264 L19747, L19757). UNVERIFIED (2026-10-20): that CPU time and heap are shared in the same way.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Which invoker starts the Flow: Apex, REST, platform event or parent Flow? | Decision Guidance: each has its own limit and error behaviour (platform_events 264 L2187-2188) | One invocation pattern chosen |
| Which variables does the caller set or read, and are `isInput` / `isOutput` set? | Gotcha 4: a missing or private variable returns null (apexref 262 L158151-158152; api_meta 264 L75629-75658) | A variable contract table |
| How many records can reach the Flow in one transaction? | Gotcha 1: SOQL and DML limits are shared (apexref 262 L157938) | A collection-input design and a limit budget |
| What happens when an element fails and who is told? | Gotcha 2: fault paths and `FlowException` (apexref 262 L214963) | A fault connector on each element and a log target |
| Is the Flow API name copied from Setup, and is it constant in code? | Gotcha 3: a missing flow throws TypeException (L158086) | One constant per Flow name |
| Does the Flow need to enforce the caller's sharing? | Core Concept 1: `with sharing` on API 62.0+ (apexref 262 L157958-157962) | A sharing decision per call site |
| Does the publisher need an answer back? | Gotcha 5: platform event flows run in a separate transaction (pe 264 L2187-2188) | Sync Apex or async event chosen on that basis |

A proper configuration adds a variable contract, a limit budget and a fault path before the first call; just wiring `start()` gives you none of them.

---

## Core Concepts

### Concept 1: Flow.Interview — Apex-to-Flow Bridge

The `Flow.Interview` class is the Apex API for invoking auto-launched Flows. The standard pattern is:

1. Build a `Map<String, Object>` of input variable name → value pairs.
2. Call `Flow.Interview.createInterview('Flow_API_Name', inputMap)` to create an interview instance.
3. Call `interview.start()` to execute the Flow.
4. Call `interview.getVariableValue('outputVarName')` to read output variables after `start()` returns.

`createInterview(flowName, inputVariables)` takes a `Map<String,Object>` of initial input values (apexref 262 L158094-158104; a namespaced overload adds the namespace, L158043-158048), and `start()` is `void` and works only for autolaunched or user provisioning flows (L158161-158177). A flow user runs the active version, falling back to the latest; an admin always runs the latest (L158179-158181). `getVariableValue(name)` returns null when the variable is not found in the running flow, and checks existence only at run time (L158151-158153). The guide recommends `createInterview()` only when you must reuse a method or class, because a packaged class needs the flow added manually and deleting a flow is not checked against it (L157941-157944); the static form is `new Flow.Interview.flowName(inputs)` (L157946-157950, example L157976-157978). `FlowException` is the built-in exception for "any problem with starting flow interviews from Apex", such as no active version (apexref 262 L214963-214964). UNVERIFIED (2026-10-20): that every unhandled Flow fault surfaces from `start()` as `System.FlowException`, that `createInterview` and `start()` are "both synchronous" as a documented guarantee, and the Apex-to-Flow type-mapping table that earlier text listed (neither corpus has one).

Sharing: to enforce sharing rules, run the flow or Apex on API 62.0 or later and declare the Apex class `with sharing`; the flow then enforces the sharing rules of the user who executed the class (apexref 262 L157958-157962).

### Concept 2: REST API Invocation via the Flows Resource

External systems (integration middleware, Experience Cloud pages, third-party apps) can start an auto-launched Flow using the Salesforce REST API:

- **Endpoint:** `POST /services/data/vXX.X/actions/custom/flow/<FlowApiName>`; the guide lists `flow` under `/actions/custom` (api_rest 264 L13679) and shows the call with a body `{"inputs": [ { ... } ]}` (L13532-13535). UNVERIFIED (2026-10-20): `/actions/standard/flow` (not in api_rest). `/services/data/vXX.X/process/rules` is not a Flow path at all: it "accesses a list of all active workflow rules" and POST triggers them (api_rest 264 L7623-7625); the earlier text called it a legacy path for older Flows.
- The response carries `actionName`, `errors`, `isSuccess` and `outputValues` (api_rest 264 L13589-13599).

A flow user invoking an autolaunched flow runs the active version, else the latest (api_rest 264 L13624-13625). "Run Flows" is the user permission for flow calls (object_reference 264 L140566-140567). With the `enableFlowViaRestUsesUserCtxt` setting, a flow run via REST uses the running user's profile and permission sets for object and field access (api_meta 264 L120069-120073, API 54.0+). UNVERIFIED (2026-10-20): the `api` and `flow` OAuth scopes.

### Concept 3: Platform Event as a Flow Trigger

An auto-launched Flow can be configured with a **Start element that listens for a Platform Event**. When the Platform Event fires, the flow receives the event messages: "a flow can receive a batch of event messages at once, up to a maximum of 200", in replay-ID order within the batch (platform_events 264 L2184-2186), so it is not one interview per message as earlier text said. This decouples the publisher (e.g., an Apex trigger) from the processing logic (the Flow). Key characteristics:

- Each platform event-triggered flow "runs asynchronously in a separate transaction from the transaction that published the event message", so there can be a delay (pe L2187-2189). Which limit set applies to that transaction is UNVERIFIED (2026-10-20): the guide does not say, and asynchronous delivery does not by itself imply asynchronous limits.
- The Flow reads event fields through the `$Record` global variable (pe L2156); the caller does not pre-populate variables.
- "If an event fails, the flow doesn't start. Because the flow is never triggered, a flow error email isn't sent" (pe L2201-2202). UNVERIFIED (2026-10-20): that a fault inside a started flow logs to Paused and Failed Flow Interviews.

### Concept 4: Calling an Auto-Launched Flow as a Subflow

A parent Flow can invoke another auto-launched Flow using the **Subflow** element. The parent maps its own variables to the child Flow's input variables and can receive output variables back. This enables modular, reusable logic packages. A FlowSubflow element "references another flow, which it calls at run time" and carries input and output assignments (api_meta 264 L75363-75378). UNVERIFIED (2026-10-20): that the child runs synchronously in the same transaction and shares the parent's governor limit budget; neither corpus states it.

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
            'Calculate_Opportunity_Discount',  // exact API name, copied from Setup
            inputs
        );

        try {
            pricingFlow.start();
        } catch (System.FlowException e) {
            // FlowException covers problems starting the interview (apexref 262 L214963);
            // that every in-flow fault surfaces this way is UNVERIFIED (2026-10-20)
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

The response fields are `actionName`, `errors`, `isSuccess`, `outputValues` (api_rest 264 L13589-13599); check `isSuccess` before reading `outputValues`. UNVERIFIED (2026-10-20): when `errors` is populated (fault versus input mismatch).

**Why not Apex REST custom endpoint:** Using the standard Flows REST resource avoids a custom Apex class, reducing the code surface area to maintain.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Apex needs to invoke Flow logic for a single record synchronously | `Flow.Interview.createInterview()` + `start()` in Apex | Direct, synchronous, output variables readable immediately |
| Apex trigger fires on up to 200 records and Flow does SOQL inside | Collect all records, pass as collection variable, single `start()` call | Prevents per-record SOQL multiplication against governor limits |
| External system needs to trigger a Flow via HTTP | REST Flows resource (`/actions/custom/flow/<ApiName>`) | No custom Apex endpoint needed; standard auth applies |
| Publisher needs to fire-and-forget async processing | Platform Event + Flow Start element listening on the event | Separate transaction; publisher does not block or share limits |
| A complex reusable logic block is needed across multiple Flows | Auto-launched Flow called as a Subflow element | Encapsulates logic; parent maps variables (api_meta 264 L75374-75378); same-transaction execution is UNVERIFIED (2026-10-20) |
| Flow logic must be retried on failure with no data loss | Platform Event + Flow (with fault path that re-publishes or logs) | Async invocation decouples retries from the original transaction |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. **Identify the invoker** — Apex (single record, bulk trigger, batch), REST, platform event or parent Flow, using the Decision Guidance table; copy the Flow API name from Setup > Flows.
2. **Fix the variable contract** — list each input and output variable with its type and confirm `isInput` / `isOutput` are set for the caller (api_meta 264 L75629-75658); prefix names `input` and `output`.
3. **Budget the limits** — estimate SOQL and DML per interview times the maximum interviews per transaction against 100 and 150 (apexdev 264 L19747, L19757); pass a collection and call `start()` once when the caller is bulk.
4. **Wire the failure path** — add a Fault connector to every element that can fail and wrap `start()` in a try/catch (`FlowException` covers start-up problems, apexref 262 L214963).
5. **Run the checker** — `python3 scripts/check_auto_launched_flow_patterns.py --manifest-dir <project>`; fix loop invocations, missing fault connectors and unmatched API names.
6. **Test both versions** — confirm which version runs (active, else latest for a flow user; always latest for an admin, apexref 262 L158179-158181) and record deviations in the template.

---

## Review Checklist

Run through these before marking auto-launched Flow invocation work complete:

- [ ] All Flow input/output variables have the correct Access setting (not "Private") and the Apex or API caller uses the exact variable API name with matching case
- [ ] Apex callers wrap `interview.start()` in a try/catch for `System.FlowException` (start-up problems, apexref 262 L214963); that uncaught in-flow faults surface in the caller this way is UNVERIFIED (2026-10-20)
- [ ] The Flow has a Fault connector on every element that can fail (Get Records, Create Records, Update Records, Delete Records, external calls); the fault path terminates gracefully and logs the fault message (`{!$Flow.FaultMessage}` is UNVERIFIED (2026-10-20): `$Flow.FaultMessage` is not in either corpus)
- [ ] In bulk Apex contexts (triggers, batch jobs), the invocation passes collection variables rather than calling `start()` once per record
- [ ] SOQL and DML counts inside the Flow have been estimated and verified to stay within the shared governor limit budget of the calling transaction
- [ ] For REST API invocations, the integration user has the "Run Flows" permission and the required object permissions for any DML the Flow performs
- [ ] The Flow API name used in Apex or the REST endpoint matches the Setup-visible API name exactly (including underscores and capitalisation)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Auto-launched Flows share the calling Apex transaction's SOQL and DML limits** — "SOQL and DML limits apply during flow execution" (apexref 262 L157938), against 100 queries and 150 DML statements synchronously (apexdev 264 L19747, L19757). UNVERIFIED (2026-10-20): CPU time and heap sharing. A Flow that is well within limits alone can push a batch trigger transaction into a LimitException; budget Flow resource usage when designing Apex-invoked Flows.

2. **`$Flow.FaultMessage` and the Fault path** — UNVERIFIED (2026-10-20): `$Flow.FaultMessage` is in neither corpus, nor is its fault-path-only availability, nor that the fault message is not logged automatically. The guide does say `FlowException` signals a problem starting an interview (apexref 262 L214963). Add a fault path on every DML/SOQL element and record the message in a custom log object or alert.

3. **Flow API name must match** — if the flow doesn't exist in the org, a TypeException is thrown (apexref 262 L158086). UNVERIFIED (2026-10-20): that `my_flow` and `My_Flow` are different references; always copy the API name from Setup > Flows rather than typing it.

4. **Output variables are `null` when the variable is not found** — `getVariableValue()` returns null if the variable can't be found in the running flow (apexref 262 L158151-158152). UNVERIFIED (2026-10-20): the same result when a path never assigns the variable, and when `start()` throws. Null-check output values in Apex before casting.

5. **Platform Event-triggered Flows run in a separate transaction** — "asynchronously in a separate transaction from the transaction that published the event message" (pe 264 L2187-2188), so the publisher cannot block them and their failures do not roll back the publisher. Record Ids in the event payload must be re-queried inside the Flow. The limit set for that transaction is UNVERIFIED (2026-10-20); do not assume asynchronous limits from the word asynchronous.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Apex Flow.Interview invocation snippet | Copy-paste Apex pattern with correct variable mapping, start(), and exception handling |
| Bulk collection invocation pattern | Apex pattern for passing record collections to a Flow in a trigger or batch context |
| REST API request/response example | HTTP request structure for calling a Flow from an external system |
| Fault path design recommendation | Guidance for connecting fault paths and capturing the fault message (`{!$Flow.FaultMessage}`: UNVERIFIED (2026-10-20): `$Flow.FaultMessage` is not in either corpus) |

---

## Related Skills

- `flow/record-triggered-flow-patterns` — use for Flows that start automatically when a record is created or updated; NOT invoked via Apex or REST
- `flow/scheduled-flows` — use for Flows that run on a time-based schedule; NOT invoked by external callers
- `flow/fault-handling` — deep-dive on Flow fault connector design, error logging, and recovery strategies
- `flow/flow-bulkification` — broader bulkification patterns covering loop-and-assignment anti-patterns inside Flows
- `flow/subflows-and-reusability` — use when designing modular Flows that call each other via the Subflow element
- `apex/invocable-methods` — use when Flows need to call Apex from inside the Flow (inverse of this skill)
