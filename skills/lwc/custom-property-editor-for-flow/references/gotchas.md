# Gotchas - Custom Property Editor For Flow

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Metadata Registration Is The Real Entry Point

**What happens:** The editor component exists, but Flow Builder never uses it.

**When it occurs:** The `configurationEditor` metadata hookup is missing or wrong.

**How to avoid:** Treat metadata registration as part of the feature, not as packaging trivia.

---

## Gotcha 2: Builder APIs Are Not Runtime State

**What happens:** Developers try to use builder-specific properties like normal runtime component inputs.

**When it occurs:** The boundary between the editor and the runtime component was not kept clear.

**How to avoid:** Keep `inputVariables`, `builderContext`, and `validate()` scoped to the editor contract.

---

## Gotcha 3: UI Changes Without Event Dispatch Are Lost

**What happens:** The editor appears to change values, but Flow Builder does not persist them.

**When it occurs:** The editor forgets to dispatch the configuration-editor change event.

**How to avoid:** Validate the editor by proving a user change updates the builder model, not just the DOM.
