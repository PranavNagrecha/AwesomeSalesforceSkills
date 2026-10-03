# Examples: Multi Currency And Advanced Currency Management

Deployable settings metadata and the exchange-rate REST call are in `metadata-examples.md`. This file holds the Apex worked example.

## Example 1: Return amounts with their currency from code that runs in any org

**Context:** A service returns Opportunity amounts to an external system. The same class ships to orgs with and without multi-currency.

**File:** `force-app/main/default/classes/CurrencyAwareAmountService.cls`

```apex
public with sharing class CurrencyAwareAmountService {

    public class Money {
        public Decimal amount;
        public String isoCode;
        Money(Decimal amount, String isoCode) {
            this.amount = amount;
            this.isoCode = isoCode;
        }
    }

    // Each amount travels with the currency it is stored in.
    // Dynamic SOQL keeps the class valid in single-currency orgs, where CurrencyIsoCode does not exist.
    public static Map<Id, Money> amountsWithCurrency(Set<Id> opportunityIds) {
        Map<Id, Money> result = new Map<Id, Money>();
        if (opportunityIds == null || opportunityIds.isEmpty()) {
            return result;
        }
        Boolean multiCurrency = UserInfo.isMultiCurrencyOrganization();
        String soql = 'SELECT Id, Amount' + (multiCurrency ? ', CurrencyIsoCode' : '')
            + ' FROM Opportunity WHERE Id IN :opportunityIds';
        List<SObject> rows = Database.queryWithBinds(
            soql,
            new Map<String, Object>{ 'opportunityIds' => opportunityIds },
            AccessLevel.USER_MODE
        );
        for (SObject row : rows) {
            String isoCode = multiCurrency
                ? (String) row.get('CurrencyIsoCode')
                : UserInfo.getDefaultCurrency();
            result.put(row.Id, new Money((Decimal) row.get('Amount'), isoCode));
        }
        return result;
    }
}
```

**File:** `force-app/main/default/classes/CurrencyAwareAmountServiceTest.cls`

```apex
@IsTest
private class CurrencyAwareAmountServiceTest {

    @IsTest
    static void everyAmountCarriesACurrency() {
        Account acct = new Account(Name = 'Currency Test Account');
        insert acct;
        List<Opportunity> opps = new List<Opportunity>();
        for (Integer i = 0; i < 200; i++) {
            opps.add(new Opportunity(
                Name = 'Currency Opp ' + i,
                AccountId = acct.Id,
                StageName = 'Prospecting',
                CloseDate = Date.today().addDays(30),
                Amount = 1000 + i
            ));
        }
        insert opps;
        Set<Id> ids = new Map<Id, Opportunity>(opps).keySet();

        Test.startTest();
        Map<Id, CurrencyAwareAmountService.Money> result = CurrencyAwareAmountService.amountsWithCurrency(ids);
        Test.stopTest();

        System.assertEquals(200, result.size(), 'one entry per opportunity');
        for (CurrencyAwareAmountService.Money m : result.values()) {
            System.assertNotEquals(null, m.isoCode, 'no bare decimals');
            System.assertNotEquals(null, m.amount, 'amount returned');
        }
    }

    @IsTest
    static void emptyInputReturnsEmptyMap() {
        System.assertEquals(0, CurrencyAwareAmountService.amountsWithCurrency(new Set<Id>()).size());
        System.assertEquals(0, CurrencyAwareAmountService.amountsWithCurrency(null).size());
    }
}
```

Each class needs its `-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

package.xml members: `CurrencyAwareAmountService` and `CurrencyAwareAmountServiceTest` under `<name>ApexClass</name>`.

**Why it works:** `UserInfo.isMultiCurrencyOrganization()` and `getDefaultCurrency()` behave as the Apex Reference Guide (262) describes, and `CurrencyIsoCode` is "available only for orgs with the multicurrency feature enabled" (Object Reference). The `StageName` value assumes the default sales process; change it if the org's picklist differs. For bigger test data sets, the shared factory is `templates/apex/tests/TestDataFactory.cls`.

---

## Anti-Pattern: Hardcoded currency math

**What practitioners do:** Multiply or divide amounts by a hardcoded rate or assume USD in Apex.

**What goes wrong:** The logic breaks as soon as records or users span currencies, or rates change.

**Correct approach:** Keep the ISO code with the amount, use `convertCurrency()` where the viewer's currency is wanted, and read rates from `CurrencyType` (static) or `DatedConversionRate` (ACM) with dynamic SOQL when code must run in any org.
