# LLM Anti-Patterns — Patient Engagement Requirements

Common mistakes AI coding assistants make when generating or advising on patient engagement requirements.

## Anti-Pattern 1: Assuming Patient Portal Is Included in Base Health Cloud

**What the LLM generates:** Architecture designs and implementation steps for a patient-facing portal that assume Health Cloud includes patient portal capability, without noting that Experience Cloud for Health Cloud is a separately licensed add-on.

**Why it happens:** Health Cloud documentation extensively describes patient portal features. LLMs present these features as part of Health Cloud without knowing the product boundary between Health Cloud (care coordinator/clinician tool) and Experience Cloud for Health Cloud (patient-facing portal, separate add-on).

**Correct pattern:**
Patient portal functionality requires the Experience Cloud for Health Cloud add-on SKU with per-user licensing. This must be explicitly included in the contract. Confirm the add-on is licensed before scoping any patient-facing portal features.

**Detection hint:** If the patient portal implementation plan does not mention "Experience Cloud for Health Cloud" as a separate licensed add-on, the license dependency is missing.

---

## Anti-Pattern 2: Including No-Show Prediction Without CRM Analytics License

**What the LLM generates:** Intelligent Appointment Management requirements that include no-show risk prediction as a standard feature, without noting the CRM Analytics license dependency.

**Why it happens:** No-show prediction is prominently featured in IAM product marketing and documentation. LLMs present it as a native IAM feature without knowing that the AI/ML prediction layer requires a separately licensed CRM Analytics add-on.

**Correct pattern:**
IAM core appointment scheduling works without CRM Analytics. No-show prediction specifically requires CRM Analytics (formerly Tableau CRM) as a separate license. When scoping IAM, explicitly separate core scheduling from predictive analytics requirements and confirm the CRM Analytics license if prediction is needed. Recording a no-show needs no add-on: `NoShow` already exists as a booking status and a Service Appointment Status Reason value (Agentforce Health Developer Guide). UNVERIFIED (2026-10-03): the CRM Analytics dependency itself is not described in the developer guide.

**Detection hint:** If IAM requirements include no-show prediction without mentioning CRM Analytics as a license requirement, the dependency is missing.

---

## Anti-Pattern 3: Assuming OmniStudio and Discovery Framework Are Ready Because Health Cloud Is Licensed

**What the LLM generates:** Health assessment configuration steps that assume OmniStudio and Discovery Framework are ready to use immediately after Health Cloud is licensed. The opposite error also appears: instructions to find "the Discovery Framework package" under Installed Packages.

**Why it happens:** OmniStudio is licensed as part of Health Cloud. LLMs conflate "licensed" with "set up and active", and they assume every Industries capability is a managed package.

**Correct pattern:**
Record which OmniStudio runtime the org uses: Omnistudio for Managed Packages (installed package, custom objects) or the standard runtime. Confirm the Discovery Framework feature is enabled; the Salesforce Industries Developer Guide describes it as a feature enabled in the org, not as a package. Add the Health Cloud and Health Cloud Platform permission set licenses and the Health Cloud Permission Set License permission set for assessment users, because the Assessment objects are visible only with them (Agentforce Health Developer Guide, Health Assessments).

**Detection hint:** Flag assessment plans that skip the runtime check, that look for Discovery Framework under Installed Packages, or that never mention the permission set licenses.

---

## Anti-Pattern 4: Using Standard Chatter for Patient-Clinician Messaging

**What the LLM generates:** Patient messaging solutions that route clinical communications (care instructions, assessment results) through Salesforce Chatter because it is built-in and available.

**Why it happens:** Chatter is the default Salesforce collaboration tool with extensive training data. LLMs recommend it for internal messaging without knowing that standard Chatter is not covered by the default Salesforce BAA for PHI.

**Correct pattern:**
Patient-clinician clinical communications (appointment details, care instructions, PHI-containing messages) must use HIPAA-covered channels. Use Messaging for In-App and Web with the Messaging User permission set. Verify BAA coverage for the specific messaging channel. Do not use standard Chatter for PHI-containing clinical communications.

**Detection hint:** If the patient messaging solution uses standard Chatter or generic email without BAA coverage verification, the HIPAA channel compliance requirement is missing.

---

## Anti-Pattern 5: Designing Portal Features Without Per-User License Planning

**What the LLM generates:** Patient portal implementations that do not account for per-user Experience Cloud for Health Cloud license assignment, assuming a single org-level license covers all patient users.

**Why it happens:** Experience Cloud licensing models (per-user vs. login vs. member-based) are complex. LLMs often present portal implementation steps without detailing per-user license assignment requirements, particularly for patient-facing portals where each patient is an Experience Cloud user.

**Correct pattern:**
Experience Cloud for Health Cloud uses per-user licensing — each patient portal user requires an Experience Cloud for Health Cloud license assigned via permission set. Estimate the patient user population size for licensing cost planning. Factor per-user license costs into the total project budget. Plan the permission set assignment process for patient onboarding.

**Detection hint:** If the portal design does not include per-user license assignment planning and cost estimation, the per-user licensing requirement has been overlooked.

---

## Anti-Pattern 6: Scoping Self-Scheduling as a Salesforce-Only Feature

**What the LLM generates:** "Enable Intelligent Appointment Management, create work types, and patients can book online", with no mention of the EHR.

**Why it happens:** LLMs know Salesforce Scheduler and assume IAM is the same thing for healthcare. The developer guide describes IAM as integrating with the customer's appointment management system: Health Cloud queries the source EHR for practitioner availability at a facility using the source system's IDs.

**Correct pattern:**
```
For each specialty, record:
  system of record for slots ..... EHR name / Salesforce Scheduler
  integration .................... default AppointmentBookingInteropFhirAdapter (FHIR R4)
                                   or custom class implementing healthcloudext.AppointmentBookingInterop
  credentials .................... Named Credential, mapped in AppointmentBookingConfig
  patient-facing reasons ......... AppointmentReason records
  channels per reason ............ ApptReasonEngmtChannelType rows (video, phone, in person)
  work types ..................... DefaultWorkTypeId (new patient), EstablishedWorkTypeId (established patient)
```

**Detection hint:** Self-scheduling requirements with no source-system column, no Named Credential, or no reason-by-channel matrix.

---

## Anti-Pattern 7: Granting Portal Users Clinical Data Without the FHIR Experience Cloud Permission Set

**What the LLM generates:** A portal design that shows `ClinicalEncounter` or `HealthCondition` records to patients through standard sharing alone.

**Why it happens:** LLMs apply the usual Experience Cloud recipe (profile, sharing set) and stop. The developer guide adds two conditions: community users need the FHIR R4 for Experience Cloud Sites permission set, and objects such as `ClinicalEncounter` and `HealthCondition` exist only after the FHIR-Aligned Clinical Data Model org preference is enabled.

**Correct pattern:** List the clinical objects per portal page, enable the org preference where the object requires it, and assign the FHIR R4 for Experience Cloud Sites permission set to portal users, then apply sharing.

**Detection hint:** Portal requirements that read Clinical Data Model objects without naming the org preference or the permission set.
