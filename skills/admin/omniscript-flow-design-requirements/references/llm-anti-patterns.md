# LLM Anti-Patterns — OmniScript Flow Design Requirements

Common mistakes AI coding assistants make when generating or advising on OmniScript flow design requirements. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Conflating OmniScript Requirements with Screen Flow Requirements

**What the LLM generates:** A requirements document that uses Decision element notation, Fault path annotations, and generic "condition" branching markers borrowed from Screen Flow design patterns — without OmniScript-specific Conditional View JSON expressions or Block container groupings.

**Why it happens:** LLMs are trained on a much larger corpus of Screen Flow documentation and examples than OmniScript documentation. The structural differences between the two tools are not prominent enough in training data to override the default Screen Flow mental model.

**Correct pattern:**
```
Conditional branching in OmniScript uses Conditional View on Block containers:
- Block Name: AutoBlock
  - Conditional View: %LossType:value% == 'Auto'
  - Elements: VehicleYear, VehicleMake, VehicleModel
- Block Name: PropertyBlock
  - Conditional View: %LossType:value% == 'Property'
  - Elements: PropertyAddress, StructureType
```

**Detection hint:** Look for "Decision element," "Fault path," or generic `IF condition THEN show field X` notation in requirements output — these indicate Screen Flow bleed.

---

## Anti-Pattern 2: Omitting Navigate Action from Requirements

**What the LLM generates:** A requirements document that specifies all Steps and their data sources but treats the final "Submit" as a standard form submission with no Navigate Action specification.

**Why it happens:** LLMs treat "submit form" as a universal pattern equivalent to Screen Flow's Finish element or web form POST. They do not flag Navigate Action as a distinct OmniScript structural requirement.

**Correct pattern:**
```
Final Step: Summary & Submit
- Post-Step action: Integration Procedure (CreateClaimIP)
- Navigate Action: Type = Navigate to Record, Target = {ClaimId} returned by IP
```

**Detection hint:** If the requirements document's final step ends with "user submits the form" or "data is saved" without specifying a Navigate Action element, this anti-pattern is present.

---

## Anti-Pattern 3: Specifying DataRaptor for External API Calls

**What the LLM generates:** Requirements that say "use a DataRaptor to call the external billing API" or "DataRaptor Transform to send data to the ERP."

**Why it happens:** LLMs treat DataRaptor as a generic data connector similar to an MuleSoft flow or Apex callout. They do not distinguish between DataRaptor (SOQL/DML-based, no HTTP callout capability) and Integration Procedure (HTTP callout via HTTP Action or Remote Action element).

**Correct pattern:**
```
External API calls require an Integration Procedure with an HTTP Action element (or Remote Action calling an Apex class).
DataRaptors support: SOQL queries, Salesforce DML inserts/updates, field transformations.
DataRaptors do NOT support: external HTTP callouts, multi-system orchestration, conditional branching.
```

**Detection hint:** Any requirements note that says "DataRaptor calls [external system]" — DataRaptors cannot make HTTP callouts.

---

## Anti-Pattern 4: Recommending OmniScript Without License Check

**What the LLM generates:** An OmniScript requirements document without any mention of license requirements, assuming OmniScript is available in all Salesforce orgs.

**Why it happens:** LLMs do not consistently model Salesforce's license-per-feature access model. OmniStudio sounds like a standard platform feature but requires a specific cloud license (Health Cloud, FSC, Manufacturing Cloud, etc.) not included in core Sales/Service Cloud.

**Correct pattern:**
```
Requirements document header must include:
- OmniStudio license: Confirmed [Health Cloud / Manufacturing Cloud / etc.]
- Org runtime: Standard Runtime (Spring '25+) / Package Runtime (VBT managed package)
```

**Detection hint:** Requirements document has no license or runtime type in the header.

---

## Anti-Pattern 5: Specifying Field-Level Conditions Instead of Block-Level Conditions

**What the LLM generates:** Requirements that list individual field conditions: "Show VehicleYear field if LossType == Auto; show PropertyAddress field if LossType == Property" — implying per-field visibility control.

**Why it happens:** Per-field visibility conditions are standard in HTML form design, standard Flow, and most UI frameworks. LLMs default to this pattern because it is the most common mental model for conditional form fields.

**Correct pattern:**
```
OmniScript Conditional Views are set on Block container elements, not individual fields.
All fields that share a condition must be grouped inside a named Block.
Block: AutoBlock
  Conditional View: %LossType:value% == 'Auto'
  Contains: VehicleYear, VehicleMake, VehicleVIN
Block: PropertyBlock
  Conditional View: %LossType:value% == 'Property'
  Contains: PropertyAddress, StructureType, SquareFootage
```

**Detection hint:** Requirements list individual field conditions in a flat format without Block grouping notation.
