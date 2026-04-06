# Well-Architected Alignment — HA/DR Architecture

## Reliability Pillar

The Salesforce Well-Architected Reliability pillar requires that systems are designed to recover from failures, meet defined availability targets, and maintain data integrity under adverse conditions. HA/DR architecture is the primary vehicle for operationalizing reliability in a Salesforce context.

Key reliability practices this skill addresses:
- **Define and document RTO and RPO** — reliability targets must be explicit and measurable, not implicit assumptions.
- **Test recovery procedures** — a runbook that has never been tested is not a runbook; it is a hypothesis. Tabletop exercises and actual restore drills are required.
- **Design for partial failure** — not all Salesforce outages are total. Design integrations and user-facing processes to degrade gracefully rather than fail completely.
- **Monitor proactively** — Trust site monitoring is a reliability control. Discovering an outage through user reports is a reliability failure in the operational model.

## Operational Excellence Pillar

The Operational Excellence pillar covers the processes, tooling, and team practices needed to run Salesforce systems reliably over time.

Key operational excellence practices this skill addresses:
- **Runbook-driven incident response** — recovery actions must be documented, assigned, and tested before an incident occurs.
- **Automated alerting** — Trust site webhook/API integration with incident management tools is the operational excellence baseline for Salesforce org monitoring.
- **Post-incident review** — after any significant outage or recovery drill, capture findings and update the runbook. HA/DR architecture is a living design, not a one-time deliverable.
- **Ownership clarity** — the shared responsibility model must be explicitly documented so no one assumes Salesforce will handle a customer-responsibility item during an incident.

---

## Official Sources Used

- Salesforce Well-Architected Framework Overview — reliability and operational excellence pillars framing
  URL: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Trust Site — real-time instance status, SLA documentation, maintenance notification
  URL: https://trust.salesforce.com
- Salesforce Trust Site Status API — instance status JSON API
  URL: https://api.status.salesforce.com/v1/instances/{instance}/status
- Salesforce Backup and Restore product documentation — native backup capabilities and restore mechanics
  URL: https://help.salesforce.com/s/articleView?id=sf.backup_restore_overview.htm
- Salesforce Platform Events Developer Guide — event retention, replay, and delivery guarantees
  URL: https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_intro.htm
- Salesforce Integration Patterns — async integration and event-driven pattern selection
  URL: https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
- Hyperforce Architecture Overview — infrastructure model, data residency, region availability
  URL: https://help.salesforce.com/s/articleView?id=sf.hyperforce_overview.htm
