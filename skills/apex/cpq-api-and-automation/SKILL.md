---
name: cpq-api-and-automation
description: "Use when programmatically driving Salesforce CPQ operations from Apex or REST — creating quotes, adding products, calculating pricing, saving quotes, amending contracts, or renewing contracts through the SBQQ.ServiceRouter API. Trigger keywords: CPQ API, SBQQ.ServiceRouter, QuoteCalculator, QuoteReader, QuoteSaver, QuoteProductAdder, ProductLoader, ContractAmender, ContractRenewer, programmatic quote, calculate callback, CPQ REST API. NOT for standard REST API or Salesforce Connect. NOT for declarative CPQ configuration such as price rules, discount schedules, or product rules. NOT for CPQ plugin interfaces (QuoteCalculatorPlugin, OrderPlugin)."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Reliability
  - Operational Excellence
triggers:
  - "how do I programmatically create a CPQ quote and add products without using the UI"
  - "how do I call the CPQ calculate API from Apex to reprice a quote after changing line fields"
  - "how do I amend or renew a contract programmatically using the CPQ API"
  - "SBQQ.ServiceRouter not found or loaderName parameter invalid"
  - "CPQ quote totals are wrong after I updated quote line fields with DML"
  - "how do I use the CPQ REST endpoint to create a quote from an external system"
  - "quote calculation is taking too long or timing out with many lines"
tags:
  - cpq
  - salesforce-cpq
  - sbqq
  - cpq-api
  - service-router
  - quote-calculation
  - contract-amendment
  - contract-renewal
  - programmatic-quoting
  - calculate-callback
inputs:
  - "Org's CPQ managed package version (SBQQ namespace)"
  - "Operation type: quote creation, product addition, calculation, save, amendment, or renewal"
  - "Quote ID or Contract ID for read/amend/renew operations"
  - "Product IDs and quantities to add via ProductLoader or QuoteProductAdder"
  - "Whether operation is invoked from Apex or via REST from an external system"
  - "Number of quote lines (affects sync vs. async calculation decision)"
outputs:
  - "Apex code invoking SBQQ.ServiceRouter with correct loaderName and serialized model"
  - "REST call shape for POST /services/apexrest/SBQQ/ServiceRouter"
  - "SBQQ.CalculateCallback implementation for async calculation"
  - "Decision table for loader string selection"
  - "Amendment and renewal workflow code"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# CPQ API and Automation

This skill covers all programmatic CPQ operations driven through `SBQQ.ServiceRouter` — the single correct entry point for creating, pricing, amending, and renewing CPQ quotes without using the CPQ UI. Activate when Apex code, a batch job, an integration, or an external system needs to drive CPQ operations that must respect the pricing engine.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Confirm CPQ managed package is installed.** All API classes live in the `SBQQ` namespace provided by the CPQ managed package. If `SBQQ.ServiceRouter` is not accessible, the package is not installed or the running user lacks the CPQ permission set.
- **Know the operation type.** Each CPQ operation maps to a specific loader string. Using the wrong loader string produces a runtime error or silently returns an empty model. Confirm whether the task is read, product-add, calculate, save, amend, or renew before writing any code.
- **Count the quote lines.** Synchronous quote calculation degrades noticeably past approximately 100 lines and can hit CPU governor limits in complex orgs. For high line-count quotes, plan to use the async calculate path or Large Quote Mode.
- **Never use direct DML on SBQQ objects for pricing fields.** Direct `insert` or `update` on `SBQQ__QuoteLine__c` bypasses the CPQ pricing engine. Fields such as `SBQQ__NetPrice__c`, `SBQQ__CustomerPrice__c`, `SBQQ__Discount__c`, and `SBQQ__RegularTotal__c` will be stale or inconsistent until the next full recalculation — which may overwrite your changes or produce corrupt totals on the quote.

---

## Core Concepts

### SBQQ.ServiceRouter — The Single Entry Point

All CPQ programmatic operations flow through `SBQQ.ServiceRouter`. The class exposes two key static methods:

- `SBQQ.ServiceRouter.read(String loaderName, String uid)` — reads a serialized JSON model for a given record.
- `SBQQ.ServiceRouter.save(String saverName, String model)` — persists a serialized JSON model back to the database.

A separate method handles calculation:

