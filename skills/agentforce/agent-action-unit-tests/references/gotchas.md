# Gotchas — Agent Action Unit Tests

Sources: Apex Developer Guide (Spring '26 PDF: InvocableMethod and InvocableVariable annotations, Testing Apex, Testing HTTP Callouts, Execution Governors and Limits, Using the runAs Method), the Generative AI guide (Spring '26 PDF), and the Agentforce Developer Guide testing pages, read on 2026-10-03.

## Gotcha 1: Async Work Needs the Test.startTest/stopTest Boundary

**What happens:** An action enqueues a Queueable (or calls a future method), and the test asserts on records the job should write. The assertions fail or, worse, the test asserts nothing useful. The guide says all asynchronous calls made after `Test.startTest()` are collected and run synchronously when `Test.stopTest()` executes; outside the boundary, a batch job runs at the end of the test method, after the assertions.

**When it occurs:** Any action that hands work to async Apex.

**How to avoid:** Call the action between `Test.startTest()` and `Test.stopTest()`, then assert. Async calls inside the block also don't count against the queued-job limits.

**Source:** Apex Developer Guide, Testing Queueable Jobs, Testing the Apex Scheduler, and Using Batch Apex ("All asynchronous calls made after the startTest method are collected by the system. When stopTest is executed, all asynchronous processes are run synchronously"); Asynchronous Apex and Mock Callouts.

---

## Gotcha 2: `defaultValue` Does Not Fill Fields When a Test Builds the Request Itself

**What happens:** A test constructs `new Request()` and sets only one field, expecting the others to take their `@InvocableVariable(defaultValue=...)` values. They stay null. The guide describes `defaultValue` as the value provided to the action at runtime when no value is supplied, which is the action framework's job, not the Apex constructor's.

**When it occurs:** Manual construction of Request objects in tests.

**How to avoid:** Set every field explicitly in a helper factory, then add one test per genuinely optional field that asserts the null path. UNVERIFIED (2026-10-03): the guide does not state in so many words that a direct Apex call skips `defaultValue`; the conclusion follows from its runtime wording.

**Source:** Apex Developer Guide, InvocableVariable Annotation (`defaultValue` modifier).

---

## Gotcha 3: Asserting on user_message Strings

**What happens:** A UX copy change breaks forty tests at once, and the team learns to ignore the test class.

**When it occurs:** Copy-pasted UX text in assertions.

**How to avoid:** Assert on the reason code only, and assert the copy in one dedicated test that owns the wording.

**Source:** Design guidance; the reason-code contract follows the Apex Developer Guide's pattern of reporting failures in result objects (InvocableMethod Annotation, exception-handling paragraph).

---

## Gotcha 4: DML Before a Mock Callout Needs a Specific Order

**What happens:** A test inserts a Case, then calls an action that makes a mocked callout, and fails with an uncommitted-work exception. By default, callouts aren't allowed after DML in the same transaction. The guide's fix: enclose the callout portion in `Test.startTest()`/`Test.stopTest()`, call `Test.startTest()` before `Test.setMock()`, and keep the DML outside that block.

**When it occurs:** Callout actions whose tests create their own data.

**How to avoid:** Insert test data first (or in `@TestSetup`), then `Test.startTest()`, then `Test.setMock(...)`, then call the action, then `Test.stopTest()`.

**Source:** Apex Developer Guide, Performing DML Operations and Mock Callouts.

---

## Gotcha 5: Real Callouts Fail in Tests

**What happens:** A callout branch is exercised without a mock and the test fails. The guide states test methods don't support web service callouts, and tests that perform them fail.

**When it occurs:** Tests written against a sandbox endpoint "for realism".

**How to avoid:** Register an `HttpCalloutMock` per status class you care about (2xx, 4xx, 5xx, malformed body) and assert the reason code each one maps to.

**Source:** Apex Developer Guide, Testing HTTP Callouts (and the test-method considerations list: "Test methods don't support web service callouts").

---

## Gotcha 6: A One-Element Test Cannot Prove the Size-and-Order Contract

**What happens:** An action drops failed inputs or reorders outputs, and every single-request test still passes. The guide requires inputs and outputs to "match on both the size and the order", and the method to "return the same number of results as inputs received even if errors occur".

**When it occurs:** Test classes with only one Request per call.

**How to avoid:** Add a test with mixed good and bad inputs, assert the output count first, then assert each position.

**Source:** Apex Developer Guide, InvocableMethod Annotation (Inputs and Outputs; exception-handling paragraph).

---

## Gotcha 7: Tests That Run as an Admin Hide Agent-User Access Gaps

**What happens:** Every test passes as the running admin, and the deployed action returns nothing for the agent. The agent user "determines what your agent can access and do". Inside a `System.runAs` block, the user's sharing rules and object- and field-level permissions are enforced regardless of the test class's sharing mode.

**When it occurs:** Actions that query with `WITH USER_MODE` or rely on the agent user's permission sets.

**How to avoid:** Create a test user with the same permission sets as the agent user and call the action inside `System.runAs(agentUser)`. Each `runAs` call counts against the DML statement limit, so keep them few.

**Source:** Apex Developer Guide, Using the runAs Method; Generative AI guide, Create an Agent (the agent user).

---

## Gotcha 8: Unit Tests Do Not Test Whether the Agent Calls the Action

**What happens:** The action has full branch coverage, and the agent still never invokes it, because routing and action selection are decided by the agent, not by Apex.

**When it occurs:** Teams that treat Apex coverage as agent coverage.

**How to avoid:** Keep Apex tests for the action's contract. Test selection separately with an `AiEvaluationDefinition` whose test cases use `action_sequence_match` expectations.

**Source:** Agentforce Developer Guide, Build Tests in Metadata API (AiEvaluationDefinition sample with `action_sequence_match`).

---

## Gotcha 9: Savepoints Are Released at Test.startTest and Test.stopTest

**What happens:** An action that sets a savepoint and rolls back on failure behaves differently in a test that wraps it in the boundary. For Apex tests with API version 60.0 or later, all savepoints are released when `Test.startTest()` and `Test.stopTest()` are called, and a SAVEPOINT_RESET event is logged.

**When it occurs:** Actions that use `Database.setSavepoint()` for partial rollback, tested with a savepoint created before the boundary.

**How to avoid:** Create savepoints inside the code under test, not in the test before `Test.startTest()`, and check the debug log for SAVEPOINT_RESET when results look wrong.

**Source:** Apex Developer Guide, Versioned Behavior Changes (savepoints in tests, API 60.0).
