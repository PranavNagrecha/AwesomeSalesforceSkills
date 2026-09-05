---
name: requirements-gathering-for-sf
description: "Eliciting, documenting and structuring requirements for a Salesforce implementation: stakeholder discovery interviews, As-Is and To-Be process mapping, and gap analysis against standard Salesforce capability. Trigger keywords: requirements gathering, user story, As-Is To-Be, gap analysis, stakeholder interview, process mapping, business requirements, fit gap. NOT for authoring the user stories themselves - use admin/user-story-writing-for-salesforce. NOT for scoring requirements against a specific org - use admin/fit-gap-analysis-against-org. NOT for technical design decisions - use architect/solution-design-patterns. Also covers the requirements catalogue itself (one row per requirement, MoSCoW priority, source stakeholder, downstream target) and Salesforce non-functional requirements: record volume, sharing layer, integration pattern, reporting joins, mobile/offline, and licence implication."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - User Experience
triggers:
  - "how do I write user stories for a Salesforce implementation project"
  - "user story format for Salesforce features with acceptance criteria"
  - "gather requirements for a salesforce implementation"
  - "what questions should I ask stakeholders before building in Salesforce"
  - "run a discovery interview for a Salesforce project"
  - "build a requirements catalogue that feeds user stories and fit-gap"
  - "capture non-functional requirements for a Salesforce implementation"
  - "requirement came in as build a trigger and skipped the automation decision"
  - "stakeholder said only managers should see it and the sharing model came out wrong"
  - "UAT surfaced a record volume nobody captured during requirements"
  - "licence cost discovered after the solution design was signed off"
  - "how to document As-Is and To-Be process for a Salesforce project"
  - "what does a BA need to gather before a Salesforce admin starts building"
tags:
  - requirements-gathering
  - business-analysis
  - elicitation
  - requirements-catalogue
  - non-functional-requirements
  - process-mapping
  - gap-analysis
inputs:
  - "Business domain or feature area under analysis (e.g., Lead-to-Opportunity process, Case management)"
  - "List of stakeholder roles to interview (e.g., sales reps, support agents, managers)"
  - "Existing documentation: current process SOPs, data dictionaries, or system screenshots"
  - "Project scope: which Salesforce clouds or feature areas are in scope"
  - "Known constraints: org edition, licence types already owned, integration inventory"
outputs:
  - "Requirements catalogue: one row per requirement with type, object/field candidates, automation candidate, sharing impact, volume, licence implication, source stakeholder, MoSCoW priority, status, and downstream target"
  - "Salesforce NFR sheet: the platform fact that bounds each non-functional requirement"
  - "Stakeholder interview guide with Salesforce-aware probes for the feature domain"
  - "As-Is / To-Be summary table with the transition state named"
  - "Handoff map: which catalogue rows go to which downstream skill or agent"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-04
---

# Requirements Gathering for Salesforce

This skill activates when a Business Analyst (BA) or admin needs to elicit, structure, and document requirements before building in Salesforce. It owns **elicitation and the requirements catalogue**: discovery interviews, As-Is / To-Be discovery, Salesforce-specific non-functional requirements, and the catalogue rows that feed story writing, fit-gap and the configuration workbook.

The downstream artefacts are owned elsewhere and are cited, not duplicated: story shape by `admin/user-story-writing-for-salesforce`, Given/When/Then criteria by `admin/acceptance-criteria-given-when-then`, the org-scored classification by `admin/fit-gap-analysis-against-org`, the swim-lane diagram by `admin/process-flow-as-is-to-be`, the traceability grid by `admin/requirements-traceability-matrix`, and the 10-section handoff by `admin/configuration-workbook-authoring`.

---

## Before Starting

Gather this context before conducting discovery:

- **What is the trigger for this project?** Understand whether it is a greenfield implementation, an enhancement to an existing org, a migration from a legacy system, or a post-release fix. Each context changes what questions to ask and which stakeholders to prioritize.
- **Who are the actual end users?** Salesforce has distinct personas: sales reps, service agents, managers, data stewards, and admins. Requirements differ sharply by persona. Avoid gathering requirements only from managers — the people who will use the system daily have different needs than those who sponsor it.
- **What constraints exist?** Platform limits (objects, fields, automation), licensing tier, existing technical debt, and integration dependencies all bound what is buildable. Establish these early to avoid promising what cannot be delivered declaratively.
- **Who decides?** A requirement with no named decision-maker cannot be closed. `admin/stakeholder-raci-for-sf-projects` owns the authority map; this skill consumes it to fill the `source_stakeholder` column and to route conflicts.

---

## Questions to Ask Before Configuring

Ask these in the interview, before any story, workbook row or Setup change exists. Each one exists because skipping it produces a specific, documented failure — the gotcha number is named.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Walk me through what you do today — what do you type, where, and what do you do next?" | Stakeholders describe the *workaround* they built around the legacy tool as if it were the requirement (Gotcha 10) | An As-Is step list where each step is tagged keep / drop / replace, so the To-Be is not a re-implementation |
| "When you say only managers see it — can others not open the record at all, or can they open it but should not see that number?" | Record access and field access are different mechanisms configured in different places; and "record access" itself is seven ordered layers (Gotchas 2 and 6) | A `sharing_impact` value that names the layer — OWD, role hierarchy, sharing rule, team, manual/Apex, restriction — plus a separate FLS row |
| "How many of these exist today, how many are created a day, and what is the biggest single batch anyone has ever pushed?" | Automation that passes UAT on ten records fails on a 10,000-record Bulk API load; the transaction limits are shared by Flow and Apex (Gotcha 4) | A `data_volume` value with a steady-state number and a worst-case batch number, which decides sync vs async |
| "Where does this data live right now — in Salesforce, or in another system?" | A requirement sourced from an ERP or billing system is an integration requirement wearing a validation-rule costume, and needs a pattern decision before sizing (Gotchas 3 and 8) | An integration row naming direction, volume, latency tolerance, and the `integration-pattern-selection` branch |
| "Who exactly does this — an employee, a customer, a partner, or a contractor?" | The answer selects a licence, and licence selects API allocation, object access and portal template long before design starts (Gotcha 9) | A `licence_implication` value, and an escalation to `architect/license-optimization-strategy` when the answer is not an employee |
| "What number do you need out of this, and what has to appear on the same row as it?" | Reporting requirements assume joins the report-type rules forbid; a four-object chain is the ceiling (Gotcha 7) | A reporting row that names base object, the join chain, and whether rows must appear with no related record |
| "What must NOT happen automatically, and who fixes it when the automation is wrong?" | "Make it automatic" hides the trigger, the condition, the exception path and the owner of the failure | The exception path and a named owner, which is what makes the automation row estimable |

What a proper requirements catalogue adds over a list of bullet points: every row carries the five Salesforce facts (object, automation tier, sharing layer, volume, licence) that a downstream agent needs to act without re-interviewing the stakeholder, and every row has exactly one downstream target so nothing is silently dropped between discovery and build.

---

## Core Concepts

### The Requirements Catalogue — One Row Per Requirement

The catalogue is this skill's primary artefact. It is a flat, machine-lintable list — not prose — because every downstream consumer reads rows, not paragraphs.

| Column | Purpose | Consumed by |
|---|---|---|
| `id` | Stable `REQ-nnn` identity; never renumbered | `admin/requirements-traceability-matrix` |
| `statement` | The requirement in the stakeholder's own outcome language, not a solution | all |
| `type` | `functional` or `nfr` | all |
| `source_stakeholder` | Named person and role — not "the business" | conflict routing, `admin/stakeholder-raci-for-sf-projects` |
| `objects` / `fields` | Candidate standard or custom objects and fields, marked as candidates | `agents/object-designer`, `agents/config-workbook-author` |
| `automation_candidate` + `decision_tree_step` | The tier and the branch of `standards/decision-trees/automation-selection.md` that produced it | `agents/flow-builder`, `agents/apex-builder` |
| `sharing_impact` + `sharing_layer` | Which of the seven layers in `standards/decision-trees/sharing-selection.md` is being asked for | `agents/permission-set-architect`, `agents/access-path-explainer` |
| `data_volume` | Steady-state and worst-case batch | `agents/data-loader-pre-flight`, `architect/large-data-volume-architecture` |
| `licence_implication` | Employee / Customer Community / Partner Community / platform-only | `architect/license-optimization-strategy` |
| `priority` | MoSCoW — `Must` / `Should` / `Could` / `Wont` | `admin/moscow-prioritization-for-sf-backlog` |
| `status` | `draft` / `confirmed` / `deferred` / `descoped` / `blocked` | steering-committee reporting |
| `downstream` | Story id, fit-gap row id, and/or workbook section | `agents/story-drafter`, `agents/fit-gap-analyzer`, `agents/config-workbook-author` |

