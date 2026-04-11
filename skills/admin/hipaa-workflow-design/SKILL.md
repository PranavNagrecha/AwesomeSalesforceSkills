---
name: hipaa-workflow-design
description: "Use this skill when designing HIPAA-compliant workflow requirements for Health Cloud: minimum necessary access design, audit trail requirements mapping, access control patterns, and BAA dependency identification. NOT for security implementation (Shield Platform Encryption configuration, event monitoring setup) — this skill covers workflow requirements design, not technical security build steps."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "How do I design HIPAA-compliant workflows in Health Cloud for minimum necessary access?"
  - "What are the HIPAA audit trail requirements in Salesforce and how do they map to platform controls?"
  - "BAA with Salesforce prerequisites for storing PHI in Health Cloud"
  - "Why is Field Audit Trail required for HIPAA instead of standard Field History Tracking?"
  - "HIPAA Security Rule mapping to Salesforce Shield controls for healthcare implementation"
tags:
  - health-cloud
  - hipaa
  - phi-compliance
  - audit-trail
  - shield
  - baa
  - access-control
inputs:
  - Health Cloud org (BAA signed or in process with Salesforce)
  - PHI field inventory (which fields contain protected health information)
  - Documented user role taxonomy
  - HIPAA compliance requirements from legal/compliance team
outputs:
  - HIPAA workflow requirements mapped to Salesforce platform controls
  - PHI access control design (OWD + sharing + permission sets)
  - Audit trail requirements specification (Shield Field Audit Trail vs. standard field history)
  - Event Monitoring retention policy requirements
  - BAA dependency checklist
dependencies:
  - admin/health-cloud-patient-setup
  - admin/health-cloud-consent-management
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# HIPAA Workflow Design for Health Cloud

Use this skill when designing HIPAA-compliant workflow requirements for Health Cloud: defining minimum necessary access patterns, identifying audit trail requirements, designing access controls for PHI, and mapping HIPAA Security Rule provisions to Salesforce platform controls. This skill focuses on requirements design and mapping. It does NOT cover the technical implementation of security controls (Shield Platform Encryption field configuration, Event Monitoring stream setup, field-level security configuration) — those are implementation-layer skills.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm that a Business Associate Agreement (BAA) has been signed with Salesforce OR is in the procurement pipeline. No PHI may legally reside in any Salesforce org until the BAA is executed. This is a hard prerequisite.
- Identify which Salesforce products are covered under the BAA. Only specific Salesforce products are BAA-eligible. PHI stored in non-covered services (certain Chatter features, some AppExchange products) voids HIPAA coverage even with Shield enabled.
- Inventory all PHI fields. PHI includes all 18 HIPAA identifier categories: names, dates (except year), geographic data below state, phone/fax, email, SSN, medical record numbers, health plan numbers, account numbers, certificate/license numbers, VINs, device identifiers, URLs, IP addresses, biometric identifiers, full-face photos, and any unique identifying code.
- Confirm Shield Platform Encryption, Field Audit Trail, and Event Monitoring licenses are in the contract. Shield is a paid add-on not included in any Salesforce edition.

---

## Core Concepts

### HIPAA Shared Responsibility Model

Salesforce is responsible for infrastructure security (data center, network, platform availability). The customer is responsible for application-level controls: who can access PHI, encryption configuration, audit trail setup, consent workflows, and policies/procedures. The BAA documents this shared responsibility. A signed BAA does not make the org HIPAA-compliant — the customer must implement all required technical safeguards.

### HIPAA Security Rule to Salesforce Control Mapping

| HIPAA Requirement | Salesforce Control |
|---|---|
| Access Control (§164.312(a)(1)) | OWD = Private + sharing rules + permission sets + care team role-scoped access |
| Audit Controls (§164.312(b)) | Shield Field Audit Trail (10-year retention); Event Monitoring for system access logs |
| Integrity (§164.312(c)(1)) | Shield Platform Encryption for PHI at rest; TLS for data in transit |
| Transmission Security (§164.312(e)(1)) | TLS enforced; no PHI in HTTP headers or query strings |
| Minimum Necessary (§164.514(d)) | OWD-Private + care team role scoping |

### Standard Field History Tracking Does NOT Satisfy HIPAA

HIPAA requires audit log retention for 6 years from the date of creation or last effective date. Standard Field History Tracking retains only 18 months. Shield Field Audit Trail provides up to 10 years of field-level change history. Using standard Field History Tracking for PHI fields will fail a HIPAA audit — this is one of the most consequential architectural mistakes in Health Cloud implementations.

### Event Monitoring Log Expiration

Event Monitoring logs in Salesforce are retained for only 30 days by default. HIPAA requires 6-year retention for access audit logs. Event Monitoring logs must be streamed to an external SIEM (Security Information and Event Management) system within 30 days. Salesforce does not provide long-term storage — this is an ongoing operational requirement, not a one-time configuration.

