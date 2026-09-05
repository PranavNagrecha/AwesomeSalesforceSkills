# Well-Architected Notes — Flow Governor Limits Deep Dive

## Relevant Pillars

- **Performance** — Limit budgeting is performance engineering. A flow with 70% headroom survives load spikes; a flow at 95% fails on the first busy day.
- **Reliability** — Shared-transaction math predicts cascading failures before they happen. Adding "one more flow" without budget analysis is how orgs become fragile.

## Architectural Tradeoffs

### Inline vs async execution

| Inline (sync transaction) | Async (Scheduled Path, Platform Event) |
|---|---|
| Fresh limits? No — shared with caller | Fresh limits? Yes |
| Latency | Immediate | 1-5 min |
| Rollback on failure | Yes (with original save) | No (original already committed) |
| User-perceived save time | Flow time adds to save | Negligible |

Rule: async for work that doesn't need to be atomic with the save.

### Budget thresholds

- 70% of limit = healthy
- 70-90% = monitor, consider tuning
- 90%+ = unstable, must tune

Design target: stay under 70% at peak bulk size.

## Anti-Patterns

1. **SOQL/DML in a Loop** — The classic limit breach. Fix: hoist out, bulk-operate on collections.
2. **Nominal-limit reasoning** — Ignoring shared transaction. Fix: forecast total across all automations on the object.
3. **Unbounded collections** — Heap breach. Fix: chunk + process.
4. **No test-level limit assertion** — Regressions ship silently. Fix: assert `Limits.getQueries()` in tests.
5. **Async-as-panacea** — Routing to Scheduled Path without fixing bulk-unsafe code. Fix: fix the code first; async is for transaction isolation, not bulk safety.

## The Budget Ladder

Four levers, cheapest first. Each one costs something the previous one did not.

| Lever | What it changes | What it costs | Grounding |
|---|---|---|---|
| Take DML and SOQL out of loops | spend, not budget | design time only | `apexdev.txt` L19544, L19554 |
| `maxBatchSize` on a scheduled path | how many interviews share one async transaction | more transactions, more elapsed time | `api_meta.txt` L71397–L71398 |
| `flowTransactionModel` `NewTransaction` on an action | the action's own meters | atomicity: committed work is not rolled back if the action fails | `api_meta.txt` L68477–L68478 |
| `scheduledPaths` `pathType` `AsyncAfterCommit` | moves whole branches post-commit | atomicity, plus an idempotency requirement | `api_meta.txt` L71412–L71414; `apexdev.txt` L15479, L15489 |

The ladder is ordered deliberately. The first rung reduces the bill; the other three only move it,
and each one trades a reliability property for headroom. A flow that needs rungs 2–4 before rung 1 has
been applied is being made faster at the failure, not fixed.

## Official Sources Used

- Apex Developer Guide — "Execution Governors and Limits", per-transaction table
  (<https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf>,
  text extract `apexdev.txt` L19542–L19599): every ceiling in this skill's meter table — SOQL 100/200,
  SOQL rows 50,000, DML 150, DML rows 10,000, stack depth 16, callouts 100, `@future` 50,
  `System.enqueueJob` 50/1, `sendEmail` 10, heap 6/12 MB, CPU 10,000/60,000 ms, publish-immediately
  150.
