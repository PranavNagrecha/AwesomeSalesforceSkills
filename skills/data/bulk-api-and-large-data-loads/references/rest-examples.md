# REST Examples: Bulk API 2.0 Ingest, Query, and a Bulk API 1.0 Serial Job

Complete request and response bodies for one upsert pipeline, one query extract, and the Bulk API 1.0 serial fallback. Resource paths, body properties, and response fields come from the Bulk API 2.0 and Bulk API Developer Guide, Version 67.0 (api_asynch.pdf). IDs and tokens below are placeholders. Store the request bodies in the integration repo, for example under `bulk/contact_upsert/`.

## 1. Create the upsert job (CRLF file from a Windows export)

`POST /services/data/v67.0/jobs/ingest` with `Authorization: Bearer <token>` and `Content-Type: application/json`.

File: `bulk/contact_upsert/create_job.json`

```json
{
  "object": "Contact",
  "operation": "upsert",
  "externalIdFieldName": "Legacy_Id__c",
  "contentType": "CSV",
  "columnDelimiter": "COMMA",
  "lineEnding": "CRLF"
}
```

Response (abridged to the fields the pipeline reads):

```json
{
  "id": "750XXEXAMPLEJOB01",
  "operation": "upsert",
  "object": "Contact",
  "state": "Open",
  "externalIdFieldName": "Legacy_Id__c",
  "concurrencyMode": "Parallel",
  "contentType": "CSV",
  "apiVersion": 67.0,
  "jobType": "V2Ingest",
  "contentUrl": "services/data/v67.0/jobs/ingest/750XXEXAMPLEJOB01/batches",
  "lineEnding": "CRLF",
  "columnDelimiter": "COMMA"
}
```

`concurrencyMode` comes back `Parallel` because Bulk API 2.0 supports no other mode.

## 2. Upload the CSV (one PUT, at most 100 MB raw)

`PUT /services/data/v67.0/jobs/ingest/750XXEXAMPLEJOB01/batches` with `Content-Type: text/csv`. The header row uses API names and the external ID column.

```text
Legacy_Id__c,FirstName,LastName,Email,AccountId
C-000001,Ana,Ruiz,ana.ruiz@example.com,001XXEXAMPLEACC01
C-000002,Raj,Patel,raj.patel@example.com,001XXEXAMPLEACC01
```

The response is `201 Created` with no body. Sorting rows by `AccountId` keeps contacts of one account in the same batch.

## 3. Close the upload

`PATCH /services/data/v67.0/jobs/ingest/750XXEXAMPLEJOB01/`

File: `bulk/contact_upsert/upload_complete.json`

```json
{ "state": "UploadComplete" }
```

The response repeats the job with `"state": "UploadComplete"`.

## 4. Poll until a terminal state

`GET /services/data/v67.0/jobs/ingest/750XXEXAMPLEJOB01/` with backoff. Stop on `JobComplete`, `Failed`, or `Aborted`.

```json
{
  "id": "750XXEXAMPLEJOB01",
  "operation": "upsert",
  "object": "Contact",
  "state": "JobComplete",
  "concurrencyMode": "Parallel",
  "jobType": "V2Ingest",
  "lineEnding": "CRLF",
  "columnDelimiter": "COMMA",
  "numberRecordsProcessed": 2,
  "numberRecordsFailed": 1,
  "retries": 0,
  "totalProcessingTime": 886,
  "apiActiveProcessingTime": 813,
  "apexProcessingTime": 619
}
```

## 5. Pull all three result sets and reconcile

- `GET .../jobs/ingest/750XXEXAMPLEJOB01/successfulResults/` returns CSV starting `"sf__Id","sf__Created",...`.
- `GET .../jobs/ingest/750XXEXAMPLEJOB01/failedResults/` returns CSV starting `"sf__Id","sf__Error",...` (sf__Id on failed rows is available in API 53.0 and later).
- `GET .../jobs/ingest/750XXEXAMPLEJOB01/unprocessedrecords/` returns the original rows that were never processed (failed or aborted jobs).

Reconcile with this rule before marking the run complete: rows in successful + failed + unprocessed = rows uploaded. Resubmit failed and unprocessed rows in a new job after fixing the cause. Results stay retrievable for 7 days.

## 6. Small payloads: multipart create (100,000 characters or less)

`POST /services/data/v67.0/jobs/ingest` with `Content-Type: multipart/form-data; boundary=BOUNDARY`. The upload completes automatically, so no PATCH is needed.

```text
--BOUNDARY
Content-Type: application/json
Content-Disposition: form-data; name="job"

{"object":"Contact","contentType":"CSV","operation":"insert","lineEnding":"LF"}
--BOUNDARY
Content-Type: text/csv
Content-Disposition: form-data; name="content"; filename="content"

FirstName,LastName,Email
Lee,Chen,lee.chen@example.com
--BOUNDARY--
```

## 7. Query job for a large extract

`POST /services/data/v67.0/jobs/query`

```json
{
  "operation": "query",
  "query": "SELECT Id, Name, Industry, LastModifiedDate FROM Account WHERE LastModifiedDate = LAST_N_DAYS:30",
  "contentType": "CSV",
  "columnDelimiter": "COMMA",
  "lineEnding": "LF"
}
```

When the job is `JobComplete`, page through results with `GET .../jobs/query/<jobId>/results?maxRecords=50000`, then `...?locator=<value>&maxRecords=50000`. Take the locator only from the `Sforce-Locator` response header and stop when its value is the string `null`. Query jobs do not consume the 15,000-batch allocation.

## 8. Fallback for proven lock contention: Bulk API 1.0 serial job

Bulk API 2.0 cannot run serially. When sorting by parent still leaves lock failures, create that one load as a Bulk API 1.0 job. `POST /services/async/67.0/job` with the `X-SFDC-Session` header and `Content-Type: application/xml`.

File: `bulk/account_team_serial/create_job.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<jobInfo xmlns="http://www.force.com/2009/06/asyncapi/dataload">
    <operation>insert</operation>
    <object>AccountTeamMember</object>
    <concurrencyMode>Serial</concurrencyMode>
    <contentType>CSV</contentType>
</jobInfo>
```

UNVERIFIED (2026-10-03): the guide's create-job sample omits `concurrencyMode`, and it documents the field on JobInfo without stating whether element order is enforced in the request; the order above follows the order fields appear in the guide's response sample. In Bulk API 1.0 you create batches yourself (up to 10,000 records and 10 MB per batch) and close the job with `<state>Closed</state>`.
