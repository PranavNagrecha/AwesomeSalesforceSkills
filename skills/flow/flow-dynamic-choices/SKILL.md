---
name: flow-dynamic-choices
description: "Build Flow choice sets from records, picklist fields, or collections, including dependent choices. Triggers: dynamic choices Flow, record choice set, dependent picklist Flow, FlowDynamicChoiceSet, picklistField, collectionReference, valueField, displayField, outputAssignments, choiceReferences, defaultSelectedChoiceReference, semicolon multi-select output. NOT for static hard-coded choices — use flow/screen-flow-choice-component-selection."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Reliability
  - Performance
triggers:
  - "dynamic choice flow"
  - "record choice set flow"
  - "dependent picklist flow"
  - "flow picklist from records"
  - "render flow choices as tiles"
  - "add visual picker to screen flow"
  - "add choice lookup component to screen flow"
  - "let flow users search a filtered list of records"
  - "write the flow xml for a record choice set with filters and outputAssignments"
  - "filter a second screen's choices by what the user picked on the first screen"
  - "my record choice set only returns 200 records"
  - "flow deploy fails on dataType Picklist for a dropdown screen field"
  - "split the semicolon output of a multi-select checkbox field in flow"
  - "why does my flow dropdown pre-select the first record"
  - "get a second field from the record the user selected in a choice set"
  - "test screen flow choices when FlowTest does not support screen flows"
  - "add OR logic to a record choice set filter"
  - "choice set is empty and the required field blocks the screen"
tags:
  - flow
  - choices
  - screen-flow
  - record-choice-set
  - picklist-choice-set
  - collection-choice-set
inputs:
  - "picklist source (SObject query or picklist field)"
  - "filter criteria"
  - "expected set size at p99 and the field the user recognises a row by"
  - "which downstream elements need fields from the selected record"
outputs:
  - "Choice configuration + fallback on empty results"
  - "Deployable `*.flow-meta.xml` with the choice sets, screens and fault routing"
  - "Debug-run verification checklist (FlowTest does not cover screen flows)"
dependencies: []
version: 1.3.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Flow Dynamic Choices

