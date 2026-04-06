# Examples — API Error Handling Design

## Example 1: Custom Apex REST Endpoint with RFC 7807 Error Envelope

**Context:** A custom `@RestResource` endpoint creates Opportunities via a B2B partner API. Callers are external systems that parse HTTP responses programmatically and need to distinguish validation errors from server faults.

**Problem:** Without a structured error contract, an unhandled `DmlException` returns HTTP 500 with a raw Apex stack trace in the body. The caller cannot distinguish "required field missing" from "governor limit hit" — both look like opaque 500s. Callers retry all failures, creating duplicate Opportunity creation attempts.

**Solution:**

```apex
@RestResource(urlMapping='/v1/opportunities/*')
global with sharing class OpportunityRestResource {

    // RFC 7807-style error envelope
    global class ProblemDetail {
        public String type;
        public String title;
        public Integer status;
        public String detail;
        public String instance;

        public ProblemDetail(String type, String title, Integer status, String detail, String instance) {
            this.type = type;
            this.title = title;
            this.status = status;
            this.detail = detail;
            this.instance = instance;
        }
    }

    @HttpPost
    global static void createOpportunity() {
        RestRequest req = RestContext.request;
        RestResponse res = RestContext.response;
        res.addHeader('Content-Type', 'application/json');

        Map<String, Object> body;
        try {
            body = (Map<String, Object>) JSON.deserializeUntyped(req.requestBody.toString());
        } catch (Exception e) {
            res.statusCode = 400;
            res.responseBody = Blob.valueOf(JSON.serialize(
                new ProblemDetail(
                    'https://developer.salesforce.com/errors/invalid-json',
                    'Invalid JSON',
                    400,
                    'Request body could not be parsed as JSON.',
                    req.requestURI
                )
            ));
            return;
        }

        // Validate required fields
        if (!body.containsKey('Name') || String.isBlank((String) body.get('Name'))) {
            res.statusCode = 400;
            res.responseBody = Blob.valueOf(JSON.serialize(
                new ProblemDetail(
                    'https://developer.salesforce.com/errors/missing-required-field',
                    'Missing Required Field',
                    400,
                    'The "Name" field is required.',
                    req.requestURI
                )
            ));
            return;
        }

        try {
            Opportunity opp = new Opportunity(
                Name = (String) body.get('Name'),
                CloseDate = Date.parse((String) body.get('CloseDate')),
                StageName = (String) body.get('StageName')
            );
            insert opp;

            res.statusCode = 201;
            res.responseBody = Blob.valueOf(JSON.serialize(new Map<String, String>{
                'id' => opp.Id,
                'name' => opp.Name
            }));
        } catch (DmlException e) {
            // DML validation failure — 422 Unprocessable Entity
            res.statusCode = 422;
            res.responseBody = Blob.valueOf(JSON.serialize(
                new ProblemDetail(
                    'https://developer.salesforce.com/errors/dml-validation-failed',
                    'Validation Failed',
                    422,
                    e.getDmlMessage(0),
                    req.requestURI
                )
            ));
        } catch (Exception e) {
            // Unexpected server error — 500, sanitized message
            res.statusCode = 500;
            res.responseBody = Blob.valueOf(JSON.serialize(
                new ProblemDetail(
                    'https://developer.salesforce.com/errors/internal-server-error',
                    'Internal Server Error',
                    500,
                    'An unexpected error occurred. Contact support with the request ID.',
                    req.requestURI
                )
            ));
            // Log full exception server-side — never expose stack trace externally
            System.debug(LoggingLevel.ERROR, 'Unhandled exception: ' + e.getMessage() + '\n' + e.getStackTraceString());
        }
    }
}
```

**Why it works:** Every code path returns the same JSON structure. The HTTP status code is semantically correct — callers can branch on `status` without parsing the message body. Catch blocks are ordered from most specific (`DmlException`) to least specific (`Exception`), preventing DML failures from falling into the 500 bucket. The server-side `System.debug` preserves the full stack trace for debugging without exposing it externally.

---

## Example 2: Client-Side Error Classification When Calling the Salesforce REST API

**Context:** A cross-org integration uses Apex callouts to create records in a target Salesforce org via the sObject REST API. The callout is in a Queueable job that decides whether to retry or dead-letter based on the response.

**Problem:** The consumer code checks `res.getStatusCode() != 200` and enqueues a retry for every non-success response, including 400 errors where the payload schema is wrong. This creates infinite retry loops on permanent failures and burns the daily async Apex limit.

**Solution:**