A filled catalogue, an NFR sheet and the handoff map are in `references/worked-examples.md`. Lint any catalogue with `scripts/check_requirements_catalogue.py`.

**Capture candidates, not decisions.** `objects` and `automation_candidate` are hypotheses the BA records so the downstream agent has a starting point and a reason to disagree. The BA does not own the Flow-vs-Apex call — the tree and the builder agent do. What the BA owns is that the row *names a tree step at all*, so the decision is visible rather than assumed.

### Salesforce Non-Functional Requirements

Generic NFR checklists (performance, availability, security) do not survive contact with a multitenant platform. Six NFR classes matter on a Salesforce project, and each is bounded by a specific platform fact that must be written next to the requirement:

| NFR class | Elicit | Bounding platform fact to record beside it |
|---|---|---|
| Record volume | Steady-state count, growth rate, worst-case single batch | Per-transaction limits are shared by Flow and Apex: 100 SOQL sync / 200 async, 50,000 rows retrieved, 150 DML statements, 10,000 records processed by DML (App Limits, Per-Transaction Apex Limits) |
| Data movement | Who loads, how often, how many rows | "Any data operation that includes more than 2,000 records is a good candidate for Bulk API 2.0… Jobs with fewer than 2,000 records should involve 'bulkified' synchronous calls in REST… or SOAP" (App Limits, Bulk API section) |
| Integration | Direction, latency tolerance, volume, ownership of the record | Total API calls per 24 h in Enterprise Edition = 100,000 + (licences × calls per licence type) + purchased add-ons; a Salesforce licence contributes 1,000 in EE and 5,000 in UE/PE (App Limits, API Request Limits) |
| Sharing / visibility | Who must see the record, who must not, and who must see the field | The seven ordered layers in `standards/decision-trees/sharing-selection.md`; naming a layer is the requirement, "only managers" is not |
| Reporting | The number, the grain, and what must appear on the same row | "A maximum of four objects can be joined in a custom report type. When more than two objects are joined, an inner join isn't allowed if there has been an outer join earlier in the join sequence" (Metadata API Developer Guide, `ObjectRelationship`) |
| Licence / persona | Employee, customer, partner, contractor, unauthenticated | API calls per licence per 24 h: Customer Community 0, Customer Community Login 0, Customer Community Plus 200, Partner Community 200, Partner Community Login 10 (App Limits, API Request Limits) |

Storage is deliberately absent from that table: the Developer Limits quick reference states up front that it does not cover contractual limits, so data and file storage allocations must be read from the org's own Storage Usage page rather than quoted from a guide.

Mobile and offline capture belongs in the interview — which steps happen away from a desk, and whether the user can be assumed online — but the capability that satisfies it is org-specific. UNVERIFIED (2026-09-04): no offline-entry limit or allocation appears in the eight extracted Salesforce guides used to ground this skill; confirm the org's mobile configuration before promising offline data entry.

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

This format forces discovery of FLS, page layout, and sharing requirements at the story level — not as a surprise during UAT. The story *shape* and the splitting techniques belong to `admin/user-story-writing-for-salesforce`; what this skill owns is that the catalogue row feeding the story already carries the object, automation, sharing and volume facts.

### As-Is / To-Be Process Mapping

As-Is mapping documents how the business currently operates — often in spreadsheets, email, or a legacy CRM. It is essential to capture:
- Who does what, in what order
- Where handoffs between teams occur
- Where data is duplicated or lost
- Where manual steps are error-prone

