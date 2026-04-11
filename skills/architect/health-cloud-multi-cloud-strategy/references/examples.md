# Examples — Health Cloud Multi-Cloud Strategy

## Example 1: Patient Portal Licensing Gap Discovered at UAT

**Scenario:** Mid-size regional health system implementing Health Cloud with a patient self-service portal.

**Context:** The implementation team built an Experience Cloud site for patient portal access to care plans and care program enrollment status. The site was built and tested in a developer sandbox where the project lead had System Administrator access. UAT was the first time external patient test users (provisioned with Customer Community Plus profiles) attempted to log in.

**Problem:** External test users received "Insufficient Privileges" errors when attempting to view their CareProgramEnrollee records and the Care Plan FlexCard on the portal home page. Internal admin users saw everything correctly. The implementation team spent two days debugging OWD settings and Sharing Sets before identifying the real root cause.

**Solution:**

The root cause was a missing Health Cloud for Experience Cloud permission set license assignment. The fix requires two steps:

Step 1 — Assign the Experience Cloud for Health Cloud PSL to the portal user profile (or to each individual portal user):

```
Setup > Users > Permission Set Licenses > Health Cloud for Experience Cloud
> Assign to Users (or Manage Assignments from the Portal Profile)
```

Step 2 — Verify the portal user's profile includes the Experience Cloud for Health Cloud permission set (not just the PSL):

```
Setup > Permission Sets > Health Cloud for Experience Cloud
> Manage Assignments > Add Assignments > [portal user or profile]
```

In a org with many portal users, this is best automated via a Salesforce CLI data script or a Flow that assigns the PSL when a new Contact is converted to a portal user.

**Why it works:** The Health Cloud FlexCards and OmniScript components on the Experience Cloud site enforce Health Cloud object-level access via the permission set, not via OWD alone. Without the PSL and permission set, the portal user's session has no access to CareProgramEnrollee, CarePlan, or ClinicalEncounter records regardless of Sharing Set configuration.

---

## Example 2: OmniScript Fails Silently Due to Incomplete PSL Stack

**Scenario:** Large hospital network implementing guided SDOH screening assessments via OmniStudio OmniScripts for care coordinators.

**Context:** The care coordinator user profile was assigned the Health Cloud permission set license during initial setup. A month later, the development team enabled OmniStudio and assigned the OmniStudio User PSL to all care coordinators. The OmniScripts launched and displayed correctly in the UI. However, during testing, the DataRaptor steps that read EpisodeOfCare and write to CarePlan records returned empty results or "Record not found" errors, even for records the care coordinator could see on the standard record page.

**Problem:** The Health Cloud Platform PSL was never assigned. Without it, the care coordinator session cannot perform CRUD operations on Health Cloud-specific objects (EpisodeOfCare, ClinicalEncounter, CarePlan) even though those objects are visible in standard page layouts via the base Health Cloud PSL.

**Solution:**

Assign all three PSLs to every care coordinator who uses OmniStudio components:

```
PSL 1: Health Cloud                  → base Health Cloud object visibility
PSL 2: Health Cloud Platform         → CRUD rights on HLS-specific objects
PSL 3: OmniStudio User               → right to execute OmniScripts / FlexCards
```

Verification query via Salesforce CLI to confirm all three are assigned:

```bash
sf data query \
  --query "SELECT PermissionSetLicense.DeveloperName, Assignee.Name \
           FROM PermissionSetLicenseAssign \
           WHERE PermissionSetLicense.DeveloperName IN \
           ('HealthCloudPsl','HealthCloudPlatformPsl','OmniStudioUser') \
           AND Assignee.Profile.Name = 'Health Cloud Care Coordinator'" \
  --use-tooling-api
```

If any of the three PSLs is missing for a given user, the OmniScript runtime will fail at the DataRaptor step with a non-descriptive error rather than a permissions error.

**Why it works:** OmniStudio DataRaptors execute object CRUD under the running user's session. The Health Cloud Platform PSL is the one that grants field-level and object-level CRUD for Health Cloud's extended data model objects. Without it, DataRaptors that reference those objects get empty query results, which surfaces as "no record found" in the OmniScript UI.

---

## Example 3: Marketing Cloud PHI Flow Without a Dedicated BAA

**Scenario:** A care management organization wanted to automate appointment reminder journeys via Marketing Cloud using Health Cloud appointment data.

**Context:** The team configured Marketing Cloud Health Cloud Connect and began syncing Contact, CareProgramEnrollee, and Appointment records from Health Cloud to Marketing Cloud for use in Journey Builder. They had a HIPAA BAA in place for their Health Cloud org. The compliance team reviewed the architecture six weeks into implementation and flagged a critical issue.

**Problem:** The HIPAA BAA that covered the Health Cloud org did not extend to Marketing Cloud. PHI (patient names, appointment dates, care program enrollment status) was flowing into Marketing Cloud's data extensions without a BAA covering that environment. This was a reportable HIPAA violation under the organization's compliance framework.

**Correct Approach:**

Before any PHI data flows from Health Cloud to Marketing Cloud:

1. Work with the Salesforce account team to execute a separate HIPAA BAA specifically for Marketing Cloud.
2. Confirm the BAA covers all Marketing Cloud business units that will receive Health Cloud data.
3. Until the BAA is executed, restrict the Marketing Cloud Health Cloud Connect sync to non-PHI fields only (e.g., internal IDs, anonymized cohort flags).
4. Document the approved PHI field list in the data flow diagram and keep it as a compliance artifact.

**Why it works:** Marketing Cloud is a separate product with its own data processing infrastructure. Salesforce's HIPAA BAA for Health Cloud covers the CRM platform. Marketing Cloud's data extensions, Journey Builder triggers, and Email Studio logs are outside that scope. Each must be explicitly covered.

---

## Anti-Pattern: Treating Health Cloud + Service Cloud as Two Separate License SKUs

**What practitioners do:** Architects unfamiliar with the Health Cloud bundle structure add "Service Cloud" as a separate license line item in the architecture documentation and in procurement requests for internal care coordinator users.

**What goes wrong:** Either the customer purchases redundant Service Cloud licenses (increasing cost unnecessarily), or the licensing model document causes confusion during legal review and procurement, leading to delayed contract execution. In sandbox orgs where licenses are allocated manually, over-counting also leads to Service Cloud licenses being allocated that could be used for non-Health Cloud users.

**Correct approach:** Health Cloud licenses implicitly include Service Cloud at the same edition level. Internal care coordinators access Cases, Entitlements, Omni-Channel, and all standard Service Cloud features under their Health Cloud license. The architecture documentation should explicitly state "Service Cloud case management is included in the Health Cloud license — no separate Service Cloud license is required for internal care team users."
