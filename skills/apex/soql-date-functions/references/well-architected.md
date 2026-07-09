# Well-Architected Notes — SOQL Date Functions

## Relevant Pillars

- **Performance** — the central win. A date function pushes period bucketing (year, quarter,
  month, day, hour) into the database, so a rollup returns one row per period instead of every
  matching record. That reduces query rows consumed, heap pressure, and Apex CPU versus reading
  all rows and grouping them in a loop. Grouping in SOQL also lets the platform apply selective
  filters before aggregating.
- **Operational Excellence** — `FISCAL_MONTH/QUARTER/YEAR` depend on an org-level setting:
  they are unsupported when custom (generic) fiscal years are enabled. A query can pass in one
  org and fail in another purely because of that configuration, so fiscal-function usage is a
  deployment-portability concern, not just a coding choice.
- **Reliability** — the two correctness traps (comparing a date-function result to a date
  literal, and using a date function in `SELECT` without a matching `GROUP BY`) fail at query
  compile time. Catching them before deploy — with the review checklist and the checker script
  — keeps them out of runtime.

## Architectural Tradeoffs

- **Group in the database vs. in Apex.** SOQL date-function grouping is far cheaper than
  Apex-side bucketing, but it returns `AggregateResult` (typed access by alias) and caps at the
  aggregate-query row limits. For very large or multi-dimensional rollups, weigh a reporting
  layer (reports, CRM Analytics) instead. See `apex/apex-aggregate-queries` for the mechanics
  and limits.
- **Fiscal function vs. fiscal formula field.** `FISCAL_*` is concise and follows the org's
  standard fiscal calendar, but it is unusable under custom fiscal years. A fiscal-period
  formula/roll-up field is more work to maintain but portable across fiscal configurations.
- **UTC bucketing vs. local-day accuracy.** Bucketing on the raw UTC instant is simplest and
  cheapest; wrapping the field in `convertTimezone()` makes buckets follow the user's local day
  at the cost of a per-row conversion. Choose based on whether "day" means calendar-UTC or
  user-local.

## Anti-Patterns

1. **Reading every row to bucket by period in Apex** — defeats the purpose of the functions;
   move the bucketing into `SELECT` + `GROUP BY` and read `AggregateResult`.
2. **Hard-coding fiscal boundaries to dodge FISCAL_\* portability** — instead, detect the
   fiscal configuration and fall back to calendar functions or a fiscal formula field.
3. **Ignoring time zone in DateTime rollups** — silently mis-buckets edge-of-day records; make
   the UTC-vs-local decision explicit with `convertTimezone()`.

## Official Sources Used

- SOQL and SOSL Reference — Date Functions — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_date_functions.htm
- SOQL and SOSL Reference — SELECT Functions (Aggregate, convertCurrency, convertTimezone, Date, FORMAT, GROUPING, toLabel) — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_functions.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
