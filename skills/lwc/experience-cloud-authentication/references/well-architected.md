# Well-Architected Notes — Experience Cloud Authentication

## Relevant Pillars

- **Security** — Authentication is the primary security gate for an Experience Cloud site. Misconfigured auth providers, missing Federation ID matching, or incorrect handler implementations can expose data to the wrong user or allow account takeover. All external identity flows must be tested in sandbox before production, and Registration Handlers must never expose internal user data through error messages.
- **Adaptability** — Authentication requirements change as sites scale. Using the correct handler interface (`Auth.RegistrationHandler` vs `Auth.HeadlessSelfRegistrationHandler`) ensures the flow can be extended without a full rewrite. Headless flows decouple the identity layer from the UI, enabling mobile and web surfaces to share the same authentication backend.
- **Reliability** — Auth provider callback URLs, Federation ID matching, and headless handler assignments are all points of silent failure. A missing `community` parameter or a handler interface mismatch produces no compile error but breaks the login flow entirely. Observability (debug logs, Login History in Setup) is essential for diagnosing failures in production.

## Architectural Tradeoffs

**VF login page vs LWC login page:** VF is simpler to build for Aura sites and has a long support history. LWC login pages for LWR sites provide full component composability and align with the modern Salesforce development model. If migrating a site from Aura to LWR, the login page must be rebuilt as an LWC — plan this migration work explicitly.

**Standard RegistrationHandler vs ConfigurableSelfRegHandler:** `Auth.RegistrationHandler` is sufficient for social login where the IdP provides identity. `Auth.ConfigurableSelfRegHandler` adds lifecycle hooks (`getUserAttributes`, `postRegister`) that are valuable when self-registration must integrate with lead capture, approval workflows, or custom profile selection. Use the more capable interface only when the additional hooks are genuinely needed.

**Standard passwordless vs headless passwordless:** Standard passwordless is faster to implement (a configuration toggle) but requires the Salesforce-hosted login page. Headless passwordless requires two Apex handler implementations but supports fully branded native mobile apps. If the experience will ever be delivered through a mobile app, choose headless from the start to avoid rearchitecting later.

**Federation ID matching vs email matching:** Email matching is convenient but fragile — users can change their email in the IdP, and the Salesforce record retains the old email, causing a broken match on the next login. Federation ID is the immutable IdP subject identifier and is the correct long-term matching key for any social login implementation at scale.

## Anti-Patterns

1. **Using email as the primary match key in RegistrationHandler** — Email addresses change. A user who updates their Google email will fail to match their existing Salesforce record and receive a duplicate user on next login. Use `FederationIdentifier` as the primary match key and fall back to email only as a one-time migration path.

2. **Skipping sandbox validation for auth provider callback URLs** — Auth provider callback URLs are environment-specific (`myDomain.sandbox.my.site.com` vs `myDomain.my.site.com`). Testing only in production or skipping the sandbox round-trip means the first real-user failure is a production incident. Always register both the sandbox and production callback URLs with the IdP and test the full round-trip in sandbox.

3. **Building one Registration Handler for both headless and standard flows** — The handler interface requirements are incompatible. A single class cannot implement both `Auth.RegistrationHandler` and `Auth.HeadlessSelfRegistrationHandler` and serve both flows. Design separate handler classes from the start to avoid logic entanglement.

## Official Sources Used

- Salesforce Help: Authenticate Experience Cloud Site Users — https://help.salesforce.com/s/articleView?id=sf.networks_authentication.htm
- Salesforce Help: Passwordless Login — https://help.salesforce.com/s/articleView?id=sf.networks_member_self_reg_passwordless.htm
- Salesforce Help: Headless Passwordless Login Settings — https://help.salesforce.com/s/articleView?id=sf.experience_headless_passwordless_login.htm
- Salesforce Developer: HeadlessSelfRegistrationHandler Interface — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_interface_Auth_HeadlessSelfRegistrationHandler.htm
- Salesforce Developer: HeadlessUserDiscoveryHandler Interface — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_interface_Auth_HeadlessUserDiscoveryHandler.htm
- Salesforce Developer: Auth.RegistrationHandler Interface — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_auth_registration_handler.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- LWC Best Practices — https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
