# Gotchas — Continuation Callouts

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Continuation Cannot Be Used Outside a User-Initiated UI Request Context

**What happens:** Instantiating `new Continuation(n)` inside a trigger, Batch Apex `execute` method, Scheduled Apex `execute` method, `@future` method, or any other asynchronous Apex context throws `System.ContinuationException` at runtime. The class is only valid when the originating transaction is a Visualforce page action request or an LWC `@AuraEnabled(continuation=true)` method invoked from the Lightning runtime.

**When it occurs:** When a developer tries to "simplify" the integration by moving a Continuation call into a helper method that gets reused across both UI and async contexts, or when copying a Continuation pattern into a Queueable class for batch-mode use.

**How to avoid:** Audit every call site before adding Continuation logic. If the Apex class is also called from a trigger, batch, or scheduled job, do not add Continuation there — use `Queueable` with `AllowsCallouts` for asynchronous contexts, and reserve `Continuation` strictly for the Visualforce or LWC entry points. Use a separate controller class for each context.

---

## Gotcha 2: Non-Serializable `state` Silently Causes Callback Failure

**What happens:** The `Continuation.state` property is serialized by the platform between Phase 1 (startRequest) and Phase 2 (callback). If the assigned value is not JSON-serializable — for example, an SObject with relationship fields loaded via SOQL, a `Type` reference, a `Blob`, or any class that implements `Comparable` with non-primitive fields — the platform throws `System.SerializationException` when attempting to invoke the callback. Because this exception occurs after the HTTP response returns, it may surface as a cryptic page error rather than a clear callout failure.

**When it occurs:** Most commonly when a developer passes a full SObject (e.g., `Account` with `Contacts` subquery) as state, or when a wrapper class is used that contains a reference to a non-serializable type.

**How to avoid:**
- Pass only primitive scalars (`String`, `Integer`, `Decimal`), `List<String>`, or `Map<String, String>` as state.
- If a complex object is needed, serialize it manually before assigning: `con.state = JSON.serialize(myWrapper);` then deserialize in the callback: `MyWrapper w = (MyWrapper) JSON.deserialize((String) state, MyWrapper.class);`.
- Write a test that invokes `Test.invokeContinuationMethod()` — serialization errors surface during test execution, not just at runtime.

---

## Gotcha 3: `continuationMethod` Must Be a Public Instance Method With the Exact Signature

**What happens:** The platform resolves `continuationMethod` by name at runtime using reflection. If the method name is misspelled, the method is `private` or `static`, or the method signature does not match `public Object methodName(List<String> labels, Object state)`, the callback silently never fires. No exception is thrown in Phase 1. The page simply hangs until the Continuation timeout elapses, then returns an empty or stale page state.

**When it occurs:**
- Typo in `con.continuationMethod = 'processRespone'` (missing 's').
- Callback declared as `private Object processResponse(...)` instead of `public`.
- Callback declared as `public static Object processResponse(...)` — static is not allowed.
- Signature mismatch: `public Object processResponse(HttpResponse res)` instead of the required `(List<String> labels, Object state)`.

**How to avoid:**
- Always verify the callback method is `public`, non-static, and has the exact signature after writing it.
- Use a test that calls `Test.invokeContinuationMethod(controllerInstance, con)` — if the method is not found or has the wrong signature, the test framework throws a descriptive error immediately.
- Consider defining an Apex interface `IContinuationCallback` with the required signature and having the controller implement it; this enforces signature correctness at compile time.

---

## Gotcha 4: Maximum 3 Parallel Requests Per Continuation Object

**What happens:** Calling `con.addHttpRequest(req)` more than three times throws `System.LimitException: Too many callouts: 4` (or a similar limit message) at the point of the fourth `addHttpRequest` call in Phase 1.

**When it occurs:** When aggregating data from more than three APIs in a single page load — common in dashboard-style pages that call four or more microservices.

**How to avoid:** Chain Continuation requests by returning a new `Continuation` from the callback method instead of `null`. The callback can fire a second round of up to three callouts, supporting up to six total across two rounds. For more than six, evaluate whether all data is truly needed on a single page load, or whether background jobs with polling are more appropriate.

---

## Gotcha 5: Continuation Timeout Clock Starts at Request Dispatch, Not Page Load

**What happens:** The `Continuation` timeout value is measured from when the platform dispatches the HTTP request, not from when the user clicked the button. If Phase 1 has significant Apex processing before `return con`, a few seconds of governor time are already consumed before the clock even starts on the external callout — but the *page-level* timeout (Salesforce's 120-second hard limit) includes all Phase 1 time. If Phase 1 takes 30 seconds of Apex processing and the callout takes 100 seconds, the combined 130 seconds exceeds the platform's outer limit.

**When it occurs:** Phase 1 controller actions that execute complex SOQL queries, loops, or DML before building the `Continuation` object.

**How to avoid:** Keep Phase 1 lean. Move expensive Apex logic into the callback (Phase 2) where it processes the returned data. Set the Continuation timeout to the maximum you expect the *external service* to take, while keeping Phase 1 processing to a minimum.
