# HTTP Callout Review Worksheet

## Endpoint And Identity

| Item | Value |
|---|---|
| Named Credential | |
| External Credential | |
| Identity model | Org-wide / Per-user |
| Endpoint path | |
| Timeout | |

## Request Contract

| Concern | Decision |
|---|---|
| HTTP method | |
| Required headers | |
| Payload schema | |
| Expected success status codes | |
| Retryable status codes | |

## Guardrails

- [ ] Endpoint uses `callout:` syntax
- [ ] No secret or token is hardcoded in Apex
- [ ] Queueable or Batch callout workers implement `Database.AllowsCallouts`
- [ ] Non-200 responses are classified explicitly
- [ ] Tests include success, auth failure, and timeout-like behavior

## Operational Notes

**Failure destination:**  
Custom object / Platform event / AsyncApexJob monitoring / External monitor

**Retry owner:**  
Manual / Scheduled retry / Queue-based retry
