---
name: client-onboarding-design
description: "Use this skill when designing the FSC client onboarding process — mapping document collection touchpoints, approval steps, compliance checkpoint sequencing, and welcome journey handoffs. Trigger keywords: client onboarding design, onboarding workflow requirements, document collection flow, compliance checkpoint, welcome journey, intake process design. NOT for Action Plan template configuration mechanics, OmniStudio component implementation, or Flow builder steps — use fsc-action-plans for template setup details."
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
  - Template versioning governance recommendation (clone-and-republish protocol)
  - Welcome journey handoff specification (trigger, recipient, channel, timing)
  - Compliance checkpoint sequencing with escalation paths
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-11
---

# Client Onboarding Design

This skill activates when a practitioner needs to design the end-to-end FSC client onboarding process — mapping document collection touchpoints, sequencing compliance checkpoints, defining approval steps, and specifying welcome journey handoffs before any platform configuration begins. It does NOT cover Action Plan template configuration mechanics (see fsc-action-plans), OmniStudio component implementation details, or Flow builder construction.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm whether OmniStudio is licensed in the org. OmniStudio FlexCards and OmniScripts are a separately licensed add-on — they are not included with the base FSC license. If OmniStudio is not licensed, standard Screen Flows are the native fallback for guided intake. Do not assume OmniStudio availability without checking the org's installed packages and license entitlements.
- Identify the compliance and regulatory requirements that govern sequencing. In financial services, certain steps are legally mandatory in a specific order (e.g., KYC identity verification before account funding, consent capture before any data processing). These constraints drive the entire workflow structure and cannot be compromised for UX convenience.
- Understand the template versioning constraint before designing process governance. Action Plan templates — the primary task execution mechanism — cannot be edited after activation. Publishing a revised process requires a clone-and-republish workflow. This constraint must be designed into governance from day one: who owns template versioning, how changes are requested, and how in-flight onboarding journeys are handled during a version transition.
- Establish the anchor record for onboarding. In FSC, the process typically centers on a FinancialAccount or Account record. Clarifying the anchor object determines which Action Plan template types can be used and how the welcome journey trigger is configured.

---

## Core Concepts

### Action Plan Templates as Task Execution Layer

Action Plan templates are the primary mechanism for structured task sequences in FSC onboarding. A template is a reusable blueprint (ActionPlanTemplate) containing ordered task items (ActionPlanTemplateItem) with relative deadlines expressed as days from the plan start date. At process design time, the practitioner must define the full task inventory — names, owners, deadline offsets, and required vs. optional flags — so the template can be implemented correctly by the fsc-action-plans skill. The critical constraint: once a template is published (Status = Active), it cannot be edited. Any revision requires cloning the active template, modifying the clone in Draft status, then publishing the new version. This governance constraint must be reflected in the process design.

### OmniStudio vs. Screen Flow for Guided Intake

Guided intake — collecting client information through a structured multi-step form — can be delivered two ways in FSC. OmniStudio OmniScripts provide a purpose-built, declarative, multi-step intake experience with branching logic, data integration steps, and reusable components (FlexCards for display). They are preferred for complex, multi-page intake flows in orgs that are licensed for OmniStudio. However, OmniStudio is a separately licensed add-on; it is not included with the base FSC license. Standard Screen Flows are the correct fallback for orgs without OmniStudio and are sufficient for most onboarding intake scenarios. At process design time, the practitioner must determine license availability before recommending either approach.

### Compliance Checkpoint Sequencing

Financial services onboarding is regulated. Process design must identify which compliance checkpoints are legally mandated, the minimum required sequence, and who has authority to clear each gate. Common checkpoints include: identity verification (KYC/AML), suitability assessment, consent capture, document collection confirmation, and advisor or compliance officer sign-off. Each checkpoint must have a defined escalation path (what happens if a document is missing or a verification step fails) and a clear owner. These checkpoints become required tasks in the Action Plan template and/or approval steps in the intake Flow.

### Welcome Journey Handoffs

The welcome journey begins after a client clears the initial onboarding gates. Design decisions include: the trigger event (plan task completion, record status change, or approval step outcome), the channel (email, SMS via Marketing Cloud or Messaging, or a portal notification), and the timing relative to account activation. The process design must specify the handoff clearly enough for the implementation team to configure the trigger without ambiguity — typically a named platform event, Flow-triggered action, or Marketing Cloud journey entry event.

---

## Common Patterns

### Phased Onboarding with Compliance Gates

**When to use:** Regulatory requirements mandate that certain steps must be completed and verified before subsequent steps begin — for example, KYC clearance is required before account funding instructions are sent.

**How it works:**
1. Map the full onboarding journey into discrete phases: Pre-Onboarding (identity and eligibility checks), Document Collection, Compliance Review, Account Activation, and Welcome Journey.
2. Define a gate at the end of each phase. A gate is a required action — either a required task in an Action Plan, an approval step, or a Flow decision element — that must be completed before the next phase begins.
3. For each gate, identify: the owner, the SLA (how many business days before escalation), and the escalation path.
4. Map the resulting sequence to Action Plan template task items (required flag = true on gate tasks) and Screen Flow or OmniScript steps for intake collection.
5. Deliver the process map as a structured design brief before any configuration begins.

**Why not the alternative:** Building the onboarding Flow or Action Plan template without a compliance-gated process map leads to out-of-order task execution, missed checkpoints, and regulatory risk that is expensive to remediate post-launch.

### Template Versioning Governance Design

**When to use:** The business needs the ability to update onboarding process steps after go-live without disrupting clients who are already in the middle of onboarding.

