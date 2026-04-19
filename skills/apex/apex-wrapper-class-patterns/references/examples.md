# Examples — Apex Wrapper Class Patterns

## Example 1: Account + Open Opportunity Count Wrapper for LWC

**Context:** A Lightning Web Component dashboard needs to show a table of Accounts alongside the count of open Opportunities for each Account. There is no formula field for this count on Account because it depends on a `StageName != 'Closed Won'` filter that DLRS or roll-up summary fields cannot express simply.

**Problem:** Returning a plain `List<Account>` gives only the SObject fields. Returning `AggregateResult` gives counts but loses Account field access. The component would need two separate wire calls and client-side join logic.

**Solution:**

```apex
/**
 * AccountDashboardController
 * Inner class pattern — wrapper lives only in heap, no schema footprint.
 * Outer class declared with sharing so SOQL respects record visibility.
 */
public with sharing class AccountDashboardController {

    /**
     * Wrapper that combines an Account record with a computed open-opp count.
     * @AuraEnabled on every field the LWC template needs to read.
     * Fields without @AuraEnabled are invisible to the JavaScript client.
     */
    public class AccountRow {
        @AuraEnabled public Id accountId;
        @AuraEnabled public String accountName;
        @AuraEnabled public String industry;
        @AuraEnabled public Integer openOpportunityCount;

        public AccountRow(Account acct, Integer oppCount) {
            this.accountId = acct.Id;
            this.accountName = acct.Name;
            this.industry = acct.Industry;
            this.openOpportunityCount = oppCount;
        }
    }

    /**
     * Returns a list of AccountRow instances for LWC wire consumption.
     * cacheable=true is required for @wire; use plain @AuraEnabled for imperative.
     */
    @AuraEnabled(cacheable=true)
    public static List<AccountRow> getAccountRows() {
        // Step 1: Query Accounts (sharing enforced by outer class declaration)
        List<Account> accounts = [
            SELECT Id, Name, Industry
            FROM Account
            WHERE IsDeleted = FALSE
            LIMIT 200
        ];

        // Step 2: Aggregate open Opportunity counts grouped by AccountId
        Map<Id, Integer> openOppCountByAccountId = new Map<Id, Integer>();
        for (AggregateResult ar : [
            SELECT AccountId, COUNT(Id) cnt
            FROM Opportunity
            WHERE StageName != 'Closed Won'
              AND AccountId IN :accounts
            GROUP BY AccountId
        ]) {
            openOppCountByAccountId.put(
                (Id) ar.get('AccountId'),
                (Integer) ar.get('cnt')
            );
        }

        // Step 3: Assemble wrappers — no DML inside constructor
        List<AccountRow> rows = new List<AccountRow>();
        for (Account acct : accounts) {
            Integer cnt = openOppCountByAccountId.containsKey(acct.Id)
                ? openOppCountByAccountId.get(acct.Id)
                : 0;
            rows.add(new AccountRow(acct, cnt));
        }
        return rows;
    }
}
```

**LWC usage sketch:**

```javascript
// accountDashboard.js
import getAccountRows from '@salesforce/apex/AccountDashboardController.getAccountRows';
import { wire } from 'lwc';

export default class AccountDashboard extends LightningElement {
    @wire(getAccountRows)
    accountRows;
}
```

```html
<!-- accountDashboard.html -->
<template>
    <template for:each={accountRows.data} for:item="row">
        <div key={row.accountId}>
            {row.accountName} — Open Opps: {row.openOpportunityCount}
        </div>
    </template>
</template>
```

**Why it works:** Every field referenced in the HTML template (`accountId`, `accountName`, `openOpportunityCount`) carries `@AuraEnabled`. The platform serializes the wrapper list to JSON automatically — no explicit `JSON.serialize()` needed. The outer-class `with sharing` declaration ensures the Account query respects record-level security; the inner class's own execution context is system mode but the SOQL runs through the outer class method.

---

## Example 2: Multi-Strategy List Sort with Comparator (Spring '24+ / API v60+)

