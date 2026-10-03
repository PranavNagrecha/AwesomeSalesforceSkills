---
name: flexcard-requirements
description: "Specify a FlexCard before a developer opens Card Designer: the card-state set and the condition that selects each state, the data source type behind each card (DataRaptor, Integration Procedure, Apex remote, SOQL), the action menu users get (navigate, launch OmniScript, Apex, DataRaptor), and every embedded child FlexCard or custom LWC. Produces the artifacts a BA hands to the builder. Trigger keywords: FlexCard requirements, FlexCard BA, FlexCard layout design, FlexCard data sources, FlexCard actions, FlexCard card states, OmniStudio FlexCard scoping. NOT for building the card in Card Designer, NOT for OmniScript step and branching requirements (use admin/omniscript-flow-design-requirements), NOT for standard Lightning record-page component requirements."
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
  - "write the spec for a FlexCard shown to guest users on a public Experience Cloud page"
  - "list the permissions a FlexCard's audience needs before activation"
tags:
  - omnistudio
  - flexcard
  - requirements-gathering
  - card-design
  - card-states
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
version: 1.0.2
author: Pranav Nagrecha
updated: 2026-10-03
---

# FlexCard Requirements

This skill activates when a business analyst or product owner must gather and document FlexCard requirements before a developer builds in Card Designer. It produces the data source inventory, action register, state specification, embedded component list, and audience permission list that turn stakeholder intent into a buildable card.

Grounding note: the OmniStudio FlexCard guide is published on help.salesforce.com and as an atlas guide, and neither returned content for this pass. The grounded sources are the Salesforce Industries Developer Guide (OmniStudio objects and Business APIs), the Security Guide (guest user access), and the Metadata API guide (permission sets). Card Designer behavior carried from earlier versions of this skill is marked UNVERIFIED where it is stated as fact.

---

## Before Starting

- Confirm which OmniStudio runtime the org uses. The Industries guide distinguishes "OmniStudio Standard" from "OmniStudio for Vlocity", and some objects (for example `OmniTrackingGroup` and `OmniTrackingComponentDef`, API 60.0, used for OmniAnalytics) exist only in OmniStudio Standard.
- Determine where the card runs: a Lightning record page, a console, or an Experience Cloud site. For unauthenticated visitors, guest users' org-wide defaults are Private for all objects and cannot be changed, and guest user sharing rules can grant only Read Only access.
- Keep requirements separate from implementation. This skill scopes what the card shows and does; Card Designer configuration belongs to `omnistudio/flexcard-design-patterns`.
- UNVERIFIED (2026-10-03): earlier versions of this skill listed exactly five data source types (SOQL, Apex, DataRaptor, Integration Procedure, Streaming) and five action types (Navigation, OmniScript Launch, Apex, DataRaptor, Custom LWC), and said card states compile to LWC at activation. The Industries guide confirms only that "an Integration Procedure ... can be a data source for a Flexcard" and that Data Mappers "supply data to Omniscripts, Integration Procedures, Flexcards, and Apex classes". Confirm the full lists in the org's Card Designer.

---

## Questions to Ask Before Configuring

Ask these before the developer opens Card Designer. Each one traces to a gotcha in `references/gotchas.md`.

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "Who sees this card: internal users, authenticated portal users, or anonymous guests?" | Guest OWD is Private and fixed; guest sharing rules grant Read Only only (gotcha 2) | The audience per placement and the records each may read | A card that shows data to the right audience instead of blank fields or over-exposure |
| "Which fields come from one object, and which need several objects or an external system?" | Multi-source data points to an Integration Procedure; single-object data may not (gotcha 3) | A data source per field group | No mid-build re-architecture when a field turns out to need another source |
| "Which actions change data, and through what (Data Mapper, Apex, OmniScript)?" | Each server-side action needs access for the card's users (gotcha 4) | An action register with the permission each action needs | Actions that work for every audience on the first test |
| "Does anyone need usage analytics on the card?" | OmniAnalytics tracking uses tracking groups, available in OmniStudio Standard (gotcha 5) | A tracking decision and the runtime it depends on | Analytics designed in rather than requested after go-live |
| "Will anyone load, copy, or clean up cards with data tools?" | `OmniUiCard` records are internal-use only (gotcha 1) | A rule that cards move only through supported deployment tools | No corrupted cards from direct record edits |
| "Do any actions call expression sets or decision matrices?" | The older OmniStudio Business REST APIs for these were deprecated in API 55.0 (gotcha 6) | The supported API for each calculation | Actions built on current APIs |

What a proper requirements package adds over "just designing a card": every field has a source, every action has a permission, every audience has a defined record access path, and the build order is known before activation.

---

## Core Concepts

### Data sources

| Source | When to use | Grounding |
|---|---|---|
| Integration Procedure | Multi-source or external data; orchestration | Industries guide: an IP "can be a data source for a Flexcard" |
| Data Mapper (DataRaptor) | Declarative read and remap of Salesforce data | Industries guide: Data Mappers supply data to Flexcards |
| SOQL, Apex, Streaming | Single-object reads, computed data, event-driven updates | UNVERIFIED (2026-10-03): help-only |

