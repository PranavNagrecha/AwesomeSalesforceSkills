# Well-Architected Notes — IP Range and Login Flow Strategy

## Relevant Pillars

- **Security** -- Login Flows are a security control layer that adds post-authentication verification. They enforce conditional MFA, IP-based routing, and compliance gates (terms acceptance). The core value proposition is defense-in-depth: adding intelligent friction beyond static credential verification without resorting to blanket IP blocking.

- **Reliability** -- A poorly designed Login Flow can prevent all users on a profile from logging in. Unhandled faults, missing Custom Metadata records, or broken Apex actions in a Login Flow create a single point of failure for org access. Reliability requires fault-tolerant flow design with Fault connectors on every action element and a graceful bypass path.

- **Operational Excellence** -- Login Flows must be documented, monitored, and maintainable. IP ranges stored in Custom Metadata are deployable and auditable. Login Flow assignments must be tracked because they are invisible in standard change sets and easy to forget during sandbox refreshes.

- **Performance** -- Every screen and Apex call in a Login Flow adds latency to the login process. The Well-Architected principle of efficient resource use applies directly: the happy path should be as fast as possible, with extra screens reserved for the conditional paths that need them.

## Architectural Tradeoffs

1. **Declarative vs. Apex-heavy Login Flows** -- Pure declarative flows (no Apex) are easier to maintain and audit but cannot reliably detect IP addresses or perform complex verification logic. Apex Invocable Actions add capability but introduce a code dependency that requires developer involvement for changes. The recommended balance is to use Apex only for IP detection and record updates, keeping all branching logic in declarative Decision elements.

2. **Profile-level vs. site-level assignment** -- Profile-level Login Flows are more granular (different profiles can have different flows) but do not apply to Experience Cloud sites when a site-level flow exists. Site-level flows are simpler to manage for external users but lose profile-level differentiation. The tradeoff is granularity vs. simplicity, and most organizations should use site-level for external users and profile-level for internal users.

3. **Conditional MFA in Login Flow vs. native Salesforce MFA** -- Salesforce's built-in MFA (enforced at the org level or via the "Multi-Factor Authentication for User Interface Logins" permission) is the platform-standard approach and covers all login scenarios. Login Flow conditional MFA is useful when the requirement is to add verification beyond native MFA for specific conditions (untrusted IP, first login in 90 days), but it should supplement, not replace, native MFA. Organizations that disable native MFA and rely solely on Login Flow MFA create a security gap for scenarios where the Login Flow is bypassed (API logins, SSO direct-to-org).

4. **Login latency vs. security depth** -- Adding screens to the login process increases security verification depth but degrades user experience. The tradeoff should be resolved by designing the flow so the common case (trusted IP, data already collected, terms already accepted) reaches the end element with zero screens displayed. Extra screens should only appear on the exception path.

## Anti-Patterns

1. **Using Login Flows as a replacement for profile Login IP Ranges** -- Login Flows add screens and verification but cannot hard-block login from an untrusted IP. If the requirement is to deny login entirely from outside a CIDR range, use profile Login IP Ranges (a network-layer control). Login Flows are for conditional friction, not hard deny.

2. **Testing Login Flows only in Flow Builder debug mode** -- Debug mode runs as the current admin with full permissions and does not replicate the Login Flow User context. Flows that pass debug testing frequently fail in production because Apex actions lack the expected permissions. Always test by logging in as a real user through the actual login page.

3. **Deploying a Login Flow without a fault-handling path** -- A Login Flow with no Fault connectors on Apex Actions or Get Records elements becomes a login-blocking failure mode. One broken Apex class or missing Custom Metadata record prevents all users on the assigned profile from accessing the org. Every action element must have a Fault path that routes to a user-friendly error screen with a "Continue" option.

## Official Sources Used

- Salesforce Help: Custom Login Flows -- https://help.salesforce.com/s/articleView?id=sf.security_login_flow.htm
- Salesforce Help: Set Up a Login Flow and Connect to Profiles -- https://help.salesforce.com/s/articleView?id=sf.security_login_flow_associate.htm
- Salesforce Help: Login Flow Examples -- https://help.salesforce.com/s/articleView?id=sf.security_login_flow_examples.htm
- Salesforce Help: Custom Login Flow Considerations -- https://help.salesforce.com/s/articleView?id=sf.custom_login_flow.htm
- Salesforce Security Implementation Guide: Login Flow Examples -- https://developer.salesforce.com/docs/atlas.en-us.securityImplGuide.meta/securityImplGuide/security_login_flow_examples.htm
- Salesforce Help: Restrict Login IP Addresses in Profiles -- https://help.salesforce.com/s/articleView?id=platform.login_ip_ranges.htm
- Salesforce Well-Architected Overview -- https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
