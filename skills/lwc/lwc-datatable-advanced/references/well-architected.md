# Well-Architected Notes — LWC Datatable Advanced

## Relevant Pillars

- **Performance** — Inline-edit datatables are a common
  performance footgun. Sequential awaits, full-page reloads after
  every save, undeduplicated infinite-scroll pages, and
  client-side sorting on partially loaded data all cause
  noticeable lag for users on commodity hardware. The patterns in
  this skill (Promise.all-bulkified saves, dedup by `key-field`,
  server-side sort + paging, virtualized rendering past ~5K rows)
  push the latency floor by 5-10×.
- **Operational Excellence** — `lightning-datatable`'s row-level
  error model (`errors = {rows: {<Id>: {messages, fieldNames}}}`)
  surfaces partial-save failures inline at the cell. Without
  using it, a user editing 20 rows sees "save failed" with no
  indication of which row, and starts re-saving everything blind.

## Architectural Tradeoffs

The main tradeoff is **client-side simplicity vs server-side
correctness for sorting and paging**. Client-side sort is easy
to implement (one `Array.sort` on the local array) but only
sorts the loaded page — subsequent infinite-scroll pages arrive
in the original DB order, breaking the user's mental model.
Server-side sort is more code (refetch with sort params, reset
the page) but consistent across all rows.

Specifically:

- **<200 rows total**: client-side everything; load all up front.
- **200-5,000 rows**: server-side paging with infinite scroll;
  server-side sort.
- **>5,000 rows**: paging with explicit page controls; consider
  a virtualized third-party grid.

## Anti-Patterns

1. **Sequential `await updateRecord` in onsave.** 50 rows × 400ms
   = 20 seconds. Promise.all gets it to ~500ms.
2. **Mutating wired data.** Reactivity drops; `.push` silently
   no-ops. Always copy via `[...wiredArray]`.
3. **Component-scoped CSS for custom cell types.** Doesn't pierce
   the table's shadow DOM. Use SLDS hooks or ship CSS in the type
   module.

## Official Sources Used

- lightning-datatable (LWC Component Reference) — https://developer.salesforce.com/docs/component-library/bundle/lightning-datatable/documentation
- Custom Data Types — https://developer.salesforce.com/docs/component-library/bundle/lightning-datatable/documentation
- updateRecord (uiRecordApi) — https://developer.salesforce.com/docs/platform/lwc/guide/reference-lightning-ui-api-record.html
- Inline Edit (Lightning Data Service) — https://developer.salesforce.com/docs/platform/lwc/guide/data-ui-api.html
- Salesforce Well-Architected: Performant — https://architect.salesforce.com/well-architected/performant/efficient
