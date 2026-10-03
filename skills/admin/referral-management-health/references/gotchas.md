# Gotchas — Referral Management Health Cloud

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

Primary source: Agentforce Health Developer Guide (the Health Cloud developer guide PDF, `health_cloud_dev_guide.pdf`, Spring '26), read on 2026-10-03. Claims about licenses, permission sets, and Data Processing Engine jobs come from Salesforce Help in earlier revisions and are marked UNVERIFIED.

## Gotcha 1: Data Pipelines Base User License Required for DPE Provider Search Population

**What happens:** The Data Processing Engine job that populates CareProviderSearchableField silently produces zero records or fails with a license error visible only in job execution logs. Provider search components return empty results with no user-facing error. UNVERIFIED (2026-10-03): the developer guide confirms that provider search APIs query `CareProviderSearchableField` and that the object supports only query, retrieve, search, delete, and undelete calls (no create or update), so something other than users must populate it; it does not name the DPE job or the license.

**When it occurs:** Whenever the process user or integration user running the DPE job does not have the Data Pipelines Base User permission set license assigned.

**How to avoid:** Before go-live, verify the service user that runs DPE jobs has Data Pipelines Base User assigned. After assigning the license, manually run the job and confirm records appear in CareProviderSearchableField before enabling provider search for end users.

**Source:** Agentforce Health Developer Guide, Provider Relationship Management, `CareProviderSearchableField` (description and supported calls).

---

## Gotcha 2: HealthCloudICM Permission Set Required on ClinicalServiceRequest

**What happens:** Users without the HealthCloudICM permission set receive an insufficient privileges error when attempting to create, view, or update ClinicalServiceRequest records, even if their profile has object-level access. UNVERIFIED (2026-10-03): the permission set name does not appear in the developer guide read for this revision.

**When it occurs:** Any user who interacts with referral records, including integration users and automated process users.

**How to avoid:** Include the required Health Cloud permission sets in the assignment checklist for every persona, including the integration user. Test referral creation from each persona in a sandbox before go-live.

**Source:** Carried from earlier revisions (Salesforce Help).

---

## Gotcha 3: The Provider Search Index Lags Behind Provider Record Updates

**What happens:** When a provider's specialty, network status, or location changes, provider search keeps returning the old values until the index is rebuilt. `CareProviderSearchableField` holds denormalized copies of Provider Relationship Management fields, so it is a snapshot, not a live view.

**When it occurs:** Any time provider records are updated between index refreshes.

**How to avoid:** Schedule the index refresh at a frequency that matches the provider roster change rate. Document the latency for care coordinators. UNVERIFIED (2026-10-03): the refresh mechanism (a DPE job and its schedule) is described in Help, not in the developer guide.

**Source:** Agentforce Health Developer Guide, `CareProviderSearchableField` ("holds denormalized data from certain fields in the Provider Relationship Management data model").

---

## Gotcha 4: FSC Referral Configuration Conflicts with Health Cloud Referrals

**What happens:** An org with both FSC and Health Cloud licenses may have FSC Referral Management configuration (Lead/Opportunity fields for advisor referrals, Einstein Referral Scoring metadata) that creates confusion with Health Cloud's ClinicalServiceRequest referral workflow. UNVERIFIED (2026-10-03): the FSC side was not re-read for this revision.

**When it occurs:** Multi-cloud implementations where both FSC and Health Cloud are active in the same org.

**How to avoid:** Document which referral workflow applies to which persona and record type at project inception. Use separate record types and page layouts.

**Source:** Carried from earlier revisions.

---

## Gotcha 5: Several Commonly Quoted Referral Fields Do Not Exist

**What happens:** Flows, validation rules, and integration mappings reference `ReferralType`, `ReferredToId`, `ReferralDate`, or `AuthorizationNumber` on `ClinicalServiceRequest`, and deployment fails or the mapping silently drops data. None of these fields is in the object reference. Earlier versions of this skill listed all four.

**When it occurs:** When requirements or generated code are written from memory of other referral products instead of from the object reference.

**How to avoid:** Map the requirement onto real fields: `RequesterId` and `PerformerId` for the two parties, `StartDate` or `DateSigned` for dates, `Type` and `Priority` for classification, and a `ClinicalServiceRequestDetail` record (or a custom field) for an authorization number.

**Source:** Agentforce Health Developer Guide, Clinical Data Model, `ClinicalServiceRequest` field list.

---

## Gotcha 6: Status Uses FHIR Values, and Acceptance Is a Separate Checkbox

**What happens:** Automation is built around "Submitted", "Accepted", and "Declined" status values that are not in the standard picklist. The standard `Status` values are Active, Completed, Draft, Entered-in-Error, On-Hold, Revoked, and Unknown. Acceptance is the `IsAccepted` checkbox (default false), and reasons go in the multi-select `StatusReason`.

**When it occurs:** When the referral lifecycle is designed as one status picklist with business-specific values.

**How to avoid:** Map each business state to Status, IsAccepted, and StatusReason before adding custom picklist values. Keep custom values out of FHIR exchange unless the receiving system accepts them.

**Source:** Agentforce Health Developer Guide, `ClinicalServiceRequest` (`Status`, `IsAccepted`, `StatusReason`).

---

## Gotcha 7: The Performer Cannot Be a Contact

**What happens:** A design stores the receiving physician as a Contact and tries to put that Contact on the referral. `PerformerId` and `RequesterId` are polymorphic references limited to Account, Asset, HealthcareProvider, and CareRegisteredDevice.

**When it occurs:** When the provider network was loaded as Accounts and Contacts only, without `HealthcareProvider` records.

**How to avoid:** Point `PerformerId` at the practitioner's `HealthcareProvider` record (or the facility Account). Load `HealthcareProvider` records for every practitioner who can receive referrals.

**Source:** Agentforce Health Developer Guide, `ClinicalServiceRequest` (`PerformerId` and `RequesterId` referenced objects).

---

## Gotcha 8: ClinicalServiceRequest Needs the FHIR-Aligned Clinical Data Model Org Preference

**What happens:** The referral object, its detail object, and the encounter junction are missing from the org, so nothing can be configured. `ClinicalServiceRequest`, `ClinicalServiceRequestDetail`, and `ClinicalEncounterSvcRequest` are on the developer guide's list of objects that require the FHIR-Aligned Clinical Data Model org preference. `HealthcareProvider` and `HealthcarePractitionerFacility` do not need it, which is why provider data can exist while referral objects do not.

**When it occurs:** Orgs that enabled Health Cloud provider management but never turned on the clinical data model.

**How to avoid:** Enable the preference in Setup > FHIR R4 Support Settings before configuring referrals, and include it in sandbox setup scripts.

**Source:** Agentforce Health Developer Guide, Clinical Data Model ("To enable these objects in your org, go to FHIR R4 Support Settings in Setup and enable the FHIR-Aligned Clinical Data Model org pref").

---

## Gotcha 9: Referral Access Follows the Patient Until Sharing Is Changed

**What happens:** `PatientId` is a master-detail reference to Account, so access to a referral is controlled by access to the patient. Queues cannot own referrals until sharing changes. The object reference notes that to enable queues, the sharing setting for the object must change from Controlled By Parent to Private.

**When it occurs:** When an intake team wants a referral queue, or when external partners should see referrals but not the full patient record.

**How to avoid:** Decide the ownership model early. If queues are needed, change the sharing setting to Private and design sharing rules for the teams that work referrals.

**Source:** Agentforce Health Developer Guide, `ClinicalServiceRequest` (`PatientId` master-detail; `OwnerId` note on queues, API 56.0).

---

## Gotcha 10: The Referral Management API Caps Performers and Can Create Patients

**What happens:** An external intake system sends six candidate specialists and the request is rejected, or a typo in patient details creates a duplicate patient Account. The Referral Management Connect API (`POST /services/data/vXX.X/connect/health/referral-management/referrals`, API 59.0+) accepts at most five performer IDs per request. When `patient` carries `fields` instead of an `id`, the API creates the Account, and `shouldUseHighConfidenceMatch` decides whether it matches the duplicate record with the highest confidence instead.

**When it occurs:** Integrations that pass every in-network specialist, or that send new-patient details without duplicate settings.

**How to avoid:** Send at most five performers. Send `patient.id` when the patient is known. Set `shouldUseHighConfidenceMatch` deliberately and test it against the org's duplicate rules.

**Source:** Agentforce Health Developer Guide, REST Reference, Referral Management (request body properties).

---

## Gotcha 11: Two Referral Models Coexist in Health Cloud

**What happens:** Reports disagree because some referrals sit on Lead records with Health Cloud referral fields (`ReferralStatus__c`, `ReferredToOrganization__c`, `ReasonForReferral__c`, `ReferringPractitioner__c`) and others on `ClinicalServiceRequest`. The developer guide documents both sets.

**When it occurs:** Orgs that started with the Lead-based intake model and later adopted the clinical data model.

**How to avoid:** Pick one model per persona, document it, and migrate or archive the other. Do not build automation that reads both without a reconciliation rule.

**Source:** Agentforce Health Developer Guide, "Health Cloud Referral Management Fields on Contact, Lead, and Opportunity".

---

## Gotcha 12: Extra Provider Search Fields Need a Mapping and a Target Field

**What happens:** A custom field added to `HealthcareProvider` never shows up in provider search. Search reads `CareProviderSearchableField`, and fields reach it only through a `CareProviderSearchConfig` record that maps a source field on `HealthcareProvider` or `HealthcarePractitionerFacility` to a target field on the search object.

**When it occurs:** When coordinators ask to filter by a new attribute (language spoken, accepting new patients) and only the source field is created.

**How to avoid:** Create the source field, a matching target custom field on `CareProviderSearchableField`, and an active `CareProviderSearchConfig` mapping. Deploy all three together.

**Source:** Agentforce Health Developer Guide, `CareProviderSearchConfig` object and Metadata API type (sample definition and package.xml listing both custom fields).
