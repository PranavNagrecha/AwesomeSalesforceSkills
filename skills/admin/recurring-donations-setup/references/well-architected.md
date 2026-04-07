# Well-Architected Notes — Recurring Donations Setup

## Relevant Pillars

- **Reliability** — The nightly NPSP recurring donations batch is critical infrastructure. If it fails silently, status transitions stop, rollup fields go stale, and new installment Opportunities are not created. Reliability requires active monitoring of the batch job, alerting on failures, and documented re-run procedures.
- **Operational Excellence** — ERD introduces a schedule-driven architecture (npe03__RecurringDonationSchedule__c) that practitioners must understand to operate correctly. Documentation, training, and runbooks covering the single-installment constraint, the Effective Date pattern, and the batch recalculation cycle are essential for sustainable operations.
- **Performance** — The nightly batch recalculates rollup fields (Total Paid Amount, Number of Paid Installments) across all active Recurring Donations. In large orgs (50,000+ Recurring Donations), batch chunking and scheduling strategy matter. Running the batch during off-peak hours and verifying governor limits are not being hit prevents silent batch aborts.
- **Security** — Recurring Donation records often contain sensitive donor financial data and giving history. Field-level security and object-level sharing rules must be configured appropriately to prevent unauthorized access. The `npe03__RecurringDonationSchedule__c` object, which contains amount and frequency history, should have the same access controls as the Recurring Donation itself.

## Architectural Tradeoffs

**Single-installment vs. full-horizon Opportunities:** ERD's one-at-a-time Opportunity model reduces pipeline clutter and prevents premature revenue recognition but means future giving projections must be derived from schedule calculations, not from Opportunity record counts. Orgs that rely on Opportunity-based revenue forecasting must adapt their reporting approach to read from schedule objects for projection data.

**Batch recalculation vs. real-time triggers:** NPSP uses a nightly batch rather than real-time triggers for status transitions and rollup recalculation. This is a deliberate scalability choice — real-time recalculation at scale would hit governor limits. The tradeoff is latency: status and rollup changes are not instant. Orgs with same-day reporting requirements must account for this batch delay.

**Effective Date changes vs. immediate updates:** Using Effective Date for schedule changes protects in-flight Opportunities but introduces a two-schedule transition window where both old and new schedule records are Active. Any query logic must handle this window correctly by also filtering on Effective Date. Immediate updates are simpler but risk corrupting the current open Opportunity's amount.

## Anti-Patterns

1. **Pre-creating twelve future installment Opportunities manually** — In ERD, pre-creating future Opportunities bypasses NPSP's schedule-driven creation logic, creates records the batch does not own (leading to duplicates), and breaks rollup calculations. Always let NPSP create installment Opportunities via the batch. If future projections are needed, read from the schedule object.

2. **Editing pledged Opportunity fields directly instead of using schedule changes** — Direct edits to open pledged Opportunities are temporary: the nightly batch may overwrite them. This creates a confusing experience for staff and leads to data integrity issues in giving history. All intended persistent changes (amount, frequency, date) must go through the schedule change interface using an Effective Date.

3. **Ignoring batch job health as a monitoring concern** — Treating the nightly NPSP batch as invisible infrastructure until something breaks results in days of stale status data, un-created installments, and inaccurate rollup totals before anyone notices. Proactive batch monitoring via Salesforce Scheduled Jobs, error email alerts, or a third-party monitoring tool is a reliability requirement, not optional.

## Official Sources Used

- NPSP Recurring Donations Overview — https://help.salesforce.com/s/articleView?id=sfdo.RD2_Overview.htm
- Configure Recurring Donations (NPSP) — https://help.salesforce.com/s/articleView?id=sfdo.RD2_Configure.htm
- Manage Recurring Donations — https://trailhead.salesforce.com/content/learn/modules/nonprofit-success-pack-recurring-donations
- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
