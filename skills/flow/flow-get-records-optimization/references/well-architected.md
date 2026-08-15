# Well-Architected — Get Records

## Relevant Pillars

- **Performance Efficiency** — the four dimensions that make a Get Records
  expensive are how often it runs, how many rows it touches, how many fields it
  stores, and whether the filter is selective. Only the first is visible on the
  canvas, which is why flows that look fine perform badly.
- **Reliability** — a query that is merely slow inside a 200-interview batch
  surfaces as a CPU limit somewhere that looks unrelated. Selectivity work is
  reliability work, not just performance work.
- **Adaptable** — a named `queriedFields` list is faster and more brittle than
  automatic storage: a field added downstream and forgotten in the query returns
  null rather than erroring. Choosing per element rather than by blanket rule is
  what keeps both properties where they belong.

## Architectural Tradeoffs

- **One query plus in-memory matching vs a query per record:** the nested-loop
  match is O(n×m) CPU and zero extra queries. Given SOQL is budgeted at 100
  statements and CPU at 10,000 ms synchronous, that trade almost always favours
  the single query — but at large n×m it inverts, and the answer is an invocable
  Apex helper doing the join in a real `Map`. Make that call on measured CPU.
- **Two selective queries vs one clever cross-object query:** filtering children
  on a parent field is one statement and often non-selective. Querying parents,
  collecting Ids, then querying children on the indexed foreign key is two
  statements and two selective queries. Two cheap beats one expensive, given the
  100-statement budget.
- **Named fields vs automatic storage:** heap is 6 MB synchronous and 12 MB
  asynchronous, and a screen flow re-serializes variables between screens.
  Name fields on large collections over wide objects; accept automatic storage on
  single-record lookups where the saving is negligible and the brittleness is
  not.
- **Cache in a variable vs re-query:** cache facts that cannot change during the
  interview (the running user's manager, a Custom Metadata row); re-query facts
  another user can edit. A paused interview makes staleness a matter of days,
  not seconds, so "query once" is not a universal rule.
- **Flow Get Records vs an Apex selector:** Flow keeps the query admin-visible
  and admin-owned. Apex gets real `Map` semantics, `QueryLocator` streaming past
  the 50,000-row transaction ceiling, and a loud `QueryException` on a
  non-selective query against a large object rather than silent slowness. Cross
  over for hot paths and complex joins.

## Hygiene

- No Get Records reachable from inside a Loop.
- Every limits analysis states `per-interview cost × batch size`.
- Every large-object filter leads with something genuinely selective, verified in
  the Developer Console Query Plan tool (Cost above 1 means a full table scan).
- `assignNullValuesIfNoRecordsFound` is `true` wherever an `IsNull` check
  follows.
- Not-found is handled by a Decision, never by a fault connector.
- Named `queriedFields` on collections over wide objects.
- Collections are trimmed before a Pause element.
- No `Contains` filter on a large object in a screen flow.

## Related

- `flow/flow-bulkification` — the collection patterns that replace a query in a
  loop.
- `flow/flow-large-data-volume-patterns` — indexes, skinny tables, and LDV
  behaviour in depth.
- `flow/flow-batch-processing-alternatives` — when the batch-size arithmetic says
  the workload has outgrown the flow.
- `flow/flow-governor-limits-deep-dive` — the full per-transaction budget.
- `flow/flow-interview-debugging` — attributing a limit error to the right
  consumer.
- `standards/decision-trees/automation-selection.md` — when the query work is a
  signal the logic belongs in Apex.

## Official Sources Used

- Get Records Element — https://help.salesforce.com/s/articleView?id=platform.flow_ref_elements_data_get.htm&type=5
- Per-Transaction Apex Governor Limits — 100 SOQL synchronous / 200 asynchronous, 50,000 query rows, 10,000 ms / 60,000 ms CPU, 6 MB / 12 MB heap — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- Best Practices for Deployments with Large Data Volumes — https://developer.salesforce.com/docs/atlas.en-us.salesforce_large_data_volumes_bp.meta/salesforce_large_data_volumes_bp/
- Maximizing the Performance of Force.com SOQL, Reports, and List Views (Salesforce Developers) — standard index selective below 30% of the first million targeted records and 15% beyond, capping at 1,000,000; custom index below 10% / 5%, capping at 333,333; standard-indexed fields are primary keys (Id, Name, OwnerId), foreign keys (CreatedById, LastModifiedById, lookup and master-detail fields), and audit fields (CreatedDate, SystemModstamp) — https://developer.salesforce.com/blogs/engineering/2013/07/maximizing-the-performance-of-force-com-soql-reports-and-list-views
- Developer Console Query Plan Tool FAQ — a Cost above 1 means the filter is not selective and a full table scan will be used — https://help.salesforce.com/s/articleView?id=000386864&type=1
- Make a SOQL Query Selective by Marking a Field as External ID or Unique — https://help.salesforce.com/s/articleView?id=000383981&type=1
- Flow metadata type — `FlowRecordLookup` fields (`object`, `filters`, `filterLogic`, `queriedFields`, `sortField`, `sortOrder`, `limit`, `getFirstRecordOnly`, `storeOutputAutomatically`, `assignNullValuesIfNoRecordsFound`, `outputReference`, `faultConnector`) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_visual_workflow.htm
- Improve Performance with Batching for Scheduled Flows (Summer '26) — batch size 1–200 on the Start element, runtime version 63.0+ — https://help.salesforce.com/s/articleView?id=release-notes.rn_automate_flow_builder_scheduled_flow_batching.htm&release=262&type=5
