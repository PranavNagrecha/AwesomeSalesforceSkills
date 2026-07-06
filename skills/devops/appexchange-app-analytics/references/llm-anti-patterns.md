# LLM Anti-Patterns — AppExchange App Analytics

Common mistakes AI coding assistants make when generating or advising on AppExchange App
Analytics. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Running the request from the wrong org

**What the LLM generates:** Apex or API calls that create `AppAnalyticsQueryRequest` records
in the packaging org, the Dev Hub, or — worst — a subscriber org, sometimes wrapped in advice
to "query usage in the customer's org."

**Why it happens:** most Salesforce telemetry examples in training data (Event Monitoring,
debug logs) run inside the org being measured, so the model defaults to that topology.

**Correct pattern:**

```text
Log in to the License Management Org (LMO) the package is registered to,
and create AppAnalyticsQueryRequest there via the SOAP API.
```

**Detection hint:** any mention of running the request in a "subscriber org", "customer org",
"packaging org", or "Dev Hub" — App Analytics is partner-side, LMO-only.

---

## Anti-Pattern 2: Inventing a REST endpoint or Setup dashboard

**What the LLM generates:** a fictional `GET /services/data/vXX.X/app-analytics` endpoint, an
"App Analytics dashboard in Setup," or an AppExchange console download button for usage logs.

**Why it happens:** most modern Salesforce data products expose REST APIs or Setup UIs, so
the model pattern-fills one.

**Correct pattern:** the only way to download App Analytics logs is by creating
`AppAnalyticsQueryRequest` records (create/query are supported SOAP API calls), polling
`RequestState`, and fetching the time-limited `DownloadUrl`.

**Detection hint:** any REST URL path or Setup navigation instruction for retrieving App
Analytics data.

---

## Anti-Pattern 3: Wrong or legacy DataType values

**What the LLM generates:** `DataType = 'UsageLog'`, `'CustomObjectUsageLog'`, or
`'PackageUsageLogs'` (plural).

**Why it happens:** the pre-Summer '20 names (`CustomObjectUsageLog`,
`CustomObjectUsageSummary`) linger in older blog posts and training data, and the model
guesses plausible variants.

**Correct pattern:**

```text
DataType ∈ { PackageUsageLog, PackageUsageSummary, SubscriberSnapshot }
```

The legacy names work only with API v47.0 and earlier.

**Detection hint:** grep for `CustomObjectUsage` or any `DataType` value outside the three
current picklist values.

---

## Anti-Pattern 4: Time-window fields that violate the documented rules

**What the LLM generates:** a request with neither `StartTime` nor `AvailableSince`; or
`AvailableSince` set *before* the `StartTime`/`EndTime` window "to be safe"; or local-time
timestamps.

**Why it happens:** generic date-range API patterns don't have the arrival-time vs
event-time distinction, so the model treats `AvailableSince` as just another start date.

**Correct pattern:** "a query must include StartTime, AvailableSince, or both";
`AvailableSince` must be **later** than `StartTime` and `EndTime` if they're specified, is
transmitted in UTC, and filters by data-lake **arrival** time, not event time. Format:
`yyyy-MM-ddTHH:mm:ss`.

**Detection hint:** a request spec missing both `StartTime` and `AvailableSince`, or an
`AvailableSince` ≤ `EndTime`.

---

## Anti-Pattern 5: Treating pseudonymized tokens as user IDs

**What the LLM generates:** SOQL or warehouse joins mapping `user_id_token` to `User.Id`,
or claims that App Analytics reports "which users" clicked a feature by name.

**Why it happens:** the column name pattern (`user_id_*`) matches real-ID columns in most
schemas the model has seen.

**Correct pattern:** `user_id_token` is a hashed token; in compliance with privacy
regulations Salesforce can't store an actual user ID and tokens can't be linked back to
actual users. Aggregate by org, `user_type`, and session (`login_key`) instead.

**Detection hint:** any join between App Analytics output and the `User` object, or
per-named-user reporting claims.

---

## Anti-Pattern 6: Ignoring the operational limits or asserting a maturity label

**What the LLM generates:** "download all history whenever you need it" pipelines with no cap
handling, links emailed for later download, claims that the data covers all clouds, or a
confident "App Analytics is GA since Winter '21."

**Why it happens:** models default to optimistic, limit-free API descriptions and pattern-fill
GA/Beta labels.

**Correct pattern:** design around the documented constraints — 20 GB of data per 24-hour
period, `DownloadUrl` expiry 60 minutes after completion, 45-day retention for
logs/snapshots (10 years for summaries), 90-day inactivity risk to collection, no Government
Cloud / Government Cloud Plus data — and do not state a GA/Beta/Pilot status the docs don't
give.

**Detection hint:** absence of the 20 GB / 60-minute / 45-day numbers in any pipeline design,
or any unsourced maturity label.
