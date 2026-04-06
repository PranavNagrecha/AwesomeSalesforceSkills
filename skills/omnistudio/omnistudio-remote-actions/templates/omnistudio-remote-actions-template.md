# OmniStudio Remote Action — Work Template

Use this template when configuring or reviewing Remote Actions in an OmniScript or FlexCard.

## Scope

**Skill:** `omnistudio-remote-actions`

**Request summary:** (fill in what the user asked for)

## Context Gathered

- **Consuming component:** (OmniScript / FlexCard / LWC wrapper)
- **Backend type:** (Integration Procedure / Apex class / REST endpoint / DataRaptor)
- **OmniStudio package type:** (native `omnistudio` / managed `vlocity_cmt`)
- **Known constraints:** (timeout limits, payload size, governor concerns)

## Action Configuration

| Setting | Value |
|---|---|
| Action Type | (Integration Procedure Action / Apex Remote Action / REST Action / DataRaptor Action) |
| Target | (IP name / Apex class name / Endpoint) |
| Method Name | (for Apex Remote Actions) |
| Send JSON Path | (specific node — never blank) |
| Response JSON Path | (dedicated output node — never blank) |
| Invoke Mode | (Promise / Fire and Forget / On Click) |

## Input Contract

| Field | Source in OmniScript JSON | Type | Required |
|---|---|---|---|
| (field name) | (JSON path) | (String/Number/Boolean/Object) | (Yes/No) |
| | | | |

## Output Contract

| Field | Key in outputMap / IP Response | Type | Consumed By |
|---|---|---|---|
| (field name) | (exact key name — case-sensitive) | (String/Number/Boolean/Object) | (Step X element Y) |
| | | | |

## Apex Class Skeleton (if Apex Remote Action)

```apex
global class __ACTION_CLASS_NAME__ implements __NAMESPACE__.VlocityOpenInterface2 {

    global Object invokeMethod(String methodName, Map<String, Object> inputMap,
                               Map<String, Object> outputMap, Map<String, Object> options) {
        if (methodName == '__METHOD_NAME__') {
            // Read from inputMap
            // Execute business logic
            // Write results to outputMap
            outputMap.put('__OUTPUT_KEY__', result);
        }
        return null;
    }
}
```

## Pre-Deployment Checklist

- [ ] Action type matches backend complexity (IP for orchestration, Apex for single ops)
- [ ] Send JSON Path is scoped — not blank
- [ ] Response JSON Path targets a dedicated node — not blank
- [ ] Invoke mode is Promise for any data consumed by current or later steps
- [ ] Apex class is `global` with `global` invokeMethod (if Apex Remote Action)
- [ ] Apex writes to `outputMap`, not return value
- [ ] outputMap key casing matches OmniScript JSON path references exactly
- [ ] Named Credentials used for external callouts — no hardcoded URLs or tokens
- [ ] Error handling returns user-friendly messages
- [ ] Tested: happy path, empty input, null fields, backend error, timeout

## Notes

(Record any deviations from the standard pattern and why.)
