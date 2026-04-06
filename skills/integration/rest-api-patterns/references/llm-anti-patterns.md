# LLM Anti-Patterns — REST API Patterns

Common mistakes AI coding assistants make when generating or advising on Salesforce REST API integration patterns.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Not Handling nextRecordsUrl for Query Pagination

**What the LLM generates:** `GET /services/data/vXX.0/query/?q=SELECT+Id+FROM+Account` and directly using the `records` array without checking for `nextRecordsUrl`, which is required when query results exceed 2,000 records.

**Why it happens:** Small-dataset examples dominate training data. Pagination handling adds complexity that tutorials often skip.

**Correct pattern:**

```text
REST SOQL query pagination:

1. Initial query:
   GET /services/data/vXX.0/query/?q=SELECT+Id,Name+FROM+Account
   Response: { totalSize: 50000, done: false, nextRecordsUrl: "/services/data/vXX.0/query/01gxx...-2000", records: [...] }

2. Follow nextRecordsUrl until done = true:
   GET /services/data/vXX.0/query/01gxx...-2000
   Response: { done: false, nextRecordsUrl: "...-4000", records: [...] }

3. Continue until: { done: true, records: [...] }

Default page size: 2,000 records
Maximum results: 50,000 records via REST query (use Bulk API for more)
```

**Detection hint:** Flag REST API query code that reads `records` without checking the `done` field or following `nextRecordsUrl`. Regex: missing `nextRecordsUrl` handling in query response processing.

---

## Anti-Pattern 2: Making Individual API Calls Instead of Using Composite Resources

**What the LLM generates:** Separate POST calls to create a parent Account and then a child Contact, consuming 2 API calls when the Composite API can do both in a single call with referencing.

**Why it happens:** Individual CRUD calls are simpler and more represented in training data. Composite resources (Composite, Composite Batch, SObject Tree) are underutilized in examples.

**Correct pattern:**

```text
Composite API options for reducing API call count:

1. Composite (/services/data/vXX.0/composite/):
   - Up to 25 subrequests per call
   - Subrequests can reference results of previous subrequests
   - All-or-nothing with allOrNone: true
   - Best for: related record creation with dependencies

2. Composite Batch (/services/data/vXX.0/composite/batch/):
   - Up to 25 independent subrequests
   - No cross-referencing between subrequests
   - Best for: independent operations in parallel

3. SObject Collections (/services/data/vXX.0/composite/sobjects/):
   - Up to 200 records per call (same object, same operation)
   - Best for: bulk create/update/delete of same object type

4. SObject Tree (/services/data/vXX.0/composite/tree/):
   - Create parent + children in one call
   - Up to 200 total records
   - Best for: parent-child record creation
```

**Detection hint:** Flag integration code that makes 3+ sequential API calls for related operations. Check whether Composite or SObject Collections could reduce call count.

---

## Anti-Pattern 3: Hardcoding API Version in Integration Code

**What the LLM generates:** `GET /services/data/v55.0/sobjects/Account/` with a hardcoded API version that will become outdated as Salesforce releases new versions (3 times per year).

**Why it happens:** Every REST API example includes a specific version number. LLMs reproduce the version from their training data, which may be several releases old.

**Correct pattern:**

```text
API version management strategies:

1. Discover the latest version dynamically:
   GET /services/data/
   Returns: [{"version": "60.0", "url": "/services/data/v60.0"}, ...]
   Use the latest version or a specific minimum version.

2. Store the version as configuration (not hardcoded):
   API_VERSION = "61.0"  // in environment variable or config file
   endpoint = f"/services/data/v{API_VERSION}/sobjects/Account/"

3. Version pinning strategy:
   - Pin to a specific version for stability
   - Update after testing with each Salesforce release
   - Salesforce supports the current version + ~3 years of previous versions
   - Deprecated versions return errors

4. For Salesforce CLI integrations:
   sf project deploy uses the version from sfdx-project.json
```

**Detection hint:** Flag hardcoded API versions in integration code (e.g., `v55.0`, `v56.0`) that are more than 2 releases old. Check for dynamic version discovery or configurable version.

---

## Anti-Pattern 4: Ignoring API Rate Limits in Integration Design

**What the LLM generates:** Integration code that makes API calls in a tight loop without considering Salesforce's daily API request limit (varies by edition and license count) or the per-user concurrent request limit.

**Why it happens:** API limits are operational constraints not always surfaced in API documentation examples. LLMs generate code for correctness without throttling.

**Correct pattern:**

```text
Salesforce REST API rate limits:

Daily API request allocation:
  Enterprise: 100,000 + (user licenses x per-license add)
  Unlimited: 500,000 + (user licenses x per-license add)
  Check: GET /services/data/vXX.0/limits/

Concurrent request limits:
  25 concurrent long-running requests per org
  Per-user concurrency limits may apply

Rate limit response:
  HTTP 403 with error code REQUEST_LIMIT_EXCEEDED

Integration design for rate limits:
1. Monitor /limits/ endpoint before large batch operations
2. Implement exponential backoff on 403 responses
3. Use Composite API to reduce call count (25 subrequests = 1 API call)
4. Use Bulk API for operations over 2,000 records
5. Schedule high-volume operations during off-peak hours
6. Cache frequently-accessed reference data client-side
```

**Detection hint:** Flag integration code that makes API calls in a loop without rate limit handling. Look for missing 403 error handling and backoff logic.

---

## Anti-Pattern 5: Not Using ETags or Conditional Requests for Polling

**What the LLM generates:** "Poll the REST API every 30 seconds to check for record changes" without using ETags, If-None-Match headers, or event-driven alternatives (CDC, Platform Events) that are more efficient.

**Why it happens:** Polling is the simplest pattern and is familiar from general API integration. LLMs do not consistently recommend Salesforce-specific alternatives that reduce API consumption.

**Correct pattern:**

```text
Alternatives to polling for record changes:

1. Change Data Capture (CDC): automatic events on record changes
   Subscribe via Pub/Sub API — zero API calls consumed
   Best for: real-time sync of record mutations

2. Platform Events: custom events published by automation
   Subscribe via Pub/Sub API — zero API calls consumed
   Best for: business events, custom notification payloads

3. Outbound Messages: SOAP-based push notifications
   Triggered by Workflow Rules — legacy but still functional
   Best for: simple integrations with SOAP endpoints

4. If polling is unavoidable:
   - Use If-Modified-Since header on record queries
   - Increase polling interval to match business SLA
   - Query SystemModstamp for change detection
   - Use SOQL with WHERE SystemModstamp > :lastPollTime
```

**Detection hint:** Flag polling-based integration designs that make REST API calls on a short interval. Check whether CDC or Platform Events would be more efficient.
