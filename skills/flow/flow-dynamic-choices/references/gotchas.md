# Gotchas — Flow Dynamic Choices

Line citations are into the Metadata API Developer Guide text extract
(`api_meta.txt`, Summer '26 / v62 of
<https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf>) and the Apex
Developer Guide extract (`apexdev.txt`). Claims that rest on help.salesforce.com — which cannot be
fetched here — carry an `UNVERIFIED (2026-09-05)` marker beside them.

## Gotcha 1: Sharing depends on `runInMode`, not on the choice set

**What happens:** The picker offers records the user then can't open, or the picker is empty for a
user who can see the records perfectly well in a list view.

**When it occurs:** A record choice set has no context of its own. The flow's `runInMode` decides:
`DefaultMode` means "how the flow is launched determines whether the flow runs in user context or in
system context"; `SystemModeWithSharing` "respects org-wide default settings, role hierarchies,
sharing rules, manual sharing, teams, and territories" but "doesn't respect object permissions,
field-level access, or other permissions of the running user"; `SystemModeWithoutSharing` "can access
all data" (`api_meta.txt` L68374–L68393, API 48.0+; `SystemModeWithoutSharing` API 49.0+). So the
same choice set changes its result set when the flow is embedded somewhere else.

**How to avoid:** Set `runInMode` explicitly rather than leaving it at `DefaultMode`, then debug-run
as the least-privileged persona. `SystemModeWithSharing` is the usual answer for a choice set: record
access is enforced, but FLS on the `displayField` and on every `outputAssignments/field` is not — so
the label renders for a user who could not read that field in a report.

---

## Gotcha 2: The empty result set makes a required field unpassable

**What happens:** The user reaches a screen with a dropdown containing nothing, `isRequired` is
`true`, and Next is unreachable. The interview dead-ends with no error and no fault path.

**When it occurs:** The `filters` matched zero rows — a track with no open offering, a parent with no
children, a user whose sharing hides everything. `FlowDynamicChoiceSet` extends `FlowElement`, not
`FlowNode` (`api_meta.txt` L70267–L70268, L70393–L70398), so it has **no `faultConnector` and no
`connector`** — there is nothing to route and nothing to catch. `isRequired` on the screen field is
enforced regardless of how many choices rendered (L71746–L71749).

**How to avoid:** Put a Get Records with the same `filters` *before* the screen and a Decision on its
result. Route the zero-row case to a message screen. A record choice set gives you no branch point;
a Get Records does — and its collection can then feed a collection choice set via
`collectionReference`, so you pay for the query once instead of twice.

---

## Gotcha 3: `allowBack` re-renders the choice set but not the stored value

**What happens:** The user goes back, the underlying record changes (or another screen's selection
changes), the user comes forward — and the field still shows a value that is no longer in the set,
or silently loses one that is.

**When it occurs:** `allowBack` defaults to `true` (`api_meta.txt` L71434–L71452), and a dynamic
choice set is evaluated when its screen renders. `inputsOnNextNavToAssocScrn` governs what happens to
the stored input: `UseStoredValues` (the default) "uses values from when the user last visited this
screen"; `ResetValues` "refreshes inputs to incorporate changes elsewhere in the flow"
(L71733–L71745). The default therefore preserves a selection that the re-queried set may no longer
contain.

**How to avoid:** On any screen whose choice sets depend on an earlier screen, set
`inputsOnNextNavToAssocScrn` to `ResetValues` — or set `allowBack` to `false` and give the user an
explicit "start over" path instead. `UNVERIFIED (2026-09-05)`: the guide scopes this property to
"screen components in API version 51.0 and later and to record fields on flow screens in API version
57.0 and later" without saying whether a plain `DropdownBox` counts as a screen component here; the
guide's own sample only sets it on `ComponentInstance` fields (L73505, L73545). Confirm in a debug
run before relying on it.

---

## Gotcha 4: `limit`'s default IS its maximum — omitting it does not mean "all"

**What happens:** A choice set built to show "every active product" quietly truncates at 200, and the
201st row is invisible with no error, no warning and no log entry.

**When it occurs:** `FlowDynamicChoiceSet.limit` is documented as "Maximum **and default**: 200"
(`api_meta.txt` L70319–L70321). Leaving `<limit>` out does not remove the ceiling; it sets it to 200.
And because "if `sortField` and `sortOrder` are also specified, the records are sorted before the
limit takes effect" (L70321–L70322), an unsorted choice set returns an arbitrary 200 of N.

