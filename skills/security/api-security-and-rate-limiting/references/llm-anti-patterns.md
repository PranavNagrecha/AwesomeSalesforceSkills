# LLM Anti-Patterns — API Security and Rate Limiting

Common mistakes AI coding assistants make when generating or advising on API security and rate limiting in Salesforce.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Confusing Concurrent Request Limits with Daily Call Limits

**What the LLM generates:** When a user reports "we're hitting API limits," the LLM recommends reducing the total number of API calls per day or batching requests together, when the actual error is a concurrent limit error (requests taking more than 20 seconds running simultaneously).

**Why it happens:** LLMs conflate "API limits" as a single category because training data discusses daily limits far more frequently than concurrent limits. The concurrent limit is a distinct bucket with different triggers and remediation paths.

**Correct pattern:**

```
Diagnosis path:
1. Identify the error: HTTP 429 with Retry-After → rate throttle (momentary)
   HTTP 503 or SOAP REQUEST_LIMIT_EXCEEDED → either concurrent or daily exhaustion
   SOAP fault body containing "TXN_SECURITY_METERING_ERROR" or "CONCURRENT_REQUESTS_LIMIT_EXCEEDED" → concurrent limit

2. If concurrent limit:
   - Identify which requests are taking > 20 seconds (check Event Log TOTAL_TIME column)
   - Optimize slow queries, remove unnecessary triggers, or serialize long-running operations
   - Switch to Bulk API for high-volume DML that generates slow triggers

3. If daily limit:
   - Identify top consumers via Event Log Files
   - Optimize or throttle high-volume callers
   - Consider Bulk API for large record volumes
```

**Detection hint:** If the LLM recommends "reduce total API calls" for a concurrent limit error, or recommends "parallelize more" for a daily limit problem, it has conflated the two. Look for responses that do not specify which limit type is being addressed.

---

## Anti-Pattern 2: Recommending `full` OAuth Scope as the Default for Integrations

**What the LLM generates:** When scaffolding a Connected App configuration or integration setup, the LLM suggests selecting `full` scope "to ensure the integration has everything it needs" or "to avoid scope-related errors."

**Why it happens:** `full` scope is listed prominently in Salesforce OAuth documentation as the most permissive option, and LLMs trained on integration tutorials often see it used as a default to avoid debugging scope issues. The security implications are underweighted in typical integration setup examples.

**Correct pattern:**

```
Default Connected App OAuth scopes for headless server-to-server integration:
  api                         — REST API access bounded by user permissions
  refresh_token offline_access — background token refresh without user re-auth

Add only if specifically required:
  visualforce                 — only if integration calls Visualforce endpoints
  content                     — only if integration uses Salesforce Files/Content API
  chatter_api                 — only if integration posts to Chatter

Never grant:
  full                        — broader than api without justification
  web                         — not needed for API-only integrations
```

**Detection hint:** Any recommendation to use `full` scope for a server-to-server or automated integration without explicit justification is this anti-pattern.

---

## Anti-Pattern 3: Treating 429 and REQUEST_LIMIT_EXCEEDED as Identical Retry Scenarios

**What the LLM generates:** A retry handler that retries any non-200 response (or any 4xx response) with exponential backoff, applying the same strategy to both 429 (rate throttle) and `REQUEST_LIMIT_EXCEEDED` (daily limit exhausted).

**Why it happens:** Generic API resilience patterns (retry with backoff) are well-represented in training data and are broadly correct for transient errors. The Salesforce-specific distinction between momentary throttling and daily allocation exhaustion is not commonly surfaced in generic patterns.

**Correct pattern:**

```python
def handle_api_response(response):
    if response.status_code == 200:
        return response.json()

    if response.status_code == 429:
        # Transient rate limit — retry with Retry-After or exponential backoff
        retry_after = response.headers.get('Retry-After', '5')
        raise RetryableError(wait_seconds=float(retry_after))

    body = response.json()
    error_code = body[0].get('errorCode', '') if isinstance(body, list) else ''

    if error_code == 'REQUEST_LIMIT_EXCEEDED':
        # Daily limit exhausted — do NOT retry; alert and fail fast
        raise DailyLimitExhaustedError("Daily API limit exhausted; will not retry until reset")

    # Other errors: inspect individually
    raise ApiError(response.status_code, error_code)
```

