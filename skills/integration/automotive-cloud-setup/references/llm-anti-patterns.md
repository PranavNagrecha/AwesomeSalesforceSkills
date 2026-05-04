# LLM Anti-Patterns — Automotive Cloud Setup

Common mistakes AI coding assistants make when generating or advising on Automotive Cloud Setup.
These patterns help the consuming agent self-check its own output.

## Pattern 1: Suggesting Custom `Vehicle__c` Without Checking Standard `Vehicle`

**What the LLM generates:** A custom-object data model with `Vehicle__c`, `Vehicle_Definition__c`, fields for VIN, MSRP, Make, Model.

**Why it happens:** Standard Industries-cloud objects are not heavily represented in pretrained Salesforce content. LLMs default to generic Sales-Cloud reasoning ("the user has a custom data model — define custom objects").

**Correct pattern:** When the org has Automotive Cloud licensed, use standard `Vehicle` and `VehicleDefinition`. Only create custom objects for org-specific extensions that the standard model does not cover.

**Detection hint:** Any answer that defines `Vehicle__c` without first asking "do you have Automotive Cloud licensed?" is suspect. Scan generated metadata for `Vehicle__c.object-meta.xml` — flag for review.

---

## Pattern 2: Putting Per-VIN State on `VehicleDefinition`

**What the LLM generates:** A `VehicleDefinition` record with `Mileage__c`, `CurrentOwnerId__c`, `LastServiceDate__c` fields.

**Why it happens:** The model/template vs. instance distinction is non-obvious from the object names alone. LLMs flatten the data model into one object when given a single example.

**Correct pattern:** `VehicleDefinition` holds spec/template attributes (one per build); `Vehicle` holds per-VIN state (mileage, owner, service history). Mileage on the definition would mean every VIN of that build had identical mileage.

**Detection hint:** Search generated field definitions for ownership / state fields on `VehicleDefinition`. Any dynamic per-instance field is misplaced.

---

## Pattern 3: Modeling Multi-Franchise Dealer with `ParentId`

**What the LLM generates:** Dealer Account with `ParentId` pointing at the OEM Account, with a comment "use ParentAccount for the OEM relationship."

**Why it happens:** `ParentId` is the well-known Salesforce account-hierarchy pattern. LLMs reach for it before considering whether multi-franchise scenarios exist.

**Correct pattern:** Use `AccountAccountRelation` with role `Franchisee` and effective dates. A dealer that sells two OEMs has two relation records, not two `ParentId` values.

**Detection hint:** Any Apex / Flow that filters dealers by `ParentId = :oemId` is suspect. Replace with subquery on `AccountAccountRelation`.

---

## Pattern 4: Direct DML on `ActionableEventOrchestration.Status`

**What the LLM generates:**

```apex
ActionableEventOrchestration o = [SELECT Id, Status FROM ActionableEventOrchestration WHERE Id = :orchId];
o.Status = 'Completed';
update o;
```

**Why it happens:** LLMs treat orchestration objects as plain SObjects and reach for DML. The orchestration engine's invocable-action pattern is not in the typical Apex pretrained corpus.

**Correct pattern:** Drive state through `Invocable.Action.createCustomAction('standard', 'orchestrationActionName')` or the prebuilt orchestration invocable actions (Start, Advance, Complete). The invocable path performs side-effects that direct DML skips.

**Detection hint:** Any `update` statement on `ActionableEventOrchestration` is suspect. Replace with invocable-action call.

---

## Pattern 5: Loading Vehicles Before Definitions Without Dedup

**What the LLM generates:** A data-loader script that iterates the source CSV row-by-row, creating a `VehicleDefinition` and `Vehicle` per row.

**Why it happens:** Row-by-row insert is the simplest pattern and what LLMs default to for migration scripts.

**Correct pattern:** Two-pass load: dedup the source CSV into a definition table keyed on `(Make, Model, ModelYear, Trim)`, upsert `VehicleDefinition` records first, then upsert `Vehicle` records resolving `VehicleDefinitionId` via the dedup key.

**Detection hint:** Any data-load script that creates `VehicleDefinition` and `Vehicle` in the same loop iteration is producing definition explosion. Refactor to two-pass.
