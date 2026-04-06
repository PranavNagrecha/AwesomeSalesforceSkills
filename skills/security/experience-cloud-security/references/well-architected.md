# Well-Architected Notes — Experience Cloud Security

## Relevant Pillars

- **Security** — Experience Cloud security is directly a security pillar concern: external OWD, Sharing Sets, and guest user hardening define the data access boundary for external users. Misconfiguration is a direct path to unauthorized data exposure.
- **User Experience** — Security controls must not impede legitimate portal users. Overly restrictive external OWD or missing Sharing Sets cause portal users to see empty lists, creating support burden and trust issues.
- **Operational Excellence** — Changes to external OWD trigger background sharing recalculation jobs that must be monitored. Security configuration for Experience Cloud sites must be audited periodically as objects and relationships change.

## Architectural Tradeoffs

- **Sharing Sets vs Apex sharing:** Sharing Sets are declarative and maintainable but only support objects with Account/Contact lookup relationships. Apex sharing is more flexible but requires code maintenance and a re-sharing trigger mechanism when the lookup relationship changes.
- **External OWD restrictiveness vs Sharing Set coverage:** More restrictive external OWD reduces the risk surface but requires complete Sharing Set coverage for all objects portal users need. Missing Sharing Set entries result in silent data access failures.
- **Guest user functionality vs security:** Guest user pages require some access to display content, but each permission granted expands the attack surface. Prefer Apex with `with sharing` and explicit field access over broad guest profile permissions.

## Anti-Patterns

1. **Relying on internal OWD to restrict external users** — Internal OWD controls internal user access, not external. External users have a separate external OWD. If only internal OWD is configured and external OWD is left at its default, external users may have broader access than intended.
2. **Using "without sharing" Apex classes accessible to guest profile** — Guest users calling `without sharing` Apex bypass all data security controls. All Apex accessible to guest or portal users must use `with sharing` or explicitly enforce CRUD/FLS.
3. **Not reviewing guest user profile after site creation** — Default guest profiles created during site setup may include object permissions that are appropriate for internal developers but not for anonymous visitors.

## Official Sources Used

- Salesforce Security Implementation Guide — External OWD and Sharing Sets — https://developer.salesforce.com/docs/atlas.en-us.securityImplGuide.meta/securityImplGuide/networks_setting_light_users.htm
- Experience Cloud Developer Guide — Secure Sites: Authenticated and Guest Users — https://developer.salesforce.com/docs/atlas.en-us.communities_dev.meta/communities_dev/communities_dev_security_overview.htm
- Salesforce Help — Securely Share Experience Cloud Sites — https://help.salesforce.com/s/articleView?id=sf.networks_security.htm&type=5
- Salesforce Security Guide — https://help.salesforce.com/s/articleView?id=sf.security_overview.htm&type=5
