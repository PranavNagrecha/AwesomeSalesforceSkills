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
