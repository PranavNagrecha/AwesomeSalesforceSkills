# Gotchas — Agent Action Error Handling

Failure modes specific to Apex invocable actions consumed by an Agentforce
planner. Several have no console error and no test failure — they only appear as
odd agent behaviour in a live conversation.

---

## 1. Returning fewer Responses than Requests desynchronises the whole batch

**What happens:** the action skips a request (an early `continue`, a filtered
collection, an exception that aborts the loop) and returns 4 responses for 5
requests. Downstream, response *n* is attributed to request *n*, so from index 3
onward every answer is about the wrong record — silently, with no error.

**When it occurs:** any `for` loop that conditionally `add`s to the output, and
every loop that lets an exception escape mid-iteration.

**The documented rule:** *"The inputs and outputs must match on both the size and
the order"*, and methods *"must return the same number of results as inputs
received, even when errors occur."*
— [InvocableMethod Annotation](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_annotation_InvocableMethod.htm)

**How to avoid:** pre-size the output list with `null` placeholders and assign by
index, never `add`. Then assert it in the test:

```apex
Assert.areEqual(requests.size(), responses.size(),
    'Invocable must return one Response per Request');
```

---

## 2. `LimitException` is uncatchable — your `catch (Exception e)` never runs

**What happens:** the action does DML inside the per-request loop. A bulk
invocation of 200 requests blows the 150-statement DML limit. The transaction
dies, the planner receives a raw framework failure, and the carefully designed
envelope is never constructed.

**When it occurs:** per-row DML or per-row SOQL inside the invocable loop. It is
invisible in single-request testing, which is how every action is first tested.

**The behaviour:** governor limit exceptions extend `System.LimitException`,
which cannot be caught by `catch (Exception e)` in the normal way — the
transaction is terminated. No amount of defensive `try/catch` inside the loop
recovers it.

**How to avoid:** the two-phase shape in `references/examples.md` Example 1 —
validate and collect in phase 1, execute one bulkified DML in phase 2. Then
prove it with a bulk test using `templates/apex/tests/BulkTestPattern.cls`, which
exercises the 200-record path that a hand-written test never does.

---

## 3. `AuraHandledException` is meaningless outside the Aura/LWC stack

**What happens:** an action is copied from an LWC controller and keeps
`throw new AuraHandledException('Case not found')`. The message the user was
supposed to see never reaches the planner as data — the framework surfaces a
generic failure and the agent loops.

**When it occurs:** any action derived from `@AuraEnabled` code, which is the
most common source of copy-paste for Apex authors.

**How to avoid:** invocables *return*, they do not throw. `AuraHandledException`
exists to sanitise messages for a JavaScript caller; there is no equivalent
contract for the planner. Grep for `AuraHandledException` in any class carrying
`@InvocableMethod`.

---

## 4. One `@InvocableMethod` per class — the "add a second entry point" refactor fails at compile time

**What happens:** a developer adds `closeCase` and `reopenCase` to one class,
both annotated. Compilation fails.

**The documented rule:** the method must be `static` and `public` or `global`,
must live in an outer class (not an inner class), and *"only one invocable
method per class"* is permitted. The only annotation that can coexist with
`@InvocableMethod` is `@Deprecated`.
— [InvocableMethod Annotation](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_annotation_InvocableMethod.htm)

**How to avoid:** one class per action, which matches the design rule in
`templates/agentforce/README.md` — one action is one verb. If two operations
want to share logic, they share a service class and each gets its own thin
invocable wrapper.

---

## 5. `List<List<sObject>>` inside an `@InvocableVariable` is a runtime error

**What happens:** a Response class declares
`@InvocableVariable public List<List<Account>> matches;`. It compiles. It fails
at runtime when the action is invoked.

**The documented rule:** `@InvocableVariable` fields of type `List<List<sObject>>`
are not supported in user-defined classes and cause runtime errors;
`List<List<sObject>>` is valid only as a direct `@InvocableMethod` return type.
— [InvocableMethod Annotation](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_annotation_InvocableMethod.htm)

