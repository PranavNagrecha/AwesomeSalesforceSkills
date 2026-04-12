# Well-Architected Notes — Financial Data Quality

## Relevant Pillars

- **Reliability** — The most critical pillar for FSC financial data quality. FinancialAccount records are the source of truth for advisor-facing KPIs and regulatory reporting. Silent data integrity failures — stale rollup values, undetected duplicate accounts, unreconciled balances — undermine advisor trust and can trigger compliance findings. Reliability requires operational monitoring of the FSC rollup batch, a duplicate detection mechanism that fires on every insert path (UI and API), and a tested recovery runbook for rollup failures.

- **Security** — Validation rule bypass patterns must be implemented using Custom Permissions assigned to permission sets, not system administrator profiles or hardcoded user IDs. Integration service accounts that bypass FSC validation rules must be provisioned with least-privilege access: the bypass permission set only, no additional object permissions beyond what the integration requires. Field-level data quality controls (required fields on FinancialAccount) are a security boundary — if bypassed too broadly, invalid records can be created that cause downstream reporting errors or compliance gaps.

- **Operational Excellence** — FSC financial data quality has ongoing operational requirements: rollup batch monitoring, reconciliation cycle management, duplicate review queue processing, and validation rule audit as new FinancialAccount RecordTypes are introduced. Operational excellence means these activities are documented, automated where possible (batch health monitor, scheduled reconciliation), and executable by non-developer admins. A data quality control that requires a developer to investigate every failure is not operationally excellent.

- **Performance** — Apex duplicate detection triggers must be bulk-safe. Core banking and custodial integration loads operate in batches of up to 200 records per DML transaction. A SOQL query inside a for-loop over `Trigger.new` will hit governor limits in the first batch. Bulk-safe trigger patterns (Set collection → single SOQL → Map lookup) keep duplicate detection within governor limits at integration-scale volumes. For very high volume orgs (millions of FinancialAccount records), indexed query paths on the deduplication key field are essential for performance.

- **Scalability** — Reconciliation processes must be designed to handle growing FinancialAccount and FinancialHolding volumes. The staging-object + Apex batch reconciliation pattern scales horizontally by processing records in configurable batch sizes. Reconciliation variance thresholds should be configurable (Custom Metadata or Custom Settings) so they can be tuned without code changes as data volumes grow.

## Architectural Tradeoffs

**Duplicate detection — blocking trigger vs. advisory review queue**

A `before insert` Apex trigger that blocks duplicate inserts immediately protects data integrity but can disrupt integration loads if the deduplication logic produces false positives (e.g., due to external account number format variations). An advisory approach — allowing the insert but writing potential duplicates to a `FinancialAccountDuplicateCandidate__c` review object — is less disruptive but allows duplicates to exist in the system until a steward reviews and resolves them.

Recommended decision: use the blocking trigger for fields that are definitive business keys (external account numbers from a single authoritative source). Use the advisory approach for probabilistic matches (name similarity + owner combination) where false positives are expected.

**Validation rule enforcement vs. integration load completeness**

Strict validation rules at insert time enforce data quality but can cause integration loads to fail on records that arrive with incomplete data (common when source systems have staged loads — account shell first, then detail records). Permissive rules reduce load failures but allow incomplete records into the system.

Recommended decision: use RecordType-scoped validation rules with Custom Permission bypass. Allow the integration user to bypass on the initial load, then re-validate completeness via a separate post-load Apex batch that flags and routes incomplete records for stewardship. This separates the load concern from the quality concern without sacrificing either.

**Reconciliation frequency — real-time vs. batch**

Real-time reconciliation (compare every FinancialAccount write against the source system immediately) provides the highest fidelity but creates a synchronous dependency on the source system that can slow down FSC saves and adds integration complexity. Batch reconciliation (daily or intraday comparison cycle) introduces a time window of tolerable discrepancy but is far simpler to operate and recover from.

Recommended decision: batch reconciliation is the standard pattern for FSC. Use real-time reconciliation only for high-value account types where regulatory requirements mandate it and the source system can support synchronous lookups at the required throughput.

## Anti-Patterns

1. **Relying on standard Duplicate Rules for FinancialAccount** — Standard Duplicate Management is scoped to Account, Contact, and Lead. Configuring a Duplicate Rule with the expectation it will protect `FinancialAccount` records results in no protection at all. This anti-pattern leaves FSC financial data with zero duplicate detection coverage and is the most common data integrity gap found in FSC production orgs.

2. **Writing non-bulk-safe duplicate detection triggers** — A trigger that queries inside a for-loop over `Trigger.new` works in developer sandboxes where one record is inserted at a time, but fails in production during integration loads. The trigger hits governor limits, throws an unhandled exception, and the integration job fails or bypasses the check. This gives false confidence that duplicate detection is in place when it is actually not functioning under load.

3. **Operating without FSC rollup batch monitoring** — The FSC rollup batch has no native alerting. Running without a health monitor means rollup failures go undetected until advisors report incorrect household totals, which can be days after the failure. By then, client meetings and regulatory snapshots may have been based on stale data. Operational monitoring of the rollup batch is not optional in any production FSC org used for advisor-facing or compliance-facing reporting.

## Official Sources Used

- Financial Services Cloud Admin Guide — https://help.salesforce.com/s/articleView?id=sf.fsc_admin.htm&type=5
- Financial Services Cloud Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.financial_services_cloud_object_reference.meta/financial_services_cloud_object_reference/fsc_dev_guide.htm
- Financial Services Cloud Object Reference — https://developer.salesforce.com/docs/atlas.en-us.financial_services_cloud_object_reference.meta/financial_services_cloud_object_reference/fsc_object_reference_intro.htm
- Industries Common Resources Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.industries_reference.meta/industries_reference/industries_dev_guide.htm
- Apex Developer Guide — Trigger Context Variables and Governor Limits — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_context_variables.htm
- Salesforce Duplicate Management — https://help.salesforce.com/s/articleView?id=sf.duplicate_management_overview.htm&type=5
- Salesforce Well-Architected Framework — https://architect.salesforce.com/well-architected/overview
