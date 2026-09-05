# Code Examples - LWC Accessibility

A complete, deployable bundle for the one case where a custom control is genuinely
unavoidable: an accessible input wrapper that owns its own label association, error
association, focus contract, and status announcement. Everything else in this skill
pushes you back to `lightning-input`; this file is what "we really do need custom
markup" looks like when it is done correctly.

Canonical shells to start from instead of retyping structure:

- `templates/lwc/component-skeleton/` — bundle shape, loading/error state modelling, `js-meta.xml`.
- `templates/lwc/jest.config.js` — `sfdx-lwc-jest` config with coverage thresholds.
- `templates/lwc/patterns/ldsRecordEditForm.html` — prefer this whenever the field is a real
  record field; a `lightning-record-edit-form` already supplies the accessible label association
  described below (`create-components-accessibility-attributes` L3988).

---

## Design decisions and where they come from

| Decision | Guide statement | Line |
|---|---|---|
| `<label for>` and `<input id>` live in the **same** template | "IDs and ARIA attributes in the same template are linked automatically." | `create-components-accessibility-attributes` L4034 |
| Do **not** split label and input across two components in shadow DOM | "In native shadow DOM, you can't link IDs and ARIA attributes between elements in separate templates." | same page L4035 |
| Consumer-supplied `aria-labelledby` is set with `setAttribute()`, not as a plain property | `for`, `aria-labelledby`, `aria-describedby`, `aria-controls`, `aria-owns`, `aria-details`, `aria-errormessage`, `aria-activedescendant`, `aria-flowto`: "To set and get these attributes, use `setAttribute()` and `getAttribute()`." | `js-props-html-attributes` L2531–2542 |
| `id` is never used as a query selector | "When a template is rendered, `id` values may be transformed into globally unique values. Don't use an `id` selector in CSS or JavaScript… Instead, use the element's `class` attribute or a `data-*` attribute like `data-id`." | `create-components-accessibility-attributes` L4010 |
| Element lookup uses `lwc:ref` / `this.refs` | "Refs locate DOM elements without a selector and only query elements contained in a specified template." | `create-components-dom-work` L3078 |
| `static delegatesFocus = true` instead of hand-rolled focus plumbing | "To manage focus automatically, set `delegatesFocus` to true." / "Adds focus to the native button HTML element using `coolButton.focus()`." | `create-components-focus` L4057, L4062 |
| No `tabindex` anywhere in this bundle | "Don't use `tabindex` with `delegatesFocus` because it throws off the focus order." | `create-components-focus` L4065 |
| Default ARIA is applied in `connectedCallback()`, never `constructor()` | "Define attributes in `connectedCallback()`. Don't define attributes in `constructor()`." | `create-components-accessibility-attributes` L4021 |
| Visually-hidden text uses `slds-assistive-text` | The guide names this class as the mechanism base components use to visually hide a description. | `base-components-accessibility` L4964 |
| `role="status"` + `aria-live="polite"` for the announcement region | **Web standard, not guide-grounded** — WAI-ARIA live-region semantics (`role=status` has an implicit `aria-live="polite"`). The LWC Developer Guide does not document live regions. | — |

---

## 1. `accessibleInputField.html`

```html
<template>
    <div class="slds-form-element" data-id="form-element">
        <!-- for/id pair is in ONE template, so LWC links them automatically. -->
        <label class="slds-form-element__label" for="field-input">
            <abbr lwc:if={required} class="slds-required" title="required">*</abbr>
            {label}
        </label>

        <div class="slds-form-element__control">
            <input
                id="field-input"
                lwc:ref="input"
                class="slds-input"
                type="text"
                value={value}
                required={required}
                aria-describedby={describedByIds}
                aria-invalid={ariaInvalid}
                onchange={handleChange}
                oninput={handleInput}
                onkeydown={handleKeyDown}
            />
        </div>

        <div id="field-help" class="slds-form-element__help" lwc:if={helpText}>
            {helpText}
        </div>

        <!-- Error text is referenced by aria-describedby above, same template. -->
        <div
            id="field-error"
            class="slds-form-element__help slds-text-color_error"
            role="alert"
            lwc:if={errorMessage}
        >
            {errorMessage}
        </div>

        <!-- Polite announcement channel. Always in the DOM so the AT is already
             observing it when the text changes; visually hidden via SLDS. -->
        <div
            class="slds-assistive-text"
            role="status"
            aria-live="polite"
            data-id="status"
        >{statusMessage}</div>
    </div>
</template>
```

