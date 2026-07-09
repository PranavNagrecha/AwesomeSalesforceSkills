---
name: flow-dynamic-choices
description: "Build picklists and choice sets in Flow Builder sourced from records, picklist fields, or collections, including dependent choices. NOT for static hard-coded choice sets."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Reliability
triggers:
  - "dynamic choice flow"
  - "record choice set flow"
  - "dependent picklist flow"
  - "flow picklist from records"
  - "render flow choices as tiles"
  - "add visual picker to screen flow"
  - "add choice lookup component to screen flow"
  - "let flow users search a filtered list of records"
tags:
  - flow
  - choices
  - screen-flow
inputs:
  - "picklist source (SObject query or picklist field)"
  - "filter criteria"
outputs:
  - "Choice configuration + fallback on empty results"
dependencies: []
version: 1.2.1
author: Pranav Nagrecha
updated: 2026-07-08
---

# Flow Dynamic Choices

Screen Flows often need choices that reflect current data — active Accounts, open Cases, active picklist values. Record Choice Sets pull from SOQL; Picklist Choice Sets pull from field metadata; Collection Choice Sets iterate a variable. This skill covers each plus dependent-picklist patterns and empty-state handling. Sourcing the choices and rendering them are largely separate decisions — a Record, Picklist, or Collection Choice Set can drive a plain Picklist or Radio Buttons set, while the Visual Picker renders only standalone Choice resources that carry an icon (it doesn't support Record or Picklist Choice Sets). For long or filterable lists, a Choice Lookup component renders any Choice resource as a searchable, typeahead selector with single- or multi-select.

## Recommended Workflow

1. Pick source: Record Choice Set (SOQL), Picklist Choice Set (metadata), or Collection Choice Set (from a Get/Loop).
2. Pick the on-screen renderer: a Picklist or Radio Buttons set for short lists, a Visual Picker for icon tiles, or a Choice Lookup for long or filterable lists (searchable typeahead, single- or multi-select up to 25). A Record, Picklist, or Collection Choice Set can feed a Picklist, Radio Buttons, or Choice Lookup; the Visual Picker takes only standalone Choice resources that carry an icon (no Record or Picklist Choice Sets).
3. Constrain the query: filter active, limit rows, order for UX.
4. For dependent choices: second choice set filters on the first's stored value; use the reactive screen component — Choice Lookup is reactive-capable.
5. Handle empty set: branch to a message screen or preselect a fallback.
6. Test with a user whose sharing hides the query results; verify graceful empty state. Run in Lightning — Choice Lookup multi-select isn't supported in Classic runtime.

## Key Considerations

- Record Choice Sets ignore sharing by default with admin-run flow; use `Run In` = 'System Context With Sharing' carefully.
- Large result sets (>200) should be filtered — UI becomes unusable.
- Picklist Choice Set uses active values only; inactive values don't appear.
- Dependent fields in metadata are honored by Record-Triggered paths but not always by Screen picklists — test.
- Visual Picker (introduced in Summer '25 / release 256) renders Choice resources as icon-and-text tiles instead of a dropdown or radio list, so users can pick faster with visual cues. It's a standard screen input component listed alongside Picklist, Radio Buttons, and Checkbox Group — not a custom LWC, so reach for it before building one. It's configured using standalone Choice resources (text data type, each carrying an SLDS icon) and doesn't yet support Record Choice Sets or Picklist Choice Sets — map those into standalone Choice resources first.
- A Choice resource must carry an icon before it renders as a tile in a Visual Picker. Choices without an icon fall back to a plain list and are wasted on a Visual Picker.
- Choice Lookup renders any Choice resource as a searchable, typeahead selector — the right pick for long or filterable lists. It shows 20 options first, loads 100 more each scroll up to 1,020 displayed, and resets to 20 when a filter is reapplied, so keep the underlying set well-filtered enough that the target stays reachable.
- Choice Lookup single- vs multi-select is a per-component toggle ("Let Users Select Multiple Options"); multi-select allows up to 25 selections and shipped GA in Winter '25 (no beta phase). It isn't supported in Classic runtime for flows — wire multi-select output to a collection variable.
- Standard Lookup vs Choice Lookup: the standard Lookup surfaces recent and global-search records with no author-defined filter; Choice Lookup restricts users to a filtered Record or Collection Choice Set. Pick Choice Lookup when the selectable records must be constrained — see the official "Choose a Lookup Option for a Flow Screen" guide.
- Choice Lookup is a reactive screen component (Reactive Screen Components GA, Winter '24), so it can update live in response to another selection on the same screen — the basis for dependent choices without a page reload — and applies across Essentials, Professional, Enterprise, Performance, Unlimited, and Developer editions. Summer '26 also extended Style-tab overrides (colors, borders that override the org/site theme) to Choice Lookup for per-screen branding.

## Worked Examples (see `references/examples.md`)

- *Active Account picker* — Case creation flow
- *Country → State dependent* — Address capture
- *Icon tile picker* — Visual Picker rendering of a Choice resource
- *Searchable record picker* — Choice Lookup over a filtered Record Choice Set

## Common Gotchas (see `references/gotchas.md`)

- **Sharing mismatch** — User sees choices they can't open.
- **Empty state not handled** — User sees empty dropdown; stuck.
- **Inactive picklist values** — Historical values invisible.
- **Visual Picker needs an icon** — Choice without an icon won't render as a tile.
- **Choice Lookup display cap** — Scrolling stops at 1,020 options; filter the set instead.
- **Multi-select needs a collection + Lightning** — Wire output to a collection; Classic runtime is unsupported.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Hard-coded choices that mirror records
- Unbounded SOQL in Choice Set
- No empty-state path
- Custom LWC when the standard Visual Picker would do
- Standard Lookup when the list must be filtered — that's Choice Lookup's job
- Choice Lookup multi-select assumed in Classic runtime or wired to a single-value variable

## Official Sources Used

- Flow Builder Guide — https://help.salesforce.com/s/articleView?id=sf.flow.htm
- Flow Best Practices — https://help.salesforce.com/s/articleView?id=sf.flow_best_practices.htm
- Reactive Screens — https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_screen_reactive.htm
- Flow HTTP Callout Action — https://help.salesforce.com/s/articleView?id=sf.flow_concepts_callout.htm
- Standard Flow Screen Components — https://help.salesforce.com/s/articleView?id=platform.flow_ref_elements_screencmp.htm&language=en_US&type=5
- Visual Picker Screen Input Component — https://help.salesforce.com/s/articleView?id=platform.flow_ref_elements_screencmp_visual_picker.htm&language=en_US&type=5
- Help Users Select Faster by Using Visual Cues in Choices — https://help.salesforce.com/s/articleView?id=platform.automate_flow_build_help_users_select_faster_by_using_visual_cues_in_choices.htm&language=en_US&type=5
- Display Choices in Tiles with the Visual Picker Component (Summer '25 release note) — https://help.salesforce.com/s/articleView?id=release-notes.rn_automate_flow_builder_display_choices_in_tiles_with_the_visual_picker_component_in_screen_flows.htm&language=en_US&release=256&type=5
- Choice Lookup Screen Input Component — https://help.salesforce.com/s/articleView?id=platform.flow_ref_elements_screencmp_choice_lookup.htm&language=en_US&type=5
- Choose a Lookup Option for a Flow Screen — https://help.salesforce.com/s/articleView?id=platform.flow_ref_elements_screencmp_lookup_comparison.htm&language=en_US&type=5
- Record Choice Set Resource — https://help.salesforce.com/s/articleView?id=platform.flow_ref_resources_recordchoice.htm&language=en_US&type=5
- Customize Component and Field Layout in Screen Flows — https://help.salesforce.com/s/articleView?id=platform.automate_flow_build_customize_component_and_field_layout_in_screen_flows.htm&language=en_US&type=5
- Provide Users a List of Choices for Easy Selection with Choice Lookup (Summer '23 GA release note) — https://help.salesforce.com/s/articleView?id=release-notes.rn_automate_flow_builder_choice_lookup_ga.htm&language=en_US&release=244&type=5
- Select Multiple Choices with Choice Lookup Component (Winter '25 release note) — https://help.salesforce.com/s/articleView?id=release-notes.rn_automate_flow_builder_choice_lookup.htm&language=en_US&release=252&type=5
