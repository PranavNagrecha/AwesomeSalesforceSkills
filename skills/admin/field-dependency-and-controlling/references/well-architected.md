# Well-Architected Notes — Field Dependency And Controlling

## Relevant Pillars

### Operational Excellence

The dependency matrix is metadata, and its failure mode is omission rather than error. `valueSettings` is an allow-list: a partial deploy disables every pair it does not mention, and nothing in the deploy result says so. Operationally excellent teams retrieve the field before editing it, deploy the complete matrix as one unit, and diff enabled-pair counts between source and target as a release check — the same discipline applied to any allow-list configuration.

### User Experience

Dependent picklists exist to reduce the choice a user has to make. They fail the pillar in two directions: too little filtering (an unenforced matrix, so users pick combinations the business does not recognise) and too much (an empty dropdown with no explanation, which is what a hidden controlling field produces). Both look like a broken form to the person using it. The design goal is that a user always sees either a valid, filtered list or a clear reason there is none.

### Security

The controlling field is a security surface, not just an input. "If the controlling field is protected by field-level security (FLS), it doesn't appear in the controllerValues property" — so hiding a controlling field for a profile silently removes that profile's ability to use the dependent field. Withholding a classification, pricing tier, or internal-segment field from partner users is a legitimate security decision, but it has to be made in the same review as the dependency, or the access design and the form design contradict each other in production.

## Architectural Tradeoffs

**Dependency matrix vs. two flat picklists and a rule.** The matrix filters at the point of entry and needs no runtime logic, but it is per-field metadata that must be redeployed whenever values change. Two independent picklists plus a validation rule express the same constraint in one place and enforce it on every write path, at the cost of letting the user make the mistake before being told. Most orgs need both: the matrix for the UI, the rule for everything else.

**Depth vs. debuggability.** Each additional cascade level is another wire call, another index map, and another selection your code must clear when an ancestor changes. Two levels is cheap. Three is the point at which a custom component needs deliberate state management. Beyond that, a lookup to a reference object usually models the hierarchy better than a chain of picklists.

**Shared Global Value Set vs. per-field value sets.** A GVS keeps values consistent across objects and is capped at 1,000 total values including inactive ones. It does not carry the dependency: `controllingField` and `valueSettings` live on each field's own `ValueSet`, so two fields sharing a GVS still need two independently maintained matrices. Sharing values does not mean sharing behaviour.

## Anti-Patterns

1. **Deploying a partial `valueSettings` collection.** Adding one pair by deploying only that pair disables the rest of the matrix. The pattern looks like a minimal diff and behaves like a wipe. Always deploy the full matrix retrieved from the source org.

2. **Treating `restricted` as combination enforcement.** `restricted` limits "the picklist's values ... to only the values defined by a Salesforce admin" — membership, not pairing. A load can still write a legal value against the wrong controller. Combination enforcement needs an explicit rule.

3. **Building a dependent picklist component that ignores the empty-map case.** An independent picklist and an FLS-hidden controller both yield an empty `controllerValues`, and an independent picklist's `validFor` is an empty list. A component that filters unconditionally renders nothing and reports no error, which is the hardest class of bug to get a user to describe accurately.

## Official Sources Used

- User Interface API — Build UI for Picklists — FLS hides the controlling field from `controllerValues`; a controlling field can be a picklist or a checkbox; `validFor` indexes map to `controllerValues` (verified 2026-08-14) — https://developer.salesforce.com/docs/atlas.en-us.uiapi.meta/uiapi/ui_api_features_records_dependent_picklist.htm
- User Interface API — Picklist Values response body — `controllerValues` is a map of the *immediate* controlling field's values to their indexes (verified 2026-08-14) — https://developer.salesforce.com/docs/atlas.en-us.uiapi.meta/uiapi/ui_api_responses_picklist_values.htm
- User Interface API — Picklist Value response body — `validFor` is an Integer array, empty on independent picklists (verified 2026-08-14) — https://developer.salesforce.com/docs/atlas.en-us.uiapi.meta/uiapi/ui_api_responses_picklist_value.htm
- Metadata API — Metadata Field Types — `ValueSet.controllingField`, `ValueSet.restricted`, `ValueSettings.controllingFieldValue` (string array) and `valueName` (verified 2026-08-14) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_field_types.htm
- Metadata API — `GlobalValueSet` — 1,000-value ceiling including inactive values; the value set is inherited by fields that use it (verified 2026-08-14) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_globalvalueset.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
