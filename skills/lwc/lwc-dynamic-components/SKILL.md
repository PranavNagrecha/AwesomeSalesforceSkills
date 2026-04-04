---
name: lwc-dynamic-components
description: "Dynamic LWC component creation using the `lwc:component` directive, lazy-loaded dynamic imports (`import()`), and runtime component resolution for conditional rendering at scale. Triggers: 'render different components based on record type', 'dynamically load lwc at runtime', 'lwc:component lwc:is constructor', 'lazy load component only when needed', 'dynamic import lwc'. NOT for static component composition or `lwc:if` conditional rendering when the component set is fixed at build time (use lwc-conditional-rendering)."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Operational Excellence
triggers:
  - "how to render different components at runtime based on record type"
  - "dynamic component loading in LWC using lwc:component and lwc:is"
  - "lazy load a component only when the user triggers an action"
  - "lwc:is must be a constructor not a string"
  - "use dynamic import to switch between form components at runtime"
  - "how do I pass properties to a dynamically loaded LWC"
tags:
  - lwc-dynamic-components
  - dynamic-import
  - lazy-loading
  - lwc-component-directive
  - runtime-rendering
inputs:
  - "the use case driving runtime component selection: record type, user role, configuration flag, or feature flag"
  - "whether the component runs in a managed package or unlocked package (affects dynamic import support)"
  - "whether Lightning Web Security (LWS) is enabled in the org"
  - "the list of candidate components that may be rendered dynamically"
  - "any @api properties that must be set on the dynamically loaded component"
outputs:
  - "a working lwc:component pattern with dynamic import wiring"
  - "error-handling wrapper for failed module loads"
  - "decision guidance on when dynamic components are justified versus lwc:if-based conditional rendering"
  - "checker output flagging common dynamic-component misconfigurations"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# LWC Dynamic Components

Use this skill when a Lightning Web Component must select and render a different child component at runtime — not at build time — based on record type, user role, server-side configuration, or a feature flag that cannot be resolved statically. The `lwc:component` directive combined with dynamic `import()` is the platform-supported mechanism for this pattern since Spring '23.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is the component deployed in a **managed package** or an **unlocked package**? Dynamic imports require managed-package context; unlocked packages do not support the `lwc:component` dynamic loading pattern.
- Is **Lightning Web Security (LWS)** enabled? Dynamic imports are not available in the legacy Locker Service environment. LWS is required.
- What is the complete set of components that may be rendered? Dynamic imports use static string paths resolved at bundle time — you cannot construct the module specifier from a variable at runtime.
- Does the selected component receive `@api` properties, and which ones? Property passing is straightforward but must be handled after the constructor is set.
- Is there an error path if the module load fails? A missing `try/catch` leaves the user with a blank area and no feedback.

---

## Core Concepts

### The `lwc:component` Directive and `lwc:is`

The `lwc:component` tag is a special host element introduced in Spring '23 that renders whatever constructor is assigned to its `lwc:is` property. The template syntax is:

```html
<lwc:component lwc:is={dynamicCtor}></lwc:component>
```

`lwc:is` must receive a component **constructor** (a class reference), not a string name. Passing a string does nothing and renders no component. When `lwc:is` is `null` or `undefined`, nothing is rendered, which is the correct initial state before the import resolves.

### Dynamic Import and the `default` Export

The `import()` function loads a module asynchronously and returns a Promise that resolves to the module object. LWC component modules export their class as the **default export**, so you must destructure `default` to get the constructor:

```js
// Correct
const { default: Ctor } = await import('c/myComponent');
this.dynamicCtor = Ctor;

// Also correct (explicit)
const module = await import('c/myComponent');
this.dynamicCtor = module.default;

// Wrong — this sets lwc:is to the module object, not the constructor
this.dynamicCtor = await import('c/myComponent');
```

Assign the constructor to a reactive property decorated with `@track` or declared as a class field so the template re-evaluates when it changes.

### Lazy Loading and Bundle Splitting

Dynamic imports cause the module to be loaded as a **separate chunk** at runtime rather than included in the page's initial JavaScript bundle. This is the main performance benefit: a large component that is only sometimes needed does not inflate the first-paint payload. The component is fetched the first time `import()` is called; subsequent imports of the same module resolve from cache.

This also means there is a **network round-trip** the first time the component loads. For components that are almost always needed, a static import is cheaper. Reserve dynamic import for components that are genuinely conditional and large enough to justify the separate fetch.

### Property Passing and Event Handling

After setting `lwc:is`, you can pass `@api` properties to the dynamic component using standard attribute binding on the `lwc:component` tag. The dynamic child can dispatch custom events; the parent listens with a standard `oneventname` handler on the `lwc:component` element. There is no difference from static composition once the constructor is resolved.

---

## Common Patterns

### Mode 1: Implement a Dynamic Component Renderer

**When to use:** You need to select from a known set of LWC components at runtime based on record type, user role, or server-returned configuration.

**How it works:**

1. Declare a reactive property for the constructor and an optional map for `@api` inputs:

```js
import { LightningElement, api, track } from 'lwc';

export default class DynamicFormRouter extends LightningElement {
    @api recordTypeId;
    @track dynamicCtor = null;
    @track componentProps = {};

    async connectedCallback() {
        await this._loadComponent();
    }

    async _loadComponent() {
        try {
            let mod;
            if (this.recordTypeId === '012ABC') {
                mod = await import('c/caseDetailView');
            } else if (this.recordTypeId === '012DEF') {
                mod = await import('c/orderDetailView');
            } else {
                mod = await import('c/genericDetailView');
            }
            this.dynamicCtor = mod.default;
            this.componentProps = { recordId: this.recordTypeId };
        } catch (err) {
            console.error('Failed to load dynamic component', err);
            this.dynamicCtor = null;
        }
    }
}
```

