# Examples — Referral Management Health Cloud

## Example 1: Setting Up Outbound Specialist Referral Workflow

**Context:** A health system is implementing Health Cloud for a primary care network. Clinicians need to refer patients to specialists and track the full referral lifecycle from submission through completion.

**Problem:** The team defaulted to creating a custom Referral__c object but discovered it has no FHIR R4 alignment, no native provider network search integration, and duplicates the standard ClinicalServiceRequest object that ships with Health Cloud.

**Solution:**
1. Enable the HealthCloudICM permission set for all clinical users.
2. Create two record types on ClinicalServiceRequest: Inbound and Outbound.
3. Configure the Status picklist with values: Draft, Submitted, In Review, Accepted, Declined, Completed, Cancelled.
4. Build a Record-Triggered Flow on ClinicalServiceRequest to: (a) notify the receiving provider via email when Status transitions to Submitted; (b) create a follow-up Task on the care coordinator when Status = Declined; (c) update the related care plan task when Status = Completed.
5. Set field-level security to make PatientId, ReferralType, and ReferredToId required on page layout.
6. Build a report on ClinicalServiceRequest grouped by Status and ReferralType for care coordinator dashboards.

**Why it works:** ClinicalServiceRequest is a platform-standard FHIR R4-aligned object. It participates in Health Cloud's clinical data model, supports FHIR API reads/writes, and will receive ongoing Salesforce investment. Custom Referral__c objects must be rebuilt every time the FHIR model evolves.

---

## Example 2: Fixing Blank Provider Search Results

**Context:** A Health Cloud implementation has provider records (Accounts with HealthcareProvider record type) set up correctly. The care coordinator uses the provider search component but every search returns zero results.

**Problem:** The Data Processing Engine (DPE) job that populates CareProviderSearchableField was never run, and the automated process user lacks the Data Pipelines Base User permission set license — causing the job to complete with zero records written and no visible error in the provider search UI.

**Solution:**
1. Navigate to Setup > Permission Set Licenses and confirm a Data Pipelines Base User license is available.
2. Assign the Data Pipelines Base User permission set to the integration user or process credential that runs DPE jobs.
3. Navigate to Setup > Data Processing Engine and locate the provider search DPE job.
4. Run the job manually and confirm it completes with records processed > 0.
5. Verify CareProviderSearchableField records exist using Developer Console: `SELECT Id, Name FROM CareProviderSearchableField LIMIT 10`.
6. Retest provider search — results should now appear for matching specialty and location.
7. Schedule the DPE job to run nightly to keep the index current as provider records change.

**Why it works:** CareProviderSearchableField is a denormalized search index, not a live view of provider records. It must be explicitly populated by the DPE job before provider search has any data to query. The license requirement is not surfaced as a visible error in the provider search UI — it only appears in DPE job execution logs.

---

## Anti-Pattern: Using FSC Referral Scoring Config for Health Cloud Referrals

**What practitioners do:** Copy configuration steps from FSC Referral Management documentation (referral types, Einstein Referral Scoring, advisor-linked referrals) into a Health Cloud implementation because both are labeled "Referral Management" in Salesforce documentation.

**What goes wrong:** FSC Referral Management uses a completely different data model (custom Lead/Opportunity fields, Einstein scoring, advisor-to-client referral workflow). Configuring FSC Referral features in a Health Cloud org either does nothing (features simply are not active without FSC license) or conflicts with ClinicalServiceRequest-based clinical referral workflows.

**Correct approach:** Health Cloud referral management is built on ClinicalServiceRequest (API v51.0+) with provider network integration via CareProviderSearchableField. Start from the Health Cloud Administration Guide — Configure Referral Management, not FSC documentation.
