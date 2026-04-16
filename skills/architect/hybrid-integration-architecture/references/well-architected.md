# Well-Architected Notes — Hybrid Integration Architecture

## Relevant Pillars

### Security
Hybrid integration surface area is a security-critical design decision. The choice between DMZ relay, Private Connect, mTLS, and IP allowlisting determines whether data traverses the public internet and how identities are verified. Hyperforce's ephemeral IP model means IP allowlisting provides no reliable authentication guarantee.

### Reliability
A DMZ relay is a single point of failure unless deployed in HA configuration. Private Connect relies on AWS PrivateLink SLA. Architecture must document fallback behavior when the relay or PrivateLink endpoint is unavailable — synchronous integrations must handle timeout/retry; asynchronous integrations must have a dead-letter or replay capability.

### Operational Excellence
Hybrid architectures introduce multiple runtime environments (Salesforce, middleware host, on-premises network). Observability requires log aggregation across all layers. MuleSoft Anypoint Monitoring, Splunk, or similar must collect from both the DMZ relay and the Salesforce side to enable end-to-end tracing.

## WAF Alignment

| WAF Area | Guidance |
|---|---|
| Security — Network Controls | mTLS or Private Connect, not IP allowlisting, on Hyperforce |
| Security — Connectivity | Private Connect (AWS PrivateLink) for private network; DMZ relay for VPN-equivalent on-premises reach |
| Reliability — HA | DMZ relay nodes deployed in HA pairs; PrivateLink target NLB across multi-AZ |
| Operational Excellence | End-to-end correlation IDs from Salesforce through relay to on-premises system |

## Cross-Skill References

- `integration/middleware-integration-patterns` — Middleware platform selection (MuleSoft, Boomi, Dell Boomi)
- `integration/change-data-capture-integration` — CDC for event-driven on-premises sync as alternative to polling relay
- `security/salesforce-shield-platform-encryption` — Field-level encryption at rest in Salesforce (distinct from in-transit gateway encryption)

## Official Sources Used

- Salesforce Help — Salesforce Private Connect: https://help.salesforce.com/s/articleView?id=sf.private_connect_overview.htm
- Salesforce Architects — Integration Patterns: https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
- Salesforce Architects — Hyperforce Architecture: https://architect.salesforce.com/docs/architect/infrastructure/guide/hyperforce-architecture
- MuleSoft Docs — Hybrid Deployment: https://docs.mulesoft.com/runtime-manager/deployment-strategies
- Salesforce Trust — IP Ranges: https://help.salesforce.com/s/articleView?id=sf.salesforce_app_ip_allowlist.htm
