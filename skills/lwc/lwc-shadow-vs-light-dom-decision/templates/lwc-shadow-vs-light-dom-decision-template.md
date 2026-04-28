# Template — LWC Shadow vs Light DOM Decision

Use this template when deciding the render mode for a new LWC, or when reviewing a render-mode migration. Fill in each section before writing or merging code.

---

## 1. Component identity

| Field | Value |
|---|---|
| Component bundle | `force-app/main/default/lwc/<componentName>/` |
| Author / owner | `<name>` |
| Decision date | `YYYY-MM-DD` |

---

## 2. Runtime

Mark the single runtime where this component is primarily intended to render:

- [ ] Internal Lightning Experience (record page, App Builder, utility bar)
- [ ] Flow screen (`lightning__FlowScreen` target)
- [ ] Experience Cloud — **LWR** site (public-facing, SEO-critical)
- [ ] Experience Cloud — **LWR** site (internal, authenticated, no SEO)
- [ ] Experience Cloud — **Aura** site
- [ ] Aura host (legacy console app, Aura record page)
- [ ] Agentforce surface (`lightning__AgentforceAction` target)
- [ ] **Managed package destined for AppExchange**

If the last box is ticked, **STOP. Render mode is Shadow DOM (the default). Light DOM is forbidden in managed packages.** Skip to section 6 and document Shadow DOM with the design-tokens theming approach.

---

## 3. CSS contract

Mark the CSS that will reach (or attempt to reach) the component:

- [ ] SLDS only — design tokens (`--slds-c-*`) are enough
- [ ] SLDS + a small corporate token set (a dozen `--corp-*` brand colours / spacing values) — design tokens scale
- [ ] Third-party utility framework (Bootstrap, Tailwind, custom corp utility classes) — **utility classes do not pierce shadow boundaries**
- [ ] Aura host page with global stylesheet — depends on size (small token set vs hundreds of selectors)
- [ ] All-custom CSS owned by this component only

---

## 4. Accessibility requirements

- [ ] Component is self-contained; all ARIA references stay inside this component
- [ ] Component contains an input that needs `aria-describedby` pointing at an error message in **another component / different root** — flag for resolution
- [ ] Component renders `sr-only` content that an external screen reader must navigate as part of a larger flow
- [ ] Component is purely presentational and has no ARIA cross-references

Walk every `aria-describedby`, `aria-labelledby`, `aria-controls`, `aria-owns` attribute. For each, confirm both endpoints will live in the same root under the chosen render mode.

---

## 5. Events

List every custom event this component dispatches:

| Event name | `bubbles` | `composed` | External listener? | Notes |
|---|---|---|---|---|
| `<eventname>` | `true` / `false` | `true` / `false` | yes / no | |

Rules:
- Light DOM → `composed` is irrelevant; omit it. Setting `composed: false` is dead configuration.
- Shadow DOM with an external listener → `composed: true` is required.

---

## 6. Decision

Pick exactly one row that matches this component's situation:

| Situation | Mode | CSS file | `:host` allowed? | `composed:true` events? |
|---|---|---|---|---|
| Corp utility framework required (Bootstrap, Tailwind) | **Light DOM** | `<componentName>.scoped.css` for component-local; global handled by host | **No** | Default — no flag needed |
| Aura host with hundreds-of-selectors theme | **Light DOM** | `<componentName>.scoped.css` | **No** | Default — no flag needed |
| LWR public site, SEO-critical | **Light DOM** | `<componentName>.scoped.css` | **No** | Default — no flag needed |
| Aura host with small token set | **Shadow DOM** | `<componentName>.css` (auto-scoped) | **Yes** | `composed: true` for external listeners |
| Internal LEX-only, SLDS theming | **Shadow DOM** | `<componentName>.css` | **Yes** | `composed: true` for external listeners |
| Managed package | **Shadow DOM** (mandatory) | `<componentName>.css` | **Yes** | `composed: true` for external listeners |
| Security-sensitive form (PII, payment) | **Shadow DOM** | `<componentName>.css` | **Yes** | `composed: true` for external listeners |
| Modal / overlay | **Shadow DOM** + consider `lightning-modal` | `<componentName>.css` | **Yes** | `composed: true` for external listeners |

Recommended mode: `<Shadow DOM | Light DOM>`

---

## 7. Blocker statement (mandatory if Light DOM)

Write one sentence explaining the specific blocker that makes Light DOM necessary. This sentence goes into the component's class-level JSDoc and survives every refactor.

> "We are Light DOM because <Bootstrap utility classes / corp theme of N selectors / LWR SEO requirement / Aura host stylesheet of N selectors>."

If Shadow DOM, write one sentence confirming why Shadow DOM is sufficient:

> "We are Shadow DOM (default); the corp theme is expressible as design tokens and the component has no external CSS framework reaching in."

---

## 8. Skeleton

### Shadow DOM (default)

```javascript
// componentName.js
import { LightningElement } from 'lwc';

export default class ComponentName extends LightningElement {
    // No renderMode override — Shadow DOM is the default

    handleAction() {
        this.dispatchEvent(new CustomEvent('actioned', {
            detail: { /* ... */ },
            bubbles: true,
            composed: true     // crosses shadow boundary to external listener
        }));
    }
}
```

```css
/* componentName.css — auto-scoped */
:host {
    display: block;
    --slds-c-button-color-background-brand: var(--corp-brand-primary, #0070d2);
}
```

### Light DOM (opt-in)

```javascript
// componentName.js
import { LightningElement } from 'lwc';

/**
 * Light DOM blocker: <one-sentence explanation>.
 */
export default class ComponentName extends LightningElement {
    static renderMode = 'light';

    handleAction() {
        // No `composed` — Light DOM has no boundary to traverse
        this.dispatchEvent(new CustomEvent('actioned', {
            detail: { /* ... */ },
            bubbles: true
        }));
    }
}
```

```html
<!-- componentName.html -->
<template lwc:render-mode="light">
    <!-- ... -->
</template>
```

```css
/* componentName.scoped.css — component-local rules ONLY */
.component-local-class { /* ... */ }
/* Global rules for this component live in a host stylesheet, not here */
```

---

## 9. Verification

- [ ] Render-mode decision is justified by a single-sentence blocker statement
- [ ] If managed package: component is Shadow DOM (no exceptions)
- [ ] If Light DOM: no `:host` selectors anywhere in the bundle
- [ ] If Light DOM: component-local CSS is in `*.scoped.css`, not the global `<componentName>.css`
- [ ] If Light DOM: dispatched events do NOT explicitly set `composed: false`
- [ ] If Shadow DOM: parent-driven theming uses `--slds-*` / `--corp-*` design tokens, not parent-side global selectors
- [ ] If Shadow DOM: every external custom event sets `composed: true`
- [ ] Every ARIA cross-reference has both endpoints in the same root
- [ ] `python3 skills/lwc/lwc-shadow-vs-light-dom-decision/scripts/check_lwc_shadow_vs_light_dom_decision.py force-app/main/default/lwc/<componentName>` exits 0
