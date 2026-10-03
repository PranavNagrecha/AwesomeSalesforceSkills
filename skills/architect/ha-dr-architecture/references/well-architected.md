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
  URL: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html (on 2026-10-03 this URL redirected to the architect.salesforce.com home page, so the guide was not re-read; pillar framing follows `standards/well-architected-mapping.md`)
- Salesforce Trust Site — real-time instance status, SLA documentation, maintenance notification
  URL: https://trust.salesforce.com
- Salesforce Trust Site Status API — instance status JSON API
  URL: https://api.status.salesforce.com/v1/instances/{instance}/status (fetched 2026-10-03 for NA224: `status`, `maintenanceWindow`, `Services`, `Incidents` with per-incident `status`, `Maintenances`; no authentication required)
- Salesforce Backup and Restore product documentation — native backup capabilities and restore mechanics
  URL: https://help.salesforce.com/s/articleView?id=sf.backup_restore_overview.htm (help.salesforce.com does not fetch; product claims marked UNVERIFIED)
- Salesforce Platform Events Developer Guide — event retention, replay, and delivery guarantees
  URL: https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_intro.htm
- Salesforce Integration Patterns — async integration and event-driven pattern selection
  URL: https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
- Hyperforce Architecture Overview — infrastructure model, data residency, region availability
  URL: https://help.salesforce.com/s/articleView?id=sf.hyperforce_overview.htm (help.salesforce.com does not fetch; Hyperforce claims marked UNVERIFIED)
- Platform Events Developer Guide, Summer '26 (PDF): "Event Retention in the Event Bus" (72 hours high-volume, 24 hours legacy standard-volume)
  URL: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/platform_events.pdf
- Change Data Capture Developer Guide, Summer '26 (PDF): change events retained for three days
  URL: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_change_data_capture.pdf
- Integration Patterns and Practices, Spring '26 v66.0 (PDF): outbound messaging retries (24 hours, 15 s to 60 min backoff, extendable to 7 days), message ID idempotency, platform events published once with no Salesforce-side retry, replay by replay ID
  URL: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/integration_patterns_and_practices.pdf
- Salesforce Developer Limits and Allocations Quick Reference (PDF served under the 262 path; the document carries no release label): Bulk API and Bulk API 2.0 batch allocation (15,000 per rolling 24 hours, shared) and 150,000,000 records per 24 hours
  URL: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_app_limits_cheatsheet.pdf
- Apex Developer Guide, Summer '26 (PDF): "Deleting Records" and "Restoring Deleted Records" (15-day Recycle Bin, undelete), "Triggers and Order of Execution" (restores run the full save path)
  URL: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Big Objects Implementation Guide, Summer '26 (PDF): `insertImmediate()` idempotent overwrite, `deleteImmediate()` 50,000-record batch, no triggers or flows on big objects
  URL: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/big_objects_guide.pdf
- Object Reference, Summer '26 (PDF): `Organization.InstanceName`
  URL: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf

