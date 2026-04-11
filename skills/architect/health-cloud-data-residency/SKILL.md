---
name: health-cloud-data-residency
description: "Use this skill when architecting Health Cloud orgs that must satisfy geographic data residency, HIPAA, GDPR, or national health-data regulations on Hyperforce — including scoping the HIPAA BAA, mapping transient processing exceptions, and documenting which features require separate compliance addenda. NOT for generic multi-region Salesforce architecture unrelated to healthcare data, and NOT for non-healthcare data residency requirements (use a general Hyperforce architecture skill for those)."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "where does Salesforce Health Cloud store patient data and which region can I select on Hyperforce"
  - "does the HIPAA Business Associate Agreement cover Einstein AI features and Health Cloud Intelligence analytics"
  - "our healthcare org must comply with GDPR Article 9 special-category health data rules — what does that mean for our Salesforce setup"
  - "Australia My Health Records Act cross-border restriction with Hyperforce regional selection"
  - "transient processing outside region for Flow automation or Einstein features in Health Cloud"
tags:
  - hyperforce
  - hipaa
  - gdpr
  - data-residency
  - health-cloud
  - special-category-data
  - compliance
inputs:
  - "Target deployment region (US, EU, APAC, Australia, etc.)"
  - "List of Health Cloud features in scope (Health Cloud Intelligence, Einstein, MuleSoft, Marketing Cloud)"
  - "Applicable regulatory frameworks (HIPAA, GDPR, My Health Records Act, local health data laws)"
  - "Existing BAA or Data Processing Agreement status with Salesforce"
  - "Sandbox strategy and use of Data Mask or anonymized datasets"
outputs:
  - "Data residency gap analysis documenting which features satisfy regional storage vs. which involve transient cross-region processing"
  - "BAA coverage matrix mapping features to HIPAA BAA scope vs. addenda required"
  - "Architecture decision record (ADR) for Hyperforce region selection with regulatory rationale"
  - "Review checklist for compliance sign-off before go-live"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-11
---

# Health Cloud Data Residency

This skill activates when an architect or compliance team must establish and document where Health Cloud patient data is stored and processed on Hyperforce, identify which Salesforce features fall outside HIPAA BAA coverage, and satisfy jurisdiction-specific regulations that go beyond simple regional selection. It covers HIPAA BAA scoping, GDPR Article 9 obligations, Australia My Health Records Act cross-border constraints, and the transient processing gap that affects Einstein, Flow, and analytics workloads.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Hyperforce region confirmation:** Confirm which Hyperforce region the org is provisioned in (or will be provisioned in). Primary data storage region is set at org provisioning time and cannot be changed post-provisioning without a full re-provisioning engagement.
- **BAA and Infrastructure Agreement status:** Both the HIPAA Business Associate Agreement (BAA) AND the Hyperforce Infrastructure Agreement must be separately executed with Salesforce. Holding one does not imply the other.
- **Feature inventory:** Identify whether the project uses Health Cloud Intelligence (formerly Tableau CRM / Einstein Analytics for Health Cloud), MuleSoft integrations, Marketing Cloud connectors, or Einstein AI features. Each of these may require separate BAA addenda or is explicitly excluded from the standard HIPAA BAA.
- **Most common wrong assumption:** Practitioners routinely assume that selecting an EU or AU Hyperforce region guarantees complete data residency for all features. Transient processing for AI, analytics pipelines, and some platform services may occur outside the selected region even when primary storage is compliant.
- **Regulatory framework inventory:** Determine which jurisdictions apply — US HIPAA, EU GDPR (especially Article 9 for health data as special-category data), Australia My Health Records Act 2012, or other national frameworks.

---

## Core Concepts

### Hyperforce Regional Model and Its Limits

Hyperforce is Salesforce's next-generation public cloud infrastructure that allows Health Cloud customer data to be stored primarily within a specified geographic region (e.g., EU, US, Australia). Regional selection controls **primary data-at-rest storage** for core Health Cloud objects, standard platform data, and most metadata.

