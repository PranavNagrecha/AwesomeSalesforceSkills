# Examples — LWC Shadow vs Light DOM Decision

Three realistic scenarios showing the render-mode decision, the CSS contract that goes with it, and the event-composition consequences.

---

## Example 1 — Light DOM for a Bootstrap-themed LWR site header

### Context

A retail org runs a public-facing Experience Cloud LWR site. The marketing team mandates the corporate Bootstrap 5 theme published as a static resource, and every page across the digital estate must look consistent — same header, same nav, same buttons. The component team is building a `corpHeader` LWC that wraps the site logo, primary nav, and a CTA.

### Problem

Started in Shadow DOM, the team discovered:

- Bootstrap utility classes (`.container-fluid`, `.col-md-6`, `.btn-primary`, `.text-muted`) had zero effect inside the component.
- Adding `--brand-primary` design tokens helped one button colour but did not solve the dozens of layout utilities that Bootstrap binds at the document root.
- SEO crawlers were not indexing the nav links inside the shadow root.

### Solution — Light DOM with a scoped escape hatch

```javascript
// corpHeader.js
import { LightningElement } from 'lwc';

export default class CorpHeader extends LightningElement {
    static renderMode = 'light';   // opt out of shadow DOM

    handleNavClick(event) {
        // No `composed: true` needed — Light DOM has no boundary to cross
        this.dispatchEvent(new CustomEvent('navigate', {
            detail: { to: event.currentTarget.dataset.target },
            bubbles: true
        }));
    }
}
```

```html
<!-- corpHeader.html -->
<template lwc:render-mode="light">
    <header class="container-fluid bg-light border-bottom">
        <div class="row align-items-center py-2">
            <div class="col-md-3"><img src="/logo.svg" alt="Acme" /></div>
            <nav class="col-md-9 d-flex justify-content-end">
                <a class="btn btn-link" data-target="products" onclick={handleNavClick}>Products</a>
                <a class="btn btn-link" data-target="solutions" onclick={handleNavClick}>Solutions</a>
                <a class="btn btn-primary ms-2" data-target="contact" onclick={handleNavClick}>Contact</a>
            </nav>
        </div>
    </header>
</template>
```

```css
/* corpHeader.scoped.css — only what must stay component-local */
.acme-logo-wrapper {
    max-width: 180px;
}
```

### Why it works

- Bootstrap utility classes can now reach the elements because there is no shadow root between the document and the component's children.
- SEO crawlers see the nav links as part of the document tree — they get indexed.
- The `*.scoped.css` rename keeps `acme-logo-wrapper` from leaking to the rest of the page.
- The event omits `composed`; the default (`composed: false`) is fine because Light DOM has no boundary to traverse. Setting `composed: true` would be redundant; setting `composed: false` would be dead configuration.

### Blocker statement (for future readers)

> "We are Light DOM because the LWR site mandates Bootstrap utility classes, which bind at the document root and cannot pierce a shadow boundary."

---

## Example 2 — Shadow DOM (default) for an internal record-form component

### Context

An internal sales-ops LWC, `commissionRecordForm`, is dropped on the Opportunity record page in LEX. It handles commission overrides, a sensitive financial field that an Ops Manager edits inline. Only SLDS is in play. The component will not be packaged.

### Problem

A junior dev opened a PR proposing Light DOM "to make the form easier to style." Code review caught it because:

- Nothing about the form requires host-page CSS to reach in.
- The form contains PII (rep name, payout amount); DOM-level isolation is a defensive line worth keeping.
- A future "global stylesheet" rolled out by another team (or by Salesforce in a release) could accidentally restyle the form fields.

### Solution — Shadow DOM (default), themed via SLDS Styling Hooks

```javascript
// commissionRecordForm.js
import { LightningElement, api } from 'lwc';

export default class CommissionRecordForm extends LightningElement {
    @api recordId;

    handleSave() {
        // External listener sits on the parent record page (different shadow root)
        // so we MUST set composed: true to cross the boundary.
        this.dispatchEvent(new CustomEvent('commissionsaved', {
            detail: { recordId: this.recordId },
            bubbles: true,
            composed: true
        }));
    }
}
```

