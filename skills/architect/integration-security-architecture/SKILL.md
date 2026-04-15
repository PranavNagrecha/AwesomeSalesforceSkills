---
name: integration-security-architecture
description: "Architecture-layer guidance for securing Salesforce integrations: mTLS mutual authentication, OAuth 2.0 flow selection, API gateway placement, IP allowlisting strategy on Hyperforce, and certificate lifecycle management. Trigger keywords: mTLS, mutual TLS, Hyperforce IP allowlisting, Salesforce Private Connect, certificate limit, integration authentication architecture. NOT for basic Connected App setup, Named Credential field configuration, or Apex callout code patterns — see integration/named-credentials-setup and integration/apex-callouts-and-limits."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "how to secure Salesforce integrations on Hyperforce without IP allowlisting"
  - "mTLS mutual TLS configuration strategy for Salesforce outbound and inbound calls"
  - "should I use IP whitelisting or mTLS to authenticate third-party systems calling Salesforce"
  - "Salesforce Private Connect vs VPN vs API gateway for integration security"
  - "certificate management strategy when approaching 50 certificate limit per org"
  - "OAuth signing certificate versus mTLS client certificate — what is the difference"
  - "API gateway pattern for multi-system Salesforce integration security"
tags:
  - integration-security
  - mtls
  - oauth
  - hyperforce
  - certificate-management
  - api-gateway
  - named-credentials
  - private-connect
inputs:
  - "Deployment infrastructure: Hyperforce vs Classic (determines whether IP allowlisting is viable)"
  - "Integration direction: Salesforce-initiated (outbound), external-initiated (inbound), or bidirectional"
  - "Number of active integrations and current certificate inventory"
  - "Regulatory or compliance requirements (PCI-DSS, HIPAA, FedRAMP) that constrain auth choices"
  - "Whether a dedicated API gateway or middleware layer exists in the architecture"
outputs:
  - "Integration authentication architecture decision (mTLS, OAuth flow selection, Private Connect recommendation)"
  - "Certificate strategy including naming convention, lifecycle ownership, and org limit headroom plan"
  - "IP allowlisting go/no-go assessment with Hyperforce migration impact"
  - "API gateway placement diagram with security control responsibilities mapped"
  - "Completed integration-security-architecture-template.md for design sign-off"
dependencies:
  - integration/named-credentials-setup
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-15
---

# Integration Security Architecture

This skill activates when designing or reviewing the security model for Salesforce integrations at the architecture level — selecting authentication mechanisms (mTLS, OAuth flows), deciding whether an API gateway is needed, evaluating IP allowlisting viability on Hyperforce, and planning certificate lifecycle strategy. Use this skill before configuring individual Named Credentials or Connected Apps.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Hyperforce vs Classic**: IP allowlisting strategy is fundamentally different. Hyperforce IPs are ephemeral and not published in a stable static list — IP-based allowlisting cannot reliably secure Hyperforce integrations. Confirm the org's deployment model before recommending any perimeter controls.
- **Integration direction**: Inbound (external system calling Salesforce APIs), outbound (Salesforce calling external endpoints), and bidirectional each require different security controls. mTLS applies at different layers for each direction.
- **Current certificate count**: The hard org-level limit is 50 certificates. In multi-integration orgs, this limit constrains the architecture. Confirm the current count before designing a certificate-per-integration strategy.
- **Existing middleware or API gateway**: If an API gateway (MuleSoft, AWS API Gateway, Apigee) already exists, mTLS termination may happen at the gateway rather than the Salesforce endpoint — this changes where certificates are managed.

---

## Core Concepts

### mTLS Is Not a Replacement for OAuth — They Operate at Different Layers

Mutual TLS (mTLS) authenticates the transport channel — it proves that the connecting party holds the private key for a specific certificate. OAuth 2.0 authenticates the application identity and authorizes data access scopes. These two mechanisms are complementary and are configured independently in Salesforce.

In practice: an outbound callout from Salesforce to an external REST API may use OAuth 2.0 JWT Bearer for authorization while simultaneously presenting a client certificate over mTLS for transport-layer authentication. The Named Credential holds the OAuth token; the certificate is configured separately in Setup > Certificate and Key Management and referenced in the Named Credential endpoint URL via port 8443.

