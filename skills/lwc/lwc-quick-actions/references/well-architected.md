# Well-Architected Notes — LWC Quick Actions

## Relevant Pillars

- **Performance** — Headless actions avoid unnecessary modal rendering for one-tap operations; screen actions avoid full-page navigation for short edits. Both keep the user inside the record context, reducing page loads and wire refetches compared to a navigation-based UX. Using `getRecordNotifyChange` instead of `window.location.reload()` preserves cache warmth and in-flight wire data.
- **Security** — The quick-action surface does not change the permission model. Apex called from `invoke()` or from a screen action's save handler must still enforce CRUD/FLS via `WITH USER_MODE` or `Security.stripInaccessible`, and `@AuraEnabled` methods should be explicitly `with sharing`. Injected `recordId` is user-supplied input in security terms — do not assume it is one the user has access to without checking.
- **Operational Excellence** — A consistent pattern (headless for one-tap, screen for forms, Flow for declarative UX) keeps incident response and handoff simple. Using `ShowToastEvent` for both success and error paths gives operators a predictable UX contract to instrument and support.

## Architectural Tradeoffs

Choosing between a quick-action LWC and a Flow launched as a quick action is the main decision. The Flow path is better when the UX is declarative (screen flows with standard inputs, visual decision logic, admin-owned maintenance). The LWC path is better when the UX needs custom rendering, imperative side effects, or tight integration with other components on the page. Reaching for LWC because "Flow is slow" is usually premature — the overhead is small compared to the Apex work either route triggers.

Screen action vs headless is a UX decision, not a code-size decision. If the user has nothing to read or confirm, a screen action is visual noise. If the user needs to see current values or pick between options, a headless action that opens a hidden dialog is worse than a screen action with a proper form.

## Anti-Patterns

1. **Using a screen action for a one-tap update** — renders a modal the user does not need, adds two clicks, and creates a race condition between the save and the close.
2. **Using a headless action that internally opens a modal** — the bundle has nowhere to render the modal; the action closes as soon as `invoke()` resolves and tears the modal down. Use a screen action or `LightningConfirm.open` instead.
3. **Refreshing the page with `window.location.reload()` after the action** — breaks SPA navigation, discards warm caches, and interrupts other in-flight components. Use `getRecordNotifyChange`, `refreshApex`, or `NavigationMixin` instead.

## Official Sources Used

- LWC Best Practices — https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
- Lightning Component Reference — https://developer.salesforce.com/docs/platform/lightning-component-reference/guide
- LWC Data Guidelines — https://developer.salesforce.com/docs/platform/lwc/guide/data-guidelines.html
- Use Quick Actions (LWC) — https://developer.salesforce.com/docs/platform/lwc/guide/use-quick-actions.html
- Screen Quick Actions — https://developer.salesforce.com/docs/platform/lwc/guide/use-quick-actions-screen.html
- Headless Quick Actions — https://developer.salesforce.com/docs/platform/lwc/guide/use-quick-actions-headless.html
- `lightning/actions` module reference — https://developer.salesforce.com/docs/platform/lwc/guide/reference-lightning-record-action.html
- `lightning__RecordAction` target reference — https://developer.salesforce.com/docs/platform/lwc/guide/reference-lightning__recordaction.html
