# Gotchas — LWC Lightning Record Forms

Non-obvious LDS form behaviors that cause real production problems.

---

## Gotcha 1: `field-name` accepts a string but loses validation

```html
<!-- accepted -->
<lightning-input-field field-name="Subject"></lightning-input-field>
<!-- preferred -->
<lightning-input-field field-name={subjectField}></lightning-input-field>
```

The string form silently renders nothing if the field name has a
typo. The schema-import form fails the compile, surfaces FLS
correctly, and refactors safely. Always import.

---

## Gotcha 2: `layout-type` and explicit `fields` are mutually exclusive

`lightning-record-form` accepts either `layout-type` ("Compact" or
"Full") or `fields=[...]`, not both. Setting both is a runtime
error. Pick the one that matches the source-of-truth: layout for
admin-editable forms, fields for fixed-shape forms.

---

## Gotcha 3: `onsubmit` requires `event.preventDefault()` to mutate fields

```js
handleSubmit(event) {
    // missing preventDefault — submits original AND modified
    event.detail.fields.OwnerId = this.defaultOwnerId;
    this.refs.form.submit(event.detail.fields);
}
```

Without `event.preventDefault()`, LDS proceeds with the original
payload. Then `submit(...)` runs a second save with the modified
payload. The user sees a double-save and can race with themselves.

---

## Gotcha 4: `lightning-record-form` does not honor record types implicitly

For multi-record-type objects, the form uses the user's *default*
record type. To force a different one, set the `record-type-id`
attribute. This is a surprise for orgs where Sales and Service
share an object — the form renders the wrong picklist values.

---

## Gotcha 5: FLS enforcement is silent

If the running user lacks Read on a field, the field renders
empty. If they lack Edit, the field renders read-only. There is
no error message, no console warning. To distinguish "no value" from
"no permission", call `getObjectInfo` or `getRecord` and inspect
`fields[X].editable` / `fields[X].readable`.

---

## Gotcha 6: Master-detail required fields fail silently in create mode

A master-detail field is required-by-platform. If you omit it from
the form (or from the layout), the form's submit fails with a
generic "REQUIRED_FIELD_MISSING" — but only on save, not on submit
to the form. Always include the master-detail in the field list.

---

## Gotcha 7: `onerror` does not fire for validation rule failures

Server-side validation rule failures show inline via
`lightning-messages` and do not fire the `onerror` event. Only
DML-level errors (FLS denial post-submit, locking, callout limits)
fire `onerror`. Don't rely on `onerror` for "save failed" UX.

---

## Gotcha 8: Compact density depends on user setting

`density="auto"` follows the user's display density preference
(Setup → Personal Information → Display Density: Comfy or Compact).
If your QA team uses Comfy and prod users use Compact, the same
form looks different. Hard-coding `density="comfy"` removes the
ambiguity.

---

## Gotcha 9: `lightning-record-form` has no `lwc:ref` slot for fields

You cannot programmatically focus or query individual fields
inside `lightning-record-form` — they are encapsulated. To control
focus, switch to `lightning-record-edit-form` and add `lwc:ref`
to the `lightning-input-field` you need.
