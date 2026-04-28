# Gotchas — Flow Loop Element Patterns

Non-obvious Salesforce platform behaviors around the Loop element that cause real production failures. Every gotcha here has bitten a real practitioner; none are theoretical.

---

## Gotcha 1: Iteration variable for SObject collections is a reference, not a copy

**What happens:** Inside `Loop: LoopAccounts`, an Assignment that sets `{!vCurrentAcct.Industry} = 'Tech'` mutates the in-memory `vAccounts` collection (the source). It does NOT issue a DML. Practitioners assume "I changed the field, I'm done" and skip the post-loop Update Records. The flow runs without error, the screen shows the new value (because the in-memory record changed), and the database has the OLD value. QA catches it days later.

**When it occurs:** Any Loop body that uses Assignment to set a field on the iteration variable without a corresponding Add-to-collection plus post-loop Update Records.

**How to avoid:** Treat every Assignment-on-iteration-variable as half a refactor. Always pair it with `vAcctsToUpdate Add vCurrentAcct` AND a single Update Records on `vAcctsToUpdate` after the loop ends.

---

## Gotcha 2: Iteration variable persists after the loop ends

**What happens:** After the loop's End connector fires, the current-item variable is NOT cleared. It holds the LAST iterated record (or null if the input collection was empty). A downstream element that references it gets that value, with no warning.

**When it occurs:** Reviewers copy-paste references, or developers use the iteration variable as a temporary scratch variable elsewhere in the flow. Empty-collection edge cases also cause null-pointer errors downstream.

**How to avoid:** Never reference a loop's iteration variable outside its loop body. If you genuinely want "the last record processed," capture it explicitly with an Assignment to a clearly-named variable. Always check for the empty-collection case before referencing anything that depends on a loop having executed.

---

## Gotcha 3: 2,000-element execution limit per interview, counted per element executed

**What happens:** Flow halts with `Number of executed elements has exceeded the maximum number of 2000`. A loop body of 4 elements iterating 600 records consumes 2,400 element-executions and trips this limit, even though the DML / SOQL budgets are nowhere near exhausted.

**When it occurs:** Loops over large collections, especially nested loops (e.g., 200 × 50 = 10,000 element-executions just from the loop body). Also occurs when a sub-200-record loop calls a chunky subflow whose own elements get counted in the same interview.

**How to avoid:** Estimate `body_elements * expected_iterations` before designing. If the product is in the high hundreds or above, escalate the inner work to invocable Apex (Apex code does NOT consume Flow's 2,000-element budget; Apex has its own separate limits).

---

## Gotcha 4: DML / SOQL budgets are shared across the WHOLE transaction

**What happens:** The 150-DML and 100-SOQL caps are per-transaction, not per-flow. A loop with 1 DML inside that runs 100 iterations uses 100 of the 150 DML statements. If a record-triggered Apex trigger and three other flows run in the same transaction (very common in mature orgs), the Loop's "safe-looking" 100 DML pushes the cumulative count past 150 and the LAST automation to fire takes the failure — often blamed on the wrong code.

**When it occurs:** Mature orgs with stacked automation; record-triggered flows where a downstream After Save flow chains into a third flow.

**How to avoid:** Treat any in-loop DML as a P0 even if math says "it would only be 50 statements." Refactor to one DML statement per loop. This is non-negotiable in any flow that runs in a Bulk API path.

---

## Gotcha 5: Subflow-in-loop hides DML and SOQL from a casual review

**What happens:** A reviewer scans the parent flow, sees a Loop calling a Subflow, and waves it through because "the subflow looks reusable." Open the subflow — it does Get Records and Update Records every invocation. The parent loop bulkifies-fails just as if the DML were inline, but the failure trace points at the subflow, making diagnosis confusing.

**When it occurs:** Org has many small "utility" subflows that were authored for one-record callers and got reused inside loops without re-bulkification.

**How to avoid:** Reviewing a loop is incomplete until you have opened every subflow called inside its body and confirmed the subflow itself contains no DML, no Get Records, and no Apex Action that issues either. Refactor offending subflows to accept collection inputs (`List<>`) and do bulk DML internally.

---

## Gotcha 6: Update Records on an empty collection is NOT an error

**What happens:** Practitioners over-defensively add a Decision before the post-loop Update Records to skip the DML when the collection is empty. This is unnecessary — Flow's Update Records on an empty SObject Collection is a no-op (issues no DML), counts no element-executions beyond the Update Records itself, and does not error.

**When it occurs:** Defensive over-engineering; cargo-culted from Apex where empty-list `update` IS an error.

**How to avoid:** Drop the empty-check Decision. The post-loop DML is safe on empty input. Removing the check shrinks element count and improves readability.

---

## Gotcha 7: Collection variables append duplicates silently

**What happens:** Assignment with `Add` does not deduplicate. If a loop has two paths that both Add the current item (e.g. via two Decision branches that both fire), the post-loop Update Records receives a collection with the same SObject ID twice. On Update, Salesforce throws `Duplicate id in list` and rolls back the entire DML batch.

**When it occurs:** Branching loop bodies, or loops where the input collection itself contains duplicates (very common when the input came from a many-to-many junction join).

**How to avoid:** Either gate the Add so only one branch can append per iteration, or de-duplicate the source collection upstream (Get Records does not return duplicate IDs, but a manually-built collection can). For Text-collection accumulators, no native dedup exists in Flow — escalate to invocable Apex.

---

## Gotcha 8: Loop iteration order is the source-collection order, not deterministic

**What happens:** A loop processes records in the order they appear in the input collection. If the collection came from a Get Records WITHOUT a Sort Order, the order is whatever the database query optimizer chose — and that can change between sandboxes, between releases, after an index change, or after a bulk data load reshuffles the underlying storage.

**When it occurs:** Order-sensitive logic (e.g. "stamp the first matching record"), tests that pass in one sandbox and fail in another.

**How to avoid:** Always set an explicit Sort Order on the upstream Get Records when the loop's behavior depends on order. Document the assumed order in the loop element description.