- Apex Developer Guide — governor-table footnotes 1, 2, 3 and 5 (`apexdev.txt` L19612–L19657):
  parent-child subqueries counting as extra queries (Gotcha 3), `Approval.process` and Publish After
  Commit counting as DML statements (the meter table's `submit` and `__e` rows), the stack-depth
  rationale (Gotcha 10), and CPU excluding database and callout wait time (Gotcha 4).
- Apex Developer Guide — "Per-Transaction Certified Managed Package Limits" (`apexdev.txt`
  L19667–L19688): a certified package gets its own 150 DML and 100 SOQL but shares CPU; uncertified
  packages spend yours (Gotcha 9).
- Apex Developer Guide — "Triggers and Order of Execution" (`apexdev.txt` L15402–L15490): the shared
  transaction (Gotcha 1), flow DML re-entering the save procedure at L15468 (Gotcha 10), the recursive
  save skipping steps 9–17 at L15414–L15415 (Gotcha 11), and asynchronous flow paths as post-commit
  logic at L15489 (Gotcha 16 and the async lever in the ladder above).
- Apex Developer Guide — "Debug Log Levels", Workflow event table (`apexdev.txt` L38721–L38900): the
  four flow limit-usage events and the twelve meters each reports, which is both the diagnostic
  procedure in `references/metadata-examples.md` § 7a and the negative behind Gotcha 8.
- Apex Developer Guide — "Exceptions that Can't be Caught" (`apexdev.txt` L39720–L39727):
  `System.LimitException` is uncatchable and neither `catch` nor `finally` runs (Gotcha 6,
  Anti-Pattern 10).
- Apex Reference Guide — `EventBus.publish` usage notes
  (<https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/apexref.pdf>, text extract
  `apexrefguide.txt` L214518–L214528): Publish After Commit spends the DML meter, Publish Immediately
  spends a separate 150-call meter (Gotcha 5, Anti-Pattern 11).
- Apex Reference Guide — `Limits` class method index (`apexrefguide.txt` L220210–L220290) and the
  `Assert` class (L198622): the exact counter names used in the budget test in
  `references/metadata-examples.md` § 7b, and the fact that `System.assertTrue` does not exist
  (Anti-Pattern 12).
- Apex Reference Guide — `Flow.Interview` class usage (`apexrefguide.txt` L157938): "SOQL and DML
  limits apply during flow execution. See Per-Transaction Flow Limits in Salesforce Help." This is the
  developer-guide corpus's only pointer to Flow's own limits page, and it is why every Flow-runtime
  ceiling in this skill that is not an Apex per-transaction meter carries an UNVERIFIED marker.
- Metadata API Developer Guide — `FlowActionCall.flowTransactionModel`
  (<https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf>, text extract
  `api_meta.txt` L68472–L68480), `FlowScheduledPath` (L71389–L71420), `FlowStart.triggerOrder`
  (L68438), `FlowRecordLookup.limit` (L71173–L71180), `FlowCollectionProcessor.limit`
  (L69961–L69967), `FlowStart.object` (L72403–L72405, "a flow interview starts for each record that
  meets the filter conditions"), and `FlowTest` (L73960–L74236): every element name, enum value and
  numeric range in `references/metadata-examples.md`.
- Salesforce App Limits Cheat Sheet
  (<https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_app_limits_cheatsheet.pdf>):
  cited for a **negative** — it contains no Flow, interview or flow-element limit anywhere in its
  1,259 lines (Gotcha 14). Do not send readers there for a flow number.
- Salesforce Developer Documentation — "Configure the User and Batch Size for Your Platform Event
  Trigger" (<https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_trigger_config.htm>):
  the 2,000-message maximum and default for platform event subscriber batches (Gotcha 18).
- Salesforce Developer — Execution Governors and Limits (HTML edition of the first source):
  <https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm>
- Salesforce Developer — Trigger Order of Execution (HTML edition of the fourth source):
  <https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_order_of_execution.htm>
- Salesforce Help — Flow "Per-Transaction Flow Limits" and "Flow Runtime Limits":
  <https://help.salesforce.com/s/articleView?id=sf.flow_considerations_limit.htm>. UNVERIFIED
  (2026-09-05): help.salesforce.com cannot be fetched in this environment. Every claim in this skill
  that rests only on these pages — the paused-interview cap, the scheduled-flow daily record volume,
  the screen-flow and Pause transaction boundaries — carries its own marker beside the claim.
- Salesforce Architects — Well-Architected, Performance: <https://architect.salesforce.com/>
