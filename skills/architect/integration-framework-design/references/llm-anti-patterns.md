# LLM Anti-Patterns — Integration Framework Design

Mistakes AI assistants commonly make when designing or reviewing Salesforce integration frameworks.

---

## 1. Placing HTTP Callout Logic Directly in Triggers

**The mistake:** Generating or recommending Apex callout code inside a trigger handler, such as creating `HttpRequest` and calling `http.send()` from within a `before insert` or `after update` trigger context.

**Why it is wrong:** Salesforce does not allow synchronous callouts in trigger context when there is uncommitted DML work pending (which is always the case in a trigger). This causes a runtime exception: `System.CalloutException: You have uncommitted work pending. Please commit or rollback before calling out.` The framework's trigger-initiated integration pattern uses a Platform Event or Queueable to decouple the callout from the trigger transaction.

**Correct pattern:** Trigger enqueues a `System.enqueueJob(new IntegrationQueueable(payload))` or publishes a Platform Event. The Queueable calls the dispatcher in a clean transaction.

---

## 2. Hard-Coding Endpoint URLs and Credentials in Apex Classes

**The mistake:** Embedding endpoint URLs as string literals in concrete service classes or in the dispatcher (e.g., `String endpoint = 'https://api.externalservice.com/v2/';`). Storing API keys or bearer tokens as string constants in Apex code.

**Why it is wrong:** Hard-coded URLs break when the endpoint changes and require a code deployment to update. Credentials in code are a security vulnerability — they appear in version control and are visible to all developers. Both violations contradict the framework's core value proposition (configuration-driven, reconfigurable without code changes).

**Correct pattern:** Endpoints live in `Integration_Service__mdt.Endpoint__c`. Credentials are stored in Named Credentials and referenced via `callout:Named_Credential_Name/path`. The dispatcher constructs the full URL from CMDT + relative path passed in the request DTO.

---

## 3. No Response Logging, Treating Logging as Optional

**The mistake:** Designing the dispatcher without any logging capability and treating `IntegrationLog__c` as a "nice to have" that can be added later. Common AI-generated code examples show only the happy path: build request, send, return response.

**Why it is wrong:** Without a log record, there is no way to diagnose whether a failure was a network issue, an auth failure, a malformed payload, or a downstream service error. Support teams cannot investigate production issues. SLA reporting has no data source. Adding logging later requires touching every service class if logging was not centralized from the start.

**Correct pattern:** `IntegrationLogger` is called by the dispatcher in a `finally` block so that logging occurs regardless of success or failure. Log records include status code, duration, and correlation ID even when the callout throws.

---

## 4. Using Inheritance Instead of Interface Contracts for Service Adapters

**The mistake:** Defining a base abstract class `BaseIntegrationService` with shared callout logic and having concrete classes extend it with `override` methods. Positioning this as equivalent to the interface + dispatcher pattern.

**Why it is wrong:** Abstract class inheritance couples concrete adapters to the base class's implementation details. Every concrete adapter inherits whatever HTTP mechanics exist in the base class, making it harder to replace the dispatcher independently. Interface contracts enforce the contract only — the dispatcher is a separate, injectable collaborator. Inheritance also makes mocking in tests more brittle and breaks if a class needs to extend a different base class for other reasons.

**Correct pattern:** `IIntegrationService` is an interface, not an abstract class. Shared HTTP mechanics live in `HttpCalloutDispatcher`, which concrete classes hold a reference to (composition). Concrete classes remain thin adapters focused on payload construction and response mapping.

---

## 5. Missing Timeout Configuration, Defaulting to Platform Maximum

**The mistake:** Generating callout code without setting `req.setTimeout()`, or setting a single hard-coded timeout in the dispatcher. Not surfacing timeout as a per-service configuration value.

**Why it is wrong:** Salesforce's default callout timeout is 10 seconds, which is also the maximum. An integration framework serving five APIs should not apply the same timeout to all of them — a KYC check may need 8 seconds while a simple health check should time out in 2 seconds. Hard-coding a single timeout in the dispatcher means every API waits the same amount of time on transient hangs, wasting CPU time and risking Apex CPU limit violations.

**Correct pattern:** `Integration_Service__mdt` includes a `Timeout_Ms__c` field. The factory passes this value to the request DTO. The dispatcher applies it via `req.setTimeout(Integer.valueOf(request.timeoutMs))`. Default to a sensible org-wide value (e.g., 5000 ms) when the CMDT field is null.

---

## 6. Ignoring Retry Budget and Treating All Failures as Retry-Eligible

**The mistake:** Implementing retry logic that retries on any non-200 response code, including 400 (Bad Request), 401 (Unauthorized), and 404 (Not Found). Setting retry count to 3 or 5 without budget tracking.

**Why it is wrong:** Retrying 400 and 401 errors wastes callout governor limit (10 per transaction). A 400 error is a payload problem, not a transient failure — no amount of retrying will fix it. A 401 error usually means credentials are wrong or expired — retrying burns callouts while auth remains broken. Apex allows at most 10 callout attempts per transaction, so unbounded retry logic can exhaust this limit.

**Correct pattern:** Retry only on `429` (rate limited) and `5xx` (server error) status codes. Treat `4xx` as permanent failures that propagate immediately with the appropriate `ErrorCode`. In synchronous transactions, limit to 1 immediate retry maximum. Route durable retries (where retry budget > 1 and backoff is needed) to a Queueable-based dead-letter retry processor.

---

## 7. Registering Mock or Test Service Classes in Production Custom Metadata

**The mistake:** Creating `Integration_Service__mdt` records in production that point to test stub classes (e.g., `MockPaymentService`) to "test" the factory resolution in non-sandbox environments.

**Why it is wrong:** Test classes should not exist in production orgs. If `@IsTest` classes are referenced in CMDT, `Type.forName()` returns `null` in production because `@IsTest` classes are not visible outside test execution. This causes silent `SERVICE_DISABLED` errors in production if the wrong record is active.

**Correct pattern:** Use a separate Custom Metadata record with `Active__c = false` for any test-only service entries. In unit tests, use a `@TestVisible` method on the factory to inject a mock directly, bypassing CMDT resolution entirely.
