# Gotchas - LWC Forms And Validation

Grounded against the Lightning Web Components Developer Guide
(`/scratchpad/lwc_guide.txt`), cited as `<page-slug>:<line>`. Attribute-level facts that live
only in the Component Library are marked UNVERIFIED where they appear.

## `setCustomValidity()` Needs `reportValidity()`

**What happens:** A custom error message is assigned, but the field never shows an error to the user.

**When it occurs:** The component sets custom validity text and forgets to call `reportValidity()` as part of the submit or interaction cycle.

**How to avoid:** Treat custom validity as a two-step contract: set the message, then report it. The guide's own flow-screen example runs `setCustomValidity(msg)` / `setCustomValidity('')` and then a single `reportValidity()` on the way out (`lwc_guide`:9206–9214), and `reference-update-record`:15403 states plainly that to display field-level errors on invalid fields you call `reportValidity()`.

---

## Validation-Rule Errors Already Carry Structured Detail

**What happens:** A team logs only a generic save failure even though the platform returned specific field errors.

**When it occurs:** `onerror` is handled superficially or ignored on record-edit forms.

**How to avoid:** `event.detail.message` is only the general description; field-specific errors, such as a validation-rule failure, arrive as `event.detail.output.fieldErrors` — a list of fields and record exception errors (`data-edit-record`:5509–5510). Read both, and prefer the field map when it is populated.

---

## File Upload Usually Belongs After Record Save

**What happens:** The UX assumes files can upload before the record exists and then struggles to connect attachments correctly.

**When it occurs:** A new-record form tries to collapse record creation and file association into one undefined action.

**How to avoid:** Save the record first, keep the returned ID, then enable file upload as a distinct step. The guide points `input type="file"` users at `lightning-file-upload` specifically to *upload a file and associate it with a record* (`base-components-all`:4611). UNVERIFIED (2026-09-05): that `lightning-file-upload` requires a `record-id` is a Component Library attribute fact; the Developer Guide does not state it.

---

## Duplicate Submit Bugs Hide In Fast UIs

**What happens:** Users click Save twice during latency and create duplicated side effects or confusing error states.

**When it occurs:** The component does not disable the save action while an imperative save is still pending.

**How to avoid:** Gate save actions during submission and clear the pending state only after success or handled failure. Nothing in LDS de-duplicates a second user click: `createRecord` and `updateRecord` are ordinary imperative functions, and each call is an independent transaction (`data-guidelines`:5347).

---

## `lightning-input-field` Cannot Carry A Client-Side Custom Rule At All

**What happens:** An agent adds `setCustomValidity()` handling to a `lightning-input-field` and the rule silently never fires — no error, no message, no blocked save.

**When it occurs:** A cross-field or format rule is bolted onto an otherwise standard record-edit form, because the field is already on screen and looks like an input.

**How to avoid:** The guide is explicit: `lightning-input-field` doesn't support client-side custom validation, and if you want your own client-side validation you nest a `lightning-input` inside the `lightning-record-edit-form` instead (`data-edit-record`:5513). That swap is not free — wiring that is automatic for `lightning-input-field` is not automatic for `lightning-input`, so you supply the value (via `getRecord`) and the label yourself, and fold the value back into the submitted fields in the `onsubmit` handler (`data-edit-record`:5516). Make the swap only when validation-rule errors genuinely don't meet the requirement (`data-edit-record`:5518).

---

## A Custom Form Loses Client-Side Requiredness Entirely

**What happens:** A hand-built `updateRecord` form lets the user save with a required field empty, and the failure comes back from the server as a generic error instead of a red field.

**When it occurs:** A team moves off the `lightning-record*form` components for layout freedom and assumes the `required` attribute alone still enforces the schema.

**How to avoid:** With `updateRecord`, requiredness is not enforced on the client side; to display field-level errors on invalid fields you must call `reportValidity()` yourself (`reference-update-record`:15403). The `lightning-record-*-form` components handle requiredness on the client automatically — that is one of the things you give up (`reference-update-record`:15404). The guide's own pattern is a reduce over the inputs calling `reportValidity()` then `checkValidity()` per control (`reference-update-record`:15405–15410). UNVERIFIED (2026-09-05): that `checkValidity()` returns validity *without rendering* a message, while `reportValidity()` renders it, is HTML constraint-validation / Component Library behaviour; the Developer Guide shows both being called together but never contrasts them.

---

## A Write Error Body Is An Object; A Read Error Body Is An Array

**What happens:** The error reducer copied from a `getRecord` wire handler returns `undefined` (or throws) when the same component handles a `createRecord` rejection, so the user sees "Unknown error" for a perfectly specific server message.

**When it occurs:** One shared `reduceErrors()` helper is written against the read shape and reused for saves.

