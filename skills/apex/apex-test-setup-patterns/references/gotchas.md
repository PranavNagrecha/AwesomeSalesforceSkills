# Gotchas — Apex Test Setup Patterns

Behaviors that surface only when the test class shape moves past the
trivial "one method, one insert" template. These compound the rules in
SKILL.md's gotchas section — they are the second-order failures
practitioners hit *after* they've adopted `@TestSetup` and now have to
debug why the suite passes locally but fails in CI, or why a single
method run behaves differently than `Run All`.

## Gotcha 1: Record state mutates within a method but rolls back to the @TestSetup snapshot before the next method

**What happens:** `@TestSetup` inserts 100 Cases with `Status =
'New'`. Test method A runs `[SELECT Id FROM Case]`, sets every Status
to `'Closed'`, and asserts the update succeeded. Test method B starts
expecting either (a) the same Closed cases method A left behind, or
(b) a clean re-inserted set of records with brand-new Ids — and gets
neither. It sees 100 Cases with `Status = 'New'` again, with the
*same* Ids method A saw. Practitioners debug for an hour before
realizing both halves of their mental model were wrong.

**When it occurs:** Any multi-method `@TestSetup` test class where
test methods mutate setup records (most non-trivial test classes).
Especially confusing when the test methods cache an `Id` in a class-
level `static` variable, because the variable persists across methods
but the underlying record state doesn't.

**How to avoid:** Treat each test method as "starts from the post-
setup snapshot, ends rolling back to it." Always re-query inside the
method for the data you need — never reach across methods via static
caches of records or field values. The cheap mental model: Ids are
stable identifiers (they survive the rollback), but every
non-Id field is rewound to whatever `@TestSetup` left it as. If you
need to assert on cross-method state, you're testing the framework,
not your code — rewrite the test.

---

## Gotcha 2: @TestSetup runs even when you select a single test method to run

**What happens:** A developer runs `Run Test` on one specific method
in Developer Console or via `sf apex run test --tests
MyClass.singleMethod`, expecting the run to skip the (slow) setup
because they only want the one test. The setup still fires, and the
slow setup is now the bottleneck for "quick iteration" runs that the
developer wanted to do dozens of times per minute.

**When it occurs:** Any single-method test execution against a class
with a `@TestSetup`. The platform has no "skip setup for this run"
toggle — the setup is part of the class fixture contract, not an
optional pre-step.

**How to avoid:** Keep `@TestSetup` cheap enough that even a single-
method run is fast. If the setup must be expensive (e.g., 1,000
records), split the class: put the methods that need the heavy
fixture in one class with a heavy `@TestSetup`, and the methods that
need a light fixture in a different class with a light `@TestSetup`.
Don't try to gate setup with a static flag — the platform invokes
`@TestSetup` at the framework level before any of your code runs, so
your flag never gets read in time.

---

## Gotcha 3: Multiple @TestSetup methods in one class throw a compile error — only one is allowed

**What happens:** A developer adds a second `@TestSetup` method to
split "seed accounts" and "seed users" into two readable blocks.
The class fails to save with a compile error along the lines of
`Only one test setup method is allowed in a class`. They assumed the
platform would just run both setups in declaration order, the way
JUnit `@BeforeAll` allows multiple methods.

**When it occurs:** Refactoring an existing test class to break the
monolithic setup method into smaller named blocks for readability.
Also surfaces when merging two test classes into one without
collapsing their setups.

**How to avoid:** Keep exactly one `@TestSetup` method per class.
Decompose internally by calling helper methods from the single
`@TestSetup`: `setupAccounts(); setupUsers();`. If two test methods
truly need different setup fixtures, split into two test classes.
Resist the temptation to use `@TestVisible` flags to branch the
single setup into mutually-exclusive paths — that pattern produces
setup methods nobody can read.

---

## Gotcha 4: If @TestSetup throws, every test method in the class is reported as failed with the same setup error

**What happens:** A new validation rule on Account requires
`BillingCountry`. `@TestSetup` was written before the rule existed
and inserts an Account without it. The setup throws
`FIELD_CUSTOM_VALIDATION_EXCEPTION`. The test class run reports all
12 test methods as failures — each with the *same* setup error, none
with the assertion or behavior they were actually meant to verify.
A developer scanning failures sees 12 "different" failures and starts
diagnosing them individually before noticing the common cause.

**When it occurs:** Any time `@TestSetup` performs DML that becomes
illegal: a new validation rule, a new required field, a flow that
fires on the setup record and itself throws, a trigger that throws
on the setup-inserted records, or a profile change that makes the
setup user lose CRUD on the setup object. The blast radius is
"every test method in the class," not "the methods that touched the
specific data."

**How to avoid:** Keep `@TestSetup` minimal — every line is a class-
wide single point of failure. Move optional or branch-specific data
out of setup into per-method helper calls so a broken branch fails
only the tests that use it. When a test class's failures all look
identical and reference a line inside `@TestSetup`, scan for a
recent metadata change (validation rule, required field, profile)
before debugging the setup code itself.

---

## Gotcha 5: Test.setMock() registered in @TestSetup does not carry to test methods — mocks must be registered per method

**What happens:** A test class makes 10 HTTP callouts across its
test methods. The developer registers `Test.setMock(HttpCalloutMock.
class, new MyMock())` once inside `@TestSetup`, expecting the mock to
apply to every method. The first test method runs, hits the callout,
and gets `Methods defined as TestMethod do not support Web service
callouts` because no mock is active in that method's context.

**When it occurs:** Any test class that uses `@TestSetup` for shared
data *and* makes callouts in its test methods. The same trap exists
for `Test.setCreatedDate` and `Test.loadData` — they apply to the
transaction they're called in, and `@TestSetup` runs in a separate
framework-managed transaction from each test method.

**How to avoid:** Call `Test.setMock(...)` at the top of each test
method that issues a callout (or build a `@TestVisible` helper like
`TestUtil.installMock()` and call it from each method). The same
discipline applies to anything else that modifies test framework
state: register it inside the test method that needs it, not in
`@TestSetup`. Reserve `@TestSetup` for DML-creating shared *data*,
not for framework-state mutations.
