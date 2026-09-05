# Code Examples — LWC App Builder Config

One component, four surfaces, four different admin experiences. Everything below is deployable as written: the bundle, the Apex datasource class and its test, the Jest suite, and the manifest.

Line citations of the form `lwc_guide <page-slug> L<n>` point at the crawled Lightning Web Components Developer Guide; `apexrefguide L<n>` points at the Apex Reference Guide.

Related canonical templates — reference them, do not re-invent them:

- `templates/lwc/component-skeleton/` — the bundle skeleton (html / js / css / js-meta.xml / `__tests__`)
- `templates/lwc/jest.config.js` — the Jest config this suite assumes
- `templates/lwc/patterns/wireServicePattern.js` — when the component fetches its own data instead of receiving it

---

## The Scenario

`pipelineSummary` shows a small ranked list of amounts with an optional total. It must appear:

| Surface | Admin knobs | Objects | Form factors |
|---|---|---|---|
| Record Page | title, amount field (schema-driven), max rows, show totals | Case, Account | Large + Small |
| App Page | title (fixed list), max rows, show totals | n/a | Large + Small |
| Home Page | title, max rows | n/a | Large only |
| Experience Cloud | title, show totals, accent colour | n/a | n/a |

---

## 1. `pipelineSummary.js-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>63.0</apiVersion>
    <isExposed>true</isExposed>
    <masterLabel>Pipeline Summary</masterLabel>
    <description>Ranked amounts for the current context, with an optional total.</description>

    <targets>
        <target>lightning__RecordPage</target>
        <target>lightning__AppPage</target>
        <target>lightning__HomePage</target>
        <target>lightningCommunity__Page</target>
        <target>lightningCommunity__Default</target>
    </targets>

    <targetConfigs>
        <targetConfig targets="lightning__RecordPage">
            <objects>
                <object>Case</object>
                <object>Account</object>
            </objects>
            <property
                name="cardTitle"
                type="String"
                label="Card Title"
                description="Heading shown above the list."
                default="Pipeline Summary"
                placeholder="Pipeline Summary"/>
            <property
                name="amountField"
                type="String"
                label="Amount Field"
                description="Currency field to rank and total. The list is built from the object on this page."
                datasource="apex://PipelineFieldPickList"/>
            <property
                name="maxRows"
                type="Integer"
                label="Rows To Show"
                description="Between 1 and 50."
                default="10"
                min="1"
                max="50"/>
            <property
                name="showTotals"
                type="Boolean"
                label="Show Total"
                default="true"/>
            <supportedFormFactors>
                <supportedFormFactor type="Large"/>
                <supportedFormFactor type="Small"/>
            </supportedFormFactors>
        </targetConfig>

        <targetConfig targets="lightning__AppPage">
            <property
                name="cardTitle"
                type="String"
                label="Card Title"
                datasource="Team Pipeline,Regional Pipeline,Global Pipeline"
                default="Team Pipeline"/>
            <property
                name="maxRows"
                type="Integer"
                label="Rows To Show"
                default="10"
                min="1"
                max="50"/>
            <property
                name="showTotals"
                type="Boolean"
                label="Show Total"
                default="true"/>
            <supportedFormFactors>
                <supportedFormFactor type="Large"/>
                <supportedFormFactor type="Small"/>
            </supportedFormFactors>
        </targetConfig>

        <targetConfig targets="lightning__HomePage">
            <property
                name="cardTitle"
                type="String"
                label="Card Title"
                default="My Pipeline"/>
            <property
                name="maxRows"
                type="Integer"
                label="Rows To Show"
                default="5"
                min="1"
                max="50"/>
            <supportedFormFactors>
                <supportedFormFactor type="Large"/>
            </supportedFormFactors>
        </targetConfig>

        <targetConfig targets="lightningCommunity__Default">
            <property
                name="cardTitle"
                type="String"
                label="Card Title"
                default="My Pipeline"/>
            <property
                name="showTotals"
                type="Boolean"
                label="Show Total"
                default="false"/>
            <property
                name="accentColor"
                type="Color"
                label="Accent Colour"
                default="rgba(0, 112, 210, 1)"/>
        </targetConfig>
    </targetConfigs>