**How to avoid:** UI API read operations, such as the `getRecord` wire adapter, return `error.body` as an **array** of objects; UI API write operations, such as `createRecord`, return `error.body` as an **object**, often with object-level and field-level errors; Apex and network errors also return objects (`data-error`:6567–6571). Branch on `Array.isArray(error.body)` before reading `.message`. UNVERIFIED (2026-09-05): the specific key names inside a write-error body (`output.fieldErrors`, `output.errors`) are documented for the record-edit-form `onerror` detail (`data-edit-record`:5509) but not restated for the `createRecord` rejection — probe defensively and keep `error.body.message` as the fallback.

---

## `createRecord` Silently Ignores Record Type And Duplicate Overrides

**What happens:** A custom create form on a multi-record-type object saves records onto the wrong record type, or a duplicate-rule alert cannot be bypassed no matter what flag the code passes.

**When it occurs:** An agent ports an `updateRecord` call to `createRecord` and carries the client options across, or assumes `recordTypeId` works the same way it does on the form components.

**How to avoid:** `createRecord`'s `recordInput` takes exactly two properties, `apiName` and `fields` — passing in `allowOnSaveDuplicate` or `recordTypeId` isn't currently supported, and the guide's stated remedy for duplicates is a duplicate rule with a matching rule (`reference-create-record`:15028–15030). `updateRecord` is the one that accepts `allowSaveOnDuplicate` (default `false`), `useDefaultRule`, `triggerUserEmail`, and a `clientOptions` `ifUnmodifiedSince` conflict check (`reference-update-record`:15388–15396). If the create genuinely needs a record type, that is an argument for `lightning-record-edit-form` with `record-type-id`, not for a custom form.

---

## Picklists Are Scoped To A Record Type, And The Form Won't Guess

**What happens:** A create form shows every picklist value in the org, or shows none, on an object with more than one record type.

**When it occurs:** `record-type-id` is omitted on the form, or `getPicklistValues` is wired with only a `fieldApiName`.

**How to avoid:** With `lightning-record-form` or `lightning-record-edit-form`, you must provide a record type Id when the object has multiple record types and there is no default; otherwise the default record type Id is used (`data-considerations`:6362). For a custom form, `getPicklistValues` requires **both** `recordTypeId` and `fieldApiName`; take the Id from `getObjectInfo`'s `defaultRecordTypeId`, which is the master record type `012000000000000AAA` when no default exists, and note that passing `objectApiName` to this adapter isn't supported (`reference-wire-adapters-picklist-values`:14949–14960).

---

## The New Record's Id Is Not On The Submit Event

**What happens:** A wrapper component wired to `onsubmit` dispatches a "record created" event with an undefined Id, and downstream navigation lands nowhere.

**When it occurs:** The team handles `onsubmit` because it is the handler they already added for validation, and reuses it for post-save behaviour.

**How to avoid:** The Id is not available on the submit event — use the success event to return the Id (`data-considerations`:6376). The form fires four distinct events for four distinct jobs: `load` when record data loads, `submit` on submission, `success` on a good save, `error` on a server-side error (`data-edit-record`:5501–5504).

---

## Density And Variant Move Labels Without Touching Your Markup

**What happens:** A form reviewed as accessible in one org renders with labels beside the fields in another, breaking a layout that assumed stacked labels — and no code changed.

**When it occurs:** The org's Density Setting differs between the sandbox and production, or a user picks their own density from the profile menu.

**How to avoid:** The `lightning-record*form` components adapt to the org's display density by default, or when you set `density="auto"`; `density="compact"` or `density="comfy"` overrides it, and `cozy` is **not** a supported value for the attribute (`data-display-density`:6329–6331). Admins can't override a user's chosen density (`data-display-density`:6350). For a single field, `lightning-input-field` accepts the variants `standard`, `label-hidden`, `label-inline`, and `label-stacked` (`data-display-density`:6343). Pin the density explicitly when the layout depends on label position, and see `lwc/lwc-accessibility` for what a hidden label costs.

---

## Not Every Object Reaches These Components At All

**What happens:** A form is built for Task or Event, or for a custom metadata type, and the component renders empty or errors at runtime with no obvious cause.

**When it occurs:** The object was chosen from a requirements document rather than checked against UI API support.

**How to avoid:** Lightning Data Service supports all custom objects and the standard objects that User Interface API supports; custom metadata types are not supported (`data-guidelines`:5319, `data-ui-api`:5379). The guide names Task and Event as objects that are not supported by UI API and for which you use Apex instead (`data-guidelines`:5357). The same page notes UI API responses respect CRUD access, field-level security, and sharing (`data-ui-api`:5393) — so a field that "disappears" from a working form is usually FLS, not a bug in the component.
