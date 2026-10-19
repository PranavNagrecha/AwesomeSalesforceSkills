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

**What the LLM generates:** CSV content with a `lineEnding` that does not match the file, label-style headers, blank cells meant to clear fields, or values padded with spaces.

**Why it happens:** Models write CSV as plain text and do not apply the Bulk API 2.0 rules: UTF-8, a declared line ending that matches the file, a header row of API names, `#N/A` for null, and no trimming.

**Correct pattern:**

```text
Bulk API 2.0 CSV requirements (Prepare CSV Files):
- Encoding: UTF-8
- Line endings: LF (default) or CRLF, and the job's lineEnding must match the file
- Delimiter: comma by default; backquote, caret, pipe, semicolon, tab via columnDelimiter
- Header row: field API names; header up to 32,000 characters
- Quoting: wrap values containing the delimiter or line endings in double quotes
- Null: empty values are ignored on update; #N/A sets null
- Whitespace: values aren't trimmed; a space next to a double quote fails the row

Example header for Account upsert:
External_Id__c,Name,BillingCity,BillingState
```

**Detection hint:** Header cells with spaces (labels, not API names), upserts whose header lacks the `externalIdFieldName` column, a job body without `lineEnding` for files produced on Windows, or blank cells in an update file that is meant to clear values.

---

## Anti-Pattern 3: Not Using the Sforce-Locator Header for Query Job Pagination

**What the LLM generates:** "Download the query results from GET /jobs/query/{id}/results/" as a single call without handling pagination. For large query results, the response includes an `Sforce-Locator` header that must be used to retrieve subsequent pages.

**Why it happens:** Small-result-set examples dominate training data. The pagination mechanism (Sforce-Locator header, not nextRecordsUrl like REST SOQL) is specific to Bulk API 2.0 query jobs and is often omitted.

**Correct pattern:**

```text
Bulk API 2.0 query result pagination:

1. GET /services/data/vXX.0/jobs/query/{id}/results
   Response headers include:
   - Sforce-Locator: <locator-value>, or the string "null" on the last set
   - Sforce-NumberOfRecords: <count in this set>

2. If Sforce-Locator is not the string "null":
   GET /services/data/vXX.0/jobs/query/{id}/results?locator=<locator-value>

3. Repeat until Sforce-Locator is the string "null"

Without maxRecords the server picks a default set size; pass maxRecords
when large sets time out on the client. Never construct a locator.
```

**Detection hint:** Flag Bulk API query examples that call the results endpoint only once without checking the `Sforce-Locator` header. Look for missing pagination loops in query job code.

---

## Anti-Pattern 4: Omitting the Job Close Step After CSV Upload

**What the LLM generates:** "Upload your CSV with PUT to the batches endpoint," then polling for results, with no PATCH setting the job state to `UploadComplete`.

**Why it happens:** Many examples show only the upload. In Bulk API 2.0 a standard job stays `Open` until the client sets `"state": "UploadComplete"`; only multipart jobs complete the upload automatically.

**Correct pattern:**

```text
Bulk API 2.0 ingest job lifecycle:

1. Create job: POST /services/data/vXX.0/jobs/ingest/
   Body: {"object": "Account", "operation": "insert", "contentType": "CSV"}
   State: Open

2. Upload CSV: PUT /services/data/vXX.0/jobs/ingest/{id}/batches/
   Content-Type: text/csv
   (Total job data at most 150 MB after base64, about 100 MB raw)

3. Close job: PATCH /services/data/vXX.0/jobs/ingest/{id}/
   Body: {"state": "UploadComplete"}
   *** THIS STEP IS REQUIRED — processing does not start without it ***

4. Poll status: GET /services/data/vXX.0/jobs/ingest/{id}/
   Wait for state = "JobComplete" or "Failed"
```

**Detection hint:** Flag Bulk API 2.0 ingest examples that do not include the PATCH request with `"state": "UploadComplete"`. Search for missing job close step between upload and polling.

---

## Anti-Pattern 5: Using PK Chunking Syntax in Bulk API 2.0 Query Jobs

**What the LLM generates:** "Enable PK Chunking by setting the Sforce-Enable-PKChunking header on your Bulk API 2.0 query job."

**Why it happens:** PK chunking is widely discussed for large exports, and the header is a Bulk API v1 mechanism. The guide's comparison table says Bulk API 2.0 "automatically performs PK chunking," while in v1 it "is manually invoked and configured."

**Correct pattern:**

```text
PK chunking:
- Bulk API v1: manual. Sforce-Enable-PKChunking header (chunkSize, parent, startRow).
- Bulk API 2.0: automatic. No header; page through results with Sforce-Locator.

Do not send v1 headers to /services/data/vXX.X/jobs/query endpoints.
```

**Detection hint:** Flag any `Sforce-Enable-PKChunking` header used with a `/services/data/vXX.0/jobs/query/` endpoint (v2). PK Chunking headers belong to `/services/async/` (v1) only.

---

## Anti-Pattern 6: Treating 150 MB as a Per-Request Limit

**What the LLM generates:** "Split the file into 100 MB chunks and PUT each chunk to the same job."

**Why it happens:** Bulk API v1 batches are uploaded one by one, and models carry that shape into v2.

**Correct pattern:** The Bulk API 2.0 guide allows up to 150 MB per job after base64 encoding, so upload no more than about 100 MB of raw CSV per job. Split larger files into separate jobs and reconcile each job.

**Detection hint:** A loop that PUTs several chunks to one `jobs/ingest/{id}/batches` URL whose combined size exceeds 100 MB.
