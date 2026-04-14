# Well-Architected Notes — Salesforce To Salesforce Integration

## Relevant Pillars

- **Security** — Cross-org integration requires secure credential management; Named Credentials and Connected Apps must use minimum-required OAuth scopes; cross-org data sharing must respect field-level security in both orgs.
- **Reliability** — Native S2S has no guaranteed delivery confirmation for record shares; API-based sync provides explicit retry and error handling; choosing the right pattern determines reliability.
- **Operational Excellence** — Cross-org sync failures are silent without monitoring; error logging and alerting are mandatory for production cross-org integrations.
- **Performance** — Native S2S SOAP API consumption is unpredictable at scale; REST API with Bulk API 2.0 provides controlled performance for high-volume scenarios.
- **Scalability** — Native S2S does not scale beyond moderate volumes; API-based sync scales to millions of records via Bulk API 2.0.

## Architectural Tradeoffs

**Native S2S vs API-based sync:** Native S2S is simpler to set up but is irreversible, consumes SOAP API limits on both orgs, and lacks fine-grained control. API-based sync requires more setup (Connected App, Named Credential) but is reversible, controlled, and provides explicit error handling.

**Real-time access vs replication:** Salesforce Connect provides real-time external access without data replication but has SOQL limitations. API-based sync replicates data to the consuming org enabling full SOQL but introduces data freshness lag.

**Platform Events vs REST API for event propagation:** Platform Events provide loose coupling and async delivery. REST API callouts provide synchronous confirmation but create tight coupling. The choice depends on whether the source org needs to know the target org processed the event successfully.

## Anti-Patterns

1. **Native S2S as default cross-org mechanism** — Native S2S is irreversible and SOAP-API-limit-expensive. Modern cross-org patterns provide better control and are fully reversible.

2. **Enabling native S2S without irreversibility warning** — Practitioners who enable S2S for testing cannot disable it. Always communicate the permanent nature before enabling.

3. **No error handling for cross-org API failures** — Cross-org API calls fail when the target org is down, rate-limited, or when OAuth tokens expire. Silent failures cause data drift.

## Official Sources Used

- Salesforce to Salesforce Help — https://help.salesforce.com/s/articleView?id=sf.business_network_s2s_overview.htm
- Integration Patterns and Practices — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

## Cross-Skill References

- `architect/multi-org-strategy` — upstream multi-org architecture
- `admin/integration-pattern-selection` — pattern selection before implementation
- `integration/error-handling-in-integrations` — error recovery design