```css
/* commissionRecordForm.css — automatically scoped because we're Shadow DOM */
:host {
    /* Theme via SLDS Styling Hooks — design tokens DO pierce the shadow boundary */
    --slds-c-card-color-background: var(--corp-card-bg, #ffffff);
    --slds-c-button-color-background-brand: var(--corp-brand-primary, #0070d2);
    display: block;
}

.commission-form-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--lwc-spacingSmall);
}
```

### Why it works

- The `:host` selector targets the component's host element from inside its own (scoped) stylesheet — a Shadow DOM construct that gets silently dropped under Light DOM.
- The custom event sets `composed: true` because the listener is on the record page, in a different shadow root from this component. Without `composed: true`, the event would stop at the boundary and the parent would never see it.
- A parent that wants to recolour the brand button sets `--corp-brand-primary` at any ancestor level — design tokens inherit through shadow roots, so the boundary is preserved without sacrificing themability.
- No PII-leaking selector ever escapes the component.

### Blocker statement

> "We are Shadow DOM (default) because there is no external CSS that needs to reach in, the form handles PII, and design tokens already cover the theming requirement."

---

## Example 3 — Hybrid: Aura host with corp theme, Shadow DOM children using design tokens

### Context

A legacy Aura console app hosts a tab with three LWC children (`accountSummary`, `pipelineWidget`, `activityFeed`). The org is mid-migration to LWC and the Aura wrapper is a year away from being retired. The corp theme — about a dozen brand colours and spacing tokens — is loaded at the Aura level via static resource and applied to Aura components.

### Problem

The team's first instinct was to switch all three LWCs to Light DOM "so the corp theme reaches in." But:

- The corp theme is small (a token set, not a utility framework), so the design-tokens approach is realistic.
- One of the children (`pipelineWidget`) is a candidate for future managed-package distribution to other internal divisions, which means it must be Shadow-DOM-clean today.
- Switching all three loses the encapsulation that has been working fine.

### Solution — Shadow DOM children, theme propagated via CSS custom properties

The Aura wrapper applies the brand tokens to the LWC host elements via inline style:

```html
<!-- AuraConsoleTab.cmp -->
<aura:component>
    <c:accountSummary aura:id="acct"
        style="--corp-brand-primary: #0070d2; --corp-spacing-card: 1rem;" />
    <c:pipelineWidget aura:id="pipe"
        style="--corp-brand-primary: #0070d2; --corp-spacing-card: 1rem;" />
    <c:activityFeed aura:id="feed"
        style="--corp-brand-primary: #0070d2; --corp-spacing-card: 1rem;" />
</aura:component>
```

Each LWC child stays Shadow DOM and consumes the tokens on its `:host`:

```javascript
// accountSummary.js
import { LightningElement, api } from 'lwc';
export default class AccountSummary extends LightningElement {
    // No renderMode override — Shadow DOM (the default).
    @api accountId;
}
```

```css
/* accountSummary.css */
:host {
    display: block;
    padding: var(--corp-spacing-card, 0.75rem);
    --slds-c-card-color-border: var(--corp-brand-primary, #0070d2);
}
```

### Why it works

- CSS custom properties inherit through shadow boundaries, so the tokens set at the Aura level propagate into each LWC.
- Each LWC keeps its encapsulation — `accountSummary` cannot accidentally restyle `pipelineWidget` and vice versa.
- `pipelineWidget` is still managed-package-eligible because it never opted into Light DOM.
- The corp theme is one CSS contract (design tokens), not three different scoping rules.

### Blocker statement

> "We are Shadow DOM in all three children because the corp theme is expressible as design tokens (small, stable token set) and one component is a managed-package candidate. Reach for Light DOM only if a specific component cannot solve its problem with tokens."

---

## Anti-Pattern: Reaching for Light DOM to fix a CSS specificity issue

**What practitioners do:** a developer cannot get an SLDS button to recolour, finds that `:host > .slds-button { background: red }` does not bite, and concludes "Shadow DOM is broken, switch to Light DOM."

**What goes wrong:** the component now has no encapsulation, every host page's CSS bleeds in, future managed-packaging is blocked, and the original problem (theming the button) was solvable in a single line via the SLDS Styling Hooks token `--slds-c-button-color-background`.

**Correct approach:** before changing render mode, exhaust the SLDS Styling Hooks catalog and design-token approach. Light DOM is for blockers like "Bootstrap utility classes" or "SEO inside an LWR site," not for "I could not find the right token in 30 seconds."
