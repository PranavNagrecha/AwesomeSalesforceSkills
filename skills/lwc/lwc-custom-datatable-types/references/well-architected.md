# Well-Architected Notes — LWC Custom Datatable Types

## Relevant Pillars

- **Performance** — Custom cell templates render on every visible row inside the datatable's virtualization window. A heavy template (nested forms, large child trees, bound `typeAttributes` objects recreated per render) multiplies per-row cost and drops frames on scroll. Keeping templates trivial, `typeAttributes` primitive, and interactive state delegated to child LWCs is a direct performance lever.
- **Operational Excellence** — A custom datatable subclass is shared infrastructure. Treating it as an evolving component (clear `customTypes` registry, documented column contracts, one merged subclass per app) keeps downstream teams productive. Ad hoc parallel subclasses scattered across orgs become untraceable drift.
- **Reliability** — The `draft-values` save path, sorting, and inline-edit behavior only work when each custom type keeps the platform contract: `typeAttributes` declared, `value` bound in the edit control, `value` left as a comparable scalar. When any of those contracts is broken, features appear to work in a demo and fail under real user load.

## Architectural Tradeoffs

- **Subclass vs. composition** — A custom datatable subclass is the only supported extension point for new cell types, but each subclass must register all required types; you cannot compose two subclasses at runtime. This pushes teams toward a single shared subclass per app, which becomes a coordination point between feature teams.
- **Template simplicity vs. UX richness** — The safer a template is (small SLDS primitives, no child components), the better scroll performance scales. Richer UX (per-row multi-field edit, action menus with state) pushes cost per row up, which caps the practical dataset size before virtualization smoothness degrades.
- **Sort/filter fidelity vs. display flexibility** — The datatable's sort operates on the column's `value`. Display-driven columns (pills, progress bars) that want to look one way but sort on a different primitive need careful column design — either keep `value` as the sort key or document an explicit `sortBy` override.
- **Inline edit vs. modal edit** — Inline edit via custom `editTemplate` is fast for single-field changes and integrates with `draft-values`, but every edit scenario that grows into multi-field validation eventually wants a modal or sub-LWC row detail. Picking the right threshold up front prevents template creep.

## Anti-Patterns

1. **Embedding `lightning-record-edit-form` inside a custom cell** — Each visible row instantiates a full record edit form, layout metadata fetches, and child inputs. Scroll performance collapses and inline-edit save path conflicts with the nested form. Use a row-detail sub-LWC or a modal instead.
2. **Treating the template as a full LWC** — Adding `connectedCallback`, `@wire`, imperative handlers inside the custom template. None of these run; the template has no `this`. Wrap interactive logic in a child LWC and let the template instantiate it.
3. **Hand-writing a `<table>` to avoid the subclass** — Reinventing selection, sort, inline edit, and virtualization loses platform accessibility, SLDS styling guarantees, and future feature uptake. Extend `LightningDatatable`; only drop down to a raw table when the grid's requirements are fundamentally different (truly infinite virtualization, non-tabular layouts).

## Official Sources Used

- LWC Best Practices — https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
- Lightning Component Reference — https://developer.salesforce.com/docs/platform/lightning-component-reference/guide
- LWC Data Guidelines — https://developer.salesforce.com/docs/platform/lwc/guide/data-guidelines.html
- lightning-datatable (component reference) — https://developer.salesforce.com/docs/component-library/bundle/lightning-datatable/documentation
- lightning-datatable (examples) — https://developer.salesforce.com/docs/component-library/bundle/lightning-datatable/example
- LWC Template Directives Reference — https://developer.salesforce.com/docs/platform/lwc/guide/reference-directives.html
- Create a Custom Data Type — https://developer.salesforce.com/docs/component-library/documentation/en/lwc/lwc.custom_data_types
