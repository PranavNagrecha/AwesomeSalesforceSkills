# Well-Architected Notes — Quote-to-Cash Process (CPQ + Revenue Cloud)

## Relevant Pillars

- **Reliability** — The Q2C chain spans multiple managed package triggers across at least five object types. Each status transition (Quote approval → Contract creation → Order activation → billing run) is a potential failure point. A well-architected implementation has monitoring at each transition, clear error alerting for failed billing runs, and a documented recovery playbook for common failure modes (e.g., billing schedule not created, invoice generation failed).
- **Operational Excellence** — The process involves multiple teams (Sales, Finance, RevOps) and automated handoffs between CPQ and Billing. Operational excellence requires that status transitions are visible in real time (dashboards on `sbaa__ApprovalRequest__c` status, Order activation status, billing run logs), that manual steps are minimized and documented, and that exception handling (rejected approvals, billing failures) is explicit and owned.
- **Security** — Advanced Approvals (`sbaa__`) records must be secured appropriately — approvers must not be able to approve their own quotes. `sbaa__Approver__c` records should reference role hierarchy or queue-based approvers rather than hardcoded user IDs to avoid breakage when personnel changes. Field-level security on `SBQQ__Quote__c.SBQQ__NetAmount__c`, `SBQQ__Discount__c`, and `blng__Invoice__c.blng__InvoiceStatus__c` should be locked to read-only for Sales roles after the appropriate stage.
- **Performance** — CPQ quote calculation (pricing rules, discount schedules) can be slow on large quotes. Billing runs that process thousands of billing schedules in a single batch can hit governor limits. Well-architected implementations tune the CPQ calculator settings and schedule billing runs during off-peak hours with appropriate batch sizes.
- **Scalability** — CPQ and Billing are both trigger-heavy managed packages. Adding custom triggers or flows on `SBQQ__Quote__c`, `Order`, or `blng__BillingSchedule__c` can cause interaction effects with the package's own trigger logic. Order of operations matters: custom triggers should use `after` context where possible and avoid re-querying CPQ-managed fields during calculation.

## Architectural Tradeoffs

**Advanced Approvals vs. Standard Approval Processes for CPQ Quotes**
Standard Approval Processes work on `SBQQ__Quote__c` and are simpler to configure, but they cannot evaluate Quote Line-level attributes as entry criteria. For discount-tier routing that depends on line-level discounts or product family, Advanced Approvals is required. The tradeoff is a separate package to install, maintain, and train administrators on. For simple single-level approvals, standard processes are sufficient and lower-risk.

**Automated vs. Manual Contract Creation**
Automating Contract creation via a Flow on Quote approval reduces manual steps and accelerates the billing cycle but introduces risk if the automation fires on an incorrect Quote status transition (e.g., a Quote that was approved then recalled and re-submitted). Manual Contract creation adds a human checkpoint that catches edge cases but introduces delay and process inconsistency. A hybrid approach — automation with explicit guard conditions and a clear manual fallback — is typically the most reliable.

**Billing Run Frequency vs. Invoice Timeliness**
Scheduled billing runs (daily, weekly, monthly) are operationally simpler but delay invoice generation. On-demand billing (triggering invoice generation via the `blng` API in real time) improves invoice timeliness but increases trigger load and requires robust error handling. The right choice depends on the volume of billable orders and the finance team's invoicing cadence requirements.

## Anti-Patterns

1. **Skipping the Contract and building a direct Quote-to-Order path** — This is the most common architectural failure in CPQ implementations. It appears to work for one-time products but silently breaks recurring billing. Subscriptions, renewal forecasting, and amendment flows all depend on the Contract record existing. Building without it creates technical debt that is expensive to remediate after billing has run.

2. **Hardcoding user IDs in sbaa__Approver__c records** — `sbaa__Approver__c` records that reference specific User IDs break when an employee leaves or changes role. The well-architected approach is to use dynamic approver sources: Role Hierarchy traversal (`Manager` field on User), Public Groups, or Queues. This makes the approval chain resilient to personnel changes without requiring metadata redeployment.

3. **Adding custom triggers on CPQ and Billing objects without understanding package trigger order** — CPQ and Billing both fire extensive trigger logic on their managed objects. Custom triggers added to the same objects (e.g., `SBQQ__Quote__c`, `Order`, `blng__BillingSchedule__c`) can interfere with package logic, cause recursion, or fire before the package has set required field values. Custom logic on CPQ/Billing objects should be validated against the package's trigger order documentation and tested thoroughly in a full CPQ sandbox, not a Developer Edition org.

## Official Sources Used

- Salesforce CPQ Developer Guide — Quote and Order Capture: https://developer.salesforce.com/docs/atlas.en-us.cpq_dev_guide.meta/cpq_dev_guide/cpq_dev_guide.htm
- Revenue Cloud Help — Advanced Approvals: https://help.salesforce.com/s/articleView?id=sf.cpq_advanced_approvals.htm
- Revenue Cloud Help — Billing Schedules: https://help.salesforce.com/s/articleView?id=sf.blng_billing_schedules.htm
- Revenue Cloud Help — Generate Invoices: https://help.salesforce.com/s/articleView?id=sf.blng_invoice_generation.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Object Reference — Contract: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_contract.htm
- Object Reference — Order: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_order.htm
