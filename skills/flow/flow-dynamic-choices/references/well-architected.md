# Well-Architected Notes — Flow Dynamic Choices

**UX:** data-driven choices; render icon-tagged choices as Visual Picker tiles so users pick faster from visual cues, and use a Choice Lookup component for long or filterable lists where searchable single- or multi-select (up to 25) beats a dropdown. **Reliability:** empty-state handling.

## Pillar Tradeoffs

| Pillar | The choice-set decision that moves it | The cost of getting it wrong |
|---|---|---|
| Performance | Record choice set (queries per render) vs collection choice set over one Get Records (`collectionReference`, API 54.0+) vs picklist choice set (metadata, no query) | Two record choice sets on one screen are two queries every time the user navigates back and forward |
| Reliability | Whether the zero-row case has a branch. A choice set extends `FlowElement`, so it has no `faultConnector` and no `connector` | A required field over an empty set is an interview the user cannot leave and cannot report |
| Security | `runInMode`, not the choice set. `SystemModeWithSharing` enforces record access but explicitly not FLS | The `displayField` label renders for a user who could not read that field anywhere else |
| User Experience | `limit` + `sortField` + `sortOrder` together, and the component behind the choice set | 200 arbitrary rows in arbitrary order, with row 0 silently pre-selected on a DropdownBox |
| Operational Excellence | Whether verification is a debug run with `FLOW_ELEMENT_LIMIT_USAGE` or a `FlowTest` that cannot run | A green release checklist covering nothing, because FlowTest excludes screen flows |

## Where the budget goes

A screen with two record choice sets spends its query budget at **render** time, on a screen the
user may revisit. The three levers, in order of leverage:

1. Move the query upstream into a Get Records and feed the choice set with `collectionReference` —
   one query, a fault path, and a Decision on the empty case.
2. Set `limit` to what the screen can actually show. The default is the maximum (200), not "all".
3. Use a picklist choice set where the source really is a value set. `picklistField` /
   `picklistObject` read field *metadata*; there is no record query at all.

Measure rather than assume: `FLOW_ELEMENT_LIMIT_USAGE` reports incremented usage per element across
SOQL queries, SOQL query rows, DML statements, CPU time and heap.

## Official Sources Used

- Metadata API Developer Guide — `FlowDynamicChoiceSet` (api_meta.txt L70267–L70389) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (the record/picklist/collection discriminator, `dataType` enum and its API floors, `displayField`, `filters`, `limit` "Maximum and default: 200", `object`, `outputAssignments`, `picklistField`/`picklistObject`, `sortField`/`sortOrder`, `valueField`, `collectionReference` API 54.0+, and the absence of `filterLogic`)
- Metadata API Developer Guide — `FlowScreenField` (api_meta.txt L71583–L71833) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (`choiceReferences` and the four field types that accept it, the screen-field `dataType` enum that has no Picklist value, `defaultSelectedChoiceReference` and the DropdownBox index-0 rule, the semicolon-concatenation of multi-select values, `inputsOnNextNavToAssocScrn`, `isRequired`)
- Metadata API Developer Guide — `FlowChoice` and `FlowChoiceUserInput` (api_meta.txt L69875–L69925) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (`choiceText`, `dataType`, `value` including the null-value behaviour, `choiceIcon` API 64.0+, and `userInput` with `isRequired` / `promptText` / `validationRule` being unsupported on multi-select fields)
- Metadata API Developer Guide — `FlowScreen`, `FlowRecordLookup`, `FlowRecordFilter`, `FlowOutputFieldAssignment` (api_meta.txt L70813–L70823, L71069–L71090, L71105–L71230, L71427–L71521) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (`allowBack`/`allowFinish`/`allowPause` defaults and the "not both" rule, `showHeader`/`showFooter` and their Classic exclusion, `faultConnector` on Get Records, `filterLogic` where it does exist, filter operators, and the required `assignToReference` + `field` pair)
- Metadata API Developer Guide — `Flow` root type, `FlowAssignmentOperator`, `FlowFormula`, `FlowTest` (api_meta.txt L68065–L68445, L69767–L69865, L70596–L70612, L73960–L73990) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (`processType` `Flow` = screen flow, `runInMode` values and what each does and does not enforce, `status` enum, the fifteen assignment operators and the Metadata-API-only `Add`-a-collection note, formula scalar return types, and FlowTest's scope of record-triggered / autolaunched / Data Cloud-triggered flows)
- Apex Developer Guide — debug log event types (apexdev.txt L38768–L38805) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf (`FLOW_ELEMENT_BEGIN`/`END`, `FLOW_ELEMENT_ERROR`, `FLOW_ELEMENT_FAULT` and `FLOW_ELEMENT_LIMIT_USAGE` with its per-element SOQL / row / DML / CPU / heap breakdown — the instrument that replaces FlowTest for a screen flow)
- Flow Builder Guide — https://help.salesforce.com/s/articleView?id=sf.flow.htm (Flow Builder UI naming for choice resources; not fetchable in this environment, so UI-only claims carry UNVERIFIED markers)
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
