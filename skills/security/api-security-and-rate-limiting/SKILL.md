---
name: api-security-and-rate-limiting
description: "Use when configuring, auditing, or troubleshooting API rate limits, Connected App OAuth scope restriction, Connected App IP restrictions, API session policies, or API usage monitoring in a Salesforce org. Trigger keywords: 'API rate limit', '429 error', 'OAuth scope restriction', 'Connected App IP restriction', 'API usage monitoring', 'concurrent API limits', 'Bulk API limits'. NOT for OAuth flow implementation, token exchange mechanics, or general Connected App setup — use security/oauth-flows-and-connected-apps for those."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "we are getting 429 errors from the Salesforce API and need to understand the limits and retry strategy"
  - "how do I restrict a Connected App so it can only call specific API scopes and not access all data"
  - "our integration is being rate limited — how do we monitor API usage and find which user or app is consuming the quota"
  - "how do I lock a Connected App to specific IP ranges so it cannot be used from untrusted networks"
  - "what is the difference between concurrent API request limits and daily API request limits in Salesforce"
  - "how do I configure API session timeout and IP locking for a Connected App"
tags:
  - api-security
  - rate-limiting
  - connected-app
  - oauth-scopes
  - ip-restrictions
  - api-monitoring
  - event-monitoring
  - concurrent-limits
inputs:
  - "Connected App name and type (standard integration, managed package, internal automation)"
  - "Current API consumers: named credentials, external credentials, integration users, or third-party apps"
  - "API types in use: REST, SOAP, Bulk API 1.0/2.0, Streaming/Platform Events, GraphQL, Tooling API"
  - "Org edition and any add-on licenses (Event Monitoring, Shield) that affect monitoring capabilities"
  - "Whether the org is experiencing 429 errors or unexplained API limit exhaustion"
outputs:
  - "Connected App scope restriction configuration guidance"
  - "IP restriction setup steps and policy selection rationale"
  - "API session policy configuration (timeout, IP locking)"
  - "API usage monitoring queries using Event Log Files or API Usage Insights"
  - "429 retry strategy pattern with exponential backoff"
  - "Decision table for per-user vs per-app rate limit management"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# API Security and Rate Limiting

Use this skill when the question is about protecting Salesforce API access through Connected App restrictions, managing API rate limits across different API types, monitoring API consumption by user or app, or handling 429 rate-limit responses in integrations. This skill covers the security controls that wrap API access — not the OAuth flow mechanics themselves.

For OAuth token exchange flows, refresh token lifecycle, or general Connected App creation, use `security/oauth-flows-and-connected-apps`.

---

## Before Starting

Gather this context before working on anything in this domain:

- Which API types are involved? REST, SOAP, Bulk API 1.0, Bulk API 2.0, Streaming API, Platform Events, GraphQL, Tooling API, and the Analytics REST API each have separate rate limit buckets. A fix for one bucket does not affect the others.
- What is the org edition? Developer Edition orgs have much lower daily API call limits than Enterprise or Unlimited Edition. Managed package allocations are additive for licensed packages.
- Is the org on Event Monitoring? Full API event log access requires the Event Monitoring add-on. Without it, only summary-level API usage insights are available in Setup.
- Is the issue concurrent request exhaustion or daily allocation exhaustion? These surface differently and have different remediation paths.

---

## Core Concepts

### API Rate Limits by Type

Salesforce enforces multiple distinct rate limit buckets. Confusing them is the most common source of misdirected remediation.

**Daily API request limits (org-wide):** The primary limit is a total number of API calls per 24-hour rolling window, calculated as a base allocation plus a per-user increment. For Enterprise Edition: 1,000 calls per Salesforce license per day, plus additional base allocation. For Unlimited Edition: 5,000 calls per license. The exact formula is documented in Salesforce Help under "API Request Limits and Allocations." These limits apply to REST, SOAP, and most other API families collectively — they share the same daily bucket. Bulk API, Streaming API, and Platform Events use separate counters (see below).

**Concurrent API request limits:** Separate from the daily limit. Salesforce enforces a ceiling on the number of REST or SOAP requests that are actively in-flight at the same time, per org. As of Spring '25, the concurrent limit for long-running requests (those taking more than 20 seconds) is 25 per org across all users and integrations. Short requests that complete in under 20 seconds do not count against the concurrent limit. Exceeding the concurrent limit produces an HTTP 503 or a `REQUEST_LIMIT_EXCEEDED` / `TXN_SECURITY_METERING_ERROR` SOAP fault, not necessarily a 429.

**Bulk API limits (separate bucket):** Bulk API 1.0 and Bulk API 2.0 have separate daily batch size limits measured in records processed, not request counts. Bulk API 2.0 processes up to 150 million records per rolling 24-hour period per org. Individual job batch size is capped at 150 MB or 100 MB depending on the operation type. Bulk API does not count against the REST/SOAP daily call limit.

**Streaming API / Platform Events:** Streaming API has limits on concurrent client subscriptions (1,000 per org on Enterprise Edition) and on event storage retention. Platform Events have daily allocation limits measured in event publishes per day, which are separate from API call limits.

**HTTP 429 vs. other limit responses:** A 429 response with a `Retry-After` header indicates the client exceeded the API request rate and should back off. A `REQUEST_LIMIT_EXCEEDED` error in a SOAP response indicates the daily limit was hit. These are different conditions requiring different responses.

### Connected App OAuth Scope Restriction

Every Connected App grants a set of OAuth scopes that define what the connected application can access when a user or service authorizes it. Overly broad scope grants are a significant security risk — if an integration credential is compromised, the attacker has whatever access the scopes allow.

**Scope restriction principle:** Grant the minimum scopes required for the integration's function. For a read-only data sync, grant `api` (which covers REST API access) but not `full` (which is equivalent to the user's full permissions). For background automation, grant `api` and `refresh_token` only. Never grant `full` to machine-to-machine integrations unless the integration genuinely needs it.

**Key scopes and their reach:**
- `api` — access REST API using the logged-in user's permissions. Does not grant higher privileges than the user has.
- `full` — same as `api` but also includes Chatter and some additional access. In many orgs `full` is functionally equivalent to `api` for pure data integrations but is broader than needed.
- `refresh_token` / `offline_access` — allows the connected app to obtain new access tokens without user re-authentication. Required for background/headless integrations. Carry a policy decision about how long refresh tokens remain valid.
- `web` — allows the app to use the access token to log the user in via the login portal. Not needed for pure API integrations.
- `id` — access the OpenID Connect `/id` endpoint. Needed for identity verification, not for data access.
- `visualforce` / `content` / `chatter_api` — narrow scopes for specific Salesforce features.

**Refresh token policy:** On the Connected App's OAuth policy settings, configure how long a refresh token remains valid. Options are: the token is valid until revoked, valid for a specific number of days, or expires after a defined period of inactivity. For high-security integrations, set an explicit expiry. For production integrations with no human re-auth path, coordinate the refresh token expiry with your incident response playbook.

### Connected App IP Restrictions

Connected App IP restrictions control which source IP addresses can use the app's credentials to call Salesforce APIs. This is a runtime enforcement mechanism — it does not prevent authentication, but it governs which network locations can successfully complete API calls after authenticating.

**Two levels of IP enforcement:**
1. **Enforce IP restrictions on connected app** — when enabled, the connected app only works from the IP ranges configured on the app itself. Requests from other IPs fail even if the OAuth token is valid. This is the stricter mode and is correct for integrations that always originate from a known set of servers.
2. **Relax IP restrictions for connected apps** — applies the org-level login IP ranges to the connected app but does not add app-specific restrictions. This is less strict than option 1 but still better than no restriction.

**OAuth Policies → IP Relaxation setting:** The IP restriction behavior is governed by the "IP Relaxation" policy on each Connected App:
- `Enforce login IP ranges on every request` — validates the user's IP against their profile login IP ranges on every API call, not just at login time.
- `Relax IP restrictions with second factor` — allows calls from outside the IP range if the user completed MFA. Appropriate for interactive apps; not for headless machine integrations.
- `Relax IP restrictions` — no IP validation after initial login. Avoid for system integrations.

