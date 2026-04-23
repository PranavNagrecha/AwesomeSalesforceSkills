# Apex Flow Invocation From Apex — Work Template

Use this template when designing or reviewing Apex code that invokes a Flow.

## Scope

**Skill:** `apex-flow-invocation-from-apex`

**Request summary:** (what business problem is the Flow solving? why invoke from Apex?)

## Pre-Flight Checks

- [ ] Flow is **Autolaunched** (Flow Builder → Start element verifies Type).
- [ ] Input and output variables' API names and types are documented.
- [ ] Ownership is clear: who maintains the Flow, who maintains the Apex wrapper.
- [ ] Alternatives (inline Apex, Invocable Action framework) were considered.

## Context Gathered

- **Flow API name:**
- **Flow type (confirmed autolaunched):**
- **Input variables (name, Apex type, required):**
- **Output variables (name, Apex type):**
- **Caller context:** (trigger? Queueable? scheduled? LWC invocable?)
- **Expected record volume per invocation:**

## Approach

- [ ] Single invocation with a collection input (preferred for bulk)
- [ ] Per-invocation via Queueable wrapper (for failure isolation)
- [ ] Inline Apex instead (if Flow adds no declarative value)

## Code Sketch

```apex
public with sharing class {{FlowWrapper}} {
    private static final String FLOW_NAME = '{{FlowApiName}}';

    public static {{OutputType}} run({{InputType}} input) {
        Map<String, Object> params = new Map<String, Object>{
            '{{inputVar}}' => input
        };
        try {
            Flow.Interview i = Flow.Interview.createInterview(FLOW_NAME, params);
            i.start();
            Object out = i.getVariableValue('{{outputVar}}');
            return out == null ? null : ({{OutputType}}) out;
        } catch (Flow.FlowException e) {
            System.debug(LoggingLevel.ERROR, FLOW_NAME + ' failed: ' + e.getMessage());
            throw e;
        }
    }
}
```

## Checklist

- [ ] `Flow.Interview.createInterview` called once per transaction, not in a loop.
- [ ] Flow name is a class-level constant (not scattered inline).
- [ ] `.start()` wrapped in try/catch.
- [ ] Every `getVariableValue` is null-checked before cast.
- [ ] Parameter map values use correct Apex types (Decimal, Date, SObject).
- [ ] Test covers success, missing output, and a Flow failure path.

## Notes

Any admin-team coordination notes, Flow version history references, or reasons this invocation is not inlined in Apex.
