# Gotchas — Apex Mocking And Stubs

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## `StubProvider` Depends On A Real Seam

**What happens:** The team reaches for `Test.createStub`, but the production dependency is a static helper with no injectable boundary.

**When it occurs:** Mocking is treated as a framework problem rather than a design problem.

**How to avoid:** Add an interface or stub-friendly collaborator seam first.

---

## One Success Mock Does Not Test Reliability

**What happens:** Tests pass while retry, timeout, and malformed payload handling remain broken.

**When it occurs:** Only the happy path is mocked.

**How to avoid:** Create focused mocks for the failure paths that actually matter.

---

## Static Resource Fixtures Can Drift Quietly

**What happens:** Large JSON fixtures stay in static resources for months while the real API contract changes.

**When it occurs:** Fixtures are convenient but never reviewed.

**How to avoid:** Keep fixture ownership explicit and update them when the contract changes.

---

## Transport Mocks And Service Stubs Are Not Interchangeable

**What happens:** A team uses a callout mock to compensate for a missing internal abstraction, or vice versa.

**When it occurs:** The dependency type is not identified clearly.

**How to avoid:** Choose `Test.setMock` for transport boundaries and `StubProvider` for Apex collaborator seams.

---

## The Stub API's "Cannot Mock" List Is Exact, And It Fails At Runtime

**What happens:** `Test.createStub()` rejects the type and the test fails on execution, not on save. The documented list of elements you can't mock is: static methods (including `@future` methods), private methods, properties (getters and setters), triggers, inner classes, system types, classes that implement the `Batchable` interface, and classes that have only private constructors. Iterators can't be used as return types or parameter types.

**When it occurs:** Any time the "dependency" is a utility class of statics, a `Database.Batchable` implementation, a private inner helper, or a singleton locked behind a private constructor — which covers most of what teams reach for first.

**How to avoid:** Read the list before designing the seam, not after the test fails. Every item on it has the same fix: promote the collaborator to a top-level class or interface with a public constructor and inject it. Grounded: Apex Developer Guide, "Apex Stub API Limitations", L42199–42219.

---

## Non-Virtual Classes And Non-Virtual Methods **Are** Stubbable

**What happens:** A team adds `virtual` to every class and method "so it can be mocked", inflating the API surface for no reason — or worse, refuses to stub a plain class because it believes the Stub API can't. Neither is true: stub objects are created at runtime as *anonymous subclasses*, and the guide's own worked example stubs `DateHelper.getTodaysDate()` on a plain `public class DateHelper` with a plain `public String` method — no `virtual`, no interface.

