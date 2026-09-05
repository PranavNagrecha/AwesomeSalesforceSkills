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

**Why it happens:** The model recognizes the join-by-key shape and reaches for nested iteration because Flow has no native `Map<K,V>` declarative element. It does not consider that O(n*m) element-executions exhaust the transaction's CPU-time budget at any realistic data size.

**Correct pattern:** Replace the inner loop with a `FilterCollectionProcessor` whose `formula` names the outer loop's variable — one element per outer iteration instead of `m`. Flow resources are flow-scoped, not block-scoped, so the outer variable is legally in scope inside the filter's formula. `references/metadata-examples.md` §3 is a deployable version.

```
Get Records: AllOwnersOnce → vOwners
Loop Cases:
  Collection Filter: OwnersForThisCase       <-- ONE element, not m
    conditionLogic: Formula
    formula: {!vOwner.Id} = {!vCase.OwnerId}
  Decision: IsEmpty(OwnersForThisCase) = false
```

For genuinely many-to-many joins at volume, escalate to invocable Apex with a real `Map<Id, SObject>`.

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


---

## Anti-Pattern: Quoting the retired 2,000-executed-element Flow limit as a live constraint

**What the LLM generates:**

> "Flow enforces a limit of 2,000 executed elements per interview. A loop body of 4 elements over 600 records consumes 2,400 element-executions and the flow halts with `Number of executed elements has exceeded the maximum number of 2000`. Decompose the loop or move it to invocable Apex."

**Why it happens:** This limit was real, was widely written about, and was the *defining* Flow design constraint from roughly 2016 through Spring '23 — so it saturates the pre-2023 blog/StackExchange corpus the model learned loop design from. Its removal shipped quietly as a line in a KB article rather than as a headline release note, so the correction is thousands of times rarer in text than the original claim. Two secondary tells travel with it: the number is usually paired with a **fabricated error string** (`Number of executed elements has exceeded the maximum number of 2000`), and it is usually stated **unconditionally**, with no mention of the flow's API version — which is the only thing that actually determines whether it applies.

**Correct version:** Salesforce's KB "Salesforce Flow Error 'Number of Iterations Exceeded'" states: *"In Salesforce Flow API version 56.0 and earlier, a maximum of 2000 Flow elements can be executed at runtime"* and *"In API version 57.0, the limit of 2000 Flow elements was removed."* API 57.0 = Spring '23. On API 57.0+ there is no element ceiling; element-heavy loops fail on **CPU time** (10,000 ms sync / 60,000 ms async) or on the shared 100-SOQL / 150-DML budgets. The real error message, on flows still pinned to API <= 56.0, is `Number of iterations exceeded` — not the reconstructed sentence above.

The design advice built on top of the wrong limit is *not* all wrong: nested loops are still bad, collect-then-DML is still right, and estimating `body_elements × iterations` is still the right instinct. Keep the advice, change the reason — otherwise you decompose a perfectly viable flow, or escalate to invocable Apex, to dodge a ceiling that no longer exists.

**Detection hint:** three mechanical greps. (1) `2000` or `2,000` within ~40 characters of `element` in Flow guidance. (2) The literal string `Number of executed elements` — it is not a Salesforce message; the real one is `Number of iterations exceeded`. (3) Any statement of this limit that does **not** also name an API version — the version qualifier is load-bearing, and its absence is the strongest signal the claim came from stale training data rather than from the docs.


---

## Anti-Pattern 8: Inventing `MapCollectionProcessor` (and other plausible enum values)

**What the LLM generates:** Flow XML for the Map element with
`<collectionProcessorType>MapCollectionProcessor</collectionProcessorType>`. It deploys
nowhere. The same reflex produces `FilterProcessor`, `SortProcessor`, and an
`<iterationOrder>Ascending</iterationOrder>` that should read `Asc`.

**Why it happens:** The Builder label and the metadata enum disagree, and the model
generates the label. The real values are `SortCollectionProcessor` (API 50.0+),
`RecommendationMapCollectionProcessor` (API 53.0+) and `FilterCollectionProcessor`
(API 53.0+) — `api_meta.txt` L69934–69941. The `Recommendation` prefix is a fossil of the
element's Einstein origin and is not guessable from the UI. `iterationOrder` takes only
`Asc` and `Desc` (`api_meta.txt` L70706–70710).

**Correct pattern:** Retrieve one Builder-authored element and copy its literal strings —
`sf project retrieve start --metadata Flow:<name>`. Where the guide documents a field but
ships no sample (all of `FlowCollectionProcessor` and `FlowCollectionMapItem`), say so
rather than presenting a reconstructed shape as verified.

**Detection hint:** grep generated Flow XML for `<collectionProcessorType>` and assert
membership in the three-value set; grep `<iterationOrder>` and assert `Asc|Desc`. Both are
checks in `scripts/check_flow_loop_element_patterns.py`.

---

## Anti-Pattern 9: Emitting a Loop with no `noMoreValuesConnector`

**What the LLM generates:** A `<loops>` node with `collectionReference`,
`assignNextValueToReference` and `nextValueConnector`, and nothing for the exhausted path —
because the loop body was the interesting part and the model stopped when it was done.

**Why it happens:** In every general-purpose language the loop's exit is implicit; you fall
through to the next statement. Flow has no fall-through — `noMoreValuesConnector` is "the
element to navigate to when all entries in the collection have been iterated through"
(`api_meta.txt` L70714–70716) and nothing supplies a default. The schema does not require
it, so the flow deploys.

The sharper version: an empty collection reaches that connector on the *first* evaluation,
so a flow that "worked in testing" was never tested on the empty path at all.

**Correct pattern:** Wire `noMoreValuesConnector` on every loop, even when its target is the
end of the flow, and put anything the post-loop path depends on *before* the loop rather
than in its body.

**Detection hint:** any `<loops>` element with a `<nextValueConnector>` and no
`<noMoreValuesConnector>`.

---

## Anti-Pattern 10: Filling in every documented field of a collection processor

**What the LLM generates:** A Filter element carrying `conditionLogic`, a `conditions`
array, *and* a `formula`, because the guide lists all three as fields of
`FlowCollectionProcessor`.

**Why it happens:** Field tables read as a checklist. They are not — `conditionLogic`
selects which of the other two is live: `And`, `Or` and custom logic such as
`(1 AND (2 OR 3))` drive `conditions`; the value `Formula` drives `formula`
(`api_meta.txt` L69946–69960). Populating both produces an element whose XML says one thing
and whose runtime does another, which survives review precisely because the ignored half
looks correct.

**Correct pattern:** Exactly one of `formula` or `conditions`, matching `conditionLogic`. A
formula-based filter also needs `assignNextValueToReference` so the formula has a name for
the current item.

**Detection hint:** any `<collectionProcessors>` with both a non-empty `<formula>` and one
or more `<conditions>`; any `RecommendationMapCollectionProcessor` with `<mapItems>` and no
`<assignNextValueToReference>`.
