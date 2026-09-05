---
name: lwc-forms-and-validation
description: "Use when building or reviewing Lightning Web Component form UX, especially the choice between `lightning-record-edit-form` and custom inputs, client-side validation with `reportValidity()`, server-side validation feedback, and file upload flows. NOT for Flow screen design or Apex-only validation logic — use lwc/lwc-lightning-record-forms."
category: lwc
salesforce-version: "Spring '25+'"
well-architected-pillars:
  - User Experience
  - Reliability
tags:
  - lwc-forms
  - lightning-record-edit-form
  - validation
  - report-validity
  - file-upload
triggers:
  - "should i use lightning record edit form or custom inputs"
  - "report validity is not catching errors in lwc"
  - "how do i show validation rule errors in a form"
  - "custom validation messages in lightning input"
  - "file upload with lwc form save flow"
  - "lwc forms isn't working"
  - "block the save when two fields disagree in lwc"
  - "intercept onsubmit and change fields before saving"
  - "show validation rule error next to the field in lwc"
  - "createRecord rejected but the user sees unknown error"
  - "required field saves empty on my custom lwc form"
  - "clear a custom error message after the user fixes the field"
  - "jest test that a form refuses to submit"
  - "show field errors from the server on a record edit form"
inputs:
  - "whether the form uses LDS base components, UI API, or Apex"
  - "which fields need custom layout, conditional logic, or cross-field validation"
  - "whether file upload, multi-step save, or server-side validation must be handled"
outputs:
  - "form architecture recommendation for record-edit-form versus manual inputs"
  - "validation design for client checks, server errors, and submit lifecycle"
  - "review findings for weak form UX, missing error handling, and brittle save logic"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

Use this skill when a form is the center of the component and the team needs to be precise about where validation should live. In LWC, most form bugs come from choosing the wrong abstraction first, then fighting the platform to get labels, validation, and save behavior back under control.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is the form editing a single record that fits Lightning Data Service, or is it a custom workflow that spans records or custom payloads?
- Which validation rules should run in the browser first, and which must remain server-enforced?
- Does the UX need file upload, multi-step save, conditional sections, or custom field layout beyond what `lightning-input-field` gives you?

---

## Questions to Ask Before Configuring

Ask these before writing markup. Each one decides a branch that is expensive to reverse once the
form is built, and each traces to a gotcha in `references/gotchas.md`.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which rules must block the save in the browser, and which are validation rules already on the object?" | `lightning-input-field` doesn't support client-side custom validation at all — a browser-side rule forces a `lightning-input` nested in the form (`data-edit-record`:5513) | The list of controls that must be `lightning-input`, and the ones that stay LDS-wired |
| "Is this object supported by User Interface API, and does it have more than one record type?" | LDS covers custom objects and the standard objects UI API supports (not Task, Event, or custom metadata types — `data-guidelines`:5319, 5357); multiple record types with no default mean the form needs `record-type-id` (`data-considerations`:6362) | Either a supported-object green light, or an early switch to Apex before markup exists |
| "Does anything have to change between the user's click and the record hitting the server?" | Only `onsubmit` can intervene — the guide's instruction is to validate and update the fields inside that handler (`data-edit-record`:5516) | Whether a plain submit button is enough, or the form needs an intercepting handler |
| "What should the user see when a validation rule fires — a toast, a red field, or both?" | `event.detail.message` is generic; `event.detail.output.fieldErrors` names the fields (`data-edit-record`:5509) | The error-presentation contract, and whether `lightning-messages` alone covers it |
| "Does this form create the record, or edit an existing one?" | Create paths cannot pass `recordTypeId` or `allowOnSaveDuplicate` through `createRecord` (`reference-create-record`:15030), and the new Id is not on the submit event (`data-considerations`:6376) | The correct post-save handler and an honest duplicate-handling plan |
| "Who clicks Save twice, and what happens if they do?" | Nothing in LDS de-duplicates the second click; every call is an independent transaction (`data-guidelines`:5347) | A pending-state flag and a disabled Save button, decided rather than retrofitted |
| "Are files part of this, and does the record exist yet when they are chosen?" | File association normally needs a committed record, which splits one click into two steps | A staged save-then-upload sequence instead of an improvised mid-submit branch |

What a proper configuration adds over just building the form: the rules that must block a save actually block it in the browser, the rules that must always hold are still enforced on the server and are shown against the field that failed, and the save path has exactly one owner — so a second click, a validation rule, and a record-type change each produce a predictable outcome instead of a support ticket.

---

## Core Concepts

