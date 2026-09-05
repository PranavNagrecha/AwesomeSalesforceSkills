# Well-Architected Notes — Flow Loop Element Patterns

How correct (and incorrect) Loop usage maps to the Salesforce Well-Architected pillars.

## Relevant Pillars

- **Reliability** — A flow that handles 1 record but fails at 200 is unreliable by definition. The Loop element is the single most common cause of "works in sandbox, fails in production under data load." Bulk-safe loop patterns (collect-then-DML, no SOQL inside) are the primary mechanism for keeping a flow reliable across all entry points: UI single-record edit, Bulk API insert, integration push, Data Loader, scheduled batch. A reliable loop is one whose behavior at N=1 and N=200 differ only in element count, not in success/failure.

- **Performance** — Loop body algorithmic complexity directly determines flow runtime. A Loop with O(n) body running over 200 records is fast; the same body wrapped in a nested loop becomes O(n²) and burns the transaction's CPU-time budget on input sizes that should be trivial. Performance also touches transaction-level cost: every in-loop DML adds to the per-transaction DML budget shared with every other automation, so an O(n)-DML loop steals headroom from siblings even when it does not itself fail.

- **Operational Excellence** — Predictable element counts make a flow operationally observable. A loop whose worst-case element-execution count is `body × max_iterations + post_work` is something an operator can monitor (Setup → Flow runtime debug, paid Flow Analytics, custom CMDT thresholds). A nested or unbounded loop has no useful upper bound and fails non-deterministically as data shapes shift.

- **Security** — Indirectly applicable. Loops that issue DML inside the body cannot wrap the writes in a single transactional sharing-context decision; if any iteration's record fails sharing checks the partial-rollback semantics depend on whether the whole interview is in System or User mode. Pulling DML outside the loop collapses N security evaluations into one, which is easier to audit. Refer to `flow-runtime-context-and-sharing` for the runtime-context implications.

- **Scalability** — Bulk-safe loops are the path from "works for one user clicking a button" to "works under a 10K-row Bulk API insert." Without the collect-then-DML refactor, a flow's scalability ceiling is `min(150 ÷ in_loop_dml_count, 100 ÷ in_loop_soql_count)` records per transaction — typically under 100 in any non-trivial body. With the refactor, the ceiling becomes the bulk-batch size (200 for save triggers).

## Architectural Tradeoffs

| Tradeoff | Loop-Heavy Choice | Loop-Free / Bulk Choice | Decision Driver |
|---|---|---|---|
| Element count vs declarative intent | Loop + Decision + Assignment | Collection Filter | Fewer elements, clearer intent — always prefer when no DML / enrichment is needed |
| Read intent vs reusability | Inline loop body | Subflow called inside loop | Subflows reduce duplication, but force you to bulkify the subflow's body too — easy to miss, see Gotcha 5 |
| Flow declarative vs Apex code | Two nested loops with Decision | Invocable Apex with `Map<Id, SObject>` | When inner-collection size approaches the outer's, the O(n²) cost forces escalation to Apex |
| Per-iteration safety vs transaction efficiency | DML inside loop with try/fault path per iteration | Single post-loop DML with one fault path | Per-iteration fault paths cost element-executions and DML count; consolidate where business logic permits |
| Eager filter vs lazy filter | Pre-filter input via Get Records criteria | Loop everything, filter inside | Pushing the filter to SOQL is faster (database does the work) and saves loop iterations |
| Bounded working set vs complete pass | Loop the whole Get Records output | Sort processor with `limit`, or Get Records `limit` (2–20,000, API 63.0+) | `limit` applies *after* the sort (`api_meta.txt` L69961–69967), so top-N is exact. Cutting iterations is the only fix that scales sublinearly |
| Readable XML vs terse XML | Loop + Decision + Assignment, three named elements a reviewer can point at | One Filter processor with a `formula` | The formula is one element but is opaque to review and untestable in isolation; prefer `conditions` unless the predicate genuinely needs a formula |
| Portable metadata vs Builder-authored metadata | Hand-write the collection processor XML | Retrieve one from an org and adapt it | `api_meta.txt` documents every `FlowCollectionProcessor` field but ships no sample; the enum `RecommendationMapCollectionProcessor` is not guessable |

## Anti-Patterns This Skill Helps Avoid

