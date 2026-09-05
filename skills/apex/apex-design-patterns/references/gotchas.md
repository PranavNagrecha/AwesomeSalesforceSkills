# Gotchas — Apex Design Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Service Layers Become God-Classes Faster Than Teams Expect

**What happens:** The team adds every new concern to the service layer because it already “owns orchestration.”

**When it occurs:** There is no discipline about when logic belongs in domain, selector, or integration-specific collaborators.

**How to avoid:** Review service classes for mixed responsibilities regularly and split them when they absorb query definitions, validation rules, and transport details together.

---

## Selector Reuse Can Backfire If Field Lists Balloon

**What happens:** One selector method keeps accumulating more fields for every caller until the query is no longer efficient or reviewable.

**When it occurs:** Teams use one broad “selectEverything” method instead of intent-specific selectors.

**How to avoid:** Keep selectors focused on use cases and create separate methods for distinct query shapes.

---

## `Test.isRunningTest()` Is A Design Smell, Not Dependency Injection

**What happens:** Production code branches around integrations or expensive logic only in test context.

**When it occurs:** There is no interface boundary or injected collaborator.

**How to avoid:** Use interfaces and factories so tests replace the dependency cleanly.

---

## Framework-Like Naming Does Not Equal Good Design

**What happens:** Classes are named `SomethingService`, `SomethingSelector`, and `SomethingDomain`, but each still performs mixed responsibilities.

**When it occurs:** Teams copy naming conventions without enforcing the actual behavioral contract of each layer.

**How to avoid:** Review what each class does, not just what it is called.

---

## A Rollback Undoes Your DML But Not Your Statics

**What happens:** A service catches a `DmlException`, calls `Database.rollback(sp)`, and retries — or lets the trigger fire again. The database is clean, but the recursion guard, the memoised strategy instance, and the "already processed" `Set<Id>` all still hold the values they had at the moment of failure, so the retry silently does nothing.

**When it occurs:** Any time a savepoint-protected service coexists with a static guard or a static cache. The Apex Developer Guide is explicit: "Static variables aren't reverted during a rollback. If you try to run the trigger again, the static variables retain the values from the first run." (L8692–8693.)

**How to avoid:** Give every static mutable collection a `@TestVisible private static void reset()` and call it in the `catch` block, next to `rollbackTransaction(sp)`. The factory in `references/code-examples.md` § 6 shows the shape. Never treat "the transaction rolled back" as "the class is back to its initial state".

---

## A Bulk API Request Resets Governor Limits Between Chunks But Not Statics

**What happens:** A `private static Boolean hasRun` recursion guard works perfectly in the UI and in tests, then a 10,000-row Bulk API job processes only the first 200 rows. Chunks 2 through 50 see `hasRun == true` and skip every rule.

**When it occurs:** Whenever the guard is a scalar rather than a set of Ids. "If a Bulk API request causes a trigger to fire multiple times for chunks of 200 records, governor limits are reset between these trigger invocations for the same HTTP request. Static variables aren't reset within the multiple trigger invocations for the same Bulk API request." (Apex Developer Guide L3789–3791, restated at L14906.)

**How to avoid:** Guard on record Ids, not on a boolean — a `Set<Id>` of rows already processed is chunk-safe because chunk 2 contains different Ids. Where you must suppress exactly one re-entry, use the one-shot `TriggerHandler.skipOnce(handlerName)` in `templates/apex/TriggerHandler.cls` immediately before the DML that causes it, and remember it consumes exactly one invocation.

---

## A Savepoint Cannot Cross A Trigger Invocation, Even As A Static

**What happens:** Someone hoists `Savepoint sp` into a static so "the whole save" can be rolled back from a later trigger context. The next context throws a run-time error when the variable is used.

**When it occurs:** As soon as the second trigger invocation touches the stored savepoint. "References to savepoints can't cross-trigger invocations because each trigger invocation is a new trigger context. If you declare a savepoint as a static variable then try to use it across trigger contexts, you receive a run-time error." (Apex Developer Guide L8689–8690.) The related trap: rolling back to an *earlier* savepoint invalidates every savepoint generated after it, so reusing the later variable is also a run-time error (L8686–8688).

**How to avoid:** One savepoint per public service method, created and consumed inside that method. If the unit of work genuinely spans trigger contexts, the unit of work is wrong — move the orchestration into a single service call.

