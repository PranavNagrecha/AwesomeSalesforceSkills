# LLM Anti-Patterns — API Error Handling Design

Common mistakes AI coding assistants make when generating or advising on API error handling design for Salesforce integrations. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Deserializing Salesforce REST API Error Responses as a Map Instead of a List

**What the LLM generates:** Code that calls `(Map<String,Object>) JSON.deserializeUntyped(res.getBody())` to extract the error message from a Salesforce REST API error response.

**Why it happens:** Most REST APIs return error objects as a single JSON object at the root. LLMs trained on generic REST patterns apply `Map<String,Object>` deserialization without recognizing that Salesforce specifically returns an array `[{...}]` as the root element.

**Correct pattern:**

```apex
// WRONG — throws System.TypeException: Invalid conversion from runtime type List<ANY> to Map<String,ANY>
Map<String, Object> error = (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
String msg = (String) error.get('message');

// CORRECT — Salesforce REST error body is always a JSON array at the root
List<Object> errors = (List<Object>) JSON.deserializeUntyped(res.getBody());
if (!errors.isEmpty()) {
    Map<String, Object> firstError = (Map<String, Object>) errors[0];
    String errorCode = (String) firstError.get('errorCode');
    String msg = (String) firstError.get('message');
}
```

**Detection hint:** Search generated code for `(Map<String,Object>) JSON.deserializeUntyped` in callout response handlers that target Salesforce REST endpoints. Any such cast on the root deserialize result is likely incorrect.

---

## Anti-Pattern 2: Throwing Exceptions from `@RestResource` Methods to Signal Error Status Codes

**What the LLM generates:** A `@HttpPost` method that sets `RestContext.response.statusCode = 400` and then throws a custom exception to signal the error condition to the caller.

**Why it happens:** In Java Spring and similar frameworks, throwing an annotated exception (e.g., `@ResponseStatus(HttpStatus.BAD_REQUEST)`) is the canonical way to return an error HTTP status. LLMs apply this pattern to Apex without recognizing that Apex's platform exception handler overrides any pre-set `statusCode` with 500 when an exception escapes the method.

**Correct pattern:**

```apex
// WRONG — platform overrides statusCode=400 with 500 when exception escapes
@HttpPost
global static void create() {
    RestContext.response.statusCode = 400;
    throw new ValidationException('Name is required'); // caller receives 500, not 400
}

// CORRECT — catch all exceptions, set status, serialize body, return normally
@HttpPost
global static void create() {
    RestContext.response.addHeader('Content-Type', 'application/json');
    try {
        // ... logic ...
        RestContext.response.statusCode = 201;
        RestContext.response.responseBody = Blob.valueOf(JSON.serialize(result));
    } catch (DmlException e) {
        RestContext.response.statusCode = 422;
        RestContext.response.responseBody = Blob.valueOf(JSON.serialize(
            new Map<String,Object>{'status'=>422,'detail'=>e.getDmlMessage(0)}
        ));
    } catch (Exception e) {
        RestContext.response.statusCode = 500;
        RestContext.response.responseBody = Blob.valueOf(JSON.serialize(
            new Map<String,Object>{'status'=>500,'detail'=>'Internal server error'}
        ));
    }
    // method returns normally — status code is preserved
}
```

**Detection hint:** Any `@HttpPost`, `@HttpPut`, `@HttpDelete`, or `@HttpPatch` method that contains a `throw` statement outside a catch block, or that sets `RestContext.response.statusCode` before a throw, is likely incorrect.

---

## Anti-Pattern 3: Retrying All Non-2xx HTTP Status Codes Without Classifying 4xx as Permanent

**What the LLM generates:** Callout error handling that calls `enqueueRetry()` whenever `res.getStatusCode() >= 300` or `res.getStatusCode() != 200`, treating 400, 401, 403, 404, and 422 responses as transient errors to be retried.

**Why it happens:** "If it failed, try again" is a common instinct. LLMs generalize retry logic from examples that only handle 5xx errors without applying full HTTP semantics to the 4xx range. This creates infinite retry loops for permanent errors and exhausts the daily async Apex limit.

**Correct pattern:**

```apex
// WRONG — retries 400/403/404 which will never succeed with the same payload
if (res.getStatusCode() != 200) {
    enqueueRetry(payload, retryCount + 1);
}

// CORRECT — classify before routing
Integer status = res.getStatusCode();
if (status == 429 || status == 503 || status == 500) {
    enqueueRetry(payload, retryCount + 1); // transient
} else if (status >= 400) {
    logDeadLetter(payload, res.getBody(), status); // permanent
}
```

**Detection hint:** Look for retry calls inside any condition that matches `status != 200`, `status >= 300`, or `status >= 400` without a carve-out that routes 4xx codes to dead letter.

---

## Anti-Pattern 4: Exposing Stack Traces or Internal Class Names in External 500 Responses

