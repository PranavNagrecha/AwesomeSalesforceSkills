---
name: flexcard-container-composition
description: "Design FlexCard composition: parent/child state flow, layout modes, actions, event wiring, and data source selection. Trigger keywords: flexcard, flex card composition, parent child flexcard, flexcard state, flexcard events, flexcard datasource. Does NOT cover: the first-time FlexCard Hello-World (trailhead), LWC-native alternatives, or Experience Cloud theming."
category: omnistudio
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Performance
  - Operational Excellence
triggers:
  - "flexcard composition design"
  - "parent child flexcard state"
  - "flexcard event wiring"
  - "flexcard datasource selection"
  - "flexcard action types"
tags:
  - omnistudio
  - flexcard
  - composition
  - ui
inputs:
  - UI mock or wireframe
  - Data sources available (IP, DataRaptor, REST, Apex)
  - Required actions (OmniScript launch, update record, fire event)
outputs:
  - FlexCard composition plan (parent / child / state map)
  - Datasource binding and action wiring decisions
  - Layout mode selection (card / list / table / none)
dependencies:
  - omnistudio/integration-procedure-cacheable-patterns
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
runtime_orphan: true
---

# FlexCard Container Composition

## Decision: One Card Or Many?

- **One FlexCard** — a single record context, 1-2 actions, minimal
  internal state.
- **Parent + Child FlexCards** — master/detail, list → drilldown, or
  tabs where child state is independent.
- **FlexCard inside OmniScript** — only when the card is purely
  presentational within a flow step. Never reach up and trigger the
  parent OmniScript directly from a deeply nested FlexCard.

## Data Source Selection

| Data Source | Use When | Avoid When |
|---|---|---|
| Integration Procedure | Aggregating 2+ sources or needing caching | Single field read |
| DataRaptor (Extract) | Simple SObject read | Aggregation across objects |
| Apex REST | Custom logic or external hop | Simple read with DR |
| REST | Direct callout (rare from UI) | Anything with PII headers |
| SOQL (direct) | Lightweight, read-only | Anything needing FLS enforcement by IP |

Prefer Integration Procedure as the default — it gives you one place
to cache and centralise errors.

## Parent/Child State Flow

Pattern: parent FlexCard loads the **list**, child FlexCard loads the
**detail**. Parent fires a `flexcardevent` with the selected id, child
subscribes and reloads.

- Parent does NOT push row data into the child via state — child fetches
  its own detail (fresh, cache-aware).
- Child does NOT mutate parent state directly. On action, child fires
  event → parent reacts.
- Shared immutables (record id, layout flags) travel via input
  parameters, not events.

## Action Types

- **OmniScript launch** — inline modal or new tab.
- **Update record** — DR Update or Integration Procedure; never a direct
  UI → DML without FLS enforcement.
- **Navigate** — Lightning nav, not hardcoded URL.
- **Fire event** — for parent/child composition or cross-component wiring.
- **Custom LWC action** — for behaviour that does not fit the built-in
  action types.

## Layout Modes

| Mode | When to use |
|---|---|
| Card | Single-record detail. |
| List | Collection of card-shaped items, client-side pagination. |
| Table | Tabular view. Avoid when mobile is a primary target. |
| None | Purely a state/event container (rare). |

## Recommended Workflow

1. Sketch the UI with a clear parent/child boundary.
2. Pick one data source per card. Prefer Integration Procedure.
3. Define input parameters (immutables) and event contract (mutables).
4. Choose layout mode.
5. List actions and pick action types per action.
6. Wire events parent → child; child → parent via event name + payload.
7. Preview in multiple form factors (Desktop/Tablet/Phone) before shipping.

## Performance Notes

- A FlexCard that calls an IP on every input change can destroy
  responsiveness. Use cacheable IPs where inputs are stable (see
  `omnistudio/integration-procedure-cacheable-patterns`).
- Nested FlexCards each make their own data call. Flatten when parent
  already has the data.

## Official Sources Used

- FlexCards Overview —
  https://help.salesforce.com/s/articleView?id=sf.os_flexcards_overview.htm
- FlexCard Events —
  https://help.salesforce.com/s/articleView?id=sf.os_flexcard_events.htm
- FlexCard Data Sources —
  https://help.salesforce.com/s/articleView?id=sf.os_flexcard_data_sources.htm
