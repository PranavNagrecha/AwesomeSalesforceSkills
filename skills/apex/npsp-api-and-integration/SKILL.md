---
name: npsp-api-and-integration
description: "NPSP programmatic integration patterns: BDI gift processing API for bulk gift ingestion, ERD Schedules and Installments API for recurring donation data, and wealth screening integration via AppExchange managed packages. NOT for standard Salesforce REST/BULK API, NPSP PMM integration, or Nonprofit Cloud (NPC) native API patterns."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Security
triggers:
  - "how do I integrate gift data into NPSP without breaking allocation and soft credit logic"
  - "building a gift processing integration with NPSP BDI DataImport API"
  - "how to use NPSP recurring donation API to get projected installment schedules"
  - "wealth screening integration with NPSP iWave or DonorSearch"
  - "inserting opportunities directly into NPSP breaking household rollups"
tags:
  - npsp
  - bdi
  - bulk-data-import
  - recurring-donations
  - integration
  - gift-processing
  - apex
inputs:
  - "Integration source system (payment processor, event platform, wealth screening tool)"
  - "Gift data structure (one-time, recurring, matching, in-kind)"
  - "Whether NPSP Enhanced Recurring Donations (ERD) is enabled"
  - "Whether Salesforce Elevate or a third-party payment gateway is in use"
outputs:
  - "BDI DataImport__c field mapping for gift integration"
  - "Apex or API integration code using BDI_DataImport_API"
  - "ERD Schedule and Installment API usage examples"
  - "Wealth screening integration architecture"
dependencies:
  - npsp-trigger-framework-extension
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-13
---

# NPSP API and Integration

This skill activates when a developer needs to build integrations with NPSP's gift processing pipeline — including the BDI (Bulk Data Import) API for gift ingestion, the Enhanced Recurring Donation Schedule and Installment APIs, or wealth screening tool integration. It does NOT cover standard Salesforce REST API, NPSP PMM integration, or Nonprofit Cloud native API patterns.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Direct Opportunity insert bypasses NPSP** — The most critical rule: never insert Opportunity and npe01__OppPayment__c records directly via Data Loader or REST API. This bypasses NPSP's BDI pipeline, silently skipping GAU allocations, soft credits, household rollup calculations, and Salesforce Elevate payment linkage.
- **BDI is the canonical gift processing API** — All gift integrations must route through `npsp__DataImport__c` staging records and invoke `BDI_DataImport_API`. This is NPSP's prescribed integration surface.
- **ERD API distinction** — The Enhanced Recurring Donation API exposes two separate Apex-invocable methods: the **RD2 Schedules API** (returns projected schedule as JSON) and the **RD2 Installments API** (returns calculated future installments as a list). Installment records are NOT persisted Opportunity records — they are calculated projections.
- **Wealth screening has no native API** — There is no built-in NPSP wealth screening API. iWave, DonorSearch, and similar tools integrate via AppExchange managed packages that write scores to custom fields on Contact/Account.

---

## Core Concepts

### BDI Gift Processing Pipeline

NPSP's Bulk Data Import (BDI) framework is the prescribed gift processing integration surface. The flow is:

1. Integration inserts records into `npsp__DataImport__c` (the staging object)
2. Integration invokes `BDI_DataImport_API.process()` or the standard NPSP Data Import batch job
3. BDI processes each staging record: creates/matches Contact, Household Account, Opportunity, Payment, GAU Allocations, and Opportunity Contact Roles (soft credits)
4. Processed DataImport records have `npsp__Status__c = 'Imported'` (or 'Failed' with error detail)

Key BDI staging fields:
- `npsp__Contact1_Firstname__c`, `npsp__Contact1_Lastname__c`, `npsp__Contact1_Email__c` — primary donor
- `npsp__Donation_Amount__c`, `npsp__Donation_Date__c`, `npsp__Donation_Stage__c` — gift data
- `npsp__Donation_Campaign_Name__c` — campaign attribution
- `npsp__Payment_Method__c` — payment method
- `npsp__GAU_Allocation_1_General_Accounting_Unit__c`, `npsp__GAU_Allocation_1_Amount__c` — fund allocation
- `npsp__Contact2_Firstname__c`, etc. — soft credit recipient

Advanced Mapping must be enabled in NPSP Settings to map custom fields on Opportunity or Payment.

### ERD Schedules and Installments APIs

Enhanced Recurring Donations exposes two Apex-invocable APIs:

**RD2 Schedules API:** Returns the active schedule for a recurring donation as JSON. Useful for displaying projected payment amounts and dates to donors.
```apex
String scheduleJson = npsp.RD2_ApiService.getSchedules(rdId);
```

**RD2 Installments API:** Returns a list of projected future installment records (not persisted Opportunities). Useful for cash flow projections and displaying upcoming payment expectations.
```apex
List<npsp.RD2_ApiService.Installment> installments = 
    npsp.RD2_ApiService.getInstallments(rdId, numberOfPeriods);
```

Critical distinction: `getInstallments()` returns calculated projections, NOT the actual Opportunity records that will be created. Future installment Opportunities are created by NPSP's scheduled batch job, not by the Installments API.

### Wealth Screening Integration Pattern

Wealth screening tools (iWave, DonorSearch, Windfall) integrate via AppExchange managed packages that:
1. Connect to the vendor's API via a Connected App or API key in the managed package settings
2. Provide a Lightning component or batch process to retrieve wealth scores
3. Write scores to custom fields on Contact/Account (e.g., `iwave__iWave_Score__c`)

There is NO native NPSP or Salesforce wealth screening API. Each ISV package has its own integration configuration. Architects should not design custom HTTP callout integrations when an AppExchange package exists for the target vendor.

