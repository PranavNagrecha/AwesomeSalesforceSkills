# Well-Architected Notes — Screen Flow Choice Component Selection

## Relevant Pillars

- **Operational Excellence** — choosing the right choice component is a maintainability
  decision. Picking a component whose selection can't feed a downstream Loop or Transform forces
  a rebuild later; matching the component to iteration needs up front keeps the flow adaptable.
  Prefer a Picklist Choice Set or Record Choice Set over hand-maintained Choice values so the
  flow tracks the org's picklist/records instead of a drifting copy, and prefer a Dependent
  Picklists component over a hand-built cascade so the org field dependency stays the single
  source of truth.
- **Performance** — set size drives the widget. A Choice Lookup with typeahead scales to
  hundreds of options where a Radio Buttons wall or a giant Picklist would degrade the screen
  experience. Right-sizing the component keeps screens fast to render and quick to scan
  (Radio Button Group's compact stacked layout is a scannability optimization).
- **Security** — a Record Choice Set surfaces live records and their fields on a screen, so it
  must respect the running user's record access and field-level security. Never expose a field
  or record through a choice set that the user isn't otherwise entitled to see.
- **Reliability** — because the component and the Choice resource are independent, changing one
  shouldn't silently break the other; but switching a single-select component to multi-select
  changes downstream Loop/Transform compatibility, so treat that switch as a behavioral change,
  not a cosmetic one.

## Architectural Tradeoffs

- **Compact vs visible.** Dropdowns (Picklist, Multi-Select Picklist) save vertical space but
  hide options behind a click; Radio Buttons / Checkbox Group show everything at the cost of
  screen real estate. Radio Button Group is the middle ground for single-select. Choose by set
  size and how much the user benefits from seeing all options at once.
- **Multi-select ergonomics vs downstream compatibility.** Multi-Select Picklist and Checkbox
  Group are the natural multi-select controls, but neither can feed a Loop or Transform. When the
  selection must be iterated, trade the multi-select widget for a Data Table over a record
  collection — a heavier component, but the only Loop-compatible path.
- **Reuse vs bespoke.** Dependent Picklists and Picklist Choice Sets reuse org configuration
  (field dependencies, picklist fields), reducing drift but coupling the flow to that config. A
  hand-entered Choice or a hand-built cascade is self-contained but must be maintained in
  lockstep with the data it mirrors.

## Anti-Patterns

1. **Component-first, cardinality-second** — picking a widget before confirming single vs
   multiple selection and whether the result must be iterated. Decide cardinality and downstream
   processing first; the component falls out of those answers.
2. **One widget for every set size** — defaulting to a Picklist regardless of whether the list
   has 3 options or 300. Scale the widget to the set (Radio Buttons small, Picklist medium,
   Choice Lookup large).
3. **Copying data the org already maintains** — hand-entering Choice values that mirror a
   picklist field, or hand-building a cascade that duplicates a field dependency, instead of a
   Picklist Choice Set or Dependent Picklists component.

## Official Sources Used

- Choose the Right Screen Component for Your Flow — https://help.salesforce.com/s/articleView?id=platform.automate_flow_build_choose_screen_component.htm&language=en_US&type=5
- Give Users a Choice (Trailhead, Screen Flows) — https://trailhead.salesforce.com/content/learn/modules/screen-flows/give-users-a-choice
- Save Screen Space with Radio Button Groups in Screen Flows (Summer '26 release notes) — https://help.salesforce.com/s/articleView?id=release-notes.rn_automate_flow_screens_save_screen_space_with_radio_button_groups_in_screen_flows.htm&language=en_US&release=262&type=5
- Multi-Select Picklist Screen Input Component — https://help.salesforce.com/s/articleView?id=platform.flow_ref_elements_screencmp_msp.htm&language=en_US&type=5
- Checkbox Group Screen Input Component — https://help.salesforce.com/s/articleView?id=platform.flow_ref_elements_screencmp_checkboxgroup.htm&language=en_US&type=5
- Multi-Select Resource and Screen Field Considerations for Flows — https://help.salesforce.com/s/articleView?id=sf.flow_considerations_design_multiselect.htm&language=en_US&type=5
- Choice Lookup Screen Input Component — https://help.salesforce.com/s/articleView?id=platform.flow_ref_elements_screencmp_choice_lookup.htm&language=en_US&type=5
- Dependent Picklists Screen Input Component — https://help.salesforce.com/s/articleView?id=platform.flow_ref_elements_screencmp_dependentpicklists.htm&language=en_US&type=5
- Dependent Picklist Considerations — https://help.salesforce.com/s/articleView?id=platform.fields_dependent_field_considerations.htm&language=en_US&type=5
- Radio Buttons Screen Input Component — https://help.salesforce.com/s/articleView?id=platform.flow_ref_elements_screencmp_radio.htm&language=en_US&type=5
- Switch Between Choice Components When Building Flows (release notes) — https://help.salesforce.com/s/articleView?id=release-notes.rn_automate_flow_builder_choices_swap_components.htm&language=en_US&release=232&type=5
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
