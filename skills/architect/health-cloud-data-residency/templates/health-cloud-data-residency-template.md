# Health Cloud Data Residency — Assessment Template

Use this template when architecting or reviewing a Health Cloud deployment that must satisfy geographic data residency, HIPAA, GDPR, or national health-data regulations. Complete every section before go-live. Obtain explicit stakeholder sign-off on each section.

---

## 1. Engagement Summary

| Field | Value |
|---|---|
| Customer / Client Name | |
| Health Cloud Org ID | |
| Assessment Date | |
| Assessed By | |
| Compliance Review Authority (DPO / Privacy Officer / HIPAA Officer) | |
| Target Go-Live Date | |

---

## 2. Regulatory Framework Inventory

Check all that apply and add jurisdiction-specific notes.

| Regulatory Framework | Applies? | Notes |
|---|---|---|
| US HIPAA (Health Insurance Portability and Accountability Act) | Yes / No | |
| EU GDPR — General Data Processing | Yes / No | |
| EU GDPR — Article 9 Special-Category Health Data | Yes / No | Required if GDPR applies and health data is processed |
| UK GDPR (post-Brexit) | Yes / No | |
| Australia My Health Records Act 2012 | Yes / No | |
| Australia Privacy Act 1988 | Yes / No | |
| Other national health data law (specify) | Yes / No | |

---

## 3. Hyperforce Region Selection

| Field | Value |
|---|---|
| Hyperforce Region Selected | (e.g., EU — Frankfurt, AU — Sydney, US — North America) |
| Regulatory Basis for Region Selection | (e.g., GDPR requires EU primary storage; customer data governance policy) |
| Org Provisioning Confirmed (region locked at provisioning) | Yes / No / Pending |
| Hyperforce Infrastructure Agreement Executed | Yes / No / Pending |
| HIPAA Business Associate Agreement Executed | Yes / No / Not applicable |
| GDPR Data Processing Addendum Executed | Yes / No / Not applicable |
| UK IDTA or SCCs in place (if UK GDPR applies) | Yes / No / Not applicable |

**Important:** Hyperforce regional selection controls primary data-at-rest storage for core Health Cloud objects. It does NOT guarantee that all features (Einstein AI, CRM Analytics, MuleSoft) process data exclusively in this region. See Section 6.

---

## 4. BAA Coverage Matrix

Complete one row for each Salesforce product or feature in scope. Every feature that will process PHI must have a documented BAA status.

| Feature / Product | In Scope? | BAA Coverage Status | Addendum Required? | Addendum Executed? | PHI Permitted to Flow? |
|---|---|---|---|---|---|
| Health Cloud (core) | Yes / No | Covered by standard Salesforce HIPAA BAA | No | N/A | Yes (if BAA executed) |
| Health Cloud Intelligence / CRM Analytics | Yes / No | NOT covered by standard BAA | Yes | Yes / No / Pending | Only after addendum |
| MuleSoft Anypoint Platform | Yes / No | NOT covered by standard Salesforce BAA | Yes (MuleSoft BAA) | Yes / No / Pending | Only after addendum |
| Marketing Cloud | Yes / No | NOT covered by standard Salesforce BAA | Yes (Marketing Cloud BAA) | Yes / No / Pending | Only after addendum |
| Einstein AI features (specify) | Yes / No | Varies by feature — verify current scope | Verify per feature | Yes / No / Pending | Verify per feature |
| Salesforce Shield (encryption) | Yes / No | Covered by standard BAA | No | N/A | Yes |
| Other (specify) | Yes / No | | | | |

**Gap actions:** List any features in the table above where PHI is flowing but the addendum is not yet executed:

- [ ] Gap 1: ___
- [ ] Gap 2: ___

---

## 5. Transient Processing Exception Log

Document every feature or service where data temporarily leaves the primary Hyperforce region during processing. Obtain customer compliance sign-off on each entry.

| Feature | Nature of Transient Processing | Salesforce Documentation Reference | Data Sensitivity | Compensating Control | Compliance Sign-Off |
|---|---|---|---|---|---|
| Einstein AI inference | Inference jobs may route to non-primary-region compute | Salesforce AI Data Use Policy | High (if PHI in context window) | Limit PHI in Einstein context; disable for PHI-heavy record types if addendum not in place | Pending |
| CRM Analytics / HCI pipelines | Analytics compute layer may differ from Hyperforce primary region | Health Cloud Intelligence documentation | High (if PHI in datasets) | Require BAA addendum before PHI flows to HCI datasets | Pending |
| MuleSoft integration | Anypoint Runtime Plane may be in different region; logging captures payloads | MuleSoft Trust and Compliance docs | High (if PHI in FHIR payloads) | DataWeave payload masking; MuleSoft BAA addendum | Pending |
| Flow automation with external callouts | External service callouts during Flow execution may cross regional boundaries | Salesforce Flow documentation | Medium-High | Restrict external callouts to endpoints within compliance region; log all callout endpoints | Pending |
| (Add additional features as applicable) | | | | | |