**How it works:**
1. Establish a named owner for Action Plan templates (typically the business system admin or process owner).
2. Define a change request protocol: who can request a process change, who approves it, and what lead time is required.
3. Document the clone-and-republish workflow: when a change is approved, the admin clones the active template, applies changes to the Draft clone, and publishes the clone as the new active version. The original template remains active and backs all in-flight plans.
4. Define a naming convention that includes a version indicator (e.g., "Client Onboarding v3") so teams can identify the current standard.
5. Establish a rule for in-flight plans: clients currently in onboarding on the prior version complete on that version. Do not attempt to migrate in-flight plans to the new version unless the change is a critical compliance correction.

**Why not the alternative:** Without a governance design, admins attempt to edit active templates directly (which fails), or clone without naming conventions, creating a proliferation of unnamed template versions with no audit trail.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| OmniStudio is licensed | Design guided intake as OmniScript | Purpose-built for multi-step intake with branching, reusable across FSC apps |
| OmniStudio is NOT licensed | Design guided intake as Screen Flow | Standard platform capability, no additional license required, sufficient for most onboarding intake |
| Compliance requires step ordering | Use required Action Plan tasks as gates | Required flag prevents plan completion until the gate task is closed; enforces sequence |
| Process changes are anticipated post-launch | Build clone-and-republish governance into design | Published templates are immutable; governance must exist before first go-live |
| Welcome journey is simple (single email) | Trigger via Flow record-triggered automation | No Marketing Cloud integration needed for a single email notification |
| Welcome journey is multi-step or multi-channel | Design as Marketing Cloud journey entry event | Use a platform event or status field change as the journey trigger; specify the payload fields at design time |
| Document collection is complex (many doc types, conditional requirements) | Map document requirements to Action Plan task items with doc type labels | Keeps document collection visible in the plan dashboard; avoids hidden checklist in a form |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm license and feature baseline** — Verify whether OmniStudio is licensed (check installed packages). Confirm FSC is enabled and Action Plans is active. Establish which objects will anchor the onboarding record (FinancialAccount, Account, Opportunity).
2. **Gather requirements across all stakeholders** — Interview or review requirements from the advisor/relationship manager team (task ownership, SLAs), compliance team (mandatory checkpoints and their legal basis, escalation paths), operations team (document types, storage requirements), and IT or integration team (systems that must be notified at handoff points).
3. **Map the onboarding stages and compliance gates** — Produce a phased process map with discrete stages, gate conditions at each phase boundary, owners, SLAs, and escalation paths. This map is the primary deliverable before any configuration begins.
4. **Define the Action Plan task inventory** — For each stage, identify the tasks that belong in an Action Plan template: task name, owner role or queue, DaysFromStart offset, required or optional, and document type associated (if applicable). This becomes the design brief for the fsc-action-plans skill.
5. **Specify the intake flow design** — Based on license availability, document the guided intake as either an OmniScript design (steps, data elements, branching conditions) or a Screen Flow design (screens, variables, decision elements, record operations). Do not configure — document the design for the implementation team.
6. **Define the welcome journey handoff** — Specify the trigger event, the channel, the timing, and the data payload the downstream system (email, Marketing Cloud, portal) needs. If the trigger is a task completion or status change, name the specific field and value.
7. **Deliver governance design** — Document the template versioning protocol (owner, change request process, naming convention, in-flight plan policy) so it is in place before the first template is published.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] OmniStudio license status confirmed; intake approach (OmniScript vs. Screen Flow) selected accordingly
- [ ] All compliance checkpoints identified with legal or regulatory basis documented
- [ ] Process map includes gate conditions, owners, SLAs, and escalation paths at each phase boundary
- [ ] Action Plan task inventory is complete (name, owner, DaysFromStart, required flag, doc type) and ready for fsc-action-plans implementation
- [ ] Template versioning governance is documented with named owner and change protocol
- [ ] Welcome journey handoff is specified with trigger, channel, timing, and data payload
- [ ] In-flight plan policy documented for version transitions

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Action Plan templates cannot be edited after activation** — Once an ActionPlanTemplate is published (Status = Active), all edits are locked at the platform level. Attempting to revise the task list in a live template returns an error. Governance for this must be designed before go-live, not discovered in production when a compliance change is urgently required.
2. **OmniStudio requires a separate license** — OmniStudio FlexCards and OmniScripts are not included with the base FSC license. Recommending OmniStudio without confirming the license adds implementation risk and potential licensing cost surprises. Always check the org's installed packages before designing for OmniStudio.
3. **In-flight plans are not updated when a new template version is published** — Publishing a clone of an active template does not retroactively update plans already in progress. Clients who started onboarding under version 1 complete under version 1 even if version 2 has been published. The process design must account for how the business wants to handle the transition window.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Onboarding process map | Phased workflow diagram with stage gates, owners, SLAs, and compliance checkpoints |
| Action Plan task inventory | Per-task list (name, owner, DaysFromStart, required flag, doc type) as input to fsc-action-plans |
| Technology selection rationale | Document confirming OmniStudio vs. Screen Flow choice with license basis |
| Welcome journey handoff spec | Trigger event, channel, timing, and data payload definition |
| Template versioning governance | Owner, change protocol, naming convention, in-flight plan policy |

---

## Related Skills

- admin/fsc-action-plans — Covers Action Plan template configuration mechanics; use after this skill's task inventory design brief is complete
- admin/compliance-documentation-requirements — Covers regulatory documentation requirements; use alongside this skill to establish which compliance checkpoints are legally mandatory
- admin/financial-account-setup — Covers the FinancialAccount data model; relevant when the onboarding anchor object is FinancialAccount
- admin/hipaa-workflow-design — Covers HIPAA-specific workflow constraints; relevant for Health Cloud onboarding contexts with protected health data
