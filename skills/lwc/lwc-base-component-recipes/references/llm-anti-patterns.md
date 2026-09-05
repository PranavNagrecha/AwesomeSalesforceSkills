# LLM Anti-Patterns — LWC Base Component Recipes

Common mistakes AI coding assistants make when generating or advising on lightning-record-form, lightning-record-edit-form, lightning-record-view-form, and lightning-datatable.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using lightning-record-edit-form when lightning-record-form would suffice

**What the LLM generates:**

```html
<lightning-record-edit-form record-id={recordId} object-api-name="Account">
    <lightning-input-field field-name="Name"></lightning-input-field>
    <lightning-input-field field-name="Phone"></lightning-input-field>
    <lightning-button type="submit" label="Save"></lightning-button>
</lightning-record-edit-form>
```

**Why it happens:** LLMs default to `lightning-record-edit-form` because it appears in more training examples. For simple view/edit with standard layout and no custom submit logic, `lightning-record-form` with `mode="edit"` handles both modes with less markup.

**Correct pattern:**

```html
<lightning-record-form
    record-id={recordId}
    object-api-name="Account"
    fields={fields}
    mode="edit">
</lightning-record-form>
```

Use `lightning-record-edit-form` only when you need custom layout, custom buttons, or field-level validation control.

**Detection hint:** `lightning-record-edit-form` with only `lightning-input-field` children and a standard submit button, no custom handlers.

---

## Anti-Pattern 2: Hardcoding field API names as strings instead of importing them

**What the LLM generates:**

```javascript
fields = ['Name', 'Phone', 'Industry'];
```

**Why it happens:** String literals are simpler and appear in quick-start guides. LLMs prefer brevity over the import-based approach that provides compile-time validation and namespace awareness.

**Correct pattern:**

```javascript
import NAME_FIELD from '@salesforce/schema/Account.Name';
import PHONE_FIELD from '@salesforce/schema/Account.Phone';
import INDUSTRY_FIELD from '@salesforce/schema/Account.Industry';

fields = [NAME_FIELD, PHONE_FIELD, INDUSTRY_FIELD];
```

**Detection hint:** `fields` array or `field-name` attribute containing bare string literals instead of imported schema references.

---

## Anti-Pattern 3: Using lightning-record-view-form without lightning-output-field children

**What the LLM generates:**

```html
<lightning-record-view-form record-id={recordId} object-api-name="Account">
    <div class="slds-grid">
        <p>{record.fields.Name.value}</p>
    </div>
</lightning-record-view-form>
```

**Why it happens:** LLMs wrap manual field rendering inside `lightning-record-view-form` without understanding that the component provides its value through `lightning-output-field` children, not through JavaScript record references.

**Correct pattern:**

```html
<lightning-record-view-form record-id={recordId} object-api-name="Account">
    <div class="slds-grid">
        <lightning-output-field field-name="Name"></lightning-output-field>
    </div>
</lightning-record-view-form>
```

**Detection hint:** `lightning-record-view-form` that contains no `lightning-output-field` elements.

---

## Anti-Pattern 4: Not handling the onsuccess event to show user feedback after save

**What the LLM generates:**

```html
<lightning-record-edit-form record-id={recordId} object-api-name="Account">
    <lightning-input-field field-name="Name"></lightning-input-field>
    <lightning-button type="submit" label="Save"></lightning-button>
</lightning-record-edit-form>
<!-- No onsuccess, onerror, or onsubmit handlers -->
```

**Why it happens:** The form submits and saves without explicit handlers, so LLMs treat them as optional. Users get no visual confirmation of success or failure.

**Correct pattern:**

```html
<lightning-record-edit-form
    record-id={recordId}
    object-api-name="Account"
    onsuccess={handleSuccess}
    onerror={handleError}>
    <lightning-input-field field-name="Name"></lightning-input-field>
    <lightning-button type="submit" label="Save"></lightning-button>
</lightning-record-edit-form>
```

```javascript
handleSuccess() {
    this.dispatchEvent(new ShowToastEvent({
        title: 'Success', message: 'Record saved.', variant: 'success'
    }));
}
```

**Detection hint:** `lightning-record-edit-form` without `onsuccess` or `onerror` attributes.

---

## Anti-Pattern 5: Using lightning-datatable without a stable key-field

**What the LLM generates:**

```html
<lightning-datatable
    data={records}
    columns={columns}
    key-field="index">
</lightning-datatable>
```