---

## Common Patterns

### BDI Integration for External Gift Processing

**When to use:** Any external system (event platform, payment processor, peer-to-peer fundraising tool) that needs to push gift data into NPSP.

**How it works:**

```apex
// 1. Create DataImport staging records
List<npsp__DataImport__c> imports = new List<npsp__DataImport__c>();
for (ExternalGift gift : externalGifts) {
    imports.add(new npsp__DataImport__c(
        npsp__Contact1_Firstname__c = gift.firstName,
        npsp__Contact1_Lastname__c  = gift.lastName,
        npsp__Contact1_Email__c     = gift.email,
        npsp__Donation_Amount__c    = gift.amount,
        npsp__Donation_Date__c      = gift.giftDate,
        npsp__Donation_Stage__c     = 'Closed Won',
        npsp__Payment_Method__c     = gift.paymentMethod
    ));
}
insert imports;

// 2. Process via BDI API
npsp.BDI_DataImport_API.processDataImportRecords(
    new npsp.BDI_DataImport_API.BDIImportSettings(),
    imports,
    false // dryRun = false
);

// 3. Check results
for (npsp__DataImport__c di : [
    SELECT npsp__Status__c, npsp__FailureInformation__c
    FROM npsp__DataImport__c WHERE Id IN :imports
]) {
    if (di.npsp__Status__c == 'Failed') {
        // Handle failure
    }
}
```

**Why not direct Opportunity insert:** Direct inserts bypass GAU allocation processing, soft credit creation, household account rollup triggers, and Elevate payment ID linkage — all silently. The BDI pipeline handles all of these automatically.

### ERD Schedule Retrieval

**When to use:** Donor-facing portal or communication that needs to display a recurring donor's projected payment schedule.

```apex
// Get active recurring donation schedules for display
String scheduleJson = npsp.RD2_ApiService.getSchedules(recurringDonationId);
Map<String, Object> scheduleMap = 
    (Map<String, Object>) JSON.deserializeUntyped(scheduleJson);
// Parse schedule details for UI display
```

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Insert gift data from external system | npsp__DataImport__c + BDI_DataImport_API | Only method that triggers all NPSP gift processing logic |
| Get recurring donation schedule | RD2_ApiService.getSchedules() | Returns active schedule as JSON |
| Get projected future installments | RD2_ApiService.getInstallments() | Returns calculated projections (not persisted Opps) |
| Wealth screening integration | AppExchange managed package (iWave, DonorSearch) | No native NPSP wealth screening API exists |
| Bulk historical gift import | DataImport__c batch (50,000 records max, 100MB file) | BDI supports large batch loads |
| Custom payment/GAU field mapping | NPSP Advanced Mapping (must be enabled first) | Standard BDI mapping does not cover custom fields |

---

## Recommended Workflow

1. **Confirm BDI Advanced Mapping** — If the integration requires custom field mapping on Opportunity, Contact, or Payment, verify NPSP Advanced Mapping is enabled in NPSP Settings > Advanced Mapping.
2. **Map source data to DataImport fields** — Map every source field to the corresponding `npsp__DataImport__c` field. Document fields that have no standard BDI mapping (will need Advanced Mapping or post-processing).
3. **Write DataImport insertion code** — Build the staging record population logic, including gift data, donor match fields, GAU allocations, and soft credit recipients.
4. **Invoke BDI processing** — Call `BDI_DataImport_API.processDataImportRecords()` or trigger the batch job.
5. **Handle failures** — Check `npsp__Status__c = 'Failed'` and `npsp__FailureInformation__c` on DataImport records post-processing. Route failures to a notification or remediation queue.
6. **Validate rollup recalculation** — After bulk import, verify NPSP CRLP (Customizable Rollups) has recalculated household totals for affected Contacts. Large imports may require a manual CRLP batch run.

---

## Review Checklist

- [ ] No direct Opportunity or OppPayment inserts — all gifts routed through DataImport__c
- [ ] BDI Advanced Mapping enabled if custom fields are needed
- [ ] GAU allocation fields populated on DataImport records where required
- [ ] Soft credit recipient fields populated for matching gift and in-kind donors
- [ ] Error handling checks `npsp__FailureInformation__c` on failed DataImport records
- [ ] CRLP batch recalculation triggered after large bulk imports
- [ ] ERD Installments API not confused with persisted Opportunity records

---

## Salesforce-Specific Gotchas

1. **Direct Opportunity insert bypasses all NPSP processing** — This is the #1 NPSP integration mistake. Inserting Opportunity and OppPayment records directly (via Data Loader or REST API) silently skips GAU allocations, soft credits, household rollups, and Elevate payment linkage. Always use BDI.
2. **ERD Installments API returns projections, not Opportunities** — `RD2_ApiService.getInstallments()` returns a list of calculated projection objects. These are NOT the actual Opportunity records for future installments. Future Opportunities are created by NPSP's scheduled Apex batch job. Integrations that wait for installment Opportunities to appear immediately after calling getInstallments() will wait forever.
3. **BDI Advanced Mapping must be enabled before custom field mapping works** — Standard DataImport__c fields cover most gift data, but custom Opportunity, Contact, or Payment fields require Advanced Mapping to be enabled in NPSP Settings. Without it, custom field values in DataImport records are silently ignored.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| DataImport field mapping table | Source-to-BDI field mapping for the integration |
| BDI integration Apex class | Staging record population and BDI API invocation code |
| ERD API usage examples | Code samples for Schedule and Installments API calls |

---

## Related Skills

- `npsp-trigger-framework-extension` — For custom Apex logic that extends NPSP TDTM after BDI processing
- `gift-history-import` — For bulk historical gift migration using DataImport__c
