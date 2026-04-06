---
name: api-error-handling-design
description: "Designing HTTP error classification, RFC 7807-style error payload structure, and client-side error parsing for Salesforce REST/SOAP integrations and custom Apex REST endpoints. Use when deciding which HTTP status codes to return from custom Apex REST services, how to structure error response bodies, how to classify inbound API errors as retry-safe vs non-retry-safe, or how to parse Salesforce error responses on the consumer side. NOT for retry execution mechanics or circuit breaker implementation (use retry-and-backoff-patterns). NOT for Apex exception class design (use apex-error-handling-framework). NOT for OAuth error flows (use oauth-flows-and-connected-apps)."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "what HTTP status codes should my Apex REST endpoint return for validation errors"
  - "how do I structure error response payloads from a custom Apex REST service"
  - "how do I parse Salesforce REST API error responses in a consumer application"
  - "which HTTP errors from Salesforce should I retry vs treat as permanent failures"
  - "how do I handle timeout errors from callouts to external services"
  - "my integration doesn't know if a 400 error is retryable or a permanent bug"
tags:
  - http-status-codes
  - error-payload-design
  - rfc-7807
  - apex-rest
  - error-classification
  - callout-error-handling
  - integration-resilience
inputs:
  - "Custom Apex REST endpoint class (or requirement to build one)"
  - "List of external system error response formats that the Salesforce org consumes"
  - "Whether callers are external systems or internal Apex callouts"
  - "Known timeout requirements for synchronous and async callout contexts"
outputs:
  - "HTTP status code strategy for custom Apex REST endpoints"
  - "RFC 7807-style error payload structure for Apex REST responses"
  - "Error classification table distinguishing retry-safe vs non-retry-safe codes"
  - "Client-side error parsing pattern for consuming Salesforce REST API responses"
  - "Callout timeout handling design for Apex Http.send() calls"
dependencies:
  - retry-and-backoff-patterns
  - apex-rest-services
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# API Error Handling Design

This skill activates when a practitioner needs to design the error contract for an integration — deciding which HTTP status codes to return, how to structure error response bodies, how to classify inbound errors as safe or unsafe to retry, how to parse Salesforce's own error response format, and how to handle callout timeouts. It covers both the producer side (custom Apex REST endpoints) and the consumer side (Apex callouts to external systems or to Salesforce). It does not cover retry execution mechanics, which belong in `retry-and-backoff-patterns`.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Who are the callers of the endpoint?** External systems expect a stable, machine-parseable error contract. Internal Apex callers can recover from Apex exceptions, but the callout response still drives retry vs dead-letter decisions. Knowing the audience determines how structured the error payload needs to be.
- **Is the callout synchronous or async?** Synchronous Apex callouts (in triggers, controllers, or same-transaction logic) have a 120-second timeout ceiling enforced by the platform. Async callouts (Queueable, Batch) still have the same 120-second per-callout limit. Designing timeout handling before implementation avoids a class of silent integration failures.
- **Does the external system follow HTTP semantics?** Some APIs return 200 with an error body, or 500 for every error type. The error classification strategy must account for non-standard HTTP behavior, not just the RFC-compliant ideal.

---

## Core Concepts

### HTTP Status Code Semantics for Salesforce Integrations

Salesforce's REST API uses HTTP status codes per RFC 7231 conventions. Key mappings for Apex REST endpoint design:

- **200 OK / 201 Created / 204 No Content** — success states; use 201 for resource creation, 204 when no body is returned.
- **400 Bad Request** — malformed input: missing required fields, type mismatch, invalid enumeration value. The error is in the client's payload. Retrying the same payload will always fail.
- **401 Unauthorized** — authentication failure (expired OAuth token, invalid session). The client must re-authenticate before retrying.
- **403 Forbidden** — the authenticated user lacks the permission to perform the operation. Retrying with the same credentials will always fail.
- **404 Not Found** — the referenced record or resource does not exist. Treat as permanent unless the resource creation is expected to race.
- **409 Conflict** — state conflict, such as an attempt to create a duplicate record that violates an external-id uniqueness constraint. Requires application-level resolution, not a retry.
- **422 Unprocessable Entity** — syntactically valid payload that fails business-rule validation (e.g., a closed Opportunity cannot be re-opened via this endpoint). Distinct from 400 in that the request was well-formed.
- **429 Too Many Requests** — rate limit exceeded. Retry-safe after the `Retry-After` interval.
- **500 Internal Server Error** — unhandled server-side exception. May be transient; one retry is reasonable.
- **503 Service Unavailable** — server temporarily unable to handle the request (overload or maintenance). Retry-safe with backoff.

