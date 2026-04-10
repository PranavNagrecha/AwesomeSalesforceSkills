# LLM Anti-Patterns — CPQ Test Automation

Common mistakes AI coding assistants make when generating or advising on CPQ Test Automation.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using Direct DML and Expecting Price Rules to Fire

**What the LLM generates:** A test method that inserts `SBQQ__QuoteLine__c` records with a specific quantity and then immediately asserts that `SBQQ__CustomerPrice__c` or `SBQQ__NetPrice__c` equals the price rule's expected output — with no `ServiceRouter` call in between.

**Why it happens:** LLMs trained on general Apex patterns know that DML triggers Apex triggers and workflow rules. They generalize this to CPQ price rules, which are a fundamentally different mechanism. The training data contains many examples of "insert record, assert field" patterns that work correctly for non-CPQ objects, leading to confident but wrong CPQ advice.

**Correct pattern:**

```apex
// WRONG — price rules never fire
insert ql;
SBQQ__QuoteLine__c result = [SELECT SBQQ__CustomerPrice__c FROM SBQQ__QuoteLine__c WHERE Id = :ql.Id];
System.assertEquals(80.00, result.SBQQ__CustomerPrice__c); // always fails or false-passes

// CORRECT — invoke the CPQ calculation engine
insert ql;
Test.startTest();
SBQQ.ServiceRouter.calculateQuote(quote.Id);
Test.stopTest();
SBQQ__QuoteLine__c result = [SELECT SBQQ__CustomerPrice__c FROM SBQQ__QuoteLine__c WHERE Id = :ql.Id];
System.assertEquals(80.00, result.SBQQ__CustomerPrice__c);
```

**Detection hint:** Look for `System.assertEquals` or `System.assertNotEquals` on `SBQQ__CustomerPrice__c`, `SBQQ__NetPrice__c`, `SBQQ__RegularPrice__c`, or any custom price-rule-driven field without a preceding `SBQQ.ServiceRouter` call.

---

## Anti-Pattern 2: Hardcoding Pricebook IDs in Test Setup

**What the LLM generates:** Test setup that sets `SBQQ__PricebookId__c` to a hardcoded string like `'01s000000000001AAA'` or references a static final ID constant defined at the class level.

**Why it happens:** LLMs frequently see Salesforce test code that hardcodes IDs for various reasons (custom settings, record types, profiles). They apply the same pattern to pricebook IDs without knowing that the standard pricebook ID is org-specific and that `Test.getStandardPricebookId()` exists specifically to solve this problem.

**Correct pattern:**

```apex
// WRONG — hardcoded ID breaks in every org other than origin
SBQQ__Quote__c q = new SBQQ__Quote__c(
    SBQQ__PricebookId__c = '01s000000000001AAA', // NEVER do this
    ...
);

// CORRECT — runtime lookup, org-agnostic
Id stdPbId = Test.getStandardPricebookId();
SBQQ__Quote__c q = new SBQQ__Quote__c(
    SBQQ__PricebookId__c = stdPbId,
    ...
);
```

**Detection hint:** Search for string literals matching `01s[a-zA-Z0-9]{15}` in test class setup methods, or for `Pricebook2` ID assignments that do not call `Test.getStandardPricebookId()`.

---

## Anti-Pattern 3: Not Setting All Required SBQQ__Quote__c Lookup Fields

**What the LLM generates:** A `SBQQ__Quote__c` insert that populates only `SBQQ__Status__c` and `SBQQ__Primary__c`, omitting `SBQQ__Account__c`, `SBQQ__Opportunity__c`, or `SBQQ__PricebookId__c`.

**Why it happens:** LLMs infer required fields from the Salesforce object's visible required-field markers in documentation snippets, which often do not include CPQ's cross-object validation rules. The LLM produces code that looks syntactically complete but fails at runtime with cryptic CPQ engine errors.

**Correct pattern:**

