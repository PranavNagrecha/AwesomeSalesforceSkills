# Fault path template (Flow)

Every Create/Update/Delete/Action element in a flow can fail at runtime —
record locking, validation rule, CRUD/FLS, governor limit, callout timeout.
Without a Fault path, the error is caught by the platform but the flow stops
silently and the user sees a generic "An error has occurred" screen.

## What every fault path should do

1. **Capture the error** into a text variable (`{!$Flow.FaultMessage}`).
2. **Log it** via an `Application_Log__c` record (same object the Apex
   `ApplicationLogger` template writes to — one queryable log surface).
3. **Notify the user** via a screen flow error message or a Platform Event.
4. **Optionally notify operations** via an email alert on the log.

## Canonical fault path (declarative checklist)

```
[Create Records: Update Account]
  ├── (success) → next element
  └── (fault)   → [Assignment: Set Log Message]
                       ↓
                  [Create Records: Application_Log__c]
                       • Severity__c = 'ERROR'
                       • Source__c   = <flow API name>
                       • Message__c  = {!$Flow.FaultMessage}
                       • Request_Id__c = {!$Flow.InterviewGuid}
                       ↓
                  [Screen: "We couldn't save — please try again."]
                       ↓  (or dispatch platform event for user alerting)
                  [End]
```

## Reserved Flow fault variables

| Variable | What it contains |
|---|---|
| `{!$Flow.FaultMessage}` | Text of the error returned by the failing element |
| `{!$Flow.InterviewGuid}` | Unique ID for the flow interview — use as `Request_Id__c` for correlation with Apex logs |
| `{!$Flow.CurrentRecord}` | The record that failed in a record-triggered flow |

## What NOT to do

- Do not rely only on `{!$Flow.FaultMessage}` for screen flows on mobile —
  the string can be long and unformatted. Render a custom user-facing message
  and log the full detail.
- Do not set a fault path that simply ends the flow with no logging — the
  error is invisible to operations teams the moment the flow closes.
- Do not catch faults just to "continue" — you will corrupt data. If a flow
  cannot proceed safely, dispatch a platform event and halt.

## Related Apex

The `Application_Log__c` object referenced above is the same one the Apex
`ApplicationLogger.cls` template writes to. Deploying both gives you a single
queryable log surface across declarative and programmatic automation.
