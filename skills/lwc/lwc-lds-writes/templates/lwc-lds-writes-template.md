# LWC LDS Writes — Work Template

Use this template when implementing or reviewing an LWC that writes records via Lightning Data Service.

## Scope

**Skill:** `lwc/lwc-lds-writes`

**Request summary:** _(fill in what the user asked for — e.g. "Save Case button on a custom panel" or "wizard step that updates Opportunity")_

## Context Gathered

| Question | Answer |
|---|---|
| Operation | create / update / delete |
| sObject | _(API name)_ |
| Cardinality | single record / multi-record |
| User-initiated? | yes / no |
| Form vs imperative fit | record-edit-form / imperative |
| Same-component getRecord wires? | yes / no |
| Cross-component readers of same recordId? | yes / no |
| Sharing/CRUD/FLS posture | enforce in user context / requires `without sharing` |

## Approach

Tick whichever applies; only one should:

- [ ] `lightning-record-edit-form` — layout-driven, default choice for single-record edit
- [ ] `lightning-record-form` — dynamic field list from layout, no save customization
- [ ] imperative `updateRecord` / `createRecord` / `deleteRecord` — non-standard UX
- [ ] **Apex DML** — bulk, transactional, or `without sharing` required (this skill is the wrong fit; switch to `apex/dml-patterns`)

## `recordInput` Shape Check

For `createRecord`:

```javascript
{ apiName: <objectApiName>, fields: { /* string API names */ } }
```

For `updateRecord`:

```javascript
{ fields: { Id: <recordId>, /* string API names */ } }
```

Check:

- [ ] `apiName` only on create
- [ ] `Id` inside `fields` for update
- [ ] Computed keys use `.fieldApiName`, not the import object
- [ ] No read-only / formula fields in `fields`

## Error Handling

- [ ] Catch reads `err.body.output.fieldErrors` and binds to inputs
- [ ] Catch reads `err.body.output.errors` and surfaces as toast or summary
- [ ] No `err.message` / `err.toString()` rendered to the user

## Refresh Strategy

- [ ] Same-component `@wire(getRecord)` — relies on auto-refresh (document this)
- [ ] Cross-component readers — `notifyRecordUpdateAvailable([{ recordId }])` after success
- [ ] Apex-backed wires elsewhere — `refreshApex(wiredResult)` after success
- [ ] `getRecords` plural / GraphQL / no wire — appropriate refresh primitive named

## Tests

- [ ] Jest mocks `createRecord` / `updateRecord` / `deleteRecord` from `lightning/uiRecordApi`
- [ ] Asserts `recordInput` shape passed to the LDS call
- [ ] Asserts error-path UX renders field errors next to the right input
- [ ] Asserts post-write refresh primitive is called

## Notes

_Record any deviations, e.g. "switched to Apex DML because bulk save was required"._
