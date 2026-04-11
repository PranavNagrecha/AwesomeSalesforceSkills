---
name: wealth-management-requirements
description: "Use this skill when gathering, structuring, and documenting requirements for a Financial Services Cloud (FSC) wealth management implementation — including financial planning workflow discovery, portfolio review process mapping, client lifecycle requirements, advisor tooling needs, and FSC architecture determination (managed package vs. FSC Core). Trigger keywords: wealth management requirements, FSC requirements gathering, financial planning workflow, portfolio review process, advisor tools setup, FSC data model scoping, wealth management process mapping. NOT for implementation, configuration, or code — use financial-account-setup, fsc-action-plans, or apex/fsc-financial-calculations for those. NOT for FSC architecture decisions — use architect/wealth-management-architecture. NOT for Health Cloud or NPSP requirements."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
  - Security
triggers:
  - "what questions should I ask before building wealth management in FSC"
  - "how do I map financial planning and portfolio review workflows to Salesforce FSC"
  - "what FSC objects do I need to scope for a wealth management implementation"
  - "difference between FSC managed package and FSC Core for wealth management requirements"
  - "how to gather advisor tool requirements for Financial Services Cloud"
  - "which FSC features cover financial goals, financial plans, and client review workflows"
tags:
  - financial-services-cloud
  - fsc
  - wealth-management
  - requirements-gathering
  - financial-planning
  - portfolio-review
  - advisor-tools
  - fsc-core
inputs:
  - "FSC org model in use or under evaluation: managed-package (FinServ__ namespace) or FSC Core (Winter '23+, no namespace)"
  - "List of wealth management business capabilities to cover (e.g., financial planning, portfolio review, goal tracking, client onboarding)"
  - "Advisor and client personas involved (financial advisor, wealth manager, client, household members)"
  - "Whether third-party custodian or portfolio management ISV packages are in scope (Black Diamond, Orion, Addepar, etc.)"
  - "Whether household model, multi-owner accounts, or institutional accounts are required"
  - "Target Salesforce edition and FSC license tier"
outputs:
  - "FSC architecture determination recommendation (managed package vs. FSC Core) with rationale"
  - "Object scope list for the engagement: which FSC objects are in scope and why"
  - "Wealth management process map: financial planning lifecycle, portfolio review cadence, client lifecycle stages"
  - "Advisor tooling requirements: what advisors need to see, do, and automate in Salesforce"
  - "Fit-gap analysis: which requirements map to standard FSC features vs. configuration vs. custom development"
  - "Requirements validation checklist for FSC wealth management"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-11
---

# Wealth Management Requirements

This skill activates when a Business Analyst or admin needs to elicit, structure, and document requirements for an FSC wealth management implementation — before any build begins. It covers the first critical decision (managed package vs. FSC Core architecture determination), the object model scoping conversation, financial planning and portfolio review workflow discovery, advisor tooling requirements, and the fit-gap analysis that drives sprint planning.

This skill is strictly for requirements and process mapping. Do NOT use it to configure FSC objects, write Apex, or design data architecture. Those tasks have dedicated skills.

---

## Before Starting

Gather this context before conducting any wealth management requirements discovery:

- **Determine managed package vs. FSC Core first.** This single decision changes every API name, every SOQL query, every integration design, and every ISV package compatibility conversation. Managed-package orgs use the `FinServ__` namespace (e.g., `FinServ__FinancialAccount__c`). FSC Core orgs — General Availability since Winter '23 — use no namespace (e.g., `FinancialAccount`). Do not proceed with object scoping until this is confirmed; the wrong answer causes silent failures throughout the project.
- **Identify the household model.** FSC wealth management can be configured for individual Person Accounts, multi-member household Accounts, or both. The household model drives rollup behavior, page layout design, advisor view requirements, and client portal scope. Confirm which model is in use or desired before mapping any process.
- **List third-party ISV packages in scope.** Custodian data feeds and portfolio management platforms (Black Diamond, Orion, Addepar, Tamarac) are common in wealth management implementations. These packages may not be certified for FSC Core and must be validated before the architecture decision is finalized.
- **Understand the advisor persona.** Wealth management has distinct advisor archetypes: financial planners who build goal-based plans, portfolio managers who monitor positions and allocations, relationship managers who focus on client lifecycle and AUM, and support staff who handle onboarding and documentation. Requirements differ substantially between these roles.

---

## Core Concepts

### Managed Package vs. FSC Core Determination

The most consequential requirements decision is whether the org uses the FSC managed package or FSC Core. This must be confirmed — not assumed — at the start of requirements discovery.

