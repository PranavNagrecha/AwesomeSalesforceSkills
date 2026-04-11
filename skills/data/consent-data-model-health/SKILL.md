---
name: consent-data-model-health
description: "Use this skill when designing, implementing, querying, or troubleshooting the Health Cloud consent data model — specifically the five-object HIPAA authorization hierarchy (DataUsePurpose → AuthorizationForm → AuthorizationFormText → AuthorizationFormDataUse → AuthorizationFormConsent). Trigger keywords: authorization form consent, ConsentGiverId, AuthorizationFormConsent SOQL, CareProgramEnrollee consent gate, PHI consent trail, consent hierarchy setup. NOT for marketing consent or standard email opt-out tracking. NOT for ContactPointConsent or ContactPointTypeConsent objects used in Marketing Cloud or standard Salesforce Privacy Center."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "How do I set up patient consent for Health Cloud before enrolling in a care program?"
  - "AuthorizationFormConsent SOQL query to verify a patient has signed a consent form before clinical record access"
  - "CareProgramEnrollee status won't move to Active — is there a consent prerequisite?"
tags:
  - health-cloud
  - consent
  - hipaa
  - phi
  - data-model
  - authorization
inputs:
  - "Target org with Health Cloud enabled"
  - "Patient Individual ID (not Contact ID) for ConsentGiverId population"
  - "List of data use purposes mapped to clinical workflows (e.g., treatment, research)"
  - "Intake flow or process that captures patient authorization signature"
outputs:
  - "Configured five-object consent hierarchy with at least one AuthorizationFormConsent record per enrolled patient"
  - "SOQL query pattern to verify consent status before PHI access"
  - "Checklist of sharing rule gaps that must be addressed separately"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-11
---

# Consent Data Model Health

This skill activates when building or auditing the Health Cloud HIPAA authorization consent hierarchy. It provides authoritative guidance on the five-object consent data model, the correct field values on AuthorizationFormConsent, the prerequisite relationship to CareProgramEnrollee activation, and the critical boundary between consent recordkeeping and PHI sharing rule enforcement.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm Health Cloud is provisioned and the Health Cloud permission set is assigned; the AuthorizationForm* objects are not present in base Salesforce CRM.
- Identify whether the org uses Person Accounts or Individual records — ConsentGiverId must point to an Individual ID, not a Contact ID. Mixing these is the most common implementation error.
- Clarify which DataUsePurpose records already exist; creating duplicates silently fragments the hierarchy and breaks downstream consent queries.

---

## Core Concepts

### The Five-Object Consent Hierarchy

Health Cloud models HIPAA authorization as a strict parent-child chain:

1. **DataUsePurpose** — Defines why data is being used (e.g., Treatment, Research). The `PurposeId` field drives classification. `CanDataSubjectOptOut` controls whether the patient may revoke.
2. **AuthorizationForm** — The master consent form record. `IsSignatureRequired` = true means the status on downstream records must be `Signed`, not merely `Seen`.
3. **AuthorizationFormText** — A versioned text body of the form. One AuthorizationForm can have multiple AuthorizationFormText records representing form versions. The patient signs a specific version.
4. **AuthorizationFormDataUse** — Junction object linking AuthorizationFormText to one or more DataUsePurpose records. This declares what the signed form authorizes.
5. **AuthorizationFormConsent** — The per-patient record. This is the PHI authorization trail. Key fields:
   - `ConsentGiverId` — Lookup to **Individual** (not Contact, not Account). Required.
   - `AuthorizationFormTextId` — Links to the specific form version the patient signed.
   - `ConsentCapturedSource` — How consent was captured (e.g., `Email`, `Web`, `Verbal`, `Paper`). Required for audit completeness; missing values indicate incomplete intake flows.
   - `Status` — Enumeration: `Seen` (patient viewed but did not sign) or `Signed` (patient executed the authorization). Only `Signed` satisfies a signature-required authorization.
   - `ConsentCapturedDateTime` — Timestamp of capture. Required for HIPAA audit trails.

### CareProgramEnrollee Activation Gate

A CareProgramEnrollee record cannot be set to `Active` enrollment status unless the linked patient (Individual) has at least one AuthorizationFormConsent record in `Signed` status for the relevant DataUsePurpose associated with the care program. This is not enforced by a platform validation rule by default — implementors must build the gate as a Flow or Apex before-save trigger that queries AuthorizationFormConsent and blocks the status transition when no signed consent exists. If this gate is omitted, patients can be enrolled and receive PHI-backed care coordination without a documented HIPAA authorization on file.

### Consent Recordkeeping vs. PHI Record Access

AuthorizationFormConsent records the fact that a patient authorized a data use. It does **not** modify the Salesforce sharing model. A patient record can have a fully signed consent chain and still be inaccessible to a care team member if sharing rules are misconfigured — and vice versa: a patient record can be visible to a user with no consent record on file if org-wide defaults are set to Public Read. Sharing rules (criteria-based or role-based) must be designed and deployed separately to enforce PHI access controls. The consent hierarchy and the sharing model are orthogonal subsystems.

### Distinction from Marketing Consent

Health Cloud uses a fundamentally different object model from Marketing Cloud or Privacy Center consent. The marketing consent model uses `Individual → ContactPointTypeConsent → ContactPointConsent`. These objects track communication preferences (email opt-out, SMS opt-in) and are not HIPAA authorization records. Do not mix these hierarchies. An `AuthorizationFormConsent` record does not appear in Privacy Center dashboards, and `ContactPointConsent` records do not satisfy the CareProgramEnrollee consent gate.

---

## Common Patterns

### Pattern: Full Hierarchy Setup for Patient Portal Intake

**When to use:** A new Health Cloud implementation needs to capture HIPAA authorization during patient intake, before the patient is enrolled in a care program.

**How it works:**
1. Create one `DataUsePurpose` record per clinical use category (Treatment, Payment, Operations).
2. Create one `AuthorizationForm` record per consent form type (e.g., "General Patient Consent"). Set `IsSignatureRequired = true`.
3. Create an `AuthorizationFormText` record linked to the AuthorizationForm, containing the versioned legal text.
4. Create `AuthorizationFormDataUse` junction records linking the AuthorizationFormText to each DataUsePurpose it covers.
5. During patient portal intake, after the patient views and signs the form, create an `AuthorizationFormConsent` record with:
   - `ConsentGiverId` = the patient's Individual ID
   - `AuthorizationFormTextId` = the specific form version presented
   - `Status` = `Signed`
   - `ConsentCapturedSource` = `Web`
   - `ConsentCapturedDateTime` = system timestamp at submission

**Why not the alternative:** Creating only one record at the top of the hierarchy (e.g., just DataUsePurpose) and skipping the intermediate junction objects will result in AuthorizationFormConsent records that exist in isolation with no traceable link back to a specific form version or data use purpose — breaking audit trail requirements.

### Pattern: Pre-Access Consent Verification Query

**When to use:** A Flow, Apex class, or LWC needs to verify that a patient has valid signed consent before displaying clinical records or triggering a care protocol.

**How it works:**

```soql
SELECT Id, Status, ConsentCapturedSource, ConsentCapturedDateTime,
       AuthorizationFormText.AuthorizationForm.Name
FROM AuthorizationFormConsent
WHERE ConsentGiverId = :individualId
  AND Status = 'Signed'
  AND AuthorizationFormText.AuthorizationFormDataUses.DataUsePurpose.Name = 'Treatment'
ORDER BY ConsentCapturedDateTime DESC
LIMIT 1
```

If the query returns zero rows, block the action and route the user to the consent intake flow.

**Why not the alternative:** Checking only the `Status` field without filtering on DataUsePurpose may return a consent record for a Research purpose when Treatment authorization is required, producing a false positive clearance.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Patient must sign before enrollment | Build a before-save Flow on CareProgramEnrollee that queries AuthorizationFormConsent | Platform does not enforce this gate natively; the check must be implemented explicitly |
| Consent form is updated (new legal version) | Create a new AuthorizationFormText record linked to the same AuthorizationForm | Preserves historical consent records tied to old text versions; do not update the text in place |
| Patient revokes consent | Set `Status` to `Seen` on the AuthorizationFormConsent record or create a new record with a revocation timestamp | Allows the audit trail to reflect the revocation without deleting the original authorization record |
| Need to restrict PHI visibility after consent revocation | Update sharing rules and/or permission set assignments | AuthorizationFormConsent status change alone does not alter record visibility; the sharing model must be updated separately |
| Marketing opt-out tracking needed | Use ContactPointConsent and ContactPointTypeConsent | AuthorizationFormConsent is not the correct object for communication preference management |

