# Code Examples — Component Communication

One deployable slice that exercises all three mechanisms in the same feature, so the
choice between them is visible side by side rather than argued in the abstract.

**Scenario.** A `caseTriageBoard` (the owner) renders a list of `casePriorityCard`
children. The child announces a selection **upward** with a `CustomEvent`. The board
passes configuration **downward** with `@api` properties and reaches **into** the child
exactly once, through a public method, to move focus. A `caseContextPanel` that can sit
in a *background* console subtab has no ancestry relationship with either, so it learns
about the selection over a **Lightning Message Channel**.

| Hop | Mechanism | Why not the neighbouring one |
|---|---|---|
| board → card | `@api` properties (`record-id`, `case-number`, `priority`, `compact`) | An event would invert ownership; the board owns the data |
| board → card, "move focus now" | `@api` method `focusCard()` | Focus has no reactive trigger; encoding it as a data flag leaves stale state |
| card → board | `CustomEvent('caseselect')`, `bubbles:false`, `composed:false` | LMS would broadcast a purely local intent to the whole app |
| board → panel in another subtab | `publish()` on `Case_Selected__c` | No shared ancestor exists, so no event path exists |

Canonical building blocks this example builds on, rather than restating:
`templates/lwc/component-skeleton/` (loading/error state, the `error` event convention),
`templates/lwc/jest.config.js` (the `moduleNameMapper` block extended below), and
`templates/lwc/patterns/` for the `@wire`/imperative-Apex shapes that feed `cases`.

---

## How to read it

- **`bubbles` and `composed` both default to `false`.** With that configuration "the only
  way to listen to this event is to add an event listener directly on the component that
  dispatches the event" (`events-propagation`, `lwc_guide.txt` L5169) — which is exactly
  what `<c-case-priority-card oncaseselect={…}>` in the owner's template is. Nothing
  more permissive is needed to reach the owner.
- **`detail` carries only primitives.** The child destructures its own fields into a fresh
  object literal. The guide: "Don't include the non-primitive from `@api` or `@wire` in
  `detail`" (`events-best-practices`, L5272).
- **`compact` is a bare attribute in the parent's markup.** A boolean `@api` property must
  default to `false`, and `compact="false"` would evaluate to **true** (`js-props-boolean`,
  L2492, L2497).
- **`@api` sits on the getter only,** never on both getter and setter
  (`js-props-getters-setters`, L2476).
- **`@wire(MessageContext)` is used on both LMS components.** It is the only form that
  supports subscriber scoping, and it unregisters automatically on destroy
  (`use-message-channel-scope` L9960; `use-message-channel-publish` L9991). It cannot be
  read from `constructor()` (L9993), which is why subscription happens in
  `connectedCallback()`.
- **The panel passes `{ scope: APPLICATION_SCOPE }`; a utility-bar item would not.** The
  active area already includes utility items, which "are always active", but a console
  subtab counts only while it is the *selected* one (`use-message-channel-scope`, L9961).
- **`isExposed` on the channel is `false`.** It controls cross-namespace visibility, and
  once set to `true` it "can't change the value to false at a later time"
  (Metadata API Developer Guide, `api_meta.txt` L84292–84296).
- **`data-case-id`, not `id`.** "Don't pass an `id` to a query method like
  `querySelector`" — rendered ids are rewritten to be globally unique
  (`create-javascript-methods`, L2062).

---

## 1. The message channel

`force-app/main/default/messageChannels/Case_Selected__c.messageChannel-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningMessageChannel xmlns="http://soap.sforce.com/2006/04/metadata">
    <masterLabel>Case Selected</masterLabel>
    <isExposed>false</isExposed>
    <description>Broadcasts the Case that the triage board has selected, so console and utility components can follow it.</description>
    <lightningMessageFields>
        <fieldName>recordId</fieldName>
        <description>Id of the selected Case.</description>
    </lightningMessageFields>
    <lightningMessageFields>
        <fieldName>caseNumber</fieldName>
        <description>CaseNumber of the selected Case, so subscribers can label the UI without a query.</description>
    </lightningMessageFields>
    <lightningMessageFields>
        <fieldName>source</fieldName>
        <description>Developer name of the publishing component, for diagnostics.</description>
    </lightningMessageFields>
</LightningMessageChannel>
```

