---
name: financial-data-quality
description: "Use when validating FinancialAccount record integrity in Financial Services Cloud, detecting duplicate financial records, or reconciling FSC data against core banking and custodial source systems. Trigger keywords: FinancialAccount validation, FSC duplicate detection, financial record reconciliation, stale household KPIs, FinancialHolding data quality, FSC data integrity. NOT for generic Salesforce data quality, Duplicate Rules setup on standard objects, or bulk data migration execution."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "How do I detect and prevent duplicate FinancialAccount records in FSC when standard Duplicate Rules don't work?"
  - "Household financial totals are stale and do not match the core banking system — what is the reconciliation process?"
  - "Our FSC FinancialAccount records have invalid or missing required fields after a data migration from the core banking platform"
  - "How do I validate FinancialAccount balances against a custodial feed and flag discrepancies in Salesforce?"
  - "FSC rollup batch failed and household KPIs are showing wrong values — how do I detect and recover?"
tags:
  - fsc
  - financial-data-quality
  - financial-account
  - duplicate-detection
  - data-reconciliation
  - household-rollup
  - data-integrity
  - financial-services
inputs:
  - Whether the org uses managed-package FSC (FinServ__ namespace) or Core FSC (standard objects)
  - List of required fields and valid values for FinancialAccount record types in scope
  - Source system (core banking, custodial, insurance platform) and available reconciliation feed format
  - Scheduled FSC rollup batch configuration and last-run status
  - Volume of FinancialAccount and FinancialHolding records requiring validation
outputs:
  - FinancialAccount validation rule strategy with integration bypass pattern
  - Custom Apex-based duplicate detection approach for FinancialAccount (with Matching Rule gaps documented)
  - Reconciliation audit report template comparing FSC balances against source system feed
  - FSC rollup batch monitoring checklist with recovery runbook
  - Data quality checker script output for org metadata analysis
dependencies:
  - data/fsc-data-model
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-12
---

# Financial Data Quality

Activate this skill when a practitioner needs to enforce, audit, or recover data quality on Financial Services Cloud financial records — specifically `FinancialAccount`, `FinancialHolding`, and household rollup aggregations. This skill covers FSC-specific validation constraints, the gap in standard Duplicate Rule coverage for `FinancialAccount`, and the reconciliation patterns required when FSC data must be kept consistent with upstream core banking or custodial systems.

This skill does not cover generic Salesforce data quality (see `data/data-quality-and-governance`), step-by-step Duplicate Rule configuration for standard objects, or bulk data migration tooling.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Deployment type:** Is the org on managed-package FSC (`FinServ__FinancialAccount__c`) or Core FSC (`FinancialAccount`)? Every object name, validation rule target, and Apex reference depends on this. Check Setup > Installed Packages.
- **Standard Duplicate Rules do not cover FinancialAccount:** This is the most consequential wrong assumption in this domain. `FinancialAccount` (Core FSC) and `FinServ__FinancialAccount__c` (managed-package) are not covered by the out-of-box Duplicate Rules framework. Standard Duplicate Rules in Salesforce are designed for Account, Contact, and Lead. There is no standard Matching Rule for `FinancialAccount`. Duplicate detection on financial records must be built using custom Matching Rules on the related Account or Contact objects, or through Apex trigger logic that checks for duplicates before insert.
- **FSC rollup batch does not self-heal:** The FSC async rollup batch aggregates household-level KPIs (Total Assets, Total Liabilities, Net Worth). If the batch fails, stale values persist on the household Account without any platform alert. Recovery requires a manual re-run. This is the primary source of data reconciliation failures between FSC and source systems.
- **Source system reconciliation is manual by default:** FSC does not have a native reconciliation framework for comparing `FinancialAccount.Balance` against a core banking or custodial feed. Reconciliation must be designed as a custom process: typically an inbound scheduled integration that compares current FSC values against the source, writes discrepancies to a staging object, and triggers review workflows.

---

## Core Concepts

### FinancialAccount Validation — What Platform Enforces vs. What You Must Build

Salesforce platform validation rules work on `FinancialAccount` the same as any other object. You can define formula-based validation to enforce required field combinations, value ranges, and cross-field consistency. However, several behaviors are specific to FSC:

- **Record type-conditional validation:** FSC ships multiple `FinancialAccount` RecordTypes (e.g., Investment, Bank, Insurance, Loan). Required fields differ by type. A validation rule that fires on all RecordTypes will block legitimate variation. Use `ISPICKVAL(RecordType.DeveloperName, 'Investment')` guards to scope rules to the correct type.
- **Integration bypass is essential:** Core banking feeds and custodial integrations write `FinancialAccount` records via the API. If validation rules are not bypassed for integration users, bulk loads fail. Always wrap FSC validation rules with a Custom Permission bypass: `AND(NOT($Permission.Bypass_FSC_Validation), <formula>)`.
- **FinancialHolding cross-object limits:** Validation rules on `FinancialHolding` can reference one parent level (`FinancialAccount.Status`) but not two levels (`FinancialAccount.PrimaryOwner.Type`). Deeper checks require Apex triggers.

### Duplicate Detection on FinancialAccount — Standard Gap and Custom Solutions

Standard Salesforce Duplicate Rules are defined for Account, Contact, and Lead. The `FinancialAccount` object (both Core FSC and managed-package `FinServ__FinancialAccount__c`) has no out-of-box Duplicate Rule support. Attempting to create a standard Duplicate Rule targeting `FinancialAccount` directly through Setup will fail — there is no native Matching Rule for the object.

**Two supported approaches for FSC duplicate detection:**

1. **Matching Rules on related Account/Contact:** Create a custom Matching Rule on the Account or Contact object that uses a field from the related financial account (e.g., external account number stored on the contact). This is indirect and only works when the duplicate signal exists on the parent object.

2. **Apex trigger-based duplicate detection:** For financial records specifically, implement a `before insert` Apex trigger on `FinancialAccount` (or `FinServ__FinancialAccount__c`) that queries for existing records with matching key attributes (e.g., `ExternalAccountNumber__c`, `AccountNumber`, `FinancialAccountType` + owner combination). Use `Database.query()` with selective filters. Block the insert and return a meaningful error message if a match is found.

The Apex trigger approach is the authoritative pattern for FSC financial record deduplication. It must be bulk-safe (process `Trigger.new` as a list, not record-by-record), governor-limit-aware, and bypass-capable for integration contexts.

### FSC Rollup Batch — Failure Modes and Reconciliation

The FSC rollup engine is an asynchronous batch process that reads all `FinancialAccount` and `AssetsAndLiabilities` records associated with a household and writes aggregated values (Total Assets, Total Liabilities, Net Worth, Total AUM) to fields on the household Account. Key behaviors affecting data quality:

- **Batch execution is not event-driven:** The rollup does not run immediately when a `FinancialAccount` record is created or updated. It runs on a configured schedule (via FSC Settings > Rollup Configuration) or when manually triggered.
- **Failure is silent:** If the batch fails (due to a governor limit, a data integrity issue on a FinancialHolding record, or an org maintenance event), stale values persist on the household Account. There is no native platform alert. The last-run timestamp in FSC Settings is the only indicator.
- **No automatic retry or self-healing:** Salesforce does not re-attempt a failed FSC rollup batch. Recovery requires a manual trigger — either through FSC Admin Settings UI or via Apex calling `FinancialServicesCloudRollupAPI` or the FSC Settings batch trigger.
- **Core FSC rollup:** In Core FSC orgs, rollup configuration moves to the Industries Common Resources rollup framework. The same absence of self-healing applies.

**Monitoring pattern:** A scheduled Apex job that reads the last rollup completion timestamp and fires a Platform Event or sends an alert if the timestamp is older than the expected batch interval is the standard operational monitoring approach.

### Source System Reconciliation Pattern

When FSC financial data must stay synchronized with an external core banking or custodial system, a reconciliation process is required because the FSC rollup alone cannot detect discrepancies originating in the source system.

