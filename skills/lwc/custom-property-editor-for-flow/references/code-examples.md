# Code Examples — Custom Property Editor for Flow

One deployable slice: a Flow **screen component** (`flowRecordSummary`) that takes a
generic sObject record plus two scalar inputs, and the **custom property editor**
(`flowRecordSummaryEditor`) that configures it in Flow Builder. § 6 shows the same editor
wired to an `@InvocableMethod` instead. Everything here is shaped from the Lightning Web
Components Developer Guide's own CPE examples — see § 9 for the line cites.

Reuse `templates/lwc/component-skeleton/` for the runtime component's loading and error
states and `templates/lwc/jest.config.js` for the Jest configuration; neither is restated
below.

---

## 1. The runtime component — `force-app/main/default/lwc/flowRecordSummary/`

### `flowRecordSummary.js`

```js
import { LightningElement, api } from 'lwc';

export default class FlowRecordSummary extends LightningElement {
    /** Generic sObject supplied by the flow. Declared as type="{T}" in js-meta.xml. */
    @api record;
    /** Heading shown above the summary. */
    @api headingLabel = 'Record Summary';
    /** How many fields to render. */
    @api maxFields = 5;

    get hasRecord() {
        return this.record !== undefined && this.record !== null;
    }
}
```

### `flowRecordSummary.html`

```html
<template>
    <lightning-card title={headingLabel}>
        <template lwc:if={hasRecord}>
            <p class="slds-p-horizontal_small">{record.Name}</p>
        </template>
        <template lwc:else>
            <p class="slds-p-horizontal_small">No record selected.</p>
        </template>
    </lightning-card>
</template>
```

### `flowRecordSummary.js-meta.xml` — this is where the editor gets registered

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <isExposed>true</isExposed>
    <masterLabel>Record Summary</masterLabel>
    <targets>
        <target>lightning__FlowScreen</target>
    </targets>
    <targetConfigs>
        <targetConfig targets="lightning__FlowScreen"
                      configurationEditor="c-flow-record-summary-editor">
            <propertyType name="T" extends="SObject" label="Record Type"
                          description="The object this summary renders."/>
            <property name="record" type="{T}" label="Record"
                      description="The record to summarize." role="inputOnly"/>
            <property name="headingLabel" type="String" label="Heading" default="Record Summary"/>
            <property name="maxFields" type="Integer" label="Fields To Show" default="5"/>
        </targetConfig>
    </targetConfigs>
</LightningComponentBundle>
```

**How to read it**

- `configurationEditor` is an **attribute of `<targetConfig>`**, not a child element:
  `<targetConfig targets="lightning__FlowScreen" configurationEditor="c-volume-editor">`
  (lwc_guide `use-flow-custom-property-editor-lwc-example` L9187; attribute table at
  `targets-lightning-flow-screen` L19104).
- The value is the editor's **kebab-case module reference** with a namespace prefix. Use
  `c` unless the org has a custom namespace, in which case use that namespace
  (lwc_guide L9187, L9389).
- `<propertyType name="T" .../>` declares the generic type; the property then references it
  as `type="{T}"`, curly braces required. A generic sObject **collection** is `type="{T[]}"`
  (lwc_guide `use-flow-custom-property-editor-sobject-lwc-example` L9385).
  UNVERIFIED (2026-09-05): the guide documents the `extends` attribute as "Specifies the
  data type to extend for component properties" and states that only generic sObject and
  sObject collection types can be extended (L19126–19131), but the crawled text does not
  print a sample value; `extends="SObject"` is the conventional value and is not quoted
  from the guide.
- `role` matters for the editor, not just for the runtime surface: **`role="outputOnly"`
  means the property is not exposed in a custom property editor at all**; unset or
  `inputOnly` exposes it (lwc_guide L19128).
- Every component must specify an `apiVersion` from Spring '25 onward (lwc_guide
  `reference-configuration-tags` L18699).

---

## 2. The custom property editor — `force-app/main/default/lwc/flowRecordSummaryEditor/`

### `flowRecordSummaryEditor.js`

```js
import { LightningElement, api } from 'lwc';

const VALUE_CHANGED = 'configuration_editor_input_value_changed';
const VALUE_DELETED = 'configuration_editor_input_value_deleted';
const TYPE_MAPPING_CHANGED = 'configuration_editor_generic_type_mapping_changed';

