# Integration Framework Design — Work Template

Use this template when designing or reviewing a centralized Apex integration framework for multiple external APIs.

---

## Scope

**Skill:** `architect/integration-framework-design`
**Request summary:** (fill in what the user asked for)

---

## 1. Integration Inventory

**External APIs in scope:**

| API Name | Protocol | Auth Mechanism | Sync/Async | Retry Eligible |
|---|---|---|---|---|
| (e.g., KYC Service) | REST | OAuth 2.0 | Sync | Yes (5xx only) |

**Shared infrastructure requirements:**
- [ ] Centralized auth injection (Named Credentials)
- [ ] Centralized timeout configuration
- [ ] Retry on transient failure (5xx, 429)
- [ ] Response logging to `IntegrationLog__c`
- [ ] Correlation ID per transaction
- [ ] Dead-letter queue for durable async retry

---

## 2. Service Interface Contract

```apex
// IIntegrationService.cls
public interface IIntegrationService {
    HttpResponse callout(IntegrationRequest request);
    IntegrationResult parseResponse(HttpResponse response);
}
```

**Request DTO:**
```apex
// IntegrationRequest.cls
public class IntegrationRequest {
    public String endpoint;
    public String method;       // GET, POST, PATCH, DELETE
    public String body;
    public Map<String, String> headers;
    public Integer timeoutMs;
    public String correlationId;
}
```

**Response wrapper:**
```apex
// IntegrationResult.cls
public class IntegrationResult {
    public Boolean success;
    public Integer statusCode;
    public String rawBody;
    public Object parsedPayload;
    public String correlationId;
    public String errorCode;
    public String errorMessage;
}
```

---

## 3. Custom Metadata Type — Service Registry

**Object:** `Integration_Service__mdt`

| Field API Name | Type | Purpose |
|---|---|---|
| `DeveloperName` | Text (unique) | Key used by factory to resolve service |
| `Service_Class__c` | Text(255) | Fully-qualified Apex class name |
| `Endpoint__c` | URL | Base endpoint URL or Named Credential callout string |
| `Active__c` | Checkbox | Emergency toggle without deployment |
| `Timeout_Ms__c` | Number | Per-service callout timeout in milliseconds |
| `Retry_On_Failure__c` | Checkbox | Whether dispatcher applies retry for this service |

**Sample record (deployment target: force-app/main/default/customMetadata/):**
```
Integration_Service__mdt.Payment_US.md-meta.xml
```

---

## 4. Factory Class

```apex
// IntegrationServiceFactory.cls
public class IntegrationServiceFactory {

    // @TestVisible to allow mock injection in unit tests
    @TestVisible
    private static IIntegrationService mockService;

    public static IIntegrationService resolve(String serviceApiName) {
        if (Test.isRunningTest() && mockService != null) {
            return mockService;
        }
        Integration_Service__mdt record = [
            SELECT Service_Class__c, Endpoint__c, Active__c, Timeout_Ms__c
            FROM Integration_Service__mdt
            WHERE DeveloperName = :serviceApiName
            LIMIT 1
        ];
        if (record == null || !record.Active__c) {
            throw new IntegrationException(
                IntegrationException.ErrorCode.SERVICE_DISABLED,
                'Service ' + serviceApiName + ' is not active or not found.'
            );
        }
        Type serviceType = Type.forName(record.Service_Class__c);
        if (serviceType == null) {
            throw new IntegrationException(
                IntegrationException.ErrorCode.SERVICE_DISABLED,
                'Class not found: ' + record.Service_Class__c
            );
        }
        return (IIntegrationService) serviceType.newInstance();
    }
}
```

---

## 5. Centralized Callout Dispatcher

```apex
// HttpCalloutDispatcher.cls
public class HttpCalloutDispatcher {

    private static final Integer DEFAULT_TIMEOUT_MS = 5000;

    public HttpResponse dispatch(IntegrationRequest req) {
        HttpRequest httpReq = new HttpRequest();
        httpReq.setEndpoint(req.endpoint);
        httpReq.setMethod(req.method);
        httpReq.setTimeout(req.timeoutMs != null ? req.timeoutMs : DEFAULT_TIMEOUT_MS);
        if (req.body != null) {
            httpReq.setBody(req.body);
        }
        if (req.headers != null) {
            for (String key : req.headers.keySet()) {
                httpReq.setHeader(key, req.headers.get(key));
            }
        }

        Long start = System.currentTimeMillis();
        HttpResponse res;
        try {
            Http http = new Http();
            res = http.send(httpReq);
        } catch (System.CalloutException e) {
            IntegrationLogger.logError(req, e, start);
            throw new IntegrationException(IntegrationException.ErrorCode.CALLOUT_FAILURE, e.getMessage());
        } finally {
            if (res != null) {
                IntegrationLogger.logResponse(req, res, start);
            }
        }

        // Retry on 429 / 5xx (single immediate retry in sync context)
        if (res.getStatusCode() == 429 || res.getStatusCode() >= 500) {
            Long retryStart = System.currentTimeMillis();
            try {
                Http http = new Http();
                res = http.send(httpReq);
                IntegrationLogger.logResponse(req, res, retryStart);
            } catch (System.CalloutException e) {
                IntegrationLogger.logError(req, e, retryStart);
                throw new IntegrationException(IntegrationException.ErrorCode.CALLOUT_FAILURE, e.getMessage());
            }
        }
        return res;
    }
}
```

