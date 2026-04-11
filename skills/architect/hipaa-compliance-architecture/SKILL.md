---
name: hipaa-compliance-architecture
description: "Use this skill to design HIPAA-compliant Salesforce org architectures for healthcare organizations storing or processing Protected Health Information (PHI). Trigger keywords: HIPAA BAA, PHI storage, Shield encryption, Health Cloud compliance, HIPAA technical safeguards, covered entity Salesforce architecture. NOT for general security architecture or non-healthcare compliance."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "We are building a Health Cloud implementation for a covered entity and need to ensure we are HIPAA compliant — where do we start?"
  - "Our org stores patient data including diagnoses and SSNs — what Salesforce features are required for HIPAA and what do we need to sign with Salesforce?"
  - "The client wants to enable Chatter for clinical care teams but we have a BAA with Salesforce — is standard Chatter covered?"
  - "What is the difference between Shield Platform Encryption and HIPAA compliance — does enabling Shield make us HIPAA compliant?"
  - "We need to pass a HIPAA security risk assessment for our Salesforce org — what architecture controls must be documented?"
tags:
  - hipaa
  - phi
  - health-cloud
  - shield
  - baa
  - compliance
  - architect
  - encryption
inputs:
  - "List of Salesforce products and editions in scope (Health Cloud, Experience Cloud, Service Cloud, AppExchange products)"
  - "Categories of PHI the org will store (demographics, diagnoses, treatment records, payment info)"
  - "Executed or draft BAA with Salesforce"
  - "Existing Shield licensing status (SPE, Field Audit Trail, Event Monitoring)"
  - "Third-party integrations that will touch PHI (EHR, billing systems, data warehouses)"
outputs:
  - "HIPAA-compliant org architecture decision record including BAA scope map"
  - "Shield control-to-HIPAA safeguard mapping (technical safeguards coverage analysis)"
  - "PHI field inventory with SPE encryption policy recommendations"
  - "Non-Shield HIPAA control checklist (access controls, audit, workforce, incident response)"
  - "Uncovered-service risk register (services outside BAA scope that must not store PHI)"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-11
---

# HIPAA Compliance Architecture

This skill activates when designing or reviewing a Salesforce org that must comply with HIPAA for a covered entity or business associate. It provides architecture-level decisions — BAA scope validation, Shield control mapping to HIPAA technical safeguards, PHI storage boundaries, and non-Shield compliance requirements — that go beyond workflow configuration. Use it alongside `admin/hipaa-workflow-design` for day-to-day operational controls.

---

## Before Starting

Gather this context before working on anything in this domain:

- **BAA status**: Has a Business Associate Agreement been signed with Salesforce? Until it is signed, no PHI may be stored in any Salesforce service regardless of encryption or access controls.
- **Product inventory**: Compile every Salesforce product in use — core platform, Health Cloud, Experience Cloud, Shield add-ons, and all AppExchange products. BAA coverage is product-specific; products not listed in the executed BAA are not covered even if they run on covered infrastructure.
- **Shield licensing**: Confirm whether the org has Shield Platform Encryption, Field Audit Trail, and/or Event Monitoring enabled. Shield is a paid add-on not included in any Salesforce edition. Verify through `Setup > Company Information > Licenses`.
- **PHI categories**: Identify the 18 HIPAA-defined PHI identifiers the org will handle. This determines which object fields require SPE and which audit retention periods apply.
- **Third-party integrations**: Any connected system that receives PHI must also operate under a BAA or equivalent data processing agreement.

---

## Core Concepts

### Business Associate Agreement (BAA) Scope

The BAA is the contractual foundation of HIPAA compliance in Salesforce. Salesforce acts as a Business Associate under HIPAA when it processes PHI on behalf of a Covered Entity or another Business Associate. The executed BAA with Salesforce defines exactly which products and services are covered. Products not explicitly listed in the BAA are outside HIPAA coverage — storing PHI in uncovered services creates a HIPAA breach risk even if the org has Shield enabled.

Key BAA-covered Salesforce products typically include: Health Cloud, Sales Cloud, Service Cloud, Experience Cloud (with restrictions), Shield (SPE, FAT, Event Monitoring), and Tableau CRM (with caveats). Products that are **not** covered under the standard BAA include standard Chatter (as of current published guidance), certain Einstein features, some AppExchange managed packages (which require their own BAA addenda with the ISV), and Salesforce Sandbox environments unless explicitly addressed.

Practitioners must review the current Salesforce HIPAA BAA help article (`help.salesforce.com/s/articleView?id=sf.compliance_hipaa.htm`) because covered product lists change with releases.

