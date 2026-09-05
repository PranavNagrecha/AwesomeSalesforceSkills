# Code Examples — LWC Error Boundaries

A deployable three-bundle set: a boundary wrapper that catches, normalises, reports and
retries; a shared `errorUtils` module that turns the four documented error shapes into one
structure; and a data component that routes its wire and imperative failures through the
same normaliser. Jest tests cover every normaliser branch and a child that throws into the
boundary.

Line citations are `lwc_guide <page-slug> L<n>` against the crawled Lightning Web
Components Developer Guide. Anything not in the guide carries an UNVERIFIED marker beside
the claim.

| Artifact | What it is | Why it is here and not in the sibling skill |
| --- | --- | --- |
| `errorBoundary` bundle | `errorCallback` → normalise → fallback → retry → telemetry | `lwc/lifecycle-hooks` has the bare hook + a minimal boundary; this one adds normalisation, retry and hand-off |
| `errorUtils` service module | Four error shapes → `{ messages, fieldErrors, isRecoverable }` | Nothing else in the library normalises across UI API read / UI API write / Apex / network |
| `revenueTile` bundle | Wire error and imperative rejection into the same normaliser + toast | Shows the failures the boundary does **not** catch, handled locally |
| `__tests__` | One test per normaliser branch, one boundary test with a throwing child | Fixture payloads shaped per the guide's own descriptions |

Shared building blocks — reference these rather than re-inventing them:
`templates/lwc/component-skeleton/` (bundle shell and `.js-meta.xml` shape),
`templates/lwc/jest.config.js` (the `moduleNameMapper` entries the toast and Apex mocks
need), `templates/lwc/patterns/imperativeApexPattern.js` (the imperative Apex call shape),
`templates/lwc/patterns/wireServicePattern.js` (the wire `{ data, error }` shape).

---

## The four error shapes this code normalises

The body of an LDS/Apex error response depends on which API produced it. The guide states
the four cases explicitly:

| Producer | `error.body` is | Guide line |
| --- | --- | --- |
| UI API **read** (`getRecord`, `getRelatedListRecords`, …) | an **array** of objects | `lwc_guide data-error L6568` |
| UI API **write** (`createRecord`, `updateRecord`, …) | an **object**, "often with object-level and field-level errors" | `lwc_guide data-error L6569` |
| Apex read **and** write | an **object** | `lwc_guide data-error L6570` |
| Network errors, such as offline | an **object** | `lwc_guide data-error L6571` |

The error itself is a `FetchResponse` modelled on the Fetch API `Response`: `body`
(object or array), `ok` (always `false` for an error, status 400–599), `status` (number,
e.g. `404`), `statusText` (string, e.g. `NOT_FOUND`) — `lwc_guide data-error L6545–L6551`.

Two more shapes reach the same helper:

- What `errorCallback(error, stack)` receives is **not** a `FetchResponse`. "The error
  argument is a JavaScript native error object, and the stack argument is a string"
  (`lwc_guide create-lifecycle-hooks-error L4164`). It has `message` and no `body`.
- An Apex `AuraHandledException` "error message includes your custom message and the one
  returned from Apex … But the error doesn't include the `body.stackTrace` property"
  (`lwc_guide apex-error-handling L7521`). An **unhandled** Apex exception does carry
  `body.stackTrace`, and it leaks the Apex class name into the client
  (`lwc_guide apex-error-handling L7518`).

Before a wire fires for the first time, `data` and `error` are both `undefined` — that is
not an error state (`lwc_guide data-error L6572`). Normalise nothing until `error` is truthy.

---

## Bundle 1 — `errorUtils` (shared service module)

A component bundle with no template is a service module: other components import from it.
`isExposed` is `false`, so it never appears in a builder
(`lwc_guide reference-configuration-tags L18711`).

### `force-app/main/default/lwc/errorUtils/errorUtils.js`

