# Well-Architected Notes — Flow Dynamic Choices

**UX:** data-driven choices; render icon-tagged choices as Visual Picker tiles so users pick faster from visual cues, and use a Choice Lookup component for long or filterable lists where searchable single- or multi-select (up to 25) beats a dropdown. **Reliability:** empty-state handling.

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
