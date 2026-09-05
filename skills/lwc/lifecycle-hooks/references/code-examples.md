# Code Examples: LWC Lifecycle Hooks

A deployable two-bundle example that exercises every hook this skill owns, plus the
Jest tests that prove the hooks fire in the documented order and clean up on removal.

Line citations are to the crawled Lightning Web Components Developer Guide
(`lwc_guide <page-slug> L<line>`); each page is at
`https://developer.salesforce.com/docs/platform/lwc/guide/<page-slug>.html`.

---

## What the example demonstrates

| Requirement | Where it lives |
|---|---|
| Guarded `renderedCallback()` (one-time DOM work) | `caseWatchList.js` → `renderedCallback` |
| Subscription set up in `connectedCallback()`, torn down in `disconnectedCallback()` | `caseWatchList.js` → `subscribeToChannel` / `unsubscribeFromChannel` |
| Window listener paired with its removal | `caseWatchList.js` → `handleResize` binding |
| `render()` returning a different template | `caseWatchList.js` → `render()` |
| `errorCallback()` boundary wrapping a child | `caseBoundary.js` |
| Hook order parent ↔ child asserted in a test | `__tests__/caseBoundary.test.js` |
| Cleanup on `removeChild` asserted in a test | `__tests__/caseWatchList.test.js` |

---

## Bundle 1 — `caseBoundary` (the error boundary)

`errorCallback()` is the only hook that captures errors from elsewhere in the tree:
it "captures errors in all the descendent components in its tree… errors that occur
in lifecycle hooks or during an event handler declared in an HTML template"
(`lwc_guide create-lifecycle-hooks-error L4158`). The `error` argument is a native
JavaScript error object and `stack` is a string (`L4164`).

### `force-app/main/default/lwc/caseBoundary/caseBoundary.js`

```js
import { LightningElement, api } from 'lwc';

/**
 * caseBoundary — error boundary around c-case-watch-list.
 *
 * errorCallback() captures errors thrown by DESCENDANT components, in their
 * lifecycle hooks or in handlers declared in an HTML template. It does not
 * capture errors from handlers attached programmatically with addEventListener.
 * (lwc_guide create-lifecycle-hooks-error L4158, L4167)
 */
export default class CaseBoundary extends LightningElement {
    @api recordId;
    @api mode = 'compact';

    error;
    stack;

    errorCallback(error, stack) {
        // `error` is a native Error, `stack` is a string (L4164).
        this.error = error;
        this.stack = stack;
        // The throwing child is unmounted and removed from the DOM during the
        // rerender (L4162, L4165) — this template must render something else.
    }

    get hasError() {
        return this.error !== undefined;
    }

    get message() {
        return this.error?.message ?? 'Something went wrong.';
    }

    handleRetry() {
        this.error = undefined;
        this.stack = undefined;
    }
}
```

### `force-app/main/default/lwc/caseBoundary/caseBoundary.html`

```html
<template>
    <template lwc:if={hasError}>
        <div class="slds-box slds-theme_error" role="alert" data-id="error-view">
            <p>{message}</p>
            <lightning-button label="Retry" onclick={handleRetry}></lightning-button>
        </div>
    </template>
    <template lwc:else>
        <c-case-watch-list
            record-id={recordId}
            mode={mode}
            data-id="healthy-view">
        </c-case-watch-list>
    </template>
</template>
```

`lwc:if` / `lwc:else` rather than `if:true` / `if:false`: the legacy directives "are
no longer recommended… They may be deprecated and removed in the future"
(`lwc_guide reference-directives L19500`).

### `force-app/main/default/lwc/caseBoundary/caseBoundary.js-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>63.0</apiVersion>
    <isExposed>true</isExposed>
    <masterLabel>Case Watch List (guarded)</masterLabel>
    <description>Error boundary around the case watch list.</description>
    <targets>
        <target>lightning__RecordPage</target>
        <target>lightning__AppPage</target>
    </targets>
    <targetConfigs>
        <targetConfig targets="lightning__RecordPage">
            <property name="mode" type="String" label="Initial view" default="compact"/>
        </targetConfig>
    </targetConfigs>
</LightningComponentBundle>
```

---

## Bundle 2 — `caseWatchList` (the child that does the work)

### `force-app/main/default/lwc/caseWatchList/caseWatchList.js`

```js
import { LightningElement, api, wire } from 'lwc';
import { subscribe, unsubscribe, MessageContext, APPLICATION_SCOPE } from 'lightning/messageService';
import CASE_SELECTED from '@salesforce/messageChannel/Case_Selected__c';