```apex
public class SalesforceApiErrorClassifier {

    public enum ErrorDisposition { RETRY, DEAD_LETTER, REAUTHENTICATE }

    // Salesforce REST API error codes that are permanently non-retryable
    private static final Set<String> PERMANENT_ERROR_CODES = new Set<String>{
        'REQUIRED_FIELD_MISSING',
        'FIELD_CUSTOM_VALIDATION_EXCEPTION',
        'DUPLICATE_VALUE',
        'ENTITY_IS_DELETED',
        'INVALID_FIELD',
        'INVALID_TYPE',
        'INSUFFICIENT_ACCESS_ON_CROSS_REFERENCE_ENTITY',
        'FIELD_INTEGRITY_EXCEPTION'
    };

    public static ErrorDisposition classify(HttpResponse res) {
        Integer status = res.getStatusCode();

        // 2xx — should not be classified as error, but guard defensively
        if (status >= 200 && status < 300) {
            return null;
        }

        // 401 — needs re-authentication, then retry
        if (status == 401) {
            return ErrorDisposition.REAUTHENTICATE;
        }

        // Permanent client errors — dead letter immediately
        if (status == 400 || status == 403 || status == 404 || status == 409 || status == 422) {
            return ErrorDisposition.DEAD_LETTER;
        }

        // 429 — rate limited; retry after backoff
        if (status == 429) {
            return ErrorDisposition.RETRY;
        }

        // 5xx — check error code for permanent vs transient
        if (status >= 500) {
            String errorCode = extractErrorCode(res.getBody());
            if (PERMANENT_ERROR_CODES.contains(errorCode)) {
                return ErrorDisposition.DEAD_LETTER;
            }
            return ErrorDisposition.RETRY;
        }

        // Unknown status — conservative dead letter
        return ErrorDisposition.DEAD_LETTER;
    }

    private static String extractErrorCode(String responseBody) {
        if (String.isBlank(responseBody)) return '';
        try {
            // Salesforce REST errors are a JSON array, not an object
            List<Object> errors = (List<Object>) JSON.deserializeUntyped(responseBody);
            if (errors.isEmpty()) return '';
            Map<String, Object> firstError = (Map<String, Object>) errors[0];
            return (String) firstError.get('errorCode');
        } catch (Exception e) {
            // Non-JSON body (e.g., HTML error page) — cannot classify by errorCode
            return '';
        }
    }
}
```

```apex
// Usage in a Queueable execute() method:
HttpResponse res;
try {
    res = http.send(req);
} catch (System.CalloutException ex) {
    String msg = ex.getMessage();
    if (msg != null && msg.containsIgnoreCase('timed out')) {
        // Timeout: outcome unknown — retry with idempotency key only
        handleTimeout(recordId, payload, retryCount);
    } else {
        // Connection failure or Named Credential auth issue — dead letter
        logDeadLetter(recordId, msg, 0, retryCount);
    }
    return;
}

SalesforceApiErrorClassifier.ErrorDisposition disposition =
    SalesforceApiErrorClassifier.classify(res);

if (disposition == SalesforceApiErrorClassifier.ErrorDisposition.RETRY) {
    enqueueRetry(recordId, payload, retryCount);
} else if (disposition == SalesforceApiErrorClassifier.ErrorDisposition.REAUTHENTICATE) {
    refreshTokenAndRetry(recordId, payload, retryCount);
} else {
    logDeadLetter(recordId, res.getBody(), res.getStatusCode(), retryCount);
}
```

**Why it works:** The classifier separates the classification concern from the retry execution concern. `errorCode` drives classification for 5xx responses because a 500 can carry a `DUPLICATE_VALUE` error code (indicating a permanent conflict) despite the 5xx status. The `List<Object>` deserialization correctly handles Salesforce's array error format rather than mistyping it as a Map. Timeout is caught at the exception level, separate from HTTP status, because Named Credential auth failures also surface as exceptions rather than 401 responses.

---

## Anti-Pattern: Parsing Salesforce Error Responses as a Single JSON Object

**What practitioners do:** After receiving a non-200 response from the Salesforce REST API, developers call `(Map<String,Object>) JSON.deserializeUntyped(res.getBody())` to extract the error message.

**What goes wrong:** The Salesforce REST API returns errors as a JSON array `[{"message":"...","errorCode":"...","fields":[...]}]`. Casting the root element to `Map<String,Object>` throws `System.TypeException: Invalid conversion from runtime type List<ANY> to Map<String,ANY>`. This exception is uncaught in most callout handlers, causing the error handler itself to fail and masking the original HTTP error. In batch contexts, this causes the entire batch chunk to fail with a `TypeException` rather than cleanly routing the record to a dead-letter queue.

**Correct approach:** Deserialize the response body as `List<Object>` first, then cast each element to `Map<String,Object>`. Guard with an empty-list check before accessing index 0. See Example 2 above for the pattern.