### Salesforce Shield: Three Controls

Shield is a paid add-on bundle providing three distinct compliance controls:

1. **Shield Platform Encryption (SPE)** — Encrypts PHI at rest using AES-256 with Salesforce-managed or customer-managed keys (BYOK). Covers field-level and file encryption. Addresses the HIPAA Security Rule technical safeguard for data at rest (45 CFR §164.312(a)(2)(iv) and §164.312(e)(2)(ii)). SPE introduces functional tradeoffs: encrypted fields cannot be used in formula fields, external IDs, unique constraints, sorting, or certain SOQL operations — field selection must be designed carefully.

2. **Field Audit Trail (FAT)** — Extends field history tracking retention from 18 months (standard History Tracking limit) to up to 10 years. HIPAA requires covered entities to retain documentation of HIPAA policies and procedures for 6 years from creation or last effective date; medical records retention varies by state but FAT supports the 10-year outer bound. Standard Field History Tracking is insufficient for HIPAA audit requirements.

3. **Event Monitoring** — Provides detailed transaction security logs including login history, API calls, report exports, and data access events. Maps to HIPAA Security Rule audit control requirements (45 CFR §164.312(b)). Logs are stored as EventLogFile objects queryable via SOQL or exportable to a SIEM.

Shield addresses a subset of HIPAA technical safeguards. It does not on its own satisfy the full HIPAA Security Rule — see Non-Shield Requirements below.

### Non-Shield HIPAA Requirements

Shield is one component of a HIPAA compliance architecture. The HIPAA Security Rule (45 CFR Part 164) requires controls across three categories: Administrative, Physical, and Technical safeguards. Salesforce physical safeguards are covered by Salesforce's infrastructure (documented in their ISMS and SOC 2 reports). The following controls require customer action beyond Shield:

