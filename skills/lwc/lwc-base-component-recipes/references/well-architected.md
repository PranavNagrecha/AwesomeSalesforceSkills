# Well-Architected Notes — LWC Base Component Recipes

## Relevant Pillars

### Performance

`lightning-record-form`, `lightning-record-edit-form`, and `lightning-record-view-form` all use the UI API under the hood, which batches field reads into a single server call and benefits from platform-level caching. This is significantly more efficient than separate Apex calls per field. `lightning-datatable` is optimized for virtual DOM rendering but degrades above 1000 rows; paginate or use infinite scrolling for larger datasets.

### Reliability

Base components handle their own loading states, error display, and FLS enforcement. This reduces the surface area for reliability issues compared to custom Apex-backed forms that must manually implement each of these concerns. The primary reliability risk is developer-introduced: not wiring `draft-values` reset, using `if:true` to hide forms, or not handling the `onsuccess` / `onerror` events.

### Security

All base form components route through the UI API, which enforces CRUD and FLS at the platform level. A field the running user cannot read or write will be silently omitted or made read-only. This is the correct security posture and should not be bypassed. Developers must not mix base components with unprotected Apex methods that re-expose the same fields without FLS checks.

## Architectural Tradeoffs

**lightning-record-form vs custom Apex form:** Base components give up extensibility (custom field logic, cross-field calculations, conditional required fields) in exchange for automatic FLS, loading state management, and platform caching. For most standard CRUD scenarios, the base component wins. When business logic is complex, invest in a proper Apex-backed form using `@wire(getRecord)` and `updateRecord` — but only after confirming base components cannot meet the requirement.

**lightning-datatable inline editing vs row-level navigation:** Inline editing in `lightning-datatable` is convenient for bulk field updates, but it bypasses record validation rules that only fire on explicit save through the UI API. Validation rules, duplicate rules, and before-save flows still run, but the feedback surface is the generic `lightning-datatable` error column rather than field-level messages. For high-stakes data (financial records, regulated fields), prefer row-level navigation to a full edit form where validation is surfaced clearly.

**lightning-record-view-form vs read-only lightning-record-form:** Both render record fields in read-only mode. `lightning-record-view-form` with `lightning-output-field` gives full layout control and is preferred when field placement matters. `lightning-record-form mode="readonly"` uses the page layout and is faster to scaffold but less predictable across profiles.

## Anti-Patterns

1. **Bypassing FLS with Apex in the same component** — Using `lightning-record-edit-form` alongside a `with sharing` Apex method that reads fields the running user cannot see defeats the security posture. All data paths for a form must respect the same access model. If custom Apex is needed, it must also enforce CRUD/FLS explicitly.

2. **Rebuilding table chrome manually instead of using lightning-datatable** — Developers who use `<template for:each>` with `<input>` elements to create a manually editable table reimplement keyboard navigation, dirty state tracking, accessibility labels, and mobile responsiveness that `lightning-datatable` provides. This is a maintenance burden and an accessibility risk.

3. **Over-fetching fields in the columns array** — Passing every available field through `lightning-datatable` as columns increases payload size and degrades rendering performance. Restrict columns to the minimum required for the use case and use row actions or navigation to expose the full record detail.

## Official Sources Used

- Lightning Component Reference — https://developer.salesforce.com/docs/platform/lightning-component-reference/guide
- LWC Data Guidelines — https://developer.salesforce.com/docs/platform/lwc/guide/data-guidelines.html
- LWC Best Practices — https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
