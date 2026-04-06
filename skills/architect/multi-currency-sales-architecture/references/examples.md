# Examples — Multi-Currency Sales Architecture

## Example 1: Integrating Daily Dated Exchange Rates via REST API

**Context:** A global manufacturing company has ACM enabled with 12 active currencies. Their corporate treasury system publishes daily exchange rates at 06:00 UTC. Rates must be loaded into Salesforce before the EMEA team starts work.

**Problem:** Without automated rate loading, an admin manually enters rates in Setup. Missed days create gaps in `DatedConversionRate`, causing Salesforce to silently fall back to the static rate. Finance discovers the discrepancy weeks later during month-end reconciliation.

**Solution:**

```apex
// Scheduled Apex that runs daily to verify no DatedConversionRate gaps exist
// The actual rate insert is handled by the integration middleware (MuleSoft/custom)
// This job is the safety net that alerts on missing rates

global class DatedRateGapChecker implements Schedulable {
    global void execute(SchedulableContext sc) {
        Date today = Date.today();
        Date checkFrom = today.addDays(-3); // look back 3 days for gaps

        List<CurrencyType> activeCurrencies = [
            SELECT IsoCode FROM CurrencyType WHERE IsActive = true AND IsCorporate = false
        ];

        Set<String> currenciesWithGaps = new Set<String>();

        for (CurrencyType ct : activeCurrencies) {
            List<DatedConversionRate> rates = [
                SELECT StartDate, NextStartDate
                FROM DatedConversionRate
                WHERE IsoCode = :ct.IsoCode
                  AND StartDate <= :today
                  AND NextStartDate >= :checkFrom
                ORDER BY StartDate DESC
                LIMIT 5
            ];

            if (rates.isEmpty() || rates[0].NextStartDate < today) {
                currenciesWithGaps.add(ct.IsoCode);
            }
        }

        if (!currenciesWithGaps.isEmpty()) {
            // Send alert to finance ops team
            Messaging.SingleEmailMessage mail = new Messaging.SingleEmailMessage();
            mail.setToAddresses(new List<String>{ 'finance-ops@example.com' });
            mail.setSubject('ALERT: Missing Dated Exchange Rates');
            mail.setPlainTextBody(
                'The following currencies have gaps in DatedConversionRate: ' +
                String.join(new List<String>(currenciesWithGaps), ', ')
            );
            Messaging.sendEmail(new List<Messaging.SingleEmailMessage>{ mail });
        }
    }
}
```

**Why it works:** The integration middleware handles rate loading, but this scheduled job acts as a safety net. It queries `DatedConversionRate` to confirm every active currency has coverage through today. If a gap exists — due to a middleware failure or missing source data — finance ops gets an alert before reports go out with wrong conversions.

---

## Example 2: Custom Roll-Up That Respects Dated Exchange Rates

**Context:** An Account page shows a "Total Open Pipeline" roll-up summary of child Opportunities. With ACM enabled, the native roll-up uses the static `CurrencyType` rate, not the dated rate each Opportunity should use based on its CloseDate.

**Problem:** The Account's roll-up shows $1.2M but summing the child Opportunities' ConvertedAmount values yields $1.15M. Finance flags this as a data integrity issue.

**Solution:**

```apex
// Trigger-based approach: recalculate a custom field on Account
// that sums Opportunity amounts using dated-rate-aware conversion

trigger OpportunityAmountSync on Opportunity (after insert, after update, after delete) {
    Set<Id> accountIds = new Set<Id>();

    List<Opportunity> scope = Trigger.isDelete ? Trigger.old : Trigger.new;
    for (Opportunity opp : scope) {
        if (opp.AccountId != null) {
            accountIds.add(opp.AccountId);
        }
    }

    if (Trigger.isUpdate) {
        for (Opportunity opp : Trigger.old) {
            if (opp.AccountId != null) {
                accountIds.add(opp.AccountId);
            }
        }
    }

    // Use ConvertedAmount which already reflects dated rates on Opportunity
    List<AggregateResult> results = [
        SELECT AccountId, SUM(ConvertedAmount) totalConverted
        FROM Opportunity
        WHERE AccountId IN :accountIds
          AND IsClosed = false
        GROUP BY AccountId
    ];

    Map<Id, Decimal> accountTotals = new Map<Id, Decimal>();
    for (AggregateResult ar : results) {
        accountTotals.put((Id) ar.get('AccountId'), (Decimal) ar.get('totalConverted'));
    }

    List<Account> toUpdate = new List<Account>();
    for (Id accId : accountIds) {
        toUpdate.add(new Account(
            Id = accId,
            Total_Open_Pipeline_Converted__c = accountTotals.containsKey(accId)
                ? accountTotals.get(accId) : 0
        ));
    }

    update toUpdate;
}
```

**Why it works:** The `Opportunity.ConvertedAmount` field already uses dated rates when ACM is enabled. By querying `ConvertedAmount` instead of `Amount` and aggregating in Apex, this custom roll-up produces a total that matches what finance sees on individual Opportunity records — unlike the native roll-up summary which uses the static rate.

---

## Anti-Pattern: Storing Converted Amounts Without Recording the Rate Used

**What practitioners do:** They create a trigger that converts `Amount` to corporate currency using a hardcoded or queried current exchange rate and stores it in a custom field — but they do not record which rate was used or when the conversion happened.

**What goes wrong:** When rates change, there is no way to tell whether a stored value reflects the rate at close time, the rate at conversion time, or the current rate. Reconciliation becomes impossible. Finance cannot audit the numbers.

**Correct approach:** When snapshotting converted amounts, always store three values: the original amount, the exchange rate used, and the conversion date. This makes the conversion auditable and reproducible:

```apex
opp.Snapshot_Amount_Corporate__c = opp.Amount * rateUsed;
opp.Snapshot_Exchange_Rate__c = rateUsed;
opp.Snapshot_Conversion_Date__c = Date.today();
```
