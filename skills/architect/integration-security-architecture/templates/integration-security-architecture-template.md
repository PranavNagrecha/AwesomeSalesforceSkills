# Integration Security Architecture — Design Template

Use this template to document the integration security architecture for a Salesforce org.
Complete all sections before handing off to implementation (Named Credential configuration,
Connected App setup, certificate procurement).

---

## Scope

**Org name / instance:** _______________________________________________

**Deployment model:** [ ] Hyperforce &nbsp;&nbsp; [ ] Classic

**Current certificate count (Setup > Certificate and Key Management):** _____ / 50

**Date of assessment:** _______________________________________________

**Architect:** _______________________________________________

---

## Integration Inventory

List all integrations in scope. Complete one row per integration.

| # | Integration Name | Direction | External System | Data Classification | Current Auth Method |
|---|---|---|---|---|---|
| 1 | | Inbound / Outbound / Both | | Public / Internal / Confidential / Restricted | OAuth / IP Allowlist / Basic / mTLS / None |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

*Add rows as needed. Data Classification: Public = non-sensitive; Internal = employee-only; Confidential = customer PII/business data; Restricted = PCI, PHI, regulated data.*

---

## Authentication Architecture Decision — Per Integration

For each integration in the inventory, document the chosen authentication mechanism and rationale.

### Integration 1: _______________________________________________

| Decision Point | Selection | Rationale |
|---|---|---|
| Transport-layer auth | [ ] mTLS &nbsp;&nbsp; [ ] TLS only &nbsp;&nbsp; [ ] Private Connect | |
| Application-layer auth | [ ] OAuth 2.0 Client Credentials &nbsp;&nbsp; [ ] OAuth 2.0 JWT Bearer &nbsp;&nbsp; [ ] Basic &nbsp;&nbsp; [ ] API Key | |
| OAuth flow (if applicable) | Client Credentials / JWT Bearer / Web Server / N/A | |
| IP allowlisting needed? | Yes / No — if Yes: Classic org only, document rationale | |
| Salesforce Private Connect? | Yes / No / Evaluate | |
| Named Credential name | | |
| External Credential name | | |
| Connected App name | | |

*Repeat block for each integration in scope.*

---

## IP Allowlisting Assessment

**Deployment model is Hyperforce:** [ ] Yes &nbsp;&nbsp; [ ] No &nbsp;&nbsp; [ ] Unknown

If Hyperforce:
- IP allowlisting for authentication is **NOT viable**. Hyperforce IPs are ephemeral.
- Integrations currently using IP allowlisting must migrate to mTLS.

**Integrations requiring IP allowlisting remediation:**

| Integration | Current Approach | Target Approach | Migration Owner | Target Date |
|---|---|---|---|---|
| | IP Allowlist | mTLS | | |

---

## Certificate Strategy

### Certificate Inventory

List all certificates required by the proposed architecture.

| # | Certificate Name / Alias | Purpose | Issued By | Expiry Date | Owner | Related Integration(s) |
|---|---|---|---|---|---|---|
| 1 | | JWT Signing / mTLS Client / CA Trust | Self-signed / CA name | YYYY-MM-DD | | |
| 2 | | | | | | |
| 3 | | | | | | |

**Projected certificate count after implementation:** _____ / 50

**If projected count > 35:** Document consolidation strategy below.

### Certificate Consolidation Strategy (if applicable)

[ ] API gateway — single Salesforce cert authenticates to gateway; gateway manages external system certs

[ ] Shared certificate — multiple integrations share one cert because they share a CA trust anchor

[ ] Wildcard certificate — external system supports wildcard; one cert covers multiple endpoints

**Notes:** _______________________________________________

### Certificate Rotation Plan

| Certificate | Expiry Date | Alert Trigger (90 days prior) | Rotation Owner | Rotation Process |
|---|---|---|---|---|
| | | | | Generate new cert > Update Named Credential > Install on remote > Retire old cert |

---

## OAuth JWT Signing vs mTLS Client Certificate Separation

