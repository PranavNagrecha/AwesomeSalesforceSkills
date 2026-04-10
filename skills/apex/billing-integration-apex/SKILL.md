---
name: billing-integration-apex
description: "Use when programmatically generating invoices, integrating payment gateways, automating credit notes, or calling Salesforce Billing Apex APIs (blng.InvoiceAPI, blng.TransactionAPI) from custom Apex code. Trigger keywords: billing apex, blng.InvoiceAPI, blng.TransactionAPI, payment gateway adapter, invoice generation apex, credit note apex, programmatic invoice. NOT for admin billing setup, billing rule configuration, billing policy UI, or Invoice Run scheduling."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Performance
triggers:
  - "How do I programmatically generate an invoice from Apex for a billing schedule?"
  - "I need to integrate a custom payment gateway with Salesforce Billing using Apex"
  - "How do I issue a credit note or void a payment transaction via the Billing API?"
tags:
  - billing-integration-apex
  - blng
  - invoice-api
  - transaction-api
  - payment-gateway
  - salesforce-billing
  - managed-package
inputs:
  - "Target org has Salesforce Billing managed package installed (blng__ namespace)"
  - "API version 63.0 or later (required for Connect REST API commerce/invoices endpoint)"
  - "List of blng__BillingSchedule__c IDs or Account ID for invoice generation"
  - "Payment gateway credentials and endpoint details for custom gateway adapter implementation"
  - "Apex class or trigger context where billing API calls will be made"
outputs:
  - "Apex class using blng.TransactionAPI in an async context (Queueable or @future)"
  - "Apex class implementing blng.PaymentGateway interface for custom gateway integration"
  - "HTTP callout code targeting Connect REST API POST /commerce/invoices for invoice generation"
  - "Credit note automation using blng.InvoiceAPI"
  - "Checklist of transaction lifecycle validation steps"
dependencies:
  - callout-and-dml-transaction-boundaries
  - apex-queueable-patterns
  - callouts-and-http-integrations
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# Billing Integration Apex

Use this skill when writing Apex code that calls the Salesforce Billing managed package APIs — `blng.InvoiceAPI`, `blng.TransactionAPI`, or the Connect REST API commerce/invoices endpoint — to programmatically generate invoices, drive payment gateway lifecycles, or automate credit note issuance. This skill does NOT cover admin configuration of billing rules, billing treatments, invoice run scheduling, or tax policies.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the Salesforce Billing managed package is installed and the `blng__` namespace is present in the target org. All Billing sObjects use this namespace (e.g., `blng__Invoice__c`, `blng__BillingSchedule__c`, `blng__Payment__c`).
- Identify the API version. The Connect REST API `POST /services/data/vXX.0/commerce/invoices` endpoint requires API version 63.0 or later (Spring '25+).
- The most common wrong assumption: calling `blng.TransactionAPI` methods in the same synchronous transaction that also performs DML. `TransactionAPI` methods execute HTTP callouts internally; mixing callouts with uncommitted DML causes a `System.CalloutException: You have uncommitted work pending. Please commit or rollback before calling out` error. All `TransactionAPI` calls must run in an async context with no pending DML.
- Platform constraint: a single Connect REST API invoice generation call accepts a maximum of 200 `blng__BillingSchedule__c` IDs per request.

---

## Core Concepts

### blng.InvoiceAPI — Credit Operations

`blng.InvoiceAPI` is the managed-package Apex API for credit-side invoice operations. Its primary use is issuing credit notes against existing invoices. Credit notes create offsetting `blng__Invoice__c` records and adjust the outstanding balance on related billing schedules. The method signature follows the pattern of accepting an invoice ID and returning a result object. Credit note generation does not trigger HTTP callouts, so it can be called in a standard synchronous transaction alongside DML.

### blng.TransactionAPI — Payment Gateway Lifecycle

`blng.TransactionAPI` is the managed-package Apex API for driving the full payment transaction lifecycle. It exposes the following methods:

| Method | Purpose |
|---|---|
| `generateToken` | Tokenise payment method with the gateway |
| `authorize` | Reserve funds without capturing |
| `capture` | Capture previously authorized funds |
| `charge` | Authorize and capture in a single step |
| `void` | Cancel an authorized or captured transaction |
| `refund` | Return funds for a completed transaction |

Every one of these methods executes an HTTP callout to the configured payment gateway. Because Salesforce enforces the rule that callouts cannot be made after DML in the same transaction, all `TransactionAPI` calls must be isolated in an asynchronous context. Use a `Queueable` class implementing `Database.AllowsCallouts`, or a `@future(callout=true)` method. Queueable is preferred because it is chainable, testable with `Test.startTest()/stopTest()`, and supports `Database.AllowsCallouts` explicitly.

### Connect REST API — Programmatic Invoice Generation

Salesforce Billing exposes a Connect REST API endpoint for programmatic invoice generation outside the standard batch Invoice Run:

```
POST /services/data/v63.0/commerce/invoices
```

This endpoint accepts a request body containing either:
- `accountId` — generate invoices for all eligible billing schedules under that account, or
- `billingScheduleIds` — an array of specific `blng__BillingSchedule__c` IDs (maximum 200 per call)

The endpoint requires API version 63.0 or later. Calls are made via `HttpRequest`/`Http` in Apex or via named credentials pointing to the org itself (self-callout pattern). Because this is an HTTP callout, the same DML constraint applies: it must be called from an async context if the same transaction includes DML.

### Payment Gateway Adapter Interface

To integrate a custom payment gateway (one not natively supported by Salesforce Billing), implement the `blng.PaymentGateway` interface. This interface defines the contract that the Billing package calls when routing transactions through your custom gateway. The implementing class is registered in the org's Payment Gateway configuration record (`blng__PaymentGateway__c`) by setting the `blng__GatewayType__c` field to reference the Apex class. The Billing package then invokes the interface methods during transaction lifecycle calls, passing request objects and expecting response objects defined within the `blng` namespace.

---

## Common Patterns

### Pattern: Async Payment Transaction via Queueable

**When to use:** When a trigger, flow-invoked action, or controller needs to authorize, capture, or charge a payment but the calling context may have uncommitted DML or is synchronous.

**How it works:**
1. Collect the payment record ID and desired operation in the calling context.
2. Enqueue a `Queueable` class implementing `Database.AllowsCallouts`.
3. Inside `execute()`, call the appropriate `blng.TransactionAPI` method with no preceding DML.
4. Persist the result (success/failure, gateway reference ID) to a custom field or a related record as the only DML in the job.

**Why not the alternative:** Calling `blng.TransactionAPI` synchronously from a trigger or a batch `execute()` method that has already performed DML causes an immediate `CalloutException`. The `@future(callout=true)` pattern works but cannot be chained or easily unit-tested; Queueable is preferred.

### Pattern: Batched Invoice Generation via Connect REST API

**When to use:** When you need to programmatically trigger invoice generation for a known set of billing schedules outside the standard Invoice Run batch schedule.

**How it works:**
1. Query the `blng__BillingSchedule__c` IDs to process.
2. Chunk the IDs into lists of no more than 200.
3. For each chunk, build an `HttpRequest` to `POST /services/data/v63.0/commerce/invoices` with a JSON body containing `billingScheduleIds`.
4. Call from an async context (Queueable with `Database.AllowsCallouts`) to avoid DML conflicts.
5. Parse the response to identify any failed schedule IDs and retry or log them.

**Why not the alternative:** Invoking the standard Invoice Run batch from Apex (`blng.InvoiceRunAPI`) processes all eligible schedules and cannot be scoped to a specific subset without filtering logic inside the batch itself; the Connect REST API gives precise control.

### Pattern: Custom Payment Gateway Adapter

**When to use:** When the organization uses a payment processor not natively supported by Salesforce Billing and needs full lifecycle control (tokenise, authorize, capture, void, refund).

**How it works:**
1. Create an Apex class implementing `blng.PaymentGateway`.
2. Implement each required interface method; translate incoming Billing request objects to your gateway's API format, execute the HTTP callout, and map the response back to Billing response objects.
3. Register the class name in the `blng__PaymentGateway__c` record's `blng__GatewayType__c` field.
4. Billing's `TransactionAPI` methods will automatically route through your adapter when that gateway is selected on a payment record.

**Why not the alternative:** Directly calling the gateway from a custom trigger on `blng__Payment__c` bypasses the Billing transaction lifecycle, preventing correct status management and reconciliation.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need to issue a credit note against an existing invoice | `blng.InvoiceAPI` in synchronous Apex | No callout; can run in same transaction as DML |
| Need to charge a payment method immediately | `blng.TransactionAPI.charge()` in a Queueable with `Database.AllowsCallouts` | TransactionAPI makes HTTP callouts; must be async with no pending DML |
| Need to generate invoices for a specific set of billing schedules | Connect REST API `POST /commerce/invoices` from async context | Provides precise schedule targeting; standard Invoice Run batch cannot scope to a subset |
| Connecting a new payment processor | Implement `blng.PaymentGateway` interface | Required contract for Billing to route lifecycle calls to custom gateway |
| Generating invoices for all schedules on an account | Connect REST API with `accountId` body parameter | Simpler than specifying individual IDs; Billing resolves eligible schedules automatically |
| Large invoice batch (>200 schedules) | Chunk IDs into lists of ≤200, call API per chunk from Queueable chain | Hard limit of 200 billing schedule IDs per Connect REST API request |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm prerequisites** — Verify the `blng__` managed package namespace is present in the org and that the target API version is 63.0 or later. Identify whether the requirement is invoice generation, payment transaction management, credit note issuance, or custom gateway integration.
2. **Check transaction context** — Determine whether the calling context (trigger, batch, invocable, controller) performs DML before the billing API call. If any DML precedes a `blng.TransactionAPI` call or a Connect REST API callout, refactor the callout into an async context (Queueable implementing `Database.AllowsCallouts` is preferred over `@future`).
3. **Implement the Apex class** — For `TransactionAPI` usage, write a Queueable class. For `blng.InvoiceAPI`, write synchronous Apex. For the Connect REST API, build the `HttpRequest` with the correct endpoint, API version, and JSON body. For custom gateways, implement the `blng.PaymentGateway` interface.
4. **Handle the 200-schedule limit** — If generating invoices for more than 200 billing schedules, implement chunking logic before calling the Connect REST API. Use a Queueable chain or Batch Apex to process each chunk sequentially.
5. **Write tests with mock callouts** — Use `HttpCalloutMock` for TransactionAPI and Connect REST API tests. Ensure `Test.startTest()/stopTest()` wraps Queueable enqueues. Test both success and gateway-error response paths.
6. **Validate output records** — After execution, query `blng__Invoice__c` for invoice generation tests, `blng__Payment__c` / `blng__PaymentGatewayLog__c` for transaction tests, and confirm status fields reflect the expected lifecycle state.
7. **Review checklist below** — Confirm no uncommitted DML precedes callouts, namespace usage is correct, and API version is enforced in all endpoint URLs.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] All `blng.TransactionAPI` calls are in a Queueable implementing `Database.AllowsCallouts` or in a `@future(callout=true)` method — no synchronous context with preceding DML
- [ ] Connect REST API endpoint URL contains the correct API version (v63.0 or later)
- [ ] Invoice generation calls contain no more than 200 `billingScheduleIds` per request; chunking logic exists for larger sets
- [ ] All Billing sObject references use the `blng__` namespace prefix (e.g., `blng__Invoice__c`, not `Invoice__c`)
- [ ] Test classes use `HttpCalloutMock` for all callout-dependent paths; no live callouts in tests
- [ ] Custom gateway adapter class is registered on the `blng__PaymentGateway__c` record's `blng__GatewayType__c` field
- [ ] Error handling captures gateway response codes and persists failure details to a log record or platform event for observability

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **TransactionAPI callout + uncommitted DML** — Calling any `blng.TransactionAPI` method in a transaction that has uncommitted DML (including inserts, updates, or deletes that have not been committed) immediately throws `System.CalloutException: You have uncommitted work pending`. This is a Salesforce platform constraint, not a Billing-specific one, but it catches developers who write trigger-based payment logic without async offloading.
2. **200 billing schedule hard limit on Connect REST API** — The `POST /commerce/invoices` endpoint rejects requests containing more than 200 entries in the `billingScheduleIds` array. There is no soft warning; the call fails. Implement explicit chunking before calling the endpoint when processing large volumes.
3. **blng__ namespace on all managed package references** — Omitting the `blng__` prefix on any Billing sObject field or class reference causes a compile-time or runtime error. This applies to SOQL queries (`SELECT blng__InvoiceStatus__c FROM blng__Invoice__c`), DML operations, and field API name references. The `blng.InvoiceAPI` and `blng.TransactionAPI` classes use the `blng` namespace prefix without the double underscore — that is the Apex class namespace, distinct from the sObject namespace convention.
4. **API version enforcement on commerce/invoices endpoint** — Calling the Connect REST API commerce/invoices endpoint with an API version below 63.0 returns a 404 or unsupported resource error. Hard-code the version in named credential URL overrides or endpoint strings, and document the minimum version requirement in the class header.
5. **Gateway adapter interface changes across managed package versions** — The `blng.PaymentGateway` interface is defined inside the managed package. Upgrading the Billing package can add new required interface methods, breaking existing adapter classes with compile errors until they are updated. Pin the package version in sandbox before upgrading production when custom adapters are in use.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Queueable Apex class | Async worker implementing `Database.AllowsCallouts` that drives `blng.TransactionAPI` lifecycle calls |
| Connect REST API callout class | Apex class issuing `POST /commerce/invoices` requests with chunking support |
| `blng.PaymentGateway` adapter | Custom gateway implementation registered on `blng__PaymentGateway__c` |
| Credit note Apex | Synchronous class calling `blng.InvoiceAPI` for credit note automation |
| Test class with `HttpCalloutMock` | Unit tests covering success and failure paths for all callout-dependent code |

