# Examples — CPQ Test Automation

## Example 1: Setting Up SBQQ__Quote__c with Correct Data Prerequisites

**Context:** A developer needs to write a test class for a custom Apex trigger on `SBQQ__QuoteLine__c`. The test must create valid CPQ quote data without causing lookup validation errors deep in the CPQ managed package.

**Problem:** Tests fail with unhelpful errors like "FIELD_INTEGRITY_EXCEPTION" or "REQUIRED_FIELD_MISSING" on fields the developer did not intentionally omit, because `SBQQ__Quote__c` silently requires Account, Opportunity, and Pricebook2 to be populated and consistent.

**Solution:**

```apex
@isTest
private class CPQQuoteLineTest {

    @testSetup
    static void setupData() {
        // 1. Account — required by SBQQ__Quote__c.SBQQ__Account__c
        Account acc = new Account(Name = 'Test Account');
        insert acc;

        // 2. Opportunity — must reference the same Account
        Opportunity opp = new Opportunity(
            Name        = 'Test Opp',
            AccountId   = acc.Id,
            StageName   = 'Prospecting',
            CloseDate   = Date.today().addDays(30)
        );
        insert opp;

        // 3. Standard Pricebook — MUST use Test.getStandardPricebookId()
        //    Hardcoding the ID breaks in every org other than the one it was copied from.
        Id stdPricebookId = Test.getStandardPricebookId();

        // 4. Product and PricebookEntry in the standard pricebook
        Product2 prod = new Product2(Name = 'Cloud Storage', IsActive = true);
        insert prod;

        PricebookEntry pbe = new PricebookEntry(
            Pricebook2Id   = stdPricebookId,
            Product2Id     = prod.Id,
            UnitPrice      = 100.00,
            IsActive       = true
        );
        insert pbe;

        // 5. CPQ Quote — all three required lookups populated
        SBQQ__Quote__c quote = new SBQQ__Quote__c(
            SBQQ__Account__c     = acc.Id,
            SBQQ__Opportunity__c = opp.Id,
            SBQQ__PricebookId__c = stdPricebookId,
            SBQQ__Primary__c     = true,
            SBQQ__Status__c      = 'Draft'
        );
        insert quote;

        // 6. Quote Line
        SBQQ__QuoteLine__c ql = new SBQQ__QuoteLine__c(
            SBQQ__Quote__c       = quote.Id,
            SBQQ__Product__c     = prod.Id,
            SBQQ__PricebookEntryId__c = pbe.Id,
            SBQQ__Quantity__c    = 1
        );
        insert ql;
    }

    @isTest
    static void testQuoteLineTriggerSetsCustomField() {
        SBQQ__QuoteLine__c ql = [SELECT Id, My_Custom_Field__c FROM SBQQ__QuoteLine__c LIMIT 1];
        // Assert trigger behavior (not price rule behavior — that requires ServiceRouter)
        System.assertNotEquals(null, ql.My_Custom_Field__c,
            'Custom trigger should have populated My_Custom_Field__c');
    }
}
```

**Why it works:** All three required lookups (`Account`, `Opportunity`, `Pricebook2`) are populated before inserting the quote, satisfying CPQ's internal validation. `Test.getStandardPricebookId()` retrieves the correct pricebook ID for whatever org the test is running in, making the test org-agnostic.

---

## Example 2: ServiceRouter-Based Quote Calculation Test

**Context:** A developer needs to verify that a CPQ price rule sets the `SBQQ__CustomerPrice__c` field to a specific value when `SBQQ__Quantity__c` exceeds 10. The price rule is configured in the CPQ UI (not in Apex), so it can only be tested by invoking the CPQ calculation engine.

**Problem:** The developer writes a test that inserts a quote line with `SBQQ__Quantity__c = 15` and asserts `SBQQ__CustomerPrice__c == 80`. The test passes — but only because the field has a default value; the price rule was never actually evaluated. When someone breaks the price rule configuration, this test continues to pass.

**Solution:**

```apex
@isTest
private class CPQPriceRuleTest {

    @testSetup
    static void setupData() {
        // Same prerequisite pattern as Example 1
        Account acc = new Account(Name = 'Test Account');
        insert acc;

        Opportunity opp = new Opportunity(
            Name      = 'Test Opp',
            AccountId = acc.Id,
            StageName = 'Prospecting',
            CloseDate = Date.today().addDays(30)
        );
        insert opp;

        Id stdPricebookId = Test.getStandardPricebookId();

        Product2 prod = new Product2(Name = 'Enterprise License', IsActive = true);
        insert prod;

        PricebookEntry pbe = new PricebookEntry(
            Pricebook2Id = stdPricebookId,
            Product2Id   = prod.Id,
            UnitPrice    = 100.00,
            IsActive     = true
        );
        insert pbe;

        SBQQ__Quote__c quote = new SBQQ__Quote__c(
            SBQQ__Account__c     = acc.Id,
            SBQQ__Opportunity__c = opp.Id,
            SBQQ__PricebookId__c = stdPricebookId,
            SBQQ__Primary__c     = true,
            SBQQ__Status__c      = 'Draft'
        );
        insert quote;

        SBQQ__QuoteLine__c ql = new SBQQ__QuoteLine__c(
            SBQQ__Quote__c            = quote.Id,
            SBQQ__Product__c          = prod.Id,
            SBQQ__PricebookEntryId__c = pbe.Id,
            SBQQ__Quantity__c         = 15  // quantity > 10 triggers the price rule
        );
        insert ql;
    }

    @isTest
    static void testVolumeDiscountPriceRule() {
        SBQQ__Quote__c quote = [SELECT Id FROM SBQQ__Quote__c LIMIT 1];

        Test.startTest();
        // Invoke the CPQ calculation engine — this is what fires price rules
        // Direct DML on quote lines does NOT fire price rules
        SBQQ.ServiceRouter.calculateQuote(quote.Id);
        Test.stopTest();

        // Re-query after the engine has committed its updates
        SBQQ__QuoteLine__c ql = [
            SELECT SBQQ__CustomerPrice__c
            FROM   SBQQ__QuoteLine__c
            WHERE  SBQQ__Quote__c = :quote.Id
            LIMIT 1
        ];

        // Price rule sets CustomerPrice to 80 when Quantity > 10
        System.assertEquals(80.00, ql.SBQQ__CustomerPrice__c,
            'Volume discount price rule should set CustomerPrice to 80 for Qty > 10');
    }
}
```

**Why it works:** `SBQQ.ServiceRouter.calculateQuote()` triggers the full CPQ calculation engine, including price rule condition evaluation and action execution. `Test.startTest()` / `Test.stopTest()` ensures the async portions of the engine call flush before assertions run. Without the `ServiceRouter` call, this test would be testing nothing meaningful about price rule behavior.

---

## Anti-Pattern: Asserting Price Values After Plain DML

**What practitioners do:** Insert a `SBQQ__QuoteLine__c` with a specific quantity and immediately assert that `SBQQ__CustomerPrice__c` reflects the expected price rule outcome.

**What goes wrong:** The CPQ calculation engine never runs. `SBQQ__CustomerPrice__c` retains whatever default or manually-set value was on the record. The test passes even when the price rule is misconfigured, disabled, or deleted. This gives false confidence and masks real defects until they reach production.

**Correct approach:** Always call `SBQQ.ServiceRouter.calculateQuote(quoteId)` between inserting quote lines and asserting calculated field values. Structure assertions after `Test.stopTest()` to allow the engine's updates to commit.
