# Examples — Real-Time vs Batch Integration

## Example 1: Order Sync — Deciding Real-Time vs Nightly Batch for ERP Integration

**Context:** A retail company creates Salesforce Orders and needs them reflected in an SAP ERP system. The integration team initially proposed a trigger-based synchronous callout on Order insert. Peak order volume is 8,000 orders/day clustered in a 4-hour window (roughly 2,000 orders/hour, ~34/minute).

**Problem:** At 34 orders per minute, each triggering a synchronous callout, the team hit governor limits during peak load: up to 34 concurrent Apex transactions each consuming a callout slot, and occasional 120-second timeouts when SAP was under load. Some orders failed silently when the callout timed out and the error was swallowed. The synchronous pattern also caused the Order save to block for the full callout duration, degrading the user experience in the order entry UI.

**Solution:**

Instead of a synchronous callout in the trigger, the team published a Platform Event on Order insert and had an external MuleSoft listener consume events and write to SAP asynchronously:

```apex
// OrderTrigger.trigger — publish event instead of callout
trigger OrderTrigger on Order (after insert) {
    List<Order_Sync_Event__e> events = new List<Order_Sync_Event__e>();
    for (Order o : Trigger.new) {
        events.add(new Order_Sync_Event__e(
            Order_Id__c    = o.Id,
            Order_Number__c = o.OrderNumber,
            Status__c      = o.Status,
            Total_Amount__c = o.TotalAmount
        ));
    }
    List<Database.SaveResult> results = EventBus.publish(events);
    // Log any publish failures — these are rare but must be monitored
    for (Database.SaveResult sr : results) {
        if (!sr.isSuccess()) {
            // Insert to a custom error log or use Platform Event for monitoring
            System.debug('Event publish failed: ' + sr.getErrors());
        }
    }
}
```

The MuleSoft CometD subscriber processes events and upserts to SAP using SAP's BAPI interface. Replay IDs allow it to recover from short outages without data loss within the 72-hour window.

**Why it works:** The trigger never blocks waiting for SAP. Peak volume (2,000/hour) is well within Platform Event throughput. MuleSoft handles SAP-side retry without coupling it to the Salesforce transaction. The 72-hour replay window is sufficient for any SAP maintenance window the company schedules.

---

## Example 2: High-Volume Customer Master Sync — Bulk API 2.0 Nightly Batch

**Context:** A financial services firm needs to keep 3 million customer Account records synchronized between a legacy CRM and Salesforce. The legacy system exports a full delta file nightly containing up to 150,000 changed records. Latency tolerance is 8 hours (records updated by EOD must be visible in Salesforce before the next business day opens).

**Problem:** An earlier implementation used REST API individual record upserts from a Python script. At 150,000 records, the script took over 4 hours and consumed API daily limits (100,000 REST calls/24hr for Professional edition), causing failures for other integrations. The script also had no atomic rollback — partial failures left Salesforce in an inconsistent state mid-run.

**Solution:**

Replace individual REST upserts with a Bulk API 2.0 upsert job:

```python
# Simplified Bulk API 2.0 ingest pattern (stdlib requests + csv)
import csv, requests, time, io

SF_INSTANCE = "https://myorg.my.salesforce.com"
ACCESS_TOKEN = "<token>"  # obtained via OAuth 2.0 JWT flow

# 1. Create the job
job_resp = requests.post(
    f"{SF_INSTANCE}/services/data/v61.0/jobs/ingest/",
    headers={"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"},
    json={
        "object": "Account",
        "operation": "upsert",
        "externalIdFieldName": "Legacy_CRM_Id__c",
        "contentType": "CSV",
        "lineEnding": "LF"
    }
)
job_id = job_resp.json()["id"]

# 2. Upload the CSV batch (up to 150 MB per upload)
with open("customer_delta.csv", "rb") as f:
    requests.put(
        f"{SF_INSTANCE}/services/data/v61.0/jobs/ingest/{job_id}/batches",
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "text/csv"},
        data=f
    )

# 3. Close the job to trigger processing
requests.patch(
    f"{SF_INSTANCE}/services/data/v61.0/jobs/ingest/{job_id}/",
    headers={"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"},
    json={"state": "UploadComplete"}
)

# 4. Poll for completion
while True:
    status = requests.get(
        f"{SF_INSTANCE}/services/data/v61.0/jobs/ingest/{job_id}/",
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
    ).json()["state"]
    if status in ("JobComplete", "Failed", "Aborted"):
        break
    time.sleep(30)

# 5. Retrieve and log failed records for re-queue
failed = requests.get(
    f"{SF_INSTANCE}/services/data/v61.0/jobs/ingest/{job_id}/failedResults/",
    headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
)
# Parse failed CSV and write to error log for next cycle re-queue
```

The job is scheduled at 01:00 local time, well outside business hours, to avoid resource contention.

**Why it works:** Bulk API 2.0 processes records in parallel server-side, completing 150,000 records in under 20 minutes. It does not count against the REST API daily limit. Failed records are captured in the results CSV and re-queued in the next nightly run. The external ID (`Legacy_CRM_Id__c`) makes every upsert idempotent — re-running the same batch is safe.

---

## Anti-Pattern: Using Apex Callouts in Triggers for Bulk Operations

**What practitioners do:** Place `@future(callout=true)` methods directly in `after insert` triggers so that every inserted record fires an outbound HTTP call to an external system, assuming this is "real-time" integration.

**What goes wrong:** At moderate volume (e.g., a data load of 5,000 records via Data Loader), 5,000 `@future` jobs are enqueued. The async queue saturates, future jobs are delayed by minutes to hours, and the org hits the 250,000 async Apex limit per 24-hour rolling window. The external system receives a thundering herd of individual HTTP requests that it cannot handle. If the external endpoint is down, there is no retry mechanism and records are silently skipped.

**Correct approach:** Use Platform Events to buffer the change notifications. The external system subscribes and processes at its own rate, with built-in replay for downtime recovery. For truly high-volume scenarios, collect deltas and use Bulk API 2.0 at scheduled intervals instead of one-request-per-record.