```apex
// WRONG — missing three required lookups
SBQQ__Quote__c q = new SBQQ__Quote__c(
    SBQQ__Primary__c = true,
    SBQQ__Status__c  = 'Draft'
);
insert q; // fails with FIELD_INTEGRITY_EXCEPTION inside CPQ

// CORRECT — all three lookups populated
SBQQ__Quote__c q = new SBQQ__Quote__c(
    SBQQ__Account__c     = acc.Id,
    SBQQ__Opportunity__c = opp.Id,
    SBQQ__PricebookId__c = Test.getStandardPricebookId(),
    SBQQ__Primary__c     = true,
    SBQQ__Status__c      = 'Draft'
);
insert q;
```

**Detection hint:** Any `SBQQ__Quote__c` insert statement that does not include all three of `SBQQ__Account__c`, `SBQQ__Opportunity__c`, and `SBQQ__PricebookId__c` is incomplete.

---

## Anti-Pattern 4: Mocking or Stubbing the CPQ Package Namespace

**What the LLM generates:** Test code that attempts to use `StubProvider` or `Test.createStub()` to mock `SBQQ.ServiceRouter` or `SBQQ__Quote__c` DML, claiming this avoids the need to install the CPQ package.

**Why it happens:** LLMs are familiar with Apex's `StubProvider` interface for mocking custom Apex classes. They misapply this to managed package types, not knowing that managed package types and global methods cannot be mocked through `StubProvider` in the Apex testing framework. The generated code fails to compile.

**Correct pattern:**

```apex
// WRONG — managed package types cannot be mocked via StubProvider
// This code does not compile:
SBQQ.ServiceRouter mockRouter = (SBQQ.ServiceRouter) Test.createStub(
    SBQQ.ServiceRouter.class, new MyMockProvider()
);

// CORRECT — CPQ must be installed in the org; invoke real engine in tests
// Ensure the CPQ package is in sfdx-project.json packageAliases
// and your CI pipeline installs it before deploying tests
Test.startTest();
SBQQ.ServiceRouter.calculateQuote(quote.Id);
Test.stopTest();
```

**Detection hint:** Any use of `Test.createStub` or `StubProvider` referencing `SBQQ.*` types. Also flag comments claiming that CPQ behavior can be tested without the package installed.

---

## Anti-Pattern 5: Direct SBQQ__Contract__c Insertion to Test Contracting

**What the LLM generates:** A contracting test that directly inserts `SBQQ__Contract__c` records and asserts their existence, claiming this validates the CPQ contracting flow.

**Why it happens:** LLMs default to "if you want to test that a Contract exists, insert one and assert it exists." They miss that CPQ contracting is a managed-package orchestration that creates subscription assets, renewal opportunities, and applies contract term logic — none of which runs when records are inserted directly.

**Correct pattern:**

```apex
// WRONG — bypasses the CPQ contracting engine entirely
SBQQ__Contract__c c = new SBQQ__Contract__c(
    SBQQ__Quote__c = quote.Id,
    ...
);
insert c;
System.assertNotEquals(null, c.Id); // proves nothing about CPQ contracting

// CORRECT — invoke CPQ contracting API on a fully calculated quote
SBQQ__Quote__c quote = [SELECT Id FROM SBQQ__Quote__c LIMIT 1];
Test.startTest();
SBQQ.ContractingService.contract(quote.Id);
Test.stopTest();

// Assert that CPQ engine created the contract AND the subscription assets
List<SBQQ__Contract__c> contracts = [SELECT Id FROM SBQQ__Contract__c WHERE SBQQ__Quote__c = :quote.Id];
System.assertEquals(1, contracts.size(), 'CPQ contracting should have created one contract');

List<SBQQ__Subscription__c> subs = [SELECT Id FROM SBQQ__Subscription__c WHERE SBQQ__Contract__c = :contracts[0].Id];
System.assertFalse(subs.isEmpty(), 'CPQ contracting should have created subscription assets');
```

**Detection hint:** Any test that inserts `SBQQ__Contract__c` directly without a preceding `SBQQ.ContractingService.contract()` call. Also flag tests that only assert `SBQQ__Contract__c` existence without checking `SBQQ__Subscription__c` records.
