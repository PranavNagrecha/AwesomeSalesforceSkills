---
name: nonprofit-platform-architecture
description: "Use this skill when designing or evaluating the holistic platform architecture for a Nonprofit Cloud (Agentforce Nonprofit) implementation — spanning module selection, data model foundations, integration strategy, and phased adoption across the six independently licensable modules. Trigger keywords: Nonprofit Cloud architecture, NPC platform design, nonprofit Salesforce architecture, program and fundraising architecture, nonprofit data model strategy, Agentforce Nonprofit. NOT for individual feature design within a single module, NPSP configuration, the NPSP-vs-NPC migration decision, or day-to-day admin setup of a specific module."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Scalability
  - Reliability
  - Operational Excellence
  - Security
triggers:
  - "how should we architect our Nonprofit Cloud implementation across fundraising and program management"
  - "which Nonprofit Cloud modules should we adopt first and in what order"
  - "what does a full-platform nonprofit Salesforce architecture look like end to end"
  - "we are a nonprofit starting a Salesforce implementation and need to understand the platform structure"
  - "how do the six Nonprofit Cloud modules fit together and which ones do we need"
  - "what is the Nonprofit Cloud data model and how does Person Account fit in"
  - "our nonprofit wants to use Agentforce Nonprofit — how do the AI features integrate with the rest of the platform"
tags:
  - nonprofit-cloud
  - npc
  - agentforce-nonprofit
  - nonprofit-platform
  - person-accounts
  - standard-industry-data-model
  - fundraising
  - program-management
  - outcome-management
  - volunteer-management
  - grantmaking
  - nonprofit-architecture
  - modular-adoption
inputs:
  - "Organization's primary mission domains (fundraising, program delivery, grantmaking, volunteerism)"
  - "Current constituent data model (Person Accounts preferred; confirmation required)"
  - "Which of the six NPC modules are in scope for the implementation"
  - "Integration landscape (payment processors, marketing automation, ERP, volunteer platforms)"
  - "Data volume estimates for constituents, gift transactions, program participants"
  - "Timeline and phasing constraints for module rollout"
  - "Whether the org is net-new to Salesforce or migrating from NPSP"
outputs:
  - "Module adoption map showing which of the six NPC modules to implement and in what sequence"
  - "Data model foundation decisions (Person Account confirmation, Standard Industry Data Model alignment)"
  - "Cross-module integration points and object dependency diagram"
  - "Phased implementation roadmap with governance checkpoints"
  - "Risk register for platform-level architectural decisions"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-12
---

# Nonprofit Platform Architecture

Use this skill when designing or evaluating the end-to-end platform architecture for a Nonprofit Cloud (rebranded Agentforce Nonprofit in October 2025) implementation. This skill covers holistic architectural strategy across all six modules — Fundraising, Program/Case Management, Outcome Management, Volunteer Management, Grantmaking, and AI/Agentforce agents — as well as the foundational data model decisions and phased adoption approach that determine long-term platform health.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Confirm the platform is Nonprofit Cloud (NPC), not NPSP.** NPC is a native Salesforce Industry Cloud built on the Standard Industry Data Model and Person Accounts. NPSP is a managed package with a Household Account model. These share no upgrade path and no object namespace. If the org is on NPSP, use the `npsp-vs-nonprofit-cloud-decision` skill first.
- **Most common wrong assumption:** Practitioners assume they can configure NPC like NPSP — using NPSP namespace objects, CRLP rollup customizations, or Household Account model conventions. NPC uses an entirely different data model. Any NPSP-derived configuration patterns are inapplicable.
- **Platform constraints in play:** NPC modules are independently licensable and adoptable, but share the same foundational Person Account data model. Enabling Person Accounts is an irreversible org-level decision. The Standard Industry Data Model (SIDM) objects underpinning NPC have their own API limits, record type requirements, and sharing model implications that differ from standard CRM objects.

---

## Core Concepts

### 1. Nonprofit Cloud Is a Native Industry Cloud — Not a Managed Package

Nonprofit Cloud (NPC), rebranded as Agentforce Nonprofit in October 2025, is a first-party Salesforce product built natively on the Salesforce Platform as part of the Industry Clouds portfolio. Unlike the Nonprofit Success Pack (NPSP), NPC has no managed package namespace, no external dependency, and no App Exchange installation. It is provisioned directly through Salesforce licensing.

