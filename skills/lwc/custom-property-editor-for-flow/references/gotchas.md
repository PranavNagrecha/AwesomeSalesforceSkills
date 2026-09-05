# Gotchas - Custom Property Editor For Flow

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.
Line cites are into the crawled Lightning Web Components Developer Guide (`lwc_guide`), the
Metadata API Developer Guide (`api_meta`), and the Apex Developer Guide (`apexdev`).

## Gotcha 1: Metadata Registration Is The Real Entry Point

**What happens:** The editor component exists, but Flow Builder never uses it.

**When it occurs:** The `configurationEditor` metadata hookup is missing or wrong.

**How to avoid:** Treat metadata registration as part of the feature, not as packaging trivia.

---

## Gotcha 2: Builder APIs Are Not Runtime State

**What happens:** Developers try to use builder-specific properties like normal runtime component inputs.

**When it occurs:** The boundary between the editor and the runtime component was not kept clear.

**How to avoid:** Keep `inputVariables`, `builderContext`, and `validate()` scoped to the editor contract.

---

## Gotcha 3: UI Changes Without Event Dispatch Are Lost

**What happens:** The editor appears to change values, but Flow Builder does not persist them.

**When it occurs:** The editor forgets to dispatch the configuration-editor change event.

**How to avoid:** Validate the editor by proving a user change updates the builder model, not just the DOM.

---

## Gotcha 4: `configurationEditor` Is An Attribute, And It Is Registered In Two Different Places

**What happens:** The editor is written correctly and never loads, because the registration
was put in the wrong syntactic slot — or in the wrong file entirely.

**When it occurs:** For a **screen component**, the registration is an attribute on
`<targetConfig>`: `<targetConfig targets="lightning__FlowScreen" configurationEditor="c-volume-editor">`
(lwc_guide L9187; attribute table at L19104, and the identical row for
`lightning__FlowAction` at L19071). Written as a child element
(`<configurationEditor>c-volume-editor</configurationEditor>`) it is not the documented
shape. For an **invocable action** there is no XML at all: the registration is the
`configurationEditor` modifier on `@InvocableMethod` in the Apex class (apexdev
"Supported Modifiers" L5413; lwc_guide L9046, L9251). An action whose editor is declared
only in a `js-meta.xml` somewhere is registered nowhere.

**How to avoid:** Decide which consumer you have first, then register in exactly one place.
The value is a kebab-case module reference (`c-html-email-editor`), namespaced `c` unless
the org has its own namespace (lwc_guide L9046, L9187).

---

## Gotcha 5: `role="outputOnly"` Silently Removes A Property From The Editor

**What happens:** A property is declared, the runtime component reads it fine, and it never
appears in the custom property editor's `inputVariables`.

**When it occurs:** The `property` tag carries `role="outputOnly"`. The guide is explicit:
"If you don't set the role attribute, or if you set it to `inputOnly`, the property is
exposed in a custom property editor. If you set it to `outputOnly`, the property isn't
exposed in a custom property editor" (lwc_guide `targets-lightning-flow-screen` L19128; the
`lightning__FlowAction` table says the same at L19082). The default — no `role` attribute —
allows both input and output.

**How to avoid:** Treat `role` as a CPE visibility switch, not only a runtime direction
switch. A property the admin must configure is `inputOnly` or has no `role` at all.

---

## Gotcha 6: `typeName` Is Spelled Differently For Actions And For Screen Components

**What happens:** `configuration_editor_generic_type_mapping_changed` fires, Flow Builder
accepts the event, and the object choice never sticks.

**When it occurs:** The same editor is reused across an action and a screen component, or a
screen-component editor is written from an action example. For a **screen component**,
`typeName` is the `propertyType` tag's `name` attribute — plain `T`, referenced from the
property as `type="{T}"` with the braces required, or `type="{T[]}"` for a collection
(lwc_guide L9385, L9414, L9757). For an **invocable action**, `T__` is prepended to input
names and `U__` to output names automatically, giving `T__inputCollection` and
`U__outputMember` (lwc_guide L9337–9339, L9757). The Metadata API enforces the same rule
from the other side: `FlowDataTypeMapping.typeName` is "Required. API name of the input or
output variable. The `T__` prefix is required for input variables. The `U__` prefix is
required for output variables" (api_meta L70192–70199).

**How to avoid:** Derive `typeName` from the consumer, and assert it in a Jest test. An
editor shared by both surfaces needs `elementInfo.type` (`Screen` or `Action`, lwc_guide
L9729–9733) to pick the spelling.

---

## Gotcha 7: `validate()` Returns An Array, And Flow Builder Shows Only The Count

**What happens:** The admin clicks **Done**, Flow Builder refuses to close the screen editor
and reports "2 errors" — with no indication of what is wrong. Or the reverse: validation
logic runs, returns a truthy object, and Flow Builder lets the admin save anyway.

**When it occurs:** `validate()` must be `@api` and must return an array of
`{ key, errorString }` objects. "Flow Builder shows only the number of errors. Write code
to show error strings in your custom property editor" (lwc_guide L9731–9735; worked examples
L9091–9099 and L9231–9238). A returned boolean, a `{ isValid, errorMessage }` object, or a
`{ message, severity }` object is not the documented contract. Note that the guide's own
sObject-collection example at L9633–9642 returns `{ message, severity }` — the two disagree,
and the interface reference page is the one that describes the contract.

