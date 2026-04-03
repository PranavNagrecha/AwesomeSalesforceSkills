# Flow Fault Handling Review

## Flow Context

- Flow name:
- Flow type:
- Caller or trigger:
- Business owner:

## Fallible Elements

| Element | Why It Can Fail | Fault Connector Present? | Failure Outcome |
|---------|-----------------|--------------------------|-----------------|
|         |                 |                          |                 |

## User Experience on Failure

- User sees:
- Retry path:
- Support handoff:

## Diagnostic Handling

- `$Flow.FaultMessage` captured where:
- Error log object or notification path:
- Admin owner of failures:

## Bulk and Volume Review

- Data load or integration entry point:
- Repeated `Get Records` risks:
- Related-record fan-out risks:
- Invocable Apex list-safe confirmation:

## Release Decision

- Safe to deploy:
- Follow-up actions:
