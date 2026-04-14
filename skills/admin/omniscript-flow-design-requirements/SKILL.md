---
name: omniscript-flow-design-requirements
description: "Use this skill to gather, document, and validate OmniScript flow design requirements before development begins — covering screen layout requirements, branching logic, data source requirements, and user journey mapping. Trigger keywords: OmniScript requirements, OmniScript BA, OmniScript screen design, OmniScript user journey, OmniScript branching requirements. NOT for OmniScript development implementation, DataRaptor mapping, Integration Procedure design, or standard Screen Flow requirements."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "BA needs to document what screens and branching an OmniScript should have before the developer starts"
  - "product owner wants to map the user journey and conditional logic for an OmniScript guided process"
  - "team needs to capture OmniScript data requirements and define which data sources feed each step"
  - "stakeholder review requires an OmniScript wireframe or requirements document before build"
  - "scoping session to determine if OmniScript is the right tool and what the flow structure should be"
tags:
  - omnistudio
  - omniscript
  - requirements-gathering
  - user-journey
  - ba-role
inputs:
  - "Business process description and user journey narrative"
  - "List of data objects and fields the OmniScript must read or write"
  - "Branching rules and conditional logic scenarios"
  - "Persona or user role context (internal agent, community user, Experience Cloud)"
outputs:
  - "OmniScript requirements document with step/element inventory"
  - "User journey map showing branching paths and conditional views"
  - "Data requirements matrix mapping steps to data sources"
  - "Action requirements register (Navigation, OmniScript Launch, Apex, DataRaptor, Custom LWC)"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-14
---

# OmniScript Flow Design Requirements