- `SBQQ.ServiceRouter.calculateInBackground(String quoteId, SBQQ.CalculateCallback callback)` — triggers async calculation and invokes the callback when complete.

The same operations are available via REST at `POST /services/apexrest/SBQQ/ServiceRouter` with a JSON body containing `loaderName` (or `saverName`) and `model` (a JSON-serialized string).

### Loader Strings

Each operation maps to a specific loader string that the `ServiceRouter` dispatches on:

| Loader String | Method | Purpose |
|---|---|---|
| `QuoteReader` | `read` | Read an existing quote and all its lines as a JSON model |
| `QuoteProductAdder` | `save` | Add one or more products to a quote model |
| `QuoteCalculator` | `save` / async | Re-price the quote model (sync or async) |
| `QuoteSaver` | `save` | Persist a calculated quote model to the database |
| `ProductLoader` | `read` | Load product catalog records into a quote-compatible product model |
| `ContractAmender` | `read` | Create an amendment quote model from an approved contract |
| `ContractRenewer` | `read` | Create a renewal quote model from an approved contract |

Passing an unrecognized string raises a runtime exception. Mixing read-phase loaders with save-phase savers (e.g., passing `QuoteReader` to `save()`) produces an error or a no-op.

### Async Calculate API and SBQQ.CalculateCallback

The `QuoteCalculator` operation used synchronously inside `ServiceRouter.save()` runs the pricing engine in the same transaction. For quotes with many lines, this consumes CPU time that accumulates against governor limits. Salesforce CPQ also exposes an **async calculate path**:

1. The calling code invokes `SBQQ.ServiceRouter.calculateInBackground(quoteId, callback)`.
2. CPQ triggers a queueable calculation job outside the current transaction.
3. When calculation completes, CPQ calls `callback.onCalculated(String quoteModel)` on the class that implements `SBQQ.CalculateCallback`.

The callback class must be `global` and implement `SBQQ.CalculateCallback`, which requires a single method: `void onCalculated(String quoteModel)`. Inside `onCalculated`, the implementation typically calls `SBQQ.ServiceRouter.save('QuoteSaver', quoteModel)` to persist the result.

Errors thrown inside `onCalculated` do not surface to the originating UI session. Robust implementations must log failures explicitly.

### Why Direct DML Corrupts CPQ Totals

The CPQ pricing engine maintains a consistent financial model across related fields on `SBQQ__QuoteLine__c` and `SBQQ__Quote__c`. These fields are not independent — they are outputs of a multi-pass calculation that evaluates price rules, discount schedules, block pricing, contracted prices, and subscription math in sequence.

Direct `update` on a quote line field (e.g., setting `SBQQ__Discount__c = 10`) skips all pricing passes. CPQ does not automatically recalculate downstream fields (`SBQQ__NetPrice__c`, `SBQQ__CustomerPrice__c`, `SBQQ__RegularTotal__c`, `SBQQ__Quote__c.SBQQ__NetTotal__c`, etc.). The line record and the quote header become financially inconsistent. On the next save through the CPQ UI, CPQ may overwrite your discount value with the engine's own calculated result.

Use `ServiceRouter` with `QuoteCalculator` + `QuoteSaver` to apply any programmatic field change that affects pricing.

---

## Common Patterns

### Pattern 1: Programmatic Quote Creation with Products and Calculation

**When to use:** An external system, batch process, or automation needs to create a complete CPQ quote with products and accurate pricing without a user opening the CPQ UI.

**How it works:**

1. Create a bare `SBQQ__Quote__c` record with `insert` (header fields only — no line manipulation).
2. Load the quote model: `String quoteModel = SBQQ.ServiceRouter.read('QuoteReader', quoteId);`
3. Load product records: `String productModel = SBQQ.ServiceRouter.read('ProductLoader', productId);`
4. Add products to the quote model: `String updatedModel = SBQQ.ServiceRouter.save('QuoteProductAdder', combineModels(quoteModel, productModel));`
5. Calculate pricing: `String calculatedModel = SBQQ.ServiceRouter.save('QuoteCalculator', updatedModel);`
6. Persist to database: `SBQQ.ServiceRouter.save('QuoteSaver', calculatedModel);`

