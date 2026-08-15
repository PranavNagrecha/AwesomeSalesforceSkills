# Gotchas — Flow Interview Debugging

Non-obvious Salesforce platform behaviors that make Flow failures hard to see,
hard to reproduce, or hard to attribute. Each entry names the failure mode, the
condition that produces it, and the fix.

---

## Gotcha 1: The Error Email Goes to the Last Modifier, Not the Owner

**What happens:** A flow fails in production and the notification lands in one
person's inbox — the user who most recently saved the flow. Not the flow's
creator, not a queue, not the support alias. If that person has left, changed
teams, or has email notifications muted, the failure is invisible.

**When it occurs:** Always, under the default org setting. And the recipient
silently *changes* every time someone edits the flow, so an alerting rota that
was correct last quarter is wrong now with no signal that it moved.

**How to avoid:** Setup → Quick Find `Automation` → **Process Automation
Settings** → **Send Process or Flow Error Email to** → **Apex Exception Email
Recipients**, then maintain the list under Setup → **Apex Exception Email**.
Note the privacy trade: flow error emails include the data involved in the
interview, including user-entered data, so the alias needs to be as restricted
as the most sensitive flow in the org.

---

## Gotcha 2: A Get Records Returning Zero Rows Is Not a Fault

**What happens:** An author wires a fault connector off a Get Records expecting
it to catch "nothing found." It never fires. The flow proceeds down the normal
connector holding a null record variable, and the failure surfaces several
elements later as something unrelated — a null dereference in a formula, or a
DML that inserts a child with a blank required lookup.

**When it occurs:** Every time. Zero rows is a successful query result. The
fault connector fires only on a genuine platform exception: an invalid filter
reference, an object or field the running user cannot read, or a governor
breach during the query.

**How to avoid:** Handle "not found" with a Decision immediately after the Get,
testing the record variable with the `IsNull` operator. Set
`assignNullValuesIfNoRecordsFound` to `true` on the lookup so the variable is
reliably null rather than retaining a value from a previous loop iteration —
that stale-value case is what makes the `IsNull` check flaky when the Get sits
inside a Loop. Reserve the fault connector for real exceptions and point it at
a logger.

---

## Gotcha 3: The Debugger Does Not Run Scheduled Paths or Async Paths

**What happens:** Every element goes green in Flow Builder's debugger. The
scheduled path fails in production. The debugger showed no sign of it.

**When it occurs:** Any flow with a scheduled path, an async (Run
Asynchronously) path, a Pause element, or a platform-event trigger. The
debugger runs the interview in your session, now. Scheduled and async work runs
later, in a separate transaction, typically as the Automated Process user.

**How to avoid:** Treat the debugger as an authoring aid for the synchronous
path only. Observe the rest where it actually lives: pending scheduled-path
entries appear in Setup → **Environments** → **Monitoring** → **Time-Based
Workflow** (that page lists record-triggered flow scheduled paths alongside
older time-dependent actions), and interview state appears in Setup → **Paused
And Failed Flow Interviews**. Instrument the async branch with a fault-path log
row, because nobody is on screen to see an error there.

---

## Gotcha 4: Debugging With Rollback On Hides Everything At or After Commit

**What happens:** The flow debugs cleanly with the roll-back option enabled and
throws on the first real save.

**When it occurs:** Whenever the failure lives at commit or later: a validation
rule evaluated on the committed state, a downstream record-triggered flow or
Apex trigger on records this flow created, a roll-up summary recalculation, or
a scheduled path that is enqueued off the commit. A rolled-back run reaches none
of it.

**How to avoid:** Iterate with rollback on so you do not litter the org; do a
final pass with rollback **off**, in a sandbox with realistic data and the
downstream automation actually enabled. "Green in the debugger" is evidence the
wiring is right, not evidence the flow works.

---

## Gotcha 5: The Version in the Error Email Is Not the Version You Are Looking At

**What happens:** The email describes a failure at element `Update_Account` in
version 7. You open the flow, find no such element, and conclude the email is
wrong.

**When it occurs:** Any time someone activated a newer version between the
failure and the triage — which, for a flow under active development, is most of
the time. Flow Builder opens the latest version by default, not the version
named in the email.

**How to avoid:** Read the `Version:` line first and open that version
explicitly from the flow's detail page version list. If you also need to know
what changed between the failing version and the current one, that is a
versioning-discipline problem, not a debugging one — see
`flow/flow-versioning-strategy`.

---

## Gotcha 6: `$Flow.FaultMessage` Is Only Populated Inside a Fault Path

**What happens:** An author assigns `$Flow.FaultMessage` to a variable in the
normal path "so it's ready," and every log row carries an empty message.

**When it occurs:** Any reference to the variable outside the branch reached by
a fault connector. Outside a fault path there is no fault, so the variable is
empty.

**How to avoid:** Read `$Flow.FaultMessage` only in the elements downstream of a
`faultConnector`. And read it *immediately* — if the fault path itself contains
a second element that can fault, the second fault overwrites the first message,
and the log row ends up describing the logger's failure rather than the original
one.

