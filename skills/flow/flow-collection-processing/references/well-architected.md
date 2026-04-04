# Well-Architected Notes — Flow Collection Processing

## Relevant Pillars

### Performance

Collection processing patterns directly determine how many SOQL queries and DML statements a Flow transaction consumes. Placing DML inside a Loop degrades performance linearly with record volume. Using Collection Filter, Sort, and Transform elements instead of manual Loop-based equivalents reduces element execution count and improves both runtime speed and Flow Interview debug log readability. The correct pattern achieves the same result in fewer elements and fewer platform resource calls.

### Scalability

Record-triggered Flows operate on batches of up to 200 records per transaction. Any design that executes queries or DML proportionally to the record count will fail at scale. Collection-based DML (single `Update Records` or `Create Records` on a collection variable) keeps resource consumption flat regardless of how many records are in the collection, up to the per-transaction row limits. This is the same principle as bulkified Apex list operations.

### Reliability

An incorrectly designed Loop that hits governor limits causes a hard transaction failure that rolls back all changes for the entire batch — not just the record that triggered the fault. Collection-safe patterns protect the reliability of the full transaction. Empty-collection guards using Decision elements prevent silent failures when upstream queries return zero records.

### Operational Excellence

Declarative elements (Collection Filter, Sort, Transform) communicate intent more clearly than equivalent Loop-based implementations. A reviewer or maintainer can understand a Collection Filter in one glance; understanding the equivalent Loop requires tracing branch logic across four to six elements. Clarity reduces review time and the probability of accidental regressions during maintenance.

---

## Architectural Tradeoffs

**Loop-and-accumulate vs. Collection Filter:** Loop is more flexible — it supports per-record conditional branching that Collection Filter does not. Collection Filter is more readable and maintainable for pure subset selection. Use Collection Filter when the goal is selection only; use Loop when each record requires conditional mutation.

**Transform vs. Loop for type conversion:** Transform is limited to field-level value mapping without inline formulas. Loop allows formula-driven field construction. Use Transform when field mappings are direct or use literal values; use Loop when computed values are required.

**Single DML on collection vs. loop DML:** Single collection DML is always preferable unless there is an explicit per-record transactional isolation requirement (rare and should be implemented in Apex, not Flow). Loop DML is not a valid design for production flows with variable record volumes.

---

## Anti-Patterns

1. **DML element inside a Loop** — converts record volume directly into DML statement count. Fails when transaction volume exceeds 150 DML statements. Correct approach: accumulate in an output collection variable, commit with a single DML element after "After Last."

2. **Manual loop-based subset accumulation when Collection Filter is available** — requires 4–6 elements and branch logic to replicate what a single Collection Filter element achieves. Creates review overhead and maintenance surface. Correct approach: use Collection Filter with explicit condition logic.

3. **Unguarded Loop over a potentially empty collection with required downstream DML** — when Get Records returns zero records, the Loop exits silently and downstream DML silently creates or updates nothing. If the absence of DML is a bug rather than expected behavior, there is no fault raised. Correct approach: guard with a Decision element on collection size before the Loop.

4. **Using Transform for computed field values** — Transform does not support formula expressions. Silent null values on target fields result. Correct approach: compute intermediate values in Assignment elements or formula variables before the Transform element.

---

## Official Sources Used

- Flow Reference — Assignment Element: https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_assignment.htm
- Flow Reference — Loop Element: https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_loop.htm
- Flow Reference — Collection Filter Element: https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_collectionfilter.htm
- Flow Reference — Collection Sort Element: https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_collectionsort.htm
- Flow Reference — Transform Element: https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_transform.htm
- Flow Builder: https://help.salesforce.com/s/articleView?id=sf.flow.htm&type=5
- Salesforce Well-Architected Framework: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
