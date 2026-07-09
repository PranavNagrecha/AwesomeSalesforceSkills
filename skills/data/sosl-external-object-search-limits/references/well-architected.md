# Well-Architected Notes — SOSL External Object Search Results Limits

## Relevant Pillars

- **Reliability** — the defining risk here is *silent* failure. An external-object search returns no
  records (not an error) when search is disabled, when a sync resets the object's search flag, when the
  object has no searchable text field, or when the object is missing from `RETURNING`. Reliable behavior
  means treating "empty result" as a condition to diagnose against the four known silent causes, not as
  authoritative "no data."
- **Operational Excellence** — search enablement is not set-and-forget: syncing the external data source
  overwrites the external object's search status. Make "re-verify object search after each sync" part of
  the runbook, and enable search at the data-source layer so syncs preserve it.
- **Security / Privacy (secondary)** — SOSL still enforces the running user's field- and record-level
  access, and only text fields are searchable. Don't expose external fields in `RETURNING` that the user
  shouldn't see, and remember external objects surface data from an outside system — scope the searchable
  text fields deliberately.

## Architectural Tradeoffs

- **Search-in-platform vs search-at-source.** Enabling SOSL over an external object gives users a unified
  search box, but constrains you to text-field matching, a 100-character term, and no `LIKE`/`INCLUDES`.
  When richer matching is required, query the source system directly (or via a callout) instead of forcing
  it through SOSL.
- **Adapter choice shapes the query surface.** OData adapters forbid logical operators in FIND; custom
  adapters forbid `convertCurrency()` and generic `WITH`. The adapter decision (made in
  `integration/salesforce-connect-external-objects`) determines which SOSL workarounds you'll live with —
  weigh it when the external object is search-critical.
- **Client-side vs query-side logic.** Because translation (`toLabel`), conversion (`convertCurrency`), and
  category filtering (`WITH DATA CATEGORY`) are unavailable, that logic moves to Apex or the client. That's
  more code, but it keeps the external-object search valid instead of failing the whole statement.

## Anti-Patterns

1. **Treating an empty result as "no data."** For external objects, empty usually means a disabled search
   flag, a missing searchable field, or a missing `RETURNING` — investigate those before the adapter.
2. **Assuming object-level search enablement is durable.** A later data-source sync silently resets it;
   enable search at the data-source layer and re-verify after syncs.
3. **Porting standard-object SOSL verbatim.** `LIKE`, `INCLUDES`, `toLabel()`, logical operators in FIND,
   and long search strings are all valid on standard objects and invalid (or adapter-restricted) on
   external objects.

## Official Sources Used

- SOSL Limits on External Object Search Results (SOQL and SOSL Reference) — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_sosl_limits_external_objects.htm
- FIND {SearchQuery} (SOQL and SOSL Reference) — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_sosl_find.htm
