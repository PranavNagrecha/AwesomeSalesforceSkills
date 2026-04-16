# Examples — Data Cloud Integration Strategy

## Example 1: Streaming Ingestion for Behavioral Event Data

**Context:** A SaaS company wants to ingest website clickstream events into Data Cloud to build real-time behavioral profiles for personalization.

**Problem:** The team initially built a batch CSV upload pipeline assuming they could upload individual event CSVs every 5 minutes. They discovered that bulk ingestion uses full-replace semantics — each batch overwrites the dataset — making incremental event ingestion destructive.

**Solution:**

Use the streaming Ingestion API with the events connector:

```python
import requests

def ingest_event(dc_token: str, dc_base: str, connector_name: str, events: list):
    """Stream events to Data Cloud Ingestion API (streaming mode)."""
    headers = {
        "Authorization": f"Bearer {dc_token}",
        "Content-Type": "application/json"
    }
    payload = {"data": events}  # max 200 KB total
    resp = requests.post(
        f"{dc_base}/api/v1/ingest/connected-sources/{connector_name}/data",
        headers=headers,
        json=payload
    )
    resp.raise_for_status()
    return resp.json()

# Events batch (each call <= 200 KB)
events = [
    {"eventId": "e1", "userId": "u123", "pageUrl": "/product/abc", "eventTime": "2026-04-16T10:00:00Z"},
    {"eventId": "e2", "userId": "u123", "pageUrl": "/cart", "eventTime": "2026-04-16T10:01:00Z"}
]
result = ingest_event(dc_token, dc_base, "WebClickstream", events)
```

**Why it works:** Streaming ingestion appends individual event records asynchronously every ~3 minutes. Bulk ingestion's full-replace semantics would overwrite all previous events on each batch — catastrophically wrong for event log data.

---

## Example 2: Bulk Ingestion for Historical Customer Record Load

**Context:** A retail company is onboarding to Data Cloud and needs to load 5 years of historical customer purchase records (15 million rows) from a data warehouse as CSV files.

**Problem:** The team tried to load all 15 million rows in a single CSV file (2 GB) and hit the 150 MB per-file limit. The job failed with no clear error.

**Solution:**

1. Split the 15 million rows into chunks of 1 million rows each, producing ~14 files averaging ~100 MB each.
2. Verify each file is UTF-8 encoded, comma-delimited, RFC 4180 compliant.
3. Create a Bulk Ingestion API job and upload all files in one job (max 100 files per job).
4. Monitor job status until processing completes.

```python
import requests

def create_bulk_job(dc_token: str, dc_base: str, connector_name: str) -> str:
    headers = {"Authorization": f"Bearer {dc_token}", "Content-Type": "application/json"}
    resp = requests.post(
        f"{dc_base}/api/v1/ingest/jobs/bulk",
        headers=headers,
        json={"sourceName": connector_name}
    )
    return resp.json()["id"]

def upload_file(dc_token: str, dc_base: str, job_id: str, csv_path: str):
    with open(csv_path, "rb") as f:
        requests.put(
            f"{dc_base}/api/v1/ingest/jobs/bulk/{job_id}/batches",
            headers={"Authorization": f"Bearer {dc_token}", "Content-Type": "text/csv"},
            data=f
        )
```

**Why it works:** Files split to <150 MB each. 100-file job limit accommodated. Bulk ingestion is designed for full dataset loads, not event-stream appending.

---

## Anti-Pattern: Using Streaming Ingestion Assuming Sub-Minute Latency

**What practitioners do:** Build a real-time personalization engine that reads Data Cloud unified profiles, assuming streaming ingestion makes profile data available within seconds of an event occurring.

**What goes wrong:** Streaming ingestion processes batches asynchronously approximately every 3 minutes. After ingestion, data must traverse DSO → DLO → DMO before it is available for segmentation — additional lag. Real-time personalization within seconds is not achievable with Ingestion API streaming. The pipeline introduces minutes, not seconds, of latency.

**Correct approach:** For sub-minute personalization, query the source system directly and use Data Cloud for aggregated profile analytics and batch activation, not as a real-time lookup cache.