When designing a custom Apex REST endpoint, return the narrowest applicable code — never collapse all failures into 500 or 400.

### RFC 7807 Problem Detail for HTTP APIs

RFC 7807 defines a standard JSON error response format that allows machine consumers to parse errors without screen-scraping the message string. The canonical structure:

```json
{
  "type": "https://example.com/errors/validation-failed",
  "title": "Validation Failed",
  "status": 400,
  "detail": "The 'CloseDate' field is required for Opportunity creation.",
  "instance": "/services/apexrest/v1/opportunities/a0B5g00000XYZ"
}
```

Salesforce's own REST API returns errors as an array of objects with `message`, `errorCode`, and sometimes `fields`:

```json
[
  {
    "message": "Required fields are missing: [CloseDate]",
    "errorCode": "REQUIRED_FIELD_MISSING",
    "fields": ["CloseDate"]
  }
]
```

Custom Apex REST endpoints are not required to match Salesforce's format. Using RFC 7807 is preferable when callers are third-party systems or standards-conscious developers. Matching Salesforce's native format is preferable when callers already parse Salesforce REST responses and expect consistency.

### Retry-Safe vs Non-Retry-Safe Error Classification

The fundamental question for every non-2xx response is: will sending the same request again ever succeed? The classification drives whether to enqueue a retry or write to a dead-letter queue immediately.

**Retry-safe (transient errors):**
- 429 Too Many Requests (after Retry-After interval)
- 500 Internal Server Error (once, with caution)
- 503 Service Unavailable
- Network timeout / `System.CalloutException` with "Read timed out" message

**Non-retry-safe (permanent errors):**
- 400 Bad Request — the payload is invalid; same payload will always fail
- 401 Unauthorized — re-authenticate first; re-auth is a separate flow, not a simple retry
- 403 Forbidden — permissions issue; no automatic fix
- 404 Not Found — resource does not exist
- 409 Conflict — duplicate or state conflict; needs business logic to resolve
- 422 Unprocessable Entity — business rule violation; same payload will always fail
- 501 Not Implemented — the endpoint does not support this operation

**Ambiguous cases:**
- 401 can be made retry-safe if the retry flow re-authenticates first (fetch new access token, then retry the callout)
- 500 is sometimes a permanent bug, not a transient server error — apply at most one retry with fast-fail to dead letter if the second attempt also fails

### Callout Timeout Handling

The Apex `HttpRequest.setTimeout()` method sets the timeout in milliseconds, up to a maximum of 120,000 ms (120 seconds). The default is 10,000 ms (10 seconds) for Named Credentials and varies by context. A callout that exceeds the timeout throws `System.CalloutException` with the message "Read timed out."

Timeout errors are ambiguous: the request may have been received and processed by the remote system before the connection timed out. This makes them functionally equivalent to lost-response scenarios, and idempotency keys are mandatory before retrying any non-idempotent operation on timeout.

Set timeouts explicitly on every `HttpRequest` — relying on platform defaults leads to inconsistent behavior across Named Credential types and release changes.

---

## Common Patterns

### Pattern 1: Structured Error Response from a Custom Apex REST Endpoint

**When to use:** You are building a custom Apex REST endpoint (`@RestResource`) that will be called by an external system or internal tooling, and callers need machine-parseable errors.

**How it works:**

1. Define a lightweight inner class (or a standalone class) for the error envelope that matches RFC 7807 or Salesforce's native format.
2. In each `@HttpPost`, `@HttpPut`, or `@HttpPatch` method, wrap the logic in a try-catch. Catch `DmlException`, `QueryException`, and general `Exception` separately.
3. Map caught exceptions to the correct HTTP status code using `RestContext.response.statusCode`.
4. Serialize the error envelope with `JSON.serialize()` and set it as the response body.
5. Always return a consistent envelope — never mix plain-string errors with JSON for the same endpoint.

**Why not letting Apex throw unhandled:** An unhandled exception from an Apex REST method returns HTTP 500 with an HTML or plaintext error body that is not machine-parseable. Callers cannot distinguish a null pointer from a governor limit hit from a DML error.

