# Gotchas — CPQ API and Automation

Non-obvious Salesforce CPQ platform behaviors that cause real production problems when using the CPQ API.

## Gotcha 1: Direct DML on SBQQ__QuoteLine__c Silently Corrupts Quote Totals

**What happens:** An Apex class or trigger updates pricing fields (`SBQQ__Discount__c`, `SBQQ__AdditionalDiscount__c`, `SBQQ__UnitPrice__c`) directly on `SBQQ__QuoteLine__c` via DML. The DML succeeds with no error. But the downstream calculated fields — `SBQQ__NetPrice__c`, `SBQQ__CustomerPrice__c`, `SBQQ__RegularTotal__c`, and the quote header totals — are not updated. The quote record is now financially inconsistent.

**When it occurs:** Any time Apex code bypasses `SBQQ.ServiceRouter` to write to CPQ-owned fields. This frequently appears in custom triggers, batch jobs, integrations, and Flow-invoked Apex actions that "just want to update a discount."

**How to avoid:** All CPQ pricing field changes must go through the full ServiceRouter pipeline: `QuoteReader` → modify model JSON → `QuoteCalculator` → `QuoteSaver`. Never use DML for fields that the CPQ pricing engine owns. If a trigger on `SBQQ__QuoteLine__c` is needed for non-pricing custom fields, ensure it does not touch any CPQ-calculated field.

---

## Gotcha 2: Async CalculateCallback Errors Are Completely Silent

**What happens:** An exception thrown inside `SBQQ.CalculateCallback.onCalculated()` is swallowed by the CPQ queueable framework. The quote is left in a partially-calculated state. No error is surfaced to the user who triggered the calculation, no email is sent, and no debug log is written to a surfaced location. From the user's perspective, the quote simply never finishes calculating.

**When it occurs:** Any unhandled exception in `onCalculated` — including a `DmlException` when saving the model, a `LimitException` if the save triggers additional processing, or a `NullPointerException` on the model JSON.

**How to avoid:** Wrap the entire body of `onCalculated` in a try/catch. Log failures to a custom object (e.g., `CPQ_Calculation_Error__c`) or publish a platform event. Do not assume success — the callback may be invoked multiple times in retry scenarios. Include the quote ID (parsed from the model) and a truncated model snippet in your error log for debuggability.

---

## Gotcha 3: Synchronous Calculate Breaks Past ~100 Lines

**What happens:** `SBQQ.ServiceRouter.save('QuoteCalculator', model)` runs the pricing engine synchronously inside the current Apex transaction. For quotes with many lines, complex price rules, or bundle configurations, each additional line adds CPU cost. Past approximately 100 lines, quotes in production orgs with non-trivial CPQ configuration can consume the full 10-second CPU governor limit, resulting in an unhandled `System.LimitException` that rolls back the entire transaction.

**When it occurs:** Batch jobs processing multiple large quotes, triggers that recalculate on quote line changes, and integrations that build quotes with 150+ lines programmatically.

**How to avoid:** Use `SBQQ.ServiceRouter.calculateInBackground(quoteId, callback)` for any quote that might exceed ~100 lines. This moves the pricing engine work into a separate queueable transaction. Alternatively, enable Large Quote Mode in CPQ Settings, which optimizes the calculation engine for high line-count quotes — but this mode changes certain UI behaviors so test thoroughly.

---

## Gotcha 4: ContractAmender and ContractRenewer Require Activated Contract Status

**What happens:** Calling `SBQQ.ServiceRouter.read('ContractAmender', contractId)` or `SBQQ.ServiceRouter.read('ContractRenewer', contractId)` on a contract that is not in `Activated` status returns an empty model, a generic error, or throws a runtime exception. The error message from the ServiceRouter is often not specific enough to identify the cause.

**When it occurs:** Automations that amend contracts before the contracting flow has fully activated them, integrations that run too early in an asynchronous contracting pipeline, and test setups that create Contract records without setting the required status.

**How to avoid:** Always query `SBQQ__Status__c` on the Contract before invoking `ContractAmender` or `ContractRenewer`. Assert `SBQQ__Status__c == 'Activated'` and fail fast with a descriptive error if the condition is not met. In automated flows, add a status check with a retry or wait mechanism if the contracting job runs asynchronously.

---

## Gotcha 5: ServiceRouter Model JSON Schema Is Internal and Version-Specific

**What happens:** Code that manually constructs the JSON payload for `QuoteProductAdder` or `QuoteCalculator` by hardcoding field names or nesting structure breaks silently when the CPQ managed package is upgraded. The ServiceRouter accepts the malformed model without error but produces incorrect or incomplete output.

**When it occurs:** Any implementation that builds model JSON from scratch rather than starting from a `ServiceRouter.read()` response. This is common in integrations that receive product data from an external system and attempt to construct the CPQ model directly.

**How to avoid:** Always start from a model obtained via `ServiceRouter.read()`. Modify only known-safe fields in the returned JSON (quantities, discounts, dates). Do not add, remove, or rename top-level keys. If you need to pass external data into the model, use CPQ custom fields on the Quote or QuoteLine objects that are surfaced in the model, rather than inventing model keys.

---

## Gotcha 6: SBQQ.ServiceRouter Is Not Available in Test Context Without Data Setup

**What happens:** Unit tests that call `SBQQ.ServiceRouter.read()` or `save()` fail with a `System.CalloutException` or `NullPointerException` if the org's CPQ Settings record is not present or if `SBQQ__Product2__c` and related objects are not properly configured. CPQ's ServiceRouter relies on org configuration that is not automatically present in test contexts.

**When it occurs:** Tests run in orgs without CPQ test data factory setup, or in scratch orgs where CPQ post-install configuration has not been applied.

**How to avoid:** Use the CPQ test data factory (`SBQQ.TestDataFactory`) if available in your package version, or create the required CPQ Settings, Product, Price Book, and Price Book Entry records in `@TestSetup`. Mark tests with `@IsTest(SeeAllData=true)` only as a last resort — this is fragile and environment-dependent. Prefer building minimal required data in test setup.
