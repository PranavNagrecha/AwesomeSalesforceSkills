# LLM Anti-Patterns — Data Cloud Query API

Common mistakes AI coding assistants make when generating or advising on Data Cloud Query API.

## Anti-Pattern 1: Using SOQL Syntax for Data Cloud Queries

**What the LLM generates:** `SELECT Id, Email FROM Contact WHERE AccountId = 'someId'` — standard SOQL against CRM objects, sent to a Data Cloud endpoint.

**Why it happens:** LLMs are trained on large bodies of Salesforce SOQL documentation and code. Data Cloud uses a different query language (ANSI SQL) and a different object model. The LLM defaults to familiar SOQL patterns.

**Correct pattern:**

```sql
SELECT Id__c, Email__c
FROM ssot__Individual__dlm
WHERE ssot__AccountId__c = 'someId'
```

**Detection hint:** Look for SOQL-specific constructs: `:variable` binds, `FROM Contact` / `FROM Account` without namespace prefix, `TYPEOF`, `GROUP BY ROLLUP`, or SOQL aggregate functions like `toLabel()`.

---

## Anti-Pattern 2: Using Standard Salesforce OAuth Token Directly for Data Cloud API

**What the LLM generates:**

```python
token = get_salesforce_token()  # /services/oauth2/token
headers = {"Authorization": f"Bearer {token}"}
requests.post("https://myorg.my.salesforce.com/api/v2/query", ...)
```

**Why it happens:** LLMs know the standard Salesforce OAuth pattern well and apply it universally. They are not aware that Data Cloud requires a separate token exchange at a different endpoint.

**Correct pattern:**

```python
sf_token = get_salesforce_token()
dc_resp = requests.post(f"{sf_instance}/services/a360/token", data={
    "grant_type": "urn:salesforce:grant-type:connected:app",
    "subject_token": sf_token,
    "subject_token_type": "urn:ietf:params:oauth:token-type:access_token"
})
dc = dc_resp.json()
dc_token = dc["access_token"]
dc_base = dc["dcInstanceUrl"]  # Use this, not instance_url
```

**Detection hint:** If the code posts directly to `/api/v2/query` using a token obtained from `/services/oauth2/token` without a `/services/a360/token` exchange step, it is wrong.

---

## Anti-Pattern 3: Ignoring Pagination (No nextBatchId Handling)

**What the LLM generates:**

```python
resp = requests.post(f"{dc_base}/api/v2/query", json={"sql": sql})
data = resp.json()["data"]  # Only first batch — truncated silently
```

**Why it happens:** LLMs familiar with REST APIs that return all results in a single response apply the same pattern. Data Cloud Query V2 paginates all large result sets and requires explicit `nextBatchId` follow-up.

**Correct pattern:**

```python
rows = []
data = resp.json()
while True:
    rows.extend(data.get("data", []))
    next_id = data.get("nextBatchId")
    if not next_id:
        break
    data = requests.get(f"{dc_base}/api/v2/query/{next_id}", headers=headers).json()
```

**Detection hint:** Any code that reads `resp.json()["data"]` without checking for `nextBatchId` in a loop is truncating results.

---

## Anti-Pattern 4: Using instance_url Instead of dcInstanceUrl

**What the LLM generates:**

```python
dc_base = token_response["instance_url"]  # Wrong field
```

**Why it happens:** `instance_url` is the well-known field in all Salesforce OAuth responses. LLMs default to it. `dcInstanceUrl` is a Data Cloud-specific field returned only by the `/services/a360/token` exchange.

**Correct pattern:**

```python
dc_base = dc_token_response["dcInstanceUrl"]  # Correct field
```

**Detection hint:** Search for `instance_url` being used as the base URL for `/api/v2/query` calls — it should be `dcInstanceUrl`.

---

## Anti-Pattern 5: Asserting the 100-Event-Per-Fetch Cap Is a Rate Limit

**What the LLM generates:** "Data Cloud Query API is rate-limited to 100 rows per request — you cannot query more than 100 rows at a time."

**Why it happens:** LLMs conflate per-request fetch size limits with throughput rate limits. The 100 events per FetchRequest is a Pub/Sub API concept that bleeds into Data Cloud Query API descriptions in training data.

**Correct pattern:** Data Cloud Query V2 has per-batch row limits (platform-defined, not fixed at 100), and the limit is a batch size, not a rate limit. Pagination via `nextBatchId` allows fetching the complete result set over multiple requests. There is no 100-row hard cap on query results — only a per-batch size that determines how many rows appear per response.

**Detection hint:** Claims of "100 row limit" for Data Cloud Query API or recommendations to add `LIMIT 100` to avoid hitting limits are red flags.