Screen Flows often need choices that reflect current data — active Accounts, open Cases, active picklist values. Record Choice Sets pull from SOQL; Picklist Choice Sets pull from field metadata; Collection Choice Sets iterate a variable. This skill covers each plus dependent-picklist patterns and empty-state handling. Sourcing the choices and rendering them are largely separate decisions — a Record, Picklist, or Collection Choice Set can drive a plain Picklist or Radio Buttons set, while the Visual Picker renders only standalone Choice resources that carry an icon (it doesn't support Record or Picklist Choice Sets). For long or filterable lists, a Choice Lookup component renders any Choice resource as a searchable, typeahead selector with single- or multi-select.

This skill owns the **resource internals**: which of the three sources to use, the
`FlowDynamicChoiceSet` field shape, filter/sort/limit and their cost per screen render, defaults and
re-entry, the multi-select semicolon output, dependent choices, and how to verify any of it without a
`FlowTest`. Which *component* renders the choices belongs to
`flow/screen-flow-choice-component-selection`; the screen's own design belongs to
`flow/screen-flows`.

---

## Before Starting

- Is the source a **field's value set**, a **record query**, or a **collection you already have**?
  The answer picks the type, and the type then dictates the `dataType` — a picklist choice set must
  be `Picklist`/`Multipicklist`, a record choice set must not be (`api_meta.txt` L70269–L70276).
- What is the flow's `<apiVersion>`, and does it clear the floors you need?
  `picklistField`/`picklistObject` are API 35.0, `collectionReference` and the `Record` dataType are
  54.0, `choiceIcon` is 64.0, `inputsOnNextNavToAssocScrn` is 51.0.
- How large is the set at p99? Above 200 the platform truncates for you, silently.
- What is the flow's `runInMode`? A choice set has no sharing context of its own.
- Which fields of the selected record does downstream logic need? Those are `outputAssignments`
  entries, and there is no other route to them.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Where do these choices come from — a picklist field's value set, a query, or a collection this flow already holds?" | It decides the type, and the type decides everything else. Setting `picklistField` + `picklistObject` makes it a picklist choice and disables `displayField`, `filters`, `object`, `outputAssignments`, `sortField`, `sortOrder` and `valueField`, each "Not supported for picklist choices" (`api_meta.txt` L70269–L70386) | The `<dynamicChoiceSets>` block itself, not a description of the data — including the `dataType` that the type forces (Gotcha 6) |
| "How many rows will this return on the biggest account/track/region, and in what order should they appear?" | `limit` is "Maximum **and default**: 200" (L70319–L70321), so omitting it caps at 200 rather than removing a cap; and "if `sortField` and `sortOrder` are also specified, the records are sorted before the limit takes effect" (L70321–L70322) | An explicit `<limit>`, a `sortField` that carries the Sort API field property, and a `sortOrder` — so the truncation is deterministic instead of arbitrary (Gotcha 4) |
| "What should the user see, and what should the flow store?" | `displayField` is the label, `valueField` is the stored value, and they are usually different — "the `displayField` could be the account 'Name' while the `valueField` is the account 'Id'" (L70383–L70389) | Two field API names instead of one, and a check that the label is actually unique enough for a human to choose between two rows |
| "Which fields of the selected record does anything after this screen need?" | `outputAssignments` (`assignToReference` + `field`, both required, L70813–L70823) is the **only** way a record choice set hands you a second field. Without it, authors add a Get Records to re-fetch the row the choice set already had | A named list of fields and target variables, which removes a whole query from the design (Gotcha 7) |
| "What happens when this filter matches nothing?" | `FlowDynamicChoiceSet` extends `FlowElement`, not `FlowNode` (L70267–L70268, L70393–L70398) — no `connector`, no `faultConnector`. An `isRequired` field over an empty set is an interview the user cannot leave | A Get Records before the screen with a Decision on its result — which then also feeds the choice set via `collectionReference`, so the query is paid for once (Gotcha 2) |
| "Do the filter criteria ever need OR, or a mix of AND and OR?" | `FlowRecordLookup` declares `filterLogic` (L71124–L71131); `FlowDynamicChoiceSet`'s twelve documented fields do not (L70278–L70389). Multi-condition logic cannot live on the choice set | A decision to move the logic to a Get Records feeding a collection choice set, before the XML is written rather than after the deploy fails (Gotcha 5) |
| "Can the user go back and change the answer this choice set depends on?" | `allowBack` defaults to `true` (L71434–L71452) and the choice set re-queries on re-render, while `inputsOnNextNavToAssocScrn` defaults to `UseStoredValues` — the previously stored selection survives even if it is no longer in the set (L71733–L71745) | Either `ResetValues` on the dependent field, or `allowBack` `false` with an explicit restart path — decided deliberately rather than inherited from the default (Gotcha 3) |

**What a proper configuration adds over just doing it:** a choice set whose type, `dataType` and
field set follow from where the data actually lives; a truncation point and an order you chose rather
than inherited; every downstream field arriving from the row already fetched; and a verification plan
that survives the fact that `FlowTest` cannot run against a screen flow.

---

## Choice Source Selection

| The source | Type | Required shape | Query at render? | Floor |
|---|---|---|---|---|
| A picklist or multi-select picklist field's value set | Picklist choice set | `picklistField` + `picklistObject`, `dataType` `Picklist` or `Multipicklist` | No — field metadata | API 35.0 |
| Records matching criteria, chosen fresh each render | Record choice set | `object` + `displayField` + `valueField`, `dataType` **not** Picklist/Multipicklist | Yes | API 25.0 for `limit`/`sortField`/`sortOrder` |
| A collection this flow already holds (Get Records, Loop output, a text collection) | Collection choice set | `collectionReference` | No — reads memory | API 54.0 |
| A fixed list the author types | Static `FlowChoice` in `<choices>` | `choiceText` + `dataType` + `value` | No | — |
| A fixed list where one option needs free text | Static `FlowChoice` + `userInput` | `isRequired`, `promptText`, `validationRule`; **not** on multi-select fields | No | — |

Choosing between the last two and the components that render them:
`flow/screen-flow-choice-component-selection`.

---

## `FlowDynamicChoiceSet` Field Map

The twelve fields the guide enumerates (`api_meta.txt` L70278–L70389), and which kind of choice set
each belongs to:

| Field | Record | Picklist | Collection | Notes |
|---|---|---|---|---|
| `dataType` | required, not Picklist/Multipicklist | required, **must** be Picklist or Multipicklist | required | `Record` value is API 54.0+ |
| `object` | required | not supported | — | The object queried |
| `displayField` | required | not supported | — | What the user reads |
| `valueField` | — | not supported | — | What the flow stores; picklist choices always store the API value |
| `filters` | supported | not supported | — | `FlowRecordFilter[]`; `value` can be an `elementReference` |
| `limit` | supported | not supported | — | **Maximum and default: 200**; API 25.0+, nillable 45.0+ |
| `sortField` / `sortOrder` | supported | not supported | — | Applied *before* `limit`; `sortField` needs the Sort API field property |
| `outputAssignments` | supported | not supported | — | `assignToReference` + `field`, both required |
| `picklistField` / `picklistObject` | not supported | required | — | API 35.0+; these two are the discriminator |
| `collectionReference` | — | — | required | API 54.0+ |
| `filterLogic` | **does not exist on this type** | — | — | It exists on `FlowRecordLookup` (L71124–L71131) |

---

## Consuming the Choice Set on a Screen

`choiceReferences` is a `string[]` naming `FlowChoice`s or `FlowDynamicChoiceSet`s, and it is
supported on exactly four `fieldType` values — `RadioButtons`, `DropdownBox`,
`MultiSelectCheckboxes`, `MultiSelectPicklist` (`api_meta.txt` L71588–L71601). Three rules that trip
people up:

- **The field's `dataType` is not the choice set's `dataType`.** `FlowScreenField.dataType` accepts
  Boolean, Currency, Date, DateTime, Number, String, Time — there is no `Picklist` value
  (L71611–L71621). A field over a picklist choice set is `String`.
- **Multi-select fields are `String` only**, and at runtime they store "a concatenation of the
  user-selected choice values, separated by semicolons"; any semicolon inside a choice value is
  stripped (L71625–L71628, L71714–L71720).
- **A `DropdownBox` with no `defaultSelectedChoiceReference` defaults to row 0** — "the reference at
  index 0 of `choiceReferences` is used as the default value", for DropdownBox only (L71642–L71646).
  RadioButtons does not do this.

---

## Key Considerations

- Sharing comes from the flow's `runInMode`, not from the choice set. `DefaultMode` defers to how
  the flow was launched; `SystemModeWithSharing` enforces record access but explicitly **not** object
  permissions or field-level access; `SystemModeWithoutSharing` enforces neither (`api_meta.txt`
  L68374–L68393). A `displayField` label can render for a user who could not read that field
  anywhere else.
- A set larger than 200 is not a design the platform supports — `limit`'s maximum is 200. Filter, or
  switch to a search surface.
- Picklist Choice Set uses the field's available values; inactive values don't appear. Historical
  records carrying a retired value have nothing to select. Mix in a Record Choice Set on an active
  flag, or show the historical value as read-only text.
- `UNVERIFIED (2026-09-05)`: nothing in the Metadata API guide says whether a picklist choice set is
  scoped to a **record type**'s value set or returns the field's full set. `picklistField` /
  `picklistObject` name a field and an object and no record type (L70341–L70360), and the type has no
  record-type field. Confirm with a debug run under a restricted record type; see
  `admin/picklist-and-value-sets` for value-set design.
- Field dependencies defined in metadata are not the same thing as a dependent choice set. In a
  screen flow, "dependent" means a second choice set whose `filters` reference the first screen's
  stored value — see `references/metadata-examples.md` §1. Test the metadata-dependency behaviour
  separately.
- Visual Picker (introduced in Summer '25 / release 256) renders Choice resources as icon-and-text tiles instead of a dropdown or radio list, so users can pick faster with visual cues. It's a standard screen input component listed alongside Picklist, Radio Buttons, and Checkbox Group — not a custom LWC, so reach for it before building one. It's configured using standalone Choice resources (text data type, each carrying an SLDS icon) and doesn't yet support Record Choice Sets or Picklist Choice Sets — map those into standalone Choice resources first. `UNVERIFIED (2026-09-05)`: "Visual Picker" is a help.salesforce.com name absent from the `FlowScreenFieldType` enum (L71677–L71713), so in metadata it is a `ComponentInstance` field.
- A Choice resource must carry an icon before it renders as a tile in a Visual Picker. Choices without an icon fall back to a plain list and are wasted on a Visual Picker. In metadata the icon is `FlowChoice.choiceIcon`, a `FlowIcon` carrying `iconName`, API 64.0 and later (L69880–L69882, L70631–L70637).
- Choice Lookup renders any Choice resource as a searchable, typeahead selector — the right pick for long or filterable lists. It shows 20 options first, loads 100 more each scroll up to 1,020 displayed, and resets to 20 when a filter is reapplied, so keep the underlying set well-filtered enough that the target stays reachable. `UNVERIFIED (2026-09-05)`: those load numbers are help-page claims; a single choice set cannot exceed 200 choices anyway.
- Choice Lookup single- vs multi-select is a per-component toggle ("Let Users Select Multiple Options"); multi-select allows up to 25 selections and shipped GA in Winter '25 (no beta phase). It isn't supported in Classic runtime for flows — wire multi-select output to a collection variable.
- Standard Lookup vs Choice Lookup: the standard Lookup surfaces recent and global-search records with no author-defined filter; Choice Lookup restricts users to a filtered Record or Collection Choice Set. Pick Choice Lookup when the selectable records must be constrained — see the official "Choose a Lookup Option for a Flow Screen" guide.
- Choice Lookup is a reactive screen component (Reactive Screen Components GA, Winter '24), so it can update live in response to another selection on the same screen — the basis for dependent choices without a page reload — and applies across Essentials, Professional, Enterprise, Performance, Unlimited, and Developer editions. Summer '26 also extended Style-tab overrides (colors, borders that override the org/site theme) to Choice Lookup for per-screen branding.

---

## Recommended Workflow

1. **Pick the source with the Choice Source Selection table**, then write the `dataType` the type
   forces. Getting this wrong is a deploy failure, not a run-time bug.
2. **Answer the seven Questions above** and write the answers into
   `templates/flow-dynamic-choices-template.md`. The `limit`, the `sortField`, the
   `outputAssignments` list and the empty-set branch all come from that sheet, not from the XML
   editor.
3. **Write the XML from `references/metadata-examples.md` §1**, adapting the object names. It is a
   complete two-screen flow with a picklist choice set, static choices with a `userInput`, a
   dependent record choice set with `filters`/`sortField`/`limit`/`outputAssignments`, a collection
   choice set, a multi-select field, and a Decision on the chosen values. §2 has the
   `Multipicklist` variant; §3 has the semicolon-to-collection routes.
4. **Put the empty-set branch in before the screen, not on it.** A Get Records with the same filters,
   a Decision on its result, and — if the same rows feed the screen — a collection choice set over
   its output, which also gives you the `faultConnector` a choice set cannot have.
5. **Run the checker** —
   `python3 skills/flow/flow-dynamic-choices/scripts/check_flow_dynamic_choices.py --manifest-dir <source tree> --strict` —
   and clear every ERROR. E1/E2 catch the `dataType` discriminator, E4/E5 the screen-field enum,
   E8 the default that isn't in the list, E9 a multi-select wired to a non-text variable.
6. **Deploy in the order in `references/metadata-examples.md` §5** (objects and value sets → FLS →
   flow as `Draft`), then work the §6 debug-run checklist: least-privileged persona, a Workflow log
   at FINER for `FLOW_ELEMENT_LIMIT_USAGE`, a Back-then-Forward pass, a mid-interview data change,
   and the empty-set path. Do **not** write a `FlowTest` — it does not cover screen flows.
7. **Record every UNVERIFIED you resolved against your own org** in the flow's `<description>`, so
   the next author inherits the answer instead of the question.

---

## Worked Examples (see `references/examples.md`)

- *Active Account picker* — Case creation flow, and why the `limit` is load-bearing
- *Country → State dependent* — the one `filters` entry that makes a choice set dependent
- *Icon tile picker* — Visual Picker rendering of a Choice resource
- *Searchable record picker* — Choice Lookup over a filtered Record Choice Set
- *Multi-select output* — the table of what the flow actually receives, semicolons and all
- *Collection choice set* — swapping a second query for `collectionReference`

---

## Common Gotchas (see `references/gotchas.md`)

1. Sharing comes from `runInMode`, not from the choice set — and `SystemModeWithSharing` skips FLS.
2. An empty result set plus `isRequired` is an interview the user cannot leave, with no fault path.
3. `allowBack` re-renders the choice set but `UseStoredValues` keeps the stale selection.
4. `limit`'s default *is* its maximum; omitting it caps at 200 rather than removing a cap.
5. `FlowDynamicChoiceSet` has no `filterLogic` — every filter combines implicitly.
6. `picklistField` is the discriminator, and it forces the `dataType` both ways.
7. `outputAssignments` is the only route to a second field from the selected record.
8. `FlowScreenField.dataType` has no `Picklist` value; copying the choice set's fails the deploy.
9. A multi-select field is one semicolon-joined string, and it strips semicolons from your values.
10. There is no split — no operator and no formula turns a delimited string into a collection.
11. A `DropdownBox` with no default silently selects `choiceReferences` index 0.
12. `defaultSelectedChoiceReference` names a `FlowChoice`, and only one, even on multi-select.
13. Screen flows cannot be `FlowTest`ed — the debug log is the instrument.
14. A Visual Picker choice with no icon renders as a plain list.
15. Choice Lookup's display cap hides distant options.
16. Multi-select Choice Lookup needs a collection output and Lightning runtime.

---

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Copying the choice set's `Picklist` `dataType` onto the screen field that consumes it
- Adding `filterLogic` to a dynamic choice set by analogy with Get Records
- Treating an omitted `limit` as "no limit"
- Promising a `SPLIT()` that does not exist for the multi-select semicolon output
- Putting a `faultConnector` on a choice set — it isn't a `FlowNode`
- Generating a `FlowTest` for a screen flow
- Re-querying the record the user just selected instead of using `outputAssignments`
- Standard Lookup when the list must be filtered — that's Choice Lookup's job

---

## Proactive Triggers

Surface these WITHOUT being asked:

- **A record choice set with no `<limit>`** → High. It fetches 200 rows per render and the author
  believes it fetches all of them.
- **A record choice set with `limit` and no `sortField`** → High. Reads as top N, behaves as
  arbitrary N.
- **`<dataType>Picklist</dataType>` on a screen field** → Critical. Not a `FlowScreenField` value;
  the deploy fails.
- **A `filterLogic` element inside `<dynamicChoiceSets>`** → Critical. Not a field of this type.
- **An `isRequired` choice field with no upstream empty-set branch** → Critical. A reachable
  dead-end screen.
- **A multi-select field feeding a Loop, a Decision on equality, or a non-text variable** → High.
  The value is one semicolon-joined string.
- **A `.flowtest-meta.xml` next to a `processType` `Flow`** → High. Dead metadata; the checklist it
  greens is lying.
- **A DropdownBox over a record choice set with no explicit default** → Medium. Index 0 is
  pre-selected and the interview records a choice nobody made.
- **A second Get Records that re-fetches the record a choice set already selected** → Medium.
  `outputAssignments` had it.
- **A seasonal release name attached to a choice-set capability** → Medium. State the API version;
  this corpus has no release-name mapping.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Source decision | Picklist vs record vs collection vs static, with the `dataType` the type forces and the API floor it needs |
| Deployable flow XML | `*.flow-meta.xml` with the choice sets, the dependent `filters`, the screens and the fault routing, shaped from `references/metadata-examples.md` §1 |
| Query budget | `limit`, `sortField`, `sortOrder` per choice set, plus whether any of them can collapse into one Get Records + `collectionReference` |
| Output map | Every `outputAssignments` `field` → variable pair the downstream logic needs |
| Empty-set plan | The Get Records, the Decision and the message screen that stop a required field over an empty set |
| Debug-run checklist | The §6 verification steps, since `FlowTest` does not cover screen flows |
| Checker report | ERROR/WARN/ADVISORY findings from `scripts/check_flow_dynamic_choices.py` |

---

## Official Sources Used

- Metadata API Developer Guide — `FlowDynamicChoiceSet`, `FlowChoice`, `FlowScreenField`, `FlowScreen`, `FlowTest` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Apex Developer Guide — debug log event types (`FLOW_ELEMENT_*`) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
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

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | You are writing or reviewing actual `*.flow-meta.xml`: a complete two-screen flow with all four choice sources, the `Multipicklist` variant, the semicolon-to-collection routes, `package.xml`, deploy order, and the debug-run verification checklist |
| `references/gotchas.md` | The flow deploys and then does the wrong thing quietly — sharing, the empty set, `allowBack` re-render, the 200 default, the missing `filterLogic`, index-0 defaults, and the FlowTest negative |
| `references/llm-anti-patterns.md` | You are reviewing generated Flow XML or Flow choice advice, or self-checking your own — including the invented `SPLIT()`, the copied `Picklist` dataType, and the generated FlowTest |
| `references/examples.md` | You want the narrative walk-through, the dependent-filter fragment, or the table of what a multi-select field actually stores, before writing XML |
| `references/well-architected.md` | You need the pillar tradeoffs, the query-budget levers, or the source and guide line behind any claim in this skill |
| `templates/flow-dynamic-choices-template.md` | You are recording the source decision, the query budget and the output map for someone else to build or review |
| `scripts/check_flow_dynamic_choices.py` | Before every deploy and against any fixture directory. `--manifest-dir <source tree>`, optional `--strict`; exits 1 on any ERROR |

## Related Skills

- **flow/screen-flow-choice-component-selection** — when the question is *which component* renders
  the choices (Picklist, Radio Buttons, Checkbox Group, Choice Lookup, Data Table) rather than how
  the choice resource is built.
- **flow/screen-flows** — when the screen's navigation, layout or commit timing is the question.
- **flow/flow-screen-lwc-components** — when a custom screen component has to consume or produce the
  choice, and `choiceReferences` is not available to it.
- **flow/flow-collection-processing** — when the collection feeding a collection choice set has to be
  filtered, sorted or transformed first.
- **flow/flow-formula-and-expression-patterns** — when the `CONTAINS` / `SUBSTITUTE` formula over a
  multi-select value, or a choice `userInput` validation formula, has to be correct.
- **flow/flow-get-records-optimization** — when the Get Records that feeds a collection choice set is
  itself the cost.
- **flow/flow-testing** — for what `FlowTest` *does* cover, and the debug-interview strategy for what
  it doesn't.
- **flow/fault-handling** — when the fault routing around the Get Records and the DML needs
  designing.
- **admin/picklist-and-value-sets** — when the value set behind a picklist choice set (global value
  sets, record-type scoping, retiring a value) is the real problem.