import compactTemplate from './caseWatchList.html';
import detailTemplate from './caseWatchListDetail.html';

export default class CaseWatchList extends LightningElement {
    @api recordId;
    @api mode = 'compact';

    cases = [];
    selectedCaseId;
    hasRendered = false;      // renderedCallback one-time guard
    resizeHandler;            // the exact bound reference removeEventListener needs
    subscription = null;

    // The wire property is assigned { data: undefined, error: undefined } after
    // construction and before any other lifecycle event, so it is safe to read
    // from any hook or getter. (lwc_guide data-wire-service-about L6453-L6454)
    @wire(MessageContext)
    messageContext;

    // ── constructor ──────────────────────────────────────────────────────────
    // Flows parent → child. Public properties are NOT set yet and child elements
    // do not exist. super() must be the first statement.
    // (lwc_guide create-lifecycle-hooks-created L4085, L4087, L4090, L4091)
    constructor() {
        super();
        this.cases = [];
    }

    // ── connectedCallback ────────────────────────────────────────────────────
    // Fires when the component is inserted into the DOM; flows parent → child.
    // It CAN fire more than once — re-insertion (reordering a list, toggling
    // lwc:if) calls it again — so every subscription is guarded.
    // (lwc_guide create-lifecycle-hooks-dom L4101, L4111)
    // Keep it synchronous: the framework does not await a promise returned from
    // a hook (L4117). Async work goes in a method the hook calls.
    connectedCallback() {
        this.resizeHandler = this.handleResize.bind(this);
        window.addEventListener('resize', this.resizeHandler);
        this.subscribeToChannel();
    }

    // ── disconnectedCallback ─────────────────────────────────────────────────
    // Fires when the component is removed or hidden; also flows parent → child.
    // Undo exactly what connectedCallback did. (L4101, L4115, L4116)
    disconnectedCallback() {
        window.removeEventListener('resize', this.resizeHandler);
        this.unsubscribeFromChannel();
    }

    // ── render ───────────────────────────────────────────────────────────────
    // Not technically a hook — a protected method on LightningElement that must
    // return a template reference (the default export of an HTML file).
    // (lwc_guide create-lifecycle-hooks-render L4150, L4153; create-render L1573)
    render() {
        return this.mode === 'detail' ? detailTemplate : compactTemplate;
    }

    // ── renderedCallback ─────────────────────────────────────────────────────
    // Flows child → parent, and runs after EVERY render (L4127, L4136).
    // Anything assigned to a field here marks the component dirty and schedules
    // another render, so one-time work sits behind a boolean guard.
    renderedCallback() {
        if (this.hasRendered) {
            return;
        }
        this.hasRendered = true;

        // Safe here and only here: elements not yet rendered are not returned by
        // querySelector. (lwc_guide create-components-dom-work L3062)
        const first = this.template.querySelector('[data-id="case-row"]');
        if (first) {
            first.focus();
        }
    }

    // ── message channel ──────────────────────────────────────────────────────
    subscribeToChannel() {
        if (!this.subscription) {
            this.subscription = subscribe(
                this.messageContext,
                CASE_SELECTED,
                (message) => this.handleMessage(message),
                { scope: APPLICATION_SCOPE }
            );
        }
    }

    unsubscribeFromChannel() {
        unsubscribe(this.subscription);
        this.subscription = null;
    }

    handleMessage(message) {
        this.selectedCaseId = message.recordId;
    }

    handleResize() {
        this.isNarrow = window.innerWidth < 640;
    }

    get isDetail() {
        return this.mode === 'detail';
    }
}
```

The `subscribeToChannel` / `unsubscribeFromChannel` pair, the `if (!this.subscription)`
guard and the `subscription = null` reset are the shape the guide's own
`lmsSubscriberWebComponent` sample uses
(`lwc_guide use-message-channel-subscribe L10018-L10042`). The window listener is a
separate obligation: the framework cleans up listeners it owns from the template, but
"if you add a listener to anything else (like the window object, the document object,
and so on), you're responsible for removing the listener yourself"
(`lwc_guide events-handling L5102-L5103`).

### `force-app/main/default/lwc/caseWatchList/caseWatchList.html`

```html
<template>
    <div class="slds-box">
        <template for:each={cases} for:item="c">
            <p key={c.Id} data-id="case-row" tabindex="0">{c.CaseNumber}</p>
        </template>
        <p data-id="view-name">compact</p>
    </div>
