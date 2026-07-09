# Well-Architected Notes — SOQL Aggregate Field-Type Support

## Relevant Pillars

- **Reliability** — this is the pillar this skill most directly serves. An aggregate function on an
  unsupported field type (`SUM()` on a date, `AVG()` on a picklist, any aggregate on a boolean) does
  not fail soft — the query errors and the whole request fails. Choosing a supported (field type ×
  function) pair up front turns a runtime failure into an authoring-time check. The multi-currency
  and null-handling nuances are correctness risks too: an ungrouped currency `SUM()` and a
  null-skipping `COUNT(field)` both return "successful" numbers that are quietly wrong.
- **Performance** — aggregate functions push summarization into the database, so the rows never
  materialize on the Apex heap. Reaching for the right function (a single `COUNT(Id)` instead of
  querying rows and counting in a loop, or `SUM()` in the database instead of iterating) is the
  efficient path — but only when the field type supports it, which is exactly what this skill
  confirms.
- **Security** — marginal here, but note that surfacing an aggregate over a currency field in a
  multi-currency org can leak an unexpected corporate-currency total to an audience that should only
  see their own currency; group and label deliberately.

## Architectural Tradeoffs

- **Aggregate in the database vs. compute in Apex.** Database aggregation is cheaper and
  heap-friendly, but it is constrained by the field-type matrix. When you need a summary the matrix
  doesn't allow (e.g. an "average" over a categorical field), the tradeoff is to derive a supported
  numeric field upstream rather than force an unsupported aggregate.
- **Ungrouped simplicity vs. multi-currency correctness.** A bare `SUM(Amount)` is simplest and, in
  a single-currency org, correct. In a multi-currency org, correctness requires `GROUP BY
  CurrencyIsoCode` (more rows, more handling) to avoid a misleading corporate-currency blend.
- **COUNT(Id) vs. COUNT(field).** Counting all rows is unambiguous; counting a specific field is
  more informative (populated / distinct) but silently null-sensitive. Pick the one whose null
  semantics match the metric you're reporting.

## Anti-Patterns

1. **Forcing an unsupported aggregate instead of modeling a supported field** — e.g. hammering
   `AVG()` at a picklist. Derive a genuine numeric field (or number-returning formula) and aggregate
   that; don't fight the matrix.
2. **Ungrouped currency aggregates in multi-currency orgs** — a single `SUM(Amount)` presented as
   "the total" hides the corporate-currency conversion. Group by `CurrencyIsoCode`.
3. **Using COUNT(field) as a row count** — relying on a null-skipping count for "how many records"
   understates the total with no error to catch it. Use `COUNT(Id)` for totals.

## Official Sources Used

- SOQL and SOSL Reference — Support for Field Types in Aggregate Functions — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_agg_functions_field_types.htm
- SOQL and SOSL Reference — Aggregate Functions — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_agg_functions.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
