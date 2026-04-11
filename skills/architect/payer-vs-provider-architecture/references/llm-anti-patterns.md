# LLM Anti-Patterns — Payer vs Provider Architecture

Common mistakes AI coding assistants make when generating or advising on Health Cloud payer vs provider architecture.
These patterns help the consuming agent self-check its own output.

---

## Anti-Pattern 1: Treating Provider Relationship Management as a Clinical Provider Feature

**What the LLM generates:** Recommendations that activate Provider Relationship Management in a clinical provider org to manage the hospital's relationships with physicians, specialists, or referring providers. The LLM reads "Provider" in "Provider Relationship Management" and associates it with provider-side (clinical) deployments.

**Why it happens:** The name "Provider Relationship Management" contains the word "provider," which LLMs trained on general healthcare text associate with care delivery organizations (hospitals, clinics). The distinction that this is a payer-facing feature for insurance network credentialing is buried in Salesforce's supplemental documentation and is not prominent in general Health Cloud overviews.

**Correct pattern:**

```
Provider Relationship Management is a PAYER-side feature.
It models the relationship between a health plan and network practitioners/facilities.
Use cases: credentialing, contracting, network participation agreements, provider data management for payers.

For a clinical provider org managing physician relationships or referring networks,
use standard Account/Contact relationship models and Health Cloud care team objects.
Do NOT activate Provider Relationship Management in a provider (clinical) org.
```

**Detection hint:** If output recommends "Provider Relationship Management" for a hospital, clinic, or clinical care delivery use case — flag it. Provider Relationship Management belongs exclusively to payer deployments.

---

## Anti-Pattern 2: Assigning Only Base Health Cloud PSL to Payer Users

**What the LLM generates:** PSL assignment instructions that assign the base "Health Cloud" PSL to all users in a payer org, with no mention of Health Cloud for Payers PSL, Utilization Management PSL, or Provider Network Management PSL.

**Why it happens:** Most Health Cloud documentation and training material covers the base PSL. Payer-specific PSLs are documented in supplemental payer-sector documentation that is less prominently indexed. LLMs default to the most commonly documented PSL pattern.

**Correct pattern:**

```
Payer org PSL matrix — minimum required:
  All payer users:        Health Cloud PSL (base) + Health Cloud for Payers PSL
  Utilization Management: + Utilization Management PSL
  Provider Network Mgmt:  + Provider Network Management PSL

Base Health Cloud PSL alone does NOT unlock member management, claims,
benefit coverage, or prior authorization features in a payer org.
Missing payer PSLs produce silent feature gaps — no error is shown.
```

**Detection hint:** Any payer org PSL recommendation that does not include "Health Cloud for Payers" is incomplete. Flag PSL matrices that list only "Health Cloud" or "Health Cloud Platform."

---

## Anti-Pattern 3: Using AuthorizationForm for Clinical Consent

**What the LLM generates:** Recommendations to use `AuthorizationForm` and `AuthorizationFormConsent` objects for clinical patient consent management (consent for treatment, HIPAA authorization for release of information) in a provider deployment.

**Why it happens:** The object names contain "Authorization" and "Consent," which LLMs associate with clinical consent requirements. The Salesforce documentation for these objects is categorized under Health Cloud but the Utilization Management context is not always prominent in schema-level documentation.

**Correct pattern:**

```
AuthorizationForm and AuthorizationFormConsent are Utilization Management objects.
They model INSURANCE PRIOR AUTHORIZATION requests in a payer org.
They are NOT general-purpose consent objects.

For clinical patient consent in a provider org:
- Use Salesforce Consent Data Model objects (Individual, ContactPointTypeConsent, etc.)
- Or build a custom consent model on Account/Contact

Do NOT use AuthorizationForm in a provider org.
Do NOT use AuthorizationForm without Utilization Management PSL assigned.
```

**Detection hint:** If output places `AuthorizationForm` in a provider (clinical) deployment — flag it. If output uses `AuthorizationFormConsent` for HIPAA release-of-information or patient consent-for-treatment — flag it.

