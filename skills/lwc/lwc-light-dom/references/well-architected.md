# Well-Architected Notes — LWC Light DOM

## Relevant Pillars

- **Security** — Light DOM removes the shadow boundary that normally shields the component's internals from page-level JS and CSS. That shift increases the XSS surface (any un-sanitized HTML rendered into the component is now reachable from any script on the page) and makes global-CSS-based defacement possible. Lightning Web Security still sandboxes JavaScript, so the JS threat model is largely unchanged, but the DOM threat model is materially different. Treat any user-supplied HTML as untrusted and run it through DOMPurify or an equivalent sanitizer before injection. Review LWS compatibility for every third-party library you enable by switching to light DOM.
- **Performance** — The primary performance motivation is interop: SEO crawlers index light DOM content directly, third-party tooltip/chart libraries avoid expensive workarounds, and global theming systems apply without duplicated tokens per shadow tree. Light DOM itself is neither faster nor slower at render time for a single component, but removing the shadow boundary lets inherited styles cascade normally, which can reduce duplicated CSS payloads on large pages. The performance loss comes from *style specificity debugging* time, not runtime cost.
- **Operational Excellence** — Render mode becomes part of the component's public contract. Flipping it later is a breaking change for consumers that depended on encapsulation. Operationally excellent teams treat render-mode selection as a reviewed architectural decision, document the blocker it solves, keep managed-package components in shadow DOM, and name CSS files using the `*.scoped.css` convention so intent is visible at a glance.

## Architectural Tradeoffs

The core tradeoff is **encapsulation vs interop**. Shadow DOM gives you style isolation, ID scoping, and event retargeting — a safe default for reusable components. Light DOM gives those up to let external systems (search engines, libraries, global CSS, a11y tooling) reach the rendered markup. You cannot have both; the choice is per-component and semi-permanent.

Secondary tradeoffs referenced in `SKILL.md` → Decision Guidance:

- **Style encapsulation vs global theming flow-through** — shadow DOM blocks inherited theming by design; light DOM lets an Experience Cloud branding system reach every component consistently, at the cost of unintended style leaks if scoped files are not used.
- **Component reusability vs SEO indexability** — shadow DOM helps a widget behave the same across many pages; light DOM helps a single public-facing page rank. Components that try to do both end up brittle.
- **Isolation vs third-party DOM access** — a tooltip/chart library that calls `document.querySelector` cannot cross a shadow boundary; light DOM restores access but also re-exposes your DOM to any other script on the page.

## Anti-Patterns

1. **"Every component should be light DOM so CSS debugging is easier"** — this throws away encapsulation for an entire app. Debugging CSS specificity is a temporary pain; losing isolation is a permanent property of the component. Use styling hooks (CSS custom properties through the shadow boundary) before reaching for light DOM.
2. **Shipping a light-DOM component inside a managed package** — explicitly called out by Salesforce. Consumer orgs cannot scope the package's styles after install, so the leak is permanent and cross-org.
3. **Switching render mode to "fix" a functional bug** — render mode is not a bug-fix tool. If `querySelector` returns `null`, first check whether the component should expose a public API or custom event. Reaching for light DOM to paper over a design gap creates a larger problem than it solves.

## Official Sources Used

- Create Light DOM Components — https://developer.salesforce.com/docs/platform/lwc/guide/create-light-dom.html
- Style Light DOM Components — https://developer.salesforce.com/docs/platform/lwc/guide/create-light-dom-styles.html
- Migrate Shadow DOM Components to Light DOM — https://developer.salesforce.com/docs/platform/lwc/guide/create-light-dom-migration.html
- Lightning Web Security Introduction — https://developer.salesforce.com/docs/platform/lwc/guide/security-lwsec-intro.html
- LWC Best Practices — https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
