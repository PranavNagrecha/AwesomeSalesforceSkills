# LLM Anti-Patterns — Flow Dynamic Choices

What an AI assistant gets wrong when it writes or reviews Flow choice-set metadata, and the
grounded correction. Line citations are into `api_meta.txt` (Metadata API Developer Guide, Summer
'26 / v62).

## Anti-Pattern 1: Copying the choice set's `dataType` onto the screen field

`FlowDynamicChoiceSet.dataType` and `FlowScreenField.dataType` are different enums with the same
field name. A picklist choice set **must** be `Picklist` or `Multipicklist` (L70273–L70276); the
`DropdownBox` consuming it has no such value available — Boolean, Currency, Date, DateTime, Number,
String, Time only (L71611–L71621). The field is `String`. The guide's own sample does exactly this
(L73353–L73366 feeding L73508–L73515). Checker rule E4.

## Anti-Pattern 2: Adding `filterLogic` to a dynamic choice set

Because `FlowRecordLookup` has it (L71124–L71131), a model assumes the choice set does too. It does
not: `FlowDynamicChoiceSet`'s twelve documented fields (L70278–L70389) contain no `filterLogic`, and
`FlowElement` adds only `description` and `name` (L70393–L70398). OR logic between choice-set
criteria has to move to a Get Records feeding a collection choice set. Checker rule W2.

## Anti-Pattern 3: Treating omitted `limit` as "no limit"

The most confident wrong sentence in this area is "leave `limit` off and the choice set returns all
matching records." `limit` is documented "Maximum **and default**: 200" (L70319–L70321). Omitting it
sets 200; it does not remove the ceiling. Pair the number with `sortField` + `sortOrder` or the 200
you get is an arbitrary 200 (L70321–L70322). Checker rules W1 and A1.

## Anti-Pattern 4: Promising a formula or an operator that splits the semicolon output

A multi-select field "stores its field value as a concatenation of the user-selected choice values,
separated by semicolons" (L71714–L71720), and a model then invents a `SPLIT()` function or a "Split
Collection" element to turn it into a collection. Neither exists: `FlowAssignmentOperator` has
fifteen values and none decomposes a string (L69767–L69865), and `FlowFormula.dataType` returns one
scalar (L70596–L70612). Build the collection one `CONTAINS` test and one `Add` assignment at a time,
or keep the delimited string and use the `Contains` comparison operator.

## Anti-Pattern 5: Putting a `faultConnector` on a choice set

`FlowDynamicChoiceSet` extends `FlowElement`, not `FlowNode` (L70267–L70268, L70393–L70398) — it has
no `connector`, no `faultConnector`, and no place in the canvas graph. A query failure inside a
choice set surfaces on the screen that renders it. The routable failure lives on the Get Records or
the DML next to it (`faultConnector` at L71120 and L70965 respectively).

## Anti-Pattern 6: Generating a `FlowTest` for a screen flow

`FlowTest` covers "record-triggered, autolaunched, or Data Cloud-triggered" flows (L73960–L73962). A
choice-driven flow is `processType` `Flow` — the screen flow (L68270–L68274). A generated
`.flowtest-meta.xml` against one is dead metadata that makes a release checklist look green. Verify
with a debug run and the Workflow debug log instead (`apexdev.txt` L38768–L38805). Checker rule A3.

## Anti-Pattern 7: Writing an unbounded, unsorted, unfiltered record choice set

"Pull all Accounts into a dropdown" is the default generated answer. It is 200 rows of SOQL per
screen render, in arbitrary order, that a user cannot scan. Filter to the working set, sort it, limit
it, and if the honest set is larger than a person can scan, the requirement is a search surface, not
a choice set — route to `flow/screen-flow-choice-component-selection` for the component decision.

## Anti-Pattern 8: Ignoring the DropdownBox index-0 default

Generated flows routinely omit `defaultSelectedChoiceReference` and treat the field as unanswered.
"For DropdownBox field types only, if `defaultSelectedChoiceReference` is empty or null, the
reference at index 0 of `choiceReferences` is used as the default value" (L71642–L71646). Every
click-through interview then records the first sorted record as a deliberate choice.

## Anti-Pattern 9: Re-querying the selected record after the screen

A model adds a Get Records to fetch fields of the record the user just picked. `outputAssignments`
already delivers them from the row the choice set fetched — `assignToReference` + `field`, both
required (L70813–L70823), the guide's example being "the ID and AnnualRevenue from the user-selected
account" (L70333–L70340). The second query is pure waste.

## Anti-Pattern 10: Dating a choice capability by seasonal release name

"Available since Winter '24" is unsourced in this corpus: the developer guides state API version
floors, not release names. State the number — `picklistField`/`picklistObject` API 35.0,
`collectionReference` and the `Record` dataType API 54.0, `choiceIcon` API 64.0,
`inputsOnNextNavToAssocScrn` API 51.0 — and let the reader map it.

## Anti-Pattern 11: Ignoring sharing implications, or asserting the wrong default

"Record Choice Sets ignore sharing by default" is wrong. `runInMode` decides: `DefaultMode` defers to
how the flow was launched, `SystemModeWithSharing` enforces record access but not FLS,
`SystemModeWithoutSharing` enforces neither (L68374–L68393). A choice set has no context of its own.

## Anti-Pattern 12: Building a custom LWC for a tile picker or a filtered lookup

The standard Visual Picker renders icon-tagged Choice resources as tiles, and Choice Lookup renders
any Choice resource as a searchable typeahead over an author-filtered set — reach for those before
writing a component. `UNVERIFIED (2026-09-05)`: both are Flow Builder / help.salesforce.com names,
absent from the `FlowScreenFieldType` enum (L71677–L71713), so in metadata they are
`ComponentInstance` fields. If a component genuinely is needed, `lwc/lwc-in-flow-screens` owns it.

## Anti-Pattern 13: Assuming Choice Lookup multi-select works everywhere

Multi-select Choice Lookup output belongs in a collection variable, not a single-value variable, and
it is not supported in Classic runtime for flows. `UNVERIFIED (2026-09-05)`: help.salesforce.com
claim. The metadata corroboration is that `showFooter` and `showHeader` both carry "Classic runtime
isn't supported" (L71506–L71521) — runtime-divergent screen behaviour is a documented pattern.
