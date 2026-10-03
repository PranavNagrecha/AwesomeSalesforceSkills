# Well-Architected Notes — Hybrid Integration Architecture

## Relevant Pillars

### Security
Hybrid integration surface area is a security-critical design decision. The choice between DMZ relay, Private Connect, mTLS, and IP allowlisting determines whether data traverses the public internet and how identities are verified. Hyperforce's published IP prefixes change between versions and are shared by every org in a region, so IP allowlisting provides no reliable authentication guarantee (corrected 2026-10-03 from "ephemeral IP model").

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
- `security/platform-encryption` — Field-level encryption at rest in Salesforce (distinct from in-transit gateway encryption)

## Official Sources Used

- Salesforce Help — Salesforce Private Connect: https://help.salesforce.com/s/articleView?id=sf.private_connect_overview.htm (help.salesforce.com does not fetch; licensing and enablement claims marked UNVERIFIED)
- Salesforce Architects — Integration Patterns: https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html (HTTP 403 on 2026-10-03; the PDF edition below was read instead)
- Salesforce Architects — Hyperforce Architecture: https://architect.salesforce.com/docs/architect/infrastructure/guide/hyperforce-architecture (HTTP 403 on 2026-10-03, not re-read)
- MuleSoft Docs — Hybrid Deployment: https://docs.mulesoft.com/runtime-manager/deployment-strategies (not re-read on 2026-10-03)
- Salesforce Trust — IP Ranges: https://help.salesforce.com/s/articleView?id=sf.salesforce_app_ip_allowlist.htm (help.salesforce.com does not fetch)
- Salesforce published IP ranges (machine-readable): https://ip-ranges.salesforce.com/ip-ranges.json: fetched 2026-10-03: `syncToken`, `createDate` 2026-07-06, prefixes for 24 AWS and GCP regions; basis for correcting the "ephemeral IPs" claim
- Integration Patterns and Practices, Spring '26 v66.0 (PDF): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/integration_patterns_and_practices.pdf: Security Considerations (two-way SSL, no WS-Security support, firewall protection), Appendix C (reverse proxy products, on-premises encryption gateways, Shield Platform Encryption, WS-* alternatives)
- Metadata API Developer Guide, Summer '26 (PDF): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf: `OutboundNetworkConnection` and `InboundNetworkConnection` (`AwsPrivateLink`, properties, status lifecycle), `NamedCredential` (`namedCredentialType` = `PrivateEndpoint`, `OutboundNetworkConnection` parameter, API 56.0+)
- Apex Developer Guide, Summer '26 (PDF): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf: "Invoking Callouts Using Apex" (no remote site setting needed with a named credential), "Callout Limits and Limitations" (10-second default timeout, 120-second cumulative cap)
- Government Cloud guide (Spring '26 edition, PDF): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/government_cloud.pdf: Salesforce Express Connect as the Government Cloud Plus private route

