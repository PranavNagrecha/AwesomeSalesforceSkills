# Gotchas — Apex CPU And Heap Optimization

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Bulkified Code Can Still Blow CPU

**What happens:** SOQL and DML are already outside loops, yet CPU still fails.

**When it occurs:** The remaining algorithm still does too much in-memory work.

**How to avoid:** Inspect nested-loop shape, repeated parsing, and expensive string or regex operations.

---

## Debugging Can Inflate The Heap

**What happens:** Diagnostic serialization or giant debug strings push the transaction over the heap limit.

**When it occurs:** Teams log whole payloads or collection contents during an incident.

**How to avoid:** Log counts, keys, and narrow samples instead of full payloads.

---

## JSON Work Is Often A Double Hit

**What happens:** Parsing and re-serializing large payloads costs both CPU and heap.

**When it occurs:** Integration payloads are repeatedly transformed or copied.

**How to avoid:** Parse once, process in smaller chunks, and avoid duplicate payload representations.

---

## Micro-Optimizing Syntax Rarely Beats Algorithm Refactors

**What happens:** Teams spend time changing minor syntax choices while the real bottleneck remains nested data traversal.

**When it occurs:** There is no measurement-driven hotspot identification.

**How to avoid:** Measure first, then attack the biggest compute or memory structure.

---

## Certified Managed Packages Get Their Own SOQL And DML — But Not Their Own CPU Or Heap

**What happens:** A team installs an ISV package, reads that certified managed
packages "get their own set of limits for most per-transaction limits", and
assumes the package's compute is billed separately. It is not. The quick
reference lists exactly four exceptions: "All per-transaction limits count
separately for certified managed packages except for: • The total heap size
• The maximum CPU time • The maximum transaction execution time • The maximum
number of unique namespaces" (`salesforce_app_limits_cheatsheet.txt` L241–L248;
same list at `apexdev.txt` L19714–L19720). The cumulative cross-namespace
multiplier does not rescue you either: "The cumulative limit doesn't affect
limits that are shared across all namespaces, such as the limit on maximum CPU
time" (`salesforce_app_limits_cheatsheet.txt` L207–L209).

**When it occurs:** Your trigger is fine in a sandbox with no packages and fails
in production where a managed package subscribes to the same save order. Your
own code's CPU is unchanged; the shared 10,000 ms is what moved.

**How to avoid:** Budget CPU and heap for the whole transaction, not for your
class. Instrument with `Limits.getCpuTime()` at the top and bottom of your entry
point and compare against `Limits.getLimitCpuTime()`; if your own delta is small
but the transaction still fails, the consumer is elsewhere in the save order and
the fix is to move your work async, not to micro-tune it.

---

## Scheduled Apex Runs On Synchronous Limits

**What happens:** A `Schedulable.execute` body is written against the 60,000 ms /
12 MB asynchronous column and fails at 10,000 ms. The quick reference note is
explicit: "Although scheduled Apex is an asynchronous feature, synchronous limits
apply to scheduled Apex jobs" (`salesforce_app_limits_cheatsheet.txt` L36–L37).

**When it occurs:** Someone moves heavy work out of a trigger "into async" by
scheduling it hourly, and gets the same limits they were escaping plus a slower
feedback loop.

**How to avoid:** Keep `Schedulable.execute` as a dispatcher — have it call
`Database.executeBatch` or `System.enqueueJob` and do the work in the batch or
queueable body, which does get the asynchronous ceiling.

---

## Database Time Is Not CPU Time, But DML Server Time Is

**What happens:** A transaction takes minutes of wall clock and reports a small
`Limits.getCpuTime()`, so the team concludes there is no CPU problem — then a
different transaction with light-looking DML blows the CPU limit. Both follow
from one paragraph: "Application server CPU time spent in DML operations is
counted towards the Apex CPU limit… For example, the portion of execution time
spent in the database for DML, SOQL, and SOSL isn't counted, nor is waiting time
for Apex callouts" (`salesforce_app_limits_cheatsheet.txt` L173–L176).