For each integration using both OAuth JWT Bearer and mTLS, confirm these are distinct certificates.

| Integration | JWT Signing Certificate | mTLS Client Certificate | Are They Separate? |
|---|---|---|---|
| | | | [ ] Yes &nbsp;&nbsp; [ ] No — remediate before implementation |

---

## API Gateway Assessment

**Is a dedicated API gateway in scope?** [ ] Yes &nbsp;&nbsp; [ ] No &nbsp;&nbsp; [ ] Evaluate

If Yes:
| Decision | Selection |
|---|---|
| Gateway product | MuleSoft / Apigee / AWS API Gateway / Azure APIM / Other: ___ |
| mTLS termination point | Gateway (external certs managed by gateway, not Salesforce) |
| Salesforce authentication from gateway | OAuth 2.0 JWT Bearer / Client Credentials |
| Salesforce certificate(s) consumed | 1 (gateway JWT signing cert) |
| External system cert management | Gateway's certificate store — outside Salesforce 50-cert limit |
| Private Connect from gateway to Salesforce | [ ] Yes &nbsp;&nbsp; [ ] No |

---

## Salesforce Private Connect Assessment

| Criterion | Status | Notes |
|---|---|---|
| Integration requires private network path (regulatory / compliance) | [ ] Yes &nbsp;&nbsp; [ ] No | |
| Salesforce Private Connect licensed | [ ] Confirmed &nbsp;&nbsp; [ ] Not confirmed &nbsp;&nbsp; [ ] Not licensed | |
| Cloud region compatibility confirmed | [ ] Yes &nbsp;&nbsp; [ ] No | |
| External system operates in compatible VPC | [ ] Yes &nbsp;&nbsp; [ ] No | |
| Support case opened for enablement | [ ] Yes — case # ___ &nbsp;&nbsp; [ ] Not yet | |
| Estimated enablement lead time | | |

**Private Connect recommendation:** [ ] Proceed &nbsp;&nbsp; [ ] Not applicable — mTLS over public internet &nbsp;&nbsp; [ ] Blocked — prerequisite missing

---

## Security Control Summary

| Control | In Scope | Implemented By | Status |
|---|---|---|---|
| mTLS for inbound integrations | [ ] Yes &nbsp;&nbsp; [ ] No | Named Credential + Connected App | |
| mTLS for outbound integrations | [ ] Yes &nbsp;&nbsp; [ ] No | Named Credential + Certificate | |
| OAuth 2.0 application-layer auth | [ ] Yes &nbsp;&nbsp; [ ] No | Connected App + External Credential | |
| Connected App scope minimization | [ ] Yes &nbsp;&nbsp; [ ] No | Connected App configuration | |
| Certificate expiry monitoring | [ ] Yes &nbsp;&nbsp; [ ] No | Calendar / ticketing system | |
| API gateway centralization | [ ] Yes &nbsp;&nbsp; [ ] No | Gateway product | |
| Salesforce Private Connect | [ ] Yes &nbsp;&nbsp; [ ] No | Support-assisted enablement | |
| IP allowlisting remediation (Hyperforce) | [ ] Yes &nbsp;&nbsp; [ ] No / N/A | External firewall change | |

---

## Risks and Open Items

| # | Risk or Open Item | Impact | Owner | Resolution Date |
|---|---|---|---|---|
| 1 | | High / Medium / Low | | |
| 2 | | | | |

---

## Review Sign-Off

| Reviewer | Role | Date | Decision |
|---|---|---|---|
| | Integration Architect | | Approved / Changes Required |
| | Security Architect | | Approved / Changes Required |
| | Infrastructure / Networking | | Approved / Changes Required |

---

## Implementation Handoff Notes

After this template is approved, hand off to implementation using:
- `integration/named-credentials-setup` — for Named Credential and External Credential configuration
- `architect/api-led-connectivity-architecture` — if API gateway consolidation is selected
- Certificate procurement requests for any CA-signed certificates required for mTLS
