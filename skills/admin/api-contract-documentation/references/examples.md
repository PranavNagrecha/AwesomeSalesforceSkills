# Examples — API Contract Documentation

Two narrative walkthroughs. For the artefacts themselves — a filled contract record, an OpenAPI excerpt, a contract test, a deprecation notice — see `worked-examples.md`.

## Example 1: Versioning Policy Documentation for a Salesforce Integration

**Context:** An enterprise team inherited a Salesforce integration using API version v46.0, which was first released in Spring '19. They needed to assess the retirement risk.

**Problem:** The team had no documentation about the versioning policy and no alerting when versions approached end-of-life. They were using a version that was already approaching the retirement window.

**Solution:**
1. Called `GET /services/data/` to enumerate all live API versions and confirmed v46.0 was still listed but near the 3-year threshold.
2. Documented the official policy: 3-year support window, 1-year advance notice before retirement.
3. Checked the Salesforce API EOL page (`api_rest/api_rest_eol.htm`) for the specific retirement date.
4. Created a ticket to upgrade the integration to v60.0, with a timeline to complete before the announced retirement.
5. Added a quarterly calendar reminder to check the EOL page with each Salesforce seasonal release.

**Why it works:** `GET /services/data/` provides a live enumeration of supported versions. Cross-referencing with the EOL policy page gives a definitive retirement timeline.

**The call, and what it returns.** This request needs no authentication and does not count toward the org's API limit, so it can run from a monitor that holds no credentials:

```bash
curl https://MyDomainName.my.salesforce.com/services/data/
```

```json
[
  { "label": "Spring '11", "url": "/services/data/v21.0", "version": "21.0" },
  { "label": "Winter '26", "url": "/services/data/v65.0", "version": "65.0" },
  { "label": "Spring '26", "url": "/services/data/v66.0", "version": "66.0" }
]
```

The check the team automated is one line of logic over that array: **if the pinned version is absent, the integration is already broken** and every call is returning `410 GONE`. If it is present but sits in the lowest quartile of the returned range, it is inside the window where a `Warning: 299` header may already be arriving on every response.

---

## Example 2: Rate Limit Monitoring for a High-Volume Integration

**Context:** A nightly batch integration was periodically failing with HTTP 403 errors during peak processing windows. The team suspected API limit exhaustion.

**Problem:** The team had no monitoring of the daily API request limit. They were unaware of how many API calls were being consumed or how close they were to exhaustion.

**Solution:**
1. Called `GET /services/data/v60.0/limits` to retrieve `DailyApiRequests.Max` (the actual org limit).
2. Added logging to capture the `Sforce-Limit-Info: api-usage=X/Y` header from each API response.
3. Confirmed that at peak the integration was consuming 85% of the daily limit before the batch completed.
4. Refactored the batch to use Bulk API 2.0 for high-volume operations (Bulk API has a separate request budget).
5. Added an alert: if `X/Y > 80%`, send a PagerDuty notification.

**Why it works:** The `Sforce-Limit-Info` header is present on every REST API response. Logging it provides a continuous view of API consumption. HTTP 403 `REQUEST_LIMIT_EXCEEDED` means the 24-hour window is exhausted — not the same as transient throttling.

**The two signals, side by side.** The `/limits` resource gives the ceiling; the response header gives the running total. Document both, because the header alone cannot tell a partner whether a 403 is allocation exhaustion or the concurrency cap.

```bash
curl https://MyDomainName.my.salesforce.com/services/data/v62.0/limits \
  -H "Authorization: Bearer <token>"
```

```json
{
  "DailyApiRequests":   { "Max": 245000, "Remaining": 38412 },
  "DailyBulkApiBatches": { "Max": 15000, "Remaining": 14988 },
  "ConcurrentAsyncGetReportInstances": { "Max": 200, "Remaining": 200 }
}
```

> The numbers above are an illustration of the response *shape*, not a limit for any org. `DailyApiRequests.Max` is computed from edition, licence count and purchased add-ons — read it, never assume it.

The corresponding per-response log record, which is what actually caught the 85% peak:

| Timestamp (UTC) | Endpoint | Status | `Sforce-Limit-Info` | Used % |
|---|---|---|---|---|
| 2026-08-14T02:04:11Z | `/sobjects/Order` | 201 | `api-usage=181004/245000; api-bursts=0/750` | 73.9% |
| 2026-08-14T02:47:52Z | `/sobjects/Order` | 201 | `api-usage=208119/245000; api-bursts=0/750` | 84.9% |
| 2026-08-14T03:12:07Z | `/sobjects/Order` | 403 | `api-usage=208140/245000; api-bursts=1/750` | 85.0% |

The third row is the one that settled the diagnosis: `api-usage` is at 85%, not at the ceiling, so the 403 was **not** allocation exhaustion — it was the concurrent long-running request cap (`references/gotchas.md` § 4). Waiting for the 24-hour window, which is what the team had been doing, would never have fixed it. Reducing parallelism did.
