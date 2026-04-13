# Examples — OmniStudio vs Standard Architecture

## Example 1: Financial Services Cloud Org — Multi-Step Onboarding Wizard

**Context:** A Financial Services Cloud org needs a guided client onboarding wizard that collects data across Account, Contact, Financial Account, and an external KYC (Know Your Customer) REST API. The team includes two certified OmniStudio developers.

**Problem:** The architecture team initially proposed Screen Flow. The design called for three external Apex callouts, five Get Records elements, and four custom LWC components for complex display. The flow grew to 47 elements in design review and the team flagged maintainability concerns.

**Solution:**

The architect mapped the use case to the tooling continuum:
- 4 Salesforce objects → exceeds simple Screen Flow territory
- External REST callout to KYC API → Integration Procedure HTTP Action is declarative; Apex equivalent requires async patterns and governor limit management
- Team holds OmniStudio certification → ramp cost is zero
- Org holds FSC license (confirmed in Setup > Company Information > Licenses) → license gate satisfied

Recommendation: OmniStudio Standard Runtime.

Design:
1. Integration Procedure with parallel HTTP branches: one for Salesforce object retrieval (Account + Contact), one for KYC API callout. Built-in caching on the Account branch.
2. OmniScript with four steps (Personal Details, Financial Profile, KYC Verification, Review & Submit) using the Integration Procedure as data source.
3. FlexCards on the Account record page for post-onboarding summary display.
4. Deployed via Salesforce CLI using standard metadata API — no managed package tooling.

**Why it works:** The use case crosses both key thresholds: multi-source Salesforce objects AND external callout sequencing. OmniStudio Integration Procedures handle both declaratively with parallel branch support. The Screen Flow equivalent would require custom Apex with async callout patterns, pushing the solution into higher complexity without the declarative maintenance benefit.

---

## Example 2: Sales Cloud Org — Requesting OmniStudio for a Guided Quote Form

**Context:** A Sales Cloud org (no Industries license) requests an OmniStudio-based guided quote form after seeing OmniStudio demos in a Salesforce conference session.

**Problem:** The solution architect was asked to design an OmniScript-based guided quoting UI. The org holds only Sales Cloud Enterprise edition — no FSC, Health Cloud, or other Industries license. The development team began designing OmniStudio components before license entitlement was confirmed.

**Solution:**

License gate check:
- Setup > Company Information > Licenses — no Industries cloud license present.
- OmniStudio is unavailable. This is not a configuration gap; it is a licensing restriction.

Architecture decision:
- The guided quoting requirement involves 2 objects (Opportunity, Quote) and no external callouts.
- Mapping to the continuum: Screen Flow handles 2-object guided processes adequately.
- Recommendation: Screen Flow with 3 steps (Quote Details, Line Items, Review & Submit) + LWC for the line item entry component.

ADR filed noting: OmniStudio evaluated, license gate not satisfied, Screen Flow selected as appropriate for complexity level.

**Why it works:** The license gate is non-negotiable. The early ADR documentation prevented weeks of OmniStudio design work that would have failed at deployment. The continuum mapping also showed that Screen Flow was the correct tool for this complexity level even if the org had held an Industries license — 2 objects and no external callouts do not justify OmniStudio overhead.

---

## Example 3: Existing Vlocity Managed Package — Evaluating New OmniStudio Components

**Context:** A Health Cloud org has been running OmniStudio on the Vlocity managed package (`vlocity_ins__` namespace) since 2021. A new project wants to add five new OmniScript wizards for a patient intake use case.

**Problem:** The project team assumed they could build the new OmniScripts using Standard Runtime tooling (Salesforce CLI, standard metadata) while the existing components remain on the Vlocity package. The CI/CD pipeline was designed around the Standard Runtime model.

**Solution:**

Architecture assessment:
1. The org is running the Vlocity managed package — not Standard Runtime.
2. New OmniScript components built with Standard Runtime tooling cannot coexist with managed-package components in all configurations without migration.
3. Adding five new OmniScripts on the managed package deepens migration debt.

Recommended path:
- Scope a managed-package-to-Standard-Runtime migration using Salesforce's OmniStudio Conversion Tool before starting new development.
- Build the five new patient intake wizards on Standard Runtime after migration.
- If migration scope is too large for the current project timeline, build the new wizards on the managed package as a known interim debt and include a migration backlog item with sizing.

ADR filed: migration debt acknowledged, interim path selected, migration backlog item created with scope estimate.

**Why it works:** Explicitly surfacing the migration debt as an architectural decision prevents the split-runtime state that breaks deployment pipelines. The interim path is documented as debt, not as the target architecture — this keeps the forward path clear.

---

## Anti-Pattern: Recommending OmniStudio for Any Multi-Step UI Without License Check

**What practitioners do:** A stakeholder requests a "multi-step guided wizard," and the architect immediately proposes OmniStudio based on the UI pattern match, without confirming the org's license entitlement.

**What goes wrong:** Design work proceeds for 2–4 weeks. At the first deployment attempt to a sandbox, OmniStudio components fail because the org does not hold an Industries license. The team must reverse the design and rebuild in Screen Flow, losing weeks of work.

**Correct approach:** License gate is the first and mandatory check. Confirm entitlement in Setup > Company Information > Licenses before any OmniStudio capability discussion. If the license is not present, the decision is already made.
