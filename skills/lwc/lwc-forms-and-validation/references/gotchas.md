# Gotchas - LWC Forms And Validation

## `setCustomValidity()` Needs `reportValidity()`

**What happens:** A custom error message is assigned, but the field never shows an error to the user.

**When it occurs:** The component sets custom validity text and forgets to call `reportValidity()` as part of the submit or interaction cycle.

**How to avoid:** Treat custom validity as a two-step contract: set the message, then report it.

---

## Validation-Rule Errors Already Carry Structured Detail

**What happens:** A team logs only a generic save failure even though the platform returned specific field errors.

**When it occurs:** `onerror` is handled superficially or ignored on record-edit forms.

**How to avoid:** Inspect `event.detail.output.fieldErrors` and surface or log the resulting detail intentionally.

---

## File Upload Usually Belongs After Record Save

**What happens:** The UX assumes files can upload before the record exists and then struggles to connect attachments correctly.

**When it occurs:** A new-record form tries to collapse record creation and file association into one undefined action.

**How to avoid:** Save the record first, keep the returned ID, then enable file upload as a distinct step.

---

## Duplicate Submit Bugs Hide In Fast UIs

**What happens:** Users click Save twice during latency and create duplicated side effects or confusing error states.

**When it occurs:** The component does not disable the save action while an imperative save is still pending.

**How to avoid:** Gate save actions during submission and clear the pending state only after success or handled failure.
