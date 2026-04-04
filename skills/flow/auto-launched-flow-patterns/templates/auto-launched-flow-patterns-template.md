# Auto-Launched Flow Patterns — Work Template

Use this template when designing or reviewing an auto-launched Flow invocation.

---

## Scope

**Skill:** `auto-launched-flow-patterns`

**Request summary:** (fill in what was asked — e.g., "Call flow X from Apex trigger," "Expose flow Y to external REST caller," "Debug flow Z not returning output values")

---

## Context Gathered

Answer these before touching any code or configuration:

| Question | Answer |
|---|---|
| Flow API name (exact, from Setup > Flows) | |
| Flow process type (must be AutoLaunchedFlow) | |
| Invocation method (Apex / REST API / Platform Event / Subflow) | |
| Input variable names, types, and Access settings | |
| Output variable names, types, and Access settings | |
| Maximum record volume (single record / bulk trigger / batch job) | |
| Does the caller need a synchronous return value? | |
| Org governor limit budget available (SOQL headroom, DML headroom) | |

---

## Invocation Pattern Selection

| Criterion | Decision |
|---|---|
| Synchronous return value required → | Use `Flow.Interview` from Apex |
| Bulk volume (>1 record) in trigger or batch → | Pass collection variable; single `start()` call |
| External (non-Apex) caller → | Use REST `/actions/custom/flow/<ApiName>` |
| Fire-and-forget async, no return value needed → | Platform Event + Flow Start on event |
| Reusable sub-logic within another Flow → | Subflow element in parent Flow |

**Selected pattern:** _______________

---

## Apex Invocation Snippet (if applicable)

```apex
// Replace placeholders with actual values
private static final String FLOW_API_NAME = '<FlowApiName>';  // exact API name

Map<String, Object> inputs = new Map<String, Object>{
    '<inputVariableName>'  => <value>
    // add more input variables as needed
};

Flow.Interview flowInterview = Flow.Interview.createInterview(FLOW_API_NAME, inputs);

try {
    flowInterview.start();
} catch (System.FlowException fe) {
    // Log and handle — do not swallow silently
    System.debug(LoggingLevel.ERROR, FLOW_API_NAME + ' failed: ' + fe.getMessage());
    throw fe;
}

// Read output — always null-check before casting
Object rawOutput = flowInterview.getVariableValue('<outputVariableName>');
if (rawOutput != null) {
    <OutputType> result = (<OutputType>) rawOutput;
    // use result
}
```

---

## REST API Request Skeleton (if applicable)

```http
POST /services/data/v62.0/actions/custom/flow/<FlowApiName>
Authorization: Bearer <oauth_access_token>
Content-Type: application/json

{
  "inputs": [
    {
      "<inputVariableName>": "<value>"
    }
  ]
}
```

**Check before sending:**
- [ ] Integration user has "Run Flows" permission
- [ ] Integration user has required object-level permissions for any DML inside the Flow
- [ ] `isSuccess` is checked before reading `outputValues` in the response

---

## Flow Variable Checklist

| Variable Name | Type | Access Setting | Mapped From/To |
|---|---|---|---|
| | | Input Only / Input and Output / Output Only | |

- [ ] No variable that should be externally accessible is set to "Private"
- [ ] Apex variable names match Flow variable API names exactly (case-sensitive)

---

## Fault Path Checklist

For each DML or external-call element in the Flow:

| Element Name | Element Type | Fault Connector Present? | Fault Path Action |
|---|---|---|---|
| | recordCreates / recordUpdates / recordDeletes / actionCalls | Yes / No | Log to Error_Log__c / Send email / Assignment + End |

- [ ] Every DML element has a Fault connector
- [ ] Fault paths write `{!$Flow.FaultMessage}` to a durable log or notification
- [ ] Apex caller wraps `start()` in try/catch for `System.FlowException`

---

## Governor Limit Impact Estimate

| Resource | Flow Uses Per Interview | Max Interviews (bulk) | Total Projected | Org Limit | Headroom |
|---|---|---|---|---|---|
| SOQL queries | | | | 100 | |
| DML statements | | | | 150 | |
| CPU time (ms) | | | | 10,000 | |

- [ ] Total projected SOQL + DML stays within org limits
- [ ] If not: switch to collection variable pattern or async Platform Event

---

## Notes

Record any deviations from the standard pattern and the reason:

-
