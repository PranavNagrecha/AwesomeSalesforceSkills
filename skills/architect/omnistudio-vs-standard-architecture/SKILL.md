---
name: omnistudio-vs-standard-architecture
description: "Architecture decision framework for choosing between OmniStudio and the standard Salesforce platform (Screen Flow, LWC, Apex) for guided UI and data orchestration use cases. Covers the license gate, the Dynamic Forms → Screen Flow → OmniStudio continuum, Standard Runtime vs Vlocity managed package migration debt, and team skill considerations. NOT for implementation. NOT for OmniScript development or FlexCard configuration."
category: architect
salesforce-version: "Spring '26+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "Should we use OmniStudio or Screen Flow for this guided wizard"
  - "evaluating OmniStudio license cost vs standard platform for our org"
  - "client wants OmniStudio but we don't have an Industries license"
  - "deciding between OmniStudio Standard Runtime and the Vlocity managed package"
  - "is OmniStudio right for our team if we don't have certified developers"
tags:
  - omnistudio
  - screen-flow
  - lwc
  - decision-framework
  - industries
  - architecture
  - standard-runtime
  - vlocity
inputs:
  - "Org license profile: which Salesforce Industries cloud (FSC, Health Cloud, Manufacturing Cloud, Nonprofit Cloud, Education Cloud) is held, if any"
  - "Use case description: number of steps, objects, external callouts, and branching complexity"
  - "Team skills profile: OmniStudio-certified developers available or not"
  - "Existing OmniStudio deployment state: Vlocity managed package, Salesforce managed package, Standard Runtime, or none"
  - "Timeline and long-term maintenance owner"
outputs:
  - "Architecture decision recommendation with rationale covering license, complexity, team, and runtime path"
  - "Tooling continuum mapping for the specific use case"
  - "Standard Runtime vs Vlocity managed package risk assessment if OmniStudio is already in use"
  - "Documented architecture decision record (ADR) draft"
dependencies:
  - omnistudio-vs-standard-decision
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-13
---

# OmniStudio vs Standard Platform Architecture

This skill activates when an architect or senior practitioner needs to make or document a technology selection decision between OmniStudio (OmniScript, FlexCards, Integration Procedures) and the standard Salesforce platform (Screen Flow, LWC, Apex) for a guided UI or data orchestration requirement. It covers the full architecture decision — license gate, capability continuum, runtime path selection, team readiness, and decision documentation.

---

## Before Starting

Gather this context before working on anything in this domain:

- **License gate first:** OmniStudio is bundled exclusively with Salesforce Industries clouds. If the org does not hold a qualifying Industries license (Financial Services Cloud, Health Cloud, Manufacturing Cloud, Nonprofit Cloud, or Education Cloud), OmniStudio is not available — the architecture decision is already made. Confirm entitlement in Setup > Company Information > Licenses before any further analysis.
- **Runtime path:** If the org already uses OmniStudio, determine whether it runs the Vlocity managed package (`vlocity_ins__` namespace), the Salesforce managed package (`industries__` namespace), or the Standard Runtime (no namespace, natively embedded). These are architecturally distinct and not interchangeable without a migration project.
- **Complexity threshold:** The core question is whether the use case crosses the threshold where OmniStudio's declarative multi-source orchestration pays off. Simple single-object guided forms never do. Complex multi-step wizards with HTTP callout sequencing almost always do — if licensed.
- **Team ramp cost:** OmniStudio has its own designer tools, data model, and runtime. A team without OmniStudio experience will spend weeks ramping. Factor this into the recommendation.

---

## Core Concepts

### The Tooling Continuum

Salesforce Architects position guided UI tooling on a continuum from least-code to full-code:

1. **Dynamic Forms / Dynamic Actions** — declarative field and action visibility on record pages. Zero code. Appropriate for simple conditional field display on a single object.
2. **Screen Flow** — declarative multi-step guided processes. No Apex required for simple scenarios. Supports Get/Update Records natively. Best for 1–2 object scenarios with limited branching.
3. **Screen Flow + LWC** — Screen Flow for orchestration, LWC for complex display logic or reusable UI components. Appropriate for moderately complex guided processes without external callout requirements.
4. **OmniScript + Integration Procedure** — declarative multi-step UI with multi-source data orchestration, built-in HTTP callout sequencing, and cross-channel deployment (LWC, Communities, Mobile). Appropriate for complex scenarios — multiple related objects, external REST callouts, parallel data fetch — when the org is Industries-licensed.
5. **LWC + Apex** — full code. Maximum flexibility. Highest build and maintenance cost. Reserve for requirements that no declarative tool can satisfy.

The Salesforce Architects Building Forms decision guide maps these options explicitly. The decision is not binary OmniStudio vs Flow — it is a continuum where complexity and license availability determine the correct entry point.

Source: https://architect.salesforce.com/design/decision-guides/build-forms

### License Gate

OmniStudio is not a separate purchasable add-on for Sales Cloud or Service Cloud. It is bundled with Industries cloud licenses: Financial Services Cloud (FSC), Health Cloud, Manufacturing Cloud, Nonprofit Cloud, and Education Cloud. Without one of these licenses, OmniStudio components will fail at runtime — this is not a configuration gap, it is a licensing restriction enforced by Salesforce.

Confirming license entitlement is the first and non-negotiable step in any architecture decision involving OmniStudio. Do not proceed to capability evaluation before confirming the license is held.

Caution: not all Industries cloud editions include OmniStudio at the same level. Some starter or limited editions may have restricted OmniStudio entitlements. Validate the specific edition against the Salesforce pricing and packaging documentation for the relevant cloud.

Source: https://help.salesforce.com/s/articleView?id=sf.os_omnistudio_overview.htm

### Standard Runtime vs Vlocity Managed Package

OmniStudio has two deployment models with significant architectural implications:

**Vlocity managed package (legacy):** Delivered as a managed package using either the `vlocity_ins__` namespace (original Vlocity acquisition package) or the `industries__` namespace (post-acquisition Salesforce repackaging). Components use namespace-prefixed fields, Apex classes, and metadata types. This path carries strategic migration debt — Salesforce has directed all new investment to Standard Runtime since Spring '25 and is not extending the managed package path.

**Standard Runtime (current):** Natively embedded in the Salesforce platform as of Spring '25. Uses standard LWC runtime with no managed package and no namespace prefix. Metadata-based, fully supported in the Salesforce CLI and Metadata API. This is the path Salesforce is investing in. All new OmniStudio development should target Standard Runtime.

Migration from managed package to Standard Runtime is a real, scoped project. It requires Salesforce's OmniStudio Conversion Tool and cannot be done component by component in all configurations. Orgs running managed-package OmniStudio are accumulating migration debt with every new component they build on the legacy runtime.

Source: https://developer.salesforce.com/blogs/2026/03/omnistudio-standard-runtime

### When OmniStudio Wins

OmniStudio (Standard Runtime) is the right choice when all three of the following are true:

1. The org holds a qualifying Industries cloud license.
2. The use case requires multi-step guided UI that spans multiple related Salesforce objects AND/OR external REST callout sequencing in a declarative model.
3. The team has (or can acquire) OmniStudio expertise within the project timeline.

OmniStudio Integration Procedures are specifically superior for declarative HTTP callout sequencing — they support parallel HTTP branches, built-in caching, and conditional element chaining without writing Apex. This is the primary capability gap that Screen Flow cannot close without Apex.

### When Standard Platform Wins

Screen Flow + LWC (+ Apex if needed) is the correct choice when any of the following is true:

- The org does not hold a qualifying Industries cloud license.
- The use case is single-object or involves only two closely related objects with no external callouts.
- The team does not have OmniStudio expertise and the timeline does not accommodate ramp.
- Long-term maintainability by a generalist admin or developer team is a priority.
- The requirement is automation-only (no guided UI) — Screen Flow invoked from a record or trigger is sufficient; OmniStudio adds overhead with no benefit.

---

## Common Patterns

### Pattern 1: Standard Runtime OmniScript for Multi-Source Guided Wizard

**When to use:** The org is Industries-licensed, the use case spans 3+ objects and includes external REST callouts, and the team has OmniStudio training.

