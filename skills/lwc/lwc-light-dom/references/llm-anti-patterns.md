# LLM Anti-Patterns — LWC Light DOM

Common mistakes AI coding assistants make when generating or advising on light-DOM Lightning Web Components. These patterns help a consuming agent self-check its own output.

## Anti-Pattern 1: Switching Every Component To Light DOM As A CSS Workaround

**What the LLM generates:** The user reports any CSS problem ("my external stylesheet does not apply", "the brand color is wrong inside my widget") and the assistant adds `static renderMode = 'light'` plus `lwc:render-mode="light"` to the component without asking whether a styling hook would solve it.

**Why it happens:** LLMs pattern-match on "external CSS not reaching inside LWC → use light DOM" from tutorials, without distinguishing a real interop blocker (SEO, library DOM walk) from a regular styling-hook problem that should stay in shadow DOM.

**Correct pattern:**

```javascript
// Prefer styling hooks inside shadow DOM first
// component.css
:host {
    --metric-color: var(--brand-color, #0070d2);
}
.metric { color: var(--metric-color); }
```

Only move to light DOM when styling hooks genuinely cannot solve it (SEO indexing, third-party library DOM access, global theming system that must inherit across many components).

**Detection hint:** Any diff that flips render mode without a Decision Guidance-style justification in the commit message or surrounding context. Grep for `renderMode = 'light'` added in the same PR as a CSS fix with no reference to SEO, third-party library, or Experience Cloud branding.

---

## Anti-Pattern 2: Creating A Plain `<name>.css` File For A Light-DOM Component

**What the LLM generates:** After switching a component to light DOM, the assistant writes styles into `myComponent.css`, unaware that the file is global in light DOM and will bleed across the whole page.

**Why it happens:** LLMs carry the shadow-DOM mental model where `<name>.css` is automatically scoped. The `*.scoped.css` naming convention is a specific Salesforce rule rather than a general web standard, so it is easy to miss.

**Correct pattern:**

```text
// File layout for a light-DOM component
myComponent/
├── myComponent.js          // static renderMode = 'light'
├── myComponent.html        // <template lwc:render-mode="light">
├── myComponent.scoped.css  // component-owned styles (scoped)
└── myComponent.js-meta.xml
```

**Detection hint:** In a component whose JS contains `renderMode = 'light'`, check whether the sibling CSS file ends in `.scoped.css`. A plain `.css` file alongside light DOM is almost always a bug. The checker script in `scripts/check_lwc_light_dom.py` flags this directly.

---

## Anti-Pattern 3: Claiming Light DOM Disables Or Bypasses Lightning Web Security

**What the LLM generates:** Guidance like "switch to light DOM so LWS no longer sandboxes your third-party script" or "light DOM lets you access page globals that LWS blocks".

**Why it happens:** LLMs conflate the DOM boundary with the JS sandbox. Both are "security-adjacent" in shadow DOM, so the model generalizes that removing one also removes the other.

**Correct pattern:**

> Light DOM changes where the rendered markup lives. It does **not** change how LWS treats JavaScript. LWS still sandboxes and rewrites third-party JS in a light-DOM component. Verify the third-party library is LWS-compatible before shipping; render mode will not fix LWS incompatibilities.

**Detection hint:** Watch for assistant output that pairs "light DOM" with "bypass", "disable", "turn off", or "no longer sandboxed" near the same sentence. Any such claim is wrong.

---

## Anti-Pattern 4: Shipping A Light-DOM Component Inside A Managed Package

**What the LLM generates:** An ISV asks the assistant to build a managed-package component, and the assistant sets `renderMode = 'light'` to simplify consumer theming or to fit a library that needs DOM access.

**Why it happens:** The assistant optimizes for the immediate tooling request ("library needs to querySelector") without checking the distribution model. Salesforce's guidance against light DOM in managed packages is a specific rule, not a general web principle.

**Correct pattern:**

```javascript
// Managed-package component: stay in shadow DOM
import { LightningElement, api } from 'lwc';

export default class IsvWidget extends LightningElement {
    // No renderMode override — default shadow DOM
    @api theme; // Expose a public property so consumers theme via API
}
```

Expose styling hooks through the shadow boundary and a documented public API for DOM interactions. Do not light-DOM a managed-package component.

**Detection hint:** Cross-reference the target `sfdx-project.json` `packageDirectories[].package` entries and package type. Any component with `renderMode = 'light'` inside a directory that maps to a managed package is a red flag. The checker script warns when `type: managed` appears in `sfdx-project.json` alongside light-DOM components.

---

## Anti-Pattern 5: Using `:host` Selectors In A Light-DOM Component's CSS

**What the LLM generates:**

```css
/* myComponent.scoped.css — INVALID in light DOM */
:host {
    display: block;
    --brand: #0070d2;
}
:host(.featured) { border: 2px solid gold; }
```

**Why it happens:** `:host` is canonical for shadow-DOM LWC styling. LLMs carry it over to light-DOM components without realizing there is no shadow host element to select.

**Correct pattern:**

```html
<!-- myComponent.html -->
<template lwc:render-mode="light">
    <div class="my-component" lwc:ref="root">
        <!-- content -->
    </div>
</template>
```

```css
/* myComponent.scoped.css */
.my-component { display: block; }
.my-component.featured { border: 2px solid gold; }
```

Use a real wrapper element with a class. `:host` and `:host-context` do not exist in light DOM — they either do nothing or fail to compile.

**Detection hint:** Grep the component's CSS for `:host` or `:host-context`. If the component's JS also contains `renderMode = 'light'`, the selector is meaningless and must be replaced with a wrapper-class selector. The checker script flags `:host` usage in light-DOM components.
