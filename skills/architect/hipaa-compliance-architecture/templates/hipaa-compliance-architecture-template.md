# HIPAA Compliance Architecture Assessment Template

Use this template to document the HIPAA compliance architecture for a Salesforce org. Complete all sections before sign-off. This document supports the covered entity's security risk assessment obligation under 45 CFR §164.308(a)(1).

---

## 1. Engagement Summary

| Field | Value |
|---|---|
| Organization name | |
| Covered entity type | Covered Entity / Business Associate / Hybrid Entity |
| Salesforce org ID | |
| Salesforce edition | |
| Assessment date | |
| Architect / reviewer | |
| BAA execution date | |
| BAA document reference | |

---

## 2. PHI Scope

**Describe the categories of PHI that will be stored or processed in this Salesforce org:**

- [ ] Patient/member name
- [ ] Geographic data (address, zip code)
- [ ] Dates (birth, admission, discharge, death)
- [ ] Phone numbers
- [ ] Fax numbers
- [ ] Email addresses
- [ ] Social Security Numbers
- [ ] Medical record numbers
- [ ] Health plan beneficiary numbers
- [ ] Account numbers
- [ ] Certificate/license numbers
- [ ] Vehicle identifiers
- [ ] Device identifiers
- [ ] Web URLs
- [ ] IP addresses
- [ ] Biometric identifiers
- [ ] Full-face photographs
- [ ] Any other unique identifying numbers or codes

**PHI Objects in this org:**

| Salesforce Object | PHI Fields Present | Notes |
|---|---|---|
| Contact | | |
| Account | | |
| [Custom Object] | | |
| [Custom Object] | | |

---

## 3. BAA Scope Validation

**For each Salesforce product or service in use, confirm BAA coverage:**

| Product / Service | In Use? | BAA Covered? | Evidence / Notes |
|---|---|---|---|
| Health Cloud | | | |
| Sales Cloud | | | |
| Service Cloud | | | |
| Experience Cloud | | | |
| Shield Platform Encryption | | | |
| Shield Field Audit Trail | | | |
| Shield Event Monitoring | | | |
| Standard Chatter | | | NOT covered — do not use for PHI |
| Data Cloud | | | Verify current BAA version |
| Einstein / AI features (specify) | | | Verify per feature |
| Salesforce Files / Content | | | |
| Sandbox environments | | | |
| [AppExchange Package 1] | | | Requires ISV BAA addendum |
| [AppExchange Package 2] | | | Requires ISV BAA addendum |

**BAA Coverage Gaps (products in use but not covered):**

| Product | Gap Description | Risk Treatment (Accept / Remediate / Avoid) | Owner | Due Date |
|---|---|---|---|---|
| | | | | |

---

## 4. Shield Control Configuration

### 4a. Shield Platform Encryption — PHI Field Inventory

| Object | Field API Name | PHI Identifier Type | Encryption Scheme | Formula Dependency? | SOQL Query Dependency? | Approved |
|---|---|---|---|---|---|---|
| | | | Deterministic / Probabilistic / Not Encrypted | Yes / No | Yes / No | |

**Key Management Approach:**
- [ ] Tenant Secret (Salesforce-managed)
- [ ] BYOK (Customer-managed, HSM required)

BYOK HSM details (if applicable): ____________________

### 4b. Shield Field Audit Trail

| Object | PHI Fields Tracked | Retention Period Configured | Notes |
|---|---|---|---|
| | | 10 years | |

Field Audit Trail configured in Setup: Yes / No / Pending

### 4c. Event Monitoring

| Policy | Enabled? | Log Retention | Export Destination |
|---|---|---|---|
| Login events | | | |
| Report export events | | | |
| API call events | | | |
| Data export events (PHI objects) | | | |
| Anomalous activity alerts | | | |

---

## 5. Non-Shield HIPAA Technical Safeguards

| Safeguard | 45 CFR Reference | Salesforce Control | Status | Evidence |
|---|---|---|---|---|
| Unique user identification | §164.312(a)(2)(i) | Named user accounts; no shared logins | | |
| Emergency access procedure | §164.312(a)(2)(ii) | Documented break-glass process | | |
| Automatic logoff | §164.312(a)(2)(iii) | Session timeout policy in Setup | | |
| Encryption at rest | §164.312(a)(2)(iv) | Shield Platform Encryption | | |
| Audit controls | §164.312(b) | Field Audit Trail + Event Monitoring | | |
| User authentication | §164.312(d) | MFA enforced for all PHI-access users | | |
| Transmission security | §164.312(e)(2)(ii) | TLS 1.2+ enforced; no plaintext PHI in APIs | | |

**MFA enforcement status:** All users / Some users / Not enforced

**Session timeout configured (minutes):** ____

---

## 6. HIPAA Administrative Safeguards

| Safeguard | 45 CFR Reference | Organizational Owner | Status | Document Reference |
|---|---|---|---|---|
| Security risk analysis | §164.308(a)(1)(ii)(A) | | | This document |
| Risk management plan | §164.308(a)(1)(ii)(B) | | | |
| Sanction policy | §164.308(a)(1)(ii)(C) | | | |
| Information system activity review | §164.308(a)(1)(ii)(D) | | Event Monitoring export | |
| Assigned security responsibility | §164.308(a)(2) | | | |
| Workforce authorization | §164.308(a)(3) | | | |
| Workforce training program | §164.308(a)(5) | | | |
| Security incident procedures | §164.308(a)(6) | | | See Section 8 |
| Contingency plan | §164.308(a)(7) | | | |
| Business associate contracts | §164.308(b)(1) | | | See Section 3 |

---

## 7. Access Control Architecture

**Permission Set / Profile Matrix (summarize):**

| User Role | Objects Accessible | PHI Field Visibility | Justification (Minimum Necessary) |
|---|---|---|---|
| Care Coordinator | | | |
| Nurse / Clinician | | | |
| Administrative Staff | | | |
| Integration User | | | |
| System Administrator | | | |

**Least Privilege Verification:** Have permission sets been reviewed to confirm users access only the minimum necessary PHI for their role? Yes / No / In Progress

---

## 8. Incident Response

| Element | Detail |
|---|---|
| Incident detection method | Event Monitoring alerts + manual report |
| Incident response owner | |
| Breach notification 60-day clock trigger | Discovery of potential impermissible disclosure of PHI |
| Salesforce support escalation path | Salesforce Trust + Legal contact |
| HHS OCR notification process documented? | Yes / No |
| Affected individual notification process documented? | Yes / No |

---

## 9. Architecture Decision Records

Document significant HIPAA-related architecture decisions:

| Decision | Options Considered | Decision Made | Rationale | Date |
|---|---|---|---|---|
| Key management approach | Tenant Secret vs. BYOK | | | |
| Chatter for clinical teams | Allow / Block | | | |
| [AppExchange package] BAA gap | Accept risk / Replace vendor / Block PHI | | | |
| SPE field encryption scheme | Per field (see Section 4a) | | | |

---

## 10. Sign-Off

| Role | Name | Date | Signature |
|---|---|---|---|
| Salesforce Architect | | | |
| Covered Entity Compliance Officer | | | |
| CISO / Security Lead | | | |
| Legal (BAA Review) | | | |

---

## 11. Review History

| Version | Date | Reviewer | Changes |
|---|---|---|---|
| 1.0 | | | Initial assessment |
| | | | |
