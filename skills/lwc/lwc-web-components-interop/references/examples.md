# Examples — LWC Web Components Interop

Worked artifacts for the patterns in `SKILL.md`. Third-party web components in
LWC are a Beta feature and require Lightning Web Security to be enabled org-wide.

---

## Example 1: A wrapper LWC that owns the load, the tag, and the event names

**Context:** The design system team ships a `<relative-time>` custom element
(renders "3 days ago" and self-updates). Several record pages need it.

**Problem:** Three separate failure modes converge on the naive version: the tag
renders inert without `lwc:external`; a second component loading the same library
throws on duplicate `customElements.define()`; and any non-lowercase event the
element dispatches cannot be bound in a template.

**Solution:** One wrapper owns all three concerns.

```html
<!-- relativeTimeField.html -->
<template>
    <template lwc:if={ready}>
        <!-- lwc:external is required for LWC to render a native custom element -->
        <relative-time lwc:external
                       datetime={isoValue}
                       class="slds-text-body_small">
        </relative-time>
    </template>
    <template lwc:else>
        <lightning-formatted-date-time value={isoValue}></lightning-formatted-date-time>
    </template>
</template>
```

```js
// relativeTimeField.js
import { LightningElement, api } from 'lwc';
import { loadScript } from 'lightning/platformResourceLoader';
import TIME_ELEMENTS from '@salesforce/resourceUrl/timeElements';

const TAG = 'relative-time';

export default class RelativeTimeField extends LightningElement {
    @api isoValue;

    ready = false;
    loaded = false;   // renderedCallback fires many times

    async renderedCallback() {
        if (this.loaded) {
            return;
        }
        this.loaded = true;

        // Registration is global and per page; a second define() throws.
        if (customElements.get(TAG)) {
            this.ready = true;
            return;
        }

        try {
            // Must be a UMD/IIFE bundle — loadScript does not accept ESM.
            await loadScript(this, TIME_ELEMENTS + '/time-elements.umd.js');
            this.ready = true;
        } catch (e) {
            this.ready = false;   // template falls back to the base component
        }
    }

    connectedCallback() {
        // Non-lowercase event names cannot be bound in the template.
        this.template.addEventListener('valueChange', this.handleValueChange);
    }

    handleValueChange = (event) => {
        // Re-dispatch lowercase so consumers can bind onrelativetimechange.
        this.dispatchEvent(new CustomEvent('relativetimechange', {
            detail: { value: event.detail?.value },
            bubbles: true,
            composed: true
        }));
    };
}
```

```xml
<!-- relativeTimeField.js-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <isExposed>true</isExposed>
    <targets>
        <target>lightning__RecordPage</target>
        <target>lightning__AppPage</target>
        <!-- Deliberately NOT lightningCommunity__Page: Experience Builder does
             not support third-party web components when LWS is enabled. -->
    </targets>
</LightningComponentBundle>
```

**Why it works:** `lwc:external` is what makes LWC render the tag as a native web
component rather than an unknown element. The `customElements.get()` check makes
a second load idempotent instead of throwing. `addEventListener` is the documented
route for non-lowercase event names, and re-dispatching a lowercase event means
every consumer downstream writes ordinary `on…` bindings. The `lwc:else` branch
means a load failure degrades to a base component instead of a blank card, and
the omitted Experience Cloud target encodes the platform limitation in metadata
so nobody adds the component to a portal page by accident.

---

## Example 2: Make the data path a property, not an attribute

**Context:** A `<sl-progress-bar>` element whose value comes from a wire adapter
and updates every few seconds.

**Problem:** The bar renders once at the initial value and never moves. LWC "sets
the data as attributes by default, and sets properties only if they exist," and
after rendering "attribute changes are ignored." The reactive update writes an
attribute that the element has stopped reading.

**Solution:** Have the element expose a property with a setter — then LWC writes
the property and the update lands.

```js
// Inside the third-party element (or a thin subclass you own):
class ProgressBar extends HTMLElement {

    // Only listed attributes trigger attributeChangedCallback.
    static get observedAttributes() {
        return ['value'];
    }

    set value(v) {
        this._value = Number(v);
        this.render();          // property write -> re-render
    }
    get value() {
        return this._value;
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (name === 'value' && oldValue !== newValue) {
            this.value = newValue;   // attribute write -> property -> re-render
        }
    }

    render() { /* paint using this._value */ }
}

customElements.define('sl-progress-bar', ProgressBar);
```

```html
<!-- The LWC side is then ordinary reactive markup. -->
<template>
    <sl-progress-bar lwc:external value={percentComplete}></sl-progress-bar>
</template>
```

**Why it works:** With a `value` setter present, LWC sets the property rather
than the attribute, so every reactive update re-renders. `observedAttributes()`
plus `attributeChangedCallback()` covers the case where something writes the
attribute directly — belt and braces, and the documented fallback when you cannot
add a property to the element. Verify the update path in the spike; the initial
render passing proves nothing about it.

---

## Example 3: Bulk properties with `lwc:spread`

**Context:** A chart element taking a dozen configuration properties, most of
them derived from one Apex response.

**Problem:** A dozen individual bindings in the template is noise, and each one is
another chance to hit the attribute-vs-property trap.

**Solution:**

```html
<template>
    <acme-chart lwc:external lwc:spread={chartProps}></acme-chart>
</template>
```

```js
get chartProps() {
    return {
        type: 'bar',
        series: this.series,          // objects survive; attributes would stringify
        stacked: true,
        legend: 'bottom',
        locale: this.userLocale
    };
}
```

**Why it works:** `lwc:spread` distributes the object's key-value pairs onto the
element, and passing objects as properties avoids the attribute path stringifying
them. Note the restriction: "Only one instance of `lwc:spread` on an element is
allowed" — so one object, assembled in a getter, not several merged in the
template.

---

## Anti-Pattern: Wrapping a React or Vue component and calling it interop

**What practitioners do:** Pick a component library from a framework ecosystem,
bundle the framework runtime into a static resource, mount the component into a
`lwc:dom="manual"` div, and treat the result as a web component.

**What goes wrong:** It is not a custom element, so none of the interop
machinery applies — no `lwc:external`, no attribute/property contract, no
lifecycle callbacks. You have shipped a second UI framework into the page: its
own reactivity loop, its own event system, its own version to upgrade, and a
bundle that competes for the 5 MB static-resource ceiling. Every LWC feature that
assumes it owns the DOM now has an exception, and every upgrade is a
cross-framework regression test.

**Correct approach:** Confirm the candidate is a true standard custom element —
that it registers through `customElements.define()` and works in a plain HTML
page with no framework present — before it enters the evaluation. If it is
framework-wrapped, the honest options are to find a native alternative or to
build the control as an LWC. The wrapping route is a permanent tax that always
looks cheapest on the first day.
