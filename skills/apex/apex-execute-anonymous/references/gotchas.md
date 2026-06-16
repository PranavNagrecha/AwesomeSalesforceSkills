# Gotchas — Apex Execute Anonymous

Non-obvious Salesforce platform behaviors that catch even experienced
Apex developers when they reach for Execute Anonymous. These are the
second-order issues — beyond "anonymous commits on success" and "use
a savepoint" — that show up when the script is running in a real org.

## Gotcha 1: Anonymous runs as the executing user with full sharing + CRUD + FLS enforcement

**What happens:** A script developed in a sandbox by an admin works.
The same script run in production by a less-privileged user fails
with `INSUFFICIENT_ACCESS_ON_CROSS_REFERENCE_ENTITY`,
`FIELD_CUSTOM_VALIDATION_EXCEPTION`, or — worse — silently returns
zero rows from a SOQL query that should return thousands. The script
"worked on my machine" but is functionally broken in prod.

**When it occurs:** Anonymous Apex executes under the principal's
effective context — profile-level CRUD, permission set object/field
permissions, sharing rules, record-level access, and FLS. There is
no "system" mode for an anonymous block; the platform never elevates
the executing user. The gap is most often discovered when:

- An admin scripts a fix and then asks a support engineer (lower
  permissions) to run it.
- A CI integration user (with Modify All Data deliberately *not*
  granted) is given a script intended for an admin.
- A Customer Community user has somehow ended up running anonymous
  Apex via a custom REST endpoint — they see filtered data because
  their sharing rules apply.

**How to avoid:** Don't try to escalate from inside the anonymous
block — wrap the privileged logic in a `public without sharing` (or
`public with sharing` if appropriate) Apex class deployed via the
normal source pipeline, then call `new MyOps().doFix()` from the
anonymous script. The class declaration is where sharing mode lives;
anonymous can call into a `without sharing` method and inherit its
sharing context for that call. Don't use this to deliberately bypass
security controls — use it where the operation is legitimately
system-level and the class-level review is the audit trail.

For SOQL silent-empty-result situations, add an
`isAccessible()` check up front and fail loud:

```apex
if (!Schema.sObjectType.Account.isAccessible()) {
    throw new System.NoAccessException();
}
```

---

## Gotcha 2: The debug log truncates at 5MB — and it's the *end* that survives, not the beginning

