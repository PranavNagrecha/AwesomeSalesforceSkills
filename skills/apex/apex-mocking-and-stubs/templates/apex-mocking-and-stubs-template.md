# Apex Mocking Worksheet

## Dependency Under Test

| Item | Value |
|---|---|
| Dependency type | HTTP / SOAP / Internal collaborator |
| Current seam | Interface / Virtual class / Static helper / None |
| Success scenario | |
| Failure scenarios | |

## Chosen Test Double

| Option | Use? | Notes |
|---|---|---|
| `HttpCalloutMock` | | |
| `StaticResourceCalloutMock` | | |
| `StubProvider` | | |
| Refactor seam first | | |

## Guardrails

- [ ] Test doubles cover meaningful failure paths
- [ ] No `Test.isRunningTest()` workaround remains
- [ ] Fixture maintenance owner is known if static resources are used
- [ ] Mock choice matches dependency type

## Cannot-Mock Screening (run before writing any `StubProvider`)

Every row must be **No** before `Test.createStub` is an option. A **Yes** anywhere means the
deliverable is a seam refactor, not a mock. Source: Apex Developer Guide, "Apex Stub API
Limitations" (L42209–42219).

| Is the target… | Yes / No | If Yes, the fix |
|---|---|---|
| A static method (including `@future`)? | | Move the body to an instance method on an injectable interface |
| A private method? | | `@TestVisible` widens access but does not make it stubbable — promote it |
| A property (`get; set;`)? | | Expose an explicit method the seam can declare |
| Trigger logic? | | Move into a handler class (`templates/apex/TriggerHandler.cls`) |
| An inner class? | | Promote to a top-level class or interface |
| A system type (`Http`, `Database`, `Messaging`)? | | Use `Test.setMock`, or wrap it in your own interface |
| A `Database.Batchable` implementor? | | Extract the work into a service the batch calls |
| A class whose only constructor is private? | | Add a public (or `@TestVisible`) constructor, or inject the instance |
| In a different namespace from the test? | | Ship the interface inside the package and test in-namespace |
| Using an iterator as a parameter or return type? | | Change the signature to `List<T>` |

## Test Ordering (callout tests only)

- [ ] DML happens **before** `Test.startTest()` and outside the block
- [ ] `Test.startTest()` comes **before** `Test.setMock(...)` (L35675–35681)
- [ ] `Test.stopTest()` closes the block before the assertions that need async results

## Checker Run

```bash
python3 skills/apex/apex-mocking-and-stubs/scripts/check_apex_mocking_and_stubs.py \
  --manifest-dir force-app/main/default/classes --fail-on HIGH
```

- [ ] Zero CRITICAL / HIGH findings, or each one has a written justification below

| Finding | Justification |
|---|---|
| | |
