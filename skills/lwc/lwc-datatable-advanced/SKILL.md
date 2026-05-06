---
name: lwc-datatable-advanced
description: "Advanced lightning-datatable patterns — inline edit + draftValues, custom cell types via extending LightningDatatable, sortable columns, infinite scroll with onloadmore, row-level errors, and the cost of large data sets. NOT for read-only display of small lists (plain lightning-datatable suffices) or fully custom grids (use a third-party library)."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Operational Excellence
triggers:
  - "lightning-datatable inline edit save draft values"
  - "lwc datatable custom cell type extension"
  - "lwc datatable infinite scroll onloadmore"
  - "lwc datatable sort column server side"
  - "lightning-datatable row level error"
  - "datatable thousands of rows performance lwc"
  - "lwc datatable column actions row actions"
tags:
  - datatable
  - inline-edit
  - infinite-scroll
  - performance
  - custom-cell-type
inputs:
  - "Data shape: column metadata (label, fieldName, type, editable, sortable)"
  - "Edit semantics: row-by-row updateRecord vs bulk updateRecords"
  - "Page size and total row count (drives infinite scroll vs server-paged choice)"
outputs:
  - "lightning-datatable template with onsave and draftValues handling"
  - "Custom cell type module (LightningDatatable extension)"
  - "Decision: inline edit + LDS save vs custom save endpoint"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-05
---

# LWC Datatable Advanced

`lightning-datatable` ships with the patterns that turn it into a
real grid: inline edit with batched save, sortable columns, row
selection, row actions, infinite scroll via `onloadmore`, custom
cell types via subclassing, and row-level errors that highlight
specific cells. The hard part is composing them together without
fighting the framework.

The recurring shape is: rows come from `@wire(getRecords)` or an
Apex method, columns are a JS array with `editable: true` flags,
the user changes cells, the table emits `draftValues` on Save,
the controller calls `updateRecord` (one per row, in parallel) and
clears drafts on success / surfaces row-level errors on failure.
Infinite scroll layers on by setting `enable-infinite-loading`
and handling `onloadmore`. Custom cell types layer on by importing
`LightningDatatable` and extending it.

The mistakes are about state management. Engineers persist `data`
as an array reference and mutate it (LWC reactivity drops);
engineers don't dedupe row IDs across pages (infinite scroll
duplicates rows on hot reload); engineers fire `updateRecord`
sequentially in a loop and burn 30 seconds on 50 rows when they
could `Promise.all` the lot.

## Recommended Workflow

1. **Define columns as a class field, not in the template.** A
   JS array `columns = [{label, fieldName, type, editable, sortable}]`
   with `data` and `draftValues` is the canonical shape. Inline
   `<lightning-datatable columns={...}>` is harder to read.
2. **Bulkify the inline-edit save.** On `onsave`, build an array
   of `{fields: {Id, ...changedFields}}` from `event.detail.draftValues`,
   then `Promise.all(updateRecord(...))` them. Sequential saves
   make 50-row commits feel broken.
3. **Reset `draftValues` only after the save succeeds.** Setting
   `this.draftValues = []` on submit clears the drafts but loses
   the user's edits if the save fails mid-flight. Reset in the
   `then` of `Promise.all`.
4. **For sorting, decide client-side vs server-side up front.**
   Client-side: implement `sortBy` / `sortDirection` and mutate a
   local copy of `data`. Server-side: refetch with the new sort,
   reset infinite scroll. Mixing the two leads to inconsistent
   ordering after pagination.
5. **For infinite scroll, dedupe by row Id on every append.** A
   refresh or hot reload can cause the same row to be appended
   twice. `data = [...data, ...newRows.filter(n => !existing.has(n.Id))]`.
6. **Custom cell types: extend `LightningDatatable`.** Import
   `LightningDatatable` from `lightning/datatable`, register the
   custom type with a template. The template runs in the table's
   shadow DOM, not your component's — class names must come from
   SLDS or be set via `--slds-c-*` tokens.
7. **Show row-level errors via `errors` attribute.** Map
   `{rowId: {messages, fieldNames, title}}` after a failed save
   so the user sees the exact cell that failed.

## What This Skill Does Not Cover

- **Fully custom grids (AG Grid, Tabulator)** — use those libraries
  in their own LWC wrapper; outside this skill's scope.
- **Read-only datatables for fewer than ~50 rows** — plain
  `lightning-datatable` with no extensions is sufficient.
- **Tree grids** — see `lwc/lwc-tree-grid`.
