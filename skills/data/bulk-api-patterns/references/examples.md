# Examples — Bulk API Patterns

## Example 1: Large Account Import Using Standard Ingest Job

**Context:** A data integration team needs to insert 800,000 Account records from a legacy CRM into Salesforce. The source system exports a UTF-8 CSV with LF line endings and comma delimiters. The team needs a reference implementation for the full Bulk API 2.0 ingest lifecycle.

**Problem:** The team previously used REST Composite batches of 200 records, requiring 4,000 HTTP calls and regularly hitting API call limits. They also had no integrity check — records that ended up in `unprocessedRecords` were silently lost.

**Solution:**

```
Step 1 — Authenticate and obtain OAuth 2.0 bearer token.

Step 2 — Create the ingest job:
POST /services/data/v66.0/jobs/ingest/
Authorization: Bearer {token}
Content-Type: application/json

{
  "object": "Account",
  "operation": "insert",
  "contentType": "CSV",
  "lineEnding": "LF",
  "columnDelimiter": "COMMA"
}
Response: { "id": "750R000000xxxxAAA", "state": "Open", "contentUrl": "..." }

Step 3 — Split the CSV into ~8 chunks of ~100,000 records each
(each must be under 100 MB raw / 150 MB base64).
For each chunk:
PUT /services/data/v66.0/jobs/ingest/750R000000xxxxAAA/batches
Content-Type: text/csv
[chunk CSV body]

CSV format note: use "#N/A" in any cell to explicitly null a field.
Empty cells set an empty string, which is NOT the same as null and will
fail required-field validation on non-text fields.

Step 4 — Signal upload complete (MANDATORY):
PATCH /services/data/v66.0/jobs/ingest/750R000000xxxxAAA
Content-Type: application/json
{ "state": "UploadComplete" }
State transitions to InProgress. Job never starts without this PATCH.

Step 5 — Poll every 30 seconds:
GET /services/data/v66.0/jobs/ingest/750R000000xxxxAAA
Stop when state is "JobComplete", "Failed", or "Aborted".

Step 6 — Retrieve all three result endpoints:
GET .../750R000000xxxxAAA/successfulResults/   → 794,500 rows
GET .../750R000000xxxxAAA/failedResults/       → 5,200 rows with sf__Error
GET .../750R000000xxxxAAA/unprocessedRecords/  → 300 rows (batch timeout)

Integrity check: 794,500 + 5,200 + 300 = 800,000 ✓

Step 7 — Inspect failedResults sf__Error values:
- 4,800 rows: "REQUIRED_FIELD_MISSING: [BillingCountry]" → fix source data
- 400 rows: "DUPLICATE_VALUE" → switch to upsert for these records

Step 8 — Create a NEW job for the 5,500 failed + unprocessed records.
Never reuse the original job ID.
```

**Why it works:** Splitting into chunks keeps each upload under the 150 MB base64 ceiling. The integrity check across all three result endpoints catches unprocessed records that would be silently missed if only `failedResults` was checked. Each error category requires a different root-cause fix before resubmission.

---

## Example 2: Bulk SOQL Export with Locator Pagination

**Context:** A data analyst needs to extract 4.2 million Opportunity records for an external analytics pipeline. Synchronous SOQL is not viable (50,000-record limit per query, plus timeout risk). The analyst needs paginated CSV output that can be resumed if interrupted.

**Problem:** The team was using Export Now in Data Loader UI, which hit timeouts on large objects and produced partial exports with no way to verify completeness.

**Solution:**

```
Step 1 — Create a query job:
POST /services/data/v66.0/jobs/query
{
  "operation": "query",
  "query": "SELECT Id, AccountId, Name, Amount, StageName, CloseDate FROM Opportunity WHERE CreatedDate >= 2022-01-01T00:00:00Z"
}
Response: { "id": "750R000000yyyyBBB", "state": "UploadComplete" }
(Query jobs skip Open state and go directly to UploadComplete on creation.)

Step 2 — Poll until JobComplete:
GET /services/data/v66.0/jobs/query/750R000000yyyyBBB

Step 3 — Pagination loop in Python (stdlib only):
```

