# Gotchas — Payer vs Provider Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Payer PSL Gaps Are Silent — No Error, No Warning

**What happens:** When a user is assigned only the base Health Cloud PSL in a payer org, the member management tabs, claims views, benefit coverage components, and prior authorization workflows simply do not appear in the org. Salesforce does not display a license error, a locked-feature notice, or any indication that a PSL is missing. From the user's perspective, the features look absent or misconfigured, not unlicensed.

**When it occurs:** This surfaces during UAT or shortly after go-live when business users report that the member portal or claims processing screens are not visible. It is most common when the implementation team assigns PSLs from the standard Health Cloud documentation without reading the Health Cloud for Payers supplemental documentation. It also occurs when an admin copies PSL assignments from a provider deployment to a payer deployment — the base PSL is present, but the payer-specific PSL is not.

**How to avoid:** Before user acceptance testing, export the Permission Set License assignments from Setup > Company Information > Permission Set Licenses and verify that Health Cloud for Payers PSL is assigned to all payer-side users. For users who will process prior authorizations, verify Utilization Management PSL. For users managing provider network contracting, verify Provider Network Management PSL. Create a PSL audit checklist as part of the go-live readiness gate and re-run it after any bulk user provisioning.

---

## Gotcha 2: FHIR R4 Support Settings Are Not Enabled by Default

**What happens:** Health Cloud with base PSL assigned does not automatically activate FHIR R4-aligned clinical objects. `ClinicalEncounter` records can be created, but FHIR R4 resource mappings, FHIR API endpoints, and FHIR-specific field behaviors are not active until FHIR R4 Support Settings are explicitly enabled in Health Cloud Setup. Teams that skip this step find that FHIR API calls return unexpected results or that FHIR resource fields are not populated correctly on clinical records.

**When it occurs:** This affects provider-side deployments that require FHIR R4 interoperability for EHR integration or patient data exchange. It is commonly missed because the Health Cloud PSL assignment documentation and the clinical data model documentation are separate from the FHIR configuration documentation. An implementation team that sets up Health Cloud for care management without interoperability requirements may never encounter this — it only matters when FHIR API endpoints are tested.

**How to avoid:** For any provider deployment that includes EHR integration, patient data exchange, or FHIR API exposure, add a step to the implementation checklist: enable FHIR R4 Support Settings under Setup > Health > Health Cloud Settings. Confirm the correct FHIR version is selected. Validate the FHIR API endpoint returns a valid CapabilityStatement before beginning integration testing.

---

## Gotcha 3: AuthorizationForm Is a Utilization Management Object, Not a Consent Form

**What happens:** The `AuthorizationForm` and `AuthorizationFormConsent` objects in Health Cloud are specifically part of the Utilization Management feature set. They model prior authorization requests in a payer org — not clinical consent forms, patient authorization for release of information, or general-purpose consent management. If a team attempts to use these objects for clinical consent workflows in a provider org, they require the Utilization Management PSL (a payer-specific license) and the fields on the object are oriented toward insurance authorization workflows, not clinical consent documentation.

**When it occurs:** This occurs when a provider-side team searches for a "consent" object in Health Cloud's data dictionary, finds `AuthorizationFormConsent`, and attempts to use it for HIPAA patient authorization forms or clinical consent-for-treatment workflows. The object name is misleading in the provider context.

**How to avoid:** In provider deployments, clinical consent management should use standard Salesforce consent management objects (the Consent Data Model introduced with the Customer 360 Privacy Center) or custom consent objects on the patient's Account/Contact record. Reserve `AuthorizationForm` and `AuthorizationFormConsent` exclusively for payer orgs with Utilization Management requirements. When reviewing requirements that mention "authorization" or "consent," explicitly confirm whether the requirement is for insurance prior authorization (payer) or clinical patient consent (provider) before selecting an object.

---

## Gotcha 4: MemberPlan and ClinicalEncounter Do Not Have a Platform-Managed Relationship

**What happens:** In a dual-sector org where both payer and provider objects are active, there is no Salesforce-managed relationship between a member's `MemberPlan` and a patient's `ClinicalEncounter`. The platform does not automatically link a patient's insurance coverage to their clinical records. Architects who design workflows assuming this linkage exists will find that the data model cannot support cross-sector queries (for example: "show all encounters for members on Plan X") without custom junction objects or lookup relationships built explicitly.

**When it occurs:** This is most commonly encountered in population health or care management use cases within an IDN, where the business wants to correlate clinical utilization data with insurance coverage data. The assumption is natural — in real-world healthcare operations, the two are closely related — but Salesforce Health Cloud does not pre-wire them.

**How to avoid:** In dual-sector design, explicitly model the cross-sector linkage if it is required. A custom lookup field from `ClinicalEncounter` to `MemberPlan` (or a junction object) must be designed, governed, and populated through integration or data entry. Document this as an explicit architecture decision, not a platform-provided feature.

---

## Gotcha 5: Base Health Cloud PSL Does Not Unlock Payer Features Even in an Org with Payer Objects Installed

**What happens:** Health Cloud installs a unified managed package that contains both payer objects (`MemberPlan`, `ClaimHeader`) and provider objects (`ClinicalEncounter`, `HealthCondition`) in the org's schema. The presence of these objects in the org schema does not mean they are usable. Access to payer-specific objects, UI components, and workflows requires the Health Cloud for Payers PSL to be assigned to users and the corresponding permission sets to be granted. An org where all users have only the base Health Cloud PSL will have payer objects visible in the Object Manager but inaccessible in the user interface and restricted at the field-level for most payer-specific fields.

**When it occurs:** This trips up admins who validate the implementation by inspecting the Object Manager (seeing `MemberPlan` in the schema) and conclude that the payer feature set is active. The objects exist; the permissions to use them do not. This is most likely to cause issues when an org is converted from a provider-only deployment to a dual-sector deployment — the new payer objects appear in schema immediately but are not usable until PSLs are assigned and permission sets are activated.

**How to avoid:** Use permission set license assignment as the definitive test for feature activation, not object schema presence. After activating a new sector, assign the correct PSL to a test user and verify end-to-end that the feature UI appears and records can be created. Treat object schema presence as a necessary but not sufficient condition for feature availability.