**Detection hint:** A retry handler that catches all 4xx errors and applies exponential backoff without checking the error code in the response body is this anti-pattern.

---

## Anti-Pattern 4: Omitting IP Restrictions for Server-to-Server Connected Apps

**What the LLM generates:** When advising on Connected App security, the LLM configures OAuth scopes and session timeout but does not mention IP restrictions, or explicitly sets IP Relaxation to "Relax IP restrictions" because it "simplifies deployment."

**Why it happens:** IP restriction configuration is a separate setup step that requires knowledge of the integration's source IP infrastructure. LLMs often focus on the OAuth credential flow itself and treat the IP restriction as an optional or advanced configuration. Documentation examples frequently omit it for simplicity.

**Correct pattern:**

```
For all server-to-server Connected Apps:

1. Identify the source IP range(s) for the integration server(s)
   - Static data center IPs → configure explicit IP ranges on the Connected App
   - Dynamic IPs (cloud functions) → add a NAT gateway with a static IP, then configure that IP

2. Set IP Relaxation policy:
   - Machine integrations: "Enforce login IP ranges on every request"
   - User-facing apps where users travel: "Relax IP restrictions with second factor"
   - "Relax IP restrictions" (no restriction): only acceptable for development/scratch orgs

3. Verify by attempting an API call from an unauthorized IP after configuring
```

**Detection hint:** Any Connected App configuration recommendation that does not address IP Relaxation policy and IP ranges is incomplete for a production security context.

---

## Anti-Pattern 5: Recommending Event Log Files for Real-Time API Monitoring

**What the LLM generates:** When asked how to monitor API usage in real time (e.g., "alert me when API calls exceed 80% of daily quota"), the LLM recommends querying `EventLogFile` on a schedule or building a near-real-time dashboard from ELF data.

**Why it happens:** Event Log Files are the most detailed API usage data source in Salesforce and are prominently documented. LLMs do not reliably model the one-day lag between API call occurrence and ELF availability, treating ELF as if it provides current-day data.

**Correct pattern:**

```
Real-time or near-real-time API monitoring options:

1. Setup → API Usage Metrics (Setup UI only)
   - Shows current-day rolling call count
   - Available immediately; no add-on required
   - Granularity: total calls by API type; no per-user breakdown

2. Company Information → Daily API Requests (SOQL)
   SELECT DailyApiRequests, DailyApiRequestsUsed
   FROM Organization
   -- Returns current consumption vs. limit; queryable in real time

3. Event Log Files (Event Monitoring add-on)
   - Available the next day; covers the prior calendar day
   - Use for post-incident analysis and trend reporting
   - NOT for real-time alerting

4. Pub/Sub API / Salesforce Shield Event Streaming
   - Near-real-time event streaming for orgs with Shield
   - Appropriate for real-time SIEM integration
```

**Detection hint:** Any recommendation to use EventLogFile queries for same-day or real-time monitoring is this anti-pattern. Correct current-day consumption monitoring uses the `Organization` sObject's API usage fields or the Setup UI metrics page.

---

## Anti-Pattern 6: Assuming Connected App Session Timeout Is the Effective Timeout

**What the LLM generates:** Advises setting the Connected App session timeout to a specific value (e.g., "set to 24 hours for long-running jobs") without mentioning that the org-wide session setting may be shorter and will take precedence.

**Why it happens:** The Connected App session timeout is documented as a configuration option for the app, leading to the assumption that it directly controls session duration. The interaction with the org-wide session timeout is a platform-specific constraint not well surfaced in isolated Connected App documentation.

**Correct pattern:**

```
Effective session duration = MIN(Connected App session timeout, Org-wide session timeout)

Before configuring Connected App session timeout:
1. Check Setup → Session Settings → Timeout Value (org-wide)
2. Check Setup → Session Settings → Session Security Level Policies (may override per session type)
3. Set Connected App timeout no longer than the org-wide timeout
4. If the org-wide timeout is too short for the integration's needs:
   - Implement checkpoint-based re-authentication using refresh tokens
   - Do NOT simply raise the org-wide timeout to accommodate a single integration
```

**Detection hint:** A recommendation to set Connected App session timeout to X hours without verifying the org-wide session settings is this anti-pattern.