**How to avoid:** Always write `<limit>` explicitly at the number the UI can actually handle, and
always pair it with `sortField` + `sortOrder` so the truncation is deterministic. If the honest
answer is more than 200 selectable records, the design is wrong — a choice set is not a search
surface. The checker's W1 and A1 rules flag both halves.

---

## Gotcha 5: `FlowDynamicChoiceSet` has no `filterLogic` — every filter ANDs

**What happens:** An author writes two filters meaning "either of these", and the choice set returns
the intersection. Or they add `<filterLogic>1 OR 2</filterLogic>` by analogy with Get Records, and
the deploy fails on an unknown field.

**When it occurs:** `FlowRecordLookup` (L71124–L71131), `FlowRecordCreate` (L70968–L70974) and
`FlowRelatedRecordLookup` all declare `filterLogic`. `FlowDynamicChoiceSet`'s field table
(L70278–L70386) enumerates twelve fields and **`filterLogic` is not among them** — the type extends
`FlowElement`, whose only fields are `description` and `name` (L70393–L70398).

**How to avoid:** Model OR logic upstream: a Get Records with `filterLogic`, storing to a record
collection, feeding a collection choice set through `collectionReference`. `UNVERIFIED (2026-09-05)`:
the guide never states the combining operator for multiple `filters` on a dynamic choice set; AND is
the inference from every sibling type that documents a default, not a printed claim. Verify with a
debug run against records that match only one filter.

---

## Gotcha 6: The picklist/record discriminator is `picklistField`, and it decides `dataType`

**What happens:** A deploy fails with an enum error on `dataType`, or a choice set that looks like a
record choice set behaves like a picklist choice set (no filters applied, `displayField` ignored).

**When it occurs:** The guide makes this a hard, mutually exclusive rule. "If a dynamic choice
doesn't have the `picklistField` and `picklistObject` parameters set, it's a record choice and it
**can't** have a data type of `Picklist` or `Multipicklist`." "If a dynamic choice **has** the
`picklistField` and `picklistObject` parameters set, it's a picklist choice and it **must** have a
data type of `Picklist` or `Multipicklist`" (`api_meta.txt` L70269–L70276). Setting `picklistField`
also silently disables `displayField`, `filters`, `object`, `outputAssignments`, `sortField`,
`sortOrder` and `valueField`, each marked "Not supported for picklist choices" (L70303–L70386).

**How to avoid:** Decide which of the two you are building before writing any XML, and let the
`dataType` follow from that. The checker's E1/E2 rules are exactly this pair.

---

## Gotcha 7: `outputAssignments` is the only way a record choice set hands you a second field

**What happens:** An author adds a Get Records after the screen to re-fetch the record the user just
picked — a second query for data the choice set already had.

**When it occurs:** `valueField` stores one value, usually `Id` (`api_meta.txt` L70383–L70390). Every
other field of the selected record reaches the flow only through `outputAssignments`, an array of
`FlowOutputFieldAssignment` where both `assignToReference` and `field` are required
(L70813–L70823). The guide's own example is assigning "the ID and AnnualRevenue from the
user-selected account to variables that you specify" (L70333–L70340).

**How to avoid:** List every field the downstream logic needs as an `outputAssignments` entry on the
choice set. It costs nothing extra — the row was already fetched. It is also the *only* place these
values come from: `outputAssignments` is "Not supported for picklist choices", so a picklist choice
set can never hand you a related field.

---

## Gotcha 8: `FlowScreenField.dataType` has no `Picklist` value

**What happens:** The choice set declares `<dataType>Picklist</dataType>`, an author copies that onto
the `DropdownBox` that consumes it, and the deploy fails on an enum the error message doesn't name
helpfully.

**When it occurs:** The two types have different enums and the same field name.
`FlowDynamicChoiceSet.dataType` accepts Boolean, Currency, Date, Multipicklist, Number, Picklist,
Record, String and Time (`api_meta.txt` L70281–L70301). `FlowScreenField.dataType` accepts Boolean,
Currency, Date, DateTime, Number, String and Time — no Picklist, no Multipicklist, no Record — and is
"only supported for the InputField, RadioButtons, and DropdownBox types of screen components"
(L71611–L71621).

**How to avoid:** A screen field consuming a picklist choice set is `<dataType>String</dataType>`.
The guide's own sample flow does exactly this: `dynamicChoiceSets` `accounts` with
`<dataType>String</dataType>`, consumed by a `DropdownBox` also declaring `String`
(L73353–L73366, L73508–L73515). The checker's E4 rule catches the copy.

---

## Gotcha 9: A multi-select field is one string, and it eats semicolons in your values