The mTLS client certificate (proving Salesforce's identity to the remote) and the JWT signing certificate (used to sign the JWT assertion in OAuth 2.0 flows) are separate certificates with separate configuration paths. Treating them as the same object is the most common implementation error in this domain.

### Hyperforce Changes the IP Allowlisting Calculus

On Classic Salesforce infrastructure, org IP addresses were relatively stable and could be allowlisted at external firewalls. This approach does not work on Hyperforce. Hyperforce distributes Salesforce tenants across cloud provider infrastructure where IP addresses are dynamically assigned and not published in a stable, machine-readable allowlist.

Salesforce's official guidance is to use mTLS or Salesforce Private Connect as alternatives to IP allowlisting on Hyperforce. Attempting to build an IP allowlist for Hyperforce-based orgs leads to unpredictable authentication failures as IPs rotate, with no advance notice.

### Salesforce Private Connect Eliminates the Public Network Attack Surface

Salesforce Private Connect (formerly Salesforce Hyperforce Private Connect) establishes private network connectivity between Salesforce and external systems using AWS PrivateLink or similar cloud-provider private connectivity. Traffic never traverses the public internet, eliminating the IP allowlisting question entirely and reducing the attack surface to network-layer controls rather than application-layer certificate management.

Private Connect is appropriate when: the integration handles highly sensitive data, compliance requirements mandate private network paths (FedRAMP, HIPAA), or the external system already operates within a VPC that can establish PrivateLink connectivity. Private Connect has its own setup complexity and licensing implications — it is not the default answer for every integration.

### The 50-Certificate Org Limit Requires Portfolio Thinking

Salesforce enforces a hard limit of 50 certificates per org in Certificate and Key Management. In orgs with many integrations, this limit constrains architecture decisions. Strategies to stay within the limit include: shared certificates across integrations that trust the same remote endpoint, wildcard certificates where the external system supports them, and planned certificate retirement as integrations are decommissioned.

Certificate expiry is a reliability risk. Certificates are not auto-renewed in Salesforce. A lapsed certificate causes integration failures that may appear as authentication errors or connection timeouts depending on how the receiving system responds to expired client certs.

---

## Common Patterns

### Pattern A: mTLS for Inbound Calls from External Systems to Salesforce APIs

**When to use:** An external system (ERP, partner API, middleware) must call Salesforce REST or SOAP APIs, and IP allowlisting is unavailable (Hyperforce) or insufficient for the compliance requirement.

**How it works:**
1. Enable mutual authentication on the Salesforce org's connected app or Experience Cloud site that exposes the API endpoint.
2. The external system presents a client certificate when initiating the TLS handshake.
3. Salesforce validates the client certificate against a trusted certificate authority (CA) uploaded to Certificate and Key Management.
4. The external system also supplies an OAuth 2.0 access token (typically obtained via Client Credentials or JWT Bearer flow) for application-level authorization.
5. Both checks must pass — transport authentication (certificate) and application authorization (OAuth token).

**Why not IP allowlisting alone:** On Hyperforce, Salesforce IPs rotate. On Classic, a compromised IP range still allows any actor within that range to call the API — IP allowlisting proves network location, not identity.

### Pattern B: Outbound mTLS from Salesforce to External REST Endpoint

**When to use:** Salesforce makes outbound callouts to an external API that requires the caller to present a client certificate (common in financial services, government, and healthcare integrations).

**How it works:**
1. Generate or import the client certificate in Setup > Certificate and Key Management.
2. Configure the Named Credential with the external endpoint URL, appending `:8443` to the hostname if the endpoint uses port 8443 for mTLS (this port must be explicitly specified — Salesforce does not default to 8443).
3. In the Named Credential's authentication settings, select the certificate.
4. The OAuth credentials (if the endpoint also requires OAuth) are configured separately in the External Credential linked to this Named Credential.

**Why the port matters:** Salesforce Named Credentials require the port to be explicit in the URL when connecting to non-standard ports. A Named Credential URL of `https://api.example.com` will not present the client certificate on port 8443 — the URL must be `https://api.example.com:8443`.

### Pattern C: API Gateway as Security Perimeter for Multi-System Integration

**When to use:** Multiple external systems need to call Salesforce, or Salesforce needs to call multiple external endpoints, and centralizing security controls (rate limiting, authentication, logging) is an architectural requirement.

**How it works:**
1. Place the API gateway (MuleSoft, Apigee, AWS API Gateway) between Salesforce and all external systems.
2. The gateway terminates mTLS from external callers and re-authenticates to Salesforce using a single OAuth 2.0 Connected App identity.
3. Salesforce only needs to trust the gateway's certificate, not the certificates of every external caller.
4. The gateway handles IP allowlisting, rate limiting, payload inspection, and audit logging.

**Why not direct integration for each system:** Each direct integration requires its own certificate, OAuth app, and Named Credential configuration. In orgs approaching the 50-certificate limit, centralizing via an API gateway is both a security and a certificate-management optimization.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Hyperforce org, external system calling Salesforce | mTLS client certificate on inbound connection + OAuth for authorization | Hyperforce IPs are not stable; IP allowlisting will fail intermittently |
| Classic org, low-sensitivity integration, static external IP | IP allowlisting is viable but pair with OAuth 2.0 | Classic IPs are more stable; still need application-layer auth |
| Highly sensitive data, compliance-mandated private network | Salesforce Private Connect | Eliminates public internet exposure entirely |
| Salesforce outbound callout to API requiring client cert | Named Credential with certificate, explicit port 8443 if required | Port must be in URL; cert and OAuth are separate config objects |
| Org approaching 50-certificate limit | API gateway consolidation or shared cert strategy | Hard limit cannot be raised by support ticket |
| Multiple external systems calling Salesforce | API gateway as single entry point | Centralizes auth, limits surface area, manages cert sprawl |
| JWT signing for OAuth 2.0 JWT Bearer flow | Separate certificate from mTLS client cert | These are different certificates used at different layers |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm deployment model and certificate inventory** — Verify whether the org is on Hyperforce or Classic (`Company Information > Instance`). Pull current certificate count from Setup > Certificate and Key Management. Document both before making any recommendations.

2. **Map integration directions and sensitivity** — For each integration in scope, record: direction (inbound/outbound/bidirectional), data classification (PII, PCI, PHI, or non-sensitive), and whether a dedicated API gateway already exists. This determines which authentication pattern applies.

3. **Apply the decision table** — For each integration, select the authentication pattern from the Decision Guidance section. Flag any integrations where IP allowlisting is currently used on a Hyperforce org — these require immediate remediation planning.

4. **Design certificate strategy** — Count certificates required by the proposed architecture. If total (existing + new) approaches 50, recommend API gateway consolidation or shared-cert strategy. Define naming conventions, expiry dates, and rotation owners for each certificate.

5. **Specify Named Credential configuration requirements** — For each outbound integration using mTLS, document the Named Credential URL (including explicit port if 8443), the certificate to attach, and the separate External Credential / OAuth configuration. Do not conflate the mTLS client cert with the OAuth signing cert.

6. **Document Private Connect applicability** — For any integration with highest-sensitivity data classification or strict private network requirements, assess whether Salesforce Private Connect is appropriate and note licensing and setup prerequisites.

7. **Produce the completed work template and hand off to implementation** — Fill `templates/integration-security-architecture-template.md`. The Named Credential configuration itself is implementation work covered by `integration/named-credentials-setup`.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Confirmed org deployment model (Hyperforce vs Classic) — IP allowlisting recommendation is consistent with this
- [ ] Current certificate count documented; proposed architecture stays below 50 total
- [ ] All inbound integrations have both transport-layer auth (certificate/mTLS) and application-layer auth (OAuth) specified
- [ ] mTLS client certificate(s) are distinct from OAuth JWT signing certificate(s) — not conflated in the design
- [ ] Named Credential URLs for mTLS outbound callouts include explicit port (`:8443`) where required
- [ ] Certificate expiry dates and rotation ownership documented for each certificate in scope
- [ ] Salesforce Private Connect evaluated and disposition recorded (recommended / not applicable + reason)
- [ ] API gateway placement decision documented — single-gateway consolidation vs direct Named Credentials

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Hyperforce IP addresses are ephemeral — IP allowlisting fails unpredictably** — Hyperforce distributes Salesforce tenants across cloud infrastructure where IPs rotate without notice. IP allowlists built from observed Salesforce IPs will pass testing and then fail in production as IPs rotate. The failure appears as a connection refused or timeout at the external firewall, not as an Salesforce error — making it hard to diagnose. Use mTLS or Private Connect instead.

2. **Port 8443 must be explicit in the Named Credential URL** — When an external mTLS endpoint listens on port 8443, the Named Credential's endpoint URL must include `:8443` explicitly. A URL of `https://api.example.com` will not route to port 8443 even if the remote server only responds on 8443. The callout will silently fail or connect to port 443 with no client certificate presented.

3. **The OAuth JWT signing certificate and the mTLS client certificate are entirely separate objects** — In JWT Bearer OAuth 2.0 flows, Salesforce signs the JWT assertion using a certificate stored in Certificate and Key Management. The mTLS client certificate (presented during TLS handshake) is a different certificate, often from a different CA, with a different lifecycle. Uploading one certificate and referencing it for both purposes will cause one of the two authentication mechanisms to fail.

4. **Hard 50-certificate limit per org cannot be raised** — Certificate and Key Management enforces a hard limit of 50 certificates per org. There is no support process to raise this limit. In orgs that have grown organically, this limit can be reached before teams realize it. Certificates from decommissioned integrations that are never deleted count against the limit. Audit and retire stale certificates as part of any integration security review.

5. **Private Connect requires org-level opt-in and has separate licensing** — Salesforce Private Connect is not enabled by default and is not included in base Salesforce licensing. It requires a support-assisted enablement process and may require add-on licensing. Do not include Private Connect in an architecture recommendation without confirming licensing is in place.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Integration authentication architecture decision | Per-integration table of auth mechanism, certificates required, and OAuth flow |
| Certificate strategy document | Inventory of certificates, expiry dates, rotation owners, headroom against 50-cert limit |
| IP allowlisting assessment | Go/no-go with Hyperforce migration impact analysis |
| API gateway placement recommendation | Whether to use a gateway, where it sits, what security controls it owns |
| Completed work template | `templates/integration-security-architecture-template.md` filled for design review |

---

## Related Skills

- `integration/named-credentials-setup` — implementation-level configuration of Named Credentials and External Credentials; use after this skill defines the architecture
- `architect/security-architecture-review` — org-wide security posture review; use when integration security is one component of a broader security assessment
- `architect/api-led-connectivity-architecture` — API gateway and MuleSoft architecture patterns; use when the API gateway placement decision leads to an API-led connectivity design
- `architect/event-driven-architecture` — when integration security extends to platform events, Change Data Capture, or Pub/Sub API subscribers
- `integration/error-handling-in-integrations` — reliability patterns for integrations; use alongside this skill to ensure secure integrations are also resilient
