# Well-Architected Notes — Common LWC Runtime Errors

## Relevant Pillars

- **Reliability** — This skill is primarily a Reliability concern. Runtime errors that surface as blank components, silent navigation failures, or unhandled exceptions directly degrade user trust and task completion. Defensive wire handlers, error boundaries, and proper event propagation configuration are all reliability practices. An LWC that fails gracefully (loading state, user-visible error message, fallback content) is reliable; one that silently renders nothing is not.

- **Operational Excellence** — Debug mode enablement, structured error messages in `errorCallback`, and correct use of `console.error` with contextual data enable teams to diagnose production issues quickly. Checker scripts that enforce defensive patterns at the code level shift quality left, reducing the operational cost of production incidents.

- **User Experience** — Every runtime error in this skill has a corresponding UX failure: blank panels, disappeared form sections, silent navigation dead-ends, or frozen interfaces. The patterns in this skill (wire loading states, error messages, graceful event fallbacks) are direct UX improvements. Well-Architected framing for UX states that users should always receive feedback — even when something fails.

- **Security** — Lightning Locker and Lightning Web Security are security models, not just compatibility layers. Code that attempts to circumvent them (disabling LWS, accessing cross-origin frames, patching native prototypes) trades security isolation for a short-term fix. This skill reinforces using the security model correctly rather than working around it.

---

## Architectural Tradeoffs

**Wire vs Imperative Apex:** `@wire` is simpler to write and benefits from LDS caching, but it introduces the `undefined/undefined` initial state and has the `refreshApex` limitation for non-LDS adapters. Imperative Apex calls require more boilerplate but give the developer full control over when data is fetched and refreshed. For components where data freshness after user actions is critical (forms, data tables with CRUD), imperative calls are often the better architectural choice despite the extra code.

**Event composition (`composed: true`) scope:** `composed: true` events cross all shadow boundaries all the way up to the document root, not just the immediate parent. In deeply nested component trees, this means a composed event from a leaf component can be received by any ancestor — including `c-app` or platform container components that may have unintended side effects if they listen on generic event names. Use specific, namespaced event names (`accountrecordsaved` rather than `save`) and document which components are expected to handle each event.

**Error boundaries and UX recovery:** `errorCallback` in a parent component catches errors from child components and prevents the error from propagating further up the tree (which would crash the entire page). However, `errorCallback` replaces the child subtree with whatever the parent renders in the error state — the child's DOM is removed. Design error boundaries at the right granularity: too fine-grained and every child error replaces a small piece of UI with an error message; too coarse-grained and a single child error blanks a large region of the page.

---

## Anti-Patterns

1. **Silent wire access without guards** — Accessing `wiredResult.data.fields.SomeField.value` directly in the template or in JS without checking that `data` is defined first. This produces runtime errors on every mount and is the most common LWC bug. The platform does not validate wire access patterns at build time — they fail only at runtime. Establish a team convention that all wire results are destructured into guarded local properties.

2. **Using `document.querySelector` for component-internal DOM** — Reaching for `document.querySelector` or `window.document.querySelector` to find elements inside a component's own template violates shadow DOM encapsulation, breaks under Locker Service, fails when multiple component instances exist, and ties the component to the global DOM structure. Always use `this.template.querySelector` within a component's own shadow scope.

3. **Ignoring `errorCallback` for parent-child component trees** — Building parent components that render complex child subtrees without implementing `errorCallback` means a runtime error in any child can propagate to the Salesforce platform's top-level error handler, which may blank the entire Lightning page or app. Implement `errorCallback` in any component that renders untrusted or complex child component trees.

---

## Official Sources Used

- LWC Developer Guide: Debugging — https://developer.salesforce.com/docs/component-library/documentation/en/lwc/lwc.debug_mode_enable
- LWC Developer Guide: Property Errors — https://developer.salesforce.com/docs/component-library/documentation/en/lwc/lwc.js_props_errors
- LWC Best Practices — https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
- Lightning Component Reference — https://developer.salesforce.com/docs/platform/lightning-component-reference/guide
- LWC Data Guidelines — https://developer.salesforce.com/docs/platform/lwc/guide/data-guidelines.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
