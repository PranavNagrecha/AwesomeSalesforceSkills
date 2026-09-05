# Well-Architected Notes - LWC Data Table

## Relevant Pillars

### Performance

Datatables concentrate rendering and interaction cost in one component. Stable keys, bounded page sizes, and controlled loading are essential to keep the browser responsive.

Salesforce publishes an actual envelope rather than an adjective: best performance at a maximum of 1,000 rows and 5 columns; load at most 50 rows at a time; past 250 rows, fewer than 20 columns (`data-table-performance` L6311, L6318, L6319). Every editable column costs more (L6314), and every level of nesting inside a custom cell template costs more again (L6316–L6317). Treat those numbers as the budget the design has to fit inside, and write the chosen page size down in `templates/lwc-data-table-template.md`.

### User Experience

Users notice table quality immediately. Clear row actions, predictable selection, and trustworthy inline edit behavior make the table feel dependable instead of fragile.

The sharpest UX decision in a datatable is what a failed save does to the user's typing, because clearing `draftValues` is also what removes the Cancel/Save footer (`data-table-inline-edit` L5712). Clearing early makes the table feel snappy and loses edits on error; clearing on success keeps the edits and leaves the footer up until the server agrees. Neither is wrong — leaving it undecided is.

### Reliability

An Apex write bypasses Lightning Data Service, so a component that refreshes only its own wire leaves every other component on the record page showing stale values (`data-table-inline-edit` L5718). The reliable shape is: await the Apex call, notify LDS, then re-provision the wire.

## Architectural Tradeoffs

- **Inline edit speed vs save complexity:** in-grid editing is efficient for small changes, but it introduces draft-state and failure-path complexity.
- **UI API `updateRecord()` vs an Apex controller:** `updateRecord()` handles one record per call and keeps LDS in sync for free; Apex saves the whole draft batch in a single transaction but obliges you to notify LDS yourself. The guide recommends Apex for bulk (`data-table-inline-edit` L5714, L5717–L5718).
- **One big result set vs progressive loading:** loading everything simplifies state at first, but it degrades responsiveness as volume grows.
- **`cellAttributes` styling vs a custom data type:** styling hooks and `cellAttributes` change how a cell *looks* with no new component; a custom type is a whole extra bundle, a registered type, and an a11y obligation. Only cross that line when the cell's markup must change.
- **Highly custom cells vs maintainability:** custom cell types can improve UX, but they add code paths and testing surface quickly — and they lose `event.detail.fieldName` on sort (`data-table-custom-types` L5856).

## Anti-Patterns

1. **Index-based row identity** - the grid cannot maintain stable state across refresh or sort.
2. **Inline edit without a save contract** - users think data saved because the table changed locally.
3. **Infinite loading with no stop condition** - the component keeps accumulating rows until the page slows down.
4. **A datatable as the mobile experience** - the component is not supported on mobile devices at all.
5. **One `updateRecord()` per draft row** - N network calls where the platform documents a single-transaction Apex path.

## Official Sources Used

