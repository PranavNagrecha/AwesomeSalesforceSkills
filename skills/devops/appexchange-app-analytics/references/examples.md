# Examples — AppExchange App Analytics

All examples below are authored from the official 1GP/2GP Managed Packaging Developer Guides
and the `AppAnalyticsQueryRequest` object reference. Replace package aliases, `033` package
IDs, and org IDs with your own. All requests run in the **License Management Org (LMO)** the
package is registered to.

## Example 1: Activate App Analytics on a 2GP package

**Context:** your 2GP managed package passed security review and is registered to your LMA.
You need package usage logs and subscriber snapshots (monthly summaries already work without
activation).

**Problem:** without activation, `PackageUsageLog` and `SubscriberSnapshot` requests have no
data to return.

**Solution:**

```bash
# Keep the CLI and plug-ins current first
sf update
sf plugins update

# One-time activation, per package
sf package update --package "Your Package Alias" --enable-app-analytics

# To turn it back off later
sf package update --package "Your Package Alias" --no-enable-app-analytics
```

Then confirm the pulling user's permissions in the LMO: Create, Read, Edit, Delete, View All,
and Modify All on `AppAnalyticsQueryRequest`, plus Read on Packages and Package Versions.

**Why it works:** activation is per package and one-time; the permission set is what lets an
integration user create and poll the request records.

---

## Example 2: Pull one UTC day of package usage logs

**Context:** you want yesterday's detailed usage events for two packages, compressed to keep
the file small.

**Problem:** logs cover a 24-hour UTC window (12:00 AM–11:59 PM UTC) and regional data only
finishes arriving by 23:00 UTC the day after it was recorded — a misaligned or premature
window returns partial data.

**Solution:** create the request in the LMO via the SOAP API (`create()` is a supported call
on the object):

```text
AppAnalyticsQueryRequest
  DataType         = PackageUsageLog
  PackageIds       = 033xx0000000001,033xx0000000002   (≤16, comma-separated, no spaces)
  StartTime        = 2026-07-04T00:00:00                (UTC day boundary)
  EndTime          = 2026-07-05T00:00:00
  FileType         = csv                                (default)
  FileCompression  = gzip                               (csv allows: none | gzip)
```

Poll with a SOQL query (`query()` is a supported call):

```sql
SELECT Id, RequestState, ErrorMessage, DownloadUrl, DownloadExpirationTime, DownloadSize
FROM AppAnalyticsQueryRequest
WHERE Id = '<request id>'
```

When `RequestState` is `Complete`, download from `DownloadUrl` immediately — the URL expires
60 minutes after the request completes:

```bash
curl -L -o usage-logs-2026-07-04.csv.gz "<DownloadUrl>"
```

**Why it works:** the request scopes by package, uses aligned UTC boundaries, and is submitted
after the 23:00 UTC arrival guarantee for July 4 data. Handle the other terminal states
explicitly: `Failed` (read `ErrorMessage`), `NoData`, and `Expired`.

---

## Example 3: Incremental nightly pipeline with AvailableSince

**Context:** a warehouse pipeline that must never miss late-arriving regional data and never
double-count.

**Problem:** fixed `StartTime`/`EndTime` windows key off *event time*, but data *arrives* in
the lake region by region (EMEA first, then NA, then AP). A fixed window pulled too early
misses AP data; re-pulling the same window duplicates what you already loaded.

**Solution:** keep a watermark of the last successful pull and request by arrival time:

```text
AppAnalyticsQueryRequest
  DataType        = PackageUsageLog
  AvailableSince  = 2026-07-05T02:15:00     (last successful pull, UTC)
  FileType        = parquet
  FileCompression = snappy                   (parquet allows: snappy | gzip | none)
```

Per the object reference, "a query must include StartTime, AvailableSince, or both", and
`AvailableSince` limits the results file to data **newly arrived in the data lake** after the
specified date and time. If you combine it with `StartTime`/`EndTime`, `AvailableSince` must
be later than both.

After each `Complete` download, advance the watermark and record `DownloadSize` to track the
20 GB/24h budget.

**Why it works:** arrival-time watermarking makes the pipeline idempotent against regional
lag without re-downloading whole days.

---

## Example 4: Monthly adoption trend from usage summaries

**Context:** leadership wants month-over-month adoption per subscriber without standing up a
nightly pipeline.

**Problem:** usage logs are only retained 45 days, so they can't back-fill a yearly trend.

**Solution:** pull `PackageUsageSummary` (no activation needed, retained 10 years) a couple of
days after month end — summary timestamps are normalized to 00:00 UTC on the last day of the
month, and the docs recommend a ~2-day delay so all worldwide instances finish processing:

```text
AppAnalyticsQueryRequest
  DataType  = PackageUsageSummary
  StartTime = 2026-06-01T00:00:00
  EndTime   = 2026-07-01T00:00:00
  FileType  = csv
```

**Why it works:** summaries are the long-retention, low-volume product; the 2-day delay
avoids a partial final month.

---

## Anti-Pattern: joining user_id_token back to real users

**What practitioners do:** try to decode or match `user_id_token` in the usage-log CSV to
`User` records in a subscriber org to build per-person usage reports.

**What goes wrong:** the token is a hashed, pseudonymized identifier — in compliance with
privacy regulations Salesforce can't store an actual user ID, and tokens can't be linked back
to actual users. Any join you build is fictional.

**Correct approach:** analyze at the level the data supports — distinct token counts per org
(`organization_id`), `user_type` (Guest / Partner / Standard), `login_key` sessions, and
per-component `operation_type` / `operation_count` — and treat per-user identity as out of
scope by design.
