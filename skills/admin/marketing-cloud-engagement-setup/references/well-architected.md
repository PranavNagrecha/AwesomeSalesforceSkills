# Well-Architected Notes — Marketing Cloud Engagement Setup

## Relevant Pillars

- **Security** — Business Unit isolation enforces data segregation between brands, regions, or compliance domains. User role assignments at the BU level control which team members can access subscriber data, send live campaigns, or modify account-level settings. The principle of least privilege is directly applicable: Content Creator and Analyst roles should be the default; Administrator and Marketing Cloud Administrator roles must be explicitly justified. Authenticated sending domains (SPF, DKIM, DMARC) on Sender Profiles protect brand reputation and prevent spoofing.

- **Reliability** — Correct Send Classification type (Commercial vs. Transactional) determines whether business-critical emails (order confirmations, security alerts) reliably reach subscribers regardless of opt-out status. Misconfiguration here causes silent delivery failures. Reply Mail Management configuration ensures bounce and reply handling does not become a silent backlog that corrupts subscriber status over time.

- **Operational Excellence** — A documented Send Classification naming convention and a role assignment matrix reduce configuration drift as teams change. Cross-BU IP coordination policies prevent one team's campaign decisions from degrading deliverability for others. Runbooks for BU provisioning (including the support case requirement) prevent project delays.

- **Scalability** — The Enterprise 2.0 BU model scales horizontally: new brands, regions, and product lines get their own BU with isolated data, content, and subscriber management. The alternative — a single BU with folder-based segmentation — does not scale and creates compounding operational risk as volume grows.

- **Performance** — Dedicated IP warm-up planning directly affects deliverability performance. Because the IP is shared across BUs, volume planning must account for combined send throughput across all BUs, not just individual BU projections.

## Architectural Tradeoffs

**BU-per-brand vs. single BU with segmentation:**
BU isolation is the architecturally correct choice whenever distinct brands, legal entities, or compliance boundaries are involved. The tradeoff is operational overhead (each BU needs its own Sender Profiles, Delivery Profiles, Send Classifications, and role assignments configured independently). The single-BU approach trades this overhead for reduced governance complexity but creates subscriber data commingling, cross-team visibility risk, and ambiguous unsubscribe semantics.

**Custom roles vs. standard roles:**
Standard roles cover most use cases and require no maintenance. Custom roles are appropriate when a standard role grants more access than needed (e.g., a role between Content Creator and Administrator). The tradeoff: custom roles must be recreated per BU with no inheritance mechanism, creating a maintenance burden in accounts with many BUs.

**Commercial vs. Transactional Send Classification:**
Transactional classification enables delivery to opted-out subscribers for legally transactional messages. The tradeoff is legal exposure: any promotional content sent under Transactional classification is a CAN-SPAM violation. The operational tradeoff is the governance overhead of ensuring the Transactional classification is used only for approved message types.

## Anti-Patterns

1. **Folder-based brand separation within a single BU** — Using Email Studio folders to separate brand content instead of provisioning separate BUs. This provides no access control enforcement, comingles subscriber lists, and creates compliance risk. The folder structure is cosmetic; the platform enforces no data isolation. Use separate BUs for distinct brands or compliance boundaries.

2. **Assigning Marketing Cloud Administrator role broadly** — Granting Marketing Cloud Administrator to any user who needs cross-BU access, rather than scoping users to only the BUs they genuinely need to manage. Marketing Cloud Administrator grants account-level Setup access including IP configuration, parent account settings, and all BU data. This role should be restricted to a small number of dedicated account administrators.

3. **Using a single Commercial Send Classification for all message types** — Reusing one Send Classification for both promotional and transactional emails. This causes transactional messages to be silently suppressed for opted-out subscribers. Create dedicated Send Classifications per message category with explicit Type settings.

## Official Sources Used

- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Marketing Cloud Engagement — Business Units Help: https://help.salesforce.com/s/articleView?id=sf.mc_overview_business_units.htm
- Marketing Cloud Engagement — Roles and Permissions: https://help.salesforce.com/s/articleView?id=sf.mc_overview_roles.htm
- Marketing Cloud Engagement — Sender Profiles: https://help.salesforce.com/s/articleView?id=sf.mc_es_sender_profile.htm
- Marketing Cloud Engagement — Delivery Profiles: https://help.salesforce.com/s/articleView?id=sf.mc_es_delivery_profile.htm
- Marketing Cloud Engagement — Send Classifications: https://help.salesforce.com/s/articleView?id=sf.mc_es_send_classification.htm
- Marketing Cloud Engagement — Reply Mail Management: https://help.salesforce.com/s/articleView?id=sf.mc_es_reply_mail_management.htm
- CAN-SPAM Act Compliance Requirements: https://www.ftc.gov/business-guidance/resources/can-spam-act-compliance-guide-business