**Why not direct insert of SBQQ__QuoteLine__c:** Inserting lines directly bypasses the product configuration model, skips bundle expansion, and produces lines with no pricing engine state. The resulting lines will have null or zero values for all calculated price fields.

### Pattern 2: Async Calculation for High Line-Count Quotes

**When to use:** The quote has more than approximately 100 lines, or the sync calculation path is hitting CPU governor limits or taking over 5 seconds.

**How it works:**

1. Implement a `global class MyCalculateCallback implements SBQQ.CalculateCallback`.
2. In `onCalculated(String quoteModel)`, call `SBQQ.ServiceRouter.save('QuoteSaver', quoteModel)` and log any errors.
3. Invoke: `SBQQ.ServiceRouter.calculateInBackground(quoteId, new MyCalculateCallback());`
4. The method returns immediately; calculation runs asynchronously as a queueable.
5. Poll or use a platform event to detect completion if the calling process needs to wait.

**Why not sync calculate:** Synchronous `QuoteCalculator` via `ServiceRouter.save()` processes all lines in the current transaction. Past ~100 lines, CPU consumption can breach the 10-second limit, causing an unhandled `LimitException` that rolls back the entire transaction.

### Pattern 3: Contract Amendment and Renewal via API

**When to use:** An integration or automation needs to programmatically create amendment or renewal quotes from approved contracts without a user clicking "Amend" or "Renew" in the UI.

**How it works:**

Amendment:
1. Read the amendment model: `String amendModel = SBQQ.ServiceRouter.read('ContractAmender', contractId);`
2. Modify the returned model JSON to change quantities, add products, or end-date lines.
3. Calculate: `String calculatedModel = SBQQ.ServiceRouter.save('QuoteCalculator', amendModel);`
4. Save: `SBQQ.ServiceRouter.save('QuoteSaver', calculatedModel);`

Renewal:
1. Read the renewal model: `String renewModel = SBQQ.ServiceRouter.read('ContractRenewer', contractId);`
2. Optionally modify the model (e.g., adjust quantities or pricing).
3. Calculate and save as above.

The contract must have `SBQQ__Status__c = 'Activated'` (approved). Passing an unapproved contract ID returns an error or an empty model.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Create a quote and add products programmatically | QuoteReader → QuoteProductAdder → QuoteCalculator → QuoteSaver | Follows the CPQ calculation pipeline in correct order |
| Re-price a quote after changing a field | QuoteReader → modify model → QuoteCalculator → QuoteSaver | Pricing engine must see the full model; partial updates are not supported |
| Quote has 100+ lines | Async calculate via calculateInBackground + CalculateCallback | Sync path risks CPU governor limit; async is the safe path |
| Amend an existing contract | ContractAmender → QuoteCalculator → QuoteSaver | ContractAmender sets up the amendment delta model correctly |
| Renew an expiring contract | ContractRenewer → QuoteCalculator → QuoteSaver | ContractRenewer clones subscriptions into a renewal quote |
| Add a product to a quote | ProductLoader + QuoteProductAdder | Load product into model format before adding to quote |
| Direct DML on SBQQ__QuoteLine__c for pricing fields | Never — use ServiceRouter | Direct DML bypasses pricing engine; produces corrupt totals |
| Call CPQ API from an external system | REST POST /services/apexrest/SBQQ/ServiceRouter | Same loaderName/model pattern over HTTP with OAuth session |

---

## Recommended Workflow

1. **Identify the operation and select the loader string.** Match the business requirement to the correct loader string from the taxonomy table. Confirm the input record (quote ID, contract ID, product ID) is available and the record is in the required state (e.g., contract must be activated for amendment/renewal).
2. **Read the current model.** Call `SBQQ.ServiceRouter.read(loaderName, recordId)` to obtain the JSON model. Do not construct the model JSON manually — the schema is internal to the CPQ package and changes across versions.
3. **Modify the model if required.** For add-product flows, load the product model separately and pass both to `QuoteProductAdder`. For field changes, parse the JSON, update the relevant fields, re-serialize, and pass to `QuoteCalculator`.
4. **Calculate pricing.** Pass the modified model through `QuoteCalculator`. For quotes under ~100 lines, use synchronous `ServiceRouter.save('QuoteCalculator', model)`. For larger quotes, use `calculateInBackground` with a `CalculateCallback` implementation.
5. **Save the calculated model.** Call `ServiceRouter.save('QuoteSaver', calculatedModel)` to persist all CPQ fields. Do not save the model by DML — always use `QuoteSaver`.
6. **Validate the results.** Query the saved `SBQQ__Quote__c` and spot-check key calculated fields (`SBQQ__NetTotal__c`, `SBQQ__GrossTotal__c`, line-level `SBQQ__NetPrice__c`). Confirm the totals are non-null and match the expected pricing.
7. **Handle errors explicitly.** `ServiceRouter` calls can throw runtime exceptions. Wrap each call in try/catch, log failures with context (loaderName, record ID, model snippet), and surface errors to calling processes. In async callbacks, log failures to a custom object or platform event since exceptions in `onCalculated` are silent.

