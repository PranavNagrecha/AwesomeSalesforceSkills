---
name: hipaa-workflow-design
description: "Use this skill when designing HIPAA-compliant workflow requirements for Health Cloud: minimum necessary access design, audit trail requirements mapping, access control patterns, and BAA dependency identification. NOT for org-level HIPAA architecture or Shield encryption configuration — use architect/hipaa-compliance-architecture. NOT for care team and SDOH process design — use admin/care-coordination-requirements."
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
  - "tag PHI fields with the HIPAA compliance group in field metadata"
  - "keep field history for clinical fields longer than 18 months"
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
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

# HIPAA Workflow Design for Health Cloud

Use this skill when designing HIPAA-driven workflow requirements for Health Cloud: minimum necessary access, audit trail requirements, PHI access controls, and the mapping from HIPAA safeguards to Salesforce controls. It covers requirements design and mapping. It does NOT cover the build of security controls (Shield Platform Encryption configuration, Event Monitoring pipelines, field-level security setup), which belong to implementation skills.

Grounding note: retention, field tracking, encryption, and Event Monitoring facts here are grounded in the Salesforce Security Guide, Object Reference, and Metadata API Developer Guide (Summer '26). HIPAA regulation text (45 CFR Part 164) and the Salesforce BAA terms did not fetch for this pass, so regulatory citations and BAA scope statements carry UNVERIFIED markers. Legal counsel owns those interpretations.

---

## Before Starting

- Confirm the Business Associate Agreement (BAA) status with Salesforce and which services it covers. UNVERIFIED (2026-10-03): BAA coverage is product-specific and must be in place before PHI is stored; this is a contractual matter not described in the technical guides read.
- Inventory every field that holds PHI and tag it in metadata. `CustomField.complianceGroup` accepts `HIPAA` (with `CCPA`, `COPPA`, `GDPR`, `PCI`, `PII`), and `securityClassification` accepts `Public`, `Internal`, `Confidential`, `Restricted`, and `MissionCritical`.
- Check which PHI fields can be history-tracked at all. Field history cannot track formula, roll-up summary, or auto-number fields, Created By and Last Modified By, long text fields, or multi-select fields. Clinical notes in long text fields need another audit approach.
- Confirm Shield licences (Platform Encryption, Event Monitoring, Field Audit Trail) are in the contract. UNVERIFIED (2026-10-03): that Shield is never included in any edition is a commercial claim not in the guides read.

---

## Questions to Ask Before Configuring

Ask these before designing access or audit controls. Each one traces to a gotcha in `references/gotchas.md`.

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "How long must field change history be kept, and who decides when it may be deleted?" | Without Field Audit Trail, history lasts 18 months (24 via API); with it, archived history is kept until deleted (gotcha 1) | A retention period, an owner, and a deletion procedure | Audit evidence that exists when an investigator asks |
| "Which PHI fields are long text, multi-select, or formulas?" | Those fields cannot be history-tracked (gotcha 2) | A list of untrackable PHI fields and the alternative evidence for each | No false assumption that every PHI change is audited |
| "How long must access logs be kept, and where?" | Event Log Files are kept one year by default for Shield and Event Monitoring customers; streaming events three days; Event Log Objects 30 days (gotcha 3) | A log retention target and an external store | Access history that survives past the platform window |
| "Will Platform Encryption be turned on after history is already archived?" | Previously archived field history stays unencrypted (gotcha 4) | An encryption timeline aligned with archiving | No unencrypted PHI left in the archive |
| "Which roles need which PHI fields?" | Minimum necessary access is field-level as well as record-level (gotcha 6) | An access matrix per role and field | Permission sets that grant only what each role needs |
| "Are PHI fields tagged so they can be found later?" | `complianceGroup` and `securityClassification` live on the field definition (gotcha 7) | A tagging rule applied in every field deploy | A PHI inventory that maintains itself |

What a proper HIPAA design adds over "just turning on Shield": every PHI field is tagged, its history is kept as long as policy requires, access logs leave the platform before they expire, and each role sees only the fields it needs.

---

## Core Concepts

### Shared responsibility

Salesforce runs the infrastructure; the customer configures who can access PHI, encryption, audit retention, consent workflows, and policies. UNVERIFIED (2026-10-03): the BAA documents this split; its text was not read for this pass.

### HIPAA safeguard to Salesforce control mapping

| HIPAA safeguard (as cited by earlier versions of this skill) | Salesforce control | Grounded platform fact |
|---|---|---|
| Access control | Private org-wide defaults, sharing, permission sets with field-level security | Permission sets carry `fieldPermissions` and `objectPermissions` |
| Audit controls | Field history tracking with Field Audit Trail; Event Monitoring | Retention figures in gotchas 1 and 3 |
| Integrity and encryption at rest | Shield Platform Encryption (`encryptionScheme` on fields) | `ProbabilisticEncryption`, `CaseSensitiveDeterministicEncryption`, `CaseInsensitiveDeterministicEncryption` |
| Minimum necessary | Role-scoped records plus field-level permission sets | Same as access control |

UNVERIFIED (2026-10-03): the section numbers earlier versions of this skill attached to these safeguards (§164.312(a)(1), §164.312(b), §164.312(c)(1), §164.312(e)(1), §164.514(d)) and the "6-year" retention figure come from HIPAA regulation text that did not fetch. The 6-year figure is commonly attributed to the documentation retention rule in 45 CFR 164.316(b)(2); confirm with counsel whether it applies to raw audit logs.

### Field history retention

| Setup | Retention | Fields per object |
|---|---|---|
| Field history tracking without Field Audit Trail | Up to 18 months, and up to 24 months through the API | Up to 20 |
| Field Audit Trail on | Archived history kept until you delete it; by default history moves to the `FieldHistoryArchive` big object after 18 months in production and 1 month in sandboxes | Up to 200 |

A `HistoryRetentionPolicy` sets `archiveAfterMonths` (1 to 18, default 18) and `archiveRetentionYears` (a reminder for manual deletion; data is not deleted automatically). Earlier versions of this skill said Field Audit Trail keeps history "up to 10 years"; the Summer '26 Security Guide says archived data is kept until you delete it.

### Event Monitoring retention

| Source | Retention |
|---|---|
| Event Log Files | "All Shield and Event Monitoring customers have 1 year of Event Log File storage enabled by default" |
| Real-time event streams | "Streaming events are retained for up to three days" |
| Event Log Objects (Hyperforce) | "Log data is retained for up to 30 days" |
| LoginHistory and LoginEvent | 6 months |

Earlier versions of this skill said Event Monitoring logs expire after 30 days by default; that is true of Event Log Objects and of the Login event log lines in one comparison table, but not of Event Log File storage for Shield and Event Monitoring customers. Multi-year retention still requires an external store.

---

## Common Patterns

### Minimum necessary access design

**When to use:** Several roles need different slices of PHI.

**How it works:**
1. Define roles: clinicians, specialists, care coordinators, front desk, billing, compliance.
2. Set org-wide defaults to Private for patient accounts and clinical objects.
3. Grant record access through care team or role-based sharing.
4. Grant field access with permission sets, one per role, from the access matrix; front desk gets demographics, billing gets billing codes, neither gets clinical notes.
5. Tag every PHI field with `complianceGroup` HIPAA and a `securityClassification` (deployable example in `references/metadata-examples.md`).

### Audit trail architecture

**When to use:** Specifying audit controls for production.

**How it works:**
1. Track history on every trackable PHI field (`enableHistory` on the object, `trackHistory` on the field).
2. With Field Audit Trail, set a `HistoryRetentionPolicy` per object and a documented deletion procedure for archived data.
3. List untrackable PHI fields (long text, multi-select, formulas) and define alternative evidence.
4. Export Event Log Files to an external store before the one-year window ends, and subscribe to real-time events if near-real-time alerting is needed.
5. Set the external retention period from counsel's interpretation.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| PHI field change history beyond 18 months | Field Audit Trail with a `HistoryRetentionPolicy` | Standard history lasts 18 months (24 via API) |
| PHI in a long text field | Alternative evidence (versioned records, an audit object, or Event Monitoring) | Long text fields cannot be history-tracked |
| Access logs beyond one year | Export Event Log Files to an external store | One year of Event Log File storage by default |
| Turning on encryption after archiving | Plan re-encryption of archived history with Salesforce | Archived history stays unencrypted |
| PHI inventory upkeep | `complianceGroup` HIPAA on every PHI field | The tag travels with the field definition |
| BAA not yet signed | Do not store PHI | Contractual prerequisite (UNVERIFIED (2026-10-03): legal) |

---

## Recommended Workflow

1. **Verify contractual prerequisites.** BAA status and covered services, confirmed by the account team and counsel.
2. **Build the PHI field inventory as metadata.** Tag every PHI field with `complianceGroup` HIPAA and a `securityClassification`, and flag untrackable types.
3. **Design access.** Private org-wide defaults, sharing per care relationship, and a field-level access matrix turned into permission sets.
4. **Design field audit.** History on trackable PHI fields, Field Audit Trail policies with `archiveAfterMonths`, a deletion procedure, and alternatives for untrackable fields.
5. **Design log retention.** Event Log File export before the one-year window, real-time streams if needed, and an external retention period from counsel.
6. **Specify encryption order.** Enable Platform Encryption before history is archived, or plan re-archiving, and record which fields use which `encryptionScheme`.

---

## Review Checklist

- [ ] BAA status and covered services confirmed in writing
- [ ] Every PHI field tagged `complianceGroup` HIPAA with a `securityClassification`
- [ ] Untrackable PHI fields listed with alternative evidence
- [ ] Private org-wide defaults on PHI objects; sharing designed per care relationship
- [ ] Field access matrix implemented as role permission sets
- [ ] History tracking and Field Audit Trail policies defined, with a deletion procedure
- [ ] Event Log Files exported before the one-year window
- [ ] Encryption timeline aligned with history archiving

---

## Salesforce-Specific Gotchas

The deep versions, with sources, live in `references/gotchas.md`.

| # | Gotcha | One-line consequence |
|---|---|---|
| 1 | History lasts 18 months without Field Audit Trail | Older PHI change evidence is gone |
| 2 | Long text, multi-select, and formula fields cannot be tracked | Clinical notes changes leave no history |
| 3 | Log retention differs by source: 1 year, 30 days, 3 days | Access evidence expires on different clocks |
| 4 | Archived history is not encrypted retroactively | Unencrypted PHI stays in the archive |
| 5 | Deleting a record does not delete its archived history | Archive needs its own deletion procedure |
| 6 | Field limits: 20 tracked fields, or 200 with Field Audit Trail | Large PHI objects exceed standard tracking |
| 7 | PHI tags live on the field definition | Untagged fields fall out of the inventory |
| 8 | Retention policy metadata has documentation conflicts | Hand-written policies may not deploy |

---

## Output Artifacts

| Artifact | Description |
|---|---|
| PHI field inventory | Field metadata tagged with `complianceGroup` and `securityClassification` |
| HIPAA controls specification | Safeguard-to-control mapping with grounded platform facts |
| Access control matrix | Role-by-field access implemented as permission sets |
| Audit and log retention requirements | History policies, deletion procedure, Event Log File export, external retention |

---

## Related Skills

- `admin/health-cloud-patient-setup`: PHI field configuration on patient records
- `admin/health-cloud-consent-management`: consent records and their history
- `architect/hipaa-compliance-architecture`: org-level HIPAA architecture and Shield configuration
