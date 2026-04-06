# LLM Anti-Patterns — Bulk API Patterns

Common mistakes AI coding assistants make when generating or advising on Salesforce Bulk API 2.0 REST implementation patterns.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using Bulk API v1 Endpoints When v2 Is Intended

**What the LLM generates:** REST calls to `/services/async/XX.0/job` (Bulk API v1) when the context clearly calls for Bulk API 2.0, which uses `/services/data/vXX.0/jobs/ingest/` or `/services/data/vXX.0/jobs/query/`.

**Why it happens:** Bulk API v1 has years more training data than v2. LLMs default to the older endpoint format, especially when generating curl examples or HTTP client code.

**Correct pattern:**

```text
Bulk API 2.0 endpoints:

Ingest (insert/update/upsert/delete/hardDelete):
  POST /services/data/vXX.0/jobs/ingest/        (create job)
  PUT  /services/data/vXX.0/jobs/ingest/{id}/batches/  (upload CSV)
  PATCH /services/data/vXX.0/jobs/ingest/{id}/  (close/abort job)
  GET  /services/data/vXX.0/jobs/ingest/{id}/   (check status)

Query:
  POST /services/data/vXX.0/jobs/query/          (create query job)
  GET  /services/data/vXX.0/jobs/query/{id}/     (check status)
  GET  /services/data/vXX.0/jobs/query/{id}/results/  (download results)

Bulk API v1 (legacy):
  POST /services/async/XX.0/job  (different URL path entirely)
```

**Detection hint:** Flag any Bulk API code using `/services/async/` when the recommendation is for Bulk API 2.0. Search for `async` in the endpoint URL path.

---

## Anti-Pattern 2: Wrong CSV Format for Bulk API 2.0 Uploads

**What the LLM generates:** CSV files with wrong line endings (LF-only on Windows clients), BOM characters, or missing headers, which cause parsing failures or silent data corruption in Bulk API 2.0.

**Why it happens:** LLMs generate CSV content as plain text without specifying the exact format requirements that Bulk API 2.0 enforces: UTF-8 encoding, CRLF or LF line endings, comma delimiter, and a mandatory header row matching field API names.

**Correct pattern:**

```text
Bulk API 2.0 CSV requirements:
- Encoding: UTF-8 (no BOM)
- Line endings: LF or CRLF (both accepted)
- Delimiter: comma by default (configurable via columnDelimiter in job creation)
- Header row: REQUIRED, must use field API names (not labels)
- Quoting: fields containing commas, newlines, or double-quotes must be quoted
- Double-quote escaping: use "" (two double-quotes) inside a quoted field

Example header for Account upsert:
External_Id__c,Name,BillingCity,BillingState

Common mistakes:
- Using field labels instead of API names in headers
- Including the Salesforce Id column for insert operations (omit it)
- Missing External_Id__c in header for upsert operations
```

**Detection hint:** Check CSV header rows for spaces (likely labels, not API names). Flag inserts that include an `Id` column or upserts missing the external ID field.

---

## Anti-Pattern 3: Not Using the Sforce-Locator Header for Query Job Pagination

**What the LLM generates:** "Download the query results from GET /jobs/query/{id}/results/" as a single call without handling pagination. For large query results, the response includes an `Sforce-Locator` header that must be used to retrieve subsequent pages.

**Why it happens:** Small-result-set examples dominate training data. The pagination mechanism (Sforce-Locator header, not nextRecordsUrl like REST SOQL) is specific to Bulk API 2.0 query jobs and is often omitted.

**Correct pattern:**

```text
Bulk API 2.0 query result pagination:

1. GET /services/data/vXX.0/jobs/query/{id}/results/
   Response headers include:
   - Sforce-Locator: <locator-value>  (present if more pages exist)
   - Sforce-NumberOfRecords: <count>

2. If Sforce-Locator is not "null":
   GET /services/data/vXX.0/jobs/query/{id}/results/?locator=<locator-value>

3. Repeat until Sforce-Locator = "null"

Default page size: ~1 GB or system-determined row count per page.
Use maxRecords parameter to control page size if needed.
```

**Detection hint:** Flag Bulk API query examples that call the results endpoint only once without checking the `Sforce-Locator` header. Look for missing pagination loops in query job code.

---

## Anti-Pattern 4: Omitting the Job Close Step After CSV Upload

**What the LLM generates:** "Upload your CSV with PUT to the batches endpoint" and then immediately polling for results, without sending the PATCH request to change the job state from `UploadComplete` to signal processing should begin.

**Why it happens:** In Bulk API v1, closing a batch was implicit. In v2, the client must explicitly close the job (PATCH with `"state": "UploadComplete"`) before processing begins. Training data from v1 patterns omits this step.

**Correct pattern:**

```text
Bulk API 2.0 ingest job lifecycle:

1. Create job: POST /services/data/vXX.0/jobs/ingest/
   Body: {"object": "Account", "operation": "insert", "contentType": "CSV"}
   State: Open

2. Upload CSV: PUT /services/data/vXX.0/jobs/ingest/{id}/batches/
   Content-Type: text/csv
   (Can repeat for multiple uploads)

3. Close job: PATCH /services/data/vXX.0/jobs/ingest/{id}/
   Body: {"state": "UploadComplete"}
   *** THIS STEP IS REQUIRED — processing does not start without it ***

4. Poll status: GET /services/data/vXX.0/jobs/ingest/{id}/
   Wait for state = "JobComplete" or "Failed"
```

**Detection hint:** Flag Bulk API 2.0 ingest examples that do not include the PATCH request with `"state": "UploadComplete"`. Search for missing job close step between upload and polling.

---

## Anti-Pattern 5: Using PK Chunking Syntax in Bulk API 2.0 Query Jobs

**What the LLM generates:** "Enable PK Chunking by setting the Sforce-Enable-PKChunking header on your Bulk API 2.0 query job" when PK Chunking is only available in Bulk API v1, not v2.

**Why it happens:** PK Chunking is a frequently discussed optimization for large query exports. LLMs do not consistently distinguish between v1 and v2 feature availability, and PK Chunking is one of the features that did not carry over to v2.

**Correct pattern:**

```text
PK Chunking availability:
- Bulk API v1: SUPPORTED. Set Sforce-Enable-PKChunking: true header.
  Splits large queries into chunks based on record ID ranges.
- Bulk API 2.0: NOT SUPPORTED. The platform handles chunking internally.

If you need PK Chunking for very large query exports:
- Use Bulk API v1 for that specific job
- Or use Bulk API 2.0 and let the platform manage result pagination
  via the Sforce-Locator mechanism

Do not mix v1 headers (PKChunking) with v2 endpoints.
```

**Detection hint:** Flag any `Sforce-Enable-PKChunking` header used with a `/services/data/vXX.0/jobs/query/` endpoint (v2). PK Chunking headers belong to `/services/async/` (v1) only.
