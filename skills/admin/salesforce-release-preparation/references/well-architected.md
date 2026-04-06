# Well-Architected Notes — Salesforce Release Preparation

## Relevant Pillars

- **Operational Excellence** — Release preparation is a core operational discipline. The Well-Architected Framework's Operational Excellence pillar requires that changes to the system are managed with defined processes, tested before production exposure, and communicated to stakeholders. A structured release preparation cycle — notes triage, Release Update activation, preview testing, and stakeholder communication — is the direct implementation of Operational Excellence for Salesforce seasonal releases.

- **Reliability** — The Reliability pillar requires that the org continues to function as expected after a platform upgrade. Release Updates that are allowed to auto-activate without prior testing are a reliability risk: they can silently change behavior in business-critical automations, Apex code, or integrations. Proactive Release Update testing is the primary reliability control for seasonal releases.

- **Security** — Some Release Updates address security-relevant behavior: stricter CSRF protections, tighter Visualforce remote method restrictions, Lightning Locker or LWS behavior changes. Missing enforcement deadlines for security-related updates means the org may remain on a behavior that Salesforce has deprecated for security reasons. The Trusted pillar of the Well-Architected Framework requires keeping security controls current, which includes timely adoption of security-related Release Updates.

- **Performance** — Performance is a secondary pillar for release preparation. Some releases change governor limit behavior, query execution, or async job scheduling. Release notes items with a "Developer" or "Admin" impact related to Apex or SOQL may affect bulk operation performance and should be validated under load conditions, not just functional conditions.

- **Scalability** — Not a primary concern for this skill. Release preparation does not directly affect org data model or sharing model scalability.

## Architectural Tradeoffs

**Depth of preview testing vs. cost of maintaining a preview sandbox:** Enrolling a Partial Copy or Full Sandbox in preview gives the most production-realistic test signal, but those sandboxes have higher refresh costs and are often needed for parallel UAT. The tradeoff is a Developer or Developer Pro sandbox for preview (lower cost, less realistic data) versus a higher-tier sandbox for preview (higher cost, better fidelity). For most orgs, a Developer Pro sandbox refreshed specifically for preview is the right balance.

**Early voluntary activation vs. waiting for auto-activation:** Activating Release Updates early gives the team control over timing and monitoring. Auto-activation gives more time to prepare but removes timing control. The Well-Architected Operational Excellence pillar favors deliberate, timed changes over platform-controlled surprises. The recommended practice is always to activate voluntarily after sandbox validation.

**Admin-driven triage vs. developer-driven triage:** Some release changes require developer action even when tagged "Admin." Limiting triage to the admin team creates a handoff gap. The Operational Excellence approach assigns cross-functional ownership at the triage stage, not after a gap is discovered.

## Anti-Patterns

1. **Reactive Release Preparation** — Waiting until the week before the production upgrade to read release notes and test Release Updates. This eliminates the lead time needed to fix identified issues, leaves no time for stakeholder communication, and means any Release Update breakage is first discovered in production. The WAF Operational Excellence pillar explicitly requires proactive change management.

2. **Undifferentiated Release Notes Review** — Reading release notes cover to cover without applying Feature Impact filters, assigning owners, or cross-referencing feature areas. This produces inconsistent coverage and review fatigue. It is equivalent to deploying untriaged changes — the opposite of the WAF principle that all changes should be reviewed with appropriate rigor before production.

3. **Treating Release Updates as Optional Forever** — Some teams discover that Release Updates can be toggled off and treat the toggle as a permanent opt-out. Every Release Update has an enforcement date after which it cannot be turned off. Treating the toggle as permanent is a false assumption that sets up a future forced change with no preparation time.

## Official Sources Used

- Salesforce Help — Sandbox Preview Instructions (Knowledge Article 000391927): https://help.salesforce.com/s/articleView?id=000391927&type=1
- Salesforce Help — Release Updates: https://help.salesforce.com/s/articleView?id=sf.release_updates.htm&type=5
- Salesforce Help — Upgrade Release Schedule FAQ (Knowledge Article 005224913): https://help.salesforce.com/s/articleView?id=000005224913&type=1
- trust.salesforce.com — Planned Maintenance Calendar: https://status.salesforce.com/maintenance
- admin.salesforce.com — Be Release Ready: https://admin.salesforce.com/blog/2023/be-release-ready
- Trailhead — Advanced Release Readiness Strategies: https://trailhead.salesforce.com/content/learn/modules/advanced-release-readiness-strategies
- Salesforce Well-Architected Framework — Operational Excellence: https://architect.salesforce.com/docs/architect/well-architected/guide/operational-excellence.html
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
