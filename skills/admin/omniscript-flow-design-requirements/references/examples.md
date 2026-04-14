# Examples — OmniScript Flow Design Requirements

## Example 1: Claims Intake OmniScript for Insurance Cloud

**Context:** An insurance company wants a guided claims intake OmniScript for service agents running in Lightning Experience. The BA must produce requirements before the developer starts.

**Problem:** Without structured requirements, the developer discovers mid-build that branching logic wasn't mapped to OmniScript Conditional View syntax and the data source timing (Pre vs Post Step) was unspecified. Build must be restarted.

**Solution:**
The BA produces a requirements document that specifies:
- Step 1: Policy Lookup — Pre-Step Read DataRaptor pulling InsurancePolicy fields by Policy_Number__c input
- Step 2: Loss Details — Radio Button "Loss Type" (Auto/Property/Liability) with three Block containers, each with Conditional View set to `%LossType:value% == 'Auto'`, `== 'Property'`, `== 'Liability'` respectively
- Step 3: Coverage Selection — Post-Step Integration Procedure that validates coverage eligibility
- Step 4: Summary & Submit — Post-Step Integration Procedure creates Claim and ClaimItem records; Navigate Action routes to the new Claim record page

**Why it works:** The branching is documented in OmniScript Conditional View notation so the developer can directly wire the JSON condition without a discovery session. The Pre/Post timing is explicit, preventing the common "data loaded Post-Step can't be seen on current screen" bug.

---

## Example 2: Employee Onboarding OmniScript for Manufacturing Cloud

**Context:** A manufacturing org running OmniStudio on Core (Standard Runtime, Spring '25+) needs a 5-step employee onboarding OmniScript with different paths for full-time vs contractor employees.

**Problem:** The team copies requirements from a Screen Flow document. The developer applies standard Decision element branching logic, which does not exist in OmniScript, and the conditional screens never appear.

**Solution:**
Requirements explicitly note:
- Branching mechanism: Conditional View on Block containers — NOT Decision elements (OmniScript has no Decision elements)
- Full-Time path Block: shown when `%EmploymentType:value% == 'Full-Time'` — contains Benefits selection and beneficiary fields
- Contractor path Block: shown when `%EmploymentType:value% == 'Contractor'` — contains NDA acknowledgment, rate card, and engagement end date
- Step 5 Navigate Action: two separate Navigate Action elements each with a Condition property pointing to the same employment type field — Full-Time routes to Onboarding Dashboard, Contractor routes to Document Signing page

**Why it works:** Specifying Conditional View JSON notation in requirements documents prevents the developer from applying Screen Flow patterns that don't translate to OmniStudio's declarative branching model.

---

## Anti-Pattern: Treating OmniScript Requirements as Screen Flow Requirements

**What practitioners do:** They produce a standard business requirements document using Flow screen wireframes, Decision element annotations, and generic form field lists — without OmniScript-specific structural notes.

**What goes wrong:** The developer must re-derive the OmniScript structural requirements (Step containers, Block groupings for conditions, Pre vs Post action timing, Navigate Action specification) from generic requirements, creating ambiguity and rework. The activation failure for missing Navigate Action is only discovered when the developer tries to activate the OmniScript.

**Correct approach:** Use an OmniScript-specific requirements template that explicitly captures: Step inventory, Block container groupings with Conditional View expressions, data source type per step (DataRaptor vs IP vs Remote Action) with Pre/Post timing, and Navigate Action destination.