---

## Every Savepoint And Every Rollback Costs A DML Statement

**What happens:** A service wraps each individual DML in its own savepoint "for safety". A 200-record trigger batch that touches four objects burns 8 statements on savepoint bookkeeping before doing any work, and a later loop tips the transaction over the limit.

**When it occurs:** At scale, not in a unit test with three records. "Each savepoint you set counts against the governor limit for DML statements" (Apex Developer Guide L8691), and the synchronous ceiling is 150 DML statements per transaction (L19554). `Database.rollback` counts too, though from API version 60.0 neither counts against the DML *row* limit (L8695–8696, L44555–44559).

**How to avoid:** Exactly one savepoint per public service method, taken before the first DML. If you need per-record tolerance rather than all-or-nothing, that is `Database.insert(rows, false)` and `Database.SaveResult` inspection, which is a different requirement — not an excuse for more savepoints.

---

## Rolling Back Deletes The Log Row You Just Wrote

**What happens:** The `catch` block logs the exception and then rolls back. The rollback discards the log insert along with the failed work, so production has a silent failure and no audit row.

**When it occurs:** Whenever the logger performs DML — as `templates/apex/ApplicationLogger.cls` does, inserting `Application_Log__c` — and the log call sits before the rollback, or inside the `try`. "Any DML statement that occurs after the savepoint can be discarded, restoring the database to the condition it was in when you generated the savepoint." (Apex Developer Guide L8682–8684.)

**How to avoid:** In the `catch`, roll back first and log second — the order `BaseService` is designed for, and the order `references/code-examples.md` § 4 uses. If a log entry must survive a rollback under all circumstances, publish a Platform Event instead of inserting a record.

---

## `Type.forName` Returns Null For Inner And Private Classes, And Fails Later

**What happens:** A Custom Metadata row names `MyFactory.PhoneStrategy` or a private helper class. `Type.forName` returns `null`, `newInstance()` is called on it, and the transaction dies with a null dereference far from the CMDT row that caused it.

**When it occurs:** With inner classes, private classes, and non-global classes belonging to an installed managed package. "Use the forName methods to retrieve the type of an Apex class... You can use these methods to retrieve the type of public and global classes, and not private classes even if the context user has access." (Apex Reference Guide L241920–241922.) It "returns null if called outside a managed package to get the type of a non-global class in a managed package" (L242076–242079). A call to `Type.forName()` can also cause the class to be compiled (L241925).

**How to avoid:** Only ever name public top-level classes in configuration. Null-check the `Type` before `newInstance()`, `instanceof`-check the result before the cast, and fall back to a named default — the pattern in `references/code-examples.md` § 6. Add the CMDT-row-to-class reconciliation query from § 11 to your post-deploy checks.

---

## `newInstance()` Can Only Reach A No-Argument Constructor

**What happens:** A strategy class gains a constructor that takes a configuration object. Everything compiles, the class is public, `Type.forName` resolves it — and the factory fails at run time.

**When it occurs:** The moment a parameterised constructor is added. `newInstance()`'s signature is `public Object newInstance()` (Apex Reference Guide L242303), so it can only invoke a no-argument constructor, and "if you create a constructor that takes arguments, and you still want to use a no-argument constructor, you must create your own no-argument constructor in your code. After you create a constructor for a class, you no longer have access to the default, no-argument constructor" (Apex Developer Guide L3582–3584). *UNVERIFIED (2026-09-05): the Apex Reference Guide does not name the exception `newInstance()` raises when no accessible no-argument constructor exists; only the signature constraint is documented.*

**How to avoid:** Keep every dynamically-instantiated class constructor-free, and pass configuration through an interface method argument instead. If a strategy needs state, give the interface an `initialise(Map<String, Object> config)` method the factory calls right after `newInstance()`.

---

## At API 65.0 An `abstract` Or `override` Method Without An Access Modifier Will Not Compile

**What happens:** A handler subclass written as `override void beforeUpdate()` compiles against an old API version and then fails on the next class-version bump with *"Abstract methods require at least one of the following: global, public, protected"*.

**When it occurs:** From API version 65.0 onward. "In API version 65.0 and later, an abstract or override method requires a protected, public, or global access modifier. If one of these access modifiers isn't explicitly included in the method declaration, then method access defaults to private. Private access is invalid for these method types because the implementing class can't access the abstract method." (Apex Developer Guide L3359–3364.)