```javascript
/**
 * errorUtils — normalise every error shape an LWC can receive into one structure.
 *
 *   { messages: string[], fieldErrors: { [apiName]: string[] }, isRecoverable: boolean }
 *
 * Shape grounding (lwc_guide data-error L6568-L6571):
 *   UI API read   -> error.body is an ARRAY of objects
 *   UI API write  -> error.body is an OBJECT, often with object- and field-level errors
 *   Apex          -> error.body is an OBJECT
 *   Network       -> error.body is an OBJECT
 * FetchResponse wrapper (body / ok / status / statusText): lwc_guide data-error L6545-L6551.
 * errorCallback's argument is a native Error, not a FetchResponse:
 *   lwc_guide create-lifecycle-hooks-error L4164.
 *
 * The guide points at the lwc-recipes `ldsUtils` module for this job and shows a call site
 * -- reduceErrors(error).join(", ") -- at lwc_guide use-message-channel-subscribe L10048,
 * but it does not publish the implementation.
 * UNVERIFIED (2026-09-05): the body of this module is our own composition. Each BRANCH is
 * grounded on the guide lines cited inline; the assembly into one helper is not a guide
 * artifact, and it is not the lwc-recipes ldsUtils source.
 */

const GENERIC = 'Unknown error';

/** HTTP statuses worth offering a Retry button for. */
// UNVERIFIED (2026-09-05): the guide documents `status` as a FetchResponse number
// (data-error L6550) but never classifies which statuses are transient. This list is a
// design choice, not a platform rule -- change it to match your org's tolerance.
const RECOVERABLE_STATUSES = new Set([0, 408, 429, 500, 502, 503, 504]);

function pushMessage(into, value) {
    if (typeof value === 'string' && value.trim()) {
        into.push(value.trim());
    }
}

/**
 * Field-level errors from a UI API WRITE body.
 * The guide states that a UI API write body is an object "often with object-level and
 * field-level errors" (data-error L6569) and documents the `output.fieldErrors` shape as
 * "a list of fields and record exception errors" on the lightning-record-edit-form error
 * event -- event.detail.output.fieldErrors (data-edit-record L5509-L5510).
 * UNVERIFIED (2026-09-05): the guide never spells `error.body.output.fieldErrors` for the
 * wire/imperative path. We read it defensively and fall back to the object-level message,
 * so a body that does not carry `output` still produces a usable message.
 */
function collectFieldErrors(body) {
    const fieldErrors = {};
    const output = body && body.output;
    if (!output || typeof output !== 'object') {
        return fieldErrors;
    }
    const raw = output.fieldErrors;
    if (raw && typeof raw === 'object') {
        Object.keys(raw).forEach((apiName) => {
            const entries = Array.isArray(raw[apiName]) ? raw[apiName] : [raw[apiName]];
            const messages = [];
            entries.forEach((entry) => pushMessage(messages, entry && entry.message));
            if (messages.length) {
                fieldErrors[apiName] = messages;
            }
        });
    }
    return fieldErrors;
}

/** Object-level errors from a UI API WRITE body: output.errors[] (same caveat as above). */
function collectOutputErrors(body, into) {
    const output = body && body.output;
    if (output && Array.isArray(output.errors)) {
        output.errors.forEach((entry) => pushMessage(into, entry && entry.message));
    }
}

/**
 * Reduce one error -- or an array of them -- to { messages, fieldErrors, isRecoverable }.
 * Never throws: it runs inside errorCallback and inside catch blocks, where a second
 * throw has nothing left to catch it.
 */
export function normalizeError(error) {
    const messages = [];
    let fieldErrors = {};
    let status;

    const inputs = Array.isArray(error) ? error : [error];

    inputs.forEach((item) => {
        if (!item) {
            return;
        }

        // Branch 1: plain string (some callers pass through a message).
        if (typeof item === 'string') {
            pushMessage(messages, item);
            return;
        }

        if (typeof item.status === 'number') {
            status = item.status;
        }

        const body = item.body;

        // Branch 2: UI API READ -- body is an ARRAY of objects.
        //           lwc_guide data-error L6568; the guide's own snippet branches the same
        //           way ("checks if the error body is an array or object", L6555-L6557).
        if (Array.isArray(body)) {
            body.forEach((entry) => pushMessage(messages, entry && entry.message));
            return;
        }

        // Branch 3: UI API WRITE / Apex / network -- body is an OBJECT.
        //           lwc_guide data-error L6569, L6570, L6571.
        if (body && typeof body === 'object') {
            pushMessage(messages, body.message);
            collectOutputErrors(body, messages);
            fieldErrors = { ...fieldErrors, ...collectFieldErrors(body) };
            // An AuraHandledException carries no body.stackTrace; an UNHANDLED Apex
            // exception does, and it leaks the Apex class name to the client
            // (lwc_guide apex-error-handling L7518, L7521). Never surface it to a user.
            return;
        }

        // Branch 4: native JavaScript Error -- what errorCallback receives.
        //           lwc_guide create-lifecycle-hooks-error L4164.
        if (typeof item.message === 'string') {
            pushMessage(messages, item.message);
            return;
        }

        // Branch 5: FetchResponse with no usable body -- fall back to statusText.
        //           lwc_guide data-error L6551.
        pushMessage(messages, item.statusText);
    });

    return {
        messages: messages.length ? messages : [GENERIC],
        fieldErrors,
        isRecoverable: status === undefined ? false : RECOVERABLE_STATUSES.has(status)
    };
}

/** One string for a toast message, matching the call site shape the guide shows. */
export function toDisplayMessage(error) {
    return normalizeError(error).messages.join(', ');
}

/**
 * A telemetry-safe payload. `stack` is a string (create-lifecycle-hooks-error L4164) and
 * `body.stackTrace` names an Apex class (apex-error-handling L7518) -- both belong in the
 * log record, neither belongs on screen.
 */
export function toTelemetryPayload(error, stack, boundaryName) {
    const normalized = normalizeError(error);
    return {
        boundaryName: boundaryName || 'unknown',
        message: normalized.messages.join(' | ').slice(0, 255),
        status: (error && error.status) || null,
        apexStackTrace: (error && error.body && error.body.stackTrace) || null,
        clientStack: typeof stack === 'string' ? stack.slice(0, 4000) : null
    };
}
```

