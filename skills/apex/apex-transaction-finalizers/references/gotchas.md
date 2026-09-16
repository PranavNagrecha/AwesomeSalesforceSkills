# Gotchas — Apex Transaction Finalizers

Non-obvious Salesforce platform behaviors that cause real production problems in this domain. Line references are into the Apex Developer Guide v67.0, Summer '26 (`apexdev`) and the Apex Reference Guide v67.0 (`apexrefguide`).

## Gotcha 1: Finalizer Execution Is Not Guaranteed Under Unexpected Termination

**What happens:** the Finalizer registration is discarded and no callback fires. Nothing raises, nothing retries, and the only trace is an `AsyncApexJob` row that never got a matching compensation record.

**When it occurs:** the guide names one cause explicitly — "If a job request is terminated unexpectedly, such as a database shutdown during system upgrade, the transaction finalizer can fail to execute" (apexdev L16533–16534). Practitioners also widely report that `System.abortJob()` on the parent skips the Finalizer. UNVERIFIED (2026-09-05): the v67.0 Apex Developer Guide does not mention `System.abortJob()` anywhere in the Transaction Finalizers section, and the previous version of this file claimed the abort behaviour was "confirmed in the official Apex Developer Guide" — it is not. Treat abort as untested until you have run it in a scratch org.

**How to avoid:** do not let a Finalizer be the only mechanism that releases a lock or clears an "in flight" flag. Pair it with a Schedulable that queries `AsyncApexJob WHERE Status IN ('Aborted','Failed')` and compensates for anything with no dead-letter row — see apex/scheduled-apex-failure-detection-and-monitoring.

---

## Gotcha 2: `FinalizerContext` Has Four Methods, and `getJobId()` Is Not One of Them

**What happens:** `ctx.getJobId()` fails to compile against a plain `FinalizerContext` — or, worse, compiles and returns the wrong thing in a class that implements both `Queueable` and `Finalizer`, where `QueueableContext.getJobId()` (apexdev L16380) is also in scope.

**When it occurs:** whenever the two interfaces live in one class, which the guide itself recommends ("you can implement both Queueable and Finalizer interfaces with the same class", apexdev L16296) and both of its worked examples do (apexdev L16373, L16477). The guide's own sample code uses `ctx.getJobId()` in the Queueable half and `ctx.getAsyncApexJobId()` in the Finalizer half, four lines apart.

**How to avoid:** the interface "contains four methods: getAsyncApexJobId, getRequestId, getResult, and getException" (apexrefguide L215612–215614). Use `getAsyncApexJobId()` for anything that joins to `AsyncApexJob`, and `getRequestId()` only for Event Monitoring correlation — the two share a value with the parent Queueable but are not interchangeable as keys.

---

## Gotcha 3: The Finalizer's Own State Survives; the Parent's Database Work Does Not

**What happens:** developers assume one of two opposite falsehoods. Either they assume nothing crosses the boundary and pass the payload through a query that returns rolled-back-away rows, or they assume everything crosses and read the parent's local variables.

**When it occurs:** the truth is split. "The Queueable job and the Finalizer run in separate Apex and Database transactions" (apexdev L16297) — so the parent's uncommitted DML is gone. But "The Finalizer framework uses the state of the Finalizer object (if attached) at the end of Queueable execution. Mutation of the Finalizer state, after it's attached, is therefore supported" (apexdev L16358–16359), and "The finalizer state is preserved even if the Queueable job fails" (apexdev L16369–16370) — so fields on the *Finalizer instance* do cross.

**How to avoid:** treat the Finalizer object as the only channel. Push everything the compensation needs onto it (`finalizer.note(...)`, the retry count, the ID list) *before* the code that can throw, exactly as the guide's `LoggingFinalizer.addLog()` does (apexdev L16401). Never query for records the parent was mid-way through writing.

---

## Gotcha 4: Only One Async Job May Be Enqueued — and It Is Not Queueable-Only

**What happens:** a second enqueue in the same Finalizer fails, and because the Finalizer's exception has nowhere to propagate, both the retry and whatever came after it are lost.

**When it occurs:** the classic shape is a Finalizer that enqueues a logging Queueable and then enqueues the retry job. The guide's wording is broader than most code assumes: "You can enqueue a single asynchronous Apex job (Queueable, Future, or Batch) in the finalizer's implementation of the execute method" (apexdev L16355–16356). A `Database.executeBatch(...)` or a call to a `@future` method spends the same single slot as `System.enqueueJob`. UNVERIFIED (2026-09-05): the guide does not name the exception type thrown on the second enqueue; earlier versions of this skill asserted `System.AsyncException` without a source.

**How to avoid:** do the logging synchronously with DML inside the Finalizer — it has a DML budget of its own — and reserve the one slot for the retry or compensation job. Where async logging is genuinely required, fold it into the retry Queueable so one enqueue covers both.

---

## Gotcha 5: The Retry Chain Stops at Five, by Failing

**What happens:** an "unbounded" retry Finalizer does not loop forever. It re-enqueues four more times and then the enqueue call itself fails on the fifth consecutive failure — leaving no dead-letter record, because the code that would have written one was in the `else` branch that never ran.

**When it occurs:** "A Queueable job that failed due to an unhandled exception can be successively re-enqueued five times by a transaction finalizer. This limit applies to a series of consecutive Queueable job failures. The counter is reset when the Queueable job completes without an unhandled exception" (apexdev L16293–16295). The guide's own retry sample annotates the enqueue `// This call fails after 5 times when it hits the chaining limit` (apexdev L16523). The reset-on-success clause is the trap for intermittent failures: a job that alternates fail/succeed/fail never accumulates toward the cap and can retry indefinitely in wall-clock terms.

