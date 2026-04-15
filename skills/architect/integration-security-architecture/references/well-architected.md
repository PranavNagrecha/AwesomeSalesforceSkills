# Well-Architected Notes — Integration Security Architecture

## Relevant Pillars

- **Security** — This is the primary pillar for this skill. Every integration represents a potential attack surface: inbound API calls that could be spoofed, outbound credentials that could be leaked, transport channels that could be intercepted. The authentication mechanism selection (mTLS, OAuth, Private Connect) and the certificate lifecycle management strategy are direct security controls. Principle of least privilege applies to OAuth scope selection — Connected Apps should request the minimum scopes required for the integration's data access needs.

- **Reliability** — Certificate expiry is a reliability risk: expired mTLS certificates or JWT signing certificates cause integration failures that are often misdiagnosed. Certificate rotation procedures and expiry tracking directly affect integration uptime. IP allowlisting on Hyperforce is a reliability anti-pattern because the non-deterministic nature of Hyperforce IP rotation produces intermittent failures that are hard to diagnose and resolve.

- **Operational Excellence** — Certificate inventory management, rotation schedules, and decommissioning procedures are operational discipline requirements. The 50-certificate org limit means poor operational hygiene (never retiring old certificates) eventually blocks new integrations. Centralizing integration authentication through an API gateway improves operational visibility: a single audit log, single set of credentials to rotate, and single point for rate limiting and throttling.

- **Performance** — mTLS adds latency to every TLS handshake (one additional round-trip for the client certificate exchange). For high-frequency callouts (>100/second), the cumulative latency impact should be measured. This is rarely a blocking concern but should be documented in performance-sensitive integrations.

- **Scalability** — The 50-certificate hard limit is a scalability constraint. Architecture decisions made at low integration volume (one cert per integration) that seem harmless early become blockers at scale. Designing for certificate portfolio headroom from the start — shared certs, gateway consolidation — is a scalability decision.

---

## Architectural Tradeoffs

### mTLS vs OAuth-Only for Inbound Authentication

mTLS adds a transport-layer identity proof on top of the application-layer OAuth token. This defense-in-depth approach is preferred for high-sensitivity integrations. The tradeoff is operational overhead: certificates must be managed, distributed to external systems, and rotated. For lower-sensitivity integrations on non-Hyperforce infrastructure, OAuth 2.0 with Client Credentials may be sufficient. The decision point is data sensitivity and compliance requirement, not preference.

### API Gateway Consolidation vs Direct Named Credentials

A centralized API gateway improves security posture (single audit trail, rate limiting, reduced Salesforce certificate budget usage) at the cost of adding an infrastructure component that must be maintained, scaled, and secured. Direct Named Credentials are simpler to set up but create a distributed security configuration that is hard to audit holistically. The inflection point is typically 5–8 integrations: below that, direct Named Credentials are manageable; above that, gateway consolidation pays off.

### Salesforce Private Connect vs mTLS for Hyperforce

Private Connect is architecturally cleaner (no public internet exposure at all) but has higher setup complexity, licensing cost, and lead time. mTLS over the public internet is adequate for most integrations when the certificate management is sound. Private Connect is reserved for integrations with the most stringent data handling requirements or where the external system already operates in a VPC that can establish PrivateLink connectivity.

---

## Anti-Patterns

1. **IP Allowlisting as the Primary Authentication Mechanism for Hyperforce** — IP-based access control for Salesforce integrations assumes stable, predictable IP addresses. Hyperforce's dynamic infrastructure makes this assumption false. Teams that build IP allowlists against Hyperforce orgs create integrations that work initially and fail unpredictably as IPs rotate. The correct control is cryptographic identity proof via mTLS, which is independent of network topology.

2. **Single Certificate Serving Multiple Authentication Roles** — Using one certificate for both OAuth JWT signing and mTLS client authentication is an anti-pattern because the two roles have different CA trust requirements, different lifecycle considerations, and different configuration paths. Conflating them means that if either role requires a certificate change (CA rotation on the remote side, for example), both roles are disrupted. Design each certificate for a single, explicit purpose.

3. **Certificate Sprawl Without Retirement Process** — Creating a new certificate for every integration without a corresponding retirement process fills the 50-cert limit without deliberate architectural decisions. Each certificate should have a named owner, documented purpose, expiry date, and a retirement trigger (integration decommissioning). Running a quarterly certificate audit against the active integration list is a minimum operational control.

4. **Hardcoded Credential References in Apex or Flow** — Storing OAuth tokens, client secrets, or certificate-related configuration in Apex custom settings, custom metadata, or hard-coded Apex strings bypasses the Named Credential and External Credential architecture entirely. This is a security anti-pattern (credentials in source control, no rotation mechanism) and an operational anti-pattern (manual updates required everywhere the credential is referenced). All credential material must be stored in Named Credentials and External Credentials.

---

## Official Sources Used

- Salesforce Integration Patterns and Practices — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
- Preferred Alternatives to IP Allowlisting on Hyperforce — https://help.salesforce.com/s/articleView?id=sf.security_networkaccess.htm
- Salesforce Well-Architected: Security — https://architect.salesforce.com/docs/architect/well-architected/guide/security.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Certificate and Key Management (Salesforce Help) — https://help.salesforce.com/s/articleView?id=sf.security_keys_about.htm
- Named Credentials as Callout Endpoints — https://help.salesforce.com/s/articleView?id=sf.named_credentials_about.htm
- Salesforce Private Connect Overview — https://help.salesforce.com/s/articleView?id=sf.salesforce_private_connect.htm
