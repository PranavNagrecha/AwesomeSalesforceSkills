# Flow Custom Property Editor Worksheet

Fill this in at step 1 of the Recommended Workflow. Everything below becomes an assertion in
`references/code-examples.md` § 4.

## Component Pairing

| Question | Answer |
|---|---|
| Runtime component | |
| Editor component | |
| Flow target (`lightning__FlowScreen` / `lightning__FlowAction` / Apex invocable) | |
| Registration site (`targetConfig` attribute **or** `@InvocableMethod` modifier) | |
| Module reference (kebab-case, namespaced) | |
| Default property pane insufficient because | |

## Builder Contract

- `configurationEditor` metadata value:
- `inputVariables` used:
- `builderContext` need:
- `validate()` behavior:

## Input Inventory

| Property | `type` in js-meta.xml | `role` | `newValueDataType` on change | Deletable? |
|---|---|---|---|---|
| | | | | |

## Generic sObject Mapping (skip if none)

| Question | Answer |
|---|---|
| `propertyType` name (screen component) | |
| `typeName` string the editor sends | `T` / `T__<input>` / `U__<output>` |
| Object options offered | |
| Where the mapping is persisted | `FlowActionCall.dataTypeMappings` for an action; unverified for a screen component |

## Validation Gate

| Blocking condition | `key` | `errorString` | Which control renders it |
|---|---|---|---|
| | | | |

## Guardrails

- [ ] Runtime and editor responsibilities are separate
- [ ] Metadata hook is correct
- [ ] Value-change event is implemented
- [ ] Builder validation is intentional
- [ ] `bubbles: true` and `composed: true` on every configuration-editor event
- [ ] Clearing an input dispatches `configuration_editor_input_value_deleted`
- [ ] `validate()` returns an array of `{ key, errorString }`, `[]` when valid
- [ ] Every `builderContext` read is guarded
- [ ] CPE bundle carries `apiVersion` + `isExposed` only
- [ ] Packaging decision recorded before the first release (`isExposed` is one-way)