1. **DML inside loop body** — directly issues N DML statements; the highest-frequency cause of `Too Many DML Statements: 151` in record-triggered flows. Refactor with collect-then-DML.
2. **SOQL inside loop body** — issues N SOQL queries against the 100-sync-SOQL cap; resolve with a single up-front Get Records that loads all needed rows into a collection used as a map.
3. **Subflow-in-loop with hidden DML / SOQL** — passes review because the parent flow looks clean. Mandates inspecting every subflow called inside any loop body and re-bulkifying it to accept a `List<>` input.
4. **Nested loops** — O(n*m) element-execution cost. Acceptable only when one collection is hard-bounded to a small constant; otherwise pre-load and use a map-lookup pattern, or escalate to invocable Apex.
5. **Mutating the iteration variable expecting database persistence** — Flow's loop variable for SObject collections is a reference, but Flow does not auto-DML on loop end. Practitioners assume persistence; a single Update Records on the accumulated collection is required.
6. **Wrapping the in-loop DML in a Decision to "fix" it** — gating the DML still keeps it inside the loop and N-bounded. The fix must be structural: move the DML out.
7. **Designing against the retired 2,000-element ceiling** — decomposing a viable flow, or escalating it to invocable Apex, to dodge a limit that appears in no developer guide (see `references/gotchas.md` Gotcha 3). The estimate stays useful as a CPU proxy; the ceiling does not exist to be avoided.
8. **Using `iterationOrder` as a sort** — `Desc` reverses the collection's listed order, so on an unsorted Get Records it reverses nothing meaningful. Ordering belongs on the query or a Sort processor.
9. **Building a counter loop, an emptiness check, or a set intersection as iteration** — `AssignCount`, an empty-safe post-loop DML, and `RemoveUncommon` / `RemoveAll` each collapse one of those to a single element (API 43.0+).
10. **Omitting `noMoreValuesConnector`** — the loop deploys, and the interview has nowhere to go when the collection empties, including on the first evaluation when it was empty to begin with.

## Official Sources Used

- Metadata API Developer Guide, `FlowLoop` (`api_meta.txt` L70698–70716) — supports the Reliability and Performance claims about what a Loop can and cannot do: five fields, no `faultConnector`, `iterationOrder` as position not sort, `noMoreValuesConnector` as the empty and exhausted path — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide, `FlowAssignmentOperator` (`api_meta.txt` L69767–69880) — supports the "loop-free alternative" tradeoff rows: `AssignCount`, `RemoveAll`, `RemoveUncommon`, `Add` semantics by target type, all API 43.0 and later — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide, `FlowCollectionProcessor` and `FlowCollectionSortOption` (`api_meta.txt` L69927–69996) — supports the Operational Excellence claim that element counts are predictable, and the bounded-working-set tradeoff: the three processor types with version floors, `conditionLogic` `Formula`, and `limit` applying after the sort — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide, `FlowRecordLookup` (`api_meta.txt` L71091–71240) — supports the eager-filter tradeoff row and the ordering anti-pattern: "If `sortField` or `sortOrder` isn't specified, records aren't returned in any particular order", plus `limit` 2–20,000 (API 63.0+) and the `storeOutputAutomatically` / `outputReference` split — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Apex Developer Guide, "Execution Governors and Limits" (`apexdev.txt` L19535–19585) — supports every numeric ceiling in the Scalability and Performance pillars: 150 DML, 100 sync / 200 async SOQL, 50,000 rows, 6 MB / 12 MB heap, 10,000 ms / 60,000 ms CPU, per transaction — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Apex Developer Guide, Workflow-category debug events (`apexdev.txt` L38715–38900) — supports the Operational Excellence claim that a loop is observable: `FLOW_LOOP_DETAIL` gives the real iteration index, `FLOW_BULK_ELEMENT_DETAIL` the records per DML element, `FLOW_INTERVIEW_FINISHED_LIMIT_USAGE` the CPU and DML spend — and shows no executed-element event exists — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Metadata API Developer Guide, `FlowTest` (`api_meta.txt` L73960–74340) — supports the "predictable element counts are testable" claim and its limit: test points attach only to `Start` and `Finish`, so a loop is asserted through the variables it leaves behind — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Salesforce Well-Architected Framework — the pillar definitions this file maps onto — https://architect.salesforce.com/well-architected/overview
- Salesforce KB "Flow Error 'Number of Iterations Exceeded'" — the sole source for the retired 2,000-element limit and its removal in API 57.0, uncorroborated by any developer guide; supports anti-pattern 7 only as the thing not to design against — https://help.salesforce.com/s/articleView?id=000382258&language=en_US&type=1
- Flow Best Practices (avoid DML / SOQL inside loops) — supports anti-patterns 1 and 2 — https://help.salesforce.com/s/articleView?id=sf.flow_prep_bestpractices.htm&type=5
