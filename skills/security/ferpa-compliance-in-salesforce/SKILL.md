---
name: ferpa-compliance-in-salesforce
description: "Use this skill when implementing FERPA (Family Educational Rights and Privacy Act) compliance controls in Salesforce Education Cloud or Education Data Architecture (EDA): LearnerProfile FERPA boolean fields, directory information opt-out via FLS and Individual data privacy flags, ContactPointTypeConsent for parental and third-party disclosure, 45-day student records response window tracking, and consent workflow automation. Trigger keywords: FERPA, student records privacy, LearnerProfile, parental disclosure, directory information opt-out, education data privacy, student consent, education cloud compliance. NOT for GDPR/CCPA general data privacy (see gdpr-data-privacy skill), platform encryption at rest (see platform-encryption skill), or HIPAA health-data compliance."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "how do I configure FERPA consent tracking on LearnerProfile in Education Cloud"
  - "student requested directory information opt-out — where do I store that in Salesforce"
  - "how to track parental FERPA disclosure consent using Individual and ContactPointTypeConsent"
  - "need to enforce the 45-day FERPA response window for student records requests"
  - "HasFerpaParentalDisclosure and HasFerpaThrdPtyDisclosure fields on LearnerProfile — what do they control"
  - "setting up FERPA-compliant field-level security to restrict access to education records"
  - "how do I configure FERPA consent tracking and directory opt-out in Education Cloud"
tags:
  - ferpa
  - education-cloud
  - student-privacy
  - learner-profile
  - consent-management
  - directory-information
  - education-data-architecture
inputs:
  - "Whether the org uses Education Cloud or Education Data Architecture (EDA)"
  - "Which LearnerProfile and ContactProfile objects are deployed"
  - "Current field-level security configuration on education record fields"
  - "Whether the Individual object and consent model are already in use"
  - "Volume of students and frequency of records requests"
outputs:
  - "LearnerProfile FERPA field configuration (HasFerpaParentalDisclosure, HasFerpaThrdPtyDisclosure, HasParentalFerpa, HasThirdPartyFerpa)"
  - "Directory information opt-out design using FLS on LearnerProfile/ContactProfile and Individual privacy flags"
  - "ContactPointTypeConsent records for parental and third-party disclosure tracking"
  - "45-day response window tracking workflow (Case or custom object)"
  - "Review checklist for FERPA compliance posture"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# FERPA Compliance in Salesforce

Use this skill when a practitioner needs to implement FERPA (Family Educational Rights and Privacy Act) compliance controls inside Salesforce Education Cloud or Education Data Architecture (EDA). This skill covers the LearnerProfile FERPA boolean fields, directory information opt-out mechanisms, parental and third-party disclosure consent tracking through the Individual and ContactPointTypeConsent infrastructure, and the 45-day response window for student records requests.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm whether the org runs Education Cloud (with LearnerProfile, ContactProfile, and related objects) or a custom EDA implementation. The four FERPA boolean fields exist only on LearnerProfile; custom EDA orgs may need custom fields to replicate this behavior.
- Check whether the Individual sObject is already linked to Contact records. FERPA consent tracking reuses the same Individual + ContactPointTypeConsent infrastructure used by GDPR/CCPA. If the org already has an Individual linkage pattern, extend it rather than creating a parallel design.
- Identify which fields on LearnerProfile, ContactProfile, and related objects constitute "education records" under FERPA and which qualify as "directory information." This distinction determines whether data can be disclosed without consent or requires explicit parental/student authorization.

---

## Core Concepts

### LearnerProfile FERPA Boolean Fields

The LearnerProfile object in Education Cloud includes four FERPA-specific boolean fields that track consent status at the student level:

- `HasFerpaParentalDisclosure` — indicates whether the institution has obtained parental consent to disclose education records to the parent or guardian. Relevant when the student is under 18 or is a dependent for tax purposes.
- `HasFerpaThrdPtyDisclosure` — indicates whether the institution has obtained consent to disclose education records to specified third parties (employers, other institutions, scholarship committees).
- `HasParentalFerpa` — indicates whether parental FERPA rights are active. When a student turns 18 or enrolls in a postsecondary institution, FERPA rights transfer from parent to student. This field tracks whether the parent still holds rights.
- `HasThirdPartyFerpa` — indicates whether a third party has been granted FERPA access rights by the eligible student or parent.

These are status flags only. Setting them to `true` does not automatically restrict or permit data access. Your org must enforce the business logic through field-level security, sharing rules, and consent workflows that respond to these flags.

### Directory Information Opt-Out