- **Access Controls (Technical — 45 CFR §164.312(a))**: Unique user IDs, emergency access procedures, automatic logoff, and encryption. In Salesforce: enforce MFA (required for all users since Summer '22 for orgs with PHI under BAA), profile and permission set least-privilege design, Named Credentials for integration users, and Connected App policies.
- **Risk Assessment (Administrative — 45 CFR §164.308(a)(1))**: Covered entities must conduct and document a security risk assessment. For Salesforce, this means a formal review of the org architecture against HIPAA controls — this skill's output artifacts feed that assessment.
- **Workforce Training and Sanctions Policy (Administrative — 45 CFR §164.308(a)(5))**: Platform alone does not satisfy this — training and policies must be documented and enforced by the covered entity.
- **Incident Response (Administrative — 45 CFR §164.308(a)(6))**: Salesforce Event Monitoring supports detection; the covered entity must define and test breach notification procedures within the 60-day HIPAA notification window.
- **Audit Controls (Technical — 45 CFR §164.312(b))**: Event Monitoring plus FAT together provide the Salesforce-side audit record. The covered entity must retain and review these logs.

---

## Common Patterns

### BAA Scope Boundary Architecture

**When to use:** Any new Health Cloud or healthcare implementation where PHI will be stored in Salesforce, or when an existing org is expanding feature use (adding AppExchange packages, Experience Cloud portals, Einstein features).

**How it works:**
1. Enumerate every Salesforce product and AppExchange package used by the org.
2. Obtain the current signed BAA and identify the covered product list by name.
3. For each product not listed, document a BAA coverage gap.
4. For AppExchange packages: request a signed BAA addendum from each ISV. Until received, treat these services as uncovered and do not write PHI to any field managed by that package.
5. For Experience Cloud: confirm the specific Experience Cloud template (LWR, Aura, Tabs+VF) is addressed in the BAA; review sharing architecture to ensure PHI-bearing records are not accessible to guest users.
6. Document the approved product set in the org architecture decision record and enforce via a custom metadata registry (`HIPAA_Covered_Service__mdt`) checked during deployment validation.

**Why not the alternative:** Assuming all Salesforce infrastructure is uniformly covered by a single BAA is the most common compliance gap in Salesforce HIPAA implementations. Product-specific coverage is contractual, not technical.

### Shield PHI Field Encryption Design

**When to use:** Designing the SPE encryption policy for a Health Cloud org that has Shield enabled and an executed BAA. Covers field selection, key management approach, and functional limitation mitigation.

**How it works:**
1. Conduct a PHI field inventory across all standard and custom objects. Map each field to one of the 18 HIPAA-defined identifiers.
2. Apply the SPE deterministic encryption scheme to fields that must be searchable (e.g., Name, Phone, Email) — deterministic encryption allows exact-match SOQL queries but does not support range queries or LIKE operators.
3. Apply probabilistic encryption to fields that require maximum security and do not need to be queried by value (e.g., Social Security Number stored in a custom field, clinical notes text areas).
4. Do not encrypt fields used in: formula fields, workflow rules that reference field values, external IDs, unique fields, or SOQL ORDER BY clauses — re-architect those query patterns before enabling SPE.
5. For key management: evaluate whether tenant secret (Salesforce-managed, lowest operational burden) or BYOK (customer-controlled key material, highest control) is required by the organization's security policy. BYOK requires HSM infrastructure.
6. Document the encryption policy in a data classification matrix and validate in a Sandbox with Shield before production deployment — SPE enablement on existing data triggers an async re-encryption job that can affect org performance.

**Why not the alternative:** Applying probabilistic encryption to all PHI fields (the "encrypt everything" anti-pattern) breaks SOQL queries, formula fields, and workflow rules silently — flows and automation may produce incorrect results without error messages during testing.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| BAA not yet executed and go-live is imminent | Block PHI entry to the org via validation rules; do not proceed with PHI population until BAA is countersigned | No BAA = no HIPAA coverage regardless of technical controls |
| AppExchange package will store PHI (e.g., e-signature, document generation) | Obtain a signed BAA addendum from the ISV before activation | Managed packages are separate business associates; ISV data handling is outside Salesforce's BAA |
| Team requests standard Chatter for clinical care team collaboration | Redirect to Salesforce Communities or a BAA-covered messaging channel; document risk if standard Chatter is used with PHI | Standard Chatter is not covered under the Salesforce BAA as of current guidance |
| Org needs 10-year audit trail for PHI fields | Enable Shield Field Audit Trail; configure retention to 10 years on all PHI fields | Standard Field History Tracking retains only 18 months — insufficient for HIPAA and many state medical records laws |
| Client asks if Shield alone makes them HIPAA compliant | Provide Shield-to-HIPAA safeguard gap analysis; identify non-Shield requirements (MFA, access controls, risk assessment, workforce training, incident response) | Shield covers encryption at rest, audit trail, and event logging but does not address administrative or all technical safeguards |
| PHI must be shared with external partner via Experience Cloud | Design sharing rules, guest user access controls, and data encryption; verify Experience Cloud is BAA-covered in executed agreement | Guest user misconfiguration is a leading PHI exposure vector in Experience Cloud |
| Org uses Salesforce Sandbox for development/testing | Use synthetic or de-identified data in Sandbox unless Sandbox is explicitly covered in the BAA | Sandbox environments may not be covered under all BAA versions |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner architecting a HIPAA-compliant Salesforce org:

1. **Validate BAA coverage first.** Obtain the signed BAA. Extract the covered product list. Cross-reference against the full org product inventory (platform edition, add-ons, AppExchange packages). Produce a BAA gap register listing every product not covered. Do not proceed to technical design until gaps are resolved or explicitly accepted with a risk treatment decision.

2. **Conduct PHI field inventory.** Working with the health data team, enumerate all objects that will store any of the 18 HIPAA-defined PHI identifiers. Record object name, field name, data type, field label, and the HIPAA identifier category. This inventory drives the SPE encryption policy, FAT configuration, and access control design.

3. **Design the Shield control stack.** For each PHI field, assign an SPE encryption scheme (deterministic vs. probabilistic). Identify functional conflicts (formula fields, external IDs, SOQL sorting) and re-architect those query patterns. Configure FAT retention to 10 years on all PHI fields. Confirm Event Monitoring transaction security policies capture login, report, and data export events for PHI-bearing objects. Document the key management approach (tenant secret vs. BYOK).

4. **Design non-Shield technical safeguards.** Enforce MFA for all users accessing PHI. Apply least-privilege profile and permission set architecture — users should access only the minimum necessary PHI. Configure automatic session timeout. Define Named Credentials or OAuth flows for integration users — do not embed credentials in PHI-touching integration code. Review Connected App policies for external data consumers.

5. **Document administrative safeguard controls.** Produce or reference the organization's risk assessment document mapping Salesforce org controls to HIPAA Security Rule requirements. Confirm workforce training program covers Salesforce-specific PHI handling. Define incident response runbook including Salesforce Event Monitoring alert thresholds and the 60-day breach notification clock.

6. **Validate architecture against HIPAA Security Rule safeguards matrix.** Run `scripts/check_hipaa_compliance_architecture.py` against org metadata. Complete the architecture review checklist below. Produce the HIPAA controls specification artifact for the covered entity's compliance documentation package.

7. **Establish ongoing operational controls.** Set up Event Monitoring log export to a SIEM or secure log store. Configure Shield Key Management rotation schedule. Schedule quarterly BAA coverage reviews when new products or AppExchange packages are added. Assign a designated compliance reviewer role in the org.

---

## Review Checklist

Run through these before marking a HIPAA compliance architecture design complete:

- [ ] BAA is executed and signed; covered product list has been verified against org product inventory
- [ ] All AppExchange packages handling PHI have their own signed BAA addendum with the ISV
- [ ] Standard Chatter is confirmed NOT used for PHI — or a risk acceptance is documented
- [ ] PHI field inventory is complete covering all 18 HIPAA identifiers across all objects
- [ ] SPE encryption policy assigns deterministic or probabilistic scheme to every PHI field with functional conflict analysis completed
- [ ] Shield Field Audit Trail is configured with 10-year retention on all PHI fields
- [ ] Event Monitoring transaction security policies are active for login, report export, and data access events on PHI objects
- [ ] MFA is enforced for all users with access to PHI (required, not optional)
- [ ] Least-privilege permission set architecture is documented and enforced
- [ ] Integration users use Named Credentials or OAuth — no embedded credentials in PHI-touching code
- [ ] Sandbox environments either do not contain real PHI or are explicitly covered in the BAA
- [ ] Risk assessment document references Salesforce org controls
- [ ] Incident response runbook includes Salesforce-specific detection and 60-day breach notification procedure
- [ ] Workforce training program covers Salesforce PHI handling procedures

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **SPE breaks formula fields and SOQL ORDER BY silently** — Enabling SPE on a field used in a formula field causes the formula to return a blank or error result rather than a compile-time failure. Similarly, SOQL queries with ORDER BY on an SPE-encrypted field fail at runtime. Audit all formula fields and SOQL references to candidate PHI fields before enabling encryption.

2. **Event Monitoring logs are transient by default** — EventLogFile records are retained for only 1 day (hourly logs) or 30 days (daily logs) unless the org has purchased Event Log File Storage or is streaming logs to an external system. Without active log export, audit trail data required for HIPAA incident investigation may be unavailable. Configure log export before go-live.

3. **BYOK key deletion is irreversible data destruction** — Shield BYOK allows customers to control key material. Destroying a BYOK key permanently renders all data encrypted under that key unreadable — there is no recovery path. BYOK is appropriate for regulatory key control requirements, not routine key rotation. Establish strict key lifecycle governance before enabling BYOK.

4. **Re-encryption jobs can cause org performance degradation** — Enabling SPE on a field that already contains data triggers an asynchronous bulk re-encryption job. In large orgs (millions of records), this can saturate async job queues, slow page loads, and affect integration throughput for hours. Plan SPE enablement during a maintenance window with monitoring.

5. **Guest user access ignores sharing rules for certain object types** — Experience Cloud guest users with access to Health Cloud objects can sometimes access PHI through indirect object relationships even when direct access is restricted. Always run a guest user access audit using the Salesforce Org Security Health Check and the Guest User Sharing Rules report before go-live.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| BAA scope map | Table mapping every Salesforce product and AppExchange package to BAA coverage status (covered / gap / ISV addendum required) |
| PHI field inventory | Complete catalog of PHI fields across all objects, including HIPAA identifier category and SPE encryption scheme assignment |
| HIPAA controls specification | HIPAA Security Rule safeguard to Salesforce control mapping matrix, identifying gaps and remediation owners |
| Shield configuration guide | SPE field-by-field encryption policy, FAT retention settings, and Event Monitoring policy configuration |
| Risk register | Non-Shield HIPAA requirements with implementation status and evidence references for the covered entity's risk assessment |
| Architecture decision record | Formal ADR documenting BAA scope, product boundaries, PHI storage decisions, and key management approach |

---

## Related Skills

- `admin/hipaa-workflow-design` — Day-to-day HIPAA workflow controls: minimum necessary access design, Flows with PHI, and audit trail implementation steps; use alongside this skill for full coverage
- `architect/security-architecture-review` — Broader Salesforce security architecture review process; HIPAA compliance architecture is a specialization within it
- `architect/nfr-definition-for-salesforce` — NFR definition framework that includes HIPAA control requirements as a structured section; use to integrate HIPAA requirements into the broader solution NFR set
- `architect/government-cloud-compliance` — Government Cloud compliance architecture; analogous pattern for FedRAMP/FISMA compliance in Government Cloud orgs