- LWC Developer Guide, *Display Data in a Table with Inline Editing* (`data-table-inline-edit`) — https://developer.salesforce.com/docs/platform/lwc/guide/data-table-inline-edit.html (`key-field` is required and associates a row with a record L5675; `onsave` and `updateRecord(recordInput, clientOptions)` L5676; `editable: true` and compound fields L5678; `event.detail.draftValues` shape L5711; clearing `draftValues` hides the footer L5712; `updateRecord()` takes one record L5714; Apex recommended for bulk L5717; `notifyRecordUpdateAvailable` required after an Apex write L5718; await before notifying L5721)
- LWC Developer Guide, *Improve Datatable Performance* (`data-table-performance`) — https://developer.salesforce.com/docs/platform/lwc/guide/data-table-performance.html (failure modes L6304–L6308; 1,000 rows / 5 columns L6311; `enable-infinite-loading` + `onloadmore` L6313; editable columns cost performance L6314; custom-type nesting guidance L6316–L6317; 50 rows per load L6318; 250 rows / 20 columns L6319)
- LWC Developer Guide, *Create a Custom Data Type for lightning-datatable* (`data-table-custom-types`) — https://developer.salesforce.com/docs/platform/lwc/guide/data-table-custom-types.html (the standard type list L5773–L5786; extending `LightningDatatable` only for custom types L5795; the `customTypes` property table `template` / `typeAttributes` / `standardCellLayout` L5804–L5806; `fieldName` matches the row key L5812; `cellAttributes` for SLDS classes L5819; `onsort` gives `event.detail.fieldName`, `undefined` for custom types L5855–L5856; `super.connectedCallback()` L5857–L5859; nested datatables unsupported L5860)
- LWC Developer Guide, *Make a Custom Data Type Editable* (`data-table-custom-types-editable`) — https://developer.salesforce.com/docs/platform/lwc/guide/data-table-custom-types-editable.html (`lightning-input` recommended in the edit template L6139; `editedValue` / `columnLabel` / `required` / `typeAttributes` L6144–L6147; `data-inputable="true"` required for a11y L6149; `editTemplate` property L6150; `standardCellLayout: true` L6151; single-input base components only L6169; `lightning-input-field` unsupported in a datatable L6170; no server-side validation rules for custom types L6171)
- LWC Developer Guide, *Reactivity for Fields, Objects, and Arrays* (`reactivity-fields`) — https://developer.salesforce.com/docs/platform/lwc/guide/reactivity-fields.html (shallow tracking with `===` L2287; a new object or array must be assigned for the change to be detected L2288; array element mutation is not observed L2311–L2315)
- LWC Developer Guide, *Wire Apex Methods to Components* (`apex-wire-method`) and *Client-Side Caching* (`apex-result-caching`) — https://developer.salesforce.com/docs/platform/lwc/guide/apex-wire-method.html · https://developer.salesforce.com/docs/platform/lwc/guide/apex-result-caching.html (`@AuraEnabled(cacheable=true)` required for `@wire`, LDS does not manage Apex data L7098; `data`/`error` are hardcoded property names L7106–L7107; method must be static and global or public L7111; cacheable methods cannot mutate data L7254; `notifyRecordUpdateAvailable` for imperative Apex L7261; `refreshApex` argument must be an object previously emitted by an Apex `@wire` L7264)
- LWC Developer Guide, *Support Datatable Accessibility* (`data-table-a11y`) and *Customize Data Type Layout and Styles* (`data-table-custom-types-styling`) — https://developer.salesforce.com/docs/platform/lwc/guide/data-table-a11y.html · https://developer.salesforce.com/docs/platform/lwc/guide/data-table-custom-types-styling.html (navigation mode and action mode, `tabindex` `-1` vs `0` L6215–L6224; custom-type elements do not participate by default L6234; `tabindex={internalTabIndex}` and `data-navigation="enable"` L6239–L6240; bare layout is the default and drops a11y for editable types L6092–L6095; `standardCellLayout: true` L6097). The keyboard contract itself is owned by `lwc/lwc-accessibility`.
- LWC Developer Guide, *Compare lightning-datatable and lightning-tree-grid* (`data-table-vs-tree-grid`) — https://developer.salesforce.com/docs/platform/lwc/guide/data-table-vs-tree-grid.html (tree-grid supports neither column sorting, inline editing, nor infinite scrolling L5596–L5598; neither component is supported on mobile devices L5600)
- LWC Developer Guide, *Write Jest Tests* (`unit-testing-using-jest-create-tests`) and *Write Jest Tests for Wire Service* (`unit-testing-using-wire-utility`) — https://developer.salesforce.com/docs/platform/lwc/guide/unit-testing-using-jest-create-tests.html · https://developer.salesforce.com/docs/platform/lwc/guide/unit-testing-using-wire-utility.html (`__tests__` at the top of the bundle L12328; `.forceignore` glob keeps tests out of the org L12329–L12330; files end in `.test.js` L12331; reset the shared jsdom in `afterEach` L12336–L12339; `element.shadowRoot` is the test-only query root L12379; the Apex wire adapter mock L12524; `emit()` then resolve a promise before asserting L12548–L12549)
- Component Reference: `lightning-datatable` — https://developer.salesforce.com/docs/platform/lightning-component-reference/guide/lightning-datatable.html (the authority for the attribute and column-type catalogue the developer guide does not carry: `sorted-by`, `sorted-direction`, `default-sort-direction`, `is-loading`, `onrowaction` and the `action` type's `rowActions` typeAttribute, `max-row-selection`, `selected-rows`. Claims resting only on this page are marked UNVERIFIED in `references/code-examples.md`, since it was not fetchable while authoring.)