**What happens:** A downstream Decision, formula or DML gets `Interpreter;Step Free;Large Print` where
it expected a collection — or a choice whose value was `Level 1; advanced` comes back as
`Level 1 advanced` with the semicolon gone and no error.

**When it occurs:** "At runtime, each multi-select field stores its field value as a concatenation of
the user-selected choice values, separated by semicolons. **Any semicolons in the selected choice
values are removed** when added to the multi-select field value" (`api_meta.txt` L71714–L71720). Only
`String` is supported as the `dataType` for multi-select checkboxes and multi-select picklist fields
(L71625–L71628), and `FlowChoiceUserInput` "isn't supported for choices in multi-select fields"
(L69902–L69905) — so you cannot even collect a free-text alternative on one.

**How to avoid:** Never put a semicolon in a `FlowChoice.value` that a multi-select field will use.
Treat the output as a delimited string: `CONTAINS()` in a formula, or the `Contains` comparison
operator in a Decision (L70066–L70110). See Gotcha 10 before assuming you can split it.

---

## Gotcha 10: There is no split — Flow cannot turn a delimited string into a collection

**What happens:** An author writes a formula intended to return a text collection, or looks for a
"Split" operator that does not exist, and ships a design that cannot be built declaratively.

**When it occurs:** `FlowAssignmentOperator` enumerates fifteen values — `Add`, `AddAtStart`,
`AddItem`, `Assign`, `AssignCount`, `RemoveAfterFirst`, `RemoveAll`, `RemoveBeforeFirst`,
`RemoveFirst`, `RemovePosition`, `RemoveUncommon`, `Subtract` and friends (`api_meta.txt`
L69767–L69865) — and none decomposes a string. `FlowFormula.dataType` is Boolean, Currency, Date,
DateTime, Number, String or Time (L70596–L70612): a formula returns one scalar, never a collection.

**How to avoid:** Either keep the semicolon string and test membership with `CONTAINS`, or build the
collection one value at a time — a Decision on a Boolean formula per value, routing to an Assignment
with the `Add` operator and a literal `<stringValue>`. And note the trap on the shortcut: `Add`
accepts a *collection* as its value only "in API version 43.0 and later, but **only via Metadata
API**. From Flow Builder, you can't save an Assignment element that contains a collection variable in
the Value column for the `Add` operator" (L69786–L69790) — hand-written XML that does it deploys and
then makes the flow un-editable in Builder.

---

## Gotcha 11: A `DropdownBox` with no default silently defaults to row 0

**What happens:** The flow records a selection the user never made. Every interview where the user
clicked straight through carries the first sorted record.

**When it occurs:** "For `DropdownBox` field types **only**, if `defaultSelectedChoiceReference` is
empty or null, the reference at index 0 of `choiceReferences` is used as the default value"
(`api_meta.txt` L71642–L71646). With a record choice set behind it, index 0 is whatever `sortField` +
`sortOrder` put first — which, if `sortField` is absent, is arbitrary and can change between renders.
RadioButtons, MultiSelectCheckboxes and MultiSelectPicklist do **not** do this; only DropdownBox.

**How to avoid:** For a DropdownBox over a record choice set, either use `RadioButtons` (no implicit
default), or add a static "-- Select --" `FlowChoice` at index 0 with a null `value` — "if null, this
choice always has the value of null" (L69896–L69898) — and make the field `isRequired`, so an
untouched dropdown fails validation instead of passing silently.

---

## Gotcha 12: `defaultSelectedChoiceReference` must name a `FlowChoice`, and only one

**What happens:** A deploy fails, or a multi-select field renders with fewer defaults than the author
listed.

**When it occurs:** The field is a single `string`, and the guide describes it as "the name of the
**FlowChoice** element to use as the default value" (`api_meta.txt` L71634–L71636) — not a choice
*set*. For multi-select fields it adds: "You can specify only **one** FlowChoice element as the
default value for multi-select checkboxes and multi-select picklist fields" (L71647–L71659).

**How to avoid:** Point it at a static `FlowChoice` that also appears in that field's
`choiceReferences`. `UNVERIFIED (2026-09-05)`: the guide does not state what happens when
`defaultSelectedChoiceReference` names a `FlowDynamicChoiceSet` rather than a `FlowChoice`; the
wording says FlowChoice, so the checker's E8 rule only verifies membership in `choiceReferences`.
Pre-selecting a *record* therefore has no documented shape — do it with a screen-field
`visibilityRule` or an Assignment before the screen instead.

---