NPC is built on the **Standard Industry Data Model (SIDM)** — a shared object schema used across multiple Salesforce Industry Clouds (Health Cloud, Financial Services Cloud, etc.) that provides interoperability and reduces custom object proliferation. This matters architecturally because SIDM objects have their own API naming conventions, field-level permissions behavior, and OWD defaults that differ from Sales/Service Cloud conventions.

Because NPC is native, it participates fully in all Salesforce platform capabilities: Salesforce Flow, Einstein AI, MuleSoft, Data Cloud, and Agentforce agents — without the managed package isolation constraints that NPSP imposed.

### 2. Person Accounts Are Required and Non-Negotiable

Nonprofit Cloud requires **Person Accounts** as the constituent data model. Person Accounts merge the Contact and Account objects into a single record type, enabling constituent-centric relationship management without the Household Account intermediary required by NPSP.

Enabling Person Accounts is an **irreversible org-level setting**. Once enabled, it cannot be turned off. This means:
- The org architecture decision to use Person Accounts must be made before any data is loaded or modules are configured.
- Any existing org with Household Accounts (i.e., NPSP) cannot be converted in place — a net-new NPC org is required.
- Third-party integrations must be validated for Person Account compatibility before go-live, since many integrations assume standard Contact/Account separation.

### 3. Six Independently Adoptable Modules

NPC is structured as six independently licensable modules that share the SIDM foundation but can be adopted in any sequence depending on organizational priorities:

| Module | Core Purpose | Key Objects |
|---|---|---|
| **Fundraising** | Gift transaction processing, gift entry, recurring commitments, batch entry | Gift Transaction, Gift Commitment, Designation, Donor, Gift Entry Batch |
| **Program and Case Management** | Program delivery, benefit assignment, participant tracking | Program, Program Cohort, Benefit, Benefit Assignment, Case Plan |
| **Outcome Management** | Impact measurement, indicator tracking, result scoring | Outcome, Indicator, Result |
| **Volunteer Management** | Volunteer recruitment, scheduling, hour tracking | Volunteer Project, Volunteer Job, Volunteer Shift, Volunteer Shift Worker (19 objects total) |
| **Grantmaking** | Grant lifecycle for foundations — applications, awards, disbursements | Funding Award, Funding Disbursement, Funding Opportunity, Funding Request |
| **AI/Agentforce Agents** | Purpose-built AI agents for nonprofit use cases (e.g., constituent engagement, donor outreach) | Agentforce Agent framework; requires Data Cloud for memory and grounding |

The modular architecture enables phased adoption but also introduces cross-module data dependencies. For example, an Outcome Management implementation that references Program Cohort records requires Program and Case Management to be active first.

### 4. Connect API for Fundraising Integration

The Fundraising module exposes a **Connect API** (available from API version 59.0 onward) for headless gift entry, payment processing integration, and external fundraising platform connectivity. Architecturally this matters because:
- Payment processor integrations (Stripe, iATS, PayPal) should route through the Connect API rather than direct DML on Gift Transaction objects to maintain audit trail integrity.
- External fundraising platforms (Classy, Fundraise Up, Double the Donation) integrate via the Connect API or dedicated managed connectors.
- Any custom Lightning component that creates gift records should use the API, not direct Apex inserts, to enforce business logic defined at the Fundraising layer.

---

## Common Patterns

### Pattern 1: Phased Module Adoption — Fundraising First

**When to use:** Organizations coming to NPC from scratch or from NPSP where fundraising is the primary driver. This is the most common nonprofit implementation pattern.

**How it works:**
1. Establish the Person Account data model foundation and load constituent data.
2. Implement Fundraising module: configure Gift Entry Manager, payment processor integration via Connect API, batch entry processes, and recurring commitments (Gift Commitments).
3. Validate gift transaction data integrity and reporting with finance stakeholders before launching Program Management.
4. Add Program and Case Management in phase 2 once fundraising is stable — link program participants to the same Person Account constituent records.
5. Layer Outcome Management in phase 3 to track impact against program cohorts.

**Why not launch all modules simultaneously:** Cross-module dependencies mean data model errors in the Fundraising layer propagate into program and outcome records. A staged approach isolates defects and reduces rollback complexity.

