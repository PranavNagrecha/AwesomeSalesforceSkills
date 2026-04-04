# Examples — REST API Patterns

## Example 1: Composite Request — Create Account and Contact Atomically

**Context:** An external ERP system provisions new customers and must create an Account with a primary Contact in Salesforce. Both records must succeed or neither should be created.

**Problem:** Two separate REST POST calls require the caller to capture the new Account ID after the first call, then pass it into the Contact creation payload. If the Contact creation fails, the Account exists without a Contact and a compensating delete is needed. Race conditions are possible in concurrent scenarios.

**Solution:**

```http
POST /services/data/v63.0/composite/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "allOrNone": true,
  "compositeRequest": [
    {
      "method": "POST",
      "url": "/services/data/v63.0/sobjects/Account/",
      "referenceId": "NewAccount",
      "body": {
        "Name": "Acme Corp",
        "BillingCity": "San Francisco",
        "BillingState": "CA"
      }
    },
    {
      "method": "POST",
      "url": "/services/data/v63.0/sobjects/Contact/",
      "referenceId": "NewContact",
      "body": {
        "LastName": "Smith",
        "FirstName": "Jane",
        "Email": "jane.smith@acme.com",
        "AccountId": "@{NewAccount.id}"
      }
    }
  ]
}
```

**Response (success):**

```json
{
  "compositeResponse": [
    {
      "body": { "id": "001XX000003GYn1", "success": true, "errors": [] },
      "httpHeaders": { "Location": "/services/data/v63.0/sobjects/Account/001XX000003GYn1" },
      "httpStatusCode": 201,
      "referenceId": "NewAccount"
    },
    {
      "body": { "id": "003XX000004TkZp", "success": true, "errors": [] },
      "httpHeaders": { "Location": "/services/data/v63.0/sobjects/Contact/003XX000004TkZp" },
      "httpStatusCode": 201,
      "referenceId": "NewContact"
    }
  ]
}
```

**Why it works:** The `@{NewAccount.id}` reference is resolved server-side before the Contact subrequest executes. `allOrNone: true` ensures database-level atomicity — a validation failure on the Contact rolls back the Account insert with no compensating logic required on the caller.

---

## Example 2: Paginated SOQL Query Loop

**Context:** A nightly sync job needs to export all Opportunity records created in the last 30 days. The org has 12,000 such records — well above the 2,000-record batch size.

**Problem:** A single `/query/` request returns only up to 2,000 records. An integration that does not follow pagination silently exports a fraction of the data with no error raised.

**Solution (pseudocode with HTTP calls shown):**

```
# Initial request
GET /services/data/v63.0/query/?q=SELECT+Id%2CName%2CStageName%2CAmount+FROM+Opportunity+WHERE+CreatedDate=LAST_N_DAYS%3A30

# Response (abbreviated):
{
  "totalSize": 12000,
  "done": false,
  "nextRecordsUrl": "/services/data/v63.0/query/01gXX000000ABC1AAA-2000",
  "records": [ ...2000 records... ]
}

# Follow the next page — prepend instance hostname
GET https://<instance>.salesforce.com/services/data/v63.0/query/01gXX000000ABC1AAA-2000

# Repeat until response contains "done": true
```

**Python loop skeleton (stdlib only):**

```python
import urllib.request
import json

def fetch_all_records(instance_url, access_token, soql):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    encoded_soql = urllib.parse.quote(soql)
    url = f"{instance_url}/services/data/v63.0/query/?q={encoded_soql}"
    records = []

    while url:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
        records.extend(data["records"])
        if data.get("done"):
            break
        # nextRecordsUrl is a path; prepend instance host
        url = instance_url + data["nextRecordsUrl"]

    return records
```

**Why it works:** The loop inspects `done` on every response and constructs the next URL by prepending the instance hostname to `nextRecordsUrl`. The query locator embedded in `nextRecordsUrl` is server-managed — it holds the cursor position and handles result-set consistency for the life of the query.

---

## Example 3: Upsert Account by External ID

**Context:** An integration syncs Account records from a CRM with a field `External_Id__c` (External ID, unique, indexed). On each sync cycle, records may or may not already exist in Salesforce.

**Problem:** A query-then-insert-or-update pattern requires two REST calls per record and introduces a race window between the read and the write.

**Solution:**

```http
PATCH /services/data/v63.0/sobjects/Account/External_Id__c/CRM-12345
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "Name": "Acme Corp",
  "BillingCity": "San Francisco"
}
```

- HTTP 201 = record was created (new external ID)
- HTTP 200 = record was updated (existing external ID)
- HTTP 300 = multiple records share that external ID value (data quality issue — fix duplicates before re-trying)

**Why it works:** Salesforce handles the create-vs-update decision atomically server-side. No pre-query is needed. The external ID field must be marked as External ID and unique in the object definition to guarantee the 300 duplicate-detection behavior.

---

## Anti-Pattern: Checking Only the Outer HTTP Status on Composite Calls

**What practitioners do:** After calling `/composite/` or `/composite/batch/`, they check whether the outer HTTP response code is 200 and assume all subrequests succeeded.

**What goes wrong:** Composite always returns HTTP 200 for the outer envelope even when individual subrequests fail with 4xx. The partial failure is only visible by inspecting `httpStatusCode` on each entry in `compositeResponse`. Silently skipping failed subrequests causes data loss or partial record states that are difficult to diagnose later.

**Correct approach:** After confirming the outer HTTP 200, iterate over `compositeResponse` and check each entry's `httpStatusCode`. Treat any 4xx or 5xx within a subrequest as an error requiring retry, alerting, or compensating logic. When `allOrNone: true` is set, a single subrequest 4xx rolls back the whole call — but you still need to read the response to know which subrequest failed and why.
