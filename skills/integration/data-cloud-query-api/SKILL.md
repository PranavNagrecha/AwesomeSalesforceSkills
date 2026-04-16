---
name: data-cloud-query-api
description: "Use this skill when querying unified profile data, calculated insights, or Data Lake Objects from Data Cloud using ANSI SQL via the Query V2 or Query Connect APIs. Triggers on: SQL queries against Data Cloud, querying unified individuals, querying DMOs via API, paginating large Data Cloud result sets. NOT for SOQL queries against standard Salesforce objects, not for Data Cloud segment filtering in the UI, not for vector/semantic search (use data-cloud-vector-search-dev)."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Performance
tags:
  - data-cloud
  - query-api
  - sql
  - ansi-sql
  - unified-profile
  - calculated-insights
  - data-lake-objects
  - pagination
inputs:
  - "Data Cloud org with Query API access enabled"
  - "Unified Data Model objects (DMOs) or Data Lake Objects (DLOs) to query"
  - "Data Cloud-specific access token (from /services/a360/token endpoint)"
  - "dcInstanceUrl from the token response"
outputs:
  - "SQL query results from unified profiles, calculated insights, or DLOs"
  - "Pagination strategy using nextBatchId for large result sets"
  - "Query Connect API migration plan for row-count-unlimited querying"
triggers:
  - "query Data Cloud unified profile via API"
  - "Data Cloud SQL query returns no results"
  - "dcInstanceUrl vs instance_url Data Cloud"
  - "paginate Data Cloud query results nextBatchId"
  - "Data Cloud token exchange a360 token endpoint"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-16
---

# Data Cloud Query API

This skill activates when a practitioner needs to query unified profile data, calculated insights, or Data Lake Objects in Data Cloud programmatically using the Query V2 or Query Connect API. It covers authentication, SQL syntax requirements, pagination patterns, and the key differences between Query V2 and Query Connect.

---

## Before Starting

Gather this context before working on anything in this domain:

- Data Cloud Query API requires a Data Cloud-specific access token — NOT the standard Salesforce OAuth2 token from `/services/oauth2/token`. You must call `/services/a360/token` instead.
- The base URL for all Query API requests is `dcInstanceUrl` returned in the token response, NOT the standard Salesforce instance URL.
- Query V2 is synchronous and cursor-paginated via `nextBatchId`. Practitioners must fetch the full result set within 1 hour; inter-batch gaps must not exceed 3 minutes or the cursor expires.

---

## Core Concepts

### Authentication Is Separate from Standard Salesforce OAuth

Data Cloud uses a distinct token endpoint. After obtaining a standard Salesforce access token, you exchange it for a Data Cloud-scoped token:

```
POST https://<sf-instance>/services/a360/token
Content-Type: application/x-www-form-urlencoded
grant_type=urn:salesforce:grant-type:connected:app&subject_token=<sf_access_token>&subject_token_type=urn:ietf:params:oauth:token-type:access_token
```

The response contains `access_token`, `instance_url`, and critically `dcInstanceUrl`. Use `dcInstanceUrl` as the base for all subsequent Query API calls. Using the standard `instance_url` causes 404 errors.

### Query V2 — Synchronous Cursor-Paginated SQL

Query V2 (`POST /api/v2/query`) executes ANSI-standard SQL (not SOQL) against unified profile objects (DMOs), calculated insights, and Data Lake Objects. It returns up to a platform-defined row limit per batch, plus a `nextBatchId` for pagination. Practitioners must issue a follow-up GET to `/api/v2/query/{nextBatchId}` to retrieve subsequent pages. The entire fetch operation must complete within 1 hour from query submission and no single inter-batch gap may exceed 3 minutes, or the cursor is invalidated.

### Query Connect API — Row-Count-Unlimited Long-Running Queries

The Query Connect API is the successor pattern for large-scale result sets. It extends result availability to 24 hours and removes per-batch row-count restrictions. It is suited for nightly exports and data pipeline integrations where Query V2's 1-hour window is insufficient.

### ANSI SQL, Not SOQL

Data Cloud Query API uses ANSI SQL with Data Cloud-specific object names (e.g., `ssot__Individual__dlm` for the unified Individual DMO). SOQL syntax (e.g., `SELECT Id FROM Contact WHERE ...`) is invalid. Calculated Insight aliases are queried by their API name. You cannot use SOQL operators like `IN :idList` — only standard SQL `IN (...)` literals are supported.

---

## Common Patterns

### Pattern 1: Authenticate and Execute a Simple Profile Query

**When to use:** Querying unified individual profiles for a specific segment or identity match.

**How it works:**

```python
import requests

# Step 1: Get standard SF token
sf_token = get_salesforce_token()

# Step 2: Exchange for Data Cloud token
dc_token_resp = requests.post(
    f"{sf_instance}/services/a360/token",
    data={
        "grant_type": "urn:salesforce:grant-type:connected:app",
        "subject_token": sf_token,
        "subject_token_type": "urn:ietf:params:oauth:token-type:access_token"
    }
)
dc = dc_token_resp.json()
dc_base = dc["dcInstanceUrl"]
dc_access_token = dc["access_token"]

# Step 3: Execute query
headers = {"Authorization": f"Bearer {dc_access_token}", "Content-Type": "application/json"}
query_resp = requests.post(
    f"{dc_base}/api/v2/query",
    headers=headers,
    json={"sql": "SELECT Id__c, FirstName__c, Email__c FROM ssot__Individual__dlm LIMIT 1000"}
)
result = query_resp.json()
```