---

## Related Skills

- `callout-and-dml-transaction-boundaries` — Core platform rule this skill depends on; read before writing any TransactionAPI code
- `apex-queueable-patterns` — Patterns for Queueable chaining and error handling relevant to batched invoice generation
- `callouts-and-http-integrations` — HTTP callout patterns, named credentials, and mock strategies used for Connect REST API calls
- `admin/billing-schedule-setup` — Admin skill for configuring the billing rules and schedules that this skill operates on programmatically

---

## Official Sources Used

- Salesforce Billing Developer Guide — InvoiceAPI Class: https://developer.salesforce.com/docs/atlas.en-us.billing.meta/billing/billing_dev_invoice_api.htm
- Salesforce Billing Developer Guide — TransactionAPI Class: https://developer.salesforce.com/docs/atlas.en-us.billing.meta/billing/billing_dev_transaction_api.htm
- Salesforce Billing Developer Guide — Payment Gateway Adapter: https://developer.salesforce.com/docs/atlas.en-us.billing.meta/billing/billing_dev_gateway_adapter.htm
- Connect REST API — Create Invoices: https://developer.salesforce.com/docs/atlas.en-us.chatterapi.meta/chatterapi/connect_resources_commerce_invoices.htm
- Apex Developer Guide — Callouts and DML: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts_dml.htm
