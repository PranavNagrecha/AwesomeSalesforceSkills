# Gotchas - LWC Data Table

Grounding note: line references are to the Lightning Web Components Developer Guide page
named in each *Grounded* line. `lightning-datatable`'s full attribute and column-type
catalogue lives in the **Component Library**, which is not a developer-guide page — any
attribute the guide never names is called out as such.

## `key-field` Problems Masquerade As Rendering Bugs

**What happens:** Selected rows, inline edits, or rerendered cells appear to attach to the wrong record.

**When it occurs:** The table uses an unstable or non-unique value for `key-field`.

**How to avoid:** Treat row identity as part of the data model. Use a stable key such as `Id` and carry it through every load and refresh. `key-field` is not optional decoration — the guide calls it "the required `key-field` attribute" and says it is what "associates each row with a contact record". Anything the shaping layer computes (a row number, a concatenation, an array index) is re-derived on every load and therefore is not a key.

*Grounded:* `data-table-inline-edit` L5675.

---

## Draft State Stays Until You Reset It — But *When* You Reset It Is A Design Decision

**What happens:** The table keeps showing pending edits after save, or later saves include stale changes — or, in the opposite failure, a save fails and the user's typing is gone.

**When it occurs:** The component treats `draftValues = []` as a formality rather than as the thing that hides the footer. Clearing `draftValues` is what removes the Cancel/Save footer, so the two guide examples clear it at different moments: the UI API recipe clears it immediately after copying the values into record objects, before the `updateRecord` promises resolve; the Apex recipe clears it after `await`ing the update and the refresh.

**How to avoid:** Pick deliberately. Clear early only if a failed save can safely discard the edits; clear late (inside the success branch, as the worked example in `references/code-examples.md` does) whenever losing the user's typing on a server error is unacceptable. Never clear in a `finally`.

*Grounded:* `data-table-inline-edit` L5712 ("To hide the datatable footer, clear the `draftValues` property"), L5683–L5684 (UI API path clears before the awaits), L5739 (Apex path clears after).

---

## Infinite Loading Without A Stop Rule Becomes A Memory Problem

**What happens:** The table keeps requesting and holding more rows until the page becomes sluggish, or the whole page freezes.

**When it occurs:** The component sets `enable-infinite-loading` and an `onloadmore` handler but never disables loading or bounds the server page. Everything the datatable displays is held in the browser, so the failure modes are slow load, laggy interaction, no load at all, and a frozen or crashed browser.

**How to avoid:** Bound the query — the guide recommends loading a maximum of 50 rows at a time using `LIMIT`, `LIMIT`/`OFFSET` pagination, or GraphQL pagination — and stop when a returned batch is shorter than the requested page. Salesforce's own testing puts best performance at a maximum of 1,000 rows and 5 columns; past 250 rows the guide asks for fewer than 20 columns.

*Grounded:* `data-table-performance` L6304–L6308 (failure modes), L6311 (1,000 rows / 5 columns), L6313 (`enable-infinite-loading` + `onloadmore`), L6318 (50 rows), L6319 (250 rows / 20 columns). The pattern of setting the loading flag back to `false` is Component-Library-only. UNVERIFIED (2026-09-05): no developer-guide page names an `isLoading` or `enable-infinite-loading` setter on the element instance.

---

## The Element Is Kebab-Case, The Column Object Is camelCase — And The Boundary Is Invisible

**What happens:** Formatting or custom behavior seems ignored for a column even though the code looks plausible. Nothing errors.

**When it occurs:** The two naming worlds get mixed. Property names in JavaScript are camelCase while HTML attribute names are kebab-case, and the datatable straddles both: the markup carries `key-field`, `draft-values`, `enable-infinite-loading`; the objects inside the `columns` array carry `fieldName`, `typeAttributes`, `cellAttributes`, `standardCellLayout`, `editTemplate`. A kebab-case key inside a column object is simply an unrecognised property.