### Pattern 2: Client-Side Error Parsing for Salesforce REST API Responses

**When to use:** An Apex class makes callouts to the Salesforce REST API (e.g., composite API, sObject API) and must classify responses for retry or dead-letter decisions.

**How it works:**

1. After `HttpResponse res = http.send(req)`, check `res.getStatusCode()`.
2. For non-2xx responses, deserialize `res.getBody()` as `List<Map<String,Object>>` (Salesforce's error array format).
3. Extract `errorCode` from the first error object to apply classification logic — `REQUIRED_FIELD_MISSING` and `FIELD_CUSTOM_VALIDATION_EXCEPTION` are permanent; `REQUEST_LIMIT_EXCEEDED` is transient.
4. Pass the `errorCode`, `statusCode`, and original payload to the retry/dead-letter router.

**Why not parsing message string:** The `message` field is human-readable and subject to localization or phrasing changes. The `errorCode` is a stable programmatic identifier defined in the REST API Developer Guide.

### Pattern 3: Timeout Handling with Idempotency Awareness

**When to use:** An Apex callout to an external system (or to Salesforce via cross-org integration) catches a `System.CalloutException` with a "timed out" message.

**How it works:**

1. Catch `System.CalloutException ex` after `http.send(req)`.
2. Check `ex.getMessage().containsIgnoreCase('timed out')` to distinguish a timeout from other callout failures (e.g., "Exceeded max size limit").
3. If the operation was a POST/PUT/PATCH (non-idempotent), only enqueue a retry if an idempotency key was set on the request before the first attempt.
4. If the operation was a GET or DELETE (idempotent by nature for GETs), retry without idempotency guards.
5. Log the ambiguity — note in the retry log that the outcome of the original request is unknown.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Custom Apex REST endpoint returns errors | RFC 7807 or Salesforce-native JSON envelope with correct HTTP status code | Machine-parseable; callers can branch without string matching |
| Callers already consume Salesforce REST API | Match Salesforce native error format (array with `message`, `errorCode`, `fields`) | Consistency reduces parser complexity on caller side |
| Inbound HTTP 400 from external system | Write to dead letter immediately — no retry | Same payload will always fail; investigate the request format |
| Inbound HTTP 401 from external system | Re-authenticate (refresh OAuth token), then retry once | Auth failure is fixable without payload changes, but retry must be conditional on re-auth success |
| Inbound HTTP 429 from external system | Retry after `Retry-After` header interval or with exponential backoff | Transient rate limit; see retry-and-backoff-patterns for execution |
| Inbound HTTP 500 from external system | Retry once with backoff; dead-letter on second failure | May be transient, but persistent 500s indicate a bug — avoid masking it |
| Callout times out | Retry with idempotency key for non-idempotent operations; retry freely for GET | Outcome of timed-out request is unknown; idempotency prevents duplicates |
| Apex REST endpoint receives a DmlException | Map to 422 Unprocessable Entity, include `fields` in error body | Semantically correct; helps caller identify which fields caused the failure |
| Apex REST endpoint catches unexpected Exception | Return 500 with a sanitized message — never expose stack traces | Stack traces leak implementation details; log the full trace server-side |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner designing the error contract for an integration:

1. **Identify all endpoints and their directions.** List every custom Apex REST endpoint being produced and every external API being consumed. Classify each as producer (you control the error format) or consumer (you must parse someone else's format).
2. **Define the error envelope format for all producer endpoints.** Choose RFC 7807 or Salesforce-native format. Create a shared inner class or utility class that all `@RestResource` methods use — do not define error response structures ad hoc per method.
3. **Map application exceptions to HTTP status codes.** For each exception type that can be thrown (`DmlException`, `QueryException`, `AuraHandledException`, business-logic custom exceptions), define the target HTTP status code. Document this mapping in the endpoint's class-level Javadoc.
4. **Build the error classification table for consumer callouts.** For each external system being called, document which HTTP status codes are retry-safe, which require re-authentication, and which are permanent failures. If the system returns non-standard errors (200 with error body, 500 for all failures), add normalization logic before the classification switch.
5. **Add explicit timeout configuration to all `HttpRequest` instances.** Set `req.setTimeout()` to a value appropriate for the operation (typically 10,000–30,000 ms for synchronous contexts; up to 120,000 ms for async batch callouts). Document the chosen value and the reasoning.
6. **Implement client-side error parsing using `errorCode` for Salesforce responses, not `message`.** Build a parser that extracts `errorCode` from the Salesforce REST error array and maps it to retry-safe vs permanent via a lookup structure.
7. **Test all error paths explicitly.** Write Apex tests using `HttpCalloutMock` that return each classified status code. Assert that permanent errors route to dead letter and transient errors route to retry. Test that timeout exceptions with idempotency keys do not create duplicate records.

---

## Review Checklist

Run through these before marking integration error-handling work complete:

- [ ] Every custom Apex REST endpoint returns a consistent JSON error envelope — no mixed plain-string and JSON responses
- [ ] HTTP status codes are semantically correct — 400 for bad input, 422 for business validation, 500 for unhandled server errors
- [ ] No Apex stack traces or internal class names appear in external-facing error responses
- [ ] All `HttpRequest` instances have an explicit `setTimeout()` call — no implicit platform defaults
- [ ] Error classification table exists distinguishing retry-safe (429, 500, 503, timeout) from permanent (400, 401, 403, 404, 409, 422)
- [ ] Callout timeout handling checks for non-idempotent operations and gates retry on idempotency key presence
- [ ] Salesforce REST API error parsing uses `errorCode` field, not `message` string matching
- [ ] Apex tests cover all classified error codes and assert correct routing (retry vs dead letter)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Apex REST methods that throw uncaught exceptions return 500 with HTML or plaintext body** — When an `@HttpPost` method throws any unhandled exception, the platform returns an HTTP 500 with a body that is not valid JSON. External callers parsing `res.getBody()` as JSON will throw a parse error on top of the original integration failure, making debugging harder. Always wrap `@HttpPost`/`@HttpPut` bodies in try-catch and return a structured response.

2. **`RestContext.response.statusCode` defaults to 200 even if you set it to something else and then throw** — If you set `RestContext.response.statusCode = 400` and then throw an exception before returning, the platform overrides your status code with 500. You must catch all exceptions and return normally (not throw) from the method if you want to control the HTTP status code. Rethrowing after setting the status code does not work.

3. **Salesforce REST API error responses are an array, not an object** — The Salesforce REST API returns errors as a JSON array `[{"message":"...","errorCode":"..."}]`, not a single object `{"message":"..."}`. Consumer code that calls `(Map<String,Object>) JSON.deserializeUntyped(body)` will throw a `System.TypeException` because the root is a List, not a Map. Always deserialize as `List<Object>` first, then cast each element.

4. **`System.CalloutException` message varies by failure mode** — A timeout produces "Read timed out." A DNS failure produces "Unauthorized endpoint." A connection refused produces "Connection refused." Code that catches `CalloutException` and treats all instances as timeouts will misclassify connection failures (which may have a different retry strategy). Always check `ex.getMessage()` to distinguish timeout from other callout failures.

5. **Named Credential callouts mask authentication errors as generic callout exceptions** — When a Named Credential uses per-user authentication and the user's stored credential has expired, the callout throws `System.CalloutException: Unauthorized endpoint or unable to complete the request` rather than returning HTTP 401. Consumer code that only checks `res.getStatusCode() == 401` will miss this case entirely. Named Credential auth failures must be handled at the exception level, not the HTTP status level.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `ApiErrorEnvelope.cls` | Shared Apex class encapsulating RFC 7807-style error response structure for all `@RestResource` endpoints |
| `CalloutErrorClassifier.cls` | Utility class mapping HTTP status codes and `errorCode` values to retry vs dead-letter routing decisions |
| `api-error-handling-design-template.md` | Filled work template recording the error contract decisions for a specific integration |

---

## Related Skills

- `retry-and-backoff-patterns` — Queueable retry chain, exponential backoff, and circuit breaker execution; this skill defines what triggers a retry, retry-and-backoff-patterns defines how to execute it
- `apex-error-handling-framework` — org-wide Apex exception class hierarchy and logging; complements error payload design with server-side observability
- `callout-limits-and-async-patterns` — governor limits on callouts (100 per transaction, 120-second timeout ceiling) that constrain timeout configuration choices
- `named-credentials-setup` — Named Credential configuration affects how authentication errors surface at the callout level
- `composite-api-patterns` — Salesforce Composite API returns per-subrequest error arrays alongside 200 OK; error parsing patterns here apply directly
