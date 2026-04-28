# Examples — LWC Public API Hardening

Three realistic before/after hardenings of LWC public APIs. Each shows the JS file, the relevant `<targetConfig>` block in `.js-meta.xml`, and the coercion / validation that turns a fragile contract into a defensive one.

---

## Example 1 — `cAccountSummary` with `recordId` and a numeric design attribute

### Before

`accountSummary.js`:

```js
import { api, LightningElement } from 'lwc';
import { getRecord } from 'lightning/uiRecordApi';

export default class AccountSummary extends LightningElement {
    @api recordId;       // declared `number` in JSDoc by a hopeful author
    @api maxContacts = 5; // looks like a number

    connectedCallback() {
        // No validation — if recordId is missing, getRecord throws an opaque error.
        // No coercion — maxContacts may be the string "5" from App Builder.
    }

    get displayLimit() {
        return this.maxContacts + 1; // string concatenation if maxContacts is "5"
    }
}
```

`accountSummary.js-meta.xml`:

```xml
<targetConfigs>
    <targetConfig targets="lightning__RecordPage">
        <property name="maxContacts" label="Max contacts" type="Integer" />
    </targetConfig>
</targetConfigs>
```

Symptoms:
- `displayLimit` returns `"51"` (string concatenation) when admin sets `maxContacts` in App Builder, because the property arrives as a string.
- A unit test that uses `createElement` and never sets `recordId` produces a confusing `getRecord` failure deep in the wire stack.
- No `default` on `maxContacts` — admins who forget to fill it get `undefined` and the component shows `NaN+1`.

### After

`accountSummary.js`:

```js
import { api, LightningElement, wire } from 'lwc';
import { getRecord } from 'lightning/uiRecordApi';

const DEFAULT_MAX_CONTACTS = 5;

/**
 * Account summary card.
 *
 * Public API:
 *   @api recordId         - REQUIRED. 15- or 18-char Salesforce Account Id.
 *   @api maxContacts      - OPTIONAL. Integer 1-50. Default 5.
 *
 * Events emitted:
 *   `summaryloaded` - { detail: { recordId } } once the record fetch resolves.
 */
export default class AccountSummary extends LightningElement {
    @api recordId;

    _maxContacts = DEFAULT_MAX_CONTACTS;
    @api
    get maxContacts() { return this._maxContacts; }
    set maxContacts(value) {
        // App Builder passes "5" (string). Programmatic callers may pass undefined.
        const n = Number(value);
        if (Number.isFinite(n) && n >= 1 && n <= 50) {
            this._maxContacts = n;
        } else {
            this._maxContacts = DEFAULT_MAX_CONTACTS;
        }
    }

    connectedCallback() {
        if (!this.recordId || typeof this.recordId !== 'string') {
            throw new Error('c-account-summary requires a string `record-id` to be set');
        }
    }

    get displayLimit() {
        return this._maxContacts + 1; // arithmetic, not concatenation
    }
}
```

`accountSummary.js-meta.xml`:

```xml
<targetConfigs>
    <targetConfig targets="lightning__RecordPage" objects="Account">
        <property
            name="maxContacts"
            label="Max contacts"
            type="Integer"
            default="5"
            min="1"
            max="50"
            description="Number of contact rows to render. 1-50." />
    </targetConfig>
</targetConfigs>
```

Result: setter coerces App Builder strings, defends against programmatic `undefined`, enforces the 1-50 range. `connectedCallback` fails fast with a useful message. `objects="Account"` constrains the record-page placement so admins don't accidentally drop it on a Contact page.

---

## Example 2 — `cReadyButton` with a misplaced `@api` method

### Before

`readyButton.js`:

```js
import { api, LightningElement } from 'lwc';

export default class ReadyButton extends LightningElement {
    @api label = 'Save';
    _isSaving = false;

    @api
    triggerSave() {
        // Parent calls this when it wants the child to start a save.
        this._isSaving = true;
        this.doSave().then(() => {
            this._isSaving = false;
        });
    }

    async doSave() {
        // ... apex call
    }
}
```

Parent template:

```html
<c-ready-button label="Save now"></c-ready-button>
<lightning-button label="Save from parent" onclick={callChildSave}></lightning-button>
```

```js
callChildSave() {
    this.template.querySelector('c-ready-button').triggerSave();
}
```

Symptoms:
- The parent reaches into the child to imperatively trigger work — coupled and recursion-prone.
- No way to know from outside the child whether it succeeded; parent must rely on side channels.
- `label="Save"` becomes a string from HTML — fine here, but easy to forget the rule when adding more props.

### After — flip the contract; child emits, parent reacts

`readyButton.js`:

```js
import { api, LightningElement } from 'lwc';

/**
 * Save button.
 *
 * Public API:
 *   @api label    - OPTIONAL. Button label. Default 'Save'.
 *   @api disabled - OPTIONAL. Boolean. Default false.
 *
 * Events emitted:
 *   `savestart`   - fired when the user clicks save and the async work begins.
 *   `savesuccess` - fired when the async work resolves. detail: { recordId }.
 *   `savefail`    - fired when the async work rejects. detail: { error }.
 */
export default class ReadyButton extends LightningElement {
    _label = 'Save';
    @api
    get label() { return this._label; }
    set label(v) { this._label = (v == null || v === '') ? 'Save' : String(v); }

    _disabled = false;
    @api
    get disabled() { return this._disabled; }
    set disabled(v) { this._disabled = v === true || v === 'true'; }

    handleClick() {
        this.dispatchEvent(new CustomEvent('savestart'));
        this.doSave()
            .then((recordId) => {
                this.dispatchEvent(new CustomEvent('savesuccess', { detail: { recordId } }));
            })
            .catch((error) => {
                this.dispatchEvent(new CustomEvent('savefail', { detail: { error } }));
            });
    }

    async doSave() {
        // ... apex call
    }
}
```

Parent now listens, doesn't reach in:

```html
<c-ready-button
    label="Save now"
    onsavestart={handleSaveStart}
    onsavesuccess={handleSaveSuccess}
    onsavefail={handleSaveFail}>
</c-ready-button>
```

Result: the child has zero `@api` methods. The contract is one-way and DOM-removal-safe. Boolean `disabled` is correctly coerced from the HTML string `"true"`.

---

## Example 3 — `cTopicPicker` consumed by Flow with `propertyType`

### Before

`topicPicker.js-meta.xml`:

```xml
<targets>
    <target>lightning__FlowScreen</target>
    <target>lightning__RecordPage</target>
</targets>
<targetConfigs>
    <targetConfig targets="lightning__FlowScreen">
        <property name="initialTopic" label="Initial Topic" type="String" />
    </targetConfig>
    <targetConfig targets="lightning__RecordPage">
        <property name="initialTopic" label="Initial Topic" type="String" />
    </targetConfig>
</targetConfigs>
```

`topicPicker.js`:

```js
import { api, LightningElement } from 'lwc';

export default class TopicPicker extends LightningElement {
    @api initialTopic;

    connectedCallback() {
        // Just trusts whatever arrives.
        this._currentTopic = this.initialTopic;
    }
}
```

Symptoms:
- Flow can pass a `Topic__c` SObject record but the design attribute is `String`, so admins must hand-type the Id. Awkward UX.
- No coercion — Flow may pass `null`, App Builder may pass `""`.
- Same property block is duplicated across targets with no per-target defaults.

### After — use `propertyType` for the Flow target only

`topicPicker.js-meta.xml`:

```xml
<targets>
    <target>lightning__FlowScreen</target>
    <target>lightning__RecordPage</target>
</targets>
<targetConfigs>
    <targetConfig targets="lightning__FlowScreen">
        <propertyType name="T" extends="SObject" label="Topic SObject" />
        <property
            name="initialTopic"
            label="Initial Topic"
            type="{T}"
            description="Topic SObject record from a Flow variable." />
    </targetConfig>
    <targetConfig targets="lightning__RecordPage" objects="Topic__c">
        <property
            name="initialTopicId"
            label="Initial Topic Id"
            type="String"
            description="18-char Topic Id (record-page mode falls back to a typed Id)." />
    </targetConfig>
</targetConfigs>
```

`topicPicker.js`:

```js
import { api, LightningElement } from 'lwc';

/**
 * Topic picker that works in Flow (SObject input) and on a Record Page (string Id input).
 *
 * Public API:
 *   @api initialTopic   - Flow target. SObject from a Flow variable. May be null.
 *   @api initialTopicId - Record-page target. 18-char Id. May be null.
 *
 * Events emitted:
 *   `topicchange` - { detail: { topicId } } whenever the user picks a topic.
 */
export default class TopicPicker extends LightningElement {
    _initialTopic;
    @api
    get initialTopic() { return this._initialTopic; }
    set initialTopic(v) {
        // Flow may pass null, undefined, an SObject, or (rarely) a string.
        if (v && typeof v === 'object' && v.Id) {
            this._initialTopic = v;
            this._currentTopicId = v.Id;
        } else {
            this._initialTopic = null;
        }
    }

    _initialTopicId;
    @api
    get initialTopicId() { return this._initialTopicId; }
    set initialTopicId(v) {
        if (typeof v === 'string' && (v.length === 15 || v.length === 18)) {
            this._initialTopicId = v;
            this._currentTopicId = v;
        } else {
            this._initialTopicId = null;
        }
    }

    _currentTopicId;

    connectedCallback() {
        if (!this._currentTopicId) {
            // Soft fallback - Flow halts on uncaught errors; we render a "pick a topic" prompt instead.
            return;
        }
    }

    handlePicked(evt) {
        this._currentTopicId = evt.detail.topicId;
        this.dispatchEvent(new CustomEvent('topicchange', { detail: { topicId: this._currentTopicId } }));
    }
}
```

Result: Flow gets a proper SObject picker; record page gets a typed Id input; the JS file is defensive against every container's input shape; the component renders a soft fallback on Flow rather than throwing.