**What happens:** A long-running script with `System.debug` inside
a loop runs to completion. You scroll the log to find the "Updated
N records" summary at the bottom and instead see `MAXIMUM DEBUG LOG
SIZE REACHED` — the platform has dropped the start of the log to keep
the most recent ~5MB, but if your summary fired before the dropped
window or the truncation happened mid-line, you can lose the exact
output you wanted. (The 5MB cap applies to the log body; the platform
also enforces a 250MB-per-24h-per-user log allocation that, when hit,
silently disables further log capture for that user.)

**When it occurs:** Loops with `System.debug` inside, especially at
`FINEST` log level which dumps method enter/exit for every framework
call. Common scenario: "I'll add more debug so I can find the bug"
→ next run produces zero usable log because the bug-relevant lines
got truncated.

**How to avoid:** Set the debug levels explicitly before running, with
`Apex Code = INFO` (the default) and `System = INFO`, keeping noisier
categories (`Database = DEBUG`, `Workflow = INFO`) at the bottom of the
verbosity ladder unless you specifically need them. Wrap critical
output in `System.debug(LoggingLevel.ERROR, ...)` so it survives even
if a downstream framework boosts the level. Avoid `System.debug` inside
tight loops — accumulate into a `List<String>` and emit once at the
end:

```apex
List<String> trail = new List<String>();
for (Account a : accs) {
    trail.add(a.Id + ' -> ' + a.Name);
}
System.debug(LoggingLevel.ERROR, 'Processed: ' + String.join(trail, '\n'));
```

For longer captures, increase the `TraceFlag.ExpirationDate` (max 24h
in the future) and pull logs via the Tooling API rather than
scrolling the Developer Console.

---

## Gotcha 3: Governor limits are per anonymous execution — you don't get a "script mode" bonus

**What happens:** Developers assume an anonymous block — because
it's "just a script, not a transaction" — has more headroom than a
production trigger. It doesn't. The per-transaction governor limits
apply identically: 100 SOQL queries, 50,000 query rows, 150 DML
statements, 10,000 DML rows, 6MB heap, 10,000ms (sync) / 60,000ms
(async) CPU time. A script that loops "all Accounts" doing one update
per iteration hits the DML-statement cap at row 151 and the entire
transaction rolls back — the `Database.setSavepoint` doesn't save you
from a governor-limit fault because the limit cancels the transaction
before your `catch` block runs.

**When it occurs:** Bulk fixes written as "for each record, do the
thing" rather than "build a collection, do the thing once." Also
common when an engineer copy-pastes trigger code into anonymous and
runs it against more rows than the trigger ever sees in one
transaction (triggers see batches of 200; anonymous scripts often
load 10,000+ rows).

**How to avoid:** Treat anonymous Apex with the same bulkification
discipline as a trigger. Bound the SOQL with `LIMIT`, build mutations
into a `List<sObject>` *inside* the loop, and call DML *outside* the
loop once. For volumes above the per-transaction caps, use a paginated
loop pattern where each iteration re-runs the anonymous script (see
`examples.md` Example 1), or convert to Batch Apex — anonymous is
fundamentally a single-transaction tool.

---

## Gotcha 4: Top-level variables and methods don't persist across `executeAnonymous` calls — even in the same Dev Console session

**What happens:** The Developer Console UI shows a persistent "Open
Execute Anonymous Window" with the editor preserving what you typed
between Execute clicks. This visual continuity tricks developers into
thinking the runtime is also stateful — they declare `List<Account>
batch = ...` on the first run, modify it interactively, then on the
second click try to reference `batch` and get `Variable does not
exist: batch`. Each click is an independent compilation and execution;
nothing leaks between them.

**When it occurs:** Multi-step debugging where the developer wants to
"poke at" state — set up a collection, then inspect it, then mutate
it. Also when developers paste a fragment that depends on a class
imported above, then run just the fragment.

**How to avoid:** Treat every `executeAnonymous` invocation as a
fresh process with a fresh JVM. To share state between steps, either
(a) write a single longer script that contains all the steps, or
(b) persist intermediate state to a `Custom Setting` or a temporary
custom object and re-query at the start of each subsequent run. For
interactive exploration, the Apex Replay Debugger (VS Code) gives
true single-stepping over a debug log — closer to the REPL experience
the Dev Console seems to promise but doesn't deliver.

---

## Gotcha 5: `Database.executeBatch` and `System.enqueueJob` queue but don't run synchronously — the script returns before the async job finishes

**What happens:** An anonymous script calls
`Database.executeBatch(new MyBatch())` or
`System.enqueueJob(new MyQueueable())`. The script exits, the CLI
or Tooling API returns `success: true`, and the developer assumes
the work is done. The Batch/Queueable is actually still in the
async queue and hasn't started — or worse, started, threw, and
silently failed without surfacing in the script's output.

**When it occurs:** Any time anonymous Apex is used to kick off
async work in a pipeline or runbook. The pattern is correct (async
work is the right tool for volume) but the synchronization assumption
is wrong — there's no `await` in Apex, and the anonymous block
contract ends the moment the synchronous portion completes.

**How to avoid:** Capture the async job ID returned by
`Database.executeBatch` / `System.enqueueJob` and poll
`AsyncApexJob` separately:

```apex
Id jobId = Database.executeBatch(new MyBatch(), 200);
System.debug(LoggingLevel.ERROR, 'Enqueued: ' + jobId);
// Script returns here; the batch hasn't started yet
```

Then, in a follow-up step (separate anonymous run, or in your CI
pipeline):

```bash
sf data query --query "SELECT Id, Status, NumberOfErrors, JobItemsProcessed, TotalJobItems FROM AsyncApexJob WHERE Id = '707...'" --target-org prod
```

Poll until `Status = 'Completed'` (success) or `'Failed'`/`'Aborted'`
(investigate). For tight pipelines that need synchronous confirmation,
either keep the work inside the anonymous block (within governor
limits) or invoke a `Queueable` that publishes a Platform Event on
completion and subscribe to the event from your monitoring system.
Do not assume `success: true` from the anonymous-block response means
the async work succeeded — it means the *enqueue* succeeded.
