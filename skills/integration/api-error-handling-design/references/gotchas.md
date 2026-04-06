# Gotchas — API Error Handling Design

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Setting `RestContext.response.statusCode` Before Throwing Does Not Preserve the Status Code

**What happens:** A developer sets `RestContext.response.statusCode = 400` inside a `@HttpPost` method to signal a validation error, then throws an exception expecting the 400 status to be returned to the caller. The platform ignores the pre-set status code when an exception escapes the method and returns HTTP 500 with a non-JSON body.

**When it occurs:** Any time an exception is thrown (or re-thrown) from an `@RestResource` method after the developer has already set `RestContext.response.statusCode`. The platform's exception handler overrides the status code with 500. This affects custom error classes thrown by helper methods called from the `@RestResource` method.

**How to avoid:** Never allow exceptions to escape `@RestResource` methods. Wrap the entire method body in a try-catch. In the catch block, set `RestContext.response.statusCode` and serialize the error body, then return normally. The status code assignment in the catch block (before `return`) is respected because the method exits normally, not via an exception.

---

## Gotcha 2: Composite API Returns HTTP 200 with Per-Subrequest Errors

**What happens:** The Salesforce Composite API (`/services/data/vXX.0/composite`) returns HTTP 200 even when individual subrequests within the composite batch fail. Each subrequest result has its own `httpStatusCode` in the response body. Consumer code that only checks the top-level `res.getStatusCode() == 200` and assumes success will silently swallow individual record failures.

**When it occurs:** Any callout to the Composite REST API or Composite Batch endpoint where one or more subrequests fail (e.g., validation error on one of 10 records in a batch). The outer response is always 200 as long as the composite request itself was valid. Only the per-element `httpStatusCode` fields within `compositeResponse` or `results` reveal the individual failures.

**How to avoid:** After receiving a 200 from the Composite API, deserialize the response body and iterate over every subrequest result. Check each `httpStatusCode` individually. Build a per-record error classification loop rather than a single top-level status check. Log failed subrequests to the dead-letter queue with their individual error detail.

---

## Gotcha 3: Named Credential Auth Failures Surface as `CalloutException`, Not HTTP 401

**What happens:** When a Named Credential uses per-user authentication (OAuth user-agent flow) and the stored access token has expired or been revoked, the callout throws `System.CalloutException` with the message "Unauthorized endpoint or unable to complete the request" instead of returning an HTTP response with status 401. Consumer code that only checks `res.getStatusCode() == 401` to detect auth failures never executes the re-authentication branch.

**When it occurs:** Per-user Named Credentials where users have revoked consent, token refresh has failed, or the connected app credentials were rotated. Org-wide Named Credentials using client credentials flow typically return the actual HTTP 401 from the target system, so this behavior is specific to per-user auth flows where Salesforce itself can't retrieve a token.

**How to avoid:** Auth failure handling must occur at two levels: catch `CalloutException` and check `ex.getMessage().containsIgnoreCase('Unauthorized endpoint')` as the Named Credential auth failure path, and separately check `res.getStatusCode() == 401` for target-system-returned auth failures. Document both paths explicitly in the error classification table for each endpoint.

---

## Gotcha 4: Salesforce REST API FIELD_INTEGRITY_EXCEPTION Returns HTTP 400, Not 422

**What happens:** Salesforce's REST API returns HTTP 400 (Bad Request) for field-level DML failures such as `FIELD_INTEGRITY_EXCEPTION` (invalid lookup value) or `INVALID_CROSS_REFERENCE_KEY`, even though these are semantically business validation failures that RFC 7231 would map to 422 Unprocessable Entity. Consumer code that routes all 400 responses to dead letter without inspecting `errorCode` will correctly dead-letter these, but code that logs "bad request" without context creates confusing support tickets that appear to blame the payload format rather than the data content.

**When it occurs:** Any DML-backed callout to the Salesforce sObject API that violates referential integrity — setting a lookup to a deleted record, providing an invalid picklist value for a restricted picklist, or violating a master-detail relationship constraint.

**How to avoid:** When dead-lettering a 400 response from the Salesforce REST API, always extract and log the `errorCode` alongside the HTTP status. For `FIELD_INTEGRITY_EXCEPTION` and `INVALID_CROSS_REFERENCE_KEY`, the retry strategy is always dead letter, but the logged classification should reflect "data integrity failure" rather than "malformed request" so support teams investigate the data rather than the payload schema.

---

## Gotcha 5: `req.setTimeout()` Is Per-Callout, Not Per-Transaction

**What happens:** Developers assume that calling `req.setTimeout(30000)` sets a 30-second limit for all callouts in the transaction. In fact, `setTimeout()` sets the timeout for that specific `HttpRequest` instance only. Other `HttpRequest` instances in the same transaction retain their default or previously set timeouts. A transaction making two callouts — one with `setTimeout(30000)` and one that never calls `setTimeout()` — uses 30,000 ms for the first and the platform default for the second.

**When it occurs:** Any integration that makes multiple callouts in a single transaction (e.g., Composite API pattern with a token fetch followed by a data callout, or multi-step Queueable that makes two sequential callouts). If the second callout's timeout is not explicitly set, its behavior depends on the Named Credential type and platform release defaults.

**How to avoid:** Set `setTimeout()` explicitly on every `HttpRequest` instance. Create a utility method or factory that constructs `HttpRequest` objects with the timeout always set, preventing any callout from inadvertently using a platform default.
