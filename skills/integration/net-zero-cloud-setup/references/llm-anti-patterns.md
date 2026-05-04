# LLM Anti-Patterns — Net Zero Cloud Setup

Common mistakes AI coding assistants make when generating or advising on Net Zero Cloud Setup.
These patterns help the consuming agent self-check its own output.

## Pattern 1: Building Custom `Carbon_Footprint__c` Objects

**What the LLM generates:** A custom data model with `Carbon_Footprint__c`, `Emission_Factor__c`, `Activity_Data__c`.

**Why it happens:** The Net Zero Cloud standard objects (`StnryAssetCrbnFtprnt`, `Scope3CrbnFtprnt`, `EmssnFctr`) have terse SOQL-friendly names that LLMs don't recognize as standard. Defaults to custom-object generation.

**Correct pattern:** When the org has Net Zero Cloud licensed, use the standard objects. Custom objects only for org-specific extensions the standard model doesn't cover.

**Detection hint:** Any answer that defines `Carbon_Footprint__c` or similar without first asking "do you have Net Zero Cloud licensed?" is suspect.

---

## Pattern 2: Suggesting Real-Time Calculation Triggers

**What the LLM generates:** An Apex trigger on `StnryAssetEnrgyUse` that calls a calculation routine on insert/update to keep `StnryAssetCrbnFtprnt` real-time.

**Why it happens:** Trigger-based real-time updates are a familiar Sales-Cloud pattern. LLMs apply it without considering whether real-time is necessary.

**Correct pattern:** Use the DPE batch calculation. Activity data arrives in periodic feeds (utility bills, ERP exports). Real-time calc is unnecessary, consumes DPE quota, and undermines the audit-trail benefit of versioned batch runs.

**Detection hint:** Any Apex trigger on `…EnrgyUse` or `Scope3PcmtItem` that performs calculation is misplaced. Move logic into the DPE definition.

---

## Pattern 3: Loading All 15 Scope 3 Categories Without Materiality Screen

**What the LLM generates:** Setup runbook that loads all 15 Scope 3 categories as a single bulk operation.

**Why it happens:** "All 15 categories" is the canonical reference list; LLMs treat it as a checklist to satisfy rather than a menu to filter.

**Correct pattern:** Perform a structured materiality assessment first. Load only material categories with documented exclusion reasoning for the rest. Most orgs cover 4–6 of 15.

**Detection hint:** Any Net Zero Cloud rollout plan that loads all 15 categories without a materiality assessment step is over-scoping.

---

## Pattern 4: Hand-Editing Calculated Totals to Match External Data

**What the LLM generates:** Apex routine or Flow that updates `StnryAssetCrbnFtprnt.TotalCO2e` directly to match a supplier-provided figure.

**Why it happens:** Direct DML on calculated fields is a familiar pattern. The "calculated rows are owned by DPE" invariant is implicit and not in pretrained material.

**Correct pattern:** Corrections must happen at the activity-data layer (`StnryAssetEnrgyUse`) or factor layer (`EmssnFctr`). Direct edits to calculated rows are overwritten on the next DPE run and create audit-trail risk.

**Detection hint:** Any code that updates a `…CrbnFtprnt` field other than metadata fields (Description, Notes) is suspect.

---

## Pattern 5: Co-Mingling CSRD and TCFD in One Disclosure Pack

**What the LLM generates:** A single disclosure pack configuration that maps the same metrics to CSRD and TCFD targets.

**Why it happens:** Both frameworks reference Scope 1/2/3, so LLMs assume the metrics are interchangeable. They aren't — aggregation rules and reporting boundaries differ.

**Correct pattern:** One disclosure pack per framework. Each pack carries its framework-specific aggregation rules and reporting metric definitions.

**Detection hint:** Any disclosure-pack configuration that lists more than one framework target is over-merged. Split into separate packs.