**Important: refresh tokens bypass IP restrictions at token refresh time** — when a refresh token is used to obtain a new access token, the IP restriction check applies based on the policy at that moment. But the access token, once issued, may be usable from a different IP depending on the session policy. Audit this behavior in your org's session settings.

### API Session Policies

Session policies for API access are separate from browser session policies and are configured at the Connected App level and in org-wide Session Settings.

**Connected App session timeout:** Under the Connected App's OAuth Policies, the "Session Timeout" setting controls how long an API access token remains valid if not actively renewed. Options range from 15 minutes to 24 hours. For high-security integrations, use shorter timeouts and rely on the refresh token mechanism to re-issue access tokens frequently. For long-running batch processes, ensure the session timeout is longer than the longest expected batch run, or implement re-authentication logic.

**"Lock sessions to the IP address from which they originated":** This org-level session setting, in Setup → Session Settings, forces Salesforce to validate that each API request comes from the same IP address that created the session. For server-to-server integrations from static IPs, this is a strong security control. For integrations on dynamic IPs (cloud functions, distributed systems), this will cause session invalidation mid-operation.

**Require secure connections (HTTPS):** Ensure the org-level setting "Require Secure Connections (HTTPS)" is enabled. All API calls must use TLS. This is enforced by Salesforce for `.salesforce.com` endpoints by default, but verify it is not accidentally relaxed in session settings.

### API Usage Monitoring

**API Usage Insights (no add-on required):** Setup → Company Information includes total API call usage for the current 24-hour period. Setup → API Usage Metrics provides a graphical view of API calls by type over recent days. This is sufficient for spotting trend-level exhaustion but lacks per-user or per-app detail.

**Event Log Files (Event Monitoring add-on required):** Event Monitoring provides granular per-transaction logs. The relevant event types for API monitoring are:
- `API` — logs each REST API call with user, endpoint, method, response code, and execution time.
- `BulkAPI` — logs Bulk API job creation and completion events.
- `BulkApiRequest` — logs individual batch-level Bulk API requests.
- `ApexCallout` — logs outbound callouts made from Apex, not inbound API consumption.

Event Log Files are generated once per 24-hour period and retained for 30 days (1 day retention in Developer Edition). Query them via the REST API at `/services/data/vXX.0/query?q=SELECT+Id,+EventType,+LogDate+FROM+EventLogFile+WHERE+EventType='API'`.

**Platform Events and Pub/Sub API consumption:** Monitor delivery throughput and subscriber lag separately through the Event Monitoring `PlatformEventUsage` event type or through Setup → Platform Events usage metrics.

---

## Common Patterns

### Pattern 1: Restrict a Connected App to Minimum Scopes and Known IP Ranges

**When to use:** A new server-to-server integration is being deployed and needs to be locked down before going to production.

**How it works:**
1. In Setup → App Manager, open the Connected App and click Edit.
2. Under OAuth Settings, remove all scopes except those the integration explicitly needs (typically `api` and `refresh_token offline_access` for a headless integration). Remove `full`, `web`, `id`, and any others not required.
3. Under OAuth Policies → IP Relaxation, select "Enforce login IP ranges on every request."
4. If the integration originates from a fixed IP range, add those IPs to the Connected App's IP restrictions (separate from profile-level restrictions): navigate to the Connected App record → OAuth Policies → IP Ranges. Add each CIDR block.
5. Set Session Timeout on the Connected App to the shortest value compatible with the integration's operation (typically 2 hours for sync integrations, up to 8–24 hours for long-running batch jobs).
6. Save and test from both an authorized IP and an unauthorized IP to confirm restriction is enforced.

**Why not the alternative:** Leaving the default `full` scope and no IP restrictions means a compromised integration credential gives an attacker unrestricted API access from any location. Even if the credential is rotated, re-compromise is equally damaging.

### Pattern 2: Monitor API Consumption to Identify Limit-Exhausting Consumers

**When to use:** The org is hitting its daily API limit and it is not clear which user, app, or process is responsible.

**How it works:**
1. In Setup → API Usage Metrics, review the rolling trend. Identify the day and approximate hour when consumption spiked.
2. If Event Monitoring is enabled, query the API event log for that day:
   ```
   SELECT Id, EventType, LogDate
   FROM EventLogFile
   WHERE EventType = 'API' AND LogDate = YYYY-MM-DDT00:00:00.000Z
   ```