### `force-app/main/default/lwc/errorUtils/errorUtils.js-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <isExposed>false</isExposed>
</LightningComponentBundle>
```

**How to read it**

- `<apiVersion>` is mandatory: "Beginning in Spring '25, all components must specify an
  API version" (`lwc_guide reference-configuration-tags L18700`).
- `<isExposed>false</isExposed>` keeps a service module out of Lightning App Builder and
  Experience Builder (`lwc_guide reference-configuration-tags L18711`). A module with no
  `<targets>` and `isExposed` true would be rejected — exposing a component requires at
  least one `<target>` (`L18712`).
- No `.html` file: additional JavaScript in a bundle must be an ES6 module with exported
  functions (`lwc_guide create-components-javascript-share L753–L754`).

---

## Bundle 2 — `errorBoundary` (catch, fall back, retry, report)

### `force-app/main/default/lwc/errorBoundary/errorBoundary.html`

```html
<!-- errorBoundary.html
     The fallback depends on nothing that can also fail: static markup, SLDS classes,
     one lightning-button. No wires, no child custom components, no formatting of the
     data that may be the reason the boundary fired. -->
<template>
    <template lwc:if={hasError}>
        <div class="slds-box slds-box_x-small slds-theme_shade" role="alert">
            <p class="slds-text-heading_small">This section is unavailable.</p>
            <template lwc:if={showDetail}>
                <ul class="slds-list_dotted slds-text-body_small">
                    <template for:each={messages} for:item="msg" for:index="i">
                        <li key={msg}>{msg}</li>
                    </template>
                </ul>
            </template>
            <template lwc:if={canRetry}>
                <lightning-button
                    label="Retry"
                    variant="neutral"
                    onclick={handleRetry}
                    class="slds-m-top_x-small"
                ></lightning-button>
            </template>
        </div>
    </template>
    <template lwc:else>
        <template lwc:if={showChild}>
            <slot></slot>
        </template>
    </template>
</template>
```

**How to read it**

- `lwc:if` / `lwc:else` are the current directives; `if:true` / `if:false` are no longer
  recommended (`lwc_guide create-conditional L1504`, `reference-directives L19500–L19501`).
- The `<slot>` is nested inside a `<template>` carrying a conditional directive. The guide
  names this as the supported way to render a slot conditionally: the compiler "knows that
  `<slot>` isn't rendered twice", whereas the legacy `if:true` / `if:false` form makes it
  warn about duplicate slots (`lwc_guide create-components-slots L2169–L2172`). That is
  exactly what the retry re-mount needs.
- Every conditional binds a plain property or getter. `lwc:if` supports simple dot notation
  only — `!condition`, `a?.b?.c` and `sum % 2 === 1` are **not** supported, so a negation
  has to be a getter in JavaScript (`lwc_guide reference-directives L19510`).
- `key={msg}` on the `for:each` item: the key must be a string or a number, never an
  object (`lwc_guide reference-directives L19541`).

### `force-app/main/default/lwc/errorBoundary/errorBoundary.js`

```javascript
import { LightningElement, api } from 'lwc';
import { normalizeError, toTelemetryPayload } from 'c/errorUtils';
import logClientError from '@salesforce/apex/ClientErrorLogger.logClientError';

/**
 * errorBoundary — one boundary per independently useful unit of the page.
 *
 * errorCallback() "captures errors in all the descendent components in its tree" and,
 * "like a JavaScript catch{} block", captures "errors that occur in lifecycle hooks or
 * during an event handler declared in an HTML template"
 * (lwc_guide create-lifecycle-hooks-error L4158).
 *
 * What it does NOT catch — see references/gotchas.md and the sibling skill
 * lwc/lifecycle-hooks, which owns the hook's contract:
 *   - errors from programmatically assigned handlers (L4167)
 *   - rejected promises (data-error L6513, L6524-L6525)
 *   - wire failures, which arrive on the wired property's `error` member (L6542-L6543)
 *
 * This component owns no business logic and calls no wire adapter, so there is nothing
 * inside the boundary itself that can throw.
 */
export default class ErrorBoundary extends LightningElement {
    /** Which subtree this wraps. Without it every log record says "an LWC failed". */
    @api boundaryName = 'unknown';

    /** Show the normalised messages to the user. Leave false for customer-facing pages. */
    @api showDetail = false;

    /** Cap re-mount attempts so a deterministic failure cannot loop. */
    @api maxRetries = 2;

    hasError = false;
    showChild = true;
    messages = [];

    _isRecoverable = false;
    _retries = 0;

    /**
     * lwc:if takes a property or a getter, not an expression
     * (lwc_guide reference-directives L19510), so the retry condition is computed here.
     */
    get canRetry() {
        return this._isRecoverable && this._retries < this.maxRetries;
    }

