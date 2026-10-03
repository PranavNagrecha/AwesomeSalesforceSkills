---
name: client-onboarding-design
description: "Use this skill when designing the FSC client onboarding process — mapping document collection touchpoints, approval steps, compliance checkpoint sequencing, and welcome journey handoffs. Trigger keywords: client onboarding design, onboarding workflow requirements, document collection flow, compliance checkpoint, welcome journey, intake process design. NOT for configuring the Action Plan template itself — use admin/fsc-action-plans. NOT for OmniScript screen and branching requirements — use admin/omniscript-flow-design-requirements."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Security
  - Reliability
triggers:
  - "how should I design the FSC client onboarding workflow to include document collection, compliance checks, and welcome journey handoffs"
  - "what touchpoints do I need to map before building an onboarding process in Financial Services Cloud"
  - "the compliance team wants defined approval steps and document checkpoints built into our new client intake process"
  - "we need to decide whether to use OmniStudio or standard Flow for our FSC onboarding guided intake"
  - "how do I structure client onboarding governance so advisors can update the process without breaking active onboarding journeys"
  - "sequence KYC before account funding in an Action Plan template"
  - "track required onboarding documents with document checklist items"
tags:
  - client-onboarding-design
  - financial-services-cloud
  - onboarding-process
  - action-plan-templates
  - compliance-checkpoints
  - document-collection
  - welcome-journey
  - omnistudio
  - screen-flow
inputs:
  - Business requirements for the onboarding process (who owns each step, what documents are required, what compliance checks are mandated)
  - FSC license details — confirm whether OmniStudio is licensed separately or if standard Flows are the intake tool
  - List of approval steps and the roles or queues responsible for each
  - Compliance or regulatory requirements that dictate sequencing (e.g., KYC before account funding, consent capture before data processing)
  - Target Salesforce objects that anchor the onboarding record (Account, FinancialAccount, Opportunity)
  - Existing process maps, intake forms, or welcome journey touchpoints from the business
outputs:
  - Onboarding process map with sequenced stages, owners, document touchpoints, and compliance gates
  - Technology selection rationale (OmniStudio vs. Screen Flow for intake, Action Plans for task execution)
  - Action Plan template design brief for the fsc-action-plans skill to implement
  - Template versioning governance recommendation (version-and-republish protocol)
  - Welcome journey handoff specification (trigger, recipient, channel, timing)
  - Compliance checkpoint sequencing with escalation paths
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

# Client Onboarding Design

This skill activates when a practitioner needs to design the end-to-end FSC client onboarding process: document collection touchpoints, compliance checkpoint sequencing, approval steps, and welcome journey handoffs, before any platform configuration begins. It does NOT cover Action Plan template configuration mechanics (see `admin/fsc-action-plans`), OmniStudio component implementation, or Flow construction.

Licence gate: Action Plan templates need the IndustriesActionPlans license (plus Customize Application to create them). Document checklist items are documented in the Financial Services Cloud developer guide, and some of their fields exist only with Integrated Onboarding for Agentforce Financial Services enabled.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm whether OmniStudio is available in the org (check installed packages and licences). If it is not, standard Screen Flows are the native fallback for guided intake. UNVERIFIED (2026-10-03): that OmniStudio is always a separately licensed add-on to FSC is a commercial claim not stated in the guides read.
- Identify the regulatory sequencing rules (KYC before account funding, consent before data processing). They drive the workflow structure and cannot be traded for UX convenience.
- Understand template versioning before designing governance. Each template has versions (`ActionPlanTemplateVersion`) whose `Status` is `Draft`, `Final` (published), `Obsolete`, or `ReadOnly`, and a plan can only be created from a published version. Design who owns new versions and how in-flight plans are handled.
- Establish the anchor record. The Metadata API lists supported template parents as Account, BusinessMilestone, Campaign, Case, Claim, Contact, Contract, InsurancePolicy, InsurancePolicyCoverage, Lead, Opportunity, PersonLifeEvent, Visit, and custom objects with activities. The object reference lists Financial Account as a plan parent from API 48.0. Confirm the anchor in a sandbox before committing.

---

## Questions to Ask Before Configuring

