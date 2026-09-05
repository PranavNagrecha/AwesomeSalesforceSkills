# Code Examples — Navigation and Routing

Deployable bundles for the routing contract this skill describes. Two components:

| Bundle | Role |
|---|---|
| `navHub` | Source component. Navigates to five destination types and renders a `GenerateUrl` anchor. |
| `caseDashboardHost` | URL-addressable target. Reads `c__view` from `CurrentPageReference` and rewrites its own state. |

Both extend `NavigationMixin(LightningElement)`. Start from
[`templates/lwc/component-skeleton/`](../../../../templates/lwc/component-skeleton) for the bundle
shape and [`templates/lwc/jest.config.js`](../../../../templates/lwc/jest.config.js) for the Jest
`moduleNameMapper` — it already maps `^lightning/navigation$` to a local mock.

## How to read it

- **`extends NavigationMixin(LightningElement)` is not optional.** The navigation service adds
  `Navigate` and `GenerateUrl` as methods on the class; importing the symbol without applying the
  mixin leaves nothing to call (`use-navigate-basic`, L10100, L10105–10106).
- **`Navigate(pageReference, [replace])`.** When `replace` is `true` the PageReference replaces the
  current browser-history entry so the user does not press Back twice. Default is `false`
  (`use-navigate-basic`, L10108).
- **`GenerateUrl(pageReference)` returns a promise**, not a string. The resolved URL goes in an
  anchor's `href` or into `window.open({url})` (`use-navigate-basic`, L10103–10104).
- **Every `state` value is a string.** The key-value pairs are serialized to URL query parameters,
  and consuming code parses them back (`use-navigate-add-params-url`, L10140–10141).
- **Custom `state` keys carry a namespace prefix and two underscores** — `c__` outside a managed
  package, the package namespace inside one (`use-navigate-add-params-url`, L10139).
- **`caseDashboardHost` declares `lightning__UrlAddressable`.** That target is what makes
  `standard__component` navigation resolve, and it is supported only in Lightning Experience, the
  Salesforce mobile app, and custom apps such as Lightning console apps — never in Experience
  Builder sites (`targets-lightning-url-addressable`, L19402–19406).

## navHub — the navigating component

### `navHub.js`

```js
import { LightningElement, api } from 'lwc';
import { NavigationMixin } from 'lightning/navigation';

export default class NavHub extends NavigationMixin(LightningElement) {
    @api recordId;
    @api objectApiName;

    recordUrl;

    // --- 1. Record page -------------------------------------------------
    // actionName: clone | edit | view. Experience Builder sites do not
    // support clone or edit. objectApiName is required in LWR sites and
    // optional elsewhere; always sending it is the portable choice.
    get recordPageRef() {
        return {
            type: 'standard__recordPage',
            attributes: {
                recordId: this.recordId,
                objectApiName: this.objectApiName,
                actionName: 'view'
            }
        };
    }

    handleRecord(evt) {
        evt.preventDefault();
        evt.stopPropagation();
        this[NavigationMixin.Navigate](this.recordPageRef);
    }

    // --- 2. Object list view --------------------------------------------
    // actionName for standard__objectPage: home | list | new.
    // filterName is a documented state key (ID or developer name of the
    // list view); it defaults to Recent and is only honoured for list.
    handleListView() {
        this[NavigationMixin.Navigate]({
            type: 'standard__objectPage',
            attributes: {
                objectApiName: 'Case',
                actionName: 'list'
            },
            state: {
                filterName: 'My_Open_Cases'
            }
        });
    }

    // --- 3. Custom tab ---------------------------------------------------
    // apiName is the tab NAME, not its label. A tab created with the label
    // "Case Console" has the api name Case_Console. The target component
    // needs the lightning__Tab target in its own -meta.xml.
    handleCustomTab() {
        this[NavigationMixin.Navigate]({
            type: 'standard__navItemPage',
            attributes: {
                apiName: 'Case_Console'
            }
        });
    }

    // --- 4. External web page --------------------------------------------
    // standard__webPage is for URLs the platform does not own. In an
    // Aura-based Experience Builder site certain Salesforce URLs get
    // site-specific processing (/apex/ becomes /sfdcpage/ and renders in an
    // iframe); use window.open to bypass that, not a rewritten page ref.
    handleExternal() {
        this[NavigationMixin.Navigate]({
            type: 'standard__webPage',
            attributes: {
                url: 'https://status.salesforce.com'
            }
        });
    }

    // --- 5. URL-addressable component with c__ state ----------------------
    // componentName uses the namespace__componentName format and is
    // case-sensitive. The resulting URL is
    // /lightning/cmp/c__caseDashboardHost?c__view=open
    // uid keeps a Lightning console app from opening a duplicate workspace
    // tab for a component that is already open.
    handleDashboard() {
        this[NavigationMixin.Navigate]({
            type: 'standard__component',
            attributes: {
                componentName: 'c__caseDashboardHost'
            },
            state: {
                c__view: 'open',
                c__recordId: this.recordId,
                uid: this.recordId
            }
        });
    }

    // --- GenerateUrl for a real anchor -----------------------------------
    // The promise is what makes this work: the URL is not available on the
    // synchronous return. Resolve it into a tracked field and bind that
    // field into href, so the anchor supports middle-click and copy-link
    // while the click handler still routes through the navigation service.
    connectedCallback() {
        this[NavigationMixin.GenerateUrl](this.recordPageRef)
            .then((url) => {
                this.recordUrl = url;
            })
            .catch(() => {
                // No URL means no anchor; the click handler still navigates.
                this.recordUrl = undefined;
            });
    }
}
```

### `navHub.html`

```html
<template>
    <lightning-card title="Navigate">
        <div class="slds-p-around_medium">
            <!-- href comes from GenerateUrl so copy-link and open-in-new-tab
                 work; onclick routes the in-app case through Navigate. -->
            <a href={recordUrl} onclick={handleRecord}>Open this record</a>

            <lightning-button
                label="Open Cases list"
                onclick={handleListView}
                class="slds-m-left_small">
            </lightning-button>

            <lightning-button
                label="Open Case Console tab"
                onclick={handleCustomTab}
                class="slds-m-left_small">
            </lightning-button>

            <lightning-button
                label="Trust status"
                onclick={handleExternal}
                class="slds-m-left_small">
            </lightning-button>

            <lightning-button
                label="Open dashboard"
                onclick={handleDashboard}
                class="slds-m-left_small">
            </lightning-button>
        </div>
    </lightning-card>
</template>
```

### `navHub.js-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <isExposed>true</isExposed>
    <targets>
        <target>lightning__RecordPage</target>
        <target>lightning__AppPage</target>
    </targets>
    <targetConfigs>
        <targetConfig targets="lightning__RecordPage">
            <objects>
                <object>Case</object>
            </objects>
        </targetConfig>
    </targetConfigs>
</LightningComponentBundle>
```

## caseDashboardHost — the URL-addressable target

### `caseDashboardHost.js`

```js
import { LightningElement, wire } from 'lwc';
import { CurrentPageReference, NavigationMixin } from 'lightning/navigation';

const DEFAULT_VIEW = 'open';

export default class CaseDashboardHost extends NavigationMixin(LightningElement) {
    currentPageReference;
    connected = false;
    generateUrlOnConnected = false;
    escalatedUrl;

    // In Lightning Experience and in Aura- or LWR-template Experience
    // Builder sites the view is NOT rerendered when only the query string
    // changes. Observing CurrentPageReference is what makes the component
    // react to its own deep link.
    @wire(CurrentPageReference)
    setCurrentPageReference(pageRef) {
        this.currentPageReference = pageRef;
        if (this.connected) {
            this.generateUrls();
        } else {
            this.generateUrlOnConnected = true;
        }
    }

    connectedCallback() {
        this.connected = true;
        if (this.generateUrlOnConnected) {
            this.generateUrls();
        }
    }

    // state values arrive as strings; parse them into whatever the
    // component actually needs.
    get view() {
        return this.currentPageReference?.state?.c__view ?? DEFAULT_VIEW;
    }

    get showEscalatedOnly() {
        return this.view === 'escalated';
    }

    // The PageReference handed to you is frozen. To navigate to the same
    // page with different state, copy it and modify the copy. Setting a
    // state property to undefined removes it from the URL.
    getUpdatedPageReference(stateChanges) {
        return Object.assign({}, this.currentPageReference, {
            state: Object.assign({}, this.currentPageReference.state, stateChanges)
        });
    }

    generateUrls() {
        this[NavigationMixin.GenerateUrl](
            this.getUpdatedPageReference({ c__view: 'escalated' })
        ).then((url) => {
            this.escalatedUrl = url;
        });
    }

    // replace = true rewrites the current history entry instead of pushing
    // a new one, so a filter toggle does not force the user to press Back
    // once per toggle.
    handleEscalated(evt) {
        evt.preventDefault();
        evt.stopPropagation();
        this[NavigationMixin.Navigate](
            this.getUpdatedPageReference({ c__view: 'escalated' }),
            true
        );
    }

    handleClearView(evt) {
        evt.preventDefault();
        evt.stopPropagation();
        this[NavigationMixin.Navigate](
            this.getUpdatedPageReference({ c__view: undefined }),
            true
        );
    }
}
```

### `caseDashboardHost.html`

```html
<template>
    <lightning-card title="Case dashboard">
        <div class="slds-p-around_medium">
            <p data-id="view-label">Showing: {view}</p>
            <a href={escalatedUrl} onclick={handleEscalated}>Escalated only</a>
            <a href="#" onclick={handleClearView} class="slds-m-left_small">Clear</a>
        </div>
    </lightning-card>
</template>
```

### `caseDashboardHost.js-meta.xml`

`lightning__UrlAddressable` accepts no `<property>` tags — the component receives its data through
the `state` object of the `standard__component` PageReference. `<isExposed>` must be `true`; the
`<apiVersion>` value has no bearing on this target.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <isExposed>true</isExposed>
    <targets>
        <target>lightning__UrlAddressable</target>
        <target>lightning__AppPage</target>
    </targets>
</LightningComponentBundle>
```

## Jest tests

### The `lightning/navigation` mock

`sfdx-lwc-jest` ships a `lightning/navigation` mock, but you must point Jest at your own copy
through `moduleNameMapper` to get the call-inspection helpers. This is the mock the `lwc-recipes`
navigation components use; save it as `force-app/test/jest-mocks/lightning/navigation.js`.

```js
import { LightningElement } from 'lwc';

export const Navigate = Symbol('Navigate');
export const GenerateUrl = Symbol('GenerateUrl');
const mockNavigate = jest.fn();
const mockGenerate = jest.fn();

export const NavigationMixin = (Base) => {
    return class extends Base {
        [Navigate](pageReference, replace) {
            mockNavigate({ pageReference, replace });
        }
        [GenerateUrl](pageReference) {
            mockGenerate({ pageReference });
            return new Promise((resolve) => resolve('https://www.example.com'));
        }
    };
};
NavigationMixin.Navigate = Navigate;
NavigationMixin.GenerateUrl = GenerateUrl;

export const CurrentPageReference = jest.fn();

/*
 * Tests do not have access to the internals of this mixin used by the
 * component under test so save a reference to the arguments the Navigate method is
 * invoked with and provide access with this function.
 */
export const getNavigateCalledWith = () => {
    if (mockNavigate.mock.calls.length === 0) {
        return { pageReference: undefined, replace: undefined };
    }
    return mockNavigate.mock.lastCall[0];
};

export const getGenerateUrlCalledWith = () => {
    if (mockGenerate.mock.calls.length === 0) {
        return { pageReference: undefined };
    }
    return mockGenerate.mock.lastCall[0];
};
```

The `LightningElement` import above is unused by the mixin itself and can be dropped; the rest is
the guide's mock verbatim.

**UNVERIFIED (2026-09-05):** the guide's mock listing (`unit-testing-using-jest-create-tests`,
L12383–12428) begins mid-file in the extracted text, so the `Symbol('Navigate')` /
`Symbol('GenerateUrl')` declarations and the `jest.fn()` definitions above are reconstructed from
the mock's own usage rather than read directly. `CurrentPageReference` is likewise not shown in the
guide listing; exporting it as a `jest.fn()` is what makes `registerTestWireAdapter`-style emission
work once you override the module. Verify against
`https://github.com/salesforce/sfdx-lwc-jest` before relying on the exact shape.

### `jest.config.js`

Repo canonical: [`templates/lwc/jest.config.js`](../../../../templates/lwc/jest.config.js). The
mapping the navigation tests need:

```js
const { jestConfig } = require('@salesforce/sfdx-lwc-jest/config');

module.exports = {
    ...jestConfig,
    moduleNameMapper: {
        '^lightning/navigation$':
            '<rootDir>/force-app/test/jest-mocks/lightning/navigation'
    },
    testTimeout: 10000
};
```

### `navHub/__tests__/navHub.test.js`

```js
import { createElement } from 'lwc';
import NavHub from 'c/navHub';
import {
    getNavigateCalledWith,
    getGenerateUrlCalledWith
} from 'lightning/navigation';

const RECORD_ID = '500xx0000000001AAA';

describe('c-nav-hub', () => {
    let element;

    beforeEach(() => {
        element = createElement('c-nav-hub', { is: NavHub });
        element.recordId = RECORD_ID;
        element.objectApiName = 'Case';
        document.body.appendChild(element);
    });

    afterEach(() => {
        while (document.body.firstChild) {
            document.body.removeChild(document.body.firstChild);
        }
        jest.clearAllMocks();
    });

    it('generates the record href on connect', () => {
        const { pageReference } = getGenerateUrlCalledWith();
        expect(pageReference.type).toBe('standard__recordPage');
        expect(pageReference.attributes.recordId).toBe(RECORD_ID);

        return Promise.resolve().then(() => {
            const anchor = element.shadowRoot.querySelector('a');
            expect(anchor.href).toContain('https://www.example.com');
        });
    });

    it('navigates to the record page with an explicit actionName', () => {
        element.shadowRoot.querySelector('a').click();

        const { pageReference, replace } = getNavigateCalledWith();
        expect(pageReference).toEqual({
            type: 'standard__recordPage',
            attributes: {
                recordId: RECORD_ID,
                objectApiName: 'Case',
                actionName: 'view'
            }
        });
        // replace defaults to false, so the Back button still works.
        expect(replace).toBeUndefined();
    });

    it('navigates to the object list view, not the record page', () => {
        const buttons = element.shadowRoot.querySelectorAll('lightning-button');
        buttons[0].click();

        const { pageReference } = getNavigateCalledWith();
        expect(pageReference.type).toBe('standard__objectPage');
        expect(pageReference.attributes.actionName).toBe('list');
        expect(pageReference.attributes.recordId).toBeUndefined();
        expect(pageReference.state.filterName).toBe('My_Open_Cases');
    });

    it('navigates to a custom tab by api name', () => {
        const buttons = element.shadowRoot.querySelectorAll('lightning-button');
        buttons[1].click();

        const { pageReference } = getNavigateCalledWith();
        expect(pageReference.type).toBe('standard__navItemPage');
        expect(pageReference.attributes.apiName).toBe('Case_Console');
    });

    it('sends external destinations through standard__webPage', () => {
        const buttons = element.shadowRoot.querySelectorAll('lightning-button');
        buttons[2].click();

        const { pageReference } = getNavigateCalledWith();
        expect(pageReference.type).toBe('standard__webPage');
        expect(pageReference.attributes.url).toBe('https://status.salesforce.com');
    });

    it('namespaces every custom state key on the component page', () => {
        const buttons = element.shadowRoot.querySelectorAll('lightning-button');
        buttons[3].click();

        const { pageReference } = getNavigateCalledWith();
        expect(pageReference.type).toBe('standard__component');
        expect(pageReference.attributes.componentName).toBe('c__caseDashboardHost');

        const customKeys = Object.keys(pageReference.state).filter(
            (key) => key !== 'uid'
        );
        expect(customKeys.length).toBeGreaterThan(0);
        customKeys.forEach((key) => expect(key).toMatch(/^[a-zA-Z0-9]+__/));
        // Values are serialized to query parameters, so they must be strings.
        Object.values(pageReference.state).forEach((value) =>
            expect(typeof value).toBe('string')
        );
    });
});
```

### `caseDashboardHost/__tests__/caseDashboardHost.test.js`

```js
import { createElement } from 'lwc';
import CaseDashboardHost from 'c/caseDashboardHost';
import {
    CurrentPageReference,
    getNavigateCalledWith
} from 'lightning/navigation';
import { registerTestWireAdapter } from '@salesforce/sfdx-lwc-jest';

const pageRefAdapter = registerTestWireAdapter(CurrentPageReference);

describe('c-case-dashboard-host', () => {
    let element;

    beforeEach(() => {
        element = createElement('c-case-dashboard-host', {
            is: CaseDashboardHost
        });
        document.body.appendChild(element);
    });

    afterEach(() => {
        while (document.body.firstChild) {
            document.body.removeChild(document.body.firstChild);
        }
        jest.clearAllMocks();
    });

    it('falls back to the default view when no state is present', () => {
        pageRefAdapter.emit({
            type: 'standard__component',
            attributes: { componentName: 'c__caseDashboardHost' },
            state: {}
        });

        return Promise.resolve().then(() => {
            const label = element.shadowRoot.querySelector('[data-id="view-label"]');
            expect(label.textContent).toBe('Showing: open');
        });
    });

    it('reads c__view out of the page reference state', () => {
        pageRefAdapter.emit({
            type: 'standard__component',
            attributes: { componentName: 'c__caseDashboardHost' },
            state: { c__view: 'escalated' }
        });

        return Promise.resolve().then(() => {
            const label = element.shadowRoot.querySelector('[data-id="view-label"]');
            expect(label.textContent).toBe('Showing: escalated');
        });
    });

    it('replaces the history entry instead of pushing when state changes', () => {
        pageRefAdapter.emit({
            type: 'standard__component',
            attributes: { componentName: 'c__caseDashboardHost' },
            state: { c__view: 'open' }
        });

        return Promise.resolve()
            .then(() => {
                element.shadowRoot.querySelector('a').click();
            })
            .then(() => {
                const { pageReference, replace } = getNavigateCalledWith();
                expect(replace).toBe(true);
                expect(pageReference.state.c__view).toBe('escalated');
            });
    });

    it('removes a state key by setting it to undefined', () => {
        pageRefAdapter.emit({
            type: 'standard__component',
            attributes: { componentName: 'c__caseDashboardHost' },
            state: { c__view: 'escalated' }
        });

        return Promise.resolve()
            .then(() => {
                element.shadowRoot.querySelectorAll('a')[1].click();
            })
            .then(() => {
                const { pageReference } = getNavigateCalledWith();
                expect(pageReference.state.c__view).toBeUndefined();
            });
    });
});
```

**UNVERIFIED (2026-09-05):** `registerTestWireAdapter` and the `emit()` call shape are
`sfdx-lwc-jest` test-utility APIs. The guide states that the utility supplies a generic wire
adapter, an LDS adapter and an Apex adapter (`unit-testing-using-jest-create-tests`, L12519–12525)
but the extracted text does not show the import path or the emit signature. Confirm against your
installed `@salesforce/sfdx-lwc-jest` version — newer releases prefer
`createTestWireAdapter` from `@salesforce/wire-service-jest-util`.

## `package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>navHub</members>
        <members>caseDashboardHost</members>
        <name>LightningComponentBundle</name>
    </types>
    <types>
        <members>Case_Console</members>
        <name>CustomTab</name>
    </types>
    <version>67.0</version>
</Package>
```

`Case_Console` is listed because `standard__navItemPage` resolves against a real `CustomTab` record.
Deploying `navHub` without it produces a button that navigates nowhere.

## Deploy and verify

```bash
# Retrieve the current state of the two bundles before editing
sf project retrieve start --metadata "LightningComponentBundle:navHub" \
                                     "LightningComponentBundle:caseDashboardHost"

# Run the navigation tests locally — no org needed
npm run test:unit -- navHub caseDashboardHost

# Static routing check over the source tree
python3 skills/lwc/navigation-and-routing/scripts/check_navigation_and_routing.py \
    --manifest-dir force-app/main/default/lwc

# Validate against the target org without committing the deploy
sf project deploy start --manifest manifest/package.xml --dry-run

# Deploy
sf project deploy start --manifest manifest/package.xml
```

**Verification step.** After deploying, confirm the custom tab that `standard__navItemPage` targets
actually exists under the api name the code uses — a mismatched tab name is the most common cause
of a `navItemPage` navigation that silently does nothing:

```sql
SELECT DurableId, Label, Type FROM TabDefinition WHERE DurableId = 'Case_Console'
```

Then open `navHub` on a Case record page and check the browser URL after clicking **Open
dashboard**. It must read `/lightning/cmp/c__caseDashboardHost?c__view=open&...`. A URL of
`/lightning/cmp/c__caseDashboardHost` with no query string means the state keys were dropped;
re-check that every custom key carries the `c__` prefix.