**How to avoid:** Write `protected override void beforeUpdate()` everywhere, matching the `protected virtual` declarations in `templates/apex/TriggerHandler.cls`. Remember the companion rule: methods and classes are final by default and cannot be overridden at all unless declared `virtual` or `abstract` (L4577–4578).

---

## `inherited sharing` Behaves Differently Depending On Who Called It — And Not At All In Async

**What happens:** A selector marked `inherited sharing` is expected to run without sharing when a system-context batch calls it. It runs *with* sharing instead, and the batch sees fewer rows than the author intended.

**When it occurs:** At every entry point. An `inherited sharing` class runs `with sharing` as an Aura controller, an `@AuraEnabled` method called from LWC, a Visualforce controller, an Apex REST service, an asynchronous Apex class, or "any other entry point to an Apex transaction", and "runs as without sharing only when explicitly called from an already established without sharing context" (Apex Developer Guide L4851–4860). Asynchronous classes declared `inherited sharing` "always run in with sharing mode" because each async operation is a new entry point and the sharing mode is not serialized (L4935–4936). Two further traps: inner classes do not adopt the container's sharing mode (L4931–4932), and object- or field-level security is not covered by any sharing declaration at all (L4925–4926).

**How to avoid:** Declare the mode on every class, inner classes included, and choose it per layer: `inherited sharing` on selectors that are always called by something else, `with sharing` on services and handlers that are entry points. Enforce CRUD/FLS separately with `AccessLevel.USER_MODE` in the query and `templates/apex/SecurityUtils.cls` at the DML edge.

---

## `getAll()` Silently Truncates Every Custom Metadata Field At 255 Characters

**What happens:** A strategy row holds a JSON configuration blob. Everything works with short values, then a longer configuration is deployed and the Apex parses a truncated string into a confusing exception.

**When it occurs:** On every `<Type>__mdt.getAll()` call. "Only the first 255 characters are returned for any field in a custom metadata type record, so longer text fields get truncated. If you want all the field data from a custom metadata type record, use a SOQL query." (Apex Reference Guide L204568–204572.) The consolation is that the SOQL alternative is cheap: custom metadata records have no SOQL query limit inside a transaction (Apex Developer Guide L19614–19615).

**How to avoid:** Keep `getAll()` for short scalar values — a class name, a flag, a threshold. Anything that could exceed 255 characters must be read with SOQL against the `__mdt` type, which costs nothing against the query limit.

---

## Test Savepoints Are Released At `Test.startTest()` And `Test.stopTest()`

**What happens:** A test takes a savepoint, calls `Test.startTest()`, provokes a failure, and rolls back — and the rollback does not do what the author expected.

**When it occurs:** From API version 60.0 onward. "For Apex tests with API version 60.0 or later, all savepoints are released when `Test.startTest()` and `Test.stopTest()` are called. If any savepoints are reset, a `SAVEPOINT_RESET` event is logged." (Apex Developer Guide L8783–8784, restated at L44554–44557.) Rolling back to a released savepoint results in a `TypeException` (L8776).

**How to avoid:** Keep the savepoint entirely inside the code under test, as the service does, and let the test assert on the *outcome* of the rollback rather than driving one itself. `references/code-examples.md` § 8 does exactly this: the whole savepoint lifecycle happens inside the single `escalate()` call between `startTest` and `stopTest`.

---

## Static Initialisation Runs Once, In Source Order, Before Any Instance Exists

**What happens:** A `private static final Map<String, String> CONFIG` is built in a static block that reads another static declared *below* it. The map is silently empty rather than throwing, and the strategy lookup falls back for every row.

**When it occurs:** On the first use of the class in a transaction. "Before an object of a class is created, all static member variables in a class are initialized, and all static initialization code blocks are executed. These items are handled in the order in which they appear in the class." (Apex Developer Guide L3733–3734.) "Similar to other static code, a static initialization code block is only initialized one time on the first use of the class" (L3858), and code blocks execute in the order they appear in the file (L3859–3860).

**How to avoid:** Do not build derived static state in a static block. Use lazy initialisation behind a method — `if (cache != null) { return cache; }` — as `TriggerControl.getCache()` and the strategy factory's `classNames()` both do. Lazy initialisation also gives you the reset hook the rollback gotcha above requires.