**When it occurs:** Carrying Java/Mockito intuition (where non-virtual/final methods genuinely can't be intercepted) into Apex.

**How to avoid:** Add `virtual` only when you actually want subclass overrides in production. Interfaces are still the better seam for other reasons (they document the contract and survive refactoring), but "the class isn't virtual" is not one of them. Grounded: Apex Developer Guide L42052 (anonymous subclasses), L42060–42073 (the non-virtual `DateHelper`) and L42180–42192 (that same class being stubbed and asserted on).

---

## The Mocked Object Must Share The Caller's Namespace

**What happens:** `Test.createStub()` fails when the class being mocked lives in a different namespace from the code calling `createStub()`. Note the asymmetry: the *`StubProvider` implementation itself* is allowed to live in another namespace — only the mocked type is constrained.

**When it occurs:** A subscriber org tries to stub a managed-package service class from its own test code, or a package's tests are moved into the subscriber's namespace during a refactor.

**How to avoid:** Ship the stub-friendly interfaces inside the package and test them from a test class in the same namespace. For managed-package HTTP callouts the parallel rule applies to `Test.setMock`: call it from a test method in the same package with the same namespace. Grounded: Apex Developer Guide L42201–42202 (`createStub` namespace), L35429–35430 (`setMock` namespace).

---

## `Test.startTest()` Must Come *Before* `Test.setMock()` When The Test Does DML First

**What happens:** The test inserts fixture rows, calls `Test.setMock(...)`, then calls the method under test, and the callout throws "uncommitted work pending". Callouts aren't allowed after DML in the same transaction because DML leaves pending uncommitted work.

**When it occurs:** Any callout test that builds its own data instead of using `@TestSetup`. It also breaks when the DML is accidentally moved *inside* the `startTest`/`stopTest` block, which is the other half of the rule.

**How to avoid:** Order it exactly: DML first, then `Test.startTest()`, then `Test.setMock()`, then the call, then `Test.stopTest()`. DML operations that occur *after* mock callouts need no special handling. Grounded: Apex Developer Guide, "Performing DML Operations and Mock Callouts", L35675–35681.

---

## A Test That Reaches A Real Callout Fails Rather Than Skipping It

**What happens:** By default test methods don't support HTTP callouts or web-service callouts; tests that perform them fail outright. There is no silent pass-through and no "the callout was skipped" outcome — the test simply errors.

**When it occurs:** A new code path adds a callout behind an existing method, and the old test that never needed `Test.setMock` starts failing on a deploy nobody expected to touch it.

**How to avoid:** Treat "this test now needs a mock" as a signal that a callout entered the call graph, not as a test bug to be worked around. Set the mock at the top of every test whose call graph can reach the transport, even when today's branch doesn't. Grounded: Apex Developer Guide L35384–35385 (HTTP), L35014–35016 (web service).

---

## `Test.setMock` Intercepts The Transport, Not A Class — So It Cannot Fake A Collaborator

**What happens:** `setMock` sets the response mock mode and instructs the Apex runtime to send a mock response *whenever a callout is made through the HTTP classes or the auto-generated code from WSDLs*. It has no view of your service classes. Registering a mock and expecting `MyService.doWork()` to be replaced does nothing at all — the real method runs.

**When it occurs:** The instinct that "mocking in Apex = `Test.setMock`", usually reinforced by the fact that most Apex mocking tutorials only cover callouts.

**How to avoid:** Split the question in two before choosing: *is the thing being replaced on the far side of an HTTP/SOAP boundary?* If yes, `Test.setMock`. If it's Apex calling Apex, only a seam plus `Test.createStub` (or a hand-written fake) can replace it. Grounded: Apex Reference Guide, `Test.setMock(interfaceType, instance)`, L240947–240950.

---

## Void Methods Still Route Through `handleMethodCall`

**What happens:** `handleMethodCall` is declared to return `Object`, and it is called for *every* stubbed method invocation. A provider whose fallback is `throw new UnstubbedMethodException(...)` — the correct fallback for value-returning methods — blows up the moment the code under test calls a `void` method on the stub, even though the test never cared about that call.

**When it occurs:** Stubbing a collaborator that mixes queries (return values) with commands (`void log(...)`, `void publish(...)`).

**How to avoid:** Register void methods explicitly (`allowsVoid('publish')` in `references/code-examples.md` § 3) so the provider returns `null` for them and still throws for genuinely unstubbed value-returning methods. UNVERIFIED (2026-09-05): the guide documents `returnType` as `System.Type` (Apex Reference Guide L238498–238500) but does not state what it holds for a `void` method, so an explicit registration is more reliable than inspecting `returnType`. Grounded for the signature: Apex Reference Guide L238486–238488.

---

## A Stub Runs In Its Parent Class's Sharing Mode, And API 67 Changed The Default

**What happens:** Stub objects are anonymous subclasses of the type being stubbed, so a stubbed selector still carries the sharing semantics of the class it subclasses. Separately, in API version 67.0 and later, classes without an explicit sharing declaration run in `with sharing` mode — a reversal of the earlier default. A selector saved at 66.0 or earlier and one saved at 67.0 with no declaration behave differently.

**When it occurs:** A `System.runAs` test that passes on an old class version and fails after the class is bumped to 67.0, or vice versa. Inside a `runAs` block, the sharing mode enforced for a user-defined method is that of the class where the method is *defined*, not the test class — so the test class's own `with sharing` tells you nothing.

**How to avoid:** Put an explicit `with sharing` / `inherited sharing` / `without sharing` declaration on every class with SOQL or DML, including the ones you intend to stub, so the stub's behaviour is not a function of the class's API version. Grounded: Apex Developer Guide L42052 (anonymous subclasses), L4961–4967 ("Versioned Behavior Changes"), L41328–41332 (`runAs` sharing note).

---

## Checker Ignores Comments And String Literals

**What happens:** The skill checker flags a keyword that appears only in a comment or a string literal (for example a note that `WITH SECURITY_ENFORCED` is not used, or an assertion message that mentions `EventBus.publish`).

**When it occurs:** Before the checker blanked `//` line comments, `/* … */` block comments, and `'…'` string literals to spaces (same length, newlines preserved) for code-pattern rules.

**How to avoid:** Trust the checker on executable code only. Mentions inside comments and string literals are ignored for pattern matches; rules that intentionally read comments (for example a `// reason:` search) still read the original text.