### Pattern 2: Volunteer Management as a Standalone Module

**When to use:** Organizations where volunteerism is operationally separate from fundraising and program delivery (e.g., environmental orgs, food banks).

**How it works:**
1. Provision Volunteer Management module independently — it does not require Fundraising or Program Management to be active.
2. Configure Volunteer Projects, Jobs, and Shifts. The 19 Volunteer Management objects are self-contained.
3. Link Volunteer Shift Worker records to Person Account constituents to unify the 360-degree constituent view — this is the primary integration point with the rest of the NPC data model.
4. If volunteer hours should feed into outcome measurement, add Outcome Management after Volunteer Management is stable.

**Why not use a third-party volunteer platform:** Third-party platforms (VolunteerHub, Galaxy Digital) introduce duplicate constituent records unless a robust Person Account matching strategy is in place. NPC native Volunteer Management avoids this by sharing the same constituent record.

### Pattern 3: Grantmaking for Foundation Sub-Organizations

**When to use:** A nonprofit that also operates a foundation arm that makes grants to other organizations (as opposed to receiving grants — that is grant management, not grantmaking).

**How it works:**
1. Confirm the correct module — Grantmaking is for foundations that award grants outward. Grant management (receiving grants from funders) is handled in the Fundraising module.
2. Configure Funding Opportunities and Funding Request intake forms using Experience Cloud for external applicant access.
3. Model the review and award workflow using Salesforce Flow against Funding Request and Funding Award objects.
4. Configure Funding Disbursements with finance system integration for payment scheduling.

