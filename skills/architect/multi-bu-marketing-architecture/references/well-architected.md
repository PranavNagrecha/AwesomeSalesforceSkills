# Well-Architected Notes — Multi-BU Marketing Architecture

## Relevant Pillars

- **Security** — BU-level scoping is the primary data isolation boundary. Misconfigured Shared DE permissions or over-provisioned user roles can expose subscriber data across brands or regions, creating regulatory and reputational risk. Every cross-BU data sharing decision must be intentional and documented.
- **Operational Excellence** — Multi-BU organizations accumulate operational debt quickly if BU creation, user provisioning, and shared asset management are not governed by runbooks. Flat hierarchies and consistent naming conventions are the primary levers for keeping the org manageable as it scales.
- **Scalability** — Enterprise 2.0 supports unlimited Child BUs, but operational overhead (user management, SAP setup, reporting aggregation) grows non-linearly with hierarchy depth. Architectural decisions made early — particularly hierarchy depth and shared asset strategy — determine how well the org scales as new brands or markets are onboarded.
- **Reliability** — A global suppression list implemented as a Shared DE in the Parent BU is more reliable than distributed per-BU suppression lists, because it eliminates the risk of an opt-out being missed by a sibling BU. Centralized suppression is a reliability pattern as well as a compliance pattern.
- **Performance** — Shared DEs accessed by many Child BUs can become contention points if they are written to simultaneously from multiple BU automations. Write access to Shared DEs should be controlled and, where possible, centralized in the Parent BU's automation tier rather than distributed across Child BUs.

## Architectural Tradeoffs

**Flat vs. nested hierarchy:** A flat hierarchy (Parent + one tier of Children) is simpler to govern and produces cleaner native reporting, but may feel counterintuitive to organizations that think of their structure as genuinely hierarchical (continent → country → market). A nested hierarchy mirrors the org chart but introduces reporting gaps and multiplies admin surface area. The Well-Architected recommendation is to keep the hierarchy flat unless there is a documented, unavoidable operational need for a second tier.

**Centralized vs. distributed data management:** Centralizing shared assets (suppression lists, seed lists, master subscriber records) in the Parent BU increases governance quality and consistency but creates a dependency on Parent BU availability and admin access for all shared asset changes. Distributed management (each Child BU manages its own lists) reduces the dependency but increases the risk of inconsistency. The recommended balance is: centralize compliance-critical assets (suppression, consent), distribute operational assets (segment audiences, send-specific DEs) to the owning Child BU.

**Central admin vs. delegated BU admins:** A single central team managing all BUs from the Parent BU simplifies governance but creates a bottleneck. Delegated Child BU admins move faster but require careful role scoping to prevent cross-BU access. Most mature multi-BU implementations use a hybrid: a central team owns the Parent BU and shared assets; each Child BU has a local admin with the Marketing Cloud Administrator role scoped to that BU only.

## Anti-Patterns

1. **Attempting brand separation within a single BU via folder restrictions** — Folder-level role restrictions within a BU do not provide platform-enforced data isolation. Administrators and some standard roles can bypass folder restrictions through direct API access or cross-BU tooling. Use separate Child BUs for genuine brand separation.
2. **Creating deeply nested BU hierarchies to mirror org charts** — The org chart and the Marketing Cloud BU structure need not be identical. Hierarchy depth should be determined by operational and data segregation requirements, not by reporting relationships. Two or more tiers of Children introduce disproportionate admin complexity relative to their operational benefit.
3. **Assuming the All Subscribers enterprise list decides global suppression**: Master unsubscribe scope is a per-BU setting (`MasterUnsubscribeBehavior`: `ENTIRE_ENTERPRISE` or `BUSINESS_UNIT_ONLY`). Set it deliberately on every BU, and use a Shared DE referenced in each BU's sends for suppression rules the setting does not express.

## Official Sources Used

Read for this revision (2026-10-03), Marketing Cloud Engagement developer guide:

- BusinessUnit object: https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/businessunit.html. `MasterUnsubscribeBehavior` (`ENTIRE_ENTERPRISE`, `BUSINESS_UNIT_ONLY`), `SubscriberFilter`, `DefaultSendClassification`, `ParentID`, `Children`, edition IDs for Enterprise 2.0 and Enterprise 2.0 Business Unit.
- AccountUser object: https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/accountuser.html. `AssociatedBusinessUnits`, `DefaultBusinessUnit`.
- Account object: https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/account.html. Parent and child account properties for Enterprise and Enterprise 2.0.
- Integration Considerations: https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/integration-considerations.html. Single-BU token context, per-BU server-to-server enablement, `account_id`, package-owning BUs must stay active, deleted BUs cannot be recovered.
- Access Token for Server-to-Server Integrations: https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/access-token-s2s.html. `v2/token` request, `account_id` (target BU MID), 20-minute token lifetime.
- Authenticate Your SOAP API Calls: https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/authenticate-soap-api.html. `fueloauth` header; a token "doesn't flow down through child accounts".
- Installed Package Types: https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/installed-package-types.html. Legacy versus enhanced packages, credential sets per BU.
- RetrieveRequest object and Retrieve method: https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/retrieverequest.html and https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/retrieve.html. `ObjectType`, `Properties`, `QueryAllAccounts`, `MoreDataAvailable` above 2,500 records.
- Content Builder Sharing and Shared Categories: https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/sharing.html and https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/shared-categories.html. Enterprise 1.0 versus 2.0 sharing, up to 100 MIDs, `view`, `edit`, and `local` sharing types, enterprise-owned shared categories.
- Your Subdomain and Your Tenant's Endpoints: https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/your-subdomain-tenant-specific-endpoints.html. One tenant for the top-level Enterprise account and its business units.
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html (a direct fetch does not return the guide page; read via Wayback snapshot 2026-06-16).

Listed in the original version; Salesforce Help does not fetch, so these were not re-read and claims resting only on them are marked UNVERIFIED in `gotchas.md`:

- Salesforce Help: Business Units in Marketing Cloud Engagement — https://help.salesforce.com/s/articleView?id=sf.mc_overview_business_units.htm
- Salesforce Help: Shared Data Extensions in Enterprise 2.0 — https://help.salesforce.com/s/articleView?id=sf.mc_es_shared_data_extensions.htm
- Salesforce Help: Set Enterprise 2.0 Shared Data Extension Permissions — https://help.salesforce.com/s/articleView?id=sf.mc_es_set_enterprise_20_shared_data_extension_permissions.htm
- Salesforce Help: Managing Multiple Business Units (Marketing Cloud Account Engagement) — https://help.salesforce.com/s/articleView?id=sf.pardot_business_units_overview.htm
