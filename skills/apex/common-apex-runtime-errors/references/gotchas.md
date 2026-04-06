# Gotchas — Common Apex Runtime Errors

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: LimitException is uncatchable — try/catch is silently useless

**What happens:** A `catch (System.LimitException e)` block compiles without error but never executes. When a governor limit is breached, the platform terminates the transaction immediately, bypassing all catch and finally blocks. The exception propagates to the caller as if no try/catch existed.

**When it occurs:** Any trigger, class, or test that wraps SOQL, DML, or CPU-intensive code in a try/catch hoping to gracefully handle limit overruns. Particularly common after migrating code from other languages where resource limits throw catchable exceptions.

**How to avoid:** Never rely on catching LimitException. Use `Limits.getQueries()`, `Limits.getLimitQueries()`, `Limits.getDmlStatements()`, `Limits.getCpuTime()`, etc. to measure proximity before executing the operation. If limits are consistently close, the architecture needs to change (bulkification, Queueable, Batch Apex).

---

## Gotcha 2: Scalar SOQL returns null on zero rows — the NPE hits the next line, not the query

**What happens:** When a SOQL query assigned to a scalar SObject variable matches zero rows, the variable is set to `null` — the platform does not throw `QueryException` at the query site. The `QueryException: List has no rows` error is thrown only when the zero-row scalar assignment is the direct result of a single-row query that Apex evaluates as requiring one row. The more common outcome is a `NullPointerException` on the first field access after the assignment.

**When it occurs:** Code like `Account a = [SELECT Id FROM Account WHERE Id = :someId];` followed by `a.Name`. The stack trace shows line N+1 (the field access), not line N (the query). Developers spend time looking at the wrong line.

**How to avoid:** Always use `List<SObject>` for SOQL queries where the result count is not guaranteed. The `QueryException: List has no rows` form only fires when the query is written in a context where the platform strictly requires exactly one row. In most cases you get a null reference instead — so default to Lists.

---

## Gotcha 3: DmlException.getDmlIndex(i) vs. SaveResult array index are different things

**What happens:** When using `Database.insert(records, true)` (allOrNone=true, the default), a `DmlException` is thrown and `e.getDmlIndex(i)` returns the index of the failed record in the original input list. When using `Database.insert(records, false)` (allOrNone=false), no exception is thrown and the `SaveResult` array has the same length as `records` — index i in `SaveResult` directly maps to index i in `records`. Confusing these two access patterns causes developers to log the wrong source record when debugging DML failures.

**When it occurs:** Mixed use of allOrNone=true and allOrNone=false in the same codebase, or when copy-pasting error-logging code between the two patterns.

**How to avoid:** For `allOrNone=true` / exception mode: use `e.getDmlIndex(i)` inside a for loop over `e.getNumDml()` to find the source record. For `allOrNone=false` / SaveResult mode: iterate `results` with `for (Integer i = 0; i < results.size(); i++)` and use `records[i]` directly — no `getDmlIndex` needed.

---

## Gotcha 4: TypeException from JSON.deserialize when the JSON shape drifts from the Apex type

**What happens:** `JSON.deserialize(jsonString, MyClass.class)` throws `TypeException` if the JSON contains a field with a value that cannot be coerced to the target Apex type — for example, a string `"true"` in JSON where the Apex field is `Boolean`, or an integer where the Apex field is `Date`. The error message is often generic and does not indicate which field caused the mismatch.

**When it occurs:** Integrations that receive JSON from external systems where the schema is not strictly controlled. Also common when Apex types use `Decimal` but the JSON sends an integer, or vice versa.

**How to avoid:** Use `JSON.deserializeUntyped()` to get a `Map<String, Object>` first, validate the types of critical fields manually, then map to Apex types. Alternatively, catch `JSONException` (not `TypeException`) and log the raw JSON for forensics — `JSON.deserialize` wraps type coercion failures in `JSONException` in some versions, so test which exception class is thrown in your org's API version.

---

## Gotcha 5: ListException on Trigger.new[0] when the trigger fires on delete

**What happens:** A trigger accesses `Trigger.new[0]` or `Trigger.new` directly, assuming the list is non-empty. On `before delete` and `after delete` events, `Trigger.new` is null — only `Trigger.old` is populated. Accessing `Trigger.new[0]` on a delete event throws `NullPointerException`, not `ListException`.

**When it occurs:** Trigger handlers that are designed for insert/update but are accidentally deployed with `before delete` or `after delete` events included in the trigger definition.

**How to avoid:** In the trigger handler, check `Trigger.isDelete` before accessing `Trigger.new`. Use a trigger framework that routes context-specific logic to separate handler methods keyed by `TriggerOperation` enum values (`BEFORE_INSERT`, `BEFORE_DELETE`, etc.) rather than checking `Trigger.new` defensively everywhere.
