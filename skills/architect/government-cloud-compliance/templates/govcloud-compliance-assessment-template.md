# Government Cloud Compliance Assessment

## Assessment Metadata

| Property | Value |
|----------|-------|
| **Program / Agency** | TODO |
| **Salesforce Org ID** | TODO |
| **Assessment Date** | TODO |
| **Assessor(s)** | TODO |
| **Current GovCloud Offering** | TODO: GovCloud / GovCloud Plus / Hyperforce GovCloud / Not yet deployed |
| **ATO Status** | TODO: No ATO / ATO in progress / Active ATO (expiry: TODO) / Continuous authorization |

---

## 1. Authorization Level Determination

### FISMA Impact Level

| Data Element | Confidentiality | Integrity | Availability |
|-------------|----------------|-----------|-------------|
| TODO: data type | Low / Moderate / High | Low / Moderate / High | Low / Moderate / High |
| TODO: data type | Low / Moderate / High | Low / Moderate / High | Low / Moderate / High |

**Overall FISMA Impact Level:** TODO: Low / Moderate / High

**Rationale:** TODO: explain why the highest impact level across all data elements determines the system categorization

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
- [ ] Other: TODO

---

## 2. Salesforce Offering Selection

### Offering Recommendation

Based on the authorization level determination above:

| Requirement | Recommended Offering | Rationale |
|-------------|---------------------|-----------|
| FISMA Moderate | Salesforce Government Cloud | FedRAMP Moderate ATO |
| FISMA High (civilian) | Salesforce Government Cloud Plus | FedRAMP High ATO |
| DoD IL4 | Salesforce Government Cloud Plus | FedRAMP High minimum for IL4 |
| DoD IL5 | Hyperforce GovCloud (AWS GovCloud) + CMEK | Additional IL5 controls required |

**Selected Offering:** TODO

**Justification:** TODO: explain why this offering was selected

### Feature Availability Gap Analysis

| Required Feature | Available in Selected Offering? | Alternative / Notes |
|-----------------|--------------------------------|---------------------|
| TODO: feature | Yes / No / Confirm needed | TODO |
| TODO: feature | Yes / No / Confirm needed | TODO |
| TODO: feature | Yes / No / Confirm needed | TODO |
| Einstein / AI features | TODO: verify current GovCloud authorization | TODO |
| AppExchange packages (list): TODO | TODO: verify each on GovCloud authorized list | TODO |

---

## 3. Data Residency Assessment

### Data Flow Inventory

| Data Element | Classification | Source System | Destination | Residency Compliant? |
|-------------|---------------|--------------|-------------|---------------------|
| TODO | CUI / PHI / PII / Public | TODO | TODO | Yes / No / Needs review |
| TODO | CUI / PHI / PII / Public | TODO | TODO | Yes / No / Needs review |

### Residency Compliance Gaps

| Gap | Risk | Remediation |
|-----|------|-------------|
| TODO: e.g., middleware on non-FedRAMP platform | High / Medium / Low | TODO |

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
| AC-2 | Account Management | TODO: Implemented / Partial / Not implemented | TODO |
| AC-6 | Least Privilege | TODO | TODO |
| AU-2 | Event Logging | TODO | TODO |
| AU-11 | Audit Record Retention | TODO | TODO |
| IA-2(1) | MFA for Privileged Users | TODO | TODO |
| IA-2(2) | MFA for Non-Privileged Users | TODO | TODO |
| SC-28 | Protection of Information at Rest | TODO | TODO |
| CM-3 | Configuration Change Control | TODO | TODO |
| CM-6 | Configuration Settings | TODO | TODO |
| IR-6 | Incident Reporting | TODO | TODO |

---

## 5. Integration FedRAMP Authorization Checklist

| Integration / System | FedRAMP Status | Authorization Level | Action Required |
|---------------------|---------------|--------------------| --------------|
| TODO: system name | Authorized / Not authorized / Pending | Moderate / High / N/A | TODO |
| TODO: system name | Authorized / Not authorized / Pending | Moderate / High / N/A | TODO |
| TODO: system name | Authorized / Not authorized / Pending | Moderate / High / N/A | TODO |

**Integrations with compliance gaps (require remediation before ATO):**

- TODO: describe gap and remediation approach
- TODO: FedRAMP-authorized alternative if the current system is not authorized

---

## 6. Compliance Automation Configuration

### Shield Event Monitoring

- [ ] Shield Event Monitoring licensed
- [ ] EventLogFile API export configured (target: nightly)
- [ ] LoginEvent export to SIEM configured
- [ ] ReportEvent and ContentDistributionEvent export configured
- [ ] ApiEvent and BulkApiResultEvent export configured
- [ ] SIEM platform: TODO (confirm FedRAMP-authorized: Yes / No)
- [ ] Log retention period configured to meet AU-11 requirements: TODO days/years

### Automated Control Evidence Collection

- [ ] Metadata API scheduled backup for org configuration (weekly minimum for CM-6)
- [ ] Connected App inventory export configured (AC-17 evidence)
- [ ] Permission set assignment alert flow configured (AC-2 account management)
- [ ] MFA enforcement status report configured (IA-5 evidence)
- [ ] Platform Encryption policy documentation scheduled (SC-28 evidence)

### Platform Encryption (if required for SC-28)

- [ ] Platform Encryption licensed
- [ ] Fields containing CUI / PHI / CDI encrypted (list fields: TODO)
- [ ] Key rotation schedule set to: TODO (90 days recommended for FedRAMP High)
- [ ] BYOK configured (required for IL5): Yes / No / N/A
- [ ] Key storage location (BYOK): TODO

---

## 7. FISMA Continuous Monitoring Plan

### Monitoring Cadence

| Activity | Frequency | Responsible Party | Evidence Artifact |
|----------|-----------|------------------|------------------|
| Vulnerability scanning (infrastructure) | Monthly | Salesforce (inherited) | Salesforce scan reports |
| Vulnerability scanning (customer middleware/integration) | Monthly | TODO | TODO |
| POA&M review and update | Monthly | TODO | POA&M document |
| Monthly report to agency AO | Monthly | TODO | Monthly status report |
| Control assessment (rotating subset) | Annual | TODO 3PAO | SAR update |
| Contingency plan test | Annual | TODO | CP-4 test report |
| Significant change review | Per change | TODO | Change assessment record |

### Current POA&M Summary

| POA&M ID | Control | Weakness | Risk Rating | Due Date | Status |
|----------|---------|----------|-------------|----------|--------|
| TODO | TODO | TODO | High / Moderate / Low | TODO | Open / In progress / Closed |

### Significant Change Notification Procedure

1. Proposed change submitted to: TODO (change control board / security team)
2. Significant change determination by: TODO
3. AO notification required: Yes / No / TBD
4. Partial re-assessment required: Yes / No / TBD
5. Pre-deployment approval gate: TODO process

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
| GOV-001 | TODO | TODO | High / Medium / Low | TODO | TODO |
| GOV-002 | TODO | TODO | High / Medium / Low | TODO | TODO |

### Architecture Decisions Required

| Decision | Options Considered | Recommended | Decision Owner | Decision Due |
|----------|-------------------|-------------|----------------|-------------|
| TODO | TODO | TODO | TODO | TODO |

---

## Assessor Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Lead Assessor | TODO | TODO | TODO |
| Agency ISO / Security Officer | TODO | TODO | TODO |
| Authorizing Official (AO) | TODO | TODO | TODO |
