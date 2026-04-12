# Gotchas — Financial Data Quality

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Standard Duplicate Rules Have No FinancialAccount Support — All Detection Must Be Custom

**What happens:** A practitioner configures Salesforce Duplicate Management expecting standard Duplicate Rules and Matching Rules to detect and block duplicate `FinancialAccount` or `FinServ__FinancialAccount__c` records. The Setup wizard for Duplicate Rules only surfaces Account, Contact, and Lead as protectable objects. `FinancialAccount` is a standard FSC object in Core FSC, but it is not included in the standard Duplicate Management framework. No out-of-box Matching Rule configuration exists for FSC financial objects.

**When it occurs:** During FSC data migrations, when core banking integrations load accounts nightly via Bulk API, or when advisors manually create financial accounts in the UI — all scenarios where a duplicate insert could silently succeed because no platform-enforced blocking mechanism exists. The problem is discovered only when advisors report seeing the same account twice on a client's financial profile.

**How to avoid:** Implement a `before insert` Apex trigger on `FinancialAccount` (Core FSC) or `FinServ__FinancialAccount__c` (managed-package) that checks for existing records using a business key — typically an external account number, an ISIN/CUSIP for investment holdings, or a policy number for insurance accounts. The trigger must be bulk-safe: collect all deduplication keys from `Trigger.new` into a Set, execute one SOQL query for the entire batch, and call `addError()` on matching records. Do not create a cross-object Matching Rule on Account expecting it to cover FinancialAccount records — the relationship is not traversed by standard Duplicate Management.

---

## Gotcha 2: FSC Rollup Batch Does Not Self-Heal After Failure — Stale Household KPIs Persist Silently

**What happens:** The FSC rollup batch aggregates household-level financial data (Total Assets, Total Liabilities, Net Worth, Total AUM) and writes the results to fields on the household Account. When the batch fails — due to a governor limit violation, a malformed `FinancialHolding` record, or an org maintenance window that interrupts the scheduled batch — the aggregated values on the household Account freeze at whatever they were at the last successful run. New `FinancialAccount` or `FinancialHolding` changes made after the failure are not reflected. There is no platform alert visible to advisors, branch managers, or end users. The household KPI fields continue to display the stale values as though they are current.

**When it occurs:** After bulk data loads that introduce malformed financial records (e.g., a `FinancialHolding` with a null required field that causes the rollup batch to error mid-execution), after automation changes that increase governor limit consumption, or after weekend maintenance windows that disrupt the scheduled batch without an automatic re-run. Orgs that do not monitor batch completion timestamps may run with stale household totals for days before anyone notices.

**How to avoid:** Build operational monitoring on top of the FSC rollup batch. The recommended approach is a custom `Rollup_Audit__c` object updated by a post-completion Flow or Apex job, combined with a scheduled Apex health monitor that alerts operations if the last-run timestamp is older than the expected batch interval. Document the manual re-run procedure (FSC Settings > Rollup Configuration > Run Rollups Now) so any admin can execute it without requiring a developer. Include "verify rollup batch last-run timestamp" as a mandatory step in any post-deployment checklist.

---

## Gotcha 3: Validation Rules on FinancialHolding Are Limited to One Cross-Object Level — Grandparent Fields Cause Compile Errors

**What happens:** A practitioner writes a validation rule on `FinancialHolding` that attempts to access a field two levels up the relationship chain — for example, checking the `PrimaryOwner.Type` on the related `FinancialAccount` (which would be `FinancialAccount.PrimaryOwner__r.Type`). The validation rule formula compiles successfully in some test environments but fails in others, or the Setup formula editor itself rejects the formula with a compile error: "Relationship traversal cannot exceed one level."

**When it occurs:** When data quality requirements for a `FinancialHolding` record depend on attributes of the account's owner (e.g., "if the holding type is equities and the account owner is classified as a retail client, require a risk tolerance field"), the natural formula traversal goes two levels deep: `FinancialHolding > FinancialAccount > Contact (owner)`. This exceeds the one-level cross-object formula limit.

**How to avoid:** For validation checks that require grandparent field access, use a `before insert` and `before update` Apex trigger on `FinancialHolding`. Query the necessary parent and grandparent fields in a single SOQL join within the trigger, then apply the validation logic programmatically with `addError()`. Alternatively, use a formula field on `FinancialAccount` to "flatten" the required grandparent value into the intermediate object, making it accessible to `FinancialHolding` in a single cross-object reference.

---

## Gotcha 4: FinancialAccount RecordType Guards Are Required on Validation Rules — Missing Guards Block Unrelated Account Types

**What happens:** A practitioner adds a validation rule to enforce a field (e.g., `PolicyNumber__c`) that is required only for insurance-type `FinancialAccount` records. The rule is written without a `RecordType` guard because the field was introduced specifically for the Insurance account type. Shortly after deployment, integration loads for investment and bank account types begin failing because the validation rule fires on all `FinancialAccount` records regardless of type, blocking the creation of records where `PolicyNumber__c` is legitimately not applicable.

**When it occurs:** When new FSC RecordTypes are introduced over time (Insurance, Bank, Investment, Loan, custom types) and validation rules are written against an early assumption that the field is required everywhere. The problem surfaces immediately after the rule is deployed to an org that processes multiple FinancialAccount types — or later, when a new account type is introduced that does not need the validated field.

**How to avoid:** Always scope `FinancialAccount` validation rules to the relevant RecordType using `ISPICKVAL(RecordType.DeveloperName, 'TargetType')` as the outermost guard in the AND() formula. Document which RecordTypes each validation rule applies to in the rule description. When a new FinancialAccount RecordType is introduced, audit all existing validation rules to confirm none of them unintentionally apply to the new type.

---

## Gotcha 5: Apex Duplicate Triggers That Are Not Bulk-Safe Fail Silently During Integration Loads

**What happens:** A practitioner implements a `before insert` duplicate detection trigger on `FinancialAccount` that contains a SOQL query inside the for-loop over `Trigger.new`:

```apex
// WRONG — SOQL inside a for-loop is not bulk-safe
for (FinancialAccount fa : Trigger.new) {
    List<FinancialAccount> existing = [
        SELECT Id FROM FinancialAccount
        WHERE ExternalAccountNumber__c = :fa.ExternalAccountNumber__c
    ];
    if (!existing.isEmpty()) {
        fa.addError('Duplicate detected');
    }
}
```

During UI use (single record insert), this works correctly. During a nightly core banking integration load using Bulk API with batches of 200 records, the trigger hits the governor limit of 100 SOQL queries per transaction on the first batch and throws an unhandled `System.LimitException`. The integration job fails with a generic error; the duplicate detection is effectively bypassed, and the load either aborts entirely or the error handling retries without the trigger check.

**When it occurs:** Any time the non-bulk-safe trigger processes more than 100 `FinancialAccount` records in a single DML transaction. Core banking integrations almost always operate in batches of 200 records per transaction, hitting this limit immediately.

**How to avoid:** Collect all deduplication keys from `Trigger.new` into a Set before any SOQL. Execute one SOQL query for the entire batch, populate a Map from the results, then iterate `Trigger.new` to check the Map in memory. This pattern uses exactly one SOQL query per trigger execution regardless of batch size. See the bulk-safe trigger in Example 1 for the correct implementation.
