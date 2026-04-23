# Well-Architected Notes — LWC Conditional Rendering

## Relevant Pillars

- **Performance** — Conditional rendering is a lazy-instantiation tool. `lwc:if` ensures a subtree is not created, not measured, and not re-rendered until the controlling property is truthy. Choosing `lwc:if` over "always mount and hide" defers child-component construction cost, script evaluation, and wire-adapter provisioning. Conversely, choosing CSS hide over `lwc:if` avoids repeated mount/unmount cost for frequently toggled panels. The `lwc:if` / `lwc:elseif` chain also short-circuits, so exclusive branches are cheaper than parallel `if:true` blocks that all evaluate independently — Salesforce's own guidance calls chained `if:true` / `if:false` less performant and flags the legacy directives for potential future removal.
- **Reliability** — Chained `lwc:if` / `lwc:elseif` / `lwc:else` encodes mutual exclusivity at the template level. Parallel `if:true` blocks rely on JavaScript to maintain exclusivity, and any bug that leaves two flags true simultaneously renders conflicting UI. Using `lwc:else` as the catch-all also eliminates the "unreachable state" class of bug where a status value that does not match any branch renders nothing.
- **Operational Excellence** — Getter-backed booleans (`isLoading`, `isReady`) give unit tests and code readers intention-revealing names. Template expressions are intentionally limited, which pushes computed logic into JS where it can be covered by Jest. A template reviewer can understand the state machine at a glance instead of reverse-engineering `a && b || !c` from the markup.

Not primarily applicable: **Security** (conditional rendering does not alter data access; always pair it with server-side enforcement) and **Scalability** (the directive works identically regardless of org size; relevant scale concerns belong in `lwc/lwc-performance`).

## Architectural Tradeoffs

The core tradeoff is **mount/unmount (`lwc:if`) vs hide/show (CSS)**. `lwc:if` gives you cheap absence when the branch is false but pays re-mount cost on every toggle and discards child state. CSS hide pays initial mount cost once but keeps the subtree alive — fast toggles, preserved state, but a bigger baseline DOM. Pick intentionally per toggle: reset-on-close UX wants `lwc:if`; preserve-on-close UX wants CSS hide. The skill's examples in `references/examples.md` show both variants side by side.

A secondary tradeoff is **where logic lives**: template expressions are limited on purpose. That restriction pushes complexity into JS getters, which are testable but add a layer of indirection. Resist the urge to work around the restriction with creative property chaining — the getter is the idiom.

## Anti-Patterns

1. **Chained `if:true` / `if:false` as a fake else** — Using `if:true={flag}` followed by a sibling `if:false={flag}` to simulate if/else. This is the legacy directive pair, officially discouraged, with no short-circuit between branches. Replace with `lwc:if` + `lwc:else`.
2. **Parallel `lwc:if` blocks for mutually exclusive states** — Writing three separate `lwc:if={isA}`, `lwc:if={isB}`, `lwc:if={isC}` blocks when the states are exclusive. A state bug that makes two flags true at once renders conflicting UI. Use `lwc:if` / `lwc:elseif` / `lwc:else` so the exclusivity is a template-level invariant.
3. **Using `lwc:if` for panels that must preserve in-progress user input** — Toggling a multi-field filter drawer with `lwc:if` silently destroys whatever the user was typing. Use CSS `display:none` via a class getter when state must survive the toggle.

## Official Sources Used

- LWC Best Practices — https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
- Render DOM Elements Conditionally — https://developer.salesforce.com/docs/platform/lwc/guide/create-components-conditional.html
- LWC Template Directives Reference — https://developer.salesforce.com/docs/platform/lwc/guide/reference-directives.html
- How a Component Is Rendered — https://developer.salesforce.com/docs/platform/lwc/guide/create-components-render-dom.html
- Lightning Component Reference — https://developer.salesforce.com/docs/platform/lightning-component-reference/guide
- LWC Data Guidelines — https://developer.salesforce.com/docs/platform/lwc/guide/data-guidelines.html
