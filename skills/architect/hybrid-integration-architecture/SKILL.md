---
name: hybrid-integration-architecture
description: "Use this skill when designing hybrid on-premises-to-Salesforce integration architectures: DMZ relay patterns, reverse proxy configuration, VPN connectivity, Salesforce Private Connect (AWS PrivateLink) topology, and data residency patterns for regulated data. Trigger keywords: on-premises to Salesforce integration network topology, DMZ relay Salesforce, hybrid integration VPN, Private Connect architecture, data residency Salesforce hybrid. NOT for cloud-to-cloud only integration patterns, OAuth or authentication mechanism design (use integration-security-architecture), or standard Connected App setup."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "how do I connect Salesforce to an on-premises system without exposing it to the internet"
  - "how do I set up Salesforce Private Connect with AWS PrivateLink"
  - "Hyperforce IP allowlisting is not working — Salesforce IPs keep changing"
  - "what is the DMZ relay pattern for Salesforce on-premises integration"
  - "how do I configure a VPN between Salesforce and our data center"
  - "we need data residency for regulated data in our Salesforce hybrid integration"
tags:
  - hybrid-integration
  - on-premises
  - private-connect
  - dmz
  - network-topology
  - data-residency
inputs:
  - "On-premises system type and location (data center, private cloud)"
  - "Connectivity requirements: VPN, DMZ relay, or Private Connect"
  - "Data residency requirements: regulated industry, data sovereignty"
  - "Hyperforce vs non-Hyperforce org"
outputs:
  - "Hybrid integration network topology diagram and pattern selection"
  - "DMZ relay configuration guidance"
  - "Private Connect architecture overview and licensing prerequisites"
  - "Data residency pattern for regulated data in hybrid scenarios"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-16
---

# Hybrid Integration Architecture

Use this skill when designing the network topology for integrations between on-premises systems and Salesforce — including DMZ relay patterns, reverse proxy configurations, VPN-based connectivity, and Salesforce Private Connect. This skill covers network and connectivity architecture, not authentication mechanisms (see `integration-security-architecture` for mTLS and OAuth).

---

## Before Starting

Gather this context before working on anything in this domain:

- Is the Salesforce org on Hyperforce? Hyperforce uses ephemeral IPs — IP allowlisting is not a viable strategy and must be replaced with mTLS or Private Connect.
- What is the on-premises system type: mainframe, ERP, database, or middleware?
- Is the connection **outbound from Salesforce** to on-premises, **inbound from on-premises** to Salesforce, or bidirectional?
- Are there data residency or regulated-industry requirements (HIPAA, GDPR, financial regulation) that require the integration data to remain within a specific geography or network boundary?
- Is Salesforce Private Connect licensed? Private Connect requires support-assisted opt-in and carries separate add-on licensing.

---

## Core Concepts

### DMZ Relay Pattern for Outbound Callouts from Salesforce

When Salesforce makes outbound callouts to an on-premises system, the on-premises system is often behind a corporate firewall that does not accept inbound connections from the public internet. The **DMZ relay** pattern uses a relay server in the corporate DMZ to forward requests:

1. Salesforce callout goes to the **DMZ relay host** (a server in the corporate demilitarized zone with a public FQDN).
2. The relay (e.g., reverse proxy products such as IBM WebSeal or CA SiteMinder) authenticates the incoming request and forwards it to the internal on-premises system over the corporate LAN.
3. The response travels back through the relay to Salesforce.

The DMZ relay is the on-premises side of the architecture. Salesforce has no native VPN client — Salesforce cannot terminate a VPN tunnel. All on-premises connectivity from Salesforce must traverse through an internet-facing relay, a Private Connect endpoint, or an intermediary integration platform (MuleSoft Runtime Fabric) that handles the corporate network boundary.

### Salesforce Private Connect (AWS PrivateLink)

Salesforce **Private Connect** provides a private network path between Salesforce (hosted on AWS) and the customer's AWS environment using **AWS PrivateLink**. This eliminates the public internet from the data path entirely:

- Data does not traverse the public internet
- No need to manage Salesforce-side IP allowlists (which fail on Hyperforce)
- Provides the strongest network-level isolation for regulated data

**Key constraints:**
- Requires **support-assisted opt-in** — cannot be self-service enabled
- Carries **separate add-on licensing**
- Requires the customer environment to also be on AWS (or have AWS connectivity)
- The existing `integration-security-architecture` skill covers Private Connect authentication details thoroughly; this skill covers the network topology decision

Private Connect is NOT the universal solution — it only applies when the on-premises system connects through AWS and the licensing is available.

### On-Premises Encryption Gateways for Data Residency

For organizations with regulated data that cannot leave their network boundaries (e.g., HIPAA-protected health data, financial data under specific sovereignty requirements), **on-premises encryption gateways** (such as IBM DataPower or CipherCloud) can be placed between the corporate network and Salesforce:

1. Data from Salesforce travels to the encryption gateway in the customer DMZ.
2. The gateway encrypts or tokenizes sensitive fields before the data reaches internal systems (or vice versa for inbound).
3. The encryption keys never leave the customer's network — Salesforce stores only tokenized values.

This pattern requires that the Salesforce fields holding sensitive values are designed for tokenized data, and that all reporting and business logic use the tokenized representation or decrypt at the gateway layer.

---

## Common Patterns

### Pattern: Reverse Proxy Relay for On-Premises Salesforce Callouts

**When to use:** Salesforce must call an on-premises API or database that is not accessible on the public internet and Private Connect is not available.

