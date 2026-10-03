---
name: omniscript-flow-design-requirements
description: "Use this skill to gather, document, and validate OmniScript flow design requirements before development begins — covering screen layout requirements, branching logic, data source requirements, and user journey mapping. Trigger keywords: OmniScript requirements, OmniScript BA, OmniScript screen design, OmniScript user journey, OmniScript branching requirements. NOT for building the OmniScript or moving logic into an Integration Procedure — use omnistudio/omniscript-design-patterns. NOT for FlexCard requirements — use admin/flexcard-requirements."
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
  - "omniscript flow design requirements screen steps data raptor BA"
  - "write the requirements for an omniscript before the developer builds it"
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
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

# OmniScript Flow Design Requirements

This skill activates when a business analyst or product owner needs to gather and document OmniScript requirements before the developer begins building. It produces structured requirements artifacts — journey maps, branching logic docs, and data requirement matrices — that translate stakeholder intent into buildable OmniScript specifications.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the org has an OmniStudio license (included with Health Cloud, FSC, Manufacturing Cloud, Nonprofit Cloud, Education Cloud, Communications Cloud, Energy & Utilities Cloud) — OmniScript is not available in core Sales/Service Cloud without an additional license. UNVERIFIED (2026-10-03): the bundle list is from Salesforce Help and contracts, not from a source read for this revision. The OmniScript metadata type entry in the Salesforce Industries Developer Guide (Discovery Framework Metadata API Types) does say "you must have an Omnistudio license" to use that type.
- Determine whether the org runs OmniStudio on the standard runtime or Omnistudio for Managed Packages (managed package runtime with custom objects). Trailhead's OmniScript modules state which one they cover, and the two differ in where definitions are stored. It does not change the requirements artifact format.
- The most common wrong assumption: practitioners treat OmniScript requirements as interchangeable with Screen Flow requirements. OmniScript has structural expectations (at least one Step, two data sources, one Navigate Action) that must be reflected in requirements artifacts.
- Trailhead ("Design and Build a Branching Omniscript") states that all Omniscripts require at least two data sources (Integration Procedures as best practice), at least one Step to show inputs, and a Navigate Action to direct the user at the end. UNVERIFIED (2026-10-03): no source read for this revision says activation is blocked when one of these is missing; treat them as design requirements.

---

## Questions to Ask Before Configuring

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| What is the OmniScript's Type, SubType, and Language, and who owns new versions? | Type, SubType, and Language are its identity; only one active OmniScript can share them, and only one version is active at a time (Trailhead, Configure a Simple OmniScript). | A unique key such as `claims/intake/English` and a versioning owner. | Changes ship as a new version while the active one keeps serving users. |
| For every screen field, which data source fills it, and what is the JSON node name? | The OmniScript matches returned JSON to inputs by element name; a mismatched name leaves the field empty (same Trailhead unit). | A field-to-node mapping table per Step. | Pre-filled fields work on the first build instead of after a debugging session in Preview. |
| Which data must load before the user sees a Step, and which saves after? | Actions placed before or after a Step run automatically in order; actions inside a Step render as buttons (same Trailhead unit). | A Pre-Step / Post-Step / button column for each action. | Loads and saves fire at the right moment without extra clicks. |
| Which rules check values across Steps, not just on the current one? | Required fields and Messaging only work on the current Step; Set Errors sends the user back to an earlier Step (Trailhead, Validate Data and Handle Errors). | A list of cross-step rules with the element that shows each error. | Users fix a missing value at its source Step instead of failing on submit. |
| Which parts are reusable child OmniScripts? | Omniscripts nest only one level, and element names must be unique across parent and child (Trailhead, Use Action, Function, and Display Elements). | A parent/child map with reserved element-name prefixes. | Reuse without a nesting dead end or name collisions found at build time. |
| Where does the user land at the end, and is it the same for every branch? | The Navigate Action tells the OmniScript where to send the user when it completes. | A destination per branch (record page, console tab, URL, other OmniScript). | Users finish on the right record instead of a dead final Step. |