Ask these before drawing the process map. Each one traces to a gotcha in `references/gotchas.md`.

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "Which steps must finish before the next can start, by regulation?" | Sequencing between items is an explicit dependency (`OnPreviousItemCompleted`), not a side effect of marking a task required (gotcha 2) | The dependency pairs, each with its legal basis | A plan that cannot send funding instructions before KYC is complete |
| "Which record anchors onboarding: Account, Financial Account, Opportunity?" | Template parent support differs between the Metadata API list and the plan object list (gotcha 3) | One anchor object, tested in a sandbox | Templates that launch from the record users actually work on |
| "Which documents are required, and can a document ever be waived?" | Document checklist items have `Status` values `Accepted`, `New`, `Pending`, `Waived`, and `IsRequired` cannot be changed after creation (gotcha 5) | A document list with required flags and a waiver policy | Document tracking that matches compliance rules from the first client |
| "How will the process change after go-live, and what happens to clients mid-onboarding?" | A plan stays bound to the published version it was created from (gotcha 1) | A version owner, a change protocol, and an in-flight policy | Regulatory changes shipped as a reviewed new version, not an emergency edit |
| "Are SLAs in calendar days, weekdays, or business days with holidays?" | Due dates come from `StartDate + N` formulas; holiday handling is a plan-level flag (gotcha 4) | The SLA definition per gate | Due dates that compliance agrees with |
| "Is OmniStudio available, or is Screen Flow the intake tool?" | Designing OmniScript intake without the product causes rework (gotcha 6) | The intake tool with its licence basis | An intake design the team can build |

What a proper onboarding design adds over "just building tasks": the platform enforces the regulatory order, document status is auditable, and process changes reach new clients without disturbing clients already in flight.

---

## Core Concepts

### Action Plan Templates as the Task Execution Layer

An Action Plan template is a reusable blueprint (`ActionPlanTemplate`) with versions (`ActionPlanTemplateVersion`) holding ordered items (`ActionPlanTemplateItem`). Each item has an `ItemEntityType` of `Task`, `Event` (API 63.0), `RecordAction`, or Document Checklist Item, a `DisplayOrder`, and an `IsRequired` flag. Item field values are set with `actionPlanTemplateItemValue` entries; a due date is a formula such as `StartDate + 10` on `ActivityDate`. From API 59.0, `actionPlanTemplateItemDependencies` make one item wait for another, with `creationType` `OnPreviousItemCompleted` in the guide's sample. The deployable form is in `references/metadata-examples.md`.

Versions and immutability: a version carries `IsLocked`, `MayEdit`, `ActivationDateTime`, and a `Version` index. A plan's `ActionPlanTemplateVersionId` must reference a published version at creation. UNVERIFIED (2026-10-03): the exact UI path for revising a published template (clone the template, or create a new version of the same template) is help-only; design governance around "a new published version", whichever path the org's release uses.

### OmniStudio vs Screen Flow for Guided Intake

Guided intake can be an OmniScript (where OmniStudio is available) or a Screen Flow. Screen Flow is a standard platform capability and is sufficient for most onboarding intake. Choose after confirming availability.

### Compliance Checkpoint Sequencing

Financial services onboarding is regulated. Identify each mandated checkpoint, the minimum sequence, who can clear it, and the escalation path. Common checkpoints: identity verification (KYC/AML), suitability assessment, consent capture, document collection confirmation, and advisor or compliance sign-off. In the platform, a checkpoint becomes a required item, and the order between checkpoints becomes an item dependency or an approval step.

### Document Collection

Document checklist items (`DocumentChecklistItem`, API 47.0) track a required upload against a parent record (`ParentRecordId`). `Status` is `Accepted`, `New`, `Pending`, or `Waived`; `IsRequired` is set at creation only; `IsFrozen` locks the item. Document types are deployable as `DocumentType` metadata (API 59.0), and org behavior as `DocumentChecklistSettings` (API 55.0).

### Welcome Journey Handoffs

