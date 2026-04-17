# Flow Transactional Boundaries — LLM Anti-Patterns

AI assistants make predictable mistakes when reasoning about Flow transaction boundaries. The errors below have been observed across code reviews, design proposals, and "fix my Flow" conversations.

## 1. Suggesting Before-Save for Work That Requires a Record Id

The assistant sees "just update a field on this record" and recommends Before-Save. The actual requirement is to create a child record referencing the triggering record's Id. Before-Save runs BEFORE the Id is assigned on insert, so the child record creation would fail.

Correct approach:
- Check whether the flow needs `$Record.Id` for a child-record DML.
- If yes, it cannot be Before-Save on insert. Use After-Save or split: Before-Save sets fields, After-Save creates children.

## 2. Recommending "Use a Pause Element" as a General Delay Mechanism

When asked to "run this work 5 minutes later", a naive assistant suggests a Pause element. Pause is for genuine external waits (events, approvals), not for throttling. Using Pause as a delay creates persisted interviews that clutter the org and do not free the transaction budget meaningfully.

Correct approach:
- For time-delayed work with no external trigger, use a Scheduled Path (record-triggered flow) or a scheduled autolaunched flow.
- Reserve Pause for waits on user action, platform events, or wall-clock absolute times in Screen Flows.

## 3. Claiming Subflows Create a New Transaction

Assistants have stated that "calling a subflow resets governor limits." It does not. Subflows run in the parent transaction. An LLM that writes "move the query-heavy logic into a subflow to isolate limits" is giving dangerously wrong advice.

Correct approach:
- State explicitly: subflow calls inherit the parent transaction.
- For isolation, recommend Platform Events + PE-triggered flows, Scheduled Paths, or Queueable Apex.

## 4. Treating `Publish After Commit` as a Substitute for Async Processing

An assistant may say "publish a Platform Event after commit to make the work asynchronous". The PUBLISHER still runs in the originating transaction. Only the SUBSCRIBER runs async. If the publisher is already near its governor limit, `Publish After Commit` does not help.

Correct approach:
- Clarify publisher vs subscriber contexts.
- For publisher-side offloading, use Scheduled Path or Queueable Apex.

## 5. Assuming Flow-Called-From-Apex Gets Its Own Limit Budget

A common mistake is writing code like `Flow.Interview flow = ...; flow.start();` inside a trigger that's already done 140 DML, expecting the Flow to "have its own" budget. It inherits the same budget.

Correct approach:
- Always check `Limits.getDmlStatements()` and `Limits.getQueries()` before dispatching a Flow from Apex in a constrained context.
- For bulk-safe reuse, dispatch Queueable wrapping the Flow instead of calling inline.

## 6. Recommending "Set Up an Async Scheduled Path" Without a Fault Log

An assistant that correctly routes heavy work to an async boundary but does NOT add a fault path to a durable error store has introduced a silent failure mode. The originating save succeeds; the async path fails; nobody knows.

Correct approach:
- Whenever recommending Scheduled Path, also recommend: fault path → Create Records on an error-log object → notification mechanism.
- State the compensation strategy (retry, admin review, auto-reenqueue).

## 7. Confusing "Async" With "Faster"

Assistants sometimes suggest moving work to Scheduled Path to "make the save faster for the user." Scheduled Paths DO move latency off the user's save, but they don't make the total work faster — they often make it slower overall. If the user is waiting on the downstream result, async makes the UX worse.

Correct approach:
- Only recommend async when the user does NOT need the downstream result to complete their workflow.
- For user-visible work that must be done before they proceed, stay synchronous and optimize the work itself.

## 8. Overlooking Combined-Transaction Budget With Apex Triggers

An assistant may approve a Flow's 50-DML after-save design without checking whether the object ALSO has an Apex trigger that does 110 DML. Combined, that's 160 DML — over the 150 limit.

Correct approach:
- Ask whether the object has Apex triggers, other flows, validation rules, or process-builder remnants.
- Sum SOQL and DML across ALL automation on the object.

## 9. Suggesting Orchestration for Short Same-User Flows

Because Orchestration is powerful, assistants over-recommend it. Orchestration has operational overhead (Work Guide visibility, deployment complexity, licensing considerations). A single-user multi-screen flow with no cross-transaction step is better served by a Screen Flow with internal Decision branching.

Correct approach:
- Recommend Orchestration only when steps cross users, days, or require independent retry semantics.
- For linear same-user flows, prefer Screen Flow with Pause elements only when needed.

## 10. Ignoring the Running User of a Resumed Pause

An assistant proposes a Screen Flow that Pauses for 2 days and then queries records. On resumption, the running-user context may differ from the pausing user (scheduler or Automated Process in some cases). Queries that worked at Pause may return different rows.

Correct approach:
- Note which user resumes the interview.
- When resumption user differs from initiator, either re-query defensively or switch to Orchestration (explicit user per step).

## 11. Claiming Before-Save Handles Related Records "If You're Clever"

There is no clever trick. Before-Save does not support related-record create, update, or delete. An assistant that writes a workaround using invocable Apex inside Before-Save is accurate about feasibility, but the invocable Apex workaround shares the same limits and is not a general recommendation.

Correct approach:
- State the restriction plainly.
- Route related-record work to After-Save; reserve invocable-Apex-in-Before-Save for narrowly-scoped performance wins.

## 12. Treating All Async Paths as Equivalent

Scheduled Path, Platform Event subscriber, Queueable, Batch Apex, `@future`, and Orchestration Background Steps are NOT interchangeable. Each has different retry behavior, max duration, concurrency, and failure surfacing. An assistant that says "just make it async" without picking the specific boundary is skipping the actual design step.

Correct approach:
- Route the choice through `standards/decision-trees/async-selection.md`.
- Cite the tree branch that resolves which async mechanism fits the use case.
