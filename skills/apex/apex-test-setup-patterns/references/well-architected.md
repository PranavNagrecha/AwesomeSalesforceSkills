# Well-Architected Notes — Apex Test Setup Patterns

## Relevant Pillars

Test infrastructure looks like a Reliability-only concern but it spans
five pillars because the test suite is itself a production-critical
artifact: it gates every deploy, sets the lower bound on developer
feedback latency, and is the only place a team validates governor-
limit behavior before customers experience it.

- **Reliability** — `@TestSetup` is the difference between a 95%
  deterministic test suite and a flaky one. Tests that recreate their
  own data per-method occasionally race against org-level processes
  (sharing rule recalc, indexed-field updates) in busy sandboxes; a
  single `@TestSetup` block lets the platform serialize once and rolls
  back to the same snapshot every method. Tests that share static
  state across methods or cache `Id` values outside re-queries appear
  reliable in dev but fail nondeterministically in CI.
- **Performance** — Most Apex test suites at 70%+ coverage spend more
  CPU on data setup than on the code under test. Moving from per-
  method data creation to `@TestSetup` typically yields a 3–5x
  wall-clock speedup on a class with 5+ test methods. At the org
  level, that compounds: a suite that drops from 22 minutes to 7
  minutes per CI run pays back the refactor inside a quarter.
- **Scalability** — `@TestSetup` plus a bulk-insert pattern is how
  the test class proves the trigger handles 200 records in one
  transaction. Per-method tests with looped inserts top out at 150
  DML statements and silently never exercise the bulk path the
  trigger was written for. Production behavior at batch size 200
  is *only* validated if test fixtures match production scale.
- **Security** — `System.runAs` inside `@TestSetup` is the only legal
  way to mix setup-object DML (User, UserRole, Group,
  PermissionSetAssignment) with non-setup-object DML in one fixture.
  Skipping the wrapper produces `MIXED_DML_OPERATION` errors that
  obscure what the test actually fails to validate. Tests that should
  exercise community/portal user perspectives but skip `runAs`
  silently run as the system admin and miss real CRUD/FLS bugs.
- **Operational Excellence** — A test class with one `@TestSetup` has
  exactly one place to update when a validation rule lands. The same
  class with per-method inline data has N places, and the developer
  has to find every one. The same logic applies to required-field
  drift, profile changes, and trigger additions that affect setup-
  inserted records.

## Architectural Tradeoffs

The defining choice for any non-trivial test class is **where to put
the data setup** — and the right answer depends on test count and
data variation:

| Approach | Time per method | Data freedom | When to use |
|---|---|---|---|
| Per-method inline DML | Highest setup cost | Total — each method builds what it needs | <3 methods, or each needs wildly different data |
| `@TestSetup` shared baseline | Setup runs once, ~free per method | Common baseline, each method tweaks via re-query + DML | 5+ methods sharing a hierarchy |
| `TestDataFactory` called from `@TestSetup` | Same as `@TestSetup` plus factory overhead | Factory enforces required-field consistency across classes | Org with many test classes touching the same SObjects |
| `Test.loadData` from a static resource CSV | Setup runs once, ~free | Frozen — CSV is data, not Apex | Large reference datasets (price books, country lists) that don't change between tests |

`@TestSetup` + bulk inserts is the default. The exceptions are real
but narrow: tests that legitimately need every record to be different
(e.g., a test of name-uniqueness handling) are better off per-method.
Tests on org-wide singleton data (standard Pricebook2) need
`SeeAllData=true` and therefore cannot use `@TestSetup` at all.

A second tradeoff is **where `Test.startTest()` / `Test.stopTest()`
goes**. The most common failure mode is to wrap the entire test
method, including DML that prepares per-test variations of the
`@TestSetup` data. That defeats the purpose: `startTest` is meant to
reset the governor budget for the *code under test*, isolating it
from setup costs. The correct shape is "use setup data to build the
trigger input → call `startTest` → invoke the code under test → call
`stopTest` → assert." For async code (Queueable, @future, Batch),
`stopTest` is also when the async work executes synchronously, so
assertions on its output go *after* `stopTest`.

A third tradeoff is **`@TestVisible` vs dependency injection**.
`@TestVisible` is convenient — flip a private static to true inside a
test, exercise the failure branch, done — but it couples the test to
the implementation. A future refactor that splits the class or
renames the static breaks tests without breaking behavior. Constructor
or method-parameter injection is more typing but produces tests that
care only about contract. Use `@TestVisible` for genuinely test-only
flags (mock-mode toggles, deterministic random seeds); use DI for
collaborators (services, gateways) the test wants to swap out.

## Anti-Patterns

1. **Multiple `@TestSetup` methods in one class** — compile error,
   not a runtime warning. Decompose by calling helpers from the
   single setup method instead. See gotchas.md Gotcha 3.
2. **Setup work that touches `Test.setMock`, `Test.setCreatedDate`,
   or other framework-state mutations** — those only apply in the
   transaction that calls them. `@TestSetup` runs in a separate
   framework-managed transaction, so the mutations silently don't
   carry. Register them per test method.
3. **Caching record references in class-level statics across test
   methods** — Ids survive the post-method rollback, but every other
   field is rewound to the `@TestSetup` state. Cached references
   produce assertions that succeed in dev (when methods run in a
   specific order) and fail in CI (when they don't).
4. **Per-method inline data creation in classes with 5+ methods** —
   3–5x slower than the equivalent `@TestSetup` version, with N
   copies of every required-field workaround that have to be
   updated together when the schema changes.
5. **`@IsTest(SeeAllData=true)` co-existing with `@TestSetup`** — the
   setup method is silently ignored and the class runs against
   whatever org data happens to exist. There is no error or warning;
   the failure surfaces as nondeterministic test results across orgs.
   Remove `SeeAllData=true` entirely; rebuild the dependency on org
   data through factory methods.

## Official Sources Used

- Apex Developer Guide — Using the testSetup Method:
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_testing_testsetup_using.htm
- Apex Developer Guide — Mixed DML Operations in Test Methods:
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dml_non_mix_sobjects_test_methods.htm
- Apex Developer Guide — System.runAs:
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_testing_tools_runas.htm
- Apex Developer Guide — Common Test Utility Classes (Factory Pattern):
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_testing_utility_classes.htm
- Apex Developer Guide — Annotations (IsTest, TestSetup, TestVisible):
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_annotation.htm
- Salesforce Well-Architected — Trusted (Reliable):
  https://architect.salesforce.com/well-architected/trusted/reliable