**How to read it**

- `for="field-input"` / `id="field-input"` are in the same template, so LWC links them after the
  ids are rewritten (L4034). Nothing in JS ever queries `#field-input`.
- `aria-describedby={describedByIds}` is a computed string of ids **from this same template**. A
  checker rule in `scripts/check_lwc_accessibility.py` fails any `aria-describedby` /
  `aria-labelledby` / `for` whose literal target id is not declared in the same file.
- `role="alert"` on the error and `role="status"` on the announcer are two different channels:
  `alert` is assertive and interrupts, `status` is polite and waits. Using `alert` for routine
  "Saved" text is a real-world annoyance, not a compliance win.
- There is no `tabindex` on any element in the bundle — see `delegatesFocus` in the JS (L4065).
- The `<abbr class="slds-required">` marker is the SLDS blueprint's required indicator; it carries
  a `title`, so the asterisk is not the only signal.

---

## 2. `accessibleInputField.js`

```js
import { LightningElement, api } from 'lwc';

/**
 * c-accessible-input-field
 *
 * A custom text input that keeps its own label, help text, and error text in ONE
 * template so LWC links them automatically after id transformation
 * (create-components-accessibility-attributes L4034).
 *
 * Use this ONLY when lightning-input cannot express the control. lightning-input
 * already associates its label for you (create-components-accessibility-attributes
 * L3988) and follows the WCAG input-assistance guidelines (base-components-accessibility L4958).
 */
export default class AccessibleInputField extends LightningElement {
    // Focus delegation: element.focus() from a parent lands on the <input>,
    // and clicking a non-focusable node inside the shadow root focuses the input
    // (create-components-focus L4057, L4062-L4064).
    static delegatesFocus = true;

    @api label = 'Field';
    @api helpText;
    @api required = false;

    _value = '';
    _ariaLabelledBy;
    errorMessage;
    statusMessage = '';

    @api
    get value() {
        return this._value;
    }
    set value(next) {
        this._value = next ?? '';
    }

    /**
     * aria-labelledby is an id-referencing ARIA attribute. Per
     * js-props-html-attributes L2531-L2542 it must be read and written with
     * getAttribute()/setAttribute() rather than treated as a plain property.
     *
     * Cross-component id references only resolve when both elements share a
     * shadow root (create-components-accessibility-attributes L4035). Consumers
     * in native shadow DOM must place the labelling element in light DOM
     * (create-light-dom L3242) or leave this unset and use `label` instead.
     */
    @api
    get ariaLabelledBy() {
        return this.getAttribute('aria-labelledby');
    }
    set ariaLabelledBy(refIds) {
        this._ariaLabelledBy = refIds;
        if (refIds) {
            this.setAttribute('aria-labelledby', refIds);
        } else {
            this.removeAttribute('aria-labelledby');
        }
    }

    connectedCallback() {
        // Host-element attributes are set here, never in constructor()
        // (create-components-accessibility-attributes L4021,
        //  create-lifecycle-hooks-created L4084).
        if (this._ariaLabelledBy && !this.getAttribute('aria-labelledby')) {
            this.setAttribute('aria-labelledby', this._ariaLabelledBy);
        }
    }

    get ariaInvalid() {
        return this.errorMessage ? 'true' : 'false';
    }

    /** Only ids that exist in THIS template are ever referenced. */
    get describedByIds() {
        const ids = [];
        if (this.helpText) {
            ids.push('field-help');
        }
        if (this.errorMessage) {
            ids.push('field-error');
        }
        return ids.length ? ids.join(' ') : undefined;
    }

    /**
     * Public focus entry point for parents that want an explicit method rather
     * than relying on host focus() delegation.
     */
    @api
    focusInput() {
        this.refs.input?.focus();
    }

    /** Move focus to the field and announce why. Used after a failed save. */
    @api
    reportValidity(message) {
        this.errorMessage = message;
        if (message) {
            this.announce(`${this.label}: ${message}`);
            // Wait one microtask so the error node exists before focusing.
            Promise.resolve().then(() => this.refs.input?.focus());
            return false;
        }
        return true;
    }

    handleInput(event) {
        this._value = event.target.value;
        if (this.errorMessage) {
            this.errorMessage = undefined;
        }
    }

    handleChange(event) {
        this._value = event.target.value;
        this.dispatchEvent(
            new CustomEvent('valuechange', { detail: { value: this._value } })
        );
        this.announce(`${this.label} updated`);
    }

    handleKeyDown(event) {
        // Escape reverts the in-progress edit; Enter commits it. Both are
        // keyboard-only affordances that a mouse user gets from blur/click.
        if (event.key === 'Escape') {
            event.stopPropagation();
            event.target.value = this._value;
            this.announce(`${this.label} reverted`);
        } else if (event.key === 'Enter') {
            this.handleChange(event);
        }
    }

    /**
     * Re-writing identical text into a live region is not reliably re-announced,
     * so blank it first and set it on the next microtask.
     * Live-region behaviour is a WAI-ARIA web standard, not documented in the
     * LWC Developer Guide.
     */
    announce(message) {
        this.statusMessage = '';
        Promise.resolve().then(() => {
            this.statusMessage = message;
        });
    }
}
```