`masterLabel` is required; `isExposed` defaults to `false`; each `lightningMessageFields`
entry requires `fieldName` (Metadata API Developer Guide, `api_meta.txt` L84321–84328,
L84338; sample definition L84352–84366). The file suffix is `.messageChannel` and it lives
in the `messageChannels` folder (L84300–84301; `use-message-channel-intro`, L9946).

`lightningMessageFields` is **documentation of the payload shape, not enforcement** — the
`publish()` call is a plain JavaScript object. Treat the field list as the contract that
reviewers diff, and keep the publisher and every subscriber in step with it by hand.

---

## 2. `casePriorityCard` — the child

`force-app/main/default/lwc/casePriorityCard/casePriorityCard.js`

```js
import { LightningElement, api } from 'lwc';

const HIGH = 'High';

export default class CasePriorityCard extends LightningElement {
    @api recordId;
    @api caseNumber;
    @api subject;

    // Boolean public property: the default MUST be false. `compact="false"` in
    // markup evaluates to true; only omitting the attribute yields false.
    @api compact = false;

    _priority = 'Medium';
    _badgeClass = 'slds-badge';

    // @api decorates the getter only — never both getter and setter.
    @api
    get priority() {
        return this._priority;
    }
    set priority(value) {
        this._priority = value;
        this._badgeClass =
            value === HIGH ? 'slds-badge slds-theme_error' : 'slds-badge';
    }

    get badgeClass() {
        return this._badgeClass;
    }

    get showSubject() {
        return !this.compact;
    }

    /**
     * The single imperative surface. Focus has no reactive trigger, so it is a
     * public method rather than a data flag the owner has to remember to clear.
     */
    @api
    focusCard() {
        this.refs.card.focus();
    }

    handleSelect() {
        // bubbles:false + composed:false (the defaults) — the owner listens with
        // oncaseselect on <c-case-priority-card> in its own template. detail is a
        // fresh object literal of primitives: nothing the owner mutates can reach
        // back into this component's state.
        this.dispatchEvent(
            new CustomEvent('caseselect', {
                detail: {
                    recordId: this.recordId,
                    caseNumber: this.caseNumber
                }
            })
        );
    }
}
```

`force-app/main/default/lwc/casePriorityCard/casePriorityCard.html`

```html
<template>
    <button
        type="button"
        lwc:ref="card"
        class="slds-box slds-box_x-small slds-text-align_left"
        onclick={handleSelect}
    >
        <span class={badgeClass}>{priority}</span>
        <span class="slds-text-title_bold slds-var-m-left_x-small">{caseNumber}</span>
        <template lwc:if={showSubject}>
            <p class="slds-text-body_small">{subject}</p>
        </template>
    </button>
</template>
```

`force-app/main/default/lwc/casePriorityCard/casePriorityCard.js-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <isExposed>false</isExposed>
</LightningComponentBundle>
```

`isExposed` is `false`: this card is a building block, not something an admin drops on a
page. Every component must carry an `apiVersion` — "Beginning in Spring '25, all
components must specify an API version" (`reference-configuration-tags`, L18700). 67.0 is
the Summer '26 platform version (Metadata API Developer Guide, `api_meta.txt` L2).

---

## 3. `caseTriageBoard` — the owner and publisher

`force-app/main/default/lwc/caseTriageBoard/caseTriageBoard.js`

