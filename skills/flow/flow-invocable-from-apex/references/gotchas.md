# Gotchas — Flow Invocable From Apex

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Input parameter MUST be a `List<T>`

**What happens:** A signature like `public static Result doWork(String input)` does not meet the guide's rule of "at most one input parameter" whose type is a list (apexdev 264 L5486-5490). UNVERIFIED (2026-10-20): the exact compile-error text `"Method annotated with @InvocableMethod must have a single argument of type List<X>"` is not in the corpus.

**When it occurs:** Any time an author treats the invocable as if Flow calls it per record.

**How to avoid:** Always declare `public static List<Response> method(List<Request> requests)`. Flow passes a list regardless of whether the caller looks single-record.

---

## Gotcha 2: Return list length must match input list length

**What happens:** "The i-th Output entry must correspond to the i-th Input entry" and the lists "must match on both the size and the order" (apexdev 264 L5510-5512). A shorter output list shifts later outputs onto the wrong inputs. UNVERIFIED (2026-10-20): that this happens silently through Flow's Loop element is not stated in the corpus.

**When it occurs:** When an author "skips" records that don't meet a criterion by not appending anything to the output list.

**How to avoid:** Return exactly `inputs.size()` elements. For records you would skip, add a response with all null fields or an explicit `status='skipped'` marker.

---

## Gotcha 3: `@InvocableVariable` only works on `public` or `global` member variables

**What happens:** "Only global and public variables can be invocable variables"; a property, a static or local variable, a final variable and a protected or private variable cannot be (apexdev 264 L5773-5778). The action is then missing a variable the admin expects. UNVERIFIED (2026-10-20): the corpus does not say whether such a variable is silently invisible or rejected at save. Starting in API version 66.0 the wrapper class also needs a visible no-argument constructor (apexdev 264 L5792-5794).

**When it occurs:** Refactoring a wrapper class to use getters/setters, or accidentally making the field `private`.

**How to avoid:** Keep wrapper fields as `public` instance fields. Validate in code review with a search for `private.*@InvocableVariable`.

---

## Gotcha 4: `callout=true` tells a screen flow the action calls out

**What happens:** The `callout` modifier "identifies whether the method calls to an external system" (apexdev 264 L5461-5462). Screen flows use it to decide whether the action can run safely in the current transaction; with Transaction Control set to let the flow decide and uncommitted work pending, the flow commits, starts a new transaction and then makes the call (apexdev 264 L27275-27282). With `callout=false` the flow executes the action in the current transaction (L27284). Apex's own rule applies there: "You can't make a callout when there are pending operations in the same transaction" (apexdev 264 L36340-36342). UNVERIFIED (2026-10-20): the error text `System.CalloutException: Callout from triggers are currently not supported` and any effect on record-triggered flows are not in the corpus.

**When it occurs:** The method calls an external system but the annotation says `callout=false` (or omits it) and a screen flow has pending DML.

**How to avoid:** Set `callout=true` on the `@InvocableMethod` annotation whenever the method calls an external system, and set the action's Transaction Control in the screen flow (apexdev 264 L27281). The earlier claim that the modifier restricts the action to asynchronous contexts is not supported by the guide.

---

## Gotcha 5: Flow API name, not label, in `Flow.Interview.createInterview`

**What happens:** "If the flow doesn't exist in the current org, a TypeException is thrown" (apexref 262 L158128). The earlier text named a `Flow.InterviewException`; the guide names `TypeException`.

**When it occurs:** Apex passes the flow's admin-facing label instead of its developer name.

**How to avoid:** Use the API name: the parameter is documented as "The flow's API name" (apexref 262 L158101). Verify by opening the flow in Setup; the developer name is shown next to the label.

---

## Gotcha 6: Static fields leak across invocations in the same transaction

**What happens:** "The value of a static variable persists within the context of a single transaction and is reset across transaction boundaries" (apexdev 264 L3746-3748), so values set in a static Map persist across multiple invocable calls in the same transaction, including calls from different flow interviews.

**When it occurs:** Author caches a lookup map as a `static Map<String, Thing>` for "efficiency". Works in tests with one flow. Under mixed production load, data from flow A leaks into flow B's response.