**Why it happens:** LLMs sometimes use array index or a non-unique field as the key. This causes row identity issues with selection, inline editing, and sorting.

**Correct pattern:**

```html
<lightning-datatable
    data={records}
    columns={columns}
    key-field="Id">
</lightning-datatable>
```

Always use a stable, unique identifier like the Salesforce `Id` field.

**Detection hint:** `key-field` set to `"index"`, `"name"`, or any field that is not guaranteed unique per row.

---

## Anti-Pattern 6: Overriding onsubmit without calling event.preventDefault() and submitting manually

**What the LLM generates:**

```javascript
handleSubmit(event) {
    // Tries to modify fields but does not prevent default submission
    const fields = event.detail.fields;
    fields.Status__c = 'Submitted';
    // Form submits twice — once from default, once from manual call
    this.template.querySelector('lightning-record-edit-form').submit(fields);
}
```

**Why it happens:** LLMs know that `onsubmit` provides access to field values but forget that the form will auto-submit unless `preventDefault()` is called first.

**Correct pattern:**

```javascript
handleSubmit(event) {
    event.preventDefault();
    const fields = event.detail.fields;
    fields.Status__c = 'Submitted';
    this.template.querySelector('lightning-record-edit-form').submit(fields);
}
```

**Detection hint:** `onsubmit` handler that calls `.submit()` without a preceding `event.preventDefault()`.

---

## Anti-Pattern 7: Hand-rolling SLDS blueprint markup when a base component exists

**What LLMs generate:** A block of `slds-*` markup copied out of a design-system example — a
`<button class="slds-button slds-button_brand">`, a `<div class="slds-card">` with nested
`slds-card__header` / `slds-card__body`, a `<div class="slds-spinner_container">` — instead of the
`lightning-button`, `lightning-card` and `lightning-spinner` that already implement those blueprints.

```html
<!-- generated -->
<div class="slds-card">
  <div class="slds-card__header slds-grid">
    <h2 class="slds-card__header-title">Account Summary</h2>
  </div>
  <div class="slds-card__body slds-card__body_inner">
    <button class="slds-button slds-button_brand" onclick={handleSave}>Save</button>
  </div>
</div>
```

**Why it happens:** SLDS blueprint HTML is heavily represented in training data because it is
framework-agnostic and appears in every design-system doc, blog post and Aura example. It looks
correct and it renders.

**Why it is wrong:** The guide's own rule is to *"Use base components where possible instead of
creating your own component from an SLDS guideline. Using base components, you get the latest SLDS
design updates automatically"* (`lwc_guide base-components-all` L4543). The maintenance asymmetry is
the point: *"If SLDS updates the related blueprint, your component code isn't updated automatically.
To match the latest blueprint, you must manually update your component. Salesforce automatically
updates the base components when SLDS updates the associated blueprint"*
(`lwc_guide create-components-css-slds-blueprint` L1737). You also give up the ARIA state management,
keyboard behaviour and WCAG 2.1 AA contrast that base components carry
(`lwc_guide base-components-accessibility` L4953–L4957).

**Correct pattern:** Check the catalogue first. Build from a blueprint only when no base component
exists — and then *"replace standard HTML elements with Lightning base components wherever
possible"* inside it (L1747–L1748).

**Detection hint:** `class="slds-button` on a raw `<button>`, or `slds-card__` / `slds-spinner`
class names, in a template that imports nothing from `lightning/`.

---

## Anti-Pattern 8: Asserting `getAttribute` on a `lightning-*` stub in a Jest test

**What LLMs generate:** Tests that treat the base-component mock as if it rendered real DOM.

```javascript
// generated — passes and fails for the wrong reasons
const combobox = element.shadowRoot.querySelector('lightning-combobox');
expect(combobox.getAttribute('options')).toBe('[object Object]');
expect(combobox.getAttribute('label')).toBe('Rating');
// and then waits for the component's onchange handler to fire by itself
combobox.click();
```

**Why it happens:** Standard web-testing habits. In ordinary DOM testing, properties and attributes
track each other closely enough that `getAttribute` is a reasonable proxy.

**Why it is wrong:** *"Lightning base components have some properties that aren't reflected as
attributes in the DOM"* — the guide's example is `iconPosition` on `lightning-button`, which selects
an SLDS class and is never rendered — and *"No events are fired from these mocks but you can call
dispatchEvent() against them"* (`lwc_guide unit-testing-using-jest-patterns` L12626–L12627). An array
property such as `options` cannot round-trip through an attribute at all, so the assertion is
meaningless in both directions.

