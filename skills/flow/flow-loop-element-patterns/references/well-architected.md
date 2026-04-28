# Well-Architected Notes — Flow Loop Element Patterns

How correct (and incorrect) Loop usage maps to the Salesforce Well-Architected pillars.

## Relevant Pillars

- **Reliability** — A flow that handles 1 record but fails at 200 is unreliable by definition. The Loop element is the single most common cause of "works in sandbox, fails in production under data load." Bulk-safe loop patterns (collect-then-DML, no SOQL inside) are the primary mechanism for keeping a flow reliable across all entry points: UI single-record edit, Bulk API insert, integration push, Data Loader, scheduled batch. A reliable loop is one whose behavior at N=1 and N=200 differ only in element count, not in success/failure.

- **Performance** — Loop body algorithmic complexity directly determines flow runtime. A Loop with O(n) body running over 200 records is fast; the same body wrapped in a nested loop becomes O(n²) and burns the 2,000-element budget on input sizes that should be trivial. Performance also touches transaction-level cost: every in-loop DML adds to the per-transaction DML budget shared with every other automation, so an O(n)-DML loop steals headroom from siblings even when it does not itself fail.

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

## Anti-Patterns This Skill Helps Avoid

1. **DML inside loop body** — directly issues N DML statements; the highest-frequency cause of `Too Many DML Statements: 151` in record-triggered flows. Refactor with collect-then-DML.
2. **SOQL inside loop body** — issues N SOQL queries against the 100-sync-SOQL cap; resolve with a single up-front Get Records that loads all needed rows into a collection used as a map.
3. **Subflow-in-loop with hidden DML / SOQL** — passes review because the parent flow looks clean. Mandates inspecting every subflow called inside any loop body and re-bulkifying it to accept a `List<>` input.
4. **Nested loops** — O(n*m) element-execution cost. Acceptable only when one collection is hard-bounded to a small constant; otherwise pre-load and use a map-lookup pattern, or escalate to invocable Apex.
5. **Mutating the iteration variable expecting database persistence** — Flow's loop variable for SObject collections is a reference, but Flow does not auto-DML on loop end. Practitioners assume persistence; a single Update Records on the accumulated collection is required.
6. **Wrapping the in-loop DML in a Decision to "fix" it** — gating the DML still keeps it inside the loop and N-bounded. The fix must be structural: move the DML out.

## Official Sources Used

- Flow Loop element reference — https://help.salesforce.com/s/articleView?id=platform.flow_ref_elements_loop.htm&type=5
- Flow Builder Considerations and Limits — https://help.salesforce.com/s/articleView?id=sf.flow_considerations_limits_general.htm&type=5
- Flow Best Practices — https://help.salesforce.com/s/articleView?id=sf.flow_prep_bestpractices.htm&type=5
- Apex Governor Limits (transaction-shared DML / SOQL caps) — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_gov_limits.htm
- Salesforce Well-Architected Framework — https://architect.salesforce.com/well-architected/overview
- Collection Filter element — https://help.salesforce.com/s/articleView?id=platform.flow_ref_elements_collection_filter.htm&type=5
- Transform element — https://help.salesforce.com/s/articleView?id=platform.flow_ref_elements_transform.htm&type=5