export default class FlowRecordSummaryEditor extends LightningElement {
    // --- Flow Builder JavaScript interface -------------------------------

    /** Array of { name, value, dataType } for each input variable. */
    _inputVariables = [];
    @api
    get inputVariables() {
        return this._inputVariables;
    }
    set inputVariables(variables) {
        this._inputVariables = variables || [];
    }

    /** Flow metadata: elements and resources in the flow being edited. */
    _builderContext = {};
    @api
    get builderContext() {
        return this._builderContext;
    }
    set builderContext(context) {
        this._builderContext = context || {};
    }

    /** { apiName, type } of the Screen or Action element hosting this editor. */
    _elementInfo = {};
    @api
    get elementInfo() {
        return this._elementInfo;
    }
    set elementInfo(info) {
        this._elementInfo = info || {};
    }

    /** Array of { typeName, typeValue } for generic sObject inputs. */
    _genericTypeMappings = [];
    @api
    get genericTypeMappings() {
        return this._genericTypeMappings;
    }
    set genericTypeMappings(mappings) {
        this._genericTypeMappings = mappings || [];
    }

    // --- Reads -----------------------------------------------------------

    _valueOf(name) {
        const param = this._inputVariables.find((v) => v.name === name);
        return param && param.value;
    }

    get headingLabel() {
        return this._valueOf('headingLabel');
    }

    get maxFields() {
        return this._valueOf('maxFields');
    }

    get selectedRecord() {
        return this._valueOf('record');
    }

    /** typeName is the propertyType's name attribute for a screen component. */
    get recordType() {
        const mapping = this._genericTypeMappings.find((t) => t.typeName === 'T');
        return mapping && mapping.typeValue;
    }

    get typeOptions() {
        return [
            { label: 'Account', value: 'Account' },
            { label: 'Case', value: 'Case' },
            { label: 'Lead', value: 'Lead' }
        ];
    }

    /**
     * builderContext arrives asynchronously and is {} until Flow Builder pushes it.
     * Guard every read; `variables` is absent on a brand-new flow.
     */
    get variableOptions() {
        const variables = (this._builderContext && this._builderContext.variables) || [];
        return variables.map(({ name }) => ({ label: name, value: name }));
    }

    get elementLabel() {
        return this._elementInfo.apiName
            ? `${this._elementInfo.type}: ${this._elementInfo.apiName}`
            : '';
    }

    // --- Writes ----------------------------------------------------------

    _dispatchValueChanged(name, newValue, newValueDataType) {
        this.dispatchEvent(
            new CustomEvent(VALUE_CHANGED, {
                bubbles: true,
                cancelable: false,
                composed: true,
                detail: { name, newValue, newValueDataType }
            })
        );
    }

    handleHeadingChange(event) {
        if (event && event.detail) {
            this._dispatchValueChanged('headingLabel', event.detail.value, 'String');
        }
    }

    handleMaxFieldsChange(event) {
        if (event && event.detail) {
            this._dispatchValueChanged('maxFields', event.detail.value, 'Number');
        }
    }

    handleRecordChange(event) {
        if (!event || !event.detail) {
            return;
        }
        const newValue = event.detail.value;
        if (!newValue) {
            // Clearing an input is a *different* event, not a value change to ''.
            this.dispatchEvent(
                new CustomEvent(VALUE_DELETED, {
                    bubbles: true,
                    cancelable: false,
                    composed: true,
                    detail: { name: 'record' }
                })
            );
            return;
        }
        // A flow variable is a reference, not a literal.
        this._dispatchValueChanged('record', newValue, 'reference');
    }

    handleRecordTypeChange(event) {
        if (event && event.detail) {
            this.dispatchEvent(
                new CustomEvent(TYPE_MAPPING_CHANGED, {
                    bubbles: true,
                    cancelable: false,
                    composed: true,
                    detail: { typeName: 'T', typeValue: event.detail.value }
                })
            );
        }
    }

    // --- Builder-side validation ----------------------------------------