Under FERPA, institutions may designate certain data as "directory information" (name, address, phone, enrollment status, dates of attendance, degree, honors) and disclose it without consent — unless the student or parent has opted out. In Salesforce, directory information opt-out is implemented through a combination of:

1. **Field-Level Security (FLS)** on LearnerProfile and ContactProfile fields that contain directory information. When a student opts out, restrict field visibility for profiles that represent external-facing systems or portal users.
2. **Individual data privacy flags** — the `HasOptedOutOfSolicit` and `SendIndividualData` fields on the Individual object signal that data should not be shared externally. These integrate with Marketing Cloud and Experience Cloud consent checks.
3. **Custom opt-out flag** — many implementations add a custom `HasOptedOutOfDirectoryInfo__c` checkbox on LearnerProfile or the associated Contact, then use a trigger or flow to propagate FLS restrictions or suppress the record from directory-info exports.

### The Individual + ContactPointTypeConsent Infrastructure

FERPA consent tracking reuses Salesforce's native consent model. The Individual sObject serves as the privacy container for each student or parent. ContactPointTypeConsent records capture channel-level consent decisions with time-bounded validity windows (`EffectiveFrom`, `EffectiveTo`). For FERPA, you create consent records that represent:

- Parental disclosure consent (linked to the student's Individual, with a DataUsePurpose describing "FERPA Parental Disclosure").
- Third-party disclosure consent (separate ContactPointTypeConsent per third party or third-party category).

This model provides an audit trail of who consented, when, and for what purpose — critical for FERPA compliance documentation during Department of Education audits.

### 45-Day Response Window

FERPA requires that institutions respond to a parent's or eligible student's request to inspect and review education records within 45 days. Tracking this window is operational, not technical, but Salesforce can automate it via Case records with an SLA (Entitlement Process) or a custom object with workflow rules that escalate at 30 and 40 days. Failure to respond within 45 days is a FERPA violation that can trigger a complaint to the Family Policy Compliance Office (FPCO).

---

## Common Patterns

### Pattern 1: LearnerProfile FERPA Field Configuration with Consent Automation

**When to use:** Initial setup of FERPA consent tracking in an Education Cloud org.

**How it works:**
1. Ensure LearnerProfile is deployed and linked to Contact via the standard relationship.
2. For each student, set the four FERPA boolean fields based on current consent status.
3. Create an Individual record for each student Contact (if not already present) and set `IndividualId` on Contact.
4. Create ContactPointTypeConsent records for parental and third-party disclosure, linked to the Individual via `PartyId`.
5. Build a Flow or trigger that updates the LearnerProfile FERPA booleans when ContactPointTypeConsent records are created or modified.

**Why not the alternative:** Manually managing FERPA booleans without consent records produces no audit trail. Department of Education audits require evidence of when consent was granted, by whom, and for what period. ContactPointTypeConsent provides this natively.

### Pattern 2: Directory Information Opt-Out via FLS and Automation

**When to use:** A student or parent requests that directory information not be disclosed.

**How it works:**
1. Record the opt-out on the student's LearnerProfile or Contact (custom checkbox `HasOptedOutOfDirectoryInfo__c`).
2. Propagate the opt-out to the Individual record: set `HasOptedOutOfSolicit = true` and `SendIndividualData = false`.
3. Use a Platform Event or trigger to update field-level security dynamically, or — more practically — use a permission-set-based approach where opted-out students are excluded from reports, list views, and Experience Cloud data feeds.
4. For external-facing integrations (student directories, third-party portals), query the opt-out flag before including the student in outbound data.

**Why not the alternative:** Relying solely on FLS profile changes does not scale when individual students opt out. A data-driven approach using flags + query filters handles per-student opt-out without per-student profile assignments.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Education Cloud org with LearnerProfile | Use the four native FERPA boolean fields + ContactPointTypeConsent | Native fields integrate with Education Cloud reports and dashboards |
| Custom EDA without LearnerProfile | Create custom FERPA boolean fields on Contact or a custom object | Replicate the LearnerProfile pattern; link to Individual for consent tracking |
| Student turns 18 or enters postsecondary | Update HasParentalFerpa to false, transfer rights to student | FERPA rights transfer automatically at age of majority or postsecondary enrollment |
| Directory information opt-out request | Set opt-out flag + suppress from all outbound data and portals | Must be honored for all directory information disclosures, not just marketing |
| High volume of records requests (>50/month) | Case with Entitlement Process for 45-day SLA | Automated escalation prevents missed deadlines |
| Low volume of records requests | Custom object or Case without Entitlements | Proportionate; manual tracking with calendar reminders |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Audit the data model**: Identify all objects and fields that store education records (LearnerProfile, ContactProfile, Contact, custom objects). Classify each field as either "education record" (requires consent for disclosure) or "directory information" (disclosable unless opted out).

2. **Configure Individual linkage**: Ensure every student Contact has an `IndividualId` pointing to an Individual record. Build a Flow or trigger to create Individual records automatically for new student Contacts.

3. **Set LearnerProfile FERPA fields**: For each student, populate `HasFerpaParentalDisclosure`, `HasFerpaThrdPtyDisclosure`, `HasParentalFerpa`, and `HasThirdPartyFerpa` based on current consent status. Build automation to update these when consent records change.

4. **Build the consent model**: Create ContactPointTypeConsent records for parental disclosure and third-party disclosure, linked to the student's Individual via `PartyId`. Set `EffectiveFrom`, `EffectiveTo`, and link to a DataUsePurpose record that names the FERPA basis.

5. **Implement directory information opt-out**: Add a custom opt-out flag if needed. Build automation to propagate opt-out to Individual privacy flags and suppress opted-out students from directory exports, Experience Cloud pages, and outbound integrations.

6. **Implement 45-day response tracking**: Create a Case record type or custom object for FERPA records requests. Configure an Entitlement Process or escalation rule that alerts at 30 days and escalates at 40 days. Log fulfillment with date and method of response.

7. **Test and validate**: In a sandbox, create student records with various FERPA consent combinations. Verify that disclosure restrictions are enforced, opt-outs suppress directory information, and the 45-day SLA escalation fires correctly.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Every student Contact has `IndividualId` populated and linked to an Individual record
- [ ] LearnerProfile FERPA boolean fields are populated and updated by automation when consent changes
- [ ] ContactPointTypeConsent records exist for parental and third-party disclosure with `EffectiveFrom` and `OptInStatus`
- [ ] Directory information opt-out flag is implemented and propagated to Individual privacy flags
- [ ] Opted-out students are excluded from directory exports, Experience Cloud pages, and outbound integrations
- [ ] 45-day response window is tracked via Case SLA or equivalent, with escalation at 30 and 40 days
- [ ] FERPA rights transfer logic handles students turning 18 or entering postsecondary education
- [ ] Field-level security restricts education record fields from profiles that should not access them

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **LearnerProfile FERPA booleans are flags, not enforcement** — Setting `HasFerpaParentalDisclosure = true` does not automatically permit or block data access. Your org must build the automation that reads these flags and enforces disclosure rules through FLS, sharing, or query filters.
2. **Individual.ShouldForget is GDPR, not FERPA** — Do not use the `ShouldForget` field for FERPA erasure requests. FERPA requires amendment or correction of records, not deletion. Using `ShouldForget` conflates two different regulatory obligations and may trigger GDPR erasure logic that destroys records FERPA requires you to retain.
3. **FERPA rights transfer is not automatic** — When a student turns 18 or enters a postsecondary institution, FERPA rights transfer from parent to student. Salesforce does not detect this age change or enrollment event. You must build a scheduled flow or batch job to update `HasParentalFerpa` based on the student's birthdate or enrollment status.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| LearnerProfile FERPA field configuration | Mapping of all four FERPA boolean fields with their current values and update automation |
| Directory information opt-out design | Custom flag, propagation logic, and suppression rules for opted-out students |
| Consent object model | ContactPointTypeConsent records for parental and third-party disclosure linked to DataUsePurpose |
| 45-day response tracking workflow | Case record type or custom object with SLA configuration and escalation rules |
| FERPA rights transfer automation | Scheduled flow or batch job that updates HasParentalFerpa when students age out or enroll in postsecondary |

---

## Official Sources Used

- Salesforce Security Guide — https://help.salesforce.com/s/articleView?id=sf.security_overview.htm&type=5
- Education Cloud Documentation — https://help.salesforce.com/s/articleView?id=sf.education_cloud.htm&type=5
- Salesforce Object Reference (LearnerProfile, Individual, ContactPointTypeConsent) — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- U.S. Department of Education FERPA General Guidance — https://studentprivacy.ed.gov/ferpa

---

## Related Skills

- `gdpr-data-privacy` — use alongside this skill when the institution also processes EU/EEA student data; the Individual and consent model is shared but GDPR erasure obligations differ from FERPA amendment rights
- `data-classification-labels` — use to tag fields containing education records vs. directory information, a prerequisite for building accurate FLS rules
- `permission-set-groups-and-muting` — use to manage field-level security assignments for staff roles that should or should not access education records