Form design in LWC starts with an architectural decision, not a validation helper. If the use case fits record editing on a supported object, `lightning-record-edit-form` plus `lightning-input-field` usually gives the safest path because labels, field metadata, CRUD and FLS enforcement, and server-side error handling are already integrated. Custom forms are justified when layout, data shaping, or interaction flow truly exceed that model.

### Record Form Components Solve More Than Rendering

`lightning-record-edit-form` is not just a shortcut for markup. It is a Lightning Data Service boundary that pairs naturally with `lightning-input-field`, submit handlers, success handlers, and server-driven validation display. Teams often replace it too early and then rebuild field wiring, error handling, and save state manually.

### Client Validation And Server Validation Do Different Jobs

Use client validation for fast feedback such as required combinations, formatting, or cross-field checks that can be evaluated locally. Use server validation for business rules that must always hold. In custom inputs, `setCustomValidity()` and `reportValidity()` make the browser surface intentional. In record-edit forms, validation-rule failures arrive through `onerror`, and `event.detail.output.fieldErrors` helps you interpret which fields failed.

### Error Presentation Must Match The Form Model

If the form uses `lightning-record-edit-form`, include `lightning-messages` and let the form surface platform errors in a supported way. If the form is custom, aggregate client checks before submit, disable duplicate saves during pending work, and map server errors back to specific controls or a clear form-level message.

### File Upload Is Usually A Separate Lifecycle

`lightning-file-upload` is powerful, but it changes save design. Files normally attach after a record exists, so the UX often needs a two-step pattern: save the record first, then enable file upload with the record ID. Trying to force upload into the same transaction as every field edit usually creates awkward state handling.

---

## Common Patterns

### Standard Record Form With Supported Error Handling

**When to use:** One record is being edited and the default field components can satisfy the UX.

**How it works:** Use `lightning-record-edit-form`, `lightning-input-field`, and `lightning-messages`, then handle `onsubmit`, `onsuccess`, and `onerror` only for targeted behavior such as toasts, navigation, or analytics.

**Why not the alternative:** Replacing LDS with custom inputs adds avoidable complexity around labels, field metadata, and server error mapping.

### Custom Form With Explicit Validity Sweep

**When to use:** The component needs custom layout, derived fields, cross-object inputs, or custom payload assembly.

**How it works:** Build the form with `lightning-input` and related base components, call `reportValidity()` across the relevant controls before save, and use `setCustomValidity()` only for specific field-level feedback.

**Why not the alternative:** Without an explicit validity pass, the UX becomes inconsistent and users can trigger saves that were already known to be invalid.

### Save Then Upload

**When to use:** The workflow needs both field capture and file attachment.

**How it works:** Create or update the record first, keep the save result, then render or enable `lightning-file-upload` with the final `record-id`.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single-record edit on supported fields | `lightning-record-edit-form` with `lightning-input-field` | The platform handles metadata, labels, and server validation wiring |
| Need custom layout or cross-field browser validation | Custom inputs with explicit `reportValidity()` pass | Greater control justifies manual validation responsibility |
| Need to interpret validation-rule failures | Use `onerror` and inspect `event.detail.output.fieldErrors` | Server-side errors should be surfaced intentionally |
| File upload depends on a new record | Save first, then enable `lightning-file-upload` | Upload usually needs the created record ID |
| Team wants to mix LDS fields and hand-built inputs casually | Choose one form model per save path | Mixed ownership makes state and validation harder to reason about |

---


## Recommended Workflow

1. **Answer the Questions table above**, then settle the form model in one line: LDS-wired
   `lightning-record-edit-form`, hybrid (form plus one or more `lightning-input` controls), or
   fully custom `lightning/uiRecordApi`. Cross-check the component choice against
   `lwc/lwc-lightning-record-forms` — do not re-derive it here.
2. **Build the bundle from `references/code-examples.md`.** Bundle 1 is the hybrid shape
   (`onsubmit` intercept, `setCustomValidity`/`reportValidity`, `onsuccess`/`onerror` with
   `lightning/platformShowToastEvent`); Bundle 2 is the custom `createRecord` shape with a
   field-level error map. Start from `templates/lwc/component-skeleton/` and
   `templates/lwc/patterns/ldsRecordEditForm.html`; copy `templates/lwc/jest.config.js`.
3. **Write the validation sweep before the save call, not after.** Every control gets
   `setCustomValidity(message)` or `setCustomValidity('')`, then `reportValidity()`; a custom form
   also needs the requiredness sweep it no longer gets for free
   (`references/gotchas.md` → "A Custom Form Loses Client-Side Requiredness Entirely").
4. **Wire the failure path.** `lightning-messages` inside the form, an `onerror` handler that reads
   `event.detail.output.fieldErrors`, and — for `createRecord`/`updateRecord` — a `catch` that maps
   the write-error body back onto controls. Fill in `templates/lwc-forms-and-validation-template.md`
   as you go.
