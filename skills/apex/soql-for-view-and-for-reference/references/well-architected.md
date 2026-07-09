# Well-Architected Notes — SOQL FOR VIEW and FOR REFERENCE

## Relevant Pillars

- **Security** — `FOR VIEW` / `FOR REFERENCE` turn a read into a write: they update
  `LastViewedDate` / `LastReferencedDate` and insert `RecentlyViewed` rows. A query that runs in
  system mode, or is not bounded to the records the running user can see, can stamp usage data on
  records the user has no visibility into, leaking a "this exists / was seen" signal into that
  user's Recent Items. Keep these queries in user mode (`WITH USER_MODE` / `AccessLevel.USER_MODE`)
  and scoped by Id so the write can only touch records the user is legitimately viewing.
- **Performance** — each clause adds DML side-effects to what would otherwise be a pure read
  (recency-field update plus a `RecentlyViewed` insert per row). Applied to a broad result set or
  placed inside a loop, that multiplies writes and burns DML against governor limits for no user
  benefit. Bound the query and keep the clause on the single by-Id fetch that backs the view.
- **Operational Excellence** — the whole point of the clauses is a good end-user experience:
  records the user actually opens appearing in Recent Items and search auto-complete. Misuse
  degrades exactly that experience by filling those surfaces with noise, so treat "does a real
  user view this?" as an operational quality gate, verified by opening the surface as a test user.
- **Reliability** — `RecentlyViewed` is deliberately ephemeral (retained 90 days, truncated to 200
  rows per object). Any feature that assumes recency data is durable will behave inconsistently
  over time; do not build reporting, compliance, or logic that depends on its persistence.

## Architectural Tradeoffs

- **Custom viewer vs. standard record page.** Standard Lightning record pages write recency for
  free. A custom LWC/Aura/Visualforce/mobile surface is the only case where you need these clauses
  at all — reach for a custom surface (and this skill) only when the standard page genuinely does
  not fit, then pay the small cost of opting into recency explicitly.
- **`FOR VIEW` vs. `FOR REFERENCE`.** `FOR VIEW` claims a full view (`LastViewedDate`, Recent
  Items); `FOR REFERENCE` claims a lighter reference (`LastReferencedDate`). Over-reporting a mere
  reference as a view inflates Recent Items; under-reporting a real view leaves records out of it.
  Match the clause to the actual interaction rather than defaulting to one.
- **Recency signal vs. durable log.** These clauses give a cheap, platform-native recency signal.
  If you need a permanent, queryable access history, that is a different concern — model your own
  object or use field history / event monitoring instead of leaning on `RecentlyViewed`.

## Anti-Patterns

1. **Read that silently writes in the wrong context** — placing the clause in batch, async,
   trigger, or integration-user code where no logged-in user is viewing the records. It corrupts
   usage data and adds DML; omit the clause entirely there.
2. **Unbounded recency stamping** — `SELECT ... FOR VIEW` with no `WHERE`/`LIMIT`, flooding Recent
   Items and search auto-complete. Always scope to the specific record(s) the user is viewing.
3. **Treating `RecentlyViewed` as an audit trail** — building reports or compliance on data that
   ages out at 90 days and truncates to 200 rows per object. Use a durable store for history.

## Official Sources Used

- FOR VIEW and FOR REFERENCE (SOQL and SOSL Reference) — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_for_view_for_reference.htm
- SELECT (SOQL and SOSL Reference) — statement grammar and clause ordering — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select.htm
- SOQL and SOSL Reference, Version 67.0 (Summer '26) — confirms the clauses are current, not deprecated — https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_soql_sosl.pdf
- Salesforce Help — "No Such Column LastViewedDate" on a custom object (custom tab required to enable the field) — https://help.salesforce.com/s/articleView?language=en_US&id=000315500&type=1
- Salesforce Well-Architected Overview — pillar framing — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
