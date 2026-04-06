# Examples — Performance Testing Salesforce

## Example 1: Scale Test Request for Pre-Release Validation

**Context:** An enterprise org with 3,000 daily active users is preparing for a major release that replaces a Visualforce Case management flow with a new LWC-based experience. The release NFR requires EPT under 3 seconds at 500 concurrent users.

**Problem:** Without Scale Test, the team deployed to production based on single-user testing in a Developer sandbox. The LWC pages loaded in 1.2 seconds for one user but degraded to 8+ seconds under real concurrency due to a non-cacheable Apex controller making 4 SOQL queries per component load, compounded across 500 sessions.

**Solution:**

```text
Scale Test Request — Support Case Template

Subject: Scale Test Request — Spring '26 Release Validation
Environment: Full Copy Sandbox "PERFTEST" (refreshed 2026-03-28)
Target Concurrency: 500 concurrent users
User Journeys:
  1. Case List View → Case Detail → Edit Case → Save (60% of users)
  2. New Case → Fill Form → Save → Redirect to Detail (25% of users)
  3. Dashboard Home → Drill into Report → Export (15% of users)
Preferred Test Window: April 14–18, 2026 (off-hours UTC)
Contact: performance-team@example.com
```

**Why it works:** The Scale Test request specifies the exact sandbox, realistic user journey mix with weighted percentages, target concurrency, and preferred window. The Scale Test team can configure synthetic users that replicate the actual transaction mix rather than uniform single-page loads.

---

## Example 2: k6 API Load Test Script for REST Endpoint

**Context:** A middleware integration calls a custom REST endpoint (`/services/apexrest/CaseSync/v1`) at peak rates of 200 requests per minute. The team needs to validate response time stays under 2 seconds at peak.

**Problem:** The team tested with Postman (single request, sequential) and saw 400ms response times. In production at peak concurrency, response times spiked to 6 seconds because the Apex handler performed a non-selective SOQL query that locked under concurrent access.

**Solution:**

```javascript
// k6 load test script — CaseSync API throughput test
import http from 'k6/http';
import { check, sleep } from 'k6';

// OAuth 2.0 Client Credentials flow for authentication
const TOKEN_URL = `${__ENV.SF_LOGIN_URL}/services/oauth2/token`;
const API_BASE = `${__ENV.SF_INSTANCE_URL}/services/apexrest/CaseSync/v1`;

export const options = {
  stages: [
    { duration: '2m', target: 10 },   // warm-up
    { duration: '5m', target: 50 },   // ramp to 25% peak
    { duration: '5m', target: 100 },  // ramp to 50% peak
    { duration: '10m', target: 200 }, // sustain at peak
    { duration: '2m', target: 0 },    // cool-down
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'], // 95th percentile under 2s
    http_req_failed: ['rate<0.01'],    // less than 1% failure rate
  },
};

export function setup() {
  const tokenRes = http.post(TOKEN_URL, {
    grant_type: 'client_credentials',
    client_id: __ENV.SF_CLIENT_ID,
    client_secret: __ENV.SF_CLIENT_SECRET,
  });
  return { token: tokenRes.json('access_token') };
}

export default function (data) {
  const headers = {
    Authorization: `Bearer ${data.token}`,
    'Content-Type': 'application/json',
  };

  const payload = JSON.stringify({
    subject: `Load Test Case ${Date.now()}`,
    priority: 'Medium',
    origin: 'API',
  });

  const res = http.post(API_BASE, payload, { headers });

  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 2s': (r) => r.timings.duration < 2000,
    'no rate limit': (r) => r.status !== 429,
  });

  sleep(Math.random() * 2 + 1); // think time 1-3 seconds
}
```

**Why it works:** The script uses OAuth 2.0 (not hardcoded credentials), ramps concurrency gradually through 4 stages, includes realistic think time, and defines explicit p95 latency and error rate thresholds. Environment variables keep secrets out of the script.

---

## Example 3: EPT Profiling and Optimization Cycle

**Context:** A sales team reports that the Opportunity detail page takes "forever to load." The admin sees no obvious issues in Setup.

**Problem:** Without EPT data, the team guesses at the cause and spends two sprints optimizing the wrong component.

**Solution:**

```text
EPT Measurement Steps:

1. Setup → Lightning Usage → Page-level EPT report
   Result: Opportunity Record Page — median EPT 4.8s, p90 EPT 7.2s

2. Chrome DevTools → Performance tab → Record page load
   Finding: 3 LWC components each making separate imperative Apex calls
   Total Apex round-trips: 5 (sequential, not parallel)
   Largest component render: 2.1s (related-contacts-panel)

3. Optimization actions:
   a. Consolidated 3 Apex calls into 1 composite method
   b. Made the consolidated method @AuraEnabled(cacheable=true)
   c. Replaced imperative calls with wire adapters
   d. Removed unused third-party analytics script (added 800ms)

4. Remeasure:
   Result: Opportunity Record Page — median EPT 1.9s, p90 EPT 2.8s
   Improvement: 60% reduction in median EPT
```

**Why it works:** The optimization is data-driven. EPT measurement identified the specific page and components causing the problem. The before/after comparison validates the fix against the 3-second NFR.

---

## Anti-Pattern: Testing Performance in a Developer Sandbox

**What practitioners do:** Run JMeter load tests against a Developer or Developer Pro sandbox because it is faster to provision and does not require a Support case.

**What goes wrong:** The Developer sandbox has 200 MB storage, no production data volume, no custom indexes, and simplified sharing calculations. A query that returns 50 rows in Developer may return 500,000 rows in production. Response times in Developer are 5-10x faster than production for data-intensive operations, creating false confidence.

**Correct approach:** Always use a Full Copy sandbox for performance testing. If Full Copy is not available in the org's edition, document the limitation and focus on relative comparisons (before vs. after optimization) rather than absolute performance claims. Never publish performance benchmarks from undersized sandboxes.
