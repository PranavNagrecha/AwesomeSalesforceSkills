# Examples: ETL vs API Data Patterns

## Example 1: Nightly ERP-to-Salesforce upsert with Bulk API 2.0

**Context:** An ERP is the master for customer accounts. About 300,000 accounts change per night. The team first built the sync as one REST call per record and exhausted the org's daily API requests.

**Solution:** An External ID field on Account, a control table in the ETL tool, and a Bulk API 2.0 upsert per run.

**External ID field:** `Account.ERP_Customer_Id__c`, deployable metadata in `metadata-examples.md`.

### Bulk API 2.0 upsert job, run by the ETL tool each night

```bash
#!/usr/bin/env bash
# Nightly Account upsert. Token is injected by the scheduler; never logged.
set -euo pipefail
BASE="https://MyDomainName.my.salesforce.com/services/data/v67.0/jobs/ingest"
AUTH="Authorization: Bearer ${SF_TOKEN:?missing}"

# Create the job. contentType CSV is the only valid value; upsert needs externalIdFieldName.
JOB_ID=$(curl -s "$BASE/" -H "$AUTH" -H "Content-Type: application/json" -X POST \
  -d '{"object":"Account","externalIdFieldName":"ERP_Customer_Id__c","contentType":"CSV","operation":"upsert","lineEnding":"LF"}' \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')

# Upload the delta extracted since the control table's last run (keep it under 100 MB).
curl -s "$BASE/$JOB_ID/batches/" -H "$AUTH" -H "Content-Type: text/csv" --data-binary @account_delta.csv -X PUT

# Close the upload.
curl -s "$BASE/$JOB_ID/" -H "$AUTH" -H "Content-Type: application/json" -d '{"state":"UploadComplete"}' -X PATCH

# Poll with backoff; every poll counts toward the daily API request allocation.
for wait in 30 60 120 240 480 900 900 900; do
  sleep "$wait"
  STATE=$(curl -s "$BASE/$JOB_ID/" -H "$AUTH" | python3 -c 'import json,sys; print(json.load(sys.stdin)["state"])')
  [ "$STATE" = "JobComplete" ] || [ "$STATE" = "Failed" ] || [ "$STATE" = "Aborted" ] && break
done

# Reconcile by external ID, not row order. Results are kept for 7 days.
curl -s "$BASE/$JOB_ID/failedResults/" -H "$AUTH" -H "Accept: text/csv" > "failed_$JOB_ID.csv"
curl -s "$BASE/$JOB_ID/unprocessedrecords/" -H "$AUTH" -H "Accept: text/csv" > "unprocessed_$JOB_ID.csv"
echo "$JOB_ID $STATE"
```

The ETL tool advances the control table only when `STATE` is `JobComplete` and the failed file holds no rows it cannot retry. The CSV `account_delta.csv` is sorted by parent key when the object is a child (for example Contacts by `Account.ERP_Customer_Id__c`).

**Grounding:** Job URIs, request body, `UploadComplete`, `failedResults`, and `unprocessedrecords` are from the Bulk API 2.0 Developer Guide (262), "Step 5: Bulk Upsert" and the result resources. The control-table loop is from Integration Patterns and Practices (262), "Batch Data Synchronization." The sleep schedule is an illustrative choice, not a Salesforce figure.

**Why it works:** The whole delta moves in one job instead of 300,000 requests. The job's calls still count toward the API request allocation, so the poll uses backoff.

---

## Example 2: Small-volume real-time profile sync

**Context:** A commerce platform must update a customer's Contact in Salesforce within seconds of a profile change. A burst can carry up to a few dozen changes.

**Solution:** The platform emits a webhook. Middleware groups changes that arrive together and calls sObject Collections upsert by external ID.

```http
PATCH /services/data/v67.0/composite/sobjects/Contact/Commerce_Profile_Id__c
Content-Type: application/json
Authorization: Bearer [REDACTED]

{
  "allOrNone": false,
  "records": [
    { "attributes": { "type": "Contact" }, "Commerce_Profile_Id__c": "CP-10041", "MailingCity": "Austin", "Email": "r.diaz@example.com" },
    { "attributes": { "type": "Contact" }, "Commerce_Profile_Id__c": "CP-10077", "MailingCity": "Denver" }
  ]
}
```

**Grounding:** REST API Developer Guide (262), "sObject Collections": up to 200 records per request, and the entire request counts as a single call. `Commerce_Profile_Id__c` must be an External ID field on Contact.

**Why it works:** Per-record latency needs an API pattern. Grouping a burst into one Collections call keeps request counts low without introducing a batch window.