The welcome journey starts after the client clears the onboarding gates. Specify the trigger event (a record status change, the plan's `ActionPlanState` reaching `Complete`, or an approval outcome), the channel, the timing, and the data payload, clearly enough that the implementation team can configure it without guessing.

---

## Common Patterns

### Phased Onboarding with Compliance Gates

**When to use:** Regulation requires certain steps to finish and be verified before later steps begin, for example KYC clearance before funding instructions.

**How it works:**
1. Map the journey into phases: Pre-Onboarding, Document Collection, Compliance Review, Account Activation, Welcome Journey.
2. Define a gate at the end of each phase: a required item whose completion releases the next phase's items through a dependency, or an approval step.
3. For each gate record the owner, the SLA, and the escalation path.
4. Map the sequence to template items (required gate items, dependencies between them) and to the intake Screen Flow or OmniScript.
5. Deliver the process map as a design brief before configuration begins.

### Template Versioning Governance

**When to use:** The business must update onboarding steps after go-live without disrupting clients already in onboarding.

**How it works:**
1. Name a template owner (a role, not a person).
2. Define the change protocol: who requests, who approves, and the lead time.
3. Publish changes as a new version; plans already created stay on the version they started with.
4. Use a naming convention with a version indicator (for example "Client Onboarding v3").
5. Define the in-flight rule: clients complete on their starting version unless a regulator-mandated correction requires remediation of open plans.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| OmniStudio available | Guided intake as OmniScript | Purpose-built for multi-step intake |
| OmniStudio not available | Guided intake as Screen Flow | Standard platform capability |
| Regulation requires step order | Required items plus `OnPreviousItemCompleted` dependencies | The dependency, not the required flag, creates the order |
| Process changes expected after launch | Version governance from day one | Plans stay bound to their published version |
| Simple welcome (single email) | Record-triggered Flow on the trigger field | No Marketing Cloud dependency |
| Multi-step or multi-channel welcome | Marketing Cloud journey entry event | Specify the trigger field and payload at design time |
| Many document types with conditional requirements | Document checklist items as template items, typed with `DocumentType` | Status per document is visible and auditable |

---

## Recommended Workflow

1. **Confirm licences and baseline.** Check OmniStudio availability, the IndustriesActionPlans license, and the anchor object's support for Action Plans in a sandbox.
2. **Gather requirements from every stakeholder.** Advisors (ownership, SLAs), compliance (mandated checkpoints, legal basis, escalation), operations (document types, waivers, storage), integration (systems notified at handoff).
3. **Map stages and compliance gates.** Produce a phased map with gates, owners, SLAs, and escalation paths, and list each regulatory ordering rule as a dependency pair.
4. **Define the template item inventory.** Per item: name, `ItemEntityType`, owner role or queue, due-date formula (`StartDate + N`), required flag, document type, and the item it depends on.
5. **Specify the intake design.** Document the OmniScript or Screen Flow screens, data elements, branching, and record operations for the implementation team.
6. **Define the welcome journey handoff.** Trigger field and value, channel, timing, and payload.
7. **Deliver governance.** Template owner, change protocol, naming convention, and in-flight policy, in place before the first version is published. Hand `references/metadata-examples.md` to the builder as the configuration target.

---

## Review Checklist

- [ ] OmniStudio availability confirmed; intake tool chosen accordingly
- [ ] Every compliance checkpoint has a legal or regulatory basis recorded
- [ ] Every regulatory ordering rule is an item dependency or approval step, not only a required flag
- [ ] Anchor object tested as an Action Plan parent in a sandbox
- [ ] Item inventory complete (name, type, owner, due-date formula, required, document type, dependency)
- [ ] Document waiver policy defined, with `IsRequired` decided at creation
- [ ] Version governance documented with a named owner and change protocol
- [ ] Welcome journey handoff specified with trigger, channel, timing, and payload
- [ ] In-flight plan policy documented for version transitions

---

## Salesforce-Specific Gotchas

The deep versions, with sources, live in `references/gotchas.md`.

| # | Gotcha | One-line consequence |
|---|---|---|
| 1 | Plans stay bound to the published version they started from | A new version does not fix clients already in flight |
| 2 | Order between items needs a dependency, not just `IsRequired` | Gate tasks exist but nothing stops the next phase |
| 3 | Template parent lists differ between guides | Financial Account anchoring must be tested |
| 4 | Due dates are `StartDate + N` formulas; holiday handling is a plan flag | "Business day" SLAs drift from compliance's definition |
| 5 | Document checklist `IsRequired` is fixed at creation | Waivers must use `Waived`, not an edit to the flag |
| 6 | OmniStudio availability must be confirmed | OmniScript designs stall without the product |
| 7 | A 75-item ceiling is unconfirmed | Very large templates need a sandbox test |

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Onboarding process map | Phases with gates, owners, SLAs, and compliance checkpoints |
| Template item inventory | Per item: type, owner, due-date formula, required flag, document type, dependency |
| Technology selection rationale | OmniStudio vs Screen Flow with licence basis |
| Welcome journey handoff spec | Trigger, channel, timing, and data payload |
| Version governance | Owner, change protocol, naming convention, in-flight policy |

---

## Related Skills

- `admin/fsc-action-plans`: Action Plan template configuration mechanics; use after this skill's item inventory is complete
- `admin/compliance-documentation-requirements`: which compliance checkpoints are legally mandatory
- `admin/financial-account-setup`: the FinancialAccount data model when it is the onboarding anchor
- `admin/hipaa-workflow-design`: HIPAA constraints for Health Cloud onboarding contexts
