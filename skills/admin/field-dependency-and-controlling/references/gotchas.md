# Gotchas — Field Dependency and Controlling

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Field-Level Security on the Controlling Field Empties `controllerValues` for That User

**What happens:** A custom LWC builds its dependent combobox from the UI API `getPicklistValues` payload. For most users it works. For one profile it renders an empty dropdown — or every value at once, depending on how the component treats a missing map. The User Interface API guide states the rule directly: "If the controlling field is protected by field-level security (FLS), it doesn't appear in the controllerValues property."

**When it occurs:** Any profile or permission set where the controlling field is Hidden or Read-Only-and-hidden-from-layout while the dependent field remains visible. Extremely common when a controlling field carries pricing, segmentation, or internal-classification data that is deliberately withheld from partner or community users — exactly the users who then cannot pick a dependent value.

**How to avoid:** Treat an empty `controllerValues` map as a real state, not an error: fall back to the unfiltered `values` list, or hide the dependent field entirely, rather than rendering an empty picklist with no explanation. When designing the FLS matrix, check every dependent picklist's controlling field alongside it — if the dependent field is visible to a profile, the controlling field must be too. This is a permission-design decision, not a component bug.

---

## Gotcha 2: `controllerValues` Only Describes the *Immediate* Controller

**What happens:** In a three-level chain (Region controls Country controls City), a single `getPicklistValues` call for City returns a map of Country values, not Region values. The Picklist Values response defines it as "a map of its immediate controlling field's picklist values to their indexes." Code that assumes one call describes the whole chain resolves City against the wrong index set and shows cities from the wrong country.

**When it occurs:** Any cascade deeper than two levels. It is invisible in a two-level test because there the immediate controller *is* the whole chain.

**How to avoid:** One wire call per level in the chain, each rebuilding its own index map from its own `controllerValues`. Wire the components so selecting a value at level N clears the selections at N+1 and below — Salesforce does not cascade the clear for you, and a stale level-3 value survives a level-1 change.

---

## Gotcha 3: `validFor` Is Empty on Independent Picklists, Not "Valid For Nothing"

**What happens:** A generic picklist component filters options with `value.validFor.includes(controllerIndex)`. Pointed at a dependent picklist it works. Pointed at an ordinary independent picklist every option disappears, because the Picklist Value response specifies: "If the picklist is a dependent picklist, the property contains a list of the controlling value indexes for which this value is valid. If the picklist is an independent picklist, the list is empty."

**When it occurs:** The first time the reusable component is put on a second field. It is a silent empty dropdown, not an exception, so it usually ships.

**How to avoid:** Branch on whether `controllerValues` is a non-empty map before filtering at all. If it is empty, render `values` as-is. `validFor` is an Integer array of indexes into `controllerValues` — never compare it against the controlling field's string value.

---

## Gotcha 4: `valueSettings` Is an Allow-List — Omitted Pairs Are Disabled, Not Preserved

**What happens:** An admin adds one new dependent value by deploying a `valueSettings` block containing only that pair. Every other pair in the matrix is switched off, because the deployed `valueSettings` collection replaces the matrix rather than merging into it. Users see a picklist that has lost most of its options and no error was raised.

**When it occurs:** Hand-authored partial metadata, or a source-control workflow where only the changed lines were staged. Also after a merge conflict resolution that dropped `valueSettings` elements.

**How to avoid:** Always deploy the complete matrix. In Metadata API terms, `ValueSettings.controllingFieldValue` is a string array — "Applies only to dependent custom picklists. A list of values in the controlling or parent picklist" — and `valueName` "Defines the values in the custom dependent picklist." So the natural shape is one `valueSettings` block per dependent value, listing every controlling value that enables it. Retrieve the field before editing, never assemble the block from scratch, and diff the deployed pair count against the retrieved one.

---

## Gotcha 5: `restricted` Governs Which Values Exist, Not Which Combinations Are Legal

**What happens:** A team marks the dependent picklist's value set `restricted` and assumes bad controlling/dependent combinations are now blocked. They are not. `restricted` is defined as "Whether the picklist's values are limited to only the values defined by a Salesforce admin" — it constrains membership in the value list, and says nothing about which controlling value a given member may accompany. A load can still write a legal value paired with the wrong controller.

**When it occurs:** Data loads, integrations, and Apex DML — any path that sets both fields without going through a Lightning form. The record saves and then displays oddly in the UI, where the dependency filter hides the stored value.

**How to avoid:** Enforce combinations with an explicit rule (a validation rule or a before-save automation) and treat `restricted` as a separate, complementary control that stops free-text values appearing. Also note the ceiling if you are consolidating onto a Global Value Set: "A global value set can have up to 1,000 total values, including inactive values," and the dependency itself is not defined on the GVS — the `controllingField` and `valueSettings` live on each field's own `ValueSet`, because "The global value set is inherited by any custom picklist field that uses that value set." Two fields sharing one GVS still need two separate dependency matrices.
