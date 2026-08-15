# LLM Anti-Patterns — Flow and Platform Events

Mistakes AI assistants reliably make when wiring Flow to the event bus.

---

## Anti-Pattern 1: Treating the Event as Transactional With the Publisher

**What the LLM generates:** a design in which the subscriber's failure "rolls
back" the publisher, or in which the publishing flow reads a value the
subscriber wrote a few elements later.

**Why it happens:** the model's strongest prior for "publish then handle" is an
in-process event bus or a synchronous message broker, where publisher and
handler share a call stack.

**Correct pattern:** the subscriber runs in a separate, later transaction. The
publisher has already committed and returned to the user. A subscriber exception
produces no rollback, no error on the triggering record, and no notification to
the publishing user. If the publisher needs the result, it needs a subflow or
invocable Apex, not an event.

**Detection hint:** compensating logic in the *publisher* that exists to recover
from a subscriber failure, or any wording like "if the subscriber fails, the
Case update is reverted."

---

## Anti-Pattern 2: Publishing Inside a Loop

**What the LLM generates:** a Loop over a record collection with a Create
Records on the `__e` object as the loop body.

**Why it happens:** it mirrors the imperative shape of the requirement ("send an
event for each changed contact") and reads naturally on the canvas.

**Correct pattern:** build a collection of event records inside the loop with an
Assignment, publish the whole collection with one Create Records after the loop.
Under Publish After Commit each publish is a DML statement, so 200 iterations is
200 statements against a 150 limit — and the interview dies having already
published part of the set, which leaves downstream partially notified.

**Detection hint:** a `<recordCreates>` whose `<object>` ends in `__e` appearing
between a `<loops>` element and its `nextValueConnector` target.

---

## Anti-Pattern 3: "Choose High-Volume If You Expect More Than 250,000 a Day"

**What the LLM generates:** a design step that instructs the reader to select the
high-volume event type once volume crosses some threshold.

**Why it happens:** the standard-volume / high-volume choice was real and heavily
written about before API 45.0, and that content dominates the training
distribution.

**Correct pattern:** delete the step. Event definitions created at API 45.0 and
later are high-volume; standard-volume events can no longer be defined and the
legacy ones are being retired. The only live consequence of the distinction is
retention — 72 hours for high-volume, 24 for legacy standard-volume.

**Detection hint:** the phrase "standard-volume" in guidance about a *new* event,
or any instruction to pick an event volume type in the definition UI.

---

## Anti-Pattern 4: Assuming One Event Equals One Interview

**What the LLM generates:** a subscriber with a Get Records and an Update
directly against `$Record`, with a governor analysis that reasons about a single
event.

**Why it happens:** the record-triggered flow mental model, where `$Record` is
one record, transfers cleanly and wrongly. Nothing on the canvas signals
batching.

**Correct pattern:** a platform-event-triggered flow processes up to 200 event
messages in one transaction, sharing one governor budget. Bulkify: collect Ids
across the batch, one Get Records with an `In` filter, one Update against the
collection. Reducing the batch size is a mitigation for irreducibly expensive
per-event work, not a substitute for bulkification.

**Detection hint:** a subscriber flow containing a `<recordLookups>` and a
`<recordUpdates>` with no intervening collection handling, and an explanation
that counts one SOQL query.

---

## Anti-Pattern 5: Inventing a "Publish Platform Event" Element or Action

**What the LLM generates:** a flow step named `Publish Event`, or an
`<actionCalls>` with `actionType` set to something like `publishPlatformEvent`.

**Why it happens:** every other platform in the model's training set has an
explicit publish verb, and Flow's Create-Records-on-an-`__e`-object idiom is
genuinely unintuitive.

**Correct pattern:** publishing is a Create Records element whose `object` is the
event's API name. There is no separate publish element. Set
`storeOutputAutomatically` to `false` — a publish returns no usable record Id.

**Detection hint:** any flow element name or `actionType` containing "publish"
that is not a `<recordCreates>`.

---

## Anti-Pattern 6: Publishing From a Before-Save Flow "For Performance"

**What the LLM generates:** a before-save record-triggered flow that publishes an
event, justified by before-save being faster than after-save.

**Why it happens:** "before-save is roughly ten times faster" is correct and
widely repeated guidance for field updates, and the model over-applies it.

**Correct pattern:** before-save flows cannot perform DML, and a publish is DML.
Publishing is an after-save operation. The performance advice is about updating
fields on the triggering record; it does not generalize to anything that writes.

**Detection hint:** `<triggerType>RecordBeforeSave</triggerType>` in the same
flow as a `<recordCreates>` whose object ends in `__e`.

---

## Anti-Pattern 7: Traversing Relationships From the Event

**What the LLM generates:** `$Record.Case__r.Subject` or `$Record.Account.Name`
inside a subscriber flow.

**Why it happens:** `$Record` looks like a record, and cross-object dot notation
is the natural Flow idiom for reaching a parent.

**Correct pattern:** an event carries Ids in Text fields, not lookups. There is
no relationship to traverse. Get Records on the real object, filtered by the Id
field the event carried — and remember the record may have changed since the
publish, so if the subscriber's decision depends on the transition, the event has
to carry both the old and the new value.

**Detection hint:** `__r.` or a dot-chained relationship anywhere inside a flow
whose `<start>` has `<triggerType>PlatformEvent</triggerType>`.

---

## Anti-Pattern 8: Gating Subscriber Logic on `$Permission` or `$User`

**What the LLM generates:** a Decision in the subscriber branching on
`$Permission.Some_Custom_Permission`, or an Assignment stamping `$User.Id` as
"the user who caused this."

**Why it happens:** both are ordinary Flow idioms and both are silently wrong in
this context rather than erroring.

**Correct pattern:** platform-event-triggered flows run as Automated Process by
default, which has no profile and no permission set assignments — every
`$Permission.X` evaluates false and `$User` is not the human who triggered the
publish. Carry the human's Id in the event payload if the subscriber needs it,
and use a Custom Metadata feature flag rather than `$Permission`. Since Spring
'24 the flow can be configured to run as the Workflow User when it needs real
record access; that is a configuration change, not a reason to trust
`$Permission`.

**Detection hint:** `$Permission.` or `$User.` inside a flow whose `<start>` has
`<triggerType>PlatformEvent</triggerType>`.

---

## Anti-Pattern 9: Promising Replay as the Recovery Story

**What the LLM generates:** "if the subscriber is down, the events are retained
and can be replayed when it comes back."

**Why it happens:** replay is a real event-bus capability and it is prominent in
the Platform Events documentation, so the model surfaces it as an available
mitigation.

**Correct pattern:** retention in the event bus is 72 hours for high-volume
events, and replaying from a Replay Id requires a Pub/Sub API or CometD client.
Flow has no replay affordance at all. For a Flow-only design, "we can replay it"
is false. If multi-day recovery is a requirement, the durable artifact must be a
Salesforce record the subscriber marks processed, not the event bus.

**Detection hint:** the words "replay" or "Replay Id" in a design whose
subscribers are all flows.