    /**
     * Flow Builder calls this when the admin clicks Done. Return an array of
     * { key, errorString }. Flow Builder shows only the error COUNT — render the
     * strings yourself with setCustomValidity() / reportValidity().
     */
    @api
    validate() {
        const validity = [];
        const headingCmp = this.template.querySelector('[data-id="heading"]');
        const maxFieldsCmp = this.template.querySelector('[data-id="maxFields"]');

        if (!this.recordType) {
            validity.push({
                key: 'RecordType',
                errorString: 'Choose the object this summary renders.'
            });
        }

        const heading = this.headingLabel;
        if (!heading || String(heading).trim().length === 0) {
            if (headingCmp) {
                headingCmp.setCustomValidity('Heading is required.');
                headingCmp.reportValidity();
            }
            validity.push({ key: 'Heading', errorString: 'Heading is required.' });
        } else if (headingCmp) {
            headingCmp.setCustomValidity('');
            headingCmp.reportValidity();
        }

        const max = Number(this.maxFields);
        if (Number.isNaN(max) || max < 1 || max > 20) {
            if (maxFieldsCmp) {
                maxFieldsCmp.setCustomValidity('Fields To Show must be between 1 and 20.');
                maxFieldsCmp.reportValidity();
            }
            validity.push({
                key: 'FieldsToShow',
                errorString: 'Fields To Show must be between 1 and 20.'
            });
        } else if (maxFieldsCmp) {
            maxFieldsCmp.setCustomValidity('');
            maxFieldsCmp.reportValidity();
        }

        return validity;
    }
}
```

### `flowRecordSummaryEditor.html`

```html
<template>
    <div class="slds-p-around_small">
        <p lwc:if={elementLabel} class="slds-text-body_small slds-m-bottom_x-small">
            {elementLabel}
        </p>

        <lightning-combobox
            data-id="recordType"
            label="Object"
            value={recordType}
            options={typeOptions}
            onchange={handleRecordTypeChange}
        ></lightning-combobox>

        <lightning-combobox
            data-id="record"
            label="Record Variable"
            value={selectedRecord}
            options={variableOptions}
            onchange={handleRecordChange}
        ></lightning-combobox>

        <lightning-input
            data-id="heading"
            label="Heading"
            value={headingLabel}
            onchange={handleHeadingChange}
        ></lightning-input>

        <lightning-input
            data-id="maxFields"
            type="number"
            label="Fields To Show"
            value={maxFields}
            onchange={handleMaxFieldsChange}
        ></lightning-input>
    </div>
</template>
```

### `flowRecordSummaryEditor.js-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <isExposed>true</isExposed>
</LightningComponentBundle>
```

**How to read it**

- A CPE bundle has `isExposed` **true** and **no `<targets>` and no `<targetConfigs>`**.
  Every CPE configuration file in the guide's four CPE examples is exactly this shape
  (lwc_guide L9174–9176, L9241–9243, L9375–9377, L9476–9478, L9668–9670). A CPE is never
  placed on a page, so adding `lightning__RecordPage` or `lightning__AppPage` to it is a
  signal that the runtime and editor bundles have been confused.
- `isExposed` cannot be lowered from `true` back to `false` once a managed package is
  published, and while it is `true` the package developer can no longer remove configuration
  targets or `@api` properties (lwc_guide `use-packaging` L7812, L7818). Decide the CPE's
  packaging story before the first release, not after.

---

## 3. Event contract, verbatim from the guide

| Event name | When to dispatch | `detail` keys |
|---|---|---|
| `configuration_editor_input_value_changed` | an input value changes | `name`, `newValue`, `newValueDataType` |
| `configuration_editor_input_value_deleted` | a value is removed from an input | `name` |
| `configuration_editor_generic_type_mapping_changed` | a generic sObject input's type changes | `typeName`, `typeValue` |

All three must be dispatched with `bubbles: true` and `composed: true`; the guide's examples
also set `cancelable: false` (lwc_guide `use-flow-custom-property-editor-interface`
L9736–9762, and every worked example at L9109–9121, L9218–9231, L9302–9345, L9438–9455).

`typeName` is spelled differently on the two surfaces:

| Surface | `typeName` value | Cite |
|---|---|---|
| Screen component | the `propertyType` tag's `name` attribute, e.g. `T` | lwc_guide L9757, L9414 |
| Invocable action | `T__` + input name, `U__` + output name, e.g. `T__inputCollection`, `U__outputMember` | lwc_guide L9757, L9337; api_meta L70192–70199 |

`newValueDataType` values seen in the guide's own examples: `String` (L9118),
`Number` (L9228), `reference` for a flow variable reference (L9343, L9450),
`SObject` for a literal sObject JSON payload (L9653).

---

## 4. Jest test — `flowRecordSummaryEditor/__tests__/flowRecordSummaryEditor.test.js`

```js
import { createElement } from 'lwc';
import FlowRecordSummaryEditor from 'c/flowRecordSummaryEditor';

