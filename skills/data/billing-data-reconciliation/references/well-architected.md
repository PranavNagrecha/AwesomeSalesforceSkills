# Well-Architected Notes — Billing Data Reconciliation

## Relevant Pillars

### Reliability

The billing reconciliation chain is a financial system of record. Every link in the chain — from billing schedule through invoice to payment allocation — must produce deterministic, auditable results. Reliability failures in this domain have direct financial impact: invoices that remain open despite payment received inflate AR balances; missing revenue transaction records misstate deferred and earned revenue on the balance sheet.

Key reliability concerns:
- `blng__PaymentAllocation__c` records must be created explicitly — the platform does not auto-allocate, and a missing allocation leaves an invoice open indefinitely.
- `blng__RevenueTransactionErrorLog__c` must be monitored after every billing run. Silent failures (missing recognition rules, Finance Period gaps) do not surface through standard Salesforce error channels.
- Billing schedule amounts must be verified after every Order amendment. The platform does not automatically propagate amended prices to existing billing schedules.

### Operational Excellence

Billing reconciliation is a recurring operational process (month-end close, post-billing-run validation). Operational excellence in this domain means:
- Post-billing-run SOQL checks against `blng__RevenueTransactionErrorLog__c` are part of the standard operating procedure, not an ad-hoc diagnostic.
- Payment allocation workflows are explicit and documented so that partial payments are handled consistently.
- Amount chain audits (QuoteLine → OrderItem → BillingSchedule → InvoiceLine) are run before each billing period closes, not after Finance discovers a gap.

Orgs that treat reconciliation as a reactive activity (investigate after Finance complains) will consistently have multi-day close delays. Proactive monitoring reduces close time to hours.

### Security

Billing and payment records contain financial PII and commercially sensitive contract amounts. Access control in this domain must enforce:
- `blng__Payment__c` and `blng__PaymentAllocation__c` records should be accessible only to finance and billing operations roles — not to standard sales users or service agents.
- `blng__RevenueTransactionErrorLog__c` read access should be limited to billing admins. Error messages may contain order and product details that should not be broadly visible.
- Data Loader or API access to create or delete `blng__PaymentAllocation__c` records should require explicit permission set assignment, not rely on default object-level access.
- Audit logs should capture who created or deleted payment allocation records. Salesforce Setup Audit Trail and Field History Tracking on key fields (`blng__Status__c`, `blng__Balance__c` on invoices) support audit requirements.

## Architectural Tradeoffs

### Manual Allocation vs. Automated Payment Matching

Salesforce Billing's explicit allocation model (requiring `blng__PaymentAllocation__c` records) provides full auditability — every payment application is traceable. The tradeoff is operational overhead: payment matching must be done explicitly, either manually or through custom automation (Apex or Flow).

Orgs that process high volumes of payments (hundreds per month) should implement automated payment matching using Flow or Apex. The automation should match `blng__Payment__c` to open `blng__Invoice__c` records by account and amount, create the `blng__PaymentAllocation__c` records, and surface exceptions (partial payments, payments without a matching open invoice) for manual review. This preserves auditability while eliminating manual allocation overhead.

Orgs with low payment volume can manage allocation manually through the standard Salesforce Billing UI, accepting the operational overhead in exchange for simpler configuration.

### Reactive vs. Proactive Reconciliation

A reactive reconciliation model (investigate when Finance complains) consistently produces month-end delays and missed errors that span multiple periods. A proactive model — automated post-billing-run queries against `blng__RevenueTransactionErrorLog__c`, scheduled Amount Chain audits, and dashboards on unallocated payments — surfaces issues within minutes of the billing batch completing, before they compound.

The architectural investment in proactive monitoring (scheduled reports, dashboards, post-run Apex checks) is small relative to the cost of a single missed revenue entry discovered three periods late.

## Anti-Patterns

1. **Editing blng__InvoiceLine__c or blng__Invoice__c directly to correct amounts** — Invoice records are system-generated from billing schedule data. Direct edits create a permanent divergence between the invoice layer and the billing schedule layer. The next billing run overwrites the edit, and the audit trail shows an unexplained manual modification on a financial record. All amount corrections must go through `blng__BillingSchedule__c` or the credit memo process.

2. **Setting blng__Invoice__c.blng__Status__c = Paid manually without creating a payment allocation** — This marks the invoice as paid without recording a corresponding payment or allocation. The `blng__Payment__c.blng__UnallocatedAmount__c` remains at full value (the payment appears unused), and the `blng__Invoice__c` shows as paid with no allocation trail. AR reports and GL entries are corrupted. A reconciliation audit will surface this as a liability account mismatch.

3. **Ignoring blng__RevenueTransactionErrorLog__c during billing operations** — The error log is the only place where silent billing failures are recorded. Orgs that do not monitor it accumulate undetected revenue recognition gaps. By the time Finance discovers the gap, it may span multiple billing periods and require complex manual journal entries to correct.

## Official Sources Used

- Invoice-Based Revenue Recognition Reporting — https://help.salesforce.com/s/articleView?id=sf.blng_invoice_based_revenue_recognition_reporting.htm&type=5
- Understanding Revenue Recognition Process — https://help.salesforce.com/s/articleView?id=sf.blng_understanding_the_revenue_recognition_process.htm&type=5
- Billing Invoice Data Model — Revenue Cloud Data Model Gallery — https://developer.salesforce.com/docs/revenue/revenue-cloud/guide/blng-invoice-data-model.html
- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
