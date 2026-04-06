# Gotchas — Callout Limits And Async Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Async Context Does Not Increase the 100-Callout Limit

**What happens:** A developer assumes that running callouts in a Queueable or Batch Apex context gives a larger callout limit than synchronous Apex. In fact, the 100-callout-per-transaction limit applies equally to synchronous, @future, Queueable, and Batch Apex contexts. Each async execution gets its own 100-callout budget — but that budget is still 100, not more.

**When it occurs:** A developer needs to call 300 external systems for 300 records and places all calls in a single Queueable, expecting async to have a higher limit.

**How to avoid:** To process more than 100 callout-requiring records, use Batch Apex (each `execute()` chunk gets 100 callouts in a fresh transaction) or chain multiple Queueables (each link in the chain gets 100 callouts). Design the volume to fit within these constraints.

---

## Gotcha 2: DML-Before-Callout Applies Across the Entire Transaction, Not Just the Method

**What happens:** The "uncommitted DML before callout" restriction applies to the full Apex transaction. Even if the DML was performed in a completely different class or helper method called earlier in the transaction, any subsequent callout in the same transaction will throw `System.CalloutException: You have uncommitted work pending`.

**When it occurs:** A trigger calls a service class that does a logging DML insert, then later calls a helper that makes an HTTP request. The DML and the callout are in different classes but the same transaction — the callout fails.

**How to avoid:** Audit the full call stack for any DML that occurs before a callout. If DML must precede the callout, use `System.enqueueJob()` to move the callout to a separate Queueable that executes after the current transaction commits.

---

## Gotcha 3: Continuation Is Only Available in LWC/Aura/VF Controllers — Not Triggers or Queueables

**What happens:** Attempting to instantiate or return a `Continuation` object from a trigger, Queueable, Batch, or @future context throws a runtime exception. Continuation is exclusively available in controller contexts backing user interface components.

**When it occurs:** A developer reads about Continuation's ability to handle long-running callouts and tries to use it in a trigger to avoid the 120-second synchronous timeout.

**How to avoid:** Use Continuation only in `@AuraEnabled` methods, Visualforce controller methods, or controller classes explicitly serving an LWC/Aura component. For long-running callouts in non-UI contexts, use Queueable with a polling pattern or rely on the system's 120-second per-callout timeout.

---

## Gotcha 4: @future(callout=true) Cannot Chain and Cannot Accept sObject Parameters

**What happens:** A developer uses `@future(callout=true)` and needs to pass an Account object as a parameter. The compiler rejects sObject parameters for @future methods. As a workaround, the developer passes only the Account ID, then queries inside the @future. When the @future runs, the Account may have been updated by another process, returning different data than was present when the @future was enqueued.

**When it occurs:** Any @future method that needs to use sObject-level data or needs to chain a second callout after processing the first response.

**How to avoid:** Use `Queueable implements Database.AllowsCallouts` instead of @future for any scenario requiring sObject parameters or callout chaining. @future is only appropriate for simple fire-and-forget callouts with primitive parameters and no follow-up action.
