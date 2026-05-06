# Well-Architected Notes — LWC Lightning Record Forms

## Relevant Pillars

- **Operational Excellence** — Lightning Data Service form
  components are the lowest-cost path to a Salesforce-aware form.
  They inherit field labels, help text, FLS, validation, layout
  changes, and translations directly from metadata. Every field a
  developer hand-rolls is a place admins lose declarative
  control. Choosing `lightning-record-form` over a custom form is
  the single largest reduction in LWC maintenance cost in a
  Salesforce org.
- **Security** — Field-level security and object-level CRUD are
  enforced automatically by `lightning-input-field` and
  `lightning-output-field`. A field the user cannot read renders
  empty; a field they cannot edit renders read-only; a record they
  cannot edit hides the Edit button. Hand-rolled forms must
  re-implement this through `getObjectInfo` + manual checks, and
  almost always have gaps.

## Architectural Tradeoffs

The main tradeoff is **declarative agility vs UI control**.
`lightning-record-form` with `layout-type="Full"` puts the page
layout in charge — admins re-arrange fields without a deployment.
`fields=[...]` makes the form fixed-shape, which is what you want
when the form is part of a larger guided flow that cannot tolerate
admin-driven field reorders.

Specifically:

- **Standalone record form on a record page**: `lightning-record-form`
  with `layout-type="Full"`.
- **Side-panel summary**: `lightning-record-view-form` with a
  hand-picked field list.
- **Multi-step wizard with conditional fields**:
  `lightning-record-edit-form` per step, plus `onsubmit` mutation
  for cross-step state.
- **Cross-object orchestration on save**: skip LDS forms; build
  with `lightning-input` + Apex `@AuraEnabled` controller.

## Anti-Patterns

1. **Reinventing the form with `getRecord` + `updateRecord`.**
   Lose FLS, validation UI, and inline-error rendering for no
   benefit.
2. **String-literal `field-name`.** Lose compile-time validation
   and safe refactoring.
3. **Mixing Apex save with `lightning-record-edit-form`.** Fight
   the framework; produce a fragile UX.

## Official Sources Used

- lightning-record-form (LWC Component Reference) — https://developer.salesforce.com/docs/component-library/bundle/lightning-record-form/documentation
- lightning-record-edit-form — https://developer.salesforce.com/docs/component-library/bundle/lightning-record-edit-form/documentation
- lightning-record-view-form — https://developer.salesforce.com/docs/component-library/bundle/lightning-record-view-form/documentation
- Lightning Data Service Overview — https://developer.salesforce.com/docs/platform/lwc/guide/data-ui-api.html
- Importing References from `@salesforce/schema` — https://developer.salesforce.com/docs/platform/lwc/guide/reference-salesforce-modules.html
- Salesforce Well-Architected: Secure — https://architect.salesforce.com/well-architected/trusted/secure
