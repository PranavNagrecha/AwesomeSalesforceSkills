# AppExchange App Analytics — Pull Plan Template

Use this template when activating App Analytics for a managed package or designing an
`AppAnalyticsQueryRequest` pull. All requests run in the License Management Org (LMO) the
package is registered to.

## Scope

**Skill:** `appexchange-app-analytics`

**Request summary:** (fill in what the user asked for)

## Context Gathered

- Package(s) + subscriber package ID(s) (`033…`):
- Packaging model: 1GP | 2GP
- Passed security review + registered to LMA? (both required):
- LMO login + integration user with CRUD/View All/Modify All on `AppAnalyticsQueryRequest`,
  Read on Packages/Package Versions:
- Data product(s) needed: PackageUsageLog | PackageUsageSummary | SubscriberSnapshot
- Activation status (logs/snapshots need it; summaries don't):
- Any Government Cloud subscribers? (their data is absent — exclude from reconciliation):

## Activation (2GP; skip if summaries only)

```bash
sf update && sf plugins update
sf package update --package "<Your Package Alias>" --enable-app-analytics
```

For 1GP, follow the activation steps in the 1GP Managed Packaging Developer Guide.

## Request Spec

Save as `app-analytics-request.json` and validate with the skill checker before submitting.

```json
{
  "attributes": { "type": "AppAnalyticsQueryRequest" },
  "DataType": "PackageUsageLog",
  "StartTime": "2026-07-04T00:00:00",
  "EndTime": "2026-07-05T00:00:00",
  "AvailableSince": null,
  "FileType": "csv",
  "FileCompression": "gzip",
  "PackageIds": "033xx0000000001",
  "OrganizationIds": null
}
```

Field rules (from the object reference):

- `DataType`: `PackageUsageLog` | `PackageUsageSummary` | `SubscriberSnapshot`
- A query must include `StartTime`, `AvailableSince`, or both; format `yyyy-MM-ddTHH:mm:ss` (UTC)
- `AvailableSince` filters by **data-lake arrival** time and must be later than
  `StartTime`/`EndTime` if those are set — use it as the incremental-pipeline watermark
- `FileType`: `csv` (default) | `parquet`; `FileCompression`: csv → `none`|`gzip`,
  parquet → `snappy`|`gzip`|`none`
- `PackageIds` / `OrganizationIds`: ≤16 comma-separated IDs, no spaces; blank = all

## Poll + Download

```sql
SELECT Id, RequestState, ErrorMessage, DownloadUrl, DownloadExpirationTime, DownloadSize
FROM AppAnalyticsQueryRequest
WHERE Id = '<request id>'
```

- Terminal states: `Complete` | `Failed` (read `ErrorMessage`) | `NoData` | `Expired`
- Download within **60 minutes** of completion; a missed window means a new request
- Add `DownloadSize` to the running 24-hour total (cap: **20 GB**)

## Schedule Design

- Daily logs/snapshots: pull after the 23:00 UTC next-day arrival guarantee
- Monthly summaries: pull ~2 days after month end
- Retention: logs/snapshots 45 days (land them in your own storage); summaries 10 years
- Keep pulls at least every 90 days — inactivity can stop collection (support case to resume)

## Checklist

- [ ] Eligibility confirmed (security review + LMA registration)
- [ ] Activation done if logs/snapshots are needed
- [ ] Request spec passes `scripts/check_appexchange_app_analytics.py`
- [ ] Poll handles `Failed`/`NoData`/`Expired`, not just `Complete`
- [ ] Download automated inside the 60-minute URL window
- [ ] 20 GB/24h budget and 45/90-day windows accounted for in the schedule

## Validation

```bash
python3 scripts/check_appexchange_app_analytics.py --manifest-dir <dir with request specs>
```

## Notes

(Record any deviations from the standard pattern and why — e.g. Parquet for warehouse
ingestion, per-org scoping to stay under the download cap.)
