# LLM Anti-Patterns — Flow Governor Limits Deep Dive

## Anti-Pattern 1: SOQL inside a Loop

**What the LLM generates:** Loop over records with Get Records inside.

**Why it happens:** Single-record mental model.

**Correct pattern:** Hoist the Get Records outside the loop with an IN-clause.

---

## Anti-Pattern 2: DML inside a Loop

**What the LLM generates:** Loop with Update Records inside.

**Why it happens:** Natural "for each record, update it" pattern.

**Correct pattern:** Build a collection inside the loop; single Update Records outside with the collection.

---

## Anti-Pattern 3: Assuming limits scale with org size

**What the LLM generates:** "Enterprise orgs get more SOQL." No — limits are per-transaction, same for all editions.

**Why it happens:** LLMs assume tier-based scaling.

**Correct pattern:** Design for 100 SOQL max synchronous, regardless of edition.

---

## Anti-Pattern 4: Nominal-limit math

**What the LLM generates:** "We use 80 SOQL, safe under 100."

**Why it happens:** LLMs don't account for shared transactions.

**Correct pattern:** Target 70% headroom. Plan against shared pool, not nominal limit.

---

## Anti-Pattern 5: Ignoring heap in unbounded collections

**What the LLM generates:** Accumulate all 50,000 rows in a collection.

**Why it happens:** LLMs don't model heap cost.

**Correct pattern:** Process in chunks; don't hold large collections.

---

## Anti-Pattern 6: "More async fixes limits"

**What the LLM generates:** Routes everything to Scheduled Paths to solve limit problems.

**Why it happens:** LLMs treat async as a silver bullet.

**Correct pattern:** Async gives fresh limits but doesn't fix bulk-unsafe code. A Scheduled Path with SOQL-in-loop breaks at the same iteration count — just with a 5-minute delay.

---

## Anti-Pattern 7: No benchmark assertion in tests

**What the LLM generates:** Tests for correctness, not for limit consumption.

**Why it happens:** LLMs treat limit math as separate from testing.

**Correct pattern:** Every bulk-sensitive flow test asserts `Limits.getQueries() < budget` and `Limits.getDMLStatements() < budget`.

---

## Anti-Pattern 8: Quoting the retired 2,000-executed-elements limit

**What the LLM generates:** "Flows are limited to 2,000 executed elements per interview, so keep the
loop under that."

**Why it happens:** the number circulated widely enough to be in the training data, and it has the
shape of a governor limit.

**Correct pattern:** it is not in any current developer guide, and the flow engine's own four
limit-usage debug events — `FLOW_START_INTERVIEW_LIMIT_USAGE`, `FLOW_ELEMENT_LIMIT_USAGE`,
`FLOW_BULK_ELEMENT_LIMIT_USAGE`, `FLOW_INTERVIEW_FINISHED_LIMIT_USAGE` — enumerate twelve meters and
no element count (`apexdev.txt` L38730–L38888). Budget the twelve. `references/gotchas.md` Gotcha 8
carries the full negative including the grep.

---

## Anti-Pattern 9: Inventing a millisecond cost per element

**What the LLM generates:** "A Decision costs roughly 2 ms, an Assignment 1 ms, so this flow uses
about 4,500 ms of the 10,000 ms budget."

**Why it happens:** the request asks for a number and the model would rather produce a plausible one
than say the figure is unpublished.

**Correct pattern:** no Salesforce developer guide publishes a per-element cost, and CPU is measured
across everything the transaction calls including package code (`apexdev.txt` footnote 5,
L19652–L19653). Report SOQL, DML and row counts — which *are* arithmetic — and say explicitly that
CPU and heap require a measurement, then name the measurement:
`FLOW_ELEMENT_LIMIT_USAGE` at Workflow `FINER`, or `Limits.getCpuTime()` in a bulk Apex test.

---

## Anti-Pattern 10: Treating a fault path as limit insurance

**What the LLM generates:** "Add a fault connector on every element so limit errors are logged and
handled gracefully."

**Why it happens:** fault connectors look like `try`/`catch`, and limit errors look like exceptions.

**Correct pattern:** `System.LimitException` is uncatchable — "when exceptions are uncatchable, catch
blocks, as well as finally blocks if any, aren't executed" (`apexdev.txt` L39720–L39727). The fault
route does not run, and it would have cost a DML statement and a row from the same exhausted budget if
it had. Fault paths are for record-level failures (validation rules, required fields, locks); limits
are prevented, never handled.

---

## Anti-Pattern 11: Assuming Publish Immediately and Publish After Commit cost the same

**What the LLM generates:** "Publishing the platform event adds one DML statement" — for an event
whose behavior is Publish Immediately.

**Why it happens:** both are a Create Records element on a `__e` object, and the flow XML is
identical.

**Correct pattern:** the event definition decides. Publish After Commit counts "as one DML statement
against the Apex DML statement limit"; Publish Immediately counts "against a separate event publishing
limit of 150 `EventBus.publish()` calls" (`apexrefguide.txt` L214524–L214528). Read the event, not the
flow, then say which meter moves.

---

## Anti-Pattern 12: Calling `System.assertTrue` in the budget test

**What the LLM generates:**

```apex
System.assertTrue(Limits.getQueries() < 70, 'SOQL budget exceeded');
```

**Why it happens:** JUnit and most xUnit frameworks have `assertTrue`, so the name transfers.

**Correct pattern:** there is no `System.assertTrue` method in Apex —
`grep -c "assertTrue" apexdev.txt apexrefguide.txt` returns 0 in both guides. Use the `Assert` class
(`apexrefguide.txt` L198622) or `System.assert`:

```apex
Assert.isTrue(Limits.getQueries() < 70,
    'SOQL budget: ' + Limits.getQueries() + ' of ' + Limits.getLimitQueries());
```

Also sample the counters **before** `Test.stopTest()` — limits "apply individually to each
testMethod" (`apexdev.txt` L19660) and the governor context resets at `stopTest`.

---

## Anti-Pattern 13: Claiming a subflow or a screen "starts a new transaction"

**What the LLM generates:** "Split the logic into a subflow so it gets its own governor limits", or
"each screen gives you a fresh 100 SOQL".

**Why it happens:** both feel like boundaries, and one of them nearly is.

**Correct pattern:** `flowTransactionModel` — the only field in Flow metadata that opens a transaction
— exists on `FlowActionCall` alone (`api_meta.txt` L68472–L68479). A subflow has no such field, so a
subflow provably shares the parent's meters. The screen claim is different: it is probably true and it
is **not** stated in `apexdev.txt` or `api_meta.txt`, so mark it UNVERIFIED rather than asserting it.
The documented levers, in order of how well they are grounded: `flowTransactionModel`
`NewTransaction` (L68477–L68478), then `scheduledPaths` `pathType` `AsyncAfterCommit`
(`api_meta.txt` L71412–L71414, corroborated by `apexdev.txt` L15489).