**Why this matters architecturally:** Grantmaking is the only NPC module that has a significant external-facing component (grant applicants are not internal staff). This introduces Experience Cloud licensing, external user provisioning, and data visibility requirements that must be designed before the module is configured.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New nonprofit evaluating which modules to license | License Fundraising and Program Management as the core; evaluate others based on mission | These two modules serve the universal fundraising and service delivery needs; others address specific mission types |
| Org has both a foundation that gives grants and a direct service arm | License Grantmaking separately from Fundraising | Grantmaking data model (outward grant awards) differs fundamentally from Fundraising (inward donations) |
| Volunteer program is large and operationally complex | Dedicate a full implementation phase to Volunteer Management with its 19 objects | Underestimating Volunteer Management scope is a common cause of scope creep |
| Organization wants to use Agentforce AI agents | Activate AI/Agentforce module and provision Data Cloud for agent memory and grounding | Agentforce agents without Data Cloud cannot maintain context across sessions or access unified constituent history |
| NPSP org considering adding Outcome Management | Outcome Management is NPC-only — migration to NPC is required | No Outcome Management equivalent exists in NPSP; this is a NPC-exclusive capability |
| Multi-entity nonprofit (parent + chapters) | Evaluate multi-org vs. single-org with Salesforce Experience Cloud for chapter portals | NPC does not have a native chapter management model; architecture must be explicit about entity boundaries |
| Implementation timeline is under 6 months | Scope to one or two modules maximum with a phased roadmap for the rest | Attempting all six modules simultaneously in under 6 months is a leading cause of NPC implementation failures |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm the platform foundation.** Verify the org is provisioned as Nonprofit Cloud (not NPSP). Confirm Person Accounts are enabled. Confirm the Salesforce edition and NPC module licenses that have been purchased. Document any licenses not yet activated — these constrain scope.
2. **Map mission domains to modules.** Conduct a structured discovery session to map the organization's operational domains (donor development, program delivery, impact measurement, volunteer coordination, grant-giving, constituent AI engagement) to NPC modules. Produce a module adoption map that shows which modules are in scope, which are out of scope, and which are deferred to a future phase.
3. **Define the cross-module data model.** Document how Person Account records will be used across modules (constituents as donors, program participants, volunteers, grant applicants). Identify constituent deduplication strategy, record type design, and any SIDM object customization required. This is the highest-risk architectural decision — errors here propagate across all modules.
4. **Design integration architecture.** Identify all external systems: payment processors (Fundraising Connect API v59.0+), marketing automation, volunteer platforms, finance/ERP, and HR systems. Document integration patterns (Connect API, Platform Events, MuleSoft, direct REST), data flow direction, and record ownership model.
5. **Sequence the phased implementation roadmap.** Order module rollouts by dependency and organizational priority. Document phase entry/exit criteria, data migration approach per phase, and the governance checkpoints at which architecture decisions will be reviewed before the next phase begins.
6. **Validate the architecture against the Well-Architected Framework.** Check the design against the WAF pillars: Trustworthiness (data integrity across modules), Adaptability (ability to add future modules without rework), Security (Person Account sharing model, Experience Cloud external access), and Operational Excellence (monitoring, deployment process, team skills).
7. **Document risk register.** Capture the top platform-level risks: Person Account irreversibility, cross-module data dependencies, Connect API version constraints, AI/Agentforce Data Cloud prerequisites, and any modules with known feature gaps vs. the organization's requirements.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Confirmed org is Nonprofit Cloud (native), not NPSP (managed package)
- [ ] Person Accounts confirmed as enabled and constituent record type strategy documented
- [ ] All licensed NPC modules identified and module adoption map produced
- [ ] Cross-module data model dependencies documented (especially Program → Outcome linkage)
- [ ] Fundraising Connect API version (59.0+) documented for integration design
- [ ] Payment processor integration pattern specifies Connect API routing, not direct DML
- [ ] Grantmaking module correctly scoped — outward grant-giving, not inward grant-receiving
- [ ] Volunteer Management scoped as 19-object domain with its own phase if in scope
- [ ] AI/Agentforce module prerequisites documented: Data Cloud required for agent memory
- [ ] Phased roadmap includes explicit phase entry/exit criteria
- [ ] Architecture validated against Salesforce Well-Architected Framework pillars
- [ ] Risk register created with at least one risk per licensed module

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Person Accounts cannot be disabled once enabled** — Enabling Person Accounts is an irreversible org configuration. Teams that enable it for testing and then want to revert must provision a fresh org. Always confirm Person Account strategy in a sandbox before touching production.
2. **NPC has no upgrade path from NPSP** — There is no Salesforce-provided migration tool. Moving from NPSP to NPC requires provisioning a net-new Salesforce org with NPC licenses and performing a full data migration. Any advice suggesting an "upgrade" or "in-place migration" is incorrect.
3. **Volunteer Management has 19 distinct objects** — Teams frequently underscope Volunteer Management as a simple "shift scheduling" feature. The full Volunteer Management data model has 19 objects including Volunteer Projects, Jobs, Shifts, Shift Workers, and associated capacity and eligibility objects. Attempting to configure it in under two weeks routinely causes scope failure.
4. **Agentforce Nonprofit agents require Data Cloud** — AI/Agentforce agents cannot access unified constituent history or maintain context across sessions without Data Cloud. Teams that license Agentforce agents but not Data Cloud will get agents with no memory or contextual grounding. Data Cloud must be architected and activated before Agentforce agent development.
5. **Connect API version lock at 59.0+** — The Fundraising Connect API is available from API version 59.0 onward. Any payment processor or external fundraising platform integration must target at least this API version. Legacy integrations built against earlier API versions will not have access to gift entry endpoints and must be rebuilt.
6. **Grantmaking is for foundations making grants, not for receiving them** — A frequent misidentification: organizations that apply for grants (grant seekers) should not license Grantmaking. Grantmaking is for foundations that award grants to others. Grant seeking/management is handled in the Fundraising module. Licensing the wrong module wastes budget and confuses data model design.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Module Adoption Map | Which of the six NPC modules are in scope, out of scope, and deferred — with rationale for each decision |
| Cross-Module Data Model Diagram | Person Account record types, SIDM object relationships, and cross-module linking strategy |
| Integration Architecture Document | External systems, integration patterns (Connect API, Platform Events, MuleSoft), and data flow ownership |
| Phased Implementation Roadmap | Module rollout sequence with dependencies, phase entry/exit criteria, and governance checkpoints |
| Risk Register | Platform-level risks per module with likelihood, impact, and mitigation strategy |

---

## Related Skills

- `architect/npsp-vs-nonprofit-cloud-decision` — Use before this skill when the organization is currently on NPSP and has not yet decided to move to NPC; this skill assumes the NPC decision is already made
- `admin/grant-management-setup` — Use after this skill to configure the Grantmaking module in detail once the architectural scope is confirmed
