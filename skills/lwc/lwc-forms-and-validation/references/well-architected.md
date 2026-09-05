# Well-Architected Notes - LWC Forms And Validation

## Relevant Pillars

### User Experience

Forms are where Salesforce users feel friction immediately. Correct labels, predictable validation timing, and understandable save behavior reduce abandonment and support noise.

### Reliability

Reliable forms separate browser checks from server-enforced rules and keep save sequencing deterministic. A fragile submit path creates duplicate records, silent failures, or inconsistent field state.

## Architectural Tradeoffs

- **Supported LDS forms vs custom UI freedom:** record-edit-form gives a safer default, while custom forms justify themselves only when the UX cannot fit the supported model.
- **Immediate client validation vs minimal interruption:** fast feedback is valuable, but too many premature errors create noisy forms.
- **One-click everything vs staged save and upload:** combining record save and file handling feels simpler at first, but staged flows are usually easier to reason about.

## Anti-Patterns

1. **Manual forms for standard CRUD only** - the team gives up built-in behavior without a real UX reason.
2. **Custom messages without validity reporting** - the validation logic exists in code but never appears to the user.
3. **Mixed form ownership models** - record-edit and manual inputs compete for control of one save path.

## Official Sources Used

Lightning Web Components Developer Guide pages, read as extracted text
(`/scratchpad/lwc_guide.txt`); line numbers cite that extraction.

- Edit a Record — https://developer.salesforce.com/docs/platform/lwc/guide/data-edit-record.html (`lightning-input-field` does not support client-side custom validation and `lightning-input` must be nested and hand-wired instead, lines 5513–5518; `event.detail.output.fieldErrors` carries validation-rule detail, 5509–5510; `lightning-messages` placement, 5489; the four form events, 5501–5504; `reset()` for a Cancel button, 5490–5492 — supports "Client Validation And Server Validation Do Different Jobs" and the hybrid bundle in `references/code-examples.md`)
- Create a Record — https://developer.salesforce.com/docs/platform/lwc/guide/data-create-record.html (omit `record-id` to create; `value` on `lightning-input-field` to prefill, line 5533 — supports the create-versus-edit branch in the Questions table)
- Build Custom UI to Create and Edit Records — https://developer.salesforce.com/docs/platform/lwc/guide/data-salesforce-write.html (when the `lightning-record*form` components are not enough, use the imperative `lightning/uiRecordApi` functions, lines 5550–5558 — supports the "Supported LDS forms vs custom UI freedom" tradeoff)
- Handle Errors in Lightning Data Service — https://developer.salesforce.com/docs/platform/lwc/guide/data-error.html (UI API read errors return `error.body` as an array, write errors as an object often carrying object-level and field-level errors, lines 6567–6571; `ok`/`status`/`statusText`, 6549–6551 — supports "Error Presentation Must Match The Form Model" and the write-error gotcha)
- `updateRecord(recordInput, clientOptions)` — https://developer.salesforce.com/docs/platform/lwc/guide/reference-update-record.html (requiredness is not enforced client-side on a custom form and `reportValidity()` is what displays field-level errors, line 15403; the `reportValidity()`/`checkValidity()` reduce, 15405–15410; `allowSaveOnDuplicate` and `ifUnmodifiedSince`, 15388–15396 — supports the requiredness gotcha and the Reliability pillar note)
- `createRecord(recordInput)` — https://developer.salesforce.com/docs/platform/lwc/guide/reference-create-record.html (`recordInput` is `apiName` + `fields` only; `allowOnSaveDuplicate` and `recordTypeId` are not supported, lines 15028–15030 — supports Bundle 2 and the duplicate-handling answer in the Questions table)
- Data Guidelines — https://developer.salesforce.com/docs/platform/lwc/guide/data-guidelines.html (LDS object coverage and the custom-metadata-type exclusion, line 5319; Task and Event need Apex, 5357; each `createRecord`/`updateRecord` call is an independent transaction, 5347 — supports the duplicate-submit gotcha and the supported-object question)
- Lightning Data Service — https://developer.salesforce.com/docs/platform/lwc/guide/data-ui-api.html (UI API responses respect CRUD access, field-level security, and sharing, line 5393 — supports the Security-adjacent argument for staying on LDS in "Manual forms for standard CRUD only")
- Usage Considerations for Working with Records — https://developer.salesforce.com/docs/platform/lwc/guide/data-considerations.html (record-type Id is required when an object has multiple record types and no default, line 6362; the new record's Id is not on the submit event, 6376 — supports the record-type and post-save questions)
- `getPicklistValues` — https://developer.salesforce.com/docs/platform/lwc/guide/reference-wire-adapters-picklist-values.html (both `recordTypeId` and `fieldApiName` are required; master record type `012000000000000AAA`; `objectApiName` unsupported, lines 14949–14960 — supports the picklist wiring in Bundle 2)
- Write Jest Tests — https://developer.salesforce.com/docs/platform/lwc/guide/unit-testing-using-jest-create-tests.html (`__tests__` folder and `.test.js` naming, lines 12328–12331; `element.shadowRoot` as the test-only API, 12379; return a resolved Promise to wait for asynchronous rerenders, 12494–12506 — supports both Jest suites)
- Change the Form Display Density — https://developer.salesforce.com/docs/platform/lwc/guide/data-display-density.html (`density` accepts `auto`/`compact`/`comfy` but not `cozy`; `lightning-input-field` variants, lines 6329–6343 — supports the density gotcha and the User Experience pillar)