```python
import urllib.request
import json

job_id = "750R000000yyyyBBB"
base_url = f"https://yourorg.my.salesforce.com/services/data/v66.0/jobs/query/{job_id}/results"
headers = {"Authorization": f"Bearer {token}", "Accept": "text/csv"}

locator = None
page_num = 1

while True:
    url = base_url if locator is None else f"{base_url}?locator={locator}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        csv_data = resp.read().decode("utf-8")
        sforce_locator = resp.headers.get("Sforce-Locator", "null")

    # Write page to file; skip header row after first page
    with open(f"results_page_{page_num}.csv", "w") as f:
        if page_num == 1:
            f.write(csv_data)
        else:
            # Skip the header line
            f.write(csv_data.split("\n", 1)[1] if "\n" in csv_data else "")

    # CRITICAL: compare as string, not None/falsy — "null" is a literal string
    if sforce_locator == "null":
        break

    locator = sforce_locator
    page_num += 1

print(f"Downloaded {page_num} pages.")
```

```
Result: ~85 pages × ~50,000 records = 4.2M records across 85 CSV files.
Locator values are stable — safe to save and resume the loop if interrupted.
```

**Why it works:** Bulk API 2.0 query jobs automatically apply PK chunking to split the SOQL into sub-ranges, enabling reliable extraction of arbitrarily large result sets. The `Sforce-Locator` header provides a stable cursor that allows interrupted downloads to resume from the last successful page without re-processing earlier pages.

---

## Example 3: Multipart Upsert Job for Nightly ERP Integration

**Context:** A nightly ERP sync pushes 12,000 Contact records using an `ERP_Contact_Id__c` external ID field. The payload is always under 2 MB. The integration team wants to minimize HTTP round-trips and eliminate the risk of forgetting the `UploadComplete` PATCH.

**Problem:** An earlier version of the integration sometimes failed between the upload step and the `UploadComplete` PATCH, leaving jobs orphaned in `Open` state indefinitely and consuming open-job slots.

**Solution:** Use multipart job creation to combine job creation and data upload into a single HTTP call. The job auto-transitions to `UploadComplete` on creation.

```
POST /services/data/v66.0/jobs/ingest/
Content-Type: multipart/form-data; boundary="BOUNDARY"
Authorization: Bearer {token}

--BOUNDARY
Content-Disposition: form-data; name="job"
Content-Type: application/json; charset=UTF-8

{
  "object": "Contact",
  "operation": "upsert",
  "externalIdFieldName": "ERP_Contact_Id__c",
  "contentType": "CSV",
  "lineEnding": "LF"
}
--BOUNDARY
Content-Disposition: form-data; name="content"
Content-Type: text/csv

FirstName,LastName,Email,ERP_Contact_Id__c,Title
Jane,Smith,jane.smith@example.com,ERP-00001,VP of Sales
John,Doe,john.doe@example.com,ERP-00002,#N/A
--BOUNDARY--
```

Response state will be `"UploadComplete"` immediately — no separate PATCH required.
Do NOT send a `PATCH {"state": "UploadComplete"}` afterward — the job is already past Open state and the request will error.

**Why it works:** Multipart job creation eliminates the two-step create-then-signal pattern for small datasets (up to 100,000 characters of CSV). The atomicity means there is no window between upload and signal where an integration failure can orphan the job in Open state. The 12,000-record CSV is well within the 100,000-character limit for multipart jobs.

---

## Anti-Pattern: Checking Only failedResults and Declaring Success

**What practitioners do:** After polling until `state == JobComplete`, retrieve `failedResults`, log the failure count, and declare the load successful if `failedResults` is empty or small.

**What goes wrong:** Records that ended up in batches that timed out after 20 retries appear in `unprocessedRecords` — not `failedResults`. A `failedResults` count of zero does not guarantee that all records were written. In high-volume loads during peak org load, hundreds or thousands of records can be silently lost in `unprocessedRecords` while `failedResults` appears clean.

**Correct approach:** Always retrieve all three endpoints after every job — `successfulResults`, `failedResults`, and `unprocessedRecords`. Verify that `count(successful) + count(failed) + count(unprocessed)` equals the total number of records uploaded. Treat any discrepancy as a pipeline error requiring investigation before declaring the load complete.