```js
import { LightningElement, api, wire } from 'lwc';
import { publish, MessageContext } from 'lightning/messageService';
import CASE_SELECTED_CHANNEL from '@salesforce/messageChannel/Case_Selected__c';

export default class CaseTriageBoard extends LightningElement {
    /**
     * An array @api property is the documented exception, not the pattern: the
     * guide recommends slicing complex structures here and handing primitives to
     * descendants, which is what <c-case-priority-card> receives. This array is a
     * read-only proxy — `this.cases[0].Priority = 'High'` throws.
     */
    @api cases = [];

    selectedCaseId;

    // @wire(MessageContext) unregisters on destroy and is the only form that
    // supports subscriber scoping. It cannot be read in constructor().
    @wire(MessageContext)
    messageContext;

    handleCaseSelect(event) {
        // Copy the primitives out of detail into a fresh payload. The message and
        // the child's detail object never share a reference.
        const { recordId, caseNumber } = event.detail;
        this.selectedCaseId = recordId;

        publish(this.messageContext, CASE_SELECTED_CHANNEL, {
            recordId,
            caseNumber,
            source: 'caseTriageBoard'
        });
    }

    /**
     * Public method on the owner so an enclosing component can restore focus after
     * a modal closes. Selects by data-* attribute, never by id.
     */
    @api
    focusCase(caseId) {
        const card = this.template.querySelector(
            `c-case-priority-card[data-case-id="${caseId}"]`
        );
        if (card) {
            card.focusCard();
        }
    }
}
```

`force-app/main/default/lwc/caseTriageBoard/caseTriageBoard.html`

```html
<template>
    <lightning-card title="Case Triage" icon-name="standard:case">
        <div class="slds-var-m-around_small">
            <template for:each={cases} for:item="triageCase">
                <c-case-priority-card
                    key={triageCase.Id}
                    data-case-id={triageCase.Id}
                    record-id={triageCase.Id}
                    case-number={triageCase.CaseNumber}
                    subject={triageCase.Subject}
                    priority={triageCase.Priority}
                    compact
                    oncaseselect={handleCaseSelect}
                >
                </c-case-priority-card>
            </template>
        </div>
    </lightning-card>
</template>
```

Camel-case JavaScript properties map to kebab-case attributes: `recordId` → `record-id`,
`caseNumber` → `case-number` (`js-props-names`, L2337–2339). `compact` is written bare
because that is the only way to pass `true` for a boolean property.

`force-app/main/default/lwc/caseTriageBoard/caseTriageBoard.js-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <isExposed>true</isExposed>
    <masterLabel>Case Triage Board</masterLabel>
    <description>Lists open Cases and publishes the selected Case on Case_Selected__c.</description>
    <targets>
        <target>lightning__AppPage</target>
        <target>lightning__RecordPage</target>
    </targets>
    <targetConfigs>
        <targetConfig targets="lightning__RecordPage">
            <objects>
                <object>Account</object>
            </objects>
        </targetConfig>
    </targetConfigs>
</LightningComponentBundle>
```

`isExposed` `true` **and** at least one `<target>` — either alone leaves the component out
of the builders (`reference-configuration-tags`, L18710–18712). The `targetConfigs` /
`objects` shape is the Metadata API's own sample (`api_meta.txt` L84036–84042).

---

## 4. `caseContextPanel` — the subscriber

`force-app/main/default/lwc/caseContextPanel/caseContextPanel.js`

```js
import { LightningElement, wire } from 'lwc';
import {
    subscribe,
    unsubscribe,
    APPLICATION_SCOPE,
    MessageContext
} from 'lightning/messageService';
import CASE_SELECTED_CHANNEL from '@salesforce/messageChannel/Case_Selected__c';

export default class CaseContextPanel extends LightningElement {
    recordId;
    caseNumber;
    subscription = null;

    @wire(MessageContext)
    messageContext;

    connectedCallback() {
        this.subscribeToChannel();
    }

    disconnectedCallback() {
        this.unsubscribeFromChannel();
    }

    subscribeToChannel() {
        // Guard: connectedCallback can fire more than once as the component is
        // moved in the DOM, and a second subscribe would double-handle messages.
        if (this.subscription) {
            return;
        }
        // APPLICATION_SCOPE because this panel can sit in a console subtab that is
        // not the selected one. Default scope delivers only to the active area.
        this.subscription = subscribe(
            this.messageContext,
            CASE_SELECTED_CHANNEL,
            (message) => this.handleMessage(message),
            { scope: APPLICATION_SCOPE }
        );
    }

    unsubscribeFromChannel() {
        unsubscribe(this.subscription);
        this.subscription = null;
    }

    handleMessage(message) {
        this.recordId = message.recordId;
        this.caseNumber = message.caseNumber;
    }

    get hasCase() {
        return Boolean(this.recordId);
    }
}
```

`force-app/main/default/lwc/caseContextPanel/caseContextPanel.html`

