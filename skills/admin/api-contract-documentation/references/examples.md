# Examples — API Contract Documentation

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

**Why it works:** The `Sforce-Limit-Info` header is present on every REST API response. Logging it provides a continuous view of API consumption. HTTP 403 `REQUEST_LIMIT_EXCEEDED` means the 24-hour window is exhausted — not the same as transient throttling (HTTP 429).