**How to avoid:** for a variable-length result set, return a serialised JSON
string plus a count, or flatten to `List<sObject>` with a grouping key. Prefer
the JSON string for agent actions anyway — the planner reads text, and a typed
collection buys nothing at the LLM boundary.

---

## 6. `ex.getMessage()` in `userMessage` leaks internals and breaks routing

**What happens:**

```apex
resp.userMessage = 'Sorry: ' + e.getMessage();
```

The customer is shown
`FIELD_CUSTOM_VALIDATION_EXCEPTION, Close date must be after Won date: [CloseDate]`.
Worse, if the org has a validation rule whose error text quotes a field value,
that value — potentially PII — is now in the conversation transcript.

**When it occurs:** the single most common shortcut in generated action code.

**How to avoid:** `userMessage` is authored copy, not derived text. Write one
sentence per reason code, put it in the CMDT registry, and log the raw exception
separately via `templates/apex/ApplicationLogger.cls`. The reviewer's test:
*could this string be printed on a billboard?* If not, it does not belong in
`userMessage`.

There is a secondary reason beyond disclosure: message text varies by locale and
by release, so any subagent instruction (called a topic instruction before April
2026) that pattern-matches on it is fragile in a way that branching on
`reasonCode` is not.

---

## 7. Branching on error message text instead of `StatusCode`

**What happens:** `if (e.getMessage().contains('INSUFFICIENT_ACCESS'))`. It works
in English, in this release, for this error. It stops working when the org
enables a translation, or when Salesforce rewords the message.

**How to avoid:** `Database.Error.getStatusCode()` returns a `StatusCode` enum —
a stable, comparable platform contract. For `DmlException`, use
`e.getDmlType(0)`. Both survive localisation and rewording; string matching does
not.

---

## 8. Empty input list produces an empty output the planner reads as success

**What happens:** an upstream filter removes every item, the invocable receives
an empty list, returns an empty list, and the planner — having asked for
something and received no error — generates *"Done, I've closed those cases."*

**When it occurs:** actions whose inputs are produced by another action or by a
Flow collection.

**How to avoid:** an empty response array is a legitimate answer to an empty
request array, so the fix is not in Apex. It belongs in subagent instructions:
*"If the action returns no results, do not claim success — tell the user nothing
matched and ask how to proceed."* Add a golden eval case for the empty path;
this is one of the few failures that unit tests structurally cannot catch,
because the Apex is correct.

---

## 9. `with sharing` is not FLS, and agent users usually have broad FLS

**What happens:** the action is `with sharing`, passes review, and updates a
field the running user should not be able to write. Sharing governs *record*
visibility. Field-level security is separate.

**How to avoid:** use `AccessLevel.USER_MODE` on DML and `WITH USER_MODE` on
SOQL (or `Security.stripInaccessible`) so the running user's CRUD and FLS are
enforced. `templates/apex/SecurityUtils.cls` wraps the common cases. This
matters more for agent actions than for most Apex because the running user in an
agent session is frequently provisioned for breadth of task coverage.

---

## 10. Retryable and non-retryable collapsed into one flag

**What happens:** the envelope has `success: Boolean`. The planner has no way to
distinguish "this will never work, stop" from "this might work, try once more",
so it applies its default heuristic — re-invoking — and burns turns on a
validation rule that will reject it identically every time.

**How to avoid:** `status` and `retryable` are independent axes and both are
needed:

| | retryable = false | retryable = true |
|---|---|---|
| **USER_ERROR** | Validation rule, no permission, record deleted | Rare; usually means "ask the user for different input first" |
| **SYSTEM_ERROR** | Upstream auth misconfigured, contract break | Row lock, 503, timeout, rate limit |

The subagent instruction reads both. A single boolean cannot express the table.

---

## 11. Actions that mutate are not idempotent, and the planner may call them twice