---

## Recommended Workflow

1. **Audit existing consent objects** — Query for existing DataUsePurpose, AuthorizationForm, and AuthorizationFormText records to avoid duplicates before creating new hierarchy nodes. Use `SELECT Id, Name FROM DataUsePurpose` to confirm what already exists.
2. **Build the hierarchy top-down** — Create DataUsePurpose first, then AuthorizationForm, then AuthorizationFormText, then AuthorizationFormDataUse junction records. Each child requires its parent to exist before it can be linked.
3. **Instrument the intake flow** — Add a screen component or e-signature step that presents the AuthorizationFormText body to the patient and, on confirmation, creates the AuthorizationFormConsent record with `ConsentGiverId` (Individual ID), `Status = Signed`, `ConsentCapturedSource`, and `ConsentCapturedDateTime`.
4. **Implement the CareProgramEnrollee gate** — Add a before-save Flow or Apex trigger on CareProgramEnrollee that queries AuthorizationFormConsent for the enrollee's Individual, filtered by `Status = 'Signed'` and the relevant DataUsePurpose. Block the status transition to Active if no record is found.
5. **Validate and audit** — Run the `scripts/check_consent_data_model_health.py` checker against your metadata export to confirm all consent records have `ConsentCapturedSource` populated and no AuthorizationFormConsent records reference a Contact ID in `ConsentGiverId`. Then review sharing rules to confirm PHI access controls are enforced independently of the consent hierarchy.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] All AuthorizationFormConsent records have `ConsentGiverId` pointing to an Individual (not a Contact or PersonAccount)
- [ ] All `Status = Signed` records have `ConsentCapturedSource` and `ConsentCapturedDateTime` populated
- [ ] CareProgramEnrollee activation is gated by a Flow or Apex check against AuthorizationFormConsent
- [ ] AuthorizationFormDataUse junction records exist linking each form version to the correct DataUsePurpose
- [ ] Sharing rules for PHI objects have been reviewed and configured independently of the consent hierarchy

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **AuthorizationFormConsent does not modify sharing** — Creating or signing a consent record has zero effect on who can see the patient's clinical records. Record-level PHI access is controlled entirely by the sharing model (OWD, sharing rules, manual shares). Teams that assume consent = access will expose PHI gaps in both directions.
2. **ConsentGiverId must reference Individual, not Contact** — The `ConsentGiverId` field is a polymorphic lookup that accepts Contact, Individual, and Account. Health Cloud consent requires Individual. Populating it with a Contact ID will pass save validation but will not satisfy the CareProgramEnrollee consent gate query, which filters by Individual ID. The error is silent and extremely difficult to diagnose after the fact.
3. **Marketing and Health consent models do not overlap** — `ContactPointConsent` and `AuthorizationFormConsent` are architecturally separate. Workflows that query `ContactPointConsent` to check for HIPAA authorization will always return false negatives, and vice versa. Do not mix these object families in consent verification logic.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Five-object consent hierarchy | DataUsePurpose, AuthorizationForm, AuthorizationFormText, AuthorizationFormDataUse, and AuthorizationFormConsent records correctly linked |
| Intake flow modification | Screen flow or action that creates AuthorizationFormConsent with all required fields on patient confirmation |
| Pre-access SOQL pattern | Query verifying signed consent for a specific DataUsePurpose before clinical record access |
| CareProgramEnrollee gate | Before-save Flow or Apex trigger that blocks enrollment without valid consent |

---

## Related Skills

- admin/health-cloud-consent-management — Admin-layer configuration of consent settings, permission sets, and the Consent Management feature in Health Cloud Setup
- data/health-cloud-data-model — Broader Health Cloud data model coverage including patient, clinical, and care plan objects