Requirements must name a source per field group, and per child card if cards are nested.

### Actions

List every action with its type, trigger element, expected outcome, the data passed from the card, and the permission it needs. Typical action types are navigation, OmniScript launch, Apex, and Data Mapper. UNVERIFIED (2026-10-03): the complete action type list is help-only.

### Card states

A card can show different layouts depending on record data. Requirements must give the number of states, the condition for each, the evaluation order, and what each state shows differently. UNVERIFIED (2026-10-03): that the first matching state renders, and that state changes need reactivation because templates compile to LWC at activation, are help-only claims; ask the developer to confirm in Card Designer.

### Embedded components

Child FlexCards, OmniScripts, and custom LWCs can sit inside a card. Requirements must list each one, its data dependencies, and whether it must exist (and be active or deployed) before the parent card can be activated.

---

## Common Patterns

### Pattern: Data Source Mapping Matrix

**When to use:** The card shows data from more than one object, or stakeholders have not said where data comes from.

**How it works:**
1. For each displayed field, record the source object, whether it is direct or computed, and any external dependency.
2. Assign a source type: Data Mapper for simple remapped reads, Integration Procedure for multi-source or external data.
3. Record the IP or Data Mapper name and which card element binds to which field path.

### Pattern: Audience and Permission Register

**When to use:** The card is placed in more than one context, or on an Experience Cloud site.

**How it works:**
1. List each audience and placement.
2. For each, list the objects and fields read, the Apex classes or IPs invoked, and the record access path (sharing, guest sharing rule).
3. Turn the internal and portal rows into permission sets (deployable example in `references/metadata-examples.md`) and the guest rows into guest user sharing rules with Read Only access.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Fields from one Salesforce object | Simplest source the org supports (Data Mapper read, or SOQL if available) | Fewer components to maintain |
| Data from several objects or an external API | Integration Procedure | Documented as a FlexCard data source; orchestrates multiple sources |
| Card updates a record | Data Mapper or Apex action, with access for every audience | Server-side execution runs with the user's access |
| Card launches a guided process | OmniScript launch action; record the context passed | Keeps the process in OmniScript |
| Anonymous Experience Cloud visitors | Guest user sharing rules (Read Only) plus minimal guest profile access | Guest OWD is Private and cannot be changed |
| Usage analytics needed | OmniAnalytics tracking group (OmniStudio Standard) | Tracking objects exist only in OmniStudio Standard |

---

## Recommended Workflow

1. Confirm the OmniStudio runtime (Standard or for Vlocity) and every placement of the card; record them in the requirements header.
2. Map every displayed field to a source object, field path, and data source type.
3. Write the action register: type, trigger, outcome, data passed, and permission needed.
4. Specify card states: count, condition, evaluation order, and layout differences.
5. List embedded components and their build and activation order.
6. Write the audience and permission register, including guest access for public pages, and hand `references/metadata-examples.md` to the builder for the permission set.
7. Review with the developer to confirm every source and action type is available in this org before build starts.

---

## Review Checklist

- [ ] OmniStudio runtime (Standard or for Vlocity) recorded
- [ ] Every placement and audience recorded
- [ ] Every displayed field mapped to a data source type
- [ ] Every action has a type, outcome, and required permission
- [ ] Card states specified with conditions and order
- [ ] Embedded components listed with build and activation order
- [ ] Guest access designed with Read Only guest sharing rules where the card is public
- [ ] Rule recorded that `OmniUiCard` records are never edited with data tools
- [ ] No data source or action type left as "to be determined"

---

## Salesforce-Specific Gotchas

The deep versions, with sources, live in `references/gotchas.md`.

| # | Gotcha | One-line consequence |
|---|---|---|
| 1 | `OmniUiCard` records are internal-use only | Direct edits or loads can break the card |
| 2 | Guest OWD is Private and fixed; guest sharing is Read Only | Public cards show nothing, or nothing editable |
| 3 | Integration Procedures are the documented multi-source data source | Single-source assumptions break on aggregated fields |
| 4 | Every server-side action runs with the user's access | Actions fail for portal users |
| 5 | OmniAnalytics tracking exists only in OmniStudio Standard | Analytics requests fail on the Vlocity runtime |
| 6 | Older OmniStudio Business REST APIs were deprecated in API 55.0 | Actions built on them are on a retired surface |
| 7 | State compilation and activation order are help-only claims | Build order surprises if not confirmed |

---

## Output Artifacts

| Artifact | Description |
|---|---|
| FlexCard requirements document | Data source inventory, action register, state spec, embedded components |
| Data source mapping matrix | Field-to-source table with element bindings |
| Action requirements register | Actions with type, trigger, outcome, and permission |
| Audience and permission register | Placements, audiences, record access path, permission set contents |
| Card state specification | States, conditions, order, layout differences |

---

## Related Skills

- `omnistudio/flexcard-design-patterns`: implement the card in Card Designer after requirements are complete
- `admin/omniscript-flow-design-requirements`: requirements for OmniScripts the card launches
- `architect/omnistudio-vs-standard-decision`: whether a FlexCard is the right tool
- `omnistudio/integration-procedures`: Integration Procedures named as data sources
