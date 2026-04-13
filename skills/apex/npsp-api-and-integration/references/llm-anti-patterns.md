# LLM Anti-Patterns — NPSP API and Integration

Common mistakes AI coding assistants make when generating or advising on NPSP API and Integration.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Inserting Opportunities Directly Instead of Routing Through BDI

**What the LLM generates:** Apex code that creates `Opportunity` and `npe01__OppPayment__c` records directly via `insert` statements when processing external gift data.

**Why it happens:** Direct DML insert is the most common Salesforce data creation pattern. LLMs apply this by default without knowing that NPSP's gift processing pipeline (allocations, soft credits, rollups) requires the BDI staging approach.

**Correct pattern:**

```apex
// WRONG: Direct Opportunity insert bypasses NPSP processing
Opportunity opp = new Opportunity(
    Name = 'Test Gift',
    Amount = 100.00,
    CloseDate = Date.today(),
    StageName = 'Closed Won',
    AccountId = accountId
);
insert opp;

// CORRECT: Route through DataImport__c and BDI API
npsp__DataImport__c di = new npsp__DataImport__c(
    npsp__Contact1_Firstname__c = 'Jane',
    npsp__Contact1_Lastname__c  = 'Doe',
    npsp__Donation_Amount__c    = 100.00,
    npsp__Donation_Date__c      = Date.today(),
    npsp__Donation_Stage__c     = 'Closed Won'
);
insert di;
npsp.BDI_DataImport_API.processDataImportRecords(
    new npsp.BDI_DataImport_API.BDIImportSettings(), 
    new List<npsp__DataImport__c>{ di }, false
);
```

**Detection hint:** Any Apex that creates `Opportunity` records in an NPSP integration context without referencing `npsp__DataImport__c` or `BDI_DataImport_API` is a flag.

---

## Anti-Pattern 2: Confusing RD2 Installments API with Opportunity Creation

**What the LLM generates:** Code that calls `RD2_ApiService.getInstallments()` and then queries for the resulting Opportunity records, or code that expects calling getInstallments() to create Opportunity records.

**Why it happens:** The method name "getInstallments" sounds like it retrieves or creates installment records. LLMs generate follow-up queries expecting records to exist.

**Correct pattern:**

```apex
// WRONG: getInstallments() does NOT create Opportunities
List<npsp.RD2_ApiService.Installment> projected = 
    npsp.RD2_ApiService.getInstallments(rdId, 12);
// These are projections ONLY — no Opportunity records are created
// The following query will return 0 results for future-dated installments
// that have not yet been created by the batch job:
List<Opportunity> opps = [SELECT Id FROM Opportunity 
                          WHERE npe03__Recurring_Donation__c = :rdId 
                          AND CloseDate > TODAY];

// CORRECT: use getInstallments() for display-only projections
// Use Opportunity SOQL for actual persisted installment records
// Future Opportunities are created by RD2_OpportunityEvaluation_BATCH on schedule
```

**Detection hint:** Any code that calls `getInstallments()` followed by an Opportunity SOQL expecting the API call to have created records is a flag.

---

## Anti-Pattern 3: Designing Wealth Screening as a Custom Apex HTTP Callout

**What the LLM generates:** Custom Apex code using `HttpRequest` to call iWave, DonorSearch, or Windfall APIs directly, writing results to custom Contact fields.

**Why it happens:** HTTP callout to a vendor API is a common Salesforce integration pattern. LLMs generate it without knowing that all major wealth screening vendors have AppExchange managed packages.

**Correct pattern:**

```text
Wealth screening integration approach:
1. Confirm the vendor has an AppExchange managed package:
   - iWave: AppExchange iWave for Salesforce
   - DonorSearch: AppExchange DonorSearch for Salesforce
   - Windfall: AppExchange Windfall

2. Install the vendor's managed package
3. Configure the API connection in the package settings (API key)
4. Use the package's built-in batch screen or Lightning component
5. Vendor package writes scores to managed package custom fields on Contact/Account

Custom HTTP callout is unnecessary and creates maintenance burden.
Only build custom callout if the vendor has no AppExchange offering.
```

**Detection hint:** Any custom Apex `HttpRequest` targeting a wealth screening vendor URL (iwave.com, donorsearch.net, windfall.com) should be flagged for AppExchange package availability check.

---

## Anti-Pattern 4: Missing Failure Handling on BDI Processing

**What the LLM generates:** BDI integration code that inserts DataImport records and calls BDI processing without checking `npsp__Status__c` or `npsp__FailureInformation__c` on the processed records.

**Why it happens:** LLMs generate the happy-path integration code and omit error handling as a subsequent concern. In production, BDI failures on individual records silently result in missing gifts with no notification.

**Correct pattern:**

```apex
// After BDI processing, always check for failures
List<npsp__DataImport__c> processedRecords = [
    SELECT npsp__Status__c, npsp__FailureInformation__c,
           npsp__DonationImported__c, npsp__Contact1Imported__c
    FROM npsp__DataImport__c WHERE Id IN :importIds
];

List<String> failures = new List<String>();
for (npsp__DataImport__c di : processedRecords) {
    if (di.npsp__Status__c == 'Failed') {
        failures.add(di.Id + ': ' + di.npsp__FailureInformation__c);
    }
}

if (!failures.isEmpty()) {
    // Send failure alert email to integration admin
    // Write to error log object
    // Do NOT re-process without investigating root cause
}
```

**Detection hint:** Any BDI integration that does not query `npsp__FailureInformation__c` after processing is incomplete.

---

## Anti-Pattern 5: Omitting CRLP Recalculation After Bulk Import

**What the LLM generates:** Bulk BDI import code that processes gifts successfully but does not include a step to trigger CRLP (Customizable Rollups) recalculation.

**Why it happens:** LLMs are unaware of NPSP's batch-driven rollup architecture. The assumption is that Salesforce rollups update in real-time, as they do for standard formula and rollup summary fields.

**Correct pattern:**

```apex
// After large bulk BDI import, trigger CRLP recalculation
// Option 1: Programmatic batch trigger
Database.executeBatch(new CRLP_RollupBatch_SVC.BatchData(), 200);

// Option 2: Via NPSP Settings UI
// NPSP Settings > Batch Processing > Recalculate All Rollups

// Option 3: Schedule post-import recalculation
System.scheduleBatch(new CRLP_RollupBatch_SVC.BatchData(), 
    'Post-Import CRLP Recalc', 0); // run immediately

// Document this step in the integration runbook:
// "After any bulk import of 100+ gifts, trigger CRLP recalculation.
// Household TotalGifts and LargestGift will not reflect the import until
// the next scheduled CRLP batch run (typically nightly)."
```

**Detection hint:** Any bulk BDI import procedure that ends with "done" without a CRLP recalculation step should be flagged.