**How to avoid:** Keep the column array in a module-level `const` and review it against the custom-type property table (`template`, `typeAttributes`, `standardCellLayout`) rather than against the markup. Test every non-default type explicitly — a wrong key produces a plain text cell, not an error.

*Grounded:* `js-props-names` L2338; `data-table-custom-types` L5804–L5806 (the `customTypes` property table).

---

## `columns[].fieldName` Names A Key On The Row Object, Not A Field On The sObject

**What happens:** A column renders blank for every row while the Apex query plainly returns the value.

**When it occurs:** `fieldName` is set to a field label, a relationship path the shaping layer flattened away, or a derived value that was never added to the row. The guide's own phrasing is positional: "the `columns` attribute assigns a record field to each column", and in the custom-type example "the `fieldName` property matches the `Name` field on the account object" — matches the *key on the provisioned row*, which for `SELECT Account.Name` is a nested object, not a flat `Account.Name` string.

**How to avoid:** Put a shaping layer between the wire and the table that flattens relationship fields and adds every derived key a column or `cellAttributes`/`typeAttributes` `fieldName` reference expects. The checker in this skill flags column `fieldName` values with no matching key in the Apex return shape when it can detect one.

*Grounded:* `data-table-inline-edit` L5675; `data-table-custom-types` L5812.

---

## Mutating `data` In Place Does Not Rerender The Table

**What happens:** A sort, an append after `onloadmore`, or a local patch after save changes the array but the table shows the old rows.

**When it occurs:** The code calls `this.rows.sort(...)`, `this.rows.push(...)`, or `this.rows[i].Field = x`. LWC "tracks field value changes in a shallow fashion. Changes are detected when a new value is assigned to the field by comparing the value identity using `===`", so an in-place mutation is invisible. Note that `Array.prototype.sort` sorts in place and returns the *same* reference, which is why `this.rows = this.rows.sort(...)` also fails to rerender.

**How to avoid:** "When manipulating complex types like objects and arrays, you must create a new object and assign it to the field for the change to be detected" — sort a copy (`[...this.rows].sort(...)`), append with spread, and rebuild rows with `map`. `@track` would make the mutation observable, but on a datatable it buys deep observation of every cell for no benefit; a new array reference is cheaper and is what the worked example does.

*Grounded:* `reactivity-fields` L2287–L2288, L2311–L2315.

---

## Sorting A Custom Data Type Returns `undefined` From `event.detail.fieldName`

**What happens:** The sort handler works for every stock column and silently no-ops on the one column that uses a custom type.

**When it occurs:** The handler reads `event.detail.fieldName` uniformly. For a standard data type that is how you identify the sorted column; for a custom data type it returns `undefined`.

**How to avoid:** Pass the field name into the sorting function for custom-type columns rather than reading it off the event, and guard the handler against an `undefined` field name so it fails loudly rather than reordering by `undefined`.

*Grounded:* `data-table-custom-types` L5855–L5856.

---

## `standardCellLayout` Defaults To `false`, And The Bare Layout Drops Keyboard Access

**What happens:** A custom-type column looks slightly off — no cell padding, content flush to the border — and its editable cells cannot be reached by keyboard.

**When it occurs:** A custom type is registered in `static customTypes` without `standardCellLayout`. The default is `false`, which selects the bare layout: it removes left/right padding and "doesn't support accessibility and keyboard navigation for editable types". Every standard data type uses the standard layout, which is why the custom column looks different from its neighbours.

**How to avoid:** Set `standardCellLayout: true` on any custom type that is editable or interactive, and add `data-inputable="true"` to the input in the edit template — that attribute "is required for accessibility support in the standard cell layout". The full keyboard-mode contract (navigation mode vs action mode, `tabindex={internalTabIndex}`, `data-navigation="enable"`) is owned by `lwc/lwc-accessibility`; read its datatable gotcha before shipping a custom type.

*Grounded:* `data-table-custom-types` L5806; `data-table-custom-types-styling` L6092–L6097; `data-table-custom-types-editable` L6149, L6151.

