# Gotchas — LWC Datatable Advanced

Non-obvious `lightning-datatable` behaviors that cause real production problems.

---

## Gotcha 1: Wired data is read-only — mutating breaks reactivity

`@wire(getAccounts) accounts;` produces a read-only `data` proxy.
`this.accounts.data.push(newRow)` throws or silently no-ops. Copy
into `@track data = [...this.accounts.data]` and mutate the copy.

---

## Gotcha 2: `key-field` must be unique

If `key-field="Id"` and two rows share an Id (a join, a CSV
import that re-pulled a record), the table renders one of them
and silently drops the other. For aggregate rows, build a
synthetic key.

---

## Gotcha 3: `draftValues` are not cleared automatically on save

After `await updateRecord(...)`, the rows persist server-side but
the table still shows the orange unsaved indicator. Set
`this.draftValues = []` explicitly.

---

## Gotcha 4: Custom cell types don't inherit your component's CSS

The custom-type template renders inside `lightning-datatable`'s
shadow DOM. CSS in your component's `.css` file does not pierce
that boundary. Use `--slds-c-*` styling hooks (see `lwc-css-and-styling`)
or ship the styling as part of the custom type.

---

## Gotcha 5: `enable-infinite-loading` requires `event.target.isLoading`

The platform sets `event.target.isLoading = true` when the user
scrolls past `load-more-offset`. You must set it *back to false*
when your fetch completes — otherwise the spinner stays forever.

---

## Gotcha 6: Sorting and inline edit don't compose well

If the user has unsaved drafts and clicks a column header to
sort, the platform asks them to discard or save. There is no
"sort while preserving drafts". Disable sort or save-on-sort
explicitly.

---

## Gotcha 7: `onsave` event detail does not include unchanged fields

`event.detail.draftValues` is `[{Id, ChangedField1, ChangedField2}]`
— only the cells the user touched. If your save endpoint requires
the full row (Apex method without selective field handling), join
back against `this.data` before sending.

---

## Gotcha 8: `column.actions` requires both `name` and a unique label

A list of row actions with duplicate `label` values silently
dedupes — the user only sees one. If you have "Edit" and "Edit
Status" on the same row, ensure unique labels.

---

## Gotcha 9: Performance ceiling around ~5,000 rendered rows

`lightning-datatable` is virtualized but not as aggressively as
some third-party libraries. Past ~5,000 rows, scroll performance
degrades. Move to server-side paging (20-100 rows per page) or
a third-party library at that scale.
