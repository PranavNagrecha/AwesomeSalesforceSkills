---
name: lwc-forms-and-validation
description: "Use when building or reviewing Lightning Web Component form UX, especially the choice between `lightning-record-edit-form` and custom inputs, client-side validation with `reportValidity()`, server-side validation feedback, and file upload flows. Triggers: 'record edit form in lwc', 'reportValidity not working', 'custom validation message', 'fieldErrors in onerror'. NOT for Flow screen design or Apex-only validation logic."
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
inputs:
  - "whether the form uses LDS base components, UI API, or Apex"
  - "which fields need custom layout, conditional logic, or cross-field validation"
  - "whether file upload, multi-step save, or server-side validation must be handled"
outputs:
  - "form architecture recommendation for record-edit-form versus manual inputs"
  - "validation design for client checks, server errors, and submit lifecycle"
  - "review findings for weak form UX, missing error handling, and brittle save logic"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-15
---

Use this skill when a form is the center of the component and the team needs to be precise about where validation should live. In LWC, most form bugs come from choosing the wrong abstraction first, then fighting the platform to get labels, validation, and save behavior back under control.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is the form editing a single record that fits Lightning Data Service, or is it a custom workflow that spans records or custom payloads?
- Which validation rules should run in the browser first, and which must remain server-enforced?
- Does the UX need file upload, multi-step save, conditional sections, or custom field layout beyond what `lightning-input-field` gives you?

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

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] The form model is intentional: record-edit-form or custom inputs, not an accidental mix.
- [ ] Client validation calls `reportValidity()` before save in custom forms.
- [ ] Record-edit forms include `lightning-messages` and handle `onerror` intentionally.
- [ ] Save buttons are guarded against duplicate submission during pending work.
- [ ] Server-side validation errors are mapped to fields or a clear form message.
- [ ] File upload is sequenced around record creation instead of improvised mid-submit.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **`lightning-input-field` does not support every custom validation trick** - it is designed to work with LDS and server validation, not to behave like a fully manual input.
2. **`setCustomValidity()` is inert until `reportValidity()` runs** - teams set a message and assume the field will render it automatically.
3. **Validation-rule failures return structured field errors** - if `onerror` is ignored, the team loses useful detail that could improve the UX or support logging.
4. **File upload often needs a committed record ID first** - trying to combine create and upload in one vague click path produces brittle state transitions.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Form architecture decision | Recommendation for record-edit-form versus custom input composition |
| Validation design | Mapping of client checks, server errors, and submit lifecycle handling |
| Review findings | Concrete issues in labels, save sequencing, and error presentation |

---

## Related Skills

- `lwc/wire-service-patterns` - use when the form issue is really a data loading contract problem.
- `lwc/lwc-accessibility` - use alongside this skill when labels, error messages, and keyboard flow need review.
- `lwc/custom-property-editor-for-flow` - use when the form runs inside Flow Builder design-time surfaces rather than runtime record editing.