**How it works:**
1. Confirm Standard Runtime is enabled (Setup > OmniStudio Settings > Enable OmniStudio Standard Runtime).
2. Build an Integration Procedure to retrieve data from Salesforce objects and external endpoints in a single orchestrated call with parallel HTTP branches where applicable.
3. Build an OmniScript that uses the Integration Procedure as its primary data source.
4. Expose FlexCards on the record page to surface summary data and launch the OmniScript.
5. Deploy using the Salesforce CLI with standard metadata API — no managed package tooling needed.

**Why not Screen Flow:** A Screen Flow equivalent requires multiple Get Records elements, custom Apex for external callouts (governor limit management, async patterns), and custom LWC for complex display. The build and maintenance cost at 3+ objects and external callout complexity significantly exceeds OmniStudio.

### Pattern 2: Screen Flow + LWC for Single-Object Guided Process

**When to use:** The org does not hold an Industries license, or the use case is contained to 1–2 objects with no external callouts.

**How it works:**
1. Design a Screen Flow with discrete screen steps for each phase of the guided process.
2. Use standard Get Records and Update Records elements for all data operations.
3. Embed custom LWC components on individual screens for complex display requirements.
4. Invoke Apex only if governor limits or callout requirements demand it.

**Why not OmniStudio:** OmniStudio requires an Industries license the org does not hold, and adds architectural complexity (designer tooling, runtime, deployment model) for a scenario that Screen Flow handles adequately.

### Pattern 3: Architecture Decision Record (ADR) Documentation

**When to use:** For every OmniStudio vs standard platform decision on a client engagement.

**How it works:**
1. Record the license confirmation result (licenses held, specific edition).
2. Document the use case complexity assessment (objects, callouts, steps, branching).
3. Record the team skills assessment and ramp cost estimate if OmniStudio is chosen.
4. Record the runtime path selected (Standard Runtime vs managed package — should always be Standard Runtime for new work).
5. State the recommendation with explicit rationale.
6. Get stakeholder sign-off on the decision before building.

