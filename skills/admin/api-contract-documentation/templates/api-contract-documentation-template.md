# API Contract Documentation — Work Template

Use this template when producing or reviewing API contract documentation for a Salesforce integration.

---

## Scope

**Integration name:** _______________
**API type:** [ ] Standard sObjects REST  [ ] Custom Apex REST (@RestResource)  [ ] Both
**Current API version in use:** _______________

---

## Versioning Policy Documentation

| Item | Value |
|---|---|
| Current API version | |
| Version release date (from /services/data/) | |
| Retirement risk (check api_rest_eol.htm) | |
| Upgrade SLA (team commitment) | |
| Next EOL check date | |

---

## Rate Limit Documentation

**Source:** Retrieved from `GET /limits` on [date]: _______________
**DailyApiRequests.Max:** _______________

Monitoring pattern:
- Log `Sforce-Limit-Info: api-usage=X/Y` from each response
- Alert when X/Y > 80%

---

## Error Code Catalog

| HTTP Status | Error Code | Meaning | Recovery |
|---|---|---|---|
| 200 | (none) | Success | — |
| 400 | MALFORMED_QUERY | Malformed request | Fix request |
| 401 | INVALID_SESSION_ID | Authentication failed | Re-authenticate |
| 403 | REQUEST_LIMIT_EXCEEDED | Daily API limit exhausted | Wait for 24h reset |
| 404 | NOT_FOUND | Record not found | Check ID |
| 429 | (throttle) | Transient rate limit | Exponential backoff |
| 500 | APEX_ERROR | Server error | Retry with backoff |

---

## OpenAPI Spec Location

- Standard sObjects: Generated via `GET /sobjects/{SObjectName}/describe/openapi3_0`
- Custom Apex REST: Hand-authored at: _______________