const INPUT_VARIABLES = [
    { name: 'headingLabel', value: 'Account Summary', dataType: 'String' },
    { name: 'maxFields', value: 5, dataType: 'Number' },
    { name: 'record', value: 'AccountVar', dataType: 'reference' }
];

const BUILDER_CONTEXT = {
    variables: [{ name: 'AccountVar' }, { name: 'CaseVar' }]
};

function buildEditor(overrides = {}) {
    const element = createElement('c-flow-record-summary-editor', {
        is: FlowRecordSummaryEditor
    });
    element.inputVariables = overrides.inputVariables || INPUT_VARIABLES;
    element.builderContext = overrides.builderContext || BUILDER_CONTEXT;
    element.genericTypeMappings =
        overrides.genericTypeMappings || [{ typeName: 'T', typeValue: 'Account' }];
    element.elementInfo = overrides.elementInfo || { apiName: 'Screen_1', type: 'Screen' };
    document.body.appendChild(element);
    return element;
}

describe('c-flow-record-summary-editor', () => {
    afterEach(() => {
        while (document.body.firstChild) {
            document.body.removeChild(document.body.firstChild);
        }
    });

    it('dispatches configuration_editor_input_value_changed with the documented detail shape', () => {
        const element = buildEditor();
        const handler = jest.fn();
        element.addEventListener('configuration_editor_input_value_changed', handler);

        const heading = element.shadowRoot.querySelector('[data-id="heading"]');
        heading.dispatchEvent(new CustomEvent('change', { detail: { value: 'Case Summary' } }));

        expect(handler).toHaveBeenCalledTimes(1);
        const event = handler.mock.calls[0][0];
        expect(event.detail).toEqual({
            name: 'headingLabel',
            newValue: 'Case Summary',
            newValueDataType: 'String'
        });
        // The event must cross the shadow boundary to reach Flow Builder.
        expect(event.bubbles).toBe(true);
        expect(event.composed).toBe(true);
    });

    it('dispatches configuration_editor_generic_type_mapping_changed with typeName T', () => {
        const element = buildEditor();
        const handler = jest.fn();
        element.addEventListener('configuration_editor_generic_type_mapping_changed', handler);

        const combo = element.shadowRoot.querySelector('[data-id="recordType"]');
        combo.dispatchEvent(new CustomEvent('change', { detail: { value: 'Case' } }));

        expect(handler.mock.calls[0][0].detail).toEqual({
            typeName: 'T',
            typeValue: 'Case'
        });
    });

    it('dispatches configuration_editor_input_value_deleted when the record variable is cleared', () => {
        const element = buildEditor();
        const handler = jest.fn();
        element.addEventListener('configuration_editor_input_value_deleted', handler);

        const combo = element.shadowRoot.querySelector('[data-id="record"]');
        combo.dispatchEvent(new CustomEvent('change', { detail: { value: '' } }));

        expect(handler.mock.calls[0][0].detail).toEqual({ name: 'record' });
    });

    it('validate() returns [] when the configuration is complete', () => {
        const element = buildEditor();
        expect(element.validate()).toEqual([]);
    });

    it('validate() returns { key, errorString } entries — never a boolean or an object', () => {
        const element = buildEditor({
            genericTypeMappings: [],
            inputVariables: [
                { name: 'headingLabel', value: '   ', dataType: 'String' },
                { name: 'maxFields', value: 99, dataType: 'Number' }
            ]
        });

        const validity = element.validate();
        expect(Array.isArray(validity)).toBe(true);
        expect(validity).toHaveLength(3);
        validity.forEach((entry) => {
            expect(Object.keys(entry).sort()).toEqual(['errorString', 'key']);
        });
        expect(validity.map((v) => v.key)).toEqual(['RecordType', 'Heading', 'FieldsToShow']);
    });

    it('survives a builderContext that has not arrived yet', () => {
        const element = buildEditor({ builderContext: undefined });
        expect(() => element.validate()).not.toThrow();
        expect(element.shadowRoot.querySelector('[data-id="record"]').options).toEqual([]);
    });
});
```

Run it with `npm run test:unit -- flowRecordSummaryEditor`, using
`templates/lwc/jest.config.js` as the project's `jest.config.js`.

---

## 5. Deploy — `manifest/package.xml`, order, verification

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>flowRecordSummary</members>
        <members>flowRecordSummaryEditor</members>
        <name>LightningComponentBundle</name>
    </types>
    <version>66.0</version>
</Package>
```

