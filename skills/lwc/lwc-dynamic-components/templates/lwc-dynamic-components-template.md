# LWC Dynamic Components — Work Template

Use this template when working on tasks that involve `lwc:component`, dynamic `import()`, or runtime component selection in LWC.

## Scope

**Skill:** `lwc-dynamic-components`

**Request summary:** (fill in what the user asked for)

---

## Context Gathered

Answer these before writing any code:

- **Package type:** [ ] Managed package   [ ] Unlocked package (if unlocked, stop — use lwc:if instead)
- **LWS enabled:** [ ] Yes   [ ] No   [ ] Unknown (verify before proceeding)
- **Candidate components:** (list every component that may be rendered dynamically)
  - `c/_______________`
  - `c/_______________`
  - `c/_______________`
- **Routing signal:** (what data determines which component to load?)
  - [ ] Record type ID
  - [ ] User role / permission set
  - [ ] Server-returned configuration flag
  - [ ] Feature flag via Apex wire
  - [ ] Other: _______________
- **@api props the child needs:** (list each property name and its source)
  - `_______________` from _______________
- **Child events the parent must handle:** (list each event name)
  - `_______________`

---

## Approach

Which mode applies?

- [ ] **Mode 1 — Implement:** Building a new dynamic component router from scratch
- [ ] **Mode 2 — Review:** Auditing an existing `lwc:component` implementation for correctness
- [ ] **Mode 3 — Troubleshoot:** Diagnosing why a dynamic component is not rendering

---

## Implementation Checklist

Copy from SKILL.md review checklist and tick items as you complete them:

- [ ] `lwc:is` is assigned `module.default`, not the raw module object
- [ ] Every import specifier is a **literal string** (no template literals or concatenation)
- [ ] `import()` is wrapped in `try/catch` with a user-visible error state
- [ ] The constructor property is reactive (`@track` or class field) so the template re-evaluates
- [ ] Confirmed managed package deployment (unlocked packages are not supported)
- [ ] LWS is enabled in the target org
- [ ] `@api` properties are bound on the `<lwc:component>` element
- [ ] A loading state (spinner or skeleton) displays while the import resolves
- [ ] Child events are handled via `oneventname` on the `<lwc:component>` element

---

## Template: Host Component JavaScript

```js
import { LightningElement, api, track } from 'lwc';

export default class [HostComponentName] extends LightningElement {
    @api [routingInput]; // e.g., recordTypeId, userRole, variantFlag

    @track dynamicCtor = null;
    hasError = false;

    async connectedCallback() {
        await this._loadComponent();
    }

    async _loadComponent() {
        try {
            let mod;
            if (this.[routingInput] === '[value-1]') {
                mod = await import('c/[component-1]');
            } else if (this.[routingInput] === '[value-2]') {
                mod = await import('c/[component-2]');
            } else {
                mod = await import('c/[default-component]');
            }
            this.dynamicCtor = mod.default;
        } catch (err) {
            console.error('[HostComponentName] failed to load dynamic component', err);
            this.hasError = true;
        }
    }

    handle[ChildEvent](event) {
        // handle events dispatched by the dynamic child
    }
}
```

---

## Template: Host Component HTML

```html
<template>
    <!-- Loading state -->
    <template lwc:if={dynamicCtor}>
        <lwc:component
            lwc:is={dynamicCtor}
            [api-prop-1]={[prop1Value]}
            [api-prop-2]={[prop2Value]}
            on[child-event]={handle[ChildEvent]}>
        </lwc:component>
    </template>

    <!-- Error state -->
    <template lwc:elseif={hasError}>
        <p class="slds-text-color_error">
            Unable to load the component. Please refresh the page or contact your administrator.
        </p>
    </template>

    <!-- Loading placeholder -->
    <template lwc:else>
        <lightning-spinner
            alternative-text="Loading..."
            size="small">
        </lightning-spinner>
    </template>
</template>
```

---

## Notes

Record any deviations from the standard pattern and why:

- (e.g., used wire adapter to fetch routing signal before calling import)
- (e.g., added `this.dynamicCtor = null` reset before reassignment due to wire re-trigger)
- (e.g., needed null check on routingInput because component mounts before @api prop is set)