```html
<template>
    <lightning-card title="Selected Case" icon-name="utility:info">
        <div class="slds-var-m-around_small">
            <template lwc:if={hasCase}>
                <p data-id="case-number">{caseNumber}</p>
            </template>
            <template lwc:else>
                <p class="slds-text-color_weak">No Case selected.</p>
            </template>
        </div>
    </lightning-card>
</template>
```

`force-app/main/default/lwc/caseContextPanel/caseContextPanel.js-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <isExposed>true</isExposed>
    <masterLabel>Selected Case Context</masterLabel>
    <description>Follows the Case published on Case_Selected__c from anywhere in the app.</description>
    <targets>
        <target>lightning__RecordPage</target>
        <target>lightning__UtilityBar</target>
    </targets>
</LightningComponentBundle>
```

---

## 5. Jest tests

### 5a. The event contract

`force-app/main/default/lwc/casePriorityCard/__tests__/casePriorityCard.test.js`

```js
import { createElement } from 'lwc';
import CasePriorityCard from 'c/casePriorityCard';

describe('c-case-priority-card', () => {
    afterEach(() => {
        // The jsdom instance is shared across test cases in a file, so reset it.
        while (document.body.firstChild) {
            document.body.removeChild(document.body.firstChild);
        }
        jest.clearAllMocks();
    });

    function build(props = {}) {
        const element = createElement('c-case-priority-card', {
            is: CasePriorityCard
        });
        Object.assign(element, {
            recordId: '500xx0000000001AAA',
            caseNumber: '00001234',
            subject: 'Printer offline',
            priority: 'High',
            ...props
        });
        document.body.appendChild(element);
        return element;
    }

    it('dispatches caseselect carrying only primitives', () => {
        const element = build();
        const handler = jest.fn();
        element.addEventListener('caseselect', handler);

        element.shadowRoot.querySelector('button').click();

        expect(handler).toHaveBeenCalledTimes(1);
        expect(handler.mock.calls[0][0].detail).toEqual({
            recordId: '500xx0000000001AAA',
            caseNumber: '00001234'
        });
    });

    it('keeps the event inside the owner: bubbles and composed stay false', () => {
        const element = build();
        const ownerHandler = jest.fn();
        const documentHandler = jest.fn();
        element.addEventListener('caseselect', ownerHandler);
        document.body.addEventListener('caseselect', documentHandler);

        element.shadowRoot.querySelector('button').click();

        const event = ownerHandler.mock.calls[0][0];
        // Propagation is part of the public API. Assert it so that a later
        // `bubbles: true` cannot land without a failing test.
        expect(event.bubbles).toBe(false);
        expect(event.composed).toBe(false);
        expect(documentHandler).not.toHaveBeenCalled();

        document.body.removeEventListener('caseselect', documentHandler);
    });

    it('treats compact="false" as true, which is why the default is false', () => {
        const omitted = build();
        expect(omitted.shadowRoot.querySelector('p')).not.toBeNull();

        const stringFalse = build({ compact: 'false' });
        expect(stringFalse.shadowRoot.querySelector('p')).toBeNull();
    });

    it('exposes focusCard() as the only imperative surface', () => {
        const element = build();
        const button = element.shadowRoot.querySelector('button');
        const focusSpy = jest.spyOn(button, 'focus');

        element.focusCard();

        expect(focusSpy).toHaveBeenCalledTimes(1);
    });
});
```

### 5b. The message-channel contract

The mock. `force-app/test/jest-mocks/lightning/messageService.js`

```js
import { createTestWireAdapter } from '@salesforce/sfdx-lwc-jest';

// Reproduces the documented lightning/messageService surface: publish, subscribe,
// unsubscribe, APPLICATION_SCOPE, MessageContext, and the API-module pair
// createMessageContext / releaseMessageContext.
export const APPLICATION_SCOPE = 'APPLICATION_SCOPE';
export const MessageContext = createTestWireAdapter(jest.fn());
export const publish = jest.fn();
export const subscribe = jest.fn(() => ({ id: 'test-subscription' }));
export const unsubscribe = jest.fn();
export const createMessageContext = jest.fn(() => ({}));
export const releaseMessageContext = jest.fn();
```