**Why document it:** OmniStudio decisions have long-term licensing, training, and migration implications. Undocumented decisions are relitigated repeatedly and cause costly mid-project reversals.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Org does not hold an Industries cloud license | Screen Flow + LWC + Apex | License gate not satisfied — OmniStudio unavailable |
| Org holds Industries license, use case is single-object or 2 objects, no external callouts | Screen Flow + LWC | Capability adequate; no license or complexity justification for OmniStudio |
| Org holds Industries license, multi-step wizard spanning 3+ objects and/or external REST callouts | OmniStudio (Standard Runtime) | Declarative multi-source orchestration; Integration Procedure superior for callout sequencing |
| Automation-only requirement (no guided UI) | Screen Flow / Process / Apex | OmniStudio adds overhead for a use case Screen Flow handles; OmniScript is a UI tool |
| Team has no OmniStudio expertise, tight timeline | Screen Flow + LWC | OmniStudio ramp time exceeds build savings for simple scenarios |
| Org uses Vlocity managed package, evaluating new OmniStudio components | Assess migration to Standard Runtime before adding components | Managed package carries strategic migration debt; new components on the legacy path deepen it |
| New org, Industries-licensed, starting from scratch | Standard Runtime — no managed package | Managed package is a legacy path; Salesforce investment is in Standard Runtime |
| Client asks for OmniStudio without stated license | Verify license first — do not proceed | LLM default to recommend OmniStudio for any multi-step UI; license is the primary gate |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm license entitlement:** Check Setup > Company Information > Licenses for a qualifying Industries cloud (FSC, Health Cloud, Manufacturing Cloud, Nonprofit Cloud, Education Cloud). If absent, document that OmniStudio is unavailable and recommend Screen Flow + LWC. Stop here unless the client intends to purchase an Industries license.
2. **Map use case to the continuum:** Identify the number of Salesforce objects involved, whether external REST callouts are required, step count, and branching complexity. Apply the decision table above to identify the correct entry point on the Dynamic Forms → Screen Flow → OmniStudio continuum.
3. **Assess team skills and ramp cost:** Confirm whether OmniStudio-certified developers or admins are on the project. If not, estimate ramp time (typically 2–4 weeks for a competent Salesforce developer new to OmniStudio) and weigh against build timeline.
4. **Determine runtime path if OmniStudio is selected:** If the org is new to OmniStudio, mandate Standard Runtime. If the org uses the managed package, assess migration scope before adding new OmniStudio components on the legacy runtime.
5. **Produce a documented architecture decision:** Draft an ADR covering license status, use case complexity assessment, team readiness, runtime path, and recommendation with rationale. Use the template in `templates/omnistudio-vs-standard-architecture-template.md`.
6. **Get stakeholder sign-off:** Present the ADR to technical stakeholders and the client before any build work begins. OmniStudio decisions carry licensing, training, and migration implications that require explicit agreement.
7. **Validate against current official documentation:** OmniStudio has evolved rapidly across releases. Confirm any capability or limit claims against Salesforce documentation current as of the active release.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] License entitlement confirmed for the specific org — not assumed from cloud edition name
- [ ] Use case complexity mapped to the tooling continuum (objects, callouts, steps, branching)
- [ ] Team skills and ramp cost assessed and included in the recommendation
- [ ] Runtime path specified: Standard Runtime for new work; migration assessment for orgs on managed package
- [ ] Recommendation includes explicit rationale — not just a tool name
- [ ] Architecture decision record (ADR) drafted and approved by stakeholders
- [ ] All factual claims validated against current Salesforce documentation

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Industries license edition matters, not just the cloud name** — Not all Financial Services Cloud or Health Cloud editions include OmniStudio at the same entitlement level. Some starter editions have restricted or absent OmniStudio access. Confirming "the org has FSC" is not sufficient — verify the specific edition and entitlement against the current Salesforce pricing and packaging guide before committing to an OmniStudio architecture.
2. **Vlocity managed package and Standard Runtime cannot coexist for the same component type** — Orgs migrating from managed package to Standard Runtime cannot run both concurrently for OmniScript or Integration Procedure types. Migration requires a structured conversion project using Salesforce's OmniStudio Conversion Tool. Treating the migration as a background task or a partial migration creates a split-runtime state that breaks deployment pipelines and testing.
3. **FlexCards fail silently in unlicensed orgs or sandboxes that have lost license sync** — FlexCard components appear blank or throw console errors in sandboxes where the Industries license has not been provisioned or has expired. This is a common source of confusing test failures in refresh cycles where the full-sandbox license is not carried over.
4. **Standard Runtime is natively embedded but must be explicitly enabled** — As of Spring '25+, Standard Runtime is available in all Industries-licensed orgs, but it must be enabled in Setup > OmniStudio Settings. Orgs that do not explicitly enable it continue to use the managed package runtime even if they intend to use Standard Runtime. New developers frequently assume it is auto-enabled.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Architecture decision recommendation | Written rationale covering license status, use case continuum mapping, team readiness, and runtime path |
| Tooling continuum map | Explicit mapping of the use case to the Dynamic Forms → Screen Flow → OmniStudio continuum with justification |
| Standard Runtime vs managed package risk assessment | If OmniStudio is in use, assessment of migration debt and recommended path forward |
| Architecture Decision Record (ADR) draft | Stakeholder-ready document recording the decision, rationale, and trade-offs |

---

## Related Skills

- omnistudio-vs-standard-decision — peer skill with capability matrix and license gate detail; use for granular tooling comparison
- omnistudio-testing-patterns — once OmniStudio is selected, use for testing OmniScript and Integration Procedure implementations
- omnistudio-ci-cd-patterns — once OmniStudio is selected, use for deployment pipeline design

---

## Official Sources Used

- Salesforce Architects Building Forms Decision Guide — https://architect.salesforce.com/design/decision-guides/build-forms
- OmniStudio Overview — https://help.salesforce.com/s/articleView?id=sf.os_omnistudio_overview.htm
- OmniStudio Standard Runtime Blog (March 2026) — https://developer.salesforce.com/blogs/2026/03/omnistudio-standard-runtime
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
