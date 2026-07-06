---
name: appexchange-app-analytics
description: "Use when an ISV partner needs usage telemetry for an AppExchange managed package — activating AppExchange App Analytics on a 1GP/2GP package, submitting AppAnalyticsQueryRequest records from the License Management Org, and downloading package usage logs, monthly usage summaries, and subscriber snapshots as CSV/Parquet. Trigger keywords: App Analytics, AppAnalyticsQueryRequest, package usage logs, subscriber snapshot, LMA telemetry, feature adoption, churn risk. NOT for subscriber-org login/API auditing (use security/event-monitoring), NOT for CRM Analytics datasets or dashboards (use data/analytics-* skills), and NOT for license enforcement or Trialforce provisioning (use devops/isv-license-management-and-trialforce)."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "figure out which subscribers actually use the features in our managed package"
  - "download package usage logs for our AppExchange app from the LMA org"
  - "enable app analytics on our 2GP package before the next release"
  - "troubleshoot an AppAnalyticsQueryRequest that comes back Failed or NoData"
  - "measure feature adoption and churn risk across our subscriber orgs"
tags:
  - appexchange
  - app-analytics
  - appanalyticsqueryrequest
  - managed-package
  - isv
  - usage-telemetry
inputs:
  - "The managed package (1GP or 2GP) and its subscriber package ID(s) starting with 033"
  - "Access to the License Management Org (LMO) the package is registered to"
  - "Which data product is needed: package usage logs, monthly summaries, or subscriber snapshots"
  - "The date range or incremental window (StartTime/EndTime/AvailableSince) to pull"
outputs:
  - "Activation plan (CLI command, permissions) for App Analytics on the package"
  - "AppAnalyticsQueryRequest submission + polling + download workflow run from the LMO"
  - "Downloaded CSV/Parquet usage logs, monthly summaries, and subscriber snapshots"
  - "A pull schedule that respects retention windows, the 20 GB/24h cap, and data-lake timing"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-07-06
runtime_orphan: true
runtime_orphan_reason: "ISV/AppExchange package-usage analytics; no runtime agent owns ISV partner operations"
---

# AppExchange App Analytics

This skill activates when an ISV partner wants to know how subscribers actually use their AppExchange managed package — which components get touched, by how many users, in which orgs — and needs to activate AppExchange App Analytics and pull its data. The mechanism is the `AppAnalyticsQueryRequest` object, created in the License Management Org (LMO) that owns the package; results arrive as downloadable CSV (or Parquet) files.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Confirm eligibility.** App Analytics is available for first- and second-generation (1GP and 2GP) managed packages that **passed security review** and are **registered to a License Management App**. It is available in Enterprise, Performance, Unlimited, and Developer Editions.
- **Know which data needs activation.** Monthly package usage summaries are available by default. Package usage logs and subscriber snapshots require activating App Analytics on the package first.
- **Identify the LMO.** Requests are made using the `AppAnalyticsQueryRequest` object in the SOAP API **from the LMA org that owns the package** — not from the packaging org, the Dev Hub, or any subscriber org. Creating these records is the only way to download the log files.
- **Know the hard limits up front.** 20 GB of App Analytics data per 24-hour period; download URLs expire 60 minutes after the request completes; usage logs and subscriber snapshots are retained 45 days (summaries: 10 years).
- **Set the maturity expectation honestly.** The docs describe this as a standard partner feature but do not stamp a GA/Beta/Pilot label — don't assert one. Usage data from Government Cloud and Government Cloud Plus orgs is explicitly **not** available.

---

## Core Concepts

### Three data products, three cadences

