# Well-Architected Notes — Analytics Data Governance

## Relevant Pillars

- **Trusted** — This is the primary pillar. Practitioners must ensure that CRM Analytics datasets containing sensitive or personal data are governed with the same rigor as the source CRM records. The absence of native data classification propagation and the license-gated nature of audit logging create structural gaps that must be explicitly compensated for through design decisions.

- **Security** — Access to CRM Analytics datasets must be auditable. Event Monitoring (license-gated) is the only mechanism for producing an evidence-based audit trail of dataset access. Without it, there is no defensible record of who accessed what analytics data and when. Security design must account for this constraint early — retrofitting Event Monitoring into an established compliance program is expensive and disruptive.

- **Operational Excellence** — Retention enforcement in CRM Analytics is entirely operational (no native TTL), which means it must be actively maintained: recipe schedules monitored, version cleanup verified, and governance registers kept current. Teams that treat retention as a one-time setup will experience retention SLA breaches when recipes fail silently.

- **Adaptable** — As Salesforce evolves CRM Analytics (e.g., Event Log Objects in Summer '24, potential future dataset column tagging via Data Cloud / Data 360), governance architectures should be built to accommodate new mechanisms without requiring full redesign. The REST API lineage approach is stable; ELO-based audit pipelines should be layered on top of, not replacing, the existing CSV-based pipeline.

---

## Architectural Tradeoffs

**Event Monitoring add-on cost vs. audit coverage:** The Event Monitoring add-on is a licensed add-on with significant cost at enterprise scale. Teams sometimes attempt to compensate by relying on CRM-layer audit mechanisms (Field History Tracking, Setup Audit Trail) for analytics governance. This substitution is invalid: neither mechanism captures CRM Analytics dataset access events. The tradeoff decision is binary — either the org licenses Event Monitoring and gains audit capability, or it does not and must accept the audit gap with documented compensating controls.

**Recipe-based retention vs. API-based deletion:** Using a scheduled recipe to enforce retention (via date filter + dataset overwrite) is operationally simpler but depends on recipe reliability. API-based deletion (REST API dataset version delete) provides more surgical control but requires custom tooling and scheduled automation outside Salesforce. For most teams, the recipe approach is sufficient with proper monitoring; API-based deletion should be reserved for on-demand erasure events (GDPR, incident response).

**Manual governance register vs. hypothetical future automation:** As of Spring '26, there is no automated way to propagate Salesforce Data Classification into CRM Analytics. Teams must choose between maintaining a manual governance register (operationally burdensome but immediately achievable) or waiting for a platform feature that may or may not arrive. The Well-Architected recommendation is to implement the manual register immediately and design it to be replaceable by an automated mechanism when one becomes available, rather than deferring governance entirely.

**Dataset lineage via REST API vs. Data Manager UI:** The Data Manager UI is adequate for exploratory lineage inspection on small orgs. For compliance documentation, automated audits, or orgs with 50+ recipes, the REST API approach is necessary. Build the lineage script once and schedule it to run as part of the governance cadence.

---

## Anti-Patterns

1. **Assuming data governance is inherited from the CRM layer** — treating Salesforce Data Classification, Field History Tracking, or Platform Encryption as sufficient governance for data that has been ingested into CRM Analytics. Once data crosses the ingestion boundary, it is governed entirely by CRM Analytics controls (sharing rules, predicates, Event Monitoring) — not CRM controls. This assumption leads to real compliance gaps that are discovered too late, typically during an audit.

2. **Treating dataset deletion as complete erasure** — deleting the current version of a dataset and closing a GDPR or retention enforcement ticket without also deleting all stored versions. CRM Analytics version history is a feature (enabling rollback) that becomes a liability in erasure scenarios. Every deletion runbook must include explicit version enumeration and deletion.

3. **Building an audit program that depends on Event Monitoring without confirming the license** — designing a compliance architecture that promises dataset-level access audit logs and then discovering that the Event Monitoring add-on is not licensed. This is a common failure mode in orgs that purchase Salesforce under a standard Enterprise agreement and assume all security features are included. Confirm licensing before committing to audit capability in any compliance documentation.

---

## Official Sources Used

- Analytics Security Implementation Guide (Spring '26) — dataset governance controls, Event Monitoring event types for analytics, sharing and access audit architecture
  URL: https://help.salesforce.com/s/articleView?id=analytics.analytics_security_implementation_guide

- Event Monitoring Analytics App — Event Monitoring add-on scope, WaveChange and WaveInteraction event types, log file retention configuration
  URL: https://help.salesforce.com/s/articleView?id=sf.bi_app_admin_wave.htm

- Enable CRM Analytics and Event Monitoring Integration — enabling Wave event types under Event Monitoring add-on, license prerequisites
  URL: https://help.salesforce.com/s/articleView?id=sf.bi_app_event_monitor_enable_select_PSL.htm

- CRM Analytics Limits and Considerations (Spring '26) — dataset version retention behavior, dataset storage limits, recipe scheduling constraints
  URL: https://help.salesforce.com/s/articleView?id=analytics.bi_limitations.htm

- CRM Analytics REST API Developer Guide (Spring '26) — /wave/dataflows, /wave/recipes, /wave/datasets, /wave/datasets/{id}/versions endpoints
  URL: https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_rest.meta/bi_dev_guide_rest/bi_rest_overview.htm

- Salesforce Well-Architected Overview — Trusted pillar framing, governance and audit design principles
  URL: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