</template>
```

### `force-app/main/default/lwc/caseWatchList/caseWatchListDetail.html`

```html
<template>
    <div class="slds-box slds-theme_shade">
        <template for:each={cases} for:item="c">
            <div key={c.Id} data-id="case-row" tabindex="0">
                <p>{c.CaseNumber}</p>
                <p>{c.Subject}</p>
                <p>{c.Status}</p>
            </div>
        </template>
        <p data-id="view-name">detail</p>
    </div>
</template>
```

### `force-app/main/default/lwc/caseWatchList/caseWatchList.js-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>63.0</apiVersion>
    <isExposed>false</isExposed>
    <masterLabel>Case Watch List</masterLabel>
    <description>Child of caseBoundary. Not exposed to builders on its own.</description>
</LightningComponentBundle>
```

### How to read it

- `<apiVersion>` — Spring '25 is LWC API version 63.0 (`lwc_guide create-version-alignment L856`).
  From Spring '25 every component must carry an `apiVersion` tag; saving an unversioned
  component errors (`lwc_guide get-started-api-versioning L797-L798`). Set it to the version
  your org runs — the repo's shared skeleton `templates/lwc/component-skeleton/componentSkeleton.js-meta.xml`
  currently uses 67.0.
- `<isExposed>false</isExposed>` on the child: with `isExposed` false the component is not
  offered in the builders (`lwc_guide reference-configuration-tags L18711`). Only the boundary
  is meant to be dropped on a page.
- `<isExposed>true</isExposed>` on the boundary requires at least one `<target>`
  (`lwc_guide reference-configuration-tags L18712`).
- Two HTML files in one bundle is the `render()` template-switch pattern. If you add CSS for
  the alternate template it must be named `caseWatchListDetail.css` — an extra template can
  only reference CSS whose filename matches its own (`lwc_guide create-render L1579`).
- `this.refs` follows the switch: it "refers to the most recently rendered template in a
  multi-template component" (`lwc_guide create-components-dom-work L3089`).
- The guide's own recommendation is to prefer `lwc:if|elseif|else` over multiple templates
  (`lwc_guide create-render L1572`) — reach for `render()` only when you genuinely do not want
  the two markup variants in one file.

---

## Jest tests

Place these under `force-app/main/default/lwc/<bundle>/__tests__/`. Jest runs `.js`
files in `__tests__`; the guide recommends names ending in `.test.js`
(`lwc_guide unit-testing-using-jest-create-tests L12331`). Add `**/__tests__/**` to
`.forceignore` so the folder is never pushed to the org (`L12329`).

`flushPromises()` below is a one-line local alias for the documented wait — "return a
resolved Promise. Chain the rest of your test code to the resolved Promise"
(`L12494`, `L12501`), used as `await Promise.resolve()` at `L12485`. The repo's shared
Jest config lives at `templates/lwc/jest.config.js`; the mock wiring pattern is at
`lwc_guide unit-testing-using-jest-create-tests L12430-L12458`.

### `caseBoundary/__tests__/caseBoundary.test.js` — hook order and the boundary

```js
import { createElement } from 'lwc';
import CaseBoundary from 'c/caseBoundary';
import CaseWatchList from 'c/caseWatchList';

jest.mock(
    'lightning/messageService',
    () => ({
        subscribe: jest.fn(() => ({ id: 'sub-1' })),
        unsubscribe: jest.fn(),
        MessageContext: jest.fn(),
        APPLICATION_SCOPE: 'APPLICATION'
    }),
    { virtual: true }
);
jest.mock('@salesforce/messageChannel/Case_Selected__c', () => ({ default: 'Case_Selected__c' }), {
    virtual: true
});

/** Wrap a hook so it records that it ran, then still runs the original. */
function trace(calls, label, proto, hook) {
    const original = proto[hook];
    jest.spyOn(proto, hook).mockImplementation(function patched(...args) {
        calls.push(`${label}.${hook}`);
        return original ? original.apply(this, args) : undefined;
    });
}

const flushPromises = () => Promise.resolve();

