# Examples — Health Cloud Data Residency

## Example 1: EU-Based Healthcare Provider Discovers Health Cloud Intelligence BAA Gap

**Context:** A European private hospital network is migrating patient management to Health Cloud, provisioned in Salesforce's EU Hyperforce region. The project team has the standard HIPAA BAA in place (their US subsidiary is a covered entity), a Salesforce Data Processing Addendum for GDPR, and has activated Health Cloud Intelligence for population health dashboards. The customer's DPO initiates a pre-go-live compliance review.

**Problem:** The DPO's review reveals that Health Cloud Intelligence (CRM Analytics) is processing patient encounter data — including ICD-10 diagnosis codes — to build population health dashboards. Health Cloud Intelligence runs on a separate analytics compute layer and is not covered by the standard HIPAA BAA. The GDPR DPA references CRM Analytics as an out-of-scope sub-processor unless a separate addendum is executed. No addendum is in place. PHI has been flowing into HCI datasets for three months during UAT.

**Solution:**

The remediation path has two tracks:

**Track 1 — Legal/contractual:** Engage the Salesforce account team immediately to obtain the Health Cloud Intelligence BAA addendum and update the GDPR DPA to include CRM Analytics as a covered sub-processor. This is a negotiated addendum and can take several weeks.

**Track 2 — Technical interim control:** Until the addendum is in place, restrict HCI dataset recipes to exclude direct PHI fields. Use a de-identified dataset approach:

```
CRM Analytics Dataset Recipe (de-identified interim approach):
- Source object: HealthCloudGA__EhrPatientMedication__c
- Excluded fields: SSN__c, DateOfBirth__c, DiagnosisCode__c, PatientMRN__c
- Included fields: AgeRange__c (bucketed), TherapeuticClass__c, Region__c
- Transformation: Replace individual patient identifiers with aggregate cohort keys
- Result: Population-level analytics without direct PHI exposure in HCI
```

Document the interim de-identification approach in the compliance register with a target date for addendum execution.

**Why it works:** The interim approach satisfies HIPAA's minimum necessary standard and reduces exposure while the legal track resolves. The BAA gap is identified before go-live rather than in an external audit. Documenting the remediation timeline demonstrates good-faith compliance effort.

---

## Example 2: Australian Health Cloud Org — My Health Records Act Cross-Border Restriction

**Context:** An Australian digital health startup is building a patient engagement portal on Health Cloud, integrated with the Australian government My Health Records system via a registered healthcare provider portal. They have selected the Salesforce Australia (AP3) Hyperforce region and assume this satisfies all data residency requirements under the My Health Records Act 2012 and the Australian Privacy Act.

**Problem:** The My Health Records Act 2012 imposes strict restrictions on cross-border disclosure of health records. "Disclosure" under the Act includes making data accessible to overseas entities, not just transferring a copy. Hyperforce regional selection ensures primary data storage in Australia, but the Hyperforce Infrastructure Agreement documents that certain platform services — including some identity, replication, and support access functions — may involve transient cross-border data movement. Additionally, the startup's architects want to enable Einstein for Health to generate care gap summaries, which routes inference through Einstein's global infrastructure rather than the AU region.

**Solution:**

The architecture requires three actions:

**Action 1 — Infrastructure Agreement review:** Obtain Salesforce's current Hyperforce Infrastructure Agreement for the AU region and identify every documented cross-border processing exception. Map each exception against the My Health Records Act's definition of "disclosure" with input from an Australian health law specialist.

**Action 2 — Einstein for Health scoping decision:**
```
Compliance gate for Einstein features in AU health org:

IF feature routes inference outside AU region:
  AND data in context window includes My Health Record data:
    → Feature is not permitted until Salesforce provides AU-region inference
      OR data is de-identified before reaching Einstein context window
    → Document as an open risk item in the compliance register

IF data in context window is limited to non-My Health Record patient data
(e.g., appointment scheduling, non-clinical care coordination):
  → Feature may proceed with documented DPO review and acceptance
```

**Action 3 — Salesforce account team engagement:** Request Salesforce's formal position on My Health Records Act compliance for the AU Hyperforce region, including any available letters of assurance or compliance certifications specific to the Australian healthcare regulatory environment.

**Why it works:** My Health Records Act compliance cannot be assumed from Hyperforce regional selection alone. The Act's cross-border restriction is absolute for registered system operators. Proactive engagement with Salesforce's trust and compliance team produces documented evidence of due diligence, which is required if the Office of the Australian Information Commissioner (OAIC) conducts a review.

---

## Example 3: Anti-Pattern — Assuming Data Mask Provides HIPAA-Compliant De-Identification for Sandboxes

**What practitioners do:** A Health Cloud implementation team creates a full sandbox from the production org (which contains real patient PHI) and enables Data Mask, assuming it will automatically de-identify all sensitive fields. They then share sandbox credentials with offshore developers and QA testers who are not covered under the HIPAA BAA.

**What goes wrong:** Data Mask applies masking rules only to fields explicitly configured in the Data Mask profile. Health Cloud uses numerous custom and managed package fields for clinical data — `HealthCloudGA__MedicalRecordNumber__c`, custom fields added by the implementation team for diagnosis codes, clinical notes stored in `ContentDocument` body, and task descriptions that include patient information. None of these are masked by default. The offshore testers have access to real PHI, constituting a HIPAA breach.

**Correct approach:**

Before provisioning any sandbox from a Health Cloud production org:

1. Audit every object and field that may contain PHI — include managed package fields (prefix `HealthCloudGA__`), custom fields, `ContentNote` bodies, `Task.Description`, `EmailMessage.TextBody`, and `FeedItem.Body`.
2. Build an explicit Data Mask profile that maps each PHI field to an appropriate masking type (random name, random date, nullify, pattern replacement).
3. Verify the mask profile by reviewing a sample of masked records post-sandbox-creation before granting developer or tester access.
4. Ensure offshore or non-BAA-covered personnel only access sandboxes that have been verified as fully de-identified.
5. Document the de-identification process and retain evidence for HIPAA compliance purposes.

Never treat Data Mask as a "set it and forget it" tool — it requires explicit, field-by-field configuration that must be updated whenever new fields are added to the org.
