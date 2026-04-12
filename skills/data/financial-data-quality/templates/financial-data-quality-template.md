# Financial Data Quality — Work Template

Use this template when investigating or implementing FSC financial data quality controls — including FinancialAccount validation, duplicate detection, rollup batch health, or source system reconciliation.

## Scope

**Skill:** `financial-data-quality`

**Request summary:** (fill in what the practitioner or user asked for)

---

## Context Gathered

Answer these before starting work. See SKILL.md > Before Starting for detail.

- **FSC deployment type:** [ ] Managed-package FSC (`FinServ__FinancialAccount__c`) / [ ] Core FSC (`FinancialAccount`)
- **Object(s) in scope:** (e.g., FinancialAccount — Investment RecordType, FinancialHolding)
- **Source system(s):** (e.g., core banking, custodial platform, insurance policy admin)
- **Rollup batch last-run status:** (timestamp from FSC Settings > Rollup Configuration, or "not checked")
- **Known wrong assumption confirmed absent:** Standard Duplicate Rules do NOT cover FinancialAccount — confirmed [ ]
- **Integration bypass Custom Permission exists:** [ ] Yes (`Bypass_FSC_Validation`) / [ ] No — must create

---

## Problem Type

Check the primary problem type this work addresses:

- [ ] **Validation** — enforcing required fields or value constraints on FinancialAccount/FinancialHolding
- [ ] **Duplicate detection** — blocking or flagging duplicate FinancialAccount inserts
- [ ] **Rollup health** — diagnosing or recovering from stale household KPIs after rollup batch failure
- [ ] **Source system reconciliation** — comparing FSC balances against a core banking or custodial feed
- [ ] **Audit/compliance** — verifying data quality controls are in place and functioning

---

## Validation Work (if applicable)

| Validation Rule Name | Target Object | Target RecordType(s) | Has Custom Permission Bypass? | Has RecordType Guard? | Notes |
|---|---|---|---|---|---|
| (rule name) | FinancialAccount | (e.g. InsurancePolicy) | [ ] Yes / [ ] No | [ ] Yes / [ ] No | |
| | | | | | |

**Validation rule formula skeleton:**

```
AND(
    NOT($Permission.Bypass_FSC_Validation),
    ISPICKVAL(RecordType.DeveloperName, '<RecordTypeDeveloperName>'),
    <validation condition>
)
```

Error message: (fill in)

---

## Duplicate Detection Work (if applicable)

**Deduplication key chosen:** (e.g., `ExternalAccountNumber__c`, `PolicyNumber__c`, `ISIN + FinancialAccountId`)

**Approach:**
- [ ] Blocking Apex before-insert trigger (use when the key is a definitive business identifier)
- [ ] Advisory batch job writing to review object (use for probabilistic matches)

**Trigger check — bulk-safe design confirmed:**
- [ ] All deduplication keys collected into a Set before SOQL
- [ ] Single SOQL query executes for the entire batch (not inside a for-loop)
- [ ] Results checked via Map lookup in memory
- [ ] `addError()` called on the trigger record (before insert only)

---

## Rollup Batch Recovery (if applicable)

- **Last successful rollup timestamp:** (from FSC Settings > Rollup Configuration)
- **Expected batch interval:** (e.g., daily at 2am)
- **Is timestamp within expected window?** [ ] Yes / [ ] No — recovery needed
- **Recovery action taken:** [ ] Manual re-run via FSC Settings UI / [ ] Apex trigger / [ ] Pending

**Rollup health monitor deployed?** [ ] Yes / [ ] No — needs implementation

---

## Reconciliation Work (if applicable)

- **Source system feed format:** (e.g., CSV, JSON, MuleSoft integration)
- **Feed delivery schedule:** (e.g., daily at 6am UTC)
- **Staging object name:** (e.g., `AccountReconciliationStaging__c`)
- **Discrepancy object name:** (e.g., `FinancialAccountDiscrepancy__c`)
- **Variance threshold (configurable):** (e.g., >$0.01 absolute, >0.1% relative)
- **Reconciliation batch schedule:** (e.g., daily at 7am UTC, after feed delivery)
- **Review cadence for open discrepancies:** (e.g., weekly by data steward)

---

## Checker Script Output

Run before marking work complete:

```
python3 skills/data/financial-data-quality/scripts/check_financial_data_quality.py --manifest-dir <path-to-metadata>
```

- [ ] Script run
- [ ] All WARN items resolved or documented with rationale for deferral

---

## Checklist

Copy from SKILL.md > Review Checklist and tick as complete:

- [ ] FSC deployment type confirmed (managed-package `FinServ__` vs. Core FSC standard objects)
- [ ] All FinancialAccount validation rules include Custom Permission bypass
- [ ] Validation rules are guarded by RecordType where field requirements differ by account type
- [ ] No standard Duplicate Rule is being relied on for FinancialAccount duplicate detection
- [ ] Apex duplicate detection trigger exists and is bulk-safe
- [ ] FSC rollup batch is scheduled and last-run timestamp is within expected window
- [ ] A rollup health monitor or operational alert exists for rollup batch overdue conditions
- [ ] Source system reconciliation process is documented (if applicable)
- [ ] FinancialAccountDiscrepancy__c records are reviewed on a defined cadence
- [ ] Apex triggers and validation rules have been tested with both UI and API DML scenarios

---

## Notes

(Record any deviations from the standard patterns described in SKILL.md, reasons for deferred items, and any FSC-specific limitations or platform behaviors encountered during this work.)
