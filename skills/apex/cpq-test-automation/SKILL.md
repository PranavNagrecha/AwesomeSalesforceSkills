---
name: cpq-test-automation
description: "Use when writing, reviewing, or debugging test classes for Salesforce CPQ (Steelbrick) functionality — including quote creation, price rules, contracting, ordering, and CPQ API integration. Trigger keywords: CPQ test class, SBQQ test, quote calculation test, price rule test, CPQ Apex test, ServiceRouter test, QuoteCalculator test. NOT for standard Apex testing patterns unrelated to CPQ, nor for UI/Selenium test authoring outside the CPQ context."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "My CPQ price rules are not firing in my Apex test class even though my DML looks correct"
  - "How do I set up test data for SBQQ__Quote__c with the right Account, Opportunity, and Pricebook fields?"
  - "I need to write an Apex test that exercises CPQ quote calculation using ServiceRouter or QuoteCalculator"
  - "My CPQ Apex test fails because the standard pricebook ID is hardcoded and invalid in the test org"
  - "How do I test CPQ contracting and order generation from Apex without hitting governor limits?"
tags:
  - cpq
  - sbqq
  - apex-testing
  - price-rules
  - quote-calculation
  - service-router
  - contracting
  - ordering
inputs:
  - "CPQ version and package namespace (SBQQ__) installed in the target org"
  - "Quote, QuoteLine, Product, and Pricebook2 configuration in the org"
  - "Whether price rules or advanced approval rules are in scope for testing"
  - "Whether contracting and/or ordering flows need to be covered"
outputs:
  - "Compliant Apex test class that correctly sets up SBQQ__Quote__c prerequisites"
  - "ServiceRouter-based quote calculation test invoking the CPQ calculation engine"
  - "Test coverage for contracting and order generation from CPQ quotes"
  - "Guidance on which CPQ behaviors cannot be mocked and require a full package installation"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# CPQ Test Automation

Use this skill when writing or debugging Apex test classes that cover Salesforce CPQ functionality, including quote data setup, price rule execution, CPQ API calls (ServiceRouter, QuoteCalculator), contracting, and order generation. Activate when a practitioner cannot get CPQ behaviors to trigger in tests or when test data setup causes SBQQ errors.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm that the Salesforce CPQ managed package (namespace `SBQQ__`) is installed in the test org. CPQ test classes cannot run without the package; no mock substitution is supported.
- Identify whether the test must cover price rule execution. If yes, the CPQ calculation engine must be invoked via `SBQQ.ServiceRouter` — direct DML on quote lines does not fire price rules.
- Confirm that the standard pricebook is referenced via `Test.getStandardPricebookId()` (not a hardcoded ID). Hardcoded pricebook IDs are org-specific and always invalid in Salesforce-managed test orgs.

---

## Core Concepts

### Four-Layer CPQ Test Strategy

CPQ test coverage operates at four distinct layers, each covering behaviors the layers above cannot reach:

1. **Apex unit tests** — Cover CRUD operations on CPQ objects (`SBQQ__Quote__c`, `SBQQ__QuoteLine__c`, `SBQQ__Contract__c`, `SBQQ__Order__c`), field validation, trigger logic, and custom Apex extensions. These tests do not invoke the CPQ calculation engine and therefore do not fire price rules.
2. **CPQ API tests** — Invoke `SBQQ.ServiceRouter` (or `SBQQ.QuoteCalculatorPlugin`) to exercise the CPQ calculation engine, price rule evaluation, quote line group ordering, and discount schedule application. This is the only supported way to test price rule execution in Apex.
3. **Selenium / WebDriver UI tests** — Cover option constraint enforcement, configurator UX, and guided selling flows that are embedded in the CPQ UI and are not accessible from Apex. UTAM page objects are the Salesforce-recommended approach for Shadow DOM-based CPQ components.
4. **Lightning component tests** — Jest unit tests for any custom LWC components built on top of CPQ (e.g., custom quote line editors, configurator overrides). These are isolated from the CPQ managed package.

### SBQQ__Quote__c Data Prerequisites

`SBQQ__Quote__c` has three mandatory lookup relationships that must be satisfied before any CPQ test can succeed:

- **Account** (`SBQQ__Account__c`) — A valid `Account` record must exist.
- **Opportunity** (`SBQQ__Opportunity__c`) — The Opportunity must be associated with the same Account.
- **Pricebook2** (`SBQQ__PricebookId__c`) — Must reference the standard pricebook, retrieved exclusively via `Test.getStandardPricebookId()`. Hardcoded IDs fail because the standard pricebook ID differs between every org.

Omitting any of these prerequisites causes validation errors that appear as unrelated failures deep in the CPQ calculation engine, not as obvious prerequisite errors.

### Price Rule Execution Requires the CPQ Calculation Engine

Price rules in Salesforce CPQ are evaluated by the managed package's internal calculation engine, not by Apex triggers or DML operations. When a test class inserts or updates `SBQQ__QuoteLine__c` records directly, the calculation engine does not run. Price rule conditions and actions are never evaluated. To trigger price rules in a test, the test must call `SBQQ.ServiceRouter.calculateQuote()` (or equivalent `QuoteCalculatorPlugin` interface) with a properly serialized quote model. This is a hard platform constraint — it cannot be worked around by System.runAs, Test.startTest, or any DML pattern.

---

## Common Patterns

### Pattern: ServiceRouter-Based Quote Calculation Test

**When to use:** Any test that must verify price rule outcomes, discount schedule application, quote line pricing, or net totals.

**How it works:**
1. Insert `Account`, `Opportunity`, and `Pricebook2` (standard pricebook via `Test.getStandardPricebookId()`).
2. Insert `Product2` and `PricebookEntry` records linked to the standard pricebook.
3. Insert `SBQQ__Quote__c` with all required lookups.
4. Insert `SBQQ__QuoteLine__c` records referencing the quote and product.
5. Call `SBQQ.ServiceRouter.calculateQuote(quoteId)` inside `Test.startTest()` / `Test.stopTest()`.
6. Re-query quote lines to assert expected calculated values.

**Why not direct DML:** Directly inserting quote lines and asserting prices skips price rule evaluation entirely. Tests pass locally but the price rule logic is never covered — leading to false confidence and production defects.

### Pattern: Contracting and Order Generation Test

**When to use:** Tests that verify quote-to-contract and contract-to-order flows, including the `SBQQ__Contracted__c` flag behavior and `SBQQ__Order__c` creation.

**How it works:**
1. Set up a fully calculated quote (using the ServiceRouter pattern above) with `SBQQ__Ordered__c = false` and `SBQQ__Primary__c = true`.
2. Call the CPQ contracting API (`SBQQ.ContractingService.contract(quoteId)`) within `Test.startTest()` / `Test.stopTest()`.
3. Assert that `SBQQ__Contract__c` records are created and the quote's `SBQQ__Contracted__c` is set to `true`.
4. Separately test order generation by setting `SBQQ__Quote__c.SBQQ__Ordered__c = true` and asserting `Order` and `OrderItem` creation via the CPQ order API.