---

## Common Patterns

### Minimum Necessary Access Design

**When to use:** Designing the permission model for a Health Cloud org with multiple user roles and varying PHI access needs.

**How it works:**
1. Define user roles: primary care clinicians, specialists, care coordinators, administrative staff, billing staff, compliance officers.
2. Set OWD to Private for Account (patient records) and all clinical objects.
3. Use care team role-based sharing: each care team member gets read/edit access to their assigned patient records only. Non-care-team users have no default access.
4. Use permission sets (not profiles) to control field-level access to PHI fields — administrative staff get demographic PHI access but not clinical PHI; billing staff get billing codes but not diagnosis notes.
5. Document the access matrix.

**Why not the alternative:** Public OWD or over-broad permission sets violate the minimum necessary standard by exposing all PHI to all users regardless of care role.

### HIPAA Audit Trail Architecture

**When to use:** Specifying audit trail controls for a production Health Cloud org.

**How it works:**
1. Shield Field Audit Trail for all PHI fields — set retention to 10 years.
2. Event Monitoring enabled for Login, Logout, Report, API Access, and field access events.
3. Event Monitoring logs streamed to an external SIEM within 30 days.
4. SIEM retention policy set to 6 years minimum.
5. Document the complete audit trail architecture in the BAA/compliance record.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| PHI field change history | Shield Field Audit Trail | 10-year retention; standard Field History = 18 months |
| System access log retention | Event Monitoring + SIEM streaming | Logs expire in 30 days without external streaming |
| PHI at-rest encryption | Shield Platform Encryption | Required HIPAA technical safeguard |
| Patient record access control | OWD-Private + care team sharing | Minimum necessary access enforcement |
| BAA not yet signed | Do not store PHI | Hard regulatory prerequisite |
| AppExchange product used with PHI | Verify BAA coverage for that product | Not all AppExchange products are BAA-eligible |

---

## Recommended Workflow

1. **Verify BAA status** — confirm the Salesforce BAA is executed or in process. Document which products are BAA-covered. Flag any products or integrations that may not be covered.
2. **Complete PHI field inventory** — catalog all fields across all objects containing PHI using all 18 HIPAA identifier categories. This inventory drives all downstream security control configuration.
3. **Design access control model** — define user role taxonomy, set OWD to Private for all PHI-containing objects, design care team role-based sharing, and document the access matrix per role.
4. **Map HIPAA controls to Shield** — map each HIPAA Security Rule technical safeguard to a Shield component. Identify all PHI fields for encryption and Field Audit Trail coverage.
5. **Design Event Monitoring streaming** — identify the SIEM target, define log types to stream, design the streaming pipeline, and establish a 6-year retention policy.
6. **Produce implementation requirements specification** — document the HIPAA controls specification for the security implementation team, including the PHI field inventory, access matrix, audit trail scope, and SIEM streaming requirements.

---

## Review Checklist

- [ ] BAA with Salesforce executed before any PHI is stored
- [ ] All PHI-containing Salesforce products confirmed as BAA-covered
- [ ] PHI field inventory completed (all 18 HIPAA identifier categories reviewed)
- [ ] OWD-Private designed for all PHI-containing objects
- [ ] Care team role-based sharing designed for minimum necessary access
- [ ] Shield Field Audit Trail scoped for all PHI fields (NOT standard Field History Tracking)
- [ ] Event Monitoring streaming to SIEM designed with 6-year retention policy
- [ ] Shield Platform Encryption scoped for all PHI at-rest fields

---

## Salesforce-Specific Gotchas

1. **Standard Field History Tracking does not meet HIPAA 6-year retention** — 18-month standard retention fails the audit log requirement. Shield Field Audit Trail (10 years) is required. This is the #1 HIPAA architectural mistake in Health Cloud implementations.

2. **Event Monitoring logs expire in 30 days** — without streaming to a SIEM, all access audit logs are permanently lost. This is an ongoing operational requirement, not a one-time setup step.

3. **BAA coverage is product-specific** — using PHI with an uncovered Salesforce product or AppExchange package breaks HIPAA coverage even with Shield enabled. Verify BAA coverage for every product and service that touches PHI.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| PHI field inventory | Complete catalog of PHI fields across all org objects |
| HIPAA controls specification | HIPAA Security Rule safeguard to Salesforce control mapping |
| Access control matrix | Role-by-role PHI access requirements for OWD and permission set configuration |
| Event Monitoring streaming requirements | SIEM target, log types, 6-year retention policy |

---

## Related Skills

- admin/health-cloud-patient-setup — PHI field configuration on patient records
- admin/health-cloud-consent-management — HIPAA Privacy Rule consent controls
- admin/hipaa-compliance-architecture — Full HIPAA compliance architecture design