**How it works:**
1. Deploy or configure a reverse proxy in the corporate DMZ (e.g., nginx, IBM WebSeal, CA SiteMinder, AWS API Gateway with VPC link).
2. Assign the relay a public FQDN with a valid TLS certificate.
3. In Salesforce, configure a Named Credential pointing to the relay's public FQDN.
4. The relay is configured to forward authenticated requests to the internal target over the internal network.
5. Add the relay FQDN to Salesforce's Remote Site Settings.

**Why not VPN:** Salesforce has no native VPN client and cannot terminate IPSec or SSL VPN tunnels. VPN connectivity must be managed by an intermediary (MuleSoft Runtime Fabric deployed in the customer network, or a relay in the DMZ).

### Pattern: Private Connect for Regulated On-Premises Data (AWS-Connected)

**When to use:** Regulated data (HIPAA, financial sovereignty) must never traverse the public internet; customer environment connects to AWS.

**How it works:**
1. Customer enables Private Connect via Salesforce support request (requires add-on license).
2. Customer creates a VPC Endpoint Service in their AWS VPC pointing to their on-premises systems (via Direct Connect or Site-to-Site VPN to AWS).
3. Salesforce establishes a Private Connect connection to the customer's VPC Endpoint Service via AWS PrivateLink.
4. Integration traffic flows: Salesforce → AWS PrivateLink → customer AWS VPC → customer on-premises (via Direct Connect or VPN).

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| On-premises API accessible via public internet | Named Credential + mTLS or OAuth | No special network topology needed |
| On-premises API behind corporate firewall, no Private Connect | DMZ reverse proxy relay | Relay provides public-facing FQDN that Salesforce can call |
| Regulated data, no public internet path | Private Connect (if licensed and AWS-connected) | Eliminates public internet from data path |
| Hyperforce org needing on-premises access | Private Connect or mTLS relay — NOT IP allowlisting | Hyperforce IPs are ephemeral; allowlisting is unreliable |
| On-premises system not on AWS | DMZ relay or MuleSoft Runtime Fabric on-premises | Private Connect requires AWS connectivity |
| Data residency encryption requirement | On-premises encryption gateway (DataPower/CipherCloud) | Keys stay on-premises; Salesforce stores tokenized values |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Determine org type** — Hyperforce or non-Hyperforce? On Hyperforce, IP allowlisting is architecturally unreliable — plan for mTLS or Private Connect from the start.
2. **Classify the connectivity requirement** — Outbound from Salesforce to on-premises, inbound from on-premises to Salesforce, or bidirectional. Each direction may use a different pattern.
3. **Assess Private Connect eligibility** — Is the customer environment on AWS? Is Private Connect licensed? If both yes, Private Connect is the strongest option for regulated scenarios.
4. **Design DMZ relay if Private Connect is not available** — Identify the relay host location, TLS certificate requirements, and authentication mechanism at the relay layer.
5. **Evaluate data residency requirements** — If regulated data must never be visible in plaintext outside the customer network, design an encryption gateway layer at the DMZ boundary.
6. **Document the network topology** — Produce a diagram showing: Salesforce → relay/Private Connect endpoint → on-premises target. Include all network boundaries (DMZ, internal LAN, internet).
7. **Validate against Hyperforce constraints** — Confirm that no IP allowlisting dependency exists in the design. Hyperforce IPs are not stable.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Hyperforce status confirmed; no IP allowlisting used on Hyperforce
- [ ] Connectivity direction classified (outbound from SF / inbound to SF / bidirectional)
- [ ] Private Connect eligibility assessed (AWS + license)
- [ ] DMZ relay or Private Connect endpoint configured
- [ ] Data residency requirements addressed with encryption gateway if required
- [ ] Network topology diagram produced showing all boundaries
- [ ] No assumption that Salesforce can terminate VPN tunnels

---

## Salesforce-Specific Gotchas

1. **Salesforce has no native VPN client** — A common design error is planning a VPN tunnel from Salesforce to the corporate network. Salesforce cannot terminate IPSec or SSL VPN tunnels. All corporate-network connectivity requires an intermediary relay or Private Connect.

2. **Private Connect requires support-assisted opt-in and separate licensing** — Private Connect cannot be self-service enabled. Teams that design for Private Connect without confirming the license and support enablement process will be blocked at implementation.

3. **Hyperforce IP addresses are ephemeral** — On Hyperforce, Salesforce uses cloud infrastructure with dynamic IPs. IP allowlisting for inbound connections to on-premises systems is unreliable. The official Salesforce guidance recommends mTLS as the preferred alternative to IP allowlisting on Hyperforce.

4. **DMZ relay security configuration is outside Salesforce's control** — The relay is a customer-managed component. If the relay has weak TLS configuration or insufficient authentication, the Salesforce-side security is undermined regardless of Salesforce's own security posture.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Network topology diagram | Diagram showing Salesforce, relay/Private Connect, and on-premises system boundaries |
| Connectivity pattern decision | Documents which pattern was selected and why |
| Private Connect prerequisites checklist | License, AWS setup, and support request steps |
| Data residency architecture note | Documents encryption gateway placement and key management approach |

---

## Related Skills

- `architect/integration-security-architecture` — Use for mTLS, OAuth, IP allowlisting alternatives, and Private Connect authentication details
- `architect/api-led-connectivity-architecture` — Use for API layer design (System/Process/Experience) above the network connectivity layer
- `architect/mulesoft-anypoint-architecture` — Use when MuleSoft Runtime Fabric is the on-premises relay component in the hybrid topology