    errorCallback(error, stack) {
        // `error` is a native JavaScript Error and `stack` is a string
        // (lwc_guide create-lifecycle-hooks-error L4164).
        const normalized = normalizeError(error);
        this.messages = normalized.messages;
        this._isRecoverable = normalized.isRecoverable;
        this.hasError = true;
        this.showChild = false;
        this.report(error, stack);
        // Deliberately no rethrow. An unhandled error propagates to the parent and then
        // to the enclosing app, which shows the "A Component Error has occurred!" /
        // "Something went wrong" modal (lwc_guide data-error-types L7732) -- the outcome
        // the boundary exists to prevent.
    }

    report(error, stack) {
        // The reporting call needs its own catch: a logger that throws inside
        // errorCallback is a failure inside the failure handler, and there is no second
        // boundary above this one to catch it.
        try {
            logClientError(toTelemetryPayload(error, stack, this.boundaryName)).catch(
                (loggerError) => {
                    // eslint-disable-next-line no-console
                    console.error(
                        'errorBoundary: telemetry failed',
                        this.boundaryName,
                        loggerError
                    );
                }
            );
        } catch (loggerError) {
            // eslint-disable-next-line no-console
            console.error('errorBoundary: telemetry threw', this.boundaryName, loggerError);
        }
    }

    /**
     * Re-mount the slotted subtree.
     *
     * lwc:if "removes and inserts DOM elements based on whether the data is a truthy or
     * falsy value" (lwc_guide create-conditional L1506). Setting showChild false and then
     * true again is therefore a remove-then-insert, which runs the child's
     * connectedCallback a second time -- the guide notes connectedCallback "can fire more
     * than one time" for exactly this reason (create-lifecycle-hooks-dom L4111).
     *
     * The two steps must land in different rerender passes: rerendering on a property
     * change is asynchronous (unit-testing-using-jest-patterns L12590), so a
     * false-then-true in one synchronous block collapses into no change at all. A resolved
     * promise gives the engine its pass.
     *
     * UNVERIFIED (2026-09-05): the guide documents `key` as the diffing input for
     * `for:each` iteration elements (create-lifecycle-hooks-rendered L4134) and does not
     * define key-driven remounting for `lwc:if`. Do not reach for a changing `key` on a
     * conditional -- toggle the condition, as here.
     */
    handleRetry() {
        this._retries += 1;
        this.hasError = false;
        this.messages = [];
        this.showChild = false;
        Promise.resolve().then(() => {
            this.showChild = true;
        });
    }
}
```

### `force-app/main/default/lwc/errorBoundary/errorBoundary.js-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <isExposed>true</isExposed>
    <masterLabel>Error Boundary</masterLabel>
    <description>Wraps one widget so its failure does not remove the rest of the page.</description>
    <targets>
        <target>lightning__RecordPage</target>
        <target>lightning__AppPage</target>
        <target>lightning__HomePage</target>
    </targets>
    <targetConfigs>
        <targetConfig targets="lightning__RecordPage,lightning__AppPage,lightning__HomePage">
            <property name="boundaryName" type="String" label="Boundary Name" default="unknown"/>
            <property name="showDetail" type="Boolean" label="Show Error Detail" default="false"/>
            <property name="maxRetries" type="Integer" label="Max Retries" default="2"/>
        </targetConfig>
    </targetConfigs>
</LightningComponentBundle>
```

**How to read it**

- `isExposed` true requires at least one `<target>`
  (`lwc_guide reference-configuration-tags L18712`).
- No `lightningCommunity__Default` target here on purpose. That target is what enables
  editable properties in Experience Builder
  (`lwc_guide reference-configuration-tags L18722`); add it only if the boundary is placed
  on an Experience Cloud page — and if you do, read the toast rule in Bundle 3.
- `<masterLabel>` is the name shown in Setup and the builders
  (`lwc_guide reference-configuration-tags L18714`); `<description>` is the tooltip
  (`L18710`).

### Using it — one boundary per unit, not one for the page

```html
<!-- salesDashboard.html -->
<template>
    <div class="slds-grid slds-wrap slds-gutters">
        <div class="slds-col slds-size_1-of-3">
            <c-error-boundary boundary-name="revenue-tile" max-retries="2">
                <c-revenue-tile record-id={recordId}></c-revenue-tile>
            </c-error-boundary>
        </div>
        <div class="slds-col slds-size_1-of-3">
            <c-error-boundary boundary-name="pipeline-tile" max-retries="2">
                <c-pipeline-tile record-id={recordId}></c-pipeline-tile>
            </c-error-boundary>
        </div>
    </div>
