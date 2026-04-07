# Well-Architected Notes — Marketing Cloud Connect

## Relevant Pillars

- **Security** — The connector user is a privileged integration credential with API access to CRM data. It must be protected like any service account: dedicated profile, exempted from expiration, documented in the org's identity and access management inventory. The connector user's access scope (Org-Wide vs BU) determines which CRM records Marketing Cloud can reach — over-permissive scope violates least-privilege principles. GDPR/CCPA deletion compliance requires explicit handling in both Salesforce and Marketing Cloud, as SDS does not propagate deletions automatically.

- **Reliability** — MC Connect sync is asynchronous and 15-minute cadence. Any automation that depends on real-time SF data in MC (e.g., a Journey triggered by a SF record update) must account for this lag. Triggered send failures are silent from Salesforce's perspective — reliability requires explicit monitoring in Marketing Cloud send logs. Connector user credential changes break sync with no immediate alert, making the connector user a single point of failure that requires a monitoring and alerting strategy.

- **Operational Excellence** — The 250-field limit on SDS objects is silent and will re-emerge after every deployment that adds fields to a synced object. A field-count audit must be part of the org's release checklist. Scope configuration is not version-controlled — it is UI-configured in both Salesforce and Marketing Cloud, creating drift risk during sandbox refresh cycles or new BU additions.

- **Scalability** — SDS sync load is determined by the number of synchronized objects, field counts, and record volumes. Very large orgs (millions of Contacts) can experience extended initial sync times and elevated API consumption. The 15-minute sync interval is fixed and cannot be accelerated; architectures requiring near-real-time data sync should use MC Connect triggered sends or a custom API integration, not SDS.

- **Performance** — Triggered sends are appropriate for transactional, low-volume email. High-volume batch sends should use Marketing Cloud Journey Builder with data imported via SDS SQL queries or data feed, not triggered sends. Misusing triggered sends at scale can exhaust Marketing Cloud API limits and cause silent send failures.

## Architectural Tradeoffs

**Org-Wide Scope vs Business Unit Scope**

Org-Wide scope simplifies configuration and ensures all records are accessible for sends from any BU. However, it violates data governance if different BUs should operate on distinct customer subsets (e.g., regional divisions, separate brands). BU-specific scope enforces isolation but requires careful alignment between Salesforce record ownership/territory and MC BU assignment — misalignment is the #1 cause of missing subscriber counts.

**SDS + SQL vs Journey Builder Data Feeds**

SDS with SQL query activities is the standard pattern and requires no additional Marketing Cloud licensing beyond MC Connect. It introduces a 15-minute sync lag and requires Automation Studio SQL knowledge. For near-real-time data needs or complex cross-object audience logic, a Mulesoft or custom REST integration can push data directly into Marketing Cloud DEs outside the SDS framework, at the cost of significantly higher implementation complexity.

**Triggered Sends vs Journey Builder Entry Events**

Triggered sends (via MC Connect Flow action) are low-latency and transactional-classified. They are appropriate for single-email transactional communications. Journey Builder entry events support multi-step, multi-channel journeys and have richer analytics, but introduce Journey Builder licensing requirements and are not appropriate for high-priority transactional messages that must bypass commercial suppression.

## Anti-Patterns

1. **Using a shared admin account as the connector user** — When a human admin's account is used as the connector user, any password reset, profile change, or Multi-Factor Authentication enforcement breaks MC sync without warning. The connector user must be a dedicated, purpose-built Salesforce user treated as integration infrastructure.

2. **Targeting SDS data extensions directly in sends** — SDS DEs are read-only and lack a designated sendable relationship. Targeting them directly either fails or produces unexpected results. All sends must use a sendable DE built on top of the SDS DE via SQL query or Contact Builder relationship. Bypassing this by manually marking an SDS DE as sendable corrupts the Contact Builder relationship model.

3. **Ignoring GDPR/CCPA compliance gap between SF and MC** — Treating Salesforce record deletion as sufficient for data subject deletion requests without performing a corresponding Marketing Cloud Contact Delete leaves personal data in MC data extensions, in violation of data protection regulations. These are two separate systems that each require explicit deletion steps.

## Official Sources Used

- Salesforce Help — Marketing Cloud Connect Overview: https://help.salesforce.com/s/articleView?id=sf.mc_co_marketing_cloud_connect.htm
- Salesforce Help — Set Up Marketing Cloud Connect: https://help.salesforce.com/s/articleView?id=sf.mc_co_set_up_marketing_cloud_connect.htm
- Salesforce Help — Synchronized Data Sources: https://help.salesforce.com/s/articleView?id=sf.mc_co_synchronized_data_sources.htm
- Salesforce Help — Synchronized Data Sources Best Practices: https://help.salesforce.com/s/articleView?id=sf.mc_co_best_practices_synchronized_data.htm
- Salesforce Help — Configure Scope for Marketing Cloud Connect: https://help.salesforce.com/s/articleView?id=sf.mc_co_configure_scope.htm
- Salesforce Help — Marketing Cloud Connect Triggered Sends: https://help.salesforce.com/s/articleView?id=sf.mc_co_triggered_send.htm
- Salesforce Help — Marketing Cloud Connect Connector User: https://help.salesforce.com/s/articleView?id=sf.mc_co_create_a_connector_user.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
