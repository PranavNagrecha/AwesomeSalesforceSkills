# Government Cloud Compliance — Work Template

Use this template when architecting, assessing, or advising on a Salesforce Government Cloud deployment.

## Scope

**Skill:** `architect/government-cloud-compliance`

**Request summary:** (fill in what the user asked for)

**Program type:** (civilian federal / DoD / CMS / state government / other)

---

## Context Gathered

Answer the Before Starting questions from SKILL.md before proceeding.

- **Authorization level required:** (FedRAMP Moderate / FedRAMP High / DoD IL2 / IL4 / IL5)
- **Agency type:** (civilian federal / DoD / CMS contractor / state/local)
- **Data classification:** (CUI / PHI / PII / CDI / unclassified public)
- **Applicable overlays:** (FISMA / CMS ARS / DFARS 800-171 / StateRAMP / DISA CC SRG)
- **Existing ATO status:** (new effort / inheriting existing ATO / re-authorization)
- **Salesforce products in scope:**
- **Integration landscape:**

---

## Offering Selection Decision

Based on the authorization level and data classification:

| Requirement | Selected Offering | Rationale |
|-------------|-------------------|-----------|
| Infrastructure | GovCloud / GovCloud Plus / Hyperforce GovCloud | |
| Encryption | Platform Encryption (Salesforce-managed) / BYOK via Hyperforce CMEK | |
| Personnel security | Standard GovCloud support / GovCloud Plus US-persons-only | |

**Decision rationale:** (explain why this offering was selected over alternatives)

---

## Control Inheritance Map

Document which NIST 800-53 control families are fully inherited, shared, or customer-owned for this deployment.

| Control Family | Inheritance Model | Customer Action Required |
|---------------|------------------|-------------------------|
| PE — Physical & Environmental | Fully inherited from Salesforce | None |
| AU — Audit & Accountability | Shared | Configure Shield Event Monitoring exports to SIEM |
| AC — Access Control | Shared | Implement profiles, permission sets, OWD, MFA policy |
| IA — Identification & Authentication | Shared | Configure SSO, MFA enforcement, session policies |
| SC — System & Communications Protection | Shared | Enable Platform Encryption; enforce TLS for all integrations |
| CM — Configuration Management | Customer-owned | Define change management process; metadata backup schedule |
| IR — Incident Response | Customer-owned | Define IR playbook integrated with Salesforce incident notification |
| CP — Contingency Planning | Customer-owned | Document RTO/RPO; schedule annual sandbox restore test |
| AT — Awareness & Training | Customer-owned | Define security awareness training program for all org users |

---

## Compliance Automation Plan

| Control Area | Automation Mechanism | Evidence Artifact |
|-------------|---------------------|------------------|
| AU-2 / AU-12 (Audit events) | Shield Event Monitoring — nightly EventLogFile export to SIEM | Daily log export confirmation in SIEM |
| AC-2 (Account management) | Flow alert on high-privilege permission set assignment | Alert records in SIEM / ticketing system |
| CM-6 (Configuration settings) | Weekly Metadata API configuration snapshot | Version-controlled metadata export |
| IA-5 (Authenticator management) | Automated MFA enforcement status query (AuthConfig + UserLogin) | Monthly MFA compliance report |
| SC-28 (Protection at rest) | Platform Encryption policy export (EncryptionPolicy metadata) | Quarterly encryption policy snapshot |

---

## Integration FedRAMP Authorization Checklist

For each external system in the integration landscape:

| System | Integration Type | FedRAMP Status | Authorized Level | Action |
|--------|-----------------|----------------|-----------------|--------|
| (system name) | (API / ETL / middleware) | (authorized / pending / not authorized) | (Moderate / High) | (proceed / block / replace) |

---

## Feature Availability Verification

For each planned capability, confirm GovCloud availability:

| Feature | Planned Use | GovCloud Plus Status | Source / Date Verified |
|---------|-------------|---------------------|----------------------|
| (feature name) | (use case) | (available / not available / pending authorization) | (Feature Availability Guide, MM/YYYY) |

---

## Continuous Monitoring Cadence

| Activity | Frequency | Owner | Artifact |
|----------|-----------|-------|---------|
| Monthly SIEM log review | Monthly | Agency ISO | Monthly monitoring report |
| POA&M status review | Monthly | System Owner + ISO | Updated POA&M |
| Significant change assessment | Per deployment | System Owner + ISO | Change assessment record |
| Annual control assessment | Annual | Agency + 3PAO | Security Assessment Report (SAR) |
| Annual contingency plan test | Annual | System Owner | CP test results |
| Feature availability review | Per Salesforce release | Technical Lead | Feature review log |

---

## Recommended Workflow Checklist

Copy steps from SKILL.md and tick items as you complete them.

- [ ] 1. Classified the data and determined the authorization level (FISMA impact level, DoD IL if applicable, agency overlays)
- [ ] 2. Selected the Salesforce Government Cloud offering (GovCloud / GovCloud Plus / Hyperforce GovCloud) and confirmed feature availability
- [ ] 3. Mapped customer-owned controls using Salesforce FedRAMP inheritance matrix; began drafting SSP
- [ ] 4. Designed compliance automation (Shield Event Monitoring exports, evidence collection, alert flows)
- [ ] 5. Validated FedRAMP authorization status of every integration and middleware component
- [ ] 6. Established continuous monitoring cadence (POA&M management, significant change process, monthly reporting)
- [ ] 7. Scheduled ongoing feature availability checks (per Salesforce release cycle)

---

## Open Items / Risks

| Item | Risk Level | Owner | Target Resolution |
|------|-----------|-------|------------------|
| (describe item) | High / Medium / Low | | |

---

## Notes

(Record any deviations from the standard pattern, agency-specific requirements, or findings that should be escalated.)