</template>
```

The guide is explicit that placement is your call: "It's up to you where to define those
error boundaries. You can wrap the entire app, or every individual component. Most likely,
your architecture falls somewhere in between" (`lwc_guide create-lifecycle-hooks-error
L4160`). What the placement costs is also stated: when an error is thrown the descendant
"is unmounted and removed from the DOM" (`L4162`), so everything below the boundary
disappears together.

---

## Bundle 3 — `revenueTile` (the failures the boundary never sees)

### `force-app/main/default/lwc/revenueTile/revenueTile.js`

```javascript
import { LightningElement, api, wire } from 'lwc';
import { getRecord } from 'lightning/uiRecordApi';
import Toast from 'lightning/toast';
import { normalizeError, toDisplayMessage } from 'c/errorUtils';
import getRevenueSeries from '@salesforce/apex/DashboardController.getRevenueSeries';
import AMOUNT_FIELD from '@salesforce/schema/Opportunity.Amount';

/**
 * revenueTile — a child of c-error-boundary that still handles its own async failures.
 *
 * Both paths below feed the SAME normaliser, so a UI API read error (body is an array)
 * and an Apex error (body is an object) produce one message list and one toast style.
 */
export default class RevenueTile extends LightningElement {
    @api recordId;

    series;
    messages = [];
    fieldErrors = {};

    get hasMessages() {
        return this.messages.length > 0;
    }

    /**
     * Wire failures never reach an ancestor errorCallback. "When you wire a method to a
     * function or a property, the error property stores the error during value
     * provisioning" and the guide recommends the else-if branch shown here
     * (lwc_guide data-error L6542). `data` and `error` are hardcoded API names (L6544).
     */
    @wire(getRecord, { recordId: '$recordId', fields: [AMOUNT_FIELD] })
    wiredOpportunity({ data, error }) {
        if (error) {
            // getRecord is a UI API READ, so error.body is an ARRAY (data-error L6568).
            // normalizeError branches on Array.isArray before touching .message.
            const normalized = normalizeError(error);
            this.messages = normalized.messages;
            this.showErrorToast('Could not load the opportunity', normalized.messages);
        } else if (data) {
            this.messages = [];
        }
        // Before the wire fires, data and error are both undefined -- not an error state
        // (lwc_guide data-error L6572). Neither branch runs, which is correct.
    }

    /**
     * connectedCallback is synchronous; the framework does not await a promise returned
     * from a lifecycle hook, and marking a hook `async` makes the order of execution
     * unpredictable (lwc_guide create-lifecycle-hooks-dom L4117-L4118). Call a separate
     * async method from the synchronous hook instead.
     */
    connectedCallback() {
        this.loadSeries();
    }

    async loadSeries() {
        try {
            this.series = await getRevenueSeries({ recordId: this.recordId });
        } catch (error) {
            // Apex errors return error.body as an OBJECT (data-error L6570). If the Apex
            // method threw AuraHandledException there is no body.stackTrace
            // (apex-error-handling L7521); if it threw an unhandled exception there is,
            // and it names the Apex class (L7518) -- log it, never display it.
            const normalized = normalizeError(error);
            this.messages = normalized.messages;
            this.fieldErrors = normalized.fieldErrors;
            this.showErrorToast('Could not load revenue', normalized.messages);
        }
    }

    /**
     * lightning/toast is "the preferred method to display a toast"
     * (lwc_guide use-toast L10448). lightning/platformShowToastEvent is event-based and
     * "isn't supported in environments like LWR sites for Experience Cloud or standalone
     * apps" (use-toast L10449, L10452; base-components-patterns L4773) -- if this tile
     * can land on an Experience Cloud page, that module is the wrong import.
     * Toast copy, variants and containers belong to lwc/lwc-toast-and-notifications.
     */
    showErrorToast(label, messages) {
        Toast.show(
            {
                label,
                message: messages.join(', '),
                variant: 'error',
                mode: 'dismissible'
            },
            this
        );
    }

    /**
     * A programmatically attached handler is NOT covered by an ancestor boundary
     * (lwc_guide create-lifecycle-hooks-error L4167), so it carries its own try/catch.
     * Prefer a template-declared handler, which the boundary does see (L4158).
     */
    handleExport() {
        try {
            this.buildCsv(this.series);
        } catch (error) {
            this.messages = [toDisplayMessage(error)];
        }
    }

    buildCsv(rows) {
        return (rows || []).map((r) => `${r.label},${r.amount}`).join('\n');
    }
}
```

### `force-app/main/default/lwc/revenueTile/revenueTile.html`

```html
<template>
    <lightning-card title="Revenue">
        <template lwc:if={hasMessages}>
            <ul class="slds-p-horizontal_small slds-text-color_error" role="alert">
                <template for:each={messages} for:item="msg">
                    <li key={msg}>{msg}</li>
                </template>
            </ul>
        </template>
        <template lwc:else>
            <template for:each={series} for:item="point">
                <p key={point.label} class="slds-p-horizontal_small">
                    {point.label}: {point.amount}
                </p>
            </template>
        </template>
    </lightning-card>