---

## Gotcha 7: Flow Has No "Which Element Faulted" Variable

**What happens:** An author builds one shared fault-handler subflow, wires every
fault connector in the flow to it, and then cannot tell which element produced
any given log row. The fault message sometimes hints at it and sometimes does
not.

**When it occurs:** Always. Salesforce exposes the failing element name in the
error email (`Error element <Name> (<Type>)`) but does not expose it to the flow
as a global variable at run time.

**How to avoid:** Pass the element name in as a literal. Either give each fault
connector its own Create Records with a hard-coded `Failed_Element__c`, or route
every fault to one fault-handler subflow that takes `sourceElement` as a
required text input, and type the element name at each call site. It is
duplication, but it is the only way the log row can answer the first question
triage asks.

---

## Gotcha 8: The Interview GUID Is the Only Reliable Join Between Email and Log

**What happens:** A team correlates flow error emails to log rows by timestamp
and record Id. Under bulk load — 200 records failing in the same second on the
same parent — the correlation is ambiguous and the triage picks the wrong row.

**When it occurs:** Any bulk operation. Timestamps collide at second
granularity; a single record can be touched by several interviews in one
transaction.

**How to avoid:** Capture `$Flow.InterviewGuid` on every log row. It is the same
identifier Salesforce prints in the error email, so the join is exact. Store it
in an External ID text field so the lookup from a pasted GUID is indexed rather
than a full scan.

---

## Gotcha 9: A Fault Path That Swallows the Error Turns a Loud Failure Into a Silent One

**What happens:** A team adds fault connectors everywhere, points them at a
"log and continue" branch, and the error emails stop. Everyone declares the flow
fixed. Six weeks later, a report shows a third of the child records were never
created.

**When it occurs:** Whenever a fault path logs and then rejoins the happy path
without either aborting the interview or surfacing the failure. Flow does not
re-raise. Once you catch it, it is caught.

**How to avoid:** Decide explicitly per fault path whether the interview should
continue. If the failure means the business outcome did not happen, end the
path — and in a record-triggered flow, use the **Custom Error** element so the
transaction rolls back and the user is told, rather than committing a
half-finished state. Continuing past a fault is a legitimate choice only when the
faulted step was genuinely optional, and the log row still has to exist.

---

## Gotcha 10: A Flow Interview Consumes the Transaction's Governor Budget, Not Its Own

**What happens:** A flow that is correct in isolation starts throwing
`System.LimitException: Too many SOQL queries: 101` in production, and the flow's
own element count has not changed.

**When it occurs:** When the flow shares a transaction with other automation.
Flow elements draw from the same per-transaction Apex governor budget as
everything else running in that transaction — 100 SOQL queries synchronous (200
asynchronous), 150 DML statements, 50,000 query rows, 10,000 DML rows, 10,000 ms
CPU synchronous (60,000 ms asynchronous), 6 MB heap synchronous (12 MB
asynchronous). An Apex trigger, a second record-triggered flow on the same
object, and a managed package can each consume most of it before your flow's
first element runs.

**How to avoid:** When a limit error names a number just above a governor
ceiling, stop optimizing the flow in isolation and inventory everything on that
object. The debug log's cumulative limits section, not the flow's element list,
is the artifact that tells you who spent the budget. Deep bulkification work
belongs to `flow/flow-bulkification`; this skill's job is recognizing that the
error is a shared-transaction symptom rather than a flow bug.

---

## Gotcha 11: The Element Limit Everyone Quotes Was Removed

**What happens:** Someone diagnoses a slow, loop-heavy flow as "hitting the
2,000 element limit" and refactors around a limit that is not there.

**When it occurs:** On any flow at API version 57.0 or later. The cap on
executed elements per interview was removed in API version 57.0 (Spring '23).
Flows still on an older API version keep the old behaviour, which is why the
symptom is inconsistent across an org — the API version is per flow version, and
re-saving a flow in Flow Builder can bump it.

**How to avoid:** Check the flow version's API version before attributing
anything to an element cap. On a modern flow, the real ceiling is CPU time and
the SOQL/DML governors, and the fix is the same one it always was: get the
queries and the DML out of the loop.

---

## Gotcha 12: Deleting a Flow Version Fails Because an Interview Still References It

**What happens:** Cleanup tries to delete an old flow or an old version and the
platform refuses, sometimes with an unhelpful server error rather than a clean
message.

**When it occurs:** When paused or waiting interviews still reference that
version. Since Spring '24 (API 60.0) there is no cap on how many paused and
waiting interviews an org can accumulate, so these pile up quietly and outlive
whatever retention rule the team wrote.

**How to avoid:** Before deleting, open Setup → **Paused And Failed Flow
Interviews**, filter to the flow, and drain or delete the referencing
interviews. Deleting a `FlowInterview` record requires the Manage Flow user
permission. For volume, `FlowInterview` is exposed through the REST and SOAP
APIs, so a Data Loader or Workbench pass is the practical route — one-at-a-time
deletion in the UI does not scale past a few dozen.