</LightningComponentBundle>
```

### How to read it

- **`isExposed` + at least one `target`** are both required for the component to reach a builder — `isExposed` alone does nothing (`lwc_guide reference-configuration-tags` L18711–L18712).
- **`<objects>` sits only in the record-page block.** It works only inside a `targetConfig` configured for `lightning__RecordPage`, may appear once, and does not support external objects (`lwc_guide targets-lightning-record-page` L19363–L19367). Leaving it out would make the component droppable on every UI-API-supported object.
- **The form-factor child tag is `supportedFormFactor`, singular, with a `type` attribute** whose values are `Large` (desktop) and `Small` (phone) — L18994–L18998. The set is declared once per `targetConfig`, never at the bundle root.
- **Home page gets `Large` only** because Home pages support only the `Large` form factor (`lwc_guide use-config-form-factors` L9795).
- **`Color` appears only in the `lightningCommunity__Default` block.** The App Builder targets document `Boolean`, `Integer`, `String` and nothing else (L18972–L18975, L19197–L19199, L19351–L19353); `Color` is documented for `lightningCommunity__Default` (L18778).
- **`lightningCommunity__Page` carries no `targetConfig`.** It is the drag-and-drop entry in the Components panel and supports no component properties; the editable properties live in the `lightningCommunity__Default` block (L18811–L18812, `use-config-for-community-builder` L8106–L8110).
- **`datasource` is `String`-only** and takes either a static comma-separated list or `apex://ClassName` (L18976).
- **`min`/`max` apply only to `Integer`** and `placeholder` only to `String` (L18980–L18982).
- **`default` on a required property is not optional in practice**: a required property with no default makes the component appear invalid the moment it is added in App Builder (`use-config-for-app-builder-tips` L9899).

---

## 2. `pipelineSummary.js`

```javascript
import { LightningElement, api } from 'lwc';

const DEFAULT_ROWS = 10;
const MAX_ROWS = 50;

export default class PipelineSummary extends LightningElement {
    /* ---- design attributes: one @api per `property name` in the meta file ---- */

    @api cardTitle = 'Pipeline Summary';
    @api amountField = 'Amount';
    @api accentColor = 'rgba(0, 112, 210, 1)';

    _maxRows = DEFAULT_ROWS;

    @api
    get maxRows() {
        return this._maxRows;
    }

    // App Builder hands design-attribute values in as-configured; a component that
    // is also reused programmatically can receive a string. Coerce and clamp once,
    // at the boundary, so the rest of the class only ever sees a safe number.
    set maxRows(value) {
        const parsed = Number(value);
        this._maxRows =
            Number.isFinite(parsed) && parsed >= 1
                ? Math.min(Math.trunc(parsed), MAX_ROWS)
                : DEFAULT_ROWS;
    }

    _showTotals = true;

    @api
    get showTotals() {
        return this._showTotals;
    }

    set showTotals(value) {
        this._showTotals = value === true || value === 'true';
    }

    /* ---- platform-populated context: declared in JS, never in the meta file ---- */

    @api recordId;
    @api objectApiName;
    @api flexipageRegionWidth;

    /* ---- composition seam: not a design attribute, so it is absent from the meta file ---- */

    @api rows = [];

    get hasContext() {
        return Boolean(this.recordId && this.objectApiName);
    }

    get visibleRows() {
        return this.rows.slice(0, this.maxRows);
    }

    get total() {
        return this.visibleRows.reduce((sum, row) => sum + Number(row.amount || 0), 0);
    }

    // flexipageRegionWidth is SMALL | MEDIUM | LARGE and drives layout via CSS.
    get regionClass() {
        return `pipeline-summary ${this.flexipageRegionWidth || 'MEDIUM'}`;
    }
}
```

### How to read it

- Every `<property name="…">` in the meta file has a matching `@api` field here. The guide states the value must match the property name in the component's JavaScript class (L18971).
- `recordId`, `objectApiName` and `flexipageRegionWidth` are declared with `@api` but never appear in the meta file — the platform populates them. `recordId` and `objectApiName` are set only in an explicit record context, so the component must not depend on them (`lwc_guide use-record-context` L7893, `use-object-context` L7913). `flexipageRegionWidth` receives the App Builder region width, and its CSS class values are `SMALL`, `MEDIUM`, `LARGE` (`use-width-aware` L7925–L7931).
- `rows` is an extra `@api` with no meta entry. That direction is fine — a public property does not have to be admin-configurable. The reverse (a `property name` with no `@api`) is the failure the checker flags.
- The JS initializers are what a Jest test sees. Jest tests are local and run independently of Salesforce (`unit-testing-using-jest-create-tests` L12326), so the meta file's `default` never reaches the component under test. Keeping the two in step is a manual discipline; the Jest suite below pins the JS side and the checker compares names, but nothing compares the two default *values*.
- When the JS type and the config type disagree, the configuration file wins (L18972, `use-config-for-app-builder` L9840). That is why the setters coerce rather than assume.

---

## 3. `pipelineSummary.html`

```html
<template>
    <lightning-card title={cardTitle} icon-name="standard:opportunity">
        <div class={regionClass}>
            <template lwc:if={hasContext}>
                <p class="slds-p-horizontal_small slds-text-body_small">
                    {objectApiName} · {recordId} · {amountField}
                </p>
            </template>

            <ul class="slds-p-horizontal_small">
                <template for:each={visibleRows} for:item="row">
                    <li key={row.id} class="slds-border_bottom slds-p-vertical_xx-small">
                        {row.label} — {row.amount}
                    </li>
                </template>
            </ul>

            <template lwc:if={showTotals}>
                <p class="slds-p-horizontal_small slds-text-title_bold">Total: {total}</p>
            </template>
        </div>
    </lightning-card>
</template>
```

Note what is *not* here: `lightning-datatable`. This bundle declares `<supportedFormFactor type="Small"/>`, and `lightning-datatable` and `lightning-tree-grid` are not supported on mobile devices (`lwc_guide data-table-vs-tree-grid` L5600). A plain list renders everywhere the component claims to render. The checker flags the combination.

---

## 4. `PipelineFieldPickList.cls`

```apex
/**
 * Design-time datasource for the `amountField` design attribute.
 * Referenced from the meta file as datasource="apex://PipelineFieldPickList".
 */
global with sharing class PipelineFieldPickList extends VisualEditor.DynamicPickList {

    private static final Set<Schema.DisplayType> NUMERIC_TYPES = new Set<Schema.DisplayType>{
        Schema.DisplayType.CURRENCY,
        Schema.DisplayType.DOUBLE,
        Schema.DisplayType.PERCENT
    };

    private VisualEditor.DesignTimePageContext context;

    // The parameterized constructor is what makes DesignTimePageContext available.
    global PipelineFieldPickList(VisualEditor.DesignTimePageContext context) {
        this.context = context;
    }

    global override VisualEditor.DataRow getDefaultValue() {
        return new VisualEditor.DataRow('Amount', 'Amount');
    }

    global override VisualEditor.DynamicPickListRows getValues() {
        VisualEditor.DynamicPickListRows rows = new VisualEditor.DynamicPickListRows();

        String entity = 'Opportunity';
        if (this.context != null && String.isNotBlank(this.context.entityName)) {
            entity = this.context.entityName;
        }

        List<Schema.DescribeSObjectResult> described =
            Schema.describeSObjects(new List<String>{ entity });
        if (described.isEmpty()) {
            rows.addRow(new VisualEditor.DataRow('Amount', 'Amount'));
            return rows;
        }

        for (Schema.SObjectField f : described[0].fields.getMap().values()) {
            Schema.DescribeFieldResult d = f.getDescribe();
            // Design time still runs as the admin: never offer a field they cannot read.
            if (NUMERIC_TYPES.contains(d.getType()) && d.isAccessible()) {
                rows.addRow(new VisualEditor.DataRow(d.getLabel(), d.getName()));
            }
        }

        rows.sort();
        // false => a type-ahead search in the property panel only searches the first
        // 200 values that were displayed, not the complete set.
        rows.setContainsAllRows(true);
        return rows;
    }
}
```

`PipelineFieldPickList.cls-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>63.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

### How to read it

- `VisualEditor.DynamicPickList` is an abstract class used to display picklist values in a Lightning component on a Lightning page; a custom class extends it and is then named in the component's design file (`apexrefguide` L247820–L247830).
- The overridable methods are `getDefaultValue()` returning a `VisualEditor.DataRow`, `getValues()` returning `VisualEditor.DynamicPickListRows`, plus `getLabel(attributeValue)` and `isValid(attributeValue)` (`apexrefguide` L247876–L247886).
- `VisualEditor.DataRow` takes **label first, then value** — `public DataRow(String label, Object value)` (`apexrefguide` L247586–L247594).
- `VisualEditor.DesignTimePageContext` is reached by declaring a parameterized constructor (`apexrefguide` L247706). It exposes `entityName` (the API name of the sObject the page is associated with, available only for object pages) and `pageType` (`HomePage`, `AppPage`, `RecordPage`) — L247762–L247765. That is how one datasource class serves a record page scoped to Case *and* one scoped to Account without hardcoding either.
- `containsAllRows` matters at scale: a picklist in a Lightning component can display only the first 200 values, and when `containsAllRows` is `false` a type-ahead search only looks at those first 200 (`apexrefguide` L248021–L248025).
- `isAccessible()` returns true if the current user can see the field (`apexrefguide` L191030–L191031). UNVERIFIED (2026-09-05): neither guide states which user context the design-time datasource executes in; the FLS check here is defensive, not a documented requirement.

---

## 5. `PipelineFieldPickListTest.cls`

```apex
@IsTest
private class PipelineFieldPickListTest {

    private static VisualEditor.DesignTimePageContext contextFor(String entity, String pageType) {
        VisualEditor.DesignTimePageContext ctx = new VisualEditor.DesignTimePageContext();
        ctx.entityName = entity;
        ctx.pageType = pageType;
        return ctx;
    }

    @IsTest
    static void defaultValueIsAmount() {
        PipelineFieldPickList picker =
            new PipelineFieldPickList(contextFor('Opportunity', 'RecordPage'));

        Test.startTest();
        VisualEditor.DataRow row = picker.getDefaultValue();
        Test.stopTest();

        Assert.areEqual('Amount', row.getValue(), 'default value should be Amount');
    }

    @IsTest
    static void returnsNumericFieldsForTheContextObject() {
        PipelineFieldPickList picker =
            new PipelineFieldPickList(contextFor('Opportunity', 'RecordPage'));

        Test.startTest();
        VisualEditor.DynamicPickListRows rows = picker.getValues();
        Test.stopTest();

        Assert.isTrue(rows.size() > 0, 'Opportunity has at least one currency field');
        Assert.isTrue(rows.containsAllRows(), 'type-ahead must search the whole list');

        Set<String> values = new Set<String>();
        for (VisualEditor.DataRow row : rows.getDataRows()) {
            values.add(String.valueOf(row.getValue()));
        }
        Assert.isTrue(values.contains('Amount'), 'Amount is a currency field on Opportunity');
    }

    @IsTest
    static void fallsBackWhenContextHasNoObject() {
        // App Pages and Home Pages are not associated with an object, so entityName is blank.
        PipelineFieldPickList picker = new PipelineFieldPickList(contextFor(null, 'AppPage'));

        Test.startTest();
        VisualEditor.DynamicPickListRows rows = picker.getValues();
        Test.stopTest();

        Assert.isTrue(rows.size() > 0, 'a blank entityName must still produce a usable list');
    }
}
```

`entityName` is available only for object pages, and not all Lightning pages are associated with objects (`apexrefguide` L247762–L247763) — which is exactly the third test.

UNVERIFIED (2026-09-05): the Apex Reference Guide documents `DesignTimePageContext` properties as `public String {get; set;}` (L247774, L247792) but does not document a public no-argument constructor. If `new VisualEditor.DesignTimePageContext()` is not constructible in your org's API version, test `getValues()` through the no-context path and cover the context branch with a small seam (a `@TestVisible` setter for `entityName`).

---

## 6. `__tests__/pipelineSummary.test.js`

```javascript
import { createElement } from 'lwc';
import PipelineSummary from 'c/pipelineSummary';

const ROWS = [
    { id: 'a', label: 'Alpha', amount: 100 },
    { id: 'b', label: 'Bravo', amount: 200 },
    { id: 'c', label: 'Charlie', amount: 300 }
];

function build(props = {}) {
    const element = createElement('c-pipeline-summary', { is: PipelineSummary });
    Object.assign(element, props);
    document.body.appendChild(element);
    return element;
}

describe('c-pipeline-summary', () => {
    afterEach(() => {
        while (document.body.firstChild) {
            document.body.removeChild(document.body.firstChild);
        }
    });

    describe('design-attribute defaults', () => {
        // These pin the JS-side initializers. Jest never reads js-meta.xml, so a
        // change to <default> in the meta file will NOT fail this suite — keep the
        // two in step by hand, and by review.
        it('defaults cardTitle, amountField, maxRows and showTotals', () => {
            const element = build();
            expect(element.cardTitle).toBe('Pipeline Summary');
            expect(element.amountField).toBe('Amount');
            expect(element.maxRows).toBe(10);
            expect(element.showTotals).toBe(true);
        });

        it('renders the default title on the card', () => {
            const element = build();
            const card = element.shadowRoot.querySelector('lightning-card');
            expect(card.title).toBe('Pipeline Summary');
        });
    });

    describe('property setters', () => {
        it('coerces a string maxRows to a number', () => {
            const element = build({ maxRows: '2' });
            expect(element.maxRows).toBe(2);
        });

        it('clamps maxRows to the meta-file max of 50', () => {
            const element = build({ maxRows: 500 });
            expect(element.maxRows).toBe(50);
        });

        it('falls back to 10 for a non-numeric or out-of-range maxRows', () => {
            expect(build({ maxRows: 'lots' }).maxRows).toBe(10);
            expect(build({ maxRows: 0 }).maxRows).toBe(10);
        });

        it('treats the string "true" as boolean true', () => {
            expect(build({ showTotals: 'true' }).showTotals).toBe(true);
            expect(build({ showTotals: 'false' }).showTotals).toBe(false);
        });
    });

    describe('rendering', () => {
        it('shows at most maxRows list items', () => {
            const element = build({ rows: ROWS, maxRows: 2 });
            const items = element.shadowRoot.querySelectorAll('li');
            expect(items.length).toBe(2);
        });

        it('hides the total when showTotals is false', () => {
            const element = build({ rows: ROWS, showTotals: false });
            const bold = element.shadowRoot.querySelector('.slds-text-title_bold');
            expect(bold).toBeNull();
        });

        it('omits the record context line when recordId is not injected', () => {
            // App Page and Home Page placements never receive recordId.
            const element = build({ rows: ROWS });
            expect(element.shadowRoot.querySelector('.slds-text-body_small')).toBeNull();
        });

        it('shows the record context line on a record page placement', () => {
            const element = build({
                rows: ROWS,
                recordId: '500xx0000000001AAA',
                objectApiName: 'Case'
            });
            const line = element.shadowRoot.querySelector('.slds-text-body_small');
            expect(line.textContent).toContain('Case');
        });

        it('applies the region width as a CSS class', () => {
            const element = build({ flexipageRegionWidth: 'SMALL' });
            const wrapper = element.shadowRoot.querySelector('div');
            expect(wrapper.className).toContain('SMALL');
        });
    });
});
```

Structure follows the guide's prescribed shape: import `createElement`, one top-level `describe` named after the component, `afterEach` resetting the shared jsdom instance, and `element.shadowRoot` as the query root (`lwc_guide unit-testing-using-jest-create-tests` L12353–L12379). Tests live in a `__tests__` folder inside the bundle and are excluded from deploys via `.forceignore` (L12328–L12330).

---

## 7. `package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>PipelineFieldPickList</members>
        <members>PipelineFieldPickListTest</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>pipelineSummary</members>
        <name>LightningComponentBundle</name>
    </types>
    <version>63.0</version>
