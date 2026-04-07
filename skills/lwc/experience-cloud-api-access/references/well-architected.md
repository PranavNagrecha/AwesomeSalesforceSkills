# Well-Architected Notes — Experience Cloud API Access

## Relevant Pillars

- **Security** — The dominant concern for this skill. Guest user Apex must run `with sharing`. FLS on the guest profile is the hard enforcement boundary. External OWDs are the record-visibility boundary for all external users. API scope must be minimum necessary. Over-permissioning any of these layers creates data exposure at the platform boundary where external users interact with org data.
- **Reliability** — External user API calls consume the org's shared API request pool. High-volume portal use cases (especially guest user page loads triggering Apex queries) must be designed with cacheable=true, lazy loading, and API limit monitoring to avoid throttling internal integrations.
- **Operational Excellence** — External profiles and sharing configuration for API access are often undocumented and hard to audit. Sharing Debugger, the API Usage monitor, and event log files should be part of the operational runbook for sites that expose API access to external users.

## Architectural Tradeoffs

**Apex gateway vs. direct REST API access for external users**

For guest users, the Apex gateway is the only option — there is no alternative. For authenticated Customer Community Plus and Partner Community users, the choice between surfacing data through LWC Apex calls vs. direct REST API calls depends on the client:

- LWC components on the site should use `@AuraEnabled` Apex: it runs in user context, respects sharing, and does not require a separate OAuth flow.
- External applications (mobile apps, server-side integrations) use the REST API directly with user-context OAuth, which also respects sharing but requires the "API Enabled" profile permission and a Connected App.

Neither approach bypasses the sharing model. The choice is about the client type, not about security posture. Attempting to use a system-context integration user to avoid sharing complexity trades platform-enforced security for application-layer filtering — this is an anti-pattern.

**Customer Community license ceiling**

When the product requirements call for Customer Community Plus or Partner Community API capabilities but the current license is Customer Community, the architectural choice is either:
1. Upgrade the license (preferred, cleaner security model)
2. Build a mid-tier integration service that acts as a proxy, calls Salesforce using an integration user, and enforces the community user's data scope in application code

Option 2 requires documented compensating controls and explicit security review. It should not be the default recommendation.

## Anti-Patterns

1. **Running guest-accessible Apex `without sharing`** — Exposes all org records to unauthenticated users, regardless of the guest profile configuration. There is no architectural scenario where this is acceptable for public-facing Experience Cloud pages. Use `with sharing` or `inherited sharing` throughout the entire call chain.

2. **Using a sysadmin integration user as a proxy for Customer Community API access** — Bypasses the platform sharing model and introduces a high-privilege credential into an external-facing flow. Compensating application-layer filters are fragile and unaudited. The correct fix is to use the appropriate license tier or accept the architectural tradeoff explicitly.

3. **Treating external OWDs as inherited from internal OWDs** — External OWDs are a distinct, independently configurable layer. Assuming they match the internal OWD leaves data inaccessible to legitimate external users or, if someone sets internal OWDs too broadly, can inadvertently expose records. External OWDs must be configured and reviewed separately in every org.

## Official Sources Used

- Salesforce Well-Architected Overview — architecture quality framing, Security and Reliability pillars
  https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- REST API Developer Guide — REST resource behavior, authentication, API entitlements by license
  https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_what_is_rest_api.htm
- Apex Developer Guide — with sharing / without sharing / inherited sharing semantics, user context
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
- Secure Apex Classes (LWC docs) — CRUD/FLS enforcement patterns for component-facing Apex
  https://developer.salesforce.com/docs/platform/lwc/guide/apex-security
- Salesforce Help — Experience Cloud License Limitations — Customer Community API entitlement boundary
  https://help.salesforce.com/s/articleView?id=sf.networks_license_types_communities.htm
- Salesforce Help — Securely Share Sites with Guest Users — guest profile and guest user security model
  https://help.salesforce.com/s/articleView?id=sf.networks_guest_user_sharing.htm
- Salesforce Help — OAuth 2.0 for First-Party Apps — OAuth scope semantics for external users
  https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_user_agent_flow.htm