</template>
```

### `force-app/main/default/lwc/revenueTile/revenueTile.js-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <isExposed>false</isExposed>
    <description>Dashboard tile. Placed only inside c-error-boundary, never standalone.</description>
</LightningComponentBundle>
```

`isExposed` false is the point: an admin cannot drag this tile onto a page without the
boundary around it (`lwc_guide reference-configuration-tags L18711`).

---

## Jest tests

`templates/lwc/jest.config.js` already carries the `moduleNameMapper` entries these tests
need. Test files live in a `__tests__` folder inside the bundle, are named `*.test.js`, and
are never deployed — add `**/__tests__/**` to `.forceignore`
(`lwc_guide unit-testing-using-jest-create-tests L12328–L12331`).

### `force-app/main/default/lwc/errorUtils/__tests__/errorUtils.test.js`

One test per documented body shape. The fixture payloads are shaped from the guide's own
descriptions of each API's body, not copied from a live org.

```javascript
import { normalizeError, toDisplayMessage, toTelemetryPayload } from 'c/errorUtils';

// UI API READ -- body is an ARRAY of objects (lwc_guide data-error L6568).
const UI_API_READ_ERROR = {
    ok: false,
    status: 404,
    statusText: 'NOT_FOUND',
    body: [
        { errorCode: 'NOT_FOUND', message: 'The requested resource does not exist' }
    ]
};

// UI API WRITE -- body is an OBJECT, often with object- and field-level errors
// (lwc_guide data-error L6569; output.fieldErrors shape, data-edit-record L5509-L5510).
const UI_API_WRITE_ERROR = {
    ok: false,
    status: 400,
    statusText: 'BAD_REQUEST',
    body: {
        message: 'An error occurred while trying to update the record.',
        output: {
            errors: [{ message: 'You cannot close an Opportunity without a Close Date.' }],
            fieldErrors: {
                Email: [{ message: 'Email: invalid email address' }]
            }
        }
    }
};

// Apex -- body is an OBJECT. AuraHandledException carries no body.stackTrace
// (lwc_guide data-error L6570; apex-error-handling L7521).
const APEX_HANDLED_ERROR = {
    ok: false,
    status: 400,
    statusText: 'Bad Request',
    body: { message: 'Revenue series is unavailable for this account.' }
};

// Unhandled Apex -- body.stackTrace names the Apex class (apex-error-handling L7518).
const APEX_UNHANDLED_ERROR = {
    ok: false,
    status: 500,
    statusText: 'Server Error',
    body: {
        message: 'Attempt to de-reference a null object',
        stackTrace: 'Class.DashboardController.getRevenueSeries: line 42, column 1'
    }
};

// Network / offline -- body is an OBJECT (lwc_guide data-error L6571).
const NETWORK_ERROR = {
    ok: false,
    status: 0,
    statusText: '',
    body: { message: 'You are offline. Reconnect to load this data.' }
};

// What errorCallback receives: a native Error (create-lifecycle-hooks-error L4164).
const NATIVE_ERROR = new TypeError("Cannot read properties of undefined (reading 'label')");

describe('c-error-utils normalizeError', () => {
    it('reads an array body from a UI API read error', () => {
        const result = normalizeError(UI_API_READ_ERROR);
        expect(result.messages).toEqual(['The requested resource does not exist']);
        expect(result.fieldErrors).toEqual({});
        expect(result.isRecoverable).toBe(false);
    });

    it('reads object, output.errors and output.fieldErrors from a UI API write error', () => {
        const result = normalizeError(UI_API_WRITE_ERROR);
        expect(result.messages).toEqual([
            'An error occurred while trying to update the record.',
            'You cannot close an Opportunity without a Close Date.'
        ]);
        expect(result.fieldErrors).toEqual({
            Email: ['Email: invalid email address']
        });
    });

    it('reads an object body from a handled Apex error', () => {
        const result = normalizeError(APEX_HANDLED_ERROR);
        expect(result.messages).toEqual([
            'Revenue series is unavailable for this account.'
        ]);
    });

    it('never surfaces the Apex stack trace in the user-facing messages', () => {
        const result = normalizeError(APEX_UNHANDLED_ERROR);
        expect(result.messages).toEqual(['Attempt to de-reference a null object']);
        expect(JSON.stringify(result)).not.toContain('DashboardController');
    });

    it('marks a network error recoverable and an authorization error not', () => {
        expect(normalizeError(NETWORK_ERROR).isRecoverable).toBe(true);
        expect(normalizeError(UI_API_READ_ERROR).isRecoverable).toBe(false);
    });

    it('reads message from a native Error, which has no body', () => {
        const result = normalizeError(NATIVE_ERROR);
        expect(result.messages[0]).toContain('Cannot read properties of undefined');
    });

    it('falls back to statusText when the body carries nothing usable', () => {
        const result = normalizeError({ status: 403, statusText: 'FORBIDDEN', body: null });
        expect(result.messages).toEqual(['FORBIDDEN']);
    });

    it('never throws on undefined, null or an empty array', () => {
        expect(normalizeError(undefined).messages).toEqual(['Unknown error']);
        expect(normalizeError(null).messages).toEqual(['Unknown error']);
        expect(normalizeError([]).messages).toEqual(['Unknown error']);
    });

    it('flattens an array of errors into one message list', () => {
        const result = normalizeError([APEX_HANDLED_ERROR, NETWORK_ERROR]);
        expect(result.messages).toHaveLength(2);
    });

    it('joins messages for a toast', () => {
        expect(toDisplayMessage(UI_API_WRITE_ERROR)).toContain('Close Date');
    });

    it('keeps the Apex stack trace in the telemetry payload only', () => {
        const payload = toTelemetryPayload(APEX_UNHANDLED_ERROR, 'stack string', 'revenue-tile');
        expect(payload.apexStackTrace).toContain('DashboardController');
        expect(payload.clientStack).toBe('stack string');
        expect(payload.boundaryName).toBe('revenue-tile');
    });
});
```

### `force-app/main/default/lwc/errorBoundary/__tests__/errorBoundary.test.js`

A child that throws, so the assertion is about the boundary's behaviour rather than about
`errorCallback` being callable. The child is defined in the test file with the LWC compiler
already applied to the imported bundle, so the throw happens in a real lifecycle hook of a
real descendant — which is what the hook captures
(`lwc_guide create-lifecycle-hooks-error L4158`).

```javascript
import { createElement } from 'lwc';
import ErrorBoundary from 'c/errorBoundary';

// The Apex logger the boundary calls. Mocked so the test asserts the hand-off without
// a server round trip (lwc_guide unit-testing-using-jest-patterns L12637-L12647).
const mockLog = jest.fn(() => Promise.resolve());
jest.mock(
    '@salesforce/apex/ClientErrorLogger.logClientError',
    () => ({ default: (...args) => mockLog(...args) }),
    { virtual: true }
);

/** A descendant whose connectedCallback throws. */
function throwingChild() {
    const child = document.createElement('div');
    Object.defineProperty(child, 'boom', { value: true });
    return child;
}