**How to read it**

- `static delegatesFocus = true;` is the whole focus story. A parent writes
  `this.refs.field.focus()` and lands on the `<input>`; without it, focus skips the custom element
  and goes to the elements inside it (`create-components-focus` L4045).
  *The guide states the `delegatesFocus` property in prose (L4057); the code fence showing the exact
  declaration was not captured in the text extraction, so the `static` field syntax here follows the
  same convention the guide uses for `renderMode` (`create-light-dom` L3224).*
- `this.refs.input` requires `lwc:ref="input"` in the template and returns `undefined` if the ref
  does not exist (`create-components-dom-work` L3080) — hence the optional chaining.
- `reportValidity()` deliberately waits a microtask: `errorMessage` has to render before the error
  node can be described or focused.

---

## 3. `accessibleInputField.css`

```css
:host {
    display: block;
}

/*
 * delegatesFocus makes :focus apply to the host as well as the focused element
 * (create-components-focus L4064), so the visible focus ring can live on the host.
 */
:host(:focus) .slds-form-element {
    outline: none;
}

.slds-input:focus {
    /* Never remove the focus indicator without replacing it. */
    box-shadow: 0 0 0 1px var(--slds-g-color-accent-container-2, #0176d3) inset;
}
```

---

## 4. `accessibleInputField.js-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <isExposed>true</isExposed>
    <masterLabel>Accessible Input Field</masterLabel>
    <description>Custom text input with in-template label, help, and error association.</description>
    <targets>
        <target>lightning__RecordPage</target>
        <target>lightning__AppPage</target>
        <target>lightning__HomePage</target>
    </targets>
    <targetConfigs>
        <targetConfig targets="lightning__RecordPage">
            <property name="label" type="String" label="Field Label" default="Field"/>
            <property name="helpText" type="String" label="Help Text"/>
            <property name="required" type="Boolean" label="Required" default="false"/>
        </targetConfig>
    </targetConfigs>
