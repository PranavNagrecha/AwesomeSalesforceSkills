# Examples — Data Cloud Query API

## Example 1: Export Unified Individual Profiles with Full Pagination

**Context:** A data engineering team needs to export all unified individual records from Data Cloud nightly to an external data warehouse for BI reporting.

**Problem:** The team initially used standard Salesforce REST API SOQL against Contact objects but got no Data Cloud-unified data. When they switched to Query V2, they captured only the first batch because they did not implement pagination.

**Solution:**

```python
import requests

def get_dc_token(sf_instance, sf_access_token):
    resp = requests.post(
        f"{sf_instance}/services/a360/token",
        data={
            "grant_type": "urn:salesforce:grant-type:connected:app",
            "subject_token": sf_access_token,
            "subject_token_type": "urn:ietf:params:oauth:token-type:access_token"
        }
    )
    resp.raise_for_status()
    d = resp.json()
    return d["access_token"], d["dcInstanceUrl"]

def query_all_individuals(dc_token, dc_base):
    headers = {"Authorization": f"Bearer {dc_token}", "Content-Type": "application/json"}
    sql = "SELECT Id__c, FirstName__c, LastName__c, Email__c FROM ssot__Individual__dlm"
    resp = requests.post(f"{dc_base}/api/v2/query", headers=headers, json={"sql": sql})
    resp.raise_for_status()
    data = resp.json()
    rows = []
    while True:
        rows.extend(data.get("data", []))
        next_id = data.get("nextBatchId")
        if not next_id:
            break
        # Must fetch next batch within 3-minute inter-batch window
        data = requests.get(
            f"{dc_base}/api/v2/query/{next_id}", headers=headers
        ).json()
    return rows
```

**Why it works:** Token exchange at `/services/a360/token` returns a Data Cloud-scoped token and `dcInstanceUrl`. The pagination loop follows `nextBatchId` until no further pages remain, capturing the complete result set.

---

## Example 2: Query a Published Calculated Insight

**Context:** A RevOps analyst wants to programmatically pull the latest Customer 360 Lifetime Value Calculated Insight for all gold-tier customers.

**Problem:** Querying a Calculated Insight that had never been published returned empty results with no error message. The team assumed the CI was empty.

**Solution:**

1. In Data Cloud Setup, navigate to Calculated Insights, confirm the CI status is **Published** and the last batch run succeeded.
2. Identify the CI's API name (e.g., `Customer360LTV__insight`).
3. Execute the ANSI SQL query:

```python
sql = """
SELECT
    Individual_Id__c,
    LTV__c,
    TierLevel__c
FROM Customer360LTV__insight
WHERE TierLevel__c = 'Gold'
ORDER BY LTV__c DESC
LIMIT 500
"""
headers = {"Authorization": f"Bearer {dc_token}", "Content-Type": "application/json"}
resp = requests.post(f"{dc_base}/api/v2/query", headers=headers, json={"sql": sql})
result = resp.json()
```

**Why it works:** Calculated Insights are only queryable after publication. The SQL uses standard `WHERE` and `ORDER BY` — no SOQL-specific constructs needed.

---

## Anti-Pattern: Using Standard Salesforce instance_url for Data Cloud Queries

**What practitioners do:** After getting a Data Cloud token, they construct the query URL using the standard `instance_url` field (e.g., `https://myorg.my.salesforce.com`) instead of `dcInstanceUrl`.

**What goes wrong:** All Query API requests return 404 or 401 with a misleading error. The `dcInstanceUrl` may point to a different subdomain (e.g., `https://myorg.c360a.salesforce.com`) and is mandatory for Data Cloud API routing.

**Correct approach:** Always extract and store `dcInstanceUrl` from the token exchange response. Use it exclusively as the base URL for `/api/v2/query` and all other Data Cloud API endpoints.
