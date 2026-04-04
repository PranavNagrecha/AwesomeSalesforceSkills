---
name: requirements-gathering-for-sf
description: "Use this skill when eliciting, documenting, and structuring requirements for a Salesforce implementation or enhancement: writing Salesforce-specific user stories with acceptance criteria, mapping As-Is and To-Be business processes, conducting stakeholder discovery interviews, and performing gap analysis against standard Salesforce capabilities. Trigger keywords: requirements gathering, user story, As-Is To-Be, gap analysis, stakeholder interview, process mapping, business requirements, fit gap. NOT for technical design decisions (use solution-design-patterns). NOT for automation implementation (use flow/* or apex/* skills). NOT for data model design (use data-model-design-patterns or object-creation-and-design)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - User Experience
triggers:
  - "how do I write user stories for a Salesforce implementation project"
  - "what questions should I ask stakeholders before building in Salesforce"
  - "how to document As-Is and To-Be process for a Salesforce project"
  - "how to do a gap analysis between current system and Salesforce"
  - "user story format for Salesforce features with acceptance criteria"
  - "how to map business processes to Salesforce objects and automation"
  - "what does a BA need to gather before a Salesforce admin starts building"
tags:
  - requirements-gathering
  - business-analysis
  - user-stories
  - process-mapping
  - gap-analysis
inputs:
  - "Business domain or feature area under analysis (e.g., Lead-to-Opportunity process, Case management)"
  - "List of stakeholder roles to interview (e.g., sales reps, support agents, managers)"
  - "Existing documentation: current process SOPs, data dictionaries, or system screenshots"
  - "Project scope: which Salesforce clouds or feature areas are in scope"
outputs:
  - "Completed user story set in Salesforce-ready format with acceptance criteria"
  - "As-Is process diagram or narrative with pain points annotated"
  - "To-Be process narrative mapped to specific Salesforce features"
  - "Fit-gap analysis table: requirement vs Salesforce capability vs effort classification"
  - "Stakeholder interview question set for the feature domain"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-03
---

# Requirements Gathering for Salesforce

This skill activates when a Business Analyst (BA) or admin needs to elicit, structure, and document requirements before building in Salesforce. It covers discovery interviews, user story authoring with Salesforce-specific acceptance criteria, As-Is / To-Be process mapping, and fit-gap analysis against standard platform capabilities.

---

## Before Starting

Gather this context before conducting discovery:

- **What is the trigger for this project?** Understand whether it is a greenfield implementation, an enhancement to an existing org, a migration from a legacy system, or a post-release fix. Each context changes what questions to ask and which stakeholders to prioritize.
- **Who are the actual end users?** Salesforce has distinct personas: sales reps, service agents, managers, data stewards, and admins. Requirements differ sharply by persona. Avoid gathering requirements only from managers — the people who will use the system daily have different needs than those who sponsor it.
- **What constraints exist?** Platform limits (objects, fields, automation), licensing tier, existing technical debt, and integration dependencies all bound what is buildable. Establish these early to avoid promising what cannot be delivered declaratively.

---

## Core Concepts

### Salesforce-Specific User Story Format

Generic agile user stories ("As a user, I want X so that Y") are insufficient for Salesforce because they do not capture the platform-specific decisions required before building. A Salesforce user story must answer:

1. **Who** — which Salesforce profile, permission set, or role
2. **What object** — which standard or custom object is involved
3. **What fields** — which fields need to be visible, editable, or required
4. **What automation** — what should happen automatically (Flow, validation rule, approval)
5. **What sharing** — who else needs to see or edit this record

A complete Salesforce user story format:

```
As a [persona with Salesforce role/profile context],
I want [feature involving specific Salesforce object/field/automation],
So that [business outcome].

Acceptance Criteria:
- [ ] If on [page/screen], then [specific Salesforce field/button] is visible and editable for [profile/permission set]
- [ ] If [condition], then [validation rule or automation] fires with error message "[text]"
- [ ] If [user with role], then record is accessible under [sharing rule or OWD setting]
- [ ] If [filter criteria], then [report or list view] returns records with [specific fields]
```

Salesforce Trailhead specifies the **if/then format** for acceptance criteria: each criterion takes the form "If [condition], then [observable Salesforce outcome]." This format ensures every criterion is independently testable with a boolean pass/fail result — suitable for UAT without interpretation. A story is an invitation to a conversation, not a contract; do not over-specify which Flow type or which Apex class will implement it.