**Managed package (FinServ__ namespace):**
- All FSC objects carry the `FinServ__` prefix: `FinServ__FinancialAccount__c`, `FinServ__FinancialGoal__c`, `FinServ__FinancialAccountRole__c`.
- Rollups to household totals are executed via Apex triggers, not native Record Rollup fields.
- The managed package is typically one API version behind the FSC Core release cadence.
- Financial account ownership is modeled via two lookup fields: Primary Owner and Joint Owner. This limits ownership to two named individuals per account.
- Third-party ISV packages with FSC integrations are more likely to be certified against the managed package namespace.

**FSC Core (GA since Winter '23, no namespace):**
- Objects use standard API names: `FinancialAccount`, `FinancialGoal`, `FinancialPlan`, `ActionPlan`.
- Rollups use native Salesforce Record Rollup fields — no Apex trigger required for standard rollup behavior.
- Financial account ownership uses the `FinancialAccountParty` junction object, which supports unlimited owners with typed roles. This enables complex ownership structures (trusts, partnerships, family accounts with multiple members).
- `AccountFinancialSummary` is a Core-only rollup target that aggregates balances at the household/account level. It requires a dedicated FSC PSL integration user to populate correctly.
- Third-party ISV packages must be individually validated for FSC Core support. As of Spring '26, not all custodian feed packages are certified for Core.

**Requirements impact:** If a requirements document specifies SOQL queries, object names, or API field references without confirming the architecture, those references will be wrong for at least one of the two models. Requirements should describe business intent (e.g., "advisor can see total household AUM across all accounts") — not implementation field names.

### Key FSC Objects for Wealth Management Scoping

Requirements discovery must explicitly confirm which of these objects are in scope:

| Object | Managed Package Name | FSC Core Name | Purpose |
|---|---|---|---|
| Financial Account | `FinServ__FinancialAccount__c` | `FinancialAccount` | Brokerage, IRA, checking, insurance, loan accounts |
| Financial Account Role | `FinServ__FinancialAccountRole__c` | `FinancialAccountRole` | Defines role of a person on an account (owner, beneficiary) |
| Financial Account Party | N/A (managed package uses lookup fields) | `FinancialAccountParty` | Junction: unlimited owners per account with typed roles (Core only) |
| Financial Goal | `FinServ__FinancialGoal__c` | `FinancialGoal` | Retirement, education, home purchase goals with target amounts |
| Financial Plan | `FinServ__FinancialPlan__c` | `FinancialPlan` | Container grouping goals into a formal financial plan |
| Action Plan | `ActionPlan` | `ActionPlan` | Repeatable task-based workflows (e.g., annual review checklist) |
| Action Plan Template | `ActionPlanTemplate` | `ActionPlanTemplate` | Reusable template for consistent advisor review workflows |
| Account Financial Summary | N/A | `AccountFinancialSummary` | Core-only: household-level rollup of balances and AUM |
| Financial Holding | `FinServ__FinancialHolding__c` | `FinancialHolding` | Individual positions within a financial account |

**Financial Account types to scope:** The `FinancialAccountType` picklist drives record type and page layout selection. Standard types include: Investment (brokerage), Deposit (checking/savings), Insurance (life, annuity), and Loan (mortgage, HELOC). Confirm which types are needed before mapping workflows.

### Financial Planning and Portfolio Review Workflows

Wealth management requirements involve two distinct workflow categories that are commonly conflated:

**Financial planning workflow** — goal-based, client-centric:
1. Client discovery and data gathering (household, income, assets, liabilities, goals)
2. Goal definition and prioritization (retirement, education, home purchase, estate)
3. Plan creation linking goals to projected financial account allocations
4. Periodic plan review (typically annual or semi-annual)
5. Plan update based on life events (marriage, inheritance, job change)

**Portfolio review workflow** — performance-based, advisor-driven:
1. Custodian data load (positions, transactions, market values)
2. Portfolio analysis against allocation targets
3. Rebalancing recommendations generation
4. Client review meeting preparation (agenda, performance report)
5. Post-meeting action tracking (trades, documentation, follow-up)

Each workflow maps to a distinct set of FSC features. Financial planning uses `FinancialGoal`, `FinancialPlan`, and `ActionPlan` for review cadence. Portfolio review uses `FinancialHolding`, integration with custodian data feeds, and advisor reporting tools. Requirements discovery must separate these two categories to avoid scope conflation.

### Action Plans for Repeatable Advisor Workflows

`ActionPlan` and `ActionPlanTemplate` are the FSC mechanism for creating and tracking repeatable advisor workflows such as annual client reviews, client onboarding checklists, and KYC document collection sequences. Requirements discovery for advisor tools must determine:
- Which review workflows should be standardized as templates
- What task list each template should contain
- Whether tasks have sequential dependencies or can be completed in parallel
- Who is responsible for each task (advisor, client, compliance, operations)
- What records (Account, FinancialAccount, FinancialGoal) each Action Plan should be associated with

---

## Common Patterns

### Pattern: Architecture Determination Workshop

**When to use:** At the start of every FSC wealth management engagement, before any other requirements activity.

**How it works:**
1. Ask: "Is this a net-new FSC implementation or an existing FSC org?" If existing, run `SELECT Id, Name FROM Organization` and check field API names on any FSC object to confirm namespace.
2. Ask: "Are any third-party custodian data or portfolio management packages installed or under evaluation?" List them. Validate each against the Salesforce AppExchange for FSC Core certification.
3. Ask: "Is unlimited multi-owner account support required (e.g., trusts, family LLCs with more than two owners)?" If yes, FSC Core's `FinancialAccountParty` junction is the only supported path.
4. Document the architecture decision and its rationale in the requirements document. All subsequent object names, workflow descriptions, and integration scope should reference the confirmed model.

**Why not to skip this step:** Requirements written with managed-package object names (`FinServ__FinancialGoal__c`) will fail silently in a Core FSC org where the object is `FinancialGoal`. This causes integration errors, broken SOQL in validation rules, and miscommunication between admins and developers.

### Pattern: Advisor Tooling Discovery Interview

**When to use:** When gathering requirements for advisor-facing features: record pages, action plans, financial goal tracking, household views, and performance reporting.

**How it works:**
1. **Current state questions:** "Walk me through a typical client review. What do you look up first? What do you manually check before the meeting? What do you need to document after?"
2. **Pain point questions:** "What information is missing from your current view? What do you have to log into multiple systems to find? What falls through the cracks between meetings?"
3. **Automation questions:** "Which parts of the review process should be automatic? What should Salesforce remind you to do and when?"
4. **Volume questions:** "How many clients do you manage? How many reviews do you do per week? How many accounts per client household?"
5. Map each answer to a specific FSC feature or a gap:
   - Household summary view → `AccountFinancialSummary` (Core) or custom rollup (managed package)
   - Annual review checklist → `ActionPlan` + `ActionPlanTemplate`
   - Goal progress tracking → `FinancialGoal` with target amount and target date
   - Portfolio performance → `FinancialHolding` + custodian feed integration

**Why volume matters for requirements:** Advisors managing 200+ households with weekly reviews create significant Action Plan record volume. This surfaces data storage requirements, SOQL governor limit considerations for batch processing, and list view performance design decisions that must be captured at the requirements stage.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Architecture is unknown at requirements start | Confirm managed package vs. Core before writing any object names | Wrong namespace = broken integrations and code |
| Org needs more than two account owners per account | Recommend FSC Core with FinancialAccountParty junction | Managed package limits ownership to two lookup fields |
| Third-party custodian ISV package is in scope | Validate the package for FSC Core support before committing to Core | Not all ISV packages are certified for Core as of Spring '26 |
| Requirement is "see total household AUM" | Map to AccountFinancialSummary (Core) or Apex rollup (managed package); note which architecture it requires | AccountFinancialSummary is Core-only |
| Advisor wants repeatable annual review checklist | Scope ActionPlan + ActionPlanTemplate; confirm which records they attach to | Standard FSC pattern; do not scope custom Flow or Apex for this |
| Business wants financial goals linked to a formal plan | Scope FinancialGoal + FinancialPlan objects; confirm whether financial planning module license is included | FinancialPlan may require a separate FSC license tier |
| Requirement involves custodian data feed | Separate as an integration requirement; document source system, format (CSV/API), frequency, and field mapping | Custodian feeds are integration scope, not FSC configuration scope |
| Stakeholder requests custom "portfolio dashboard" | Scope as a reporting/CRM Analytics requirement, not a core FSC feature; document data source (FinancialHolding) | CRM Analytics for FSC has separate license requirements |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. **Confirm FSC architecture** — determine whether the org uses managed package (FinServ__ namespace) or FSC Core (no namespace, Winter '23+). All subsequent requirements must reference the confirmed model.
2. **Scope FSC objects** — work through the FSC object table in Core Concepts, confirming which objects are in scope for this engagement. Document in-scope and out-of-scope objects explicitly.
3. **Conduct advisor tooling discovery** — interview advisor personas using the Advisor Tooling Discovery Interview pattern. Map each workflow step to a specific FSC feature or flag as a gap.
4. **Map financial planning and portfolio review workflows separately** — use the workflow categories in Core Concepts to avoid conflating goal-based planning requirements with performance-monitoring requirements.
5. **Validate ISV package compatibility** — if any third-party packages are in scope, confirm FSC Core certification status before finalizing architecture recommendation.
6. **Produce fit-gap analysis** — classify each requirement as Standard FSC Feature, FSC Configuration, Custom Development, or Integration Scope.
7. **Review against checklist** — run through the Review Checklist below before handing off requirements to the build team.

---

## Review Checklist

Run through these before handing requirements to the build team:

- [ ] FSC architecture (managed package vs. FSC Core) is confirmed and documented with rationale
- [ ] All object API names in requirements documents match the confirmed FSC architecture (no mixing of FinServ__ and no-namespace names)
- [ ] FinancialAccount types in scope are listed (investment, deposit, insurance, loan) with record type and page layout implications noted
- [ ] Financial account ownership model is confirmed: two-owner (managed package) vs. unlimited via FinancialAccountParty junction (FSC Core)
- [ ] Financial planning workflow and portfolio review workflow are documented as separate process flows
- [ ] ActionPlan template requirements are captured: which workflows, which tasks, which record associations
- [ ] All third-party ISV packages are listed and validated for FSC Core compatibility if Core is the chosen architecture
- [ ] AccountFinancialSummary requirements (if any) are flagged as Core-only and the PSL integration user requirement is noted
- [ ] Custodian data feed requirements are documented as integration scope (source, format, frequency, field mapping)
- [ ] Advisor volume data is captured: number of clients, review frequency, accounts per household

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Namespace mismatch between requirements and implementation** — If requirements are written with managed-package object names (`FinServ__FinancialGoal__c`) but the org runs FSC Core, every SOQL query, every validation rule field reference, and every integration mapping will fail silently or with a confusing error. Confirm the architecture once and enforce consistent naming throughout the requirements document.

2. **AccountFinancialSummary requires a dedicated integration user** — FSC Core's `AccountFinancialSummary` object is not populated by standard user activity. It requires a dedicated FSC PSL (Platform Service Layer) integration user to run the rollup aggregation. Requirements that assume advisors will see household-level AUM automatically without this setup will not behave as expected after go-live.

3. **Managed package ownership limits break complex household structures** — Managed-package FSC financial accounts support exactly two ownership lookup fields (Primary Owner, Joint Owner). Requirements for trusts, partnerships, or family accounts with three or more named owners cannot be met with the managed package model without custom fields that break rollup behavior. Surface this constraint during requirements, not during UAT.

4. **FinancialPlan licensing is not always included** — The `FinancialPlan` object and the financial planning module may require a separate FSC license add-on depending on the customer's contract. Gathering requirements for financial plans without confirming license entitlement leads to scope surprises. Verify with Salesforce AE or review the order form before scoping FinancialPlan features.

5. **ActionPlan volume drives list view and query performance** — If an advisor manages 300 clients each with an annual review Action Plan generating 10 tasks, that is 3,000 open task records per advisor. At scale across a firm, this creates significant record volume that affects list view performance, report query time, and batch job governor limits. Volume must be captured during requirements discovery, not treated as an afterthought.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| FSC architecture determination memo | Documents the confirmed architecture (managed package vs. FSC Core), the decision rationale, and the naming convention to use throughout the project |
| FSC object scope table | Lists every in-scope FSC object with its correct API name for the confirmed architecture, ownership model, and rollup behavior |
| Wealth management process maps | Separate swimlane diagrams or step narratives for (1) financial planning lifecycle and (2) portfolio review cadence, each step mapped to a specific FSC feature |
| Advisor tooling requirements set | Salesforce-ready user stories for advisor-facing features with persona, object, field, and automation context |
| ISV package compatibility checklist | List of all in-scope third-party packages with FSC Core certification status and any open validation items |
| Fit-gap analysis table | Every requirement classified as Standard FSC Feature, FSC Configuration, Custom Development, or Integration Scope |

---

## Related Skills

- financial-account-setup — use after requirements are gathered to configure FinancialAccount types, roles, and household rollup behavior
- fsc-action-plans — use to implement ActionPlan and ActionPlanTemplate once workflow requirements are documented
- architect/wealth-management-architecture — use when technical architecture decisions (feature flags, data model, Compliant Data Sharing) are needed alongside or after requirements
- apex/fsc-financial-calculations — use when requirements surface custom rollup or portfolio calculation needs that FSC Core Record Rollups cannot meet
- requirements-gathering-for-sf — use for general Salesforce requirements gathering methodology; this skill is the FSC wealth management specialization of that skill
