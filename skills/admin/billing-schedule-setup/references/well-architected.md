# Well-Architected Notes — Billing Schedule Setup

## Relevant Pillars

### Reliability

Salesforce Billing's invoice generation depends on a chain of records (Legal Entity → Billing Policy → Billing Treatment → Billing Rule → BillingSchedule → Invoice Run). A missing or misconfigured link in this chain causes silent failures — invoices are not generated, with no error thrown. Reliability requires defensive configuration: validate every link at setup time, add monitoring on `blng__InvoiceRun__c` completion status, and build automated checks that confirm `blng__BillingSchedule__c` counts match OrderProduct counts after each Order activation.

Data Pipelines is a hard external dependency — if it is disabled during a sandbox refresh or org change, billing silently breaks. Include Data Pipelines status in org health checks and deployment verification steps.

### Performance

Invoice Runs execute as batch jobs processing approximately 300 billing schedule lines per chunk. Orgs with thousands of active subscription products can generate long-running batch chains. To keep runs within acceptable windows:
- Schedule Invoice Runs during off-peak hours via Scheduled Apex or a scheduled Flow.
- Avoid running bulk Order activations (thousands of Orders simultaneously) immediately before an Invoice Run — the schedule generation jobs and the Invoice Run batch may contend for Apex governor resources.
- Monitor batch completion time in Setup > Apex Jobs and set internal SLAs for Invoice Run duration.

### Operational Excellence

Billing schedule configuration is a dependency-ordered process that cannot be safely automated without understanding object relationships. Operational excellence requires:
- A documented setup runbook with the correct sequence: Legal Entity → Billing Policy → Tax Policy → Billing Treatment → Billing Rule → Product assignment.
- A sandbox refresh checklist that explicitly re-enables Data Pipelines and re-validates Billing Policy on Accounts.
- Automated Invoice Run scheduling so billing does not depend on manual admin action each period.
- Alerting on Invoice Runs that complete with zero invoices or with error status — these are often silent failures.

---

## Architectural Tradeoffs

### In-Advance vs. In-Arrears for Subscription Products

In-Advance is simpler operationally: invoices are generated before the period, cash is collected early, and there is no dependency on usage data. In-Arrears is more accurate for usage-based models but requires usage records to be imported before the Invoice Run executes. Choosing In-Arrears for non-usage products creates unnecessary operational complexity — In-Advance is the right default for pure subscription SaaS.

### Milestone Billing vs. Custom Invoice Plans for Professional Services

Milestone billing requires manual Invoice Run triggers per milestone but uses a simple configuration. Dynamic Invoice Plans allow fully custom schedules (different amounts on arbitrary dates) but require more upfront configuration. For engagements with three or fewer milestones with predictable amounts, Milestone billing is lower overhead. For complex multi-phase projects with variable payment schedules, Dynamic Invoice Plans provide the required flexibility without custom Apex.

### Batch Invoice Runs vs. Real-Time Invoice Generation

Salesforce Billing does not support real-time per-Order invoice generation through the standard managed package. All invoicing goes through batch Invoice Runs. Architects who need near-real-time invoicing (e.g., invoice immediately at Order activation) must trigger Invoice Runs via Apex or Flow immediately after activation — this works but creates risk of governor limit contention if many Orders activate simultaneously. Design for batch-first and only add trigger-based Invoice Runs where business requirements explicitly require immediate invoicing.

---

## Anti-Patterns

1. **Configuring Billing Policy at the Order Level Only** — Setting `blng__BillingPolicy__c` on the Order record and not on the Account record creates a configuration that appears correct but produces zero invoices. The Invoice Run engine reads the Billing Policy from the Account. Always set the Billing Policy on the Account.

2. **Using Standard Revenue Schedules to Drive Billing** — Enabling "Revenue Schedules" in standard Salesforce Setup (Product2 > Schedule > Revenue) does not create or affect `blng__BillingSchedule__c` records. These are entirely separate systems. Building revenue recognition logic on native OpportunityLineItem revenue schedules and expecting it to integrate with Salesforce Billing invoicing is an architectural dead end.

3. **Manual blng__BillingSchedule__c Creation for Backfill** — Directly inserting `blng__BillingSchedule__c` records via Data Loader or Apex to backfill historical orders bypasses the managed package trigger chain that marks records as invoice-eligible. Invoice Runs will silently skip these records. Backfill must go through Order reactivation or Salesforce Professional Services tooling.

---

## Official Sources Used

- Billing Process Overview — https://help.salesforce.com/s/articleView?id=sf.blng_billing_process_overview.htm
- Invoicing Products with Billing Schedules — https://help.salesforce.com/s/articleView?id=sf.blng_invoicing_products.htm
- Milestone Billing — https://help.salesforce.com/s/articleView?id=sf.blng_milestone_billing.htm
- Salesforce Billing Custom Objects — Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_blng_billingschedule.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
