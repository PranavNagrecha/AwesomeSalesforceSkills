# Well-Architected Mapping: LWC Lifecycle Hooks

---

## Pillars Addressed

### Reliability
Memory leaks from uncleaned event listeners cause component failures on long-running sessions and in Experience Cloud. Proper cleanup prevents the component from behaving unexpectedly after navigation.

- WAF check: All `addEventListener` calls have matching `removeEventListener` in `disconnectedCallback`?
- WAF check: All wire adapters handle both `data` and `error` branches?

### Security
Lightning Locker Service / LWS enforces shadow DOM isolation. External scripts loaded inline violate CSP. `@api` property immutability enforces one-way data flow and prevents parent data corruption.

- WAF check: No inline `<script>` tags (CSP violation)?
- WAF check: No cross-component DOM access (LWS violation)?
- WAF check: `@api` properties cloned before modification?

### Performance
`renderedCallback` without a guard runs on every re-render — potentially dozens of times per user interaction. Guards prevent redundant DOM work and third-party library re-initialization.

- WAF check: `renderedCallback` has guard for one-time operations?
- WAF check: Wire service used for reads (more efficient than imperative Apex for reactive data)?

### User Experience
`NavigationMixin` works across all Salesforce deployment contexts. `ShowToastEvent` is the expected feedback mechanism in Lightning. Proper error state display prevents blank components that confuse users.

- WAF check: Navigation uses `NavigationMixin`, not `window.location`?
- WAF check: User feedback uses `ShowToastEvent`, not `alert()`?
- WAF check: All async states (loading, data, error) have visible UI representation?

## Official Sources Used

- Salesforce Well-Architected Overview — UX, performance, and reliability framing for LWC design
- Lightning Component Reference — base component behavior and supported APIs
- Best Practices for Development with Lightning Web Components — lifecycle and composition guidance
- Data Guidelines — data-access strategy for LWC
- Secure Apex Classes — server-side security expectations for component-facing Apex
