# Well-Architected Notes — Integration User Management

## Relevant Pillars

- **Security** — This is the primary pillar for this skill. Integration user setup is a foundational security control: the Salesforce Integration license and Minimum Access - API Only Integrations profile enforce authentication boundary separation between interactive users and automated systems. Permission set layering enforces least privilege. The MFA waiver must be granted explicitly rather than assumed, maintaining the integrity of org-wide MFA enforcement. Failure to follow these patterns introduces credential sharing, privilege escalation risk, and audit gaps.
- **Performance** — Indirectly relevant. A well-scoped integration user with only the required objects and fields reduces query governor limit pressure and improves the predictability of API call behavior. A misconfigured user that pulls broad SOQL results due to over-permissioning can contribute to per-integration performance degradation.
- **Scalability** — Relevant when an org grows to support multiple integrations. Designing per-integration users with separate permission sets from the start allows integrations to be scaled, retired, or modified independently. A shared integration user with a monolithic permission set becomes a scalability bottleneck — changes to one integration's permissions risk breaking another.
- **Reliability** — Correct MFA waiver assignment directly affects integration reliability. An integration user without the waiver in an MFA-enforced org will fail intermittently or completely. Login History monitoring supports reliability by enabling early detection of authentication failures before they become outages.
- **Operational Excellence** — Auditability of integration user access is an operational requirement. Login History monitoring, documented MFA waiver justifications, and named permission sets per integration reduce the operational burden of access reviews and incident response. Consistent provisioning patterns (a checklist or automation) reduce the risk of human error during setup.

## Architectural Tradeoffs

**Least Privilege vs. Speed of Setup:** The Minimum Access - API Only Integrations profile grants zero object permissions by design. Every integration requires a custom permission set. This is slower to set up than assigning a profile with broad access but is required by Well-Architected Security principles. The overhead is one-time and the ongoing risk reduction is continuous.

**Per-Integration Users vs. Shared Integration User:** A single integration user shared across multiple integrations is operationally simpler but collapses the audit trail, makes revocation risky, and inflates the user's effective permission footprint. The Well-Architected recommendation is one user per logical integration boundary. The trade-off is license consumption; evaluate against the Salesforce Integration license pricing relative to the security and operational value.

**OAuth Client Credentials vs. Username-Password Flow:** Client credentials is the architecturally correct pattern for server-to-server integrations. Username-password flow is deprecated, transmits credentials in the request body, and cannot be used with the Minimum Access - API Only Integrations profile in some configurations. The trade-off is setup complexity (Connected App with client credentials flow requires more initial configuration) against security posture.

## Anti-Patterns

1. **Admin Profile as Integration Identity** — Assigning the System Administrator profile or a cloned admin profile to an integration user removes the API-only login restriction and grants far more permissions than any integration needs. This violates Security (privilege escalation, interactive login risk) and Operational Excellence (audit trail is polluted by admin-level access). Use the Minimum Access - API Only Integrations profile and targeted permission sets instead.

2. **Shared Integration User Across Multiple Integrations** — Using one integration user for multiple distinct integrations conflates audit trails, forces permission sets to cover multiple data domains, and makes credential rotation or revocation dangerous (rotating or disabling the user breaks all integrations simultaneously). Each integration should have its own dedicated user.

3. **Assuming MFA Exemption Is Automatic** — Treating the Salesforce Integration license as an automatic MFA bypass leads to integration outages when MFA enforcement is enabled or new users are provisioned. The exemption must be explicitly assigned and documented. Undocumented exemptions create compliance gaps during security audits.

## Official Sources Used

- Give Integration Users API Only Access — https://help.salesforce.com/s/articleView?id=sf.integration_user_api_only.htm
- Platform Integration User — https://help.salesforce.com/s/articleView?id=sf.platform_integration_user.htm
- Invoke REST APIs with the Salesforce Integration User and OAuth Client Credentials — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_oauth_and_connected_apps.htm
- Salesforce Security Guide — Monitor Login History — https://developer.salesforce.com/docs/atlas.en-us.securityImplGuide.meta/securityImplGuide/users_login_history.htm
- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
