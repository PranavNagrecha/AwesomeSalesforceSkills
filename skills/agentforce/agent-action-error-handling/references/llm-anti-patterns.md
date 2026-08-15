# LLM Anti-Patterns — Agent Action Error Handling

What AI assistants generate when asked for "an Agentforce action with error
handling," why each shape is produced, the correction, and the review signal.

---

## Anti-Pattern 1: `throw` instead of `return`

**What the LLM generates:**

```apex
@InvocableMethod(label='Close Case')
public static List<String> run(List<Request> reqs) {
    for (Request r : reqs) {
        if (r.caseId == null) {
            throw new IllegalArgumentException('caseId is required');
        }
        // ...
    }
}
```

**Why it happens:** throwing on invalid input is correct, idiomatic Apex and
correct in essentially every other context — services, triggers, REST resources.
The model applies a well-founded general rule to the one place it does not hold.
It has no representation of the planner as a *consumer that reads return values
as reasoning input*.

**Correct pattern:** every failure is a `Response` in the slot belonging to that
`Request`. The method signature promises one output per input and the platform
enforces it; an exception breaks that promise for every request in the batch,
not just the failing one.

**Detection hint:** any `throw` statement inside a class carrying
`@InvocableMethod`, other than in a private helper whose caller catches it. Make
it a lint rule.

---

## Anti-Pattern 2: `ex.getMessage()` piped into the user-visible field

**What the LLM generates:**

```apex
} catch (Exception e) {
    resp.success = false;
    resp.errorMessage = e.getMessage();
}
```

**Why it happens:** it is the single most common Java/Apex catch idiom in
training data, and it is genuinely right for a log. The model does not
distinguish the log sink from the conversation sink because in most codebases
they are the same field.

**Correct pattern:** two fields with two audiences. `userMessage` is authored
copy per reason code, safe to read aloud. The raw exception goes to
`ApplicationLogger` (`templates/apex/ApplicationLogger.cls`) where SRE needs it
and the customer never sees it.

**Detection hint:** `getMessage()` appearing in any expression assigned to a
field annotated `@InvocableVariable`. One grep, high signal.

Note the canonical skeleton at `templates/agentforce/AgentActionSkeleton.cls`
uses `errorMessage = e.getMessage()` as a scaffold placeholder for the generic
case — replace it with a classified `userMessage` before the action carries
anything user-facing.

---

## Anti-Pattern 3: `Boolean success` as the entire error contract

**What the LLM generates:**

```apex
public class Response {
    @InvocableVariable public Boolean success;
    @InvocableVariable public String message;
}
```

**Why it happens:** it is the minimal shape that satisfies "return whether it
worked," and it mirrors thousands of API wrappers. The model is not modelling
the downstream consumer's decision — it produces a *result*, not a *routing
signal*.

**Correct pattern:** the planner must answer two independent questions before it
can act: *whose problem is this* (`status`: USER_ERROR vs SYSTEM_ERROR) and
*would doing it again help* (`retryable`). Plus a stable `reasonCode` to branch
instructions on. A boolean cannot express the 2×2.

**Detection hint:** a Response class with a boolean and a string and nothing
else. If the subagent instructions (called topic instructions before April 2026)
cannot be written as a branch table over the response, the response is
under-specified.

---

## Anti-Pattern 4: One catch-all `catch (Exception e)` and no classification

**What the LLM generates:**

```apex
try {
    // everything
} catch (Exception e) {
    resp.status = 'ERROR';
    resp.reasonCode = 'UNKNOWN';
}
```

**Why it happens:** a single catch is defensible, compiles, and passes review in
most codebases. Enumerating `DmlException`, `CalloutException`, `QueryException`,
`JSONException` requires knowing which the code can raise, which is exactly the
context a single-file generation lacks.

**Correct pattern:** classify by locus of control. Every branch answers "can the
user fix this?" and "is it worth retrying?" A catch-all is fine as the *last*
branch, and it should log loudly precisely because it means classification is
incomplete.

**Detection hint:** count distinct `reasonCode` literals in an action. One or two
means everything collapses to `UNKNOWN` in production, and the dashboard will be
useless.

---

## Anti-Pattern 5: Per-row DML inside the invocable loop

**What the LLM generates:**

```apex
for (Request r : requests) {
    update new Case(Id = r.caseId, Status = 'Closed');
}
```

**Why it happens:** the loop is the natural expression of "process each
request", and the model has been asked for error handling, not for
bulkification — so it optimises the requested axis. Single-request examples in
the Agentforce documentation reinforce the shape.

**Correct pattern:** two phases — validate and collect, then one bulk
`Database.update(records, false, AccessLevel.USER_MODE)` and map results back by
index. The `allOrNone = false` flag is what preserves per-request outcomes.

**Detection hint:** any DML or SOQL statement lexically inside a `for` loop in
an invocable class. This is also the anti-pattern most likely to pass all tests
and fail in production, because tests invoke with one request.

---

## Anti-Pattern 6: `AuraHandledException` in an agent action