**Recommended reconciliation architecture:**
1. Source system exports a daily or intraday reconciliation feed (CSV or JSON) containing account-level balance and status snapshots.
2. An integration layer (MuleSoft, Apex scheduled batch, or external ETL) loads the feed into a staging object (e.g., `AccountReconciliationStaging__c`) with fields: `ExternalAccountId`, `SourceBalance`, `SourceStatus`, `FeedTimestamp`.
3. A reconciliation Apex batch compares each staging record against the corresponding `FinancialAccount` in FSC, computing variance (`abs(FSC_Balance - SourceBalance)`).
4. Records with variance above a configurable threshold are written to a `FinancialAccountDiscrepancy__c` object for review and resolution.
5. A reconciliation dashboard in CRM Analytics or a report highlights open discrepancies by advisor, branch, or account type.

---

## Common Patterns

### Pattern: Apex Trigger Duplicate Check on FinancialAccount

**When to use:** Any time a new `FinancialAccount` record could be a duplicate of an existing record — most commonly during core banking integration loads and bulk migrations.

**How it works:**

```apex
trigger FinancialAccountDuplicateCheck on FinancialAccount (before insert) {
    // Collect external account numbers from incoming records
    Set<String> externalIds = new Set<String>();
    for (FinancialAccount fa : Trigger.new) {
        if (fa.ExternalAccountNumber__c != null) {
            externalIds.add(fa.ExternalAccountNumber__c);
        }
    }

    if (externalIds.isEmpty()) return;

    // Query existing FinancialAccount records with matching external IDs
    Map<String, FinancialAccount> existingByExtId = new Map<String, FinancialAccount>();
    for (FinancialAccount existing : [
        SELECT Id, ExternalAccountNumber__c, Name
        FROM FinancialAccount
        WHERE ExternalAccountNumber__c IN :externalIds
    ]) {
        existingByExtId.put(existing.ExternalAccountNumber__c, existing);
    }

    // Block duplicates with an error on the trigger record
    for (FinancialAccount fa : Trigger.new) {
        if (fa.ExternalAccountNumber__c != null
                && existingByExtId.containsKey(fa.ExternalAccountNumber__c)) {
            fa.addError('Duplicate FinancialAccount: ExternalAccountNumber '
                + fa.ExternalAccountNumber__c
                + ' already exists on record '
                + existingByExtId.get(fa.ExternalAccountNumber__c).Id);
        }
    }
}
```

**Why not standard Duplicate Rules:** `FinancialAccount` has no standard Matching Rule support. A standard Duplicate Rule cannot be configured for this object in Setup. The trigger approach is the only in-platform mechanism for blocking duplicate financial records at insert time.

### Pattern: Validation Rule with RecordType Guard and Integration Bypass

**When to use:** Enforcing required fields on `FinancialAccount` that vary by account type (Investment vs. Bank vs. Loan) while allowing integration users to bypass during bulk loads.

**How it works:**

Validation rule formula (example: Investment account requires ExternalAccountNumber):
```
AND(
    NOT($Permission.Bypass_FSC_Validation),
    ISPICKVAL(RecordType.DeveloperName, 'Investment'),
    ISBLANK(ExternalAccountNumber__c)
)
```

Error message: `Investment FinancialAccount records require an External Account Number from the custodial system.`

**Why not a universally required field:** Making `ExternalAccountNumber__c` universally required blocks valid record creation for account types where the field is not applicable (e.g., a manually tracked Insurance policy that has no external system identifier). RecordType-scoped validation rules express this conditional logic declaratively without Apex.

### Pattern: Rollup Batch Health Monitor

**When to use:** Any FSC org where household KPI accuracy is business-critical (wealth management, banking advisory dashboards).

**How it works:**

```apex
global class FSCRollupHealthMonitor implements Schedulable {
    global void execute(SchedulableContext sc) {
        // Read last rollup completion time from FSC Settings custom metadata
        // or from a custom Rollup_Audit__c record updated by a post-rollup Flow
        Rollup_Audit__c audit = [
            SELECT Last_Successful_Run__c
            FROM Rollup_Audit__c
            ORDER BY Last_Successful_Run__c DESC
            LIMIT 1
        ];
        DateTime threshold = DateTime.now().addHours(-25); // Expected: daily rollup
        if (audit.Last_Successful_Run__c < threshold) {
            // Fire alert — send email to ops team or publish Platform Event
            Messaging.SingleEmailMessage alert = new Messaging.SingleEmailMessage();
            alert.setToAddresses(new List<String>{'sfops@example.com'});
            alert.setSubject('FSC Rollup Batch Overdue — Household KPIs May Be Stale');
            alert.setPlainTextBody(
                'The FSC rollup batch last completed at '
                + audit.Last_Successful_Run__c.format()
                + '. Expected completion by '
                + threshold.format()
                + '. Investigate via FSC Settings > Rollup Configuration.'
            );
            Messaging.sendEmail(new List<Messaging.SingleEmailMessage>{ alert });
        }
    }
}
```