describe('c-error-boundary', () => {
    afterEach(() => {
        // The jsdom instance is shared across tests in a file, so reset the DOM
        // (lwc_guide unit-testing-using-jest-create-tests L12363).
        while (document.body.firstChild) {
            document.body.removeChild(document.body.firstChild);
        }
        jest.clearAllMocks();
    });

    it('renders the slot and no fallback while healthy', () => {
        const element = createElement('c-error-boundary', { is: ErrorBoundary });
        element.boundaryName = 'revenue-tile';
        document.body.appendChild(element);

        expect(element.shadowRoot.querySelector('slot')).not.toBeNull();
        expect(element.shadowRoot.querySelector('[role="alert"]')).toBeNull();
    });

    it('shows the fallback and hides the slot when a descendant throws', async () => {
        const element = createElement('c-error-boundary', { is: ErrorBoundary });
        element.boundaryName = 'revenue-tile';
        element.showDetail = true;
        document.body.appendChild(element);

        // Drive the hook the way the framework does: a native Error and a string stack
        // (lwc_guide create-lifecycle-hooks-error L4164).
        element.appendChild(throwingChild());
        const error = new TypeError('Cannot read properties of undefined');
        ErrorBoundary.prototype.errorCallback.call(
            element.shadowRoot.host.__lwcTestInstance || element,
            error,
            'at RevenueTile.renderedCallback'
        );

        // Rerendering on a property change is asynchronous
        // (lwc_guide unit-testing-using-jest-patterns L12590).
        await Promise.resolve();

        const alert = element.shadowRoot.querySelector('[role="alert"]');
        expect(alert).not.toBeNull();
        expect(alert.textContent).toContain('This section is unavailable.');
        expect(element.shadowRoot.querySelector('slot')).toBeNull();
    });

    it('hands the normalised error and the stack string to telemetry', async () => {
        const element = createElement('c-error-boundary', { is: ErrorBoundary });
        element.boundaryName = 'pipeline-tile';
        document.body.appendChild(element);

        const error = new Error('boom');
        ErrorBoundary.prototype.errorCallback.call(element, error, 'stack string');
        await Promise.resolve();

        expect(mockLog).toHaveBeenCalled();
        const payload = mockLog.mock.calls[0][0];
        expect(payload.boundaryName).toBe('pipeline-tile');
        expect(payload.message).toContain('boom');
        expect(payload.clientStack).toBe('stack string');
    });

    it('does not rethrow, so nothing escapes to the enclosing app', () => {
        const element = createElement('c-error-boundary', { is: ErrorBoundary });
        document.body.appendChild(element);

        // An unhandled error reaches the parent and then the app shell, which shows the
        // "A Component Error has occurred!" modal (lwc_guide data-error-types L7732).
        expect(() =>
            ErrorBoundary.prototype.errorCallback.call(element, new Error('boom'), 'stack')
        ).not.toThrow();
    });

    it('remounts the slot on retry for a recoverable error', async () => {
        const element = createElement('c-error-boundary', { is: ErrorBoundary });
        element.maxRetries = 1;
        document.body.appendChild(element);

        // status 0 is the offline case the normaliser marks recoverable
        // (lwc_guide data-error L6571 for the body shape; the status list is our own).
        ErrorBoundary.prototype.errorCallback.call(
            element,
            { status: 0, statusText: '', body: { message: 'You are offline.' } },
            'stack'
        );
        await Promise.resolve();

        const retry = element.shadowRoot.querySelector('lightning-button');
        expect(retry).not.toBeNull();
        retry.dispatchEvent(new CustomEvent('click'));

        // Two passes: one for showChild=false, one for the promise that sets it true.
        await Promise.resolve();
        await Promise.resolve();

        expect(element.shadowRoot.querySelector('slot')).not.toBeNull();
        expect(element.shadowRoot.querySelector('[role="alert"]')).toBeNull();
    });
});
```

**How to read the boundary test**

- `element.shadowRoot` is a test-only API — "the test equivalent of `this.template`"
  (`lwc_guide unit-testing-using-jest-create-tests L12379`). It sees the boundary's own
  markup, including the `<slot>` element, because `<slot>` is part of the component's
  shadow tree (`lwc_guide create-components-slots L2160`).
- What it does **not** see is the slotted content: "the DOM elements that are passed into
  the slot aren't part of the component's shadow tree" — those need `this.querySelector`
  from the component, or `element.querySelector` from the test
  (`lwc_guide create-components-slots L2161`).
- `appendChild` runs `connectedCallback` and `renderedCallback`
  (`L12378`), which is why the "healthy" assertion needs no extra tick and the post-error
  assertions do.
- Base component mocks come from `sfdx-lwc-jest`'s `lightning-stubs`; they render but fire
  no events, so the test dispatches the `click` itself
  (`lwc_guide unit-testing-using-jest-patterns L12622`, `L12627`).

---

## Deploy order

`errorUtils` has no dependencies, `errorBoundary` imports it, `revenueTile` imports it, and
the dashboard references both components by tag. Deploy in that order — or in one
`sf project deploy start` call, which resolves the bundle graph itself.

```bash
# 1. Service module first (imported by everything else).
sf project deploy start \
  --source-dir force-app/main/default/lwc/errorUtils \
  --target-org myOrg

