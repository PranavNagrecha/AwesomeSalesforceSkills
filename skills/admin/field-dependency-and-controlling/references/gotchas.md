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

## Gotcha 4: A Deploy Can Add Dependency Pairs but Can Never Remove One

**What happens:** A team narrows a matrix by deleting `valueSettings` blocks from the field's XML and
deploying. The deploy succeeds, the diff looks clean, source control says the pair is gone — and the pair is
still enabled in the org. Users go on selecting the combination the team believed it had retired, and the
next `sf project retrieve` quietly puts the deleted blocks back into the file.

**When it occurs:** Every attempt to shrink an existing matrix through metadata, in every org, on every API
version. The Metadata API Developer Guide states the asymmetry twice in the same page — once on
`ValueSet.valueSettings` and again on `ValueSettings.controllingFieldValue`: "You can add field dependency
values via the Metadata API but not remove them" (api_meta.txt:45855–45858 and 45873–45875). Deploying is
additive here; it is not a replace.

**How to avoid:** Treat the matrix as append-only from source control and get it right before the first
deploy. To actually disable a pair, do it in Setup — Object Manager → the object → Fields & Relationships →
the dependent field → **Field Dependencies** → Edit — then re-retrieve so source matches the org. Never
report "removed the mapping" on the strength of a green deploy; verify in the Field Dependencies grid or
against the UI API `validFor` payload. Note the inverse trap in Gotcha 8: omitting a *value* is destructive
where omitting a *pair* is inert.

> Correction (2026-09-05): an earlier revision of this file claimed `valueSettings` was an allow-list whose
> omitted pairs get disabled. The guide says the opposite. If you have downstream notes repeating the
> allow-list framing, they are wrong for pairs — though correct for picklist *values* (Gotcha 8).

---

## Gotcha 5: `restricted` Governs Which Values Exist, Not Which Combinations Are Legal

**What happens:** A team marks the dependent picklist's value set `restricted` and assumes bad controlling/dependent combinations are now blocked. They are not. `restricted` is defined as "Whether the picklist's values are limited to only the values defined by a Salesforce admin" — it constrains membership in the value list, and says nothing about which controlling value a given member may accompany. A load can still write a legal value paired with the wrong controller.

**When it occurs:** Data loads, integrations, and Apex DML — any path that sets both fields without going through a Lightning form. The record saves and then displays oddly in the UI, where the dependency filter hides the stored value.

**How to avoid:** Enforce combinations with an explicit rule (a validation rule or a before-save automation) and treat `restricted` as a separate, complementary control that stops free-text values appearing. Also note the ceiling if you are consolidating onto a Global Value Set: "A global value set can have up to 1,000 total values, including inactive values," and the dependency itself is not defined on the GVS — the `controllingField` and `valueSettings` live on each field's own `ValueSet`, because "The global value set is inherited by any custom picklist field that uses that value set." Two fields sharing one GVS still need two separate dependency matrices.

---

## Gotcha 6: The Dependency Filter Is Browser JavaScript, and It Is the Only Client-Side Check There Is

**What happens:** A record loaded through Data Loader, Bulk API, REST, or Apex DML saves a combination the matrix forbids. No error, no warning, no `FIELD_FILTER_VALIDATION_EXCEPTION`. The row then reads oddly in the UI, where the dependency filter hides the stored value and the field looks blank while SOQL still returns it.

**When it occurs:** Every non-browser write path, on every dependent picklist, always. This is architecture, not a bug: the Apex Developer Guide places the check *outside* the server sequence entirely — "Before Salesforce executes these events on the server, the browser runs JavaScript validation if the record contains any dependent picklist fields. The validation limits each dependent picklist field to its available values. No other validation occurs on the client side." (apexdev.txt:15404–15406). The seventeen-plus server-side steps that follow never mention the dependency again.

**How to avoid:** Assume zero enforcement anywhere the browser is absent, and restate the matrix as a validation rule or before-save automation whenever any integration, load, or Apex path writes both fields. Two consequences follow from the check being client-side. It cannot be trusted for security or data integrity — a determined caller simply does not use the browser. And it runs *before* step 1, so a before-save flow that sets the controlling field after the user picked a dependent value is never re-checked against the matrix.

---

## Gotcha 7: A Checkbox Controller's Values Are `checked` and `unchecked`, Not `true` and `false`

**What happens:** A checkbox-controlled matrix is authored with `<controllingFieldValue>true</controllingFieldValue>`. Either the deploy is rejected, or — worse where the value is accepted as an unrecognised string — the field ships with a matrix that maps nothing, and the dependent picklist renders empty for every user in every state of the checkbox.

**When it occurs:** Any checkbox controlling field authored by hand or generated by a tool that reasoned from the checkbox's own storage type. The confusion is legitimate: the checkbox field really does deploy `<defaultValue>false</defaultValue>` and really does read `true`/`false` in Apex, SOQL, and every API payload. Only the *matrix* uses different literals. The Metadata API Developer Guide spells them out on `controllingFieldValues`: "The values in the list depend on the field type: • Checkbox: `checked` or `unchecked`. • Picklist: The fullname of the picklist value in the controlling field" (api_meta.txt:79250–79258), and the guide's own dependent-picklist sample writes `<controllingFieldValues>checked</controllingFieldValues>` against the `isAmerican__c` checkbox (api_meta.txt:44762–44790).

