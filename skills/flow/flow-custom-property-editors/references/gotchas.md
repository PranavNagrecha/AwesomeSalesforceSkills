# Gotchas — Flow Custom Property Editors

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Builder-Only Success Can Hide Runtime Drift

**What happens:** The editor looks correct in Flow Builder, but the runtime component fails because field names or assumptions have drifted.

**When it occurs:** Teams update the component API without updating the metadata or editor logic.

**How to avoid:** Review design-time and runtime contracts together during every change.

---

## Missing Change Events Make The Editor Look Alive But Do Nothing

**What happens:** The editor UI responds to clicks and text entry, but Flow Builder does not persist the values.

**When it occurs:** The editor does not dispatch one of the documented `configuration_editor_input_value_changed`, `configuration_editor_input_value_deleted` or `configuration_editor_generic_type_mapping_changed` events with `bubbles` and `composed` true, or its `detail` lacks `name`, `newValue` and `newValueDataType` (lwcguide use-flow-custom-property-editor-interface).

**How to avoid:** Test that Flow Builder saves and reopens the configured values, not just that the editor renders.

---

## Overbuilding The Editor Hurts Admin Maintainability

**What happens:** The editor becomes a miniature application with complex state, remote calls, and hard-to-debug builder logic.

**When it occurs:** Teams use a custom editor for problems the default Flow property pane could already solve.

**How to avoid:** Build the smallest editor that materially improves the admin experience.
