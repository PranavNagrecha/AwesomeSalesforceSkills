# LLM Anti-Patterns — OmniStudio vs Standard Architecture

Common mistakes AI coding assistants make when advising on OmniStudio vs standard platform architecture decisions. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending OmniStudio for Any Multi-Step Guided UI Without Checking License Entitlement

**What the LLM generates:** A multi-step guided UI requirement is described. The LLM immediately recommends OmniScript and Integration Procedure without asking about or confirming the org's license. The recommendation includes OmniStudio designer setup steps, component scaffolding, and deployment instructions.

**Why it happens:** LLMs associate "multi-step guided UI" with OmniStudio because OmniStudio is frequently discussed alongside this use case in Salesforce training content. The license gate is a business constraint that does not appear in technical code patterns, so LLMs omit it.

**Correct pattern:**

```
Step 1: Confirm org license entitlement.
- Check Setup > Company Information > Licenses for a qualifying Industries cloud license
  (Financial Services Cloud, Health Cloud, Manufacturing Cloud, Nonprofit Cloud, or Education Cloud).
- If no qualifying license is present, OmniStudio is unavailable.
  Recommend Screen Flow + LWC instead. Do not proceed with OmniStudio design.
Step 2: Only after license is confirmed, evaluate use case complexity
  against the tooling continuum.
```

**Detection hint:** If the recommendation mentions OmniScript, FlexCards, or Integration Procedures without first confirming the license, flag it.

---

## Anti-Pattern 2: Ignoring the Vlocity Managed Package vs Standard Runtime Distinction

**What the LLM generates:** An OmniStudio architecture recommendation that treats all OmniStudio deployments as interchangeable. The LLM recommends Standard Runtime deployment patterns (Salesforce CLI, standard metadata types) to an org that is actually running the Vlocity managed package, without acknowledging the coexistence problem or migration requirement.

**Why it happens:** LLMs are trained on a mix of Vlocity, managed-package-era, and Standard Runtime documentation. They conflate the deployment models because the capability descriptions are similar. The namespace and metadata type differences are tooling-level details that LLMs frequently omit.

**Correct pattern:**

```
Before recommending OmniStudio deployment approach:
1. Determine the org's current OmniStudio runtime:
   - Vlocity managed package (vlocity_ins__ namespace)
   - Salesforce managed package (industries__ namespace)
   - Standard Runtime (no namespace, natively embedded)
   - None
2. If Vlocity or Salesforce managed package:
   - Do NOT recommend Standard Runtime tooling without a migration assessment.
   - Assess migration scope using the OmniStudio Conversion Tool.
   - Document managed package as legacy path with migration debt.
3. If Standard Runtime or none:
   - Recommend Standard Runtime for all new development.
```

**Detection hint:** If the recommendation uses both managed-package metadata type names and Standard Runtime deployment tooling in the same design, flag it as a mixed-runtime anti-pattern.

---

## Anti-Pattern 3: Conflating Industries Cloud Name With Full OmniStudio Entitlement

**What the LLM generates:** The org is described as having "Financial Services Cloud" or "Health Cloud." The LLM immediately confirms OmniStudio is available and proceeds with full capability design — including advanced Integration Procedure HTTP actions, FlexCard entitlements, and OmniScript step counts — without noting that the specific edition may have restricted entitlements.

**Why it happens:** LLMs learn that OmniStudio is bundled with FSC and Health Cloud from documentation. They do not distinguish between editions (Starter, Growth, Enterprise) or acknowledge that entitlements vary by edition. The nuance of "FSC Starter may not include full OmniStudio" is not consistently present in training data.

**Correct pattern:**

```
License confirmation is two-level:
1. Confirm the Industries cloud license is present (cloud name).
2. Confirm the specific edition and OmniStudio entitlement level
   against the current Salesforce pricing and packaging documentation.
Do not assume full OmniStudio entitlement from the cloud name alone.
If entitlement is uncertain, recommend opening a Salesforce case or
reviewing the org's order form.
```

