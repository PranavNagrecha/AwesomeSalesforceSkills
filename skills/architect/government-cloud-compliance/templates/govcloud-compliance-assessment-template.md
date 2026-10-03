# Government Cloud Compliance Assessment

## Assessment Metadata

| Property | Value |
|----------|-------|
| **Program / Agency** | <fill in> |
| **Salesforce Org ID** | <fill in> |
| **Assessment Date** | <fill in> |
| **Assessor(s)** | <fill in> |
| **Current GovCloud Offering** | <fill in: Government Cloud Plus / Government Cloud Plus - Defense / Hyperforce Government Cloud / Not yet deployed> |
| **ATO Status** | <fill in: No ATO / ATO in progress / Active ATO (expiry: <fill in>) / Continuous authorization> |

---

## 1. Authorization Level Determination

### FISMA Impact Level

| Data Element | Confidentiality | Integrity | Availability |
|-------------|----------------|-----------|-------------|
| <fill in: data type> | Low / Moderate / High | Low / Moderate / High | Low / Moderate / High |
| <fill in: data type> | Low / Moderate / High | Low / Moderate / High | Low / Moderate / High |

**Overall FISMA Impact Level:** <fill in: Low / Moderate / High>

**Rationale:** <fill in: explain why the highest impact level across all data elements determines the system categorization>

### DoD Impact Level (if applicable)

- [ ] Not a DoD program — DoD IL assessment not required
- [ ] IL2: Public/unclassified non-CUI data
- [ ] IL4: CUI / Covered Defense Information (CDI) — DFARS 252.204-7012 scope
- [ ] IL5: Higher sensitivity CUI / NSS unclassified data
- [ ] IL6: Classified (SECRET) — not available on commercial Salesforce

### Agency-Specific Overlays (check all that apply)

- [ ] CMS ARC-AMPE (Centers for Medicare and Medicaid Services programs)
- [ ] StateRAMP (state/local government programs)
- [ ] DFARS 252.204-7012 / NIST 800-171 (DoD contractor systems)
- [ ] IRS Publication 1075 (tax information handling)
- [ ] CJIS (Criminal Justice Information)
- [ ] Other: <fill in>

---

## 2. Salesforce Offering Selection

### Offering Recommendation

Based on the authorization level determination above:

| Requirement | Recommended Offering | Rationale |
|-------------|---------------------|-----------|
| FISMA Moderate | Salesforce Government Cloud | FedRAMP Moderate ATO (confirm the offering is still sold; the Spring '26 Government Cloud guide lists only Government Cloud Plus and Government Cloud Plus - Defense) |
| FISMA High (civilian) | Salesforce Government Cloud Plus | FedRAMP High P-ATO (JAB) |
| DoD IL4 | Salesforce Government Cloud Plus | FedRAMP High minimum for IL4 |
| DoD IL5 | Salesforce Government Cloud Plus - Defense | DoD IL5 PA on dedicated DoD infrastructure (Government Cloud guide) |

**Selected Offering:** <fill in>

**Justification:** <fill in: explain why this offering was selected>

### Feature Availability Gap Analysis

| Required Feature | Available in Selected Offering? | Alternative / Notes |
|-----------------|--------------------------------|---------------------|
| <fill in: feature> | Yes / No / Confirm needed | <fill in> |
| <fill in: feature> | Yes / No / Confirm needed | <fill in> |
| <fill in: feature> | Yes / No / Confirm needed | <fill in> |
| Einstein / AI features | <fill in: verify current GovCloud authorization> | <fill in> |
| AppExchange packages (list): <fill in> | <fill in: verify each on GovCloud authorized list> | <fill in> |

---

## 3. Data Residency Assessment

### Data Flow Inventory

| Data Element | Classification | Source System | Destination | Residency Compliant? |
|-------------|---------------|--------------|-------------|---------------------|
| <fill in> | CUI / PHI / PII / Public | <fill in> | <fill in> | Yes / No / Needs review |
| <fill in> | CUI / PHI / PII / Public | <fill in> | <fill in> | Yes / No / Needs review |

### Residency Compliance Gaps

| Gap | Risk | Remediation |
|-----|------|-------------|
| <fill in: e.g., middleware on non-FedRAMP platform> | High / Medium / Low | <fill in> |

---

## 4. NIST 800-53 Control Mapping

### Control Inheritance Summary

| Control Family | Inheritance Status | Customer Action Required |
|---------------|-------------------|------------------------|
| AC — Access Control | Shared (platform inherited; org config customer-owned) | Profiles, permission sets, MFA policy, OAuth scopes |
| AU — Audit and Accountability | Shared (infrastructure inherited; log config customer-owned) | Shield Event Monitoring configuration, log retention |
| IA — Identification and Authentication | Shared | SSO/SAML config, session policies, password policies |
| SC — System and Communications Protection | Shared (TLS inherited; at-rest encryption customer-configured) | Platform Encryption policy, BYOK if required |
| SI — System and Information Integrity | Shared | Key rotation schedule, integrity monitoring alerts |
| CM — Configuration Management | Customer-owned | Change management process, metadata backup |
| CP — Contingency Planning | Customer-owned | Recovery procedures, sandbox restore testing |
| IR — Incident Response | Customer-owned | Incident response playbook, US-CERT reporting procedures |
| AT — Awareness and Training | Customer-owned | Training program documentation |

### High-Priority Customer-Owned Control Implementation Status

| Control | Description | Implementation Status | Evidence Location |
|---------|-------------|----------------------|------------------|
| AC-2 | Account Management | <fill in: Implemented / Partial / Not implemented> | <fill in> |
| AC-6 | Least Privilege | <fill in> | <fill in> |
| AU-2 | Event Logging | <fill in> | <fill in> |
| AU-11 | Audit Record Retention | <fill in> | <fill in> |
| IA-2(1) | MFA for Privileged Users | <fill in> | <fill in> |
| IA-2(2) | MFA for Non-Privileged Users | <fill in> | <fill in> |
| SC-28 | Protection of Information at Rest | <fill in> | <fill in> |
| CM-3 | Configuration Change Control | <fill in> | <fill in> |
| CM-6 | Configuration Settings | <fill in> | <fill in> |
| IR-6 | Incident Reporting | <fill in> | <fill in> |

---

## 5. Integration FedRAMP Authorization Checklist

| Integration / System | FedRAMP Status | Authorization Level | Action Required |
|---------------------|---------------|--------------------| --------------|
| <fill in: system name> | Authorized / Not authorized / Pending | Moderate / High / N/A | <fill in> |
| <fill in: system name> | Authorized / Not authorized / Pending | Moderate / High / N/A | <fill in> |
| <fill in: system name> | Authorized / Not authorized / Pending | Moderate / High / N/A | <fill in> |

**Integrations with compliance gaps (require remediation before ATO):**

- <fill in: describe gap and remediation approach>
- <fill in: FedRAMP-authorized alternative if the current system is not authorized>

---

## 6. Compliance Automation Configuration

### Shield Event Monitoring

- [ ] Shield Event Monitoring licensed
- [ ] EventLogFile API export configured (target: nightly)
- [ ] LoginEvent export to SIEM configured
- [ ] ReportEvent and ContentDistributionEvent export configured
- [ ] ApiEvent and BulkApiResultEvent export configured
- [ ] SIEM platform: <fill in> (confirm FedRAMP-authorized: Yes / No)
- [ ] Log retention period configured to meet AU-11 requirements: <fill in> days/years

### Automated Control Evidence Collection

- [ ] Metadata API scheduled backup for org configuration (weekly minimum for CM-6)
- [ ] Connected App inventory export configured (AC-17 evidence)
- [ ] Permission set assignment alert flow configured (AC-2 account management)
- [ ] MFA enforcement status report configured (IA-5 evidence)
- [ ] Platform Encryption policy documentation scheduled (SC-28 evidence)

### Platform Encryption (if required for SC-28)

- [ ] Platform Encryption licensed
- [ ] Fields containing CUI / PHI / CDI encrypted (list fields: <fill in>)
- [ ] Key rotation schedule set to: <fill in> (90 days recommended for FedRAMP High)
- [ ] BYOK configured (program requirement, not stated by the Government Cloud guide for IL5): Yes / No / N/A
- [ ] Deterministic-encryption fields listed with AO risk acceptance (deterministic is not FIPS-validated): <fill in>
- [ ] Key storage location (BYOK): <fill in>

---

## 7. FISMA Continuous Monitoring Plan

### Monitoring Cadence

| Activity | Frequency | Responsible Party | Evidence Artifact |
|----------|-----------|------------------|------------------|
| Vulnerability scanning (infrastructure) | Monthly | Salesforce (inherited) | Salesforce scan reports |
| Vulnerability scanning (customer middleware/integration) | Monthly | <fill in> | <fill in> |
| POA&M review and update | Monthly | <fill in> | POA&M document |
| Monthly report to agency AO | Monthly | <fill in> | Monthly status report |
| Control assessment (rotating subset) | Annual | <fill in> 3PAO | SAR update |
| Contingency plan test | Annual | <fill in> | CP-4 test report |
| Significant change review | Per change | <fill in> | Change assessment record |

### Current POA&M Summary

| POA&M ID | Control | Weakness | Risk Rating | Due Date | Status |
|----------|---------|----------|-------------|----------|--------|
| <fill in> | <fill in> | <fill in> | High / Moderate / Low | <fill in> | Open / In progress / Closed |

### Significant Change Notification Procedure

1. Proposed change submitted to: <fill in> (change control board / security team)
2. Significant change determination by: <fill in>
3. AO notification required: Yes / No / TBD
4. Partial re-assessment required: Yes / No / TBD
5. Pre-deployment approval gate: <fill in> process

---

## 8. CMS ARC-AMPE Controls (if applicable)

*Complete this section only if the system is a CMS program subject to CMS ARS.*

- [ ] CMS ARS overlay applied to NIST 800-53 baseline: Yes / No / In progress
- [ ] Separate CMS ATO required in addition to FedRAMP: Yes / No
- [ ] CMS CI/CD pipeline controls addressed (ARC-AMPE DevSecOps requirements): Yes / No / In progress
- [ ] HIPAA controls implemented in addition to FISMA/FedRAMP: Yes / No

---

## 9. Findings and Recommendations

### Open Findings

| ID | Area | Finding | Risk | Recommendation | Target Date |
|----|------|---------|------|----------------|------------|
| GOV-001 | <fill in> | <fill in> | High / Medium / Low | <fill in> | <fill in> |
| GOV-002 | <fill in> | <fill in> | High / Medium / Low | <fill in> | <fill in> |

### Architecture Decisions Required

| Decision | Options Considered | Recommended | Decision Owner | Decision Due |
|----------|-------------------|-------------|----------------|-------------|
| <fill in> | <fill in> | <fill in> | <fill in> | <fill in> |

---

## Assessor Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Lead Assessor | <fill in> | <fill in> | <fill in> |
| Agency ISO / Security Officer | <fill in> | <fill in> | <fill in> |
| Authorizing Official (AO) | <fill in> | <fill in> | <fill in> |