**INVEST quality check:** Every Salesforce user story should meet the INVEST criteria — Independent (not blocked by another incomplete story), Negotiable (implementation detail is flexible), Valuable (delivers a business outcome), Estimable (the build team can size it), Small (fits in a sprint), Testable (acceptance criteria are boolean pass/fail). Stories that fail INVEST — especially "not independent" due to platform dependencies like page layout depending on record type completion — should be split or reordered in the backlog.

This format forces discovery of FLS, page layout, and sharing requirements at the story level — not as a surprise during UAT.

### As-Is / To-Be Process Mapping

As-Is mapping documents how the business currently operates — often in spreadsheets, email, or a legacy CRM. It is essential to capture:
- Who does what, in what order
- Where handoffs between teams occur
- Where data is duplicated or lost
- Where manual steps are error-prone

To-Be mapping documents how the same process will operate in Salesforce. Each step of the To-Be process should reference a specific Salesforce feature: a screen flow, a record-triggered flow, an approval process, a queue, a report, or a dashboard.

**Mapping notation:** Salesforce Trailhead recommends **Universal Process Notation (UPN)** as the preferred notation for BA process maps. UPN answers "Who needs to do what, when, why, and how?" in a single readable diagram. Each activity box uses a verb phrase and contains a named resource (the who). Lines between boxes represent handoffs with explanatory text. Limit each diagram to **8–10 activity boxes**; drill down to child diagrams for complex sub-processes. UPN is preferred over BPMN because it has fewer symbols and is readable left-to-right without specialized training.

For swimlane diagrams: one lane per persona (e.g., Sales Rep | Salesforce System | ERP System). Label each step with the Salesforce feature that will execute it. Steps with no Salesforce equivalent are gaps.

**Transition state:** The official Salesforce BA methodology requires three states, not two: As-Is (current), To-Be (target end state), and **Transition State** (how the org and team will operate during the migration from As-Is to To-Be). Omitting the transition state is a common gap in requirements packages that causes go-live disruption when the old process ends before the new one is stable.

### Fit-Gap Analysis

A fit-gap analysis compares each business requirement against what standard Salesforce delivers. Classification:

| Fit Type | Definition | Action |
|---|---|---|
| Standard Fit | Salesforce delivers it out-of-the-box with configuration | Configure, no custom code |
| Configuration Gap | Salesforce requires setup (custom field, flow, validation rule) | Admin builds |
| Customization Gap | Requirement needs Apex, LWC, or a managed package | Dev work or AppExchange |
| Process Gap | Requirement is not a Salesforce capability — it is a business process change | Stakeholder decision required |

Identifying process gaps early is the most valuable BA output. A requirement that cannot be met with any Salesforce feature needs to be renegotiated with the business, not coded around.

---

## Common Patterns

### Pattern: Discovery Interview for a New Salesforce Feature

**When to use:** When starting a new user story or feature with a stakeholder who has never used Salesforce before, or when requirements are vague.

**How it works:**
1. **Current state questions:** "Walk me through exactly what you do today when [business event occurs]. What system do you use? What data do you enter? Who else is involved?"
2. **Pain point questions:** "Where does this process break down? What takes the most time? What data do you wish you had but don't?"
3. **Future state questions:** "If this worked perfectly, what would the process look like? What would you see on your screen? What would happen automatically?"
4. **Volume and frequency questions:** "How many records are created per day/week/month? How many people do this? What is the peak load?"
5. **Exception questions:** "What are the edge cases? What should NOT happen automatically? Who handles exceptions?"
6. Map each answer to a Salesforce concept: object, field, automation, sharing rule, report.

**Why not to skip volume questions:** Volume determines whether a declarative solution (Flow) is safe or whether Apex/Bulk API is required. 10,000 records per day triggers governor limit conversations that a BA must surface early.

### Pattern: Fit-Gap Workshop

**When to use:** When a list of requirements exists and the team needs to classify which are standard, which need configuration, and which need custom code — before sprint planning.