2. In the template, render the dynamic component and bind properties:

```html
<template>
    <template lwc:if={dynamicCtor}>
        <lwc:component lwc:is={dynamicCtor}
                       record-id={componentProps.recordId}
                       onstatuschange={handleStatusChange}>
        </lwc:component>
    </template>
    <template lwc:else>
        <lightning-spinner alternative-text="Loading..."></lightning-spinner>
    </template>
</template>
```

**Why not the alternative:** Using a chain of `lwc:if` blocks with statically imported components works for a small fixed set, but it instantiates all imported modules in the bundle even when only one renders. Dynamic import defers the unused ones entirely.

### Mode 2: Review an Existing Dynamic Component Implementation

Check for:
- Is `lwc:is` receiving `module.default`, not the raw module object?
- Is the import call inside a `try/catch`? What does the UI show when the import fails?
- Is the reactive property triggering a re-render? Ensure it is a tracked or reactive field.
- Is the package type managed? If this is in an unlocked package, the pattern will not work.
- Is LWS enabled? Check Setup > Session Settings > Use Lightning Web Security.
- Are `@api` properties correctly bound on the `lwc:component` element?
- Does the import specifier use a literal string, not a computed value?

### Mode 3: Troubleshoot a Broken Dynamic Component

Common failure modes and their root cause:

| Symptom | Likely Cause |
|---|---|
| Nothing renders, no error | `lwc:is` is receiving the module object instead of `module.default` |
| `lwc:is` binding ignored | Using this in an unlocked package; dynamic import is not supported |
| TypeError on import | LWS is off; the dynamic import API is not available |
| Blank area with no error | `try/catch` swallowed the error; check the console |
| Props not reaching child | Properties not bound on `<lwc:component>` or `@api` missing in child |
| Import specifier error at build | Module specifier is constructed from a variable; must be a literal string |

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Small fixed set of components, always known at build time | `lwc:if` / `lwc:elseif` with static imports | Simpler, no runtime overhead, works in unlocked packages |
| Large or rarely needed component resolved from metadata at runtime | `lwc:component` with dynamic import | Defers bundle cost; component only loaded when needed |
| Component chosen from a configuration table in a managed package | Dynamic import with a switch/map | Clean separation of routing logic from rendering |
| Unlocked package deployment | Static conditional rendering only | Dynamic import is not supported in unlocked packages |
| Component must fire events back to parent | Standard `oneventname` on `<lwc:component>` | No special wiring needed; events work identically |
| Wire data needed before deciding which component to load | Wire first, then `await import()` in a reactive handler | Wire data is available in time; import is deferred until needed |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] `lwc:is` is assigned `module.default`, not the raw module object.
- [ ] The import specifier is a **literal string**, not a computed or template-literal value.
- [ ] The dynamic import is wrapped in `try/catch` with a visible error state for the user.
- [ ] The reactive property holding the constructor is properly declared (`@track` or class field) so the template re-evaluates.
- [ ] The component runs in a managed package if dynamic imports are in use (unlocked packages are not supported).
- [ ] Lightning Web Security is enabled in the org.
- [ ] `@api` properties are bound directly on the `<lwc:component>` element.
- [ ] A loading state (spinner or skeleton) is shown while the import resolves.
- [ ] Child component events are handled via `oneventname` on the `<lwc:component>` element.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **`module.default` omission silently renders nothing** — Assigning the Promise result of `await import('c/foo')` directly to `lwc:is` passes a module namespace object, not a constructor. The component silently renders nothing with no console error in most orgs. Always destructure `default`.
2. **Unlocked packages do not support dynamic import** — The `lwc:component` dynamic loading pattern is supported only in managed packages. Teams building in unlocked packages who encounter this will see a runtime failure. There is no workaround short of switching package type.
3. **The import specifier must be a static string** — The LWC build toolchain analyzes import calls at compile time to build the module chunk graph. A computed specifier like `` `c/${componentName}` `` will cause a build error or be silently ignored. All candidate components must appear as literal import strings in the source.
4. **Dynamic imports are not prefetched** — Unlike static imports that are included in the page bundle, dynamic imports fetch their chunk on the first call. This introduces a round-trip latency the first time the user triggers the load. Show a loading indicator and consider whether the round-trip cost is acceptable.
5. **LWS must be enabled** — Legacy Locker Service does not support `import()`. If an org has not migrated to Lightning Web Security, dynamic components will fail with a runtime error. Check Setup > Session Settings.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Dynamic component router | JavaScript class with async `connectedCallback` or reactive handler wiring `lwc:is` from a `module.default` assignment |
| Template with lwc:component | HTML template binding `lwc:is`, `@api` props, and event handlers on the dynamic element |
| Error handling wrapper | `try/catch` block with fallback state for failed module loads |
| Checker report | File-level findings from `scripts/check_lwc_dynamic.py` for common misconfigurations |

---

## Related Skills

- `lwc/lwc-performance` — use when the goal is general bundle optimization and the dynamic component pattern is one of several options being weighed.
- `lwc/lwc-conditional-rendering` — use when the component set is known at build time and `lwc:if` chains are the right tool.
- `lwc/lwc-in-flow-screens` — use when the dynamic component needs to run inside a Flow screen component context.
