# LLM Anti-Patterns — Org Edition and Feature Licensing

## Anti-Pattern 1: Assuming All Features Are Available in Enterprise Edition

**What the LLM generates:** Solution designs or instructions that use Agentforce, Einstein Copilot, Salesforce Shield, or CRM Analytics without noting that these require add-on licenses even in Enterprise or Unlimited Edition.

**Why it happens:** LLMs conflate "Enterprise Edition is the full platform" with "all features are available in Enterprise." Many premium features are add-ons regardless of base edition.

**Correct pattern:** Before specifying any AI, encryption, analytics, or agent feature in a design, state the required add-on license. Document: "This solution requires the [Add-on Name] license in addition to the base Enterprise Edition." Do not assume add-ons are included.

**Detection hint:** Any solution design that references Agentforce, Einstein Copilot, Shield encryption, or CRM Analytics without a licensing note.

---

## Anti-Pattern 2: Recommending Apex for Professional Edition Orgs

**What the LLM generates:** Apex trigger or Apex class code for a customer on Professional Edition.

**Why it happens:** LLMs default to Apex as the solution for complex business logic without checking the org edition. Professional Edition does not support Apex triggers or classes.

**Correct pattern:** Before recommending Apex, confirm the customer's edition. For Professional Edition orgs, propose declarative alternatives (Flow, Validation Rules, Duplicate Rules). If the requirement genuinely requires Apex, recommend an Enterprise Edition upgrade and document the decision.

**Detection hint:** Any Apex code recommendation for a customer confirmed to be on Professional or Essentials Edition.

---

## Anti-Pattern 3: Treating Developer Edition as Representative of Customer Editions

**What the LLM generates:** Instructions like "test this in a Developer Edition org to verify it works."

**Why it happens:** Developer Edition is free and accessible, so LLMs recommend it generically. But DE has Enterprise-equivalent features and is not representative of Professional, Essential, or even standard Enterprise configurations.

**Correct pattern:** Test against an org edition that matches the customer's. For Professional Edition customers, use a Professional Edition Developer Sandbox or a scratch org configured with the appropriate edition in the scratch org definition file. Note clearly when a solution has only been tested in Developer Edition.

**Detection hint:** Any test instruction that recommends "try this in a Developer Edition" without noting that DE has Enterprise features not available in the customer's edition.

---

## Anti-Pattern 4: Using Stale Edition Comparison Data

**What the LLM generates:** Specific claims about what is included in which edition (e.g., "Flow Orchestration is only available in Unlimited Edition") that were accurate at a prior release but have since changed.

**Why it happens:** LLMs are trained on documentation that was accurate at training time. Salesforce changes edition inclusions with each release. Knowledge cutoff issues compound this.

**Correct pattern:** Always qualify edition-specific claims with: "as of [release]; verify at the current Salesforce edition comparison page." Direct users to https://www.salesforce.com/editions-pricing/overview/ for authoritative current information. Never present edition availability as static fact.

**Detection hint:** Any absolute claim about "Feature X is included in Edition Y" without a date qualifier or a recommendation to verify on the official pricing page.

---

## Anti-Pattern 5: Ignoring Permission Set License Assignment Step

**What the LLM generates:** Instructions to enable an add-on feature at the org level (Setup > Feature Settings > Enable) without also providing the step to assign the Permission Set License to individual users.

**Why it happens:** LLMs describe the org-level enable toggle and assume that is sufficient. For PSL-gated features, per-user assignment is a separate required step.

**Correct pattern:** For any add-on feature that uses Permission Set Licenses, document both steps: (1) enable at org level in Setup, and (2) assign the PSL to individual users via Setup > Users > [User] > Permission Set License Assignments. Without step 2, the feature will appear enabled in Setup but will not work for individual users, generating confusing "feature not available" errors.

**Detection hint:** Any instruction to enable an add-on feature that only covers the org-level toggle without mentioning per-user PSL assignment.