**How to avoid:** Hard-code the two literals in any generator, and make the checker assert them — no checkbox-controlled matrix may contain a `controllingFieldValue` outside `{checked, unchecked}`. Note also that `checked`/`unchecked` are matrix literals, not picklist values: they never appear in `valueSetDefinition`, in SOQL, or in a validation-rule formula, where the checkbox is tested as a plain Boolean.

---

## Gotcha 8: Omitting a Picklist *Value* Deactivates It; Omitting a Dependency *Pair* Does Nothing

**What happens:** Someone hand-trims one field file and gets two opposite outcomes from the same edit. Deleting a `<value>` from `valueSetDefinition` silently deactivates it in the org and takes it out of every picklist that used it. Deleting a `<valueSettings>` block beside it changes nothing at all. The deploy result reports neither.

**When it occurs:** Partial staging, merge-conflict resolution, or any workflow that assembles a field file rather than retrieving it. The two rules live a few hundred lines apart in the guide. For values: "If picklist values are missing from a component definition, they get deactivated when deployed. Deactivation occurs for picklist values of both standard and custom fields." (api_meta.txt:79237–79239, repeated on `CustomValue` at 47481–47483). For pairs: add-only (Gotcha 4).

**How to avoid:** Never assemble a picklist field file from scratch — retrieve, edit, redeploy. A second trap compounds it: `CustomValue.isActive` documents that "An API retrieve operation for global picklist values returns all active and inactive values in the picklist. But retrieving the values of a non-global, unrestricted picklist returns only the active values" (api_meta.txt:47521–47525). So on an unrestricted local picklist, a plain retrieve-then-deploy round trip is safe only because the inactive values were already inactive — it will never resurrect one, and it will deactivate anything you delete by hand.

---

## Gotcha 9: Record Types Hide Values the Matrix Enabled, and Metadata API Retrieval Will Not Show You Why

**What happens:** A dependent value is enabled for the selected controlling value, the field is visible, FLS is open — and the value is still missing from the dropdown. It was never added to the record type's selected values. Worse, the team cannot see this in source, because the record-type file retrieved from the org is incomplete.

**When it occurs:** Whenever the object has record types and a new dependent value was added after the record types were created. The `RecordType` section carries the warning twice: "Metadata API doesn't retrieve specific picklist fields that are associated with a record type", and for person accounts "Metadata API retrieves standard picklist values only" if the picklist exists on Contact (api_meta.txt:44984–44988). Deploying values through `StandardValueSet` has its own version of the trap: "When setting `standardValue` on Record Types, including person account record types, new picklist values loaded into your organization through the Metadata API don't display in the picklist UI by default. For users to see the new values, go to the Record Types list for the object containing the picklist field, click Edit, and add the new value to the Selected Fields list." (api_meta.txt:130774–130779).

**How to avoid:** Treat "value exists" and "value is available on this record type" as two separate facts, and verify the second in Setup rather than in the repo. Every new dependent value needs a matching entry under the record type's `picklistValues` for that field, in every record type that should offer it — the checker in `scripts/` flags dependent values reachable through the matrix but absent from a record type that lists the field. Availability is the intersection of record type and matrix, so a value can be present in both files and still be unreachable if the *controlling* value is the one the record type omitted.

---

## Gotcha 10: Apex Describe Tells You a Dependency Exists but Will Not Tell You What It Contains

**What happens:** A test or a utility class tries to read the matrix from Apex so it can generate valid test data, and there is nothing to read. `Schema.PicklistEntry` has exactly four methods — `getLabel()`, `getValue()`, `isActive()`, `isDefaultValue()` (apexrefguide.txt:193673–193685). There is no `getValidFor()` on it. The `getValidFor()` that search turns up belongs to the invocable-action picklist-value class, a different type entirely (apexrefguide.txt:162512–162522).

**When it occurs:** Any attempt to build matrix-aware seed data, a generic dependent-picklist controller, or an assertion that a pair is enabled. It usually surfaces as a compile error, then as a search for the undocumented `validFor` base64 string on the serialized describe — which is not a documented API and should not go into a package.

**How to avoid:** Use describe for what it does expose: `isDependentPicklist()` "Returns true if the picklist is a dependent picklist" (apexrefguide.txt:191169–191178) and `getController()` "Returns the token of the controlling field" (apexrefguide.txt:190710–190720). That is enough to *assert the wiring* in a test — that the field is dependent and on the expected controller — which is the assertion most worth having, because it fails when a deploy drops `controllingField`. For the pair-level data, read the UI API `getPicklistValues` payload (`controllerValues` plus `validFor`) from the client, or keep the intended matrix in the test as an explicit fixture and let the validation rule be the thing under test.