**What the LLM generates:** An `@HttpPost` catch block that returns `e.getMessage()` or `e.getStackTraceString()` as the response body for unexpected exceptions.

**Why it happens:** During development, returning the full exception detail is helpful for debugging. LLMs reproduce this debugging pattern in production code without recognizing the security and information-disclosure implications. Apex stack traces include class names, method names, and sometimes SOQL fragments that reveal internal architecture.

**Correct pattern:**

```apex
// WRONG — exposes internal class names and stack trace to external callers
} catch (Exception e) {
    RestContext.response.statusCode = 500;
    RestContext.response.responseBody = Blob.valueOf(e.getMessage() + '\n' + e.getStackTraceString());
}

// CORRECT — sanitized message externally; full detail logged server-side
} catch (Exception e) {
    RestContext.response.statusCode = 500;
    RestContext.response.responseBody = Blob.valueOf(JSON.serialize(
        new Map<String,Object>{
            'status' => 500,
            'title' => 'Internal Server Error',
            'detail' => 'An unexpected error occurred. Reference ID: ' + UserInfo.getSessionId().left(8)
        }
    ));
    System.debug(LoggingLevel.ERROR, 'Unhandled exception in OpportunityResource: '
        + e.getMessage() + '\n' + e.getStackTraceString());
}
```

**Detection hint:** Any catch block in a `@RestResource` method that includes `e.getStackTraceString()` or `e.getMessage()` directly in `RestContext.response.responseBody` should be flagged.

---

## Anti-Pattern 5: Classifying Callout Timeouts as Non-Retryable Without Idempotency Awareness

**What the LLM generates:** Catch blocks for `System.CalloutException` that immediately write to the dead-letter queue or throw the exception, treating all callout exceptions as permanent failures regardless of the operation type or request state.

**Why it happens:** LLMs often model error handling as binary: success or failure. The nuance that a timeout means "unknown outcome" (the request may have been processed) requires understanding of network semantics and idempotency. Without this context, LLMs default to the simpler dead-letter path.

**Correct pattern:**

```apex
// WRONG — dead-letters a timed-out POST without considering that the server may have processed it
} catch (System.CalloutException ex) {
    logDeadLetter(payload, ex.getMessage(), 0, retryCount);
    return;
}

// CORRECT — distinguish timeout (ambiguous, retry with idempotency key) from
// other callout failures (connection refused, DNS error — cleaner dead-letter)
} catch (System.CalloutException ex) {
    String msg = ex.getMessage();
    if (msg != null && msg.containsIgnoreCase('timed out')) {
        // Outcome unknown — retry only if idempotency key is set
        if (String.isNotBlank(idempotencyKey)) {
            enqueueRetry(payload, retryCount + 1, idempotencyKey);
        } else {
            // Cannot safely retry a non-idempotent operation — dead letter with ambiguity note
            logDeadLetter(payload, 'TIMEOUT_NO_IDEMPOTENCY_KEY: ' + msg, 0, retryCount);
        }
    } else {
        // Connection failure, DNS error, or Named Credential auth issue — dead letter
        logDeadLetter(payload, msg, 0, retryCount);
    }
}
```

**Detection hint:** Any catch block for `CalloutException` that calls `logDeadLetter()` without first checking `ex.getMessage()` for "timed out" should be reviewed. Also check that the retry path for timeouts requires an idempotency key to be set.

---

## Anti-Pattern 6: Using `message` String Matching Instead of `errorCode` for Salesforce Error Classification

**What the LLM generates:** Classification logic that calls `res.getBody().contains('Required fields are missing')` or `firstError.get('message').toString().startsWith('INSUFFICIENT_ACCESS')` to identify Salesforce error types.

**Why it happens:** The `message` field is prominent in API responses and human-readable. LLMs pattern-match on it because the text content looks like a reliable discriminator. The `errorCode` field is less prominent in documentation excerpts that LLMs see, leading to its omission.

**Correct pattern:**

```apex
// WRONG — message text is human-readable, potentially localized, and can change between releases
String body = res.getBody();
if (body.contains('Required fields are missing')) {
    logDeadLetter(payload, body, res.getStatusCode(), retryCount);
}

// CORRECT — errorCode is the stable programmatic discriminator
List<Object> errors = (List<Object>) JSON.deserializeUntyped(res.getBody());
if (!errors.isEmpty()) {
    Map<String,Object> err = (Map<String,Object>) errors[0];
    String errorCode = (String) err.get('errorCode');
    if (errorCode == 'REQUIRED_FIELD_MISSING' || errorCode == 'FIELD_CUSTOM_VALIDATION_EXCEPTION') {
        logDeadLetter(payload, (String) err.get('message'), res.getStatusCode(), retryCount);
    }
}
```

**Detection hint:** Search generated code for `.contains(` or `.startsWith(` applied to a Salesforce REST response body string for error routing decisions. Any such string-matching classification should be replaced with `errorCode` lookup.
