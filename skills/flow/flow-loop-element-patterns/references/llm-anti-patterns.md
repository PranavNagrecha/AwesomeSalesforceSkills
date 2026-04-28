# LLM Anti-Patterns — Flow Loop Element Patterns

Specific failure modes that AI coding assistants exhibit when generating, refactoring, or reviewing Flows that contain Loop elements. The consuming agent (`flow-builder`, `flow-analyzer`) should self-check against every pattern below before emitting output.

---

## Anti-Pattern 1: "Wrap the in-loop DML in a Decision so it only fires when needed"

**What the LLM generates:** Asked to fix `Too Many DML Statements`, the model adds a Decision around the existing in-loop Update Records so the DML "only runs on iterations that need it." The DML stays inside the loop.

**Why it happens:** Pattern-match from generic programming advice ("avoid unnecessary work in a hot path"). The model treats the DML as expensive-but-ok if rarer, instead of recognizing the structural rule that DML belongs OUTSIDE the loop entirely.

**Correct pattern:**

```
Loop:
  Decision: NeedsUpdate?
    YES → Assignment: setFields + Add to vToUpdate
End Loop
Update Records: vToUpdate    <-- single DML, post-loop
```

**Detection hint:** Any Loop body that contains an Update / Create / Delete Records element fails review, regardless of whether it's gated by a Decision. Search the Flow XML for `<recordUpdates>`, `<recordCreates>`, `<recordDeletes>` inside `<loops>` ranges.

---

## Anti-Pattern 2: "Modify the iteration variable to update the source records"

**What the LLM generates:** A Loop whose body sets `{!vCurrentAcct.Industry} = 'Tech'` and then proceeds, with no Update Records and no collect-then-DML. The model believes Flow auto-persists changes to the iteration variable.

**Why it happens:** Java / Python / TypeScript bleed — in those languages mutating an object reference is "the change," and in some ORMs the unit-of-work pattern auto-flushes. Flow does not.

**Correct pattern:**

```
Loop:
  Assignment:
    vCurrentAcct.Industry = 'Tech'
    vAcctsToUpdate Add vCurrentAcct
End Loop
Update Records: vAcctsToUpdate
```

**Detection hint:** Any Loop body Assignment that targets `<currentItem>.<field>` MUST be paired with `Add <currentItem>` to a separate SObject Collection AND a post-loop Update Records on that collection. Missing either of those = silent data loss.

---

## Anti-Pattern 3: "Nest a loop to join two collections"

**What the LLM generates:** Asked to "for each Case, find the matching Owner from the Owners collection," the model writes nested loops with a Decision inside (O(n*m)).

**Why it happens:** The model recognizes the join-by-key shape and reaches for nested iteration because Flow has no native `Map<K,V>` declarative element. It does not consider that Flow's 2,000-element ceiling makes O(n*m) infeasible at any realistic data size.

**Correct pattern:** Pre-load one side into a collection variable, then use Map-Lookup pattern (single outer loop + bounded inner search) for low-hundreds of records, OR escalate to invocable Apex with a real `Map<Id, SObject>` for true O(n) lookup.

```
Get Records: AllOwnersOnce → vOwners
Loop Cases:
  Loop vOwners:           <-- bounded by vOwners size, not multiplicative
    Decision: match
```

For larger volumes, escalate to Apex.

**Detection hint:** Flag any Flow with two Loop elements where the inner loop's input collection is not a small bounded constant (e.g., a hardcoded list of up to ~10).

---

## Anti-Pattern 4: "Forget the Subflow-in-loop case"

**What the LLM generates:** Asked to bulkify a parent flow, the model refactors the parent's loop body but never inspects the Subflow that the loop calls. The Subflow still does Get Records + Update Records internally, so the parent flow still has SOQL-in-loop and DML-in-loop — just one indirection away.

**Why it happens:** The model treats the subflow as a black box ("it's reusable, must be fine"). Bulkification analysis must be transitive across the call graph.

**Correct pattern:** Whenever a refactor touches a loop, recurse into every Subflow / Action / Apex Invocable called inside the loop body. Refactor those to accept and operate on a `List<>` input, then pass the parent's collection into a single bulkified call (often deleting the parent's loop entirely).

**Detection hint:** Any Loop body containing `<subflows>` or `<actionCalls>` requires the reviewer to open each referenced subflow / action and confirm it has no DML / SOQL / nested DML-bearing subflows.

---

## Anti-Pattern 5: "Insert a Loop when a Get Records or Collection Filter would suffice"

**What the LLM generates:** Asked for "the top 10 Opps by amount" or "all Cases where Status = New," the model writes a Get Records that returns everything plus a Loop that filters / sorts / limits. Both are work the database can do for free.

**Why it happens:** The model defaults to imperative iteration patterns from general-programming training data. It does not recognize that Get Records supports `Sort Order`, `Sort Field`, and `Number of Records to Store` — and that Collection Filter is a pure-declarative replacement for filter-loops.

**Correct pattern:**

- "Top 10 by amount" → Get Records with `Sort Field = Amount`, `Sort Order = Desc`, `Number of Records to Store = 10`. No loop.
- "All Cases where Status = New" → put the filter in the Get Records criteria. No loop.
- "Filter an existing in-memory collection" → Collection Filter element. No loop.

**Detection hint:** Any Loop whose body is purely `Decision → Assignment(Add to output)` with no DML, no SOQL, no enrichment is a false-positive Loop and should become a Collection Filter (for in-memory) or a sharper Get Records (for database-side filter / sort / limit).

---

## Anti-Pattern 6: "Add an empty-collection check before the post-loop DML"

**What the LLM generates:** A defensive Decision before the final Update Records that skips the DML if the accumulator is empty.

**Why it happens:** Cargo-culted from Apex, where `update emptyList` would error. Flow does not error on Update Records of an empty SObject Collection — it is a no-op.

**Correct pattern:** Drop the check. The post-loop Update / Create / Delete Records is safe on an empty collection input.

**Detection hint:** A Decision element immediately preceding a post-loop DML, whose only purpose is `IsEmpty(vCollection) = false`, is dead defensive code.

---

## Anti-Pattern 7: "Use the iteration variable downstream of the loop"

**What the LLM generates:** A reference to the loop's current-item variable AFTER the loop's End connector, expecting it to be empty / reset. It is not — it holds the last iterated value (or null if input was empty).

**Why it happens:** Confusion with Apex `for (X x : list)` scoping where `x` goes out of scope at the closing brace. Flow has no block scope; loop variables are flow-scoped.

**Correct pattern:** Inside the loop, capture any value you need post-loop into a clearly-named separate variable via Assignment. Never reference the iteration variable outside the loop.

**Detection hint:** Any merge field `{!loopName_currentItem.X}` referenced in an element that comes after the loop's End connector is suspect. Either capture intent explicitly or remove the reference.