**Deploy order.** The editor bundle must exist before anything references it: a
`configurationEditor` value that resolves to nothing is a dangling reference. Deploy both
bundles in one `sf project deploy` call so the reference and its target land together.

```bash
# Retrieve what is already there
sf project retrieve start --metadata LightningComponentBundle:flowRecordSummary

# Run the Jest tests before deploying — they never run in the org
npm run test:unit -- flowRecordSummaryEditor

# Deploy editor + runtime component together
sf project deploy start --manifest manifest/package.xml --target-org myOrg

# Deploy the Apex action variant of § 6 alongside its editor
sf project deploy start \
  --metadata LightningComponentBundle:flowRecordSummaryEditor \
  --metadata ApexClass:RecordSummaryAction \
  --target-org myOrg
```

**Verification — three checks, in this order.**

1. The bundles are in the org:
   ```soql
   SELECT DeveloperName, ApiVersion, IsExposed
   FROM LightningComponentBundle
   WHERE DeveloperName IN ('flowRecordSummary','flowRecordSummaryEditor')
   ```
   UNVERIFIED (2026-09-05): the `LightningComponentBundle` Tooling API object and its
   `IsExposed` field are not described in the Metadata API Developer Guide or the Object
   Reference extracted for this skill; run the query against the Tooling API and fall back
   to `sf project retrieve start --metadata LightningComponentBundle:flowRecordSummary` if
   it does not resolve.
2. **The only check that proves the wiring:** open Flow Builder, add a Screen element,
   drag **Record Summary** onto it. If your editor renders instead of the default text
   boxes and combo boxes, `configurationEditor` resolved. If you see the default property
   pane, the reference is wrong — most often the module reference was written in camelCase
   (`c-flowRecordSummaryEditor`) instead of kebab-case (`c-flow-record-summary-editor`).
3. Click **Done** with the Object picker empty. Flow Builder must refuse to close the
   screen editor and show an error count. That proves `validate()` is being called and is
   returning the `{ key, errorString }` shape.

---

## 6. Same editor, wired to an invocable action instead

For an Apex action the registration lives in the **Apex annotation**, not in any XML file.

```apex
public with sharing class RecordSummaryAction {
    public class Request {
        @InvocableVariable(label='Records' description='Records to summarize' required=true)
        public List<SObject> inputCollection;
    }

    public class Result {
        @InvocableVariable(label='First Record')
        public SObject outputMember;
    }

    @InvocableMethod(
        label='Summarize Records'
        description='Returns the first record from a collection.'
        category='Record Utilities'
        configurationEditor='c-flow-record-summary-editor'
    )
    public static List<Result> summarize(List<Request> requests) {
        List<Result> results = new List<Result>();
        for (Request req : requests) {
            Result r = new Result();
            if (req.inputCollection != null && !req.inputCollection.isEmpty()) {
                r.outputMember = req.inputCollection[0];
            }
            results.add(r);
        }
        return results;
    }
}
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

**What changes inside the editor when the consumer is an action, not a screen component:**

- `genericTypeMappings` `typeName` becomes `T__inputCollection` for the input and
  `U__outputMember` for the output — `T__` and `U__` are prepended automatically
  (lwc_guide L9337–9339, L9757).
- `elementInfo.type` is `Action` rather than `Screen` (lwc_guide L9729–9731). This is the
  only way to disambiguate two instances of the same action in one flow.
- The flow persists the choice as `FlowActionCall.dataTypeMappings`:

```xml
<actionCalls>
    <name>Summarize_Records</name>
    <label>Summarize Records</label>
    <actionName>RecordSummaryAction</actionName>
    <actionType>apex</actionType>
    <dataTypeMappings>
        <typeName>T__inputCollection</typeName>
        <typeValue>Account</typeValue>
    </dataTypeMappings>
    <dataTypeMappings>
        <typeName>U__outputMember</typeName>
        <typeValue>Account</typeValue>
    </dataTypeMappings>