</Package>
```

---

## 8. Deploy Order And Commands

Deploy the Apex class and the bundle **in the same package**. The meta file names `apex://PipelineFieldPickList` and there is no way to declare that dependency, so a bundle-only deploy leaves a design attribute pointing at a class that may not exist.

```bash
# Retrieve what is already there before you edit it
sf project retrieve start \
  --metadata LightningComponentBundle:pipelineSummary \
  --metadata ApexClass:PipelineFieldPickList \
  --target-org my-sandbox

# Static check before you spend a deploy
python3 skills/lwc/lwc-app-builder-config/scripts/check_lwc_app_builder_config.py \
  --manifest-dir force-app/main/default --strict

# Jest, then a validate-only deploy, then the real one
npm run test:unit -- pipelineSummary
sf project deploy start --manifest manifest/package.xml --dry-run --test-level RunSpecifiedTests \
  --tests PipelineFieldPickListTest --target-org my-sandbox
sf project deploy start --manifest manifest/package.xml --test-level RunSpecifiedTests \
  --tests PipelineFieldPickListTest --target-org my-sandbox
```

UNVERIFIED (2026-09-05): neither guide states what App Builder renders when an `apex://` datasource class is absent from the org. Deploying both together avoids finding out.

---

## 9. Verification

Static checks first:

```bash
# 1. The meta file parses and the rules hold
python3 skills/lwc/lwc-app-builder-config/scripts/check_lwc_app_builder_config.py \
  --manifest-dir force-app/main/default

# 2. Confirm the component is registered and exposed
sf data query --target-org my-sandbox \
  --query "SELECT DeveloperName, MasterLabel, Description FROM LightningComponentBundle WHERE DeveloperName = 'pipelineSummary'" \
  --use-tooling-api
```

Then, in the org — one pass per configured surface:

| Where | What to confirm |
|---|---|
| Setup → Lightning Components | The bundle is listed with `masterLabel` as the title and `description` as the summary (L18710, L18714) |
| App Builder → a **Case** record page | The component appears in the palette; the four record-page knobs render; the Amount Field picklist is populated by the Apex class and reflects Case, not Opportunity |
| App Builder → a **Contact** record page | The component does **not** appear — `<objects>` scoping is working |
| App Builder → a record page, phone preview | The component still renders on the `Small` form factor |
| App Builder → an App Page | The title knob is a fixed three-value picklist, not free text |
| App Builder → a Home Page | Only two knobs; the phone preview does not offer the component |
| Experience Builder | The component appears in the Components panel (`lightningCommunity__Page`) and the property panel shows title / show total / accent colour (`lightningCommunity__Default`) |
| Experience Builder, record context | The Record ID property is blank until an admin types `{!recordId}` — Experience Builder does not auto-bind it (L7894, L7900) |

### What App Builder validates — and what it does not

| It does validate | Source |
|---|---|
| `apiVersion` values, when the component is saved to Salesforce | `create-version-components` L809 |
| That an `apiVersion` is present at all, from Spring '25 onward | L796–L798 |
| Destructive changes to a component in use on a Lightning page: removing an `<object>`, removing page-type support, changing `min`/`max`, decreasing form factors | `use-config-for-app-builder-tips` L9904–L9909 |
| Property changes on a component used in a site or managed package: no new `required=true`, no removal, no tightening of `min`/`max` | `use-config-for-community-builder` L8128–L8137 |
| Custom property types on the wrong Experience Cloud target, or a custom-type property that also sets `datasource`/`min`/`max`/`placeholder` — deployment fails | L8162–L8167 |

| It does **not** validate | Consequence | Source |
|---|---|---|
| That the JS type matches the config type | The configuration file's type silently wins | L18972, L9840, L9901 |
| `event` tag metadata against the `.js` file | A Dynamic Interactions event can name a payload the component never fires | `use-config-for-app-builder-dynamic-interactions` L9881 |
| That a `property name` has a matching `@api` field | The knob renders and the value goes nowhere | — (checker rule) |
| That `<objects>` is present on a record-page target | The component is droppable on every UI-API object | L19363 |
| That an `apex://` datasource class exists | UNVERIFIED (2026-09-05): behaviour when the class is absent is not documented | — |
