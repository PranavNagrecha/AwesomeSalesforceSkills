# LWC Datatable Design Worksheet

## Table Scope

- Data source:
- Expected visible row count:
- Needs inline edit: Yes / No
- Needs infinite loading: Yes / No
- Needs row actions: Yes / No

## Identity And Shape

- `key-field` (and: is it in the SELECT list?):
- Stable sort order:
- Column definitions — one row per column:

| Label | `fieldName` (key on the row, not the label) | `type` | `editable` | Where the key comes from (Apex SELECT / shaping layer) |
|---|---|---|---|---|
|  |  |  |  |  |

- Custom cell types (each needs `template`, `typeAttributes`, `standardCellLayout: true` if editable):
- Mobile in scope? (`lightning-datatable` is not supported on mobile devices — `data-table-vs-tree-grid` L5600):

## Interaction Plan

- Selection behavior:
- Row actions:
- Save behavior for edits (UI API `updateRecord` per row, or one Apex DML for the batch?):
- On a failed save, may the user's typing be discarded? (decides when `draftValues` is cleared):
- Refresh strategy — `refreshApex(wiredResult)` for this table, plus `notifyRecordUpdateAvailable` if the write went through Apex:

## Loading Strategy

- Initial page size (guide recommends a maximum of 50 rows per load — `data-table-performance` L6318):
- Worst-day row × column count vs the 1,000 × 5 envelope (L6311) and the 250-row / 20-column rule (L6319):
- Next-page fetch rule:
- Stop condition:
- Error surface:

## Sign-Off Checklist

- [ ] Row identity is stable and selected by the query.
- [ ] Every `fieldName` resolves to a key that exists on the provisioned row.
- [ ] Draft state is controlled, and the clear-on-failure policy is written down.
- [ ] Every row replacement produces a new array reference.
- [ ] Loading is bounded and inside the documented performance envelope.
- [ ] Action handling is intentional.
- [ ] `python3 skills/lwc/lwc-data-table/scripts/check_lwc_data_table.py --manifest-dir <src>` is clean.
- [ ] The bundle has a `__tests__` folder with a passing `describe`.