**How to avoid:** Return `[]` for valid. Render the strings yourself — the guide's example
calls `setCustomValidity()` then `reportValidity()` on the offending base component
(lwc_guide L9235–9238, L9744–9752). Pin the array shape with a Jest assertion, not a
manual click-through.

---

## Gotcha 8: Clearing A Value Is A Different Event From Changing It

**What happens:** The admin blanks an input in the editor. The flow keeps the old value, or
stores an empty string where the flow expected no assignment at all.

**When it occurs:** The editor dispatches `configuration_editor_input_value_changed` with
`newValue: ''` instead of `configuration_editor_input_value_deleted`. The guide lists three
valid event types and says explicitly: "When a value is removed from the input, dispatch a
custom `configuration_editor_input_value_deleted` event" (lwc_guide L9736–9741, L9762).

**How to avoid:** Branch in the change handler on an empty/undefined new value and dispatch
the deletion event instead. This matters most for `reference` values, where an empty string
is not a valid flow resource name.

---

## Gotcha 9: The Event Must Cross The Shadow Boundary Or Flow Builder Never Sees It

**What happens:** The `dispatchEvent` call is present, the event name is correct, the detail
is correct, and nothing reaches Flow Builder.

**When it occurs:** `bubbles` and `composed` both default to `false` on a `CustomEvent`. The
editor is rendered inside Flow Builder's own shadow tree, so a non-composed event stops at
the editor's shadow root. The guide states the requirement directly — "To report input value
changes to Flow Builder, dispatch events from the custom property editor's `handleChange`
function. Set `bubbles` and `composed` to true" (lwc_guide L9736–9737) — and every worked
example sets `bubbles: true, cancelable: false, composed: true` (L9109–9114, L9218–9224,
L9302–9312, L9438–9448, L9645–9651).

**How to avoid:** Assert `event.bubbles === true` and `event.composed === true` in the Jest
test, not just the `detail` payload. Those two flags are the difference between an editor
that works and one that looks like it works.

---

## Gotcha 10: `builderContext` Arrives Asynchronously And Is Not Populated On A New Flow

**What happens:** The editor throws `Cannot read properties of undefined (reading 'map')` in
Flow Builder, usually the first time it is opened on a flow that has no variables yet.

**When it occurs:** `builderContext` is a setter fed by Flow Builder after construction; it
is not available in `constructor()` and its `variables` array is absent on a flow with no
resources. Every guide example reads it as `const variables = this.builderContext.variables`
and then maps (lwc_guide L9296–9300, L9420–9424, L9707–9712) — the guide never shows a
guard, so the guard is yours to add.

**How to avoid:** Store `builderContext` behind a getter/setter pair that defaults to `{}`,
and default `variables` to `[]` at every read site. Cover it with a Jest case that never
sets `builderContext` at all.

---

## Gotcha 11: A CPE Bundle Has No `<targets>`, And `isExposed` Is A One-Way Door In A Package

**What happens:** Either the CPE shows up as a draggable component in Lightning App Builder
where nobody wants it, or a packaged CPE can no longer have properties removed.

**When it occurs:** Every custom property editor configuration file in the guide is
`apiVersion` + `isExposed` **true** and nothing else — no `<targets>`, no `<targetConfigs>`
(lwc_guide L9174–9176, L9241–9243, L9375–9377, L9476–9478, L9668–9670). Adding
`lightning__RecordPage` or `lightning__AppPage` to a CPE is a sign the runtime and editor
bundles were confused. Separately, `isExposed` "can only change from false to true"
(lwc_guide L7812), and once the component is in a published managed package with
`isExposed` true "the package developer can't remove configuration targets or a public
(`@api`) property from a component" — enforced even for targets added after the last
publication (lwc_guide L7818).

**How to avoid:** Keep the CPE bundle to `apiVersion` + `isExposed`. Settle the `@api`
surface of a CPE before the first managed-package release, because after it you can only add.

---

## Gotcha 12: The Guide Documents Where An Action's Type Mapping Is Stored — Not A Screen Component's

**What happens:** An admin's object choice for a generic sObject screen-component property
does not survive a metadata retrieve/deploy round trip, and there is no obvious element to
inspect in the flow XML.

**When it occurs:** For an action the mapping is real, documented metadata:
`FlowActionCall.dataTypeMappings` is "An array of data type mappings for input and output
values that have the generic sObject data type… available in API version 48.0 and later"
(api_meta L68470–68472), with the `Get_Info` sample showing `T__inputCollection` /
`U__outputMember` (api_meta L73210–73229). For a screen component, the corresponding field
`FlowScreenField.dataTypeMappings` is marked **"Reserved for future use."** (api_meta
L71632). UNVERIFIED (2026-09-05): the Metadata API Developer Guide does not document which
`FlowScreenField` field persists a screen component's `{T}` mapping, so do not assume
`dataTypeMappings` on a screen field and do not hand-edit it; retrieve the flow after the
admin saves and read the XML the platform actually wrote.

**How to avoid:** Test the generic-type path on a real flow, save, retrieve, and diff.
Do not build tooling that writes screen-component type mappings into flow metadata directly.
