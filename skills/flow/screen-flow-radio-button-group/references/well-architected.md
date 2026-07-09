# Well-Architected Notes — Screen Flow Radio Button Group

## Relevant Pillars

- **User Experience** — the component exists to save screen real estate: it renders options as
  compact boxes stacked horizontally on desktop and vertically on mobile, reducing the scrolling
  that a traditional single-column radio list, checkbox group, or picklist imposes. Applying it
  where it helps (few, visible, mutually-exclusive options) and *not* where it hurts (15 boxes in
  a grid, or an audience that relies on the most conventional radio layout) is the core UX call.
  The compact layout still has to earn its accessibility: verify labels, focus order, and
  selected-state contrast on both form factors rather than assuming the new component passes.
- **Reliability** — the single-select vs *Let Users Select Multiple Options* choice determines
  whether the output is a single value or a collection. Building downstream Decisions,
  Assignments, formulas, and reactive references to the *wrong* shape is a silent-failure class
  of bug. Reliability here means matching the stored-variable type and the read operator
  (`equals` vs `Contains`/iteration) to the selected mode, and giving dynamic choice sources an
  empty-result path so a zero-option group can't strand a required screen.
- **Security** — choices sourced from records (Record Choice Sets) run in the flow's context;
  respect the running user's access and don't surface records or field values the user shouldn't
  see. This is a property of the choice *source*, not the box layout.
- **Performance** — a Record Choice Set backing the component issues a query per interview; keep
  its filters selective and its result set small, the same discipline any dynamic choice needs.

## Architectural Tradeoffs

- **Compactness vs familiarity.** The box layout saves space but is newer and less conventional
  than a single-column radio list. For dense screens it's a clear win; for an accessibility-first
  or habit-bound audience, the traditional Radio Buttons component may be the safer default.
- **Single-select simplicity vs multi-select flexibility.** Single-select keeps a scalar output
  and simple downstream logic. Enabling multi-select adds real flexibility but converts the output
  to a collection and ripples through every consumer — adopt it deliberately, not as an afterthought.
- **Static vs dynamic choices.** Static choices are simplest and fastest; dynamic choice sets stay
  current with data but add a query and an empty-state to handle. Choose the source independently
  of the component (see `flow/flow-dynamic-choices`).

## Anti-Patterns

1. **Flipping to multi-select without retyping the output** — enabling *Let Users Select Multiple
   Options* while leaving a single-value variable and `equals` logic in place. Retype to a
   collection and switch to `Contains`/iteration instead.
2. **Assuming compact means accessible** — shipping the box layout without verifying focus order
   and contrast, then failing an audit that the old radio list passed.
3. **Empty dynamic choices with no fallback** — binding to a Record/Picklist/Collection Choice Set
   that can return zero rows and stranding the user on a required screen; add an explicit
   empty-state path.

## Official Sources Used

- Save Screen Space with Radio Button Groups in Screen Flows (Summer '26 release notes, Automate/Flow) — https://help.salesforce.com/s/articleView?id=release-notes.rn_automate_flow_screens_save_screen_space_with_radio_button_groups_in_screen_flows.htm&type=5&language=en_US
- Add Compact Radio Button Groups to Screen Flows (Summer '26 release notes, Experience Cloud) — https://help.salesforce.com/s/articleView?id=release-notes.rn_experience_add_compact_radio_button_groups_to_screen_flows.htm&type=5&language=en_US
- Radio Buttons Screen Input Component (Flow reference) — https://help.salesforce.com/s/articleView?id=platform.flow_ref_elements_screencmp_radio.htm&type=5&language=en_US
- Choice (Flow resource reference) — https://help.salesforce.com/s/articleView?id=platform.flow_ref_resources_choice.htm&type=5&language=en_US
- lightning-radio-group (base component documentation) — https://developer.salesforce.com/docs/component-library/bundle/lightning-radio-group/documentation
- lightning-checkbox-group (base component documentation) — https://developer.salesforce.com/docs/component-library/bundle/lightning-checkbox-group/documentation
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
