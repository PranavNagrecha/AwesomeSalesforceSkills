---
name: lwc-web-components-interop
description: "LWC interop with non-LWC web components: consuming third-party standard custom elements in LWC, exposing LWC as custom elements externally, Shadow DOM vs native web components, polyfills, and slotting patterns. NOT for LWC-to-LWC composition (use lwc-best-practices). NOT for Aura interop (use aura-to-lwc-migration)."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Reliability
tags:
  - lwc
  - web-components
  - custom-elements
  - shadow-dom
  - interop
  - third-party
triggers:
  - "how do we use a third party web component inside a lwc"
  - "lwc consume material web components vanilla custom element"
  - "embed external web component in lightning web component"
  - "lwc web components interop shadow dom slot"
  - "lwc static resource web component registration"
  - "lightning web component with standard custom element polyfill"
inputs:
  - Third-party web component library (Material, Shoelace, Vaadin, custom)
  - Target Salesforce surface (Lightning app, Experience Cloud, Embedded)
  - Styling requirements (SLDS vs custom theme)
  - Lifecycle and event-handling requirements
outputs:
  - Integration pattern (static resource, ES module, dynamic import)
  - Styling + SLDS compatibility plan
  - Event interop pattern (CustomEvent bridging)
  - LWC wrapper component template
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-21
---

# LWC Web Components Interop

Activate when an LWC must consume a third-party standard web component (a custom element defined outside Salesforce's LWC framework) or expose an LWC for external consumption. Web component interop is a supported pattern but full of subtle traps — shadow DOM boundary, event bubbling, styling isolation, and polyfill behavior all differ from plain LWC.

## Before Starting

- **Verify the third-party component is a true custom element.** Many "web components" are React-wrapped; those require a bridge, not direct consumption.
- **Check for Salesforce platform blockers.** Not all JavaScript APIs are available in Lightning Locker / Lightning Web Security context. Test early.
- **Audit the component's CSS approach.** If it ships a global stylesheet, it can clobber SLDS; if it uses shadow DOM, SLDS does not bleed in automatically.

## Core Concepts

### Custom elements in LWC

LWC supports embedding standard custom elements. The element must be defined via `customElements.define()`. LWC renders it like any DOM node; it is the consumer's responsibility to load the definition before first render.

### Static resource loading via loadScript

`loadScript` (from `lightning/platformResourceLoader`) imports a bundled custom element from a Static Resource. The script must call `customElements.define()` with a namespaced tag (e.g., `my-widget`) to avoid collisions across components.

### Shadow DOM boundary

LWC components have shadow DOM. A consumed web component may also have its own shadow DOM → nested shadow roots. Event bubbling respects both boundaries; styles are isolated on each side.

### Events

Third-party web components emit `CustomEvent` on their host. LWC listens via `onmyevent` in template or `this.addEventListener('myevent', ...)` in connectedCallback. Event detail payloads follow CustomEvent spec.

### Lightning Web Security (LWS)

LWS is the successor to Locker. It is more permissive but not unlimited; test custom elements that touch `window`, `document`, timers, or fetch.

## Common Patterns

### Pattern: Consume a Shoelace / Material component inside an LWC

Bundle the component JS as a Static Resource. LWC `connectedCallback` calls `loadScript(this, staticResource)` and renders `<sl-button>` (or equivalent). Events bridged via `addEventListener`.

### Pattern: Wrapper LWC with SLDS theming

An LWC wraps the third-party component, applies SLDS-consistent props, and exposes a simplified API. Rest of the codebase uses the wrapper — changing libraries becomes a wrapper-only change.

### Pattern: Event bridging to LWC events

Third-party component dispatches `CustomEvent('value-change')`. Wrapper LWC catches it and re-dispatches a Salesforce-flavored `CustomEvent('valuechange')` (lowercase, no dashes) for easier consumption in templates.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need a specific third-party control | Wrapper LWC consuming standard custom element | Native interop |
| Component depends on a heavy framework (React/Vue) | Reconsider — write native LWC or find alternative | Bridge cost exceeds value |
| Styling must match SLDS | Wrapper LWC applies SLDS props or CSS vars | Shadow DOM isolates |
| Multiple LWCs consume same third party | Single Static Resource, one define() call | Prevent collisions |
| Component touches window/document | Test in LWS early | Locker / LWS blocker |

## Recommended Workflow

1. Verify the candidate library is a true standard custom element (no framework wrapper).
2. Prototype in a scratch org: Static Resource + loadScript + render tag.
3. Test in Lightning Web Security context; note any blocked APIs.
4. Build a wrapper LWC with SLDS-consistent props and event bridging.
5. Document the wrapper's public API in JSDoc and in a README.
6. Centralize the Static Resource load (load once per page) to avoid duplicate define() errors.
7. Write LWC jest tests for the wrapper that mock the custom element.

## Review Checklist

- [ ] Third-party component confirmed as standard custom element
- [ ] Static Resource and loadScript pattern consolidated
- [ ] LWS compatibility tested
- [ ] Wrapper LWC provides SLDS-consistent API
- [ ] Events bridged to Salesforce-flavored names
- [ ] jest tests cover wrapper behavior
- [ ] Fallback or error UI if load fails

## Salesforce-Specific Gotchas

1. **customElements.define() is global.** Loading the same library twice on the same page throws "already defined" errors — centralize the load.
2. **Lightning Web Security is not identical to Locker.** Components that worked under Locker may need retesting; some APIs unblock under LWS.
3. **Experience Cloud vs Lightning App context differ.** Static Resources load consistently, but CSP, Locker/LWS, and loader timing can vary — test on every target surface.

## Output Artifacts

| Artifact | Description |
|---|---|
| Wrapper LWC template | JS + HTML + meta for the wrapper |
| Static Resource bundle | Web component JS packaged for Salesforce |
| Event bridging spec | External → Salesforce event names |
| Compatibility report | LWS / Locker blockers per API |

## Related Skills

- `lwc/lwc-best-practices` — baseline LWC patterns
- `lwc/lwc-performance-optimization` — loader optimization
- `integration/integration-pattern-selection` — adjacent choices
