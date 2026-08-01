# LLM Anti-Patterns — Agent Action Unit Tests

Scope: tests for `@InvocableMethod` classes that Agentforce topics and Flow Builder
invoke. Generic `@IsTest` structure, `@TestSetup` and factory design belong to
`apex/test-class-standards` and `apex/test-data-factory-patterns` — read those for the
fundamentals. Everything below is specific to the Invocable Request/Response contract.

## Anti-Pattern 1: One Request per test, so the size-and-order contract is never exercised

Assistants write a single-record test and stop. The Apex Developer Guide states the
contract precisely: "For a correct bulkification implementation, the Inputs and Outputs
must match on both the size and the order. For example, the i-th Output entry must
correspond to the i-th Input entry." A one-element list cannot fail either half.

**Wrong** — a one-element list, so neither half of the contract can fail:

```apex
List<CloseCaseAction.Response> out =
    CloseCaseAction.run(new List<CloseCaseAction.Request>{ req });
Assert.areEqual('CLOSED', out[0].reasonCode);
```

**Right** — assert size first, then positional correspondence:

```apex
Test.startTest();
List<CloseCaseAction.Response> out = CloseCaseAction.run(reqs);  // reqs.size() == 200
Test.stopTest();
Assert.areEqual(reqs.size(), out.size(), 'one Response per Request');
for (Integer i = 0; i < reqs.size(); i++) {
    Assert.areEqual(reqs[i].caseId, out[i].caseId,
        'Response ' + i + ' must correspond to Request ' + i);
}
```

Source: InvocableMethod annotation —
https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_annotation_InvocableMethod.htm

## Anti-Pattern 2: Generating a class with two invocable entry points

Asked to "add an escalate action to CloseCaseAction", assistants add a second
`@InvocableMethod`. That class does not compile: "Only one method in a class can have
the InvocableMethod annotation." The same reference also constrains stacking —
"The only annotation that can be used with the InvocableMethod annotation is
Deprecated" — so `@AuraEnabled @InvocableMethod` on one method is invalid too.

❌ Two `@InvocableMethod` methods in one class, or `@InvocableMethod` beside `@AuraEnabled`.
✅ One outer class per action, each with one `public static` invocable method delegating
to a shared service class. Test each action class separately; test the shared service
once.

Source: InvocableMethod annotation (link above).

## Anti-Pattern 3: Asserting on the user-facing message instead of the machine code

The `Response` field the agent narrates to the user is UX copy and changes without any
functional change; the `reasonCode` is the branch contract. Assertions on copy produce a
wave of unrelated red the next time a content designer edits a sentence, which trains
the team to ignore this test class.

❌ `Assert.areEqual('Sorry, I could not close that case.', out[0].userMessage);`
✅ `Assert.areEqual('VALIDATION_BLOCKED', out[0].reasonCode);` — then assert copy once,
in a single dedicated test that owns the wording for every code.

## Anti-Pattern 4: Omitting Test.startTest/stopTest when the action queues async work

An invocable that enqueues a `Queueable` or calls a `@future` method looks tested but is
not: the async job never runs, so its assertions never execute and the test is green.
`Test.stopTest()` is the documented boundary that forces queued asynchronous work to
complete before execution continues.

❌ Call `run(reqs)`, then assert on records the Queueable was supposed to write.
✅ `Test.startTest(); run(reqs); Test.stopTest();` then assert. The boundary also gives
the invocation a fresh governor-limit budget, so setup DML does not consume the
allowance the action is being measured against.

Source: Apex Developer Guide, Testing Apex —
https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_testing.htm

## Anti-Pattern 5: Testing a callout branch without a mock

Apex tests cannot perform live HTTP callouts; the runtime fails the test with
`Methods defined as TestMethod do not support Web service callouts`. Assistants
routinely generate the action correctly and then omit the mock from the test.

❌ Exercise the callout branch and hope a sandbox endpoint answers.
✅ `Test.setMock(HttpCalloutMock.class, new MyMock(404));` then assert which
`reasonCode` the action maps that status to — one mock per status class (2xx, 4xx, 5xx,
malformed body), one test per resulting branch.

Source: Testing HTTP Callouts —
https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts_testing.htm

## Anti-Pattern 6: Reading line coverage as branch coverage

`sf apex run test -c` reports line coverage. An action with five `reasonCode` values can
report 90% while three of those codes are returned by no test at all. The number that
matters is distinct `reasonCode` literals asserted, over distinct literals the class can
emit.

❌ "Coverage is 88%, ship it."
✅ Enumerate every literal assigned to `reasonCode` in the class and require one test per
literal. `scripts/check_agent_action_unit_tests.py` in this package performs that
comparison mechanically.

## Anti-Pattern 7: Relying on @InvocableVariable defaults that do not exist

Assistants construct a `Request` in a test setting only the field the assertion reads,
assuming the rest carry declared defaults. Unset invocable variables arrive as `null`,
so the test exercises a shape the agent will never send and misses the null-handling
branch entirely.

❌ `Request r = new Request(); r.caseId = c.Id;` — every other variable is silently null.
✅ Populate every `@InvocableVariable` explicitly in a helper factory, then write one
extra test per variable that is genuinely optional, asserting the null path.

Source: InvocableVariable annotation —
https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_annotation_InvocableVariable.htm