**How to avoid:** carry an explicit attempt counter on the Finalizer and stop at 3 or 4, below the platform ceiling, so your dead-letter DML runs. For intermittent failures, also track the attempt count on the record or payload rather than only on the in-memory chain, since the platform's counter resets on every success.

---

## Gotcha 6: Synchronous Governor Limits Apply — Except for Three Things

**What happens:** a Finalizer written on the assumption of "async limits" hits the 100-query synchronous SOQL ceiling instead of the 200-query async one, and dies mid-compensation.

**When it occurs:** "Synchronous governor limits apply for the Finalizer transaction, except in these cases where asynchronous limits apply: • Total heap size • Maximum number of Apex jobs added to the queue with System.enqueueJob • Maximum number of methods with the future annotation allowed per Apex invocation" (apexdev L16298–16303). So the Finalizer gets the *async* 12 MB heap and the *async* enqueue allowance, but the *synchronous* CPU, SOQL and DML ceilings.

**How to avoid:** size Finalizer work as if it were a synchronous controller action, not a batch. If the compensation needs real query volume, spend the one enqueue slot on a Queueable and do the heavy work there.

---

## Gotcha 7: `transient` Fields Are Silently Empty in the Finalizer

**What happens:** the buffered log, the ID list, or the retry counter arrives as `null` or an empty collection in `execute(FinalizerContext)`. There is no error — the field simply was not serialized.

**When it occurs:** "Variables that are declared transient are ignored by serialization and deserialization, and therefore don't persist in the Transaction Finalizer" (apexdev L16360–16362). The same clause exists for Queueable state (apexdev L15975–15976). `transient` is a common reflex when a class holds large collections and someone is trying to stay under heap, so it tends to be added late, by someone who is not thinking about the Finalizer.

**How to avoid:** never mark a field `transient` on a class that implements `Finalizer`. Trim the payload to IDs instead of marking the sObject list transient, and assert on the buffered state in the test class so the regression is caught at deploy time.

---

## Gotcha 8: Attaching in the Wrong Context, or Twice, Produces Log-Only Errors

**What happens:** the job runs and the compensation never happens, with no exception at the call site. The evidence exists only in the Apex debug log.

**When it occurs:** the guide's error table names the exact strings (apexdev L16543–16567): `More than one Finalizer cannot be attached to same Async Apex Job` when `System.attachFinalizer()` runs twice in the same Queueable instance; `System.attachFinalizer(Finalizer) is not allowed in this context` when it runs anywhere that is not executing a Queueable — a Batch `execute`, a trigger, a `@future` method, or inside another Finalizer's `execute`; `Class {0} must implement the Finalizer interface` when the argument is the wrong type, which is possible because the signature is `public static void attachFinalizer(Object finalizer)` (apexrefguide L238804) and so accepts anything at compile time; and `Argument cannot be null`.

**How to avoid:** call `attachFinalizer` exactly once, as the first statement of the Queueable's `execute(QueueableContext)`, with a non-null instance. To chain guaranteed behaviour, spend the one enqueue slot on a new Queueable that attaches its own Finalizer — `Queueable A → Finalizer A → Queueable B → Finalizer B`.

---

## Gotcha 9: A Finalizer That Throws Has Nowhere to Report

**What happens:** the compensation half-runs and the failure is invisible to every monitoring tool that watches `AsyncApexJob`. "Only one finalizer instance can be attached to any Queueable job" (apexdev L16354), so there is no second callback to catch it.

**When it occurs:** the runtime errors are logged as `Error processing finalizer for queueable job id: {0}` and `Error processing the finalizer (class name: {0}) for the queueable job id: {1} (queueable class id: {2})`, and the guide notes the cause "can be an unhandled catchable exception or uncatchable exception (such as a LimitException), or, less commonly, an internal system error" (apexdev L16578–16587). A validation rule or a required-field change on the error object is the usual trigger: the dead-letter insert starts failing and the pipeline goes quiet.

**How to avoid:** wrap every DML statement in the Finalizer in `try/catch`, or use `Database.insert(records, false)` as the guide's own logging example does (apexdev L16435), and fall back to `System.debug(LoggingLevel.ERROR, ...)`. Alert on the *absence* of a dead-letter row for a failed `AsyncApexJob`, not only on its presence.

---

## Gotcha 10: A Rolled-Back Enqueuing Transaction Means No Job and No Finalizer

**What happens:** the Queueable never runs at all, so nothing the Finalizer would have done happens either. The `AsyncApexJob` row is absent rather than failed, which defeats any monitor that looks for failures.

**When it occurs:** "If an Apex transaction rolls back, any queueable jobs queued for execution by the transaction aren't processed" (apexdev L15961). This bites when the enqueue happens inside a trigger or a controller that later throws, or inside a `Database.rollback(savepoint)` path — the enqueue looks committed because `System.enqueueJob` already returned an ID.

**How to avoid:** enqueue after the risky DML, not before, and never treat the ID returned by `System.enqueueJob` as proof the job exists. If the work must survive a caller rollback, publish a Platform Event instead and subscribe with the Queueable — see apex/apex-queueable-patterns.

---

## Checker Ignores Comments And String Literals

**What happens:** The skill checker flags a keyword that appears only in a comment or a string literal (for example a note that `WITH SECURITY_ENFORCED` is not used, or an assertion message that mentions `EventBus.publish`).

**When it occurs:** Before the checker blanked `//` line comments, `/* … */` block comments, and `'…'` string literals to spaces (same length, newlines preserved) for code-pattern rules.

**How to avoid:** Trust the checker on executable code only. Mentions inside comments and string literals are ignored for pattern matches; rules that intentionally read comments (for example a `// reason:` search) still read the original text.