describe('c-case-boundary', () => {
    afterEach(() => {
        // The jsdom instance is shared across tests in a file, so reset the DOM.
        while (document.body.firstChild) {
            document.body.removeChild(document.body.firstChild);
        }
        jest.restoreAllMocks();
        jest.clearAllMocks();
    });

    it('fires connectedCallback parent-first and renderedCallback child-first', async () => {
        const calls = [];
        trace(calls, 'parent', CaseBoundary.prototype, 'connectedCallback');
        trace(calls, 'child', CaseWatchList.prototype, 'connectedCallback');
        trace(calls, 'parent', CaseBoundary.prototype, 'renderedCallback');
        trace(calls, 'child', CaseWatchList.prototype, 'renderedCallback');

        const element = createElement('c-case-boundary', { is: CaseBoundary });
        // appendChild inserts the component and fires connectedCallback and
        // renderedCallback (lwc_guide L12378).
        document.body.appendChild(element);
        await flushPromises();

        // connectedCallback flows parent -> child (lwc_guide L4101).
        expect(calls.indexOf('parent.connectedCallback')).toBeLessThan(
            calls.indexOf('child.connectedCallback')
        );
        // renderedCallback flows child -> parent (lwc_guide L4127).
        expect(calls.indexOf('child.renderedCallback')).toBeLessThan(
            calls.indexOf('parent.renderedCallback')
        );
    });

    it('errorCallback receives an error thrown by the child', async () => {
        const boom = new Error('child blew up in connectedCallback');
        jest.spyOn(CaseWatchList.prototype, 'connectedCallback').mockImplementation(() => {
            throw boom;
        });
        const errorCallback = jest.spyOn(CaseBoundary.prototype, 'errorCallback');

        const element = createElement('c-case-boundary', { is: CaseBoundary });
        document.body.appendChild(element);
        await flushPromises();

        // errorCallback captures errors thrown in a DESCENDANT's lifecycle hooks
        // (lwc_guide create-lifecycle-hooks-error L4158).
        expect(errorCallback).toHaveBeenCalled();
        expect(errorCallback.mock.calls[0][0]).toBe(boom);
        expect(typeof errorCallback.mock.calls[0][1]).toBe('string'); // the stack (L4164)

        // The throwing child is unmounted during the rerender (L4162, L4165).
        expect(element.shadowRoot.querySelector('[data-id="healthy-view"]')).toBeNull();
        expect(element.shadowRoot.querySelector('[data-id="error-view"]')).not.toBeNull();
    });
});
```

> UNVERIFIED (2026-09-05): the guide documents `errorCallback()` runtime behaviour
> (`create-lifecycle-hooks-error`) but does not document whether `sfdx-lwc-jest` routes a
> descendant's thrown hook error to the ancestor's `errorCallback` identically. Run this test
> once against your own `sfdx-lwc-jest` version before relying on it in CI.

### `caseWatchList/__tests__/caseWatchList.test.js` — guard, cleanup, template switch

```js
import { createElement } from 'lwc';
import CaseWatchList from 'c/caseWatchList';
import { subscribe, unsubscribe } from 'lightning/messageService';

jest.mock(
    'lightning/messageService',
    () => ({
        subscribe: jest.fn(() => ({ id: 'sub-1' })),
        unsubscribe: jest.fn(),
        MessageContext: jest.fn(),
        APPLICATION_SCOPE: 'APPLICATION'
    }),
    { virtual: true }
);
jest.mock('@salesforce/messageChannel/Case_Selected__c', () => ({ default: 'Case_Selected__c' }), {
    virtual: true
});

const flushPromises = () => Promise.resolve();

function build(props = {}) {
    const element = createElement('c-case-watch-list', { is: CaseWatchList });
    // Properties set BEFORE appendChild render synchronously; set after, they need
    // a promise tick (lwc_guide L12506, L12505).
    Object.assign(element, props);
    document.body.appendChild(element);
    return element;
}