**Correct pattern:**

```javascript
const combobox = element.shadowRoot.querySelector('lightning-combobox');
expect(combobox.options).toEqual([{ label: 'Hot', value: 'Hot' }]);
expect(combobox.label).toBe('Rating');
combobox.dispatchEvent(new CustomEvent('change', { detail: { value: 'Hot' } }));
await Promise.resolve();
```

**Detection hint:** `getAttribute(` applied to the result of a `querySelector('lightning-…')`, or a
`.click()` on a base-component stub with no accompanying `dispatchEvent`.

---

## Anti-Pattern 9: Inventing attribute and variant names that no base component exposes

**What LLMs generate:** Plausible-looking attributes assembled from other frameworks or from the
Aura versions of the same component — `<lightning-card actions={cardActions}>`,
`<lightning-tabset selected-tab-id="two">`, `<lightning-button variant="primary">`,
`<lightning-accordion-section title="Tooltip text">`, `<lightning-badge title="Hover me">`.

**Why it happens:** Aura markup and LWC markup are near-identical in shape, so an Aura attribute name
transfers without any syntactic signal that it is wrong — and an unsupported attribute produces no
error at all.

**Why it is wrong:** Each of those is documented as a divergence. `lightning-card` takes text-only
`title` and `footer` with actions in a named slot, not an `actions` attribute (L11674);
`lightning-tabset` uses `active-tab-value` (L11733); `lightning-button`'s variant values are exactly
`base`, `neutral`, `brand`, `brand-outline`, `destructive`, `destructive-text`, `inverse`, `success`,
and an unsupported value silently falls back to the default (`lwc_guide create-components-css-slds`
L1620; `create-components-css-variants` L1683); `title` on `lightning-accordion-section` is reserved
for internal use (L11663); `title` on `lightning-badge` applies only to the wrapper, and
`icon-alternative-text` is what reaches the icon (L4794–L4801). More generally, an attribute marked
*"Reserved for internal use"* must not be used because it can change in any release
(`lwc_guide base-components-considerations` L4727).

**Correct pattern:** Every attribute is checked on the component's **Specification** tab in the
Component Reference before it is typed. Where design variations exist, use the `variant` attribute
with a documented value; where they do not, use an SLDS utility class through `class`, and only then
a styling hook (`lwc_guide create-components-css-slds` L1623–L1625).

**Detection hint:** An attribute on a `lightning-*` element that does not appear anywhere in the
Component Reference for that component; any `variant` value outside the documented list; any
attribute name in camelCase in markup (LWC markup is kebab-case).

---

## Anti-Pattern 10: Overriding SLDS classes or styling from a base component's rendered output

**What LLMs generate:** CSS that targets the internals a base component happens to render today.

```css
/* generated */
.slds-combobox__input {
  border-radius: 0;
}
lightning-button .slds-button {
  padding: 4px 12px !important;
}
```

**Why it happens:** The rendered markup is visible in the browser inspector, and targeting it is the
fastest way to make a pixel change.

**Why it is wrong:** *"Overriding base component styling isn't supported except when using documented
styling hooks"* (`lwc_guide create-components-css-slds` L1622,
`create-components-css-antipatterns` L1892). Salesforce reserves the right to redesign component
internals and documents feature changes but not internal ones (L1891); the specific
`.slds-combobox__input` case is the guide's own worked example of the mistake (L1894–L1895). From API
59.0 the generated CSS scope tokens are obfuscated strings, so selectors and test queries that rely
on them break (L1917–L1920).

**Correct pattern:** Escalate in the documented order — design variation (`variant`), then SLDS
utility class through `class`, then a styling hook, and only then your own custom class passed in via
`class` (L1623–L1625). Note that component-level hooks (`--slds-c-*`) are not yet supported in SLDS 2,
and that form elements and links cannot be styled with custom properties at all
(`create-components-css-custom-properties` L1701, L1724–L1726). Locate elements with
`lwc:ref="uniqueId"` and `this.refs` rather than a class-string match or an `id`
(`base-components-considerations` L4729).

**Detection hint:** Any `.slds-` selector in a component's own `.css` file; `!important` next to an
SLDS class; `querySelector('[class="slds-…"]')` in JavaScript or in a test.