**How to avoid:** Build lookup maps as local variables inside the invocable method. Use `Platform Cache` with explicit partition + expiry if genuine cross-call caching is required.

---

## Gotcha 7: Variables Apex reads or sets must be marked input and output

**What happens:** `getVariableValue` "returns null" when the variable "can't be found in that flow" and checks existence "at run time only, not at compile time" (apexref 262 L158151-158153). The Metadata API flags are `isInput` (can be set at the start of the flow) and `isOutput` (value can be accessed from Visualforce controllers and other flows); both default to False for variables created in API 25.0 and later (api_meta 264 L75629-75655). UNVERIFIED (2026-10-20): that Apex reading a variable with `isOutput` false returns null rather than failing is not stated in the corpus.

**When it occurs:** Apex calls a flow via `Flow.Interview`, but the flow's variable has only "Available for Input" checked — not Output. UNVERIFIED (2026-10-20): the Flow Builder checkbox labels are not in the corpus; the flags are `isInput` and `isOutput`.

**How to avoid:** In Flow Builder, open the variable's resource dialog and tick both "Available for Input" and "Available for Output" when Apex needs to read it. Name the variable exactly: the guide notes that `getVariableValue` checks the variable only at run time.

---

## Gotcha 8: The default sharing posture depends on the class's API version

**What happens:** The default depends on the class's API version. In API version 67.0 and later, "classes without an explicit sharing declaration run in with sharing mode"; in 66.0 and earlier an undeclared class is `with sharing` when any class in its inheritance chain is saved at 67.0 or later or when it is an Aura controller or `@AuraEnabled` class, takes its caller's mode if it is not an entry point, and otherwise runs `without sharing` (apexdev 264 L11930-11937).

**When it occurs:** Security review surprises; admins report "why can this user see accounts they shouldn't?"

**How to avoid:** Always declare sharing explicitly on invocable classes: `public with sharing class MyInvocable`. Default to `with sharing` unless you have a documented reason for `without sharing`. The Apex Developer Guide states that sharing rules are "always enforced by default" and that you must declare `without sharing` to turn them off (apexdev 264 L11941-11943).

---

## Gotcha 9: `AuraHandledException` vs plain `Exception`

**What happens:** A plain `throw new Exception('DB error: ' + e.getMessage())` exposes internal details to the flow's fault path, which may surface to end users. UNVERIFIED (2026-10-20): the corpus does not describe what a flow fault path shows for either exception type; the Apex Reference describes `AuraHandledException` as returning "a custom error message to a JavaScript controller" (apexref 262 L214924).

**When it occurs:** Copy-pasting error handling from LWC controllers.

**How to avoid:** Wrap internal exceptions: `throw new AuraHandledException('Unable to process request.');`. Log the full internal exception to a custom logger; don't expose it to the flow.

---

## Gotcha 10: Package namespacing breaks flow references

**What happens:** Migrating an invocable into a managed package changes its API name from `MyInvocable` to `mynamespace__MyInvocable`. Flows referencing the old name break in subscriber orgs. UNVERIFIED (2026-10-20): the rename is not stated in the corpus. The guide does say that "Only global invocable methods appear in Flow Builder" in the subscriber org and that a method added to a package cannot be removed in later versions (apexdev 264 L5514-5518).

**When it occurs:** Moving code from unmanaged to managed package.

**How to avoid:** Either (a) keep the class in the default namespace if flows reference it, or (b) version the invocable with a wrapper class in the default namespace that delegates to the packaged class, preserving the flow-facing API name.

---

## Gotcha 11: Invocable DTOs serialize on flow pause

**What happens:** If a screen flow uses the invocable's output then pauses, the wrapper class must be JSON-serializable. Complex types (Database.SaveResult, Blob) break the pause with `InvalidStateException`. UNVERIFIED (2026-10-20): pause serialization and this exception are not in the corpus. What is documented: an invocable variable must be a primitive other than Object, an sObject, or a list of primitives, sObjects or Apex-class objects (apexdev 264 L5780-5784).

**When it occurs:** Returning platform types as `@InvocableVariable` fields.

**How to avoid:** Use simple types (primitives, Strings, sObjects) in wrapper fields. Convert platform types to primitives before returning.