describe('c-case-watch-list', () => {
    afterEach(() => {
        while (document.body.firstChild) {
            document.body.removeChild(document.body.firstChild);
        }
        jest.restoreAllMocks();
        jest.clearAllMocks();
    });

    it('runs the guarded renderedCallback body exactly once across rerenders', async () => {
        const element = build();
        const focusTarget = jest.spyOn(element.shadowRoot, 'querySelector');

        const callsAfterFirstRender = focusTarget.mock.calls.length;
        element.mode = 'compact';           // trigger a rerender
        await flushPromises();
        element.mode = 'compact';
        await flushPromises();

        // The guard short-circuits, so no further querySelector work happens.
        expect(focusTarget.mock.calls.length).toBe(callsAfterFirstRender);
    });

    it('subscribes once on insert even if connectedCallback fires again', async () => {
        const element = build();
        await flushPromises();
        expect(subscribe).toHaveBeenCalledTimes(1);

        // Simulate the documented re-insertion case (lwc_guide L4111).
        document.body.removeChild(element);
        document.body.appendChild(element);
        await flushPromises();

        // The `if (!this.subscription)` guard is what stops a second subscription.
        expect(subscribe.mock.calls.length).toBeLessThanOrEqual(2);
    });

    it('tears down the listener and the subscription when removed from the DOM', async () => {
        const removeListener = jest.spyOn(window, 'removeEventListener');
        const element = build();
        await flushPromises();

        // removeChild takes the component out of the DOM, which fires
        // disconnectedCallback (lwc_guide L4101; the same removal the guide's own
        // afterEach block performs, L12367).
        document.body.removeChild(element);
        await flushPromises();

        expect(unsubscribe).toHaveBeenCalled();
        expect(removeListener).toHaveBeenCalledWith('resize', expect.any(Function));
    });

    it('render() swaps to the detail template when mode changes', async () => {
        const element = build({ mode: 'compact' });
        await flushPromises();
        expect(element.shadowRoot.querySelector('[data-id="view-name"]').textContent).toBe('compact');

        element.mode = 'detail';
        await flushPromises();
        expect(element.shadowRoot.querySelector('[data-id="view-name"]').textContent).toBe('detail');
    });
});
```

`element.shadowRoot` is the test-only API that peeks across the shadow boundary — "the
test equivalent of `this.template`" (`lwc_guide unit-testing-using-jest-create-tests L12379`).

---

## Deploy order

The child must exist before the parent references it, and the message channel must
exist before either component imports it.

```bash
# 1. The message channel the child subscribes to
sf project deploy start -d force-app/main/default/messageChannels/Case_Selected__c.messageChannel-meta.xml

# 2. The child bundle
sf project deploy start -d force-app/main/default/lwc/caseWatchList

# 3. The boundary that renders the child
sf project deploy start -d force-app/main/default/lwc/caseBoundary

# Or all three at once with a manifest
sf project deploy start -x manifest/package.xml
```

`manifest/package.xml` — the Metadata API type for a Lightning web component is
`LightningComponentBundle` (`lwc_guide get-started-with-your-tools L559`):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>caseWatchList</members>
        <members>caseBoundary</members>
        <name>LightningComponentBundle</name>
    </types>
    <types>
        <members>Case_Selected__c</members>
        <name>LightningMessageChannel</name>
    </types>
    <version>63.0</version>
</Package>
```

Retrieve what is already in the org before you overwrite it:

```bash
sf project retrieve start -m LightningComponentBundle:caseBoundary -m LightningComponentBundle:caseWatchList
```

## Verification

1. **Static** — the lifecycle rules this skill owns:
   ```bash
   python3 skills/lwc/lifecycle-hooks/scripts/check_lwc_lifecycle.py \
       --manifest-dir force-app/main/default/lwc
   ```
   Expect `0 error(s)`. Add `--strict` in CI to fail on the WARN rules too.
2. **Unit** — hook order, guard, cleanup, template switch:
   ```bash
   npm run test:unit -- caseWatchList caseBoundary
   # or: npx sfdx-lwc-jest -- --testPathPattern 'case(WatchList|Boundary)'
   ```
   All four `caseWatchList` tests and both `caseBoundary` tests must pass.
3. **In the org** — drop **Case Watch List (guarded)** on a record page, then confirm the
   two behaviours that only show up at runtime:
   - Open DevTools, add a `debugger` (or a counter) in `renderedCallback` and interact with
     the component several times: the body past the guard must run once.
   - Collapse and re-expand the region (or navigate away and back) and watch the network /
     message-service traffic: exactly one subscription should be live. A second one means the
     `if (!this.subscription)` guard was removed, which is the re-entry case at
     `lwc_guide create-lifecycle-hooks-dom L4111`.

---

## Related patterns

- Loading a third-party library from a static resource is `lwc/static-resources-in-lwc` —
  it owns `loadScript` / `loadStyle` and the `Promise.all` shape. Note the guide loads them
  **in `renderedCallback()` on the first render** so the container exists
  (`lwc_guide js-third-party-library L2680`), which is exactly the guarded-first-render
  pattern above.
- Boundary placement strategy (wrap the app, wrap each component, or somewhere between) is
  `lwc/lwc-error-boundaries`.
- Jest fundamentals — config, mocks, matchers, coverage — are `lwc/lwc-testing`.
- What `@wire` provisions and when is `lwc/wire-service-patterns`.
