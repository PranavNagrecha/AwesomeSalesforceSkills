# Gotchas — Flow Invocable From Apex

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Input parameter MUST be a `List<T>`

**What happens:** A signature like `public static Result doWork(String input)` fails to compile with `"Method annotated with @InvocableMethod must have a single argument of type List<X>"`.

**When it occurs:** Any time an author treats the invocable as if Flow calls it per record.

**How to avoid:** Always declare `public static List<Response> method(List<Request> requests)`. Flow passes a list regardless of whether the caller looks single-record.

---

## Gotcha 2: Return list length must match input list length

**What happens:** Flow's Loop element walks inputs and outputs in parallel with the same index. A shorter output list silently shifts downstream references to the wrong input record.

**When it occurs:** When an author "skips" records that don't meet a criterion by not appending anything to the output list.

**How to avoid:** Return exactly `inputs.size()` elements. For records you would skip, add a response with all null fields or an explicit `status='skipped'` marker.

---

## Gotcha 3: `@InvocableVariable` only works on `public` instance fields

**What happens:** Private fields or properties are invisible to Flow Builder. The action appears to be missing a variable the admin expects.

**When it occurs:** Refactoring a wrapper class to use getters/setters, or accidentally making the field `private`.

**How to avoid:** Keep wrapper fields as `public` instance fields. Validate in code review with a search for `private.*@InvocableVariable`.

---

## Gotcha 4: `callout=true` is not optional for HTTP callouts

**What happens:** Runtime error `System.CalloutException: Callout from triggers are currently not supported` when invoked from a record-triggered context.

**When it occurs:** Invocable issues a callout but the annotation says `callout=false` (or is omitted).

**How to avoid:** Set `callout=true` on the `@InvocableMethod` annotation whenever the method issues HTTP requests. This also informs Flow Builder that the action can only be called from async contexts.

---

## Gotcha 5: Flow API name, not label, in `Flow.Interview.createInterview`

**What happens:** Runtime `Flow.InterviewException: No flow named 'Deactivate Stale Accounts'`.

**When it occurs:** Apex passes the flow's admin-facing label instead of its developer name.

**How to avoid:** Use the API name (underscores, no spaces). Verify by opening the flow in Setup; the developer name is shown next to the label.

---

## Gotcha 6: Static fields leak across invocations in the same transaction

**What happens:** Values set in a static Map persist across multiple invocable calls in the same transaction — even across different flow interviews.

**When it occurs:** Author caches a lookup map as a `static Map<String, Thing>` for "efficiency". Works in tests with one flow. Under mixed production load, data from flow A leaks into flow B's response.

**How to avoid:** Build lookup maps as local variables inside the invocable method. Use `Platform Cache` with explicit partition + expiry if genuine cross-call caching is required.

---

## Gotcha 7: Output variables must be marked "Available for Input / Output" to be readable from Apex

**What happens:** `flow.getVariableValue('myOutput')` returns `null` with no error, even though the flow populated the variable.

**When it occurs:** Apex calls a flow via `Flow.Interview`, but the flow's variable has only "Available for Input" checked — not Output.

**How to avoid:** In Flow Builder, open the variable's resource dialog and tick both "Available for Input" and "Available for Output" when Apex needs to read it.

---

## Gotcha 8: Sharing posture defaults to the caller's context

**What happens:** An invocable declared without `with sharing` runs in the caller's context. In practice, the caller is usually a flow running with the end user's access — but a flow running via `@AuraEnabled` from LWC may run with different access.

**When it occurs:** Security review surprises; admins report "why can this user see accounts they shouldn't?"

**How to avoid:** Always declare sharing explicitly on invocable classes: `public with sharing class MyInvocable`. Default to `with sharing` unless you have a documented reason for `without sharing`.

---

## Gotcha 9: `AuraHandledException` vs plain `Exception`

**What happens:** A plain `throw new Exception('DB error: ' + e.getMessage())` exposes internal details to the flow's fault path, which may surface to end users.

**When it occurs:** Copy-pasting error handling from LWC controllers.

**How to avoid:** Wrap internal exceptions: `throw new AuraHandledException('Unable to process request.');`. Log the full internal exception to a custom logger; don't expose it to the flow.

---

## Gotcha 10: Package namespacing breaks flow references

**What happens:** Migrating an invocable into a managed package changes its API name from `MyInvocable` to `mynamespace__MyInvocable`. Flows referencing the old name break in subscriber orgs.

**When it occurs:** Moving code from unmanaged to managed package.

**How to avoid:** Either (a) keep the class in the default namespace if flows reference it, or (b) version the invocable with a wrapper class in the default namespace that delegates to the packaged class, preserving the flow-facing API name.

---

## Gotcha 11: Invocable DTOs serialize on flow pause

**What happens:** If a screen flow uses the invocable's output then pauses, the wrapper class must be JSON-serializable. Complex types (Database.SaveResult, Blob) break the pause with `InvalidStateException`.

**When it occurs:** Returning platform types as `@InvocableVariable` fields.

**How to avoid:** Use simple types (primitives, Strings, sObjects) in wrapper fields. Convert platform types to primitives before returning.
