# Examples — API Security and Rate Limiting

## Example 1: Restrict a Connected App to Specific IP Ranges

**Context:** A middleware integration platform (e.g., MuleSoft, Boomi, or custom Java service) calls Salesforce REST APIs from a fixed data-center IP block. The Connected App currently has no IP restrictions, meaning a stolen token could be used from any network.

**Problem:** Without IP restriction, a compromised OAuth client credential or access token can be used from any source IP. The integration runs from two static IPs: `203.0.113.10` and `203.0.113.11`.

**Solution:**

```
# Setup → App Manager → [Your Connected App] → Edit → OAuth Policies

IP Relaxation: Enforce login IP ranges on every request

# Then under the Connected App record → OAuth Policies → IP Ranges:
# Add the following IP ranges:

Start IP: 203.0.113.10   End IP: 203.0.113.10
Start IP: 203.0.113.11   End IP: 203.0.113.11
```

Then verify the restriction:

```bash
# From an authorized IP — should succeed
curl -s -X POST "https://login.salesforce.com/services/oauth2/token" \
  -d "grant_type=client_credentials&client_id=<CLIENT_ID>&client_secret=<CLIENT_SECRET>"

# Expected: { "access_token": "...", "token_type": "Bearer", ... }

# From an unauthorized IP — should fail
# Expected: { "error": "ip restricted", "error_description": "..." }
```

**Why it works:** The "Enforce login IP ranges on every request" policy causes Salesforce to validate the originating IP on every API call using the access token, not just at token issuance time. Tokens stolen from memory or logs become useless outside the authorized network.

---

## Example 2: Monitor API Usage with Event Log Files

**Context:** The org has Event Monitoring enabled and hit 80% of daily API call quota unexpectedly. The team needs to identify which user or process is responsible.

**Problem:** Setup → API Usage Metrics shows high consumption but doesn't break it down by user or endpoint.

**Solution:**

```apex
// Step 1: Query the EventLogFile object for the API event type
// Run this SOQL in the Developer Console or via REST API

SELECT Id, EventType, LogDate, LogFileLength, LogFileUrl
FROM EventLogFile
WHERE EventType = 'API'
ORDER BY LogDate DESC
LIMIT 5

// Step 2: Download the CSV file from the LogFileUrl
// Using REST API with authenticated session:
// GET /services/data/v60.0/sobjects/EventLogFile/<Id>/LogFile
// The response is a raw CSV

// Step 3: Key columns to analyze in the CSV:
// USER_ID_DERIVED  — the Salesforce user ID making the call
// URI              — the REST endpoint called (e.g., /services/data/v60.0/sobjects/Account)
// METHOD           — HTTP method (GET, POST, PATCH, DELETE)
// CPU_TIME         — server-side processing time in milliseconds
// TOTAL_TIME       — total response time in milliseconds
// CLIENT_IP        — source IP of the caller
// CONNECTED_APP_ID — Salesforce ID of the Connected App, if OAuth was used
```

```python
# Example: aggregate API calls by user from downloaded CSV
import csv
from collections import Counter

with open('api_event_log.csv', newline='') as f:
    reader = csv.DictReader(f)
    user_counter = Counter(row['USER_ID_DERIVED'] for row in reader)

for user_id, count in user_counter.most_common(10):
    print(f"{user_id}: {count} calls")
```

**Why it works:** Event Log Files provide per-call granularity including user, endpoint, and source IP. The `CONNECTED_APP_ID` column maps to the Connected App used, making it straightforward to identify which integration is responsible for high-volume consumption.

---

## Example 3: Trim OAuth Scopes on a Connected App

**Context:** A nightly data export job authenticates via an internal Connected App. On review, the app was created with `full` scope — equivalent to full user permissions.

**Problem:** The export job only reads Account and Contact records. The `full` scope grants it access to everything the integration user can access, including administrative APIs, Chatter, and any future permissions granted to that user profile.

**Solution:**

```
# Setup → App Manager → [Export Integration App] → Edit → OAuth Settings

# Remove:
full
web
chatter_api

# Keep:
api                         (REST API access scoped to user's object permissions)
refresh_token offline_access (allows background token refresh without user re-auth)

# Save. Existing tokens with the old scopes remain valid until they expire
# or are revoked. Revoke active tokens via:
# Setup → Connected Apps OAuth Usage → Revoke All
```

**Why it works:** OAuth scopes are enforced at the Connected App level regardless of the user's profile permissions. By removing `full` and retaining only `api`, the integration's maximum possible access is bounded by the user's object-level permissions — which are already limited to read access on Account and Contact in this scenario.

---

## Example 4: Implementing 429-Safe Retry Logic

**Context:** An integration sends record updates to Salesforce in parallel threads. Under peak load it receives HTTP 429 responses.

**Problem:** The current implementation retries immediately on 429, causing a thundering herd that continues triggering 429s.

**Solution:**

```python
import time
import random
import requests

def call_salesforce_api(url, headers, payload, max_retries=5):
    """Call Salesforce REST API with bounded exponential backoff on 429."""
    delay = 1.0  # initial base delay in seconds

    for attempt in range(max_retries):
        response = requests.patch(url, headers=headers, json=payload)

        if response.status_code == 200:
            return response

        if response.status_code == 429:
            # Respect the Retry-After header if present
            retry_after = response.headers.get('Retry-After')
            if retry_after:
                wait = float(retry_after)
            else:
                # Exponential backoff with ±20% jitter
                jitter = random.uniform(0.8, 1.2)
                wait = delay * jitter
                delay = min(delay * 2, 60)  # cap at 60 seconds

            print(f"429 received, waiting {wait:.1f}s (attempt {attempt+1}/{max_retries})")
            time.sleep(wait)
            continue

        # Non-retryable error
        response.raise_for_status()

    raise RuntimeError(f"Exhausted {max_retries} retries due to 429 rate limiting")
```

**Why it works:** Respecting `Retry-After` ensures the client waits exactly as long as Salesforce requests. Exponential backoff with jitter prevents multiple callers from retrying at the same instant. Capping retries prevents infinite loops when the daily limit (not just a momentary rate spike) has been exhausted.

---

## Anti-Pattern: Granting Full Scope to All Connected Apps

**What practitioners do:** When setting up a new Connected App, they accept the default scope selection or check `full` "just in case" the integration needs it later.

**What goes wrong:** A compromised integration credential provides unrestricted access to all data and functionality the authorized user can access. Scope creep accumulates across many Connected Apps, making it impossible to reason about the actual API attack surface. When the integration user's profile is later expanded (new permissions, new objects), those automatically become available to the integration without any explicit authorization change.

**Correct approach:** Default to `api` + `refresh_token offline_access` for all headless integrations. Add narrower scopes (`visualforce`, `content`) only when a specific feature requires them. Document the justification for each scope in the Connected App description field. Review scope grants annually or when the integration undergoes significant changes.