**Context:** A service layer builds a list of `OpportunityWrapper` objects and must sort them in different ways depending on the calling context: by close date ascending for a pipeline view, or by amount descending for a revenue view. Only one sort order can be baked into a `Comparable` implementation.

**Problem:** Using `Comparable` alone forces either (a) adding a static flag to the wrapper to toggle sort direction (fragile in multi-threaded-style patterns) or (b) creating two separate wrapper classes. Neither is clean.

**Solution using `Comparator<T>` (API v60+ required):**

```apex
/**
 * OpportunityWrapper with two interchangeable Comparator strategies.
 * Saved at API version 60.0 or higher — Comparator interface requires Spring '24+.
 */
public with sharing class OpportunityService {

    public class OpportunityWrapper {
        @AuraEnabled public Id opportunityId;
        @AuraEnabled public String name;
        @AuraEnabled public Date closeDate;
        @AuraEnabled public Decimal amount;

        public OpportunityWrapper(Opportunity opp) {
            this.opportunityId = opp.Id;
            this.name = opp.Name;
            this.closeDate = opp.CloseDate;
            this.amount = opp.Amount;
        }
    }

    /**
     * Sorts by CloseDate ascending (nulls sort last).
     */
    public class CloseDateAscComparator implements Comparator<OpportunityWrapper> {
        public Integer compare(OpportunityWrapper o1, OpportunityWrapper o2) {
            // Null-safe: treat null closeDate as "infinitely far in the future"
            if (o1.closeDate == null && o2.closeDate == null) return 0;
            if (o1.closeDate == null) return 1;
            if (o2.closeDate == null) return -1;
            if (o1.closeDate < o2.closeDate) return -1;
            if (o1.closeDate > o2.closeDate) return 1;
            return 0;
        }
    }

    /**
     * Sorts by Amount descending (nulls sort last).
     */
    public class AmountDescComparator implements Comparator<OpportunityWrapper> {
        public Integer compare(OpportunityWrapper o1, OpportunityWrapper o2) {
            Decimal a1 = o1.amount == null ? -1 : o1.amount;
            Decimal a2 = o2.amount == null ? -1 : o2.amount;
            if (a1 > a2) return -1;
            if (a1 < a2) return 1;
            return 0;
        }
    }

    /**
     * Returns sorted wrappers; the sort strategy is caller-supplied.
     * Example usages:
     *   OpportunityService.getSorted(new CloseDateAscComparator())
     *   OpportunityService.getSorted(new AmountDescComparator())
     */
    @AuraEnabled(cacheable=true)
    public static List<OpportunityWrapper> getSorted(String sortMode) {
        List<Opportunity> opps = [
            SELECT Id, Name, CloseDate, Amount
            FROM Opportunity
            WHERE IsClosed = FALSE
        ];

        List<OpportunityWrapper> rows = new List<OpportunityWrapper>();
        for (Opportunity o : opps) {
            rows.add(new OpportunityWrapper(o));
        }

        if (sortMode == 'amount') {
            rows.sort(new AmountDescComparator());
        } else {
            rows.sort(new CloseDateAscComparator());
        }
        return rows;
    }
}
```

**Why it works:** Each `Comparator` class handles nulls explicitly, preventing `NullPointerException` during `List.sort()`. The `OpportunityWrapper` itself is not modified when a new sort strategy is added — only a new comparator class is created. The `Comparator<T>` generic binding enforces type safety at compile time (API v60+).

---

## Anti-Pattern: Missing @AuraEnabled on Wrapper Fields

**What practitioners do:** Annotate the Apex method with `@AuraEnabled` but forget to annotate the individual fields on the wrapper class.

**What goes wrong:** The LWC component receives the array of wrapper objects but every property reads as `undefined` in JavaScript. No compile-time error is thrown. The component silently renders nothing, and debugging leads to a confusing "undefined is not an object" error in the browser console.

**Correct approach:** Place `@AuraEnabled` on both the method and every field of the wrapper that the component template references. Properties not needed by the client should be omitted from the annotation to minimize the serialization payload.
