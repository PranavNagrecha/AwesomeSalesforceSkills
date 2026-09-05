# LLM Anti-Patterns — Save Order

## Anti-Pattern 1: Use After-Save For Same-Record Field Updates

**What the LLM generates:** record-triggered Flow "After Save" that
updates a field on the triggering record.

**Why it happens:** defaults to after-save.

**Correct pattern:** before-save Flow. Same-record, no DML, runs at
step 3.

## Anti-Pattern 2: Expect Roll-Up In Before-Save

**What the LLM generates:** before-save Flow that reads a roll-up
summary field.

**Why it happens:** "the record has a field, read it."

**Correct pattern:** the roll-up on the parent is not recalculated until
step 16 of the child's save, long after the before-save Flow ran at
step 3. Read the recalculated value in a parent before or after trigger,
not the parent's after-save Flow — the step-16 parent save is a recursive
save, which skips steps 9–17, so step 14 never runs (see Anti-Pattern 7).
(Step 16 precedes the commit at step 19 — "roll-ups recalc after commit"
is a common but incorrect gloss.)

## Anti-Pattern 3: Workflow + Record-Triggered Flow On Same Field

**What the LLM generates:** migrates half the workflows, leaves the
other half running the same field update.

**Why it happens:** incremental migration without ordering check.

**Correct pattern:** retire workflow or flow — never both writing the
same field.

## Anti-Pattern 4: Ignore Recursion, Add `Trigger.isExecuting` Guards

**What the LLM generates:** Apex guards without addressing the flow
that fires the loop.

**Why it happens:** trigger-only mental model.

**Correct pattern:** trace the chain across flow + trigger. Kill the
DML-causing step, not the symptom.

## Anti-Pattern 5: Treat Platform Event Flows As Part Of The Save Order

**What the LLM generates:** "the platform-event flow will see the record
after the save at step 7."

**Why it happens:** conflation.

**Correct pattern:** platform-event-triggered flows are separate
transactions. Reason about them independently.

## Anti-Pattern 6: Call Before-Save Flow vs Before Trigger Order "Indeterminate"

**What the LLM generates:** "Before-save Flows and Apex before triggers
both run at step 3, and Salesforce doesn't guarantee which goes first —
so if they write the same field the result is unpredictable. Don't rely
on the order." Sometimes framed as advice to "detect and correct" any
code that assumes a fixed order.

**Why it happens:** an older revision of the Apex Developer Guide's
order-of-execution list did not enumerate before-save Flows as their own
numbered step, and a large volume of writing filled that gap by
declaring the ordering unspecified. Models trained on it reproduce the
claim confidently, and because it sounds appropriately cautious it
survives review.

This is the most damaging error in this domain: it converts a documented,
deterministic ordering into an imagined race, and then tells the reader
to distrust correct code.

**Correct pattern:**

```text
Step 3: record-triggered flows configured to run BEFORE the record is saved
Step 4: all before triggers

Separate, consecutive, documented. The Flow ALWAYS runs first.
Both write the same field → the TRIGGER's value saves. Every time.

Fix = single field ownership. If both must write, condition the TRIGGER
(the later writer). Conditioning the Flow changes nothing.
```

**Detection hint:** flag "indeterminate", "not guaranteed", "unpredictable",
"whichever runs second", or "race" appearing alongside before-save Flow and
before trigger. Flag any claim that the two share step 3. Flag any total
step count other than 20, or after-save Flows placed anywhere but step 14
(step 15 is the most common stale value; step 15 is now entitlement rules).

## Anti-Pattern 7: Claim A Cascading Parent Save Runs The Full Order

**What the LLM generates:** "the roll-up updates the parent, and the
parent then goes through the complete order of execution" — so the
design routes the reaction to the parent's after-save Flow.

**Why it happens:** the docs really do say "Parent record goes through
save procedure" at step 16, and the model completes that phrase to "all
20 steps". The exclusion sits in a Note box above the list, not in the
step text.

**Correct pattern:** "During a recursive save, Salesforce skips steps 9
(assignment rules) through 17 (roll-up summary field in the grandparent
record)." After-save Flows are step 14, so the parent's after-save Flow
does not run — silently, with no error.

**Detection hint:** flag any claim that a cascading parent or
grandparent save runs assignment rules, workflow rules, after-save
Flows, entitlement rules, or its own roll-ups.

## Anti-Pattern 8: Claim A Duplicate Rule Cannot See A Before-Save Flow's Write

**What the LLM generates:** "Duplicate rules evaluate the record as submitted,
so a value your before-save flow computes won't be considered — put the
normalization in a before trigger instead." Sometimes phrased as "duplicate
matching happens before automation".

**Why it happens:** the model knows duplicate rules are "early" and knows
before-save flows are "early", and resolves the ambiguity by ordering them the
way the words sound. The two are adjacent enough in the list that the guess is
never obviously wrong in a review.

**Correct pattern:** the direction is the other way. Before-save flows are
step 3; duplicate rules are step 6. The rule matches on whatever the flow
wrote. The same is true of custom validation rules at step 5. The consequence
the answer usually misses matters more than the ordering: a block action ends
the transaction there, so nothing at step 7 or later runs — no after trigger,
no after-save flow, no flow fault path, no log row.

**Detection hint:** flag any claim that a duplicate rule, a matching rule or a
custom validation rule sees "the submitted value" rather than the
flow-populated one. Flag any fault-handling design that expects a duplicate
block to be caught by a flow.

## Anti-Pattern 9: Treat A Flow-Published Platform Event As Part Of The Transaction

**What the LLM generates:** "Publish the event from the after-save flow — if
the transaction rolls back, the event won't be delivered, so the subscriber
stays consistent."

**Why it happens:** the model generalizes from Apex `Database.rollback` and
from the existence of `PublishAfterCommit`, and assumes transactional
semantics are the default. They are not.

**Correct pattern:** `publishBehavior` on the event definition decides this,
and the default is `PublishImmediately` — the message goes out when the publish
executes, whether or not the transaction succeeds. An after-save flow publishes
at step 14, and steps 15 through 19 can still fail. If the event means "this
record changed", the definition needs `PublishAfterCommit`.

**Detection hint:** flag any claim that a rollback un-publishes an event, or
that publishing from a flow is safe by default. Ask which `publishBehavior` the
event declares; if the answer does not name one, the answer is
`PublishImmediately`.

## Anti-Pattern 10: Invent A Ranking For Two Flows In The Same Step

**What the LLM generates:** "Flows in the same context run in the order they
were activated" — or by API name, or by version number, or "alphabetically".
Sometimes it invents a Flow Trigger Explorer behaviour to justify it.

**Why it happens:** the question ("which of my two after-save flows runs
first?") demands an answer, and every plausible-sounding tiebreak is
unfalsifiable from the docs. Saying "undefined" feels like a non-answer.

**Correct pattern:** the order of execution names step 3 and step 14 once each
and never ranks flows inside them. `triggerOrder` (int, 1–2,000, API 54.0 and
later) is the only rank the Metadata API exposes, and it is nullable. What
happens when two flows declare the *same* `triggerOrder`, or when neither
declares one, is not documented in the Metadata API guide, the Object
Reference or the Apex Developer Guide — the guide defers to a Salesforce Help
page. Say so, and fix the metadata instead of reasoning about it.

**Detection hint:** flag any stated tiebreak for co-resident flows that is not
`triggerOrder`. Flag confident answers about `triggerOrder` ties.
