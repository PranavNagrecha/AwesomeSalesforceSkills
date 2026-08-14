# Well-Architected Notes — SOQL NULL Ordering Patterns

## Relevant Pillars

- **Reliability** — Pagination correctness depends on stable, deterministic ordering. ORDER BY without explicit NULLS handling and a unique tiebreaker is the most common cause of "missing records" or "duplicate records" tickets in batch processing.
- **Performance** — Sorting on a high-null-percentage field can full-scan even on a custom-indexed field. Knowing when the index covers nulls (it usually doesn't) determines whether a query is fast or slow under real data volumes.

## Architectural Tradeoffs

- **NULLS LAST vs. NULLS FIRST:** Match the user/consumer's mental model. For "show me records I should care about, then blanks," NULLS LAST. For "show me unknowns first so I can categorize them," NULLS FIRST. Always make the choice explicit.
- **OFFSET vs. cursor pagination:** OFFSET is simpler but caps at 2,000 records and breaks under concurrent writes. Cursor pagination is slightly more code but correct at any scale.
- **Sort-field index vs. data subset:** Indexing a high-null field for sort requires a Support request for null-inclusion. The alternative — partitioning the query into "non-null" and "null" passes — sometimes simpler and faster.

## Anti-Patterns

1. **Omitting NULLS clause** — Inherits the SOQL default that often surprises users. Always explicit.
2. **No unique tiebreaker** — Pagination correctness collapses on ties; the "missing records" report is downstream.
3. **OFFSET above ~500** — Caps at 2,000, expensive on the way there, breaks under concurrent writes. Cursor is the answer.

## Official Sources Used

- Apex Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
- Apex Reference Guide — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_ref_guide.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- SOQL ORDER BY Reference — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_orderby.htm
- SOQL OFFSET Reference — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_offset.htm
- **Spring '26 Release Notes (PDF), "Use Updated Empty Value Placement in List View Sorting"** — confirms that "When you sort a list view, blank fields, or null values, now are treated as the highest value in the dataset" where "Previously, Salesforce treated blank fields as the lowest value," and that the change "applies to Lightning Experience in all editions." Scoped to list views; it does not change the SOQL ORDER BY default, which the SOQL reference still gives as "By default, null values are sorted first." (verified 2026-08-13) — https://resources.docs.salesforce.com/rel1/doc/en-us/static/pdf/salesforce_spring26_release_notes.pdf
