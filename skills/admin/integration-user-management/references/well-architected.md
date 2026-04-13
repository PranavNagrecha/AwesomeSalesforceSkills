# Well-Architected Notes — Integration User Management

## Relevant Pillars

- **Security** — Dedicated integration users with API-only profiles and least-privilege permission sets limit the blast radius of compromised credentials. The Minimum Access - API Only Integrations profile ensures that even with valid credentials, an attacker cannot access the Salesforce UI.
- **Operational Excellence** — Named, documented integration users per integration system enable rapid incident response (disable a single user to cut off a compromised integration without affecting others), clear access audit trails, and predictable quarterly access reviews.

## Architectural Tradeoffs

**One integration user vs. one per integration system:** A single "integration user" shared across all integrations creates a single point of failure (disabling it affects all integrations), makes audit logs uninterpretable (all API calls look the same), and makes least-privilege impossible (the user needs all permissions any integration needs). One integration user per system is the minimum; one per integration function is preferred for complex deployments.

**Username-password OAuth vs. JWT bearer flow:** Username-password flows for integration authentication are simpler to set up but send credentials over the network and require MFA waivers. JWT bearer flow uses a certificate pair (private key on the integration server, public key in the connected app) and never sends credentials — it is inherently MFA-resistant and more secure. For all production integrations, JWT bearer flow is the recommended authentication pattern.

## Anti-Patterns

1. **Admin profile for integration users** — Granting System Administrator or cloned admin profiles to avoid permission configuration. Creates severe least-privilege violations and enables UI login capability for service accounts.

2. **Shared integration user across multiple systems** — Using a single "IntegrationUser@org.com" for all integrations. Disabling it breaks all integrations simultaneously; audit logs are uninterpretable; permission sets must cover all integration needs.

3. **No MFA waiver for new integration users in MFA-enforced orgs** — New integration users created after MFA enforcement is enabled will fail authentication without an explicit MFA waiver. This is consistently overlooked because existing integration users are grandfathered.

## Official Sources Used

- Give Integration Users API Only Access — https://help.salesforce.com/s/articleView?id=sf.integration_user_api_only_access.htm&type=5
- Platform Integration User — https://help.salesforce.com/s/articleView?id=sf.sf_platform_integration_user.htm&type=5
- Invoke REST APIs with the Salesforce Integration User and OAuth Client Credentials — https://developer.salesforce.com/docs/apis/rest/en/invoke-rest-apis-integration-user.html
- Salesforce Security Guide — Monitor Login History — https://developer.salesforce.com/docs/atlas.en-us.securityImplGuide.meta/securityImplGuide/salesforce_security_guide_login_history.htm