What Hyperforce regional selection does NOT guarantee:
- Einstein AI feature inference and model training pipelines may process data in non-primary regions transiently.
- Health Cloud Intelligence (formerly Tableau CRM analytics) runs on a separate compute layer with its own regional routing that may differ from the primary Hyperforce region.
- Some platform background jobs (certain scheduled jobs, system replication for DR, some identity services) involve transient cross-region data movement as documented in the Hyperforce Infrastructure Agreement.
- MuleSoft Anypoint Platform is a separate service with its own regional infrastructure and requires its own compliance evaluation.

Architects must document these exceptions explicitly in the data residency design and obtain customer/DPO sign-off on the residual risks.

### HIPAA BAA Scope vs. Required Addenda

Salesforce's standard HIPAA BAA covers core Health Cloud, Sales Cloud, Service Cloud, and standard platform features. However, several commonly used Health Cloud capabilities fall outside the standard BAA scope and require separate negotiated addenda:

- **Health Cloud Intelligence** (Tableau CRM-based analytics): Requires a separate BAA addendum because it runs on a distinct analytics processing layer.
- **MuleSoft Anypoint Platform**: Covered by a separate MuleSoft BAA addendum; not included in the standard Salesforce HIPAA BAA.
- **Marketing Cloud connectors**: Marketing Cloud operates under its own BAA; cross-cloud data flows that pass PHI require both BAAs to be in place and the integration to be configured to avoid logging PHI in Marketing Cloud if that platform's BAA is not executed.
- **Einstein AI features (Einstein Copilot, Einstein for Health)**: Subject to Salesforce's AI Data Use Policy; verify current BAA coverage for specific Einstein features before including PHI in prompts or Einstein context windows.

Missing an addendum for one of these features while transmitting PHI through it constitutes a HIPAA BAA gap, which is a reportable compliance deficiency.

### Transient Processing Gap

Even when primary data residency is satisfied, transient processing occurs when Salesforce platform services temporarily load and process data in compute infrastructure that may be outside the primary region. Documented scenarios include:

- **Einstein AI inference jobs**: When a user invokes an Einstein feature, PHI included in the context window is sent to Einstein's inference infrastructure, which may not be co-located with the primary Hyperforce region.
- **Flow automation**: Complex Flow invocations, especially those calling external services or platform events, may trigger processing that crosses regional boundaries during orchestration.
- **Analytics and reporting pipelines**: Scheduled analytics jobs in Health Cloud Intelligence or CRM Analytics may temporarily move data to compute infrastructure in different regions.

The correct architectural response is to document these exceptions in the Data Processing Agreement and the customer's own HIPAA/GDPR risk register, implement field-level masking or tokenization for the highest-sensitivity fields (e.g., SSN, diagnosis codes) before they reach features with transient processing gaps, and consider whether certain Einstein features can be disabled or scoped to exclude PHI.

### Special-Category Data Under GDPR Article 9

For EU-deployed Health Cloud orgs, health data is classified as special-category personal data under GDPR Article 9. This imposes stricter requirements beyond standard GDPR:

- **Explicit consent or alternative legal basis**: Processing special-category health data requires explicit consent from the data subject, or reliance on another Article 9(2) exemption (e.g., healthcare treatment, public health necessity). Standard GDPR legitimate interest does NOT apply.
- **Data Protection Impact Assessment (DPIA)**: Mandatory before deploying Health Cloud in EU if processing health data at scale.
- **Data minimisation and purpose limitation**: Fields storing health data should be restricted to the minimum necessary; Health Cloud's default data model is expansive and may need field-level security tightening.
- **DPO involvement**: If the healthcare organisation processes health data at large scale, a Data Protection Officer (DPO) appointment is mandatory and must be involved in architecture sign-off.

---

## Common Patterns

### Pattern: Hyperforce Region + BAA Coverage Matrix

**When to use:** At architecture initiation for any Health Cloud project that involves PHI and must satisfy HIPAA or equivalent national health data law.