**When it occurs:** Bulk updates that fire many downstream automations; long
callout chains that consume the separate 10-minute transaction execution limit
and the 120-second cumulative callout timeout without touching the CPU counter.

**How to avoid:** Read two clocks. `Limits.getCpuTime()` answers "is my algorithm
too expensive"; the debug log timestamps and the 10-minute transaction ceiling
(`salesforce_app_limits_cheatsheet.txt` L93–L94) answer "is my transaction too
long". A fix for one is usually the wrong fix for the other.

---

## A Heap Size Of 0 In The Debug Log Means "Not Measured"

**What happens:** The log's `LIMIT_USAGE_FOR_NS` block reports `Maximum heap size:
0 out of 6000000` and the reviewer concludes the transaction is heap-clean. The
guide: "Heap usage is accurately reported in the debug log and an exception is
thrown whenever an Apex Heap Size error occurs. At other times, the heap size
shown in the debug log is the largest heap size that was calculated during the
transaction. To reduce the overhead on small transactions, minimal heap usage
doesn't warrant an accurate calculation and is reported as 0(zero)"
(`apexdev.txt` L38239–L38241).

**When it occurs:** Whenever a single-record repro is used to clear a
bulk-volume concern.

**How to avoid:** Get heap numbers from a bulk run, and prefer an in-code
`Limits.getHeapSize()` delta (documented as "the approximate amount of memory (in
bytes) that has been used for the heap", `apexrefguide.txt` L220711–L220722) over
the log's summary line.

---

## The Limit Exception Cannot Be Caught And `finally` Does Not Run

**What happens:** A team wraps the risky block in `try/catch (Exception e)` with a
`finally` that flushes logs or rolls back to a savepoint, then finds no log rows
and no rollback after a CPU failure. "One such exception is the limit exception
(`System.LimitException`) that the runtime throws if a governor limit such as
heap size or CPU time has been exceeded… When exceptions are uncatchable, catch
blocks, as well as finally blocks if any, aren't executed" (`apexdev.txt`
L39721–L39728).

**When it occurs:** Any defensive-logging design that assumes it will get to
record the failure that mattered most.

**How to avoid:** Log *before* you enter the expensive block, not after it fails.
Check headroom proactively (`Limits.getCpuTime()` against
`Limits.getLimitCpuTime()`) and hand the remainder to a queueable while you still
have a running transaction — see `apex/apex-limits-monitoring` for the guard
pattern.

---

## Static State Survives Trigger Re-Entry While Governor Limits Reset

**What happens:** A static `Map` used as a per-transaction cache keeps growing
across trigger invocations even though each invocation appears to start clean.
"If an Apex DML request causes a trigger to fire multiple times, the static
variables persist across these trigger invocations" (`apexdev.txt`
L3738–L3743), and for Bulk API specifically, "governor limits are reset between
these trigger invocations for the same HTTP request. Static variables aren't
reset within the multiple trigger invocations for the same Bulk API request"
(`apexdev.txt` L3785–L3792).

**When it occurs:** A 10,000-row Bulk API load hitting a trigger that caches
describes, query results, or "already processed" ids in a static collection. The
limit counters reset per chunk, so nothing warns you; the static cache is the one
thing that keeps accumulating.

**How to avoid:** Bound every static cache (cap its size, or key it to the current
chunk and clear it), and never cache whole sObjects in a static when ids would
do. A static defined *in a trigger* is a different trap — it "doesn't retain its
value between different trigger contexts within the same transaction, such as
between before insert and after insert invocations" (`apexdev.txt` L3761–L3763),
so recursion guards belong in a class.

---

## `Database.Stateful` Keeps Everything, Including What Is Eating Your Heap

**What happens:** A batch job runs 40 chunks fine and dies on chunk 41 with a
heap error. Without `Database.Stateful`, "all member variables are reset to their
initial state at the start of each transaction" (`apexdev.txt` L17742–L17743),
and "Apex governor limits are reset for each execution of `execute`"
(`apexdev.txt` L17709–L17710). Adding `Database.Stateful` to accumulate a summary
also makes every other instance member survive: "only instance member variables
retain their values between transactions. Static member variables don't"
(`apexdev.txt` L17519–L17524).

**When it occurs:** Someone adds `Database.Stateful` for a running total or an
error list, and the error list is a `List<SObject>` rather than a `List<String>`.

**How to avoid:** When you need state across chunks, keep it primitive and
bounded — counters, ids, message strings — and write detail rows out with DML per
chunk instead of holding them. The `Database.Stateful` accumulator is the first
thing to size-check when a batch fails late rather than early.

---

## A SOQL For Loop Trades Heap For CPU

**What happens:** A heap failure is fixed by converting `List<X> all = [SELECT …]`
into `for (List<X> chunk : [SELECT …])`, and the transaction then fails on CPU
instead. The guide states the trade directly: "Developers can avoid the limit on
heap size by using a SOQL for loop to process query results that return multiple
records. However, this approach can result in more CPU cycles being used"
(`apexdev.txt` L10012–L10016), and again at `apexdev.txt` L9601–L9602 where the
extra cost is attributed to increased DML calls.

**When it occurs:** Applying the guide's heap remedy (`apexdev.txt`
L20271–L20285) to a transaction whose real constraint was already CPU.

**How to avoid:** Measure which ceiling you are near before choosing. If both are
tight, the chunking has to move to Batch Apex, where each `execute` gets a fresh
set of limits, rather than to a for loop inside one transaction.

---

## `transient` Reduces Serialized State, Not Live Heap

**What happens:** A variable is marked `transient` to "save memory" and heap usage
does not move. `transient` declares "instance variables that can't be saved, and
shouldn't be transmitted as part of the view state for a Visualforce page"
(`apexdev.txt` L4743–L4752). It is not Visualforce-only — it also applies to
"controllers, controller extensions, or classes that implement the `Batchable` or
`Schedulable` interface" (`apexdev.txt` L4748–L4750), and "Variables that are
declared transient are ignored by serialization and deserialization and the value
is set to null in Queueable Apex" (`apexdev.txt` L15975–L15976). All of those are
about the serialized copy between requests or jobs, never about the live heap of
the running transaction.

**When it occurs:** A large `Map` inside a `Queueable` is marked `transient` to
fix a heap error inside `execute`; it fixes nothing there, and it silently
nulls the field for the *next* job in a chain.

**How to avoid:** Use `transient` to shrink view state and job payloads (`apexdev.txt`
L16986–L16988 recommends exactly this for scheduled Apex). To reduce live heap,
shrink what you query, chunk it, or release references you are finished with.

---

## Reading `Limits` After `Test.stopTest()` Measures The Wrong Transaction

**What happens:** A performance test asserts on CPU after `Test.stopTest()` and
either always passes or reports a number that has nothing to do with the code
under test. "Any code that executes after the call to startTest and before
stopTest is assigned a new set of governor limits" (`apexrefguide.txt` L241071),
and "Any code that executes after the stopTest method is assigned the original
limits that were in effect before startTest was called" (`apexrefguide.txt`
L241086–L241087).

**When it occurs:** Any test written in the natural order — act, stop, assert —
where the assertion itself reads `Limits.getCpuTime()`.

**How to avoid:** Capture the before and after readings into local `Integer`
variables *inside* the `startTest`/`stopTest` block, then assert on those locals
afterwards. `references/code-examples.md` §4 shows the shape. Remember too that
"Limits apply individually to each testMethod"
(`salesforce_app_limits_cheatsheet.txt` L180), so a passing test bounds one
method, not the save order it will run inside.
