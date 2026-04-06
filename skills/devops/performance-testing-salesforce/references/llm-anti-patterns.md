# LLM Anti-Patterns — Performance Testing Salesforce

Common mistakes AI coding assistants make when generating or advising on Salesforce performance testing.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Developer Sandbox for Load Testing

**What the LLM generates:** "Spin up a Developer sandbox and run your JMeter load tests there to validate performance before deploying to production."

**Why it happens:** LLMs default to the simplest sandbox type because Developer sandboxes appear most frequently in Salesforce tutorials and getting-started guides. The training data rarely distinguishes sandbox types by data volume fidelity.

**Correct pattern:**

```text
Performance testing requires a Full Copy sandbox to ensure production-representative
data volume, sharing rule calculations, and custom index availability. Developer and
Developer Pro sandboxes (200 MB storage limit) produce misleading performance results.
```

**Detection hint:** Any recommendation that pairs "Developer sandbox" or "Developer Pro sandbox" with "load test," "performance test," or "benchmark" without explicitly calling out the data volume limitation.

---

## Anti-Pattern 2: Treating the Concurrent API Limit as a Hard Per-Request Cap

**What the LLM generates:** "Salesforce allows only 25 concurrent API requests. You must implement a request queue to ensure you never exceed 25 simultaneous calls."

**Why it happens:** The LLM reads the concurrent limit documentation but misses the 20-second qualification. It conflates the concurrent long-running request limit with a general connection limit.

**Correct pattern:**

```text
The concurrent API request limit (25 for most editions) applies only to requests
that have been running for more than 20 seconds. Short-lived API calls (under 20s)
are constrained by the daily total API request limit, not the concurrency limit.
Only implement concurrency throttling for long-running operations like complex
report exports or Bulk API jobs.
```

**Detection hint:** Any mention of "25 concurrent" or "concurrent API limit" without the "20 seconds" or "long-running" qualification.

---

## Anti-Pattern 3: Hardcoding Credentials in Load Test Scripts

**What the LLM generates:** "Set the username and password in your JMeter test plan: `sf.username=admin@myorg.com` and `sf.password=MyP@ssw0rd+SecurityToken`."

**Why it happens:** LLMs generate the simplest authentication pattern. Username-password with security token is the most common example in legacy Salesforce integration tutorials. Load test examples in training data often use hardcoded credentials for brevity.

**Correct pattern:**

```text
Use OAuth 2.0 Client Credentials flow or JWT Bearer flow for load test authentication.
Store client_id and client_secret in environment variables or a secrets manager,
never in the test script or version control.

# k6 example — credentials from environment variables
const tokenRes = http.post(TOKEN_URL, {
  grant_type: 'client_credentials',
  client_id: __ENV.SF_CLIENT_ID,
  client_secret: __ENV.SF_CLIENT_SECRET,
});
```

**Detection hint:** Any load test script containing literal `username`, `password`, or `security_token` values (not environment variable references).

---

## Anti-Pattern 4: Claiming Scale Test Can Be Run On-Demand

**What the LLM generates:** "Run Salesforce Scale Test from Setup to quickly validate your page performance under load."

**Why it happens:** LLMs infer from the name "Scale Test" that it is a self-service tool accessible through Setup, similar to how other Salesforce features work. Training data may not include the Support-coordinated scheduling process.

**Correct pattern:**

```text
Scale Test engagements are coordinated through Salesforce Support. Open a Support
case 2-3 weeks before your desired test window. Provide target concurrency, user
journey definitions, and the Full Copy sandbox name. The Scale Test team configures
and executes the tests during the scheduled window.
```

**Detection hint:** Any instruction suggesting Scale Test is available through Setup UI, can be triggered via CLI, or can be run "immediately" or "on-demand."

---

## Anti-Pattern 5: Ignoring EPT Client-Side Variability

**What the LLM generates:** "Measure EPT on the Opportunity page — if it's under 3 seconds, your page performance is acceptable for all users."

**Why it happens:** LLMs treat EPT as a single deterministic value rather than a distribution that varies by client environment. Training data rarely discusses the impact of browser extensions, VPN, or geographic distance on EPT measurements.

**Correct pattern:**

```text
EPT is a client-side metric that varies by browser, network path, extensions, and
hardware. Always:
1. Measure in an incognito window with extensions disabled
2. Document the client environment (browser version, network, location)
3. Use the Lightning Usage App for aggregate EPT trends (server-side collection)
4. Report EPT as a distribution (median, p90, p95), not a single value
5. Compare against the same client environment for before/after analysis
```

**Detection hint:** Any EPT recommendation that presents a single measurement as definitive, or that does not mention client-side variability factors.

---

## Anti-Pattern 6: Recommending Selenium for Lightning EPT Testing

**What the LLM generates:** "Use Selenium to load each Lightning page and measure document.readyState to capture EPT across your critical pages."

**Why it happens:** LLMs conflate browser automation page load timing with Salesforce's EPT metric. EPT is a Salesforce-specific measurement of time-to-interactive within the Lightning framework, not the standard browser DOMContentLoaded or readyState event.

**Correct pattern:**

```text
EPT is measured internally by the Lightning framework and reported via the Lightning
Usage App and EventLogFile (EPT event type). Browser automation tools cannot access
the EPT metric directly. For automated EPT collection:
- Use EventLogFile queries (EPT event type) for historical EPT data
- Use the Lightning Usage App for real-time dashboards
- Use Scale Test for EPT under concurrent load
Selenium/Playwright are appropriate for functional regression testing, not EPT measurement.
```

**Detection hint:** Any script that uses `document.readyState`, `DOMContentLoaded`, or `window.performance.timing` and labels the result as "EPT."
