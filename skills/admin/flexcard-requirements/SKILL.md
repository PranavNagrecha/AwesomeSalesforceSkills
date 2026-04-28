---
name: flexcard-requirements
description: "Use this skill to gather, document, and validate FlexCard layout requirements before development begins — covering data visualization needs, action requirements, embedded component specifications, and user context mapping. Trigger keywords: FlexCard requirements, FlexCard BA, FlexCard layout design, FlexCard data sources, FlexCard actions. NOT for FlexCard development implementation, Card Designer configuration, or standard Lightning component requirements."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "BA needs to document what data and actions a FlexCard should display before the developer builds it"
  - "product owner wants to define the layout structure and embedded components for a FlexCard dashboard"
  - "team needs to specify which data source type feeds each FlexCard and what actions users can take"
  - "stakeholder review requires a FlexCard wireframe or requirements document before development starts"
  - "scoping session to identify FlexCard data bindings and card state template requirements"
tags:
  - omnistudio
  - flexcard
  - requirements-gathering
  - ba-role
  - card-design
inputs:
  - "Business process description and user context narrative"
  - "Data objects the FlexCard must display (Salesforce objects, external APIs, Integration Procedures)"
  - "Actions users need to take from the FlexCard (navigation, OmniScript launch, Apex, DataRaptor)"
  - "Embedded component needs (child FlexCards, OmniScript, custom LWC)"
  - "User persona and context (agent console, Experience Cloud, record page)"
outputs:
  - "FlexCard requirements document with data source inventory"
  - "Action requirements register with triggering conditions"
  - "Embedded component specification"
  - "Card state template requirements (number of states, conditions)"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# FlexCard Requirements

This skill activates when a business analyst or product owner needs to gather and document FlexCard requirements before a developer begins building in Card Designer. It produces structured requirements artifacts — data source inventory, action registers, and state template specs — that translate stakeholder intent into buildable FlexCard specifications.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the org has an OmniStudio license. FlexCards are part of OmniStudio and require the same Industries cloud licenses as OmniScript (Health Cloud, FSC, Manufacturing Cloud, etc.).
- Determine whether the FlexCard embeds in a Lightning record page, Service Console, or Experience Cloud — this context drives data source access patterns and Guest User permission requirements.
- The most common wrong assumption: practitioners confuse requirements gathering (what the card needs to show and do) with implementation (how to build it in Card Designer). This skill scopes to pre-build analysis only.
- FlexCards support five data source types (SOQL, Apex, DataRaptor, Integration Procedure, Streaming) and five action types (Navigation, OmniScript Launch, Apex, DataRaptor, Custom LWC) — requirements must specify which type is appropriate for each need.
- Card state templates are compiled to LWC at activation time (not at save time) — requirements that specify embedded LWC components must confirm the LWC is deployed before card activation.

---

## Core Concepts

### Five Data Source Types

Every FlexCard pulls data from exactly one of these sources:

| Source | When to use |
|---|---|
| SOQL | Direct query against Salesforce objects; fastest for simple record display |
| Apex | Apex class method for computed or aggregated data |
| DataRaptor | Declarative field mapping for single-object reads |
| Integration Procedure | Orchestrated multi-source or external API data |
| Streaming | Platform Event subscription for real-time updates |

Requirements must specify which type per card (and per child card if nested). SOQL is sufficient for single-object record display; Integration Procedure is required for multi-object or external API data.

### Five Action Types

Users interact with FlexCards through one of these action types:

| Action type | Behavior |
|---|---|
| Navigation | Routes the user to a record page, URL, or tab |
| OmniScript Launch | Opens an OmniScript in a modal or inline |
| Apex | Calls an Apex method (typically for record updates or processing) |
| DataRaptor | Runs a DataRaptor directly (typically for simple field updates) |
| Custom LWC | Launches a custom Lightning Web Component for complex UI interactions |

Requirements must list every action, its type, its triggering condition, and the expected outcome.

### Card State Templates

FlexCards support multiple card states — different layouts rendered based on record data:
- A FlexCard can have multiple card state templates, each with a condition expression
- The first matching state template is rendered; states are evaluated in order
- State templates are compiled to LWC at activation time — changes require reactivation
- Requirements must specify: how many states are needed, the condition expression per state, and what elements each state should display differently

### Embedded Components

FlexCards can embed child components:
- **Child FlexCards** — nested card components with their own data source
- **OmniScript** — inline or modal OmniScript launch
- **Custom LWC** — custom Lightning components

Requirements must identify any embedded components, their data dependencies, and whether they need to be built before the parent FlexCard can be activated.

---

## Common Patterns

### Pattern: Data Source Mapping Matrix

