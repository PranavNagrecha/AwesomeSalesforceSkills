# LLM Anti-Patterns — OmniStudio vs Standard Decision

Common mistakes AI coding assistants make when advising on OmniStudio vs standard tooling decisions.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending OmniStudio for a Simple Single-Object Screen Flow

**What the LLM generates:** "Use OmniScript for your guided troubleshooting wizard — it provides a better step-based UI experience than Screen Flow." (Stated without asking about license or use case complexity.)

**Why it happens:** LLMs trained on Salesforce content see OmniStudio positioned as a premium guided-UI tool and pattern-match to recommend it for any multi-step UI scenario. Training data rarely includes the license availability constraint as a disqualifying factor.

**Correct pattern:**

```
1. Confirm whether the org holds an Industries Cloud license.
2. Assess whether the use case spans 3+ objects or requires external callouts.
3. If single-object or two-object with no external callouts: recommend Screen Flow + LWC.
4. OmniStudio adds complexity that is not justified for simple scenarios even when licensed.
```

**Detection hint:** Look for OmniStudio recommendations that do not mention license verification, or that apply to scenarios involving one or two Salesforce objects with no external data sources.

---

## Anti-Pattern 2: Assuming OmniStudio Is Available in All Salesforce Orgs

**What the LLM generates:** "You can use Integration Procedures to handle this callout — they're available in your org." (No license check performed or mentioned.)

**Why it happens:** OmniStudio is heavily documented on developer.salesforce.com and help.salesforce.com without always prominently surfacing the license requirement. LLMs absorb the capability documentation without the licensing constraint.

**Correct pattern:**

```
Before recommending any OmniStudio component (OmniScript, FlexCard, 
Integration Procedure, DataRaptor), confirm:
- Setup > Company Information > Licenses shows an Industries Cloud license
  (FSC, Health Cloud, Manufacturing Cloud, Nonprofit Cloud, or Education Cloud)
If the license is not present, standard tooling is the only valid option.
```

**Detection hint:** Any OmniStudio recommendation that does not reference license verification as the first step is suspect. Flag recommendations made for Sales Cloud or Service Cloud orgs without explicit license confirmation.

---

## Anti-Pattern 3: Treating Managed Package and Standard Designers as Equivalent

**What the LLM generates:** "Upgrade your OmniScript to use Standard Designers by just redeploying the component without the namespace prefix." Or: "You can use the Standard Designers tooling in your existing managed-package org without any migration steps."

**Why it happens:** LLMs conflate the two OmniStudio deployment models because the marketing documentation presents them as versions of the same product. The architectural distinction between managed-package (namespace-prefixed, package-managed) and Standard Designers (native platform LWC) is underrepresented in training data.

**Correct pattern:**

```
- Identify the org's current state: managed package (vlocity_ins__ or industries__ 
  namespace) vs Standard Designers (no OmniStudio namespace prefix).
- Migration from managed package to Standard Designers requires the Salesforce 
  OmniStudio Conversion Tool and is a structured project, not a simple redeploy.
- Do not mix the two models without a documented migration plan.
```

**Detection hint:** Look for advice that treats namespace removal as a trivial step, or that suggests Standard Designers components can be added to a managed-package org without migration planning.

---

## Anti-Pattern 4: Conflating vlocity_ins__ and industries__ Namespaces

**What the LLM generates:** SOQL or Apex code that references `vlocity_ins__OmniScript__c` in an org that uses the `industries__` namespace, or vice versa.

**Why it happens:** Both namespaces refer to OmniStudio managed package variants. Training data includes examples from both, and LLMs do not reliably distinguish which namespace is active in a given org context.

**Correct pattern:**

```apex
// Before writing any SOQL or Apex referencing OmniStudio fields,
// confirm the active namespace by checking installed packages:
// Setup > Installed Packages
// Legacy Vlocity:    vlocity_ins__
// Salesforce-packaged: industries__
// Standard Designers: no OmniStudio prefix

// Dynamic namespace detection example:
Map<String, Schema.SObjectType> gd = Schema.getGlobalDescribe();
Boolean hasVlocity = gd.containsKey('vlocity_ins__OmniScript__c');
Boolean hasIndustries = gd.containsKey('industries__OmniScript__c');
```

**Detection hint:** SOQL queries or field references using `vlocity_ins__` or `industries__` without confirming which namespace is active in the target org.

---

## Anti-Pattern 5: Ignoring Team Skills in the Recommendation

**What the LLM generates:** "OmniStudio is the right choice for this complex guided UI — it handles multi-source data natively." (No mention of team readiness or ramp time.)

**Why it happens:** Capability-fit analysis is well-represented in training data. Team skills assessment is a consulting practice consideration that is underrepresented in technical documentation. LLMs optimize for technical correctness and underweight organizational readiness factors.

**Correct pattern:**

```
Decision factors for OmniStudio adoption:
1. License available? (gate — required)
2. Use case complexity justifies OmniStudio? (3+ objects, external callouts)
3. Team has OmniStudio expertise, or timeline allows for ramp?
   - If no expertise and tight timeline: standard tooling even if licensed and complex
   - OmniStudio has its own designer tools, runtime, and data model
   - Estimate 2-4 weeks ramp for a developer new to OmniStudio
4. Long-term maintainability: who will own the components post-launch?
```

**Detection hint:** OmniStudio recommendations that do not mention team skills, training time, or long-term maintainability. Flag recommendations made for teams described as "standard Salesforce admins" or "junior developers" without noting the OmniStudio learning curve.

---

## Anti-Pattern 6: Recommending Managed Package in New Implementations

**What the LLM generates:** "Install the OmniStudio managed package from the AppExchange to get started with OmniScript in your new FSC org."

**Why it happens:** A significant portion of OmniStudio documentation and community content predates Standard Designers (which became generally available in Spring '25). The managed package was the only path for years and remains heavily represented in training data.

**Correct pattern:**

```
For new org implementations (Spring '25+):
- Use Standard Designers (on-platform, native LWC)
- Do NOT install the managed package for new implementations
- Standard Designers is the Salesforce-recommended forward path
- Managed package is a legacy path for existing orgs with migration debt

Source: https://developer.salesforce.com/blogs/2024/omnistudio-standard-designers
```

**Detection hint:** Recommendations to install the OmniStudio AppExchange package for new org implementations when the customer is on Spring '25 or later.
