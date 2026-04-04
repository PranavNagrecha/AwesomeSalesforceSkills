---
name: integration-framework-design
description: "Use when designing a reusable integration layer in Salesforce that serves multiple external APIs through a shared callout infrastructure. Triggers: 'how to design a reusable integration layer in Salesforce', 'architect an Apex callout framework for multiple APIs', 'create a centralized error handling pattern for integrations', 'service interface pattern for external APIs', 'factory pattern for dynamic API resolution', 'centralized callout dispatcher'. NOT for individual API implementation (use apex/callouts-and-http-integrations), NOT for Named Credential setup (use integration/named-credentials-setup), NOT for async callout patterns (use apex/continuation-callouts)."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Scalability
  - Operational Excellence
tags:
  - integration
  - service-interface
  - factory-pattern
  - callout-framework
  - custom-metadata
  - error-propagation
  - response-logging
  - architecture
triggers:
  - "how to design a reusable integration layer in Salesforce"
  - "architect an Apex callout framework for multiple APIs"
  - "create a centralized error handling pattern for integrations"
  - "service interface pattern for external API integrations"
  - "factory pattern for dynamic service resolution in Apex"
  - "how do I avoid repeating HTTP logic across multiple integration classes"
  - "centralized callout dispatcher with logging and retry"
inputs:
  - "Number and types of external APIs to integrate"
  - "Synchronous vs asynchronous callout requirements"
  - "Logging and observability requirements"
  - "Retry and dead-letter queue requirements"
  - "Environment-specific endpoint or credential differences"
outputs:
  - "Integration framework architecture decision record"
  - "Interface and factory class scaffolding"
  - "Custom Metadata Type design for service registry"
  - "Centralized dispatcher pattern with retry and logging"
  - "IntegrationLog__c object field map"
  - "Error propagation strategy with exception hierarchy"
dependencies:
  - apex/callouts-and-http-integrations
  - apex/apex-design-patterns
  - apex/custom-metadata-in-apex
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

Use this skill when you are building or reviewing an integration layer that must serve more than one external API without duplicating HTTP mechanics, auth handling, logging, or retry logic across multiple callout classes. The goal is a framework that is cohesive, observable, and reconfigurable without code changes.

## Before Starting

- How many external APIs does this framework need to serve now and in the near future?
- Which callout requirements are shared (auth, retry, logging, timeout) versus API-specific (payload shape, error mapping)?
- What are the observability requirements — do integration logs need to be queryable by support teams?
- Is there a need for environment-specific endpoints (sandbox vs production) managed without code changes?
- What is the retry budget — synchronous retry on transient failure, or async dead-letter queue for durable retry?

## Core Concepts

### Service Interface Pattern

Define a single Apex interface that every external API adapter must implement. The interface declares the contract — a `callout()` method and a `parseResponse()` method — without prescribing how any particular API fulfills it. Callers depend only on the interface, not on any concrete implementation.

```apex
public interface IIntegrationService {
    HttpResponse callout(IntegrationRequest request);
    IntegrationResult parseResponse(HttpResponse response);
}
```

Each API gets its own concrete class implementing `IIntegrationService`. The class knows the API's payload structure, authentication mechanism, and response mapping. Nothing else in the org needs to know those details.

### Factory Pattern with Custom Metadata

Hard-coding which service class to instantiate in calling code creates coupling that breaks as the integration landscape grows. Use a factory class that reads from a Custom Metadata Type (`Integration_Service__mdt`) to resolve the right implementation at runtime.

```apex
public class IntegrationServiceFactory {
    public static IIntegrationService resolve(String serviceApiName) {
        Integration_Service__mdt record = [
            SELECT Service_Class__c, Endpoint__c, Active__c
            FROM Integration_Service__mdt
            WHERE DeveloperName = :serviceApiName
            AND Active__c = true
            LIMIT 1
        ];
        Type serviceType = Type.forName(record.Service_Class__c);
        return (IIntegrationService) serviceType.newInstance();
    }
}
```

`Integration_Service__mdt` fields: `DeveloperName` (API name key), `Service_Class__c` (fully-qualified Apex class name), `Endpoint__c` (base URL), `Active__c` (toggle), `Timeout_Ms__c` (per-service override).

This design allows endpoint swapping across environments without touching Apex. It also allows deactivating a service in emergency without a deployment.

### Centralized Callout Dispatcher

