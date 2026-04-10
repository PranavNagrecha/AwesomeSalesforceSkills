# CPQ Test Automation — Work Template

Use this template when writing, reviewing, or debugging Apex test classes for Salesforce CPQ functionality.

## Scope

**Skill:** `cpq-test-automation`

**Request summary:** (fill in what the user asked for — e.g., "Write a test class for a price rule that applies a 20% discount when Quantity > 10")

---

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md before writing any code.

- **CPQ package installed in target org?** [ ] Yes / [ ] No — if No, stop: tests cannot compile without SBQQ namespace
- **Test layer needed:** [ ] Apex unit (CRUD/trigger) / [ ] CPQ API (price rules/contracting) / [ ] Selenium UI / [ ] LWC Jest
- **Price rules in scope?** [ ] Yes — must use ServiceRouter / [ ] No — DML-only tests are acceptable
- **Contracting in scope?** [ ] Yes — must use ContractingService API / [ ] No
- **Standard pricebook reference method confirmed:** [ ] Test.getStandardPricebookId() used (not hardcoded)

---

## Prerequisites Checklist

Before inserting any SBQQ__Quote__c record, confirm all three required lookups will be created:

- [ ] Account (`SBQQ__Account__c`) created in @testSetup
- [ ] Opportunity (`SBQQ__Opportunity__c`) created, linked to same Account
- [ ] Pricebook2 retrieved via `Test.getStandardPricebookId()` (never hardcoded)
- [ ] Product2 + PricebookEntry inserted in the standard pricebook
- [ ] SBQQ__Quote__c inserted with all three lookups populated

---

## Test Class Skeleton

```apex
@isTest
private class [YourClass]Test {

    @testSetup
    static void setupData() {
        // 1. Account
        Account acc = new Account(Name = 'Test Account');
        insert acc;

        // 2. Opportunity
        Opportunity opp = new Opportunity(
            Name      = 'Test Opp',
            AccountId = acc.Id,
            StageName = 'Prospecting',
            CloseDate = Date.today().addDays(30)
        );
        insert opp;

        // 3. Standard Pricebook — Test.getStandardPricebookId() ONLY
        Id stdPbId = Test.getStandardPricebookId();

        // 4. Product + PricebookEntry
        Product2 prod = new Product2(Name = '[Product Name]', IsActive = true);
        insert prod;

        PricebookEntry pbe = new PricebookEntry(
            Pricebook2Id = stdPbId,
            Product2Id   = prod.Id,
            UnitPrice    = [LIST_PRICE],
            IsActive     = true
        );
        insert pbe;

        // 5. CPQ Quote
        SBQQ__Quote__c quote = new SBQQ__Quote__c(
            SBQQ__Account__c     = acc.Id,
            SBQQ__Opportunity__c = opp.Id,
            SBQQ__PricebookId__c = stdPbId,
            SBQQ__Primary__c     = true,
            SBQQ__Status__c      = 'Draft'
        );
        insert quote;

        // 6. Quote Line(s)
        SBQQ__QuoteLine__c ql = new SBQQ__QuoteLine__c(
            SBQQ__Quote__c            = quote.Id,
            SBQQ__Product__c          = prod.Id,
            SBQQ__PricebookEntryId__c = pbe.Id,
            SBQQ__Quantity__c         = [QUANTITY]
        );
        insert ql;
    }

    // --- Apex unit test (trigger / CRUD logic) ---
    @isTest
    static void test[TriggerBehavior]() {
        SBQQ__QuoteLine__c ql = [SELECT Id, [Field] FROM SBQQ__QuoteLine__c LIMIT 1];
        // Assert trigger outcome — no ServiceRouter needed for trigger-only coverage
        System.assertEquals([EXPECTED], ql.[Field], '[Assertion message]');
    }

    // --- CPQ API test (price rules / discount schedules) ---
    @isTest
    static void test[PriceRuleName]() {
        SBQQ__Quote__c quote = [SELECT Id FROM SBQQ__Quote__c LIMIT 1];

        Test.startTest();
        SBQQ.ServiceRouter.calculateQuote(quote.Id);  // fires price rules
        Test.stopTest();

        SBQQ__QuoteLine__c ql = [
            SELECT SBQQ__CustomerPrice__c, SBQQ__NetPrice__c
            FROM   SBQQ__QuoteLine__c
            WHERE  SBQQ__Quote__c = :quote.Id
            LIMIT 1
        ];
        System.assertEquals([EXPECTED_PRICE], ql.SBQQ__CustomerPrice__c,
            '[Price rule name] should set CustomerPrice to [EXPECTED_PRICE]');
    }

    // --- Contracting test ---
    @isTest
    static void testContracting() {
        SBQQ__Quote__c quote = [SELECT Id FROM SBQQ__Quote__c LIMIT 1];

        Test.startTest();
        SBQQ.ContractingService.contract(quote.Id);
        Test.stopTest();

        List<SBQQ__Contract__c> contracts = [
            SELECT Id FROM SBQQ__Contract__c WHERE SBQQ__Quote__c = :quote.Id
        ];
        System.assertEquals(1, contracts.size(), 'CPQ should have created one contract');

        List<SBQQ__Subscription__c> subs = [
            SELECT Id FROM SBQQ__Subscription__c WHERE SBQQ__Contract__c = :contracts[0].Id
        ];
        System.assertFalse(subs.isEmpty(), 'CPQ contracting should have created subscription assets');
    }
}
```

---

## Approach

Which pattern from SKILL.md applies? (circle one and explain why)

- [ ] **Apex unit test** — covering trigger logic, CRUD validation, or custom Apex extension; no engine invocation needed
- [ ] **ServiceRouter calculation test** — covering price rules, discount schedules, or net total assertions
- [ ] **Contracting API test** — covering quote-to-contract flow, subscription asset creation, or renewal opportunity generation
- [ ] **Ordering API test** — covering contract-to-order flow and OrderItem creation

Reason: _______________________________________________

---

## Review Checklist

Tick items as you complete them (from SKILL.md Review Checklist):

- [ ] `Test.getStandardPricebookId()` is used — no hardcoded pricebook IDs anywhere
- [ ] `SBQQ__Quote__c` has all three required lookups: Account, Opportunity, Pricebook2
- [ ] Any price rule assertions use `SBQQ.ServiceRouter.calculateQuote()` — not just DML
- [ ] Contracting tests use `SBQQ.ContractingService.contract()`, not direct SBQQ__Contract__c inserts
- [ ] All engine calls are wrapped in `Test.startTest()` / `Test.stopTest()`
- [ ] CPQ managed package is confirmed installed in the test org
- [ ] Tests pass individually and as full class run

---

## Notes

Record any deviations from the standard pattern and the rationale:

- _Deviation:_ _______________________________________________
- _Reason:_ _______________________________________________