---

## Core Concepts

### OmniScript Structural Requirements

Trailhead lists structural requirements for every OmniScript:
- At minimum one Step element is required — each Step presents one page to the user and holds its elements
- At least two data sources are required. Typically that is a load action placed before the Step (an Integration Procedure or an Omnistudio Data Mapper Extract) and a save action placed after it (an Integration Procedure or a Data Mapper Load)
- A Navigate Action directs the user at the end. Without it the user is left on the final Step
- Branching uses the Conditional View property. Almost every element supports it, including Steps (to route users to one Step or another) and Blocks (to show a group of fields); Radio Button values are the usual trigger

Requirements documents that omit data binding or the Navigate Action will produce incomplete developer specs. UNVERIFIED (2026-10-03): earlier versions of this skill said these omissions cause activation failures; no source read for this revision confirms that.

### Branching and Conditional Logic

OmniScript branching is declarative, not code-driven:
- Conditional Views can be set on almost any element; Blocks are the usual container when several fields share one condition. Record each condition as element, operator, and value. UNVERIFIED (2026-10-03): the expression form `%RadioField:value% == 'Yes'` used in this skill's examples is not confirmed by any source read; use it as shorthand in requirements, not as syntax to paste
- Radio Button elements in a separate Block from the conditional Block are the primary branching trigger
- Pre-Step and Post-Step action sequencing is mandatory for data flow — requirements must specify whether a data load fires before the user sees the screen (Pre-Step) or after they submit (Post-Step)
- Spring '25+ Standard Designer includes a Design Assistant that flags soft-limit warnings (too many elements per step, deep nesting) — requirements should note expected complexity levels. UNVERIFIED (2026-10-03): Design Assistant is not described in any source read for this revision

### Data Source Requirements

Each OmniScript step typically needs one or more data sources:
- Read DataRaptor (now Omnistudio Data Mapper Extract, or Turbo Extract for one object): retrieves data to pre-populate fields (Pre-Step action)
- Transform DataRaptor (Data Mapper Transform) maps data between shapes; the save itself is a Data Mapper Load (Post-Step action)
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
5. Validate structural completeness: confirm at least one Step, at least two data source bindings, and one Navigate Action are documented, and that every pre-filled field's element name matches its JSON node. Flag any gaps before handing off to the developer. A filled-in requirements spec and a retrieve manifest are in `references/metadata-examples.md`.
6. Document action requirements: list every action type needed (Navigation, OmniScript Launch, Apex, DataRaptor, Custom LWC), the triggering element, and the expected outcome.
7. Review with stakeholders and developer to confirm requirements are buildable within OmniScript constraints before development starts.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] OmniStudio license confirmed and org runtime type documented
- [ ] At least one Step element documented per requirements
- [ ] At least two data source bindings specified (read and write)
- [ ] All branching conditions documented as element, operator, value, with the Block or Step they show
- [ ] Navigate Action destination specified
- [ ] Data requirements matrix complete with field-level mappings
- [ ] External API requirements flagged as Integration Procedure (not DataRaptor)
- [ ] Experience Cloud / guest user permissions noted if applicable

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **No Navigate Action, no exit**: Without a Navigate Action the user is left on the final Step. Always document the Navigate Action and its destination in requirements.
2. **Pre-Step action timing confusion** — Data loaded in a Post-Step action is NOT available on the current step — it only fires after the user clicks Next. If a data load must pre-populate fields before the user sees the screen, it must be specified as a Pre-Step action. Requirements must explicitly note Pre vs Post timing.
3. **Group shared conditions in Blocks**: Conditional Views work on almost every element, but listing one condition per field multiplies identical rules. Group elements that share a condition into a named Block. More traps, including JSON name matching and cross-step validation, are in `references/gotchas.md`.

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
- `architect/omnistudio-vs-standard-decision` — use before requirements gathering to confirm OmniScript is the right tool
- `admin/flexcard-requirements` — companion skill for FlexCard requirements that may embed or launch OmniScripts