3. Download the CSV from the returned `LogFileUrl` and analyze by `USER_ID_DERIVED` and `URI` columns to identify which user and endpoint are generating the most calls.
4. If no Event Monitoring license, use SOQL against the `ApiEvent` object (where enabled) or review the ConnectedApplication usage through the `OauthToken` object to see which apps hold active tokens.
5. For Connected Apps specifically, review Setup → Connected Apps → OAuth Usage to see per-app token counts and last-used timestamps.

**Why not the alternative:** Guessing the source of limit exhaustion without data leads to throttling the wrong consumers or buying more API calls without addressing the root cause. Identification via event logs gives a defensible audit trail for remediation.

### Pattern 3: Implement 429-Safe Retry Logic

**When to use:** An integration is experiencing intermittent HTTP 429 responses under normal operating conditions.

**How it works:**
1. Capture the `Retry-After` response header on every 429. Salesforce sets this header to the number of seconds to wait before retrying.
2. Implement exponential backoff with jitter: if `Retry-After` is absent or you want to be conservative, start with a base delay (e.g., 1 second), double it on each successive 429, and add random jitter (±20%) to prevent thundering herd from multiple concurrent callers.
3. Set a maximum retry count (e.g., 5 retries) and a maximum total wait time. After the limit, fail the operation and emit an alert — do not loop indefinitely.
4. Log each 429 occurrence with the timestamp, endpoint, and retry attempt number. This data is essential for identifying patterns (e.g., load spikes at the top of the hour from a scheduled job).
5. For bulk import scenarios experiencing 429s, switch from parallel REST calls to Bulk API, which uses a separate allocation and is designed for high-volume data movement.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Integration credential is compromised | Revoke the Connected App's OAuth tokens immediately, then restrict scopes and IPs before re-issuing | Limiting scope reduces the damage window; restricting IPs limits future re-compromise surface |
| Org is hitting daily API limit | Use Event Monitoring to identify top consumers; optimize or throttle those callers; consider Bulk API for high-volume operations | Daily limits are shared; the highest-volume callers have the most impact |
| Getting 429 errors intermittently | Implement exponential backoff with `Retry-After` header respect; review whether load spikes can be flattened | 429 is recoverable; it means rate was exceeded momentarily, not that the daily limit is exhausted |
| Long-running batch integration failing mid-run | Increase Connected App session timeout to exceed the expected batch duration, or implement re-authentication at checkpoints | Default 2-hour session timeout terminates mid-job operations |
| Connected App used from multiple server regions | Use "Enforce login IP ranges on every request" with CIDR ranges covering all server regions; avoid "Relax IP restrictions" entirely for system integrations | Relaxed restrictions mean a stolen token is usable from anywhere |
| Need to audit which apps are making API calls | Query EventLogFile for EventType='API'; use Setup → Connected Apps → OAuth Usage for token-level visibility | Both complement each other; ELF is per-call, OAuth Usage is per-app aggregate |
| Bulk API and REST API both hitting limits | Investigate separately — Bulk API has its own daily record limit; REST has its own call count limit; they do not share a bucket | Treating them as one limit leads to wrong remediation |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. **Identify which limit type is being hit** — confirm whether the issue is daily call exhaustion (HTTP 200s stopping, `REQUEST_LIMIT_EXCEEDED` in SOAP), concurrent limit exhaustion (HTTP 503 or concurrent request errors), or momentary rate limiting (HTTP 429 with `Retry-After`).
2. **Identify the consumer** — use Setup → API Usage Metrics for summary data; use Event Monitoring Event Log Files for per-call detail. For Connected Apps, check OAuth Usage in Setup.
3. **Restrict Connected App scopes** — remove all OAuth scopes that the integration does not need. Document the minimum required set. Confirm with the integration owner.
4. **Apply IP restrictions** — for all server-to-server Connected Apps, configure app-level IP ranges and set IP Relaxation to "Enforce login IP ranges on every request." For dynamic-IP environments, evaluate profile-level IP restrictions or MFA-based relaxation.
5. **Configure session policy** — set Connected App session timeout to the shortest value compatible with the integration's run duration. Enable "Lock sessions to IP" if the integration always runs from a static IP.
6. **Implement retry logic** — ensure every API consumer respects `Retry-After` on 429 responses and implements bounded exponential backoff.
7. **Validate with monitoring** — after changes, observe API Usage Metrics for 48 hours to confirm consumption has normalized. Review Event Log Files for continued 429 or limit-exceeded errors.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Connected App scopes have been reviewed and trimmed to the minimum required set. `full` scope is not granted unless explicitly justified.
- [ ] IP restriction policy is set to "Enforce login IP ranges on every request" for all server-to-server integrations.
- [ ] Connected App session timeout is set and documented; confirmed to be compatible with the longest expected operation.
- [ ] Retry logic for 429 responses respects the `Retry-After` header and uses bounded exponential backoff.
- [ ] API usage monitoring is in place — either via Setup → API Usage Metrics (summary) or Event Monitoring Event Log Files (detailed).
- [ ] Bulk API usage has been assessed separately from REST/SOAP daily call limits.
- [ ] Refresh token expiry policy is configured and documented for each Connected App used in production.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Refresh tokens do not always respect IP restrictions at the point of re-auth** — when a refresh token is exchanged for a new access token, Salesforce evaluates the IP restriction policy of the Connected App at that moment. However, if the Connected App uses "Relax IP restrictions," the new access token can then be used from any IP for its duration. A compromised refresh token from a system not configured with strict IP policies can yield working access tokens from arbitrary locations.

