# Examples — Payer vs Provider Architecture

## Example 1: Health Plan Incorrectly Modeled with Clinical Objects

**Scenario:** Regional health insurance company migrating member management to Health Cloud

**Context:** A regional Medicaid managed care organization (MCO) is implementing Health Cloud to manage member enrollment, benefit coverage, and claims. The implementation team, familiar with Health Cloud from a previous hospital project, scaffolds the data model using `ClinicalEncounter` to track member interactions and `HealthCondition` to document member diagnoses shared by providers on claims.

**Problem:** The clinical objects are designed for care delivery documentation, not insurance administration. `ClinicalEncounter` does not carry the fields required for claims adjudication or authorization tracking. `HealthCondition` in the clinical model represents a clinician's documented diagnosis — not a diagnosis code on a claim line. The member services team cannot record plan coverage, process member enrollment, or link interactions to benefit plans. After go-live, the team discovers that the member portal tabs are absent for all users because Health Cloud for Payers PSL was never assigned — the base Health Cloud PSL was applied to all users, which does not unlock payer features.

**Solution:**

Correct the deployment type classification and rebuild the data model:

```
Payer Deployment — Canonical Object Model
------------------------------------------
Member identity:       Account (member) + Contact (subscriber/dependent)
Plan enrollment:       MemberPlan  -->  PurchaserPlan
Benefit structure:     CoverageBenefit  -->  CoverageBenefitItem
Claims:                ClaimHeader  -->  ClaimLine
Prior authorization:   AuthorizationForm + AuthorizationFormConsent
Member services:       Case (linked to MemberPlan)

PSL Assignment (per user):
  - Health Cloud PSL (base)
  - Health Cloud for Payers PSL
  - Utilization Management PSL (for prior auth users)
```

Assign Health Cloud for Payers PSL to all member services users. Assign Utilization Management PSL to clinical review nurses who process prior authorization requests. Remove `ClinicalEncounter` and `HealthCondition` from the data model — they add governance risk and are not needed for insurance administration.

**Why it works:** `MemberPlan` is the canonical payer object that links a member's identity to a specific insurance plan. All claims, benefits, and member services cases flow from this relationship. The payer PSL unlocks the member management UI components and the claims and authorization workflows that the MCO's business processes require.

---

## Example 2: Integrated Delivery Network Dual-Sector Design

**Scenario:** IDN operating both a health plan and a hospital system in a single Health Cloud org

**Context:** An integrated delivery network (IDN) owns both a regional health plan (payer) and a hospital network (provider). The CIO wants a single Salesforce org to serve both sides: payer staff administer member enrollment and process claims, while clinical care coordinators manage patient encounters and care plans. The architect must design the object model, PSL matrix, and data separation strategy.

**Problem:** Without deliberate separation, payer users can access clinical records (HIPAA minimum necessary violation) and clinical users can view insurance enrollment data they have no need to see. A naive implementation that activates all Health Cloud features for all users creates a mixed data model where clinical and insurance records are intermingled, audit trails are unreliable, and HIPAA data minimization cannot be demonstrated.

**Solution:**

Design the dual-sector architecture with explicit separation:

```
Dual-Sector Org — Separation Strategy
---------------------------------------
Shared identity layer:
  Account (member/patient — single record, dual purpose)
  Contact (subscriber/patient — same record, different relationships)

Payer side (separate record types + permission sets):
  MemberPlan        --> accessible to payer PSL holders only
  PurchaserPlan     --> accessible to payer PSL holders only
  CoverageBenefit   --> accessible to payer PSL holders only
  ClaimHeader       --> accessible to payer PSL holders only
  AuthorizationForm --> accessible to Utilization Management PSL holders only

Provider side (separate record types + permission sets):
  ClinicalEncounter   --> accessible to clinical permission set holders only
  HealthCondition     --> accessible to clinical permission set holders only
  Medication          --> accessible to clinical permission set holders only
  CareObservation     --> accessible to clinical permission set holders only

PSL Matrix:
  Payer users:    Health Cloud PSL + Health Cloud for Payers PSL
  Clinical users: Health Cloud PSL (base, with FHIR R4 activation)
  UM nurses:      Health Cloud PSL + Health Cloud for Payers PSL + Utilization Management PSL

Data separation enforcement:
  - Separate profiles: PayerUser profile, ClinicalUser profile
  - Object-level permissions: payer objects removed from ClinicalUser profile; clinical objects removed from PayerUser profile
  - Sharing rules: owner-based sharing within each sector; no cross-sector sharing rules
  - Field-level security: sensitive clinical fields (diagnosis, medication) restricted to clinical permission set holders
```

Enable FHIR R4 Support Settings for the clinical side. Confirm Health Cloud for Payers PSL is assigned to payer users and NOT to clinical-only users.

**Why it works:** The shared `Account`/`Contact` layer provides the unified member/patient identity without mixing sector-specific records. Object-level permission separation ensures payer users cannot navigate to clinical records and vice versa. The PSL matrix assigns the minimum required licenses to each persona, which satisfies both Salesforce licensing rules and HIPAA minimum necessary requirements.

---

## Anti-Pattern: Using Provider Relationship Management for Clinical Provider Data

**What practitioners do:** An architect designing a provider (clinical) deployment sees "Provider Relationship Management" in the Health Cloud feature list and activates it to manage the hospital's relationships with referring physicians and specialist networks.

**What goes wrong:** Provider Relationship Management is a payer-facing feature for credentialing and contracting practitioners in an insurance network. It models the relationship between a health plan and a network practitioner — not the relationship between a hospital and its clinical staff or referring partners. Activating it in a clinical provider org adds payer-side schema, requires payer PSL assignments to access the feature UI, and creates a data model that does not represent clinical provider relationships accurately. The credentialing and contracting workflows built for insurance network management do not map to clinical medical staff credentialing processes.

**Correct approach:** For a clinical provider org that needs to manage relationships with referring physicians, specialist networks, or medical staff, use standard Salesforce Account/Contact relationship models and Health Cloud's care team objects. If medical staff credentialing is in scope, evaluate a dedicated credentialing solution or custom Account relationship model — not Provider Relationship Management, which is designed for insurance network contracting.
