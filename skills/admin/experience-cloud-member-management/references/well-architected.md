# Well-Architected Notes — Experience Cloud Member Management

## Relevant Pillars

- **Security** — External user access is a direct security boundary. Every license type, profile, and sharing rule decision determines what data external users can see and modify. Overly permissive profiles, misconfigured guest user access, or incorrect license choices can expose CRM data to unauthorised parties. Apply least-privilege principles: choose the lowest-capability license that meets the business requirement and keep external profiles as restrictive as possible.
- **Operational Excellence** — License seat management, user provisioning workflows, and periodic audits of deactivated users are operational processes, not one-time configuration. Without runbooks and monitoring, orgs silently exhaust license pools or accumulate dormant users who consume seats. Automate onboarding flows where possible and schedule regular user audits.
- **Reliability** — Self-registration flows depend on correctly configured default accounts, active sites, and valid handler classes. A misconfigured catch-all account or a syntax error in a custom `Auth.ConfigurableSelfRegHandler` brings down the entire self-registration path with opaque error messages. Validate end-to-end in a sandbox before activating in production.

## Architectural Tradeoffs

**Self-registration (declarative) vs custom Apex handler:** The declarative Configurable Self-Registration page (no code) is simpler to deploy and maintain but offers limited post-registration customisation. A custom `Auth.ConfigurableSelfRegHandler` Apex class adds flexibility (dynamic account assignment, domain allow/deny, enrichment calls) at the cost of additional code maintenance, testing, and Apex governor limit exposure. Prefer the declarative option unless a specific business requirement cannot be met without code.

**Profile-based membership vs manual user addition:** Profile-based membership scales automatically — any user with the correct profile gets site access immediately. This is efficient for large user populations but means access control shifts entirely to profile assignment. Manual user addition provides per-user vetting at the cost of administrative overhead. Choose based on the trust level of the user population and the required vetting rigour.

**Shared catch-all account vs per-partner accounts for self-registered users:** A single catch-all account is simpler and always required for self-reg defaults, but it collapses the sharing boundary — all self-registered users on that account can potentially see each other's records depending on sharing rules. For B2B scenarios where self-registered users should be isolated from one another, consider a post-registration automation (Flow or Apex trigger) that moves the new Contact/User to their own Account after registration.

## Anti-Patterns

1. **Using internal profiles for external users** — Assigning a Salesforce-license profile to an external user and expecting it to work on an Experience Cloud site. Internal profiles cannot be added to site membership and the user will see "Insufficient Privileges" on login. Always use external profiles tied to the correct Experience Cloud license.
2. **Skipping the default account for self-registration** — Enabling self-registration without setting a Default New User Account leads to silent failures that are hard to debug. This is the most common first-time setup mistake and should be the first thing checked when self-registration does not work.
3. **Ignoring license capacity until it hits zero** — Treating license management as a set-and-forget task. Deactivated users do not automatically free seats. Orgs that churn external users without periodic cleanup will unexpectedly hit license limits in production, blocking new user creation.

## Official Sources Used

- Experience Cloud Help — Add Members to Your Experience Cloud Site: https://help.salesforce.com/s/articleView?id=sf.networks_customize_members.htm
- Experience Cloud Help — Configure Self-Registration: https://help.salesforce.com/s/articleView?id=sf.networks_self_reg.htm
- Apex Reference Guide — Auth.ConfigurableSelfRegHandler: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_auth_configurable_selfreghandler.htm
- Experience Cloud Help — Experience Cloud Licenses: https://help.salesforce.com/s/articleView?id=sf.users_license_types_communities.htm
- Salesforce Well-Architected Overview — architecture quality framing: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