</LightningComponentBundle>
```

**How to read it**

- `apiVersion` is mandatory: versioning custom components is "required" from Spring '25 / API v63.0
  onward (`create-version-components` L796–L797). Set it to your org's current release — "the latest valid
  API version is the current release of Salesforce" (L813) — and to at most that; a future version
  errors on save (`create-version-considerations` L873).
- `isExposed` must be `true` for Lightning App Builder to see the component (`get-started-sfdx-hello-world`
  L374, `use-packaging-add` L7820).
- Regardless of `apiVersion`, the component always uses the latest Lightning base components (L815),
  so pinning an old version does **not** freeze base-component accessibility behaviour.

---

## 5. `__tests__/accessibleInputField.test.js`

```js
import { createElement } from 'lwc';
import AccessibleInputField from 'c/accessibleInputField';

// element.shadowRoot is a test-only API for inspecting the shadow tree
// (unit-testing-using-jest-create-tests L12379).
function flushPromises() {
    return Promise.resolve();
}

function build(props = {}) {
    const element = createElement('c-accessible-input-field', {
        is: AccessibleInputField
    });
    Object.assign(element, props);
    document.body.appendChild(element);
    return element;
}

describe('c-accessible-input-field', () => {
    afterEach(() => {
        // jsdom is shared across tests in a file, so reset the DOM.
        while (document.body.firstChild) {
            document.body.removeChild(document.body.firstChild);
        }
        jest.clearAllMocks();
    });

    it('associates the label with the input via for/id in one template', () => {
        const element = build({ label: 'Account Name' });

        const label = element.shadowRoot.querySelector('label');
        const input = element.shadowRoot.querySelector('input');

        expect(label.textContent).toContain('Account Name');
        // Ids are rewritten at render time, so assert the RELATIONSHIP, never a literal id.
        expect(label.getAttribute('for')).toBe(input.getAttribute('id'));
    });

    it('points aria-describedby at the help text that exists in the template', () => {
        const element = build({ label: 'Amount', helpText: 'Enter a positive number' });

        const input = element.shadowRoot.querySelector('input');
        const help = element.shadowRoot.querySelector('.slds-form-element__help');

        expect(input.getAttribute('aria-describedby')).toContain(help.getAttribute('id'));
        expect(input.getAttribute('aria-invalid')).toBe('false');
    });

    it('marks the field invalid, describes the error, and moves focus to the input', async () => {
        const element = build({ label: 'Amount' });

        element.reportValidity('Enter a positive number');
        await flushPromises();
        await flushPromises();

        const input = element.shadowRoot.querySelector('input');
        const error = element.shadowRoot.querySelector('[role="alert"]');

        expect(error.textContent).toContain('Enter a positive number');
        expect(input.getAttribute('aria-invalid')).toBe('true');
        expect(input.getAttribute('aria-describedby')).toContain(error.getAttribute('id'));
        expect(element.shadowRoot.activeElement).toBe(input);
    });

    it('announces the change in the polite live region', async () => {
        const element = build({ label: 'Amount' });

        const input = element.shadowRoot.querySelector('input');
        input.value = '42';
        input.dispatchEvent(new CustomEvent('change'));
        await flushPromises();
        await flushPromises();

        const status = element.shadowRoot.querySelector('[data-id="status"]');
        expect(status.getAttribute('role')).toBe('status');
        expect(status.getAttribute('aria-live')).toBe('polite');
        expect(status.textContent).toBe('Amount updated');
    });

    it('reflects a consumer aria-labelledby onto the host element', () => {
        const element = build({ label: 'Amount', ariaLabelledBy: 'external-heading' });

        // Set via setAttribute in the setter, so it is visible on the host.
        expect(element.getAttribute('aria-labelledby')).toBe('external-heading');
    });

    it('delegates host focus() to the inner input', () => {
        const element = build({ label: 'Amount' });

        element.focus();

        const input = element.shadowRoot.querySelector('input');
        expect(element.shadowRoot.activeElement).toBe(input);
    });

    it('reverts the in-progress edit on Escape without leaving the field', async () => {
        const element = build({ label: 'Amount', value: '10' });

        const input = element.shadowRoot.querySelector('input');
        input.value = '999';
        input.dispatchEvent(
            new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })
        );
        await flushPromises();

        expect(input.value).toBe('10');
    });

    it('uses no tabindex anywhere, because delegatesFocus owns focus order', () => {
        const element = build({ label: 'Amount', helpText: 'help' });

        const withTabIndex = element.shadowRoot.querySelectorAll('[tabindex]');
        expect(withTabIndex.length).toBe(0);
    });
});
```

**How to read it**

- The `for`/`id` assertion compares the two rendered values instead of hard-coding `field-input`,
  because template ids "may be transformed into globally unique values" (L4010). A test that asserts
  the literal id passes today and breaks silently later.
- `element.shadowRoot.activeElement` is the focus assertion that works in jsdom; `document.activeElement`
  returns the host element, not the inner input, once focus is delegated.
- The last test is the regression guard for L4065 ("Don't use `tabindex` with `delegatesFocus`").

Run them with the repo's `sfdx-lwc-jest` config:

```bash
npm run test:unit -- accessibleInputField
# or, against a single file
npx sfdx-lwc-jest -- force-app/main/default/lwc/accessibleInputField
```

---

## 6. Parent usage — focus after a failed save

```html
<template>
    <c-accessible-input-field
        lwc:ref="amount"
        label="Amount"
        help-text="Enter a positive number"
        required
        onvaluechange={handleAmountChange}
    ></c-accessible-input-field>

    <lightning-button label="Save" variant="brand" onclick={handleSave}></lightning-button>