---

## Review Checklist

- [ ] All CPQ operations go through `SBQQ.ServiceRouter` — no direct DML on SBQQ pricing fields
- [ ] Loader strings match the intended operation (read vs. save vs. async)
- [ ] Contract is in Activated status before calling ContractAmender or ContractRenewer
- [ ] Quote line count evaluated — async path used if count may exceed ~100 lines
- [ ] `SBQQ.CalculateCallback` implementation is `global` and handles errors explicitly
- [ ] REST calls include valid OAuth token and correct Content-Type: application/json
- [ ] Calculated model saved via `QuoteSaver`, not via DML
- [ ] Governor limits (CPU, heap, SOQL) reviewed in debug logs under realistic line counts
- [ ] Errors from ServiceRouter calls are caught and logged with sufficient context

---

## Salesforce-Specific Gotchas

1. **Direct DML on SBQQ__QuoteLine__c corrupts pricing totals** — Writing directly to price fields (`SBQQ__Discount__c`, `SBQQ__NetPrice__c`, etc.) bypasses all pricing engine passes. The quote header totals become stale and the line data is financially inconsistent. The next UI-driven save may silently overwrite your values. Always route field changes through the ServiceRouter model pipeline.

2. **Async calculate errors are silent** — Exceptions thrown inside `SBQQ.CalculateCallback.onCalculated()` do not propagate to the original calling context. If the callback crashes, the quote is left in a partially calculated state with no user-visible error. Implement explicit logging (custom object insert, platform event) inside `onCalculated` error handlers.

3. **Sync calculate degrades past ~100 lines** — The synchronous `QuoteCalculator` path runs in the current Apex transaction. On complex orgs with many price rules or configuration rules, CPU consumption per line can be high. A 150-line quote can easily consume 8–9 seconds of CPU, leaving little headroom for the rest of the transaction. Plan the async path for any quote that could grow beyond 100 lines.

4. **Model JSON schema is internal and version-specific** — The JSON returned by `QuoteReader`, `ContractAmender`, etc. reflects the internal CPQ data model for the installed package version. Manually constructing or hardcoding model JSON is fragile — field names and nesting change across CPQ releases. Always start from a `ServiceRouter.read()` response and modify in place.

5. **ContractAmender and ContractRenewer require Activated contracts** — Passing a contract with `SBQQ__Status__c` other than `'Activated'` returns an error or an empty model. This is not always obvious because the error message from ServiceRouter can be generic. Validate contract status before invoking these loaders.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Apex ServiceRouter invocation | Code calling `SBQQ.ServiceRouter.read()` and `save()` with correct loader strings |
| CalculateCallback class | `global class` implementing `SBQQ.CalculateCallback` for async calculation flows |
| REST call example | POST body shape for `/services/apexrest/SBQQ/ServiceRouter` |
| Loader string decision table | Mapping from operation to loaderName/saverName |
| Amendment/renewal workflow | Apex sequence for contract amendment or renewal via ContractAmender/ContractRenewer |

---

## Related Skills

- `apex/cpq-apex-plugins` — CPQ plugin interfaces (QuoteCalculatorPlugin, OrderPlugin) for hooking into calculation lifecycle; distinct from ServiceRouter-based API operations
- `admin/cpq-pricing-rules` — Declarative price rules that fire during quote calculation; understand these before using the API to override prices
- `admin/cpq-quote-templates` — Quote template configuration; required to understand how quote output relates to programmatic quote data