To-Be mapping documents how the same process will operate in Salesforce. Each step of the To-Be process should reference a specific Salesforce feature: a screen flow, a record-triggered flow, an approval process, a queue, a report, or a dashboard.

**Mapping notation:** Salesforce Trailhead recommends **Universal Process Notation (UPN)** as the preferred notation for BA process maps. UPN answers "Who needs to do what, when, why, and how?" in a single readable diagram. Each activity box uses a verb phrase and contains a named resource (the who). Lines between boxes represent handoffs with explanatory text. Limit each diagram to **8–10 activity boxes**; drill down to child diagrams for complex sub-processes. UPN is preferred over BPMN because it has fewer symbols and is readable left-to-right without specialized training.

**Where the diagram lives:** this skill produces the As-Is / To-Be *summary table* — one row per step, with the pain point, the Salesforce feature and the catalogue row it generated. The swim-lane diagram itself, its lane rules, decision diamonds, sad paths and automation-tier annotations belong to `admin/process-flow-as-is-to-be` and `agents/process-flow-mapper`. Hand the summary table over; do not draw the lanes here.

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

This four-way split is the BA's *pre-org* read, made from the requirement alone. The five-tier scoring against an actual org — with effort tier, risk tag and AppExchange suggestion — is `admin/fit-gap-analysis-against-org` and `agents/fit-gap-analyzer`, which refuse to run without a target org alias. Feed them catalogue rows; do not pre-empt their tiers.

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

### Pattern: The Solution-to-Requirement Rewind

**When to use:** When the stakeholder has arrived with a solution — "build a trigger", "we need a custom object for this", "just add a checkbox" — instead of a requirement.

**How it works:**
1. Write the sentence down verbatim in the interview notes; do not correct it in the room.
2. Ask "what happens today if that doesn't exist?" and "what would you see that tells you it worked?" The answers are the requirement.
3. Restate the requirement as an outcome and get the stakeholder to confirm it: the catalogue `statement` is the confirmed sentence, not the original.
4. Move the original solution into `automation_candidate` as a hypothesis, and walk `standards/decision-trees/automation-selection.md` from Q1 to record the step that actually resolves it.
5. If the tree lands somewhere other than the stakeholder's solution, record both in the row's notes. That difference is the conversation to have at design review, not at UAT.

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
| Requirement arrives phrased as a build ("add a trigger") | Run the Solution-to-Requirement Rewind, then record the `automation-selection` step | The tier is a tree decision, not a stakeholder preference |
| Requirement has no Salesforce equivalent | Classify as process gap; present to stakeholders for redesign | Never silently code around a process gap |
| Volume exceeds 50,000 records per day | Flag as a data volume / governor limit concern for an architect | BA must surface performance-sensitive requirements early |
| Requirement involves data from an external system | Capture integration requirements separately: source, frequency, direction, transformation, and the `integration-pattern-selection` branch | Integration requirements need separate discovery from UI requirements |
| Requirement names a non-employee user | Record the `licence_implication` before design; route to `architect/license-optimization-strategy` | Licence bounds object access and API allocation, and cannot be retro-fitted cheaply |
| Requirement is "a report showing X, Y and Z together" | Record base object and join chain; check the four-object ceiling before promising it | The join chain is a report-type constraint, not a report-builder one |
| Stakeholder requests a feature in a legacy tool | Map to Salesforce equivalent; document the mapping explicitly, and mark whether the legacy behaviour was a workaround | Stakeholders think in legacy system terms; BA translates to Salesforce terms |

---

## Recommended Workflow