## Gotcha 13: Screen flows cannot be `FlowTest`ed — the test file is dead metadata

**What happens:** A generated `.flowtest-meta.xml` sits in the repo next to a screen flow, passes
nothing, covers nothing, and gives a release checklist a green tick it hasn't earned.

**When it occurs:** `FlowTest` "represents the metadata associated with a flow test. Before you
activate a **record-triggered, autolaunched, or Data Cloud-triggered** flow, you can test it to
verify its expected results and identify flow run-time failures" (`api_meta.txt` L73960–L73962).
A choice-driven flow is `processType` `Flow` — "a flow that requires user interaction because it
contains one or more screens or local actions, choices, or dynamic choices. In the UI and Salesforce
Help, it's a screen flow" (L68270–L68274). Screen flows are not in the enumerated scope.

**How to avoid:** Verify choice behaviour with a debug run and a Workflow debug log, not a FlowTest.
`FLOW_ELEMENT_LIMIT_USAGE` reports "incremented usage toward a limit for this element" across SOQL
queries, SOQL query rows, DML statements, CPU time and heap (`apexdev.txt` L38795–L38805), which is
how you find out what a screen with two choice sets actually costs; `FLOW_ELEMENT_ERROR` and
`FLOW_ELEMENT_FAULT` carry the element name for the failure and fault paths (L38777–L38793). The
checker's A3 rule flags an Active screen flow that a FlowTest names.
`UNVERIFIED (2026-09-05)`: neither guide states that each record choice set issues exactly one SOQL
query per screen render — `FLOW_ELEMENT_LIMIT_USAGE` is the instrument that settles it for your org.

---

## Gotcha 14: Visual Picker choice with no icon

**What happens:** The choice shows up but not as an icon tile — the visual cue you wanted is missing.

**When it occurs:** A Choice resource is fed to a Visual Picker component without an icon attached.
The icon is what makes it render as a tile. At the metadata level the icon is `FlowChoice.choiceIcon`,
a `FlowIcon` whose only field is `iconName`, "the name of the selected Salesforce Lightning Design
System icon", available in API version 64.0 and later (`api_meta.txt` L69880–L69882, L70631–L70637).
`UNVERIFIED (2026-09-05)`: "Visual Picker" is a Flow Builder / help.salesforce.com name. It is not a
`FlowScreenFieldType` value (`api_meta.txt` L71677–L71713), so in metadata it is a
`ComponentInstance` field — which also explains why it does not take `choiceReferences`, a field
supported only on RadioButtons, DropdownBox, MultiSelectCheckboxes and MultiSelectPicklist
(L71588–L71601).

**How to avoid:** Attach an icon to every Choice resource before pointing a Visual Picker at it. If
choices legitimately have no icon, use a Picklist or Radio Buttons component instead of a Visual
Picker.

---

## Gotcha 15: Choice Lookup display cap hides distant options

**What happens:** A user can't reach a record that exists in the underlying set.

**When it occurs:** Choice Lookup renders 20 options initially, loads 100 more each scroll, and caps
at 1,020 displayed choices (reapplying a filter resets to 20). An unfiltered set larger than that
leaves records unreachable by scrolling. `UNVERIFIED (2026-09-05)`: these load numbers come from the
Choice Lookup help page, which cannot be fetched here. The one number that *is* grounded caps the
problem anyway: a single `FlowDynamicChoiceSet` cannot produce more than 200 choices at all
(`api_meta.txt` L70319–L70321), so a set of 1,020 has to be assembled from several sources.

**How to avoid:** Filter the Record or Collection Choice Set down to a workable size and rely on the
component's typeahead search rather than the scroll cap.

---

## Gotcha 16: Multi-select Choice Lookup needs a collection output and Lightning runtime

**What happens:** Selections are lost, or the component doesn't work at all.

**When it occurs:** "Let Users Select Multiple Options" = Yes lets users pick up to 25 choices, but
the output has to go to a collection variable, and multi-select Choice Lookup isn't supported in
Classic runtime for flows. `UNVERIFIED (2026-09-05)`: the 25-selection cap and the Classic exclusion
are help.salesforce.com claims. The metadata corroboration is indirect: `showFooter` and `showHeader`
both say "Classic runtime isn't supported" (`api_meta.txt` L71506–L71521), so screen behaviour
diverging by runtime is a documented pattern rather than an invention.

**How to avoid:** Wire the multi-select output to a collection and run the flow in Lightning runtime.
With a single-select Choice Lookup over a record choice set, only the last record the user selects is
stored — expected for single-select, but a trap if you assumed the component held several.
