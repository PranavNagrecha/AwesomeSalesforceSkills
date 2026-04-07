# Well-Architected Notes — Experience Cloud Multi-IdP SSO

## Relevant Pillars

- **Security** — Multi-IdP SSO is primarily a security design decision. Each auth provider is a trust boundary. The Federation ID is the canonical SAML trust anchor; the RegistrationHandler is the OIDC trust implementation. Incorrect configuration in either can allow assertion replay, user impersonation, or silent failures that block legitimate users. Security review must cover each IdP's assertion signing, the RegistrationHandler's matching logic, and the site's guest profile to ensure unauthenticated access is not inadvertently broadened.
- **Adaptability** — Supporting multiple IdPs in one org is an adaptability investment. New tenant segments (e.g., a new partner category with a different corporate IdP) can be onboarded by adding an Auth Provider record and a login button, without restructuring the org. The `community` routing parameter makes the architecture extensible to new sites without changes to existing configurations.
- **Reliability** — SSO login flows have more failure modes than password authentication: IdP downtime, certificate expiry, clock skew, and RegistrationHandler exceptions all block user access. Reliability design must include fallback authentication options for break-glass scenarios and monitoring for login history error rates per auth provider.

## Architectural Tradeoffs

**One org with multiple sites vs. multiple orgs per tenant:** The multi-site pattern reduces cost and operational overhead but requires careful permission design to ensure tenant data isolation. If two tenant segments have genuinely incompatible data models or compliance requirements (e.g., different data residency requirements), separate orgs may be warranted. Otherwise, one org with two Experience Cloud sites and two Auth Providers is the standard recommendation.

**SAML vs. OIDC per IdP:** SAML is more common in enterprise B2B contexts where corporate IT manages the IdP. OIDC is preferred for consumer/citizen contexts and social login. Neither is inherently more secure when correctly implemented. The choice is driven by what the external IdP supports, not by Salesforce preference. Both protocols can coexist as separate Auth Provider records in the same org.

**RegistrationHandler complexity vs. JIT provisioning:** For SAML, Just-In-Time (JIT) provisioning can auto-create or update User records from SAML attributes without Apex code. For OIDC, a RegistrationHandler is mandatory. If SAML is available and the provisioning logic is straightforward, JIT provisioning reduces Apex surface area and test maintenance. Use RegistrationHandler for OIDC or for SAML scenarios requiring complex user matching or multi-object creation.

## Anti-Patterns

1. **Creating one Experience Cloud site per IdP** — This multiplies maintenance burden, portal license consumption, sharing rule complexity, and release management surface. The platform supports multiple Auth Providers per org and multiple login buttons per site. Use that instead.
2. **Activating SAML SSO before populating Federation ID** — Brownfield orgs almost always have User records with blank `FederationIdentifier`. Activating SSO before this field is populated creates a hard production incident. The correct sequence is: populate Federation ID in sandbox, validate with SAML Assertion Validator, activate in sandbox, test with pilot users, then promote.
3. **Embedding Start SSO URLs without the `community` parameter in login page code** — Login page components built as custom LWC sometimes hardcode the Start SSO URL without the community parameter, meaning the URL must be changed every time the site URL changes. The community parameter should be derived from the site's base URL at render time, not hardcoded.

## Official Sources Used

- Salesforce Help — Add Authentication Provider to an Experience Cloud Site — https://help.salesforce.com/s/articleView?id=sf.sso_provider_addprovider.htm
- Salesforce Help — Configure an Authentication Provider Using OpenID Connect — https://help.salesforce.com/s/articleView?id=sf.sso_provider_openid_connect.htm
- Salesforce Help — SAML for Experience Cloud Sites — https://help.salesforce.com/s/articleView?id=sf.sso_saml_community.htm
- Salesforce Help — Salesforce as Service Provider and Identity Provider — https://help.salesforce.com/s/articleView?id=sf.sso_saml_salesforce_as_sp_and_idp.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
