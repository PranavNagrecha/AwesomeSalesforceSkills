# Hybrid Integration Architecture — Decision Template

Use this template when designing connectivity between Salesforce and on-premises or private cloud systems.

---

## Scope

**Integration name:** _______________
**Direction:** [ ] Salesforce → On-Premises  [ ] On-Premises → Salesforce  [ ] Bidirectional
**Hyperforce org?** [ ] Yes  [ ] No  [ ] Unknown

---

## Connectivity Assessment

| Criterion | Answer | Notes |
|---|---|---|
| Can the on-premises system expose a public HTTPS endpoint? | Y/N | |
| Is data residency / no-public-internet required? | Y/N | |
| Is Private Connect (PrivateLink) licensed? | Y/N | |
| Is a DMZ host available for relay deployment? | Y/N | |
| Existing middleware platform | | MuleSoft / Boomi / Other |

---

## Connectivity Pattern Decision

**Selected pattern:**
- [ ] Direct HTTPS (on-premises exposes public endpoint with mTLS)
- [ ] DMZ Relay (middleware runtime on DMZ host, outbound-only)
- [ ] Salesforce Private Connect (AWS PrivateLink, add-on license required)
- [ ] Hybrid: _______________

**Rationale:** _______________

---

## Security Controls

| Control | Selected | Notes |
|---|---|---|
| Authentication | [ ] mTLS  [ ] OAuth  [ ] API Key | |
| IP Allowlisting | [ ] NOT used (Hyperforce)  [ ] Used (non-Hyperforce) | |
| In-transit encryption | [ ] TLS 1.2+  [ ] PrivateLink (no internet) | |
| Field-level gateway encryption | Y/N | If Y, document deterministic vs. random per field |

---

## Reliability

- [ ] Relay deployed in HA (min 2 nodes + load balancer)
- [ ] Fallback / dead-letter behavior documented
- [ ] Alert threshold on relay health defined

---

## Architecture Notes

Describe the end-to-end data flow including network segments: _______________

---

## Open Items

- [ ] Private Connect license confirmed with account team
- [ ] Support case filed for Private Connect opt-in (if applicable)
- [ ] Firewall rules documented (outbound-only from relay)
