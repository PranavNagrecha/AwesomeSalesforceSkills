# Code Examples: Apex Wrapper Class Patterns

Deployable classes, component, tests, and manifest for the wrapper patterns in `SKILL.md`. Narrative examples are in `examples.md`.

## Example 1: Accounts with an open-opportunity count, sortable two ways, for a Lightning web component

**Context:** A component shows Accounts with the number of open Opportunities on each. Users sort by name or by open count.

**Design:** The wrapper is a top-level class because the LWC guide says an inner class as a parameter or return value isn't supported. The controller holds the static `@AuraEnabled` method and the wrapper holds the `@AuraEnabled` properties, because the Aura guide says not to mix the two uses in one class. Comparators are used only inside Apex, so they can be inner classes.

### Wrapper

`force-app/main/default/classes/AccountRow.cls`

```apex
public with sharing class AccountRow implements Comparable {
    // Only public instance properties with @AuraEnabled are serialized to the component.
    // get/set lets the component send the object back as a parameter.
    @AuraEnabled public Id accountId { get; set; }
    @AuraEnabled public String accountName { get; set; }
    @AuraEnabled public String industry { get; set; }
    @AuraEnabled public Integer openOpportunityCount { get; set; }

    public AccountRow() {
    }

    public AccountRow(Account acct, Integer openCount) {
        accountId = acct.Id;
        accountName = acct.Name;
        industry = acct.Industry;
        openOpportunityCount = openCount == null ? 0 : openCount;
    }

    // Natural order: by name, nulls last. The Comparable reference requires explicit null handling.
    public Integer compareTo(Object other) {
        if (other == null) {
            return -1;
        }
        AccountRow that = (AccountRow) other;
        if (accountName == null && that.accountName == null) {
            return 0;
        }
        if (accountName == null) {
            return 1;
        }
        if (that.accountName == null) {
            return -1;
        }
        return accountName.compareTo(that.accountName);
    }
}
```

### Comparators

`force-app/main/default/classes/AccountRowComparators.cls`

```apex
public with sharing class AccountRowComparators {

    // Highest open count first; null rows and null counts last.
    public class ByOpenCountDesc implements Comparator<AccountRow> {
        public Integer compare(AccountRow a, AccountRow b) {
            if (a == null && b == null) {
                return 0;
            }
            if (a == null) {
                return 1;
            }
            if (b == null) {
                return -1;
            }
            Integer x = a.openOpportunityCount == null ? -1 : a.openOpportunityCount;
            Integer y = b.openOpportunityCount == null ? -1 : b.openOpportunityCount;
            if (x == y) {
                return 0;
            }
            return x > y ? -1 : 1;
        }
    }
}
```

### Controller

`force-app/main/default/classes/AccountDashboardController.cls`

```apex
public with sharing class AccountDashboardController {

    @AuraEnabled(cacheable=true)
    public static List<AccountRow> getAccountRows(String sortBy) {
        List<Account> accounts = [
            SELECT Id, Name, Industry
            FROM Account
            WITH USER_MODE
            ORDER BY Name
            LIMIT 200
        ];

        // One aggregate for all accounts: COUNT with GROUP BY uses one query row per group.
        Map<Id, Integer> openCountByAccount = new Map<Id, Integer>();
        for (AggregateResult ar : [
            SELECT AccountId accountId, COUNT(Id) openCount
            FROM Opportunity
            WHERE IsClosed = false AND AccountId IN :accounts
            WITH USER_MODE
            GROUP BY AccountId
        ]) {
            openCountByAccount.put((Id) ar.get('accountId'), (Integer) ar.get('openCount'));
        }

        List<AccountRow> rows = new List<AccountRow>();
        for (Account acct : accounts) {
            rows.add(new AccountRow(acct, openCountByAccount.get(acct.Id)));
        }

        if (sortBy == 'openCount') {
            rows.sort(new AccountRowComparators.ByOpenCountDesc());
        } else {
            rows.sort(); // AccountRow.compareTo: by name
        }
        return rows;
    }
}
```

### Test class

`force-app/main/default/classes/AccountDashboardControllerTest.cls`