**What the LLM generates:**

```apex
throw new AuraHandledException('You do not have access to this case.');
```

**Why it happens:** the model has strong associations between "Salesforce",
"user-friendly error", and `AuraHandledException` — it is the documented answer
for LWC controllers, which are the most common Apex-with-a-UI-consumer pattern
in training data. Agent actions look like the same problem shape.

**Correct pattern:** `AuraHandledException` sanitises a message for a JavaScript
client. There is no analogous contract with the planner; it sees a framework
failure. Return `USER_ERROR / NO_ACCESS` with an authored `userMessage`.

**Detection hint:** `AuraHandledException` + `@InvocableMethod` in the same file.

---

## Anti-Pattern 7: Inventing an Agentforce error-handling API

**What the LLM generates:** confident, syntactically plausible constructs that
do not exist — `AgentActionException`, `@InvocableMethod(errorHandler='...')`,
`Agentforce.reportError()`, a `<errorHandling>` element inside
`GenAiPlannerBundle`, or a `retryPolicy` attribute on a subagent.

**Why it happens:** this is the highest-risk failure mode in the Agentforce
domain. The product was renamed (Einstein Copilot → Agentforce), the metadata
types changed shape (`GenAiPlanner` → `GenAiPlannerBundle`), and the surrounding
ecosystem — Flow, REST, Platform Events — supplies dozens of plausible
neighbouring names to interpolate from. The result is well-formed code for an
API that never shipped.

**Correct pattern:** the real surface is small. Error handling in an agent action
is **plain Apex** — `try`/`catch`, `Database.SaveResult`, `StatusCode` — plus a
typed response class and subagent instructions written in English. There is no
platform-level retry policy, no error-handler hook, and no exception type
specific to agents. The real Agentforce metadata types are `AiAuthoringBundle`,
`Bot`, `BotVersion`, `ConversationVariable`, `GenAiFunction`,
`GenAiPlannerBundle`, and `GenAiPlugin`
([Agentforce Metadata Types](https://developer.salesforce.com/docs/ai/agentforce/references/agents-metadata-tooling/agents-metadata.html)).

**Detection hint:** any identifier containing "Agentforce" or "Agent" that is
being used as an Apex type or annotation attribute. Verify against the Apex
Developer Guide or deploy to a scratch org before it enters a design doc.

---

## Anti-Pattern 8: Building the envelope and never writing the instructions

**What the LLM generates:** a well-structured Apex response class, tests, and
no mention of the subagent configuration. The answer ends at the class.

**Why it happens:** the prompt said "Apex action", the model produced Apex. The
instruction layer is a different artefact in a different language in a different
tool, and nothing in the request pointed at it.

**Correct pattern:** the envelope is half a contract. Without one instruction
per outcome class, the planner improvises — and its default on an unsatisfied
goal is to try again, which reproduces exactly the loop the envelope was built
to prevent. Ship the instruction block with the class
(`references/examples.md` Example 2).

**Detection hint:** the PR touches `.cls` files and no subagent metadata or
instruction documentation. Ask which instruction consumes each new reason code.

---

## Anti-Pattern 9: Marking a mutating action retryable

**What the LLM generates:** a `create`/`insert` action that classifies timeouts
and 503s as `retryable = true`, on the reasonable ground that transient failures
deserve a retry.

**Why it happens:** retry-on-transient is correct and well-represented for
*reads*. The model does not track that this particular action has a side effect,
because side-effect-awareness is a property of the whole call graph rather than
of the catch block being written.

**Correct pattern:** retryable requires idempotency. Either add a caller-supplied
idempotency key and upsert on an External Id, or classify mutating failures as
terminal and let the human reconcile. A timeout is the dangerous case: the write
may have committed upstream before the connection dropped, so "retry" can mean
"do it twice."

**Detection hint:** `retryable = true` in a class that performs `insert`,
`update`, `delete`, or a non-GET callout, with no idempotency key in the Request.

---

## Anti-Pattern 10: Tests that assert "no exception" and call it error coverage

**What the LLM generates:**

```apex
@IsTest
static void testCloseCase() {
    Test.startTest();
    CloseCaseAction.run(new List<CloseCaseAction.Request>{ req });
    Test.stopTest();
    // no assertions, or System.assert(true)
}
```

**Why it happens:** it satisfies the coverage requirement, which is the
measurable gate the model is optimising against. Forcing a specific catch branch
requires org-specific setup — a validation rule, a permission-less user, a mock
callout — that a single-file generation cannot know about.

**Correct pattern:** one test per reason code, each asserting the code, the
`retryable` flag, and the absence of raw platform text in `userMessage`. Force
the branches deliberately: `TestUserFactory` for the permission path,
`MockHttpResponseGenerator` for the HTTP status paths, and a purpose-built
validation rule fixture for the DML path — all under `templates/apex/tests/`.

**Detection hint:** the test class has fewer assertions than the action has
reason codes. That ratio is a better quality signal than the coverage
percentage.