1. **Frame the scope and the deciders.** Name the process, the clouds in scope, and — from `admin/stakeholder-raci-for-sf-projects` — the one accountable owner per decision area. Open `templates/requirements-gathering-for-sf-template.md` and fill the Project Context block. A scope with no named decider produces rows that can never leave `status: draft`.
2. **Run the interviews from the seven questions.** Work the `## Questions to Ask Before Configuring` table with each persona separately — end users first, managers second. Record answers verbatim; do not translate to Salesforce terms in the room. The interview guide in `references/worked-examples.md` shows the Salesforce-aware probe under each question.
3. **Write the As-Is / To-Be summary table, including the transition state.** One row per step: actor, what happens today, the pain point, the To-Be Salesforce feature, and the `REQ-` ids that step generated. Hand the table to `admin/process-flow-as-is-to-be` for the swim-lane diagram rather than drawing lanes here.
4. **Build the catalogue.** One row per requirement in the shape above. For every row that names a mechanism, walk `standards/decision-trees/automation-selection.md` or `sharing-selection.md` and record the step id. For every external-data row, record the `integration-pattern-selection` branch. Copy the YAML skeleton from `templates/requirements-catalogue.yaml`.
5. **Fill the NFR sheet.** For each of the six NFR classes, write the requirement and the bounding platform fact beside it. Any row without a number is not yet an NFR — go back to the stakeholder.
6. **Lint.** Run `python3 scripts/check_requirements_catalogue.py --file requirements-catalogue.yaml` (or `--manifest-dir docs/discovery/`). It fails on missing required fields, duplicate ids, non-MoSCoW priorities, rows with no stakeholder, rows with no downstream target, automation rows with no decision-tree step, sharing rows that name no layer, and NFR rows with no measure. Fix every ERROR before handing off.
7. **Publish the handoff map and hand over.** Map each catalogue row to exactly one of `agents/story-drafter`, `agents/fit-gap-analyzer`, `agents/process-flow-mapper` or `agents/config-workbook-author`, then check the `## Review Checklist` below. A row with no target is a dropped requirement, not a finished one.

---

## Review Checklist

Run through these before handing requirements to the build team:

- [ ] Every catalogue row has an `id`, a `statement` in outcome language, a named `source_stakeholder`, a MoSCoW `priority`, a `status`, and at least one `downstream` target
- [ ] Every row that names an automation mechanism cites the `automation-selection` step that produced it
- [ ] Every visibility requirement names one of the seven sharing layers, and field-level requirements are recorded as separate rows from record-level ones
- [ ] Every automation requirement carries a steady-state volume and a worst-case batch number
- [ ] Every external-data requirement names direction, latency tolerance and an `integration-pattern-selection` branch
- [ ] Every reporting requirement names its base object and join chain, checked against the four-object ceiling
- [ ] Every row involving a non-employee user carries a `licence_implication`
- [ ] `python3 scripts/check_requirements_catalogue.py` reports zero ERRORs
- [ ] As-Is process has been reviewed with at least one actual end user (not just a manager)
- [ ] To-Be process maps each step to a specific Salesforce feature (not just "Salesforce does it"), and a transition state exists
- [ ] Fit-gap pre-read is complete: every requirement classified as Standard, Configuration, Customization, or Process gap, with Customization Gaps checked for AppExchange alternatives and Process Gaps escalated to a business owner
- [ ] Every "as today" requirement has been challenged: is this a business rule or a legacy workaround?

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Requirements written for the wrong persona** — BAs often interview managers, not end users. Managers describe what they want to see in reports. Sales reps describe what they want to see on a record page. Both are valid but produce entirely different requirements. If stories are written from the manager's perspective only, the resulting build frustrates end users and drives low adoption.

2. **"Make it automatic" requirements that hide complexity** — Stakeholders often request "it should just happen automatically" without understanding the trigger, the conditions, or the exception path. Before accepting any automation requirement, a BA must capture: the exact record trigger (created, updated, deleted), the field condition, what happens to exceptions, and who is notified when the automation fails. Undiscovered exception paths surface in UAT as blocking defects.

3. **Process gaps misclassified as configuration work** — Occasionally a business requirement has no Salesforce equivalent and no configuration workaround. For example, "the system should prevent a rep from creating an Opportunity if the Account credit limit is exceeded" sounds like a validation rule, but credit limits live in an ERP, not Salesforce. Without the integration requirement being surfaced as a gap, an admin may build a placeholder validation rule with hardcoded values — creating technical debt and the wrong behavior. Always ask "where does this data live?" before classifying a requirement.

