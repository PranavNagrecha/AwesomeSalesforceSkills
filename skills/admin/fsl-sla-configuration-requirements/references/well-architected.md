# Well-Architected Notes — FSL SLA Configuration Requirements

## Relevant Pillars

- **Reliability** — FSL SLA configuration is primarily a reliability concern. Entitlement processes with correctly wired milestone actions provide automated alerting before breach, reducing the risk of undetected SLA failures. The milestone completion Flow is a reliability dependency: without it, success actions never fire and breach tracking is incomplete. Well-Architected Reliable principle: build systems that detect and surface failure conditions proactively.

- **Operational Excellence** — Dispatchers and operations managers need real-time visibility into SLA risk. The WorkOrderMilestone related list with TargetDate, CompletionDate, and IsViolated columns directly enables this. Entitlement assignment automation (Flow populating EntitlementId from Service Territory) reduces manual intervention and eliminates a common source of SLA gaps caused by forgotten entitlement lookups.

- **Customer 360** — FSL SLA commitments are contractual. Breaching them damages customer trust and may have financial consequences. Configuring entitlement processes correctly — with the right process type, territory-aligned Business Hours, and auto-completion automation — ensures that SLA performance data in Salesforce reflects actual field outcomes and can be reported to customers and leadership accurately.

- **Security** — Not a primary concern for entitlement process configuration itself, but relevant for milestone action email alerts (do not send internal SLA breach data to customer-facing addresses) and for the entitlement records (ensure only authorized users can modify entitlement lookups on Work Orders to prevent SLA gaming).

- **Performance** — Work Order entitlement processes do not create meaningful query or DML load under normal conditions. The milestone completion Flow should use bulk-safe collection patterns (loop over a collected list, then batch-update) rather than DML inside loops to avoid governor limit issues on high-volume Work Order organizations.

## Architectural Tradeoffs

**One process per tier vs. milestone-level overrides:** Using one entitlement process with milestone-level Business Hours overrides reduces the number of process records but cannot vary time limits by tier. If the org has multiple SLA profiles that differ only in Business Hours (not time limits), one process with milestone overrides is simpler. If time limits also vary, separate processes are required. Default to separate processes unless the requirement is confirmed as Business-Hours-only variation — this avoids a future refactor.

**Flow vs. Apex for milestone completion:** A Record-Triggered Flow is sufficient for standard milestone completion on Work Order status change. Apex is justified only when completion logic is conditional on complex business rules (e.g., only complete the Resolution milestone if all Work Order Line Items are closed, not just the Work Order header). Use Flow for the simple case; escalate to Apex only if conditional logic cannot be expressed in Flow.

**Operating Hours alignment responsibility:** Deciding whether the FSL admin or the Service Cloud/entitlement admin owns Business Hours alignment is an operational governance decision. Misalignment is the most common configuration gap in multi-team FSL implementations. Assign explicit ownership and document the alignment mapping in the org runbook.

## Anti-Patterns

1. **Single Case Entitlement Process Reused for Work Orders** — Applying a Case-type entitlement process to Work Order records produces no milestone tracking. The correct architecture requires creating a new entitlement process of type Work Order for FSL use cases. This is a hard platform constraint, not a best-practice recommendation.

2. **No Milestone Completion Automation Deployed** — Deploying an FSL SLA configuration without a Flow (or Apex trigger) to set `WorkOrderMilestone.CompletionDate` results in all milestones appearing permanently open. Success actions never fire, SLA met/not-met reporting is unusable, and the operations team loses trust in SLA data. Milestone completion automation is a required deliverable — it is not optional.

3. **Business Hours and Operating Hours Left Unaligned** — Configuring Operating Hours on Service Territories and Business Hours on entitlement processes independently, without ensuring they match per territory, creates invisible SLA clock behavior. The milestone timer pauses at unexpected times and the SLA may appear met in Salesforce when it was actually violated in the field (or vice versa). Alignment must be verified at configuration time and re-verified whenever Operating Hours are changed.

## Official Sources Used

- Salesforce Help: Set Up Entitlements for Work Orders — https://help.salesforce.com/s/articleView?id=sf.entitlements_work_orders.htm
- Salesforce Help: Entitlements and Milestones Overview — https://help.salesforce.com/s/articleView?id=sf.entitlements_overview.htm
- Salesforce Help: Business Hours in Entitlement Management — https://help.salesforce.com/s/articleView?id=sf.entitlements_biz_hours.htm
- Trailhead: Use Entitlements with Work Orders — https://trailhead.salesforce.com/content/learn/modules/field-service-lightning-quick-look/use-entitlements-with-work-orders
- Salesforce Well-Architected: Reliable — https://architect.salesforce.com/docs/architect/well-architected/guide/reliable.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Object Reference: WorkOrderMilestone — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_workordermilestone.htm
