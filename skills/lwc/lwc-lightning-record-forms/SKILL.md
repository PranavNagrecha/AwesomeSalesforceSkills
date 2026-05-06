---
name: lwc-lightning-record-forms
description: "Lightning Data Service form components for LWC — when to use lightning-record-form vs lightning-record-edit-form vs lightning-record-view-form, output-field vs input-field, density modes, layout types (Compact/Full), and the platform-managed validation/save/error UI. NOT for fully custom form layouts (use lwc/lwc-custom-form-with-uiRecordApi) or aura:recordEditForm (Aura is deprecated for new work)."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Security
triggers:
  - "lightning-record-form lwc create edit view"
  - "lightning-record-edit-form vs record-form lwc"
  - "lightning-input-field lightning-output-field lwc"
  - "lwc form respects field-level security automatically"
  - "lwc form layout type compact full"
  - "record form spinner loading state lwc"
  - "lwc form on success on submit on error events"
tags:
  - lds
  - record-forms
  - field-level-security
  - layout
  - declarative-ui
inputs:
  - "Object API name and (optionally) record Id"
  - "Whether the form is read-only, edit, create, or mode-toggling"
  - "Whether the layout should be Compact, Full, or a hand-picked field list"
outputs:
  - "Choice of lightning-record-form vs lightning-record-edit-form vs lightning-record-view-form"
  - "Template snippet wired to onsuccess / onsubmit / onerror"
  - "Density and layout-type configuration matching org standards"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-05
---

# LWC Lightning Record Forms

Lightning Data Service ships three form base components that
remove the most common reasons developers hand-write forms:
field-level security enforcement, page-layout awareness, automatic
validation, and managed save/error UI. They are
`lightning-record-form` (the all-in-one), `lightning-record-edit-form`
(create/edit with custom layout), and `lightning-record-view-form`
(read-only with custom layout).

The decision is mostly about how much layout control you need.
`lightning-record-form` is one tag, takes an object + optional
record Id + a layout-type, and renders the entire form including
mode toggle, save/cancel buttons, spinner, and inline errors. The
two `-edit-form` and `-view-form` variants give you back the
template — you place `lightning-input-field` / `lightning-output-field`
yourself and own the buttons. Both still leverage LDS for caching,
FLS, and validation.

The mistakes follow a predictable pattern. Engineers reach for a
hand-rolled form with `@wire(getRecord)` and manual DML the moment
they need a single CSS tweak, abandoning every benefit of LDS. Or
they try to mix `lightning-record-edit-form` with custom Apex
`@AuraEnabled` saves, fighting the framework. Or they forget that
`lightning-input-field` requires `field-name` to be a value imported
via `@salesforce/schema/Object.Field`, not a string literal — and
the form silently renders nothing.

## Recommended Workflow

1. **Choose the smallest component that works.** Start with
   `lightning-record-form`. Move to `-edit-form` or `-view-form`
   only when you need a custom layout, custom buttons, or
   conditional fields. Never start with hand-rolled.
2. **Import field references via `@salesforce/schema`.** This
   is what enables compile-time validation, FLS enforcement, and
   safe refactoring. String-literal field names in `field-name`
   are accepted but lose all of the above.
3. **Pick the layout-type deliberately.** `Compact` mirrors the
   compact layout (Salesforce-managed, admin-editable). `Full`
   mirrors the page layout. A `fields=[...]` array is fully
   programmatic — use this when the form's contents must not
   shift when an admin edits the layout.
4. **Wire `onsuccess`, `onsubmit`, and `onerror`.** `onsubmit`
   fires before save, lets you mutate `event.detail.fields` for
   conditional defaults; `onsuccess` fires after, lets you fire a
   toast or navigate. Without `onerror`, validation errors still
   show inline (LDS handles it) but you cannot react
   programmatically.
5. **Set `density="comfy" | "compact" | "auto"` to match the host
   surface.** Default `auto` adapts to the SLDS density flag set
   on the user record — overriding only makes sense when the form
   is on a tightly-scoped page (a modal) where you know which
   layout you want.
6. **Test by simulating LDS in jest.** Use
   `@salesforce/sfdx-lwc-jest` mocks for `getRecord` /
   `createRecord` / `updateRecord`. Do not unit-test the form's
   internal save logic — that is platform code.

## When To Reach For Custom (Skip This Skill)

If you need a wizard with multiple steps, a custom save endpoint
that does cross-object orchestration, or a UI tightly coupled to
non-Salesforce data, do not start with `lightning-record-edit-form`.
Build the form with `lightning-input` components and call your
Apex method directly. The LDS form components are for the case
where Salesforce is the source of truth for one record at a time.

## What This Skill Does Not Cover

| Topic | See instead |
|---|---|
| Fully custom forms with `uiRecordApi` | `lwc/lwc-custom-form-with-uiRecordApi` |
| Custom lookup fields inside a form | `lwc/lwc-custom-lookup` |
| Datatable inline edit | `lwc/lwc-datatable-advanced` |
| Aura `lightning:recordEditForm` | Aura is deprecated for new work |