```apex
@IsTest
private class AccountDashboardControllerTest {

    @TestSetup
    static void setup() {
        List<Account> accounts = new List<Account>{
            new Account(Name = 'Wrapper Alpha'),
            new Account(Name = 'Wrapper Beta')
        };
        insert accounts;
        List<Opportunity> opps = new List<Opportunity>();
        for (Integer i = 0; i < 3; i++) {
            opps.add(new Opportunity(Name = 'Beta Open ' + i, AccountId = accounts[1].Id,
                StageName = 'Prospecting', CloseDate = Date.today().addDays(30)));
        }
        opps.add(new Opportunity(Name = 'Alpha Open', AccountId = accounts[0].Id,
            StageName = 'Prospecting', CloseDate = Date.today().addDays(30)));
        opps.add(new Opportunity(Name = 'Alpha Won', AccountId = accounts[0].Id,
            StageName = 'Closed Won', CloseDate = Date.today()));
        insert opps;
    }

    @IsTest
    static void sortsByOpenCountDescending() {
        Test.startTest();
        List<AccountRow> rows = AccountDashboardController.getAccountRows('openCount');
        Test.stopTest();
        System.assertEquals('Wrapper Beta', rows[0].accountName, 'most open opportunities first');
        System.assertEquals(3, rows[0].openOpportunityCount);
        System.assertEquals(1, rows[1].openOpportunityCount, 'closed opportunity not counted');
    }

    @IsTest
    static void sortsByNameByDefault() {
        List<AccountRow> rows = AccountDashboardController.getAccountRows(null);
        System.assertEquals('Wrapper Alpha', rows[0].accountName);
    }

    @IsTest
    static void comparatorsHandleNulls() {
        AccountRow blankName = new AccountRow();
        blankName.openOpportunityCount = null;
        AccountRow named = new AccountRow(new Account(Name = 'Zeta'), 5);

        List<AccountRow> byCount = new List<AccountRow>{ blankName, null, named };
        byCount.sort(new AccountRowComparators.ByOpenCountDesc());
        System.assertEquals(named, byCount[0], 'highest count first');
        System.assertEquals(null, byCount[2], 'null row last');

        List<AccountRow> byName = new List<AccountRow>{ blankName, named };
        byName.sort();
        System.assertEquals('Zeta', byName[0].accountName, 'null name sorts last');
    }
}
```

### Component

`force-app/main/default/lwc/accountDashboard/accountDashboard.js`

```javascript
import { LightningElement, wire } from 'lwc';
import getAccountRows from '@salesforce/apex/AccountDashboardController.getAccountRows';

export default class AccountDashboard extends LightningElement {
    sortBy = 'name';

    @wire(getAccountRows, { sortBy: '$sortBy' })
    accountRows;

    handleSortByCount() {
        this.sortBy = 'openCount';
    }
}
```

`force-app/main/default/lwc/accountDashboard/accountDashboard.html`

```html
<template>
    <lightning-button label="Sort by open opportunities" onclick={handleSortByCount}></lightning-button>
    <template lwc:if={accountRows.data}>
        <template for:each={accountRows.data} for:item="row">
            <div key={row.accountId}>{row.accountName}: {row.openOpportunityCount} open</div>
        </template>
    </template>
</template>
```

`force-app/main/default/lwc/accountDashboard/accountDashboard.js-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <isExposed>true</isExposed>
    <targets>
        <target>lightning__AppPage</target>
    </targets>
</LightningComponentBundle>
```

### package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>AccountRow</members>
        <members>AccountRowComparators</members>
        <members>AccountDashboardController</members>
        <members>AccountDashboardControllerTest</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>accountDashboard</members>
        <name>LightningComponentBundle</name>
    </types>
    <version>67.0</version>
</Package>
```

Each class also needs its `.cls-meta.xml` with `<apiVersion>67.0</apiVersion>` and `<status>Active</status>`.

**Why it works:** The component receives a supported top-level type with only the annotated properties. One aggregate query feeds all rows. Both sort orders handle null rows and null keys, as the Comparable and Comparator references require. The parameter to `@wire` is passed as an object whose property matches the Apex parameter name, as the LWC guide describes.