`createTestWireAdapter` is the sfdx-lwc-jest factory for the generic wire adapter, so
`@wire(MessageContext)` resolves during the test.
**UNVERIFIED (2026-09-05):** the guide names the three adapters
(`unit-testing-using-wire-utility`, L12522–L12524) but not the export's identifier; if
your `sfdx-lwc-jest` version disagrees, replace the line with that version's factory.

Wire it up in `jest.config.js`, extending `templates/lwc/jest.config.js`:

```js
const { jestConfig } = require('@salesforce/sfdx-lwc-jest/config');

module.exports = {
    ...jestConfig,
    moduleNameMapper: {
        '^lightning/messageService$':
            '<rootDir>/force-app/test/jest-mocks/lightning/messageService',
        '^lightning/navigation$':
            '<rootDir>/force-app/test/jest-mocks/lightning/navigation'
    },
    testTimeout: 10000
};
```

The `'^lightning/messageService$'` entry is the guide's own recommended mapping
(`unit-testing-using-jest-patterns`, L12444–12445).

`force-app/main/default/lwc/caseContextPanel/__tests__/caseContextPanel.test.js`

```js
import { createElement } from 'lwc';
import CaseContextPanel from 'c/caseContextPanel';
import {
    subscribe,
    unsubscribe,
    APPLICATION_SCOPE
} from 'lightning/messageService';
import CASE_SELECTED_CHANNEL from '@salesforce/messageChannel/Case_Selected__c';

jest.mock(
    '@salesforce/messageChannel/Case_Selected__c',
    () => ({ default: 'Case_Selected__c' }),
    { virtual: true }
);

describe('c-case-context-panel', () => {
    afterEach(() => {
        while (document.body.firstChild) {
            document.body.removeChild(document.body.firstChild);
        }
        jest.clearAllMocks();
    });

    function build() {
        const element = createElement('c-case-context-panel', {
            is: CaseContextPanel
        });
        document.body.appendChild(element);
        return element;
    }

    it('subscribes once on connect, with APPLICATION_SCOPE', () => {
        build();

        expect(subscribe).toHaveBeenCalledTimes(1);
        const [context, channel, listener, options] = subscribe.mock.calls[0];
        expect(context).toBeDefined();
        expect(channel).toBe(CASE_SELECTED_CHANNEL);
        expect(typeof listener).toBe('function');
        expect(options).toEqual({ scope: APPLICATION_SCOPE });
    });

    it('unsubscribes on disconnect so a cached page stops receiving', () => {
        const element = build();
        document.body.removeChild(element);

        expect(unsubscribe).toHaveBeenCalledTimes(1);
        expect(unsubscribe).toHaveBeenCalledWith({ id: 'test-subscription' });
    });

    it('renders the Case published on the channel', () => {
        const element = build();
        const listener = subscribe.mock.calls[0][2];

        listener({
            recordId: '500xx0000000001AAA',
            caseNumber: '00001234',
            source: 'caseTriageBoard'
        });

        return Promise.resolve().then(() => {
            const label = element.shadowRoot.querySelector(
                '[data-id="case-number"]'
            );
            expect(label.textContent).toBe('00001234');
        });
    });
});
```

### 5c. The publish contract

`force-app/main/default/lwc/caseTriageBoard/__tests__/caseTriageBoard.test.js`

```js
import { createElement } from 'lwc';
import CaseTriageBoard from 'c/caseTriageBoard';
import { publish } from 'lightning/messageService';
import CASE_SELECTED_CHANNEL from '@salesforce/messageChannel/Case_Selected__c';

jest.mock(
    '@salesforce/messageChannel/Case_Selected__c',
    () => ({ default: 'Case_Selected__c' }),
    { virtual: true }
);

const CASES = [
    {
        Id: '500xx0000000001AAA',
        CaseNumber: '00001234',
        Subject: 'Printer offline',
        Priority: 'High'
    }
];

describe('c-case-triage-board', () => {
    afterEach(() => {
        while (document.body.firstChild) {
            document.body.removeChild(document.body.firstChild);
        }
        jest.clearAllMocks();
    });

    it('republishes a child selection on the channel, as primitives', () => {
        const element = createElement('c-case-triage-board', {
            is: CaseTriageBoard
        });
        element.cases = CASES;
        document.body.appendChild(element);

        return Promise.resolve().then(() => {
            const card = element.shadowRoot.querySelector(
                'c-case-priority-card'
            );
            card.dispatchEvent(
                new CustomEvent('caseselect', {
                    detail: {
                        recordId: '500xx0000000001AAA',
                        caseNumber: '00001234'
                    }
                })
            );

            expect(publish).toHaveBeenCalledTimes(1);
            const [context, channel, payload] = publish.mock.calls[0];
            expect(context).toBeDefined();
            expect(channel).toBe(CASE_SELECTED_CHANNEL);
            expect(payload).toEqual({
                recordId: '500xx0000000001AAA',
                caseNumber: '00001234',
                source: 'caseTriageBoard'
            });
        });
    });
});
```