**What happens:** the action creates a Case. A transient error causes the
planner to retry. Two Cases now exist, and the second one is invisible to the
conversation because the agent reported one creation.

**When it occurs:** any `retryable = true` classification on a mutating action —
including the timeout case, where the write may well have succeeded upstream
before the connection dropped.

**How to avoid:** either make mutating actions idempotent with a caller-supplied
key, or never mark them retryable.

```apex
// Caller (subagent) supplies a stable key derived from the conversation turn.
@InvocableVariable(required=true label='Idempotency Key')
public String idempotencyKey;

// Action upserts on an External Id rather than inserting.
Case c = new Case(Idempotency_Key__c = req.idempotencyKey, /* ... */);
Database.upsert(c, Case.Idempotency_Key__c, false, AccessLevel.USER_MODE);
```

A unique External Id field makes the second call a no-op update rather than a
duplicate insert. For a timeout on a callout, the same principle applies at the
upstream API: send an idempotency key header, or classify the timeout as
non-retryable and accept the manual reconciliation.

---

## 12. Descriptions are planner input, not documentation

**What happens:** the `@InvocableMethod` description reads
`'Case handler method'` and the `@InvocableVariable` descriptions are blank. The
action is never selected, or is selected for the wrong intent, and the team
debugs the subagent instructions for a week.

**The documented behaviour:** *"The descriptions in both `@InvocableMethod` and
`@InvocableVariable` are important because they allow your agent to understand
how to use the action"*, and the instruction fields in Agentforce Builder are
pre-filled from those descriptions.
— [Agentforce Workshop: Apex Actions](https://developer.salesforce.com/agentforce-workshop/agents/4-apex-actions). The quoted sentence is from the workshop, not from [Create Custom Actions Using Apex InvocableMethod](https://developer.salesforce.com/docs/ai/agentforce/guide/agent-invocablemethod.html) — that guide page shows `description` only inside its code sample and never states why it matters. Both pages are worth reading; only one carries this claim.

**How to avoid:** write the description as the sentence you would say to a
colleague explaining when to use this and when not to. Include the negative:
*"Closes an existing case. Does not create cases and does not reopen closed
ones."* The exclusion is what stops the planner reaching for it on an adjacent
intent — the same reason skill descriptions in this repo carry a "NOT for"
clause.

---

## 13. Coverage says 100% but no error branch was ever asserted

**What happens:** the test invokes the action once with valid input, gets an
`OK`, and the deployment gate is satisfied. Every classification branch in
`classify()` is untested. The first production validation-rule failure returns
`UNKNOWN` because the branch had a typo.

**How to avoid:** one test per reason code, asserting the code and not merely
the absence of an exception:

```apex
@IsTest
static void validation_failure_returns_validation_blocked() {
    // Arrange: a Case whose validation rule will reject the close.
    Case c = TestDataFactory.caseRequiringResolution();
    CloseCaseAction.Request req = new CloseCaseAction.Request();
    req.caseId = c.Id;
    req.resolutionSummary = 'x';   // passes the Apex guard, fails the rule

    Test.startTest();
    List<CloseCaseAction.Response> out =
        CloseCaseAction.run(new List<CloseCaseAction.Request>{ req });
    Test.stopTest();

    Assert.areEqual(1, out.size());
    Assert.areEqual('USER_ERROR', out[0].status);
    Assert.areEqual('VALIDATION_BLOCKED', out[0].reasonCode);
    Assert.isFalse(out[0].retryable, 'validation failures are terminal');
    Assert.isFalse(out[0].userMessage.contains('FIELD_CUSTOM_VALIDATION'),
        'raw platform error text must not reach the user');
}
```

The last assertion is the one that keeps `getMessage()` out of `userMessage`
permanently. Use `templates/apex/tests/MockHttpResponseGenerator.cls` for the
callout branches — a 404, a 503, and a timeout each need their own test.
