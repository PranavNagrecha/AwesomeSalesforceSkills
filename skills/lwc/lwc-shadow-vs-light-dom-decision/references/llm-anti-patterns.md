# LLM Anti-Patterns — LWC Shadow vs Light DOM Decision

Common mistakes AI coding assistants make when asked to choose or migrate render modes for an LWC. These help the consuming agent self-check its own output.

---

## Anti-Pattern 1: Defaulting to Light DOM because Shadow DOM CSS "doesn't work"

**What the LLM generates:** when a developer says "my parent component's CSS isn't reaching into my LWC," the LLM proposes `static renderMode = 'light'` as the first answer and skips the design-tokens approach entirely.

**Why it happens:** training data is heavy on Web Components articles where authors complain about Shadow DOM scoping and reach for slot-based or piercing workarounds. The LLM treats encapsulation as a defect, not a feature.

**Correct pattern:**

```javascript
// Shadow DOM (default) — theme via SLDS Styling Hooks / design tokens
import { LightningElement } from 'lwc';
export default class BrandedCard extends LightningElement {
    // No renderMode override
}
```

```css
/* brandedCard.css — auto-scoped because Shadow DOM */
:host {
    --slds-c-card-color-background: var(--corp-card-bg, #fff);
    --slds-c-card-color-border: var(--corp-brand-primary, #0070d2);
}
```

A parent setting `--corp-brand-primary` at any ancestor level themes the card without breaking encapsulation. Reach for Light DOM only when a real blocker (Bootstrap utility classes, LWR SEO, host-page DOM access) makes design tokens insufficient.

**Detection hint:** any LLM-proposed `static renderMode = 'light'` without a single-sentence blocker statement explaining what utility-class framework, SEO requirement, or external-DOM-access constraint forces the choice.

---

## Anti-Pattern 2: Leaving `:host` selectors in CSS after migrating to Light DOM

**What the LLM generates:** during a Shadow → Light migration, the LLM updates the JS class to add `static renderMode = 'light'` and updates the template to add `lwc:render-mode="light"`, but leaves the CSS file untouched. The `:host { ... }` rules silently drop.

**Why it happens:** the LLM sees the migration as a JS / template concern and doesn't understand that `:host` is a Shadow-DOM-only construct.

**Correct pattern:**

```css
/* BEFORE (Shadow DOM) */
:host { display: block; padding: 1rem; }
:host([data-variant="compact"]) { padding: 0.5rem; }

/* AFTER (Light DOM) — :host is silently dropped, hoist to a real selector */
.corp-card { display: block; padding: 1rem; }
.corp-card[data-variant="compact"] { padding: 0.5rem; }
```

The component template now needs a wrapping `<div class="corp-card">` to receive those styles, since there is no host shadow root to target.

**Detection hint:** grep for `:host` in any LWC bundle whose JS contains `static renderMode = 'light'` or template contains `lwc:render-mode="light"`.

---

## Anti-Pattern 3: Setting `composed: true` on events from a Light DOM component

**What the LLM generates:** boilerplate event-dispatch code that always reads `dispatchEvent(new CustomEvent('save', { bubbles: true, composed: true }))` regardless of render mode.

**Why it happens:** LWC tutorials drill `composed: true` as the safe default, and the LLM applies it universally. It is harmless under Light DOM, but the inverse mistake (`composed: false` left over from a Shadow DOM original after migration) is dead configuration that confuses the next reader.

**Correct pattern:**

```javascript
// Light DOM component — composed is irrelevant; default is fine
this.dispatchEvent(new CustomEvent('save', {
    detail: { recordId: this.recordId },
    bubbles: true
    // No composed — there is no shadow boundary to traverse
}));
```

```javascript
// Shadow DOM component with external listeners — composed: true is required
this.dispatchEvent(new CustomEvent('save', {
    detail: { recordId: this.recordId },
    bubbles: true,
    composed: true   // crosses the shadow boundary to a parent in another root
}));
```

**Detection hint:** any Light DOM component (`static renderMode = 'light'`) whose dispatched events explicitly set `composed: false` — that is dead configuration. Any Shadow DOM component dispatching events without `composed: true` where the listener is on a parent record page or App Builder host — likely a missing flag.