**How it works:**
1. Produce a feature inventory listing every Salesforce cloud and add-on in scope (Health Cloud, CRM Analytics, MuleSoft, Marketing Cloud, Einstein features).
2. Cross-reference each feature against the current Salesforce HIPAA BAA and addenda list from the Salesforce Trust site.
3. Mark each feature as: (a) covered by standard BAA, (b) requires addendum — addendum obtained, (c) requires addendum — not yet obtained, or (d) excluded from BAA — PHI must not flow here.
4. For any feature in category (c) or (d), either execute the addendum before go-live or implement a technical control that prevents PHI from reaching that feature.
5. Document the matrix as an Architecture Decision Record and obtain sign-off from the customer's HIPAA Privacy Officer or DPO.

**Why not the alternative:** Relying solely on the standard BAA without checking addenda is the most common compliance gap. Features like Health Cloud Intelligence are actively marketed and sold alongside Health Cloud but are not automatically covered.

### Pattern: Transient Processing Exception Documentation

**When to use:** When the customer's DPO or Privacy Officer asks whether Hyperforce regional selection guarantees complete data residency, or when preparing a DPIA or risk register entry.

**How it works:**
1. Identify every feature in the org that has a transient processing exception (Einstein, Flow with external callouts, CRM Analytics pipelines, Marketing Cloud integration).
2. For each feature, document: the nature of transient processing, the Salesforce documentation reference, the data sensitivity involved, and the residual risk.
3. Implement compensating controls where feasible: field-level encryption or tokenization for highest-sensitivity fields before they reach at-risk features; consider disabling Einstein features for PHI-heavy record types if the BAA addendum is not in place.
4. Present the exception log to the customer's compliance team for formal acceptance.
5. Record formal acceptance in the project's compliance register.

**Why not the alternative:** Omitting this documentation leaves the customer exposed during audits. Regulators have begun explicitly asking about cloud provider transient processing in HIPAA and GDPR audit interviews.

---

## Decision Guidance

| Jurisdiction / Regulation | Hyperforce Region Required | Standard BAA Sufficient | Additional Requirements |
|---|---|---|---|
| US HIPAA | Not mandated by HIPAA itself, but often required by covered entity policy | Standard BAA required; addenda needed for HCI, MuleSoft, Marketing Cloud | Transient processing gap must be documented in risk register |
| EU GDPR (health data) | EU Hyperforce region strongly recommended; required if SCCs are used for lawful transfer basis | Salesforce Data Processing Addendum (DPA) required; HIPAA BAA separate if US entity also applies | DPIA mandatory; explicit consent or Article 9(2) basis required |
| Australia My Health Records Act 2012 | AU Hyperforce region required for primary storage of My Health Record data | Australian-specific terms under Hyperforce Infrastructure Agreement required | Cross-border restriction applies; verify Salesforce's approved data handling schedule |
| UK GDPR (post-Brexit) | UK Hyperforce region or adequacy decision required | UK IDTA or standard contractual clauses via Salesforce DPA required | Equivalent to EU GDPR Article 9 for health data |
| General PHI outside above | Regional selection based on covered entity policy | Standard BAA plus any required addenda | Document transient processing exceptions |

---

## Recommended Workflow

Step-by-step instructions for an architect or AI agent working on a Health Cloud data residency engagement:

1. **Inventory features and regulatory obligations.** List every Salesforce product in scope (Health Cloud, CRM Analytics / Health Cloud Intelligence, MuleSoft, Marketing Cloud, Einstein features). Identify every applicable regulatory framework (HIPAA, GDPR, My Health Records Act). Record results in the assessment template.

2. **Confirm Hyperforce region and infrastructure agreements.** Verify that the org is provisioned on Hyperforce in the correct region for the customer's primary regulatory jurisdiction. Confirm that both the HIPAA BAA (if applicable) AND the Hyperforce Infrastructure Agreement are executed. Do not assume one implies the other.

3. **Build the BAA coverage matrix.** For each feature in scope, determine whether it is covered by the standard HIPAA BAA, requires a separate addendum, or is excluded. Flag any PHI data flows that reach uncovered features as critical gaps requiring remediation before go-live.

4. **Document transient processing exceptions.** For every feature with a known transient processing gap (Einstein inference, CRM Analytics pipelines, Flow with external callouts), produce a written exception document describing the gap, Salesforce's documentation reference, the data sensitivity involved, and the compensating controls in place. Obtain customer compliance team sign-off.