**Detection hint:** If the response confirms OmniStudio availability based solely on the cloud name without noting edition-level entitlement verification, flag it.

---

## Anti-Pattern 4: Recommending Screen Flow When Declarative HTTP Callout Orchestration Is Required

**What the LLM generates:** A use case requires declarative HTTP callout sequencing to external REST APIs, parallel data fetch from multiple endpoints, and conditional response handling — all within a guided UI step. The LLM recommends Screen Flow with custom Apex for the callout logic, without noting that OmniStudio Integration Procedures handle this declaratively with parallel branch support and built-in caching.

**Why it happens:** LLMs default to the more commonly described Screen Flow + Apex pattern for callout handling because Apex callouts are extensively documented. Integration Procedure HTTP actions are a more specialized capability. LLMs also know Screen Flow is the safe recommendation when license status is uncertain.

**Correct pattern:**

```
When the use case requires declarative HTTP callout sequencing:
- OmniStudio Integration Procedures support HTTP Action elements that call
  external REST endpoints declaratively, without Apex.
- Integration Procedures support parallel HTTP branches, built-in caching,
  and conditional element chaining.
- Screen Flow requires Apex for external callouts — this adds code, governor
  limit management, and async handling complexity.
If the org is Industries-licensed and callout orchestration complexity is high,
OmniStudio Integration Procedure is the correct recommendation, not Apex.
```

**Detection hint:** If the recommendation uses Apex for external callout orchestration in an Industries-licensed org where the use case has multiple parallel callout requirements, flag it — Integration Procedures may be superior.

---

## Anti-Pattern 5: Recommending OmniStudio for Automation-Only Requirements

**What the LLM generates:** A requirement is described as needing complex multi-step processing or data transformation with no user-facing UI. The LLM recommends OmniScript because the requirement involves "multiple steps." The design includes an OmniScript with no screen steps used purely for data processing logic.

**Why it happens:** LLMs pattern-match on "multiple steps" and "complex processing" and associate it with OmniStudio. They do not distinguish between guided UI requirements (OmniScript's primary use case) and background automation requirements (Flow, Apex, Integration Procedure standalone invocation).

**Correct pattern:**

```
OmniScript is a guided UI tool. It is not appropriate for automation-only requirements.
For automation-only requirements (no guided UI):
- Screen Flow (scheduled, autolaunched, or record-triggered) for declarative automation.
- Apex for complex logic, governor limit management, or platform events.
- Integration Procedure can be invoked standalone (without OmniScript) if the org
  is Industries-licensed and the use case requires declarative HTTP orchestration
  at the automation layer.
Do not recommend OmniScript for use cases that have no user-facing UI component.
```

**Detection hint:** If the recommendation uses OmniScript for a use case described as automated processing or background data transformation with no user interaction, flag it.

---

## Anti-Pattern 6: Omitting the Architecture Decision Record From the Output

**What the LLM generates:** An OmniStudio vs standard platform recommendation is produced as a verbal opinion ("you should use OmniStudio here because it handles multi-source data better"). No decision documentation is produced, no trade-offs are recorded, and no stakeholder sign-off step is included.

**Why it happens:** LLMs optimize for direct answers. Architecture decision documentation is process overhead that the LLM omits unless explicitly requested. For OmniStudio decisions specifically — which have licensing, training, and migration implications — undocumented decisions are routinely relitigated when team composition changes.

**Correct pattern:**

```
Every OmniStudio vs standard architecture decision should produce:
1. Explicit rationale covering: license status, use case continuum mapping,
   team skills assessment, and runtime path selection.
2. A documented Architecture Decision Record (ADR) using the
   templates/omnistudio-vs-standard-architecture-template.md template.
3. A stakeholder sign-off step before build work begins.
A verbal recommendation without documentation is incomplete output for this skill.
```

**Detection hint:** If the output is a recommendation without a documented rationale and ADR, flag it as incomplete.
