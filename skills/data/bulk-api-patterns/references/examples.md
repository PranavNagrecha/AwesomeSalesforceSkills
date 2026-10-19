# Examples — Bulk API Patterns

## Example 1: Large Account Import Using Standard Ingest Job

**Context:** A data integration team needs to insert 800,000 Account records from a legacy CRM into Salesforce. The source system exports a UTF-8 CSV with LF line endings and comma delimiters. The team needs a reference implementation for the full Bulk API 2.0 ingest lifecycle.

**Problem:** The team previously used REST Composite batches of 200 records, requiring 4,000 HTTP calls and regularly hitting API call limits. They also had no integrity check, so rows from a failed job were never resubmitted.

**Solution:**

```
Step 1 — Authenticate and obtain OAuth 2.0 bearer token.

Step 2 — Size the work: the CSV is 240 MB raw. A Bulk API 2.0 job takes at most
150 MB after base64 encoding (about 100 MB raw), so split into three files of
roughly 80 MB and create one job per file. Steps 3-8 run once per job.

Step 2a — Create the ingest job:
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

Step 3 — Upload this job's file (one file per job, under 100 MB raw):
PUT /services/data/v66.0/jobs/ingest/750R000000xxxxAAA/batches
Content-Type: text/csv
[file CSV body]

CSV format note: empty values are ignored on update; use "#N/A" to set a
field to null. Values aren't trimmed, so strip spaces in the export.

Step 4 — Signal upload complete (MANDATORY):
PATCH /services/data/v66.0/jobs/ingest/750R000000xxxxAAA
Content-Type: application/json
{ "state": "UploadComplete" }
State transitions to InProgress. Job never starts without this PATCH.

Step 5 — Poll every 30 seconds:
GET /services/data/v66.0/jobs/ingest/750R000000xxxxAAA
Stop when state is "JobComplete", "Failed", or "Aborted".

Step 6 — Retrieve results for each job (all three jobs ended JobComplete):
GET .../750R000000xxxxAAA/successfulResults/   → 264,900 rows
GET .../750R000000xxxxAAA/failedResults/       → 1,767 rows with sf__Error
(unprocessedrecords/ applies only to Failed or Aborted jobs)

Integrity check per job: successful + failed = rows uploaded to that job;
across the three jobs: 794,800 + 5,200 = 800,000

Step 7 — Inspect failedResults sf__Error values:
- 4,800 rows: "REQUIRED_FIELD_MISSING: [BillingCountry]" → fix source data
- 400 rows: "DUPLICATE_VALUE" → switch to upsert for these records

Step 8 — Create a NEW job for the 5,200 fixed rows. If any job had ended
Failed, add its unprocessedrecords rows to the resubmission too.
```

**Why it works:** One file per job keeps each job under the 150 MB base64 ceiling. The per-job reconciliation proves every uploaded row is accounted for, and reading `unprocessedrecords/` for any Failed job catches rows that never ran. Each error category gets its own root-cause fix before resubmission.

---

## Example 2: Bulk SOQL Export with Locator Pagination

**Context:** A data analyst needs to extract 4.2 million Opportunity records for an external analytics pipeline. The LDV guide suggests the Bulk API 2.0 query capability for queries that can return more than a million results. The analyst needs paginated CSV output that can be resumed if interrupted.

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
base_url = f"https://yourorg.my.salesforce.com/services/data/v66.0/jobs/query/{job_id}/results?maxRecords=50000"
headers = {"Authorization": f"Bearer {token}", "Accept": "text/csv"}

locator = None
page_num = 1

while True:
    url = base_url if locator is None else f"{base_url}&locator={locator}"
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
Result: ~85 sets × up to 50,000 records (capped by maxRecords) = 4.2M records.
A locator does not change while the job exists, so a saved locator resumes the loop.
```

**Why it works:** Bulk API 2.0 query jobs perform PK chunking automatically. `maxRecords` keeps each set small enough to download without a client timeout, and the `Sforce-Locator` value, compared as the string `null` for the end, lets an interrupted download resume from the last saved locator.

---

## Example 3: Multipart Upsert Job for Nightly ERP Integration

**Context:** An hourly ERP sync pushes the Contacts changed in the last hour, usually 300 to 800 rows (well under 100,000 characters of CSV), using an `ERP_Contact_Id__c` external ID field. The integration team wants fewer HTTP round-trips and no risk of forgetting the `UploadComplete` PATCH.

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

The guide: after you create a multipart job, the upload is completed for you automatically,
so no separate PATCH is needed. The pipeline checks the returned `state` and skips the PATCH.

**Why it works:** Multipart job creation removes the create-then-signal window for small datasets (100,000 characters or less). The client measures the CSV length first and falls back to the standard pattern when a backlog pushes it over the limit; a 12,000-row file at about 60 characters per row is 720,000 characters, far too big for multipart.

---

## Anti-Pattern: Checking Only failedResults and Declaring Success

**What practitioners do:** After polling until `state == JobComplete`, retrieve `failedResults`, log the failure count, and declare the load successful if `failedResults` is empty or small.

**What goes wrong:** A job can end `Failed` (a batch still failing after 20 retries, or the daily record limit reached), and then the remaining data isn't processed. Those rows are in `unprocessedrecords/`, not `failedResults`, so a clean `failedResults` proves nothing about a failed job.

**Correct approach:** Check the terminal state first. For `JobComplete`, verify successful plus failed equals rows uploaded. For `Failed` or `Aborted`, also read `unprocessedrecords/` and resubmit those rows in a new job. Treat any discrepancy as a pipeline error before declaring the load complete.