**Why not a direct insert of SBQQ__Contract__c:** Direct insertion bypasses the CPQ contracting engine, which applies subscription asset creation, renewal opportunity generation, and contract term derivation. These behaviors will not appear in tests that bypass the API.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Testing custom Apex trigger logic on CPQ objects | Apex unit test with direct DML | Trigger logic runs on DML; no need to invoke CPQ engine |
| Testing that a price rule sets a field value correctly | ServiceRouter calculation test | Price rules only fire through the CPQ calculation engine |
| Testing CPQ configurator option constraints in the UI | Selenium / UTAM UI test | Option constraints are enforced in the CPQ UI, not in Apex |
| Testing a custom LWC built on top of CPQ | Jest unit test (LWC testing) | LWC component logic is isolated from the managed package |
| Testing quote-to-contract flow | CPQ Contracting API test | Direct SBQQ__Contract__c DML bypasses subscription asset logic |
| Verifying pricing totals after discount schedule application | ServiceRouter calculation test | Discount schedules are evaluated by the CPQ calculation engine |
| Testing custom Apex class implementing QuoteCalculatorPlugin | CPQ API test with plugin invocation | Plugin interface is only exercised via the CPQ engine call |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm package installation** — Verify the `SBQQ__` namespace is available in the org. Run `SELECT Id, NamespacePrefix FROM PackageLicense WHERE NamespacePrefix = 'SBQQ'` in Developer Console or check Installed Packages. Tests will fail at compile time if the namespace is not present.
2. **Set up mandatory Quote prerequisites** — In `@testSetup`, create an `Account`, an `Opportunity` linked to that Account, and retrieve the standard pricebook via `Test.getStandardPricebookId()`. Create `Product2` and `PricebookEntry` records linked to the standard pricebook.
3. **Create the SBQQ__Quote__c record** — Insert `SBQQ__Quote__c` with `SBQQ__Account__c`, `SBQQ__Opportunity__c`, and `SBQQ__PricebookId__c` all populated. Insert `SBQQ__QuoteLine__c` records referencing the quote and the product.
4. **Invoke the CPQ calculation engine for price-sensitive tests** — Call `SBQQ.ServiceRouter.calculateQuote(quoteId)` inside `Test.startTest()` / `Test.stopTest()` whenever the test must verify price rule outcomes, totals, or discount application. Do not assert pricing fields after plain DML.
5. **Use CPQ API for contracting and ordering** — Use `SBQQ.ContractingService.contract(quoteId)` for contracting tests and the CPQ ordering API for order generation tests. Do not directly insert `SBQQ__Contract__c` or `Order` records expecting CPQ-managed fields to be populated.
6. **Assert on re-queried records** — After `Test.stopTest()`, re-query the relevant records to assert field values. CPQ calculations and field updates happen asynchronously within the engine call and are committed when the test transaction completes.
7. **Run tests in isolation and in suite** — CPQ tests can share state through `@testSetup`, but verify tests pass both in isolation (single test method) and as a full class run. CPQ calculation engine behavior can be affected by governor limit accumulation across methods.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] `Test.getStandardPricebookId()` is used — no hardcoded pricebook IDs anywhere in test setup
- [ ] `SBQQ__Quote__c` has all three required lookups: Account, Opportunity, Pricebook2
- [ ] Any test asserting price rule outcomes calls `SBQQ.ServiceRouter.calculateQuote()` — not just DML
- [ ] Contracting tests use the CPQ contracting API, not direct `SBQQ__Contract__c` insertion
- [ ] All test methods use `Test.startTest()` / `Test.stopTest()` around CPQ engine calls
- [ ] The CPQ managed package (`SBQQ__`) is confirmed to be installed in the test org
- [ ] Tests pass both individually and as a full class to catch shared-state issues

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Direct DML does not fire price rules** — Inserting or updating `SBQQ__QuoteLine__c` records directly never invokes the CPQ calculation engine. Price rule conditions and actions are skipped entirely. Tests that assert price values after plain DML are testing nothing; they will pass even when price rules are broken.
2. **Hardcoded pricebook IDs cause silent test failures** — The standard pricebook ID is unique to each org. Hardcoding an ID from a developer sandbox causes test failures in all other orgs (including CI and production) with a generic lookup validation error that does not mention the pricebook.
3. **CPQ package must be installed in every test org** — There is no supported mock or stub for the `SBQQ__` namespace. Tests referencing CPQ types fail to compile without the package. This means CPQ test classes cannot be deployed to orgs where CPQ is not installed, which affects scratch org provisioning and CI pipeline design.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Apex test class | A `@isTest` class with `@testSetup` covering SBQQ__Quote__c prerequisites, CPQ API invocations, and assertions on price rule and contracting outcomes |
| ServiceRouter test method | A test method that invokes `SBQQ.ServiceRouter.calculateQuote()` and asserts specific price rule field values |
| Contracting test method | A test method that invokes the CPQ contracting API and asserts SBQQ__Contract__c creation and subscription asset generation |

---

## Related Skills

- cpq-api-and-automation — Use alongside when the production code being tested uses ServiceRouter, QuoteCalculatorPlugin, or the CPQ REST API
- cpq-data-model — Use to understand the full SBQQ object relationships required for valid test data setup
- automated-regression-testing — Use when adding CPQ Selenium / UTAM UI tests to a regression suite
