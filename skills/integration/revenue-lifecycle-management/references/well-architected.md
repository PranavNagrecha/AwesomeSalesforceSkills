# Well-Architected Notes — Revenue Lifecycle Management

## Relevant Pillars

- **Reliability** — DRO fulfillment plan steps do not auto-retry on failure. Stalled plans require manual intervention. All auto-task callouts must be idempotent to support safe re-execution. Billing schedule creation failures must be caught and retried.
- **Scalability** — DRO handles parallel swimlane execution natively, reducing fulfillment cycle time. Order volume spikes may require monitoring DRO concurrency against org-level limits.
- **Operational Excellence** — RLM introduces a new fulfillment operations layer (DRO dashboard) that must be monitored alongside standard Salesforce automation monitoring. Runbooks for stalled DRO plans are essential.

## Architectural Tradeoffs

**DRO Auto-Tasks vs. Apex Triggers:** DRO Auto-Tasks (declarative autolaunched Flow callouts) are the preferred pattern for fulfillment logic. Apex triggers on Order or OrderItem objects can also react to activation but are harder to parallelize and monitor. For complex fulfillment logic, DRO is more maintainable.

**Amendment Billing Aggregation vs. Current Balance:** Amendment creates a new BillingSchedule rather than updating the existing one. Reporting on total contracted value requires aggregating across all BillingSchedule records per asset. Applications that display "current billing schedule" using a single record lookup will show only the latest amendment, not the full history.

**Native RLM vs. CPQ + Salesforce Billing:** If the org is already on CPQ + Salesforce Billing, migrating to RLM is a major project involving data migration, object model changes, and automation rebuild. Only recommend RLM for new implementations or documented migration projects.

## Anti-Patterns

1. **Mixing blng__* Objects with RLM Standard Objects** — Using legacy Salesforce Billing SOQL or Apex in an RLM org causes runtime errors and data model confusion. Enforce a clear product-layer boundary.

2. **Assuming Billing Schedules Are Auto-Created** — Designing fulfillment workflows that assume BillingSchedule records appear automatically after order activation leads to missing billing data. Billing schedule creation must be an explicit DRO step.

3. **No DRO Stall Monitoring** — Relying on users to report unfulfilled orders instead of monitoring DRO for stalled plans creates invisible bottlenecks. Implement DRO fulfillment dashboard monitoring with alerting.

## Official Sources Used

- Revenue Lifecycle Management Overview — https://help.salesforce.com/s/articleView?id=sf.revenue_lifecycle_management.htm
- Dynamic Revenue Orchestrator — Trailhead — https://trailhead.salesforce.com/content/learn/modules/dynamic-revenue-orchestrator-foundations/meet-dynamic-revenue-orchestrator
- Revenue Cloud Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.revenue_lifecycle_management_dev_guide.meta/revenue_lifecycle_management_dev_guide/rlm_get_started.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