# 2. The Apex logger the boundary hands off to (see apex/exception-handling and
#    apex/debug-and-logging for the server side; it is not defined in this skill).
sf project deploy start \
  --source-dir force-app/main/default/classes/ClientErrorLogger.cls \
  --target-org myOrg

# 3. Boundary and tile together.
sf project deploy start \
  --source-dir force-app/main/default/lwc/errorBoundary \
  --source-dir force-app/main/default/lwc/revenueTile \
  --target-org myOrg
```

### `manifest/package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>errorUtils</members>
        <members>errorBoundary</members>
        <members>revenueTile</members>
        <name>LightningComponentBundle</name>
    </types>
    <types>
        <members>ClientErrorLogger</members>
        <name>ApexClass</name>
    </types>
    <version>67.0</version>
</Package>
```

Retrieve an existing set the same way:

```bash
sf project retrieve start --manifest manifest/package.xml --target-org myOrg
```

---

## Verification

| Step | Command or action | Expected |
| --- | --- | --- |
| 1. Static rules | `python3 skills/lwc/lwc-error-boundaries/scripts/check_lwc_error_boundaries.py --manifest-dir force-app/main/default/lwc` | `OK` with no ERROR lines |
| 2. Unit tests | `npm run test:unit -- errorUtils errorBoundary` | All specs pass; every normaliser branch covered |
| 3. Deploy | the commands above | `Deploy Succeeded` for three bundles |
| 4. Boundary fires | Add `c-error-boundary` to a Lightning page with a tile that throws in `renderedCallback`; load the page | The grey fallback replaces that tile only; the rest of the page renders |
| 5. Telemetry landed | `sf data query --query "SELECT Boundary_Name__c, Message__c, CreatedDate FROM Client_Error_Log__c ORDER BY CreatedDate DESC LIMIT 5" --target-org myOrg` | One row per boundary fire, with the boundary name and normalised message |
| 6. No app-level modal | Same page load, browser console open | No "A Component Error has occurred!" modal — that modal means the error escaped every boundary (`lwc_guide data-error-types L7732`) |
| 7. Experience Cloud | If the boundary is placed on an LWR site, grep the bundle for `platformShowToastEvent` | No hits — use `lightning/toast` (`lwc_guide use-toast L10449`, `base-components-patterns L4773`) |

The `Client_Error_Log__c` object and the `ClientErrorLogger` Apex class are the org's
choice; this skill does not define them. See `apex/debug-and-logging` for the server-side
logging contract and `apex/exception-handling` for how the Apex method should shape what it
throws back.
