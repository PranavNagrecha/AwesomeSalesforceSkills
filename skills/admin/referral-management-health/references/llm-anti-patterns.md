# LLM Anti-Patterns — Referral Management Health Cloud

Common mistakes AI coding assistants make when generating or advising on Health Cloud referral management.

## Anti-Pattern 1: Recommending FSC Einstein Referral Scoring for Health Cloud

**What the LLM generates:** Advice to enable Einstein Referral Scoring, configure ReferralRecordTypeMapping__mdt custom metadata, or set up advisor-linked referral workflows for a Health Cloud patient referral use case.

**Why it happens:** Both FSC and Health Cloud use the term "Referral Management" in Salesforce documentation. LLMs trained on mixed Salesforce content conflate the two products. FSC Referral Management has extensive online documentation and community content, causing it to dominate training data for "Salesforce referral management" queries.

**Correct pattern:**
Health Cloud referral management uses ClinicalServiceRequest (API v51.0+), not FSC Lead/Opportunity fields or Einstein Referral Scoring. Start with the Health Cloud Administration Guide — Configure Referral Management, not FSC documentation.

**Detection hint:** If the recommendation mentions `ReferralRecordTypeMapping__mdt`, `EinsteinReferralScoring`, or configuring referral fields on the Lead or Opportunity object for a Health Cloud org, it is applying FSC patterns to a Health Cloud use case.

---

## Anti-Pattern 2: Using the Public Sector Solutions Referral Object

**What the LLM generates:** Code or configuration referencing the `Referral` sObject from Public Sector Solutions (PSS) for Health Cloud patient referral management.

**Why it happens:** Salesforce has a `Referral` standard object used in Public Sector Solutions. LLMs confuse this with Health Cloud referral management because both are Salesforce Health/Government cloud products. The PSS `Referral` object is not part of Health Cloud's clinical data model.

**Correct pattern:**
Health Cloud clinical referrals use `ClinicalServiceRequest`. The PSS `Referral` object is a separate standard object for government/social services use cases. Check the object API name — for Health Cloud, it should be `ClinicalServiceRequest`, not `Referral`.

**Detection hint:** If code references `new Referral()` or queries `FROM Referral` in a Health Cloud context, this is the PSS object being misapplied.

---

## Anti-Pattern 3: Assuming ClinicalServiceRequest Requires No Permission Set

**What the LLM generates:** Instructions to configure ClinicalServiceRequest access via profile-level object permissions alone, without mentioning the HealthCloudICM permission set.

**Why it happens:** Standard Salesforce objects are normally accessible via profile-level object permissions. LLMs apply this default pattern to ClinicalServiceRequest without knowing the Health Cloud permission set requirement.

**Correct pattern:**
ClinicalServiceRequest access requires the HealthCloudICM permission set in addition to any profile-level object permissions. This applies to all users including integration users and automated process users. Profile-level access alone is insufficient.

**Detection hint:** If the recommended setup mentions only object-level CRUD in a profile and does not mention HealthCloudICM permission set assignment, the permission requirement is missing.

---

## Anti-Pattern 4: Treating CareProviderSearchableField as Auto-Populated

**What the LLM generates:** Instructions to query or use provider search without mentioning the requirement to run the Data Processing Engine job that populates CareProviderSearchableField.

**Why it happens:** LLMs assume denormalized index objects are populated automatically by the platform, analogous to how search indexes work in other systems. The DPE job requirement and the Data Pipelines Base User license prerequisite are runtime operational requirements not visible in the object schema.

**Correct pattern:**
CareProviderSearchableField must be explicitly populated by running a Data Processing Engine job. The process user running that job must have the Data Pipelines Base User permission set license. Without running the job, provider search returns zero results regardless of how many provider records exist.

**Detection hint:** If the answer assumes provider search will work immediately after provider records are created without mentioning the DPE job, the index population step is missing.

---

## Anti-Pattern 5: Conflating Health Cloud Referral with Standard Lead Referral Tracking

**What the LLM generates:** Recommendations to track referrals using the standard Lead object with a custom "Referred By" field and lead source tracking, rather than ClinicalServiceRequest.

**Why it happens:** Lead-based referral tracking is a common Sales Cloud pattern with extensive training data. LLMs apply this general CRM pattern to Health Cloud without recognizing that clinical referrals require the specialized Health Cloud data model.

**Correct pattern:**
Health Cloud clinical referrals belong on ClinicalServiceRequest, not Lead. Lead-based tracking is appropriate for marketing attribution and sales pipeline management, not clinical care coordination. ClinicalServiceRequest supports patient lookup, provider lookup, FHIR R4 mapping, and clinical encounter linkage — none of which are available on the Lead object.

**Detection hint:** If the referral tracking recommendation uses Lead, Opportunity, or custom referral objects for a Health Cloud clinical use case without mentioning ClinicalServiceRequest, the wrong data model is being applied.