This skill activates when a business analyst or product owner needs to gather and document OmniScript requirements before the developer begins building. It produces structured requirements artifacts — journey maps, branching logic docs, and data requirement matrices — that translate stakeholder intent into buildable OmniScript specifications.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the org has an OmniStudio license (included with Health Cloud, FSC, Manufacturing Cloud, Nonprofit Cloud, Education Cloud, Communications Cloud, Energy & Utilities Cloud) — OmniScript is not available in core Sales/Service Cloud without an additional license.
- Determine whether the org runs Standard Runtime (OmniStudio on Core, Spring '25+) or Package Runtime (managed package VBT/OmniStudio) — this affects Design Assistant availability and component HTML structure but does not change requirements artifact format.
- The most common wrong assumption: practitioners treat OmniScript requirements as interchangeable with Screen Flow requirements. OmniScript has mandatory structural rules (at least one Step, two data sources, one Navigate Action) that must be reflected in requirements artifacts.
- Every OmniScript must have: at least one Step element, at least two data source integrations (pre/post Step actions or embedded DataRaptors), and a Navigate Action to close or redirect after completion. Missing any of these blocks activation.

---

## Core Concepts

### OmniScript Structural Requirements

OmniScript has hard structural rules enforced at activation:
- At minimum one Step element is required — the Step is the container for all screen elements and controls the wizard navigation bar
- At least two data source bindings are required — typically a Pre-Step Load action (Read DataRaptor or Integration Procedure) and a Post-Step Save action (Transform DataRaptor or IP)
- A Navigate Action is required to complete the flow — without it the OmniScript hangs on the final step
- Branching lives inside Conditional View properties on Block container elements, triggered by Radio Button or Checkbox values — not on Step elements themselves

Requirements documents that omit data binding or the Navigate Action will produce incomplete developer specs that cause activation failures.

### Branching and Conditional Logic

OmniScript branching is declarative, not code-driven:
- Conditional Views are set on Block containers using the Condition property in JSON notation — e.g., `%RadioField:value% == 'Yes'`
- Radio Button elements in a separate Block from the conditional Block are the primary branching trigger
- Pre-Step and Post-Step action sequencing is mandatory for data flow — requirements must specify whether a data load fires before the user sees the screen (Pre-Step) or after they submit (Post-Step)
- Spring '25+ Standard Designer includes a Design Assistant that flags soft-limit warnings (too many elements per step, deep nesting) — requirements should note expected complexity levels

### Data Source Requirements

Each OmniScript step typically needs one or more data sources:
- Read DataRaptor — retrieves data to pre-populate fields (Pre-Step action)
- Transform DataRaptor — saves or transforms submitted data (Post-Step action)
- Integration Procedure — orchestrates multi-object reads/writes or calls external APIs
- SOQL-based DataRaptor — direct SOQL retrieval for simple lookups
- Remote Actions — Apex class methods for complex logic

Requirements must specify: what data is needed per step, whether it is read-only or read-write, what object/API it comes from, and whether it needs to be pre-populated before the user sees the screen.

---

## Common Patterns

### Pattern: Step-by-Step Journey Map

**When to use:** When the OmniScript has 3 or more steps or any conditional branching — before the developer opens the Designer.

**How it works:**
1. List all process steps in order (Step 1: Contact Info, Step 2: Service Selection, etc.)
2. For each step: document all screen elements (Text fields, Radio Buttons, Lookup, Selects), pre-population data source, and save action
3. For each Radio Button or Checkbox that drives branching: document the condition expression and which Blocks show/hide
4. Mark the Navigate Action destination (record page, Experience Cloud page, or custom URL)

**Why not the alternative:** Skipping the journey map leads to mid-build discovery of missing data sources or branching logic, requiring complete re-work of Step structure.

### Pattern: Data Requirements Matrix

**When to use:** When the OmniScript reads from or writes to 3 or more objects, or when an Integration Procedure orchestrates multiple API calls.

**How it works:**
1. Create a matrix with rows = OmniScript steps, columns = Object/API, Action (Read/Write), DataRaptor or IP name, Timing (Pre/Post)
2. For each cell: specify the field-level mapping (source field → OmniScript element name)
3. Flag any fields that require validation at requirements time (required, format, SOQL-validated)
4. Identify data that requires an Integration Procedure (multi-object write, external API) vs a simple DataRaptor (single-object CRUD)

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single-object form with no branching | Consider Screen Flow instead of OmniScript | OmniScript requires a license and adds complexity; Screen Flow covers single-object use cases natively |
| Multi-step guided journey with conditional branching | OmniScript is appropriate | Conditional Views and Step navigation are OmniScript strengths |
| External API call required mid-flow | Integration Procedure (document in requirements) | DataRaptors cannot call external APIs; IP must be specified as the data source type |
| Embedded in Experience Cloud for community users | Confirm guest user profile permissions in requirements | Community guest users cannot access all Salesforce objects; flag required sharing/CRUD/FLS |
| Complex validation rules at each step | Integration Procedure Post-Step action | Apex validation inside an IP provides server-side validation with structured error messages returned to the OmniScript |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. Confirm OmniStudio license availability and org runtime type (Standard vs Package Runtime) — this context must appear in the requirements document header.
2. Conduct requirements gathering session: capture all process steps, screen elements per step, branching triggers and conditions, and final action (what happens when the user completes the last step).
3. Build the user journey map: list Steps in sequence, document conditional branching paths with condition expressions in OmniScript notation (`%FieldName:value% == 'X'`), and mark the Navigate Action destination.
4. Build the data requirements matrix: for each step, specify data source type (Read DataRaptor, Transform DataRaptor, Integration Procedure, Remote Action), timing (Pre-Step or Post-Step), source object/API, and field-level mappings.
5. Validate structural completeness: confirm at least one Step, at least two data source bindings, and one Navigate Action are documented — flag any gaps before handing off to the developer.
6. Document action requirements: list every action type needed (Navigation, OmniScript Launch, Apex, DataRaptor, Custom LWC), the triggering element, and the expected outcome.
7. Review with stakeholders and developer to confirm requirements are buildable within OmniScript constraints before development starts.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] OmniStudio license confirmed and org runtime type documented
- [ ] At least one Step element documented per requirements
- [ ] At least two data source bindings specified (read and write)
- [ ] All branching conditions documented in OmniScript Conditional View notation
- [ ] Navigate Action destination specified
- [ ] Data requirements matrix complete with field-level mappings
- [ ] External API requirements flagged as Integration Procedure (not DataRaptor)
- [ ] Experience Cloud / guest user permissions noted if applicable

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Activation failure without Navigate Action** — An OmniScript without a Navigate Action cannot be activated. Requirements that omit the final step action will produce a skill package that fails at the developer's first activation attempt. Always document the Navigate Action in requirements.
2. **Pre-Step action timing confusion** — Data loaded in a Post-Step action is NOT available on the current step — it only fires after the user clicks Next. If a data load must pre-populate fields before the user sees the screen, it must be specified as a Pre-Step action. Requirements must explicitly note Pre vs Post timing.
3. **Conditional Views require Block containers** — Branching is set on a Block container element, not on individual field elements or Step elements. A common requirements gap is specifying "show field X if condition Y" without noting the Block grouping requirement. Requirements must group elements that share a condition into named Block containers.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| OmniScript requirements document | Step inventory with screen elements, data sources, and actions per step |
| User journey map | Visual or tabular map of Steps, branching conditions, and Navigate Action destination |
| Data requirements matrix | Per-step table of data source type, object/API, field mappings, and Pre/Post timing |
| Action requirements register | List of all action types needed with triggering element and expected outcome |

---

## Related Skills

- `omnistudio/omniscript-design-patterns` — use after requirements are complete to implement the OmniScript in the Designer
- `omnistudio/integration-procedures` — use when requirements identify multi-object or external API data needs
- `admin/omnistudio-vs-standard-decision` — use before requirements gathering to confirm OmniScript is the right tool
- `admin/flexcard-requirements` — companion skill for FlexCard requirements that may embed or launch OmniScripts