5. **Add the Jest tests.** At minimum: one test proving an invalid form does not submit, and one
   proving a server error reaches the user. Use the two suites in `references/code-examples.md` as
   the shape; stub `reportValidity`/`checkValidity` on the base-component stubs.
6. **Run the checker** —
   `python3 skills/lwc/lwc-forms-and-validation/scripts/check_lwc_forms_and_validation.py --manifest-dir force-app/main/default/lwc`
   — then `npx sfdx-lwc-jest`, then the Review Checklist below.
7. **Deploy and verify** with the `package.xml` and the three verification steps at the end of
   `references/code-examples.md` (Setup list, mismatched-field behaviour, SOQL on the saved record).

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] The form model is intentional: record-edit-form or custom inputs, not an accidental mix.
- [ ] Client validation calls `reportValidity()` before save in custom forms.
- [ ] Record-edit forms include `lightning-messages` and handle `onerror` intentionally.
- [ ] Save buttons are guarded against duplicate submission during pending work.
- [ ] Server-side validation errors are mapped to fields or a clear form message.
- [ ] File upload is sequenced around record creation instead of improvised mid-submit.
- [ ] Any `onsubmit` handler that touches the field map calls `event.preventDefault()` first.
- [ ] Every `createRecord`/`updateRecord` call has a `catch` that reads the write-error body shape.
- [ ] The bundle has a `__tests__` suite proving an invalid form does not submit.
- [ ] `scripts/check_lwc_forms_and_validation.py --manifest-dir <lwc source>` reports no errors.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **`lightning-input-field` does not support every custom validation trick** - it is designed to work with LDS and server validation, not to behave like a fully manual input.
2. **`setCustomValidity()` is inert until `reportValidity()` runs** - teams set a message and assume the field will render it automatically.
3. **Validation-rule failures return structured field errors** - if `onerror` is ignored, the team loses useful detail that could improve the UX or support logging.
4. **File upload often needs a committed record ID first** - trying to combine create and upload in one vague click path produces brittle state transitions.
5. **A custom form drops client-side requiredness** - `updateRecord` does not enforce it; you run the `reportValidity()` sweep or the user saves an empty required field (`reference-update-record`:15403).
6. **Read and write errors have different body shapes** - `getRecord` rejects with an array, `createRecord` with an object (`data-error`:6568-6569), so one shared reducer silently degrades to "Unknown error".
7. **`createRecord` accepts neither `recordTypeId` nor a duplicate override** - only `apiName` and `fields` (`reference-create-record`:15028-15030).
8. **The saved record's Id arrives on `success`, never on `submit`** (`data-considerations`:6376).
9. **Display density moves your labels between orgs** - `auto` follows the org setting and `cozy` is not a valid `density` value (`data-display-density`:6329-6331).

Full detail, with the "what happens / when it occurs / how to avoid" breakdown and the UNVERIFIED
markers, is in `references/gotchas.md`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Form architecture decision | Recommendation for record-edit-form versus custom input composition |
| Validation design | Mapping of client checks, server errors, and submit lifecycle handling |
| Review findings | Concrete issues in labels, save sequencing, and error presentation |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/code-examples.md` | You are writing the bundle: hybrid record-edit-form + custom `lightning-input`, custom `createRecord` form with a field-error map, both Jest suites, `js-meta.xml`, `package.xml`, deploy and verification steps |
| `references/gotchas.md` | A form behaves differently from what the markup implies — silent custom rules, missing requiredness, mismatched error shapes, record-type picklists, density shifts |
| `references/llm-anti-patterns.md` | You are reviewing generated form code, or want the detection hints the checker script implements |
| `references/well-architected.md` | You need the pillar framing, the tradeoffs behind the form-model choice, or the sourced claims list |
| `templates/lwc-forms-and-validation-template.md` | You are recording the form-shape decision, validation map, and submit lifecycle for review |
| `scripts/check_lwc_forms_and_validation.py` | Before deploy: run it with `--manifest-dir` over the LWC source tree |

---

## Related Skills

- `lwc/lwc-lightning-record-forms` - use first to choose between `lightning-record-form`, `lightning-record-edit-form`, and `uiRecordApi`; this skill assumes that choice is made.
- `lwc/lwc-lds-writes` - use for the write mechanics themselves: record input shapes, duplicate detection, and cache refresh after a save.
- `lwc/wire-service-patterns` - use when the form issue is really a data loading contract problem.
- `lwc/lwc-accessibility` - use alongside this skill when labels, error messages, and keyboard flow need review.
- `lwc/custom-property-editor-for-flow` - use when the form runs inside Flow Builder design-time surfaces rather than runtime record editing.
