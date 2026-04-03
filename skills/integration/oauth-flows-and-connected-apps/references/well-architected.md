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

- OAuth Authorization Flows - https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_flows.htm&type=5
- Connected Apps Overview - https://help.salesforce.com/s/articleView?id=sf.connected_app_overview.htm&type=5
- JWT Bearer Token Flow - https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_jwt_flow.htm&type=5