5. **Apply compensating controls.** For features that cannot be excluded but have BAA or residency gaps, implement field-level security tightening, Salesforce Shield Platform Encryption for sensitive fields, or tokenization before data reaches at-risk features. Configure Data Mask explicitly for all sensitive fields in sandbox environments — do not assume Data Mask de-identifies PHI automatically.

6. **Satisfy jurisdiction-specific requirements.** For EU orgs: ensure DPIA is completed, explicit consent or Article 9(2) basis is documented, and a DPO has signed off. For AU orgs: verify Salesforce's data handling schedule under the My Health Records Act. For UK orgs: ensure UK IDTA is in place via the Salesforce DPA.

7. **Produce the Architecture Decision Record and compliance register entry.** Document the final region selection rationale, BAA coverage matrix, transient processing exception log, and outstanding risks. Hand off to the customer's HIPAA Privacy Officer, DPO, or equivalent for formal sign-off.

---

## Review Checklist

Run through these before marking data residency architecture complete:

- [ ] Hyperforce region confirmed and matches customer's primary regulatory jurisdiction
- [ ] Both HIPAA BAA AND Hyperforce Infrastructure Agreement are executed (not just one)
- [ ] BAA coverage matrix completed — every in-scope feature is assigned a coverage status
- [ ] Separate BAA addenda obtained for Health Cloud Intelligence, MuleSoft, and/or Marketing Cloud if those features carry PHI
- [ ] Transient processing exceptions documented for Einstein, Flow, and analytics features with customer compliance sign-off
- [ ] DPIA completed and DPO sign-off obtained for EU Health Cloud orgs processing health data
- [ ] Australia My Health Records Act cross-border restriction addressed if AU-regulated data is in scope
- [ ] Data Mask configured explicitly for all PHI fields in sandbox — not relying on default de-identification
- [ ] Salesforce Shield Platform Encryption applied to highest-sensitivity fields (diagnosis codes, SSN, MRN)
- [ ] Architecture Decision Record finalized and stored in customer compliance register

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Hyperforce region selection is permanent at provisioning.** Once a Health Cloud org is provisioned in a Hyperforce region, the primary data storage region cannot be changed without a full re-provisioning (migration to a new org). Practitioners sometimes assume region can be changed via a setting — it cannot. Validate the correct region during the pre-provisioning architecture review, not after go-live.

2. **Data Mask does not automatically de-identify PHI.** Salesforce Data Mask is a sandbox tool that applies masking rules, but it only masks fields that are explicitly configured in the Data Mask profile. The default configuration does not know which fields contain PHI. Teams that rely on Data Mask assuming it will "handle sensitive data" often discover that diagnosis codes, clinical notes, and SSN fields are not masked unless explicitly added to the mask definition.

3. **Health Cloud Intelligence BAA gap is a silent risk.** Health Cloud Intelligence (CRM Analytics for Health Cloud) is provisioned automatically with many Health Cloud editions and appears in the org as a native tab. Most practitioners assume it is covered by the standard HIPAA BAA because it appears inside the Health Cloud UI. It requires a separate BAA addendum, and PHI should not flow into HCI datasets until that addendum is executed.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| BAA Coverage Matrix | Table mapping each in-scope feature to its BAA status (covered / addendum required / excluded) |
| Transient Processing Exception Log | Document listing each feature with cross-region transient processing, Salesforce doc reference, data sensitivity, and compensating controls |
| Architecture Decision Record (ADR) | Formal record of Hyperforce region selection rationale, regulatory basis, and outstanding risks |
| DPIA Entry | GDPR Article 35 Data Protection Impact Assessment record for EU orgs processing health data at scale |
| Data Residency Assessment | Completed version of the assessment template for customer compliance sign-off |

---

## Related Skills

- hipaa-compliance-architecture — Use alongside this skill for detailed HIPAA technical safeguard implementation beyond data residency
- compliant-data-sharing-setup — Use when configuring Salesforce Shield and field-level encryption for PHI
- health-cloud-data-model — Use to identify which Health Cloud objects and fields carry PHI and require residency controls
- fsc-data-model — Reference for financial services parallel when a combined FSC + Health Cloud deployment is in scope
