# LLM Anti-Patterns — OmniScript Flow Design Requirements

Common mistakes AI coding assistants make when generating or advising on OmniScript flow design requirements. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Conflating OmniScript Requirements with Screen Flow Requirements

**What the LLM generates:** A requirements document that uses Decision element notation, Fault path annotations, and generic "condition" branching markers borrowed from Screen Flow design patterns — without OmniScript-specific Conditional View JSON expressions or Block container groupings.

**Why it happens:** LLMs are trained on a much larger corpus of Screen Flow documentation and examples than OmniScript documentation. The structural differences between the two tools are not prominent enough in training data to override the default Screen Flow mental model.

**Correct pattern:**
```
Conditional branching in OmniScript uses the Conditional View property, usually on a Block
that groups the fields for one branch (it also works on Steps and most other elements):
- Block Name: AutoBlock
  - Conditional View: LossType equals 'Auto'
  - Elements: VehicleYear, VehicleMake, VehicleModel
- Block Name: PropertyBlock
  - Conditional View: LossType equals 'Property'
  - Elements: PropertyAddress, StructureType
(element, operator, value; the %Element:value% shorthand in older copies of this
skill is UNVERIFIED (2026-10-03) as literal designer syntax)
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

## Anti-Pattern 5: Repeating One Condition on Every Field Instead of Grouping Them

**What the LLM generates:** Requirements that list individual field conditions: "Show VehicleYear field if LossType == Auto; show PropertyAddress field if LossType == Property" — implying per-field visibility control.

**Why it happens:** Per-field visibility conditions are standard in HTML form design, standard Flow, and most UI frameworks. LLMs default to this pattern. The opposite error also appears: claiming OmniScript only supports conditions on Blocks. Trailhead says almost every element supports Conditional View, including Steps.

**Correct pattern:**
```
OmniScript Conditional Views can be set on almost any element, but fields that share
a condition belong in one named Block with one Conditional View.
Block: AutoBlock
  Conditional View: LossType equals 'Auto'
  Contains: VehicleYear, VehicleMake, VehicleVIN
Block: PropertyBlock
  Conditional View: LossType equals 'Property'
  Contains: PropertyAddress, StructureType, SquareFootage
A Step that only applies to one branch gets the condition on the Step itself.
```

**Detection hint:** Requirements list the same condition on several individual fields, or claim conditions cannot be set on Steps or fields.

---

## Anti-Pattern 6: Naming Screen Fields Without Matching the Data Contract

**What the LLM generates:** A screen inventory with friendly names ("Account Phone", "Web Address") and a separate data section that says "IP returns the account record", with no mapping between the two.

**Why it happens:** LLMs treat labels and API names as interchangeable. In OmniScript the parser fills inputs by matching JSON node names to element names, and fields appear empty when they differ (Trailhead, "Configure a Simple OmniScript").

**Correct pattern:**
```
| Step        | Element name | Label        | JSON node from IPGetAccountDetails | Read/Write |
|-------------|--------------|--------------|------------------------------------|------------|
| StepAccount | AccountName  | Account Name | AccountName                        | Read only  |
| StepAccount | Phone        | Phone        | Phone                              | Write      |
| StepAccount | Website      | Website      | Website                            | Write      |
```

**Detection hint:** A requirements document with screen fields but no element-name column, or element names that never appear in the data-source section.

---

## Anti-Pattern 7: Writing Cross-Step Rules as Required Fields

**What the LLM generates:** "Mobile Phone (Step 1) is required when SMS Alerts (Step 4) is checked", listed in the field table as a required flag.

**Why it happens:** LLMs map every conditional requirement to the field's Required property. Required fields and formula messaging only guard the current Step (Trailhead, "Validate Data and Handle Errors").

**Correct pattern:**
```
Cross-step rule CR-01
  Trigger:            SmsAlerts = true on StepPreferences
  Check:              MobilePhone is blank (collected on StepContact)
  Element:            Set Errors, placed after StepPreferences
  Element Error Map:  MobilePhone
  Value:              "Add a mobile number to receive text alerts."
  Conditional View:   SmsAlerts equals true AND MobilePhone is blank
```

**Detection hint:** A Required flag whose condition references a field from a different Step.