2. **Bulk API has a separate daily record limit, not a request count limit** — the Bulk API daily limit is measured in total records processed, not in API calls. A single Bulk API job that processes 50 million records consumes a large fraction of the daily Bulk API allocation. REST API call counts and Bulk API record counts are separate — exhausting one does not affect the other, but they must be monitored independently.

3. **The concurrent API limit counts only requests in-flight for more than 20 seconds** — short-lived requests do not contribute to the concurrent limit regardless of how many are running simultaneously. Teams that optimize for short requests may be surprised when a long-running query or complex trigger-heavy operation suddenly causes concurrent limit errors, even at relatively low total request volume.

4. **429 and REQUEST_LIMIT_EXCEEDED are different conditions** — HTTP 429 means the rate at which requests are being sent exceeded the platform's throttle; it is recoverable by waiting. `REQUEST_LIMIT_EXCEEDED` in a SOAP/REST body typically means the daily org limit was fully exhausted; no amount of waiting in the same day will resolve it without requesting a temporary limit increase via Salesforce Support. Treating both as "retry with backoff" leads to retrying indefinitely when the daily limit is actually gone.

5. **Event Log Files are generated once per day and have a 1-day lag** — ELF data for API calls made today is not available until the next day's file generation. Real-time API call monitoring requires a third-party tool or the Pub/Sub API streaming approach. For incident response, this means you cannot use ELF to investigate a limit spike happening in the current hour.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Connected App scope restriction configuration | List of minimum required scopes per integration, with justification for each retained scope |
| IP restriction configuration | CIDR ranges per Connected App, IP relaxation policy selection, and justification |
| Session policy configuration | Session timeout setting per Connected App, IP locking decision |
| API usage monitoring query | Event Log File SOQL query for API event type, filtered by date and user, with column mapping |
| 429 retry strategy | Bounded exponential backoff pattern with `Retry-After` header handling |
| API limit incident runbook | Steps to identify, triage, and remediate a daily API limit exhaustion event |

---

## Related Skills

- `security/oauth-flows-and-connected-apps` — use when the question is about OAuth flow types, token exchange, refresh token mechanics, or Connected App creation rather than security restrictions on an existing app.
- `security/security-health-check` — use when auditing the org's overall security posture via the Health Check tool; session settings are also visible there.
- `integration/rest-api-patterns` — use when the question is about REST API integration design, request/response patterns, or error handling beyond rate limiting.
- `security/transaction-security-policies` — use when you need policy-based enforcement that can block or alert on specific API event patterns in real time.
