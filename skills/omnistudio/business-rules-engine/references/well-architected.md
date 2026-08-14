# Well-Architected Notes — Business Rules Engine

## Relevant Pillars

### Reliability

BRE reliability depends on activation state and attribute name alignment. A single deactivated version, a missing default row, or a case-mismatched input attribute name silently returns wrong results — not an error the platform surfaces proactively. Reliable BRE usage requires deterministic row evaluation (unique condition combinations), explicit fallback rows, and activation verification as a mandatory post-deploy step.

### Scalability

Decision Tables are synchronous and in-transaction. High-volume processes (batch Apex, bulk Integration Procedure calls) that evaluate BRE rules per record will consume Apex CPU limits proportionally. For batch reprocessing scenarios, evaluate whether the rule can be applied in a set-based pattern (compute the rule result once per unique input combination, then bulk-apply) rather than per-record.

### Operational Excellence

BRE is the primary vehicle for business-analyst-owned rule management in Industries orgs. The operational excellence value is that rule changes can be deployed without IT involvement — but this requires a clear governance model: who owns activation, how are versions reviewed, and how are rollbacks handled. Without explicit process discipline, BRE becomes a source of untracked production changes that are hard to audit.

---

## Architectural Tradeoffs

**BRE Decision Table vs. Calculation Matrix Lookup in Calculation Procedures:**
Both are lookup mechanisms but with different use cases. A Calculation Matrix is date-effective and version-selected automatically by timestamp — it is designed for rate tables that change on scheduled dates. A Decision Table uses explicit condition rows and operator-based matching — it is designed for eligibility rules with complex multi-attribute conditions. Do not replace one with the other: use Calculation Matrices for time-series rate data, use Decision Tables for eligibility logic.

**Expression Sets vs. Apex boolean logic:**
Expression Sets externalize boolean conditions that would otherwise live in Apex. The tradeoff is testability: Apex boolean logic is easily unit-testable in isolation with mocked inputs; Expression Sets require a connected org and an active version to test. For rules that change frequently and must be managed by business users, Expression Sets are the right choice. For rules that are stable, implementation-coupled, and require complex object traversal, Apex is more appropriate.

**Standard vs. advanced vs. CSV-based decision tables:**
The three types differ by two orders of magnitude on row capacity, and the choice is expensive to reverse — changing type means re-authoring the table and every lookup that calls it. Published default ceilings, `(fixed)` meaning Salesforce does not extend it:

| Dimension | Standard | Advanced | CSV-based |
|---|---|---|---|
| Processable rows | 100,000 | 20,000,000 | 1,000,000 (fixed) |
| Uploadable rows | — | — | 50,000 |
| Columns | 15 | 31 matched (fixed) + 10 unmatched | — |
| Input conditions | 30 | — | — |
| Output results / columns | 10 (fixed) | 10 (fixed) | — |
| Simultaneously active tables | 20 | 100 | — |
| Row grouping | 200 groups × 25,000 rows | 200 rows per Equals/Required/AND combination (fixed) | — |
| Output rows returned | 50 single-input, 200 multi-input (fixed) | 40,000 across simultaneous lookups | — |
| Full refreshes per hour | 40 (fixed) | 60 | — |
| Invocations per hour | 2,000,000 | 10,800,000 | — |

Advanced tables additionally cap at 5 source objects per table (fixed) and 1,000,000 rows per incremental refresh; CSV-based tables allow 5 simultaneous uploads and 5 downloads.

Size against these at design time. A table expected to pass 100,000 rows, 15 columns, or 30 input conditions starts as an advanced decision table rather than as a standard one migrated later. For CSV-based tables the binding constraint is the 50,000 uploadable rows, not the 1,000,000 processable rows — a bulk rate-table import fails on upload long before it reaches the processing ceiling. The partitioning guidance below is about auditability and blast radius, not about an absent platform limit.

**Single large Decision Table vs. multiple smaller tables:**
A single table with 500+ rows is harder to audit and slower to evaluate than multiple partitioned tables. Partition by a high-cardinality dimension (product line, region, or customer segment) and route to the appropriate table in the Integration Procedure using a Condition step. This keeps each table focused, auditable, and fast.

---

## Anti-Patterns

1. **Activating BRE versions manually in production without a documented process** — Informal manual activation creates untracked production changes. There is no standard audit log of who activated which version and when in the BRE UI. Use the Connect API for activation and log the API call in a deployment record. This creates a traceable, repeatable activation path.

2. **Using BRE Decision Tables for sequential calculation chains** — Decision Tables return a lookup result; they do not execute multi-step computations. Teams that try to express a multi-step pricing calculation as a sequence of Decision Table lookups (one table per step, passing outputs as inputs to the next) end up with brittle, hard-to-debug pipelines. Use Calculation Procedures (Expression Sets with Assignment and Aggregation steps) for sequential math.

3. **Ignoring the default/fallback row** — A Decision Table with no default row returns null for any unmatched input. Downstream IP or Apex code that does not null-check the result will throw a NullPointerException or silently propagate null into further processing. Always add a default row.

---

## Official Sources Used

- OmniStudio Developer Guide — Business Rules Engine section — https://developer.salesforce.com/docs/atlas.en-us.omnistudio_developer_guide.meta/omnistudio_developer_guide/omnistudio_intro.htm
- Salesforce Industries Developer Guide — Decision Tables and Expression Sets REST API — https://developer.salesforce.com/docs/atlas.en-us.industries_reference.meta/industries_reference/connect_resources_business_rules.htm
- Salesforce Help — Business Rules Engine Default Limits (expression set, decision matrix, and standard / advanced / CSV-based decision table ceilings) — https://help.salesforce.com/s/articleView?id=ind.business_rules_engine_default_limits.htm&language=en_US&type=5
- Salesforce Help — Permission Sets for Business Rules Engine (Rule Engine Runtime, Rule Engine Designer, Context Service, Decision Explainer) — https://help.salesforce.com/s/articleView?id=ind.bre_permission_sets.htm&language=en_US&type=5
- Salesforce Well-Architected Overview — architecture quality framing for reliability and operational excellence — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Integration Patterns — Integration Procedure callout architecture — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