---

## Overriding `connectedCallback()` In A `LightningDatatable` Subclass Breaks Initialization

**What happens:** A datatable that extends `LightningDatatable` renders wrong or not at all after someone adds an innocuous `connectedCallback`.

**When it occurs:** The subclass defines `connectedCallback()` without calling the parent. Doing so "overrides the parent `connectedCallback()` implementation on the `lightning-datatable` component". Two neighbouring constraints bite here too: you may extend `LightningDatatable` *only* to create custom data types, and a `lightning-datatable` nested inside a custom data type cell is not supported — it leaks styles from the parent table into the child.

**How to avoid:** Run `super.connectedCallback()` as the first statement of any override. Keep the subclass to type registration; put logic in the wrapper component or in a child component the cell template embeds.

*Grounded:* `data-table-custom-types` L5795, L5857–L5859, L5860.

---

## An Apex Save Needs Two Different Refresh Calls, And They Are Not Interchangeable

**What happens:** After a successful inline-edit save through Apex the table still shows the old values, or the table updates but the related lists and highlights panel on the same record page do not.

**When it occurs:** Only one refresh mechanism is used. Lightning Data Service does not manage data provisioned by Apex, so `refreshApex()` is what re-provisions *this component's* wire — and because the write went through Apex rather than LDS, "you must notify Lightning Data Service (LDS) using the `notifyRecordUpdateAvailable(recordIds)` function so that the Lightning Data Service cache and wires are refreshed" for *everything else on the page*. `refreshApex()` also rejects the wrong argument: what you pass "must be an object that was previously emitted by an Apex `@wire`", so a component that destructures `{ data }` in its wired function has thrown away the only valid argument.

**How to avoid:** Wire a *function*, stash the whole provisioned result, and on save `await` the Apex call, then call `notifyRecordUpdateAvailable`, then `await refreshApex(storedResult)`. The guide is explicit that the notify must happen after the Apex update completes — use `async`/`await` or a promise chain, not a fire-and-forget call.

*Grounded:* `apex-wire-method` L7098; `apex-result-caching` L7261, L7264, L7266; `data-table-inline-edit` L5718, L5721.

---

## Custom Data Types Skip Server-Side Validation And Reject `lightning-input-field`

**What happens:** An editable custom-type column accepts values a validation rule would reject, and the error only appears at save. Swapping in `lightning-input-field` to get record-aware validation makes the cell stop working entirely.

**When it occurs:** The edit template is treated as a normal form field. The guide is blunt: "Server-side validation rules aren't supported for custom data types yet", and "`lightning-input-field` … isn't supported for use in a datatable. Use `lightning-input` instead". Only base components with a single input field are supported in an edit template (components like `lightning-input type="datetime"` whose multiple inputs evaluate to one value are also fine).

**How to avoid:** Do client-side validation in the edit template — `lightning-input` validates `step`/`min`/`max` for you, and a child component can expose a `validity()` getter plus `showHelpMessageIfInvalid()` for richer rules — and treat the Apex save as the real gate, surfacing DML errors back into the toast rather than assuming the cell caught them.

*Grounded:* `data-table-custom-types-editable` L6164–L6171.

---

## The Component Is Desktop-Only, Whatever The Page It Sits On

**What happens:** A table that works in Lightning Experience on a laptop renders wrong or not at all in the Salesforce mobile app.

**When it occurs:** The component's `-meta.xml` exposes it to a target that is reachable on mobile. "`lightning-datatable` and `lightning-tree-grid` aren't supported on mobile devices."

**How to avoid:** Treat mobile as a separate design problem — a list of cards, `lightning-record-form`, or a purpose-built layout — rather than as a responsive-CSS problem. Two adjacent limits from the same feature table are worth knowing before you commit: `lightning-tree-grid` supports neither column sorting, nor inline editing, nor infinite scrolling, so "we'll switch to tree-grid later" is not a free move.

*Grounded:* `data-table-vs-tree-grid` L5596–L5600.