**Why not use SOQL:** SOQL cannot reach unified DMO objects. The Data Cloud object model lives outside the standard Salesforce data layer.

### Pattern 2: Full Pagination of Large Result Sets

**When to use:** When the result set exceeds a single batch and `nextBatchId` is returned.

**How it works:**

```python
import time

rows = []
data = result

while True:
    rows.extend(data.get("data", []))
    next_id = data.get("nextBatchId")
    if not next_id:
        break
    # Must fetch next page within 3 minutes
    data = requests.get(
        f"{dc_base}/api/v2/query/{next_id}",
        headers=headers
    ).json()

print(f"Total rows: {len(rows)}")
```

**Why not ignore nextBatchId:** Ignoring it silently truncates results. There is no automatic merge — every page must be explicitly fetched.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Results fit in a few thousand rows, need results now | Query V2 synchronous | Simplest path, immediate results |
| Large export, >1 hour to paginate, nightly pipeline | Query Connect API | 24-hour result window, no row-count limit |
| Semantic/vector similarity search | data-cloud-vector-search-dev skill | Query API only supports SQL predicates, not vector search |
| Filtering on SOQL-style Salesforce IDs | Use SQL IN literals | SOQL bind variables not supported in Data Cloud SQL |
| Querying a calculated insight | Use CI API name in FROM clause | CIs are queryable as table-like objects by their API name |

---

## Recommended Workflow

1. Confirm the org has Data Cloud provisioned and the connected app has the required Data Cloud OAuth scope (cdp_api) — missing scope causes token exchange to fail with 400.
2. Obtain a standard Salesforce access token via your preferred OAuth flow (Client Credentials, JWT Bearer, or User-Agent).
3. Exchange it for a Data Cloud-specific token via `/services/a360/token` and capture `dcInstanceUrl` — never use the standard `instance_url` for Data Cloud API calls.
4. Identify the target objects (DMO API names, DLO names, or Calculated Insight API names) using Data Cloud Setup > Data Model Explorer or the Schema API.
5. Write ANSI SQL targeting the correct object names — test with LIMIT 10 first to validate schema and token before executing full queries.
6. Implement pagination by checking for `nextBatchId` in every response and issuing follow-up GET requests within the 3-minute inter-batch window.
7. For long-running exports (>1 hour), migrate to the Query Connect API and adjust your retry/polling logic accordingly.

---

## Review Checklist

- [ ] Token exchange uses `/services/a360/token`, NOT `/services/oauth2/token`
- [ ] All API base URLs use `dcInstanceUrl`, NOT `instance_url`
- [ ] SQL uses ANSI syntax, no SOQL operators or bind variables
- [ ] Pagination loop checks for `nextBatchId` and handles cursor expiry
- [ ] Query submits within time window; consider Query Connect API for exports
- [ ] Connected app OAuth scope includes `cdp_api` (Data Cloud API)
- [ ] Object names match DMO/DLO API names, not standard Salesforce object names

---

## Salesforce-Specific Gotchas

1. **Token Endpoint Confusion** — Using `/services/oauth2/token` directly will NOT return a Data Cloud token. You must first get a standard SF token, then exchange it at `/services/a360/token`. Skipping the exchange causes all Query API calls to return 401 with no clear error about which endpoint was wrong.

2. **dcInstanceUrl vs instance_url** — Even after successful token exchange, using the standard `instance_url` for Data Cloud API calls returns 404. The `dcInstanceUrl` field may point to a different subdomain. Always extract and store `dcInstanceUrl` explicitly.

3. **Cursor Expiry Silently Fails** — If you wait more than 3 minutes between pagination requests, the `nextBatchId` becomes invalid and the follow-up GET returns 404 or an error. There is no automatic warning. Design your pagination loop to minimize latency between requests.

4. **ANSI SQL Object Names Are Case-Sensitive** — DMO API names in SQL must match exactly, including underscores and suffixes (e.g., `ssot__Individual__dlm`). Querying `Individual` without namespace prefix returns an error, not an empty result.

5. **Calculated Insights Must Be Published** — A Calculated Insight is only queryable after it has been successfully published and its last batch run has completed. Querying an unpublished or failed CI returns an empty result with no error.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Data Cloud SQL query | ANSI-SQL statement targeting DMO, DLO, or Calculated Insight API names |
| Pagination driver | Python/Node loop that follows nextBatchId until no further pages remain |
| Token exchange helper | Function that obtains Data Cloud-scoped access token and dcInstanceUrl |

---

## Related Skills

- data-cloud-vector-search-dev — for semantic similarity search against Data Cloud vector indexes
- data-cloud-integration-strategy — for understanding the full connector and ingestion pipeline before querying
- rest-api-patterns — for standard Salesforce SOQL and REST queries against non-Data Cloud objects
