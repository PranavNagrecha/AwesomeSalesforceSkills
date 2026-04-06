# Well-Architected Notes — Formula Field Performance and Limits

## Relevant Pillars

- **Performance** — Formula fields are the primary subject of this skill. Their non-indexable, on-read evaluation model creates measurable query performance degradation at scale. The Well-Architected Performance pillar requires practitioners to understand query plan behavior, index usage, and the cost of runtime evaluation per row. Materializing formula results into stored indexed fields is a direct application of performance-first schema design.

- **Scalability** — Problems that are invisible at 10,000 records become production-breaking at 1 million. The scalability pillar demands that schema and query designs account for realistic growth. Formula fields in WHERE clauses and cross-object spanning formulas both carry O(n) query costs that cannot be mitigated without schema changes.

- **Reliability** — SOQL queries that time out or produce inconsistent results because of formula-field evaluation failures undermine system reliability. The on-read model means a formula referencing a deleted parent record or a circular dependency can produce null or error results silently. Stored fields are deterministic and auditable.

- **Operational Excellence** — Formula fields that approach the compile-size limit, span many relationships, or are embedded in report filters create maintenance hazards that grow over time. The operationally excellent approach is to make calculated values explicit and observable through stored fields with Flow-managed sync, rather than hidden in formula expressions that no monitoring tool can track.

---

## Architectural Tradeoffs

### Formula Field (On-Read) vs. Stored Field (On-Write)

| Dimension | Formula Field | Stored Field |
|---|---|---|
| Storage cost | None — no database column value | Minimal — one column value per record |
| SOQL filter performance | Always full table scan | Indexable; selective queries possible |
| Automation complexity | None — self-updating | Requires Flow or trigger to stay in sync |
| Trigger/CDC visibility | Never fires | Fires normally on value change |
| Compile limits | 5,000 compiled chars, 10 spanning relationships | None |
| Display accuracy | Always current (recalculated on every read) | Depends on automation coverage |

The right choice depends on whether the value is used for filtering/sorting (favor stored field) or only for display (formula field is simpler and correct).

### Backfill Risk

Introducing a stored mirror field after data exists creates a mandatory backfill dependency. Skipping or delaying the backfill introduces a data correctness window where queries return wrong results. This is the highest-risk operational step in the materialization pattern.

---

## Anti-Patterns

1. **Filtering on a formula field in SOQL without measuring query plan impact** — Practitioners add formula fields to list view filters or Apex WHERE clauses without running the Query Plan Tool. The query works in a sandbox with 10,000 records and fails in production at 2 million. The detection check is cheap (one run of the Query Plan Tool); the production incident is not.

2. **Creating a stored field but relying on a single-path Flow that misses the Update path** — A Record-Triggered Flow is created to populate the stored field on Insert but not on Update (or vice versa). The stored field becomes stale for one entire class of DML operations. Queries against the stored field return stale or missing values. Always verify the Flow runs on both Create and Update (and on Record Update for the specific fields the formula depends on).

3. **Treating a helper formula field as a user-visible business field** — Intermediate formula fields created to work around the compile-size limit get added to page layouts and exposed to users. When the business logic changes, practitioners update the main formula but forget the helper, creating inconsistency. Helper fields should be hidden from layouts and documented as infrastructure-only in their field description.

---

## Official Sources Used

- Salesforce Help — Formula Field Limits and Considerations — https://help.salesforce.com/s/articleView?id=sf.formula_limits.htm
- Salesforce Help — Operators and Functions: Formula Size Limits — https://help.salesforce.com/s/articleView?id=sf.customize_functions.htm
- Apex Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
- Apex Reference Guide — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_ref_guide.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Help — Improve Report Performance with Large Data Volumes — https://help.salesforce.com/s/articleView?id=sf.reports_perf_large_data_volumes.htm