**Why not rely on FSC Settings alone:** FSC Settings shows the rollup configuration and a last-run timestamp but does not alert on failure. Advisors and operations teams never see the Settings page. The monitor bridges this gap and feeds alerting into the org's operational workflow.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need to block duplicate FinancialAccount on insert | Apex before-insert trigger with SOQL duplicate check | Standard Duplicate Rules have no FinancialAccount Matching Rule; trigger is the only blocking mechanism |
| Need to report on potential FinancialAccount duplicates without blocking | Apex scheduled batch writing to FinancialAccountDuplicate__c review object | Non-blocking detection separates review from load; allows stewardship workflow |
| FinancialAccount field required only for specific account type | Validation rule with RecordType guard and Custom Permission bypass | Universal required fields cannot express per-type conditionality |
| Household totals don't match source system after bulk load | Check FSC rollup batch last-run timestamp; trigger manual re-run | Rollup is async and does not self-heal; stale values persist until re-run |
| Need to detect balance discrepancies vs. core banking feed | Reconciliation staging object + Apex batch with configurable variance threshold | FSC has no native source-system reconciliation; custom batch is the standard pattern |
| Validation rules blocking integration load | Add Custom Permission bypass (`NOT($Permission.Bypass_FSC_Validation)`) to all FSC validation rules | Integration users need a governed bypass; profile-based bypasses are too broad |
| FinancialHolding data quality check requires parent account fields | One-level cross-object formula in validation rule for simple checks; Apex trigger for deeper traversal | Platform cross-object limit is one relationship level in validation rule formulas |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on FSC financial data quality:

1. **Confirm FSC deployment type and object namespace** — verify managed-package (`FinServ__FinancialAccount__c`) vs. Core FSC (`FinancialAccount`) before writing any Apex, validation rules, or SOQL. All object references depend on this.
2. **Audit FinancialAccount validation coverage** — review existing validation rules for missing RecordType guards, missing integration bypass conditions, and cross-field consistency checks. Run `check_financial_data_quality.py` against the org metadata.
3. **Assess duplicate detection posture** — confirm that no standard Duplicate Rule is being relied on for `FinancialAccount`. If no Apex trigger exists for duplicate blocking, design and implement the trigger using external account number or owner + account type combination as the deduplication key.
4. **Verify FSC rollup batch health** — check the last-run timestamp in FSC Settings > Rollup Configuration. If household KPIs appear stale, trigger a manual re-run before diagnosing further. Implement a scheduled Apex rollup health monitor if one does not exist.
5. **Design source system reconciliation if required** — if FSC data must reconcile against a core banking or custodial feed, design the staging object, reconciliation batch, discrepancy object, and variance threshold configuration. Confirm the feed format and delivery schedule with the source system team.
6. **Test all validation rules and triggers in sandbox** — include both UI-triggered and API-triggered scenarios. Verify that integration users with the Custom Permission can bypass validation rules. Verify that the duplicate trigger fires on batch inserts (bulk-safe behavior).
7. **Document operational runbook** — record how to manually trigger the FSC rollup batch, how to investigate rollup failures, and how to resolve reconciliation discrepancies. Ensure any admin can execute recovery without developer involvement.

---

## Review Checklist

Run through these before marking FSC financial data quality work complete:

- [ ] FSC deployment type confirmed (managed-package `FinServ__` vs. Core FSC standard objects)
- [ ] All FinancialAccount validation rules include Custom Permission bypass (`NOT($Permission.Bypass_FSC_Validation)`)
- [ ] Validation rules are guarded by RecordType where field requirements differ by account type
- [ ] No standard Duplicate Rule is being relied on for FinancialAccount duplicate detection
- [ ] Apex duplicate detection trigger exists and is bulk-safe (processes Trigger.new as a list, not record-by-record)
- [ ] FSC rollup batch is scheduled and last-run timestamp is within expected window
- [ ] A rollup health monitor or operational alert exists for rollup batch overdue conditions
- [ ] Source system reconciliation process is documented (if applicable) with a staging object and variance threshold
- [ ] FinancialAccountDiscrepancy__c (or equivalent) records are reviewed on a defined cadence
- [ ] Apex triggers and validation rules have been tested with both UI and API DML scenarios

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Standard Duplicate Rules do not cover FinancialAccount** — Standard Duplicate Management supports Account, Contact, and Lead. There is no out-of-box Matching Rule for `FinancialAccount` (Core FSC) or `FinServ__FinancialAccount__c` (managed-package). Attempting to configure a standard Duplicate Rule for these objects through Setup fails. Duplicate detection must be custom-built via Apex trigger or Matching Rules on the related Account/Contact with indirect signal fields.

2. **FSC rollup batch does not self-heal after failure — stale household KPIs persist silently** — The FSC async rollup batch aggregates household financial KPIs. When the batch fails (governor limit, data integrity issue, maintenance window), stale values persist on the household Account indefinitely. There is no platform alert and no automatic retry. Advisors see incorrect totals without any visible error. Recovery requires a manual re-run via FSC Settings or Apex. This is the most common source of FSC data integrity incidents in production.

3. **RecordType guards are required on FinancialAccount validation rules** — FSC ships multiple FinancialAccount RecordTypes (Investment, Bank, Loan, Insurance, and custom types). A validation rule written without a RecordType guard will fire on all types, blocking legitimate record creation for types where the validated field is not applicable. Always scope validation rule formulas to the relevant RecordType using `ISPICKVAL(RecordType.DeveloperName, 'TargetType')`.

4. **Apex duplicate triggers must be explicitly bulk-safe** — During core banking integration loads (which commonly use Bulk API or batched REST calls), `Trigger.new` contains up to 200 records per execution. A trigger that runs a SOQL query inside a for-loop over `Trigger.new` will hit governor limits immediately. The correct pattern is to collect all deduplication keys into a Set before the SOQL query, execute one query for the entire batch, and check results in memory.

5. **FinancialHolding validation rules cannot traverse two relationship levels** — Validation rules on `FinancialHolding` can access parent `FinancialAccount` fields in one-level cross-object formulas (e.g., `FinancialAccount.Status`). Attempting to access grandparent fields (e.g., `FinancialAccount.PrimaryOwner__r.Type`) will cause a compile error. For checks that require deeper traversal, implement a `before insert/update` Apex trigger on `FinancialHolding`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| FinancialAccount validation rule inventory | Per-RecordType table of validation rules with bypass condition status and API-trigger safety flag |
| Duplicate detection Apex trigger | Bulk-safe before-insert trigger for FinancialAccount with external account number deduplication key |
| FSC rollup health monitor | Scheduled Apex class that checks rollup last-run timestamp and fires alert on overdue condition |
| Reconciliation staging design | Object model and batch Apex skeleton for comparing FSC FinancialAccount balances against source system feed |
| check_financial_data_quality.py output | Static metadata analysis issue list covering missing bypasses, RecordType guard gaps, and duplicate rule coverage |

---

## Related Skills

- `data/fsc-data-model` — FSC object structure, namespace differences, rollup framework configuration, and FinancialAccountParty ownership model
- `data/data-quality-and-governance` — Generic Salesforce data quality patterns including standard Duplicate Rules on Account/Contact, field history, GDPR, and Shield
- `admin/financial-account-setup` — FSC Admin Settings configuration for rollups, account types, and financial account record type setup
- `architect/fsc-architecture-patterns` — Higher-level FSC architecture decisions including CDS, managed-package vs. Core FSC selection, and integration topology
- `apex/fsc-financial-calculations` — Custom Apex calculation logic for portfolio performance, rollup recalculation after bulk loads
