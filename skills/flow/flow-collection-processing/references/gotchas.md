# Gotchas — Flow Collection Processing

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Untyped Collection Variables Break Collection Filter and Sort

**What happens:** When a collection variable is created without specifying its SObject type (left as generic or "Apex-defined"), the Collection Filter and Collection Sort configuration UI cannot expose field names. The elements appear to be configured, but field-level conditions cannot be set, causing either a save error or a runtime fault where conditions evaluate unexpectedly.

**When it occurs:** Most commonly when a developer creates a collection variable using the "New Variable" shortcut during flow design and forgets to set the SObject type dropdown, or when a variable is repurposed from an earlier version of the flow that used generic collections.

**How to avoid:** Always set a specific SObject type on collection variables when Collection Filter, Collection Sort, or Transform elements will consume them. Audit collection variable definitions in the Flow canvas sidebar before adding these elements.

---

## Gotcha 2: Object Reference Mutation in Loop — Current Item Is a Reference, Not a Copy

**What happens:** When you modify `{!Loop.currentItem}` inside a loop and then add it to an output collection using an Assignment `Add` operation, the output collection holds a reference to the same object that the loop variable points to. If a subsequent iteration modifies the same variable, earlier entries in the output collection reflect the latest modification, not the value at the time they were added.

**When it occurs:** This most often appears when developers use a single Assignment element to both modify a field and add the item to the output collection in a specific order — or when the loop variable's fields are mutated in a branching path and the item is added on a later path that expects the earlier mutation to be preserved independently.

**How to avoid:** Keep the modification and the Add in a predictable, linear order within each iteration. Do not reuse the loop current item variable for a different purpose between iterations. Test the flow with more than two records to catch accumulation order bugs.

---

## Gotcha 3: Transform Cannot Use Formula Expressions for Field Mappings

**What happens:** The Transform element's field mapping UI accepts a source field reference or a literal value for each target field. It does not accept inline formula expressions (e.g., `{!sourceRecord.FirstName} & ' ' & {!sourceRecord.LastName}`). Attempting to use a formula-style mapping silently falls through to an empty or null value on the target field.

**When it occurs:** Developers coming from Formula fields or Assignment element logic expect to combine fields in the Transform mapping. The UI does not prevent this from being attempted, and the failure is silent at design time.

**How to avoid:** If a mapped target field requires computed or combined values, prepare the value in a separate Assignment element or formula variable before the Transform element runs, then map from that intermediate variable. For complex field logic, consider whether a Loop with explicit Assignment elements is more appropriate than Transform.

---

## Gotcha 4: Collection Sort Modifies the Source Variable In Place — No Copy Is Made

**What happens:** The Collection Sort element sorts the collection variable you point it at. There is no "output variable" separate from the input. After the element runs, the original variable is in sorted order. If any downstream element later in the same flow needed the original unsorted order, it is gone.

**When it occurs:** Flows that display one version of the collection in a Screen element (sorted for display) and then process the collection in the original insertion order will see only the sorted version after the Sort element has run.

**How to avoid:** If both sorted and unsorted access are required, copy the source collection into a second collection variable using a Loop before the Sort element, then sort one and use the other for the original-order path.

---

## Gotcha 5: Empty Collection Input to Loop Exits Immediately via "After Last" — Downstream Must Handle an Empty Output

**What happens:** A Loop over an empty collection does not fault. It exits immediately through the "After Last" connector, and any output collection that was to be built inside the loop remains empty. Downstream elements that pass the empty output collection to a DML element or subflow will process zero records silently.

**When it occurs:** Any time the upstream `Get Records` or Collection Filter returns zero records — perfectly valid in production — and no null/empty guard exists before the Loop.

**How to avoid:** Add a Decision element before the Loop to check whether the input collection size is greater than zero (using the `Is Null` or size check operators). Route the zero-record path to an early exit or a fault path with a meaningful error or log event.
