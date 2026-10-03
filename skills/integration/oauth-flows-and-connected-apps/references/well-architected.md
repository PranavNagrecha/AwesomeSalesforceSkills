# Well-Architected Notes - Oauth Flows And Connected Apps

## Relevant Pillars

- **Security** - OAuth flow selection is part of the security architecture, not just setup detail.
- **Reliability** - authentication failures are operational incidents, so token lifecycle planning matters.

## Architectural Tradeoffs

- **Client Credentials vs JWT bearer:** simpler secret management versus certificate-based posture.
- **Delegated user auth vs service-principal auth:** user context versus operational simplicity.
- **Broad scopes vs narrow scopes:** faster setup versus controllable blast radius.

## Anti-Patterns

1. **Username-password flow as the default** - easy to propose, poor to operate.
2. **Connected app with no owner** - governance failure disguised as setup.
3. **Treating scopes as the whole permission model** - integration principal design still matters.

## Official Sources Used

Fetched and read on 2026-10-03 unless marked.

- Identify Your Users and Manage Access (Identity guide), Spring '26: OAuth Authorization Flows (use cases, Block Authorization Flows to Improve Security), OAuth 2.0 JWT Bearer Flow for Server-to-Server Integration, OAuth 2.0 Client Credentials Flow for Server-to-Server Integration, External Client Apps and Connected Apps, Comparison of Connected Apps and External Client Apps Features, Connected App to External Client App Migration. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/identity.pdf
- Metadata API Developer Guide, Version 67.0: ExternalClientApplication, ExtlClntAppGlobalOauthSettings, ExtlClntAppOauthSettings, ExtlClntAppOauthConfigurablePolicies, ConnectedApp (ConnectedAppOauthConfig, ConnectedAppOauthPolicy), OauthOidcSettings. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Salesforce Well-Architected: Secure (Trusted), archived 2026-07-11. http://web.archive.org/web/20260711090005/https://architect.salesforce.com/docs/architect/well-architected/guide/secure.html
- Salesforce Well-Architected Overview, archived 2026-06-16. http://web.archive.org/web/20260616115029/https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Listed by an earlier version of this skill; help.salesforce.com returns a script shell and was not re-read (the same topics were read in the Identity guide PDF): OAuth Authorization Flows https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_flows.htm&type=5, Connected Apps Overview https://help.salesforce.com/s/articleView?id=sf.connected_app_overview.htm&type=5, JWT Bearer Token Flow https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_jwt_flow.htm&type=5
