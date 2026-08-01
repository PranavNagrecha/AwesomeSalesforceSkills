# LLM Anti-Patterns — Apex Future Method Patterns

Common mistakes AI coding assistants make with `@future`.

## Anti-Pattern 1: Passing SObjects as parameters

**What the LLM generates:**

```
@future
public static void processAccounts(List<Account> accounts) { ... }
```

**Why it happens:** Model writes like a normal method.

**Correct pattern:**

```
@future only accepts primitives and collections of primitives.
Pass Ids and re-query inside:

@future
public static void processAccounts(Set<Id> accountIds) {
    List<Account> accs = [SELECT Id, Name FROM Account WHERE Id IN :accountIds];
    ...
}

Or serialize: JSON.serialize(records) → deserialize inside.
```

**Detection hint:** `@future` method with SObject or custom-class parameter.

---

## Anti-Pattern 2: Making HTTP callouts without callout=true

**What the LLM generates:**

```
@future
public static void push(Set<Id> ids) {
    Http h = new Http();
    h.send(req);  // CalloutException
}
```

**Why it happens:** Model forgets the annotation attribute.

**Correct pattern:**

```
@future(callout=true)
public static void push(Set<Id> ids) { ... }

Without callout=true, any HTTP send throws
"Callout from scheduled Apex or trigger cannot be performed."
```

**Detection hint:** `@future` without `(callout=true)` containing `Http`, `HttpRequest`, or `.send(`.

---

## Anti-Pattern 3: Chaining @future from @future

**What the LLM generates:** `@future` method that calls another `@future` method to continue async processing.

**Why it happens:** Model applies "chain async work" intuition.

**Correct pattern:**

```
@future cannot invoke another @future: the per-invocation allocation is
"0 in batch and future contexts", so you get
System.AsyncException: Future method cannot be called from a future or
batch method.
Use Queueable from the start — it chains via System.enqueueJob and, in
the other direction, IS allowed to call @future (50 in queueable
context). Rewrite the chain as a series of Queueable jobs.
```

**Detection hint:** a `@future`-annotated method calling another method marked `@future`. Do **not** flag `System.enqueueJob` inside a `@future` — the async `enqueueJob` allocation is 1, so a future may legally enqueue a single Queueable. Do not flag `@future` calls inside a `Queueable` either; that direction is explicitly allocated 50.

---

## Anti-Pattern 4: Calling @future from batch/scheduled Apex

**What the LLM generates:** Inside `Database.Batchable.execute`, calls a `@future` method.

**Why it happens:** Model treats all async contexts as equivalent.

**Correct pattern:**

```
Cannot call @future from batch Apex or scheduled Apex (AsyncException).
From batch: call a static method synchronously in execute(), or enqueue
a Queueable from the finish() method.
```

**Detection hint:** Apex class implementing `Database.Batchable` or `Schedulable` that invokes a `@future` method.

---

## Anti-Pattern 5: Relying on return value from @future

**What the LLM generates:** `String result = MyService.doWork(ids);` where `doWork` is `@future void`.

**Why it happens:** Model doesn't know `@future` must return void.

**Correct pattern:**

```
@future methods must return void. They execute asynchronously — the
caller has exited before the future runs. For results, write to a
Platform Event, a custom tracking object, or a Big Object. The caller
cannot block waiting.
```

**Detection hint:** `@future` method signature with a non-void return type, or code assigning its "result."
