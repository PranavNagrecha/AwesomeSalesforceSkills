# Examples — Integration Framework Design

Concrete scenarios illustrating when and how to apply the integration framework architecture.

---

## Scenario 1: Multi-API Integration Framework with Shared Infrastructure

**Context:** A financial services org integrates with five external APIs: a KYC identity verification service, a credit bureau, a payment processor, a fraud detection engine, and an e-signature provider. Each API has its own auth mechanism and response format, but all share the same requirements for logging, retry, and error reporting.

**Without a framework:** Each integration team builds its own `HttpRequest` / `HttpResponse` wiring. Logging is inconsistently applied. Timeouts differ across classes. When the security team requires request body masking before logging, they must update five different classes. When a new API is added, the pattern starts from scratch.

**With the integration framework:**

- `IIntegrationService` defines the shared contract. Each of the five APIs has a concrete class: `KycIntegrationService`, `CreditBureauService`, `PaymentGatewayService`, `FraudDetectionService`, `ESignatureService`.
- `HttpCalloutDispatcher` handles auth header injection (via Named Credentials for each API), timeout (pulled from `Timeout_Ms__c` on `Integration_Service__mdt`), retry on 429/503, correlation ID generation, and a single call to `IntegrationLogger`.
- `IntegrationLog__c` records every callout. The support team queries logs by `Correlation_ID__c` to trace a specific transaction across multiple service calls.
- When the security team adds PII masking to request bodies before logging, they change `IntegrationLogger` in one place. All five services inherit the fix automatically.
- A sixth API is added later. The team creates one new `Integration_Service__mdt` record and one new concrete class. Zero changes to the dispatcher, factory, or logger.

**Key result:** Shared infrastructure changes propagate to all services with one code change. New integrations are additive, not foundational.

---

## Scenario 2: Factory Resolves Payment Gateway by Country via Custom Metadata

**Context:** A global retail org processes payments through different payment gateways depending on the merchant's country: Stripe for US and Canada, Adyen for Europe, PayU for Latin America. The checkout flow invokes a single `processPayment()` method and should not know which gateway is active.

**Integration_Service__mdt records:**

| DeveloperName | Service_Class__c | Endpoint__c | Active__c |
|---|---|---|---|
| Payment_US | `PaymentGatewayStripeService` | `callout:Stripe_NC` | true |
| Payment_EU | `PaymentGatewayAdyenService` | `callout:Adyen_NC` | true |
| Payment_LATAM | `PaymentGatewayPayUService` | `callout:PayU_NC` | true |

**Factory resolution:**

```apex
String serviceKey = 'Payment_' + merchantRegion; // e.g. 'Payment_EU'
IIntegrationService paymentService = IntegrationServiceFactory.resolve(serviceKey);
IntegrationResult result = paymentService.callout(request);
```

**When PayU has a regional outage:** The support team sets `Active__c = false` on the `Payment_LATAM` record. No deployment needed. The factory throws `IntegrationException` with `SERVICE_DISABLED` code. The checkout flow catches that code and routes to a fallback messaging screen.

**When a new gateway is added for APAC:** One new `Integration_Service__mdt` record and one new concrete class. The checkout flow is unchanged.

**Key result:** The factory and Custom Metadata registry decouple routing decisions from code. Environment-specific routing is data, not logic.