---

## Anti-Pattern 4: Using `lwc:dom="manual"` as a "Light DOM lite" mechanism

**What the LLM generates:** when a third-party JS library (Chart.js, Tippy, a rich-text editor) needs DOM access, the LLM proposes wrapping a `<div lwc:dom="manual">` inside a Shadow DOM component and assumes that solves a host-page-CSS-bleed-in problem too.

**Why it happens:** the LLM conflates "DOM that LWC does not diff" with "DOM the host page can reach." They are independent.

**Correct pattern:**

- `lwc:dom="manual"` — for one element where a third-party library will mutate the DOM. The element is still inside the Shadow DOM tree; host-page CSS still does not reach it. Use this when the rest of the component does not need Light DOM.
- `static renderMode = 'light'` — for the whole-component case where host-page CSS / DOM access is required across the entire component.

```html
<!-- Correct: Shadow DOM component with one manual-managed region -->
<template>
    <div class="chart-wrapper">
        <div lwc:dom="manual"></div>  <!-- chart library writes here -->
    </div>
</template>
```

If the chart library also needs Bootstrap utility classes from the host page (the actual blocker), then yes, the component should be Light DOM — but for the host-CSS reason, not the third-party-library reason.

**Detection hint:** any answer where `lwc:dom="manual"` is proposed as the fix for "host-page CSS doesn't reach inside my component."

---

## Anti-Pattern 5: Not asking about managed-package distribution before recommending Light DOM

**What the LLM generates:** the LLM sees a CSS-bleed-in problem, recommends Light DOM, and the developer ships the component into an ISV product where it fails packaging weeks later.

**Why it happens:** the LLM has no mental model of "managed package = mandatory Shadow DOM" because it is a Salesforce-specific constraint absent from generic Web Components training data.

**Correct pattern:** the workflow's step 1 is "identify the runtime." If managed package, stop — Shadow DOM is mandatory regardless of any other input. Theme via `--slds-*` tokens; do not waste cycles on a Light DOM design that will be rejected at packaging time.

**Detection hint:** any LLM recommendation of Light DOM that does not first ask whether the component is destined for a managed package.

---

## Anti-Pattern 6: Migrating to Light DOM without sweeping ARIA cross-references

**What the LLM generates:** during a Shadow → Light migration the LLM updates the render mode and the CSS, but never audits `aria-describedby` / `aria-labelledby` / `aria-controls` / `aria-owns`. Some of those references previously pointed across what was a shadow boundary (and were silently broken); after migration they may now resolve, or vice versa, with no explicit verification step.

**Why it happens:** the LLM treats accessibility as a static-analysis concern unrelated to render mode. It is not — IDREF resolution is per-root.

**Correct pattern:** during any render-mode change, walk every ARIA cross-reference attribute and confirm both endpoints live in the same root under the new mode. Document any reference that crosses a boundary as a known-broken case to fix in the same migration.

**Detection hint:** any render-mode migration PR where no `aria-` audit appears in the diff or the description.

---

## Anti-Pattern 7: Recommending Light DOM for "all Experience Cloud LWCs"

**What the LLM generates:** the LLM oversimplifies "Experience Cloud → Light DOM" and applies the rule to every LWC in any Experience Cloud context, including Aura sites and components that have no SEO or theming requirement.

**Why it happens:** the LLM has internalized the rule of thumb but lost the underlying conditions (LWR site + SEO requirement + corporate theme).

**Correct pattern:**

- **LWR site + public-facing + needs SEO + corporate theme** — Light DOM is the canonical answer.
- **LWR site but internal authenticated app (no SEO, SLDS-only theme)** — Shadow DOM is fine.
- **Aura Experience Cloud site** — depends on the host theme; often Shadow DOM with design tokens is enough.
- **Internal LEX page that happens to embed an Experience Cloud component** — Shadow DOM (default).

**Detection hint:** any blanket "use Light DOM for Experience Cloud" recommendation that does not differentiate LWR vs Aura sites and SEO-critical vs internal use cases.
