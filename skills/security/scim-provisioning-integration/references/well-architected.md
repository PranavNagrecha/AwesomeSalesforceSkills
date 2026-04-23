# Well-Architected Notes — SCIM Provisioning

## Relevant Pillars

- **Security** — end-to-end deprovisioning closes the window on departed-user access.
- **Reliability** — IdP-driven attribute sync reduces drift between directory and Salesforce.
- **Operational Excellence** — group-to-entitlement mapping is declarative and auditable.

## Architectural Tradeoffs

- **Fine-grained PS-per-group vs PSG bundles:** fine-grained is auditable per-capability but harder to maintain at scale; bundles are lower effort but require discipline.
- **Pre-provisioning vs JIT on login:** pre-provisioning creates license exposure; JIT minimizes it but requires a login-time provisioning hook.
- **Freeze-first vs immediate deactivate:** freeze-first is safest for regulated orgs; immediate deactivate is simpler.

## Anti-Patterns

1. Mapping IdP groups directly to Salesforce Profiles.
2. Relying on deactivation alone to end access without revoking OAuth tokens.
3. Letting HR and IT own different pieces of the SCIM source-of-truth graph without a documented contract.

## Official Sources Used

- Salesforce SCIM 2.0 API — https://developer.salesforce.com/docs/atlas.en-us.identityImplGuide.meta/identityImplGuide/identity_scim.htm
- Okta Salesforce SCIM connector — https://help.okta.com/en-us/content/topics/apps/apps_about_salesforce.htm
- Microsoft Entra Salesforce provisioning — https://learn.microsoft.com/en-us/entra/identity/saas-apps/salesforce-provisioning-tutorial
- Salesforce Well-Architected Security — https://architect.salesforce.com/docs/architect/well-architected/trusted/secure