**Customer / DPO sign-off on transient processing exceptions:**

Signed: ___________________________ Date: _______________

Role: ___________________________

---

## 6. GDPR Article 9 Special-Category Obligations (EU / UK orgs only)

Complete this section only if GDPR applies and health data is processed.

| Requirement | Status | Notes |
|---|---|---|
| Legal basis for processing health data under Article 9(2) identified | Identified / Not identified | (e.g., healthcare treatment — Art 9(2)(h); explicit consent — Art 9(2)(a)) |
| Explicit consent obtained (if relying on consent basis) | Yes / No / Not applicable | |
| Data Protection Impact Assessment (DPIA) completed | Completed / In progress / Not started | DPIA is mandatory for large-scale health data processing |
| DPO appointed (if required by scale of processing) | Yes / No / Not required | |
| DPO reviewed and signed off on this assessment | Yes / No / Pending | |
| Data minimisation applied to Health Cloud field model | Yes / No / In progress | Review Health Cloud default field exposure; tighten FLS to minimum necessary |
| Processing purposes documented | Yes / No / In progress | Each data processing purpose must be explicitly documented |

**DPIA Reference:** (link to DPIA document or record ID)

---

## 7. Australia My Health Records Act Assessment (AU orgs only)

Complete this section only if the org processes My Health Record data under the My Health Records Act 2012.

| Requirement | Status | Notes |
|---|---|---|
| Salesforce Hyperforce AU region confirmed as primary storage | Confirmed / Pending | |
| Hyperforce Infrastructure Agreement for AU executed | Yes / No / Pending | |
| Cross-border disclosure restriction evaluated for each transient processing exception | Yes / No / In progress | "Disclosure" under the Act includes making data accessible to overseas entities |
| Salesforce compliance position on My Health Records Act obtained (letter of assurance or equivalent) | Yes / No / Requested | |
| Australian health law specialist reviewed the architecture | Yes / No / Pending | |
| Einstein features scoped to exclude My Health Record data (if no AU-region inference confirmed) | Yes / No / Not applicable | |

---

## 8. Sandbox and Development Environment Controls

| Control | Status | Notes |
|---|---|---|
| Data Mask profile created with explicit PHI field coverage | Yes / No / In progress | Do not rely on default Data Mask configuration |
| PHI field inventory completed (all fields including managed package fields, ContentDocument bodies) | Yes / No / In progress | Include `HealthCloudGA__*` namespace fields |
| Post-mask spot-check performed before granting developer/tester access | Yes / No / Pending | Open actual records and file attachments to verify |
| Data Mask profile updated whenever new fields are added | Process established / Not yet | |
| Non-BAA-covered personnel restricted from pre-mask sandbox access | Yes / No / Pending | |
| ContentDocument / ContentNote bodies explicitly included in mask profile | Yes / No / In progress | File bodies are not masked by default |

---

## 9. Salesforce Shield Configuration

| Control | Status | Notes |
|---|---|---|
| Platform Encryption applied to highest-sensitivity PHI fields | Yes / No / In progress | (e.g., SSN, MRN, diagnosis codes, clinical notes) |
| Field Audit Trail configured for PHI field access logging | Yes / No / Not required | |
| Event Monitoring enabled for sensitive PHI access events | Yes / No / Not required | |
| Encryption key management policy documented | Yes / No / In progress | Tenant secret rotation schedule established |

---

## 10. Architecture Decision Record Summary

Summarise the key architecture decisions made during this assessment for the project compliance register.

**Hyperforce Region Decision:**

_Describe the region selected, why it was selected, and any alternatives considered._

**BAA Coverage Decision:**

_List each feature, its BAA status, and the decision made (addendum obtained / feature excluded / PHI de-identified before feature reaches it)._

**Transient Processing Exception Acceptance:**

_Summarise the accepted exceptions and the compensating controls applied._

**Outstanding Risks:**

_List any unresolved gaps, their severity, and the target resolution date._

---

## 11. Sign-Off

| Role | Name | Signature | Date |
|---|---|---|---|
| Salesforce Architect (this assessment) | | | |
| HIPAA Privacy Officer / DPO | | | |
| Customer Technical Lead | | | |
| Customer Compliance / Legal | | | |

---

*Template version: 1.0.0 | Skill: health-cloud-data-residency | Updated: 2026-04-11*