---

## 6. Integration Logger

```apex
// IntegrationLogger.cls — writes IntegrationLog__c
public class IntegrationLogger {

    private static final Integer MAX_BODY_LENGTH = 131072; // 128 KB

    public static void logResponse(IntegrationRequest req, HttpResponse res, Long startMs) {
        IntegrationLog__c log = new IntegrationLog__c(
            Endpoint__c        = req.endpoint,
            HTTP_Method__c     = req.method,
            Status_Code__c     = res.getStatusCode(),
            Request_Body__c    = truncate(req.body),
            Response_Body__c   = truncate(res.getBody()),
            Duration_Ms__c     = System.currentTimeMillis() - startMs,
            Correlation_ID__c  = req.correlationId,
            Success__c         = res.getStatusCode() >= 200 && res.getStatusCode() < 300
        );
        insert log;
    }

    public static void logError(IntegrationRequest req, Exception e, Long startMs) {
        IntegrationLog__c log = new IntegrationLog__c(
            Endpoint__c       = req.endpoint,
            HTTP_Method__c    = req.method,
            Request_Body__c   = truncate(req.body),
            Duration_Ms__c    = System.currentTimeMillis() - startMs,
            Correlation_ID__c = req.correlationId,
            Success__c        = false,
            Error_Message__c  = e.getMessage()
        );
        insert log;
    }

    private static String truncate(String s) {
        if (s == null) return null;
        return s.length() > MAX_BODY_LENGTH ? s.substring(0, MAX_BODY_LENGTH) : s;
    }
}
```

**IntegrationLog__c — Custom Object Fields:**

| API Name | Type | Notes |
|---|---|---|
| `Endpoint__c` | URL | Callout target |
| `HTTP_Method__c` | Picklist | GET, POST, PATCH, DELETE |
| `Status_Code__c` | Number | HTTP response status |
| `Request_Body__c` | Long Text Area | Truncated at 128 KB |
| `Response_Body__c` | Long Text Area | Truncated at 128 KB |
| `Duration_Ms__c` | Number | Round-trip duration |
| `Correlation_ID__c` | Text(36) | UUID for transaction tracing |
| `Success__c` | Checkbox | True for 2xx responses |
| `Error_Message__c` | Long Text Area | Populated on exception |
| `Service_Name__c` | Text(255) | CMDT DeveloperName |

---

## 7. Exception Hierarchy

```apex
// IntegrationException.cls
public class IntegrationException extends Exception {
    public enum ErrorCode {
        CALLOUT_FAILURE,   // Network-level exception
        AUTH_FAILURE,      // 401/403 response
        TIMEOUT,           // Callout timed out
        RATE_LIMITED,      // 429 response, retry budget exhausted
        PARSE_FAILURE,     // Response body could not be deserialized
        SERVICE_DISABLED   // CMDT record inactive or class not found
    }
    public ErrorCode code { get; private set; }
    public IntegrationException(ErrorCode code, String message) {
        this(message);
        this.code = code;
    }
}
```

---

## 8. Dead-Letter Queue Pattern (Async Retry)

For durable retry beyond a single immediate attempt:

1. On `CALLOUT_FAILURE` or `RATE_LIMITED`, write a `Dead_Letter_Queue__c` record with the original request payload, service name, retry count, and next retry timestamp.
2. A scheduled Apex job (hourly) queries `Dead_Letter_Queue__c` records where `Next_Retry__c <= :now` and `Retry_Count__c < :maxRetries`.
3. For each record, enqueue an `IntegrationRetryQueueable` that calls the dispatcher, updates retry count, or deletes the record on success.
4. On final failure (retry count exhausted), set `Status__c = 'Dead'` and alert via custom notification or email.

---

## Checklist

- [ ] `IIntegrationService` interface defined
- [ ] `IntegrationRequest` and `IntegrationResult` DTOs created
- [ ] `Integration_Service__mdt` CMDT created with all required fields
- [ ] CMDT records created for all APIs and committed to source control
- [ ] `IntegrationServiceFactory` implemented with null/inactive guard
- [ ] `HttpCalloutDispatcher` implemented with timeout, retry, and finally-block logging
- [ ] `IntegrationLogger` writes `IntegrationLog__c` with truncation
- [ ] `IntegrationException` with `ErrorCode` enum
- [ ] Concrete service adapter(s) implemented and registered in CMDT
- [ ] Unit tests mock `IIntegrationService` via `@TestVisible` factory injection
- [ ] No hard-coded endpoints or credentials in Apex
- [ ] `validate_repo.py` passes