The dispatcher is the single class that wraps `HttpRequest` / `HttpResponse` mechanics. It handles authentication header injection (via Named Credentials or stored secrets), timeout configuration, retry on transient status codes (429, 503), correlation ID generation, and response logging. Concrete service classes do not create `Http` instances directly — they delegate to the dispatcher.

```apex
public class HttpCalloutDispatcher {
    public HttpResponse dispatch(HttpRequest req, String correlationId) {
        Http http = new Http();
        Long start = System.currentTimeMillis();
        HttpResponse res;
        try {
            res = http.send(req);
        } catch (System.CalloutException e) {
            IntegrationLogger.logFailure(req, e, correlationId);
            throw new IntegrationException(IntegrationException.ErrorCode.CALLOUT_FAILURE, e.getMessage());
        } finally {
            IntegrationLogger.logResponse(req, res, start, correlationId);
        }
        return res;
    }
}
```

### Request and Response DTOs

Strongly-typed request and response objects prevent primitive obsession. `IntegrationRequest` carries endpoint, method, headers, and body. `IntegrationResult` carries success flag, parsed payload, HTTP status, error code, and correlation ID. These shapes are stable across all concrete services — only the body contents differ.

### Response Logging

Every callout, successful or failed, writes an `IntegrationLog__c` record. Fields: `Endpoint__c`, `HTTP_Method__c`, `Status_Code__c`, `Request_Body__c` (truncated at 131,072 chars), `Response_Body__c` (truncated), `Duration_Ms__c`, `Correlation_ID__c`, `Success__c`, `Error_Message__c`, `Service_Name__c`, `Created_By_Context__c` (trigger, batch, queueable).

Logging synchronously from within a callout is safe in non-trigger contexts. In trigger context, use Platform Events to decouple logging DML from the transaction — see gotchas.

### Error Propagation

Define a typed exception class with an inner error code enum so callers can branch on failure type without string parsing.

```apex
public class IntegrationException extends Exception {
    public enum ErrorCode {
        CALLOUT_FAILURE,
        AUTH_FAILURE,
        TIMEOUT,
        RATE_LIMITED,
        PARSE_FAILURE,
        SERVICE_DISABLED
    }
    public ErrorCode code { get; private set; }
    public IntegrationException(ErrorCode code, String message) {
        this(message);
        this.code = code;
    }
}
```

For async contexts, implement a dead-letter pattern: failed callout requests are written to a `Dead_Letter_Queue__c` custom object or Platform Event topic for retry by a scheduled Queueable that respects a configurable retry budget.

### Dynamic Service Resolution

The `Integration_Service__mdt` Custom Metadata Type acts as a service registry. Because Custom Metadata records are queryable in tests without DML and are deployable as metadata, they travel through CI/CD pipelines alongside code. Per-environment endpoint overrides can use org-specific Custom Metadata record overrides or Named Credentials (preferred for credentials).

## Recommended Workflow

1. **Inventory integrations** — list all external APIs, their protocols, auth mechanisms, and retry requirements. Identify which callout behaviors are shared versus unique.
2. **Design the interface and DTOs** — define `IIntegrationService`, `IntegrationRequest`, and `IntegrationResult` before writing any concrete adapter. Lock the contract first.
3. **Create the Custom Metadata Type** — create `Integration_Service__mdt` with the required fields. Add one record per external API. This is the service registry.
4. **Build the dispatcher** — implement `HttpCalloutDispatcher` with auth injection, timeout, retry logic, correlation ID, and call to `IntegrationLogger`.
5. **Implement concrete service adapters** — one class per API implementing `IIntegrationService`. Each class knows only its API's payload and error mapping. It calls the dispatcher for HTTP.
6. **Implement `IntegrationServiceFactory`** — use `Type.forName()` to resolve service classes from Custom Metadata. Add `null`/`inactive` guard and surface `SERVICE_DISABLED` error code.
7. **Validate and test** — mock the dispatcher in unit tests using an interface split. Run validate_repo after scaffolding. Confirm `IntegrationLog__c` records are created in integration tests.

## Related Skills

- `apex/callouts-and-http-integrations` — use for individual HttpRequest/HttpResponse implementation details and Named Credential usage
- `apex/apex-design-patterns` — use for service layer, selector, and dependency injection patterns that complement this framework
- `apex/custom-metadata-in-apex` — use for CMDT query patterns, test data setup, and deployment considerations
- `integration/named-credentials-setup` — use when designing the auth layer of the dispatcher
- `apex/exception-handling` — use when designing the exception hierarchy and propagation strategy
