# Well-Architected Notes — AppExchange App Analytics

## Relevant Pillars

- **Security** — access to `AppAnalyticsQueryRequest` requires full CRUD plus View All and
  Modify All on the object, and Read on Packages / Package Versions; grant it to a dedicated
  integration user in the LMO, not broadly. The data itself is privacy-engineered:
  `user_id_token` is a hashed pseudonym that can't be linked back to a real user — don't try
  to re-identify, and don't promise customers per-person reporting. Treat `DownloadUrl`
  values as short-lived secrets (they grant unauthenticated file access until expiry).
- **Operational Excellence** — this is an always-on pipeline, not an ad-hoc report: pulls
  must recur inside the 45-day log/snapshot retention window and at least every 90 days or
  collection itself can stop. Monitor terminal `RequestState` values (`Failed`, `NoData`,
  `Expired`) and alert on them rather than assuming `Complete`.
- **Reliability** — data arrives in the lake region by region (EMEA → NA → AP) with a
  23:00-UTC-next-day guarantee and occasional delays. Watermark on `AvailableSince` so late
  arrivals are picked up by the next run instead of lost, and delay monthly-summary pulls
  ~2 days past month end.
- **Performance** — the 20 GB/24h download cap is the binding constraint at scale. Scope
  requests with `PackageIds`/`OrganizationIds` (≤16 each), compress (`gzip` CSV or `snappy`
  Parquet), and track cumulative `DownloadSize` so a retry never blows the day's budget.

## Architectural Tradeoffs

- **Summaries vs logs.** Monthly summaries need no activation and last 10 years but are
  coarse; usage logs are per-event but need activation, continuous pulling, and your own
  storage. Most partners need both: summaries for trend, logs for feature-level answers.
- **Fixed windows vs arrival watermark.** `StartTime`/`EndTime` windows are easy to reason
  about but race regional arrival; `AvailableSince` is idempotent against lag but yields
  files whose event times straddle days — your warehouse layer must dedupe/partition by
  event timestamp.
- **Pull everything vs scoped pulls.** Unscoped requests are simpler but risk the 20 GB cap
  and giant files; per-package/per-org scoping costs more requests but fails smaller and
  retries cheaper.

## Anti-Patterns

1. **On-demand analytics** — activating App Analytics and only pulling when someone asks.
   The 45-day retention and 90-day inactivity rule make this a data-loss design; run it as a
   scheduled pipeline or don't run it at all.
2. **Human-mediated downloads** — routing `DownloadUrl` links through email or a ticket
   queue. The 60-minute expiry guarantees dead links; downloads must be automated in the
   same job that polls.
3. **Re-identification analytics** — building "which named user did what" reports from
   `user_id_token`. It's cryptographically pointless and contradicts the privacy posture the
   feature ships with; design KPIs around orgs, sessions, and user types.

## Official Sources Used

- Get Started with AppExchange App Analytics (2GP Managed Packaging Developer Guide) — https://developer.salesforce.com/docs/atlas.en-us.pkg2_dev.meta/pkg2_dev/app_analytics_intro_2gp.htm
- Get Started with AppExchange App Analytics (1GP Managed Packaging Developer Guide) — https://developer.salesforce.com/docs/atlas.en-us.pkg1_dev.meta/pkg1_dev/app_analytics_intro_1gp.htm
- Activate AppExchange App Analytics (Packaging Guide) — https://developer.salesforce.com/docs/atlas.en-us.packagingGuide.meta/packagingGuide/app_analytics_request_access.htm
- AppExchange App Analytics Data Flow (2GP Managed Packaging Developer Guide) — https://developer.salesforce.com/docs/atlas.en-us.pkg2_dev.meta/pkg2_dev/app_analytics_data_flow.htm
- Download Package Usage Logs, Package Usage Summaries, and Subscriber Snapshots (2GP Managed Packaging Developer Guide) — https://developer.salesforce.com/docs/atlas.en-us.pkg2_dev.meta/pkg2_dev/app_analytics_download_mp_logs.htm
- AppAnalyticsQueryRequest (Object Reference for the Salesforce Platform) — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_appanalyticsqueryrequest.htm
- Package Usage Logs Schema (2GP Managed Packaging Developer Guide) — https://developer.salesforce.com/docs/atlas.en-us.pkg2_dev.meta/pkg2_dev/app_analytics_custom_object_logs.htm