</actionCalls>
```

`FlowActionCall.dataTypeMappings` is available in API version 48.0 and later
(api_meta L68470–68472); `FlowDataTypeMapping.typeName` requires the `T__` prefix for
inputs and `U__` for outputs (api_meta L70192–70199); the sample above is shaped from the
guide's own `Get_Info` action-call sample (api_meta L73210–73229).

The full `@InvocableMethod` modifier contract — including which modifiers exist and what
each defaults to — belongs to `apex/invocable-methods`; read that skill before changing
anything other than `configurationEditor`.

---

## 7. Checker

```bash
python3 skills/lwc/custom-property-editor-for-flow/scripts/check_custom_property_editor_for_flow.py \
  --manifest-dir force-app
# --strict promotes WARN to ERROR (use in CI)
```

---

## 8. What this example deliberately does not do

- It does not read `builderContext.objectInfos`. The Lightning Web Components Developer
  Guide never mentions `objectInfos`; the only `builderContext` member it uses in any CPE
  example is `variables` (L9296, L9420, L9707). Object lists here are a hardcoded
  `typeOptions` array, exactly as the guide's own generic-sObject examples do
  (L9290–9295, L9411–9416). If you need a live object list, fetch it with
  `lightning/uiObjectInfoApi` and treat that as your own addition, not a documented
  `builderContext` field.
- It does not declare `automaticOutputVariables`. That name does not appear anywhere in the
  crawled Lightning Web Components Developer Guide (676 pages, 0 hits). The documented
  Flow Builder JavaScript interface is `inputVariables`, `builderContext`, `elementInfo`,
  `genericTypeMappings`, and `validate` (L9676–9737).

---

## 9. Sources for this file

| Claim | Source |
|---|---|
| `configurationEditor` is a `targetConfig` attribute; namespace `c` | lwc_guide `use-flow-custom-property-editor-lwc-example` L9187; `targets-lightning-flow-screen` L19104 |
| `configurationEditor` on `@InvocableMethod` | apexdev "Supported Modifiers" L5413; lwc_guide L9046 |
| `inputVariables` is an array of `{ name, value, dataType }` | lwc_guide `use-flow-custom-property-editor-interface` L9676–9678; example L9101–9107 |
| `builderContext` exposes flow elements and resources; `variables` used for options | lwc_guide L9680–9682, L9296–9300, L9707–9712 |
| `elementInfo` gives `apiName` + `type` (`Screen` / `Action`) | lwc_guide L9726–9733 |
| `validate()` returns `{ key, errorString }`; Flow Builder shows only the count | lwc_guide L9095–9099, L9231–9238, L9731–9737 |
| The three event names and their `detail` keys; `bubbles`/`composed` true | lwc_guide L9736–9762 |
| `T__` / `U__` prefixes for action generic types; `T` for screen components | lwc_guide L9337–9339, L9414, L9757 |
| `propertyType` / `type="{T}"` / `type="{T[]}"` | lwc_guide L9385, `targets-lightning-flow-screen` L19126–19131 |
| `role="outputOnly"` hides a property from the CPE | lwc_guide L19128 |
| `FlowActionCall.dataTypeMappings`, API 48.0+, `T__`/`U__` prefixes | api_meta L68470–68472, L70177–70199, L73210–73229 |
| `LightningComponentBundle` package.xml and bundle layout | api_meta L84110–84165 |
| Jest structure: `createElement`, `describe`, `afterEach` DOM reset, `shadowRoot` queries | lwc_guide `unit-testing-using-jest-create-tests` L12322–12365 |
| `isExposed` cannot be lowered once published | lwc_guide `use-packaging` L7812, L7818 |
| Spring '25: every component must specify `apiVersion` | lwc_guide `reference-configuration-tags` L18699 |
