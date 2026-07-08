# Well-Architected Mapping: Connected Apps and Auth

## Pillars Addressed

### Security

Connected apps, integration users, and OAuth flows form a major part of the org's security boundary.

- Least-privilege auth reduces unnecessary access.
- Managed secrets and revocation procedures reduce incident blast radius.

### Operational Excellence

Auth choices affect how easily teams can deploy, rotate, and support integrations.

- Named Credential patterns reduce config drift across environments.
- Ownership and runbooks make auth failures supportable.

### Reliability

Stable token handling, clear endpoint management, and tested recovery steps improve integration uptime.

- Environment-safe config reduces deployment-time outages.
- Explicit flow choice reduces recurring auth failures.

## Pillars Not Addressed

- **User Experience** - user UX matters only when delegated auth is required; this skill is primarily about security and operability.
- **Performance** - the focus is authentication design and operability, not payload optimization or throughput tuning.

## Official Sources Used

- Salesforce Well-Architected Overview — security and operational framing for integration access
- REST API Developer Guide — OAuth and API usage context for connected-app design
- Integration Patterns — auth and system-boundary tradeoffs for integrations
- Salesforce Platform: New Connected Apps Can No Longer Be Created in Spring '26 (https://help.salesforce.com/s/articleView?id=005228017&language=en_US&type=1) — the default creation block via UI and Metadata API, the package-install exception, the Support-exception path, and that existing connected apps keep working
- Connected Apps and External Client Apps Features (https://help.salesforce.com/s/articleView?id=sf.connected_apps_and_external_client_apps_features.htm&type=5&language=en_US) — CA vs ECA feature parity: shared OAuth 2.0 / SAML / OpenID Connect / custom attributes / Canvas support, the 1GP-vs-2GP packaging split, and the sandbox-copy behavior gap
- Connected App to External Client App Migration (https://help.salesforce.com/s/articleView?id=xcloud.connected_app_to_external_client_app_migration.htm&language=en_US&type=5) — the documented migration flow, preserving the existing OAuth consumer key and secret