The full set, with what happens / when it occurs / how to avoid, is in `references/gotchas.md`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Requirements catalogue | One row per requirement in the shape above: id, statement, type, source stakeholder, object/field candidates, automation candidate + tree step, sharing impact + layer, volume, licence implication, MoSCoW priority, status, downstream target |
| Salesforce NFR sheet | The six NFR classes with the elicited requirement and the platform fact that bounds it |
| Interview guide + notes | Salesforce-aware probes per question, raw notes per stakeholder, unresolved conflicts flagged with the RACI owner who must decide |
| As-Is / To-Be summary table | One row per process step: actor, today, pain point, To-Be Salesforce feature, generated `REQ-` ids, plus the named transition state; input to `admin/process-flow-as-is-to-be` |
| Fit-gap pre-read | Requirement-only classification (Standard / Configuration / Customization / Process) handed to `admin/fit-gap-analysis-against-org` for org-scored tiering |
| Handoff map | Which catalogue rows go to which downstream skill or agent, with the row ids listed per target |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/worked-examples.md` | You need the filled artefacts to copy: interview guide with Salesforce probes, the catalogue in YAML, the NFR sheet, the As-Is/To-Be summary and the handoff map, all for one scenario end to end |
| `references/gotchas.md` | A requirements package looked complete and the project still hit a sharing, volume, reporting, licence or integration surprise after sign-off |
| `references/examples.md` | Sizing a discovery effort: what a spreadsheet-to-Sales-Cloud migration and a Case-management enhancement each surfaced, and what happens when only the sponsor is interviewed |
| `references/llm-anti-patterns.md` | Reviewing AI-generated requirements, stories or process maps before acting on them |
| `references/well-architected.md` | Justifying discovery depth against the pillars, or locating the official source behind a claim in this skill |
| `templates/requirements-gathering-for-sf-template.md` | Running workflow steps 1–3 and 5 — project context, interview summary, As-Is/To-Be, NFR sheet, handoff map |
| `templates/requirements-catalogue.yaml` | Running workflow step 4 — the machine-lintable catalogue skeleton |
| `scripts/check_requirements_catalogue.py` | Workflow step 6, before any handoff to a downstream agent |

---

## Related Skills

- **admin/user-story-writing-for-salesforce**: Use once catalogue rows are confirmed and each must become an INVEST story with a stem, size and handoff metadata. NOT for elicitation.
- **admin/acceptance-criteria-given-when-then**: Use to convert a story into Given/When/Then criteria with permission and data-state preconditions. NOT for capturing the requirement itself.
- **admin/fit-gap-analysis-against-org**: Use to score the catalogue against a real org — five-tier classification, effort tier, risk tag, AppExchange suggestion. It refuses without a target org alias.
- **admin/process-flow-as-is-to-be**: Use to turn the As-Is/To-Be summary table into swim lanes with decision diamonds, sad paths and automation-tier annotations.
- **admin/requirements-traceability-matrix**: Use to carry `REQ-` ids forward to story, test and defect ids for audit and steering-committee reporting.
- **admin/configuration-workbook-authoring**: Use to compile confirmed rows into the 10-section admin handoff workbook — the last document before Setup changes begin.
- **admin/stakeholder-raci-for-sf-projects**: Use to establish who is accountable for each decision area before interviews start; supplies the escalation path for conflicting requirements.
- **admin/moscow-prioritization-for-sf-backlog**: Use when the `priority` column needs to become a release-capacity decision rather than a label.
- **admin/portal-requirements-gathering**: Use when the answer to "who does this" is a customer or partner and the requirement implies an Experience Cloud site.
- **admin/report-type-strategy**: Use when a reporting requirement's join chain has to be proved legal before it is promised.
- **admin/process-automation-selection**: Use to walk the automation tier decision for a specific requirement row.
- **architect/license-optimization-strategy**: Use when licence implications recorded during discovery need costing and edition/SKU selection.
- **architect/large-data-volume-architecture**: Use when a recorded volume figure crosses into LDV territory and needs an architecture response.
- **admin/uat-and-acceptance-criteria**: Use to translate confirmed acceptance criteria into structured UAT test scripts.