---

## Anti-Pattern 4: Using ClinicalEncounter or HealthCondition in a Payer Org

**What the LLM generates:** Data model designs for a payer org that include `ClinicalEncounter` to track member service interactions or `HealthCondition` to record diagnosis information received on claims.

**Why it happens:** LLMs associate "health data" with clinical objects. The nuance that a payer org records claims-based diagnosis codes differently from a provider org recording clinician-documented diagnoses is not captured in general Health Cloud overviews. LLMs also sometimes conflate "member interaction" with "clinical encounter."

**Correct pattern:**

```
Payer org member interaction tracking:
  Use Case              --> Correct Object
  Member service contact --> Case (linked to MemberPlan)
  Claims-based diagnosis --> ClaimLine (diagnosis codes on claim lines)
  Encounter-based claim  --> ClaimHeader (claim event)
  Authorization request  --> AuthorizationForm

ClinicalEncounter and HealthCondition are provider-side clinical objects.
They carry clinical semantics (clinician documentation, FHIR clinical resources)
that do not apply to insurance claims processing.
Using them in a payer org creates governance risk and data model mismatch.
```

**Detection hint:** Any payer org data model that includes `ClinicalEncounter`, `HealthCondition`, `Medication`, or `CareObservation` should be flagged for review.

---

## Anti-Pattern 5: Assuming FHIR R4 Is Active by Default After PSL Assignment

**What the LLM generates:** FHIR integration instructions for a provider org that proceed directly from PSL assignment to FHIR API testing, without a step to enable FHIR R4 Support Settings in Health Cloud Setup.

**Why it happens:** LLMs trained on Health Cloud documentation conflate PSL assignment (the licensing step) with feature activation (the configuration step). For most Salesforce features, PSL assignment is sufficient. FHIR R4 in Health Cloud requires an additional explicit setup step that is documented separately from the PSL assignment guide.

**Correct pattern:**

```
Provider org FHIR activation — required steps in order:
1. Assign Health Cloud PSL to users (base license)
2. Navigate to Setup > Health > Health Cloud Settings
3. Enable FHIR R4 Support Settings
4. Confirm FHIR R4 is selected as the target version
5. Validate FHIR API endpoint: GET /services/data/vXX.0/health/fhir/r4/metadata
   Expected: 200 response with FHIR CapabilityStatement

PSL assignment alone does NOT activate FHIR R4 endpoints or FHIR field mappings.
FHIR R4 Support Settings must be explicitly enabled in Setup.
```

**Detection hint:** Any FHIR integration checklist that does not include a step for "Enable FHIR R4 Support Settings in Health Cloud Setup" is incomplete for a provider deployment requiring FHIR interoperability.

---

## Anti-Pattern 6: Conflating Payer "Provider" and Clinical "Provider" in Requirements Analysis

**What the LLM generates:** Requirements analysis or solution design that uses the term "provider" without disambiguation — leading to recommendations that mix payer-side provider network management with clinical provider data management in the same object model.

**Why it happens:** The word "provider" is used in both sectors with completely different meanings. LLMs default to whichever meaning appears more frequently in their training context and do not flag the ambiguity to the user.

**Correct pattern:**

```
Before any Health Cloud design that involves "providers," ask:

1. Network provider (payer context)?
   - A practitioner or facility in the health plan's provider network
   - Credentialed, contracted, billed on claims
   - Managed by: Provider Relationship Management (payer PSL required)

2. Clinical provider (provider context)?
   - The care delivery organization or clinician treating the patient
   - Documents encounters, conditions, medications
   - Modeled by: Account/Contact + clinical data model objects

These are DIFFERENT concepts. They must be disambiguated in writing
before any object model or feature selection is made.
Flag every instance of "provider" in requirements and confirm which meaning is intended.
```

**Detection hint:** Any design document or requirements analysis that uses "provider" without qualifying it as "network provider (payer)" or "clinical provider (care delivery)" is ambiguous. Flag it for explicit disambiguation before proceeding.
