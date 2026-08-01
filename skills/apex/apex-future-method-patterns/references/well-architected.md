# Well-Architected Notes — Apex Future Method Patterns

## Relevant Pillars

`@future` is a low-effort async mechanism with significant
architectural consequences. Each pillar has a non-obvious lens
that practitioners miss when they treat `@future` as
"Queueable but simpler."

- **Reliability** — `@future` has the weakest retry guarantees of any
  Apex async option. Five attempts with exponential backoff, then
  silent failure into `AsyncApexJob.Status = 'Failed'` with no
  dead-letter queue. The platform never re-queues, never alerts the
  developer, and never persists the failed payload anywhere outside
  the (truncated) `AsyncApexJob.ExtendedStatus`. Any operation whose
  loss is unacceptable should not use `@future`.
- **Performance** — `@future` is the cheapest way to release a user's
  transaction quickly (push work to a separate async context). It is
  also the cheapest way to silently exceed transaction limits, because
  the 50-future ceiling is per-transaction across all triggers and
  flows — multiple `@future`-using systems on the same object can
  trigger limit errors that neither author predicted.
- **Operational Excellence** — `@future` failures are invisible by
  default. They appear in Setup → Apex Jobs but produce no email, no
  log entry, and no record-level error. An ops-mature org wires every
  `@future` to a custom logging object on entry/exit and runs a
  scheduled audit query for stale jobs. Without that scaffolding,
  the operations team learns about failures only when downstream
  systems start complaining about missing data.
- **Scalability** — The 250,000-per-24-hours per-license limit on
  `@future` calls sounds high but is reached quickly in orgs with
  active integrations or bulk-data flows. Once hit, every future
  fails until the rolling window expires. No per-object or per-user
  partition is available — the limit is org-wide.

## Architectural Tradeoffs

The defining tradeoff for `@future` is **simplicity vs.
modernization debt**. The mechanism has zero ceremony — one
annotation, no extra classes, no chaining boilerplate. Queueable is
the modern equivalent with strictly more capability (chaining, SObject
parameters, better monitoring) but requires implementing the
`Queueable` interface, an inner state object, and explicit
`System.enqueueJob` calls.

| Dimension | `@future` | Queueable |
|---|---|---|
| Boilerplate | 1 line (`@future`) | ~10 lines (interface + class) |
| Parameter types | Primitives + collections only | Any (SObject, Apex objects, primitives) |
| Chaining | Not supported (`AsyncException`) | Up to 5 deep (1 in test) |
| Monitoring | `AsyncApexJob` (limited fields) | `AsyncApexJob` + class-name visibility |
| Test execution | Requires `Test.startTest()` boundary | Same, but jobId is queryable mid-test |
| Re-queue on fail | 5 platform retries, then silent | Same retry behavior, but easier to instrument |
| Callouts | `callout=true` annotation | `Database.AllowsCallouts` interface |

For new code, the tradeoff almost always favors Queueable. The
exception is a one-off trigger-side callout where the work is
genuinely fire-and-forget and the developer has no monitoring
budget — a temporary integration hook, for example. For
modernization of existing `@future` code, the calculus is
different: rewriting a working future into Queueable adds risk
without delivering user-visible benefit unless one of the
`@future` limitations is biting (typically: the chaining
prohibition).

A second tradeoff worth naming: **callout transactional boundary
vs. data freshness.** A `@future(callout=true)` from a trigger
sees the *committed* version of the trigger's DML when it
re-queries inside the future. If a subsequent trigger or
flow modifies the same record before the future runs, the future
sees that update too. For most use cases this is desirable
(latest data wins). For audit-style callouts where the payload
must reflect "the state that triggered the notification," the
future must serialize and stash the relevant fields into
parameters (as a JSON-encoded `String`) rather than re-querying.

## Anti-Patterns

1. **Treating `@future` as fire-and-monitor.** It is fire-and-forget.
   Without external instrumentation (custom logging object, Platform
   Event on completion, scheduled audit job), a failed future is
   indistinguishable from a future that hasn't run yet. Ops-mature
   designs always pair `@future` with persistent logging.
2. **Passing SObjects via JSON serialization to dodge the primitive
   limit.** The pattern (`@future static void f(String json) { ... JSON.deserialize(...) }`)
   compiles and runs, but it freezes the SObject state at enqueue
   time — defeating the value of `@future` re-querying for fresh
   data. If you need stale-state semantics, use it consciously;
   if you don't, pass `Set<Id>` and re-query inside.
3. **Using `@future` from a Batch Apex `execute()` method.** Throws
   `AsyncException: Future method cannot be called from a future or
   batch method.` The fix is rarely "switch the future to Queueable" —
   it's "do the work synchronously inside `execute()`," because Batch
   Apex already provides the async context the future was meant to
   create.
4. **Hoping `@future` retries will cover external-service flakiness.**
   The 5-retry budget is not enough for any service with <99.9%
   availability. Treat `@future` retries as a safety net for
   transient Salesforce-side issues (e.g., row-lock contention),
   not as an availability mechanism for the external service.

## Official Sources Used

- Apex Developer Guide — Future Methods:
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_invoking_future_methods.htm
- Apex Developer Guide — Execution Governors and Limits (future-per-invocation:
  "0 in batch and future contexts; 50 in queueable context"; enqueueJob: 50 sync / 1 async):
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- Apex Developer Guide — Async Apex limits:
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_async.htm
- Apex Reference — `@future` annotation:
  https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_classes_annotation_Future.htm
- Apex Developer Guide — `AsyncApexJob`:
  https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_asyncapexjob.htm
- Salesforce Well-Architected — Resilient:
  https://architect.salesforce.com/well-architected/adaptable/resilient
- Async-selection decision tree (repo-internal):
  `standards/decision-trees/async-selection.md`