**When to use:** When the FlexCard displays data from more than one object, or when stakeholders have not identified whether SOQL, IP, or DataRaptor is appropriate.

**How it works:**
1. For each data field the FlexCard must display: list the source object, whether it is a direct field or computed/aggregated, and any external API dependencies
2. Map each field to a data source type: SOQL for direct Salesforce object fields, DataRaptor for simple remapped reads, Integration Procedure for multi-source or external data
3. Document the SOQL query or IP name, and which FlexCard element binds to which field path

**Why not the alternative:** Leaving data source type unspecified forces the developer to make architectural decisions mid-build. Using SOQL when an Integration Procedure is required causes silent data load failures or missing data on the card.

### Pattern: Action Requirements Register

**When to use:** When users need to take actions from the FlexCard (not just view data).

**How it works:**
1. List every action the user can take: what the user clicks/triggers, what type of action it maps to, and what happens
2. For OmniScript Launch actions: identify which OmniScript, whether it opens inline or in a modal, and what data the OmniScript needs from the FlexCard context
3. For Navigation actions: specify the destination (record page, URL, tab)
4. For Apex or DataRaptor actions: specify the class/DR name and the data passed from the card

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Card displays fields from a single Salesforce object | SOQL data source | Simplest, fastest; no additional configuration needed |
| Card displays data from multiple objects or computed fields | Integration Procedure | Multi-source orchestration; SOQL joins are limited in FlexCard |
| Card updates a record when a user clicks a button | Apex action or DataRaptor action | Server-side execution; Apex for complex logic, DataRaptor for simple field updates |
| Card needs to launch a guided process | OmniScript Launch action | Inline or modal OmniScript; specify context data passed to OmniScript |
| Card shows different layouts for different record statuses | Card state templates | Document number of states and condition expressions per state |
| Card embeds in Experience Cloud for community users | Note guest user FLS requirements | Community guest users have restricted object access; flag required permissions |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. Confirm OmniStudio license availability and the FlexCard's deployment context (Lightning record page, Service Console, Experience Cloud) — document in requirements header.
2. Identify and map all data fields the FlexCard must display — source object, field path, and whether a SOQL, DataRaptor, or Integration Procedure data source is appropriate.
3. Document all user actions required — for each action: action type (Navigation, OmniScript Launch, Apex, DataRaptor, Custom LWC), triggering element or button, and expected outcome.
4. Identify card state template requirements — how many states are needed, what conditions trigger each state, and what the layout differences are between states.
5. Identify embedded component requirements — child FlexCards, inline OmniScripts, or custom LWC components; confirm each embedded component is already built or add to build dependency list.
6. Review with the developer to confirm all data source types and action types are correct and buildable within FlexCard's five supported types before development starts.
7. Document any Experience Cloud or guest user permission requirements that must be resolved before card activation.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] OmniStudio license confirmed and deployment context documented
- [ ] All displayed data fields mapped to a data source type (SOQL / DataRaptor / IP)
- [ ] All user actions documented with action type and expected outcome
- [ ] Card state templates specified with condition expressions
- [ ] Embedded components identified and build dependencies noted
- [ ] Experience Cloud / guest user permission requirements documented if applicable
- [ ] No data source type listed as "to be determined" (developer must receive complete spec)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **State templates compile to LWC at activation — not at save** — FlexCard state templates are compiled to LWC only when the card is activated, not when it is saved in Card Designer. This means that a developer editing a card must reactivate it for changes to take effect. Requirements that specify a state template change mid-project must note that reactivation (and a brief outage for users currently viewing the card) is required.
2. **Child FlexCards must be activated before the parent can be activated** — If requirements specify a nested FlexCard architecture, the child card must be fully built and activated before the parent card can be activated. This is a build dependency that must appear explicitly in the requirements document's build order section.
3. **Integration Procedure data source requires the IP to be active** — FlexCards bound to an Integration Procedure data source silently return empty data if the IP is not in Active status. Requirements must note which IP is the data source and confirm it will be active before card activation.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| FlexCard requirements document | Data source inventory, action register, state template spec, embedded component list |
| Data source mapping matrix | Per-field table mapping display fields to data source types and element bindings |
| Action requirements register | List of all user actions with type, triggering element, and expected outcome |
| Card state template spec | Number of states, condition expression per state, layout differences |

---

## Related Skills

- `omnistudio/flexcard-design-patterns` — use after requirements are complete to implement in Card Designer
- `admin/omniscript-flow-design-requirements` — companion BA requirements skill for OmniScripts that the FlexCard may launch
- `admin/omnistudio-vs-standard-decision` — use to confirm FlexCard is the right tool over standard Lightning components
- `omnistudio/integration-procedures` — use when requirements identify multi-source or external API data needs
