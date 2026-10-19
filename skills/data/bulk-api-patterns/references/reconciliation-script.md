# Reconciliation Script — Prove Every Row of an Ingest Job Is Accounted For

Run this after each Bulk API 2.0 ingest job reaches a terminal state. It reads the job info, downloads the result sets that apply to that state, and compares the counts with the source file. Stdlib only.

```python
#!/usr/bin/env python3
"""reconcile_ingest_job.py --instance URL --token TOKEN --job JOB_ID --source file.csv"""
import argparse
import csv
import io
import json
import sys
import urllib.request

API = "v67.0"


def get(url: str, token: str, accept: str) -> bytes:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "Accept": accept})
    with urllib.request.urlopen(req) as resp:
        return resp.read()


def csv_rows(raw: bytes) -> int:
    text = raw.decode("utf-8")
    if not text.strip():
        return 0
    return sum(1 for _ in csv.reader(io.StringIO(text))) - 1  # minus header


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instance", required=True)
    ap.add_argument("--token", required=True)
    ap.add_argument("--job", required=True)
    ap.add_argument("--source", required=True)
    a = ap.parse_args()

    base = f"{a.instance}/services/data/{API}/jobs/ingest/{a.job}"
    info = json.loads(get(base, a.token, "application/json"))
    state = info["state"]
    if state not in ("JobComplete", "Failed", "Aborted"):
        print(f"Job is {state}; wait for a terminal state.")
        return 2

    with open(a.source, newline="", encoding="utf-8") as fh:
        uploaded = sum(1 for _ in csv.reader(fh)) - 1

    ok = csv_rows(get(f"{base}/successfulResults/", a.token, "text/csv"))
    bad = csv_rows(get(f"{base}/failedResults/", a.token, "text/csv"))
    unprocessed = 0
    if state in ("Failed", "Aborted"):
        unprocessed = csv_rows(get(f"{base}/unprocessedrecords/", a.token, "text/csv"))

    print(f"state={state} uploaded={uploaded} successful={ok} failed={bad} unprocessed={unprocessed}")
    print(f"job info: processed={info.get('numberRecordsProcessed')} failed={info.get('numberRecordsFailed')}")
    if ok + bad + unprocessed != uploaded:
        print("MISMATCH: rows are unaccounted for; do not delete the source file.")
        return 1
    if bad or unprocessed:
        print("Resubmit failed and unprocessed rows in a NEW job after fixing their causes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

## Why each step is there

| Step | Reason (Bulk API 2.0 guide) |
|---|---|
| Wait for a terminal state | Results describe a finished job; `JobComplete` can still contain failed rows |
| Read `unprocessedrecords/` only for `Failed` or `Aborted` | The resource returns unprocessed records for failed or aborted jobs |
| Lowercase `unprocessedrecords` path | That is the documented URI |
| Compare with the source file | The guide says not to delete local CSV data until every record is confirmed processed |
| Resubmit in a new job | The guide's recovery step is a new ingest job with only the failed and unprocessed records |
| Run within 7 days | Ingest job results can be retrieved for 7 days after completion |

## Example output

```text
state=Failed uploaded=250000 successful=180000 failed=1200 unprocessed=68800
job info: processed=181200 failed=1200
Resubmit failed and unprocessed rows in a NEW job after fixing their causes.
```

A `Failed` job like this one stopped after a batch failed 20 retries or the daily record limit was reached; the 68,800 rows that never ran are only visible through `unprocessedrecords/`.
