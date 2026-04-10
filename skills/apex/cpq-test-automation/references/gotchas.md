# Gotchas — CPQ Test Automation

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Direct DML on Quote Lines Does Not Fire Price Rules

**What happens:** A developer inserts or updates `SBQQ__QuoteLine__c` records directly via DML and then asserts that price-rule-driven fields (such as `SBQQ__CustomerPrice__c`, `SBQQ__NetPrice__c`, or custom price-rule-set fields) contain expected values. The assertions pass because the fields hold their default or manually-assigned values — not because the price rule ran. The price rule evaluation logic lives entirely inside the CPQ managed package's calculation engine and is never triggered by DML operations alone.

**When it occurs:** Any time a test class inserts or updates CPQ quote lines and then queries back calculated pricing fields without calling `SBQQ.ServiceRouter.calculateQuote()`. This is the single most common CPQ test authoring mistake.

**How to avoid:** Always invoke `SBQQ.ServiceRouter.calculateQuote(quoteId)` within `Test.startTest()` / `Test.stopTest()` before asserting any field that a price rule, discount schedule, or block pricing configuration is expected to set. Do not assert pricing fields after plain DML.

---

## Gotcha 2: Hardcoded Pricebook IDs Fail in Every Other Org

**What happens:** A developer copies a standard pricebook ID directly from their developer sandbox (e.g., `01s000000000001AAA`) and hardcodes it in test data setup. Tests pass in that developer's org but fail in all CI orgs, scratch orgs, and production with a `FIELD_INTEGRITY_EXCEPTION` or `INVALID_ID_FIELD` error. The error message does not clearly identify the pricebook as the culprit because the failure occurs inside CPQ's internal validation, not at the DML layer.

**When it occurs:** Whenever `Test.getStandardPricebookId()` is not used and the pricebook ID is instead embedded as a string literal or static variable. Also occurs when the ID is stored in a Custom Setting or Custom Metadata record that differs between orgs.

**How to avoid:** Always call `Test.getStandardPricebookId()` in `@testSetup` and pass the returned ID to `SBQQ__Quote__c.SBQQ__PricebookId__c` and to any `PricebookEntry` inserts. This method is available exclusively in test context and returns the correct standard pricebook ID for the current org at runtime.

---

## Gotcha 3: CPQ Managed Package Must Be Installed in Every Test Org

**What happens:** CPQ Apex test classes reference types in the `SBQQ__` namespace (e.g., `SBQQ__Quote__c`, `SBQQ.ServiceRouter`). If the CPQ managed package is not installed in the org where tests are deployed, the classes fail to compile. Deployment errors appear as `Variable does not exist: SBQQ__Quote__c` or `Type does not exist: SBQQ`. There is no supported mock or stub mechanism for the CPQ namespace.

**When it occurs:** When deploying CPQ test classes to a scratch org provisioned without the CPQ package, or when a CI pipeline targets a sandboxed org where CPQ is not installed. This is especially common in developer experience (DX) workflows where scratch orgs are created from a project definition that omits the CPQ package install step.

**How to avoid:** Add the CPQ package installation step to your scratch org definition file (`packageAliases` in `sfdx-project.json`) and ensure the CI pipeline installs the package before deploying and running tests. Do not attempt to conditionally compile CPQ test classes based on namespace availability — Apex has no preprocessor directives.

---

## Gotcha 4: SBQQ__Quote__c Requires Account, Opportunity, and Pricebook2 — All Three

**What happens:** Developers insert `SBQQ__Quote__c` with only the fields they are aware of (e.g., Status and Primary) and omit one or more of the three required lookup fields. The resulting errors are often misleading — they manifest as internal CPQ engine failures rather than clear required-field validation errors, especially when the omission is caught during a `ServiceRouter` call rather than at DML time.

**When it occurs:** During initial test class authoring when the developer relies on the Salesforce object creation wizard's "required fields" indicator, which may not surface CPQ's cross-object validation rules. Also common when test data is refactored and one of the three lookups is accidentally removed.

**How to avoid:** Always populate `SBQQ__Account__c`, `SBQQ__Opportunity__c`, and `SBQQ__PricebookId__c` on every `SBQQ__Quote__c` test record. The Opportunity's `AccountId` must match the Quote's `SBQQ__Account__c`. Use a `@testSetup` method that always creates all three parent records in the correct order.

---

## Gotcha 5: Contracting and Ordering APIs Are Not Equivalent to Direct SBQQ__Contract__c Insertion

**What happens:** A developer tests CPQ contracting by directly inserting `SBQQ__Contract__c` records and asserting they exist. The test passes, but the CPQ contracting engine (which creates subscription assets, renewal opportunities, and derives contract terms from quote lines) never runs. Production bugs in contracting logic are not caught.

**When it occurs:** When the test goal is stated as "verify a contract is created" rather than "verify CPQ contracting produces the correct assets and relationships." Direct insertion satisfies the first goal but not the second.

**How to avoid:** Use `SBQQ.ContractingService.contract(quoteId)` to trigger the CPQ contracting flow from a fully calculated quote. Assert on `SBQQ__Subscription__c` records, renewal opportunity creation, and the `SBQQ__Contracted__c` flag on the quote — not just on `SBQQ__Contract__c` existence.
