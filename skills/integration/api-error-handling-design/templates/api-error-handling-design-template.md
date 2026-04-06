# API Error Handling Design — Work Template

Use this template when designing or reviewing the error contract for a Salesforce integration. Fill in each section before writing code.

---

## Scope

**Skill:** `integration/api-error-handling-design`

**Request summary:** (describe what was asked — e.g., "design error responses for a custom Apex REST endpoint," "classify inbound callout errors for retry routing," "add timeout handling to existing Queueable callout jobs")

---

## Endpoint Inventory

List all endpoints in scope. Classify each as **producer** (you control the error format) or **consumer** (you must parse someone else's format).

| Endpoint / System | Direction | Protocol | Error Format |
|---|---|---|---|
| (e.g., `/services/apexrest/v1/orders`) | Producer | REST | RFC 7807 / Salesforce-native / TBD |
| (e.g., `External ERP /api/orders`) | Consumer | REST | (describe external system format) |

---

## Context Gathered

Answer the Before Starting questions from SKILL.md:

- **Who are the callers?** (external systems, internal Apex, both):
- **Is the callout synchronous or async?** (trigger/controller context vs Queueable/Batch):
- **Does the external system follow HTTP semantics?** (yes / no — describe deviations if no):

---

## Producer Endpoint Design (if applicable)

### Error Envelope Format

- [ ] RFC 7807 Problem Detail
- [ ] Salesforce-native format (`[{message, errorCode, fields}]`)
- [ ] Custom format (document below)

**Format definition:** (paste the class or JSON structure)

### Exception-to-Status-Code Mapping

| Exception Type | HTTP Status Code | Rationale |
|---|---|---|
| `DmlException` (validation failure) | 422 | Business rule violation — semantically distinct from bad input |
| `DmlException` (required field missing) | 400 | Client omitted required data |
| `QueryException` | 500 | Unexpected server-side failure |
| `AuraHandledException` / custom validation | 422 | Application-level rejection |
| `Exception` (catch-all) | 500 | Unknown server error — sanitize message |
| (add rows as needed) | | |

### Timeout Configuration

- Endpoint method execution time budget: _____ ms
- `req.setTimeout()` value: _____ ms (must be ≤ 120,000)
- Rationale:

---

## Consumer Callout Error Classification (if applicable)

### Error Classification Table

Fill in for each system being called. Use the retry-safe / permanent / re-auth categories from SKILL.md.

**System:** (name the external system)

| HTTP Status | Error Code (if applicable) | Classification | Action |
|---|---|---|---|
| 200 with error body | (describe format) | Permanent / Transient | Parse body for error type |
| 400 | | Permanent | Dead letter |
| 401 | | Re-authenticate | Refresh token, retry once |
| 403 | | Permanent | Dead letter |
| 404 | | Permanent | Dead letter |
| 409 | | Permanent | Dead letter |
| 422 | | Permanent | Dead letter |
| 429 | | Transient | Retry with backoff |
| 500 | | Transient | Retry once |
| 503 | | Transient | Retry with backoff |
| Timeout (`CalloutException` "timed out") | N/A | Ambiguous | Retry with idempotency key |
| Other `CalloutException` | N/A | Permanent | Dead letter |

### Idempotency Key Status

- Is an idempotency key set before the first callout attempt? (yes / no)
- Field / header used to carry the key:
- Behavior on timeout without idempotency key: (dead letter with ambiguity note / accept risk)

---

## Checklist

Copy from SKILL.md review checklist and tick as completed:

- [ ] Every custom Apex REST endpoint returns a consistent JSON error envelope
- [ ] HTTP status codes are semantically correct
- [ ] No Apex stack traces or internal class names in external error responses
- [ ] All `HttpRequest` instances have an explicit `setTimeout()` call
- [ ] Error classification table exists distinguishing retry-safe from permanent
- [ ] Callout timeout handling checks for non-idempotent operations and gates retry on idempotency key
- [ ] Salesforce REST API error parsing uses `errorCode` field, not `message` string matching
- [ ] Apex tests cover all classified error codes and assert correct routing

---

## Design Decisions and Deviations

Record any decisions that deviate from the standard patterns in SKILL.md and the reason:

- (e.g., "Returning 400 for DML validation errors instead of 422 because the external caller's SDK does not handle 422 correctly — documented as a known inconsistency")
