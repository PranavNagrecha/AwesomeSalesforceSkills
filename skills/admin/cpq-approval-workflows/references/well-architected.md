# Well-Architected Notes — CPQ Approval Workflows

## Relevant Pillars

### Security

CPQ Advanced Approvals governs which discounts can be approved by whom — it is a commercial control boundary. Security failures here have direct revenue impact: an incorrectly configured approval rule that never fires allows reps to offer discounts without required sign-off.

Key security considerations:
- The "CPQ Advanced Approvals" permission set must be assigned to the minimum set of users required. Submitters need it; approvers need it; not every CPQ user needs it.
- Approval rules must be tested to confirm they fire for all threshold-crossing combinations, including edge cases (e.g., a single line at exactly the threshold value).
- Smart Approvals must be carefully governed: the list of approval-relevant fields must be maintained as rules change over time. An approval-relevant field that is removed from conditions but still exists in the quote can create approval gaps if not audited.

### Operational Excellence

Approval workflows are high-friction processes if poorly designed. Operational excellence in this domain means:
- Rules are documented in an approval workflow design matrix so any admin can understand why each rule exists, what it fires on, and who it routes to.
- Approval chain step order is explicit and maintained — undocumented step orders cause confusion during approver changes (e.g., when a manager leaves the company).
- The `SBAA.EscalateApprovals` scheduled job is monitored as infrastructure. Its absence causes silent escalation failures with no system alert.
- Smart Approvals reduces operational burden on approvers by eliminating redundant re-approval cycles for cosmetic quote changes.

### Reliability

Approval workflows must fire deterministically on every qualifying quote. Reliability risks in this domain:
- Approval Variables must be tested against quotes with zero lines, quotes with all lines below threshold, and quotes with mixed above/below-threshold lines to verify the aggregation behavior at boundaries.
- Escalation job availability must be verified after every sandbox refresh and package upgrade.
- Rules must be kept Active — an inadvertently deactivated rule creates an approval gap with no system warning.
- Approval Chains with user-specific approver references break when the referenced user is deactivated. Use dynamic approver references (e.g., a field on the quote or account that stores the approver's user ID) where possible to reduce single-user dependency.

## Architectural Tradeoffs

### Approval Variables vs. Formula Fields on the Quote

Using a formula field on `SBQQ__Quote__c` to pre-compute an aggregate (e.g., a max discount roll-up) and referencing that field in a standard approval process condition is tempting because it avoids the Advanced Approvals package dependency. The tradeoff: `SBQQ__Quote__c` to `SBQQ__QuoteLine__c` does not support Salesforce roll-up summary fields in the standard metadata model, and formula fields cannot natively aggregate over child records. `SBAA__ApprovalVariable__c` is the only supported, reliable mechanism and is the intended architectural solution.

### Sequential Chains vs. Multiple Independent Rules

When the same set of approvers must review every qualifying quote, a single approval chain with ordered steps is cleaner and more maintainable than multiple independent rules each routing to a different approver. Multiple rules route independently and simultaneously unless chained. Use chains when order matters; use separate rules only when independent parallel approval is acceptable.

### Smart Approvals Scope

Smart Approvals reduces re-approval friction but introduces a dependency on accurate field tracking: the list of "approval-relevant" fields must be actively maintained as conditions evolve. If a condition is added to a rule that references a new field, that field becomes approval-relevant immediately. Teams that do not maintain a field registry alongside their approval rules risk Smart Approvals carrying forward approvals that should have been re-evaluated.

## Anti-Patterns

1. **Standard Salesforce Approval Processes for Cross-Line CPQ Discounts** — Standard approval processes evaluate a single record. They cannot aggregate across `SBQQ__QuoteLine__c` child records. Practitioners who use standard processes for CPQ discount approvals create gaps where high line-level discounts bypass approval because the parent quote field does not reflect the true maximum. The correct mechanism is `SBAA__ApprovalVariable__c` within the Advanced Approvals package.

2. **Hardcoded User References in Approval Chains Without a Succession Plan** — `SBAA__Approver__c` records that reference specific Salesforce user IDs break when those users are deactivated or their role changes. In high-turnover sales organizations this causes approval chains to stall with no visible error. The architectural alternative is to use dynamic approver fields on the quote (e.g., a lookup to the account owner or the opportunity owner's manager) so approver routing survives personnel changes without rule edits.

3. **No Escalation Job Monitoring** — Configuring escalation in rules without monitoring the `SBAA.EscalateApprovals` scheduled job creates a false sense of coverage. If the job is deactivated after an org refresh, no escalation fires and there is no alert. Treat the escalation job as an operational dependency with the same monitoring treatment as other critical scheduled processes.

## Official Sources Used

- Salesforce CPQ Advanced Approvals — Advanced Approvals for Salesforce CPQ Managed Package: https://help.salesforce.com/s/articleView?id=sf.cpq_adv_approvals.htm
- Salesforce CPQ Smart Approvals: https://help.salesforce.com/s/articleView?id=sf.cpq_smart_approvals.htm
- Salesforce CPQ Approval Chains: https://help.salesforce.com/s/articleView?id=sf.cpq_approval_chains.htm
- Trailhead — Salesforce CPQ Advanced Approvals for Admins: https://trailhead.salesforce.com/content/learn/modules/salesforce-cpq-advanced-approvals-for-admins
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Well-Architected — Security Pillar: https://architect.salesforce.com/docs/architect/well-architected/guide/security.html
- Salesforce Well-Architected — Operational Excellence Pillar: https://architect.salesforce.com/docs/architect/well-architected/guide/operational-excellence.html
- Salesforce Well-Architected — Reliability Pillar: https://architect.salesforce.com/docs/architect/well-architected/guide/reliability.html
