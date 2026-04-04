# Well-Architected Notes — LWC Dynamic Components

## Relevant Pillars

### User Experience

Dynamic components directly serve user experience by enabling the UI to present contextually appropriate content without requiring a full page reload or a navigation event. When a user opens a Case with a specific record type, the correct detail form loads without the overhead of bundling every possible form into the initial page payload. This reduces time-to-interactive for the delivered content and avoids showing irrelevant UI sections. The flip side is that a poorly handled dynamic load — one without a loading state or error fallback — creates a worse experience than a static alternative. This skill enforces spinner states and error surfaces as non-optional checklist items.

### Operational Excellence

Dynamic component routing introduces a build-time dependency graph that is invisible to developers who are not familiar with how LWC modules are chunked. A computed import specifier breaks the build silently in some toolchain versions and loudly in others. Explicit literal specifiers and a clear routing map make the set of possible components auditable — a reviewer can read the source and immediately enumerate all components that may be rendered. The checker script in this skill validates that pattern programmatically so that code review is not the only gate. The package-type constraint (managed vs. unlocked) is also an operational concern: deploying this pattern into an unlocked package will cause a silent runtime failure that is difficult to diagnose after the fact.

---

## Architectural Tradeoffs

**Dynamic import vs. static `lwc:if` conditional rendering:**
Static conditional rendering with `lwc:if` is simpler, works in all package types, and requires no async handling. The cost is that all statically imported modules are included in the page bundle even if only one renders for a given user. For small, lightweight components, that cost is negligible. For large, complex forms or analytics panels, the bundle overhead is meaningful. Dynamic import should be chosen when the component is large, conditionally needed, and the packaging and security constraints are met.

**Lazy loading vs. prefetching:**
Dynamic imports are fetched on the first call, not at page load. This means the first user action that triggers the load sees a network round-trip. If the component is nearly always needed, a static import that loads with the bundle is faster overall. Reserve dynamic import for components that are needed by a subset of users or only after a deliberate user action.

**Routing logic in the host vs. in a configuration service:**
For a small number of variants, a `switch` or `if/else` block in the JavaScript class is clear and auditable. For a large or extensible set of components — e.g., a plugin-style architecture where new components can be added without modifying the host — consider a configuration-driven approach where a separate Apex service returns the component identity and a routing map in the host translates identities to literal import specifiers. This avoids hardcoding business logic in the UI layer while still satisfying the literal-string requirement for `import()`.

---

## Anti-Patterns

1. **Using dynamic import as a general-purpose lazy-loading tool in unlocked packages** — The platform restriction is categorical: dynamic imports with `lwc:component` are not supported in unlocked packages. Teams that build this pattern in a scratch org with a managed package namespace and then deploy to an unlocked package will encounter a silent runtime failure. Always confirm package type before committing to this pattern.

2. **No error boundary around the dynamic import** — A `try/catch`-less `await import(...)` means any module load failure (network error, module not found, LWS restriction) surfaces as an unhandled promise rejection with a blank component area. Users see nothing. Operators see nothing in logs unless they are watching the browser console. Always wrap `import()` in `try/catch` and render an explicit error message or fallback component.

3. **Constructing the import specifier from runtime data** — The `import()` mechanism in LWC requires static string analysis at build time. A template literal or concatenated string defeats this analysis and produces either a build failure or a runtime module-not-found error depending on toolchain version. All specifiers must be literal strings in the source, even if the routing logic that selects between them is dynamic.

---

## Official Sources Used

- LWC Best Practices — https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
- Lightning Component Reference — https://developer.salesforce.com/docs/platform/lightning-component-reference/guide
- LWC Data Guidelines — https://developer.salesforce.com/docs/platform/lwc/guide/data-guidelines.html
- Dynamic Components (LWC Developer Guide) — https://developer.salesforce.com/docs/platform/lwc/guide/dynamic-components.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
