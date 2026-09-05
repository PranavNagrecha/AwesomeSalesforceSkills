# Examples - Custom Property Editor For Flow

Short narrative walk-throughs. The full deployable slice — both bundles, the `js-meta.xml`
files, the Jest test, `package.xml`, deploy order and verification — is in
`references/code-examples.md`.

## Example 1: Metadata Hook To The Editor

**Context:** A reusable Flow screen component needs a guided design-time configuration experience.

**Problem:** The runtime component exists, but Flow Builder still shows only the default property pane.

**Solution:** Register the editor as the `configurationEditor` **attribute** on the
`<targetConfig>` of the runtime component's `js-meta.xml`, using a kebab-case module
reference: `<targetConfig targets="lightning__FlowScreen" configurationEditor="c-volume-editor">`
(lwc_guide L9187). For an invocable action there is no XML: the same value goes in the
`configurationEditor` modifier on `@InvocableMethod` (apexdev L5413).

**Why it works:** Flow Builder can only load the custom editor when the metadata contract points to it.

---

## Example 2: Value-Change Event From The Editor

**Context:** The custom editor renders inputs, but changes do not persist back into Flow Builder.

**Problem:** The editor UI updates itself without notifying the builder contract.

**Solution:**

```javascript
this.dispatchEvent(
  new CustomEvent('configuration_editor_input_value_changed', {
    bubbles: true,
    cancelable: false,
    composed: true,
    detail: {
      name: 'label',
      newValue: event.target.value,
      newValueDataType: 'String'
    }
  })
);
```

**Why it works:** The editor now communicates the updated design-time value through the
expected event contract. `bubbles` and `composed` are not optional decoration — the guide
requires both to be `true` so the event escapes the editor's shadow root and reaches Flow
Builder (lwc_guide L9736–9737).

---

## Example 3: What The Builder Actually Hands You

**Context:** An agent is writing the getters before it has ever seen the payloads, and
guesses that `inputVariables` is an object.

**Problem:** Every read is written as `this.inputVariables.headingLabel`, which is
`undefined` for all four interfaces.

**Solution:** Model the four inbound payloads first. For a screen component named
`Record Summary` sitting on `Screen_1` of a flow that declares one Account variable, Flow
Builder pushes approximately this. UNVERIFIED (2026-09-05): the guide documents each
field name individually but never prints a complete inbound payload, so this composite is
assembled from those field names rather than quoted:

```json
{
  "inputVariables": [
    { "name": "headingLabel", "value": "Account Summary", "dataType": "String" },
    { "name": "maxFields",    "value": 5,                 "dataType": "Number" },
    { "name": "record",       "value": "AccountVar",      "dataType": "reference" }
  ],
  "genericTypeMappings": [
    { "typeName": "T", "typeValue": "Account" }
  ],
  "elementInfo": { "apiName": "Screen_1", "type": "Screen" },
  "builderContext": {
    "variables": [
      { "name": "AccountVar" },
      { "name": "SummaryHeading" }
    ]
  }
}
```

Read it with `find`, never with dot access:

```javascript
get headingLabel() {
  const param = this.inputVariables.find(({ name }) => name === 'headingLabel');
  return param && param.value;
}
```

**Why it works:** `inputVariables` and `genericTypeMappings` are arrays with a `name`/`value`
and `typeName`/`typeValue` shape respectively (lwc_guide L9676–9678, L9754–9756);
`elementInfo` carries the element's API name and a `type` of `Screen` or `Action`
(lwc_guide L9726–9733); `builderContext` carries the flow's elements and resources, and the
guide's examples read only `builderContext.variables` from it (lwc_guide L9680–9682,
L9296–9300). The same editor pointed at an invocable action gets `T__inputCollection`
instead of `T` — that difference is Gotcha 6.

---

## Anti-Pattern: One LWC Doing Everything

**What practitioners do:** They blur runtime behavior and builder-only editing behavior into one mental model.

**What goes wrong:** The component becomes harder to reason about and Flow Builder integration breaks in subtle ways.

**Correct approach:** Keep runtime and design-time concerns separate and connected by a clear contract.
