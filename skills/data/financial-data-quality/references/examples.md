# Examples — Financial Data Quality

## Example 1: Blocking Duplicate FinancialAccount Records During Core Banking Integration Load

**Context:** A wealth management firm integrates their core banking system with FSC using a nightly Bulk API load that creates or updates `FinancialAccount` records. After several months, advisors begin reporting that some clients show duplicate financial accounts — the same investment account appearing twice with different balances. An investigation reveals the banking system occasionally sends the same account with a slightly different external account number format (e.g., leading zeros stripped).

**Problem:** The team attempts to configure a standard Duplicate Rule for `FinancialAccount` in Setup. The configuration wizard offers no option to select `FinancialAccount` as the target object — only Account, Contact, and Lead are available. Standard Duplicate Rules have no Matching Rule support for FSC financial objects. No duplicate blocking is in place, so the integration continues to create duplicate records silently.

**Solution:**

Implement a bulk-safe Apex before-insert trigger on `FinancialAccount` that normalizes the external account number and checks for existing records:

```apex
trigger FinancialAccountDuplicateCheck on FinancialAccount (before insert) {
    // Normalize external IDs — strip leading zeros for consistent comparison
    Map<String, FinancialAccount> incomingByNormalizedId = new Map<String, FinancialAccount>();
    for (FinancialAccount fa : Trigger.new) {
        if (fa.ExternalAccountNumber__c != null) {
            String normalized = fa.ExternalAccountNumber__c.replaceAll('^0+', '');
            incomingByNormalizedId.put(normalized, fa);
        }
    }

    if (incomingByNormalizedId.isEmpty()) return;

    // Single SOQL query for the entire batch — bulk-safe
    List<FinancialAccount> existing = [
        SELECT Id, ExternalAccountNumber__c, Name, OwnerId
        FROM FinancialAccount
        WHERE ExternalAccountNumber__c IN :incomingByNormalizedId.keySet()
    ];

    Map<String, FinancialAccount> existingByNormalizedId = new Map<String, FinancialAccount>();
    for (FinancialAccount ea : existing) {
        String normalized = ea.ExternalAccountNumber__c.replaceAll('^0+', '');
        existingByNormalizedId.put(normalized, ea);
    }

    // Flag duplicates on the incoming records
    for (FinancialAccount fa : Trigger.new) {
        if (fa.ExternalAccountNumber__c == null) continue;
        String normalized = fa.ExternalAccountNumber__c.replaceAll('^0+', '');
        if (existingByNormalizedId.containsKey(normalized)) {
            FinancialAccount dup = existingByNormalizedId.get(normalized);
            fa.addError(
                'Duplicate FinancialAccount: normalized ExternalAccountNumber '
                + normalized
                + ' already exists on record ' + dup.Id
                + ' (' + dup.Name + '). '
                + 'Investigate the source system feed for account number format inconsistencies.'
            );
        }
    }
}
```

**Why it works:** Standard Duplicate Rules are unsupported for `FinancialAccount`. The trigger fires before the record is committed to the database (`before insert`), allowing `addError()` to abort the insert. Processing all records in `Trigger.new` in a single SOQL query (not inside a for-loop) keeps the logic within governor limits even during bulk loads of thousands of records. Normalizing the external account number before comparison handles the leading-zero formatting variation that caused the original duplicates.

---

## Example 2: Detecting Stale Household KPIs After FSC Rollup Batch Failure

**Context:** A retail bank runs FSC for its branch advisory model. Household Account records display aggregated KPIs (Total Assets Under Management, Total Liabilities, Net Worth) computed by the FSC rollup batch. A production deployment on a Friday evening disrupts the scheduled rollup batch. By Monday morning, advisors notice household totals are wrong — several households show balances from three days prior. There is no alert in FSC Settings visible to advisors; the stale values appear as current data.

**Problem:** The FSC rollup batch failed silently after the deployment. No platform alert fired. The batch does not self-heal or retry automatically. Advisors who relied on household KPIs for Monday morning client calls had incorrect financial summaries. The operations team was unaware of the failure until advisors escalated.

**Solution:**

1. Implement a custom `Rollup_Audit__c` object with a `Last_Successful_Run__c` DateTime field. A Flow or Apex post-processing step updates this record after each successful rollup batch completion.

2. Deploy a scheduled Apex health monitor that checks the audit timestamp and alerts operations if the rollup has not completed within the expected window:

```apex
global class FSCRollupHealthMonitor implements Schedulable {
    // Expected rollup interval in hours — set to match your FSC rollup schedule
    @TestVisible static Integer ALERT_THRESHOLD_HOURS = 25;

    global void execute(SchedulableContext sc) {
        List<Rollup_Audit__c> audits = [
            SELECT Last_Successful_Run__c
            FROM Rollup_Audit__c
            ORDER BY Last_Successful_Run__c DESC
            LIMIT 1
        ];

        if (audits.isEmpty()) {
            sendAlert('FSC Rollup Audit record not found — rollup monitoring is not configured.');
            return;
        }

        DateTime threshold = DateTime.now().addHours(-ALERT_THRESHOLD_HOURS);
        if (audits[0].Last_Successful_Run__c == null
                || audits[0].Last_Successful_Run__c < threshold) {
            sendAlert(
                'FSC rollup batch overdue. Last successful run: '
                + (audits[0].Last_Successful_Run__c != null
                    ? audits[0].Last_Successful_Run__c.format()
                    : 'NEVER')
                + '. Threshold: ' + ALERT_THRESHOLD_HOURS + ' hours. '
                + 'Go to FSC Settings > Rollup Configuration to check status and trigger a re-run.'
            );
        }
    }

    private static void sendAlert(String message) {
        Messaging.SingleEmailMessage email = new Messaging.SingleEmailMessage();
        email.setToAddresses(new List<String>{ 'sfops@example.com' });
        email.setSubject('[ALERT] FSC Rollup Batch Health Check Failed');
        email.setPlainTextBody(message);
        Messaging.sendEmail(new List<Messaging.SingleEmailMessage>{ email });
    }
}
```

3. To recover from a failed rollup, navigate to **FSC Settings > Rollup Configuration > Run Rollups Now** in the Salesforce Setup UI, or trigger the rollup programmatically via Apex if your org version supports it. After the re-run completes, verify that household Account rollup fields (`TotalAssets`, `TotalLiabilities`, `NetWorth`) reflect current `FinancialAccount` values.

**Why it works:** The FSC rollup batch exposes no native alerting. The audit record + scheduled monitor fills this operational gap. Scheduling the monitor to run hourly (or at the same frequency as the rollup batch) catches failures within one batch interval rather than waiting for advisors to notice and escalate. The monitor is stateless — it reads a single record and sends a conditional email — keeping it within all governor limits and maintainable by any admin.

---

## Example 3: RecordType-Scoped Validation Rule for FinancialAccount with Integration Bypass

**Context:** An insurance FSC org requires that all life insurance `FinancialAccount` records carry a policy number (`PolicyNumber__c`) and a coverage start date (`CoverageStartDate__c`). These fields are irrelevant for bank and investment account types. The integration team loads `FinancialAccount` records from a policy administration system overnight and needs to bypass the validation during bulk load to avoid failures on records with missing data that will be populated by a subsequent update job.

**Problem:** Making `PolicyNumber__c` universally required blocks creation of bank and investment `FinancialAccount` records where the field is not applicable. Removing the requirement entirely allows invalid insurance records to be created through the UI.

**Solution:**

Validation rule formula on `FinancialAccount`:
```
AND(
    NOT($Permission.Bypass_FSC_Validation),
    ISPICKVAL(RecordType.DeveloperName, 'InsurancePolicy'),
    OR(
        ISBLANK(PolicyNumber__c),
        ISBLANK(CoverageStartDate__c)
    )
)
```

Error message: `Insurance policy FinancialAccount records require both a Policy Number and a Coverage Start Date.`

Steps:
1. Create a Custom Permission named `Bypass_FSC_Validation` in Setup.
2. Create a Permission Set `FSC_Integration_Bypass` and assign the Custom Permission to it.
3. Assign the Permission Set to the integration service account user only.
4. The validation rule fires on UI saves and API saves by non-integration users. Integration loads with the `FSC_Integration_Bypass` Permission Set skip the rule.

**Why it works:** The `RecordType.DeveloperName` guard restricts the rule to insurance policy records only. The `NOT($Permission.Bypass_FSC_Validation)` wrapper allows the integration service user to bypass without requiring System Administrator access. The combination enforces the business rule in the UI while keeping the integration load path clean. This is the canonical FSC validation rule pattern from the Financial Services Cloud Admin Guide.

---

## Anti-Pattern: Applying a Standard Duplicate Rule to FinancialAccount

**What practitioners do:** In Salesforce Setup, navigate to Duplicate Management > Duplicate Rules > New Rule. Select `FinancialAccount` as the object to protect. Expect standard behavior — a Matching Rule compares incoming records against existing ones and blocks or alerts on matches.

**What goes wrong:** The Setup wizard will not allow `FinancialAccount` to be selected as the protected object for a standard Duplicate Rule. Only Account, Contact, and Lead are supported. If a practitioner finds a workaround or third-party tool to partially configure something resembling a duplicate rule for `FinancialAccount`, it will not have the same platform-enforced behavior and will not fire reliably. Standard Matching Rules have no supported configuration for FSC financial objects.

**Correct approach:** Implement duplicate detection as a `before insert` Apex trigger on `FinancialAccount` (or `FinServ__FinancialAccount__c`). Use a business-key field (external account number, owner + account type combination, or ISIN/CUSIP for investment holdings) as the deduplication key. Ensure the trigger is bulk-safe — collect all keys into a Set, run one SOQL query per trigger execution, and check results in memory. See Example 1 above for a complete implementation.
