# Examples — Bulk API 2.0 Patterns (Integration)

## Example 1: Middleware closes the ingest job explicitly

**Context:** A Python worker creates a Bulk API 2.0 ingest job and streams a CSV from object storage. Operators report jobs stuck for hours with state `Open`.

**Problem:** The worker uploaded all `PUT` chunks but never notified Salesforce that uploads finished, so processing never began.

**Solution:**

```python
import json
import time
import requests

def close_ingest_job(instance_url: str, api_version: str, token: str, job_id: str) -> None:
    url = f"{instance_url}/services/data/{api_version}/jobs/ingest/{job_id}/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    resp = requests.patch(url, headers=headers, data=json.dumps({"state": "UploadComplete"}), timeout=120)
    resp.raise_for_status()


def poll_until_terminal(instance_url: str, api_version: str, token: str, job_id: str) -> dict:
    url = f"{instance_url}/services/data/{api_version}/jobs/ingest/{job_id}/"
    headers = {"Authorization": f"Bearer {token}"}
    while True:
        body = requests.get(url, headers=headers, timeout=120).json()
        state = body.get("state")
        if state in ("JobComplete", "Failed", "Aborted"):
            return body
        time.sleep(15)
```

**Why it works:** The Bulk API 2.0 ingest lifecycle requires `UploadComplete` for every non-multipart job; polling only begins after that transition is accepted.

---

## Example 2: Ordered Account then Contact loads

**Context:** A student information system pushes `Account` (district) rows then `Contact` rows that reference `AccountId`.

**Problem:** Both jobs were scheduled in parallel. Contact batches intermittently failed foreign-key validation under load.

**Solution:**

1. Create and run the Account ingest job through `JobComplete`; download `failedResults` and reconcile before continuing.
2. Persist the Salesforce job ID and final success counts in the orchestration database.
3. Only then create the Contact ingest job, embedding validated `AccountId` values from the first pass.

**Why it works:** Salesforce does not guarantee cross-job ordering; the integration layer must gate child work on verified parent completion.

---

## Anti-Pattern: Full-file replay after partial failure

**What practitioners do:** On any `numberRecordsFailed > 0`, resubmit the entire source CSV in a new insert job.

**What goes wrong:** Duplicate records unless every column is idempotent and uniqueness is enforced elsewhere; wasted API rows against daily limits.

**Correct approach:** Build the next job from `failedResults` / `unprocessedRecords`, prefer `upsert` with a stable external ID, and keep successful row IDs in the source system’s mapping table.