| Data product | `DataType` value | Cadence | Activation needed? | Retention |
|---|---|---|---|---|
| Package usage logs | `PackageUsageLog` | Nightly (~05:00 instance local time, previous day's data, precise event timestamps) | Yes | 45 days |
| Package usage summaries | `PackageUsageSummary` | Monthly (timestamps normalized to 00:00 UTC on the last day of the month) | No — available by default | 10 years |
| Subscriber snapshots | `SubscriberSnapshot` | Nightly (collected ~01:00, generated ~03:00 instance local time; timestamps normalized to 00:00 UTC) | Yes | 45 days |

Usage logs track UI, API-based, Lightning-based, and Apex operations, and log each CRUD operation on packaged components and custom objects. Each log row carries the org context (`organization_id`, edition, type), a **pseudonymized** `user_id_token` (Salesforce can't store an actual user ID for privacy compliance), a `log_record_type` (e.g. `API`, `ApexExecution`, `LightningInteraction`, `LightningPageView`, `VisualforceRequest`), the packaged `custom_entity`, and an `operation_type` (`INSERT`, `READ`, `UPDATE`, `DELETE`, `SOQL_QUERY`, `SOSL_QUERY`) with an `operation_count`.

### Activation is per package, one command for 2GP

For a 2GP package, activation is a one-time Salesforce CLI command (keep the CLI current with `sf update` and `sf plugins update`):

```bash
sf package update --package "Your Package Alias" --enable-app-analytics
# to deactivate:
sf package update --package "Your Package Alias" --no-enable-app-analytics
```

For a 1GP package, the 1GP guide's activation steps apply — the docs frame it the same way ("Activate AppExchange App Analytics on your first-generation (1GP) managed package") but the mechanics live in the 1GP developer guide, not the CLI reference.

The user pulling data needs Create, Read, Edit, Delete, View All, and Modify All on the `AppAnalyticsQueryRequest` object, plus Read on Packages and Package Versions.

### The AppAnalyticsQueryRequest lifecycle

You create a record describing what you want; the platform processes it asynchronously; you poll and then download:

- **Scope:** `DataType` (restricted picklist), optional `PackageIds` (up to 16 comma-separated `033` subscriber package IDs, no spaces; blank = all registered packages) and `OrganizationIds` (up to 16 comma-separated org IDs; blank = all installation orgs).
- **Window:** `StartTime`/`EndTime` (`yyyy-MM-ddTHH:mm:ss`), and/or `AvailableSince` — "a query must include StartTime, AvailableSince, or both." `AvailableSince` limits results to data that **newly arrived in the data lake** after that instant and must be later than `StartTime` and `EndTime` if those are specified.
- **Format:** `FileType` `csv` (default) or `parquet`; `FileCompression` — for CSV `none` (default) or `gzip`; for Parquet `snappy` (default), `gzip`, or `none`.
- **State machine:** `RequestState` moves through `New`, `Pending`, then `Complete`, `Expired`, `Failed`, or `NoData` (with `ErrorMessage` populated on failure).
- **Delivery:** on completion `DownloadUrl` is populated and `DownloadExpirationTime` is set 60 minutes after completion; `DownloadSize` reports bytes.

Prior to Summer '20 the `DataType` values were `CustomObjectUsageLog` and `CustomObjectUsageSummary`; those legacy names work only with API v47.0 and earlier.

### Data-lake timing drives when you query

Usage data flows into a Salesforce data lake throughout the day, region by region: EMEA arrives first, then North America, then Asia Pacific. Ordinarily all org data arrives by **23:00 UTC the day after it was recorded** (occasional delays happen). Practical consequences:

- Query yesterday's logs only after the 23:00 UTC arrival window, or accept partial data.
- For monthly summaries, wait ~2 days after month end so all worldwide instances finish processing.
- Logs cover a 24-hour UTC window (12:00 AM–11:59 PM UTC); use aligned UTC day boundaries.

---

## Common Patterns

### Nightly incremental pull with AvailableSince

**When to use:** an automated pipeline that lands each day's usage logs into a warehouse without gaps or duplicates.

**How it works:** persist the timestamp of the last successful pull; each night create an `AppAnalyticsQueryRequest` with `DataType = PackageUsageLog` and `AvailableSince` set to that watermark, so you only receive data that arrived in the data lake since then. Poll `RequestState`, download within the 60-minute URL window, then advance the watermark.

**Why not the alternative:** re-pulling fixed `StartTime`/`EndTime` windows either misses late-arriving regional data or double-counts it, and repeated wide pulls burn the 20 GB/24h budget.

### Scoped pulls to stay under the 20 GB cap

**When to use:** a large install base where an unscoped pull risks the daily download cap or a `Failed`/oversized request.

**How it works:** split requests by `PackageIds` (up to 16 per request) and/or `OrganizationIds`, request `gzip` CSV or Parquet, and keep windows to one UTC day. Track `DownloadSize` per request to project your 24-hour total.

**Why not the alternative:** one giant uncompressed all-orgs pull can blow the 20 GB/24h limit and leaves no room to retry a failed download that day.

### Adoption and churn baseline: summaries + snapshots

**When to use:** roadmap or renewal conversations — which features are used, which subscribers are going quiet.

**How it works:** use monthly `PackageUsageSummary` pulls (no activation required, 10-year retention) as the long-term trend line, and nightly `SubscriberSnapshot` pulls for point-in-time subscriber activity. Join on the org identifier; falling active-user counts against a stable license count is the attrition signal the feature is designed to surface.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need month-over-month adoption trend only | `PackageUsageSummary` pulls | Available by default (no activation) and retained 10 years |
| Need per-event, per-component detail | Activate App Analytics, pull `PackageUsageLog` nightly | Logs need activation and are only retained 45 days — pull continuously |
| Need "who is going quiet" churn signal | `SubscriberSnapshot` nightly + summary trend | Snapshots are the point-in-time subscriber activity view |
| Automating a pipeline | `AvailableSince` watermark pattern | Only mechanism that tracks data-lake arrival instead of event time |
| Large install base / big files | Scope by `PackageIds`/`OrganizationIds`, `gzip` or Parquet | Stay under the 20 GB/24h download cap |
| Subscriber has Government Cloud orgs | Set expectations: that data is absent | Gov Cloud / Gov Cloud Plus usage data isn't available in App Analytics |
| Need subscriber-org security auditing | Not this feature — use Event Monitoring in the subscriber org | App Analytics is partner-facing package telemetry, pseudonymized by design |

---

## Recommended Workflow

1. **Verify eligibility and access** — the package passed security review, is registered to an LMA, and you can log in to the owning LMO with CRUD/View All/Modify All on `AppAnalyticsQueryRequest` plus Read on Packages and Package Versions.
2. **Activate if you need logs or snapshots** — for 2GP run `sf package update --package "<alias>" --enable-app-analytics` (summaries need no activation); for 1GP follow the 1GP guide's activation steps.
3. **Design the pull** — pick `DataType`, scope (`PackageIds`, `OrganizationIds`), window (`StartTime`/`EndTime` and/or `AvailableSince`), and format (`FileType`, `FileCompression`), respecting UTC day boundaries and the 23:00 UTC arrival guarantee.
4. **Create the request in the LMO** — insert the `AppAnalyticsQueryRequest` record via the SOAP API and record its Id.
5. **Poll and download promptly** — poll `RequestState` until `Complete` (handle `Failed` via `ErrorMessage`, and `NoData`/`Expired` explicitly); download from `DownloadUrl` **within 60 minutes** of completion.
6. **Operationalize** — schedule pulls inside the 45-day retention window for logs/snapshots, track cumulative `DownloadSize` against the 20 GB/24h cap, and keep pulling at least every 90 days — inactivity for 90 days can cause Salesforce to stop collecting your data (a Partner Community support case is needed to resume).

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Package passed security review and is registered to an LMA; requests run from the owning LMO
- [ ] App Analytics activated on the package if logs or snapshots are needed (summaries work without it)
- [ ] Every request includes `StartTime`, `AvailableSince`, or both; `AvailableSince` (if used) is later than `StartTime`/`EndTime`
- [ ] `PackageIds`/`OrganizationIds` lists are ≤16 entries, comma-separated, no spaces; package IDs start with `033`
- [ ] Polling handles all terminal states: `Complete`, `Failed` (read `ErrorMessage`), `NoData`, `Expired`
- [ ] Download automation fires within the 60-minute `DownloadUrl` window
- [ ] Pull cadence fits the 45-day log/snapshot retention, the 20 GB/24h cap, and the 90-day inactivity rule
- [ ] No claims that Gov Cloud data is included, and no GA/Beta label the docs don't state

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems (full list in `references/gotchas.md`):

1. **90 days of inactivity can silently stop data collection** — if you don't view/pull log or snapshot data for 90 days, collection may cease and only a support case via the Salesforce Partner Community resumes it. A "set it up and come back next quarter" plan loses data.
2. **The download URL is a 60-minute window** — `DownloadExpirationTime` is 60 minutes after completion. Poll-then-download must be one automated motion, not a human checking a queue later.
3. **Querying too early looks like missing data** — regional data lands EMEA → NA → AP and is only guaranteed complete by 23:00 UTC the *next* day; an early pull returns a plausible-looking but partial file, or `NoData`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Activation runbook | CLI command + permission checklist to turn on App Analytics for the package |
| `AppAnalyticsQueryRequest` request spec | Field-by-field request definition (see `templates/appexchange-app-analytics-template.md`) |
| Pull pipeline design | Watermark (`AvailableSince`) schedule with polling, download, and cap tracking |
| Downloaded datasets | CSV/Parquet usage logs, monthly summaries, subscriber snapshots for analysis |

---

## Related Skills

- `devops/isv-license-management-and-trialforce` — the LMA/LMO setup this skill depends on; license lifecycle and Trialforce provisioning.
- `devops/second-generation-managed-packages` — 2GP package creation and the `sf package` CLI surface the activation command belongs to.
- `devops/managed-package-development` — 1GP/2GP package design decisions that determine which components show up in usage logs.
- `security/event-monitoring` — the *subscriber-org* telemetry feature this one is commonly confused with; different audience, different API.