</template>
```

```js
import { LightningElement } from 'lwc';

export default class QuoteEditor extends LightningElement {
    amount;

    handleAmountChange(event) {
        this.amount = event.detail.value;
    }

    handleSave() {
        if (!(Number(this.amount) > 0)) {
            // The child owns error text, aria-invalid, the announcement, and focus.
            this.refs.amount.reportValidity('Enter a positive number');
            return;
        }
        this.refs.amount.reportValidity(null);
        // ... persist
    }
}
```

**How to read it** — the parent never reaches into the child's shadow tree. `document.querySelector`
cannot select nodes in a component's shadow tree at all (`create-dom` L3124), and the parent's own
`this.template.querySelector` stops at the child's boundary. Every cross-boundary interaction goes
through the child's `@api` surface.

---

## 7. `package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>accessibleInputField</members>
        <name>LightningComponentBundle</name>
    </types>
    <version>67.0</version>
</Package>
```

---

## 8. Deploy and verify

```bash
# Retrieve the current bundle before you change it
sf project retrieve start --metadata LightningComponentBundle:accessibleInputField --target-org myOrg

# Run the accessibility checker over the source tree BEFORE deploying
python3 skills/lwc/lwc-accessibility/scripts/check_lwc_accessibility.py \
    --manifest-dir force-app/main/default/lwc

# Jest must pass locally; Jest tests never deploy (they are .forceignore'd)
npm run test:unit

# Validate-only deploy, then deploy
sf project deploy start --manifest package.xml --target-org myOrg --dry-run
sf project deploy start --manifest package.xml --target-org myOrg
```

**Verification step** — after deploy, confirm the bundle is the version you shipped and is exposed:

```soql
SELECT Id, DeveloperName, ApiVersion, Description
FROM LightningComponentBundle
WHERE DeveloperName = 'accessibleInputField'
```

Then do the check no query can do, on the real page:

1. Tab to the field. Focus must land on the `<input>`, not on the custom element wrapper.
2. With a screen reader running, confirm the label, then the help text, are read on focus.
3. Trigger the validation error. Confirm the error text is announced and focus returns to the input.
4. Press `Tab` through the whole component. Nothing should receive focus twice, and nothing should
   be reachable that has no visible focus indicator.
