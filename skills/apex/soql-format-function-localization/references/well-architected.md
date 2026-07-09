# Well-Architected Notes — SOQL FORMAT() Function (Localized Output)

## Relevant Pillars

- **Operational Excellence** — `FORMAT()` centralizes locale rendering in the query so exports,
  emailed reports, and API payloads match the Salesforce UI without a bespoke formatting layer
  per client. That single source of truth for display cuts drift: when the org's locale/currency
  settings change, the query output follows automatically. The tradeoff is that the output is
  observable only as a string, so keep the raw field available for anything the pipeline must
  compute or reconcile.
- **Reliability** — the biggest failure mode is a consumer that expects a typed value or a fixed
  format receiving a per-user, locale-variable string. Because output "reflect[s] the appropriate
  format for the given user locale," a query that renders `$44,000.00` for one user renders
  `44.000,00 €` for another. Use `FORMAT()` only where variability is acceptable (UI parity); for
  a stable contract, return the raw field and format explicitly downstream.
- **Security** — `FORMAT()` changes only presentation; it does not relax field-level security.
  The running user must still have read access to the underlying field, and the raw field should
  still be considered when enforcing CRUD/FLS. Do not assume a "formatted" column is somehow
  safer to expose than the value it renders.
- **Performance** — `FORMAT()` is a `SELECT`-clause presentation function, not a filter. Keep it
  out of `WHERE`/`ORDER BY`; a query must remain selective on the raw, indexed field, then format
  only the columns it returns.

## Architectural Tradeoffs

- **UI parity vs. contract stability.** Localized output is ideal for user-facing display and a
  liability for machine-to-machine contracts. Decide which side of that line the consumer is on
  before wrapping a field.
- **Query-side vs. Apex-side formatting.** `FORMAT()` is terse and locale-correct but offers no
  format mask; `Datetime.format('yyyy-MM-dd')` in Apex gives a fixed pattern at the cost of
  hand-rolled logic. Use the query function for locale parity, Apex for canonical formats.
- **Raw + formatted vs. formatted-only.** Returning both columns costs a little payload but keeps
  logic and display cleanly separated; formatted-only strands any consumer that needs the value.

## Anti-Patterns

1. **Filtering or sorting on formatted output** — putting `FORMAT()`/`convertCurrency()` in
   `WHERE`/`ORDER BY` compares locale strings and produces wrong, non-portable results; filter on
   the raw field.
2. **Treating the string as the value** — casting a `FORMAT()` column to a number/date and doing
   arithmetic or numeric sort on it; keep the raw field for computation.
3. **Formatted output as an integration contract** — relying on a per-user, locale-dependent
   string where a fixed format is required; format explicitly downstream instead.

## Official Sources Used

- FORMAT() (SOQL SELECT) — SOQL and SOSL Reference — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_format.htm
- FORMAT() (SOSL) — SOQL and SOSL Reference — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_sosl_format.htm
- convertCurrency() / Querying Currency Fields — SOQL and SOSL Reference — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_sosl_querying_currency_fields.htm
- Aggregate Functions — SOQL and SOSL Reference — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_agg_functions.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
