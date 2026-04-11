# Gotchas — Referral Management Health Cloud

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Data Pipelines Base User License Required for DPE Provider Search Population

**What happens:** The Data Processing Engine job that populates CareProviderSearchableField silently produces zero records or fails with a license error visible only in job execution logs. Provider search components return empty results with no user-facing error.

**When it occurs:** Whenever the process user or integration user running the DPE job does not have the Data Pipelines Base User permission set license assigned. This is a separate license from Health Cloud and is not included in standard Health Cloud licensing.

**How to avoid:** Before go-live, verify the service/integration user that runs DPE jobs has Data Pipelines Base User assigned. After assigning the license, manually run the job and confirm records appear in CareProviderSearchableField before enabling provider search for end users.

---

## Gotcha 2: HealthCloudICM Permission Set Required on ClinicalServiceRequest

**What happens:** Users without the HealthCloudICM permission set receive an insufficient privileges error when attempting to create, view, or update ClinicalServiceRequest records, even if their profile has object-level access to the object.

**When it occurs:** Any user who interacts with referral records — clinicians, care coordinators, integration users, and automated Flow/Apex process users — must have HealthCloudICM assigned. Profile-level access to ClinicalServiceRequest is not sufficient.

**How to avoid:** Include HealthCloudICM in the permission set assignment checklist for all users in clinical workflows. For integration users and automated processes, assign HealthCloudICM to the service user account. Test referral creation from all user personas in a sandbox before go-live.

---

## Gotcha 3: CareProviderSearchableField Is Stale After Provider Record Updates

**What happens:** When a provider's specialty, network status, or location fields are updated on the Account or Contact record, the change is NOT reflected in provider search results until the DPE index job runs again.

**When it occurs:** Any time provider records are updated between DPE job runs — typically overnight. In implementations with frequent provider roster changes, search results can be hours out of date.

**How to avoid:** Schedule the DPE job at a frequency appropriate for your provider roster change rate (daily for most orgs, more frequent for large networks with frequent changes). Document this latency for care coordinators so they understand provider search reflects the state as of the last index refresh. Optionally, build an admin trigger to queue a DPE re-run after bulk provider record updates.

---

## Gotcha 4: FSC Referral Configuration Conflicts with Health Cloud Referrals

**What happens:** An org with both FSC and Health Cloud licenses may have FSC Referral Management configuration (Lead/Opportunity fields for advisor referrals, Einstein Referral Scoring metadata) that creates confusion or naming conflicts with Health Cloud's ClinicalServiceRequest referral workflow.

**When it occurs:** Multi-cloud implementations where both FSC (for advisors/brokers) and Health Cloud (for patient referrals) are active in the same org.

**How to avoid:** Document which referral workflow applies to which user persona and record type at project inception. Use separate record types and page layouts for FSC advisor referrals vs. Health Cloud clinical referrals. Do not use FSC Referral documentation for Health Cloud referral configuration.