**How it works:**
1. List all requirements as rows in a table (one per user story or business rule).
2. For each requirement, check Salesforce Help and Trailhead for the standard feature that addresses it.
3. Classify each requirement: Standard Fit / Configuration Gap / Customization Gap / Process Gap.
4. For Customization Gaps, note the AppExchange options before defaulting to custom development.
5. Summarize by type: # standard, # config, # custom, # process. This becomes the basis for sizing.
6. Flag any requirement that cannot be met with standard Salesforce as a stakeholder decision — do not let these requirements silently become custom code.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Requirement seems like a Salesforce feature but is unclear | Map to a specific Salesforce Help article or Trailhead module | Prevents gold-plating and scope creep |
| Stakeholders describe what the UI should look like | Redirect to the business outcome they want to achieve | UI is Salesforce's responsibility; the BA captures the business need |
| Two stakeholders give conflicting requirements | Escalate as a documented conflict; do not pick a side | The BA surfaces conflicts; the business owner resolves them |
| Requirement has no Salesforce equivalent | Classify as process gap; present to stakeholders for redesign | Never silently code around a process gap |
| Volume exceeds 50,000 records per day | Flag as a data volume / governor limit concern for an architect | BA must surface performance-sensitive requirements early |
| Requirement involves data from an external system | Capture integration requirements separately: source, frequency, direction, transformation | Integration requirements need separate discovery from UI requirements |
| Stakeholder requests a feature in a legacy tool | Map to Salesforce equivalent; document the mapping explicitly | Stakeholders think in legacy system terms; BA translates to Salesforce terms |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before handing requirements to the build team:

- [ ] Every user story includes: persona with profile/permission set context, specific Salesforce object, field-level requirements, automation requirements, and sharing/visibility requirements
- [ ] Every user story has acceptance criteria that can be tested in a sandbox without ambiguity
- [ ] As-Is process has been reviewed with at least one actual end user (not just a manager)
- [ ] To-Be process maps each step to a specific Salesforce feature (not just "Salesforce does it")
- [ ] Fit-gap table is complete: every requirement classified as Standard, Configuration, Customization, or Process gap
- [ ] All Customization Gaps have been reviewed for AppExchange alternatives before accepting as custom development
- [ ] All Process Gaps have been escalated to a business owner for a decision
- [ ] Volume and frequency have been captured for all automation requirements
- [ ] Integration requirements are documented separately with source system, direction, frequency, and data mapping
- [ ] Reporting and dashboard requirements are documented as separate stories

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Requirements written for the wrong persona** — BAs often interview managers, not end users. Managers describe what they want to see in reports. Sales reps describe what they want to see on a record page. Both are valid but produce entirely different requirements. If stories are written from the manager's perspective only, the resulting build frustrates end users and drives low adoption.

2. **"Make it automatic" requirements that hide complexity** — Stakeholders often request "it should just happen automatically" without understanding the trigger, the conditions, or the exception path. Before accepting any automation requirement, a BA must capture: the exact record trigger (created, updated, deleted), the field condition, what happens to exceptions, and who is notified when the automation fails. Undiscovered exception paths surface in UAT as blocking defects.

3. **Process gaps misclassified as configuration work** — Occasionally a business requirement has no Salesforce equivalent and no configuration workaround. For example, "the system should prevent a rep from creating an Opportunity if the Account credit limit is exceeded" sounds like a validation rule, but credit limits live in an ERP, not Salesforce. Without the integration requirement being surfaced as a gap, an admin may build a placeholder validation rule with hardcoded values — creating technical debt and the wrong behavior. Always ask "where does this data live?" before classifying a requirement.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| User story set | Salesforce-ready user stories with persona, object, field, automation, and sharing context; includes acceptance criteria per story |
| As-Is process narrative/diagram | Swimlane diagram or step list documenting the current process, annotated with pain points |
| To-Be process narrative | Future state process with each step mapped to a named Salesforce feature |
| Fit-gap analysis table | Complete classification of every requirement: Standard Fit, Configuration Gap, Customization Gap, or Process Gap |
| Stakeholder interview notes | Raw and summarized notes organized by stakeholder, with unresolved conflicts flagged |

---

## Related Skills

- process-mapping-and-automation-selection — use after requirements are gathered to select the correct automation approach for each automation requirement
- data-model-documentation — use to document the resulting object/field model once requirements are clear
- uat-and-acceptance-criteria — use to translate the acceptance criteria in user stories into structured UAT test scripts
- solution-design-patterns — use when requirements are complete and technical design choices must be made
