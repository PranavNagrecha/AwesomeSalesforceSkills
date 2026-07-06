# Gotchas — AppExchange App Analytics

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: 90 days of inactivity can stop data collection

**What happens:** you activated App Analytics months ago, come back to build a dashboard, and
recent log/snapshot data simply doesn't exist.

**When it occurs:** requests to view package usage log or subscriber snapshot data are
inactive for 90 days — Salesforce may cease collecting the data. Resuming requires a support
case via the Salesforce Partner Community.

**How to avoid:** schedule pulls (even small ones) well inside the 90-day window; treat the
pipeline as always-on, not on-demand.

---

## Gotcha 2: The download URL expires 60 minutes after completion

**What happens:** a request shows `Complete` but the file 404s when someone finally clicks
the link.

**When it occurs:** `DownloadExpirationTime` is set 60 minutes after the query completes.
Any human-in-the-loop step (email a link, check tomorrow) misses the window.

**How to avoid:** make poll-then-download a single automated motion; if the window is missed,
create a new request rather than retrying the stale URL.

---

## Gotcha 3: Querying too early returns partial data or NoData

**What happens:** yesterday's pull looks fine for European subscribers but is missing US and
APAC activity — or the whole request comes back `NoData`.

**When it occurs:** usage data arrives in the data lake region by region (EMEA, then NA, then
AP) and is ordinarily only complete by 23:00 UTC the day *after* it was recorded; occasional
delays push that later. Monthly summaries similarly need ~2 days after month end.

**How to avoid:** schedule daily pulls after the arrival guarantee, or use the
`AvailableSince` watermark pattern so late-arriving data is picked up by the next run instead
of silently lost.

---

## Gotcha 4: Logs and snapshots age out at 45 days

**What happens:** a quarterly analysis project discovers it can only reconstruct the last six
weeks of detail.

**When it occurs:** package usage logs and subscriber snapshots are retained 45 days; only
monthly package usage summaries are retained 10 years.

**How to avoid:** continuously land logs/snapshots in your own storage; use summaries for
anything with a longer horizon.

---

## Gotcha 5: Government Cloud subscribers are invisible

**What happens:** active-org counts from App Analytics don't reconcile with your LMA license
records.

**When it occurs:** usage data from Government Cloud and Government Cloud Plus orgs isn't
available in App Analytics — those subscribers exist in the LMA but never appear in the
telemetry.

**How to avoid:** flag Gov Cloud installs in your license data and exclude them from
adoption/churn math instead of chasing a phantom data bug.

---

## Gotcha 6: Legacy DataType names only work on old API versions

**What happens:** a request using `CustomObjectUsageLog` or `CustomObjectUsageSummary` is
rejected as an invalid picklist value.

**When it occurs:** those pre-Summer '20 names work only with API version 47.0 and earlier;
current API versions require `PackageUsageLog`, `PackageUsageSummary`, or
`SubscriberSnapshot`.

**How to avoid:** use the modern values everywhere and pin your integration to a current API
version; treat any `CustomObject*` value in code as legacy debt to migrate.