The board's own `casePriorityCard` child is a real component here, not a stub, so this test
also proves the `oncaseselect` listener is spelled correctly in the template — the single
most common cause of "the parent never receives it".

The rerender assertion goes inside `Promise.resolve().then(…)` because "component
rerendering upon a property change is asynchronous"
(`unit-testing-using-jest-patterns`, L12589–12592).

Add `**/__tests__/**` to `.forceignore` so the test folder is never pushed to the org
(`unit-testing-using-jest-create-tests`, L12329–12331).

---

## 6. Deploy

`manifest/package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>casePriorityCard</members>
        <members>caseTriageBoard</members>
        <members>caseContextPanel</members>
        <name>LightningComponentBundle</name>
    </types>
    <types>
        <members>Case_Selected__c</members>
        <name>LightningMessageChannel</name>
    </types>
    <version>67.0</version>
</Package>
```

Deploy the channel **in the same request as** the components that import it — a bundle
whose `@salesforce/messageChannel/Case_Selected__c` import cannot resolve fails to save.

```bash
# Run the contract tests before anything reaches an org.
npm run test:unit -- casePriorityCard caseContextPanel

# Static review of the bundles.
python3 skills/lwc/component-communication/scripts/check_component_communication.py \
    --manifest-dir force-app

# Deploy channel + bundles together.
sf project deploy start --manifest manifest/package.xml --target-org myorg

# Or validate first against production.
sf project deploy validate --manifest manifest/package.xml --target-org myprod
```

`sf project deploy start` is the documented way to add a `LightningMessageChannel` to a
scratch org, sandbox, or Developer Edition org (`use-message-channel-intro`, L9951).

### Verify

1. **The channel landed with the payload contract intact.** Round-trip it and diff:

   ```bash
   sf project retrieve start \
       --metadata LightningMessageChannel:Case_Selected__c \
       --target-org myorg
   git diff --exit-code force-app/main/default/messageChannels/
   ```

   A non-empty diff means the org rewrote something you declared — most often a
   `lightningMessageFields` entry that was already present under a different name.

2. **`isExposed` and `targets` actually took.** Open Lightning App Builder on an Account
   record page. `Case Triage Board` and `Selected Case Context` must appear in the
   Components palette and `casePriorityCard` must not. A component missing from the
   palette has `isExposed` `false`, or `true` with no `<target>`
   (`reference-configuration-tags`, L18710–18712).

3. **Scope is doing what you claimed.** In a console app, select a Case on the board, then
   switch to a *different* workspace tab that also hosts `caseContextPanel`. It must show
   the Case. Remove `{ scope: APPLICATION_SCOPE }` and it will not — that is the
   difference the option buys, and the only way to see it is in a console app.

---

## Related reading in this repo

- `lwc/lwc-custom-event-patterns` — everything downstream of "it must be a CustomEvent":
  `cancelable`, retargeting, naming, and why an event is not arriving.
- `lwc/message-channel-patterns` — channel design at scale: payload versioning, multiple
  publishers, Aura and Visualforce subscribers.
- `lwc/lwc-public-api-hardening` — `@api` does not validate types; defensive coercion and
  required-prop checks for the `casePriorityCard` surface.
- `lwc/lwc-testing` — Jest beyond these two contract tests.
- `lwc/lwc-pubsub-patterns` — only when the container does not support LMS.
