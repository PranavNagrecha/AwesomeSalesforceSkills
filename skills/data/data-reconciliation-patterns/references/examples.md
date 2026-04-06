# Examples — Data Reconciliation Patterns

## Example 1: Count-Level Post-Load Reconciliation with SOQL

**Context:** A nightly batch job loads 50,000 Account records from an ERP into Salesforce via Bulk API 2.0. The next morning, users report that some accounts are missing.

**Problem:** The Bulk API job completed with status `JobComplete` but no one checked `failedResults`. Some rows silently failed due to validation rule violations. Without a count check, the discrepancy went undetected for hours.

**Solution:**

```soql
-- Run after each bulk load job completes.
-- Replace 2026-04-04T22:00:00Z with the job start time.
SELECT COUNT()
FROM Account
WHERE ERP_Account_Id__c != null
  AND SystemModstamp >= 2026-04-04T22:00:00Z
```

```python
# Pseudocode: compare counts after job
sf_count = sf.query("SELECT COUNT() FROM Account WHERE ERP_Account_Id__c != null AND SystemModstamp >= :job_start")["totalSize"]
erp_count = erp_db.execute("SELECT COUNT(*) FROM accounts WHERE updated_at >= :job_start").fetchone()[0]

if sf_count != erp_count:
    # Trigger investigation: fetch failedResults from the Bulk API job
    failed = bulk_client.get_failed_results(job_id)
    log_discrepancy(sf_count, erp_count, failed)
```

**Why it works:** `SELECT COUNT()` in SOQL returns an aggregate with no row limit and runs in system context when executed via the integration user. Comparing it to the source count immediately surfaces missing rows.

---

## Example 2: Bulk API 2.0 Upsert with External ID

**Context:** An HR system syncs employee contact records to Salesforce Contact objects daily. The HR system has a stable `employee_id` field that must drive idempotent upserts.

**Problem:** Initial implementation used REST POST to insert new records, causing duplicates on retry after a timeout — the first insert had succeeded but the caller didn't know.

**Solution:**

```http
POST /services/data/v63.0/jobs/ingest
Content-Type: application/json

{
  "object": "Contact",
  "operation": "upsert",
  "externalIdFieldName": "HR_Employee_Id__c",
  "contentType": "CSV",
  "lineEnding": "CRLF"
}
```

```csv
HR_Employee_Id__c,FirstName,LastName,Email
EMP-1001,Jane,Smith,jane.smith@example.com
EMP-1002,John,Doe,john.doe@example.com
```

```python
# After job reaches JobComplete, always check failedResults
failed_url = f"/services/data/v63.0/jobs/ingest/{job_id}/failedResults"
failed = sf_request("GET", failed_url)
if failed.strip():
    rows = list(csv.DictReader(failed.splitlines()))
    for row in rows:
        log_error(row["sf__Id"], row["sf__Error"])
```

**Why it works:** The `externalIdFieldName` parameter instructs Bulk API 2.0 to match incoming rows against `HR_Employee_Id__c`. If a Contact with that value exists, it is updated. If not, it is inserted. The operation is idempotent — retrying on timeout is safe as long as `HR_Employee_Id__c` is unique and the Unique checkbox is set on the field.

---

## Example 3: Field-Level Hash Reconciliation in Apex

**Context:** An integration syncs Account billing addresses from a CRM to Salesforce. After several weeks, customer service reports that some addresses in Salesforce no longer match the source system, but it is unclear which records drifted.

**Problem:** Running a full export of all accounts to compare field-by-field is expensive. The team needs to identify only the diverged records.

**Solution:**

```apex
// Generate a SHA-256 hash of key address fields for a single Account.
// Call this from a batch Apex job or a scheduled integration check.
public static String buildAddressHash(Account acc) {
    String raw = String.join(
        new List<String>{
            (acc.BillingStreet  != null ? acc.BillingStreet.trim().toLowerCase()  : ''),
            (acc.BillingCity    != null ? acc.BillingCity.trim().toLowerCase()    : ''),
            (acc.BillingState   != null ? acc.BillingState.trim().toLowerCase()   : ''),
            (acc.BillingPostalCode != null ? acc.BillingPostalCode.trim()         : ''),
            (acc.BillingCountry != null ? acc.BillingCountry.trim().toLowerCase() : '')
        },
        '|'
    );
    Blob digest = Crypto.generateDigest('SHA-256', Blob.valueOf(raw));
    return EncodingUtil.convertToHex(digest);
}
```

```python
import hashlib

def build_address_hash(record: dict) -> str:
    """Build the same hash on the source system side."""
    parts = [
        (record.get("street") or "").strip().lower(),
        (record.get("city") or "").strip().lower(),
        (record.get("state") or "").strip().lower(),
        (record.get("postal_code") or "").strip(),
        (record.get("country") or "").strip().lower(),
    ]
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
```

**Why it works:** Both sides produce the same deterministic hash from the same normalized input. A mismatch means at least one address field drifted. The integration can then fetch only those records for a targeted resync, rather than re-processing the full dataset.

---

## Example 4: CDC Replay Gap Recovery

**Context:** A Pub/Sub API subscriber missed 18 hours of Change Data Capture events due to a network outage.

**Problem:** The subscriber reconnected without a stored `replayId`, defaulting to `-1` (tip of stream), silently dropping all events from the outage window.

**Solution:**

```python
# Correct: persist replayId after every processed event
import json
from pathlib import Path

REPLAY_FILE = Path("/var/integration/cdc_replay_id.json")

def load_replay_id(channel: str) -> int:
    """Load last processed replayId. Return -2 for earliest available if no state."""
    if REPLAY_FILE.exists():
        data = json.loads(REPLAY_FILE.read_text())
        return data.get(channel, -2)  # -2 = replay from earliest available (up to 72h)
    return -2

def save_replay_id(channel: str, replay_id: int) -> None:
    data = {}
    if REPLAY_FILE.exists():
        data = json.loads(REPLAY_FILE.read_text())
    data[channel] = replay_id
    REPLAY_FILE.write_text(json.dumps(data))

# When subscribing:
replay_id = load_replay_id("/data/AccountChangeEvent")
# Pass replay_id to Pub/Sub API subscribe call
# After processing each event batch:
save_replay_id("/data/AccountChangeEvent", last_event_replay_id)
```

**Why it works:** Storing `replayId` persistently and defaulting to `-2` (earliest retained event) ensures that after an outage the subscriber replays from its last known position, not from the live tip. The 72-hour CDC retention window allows recovery from outages up to 3 days. Beyond that, a full reconciliation run is required.

---

## Anti-Pattern: Using LastModifiedDate Without Tombstone Logic

**What practitioners do:** Build a delta sync that queries `WHERE LastModifiedDate > :lastRun` and assumes this covers all changes including deletions.

**What goes wrong:** Hard-deleted records do not appear in standard SOQL results regardless of `LastModifiedDate`. After deletion, the record is moved to the recycle bin. If the external system is not notified, it retains the record indefinitely, causing a silent divergence that only count-level reconciliation will surface.

**Correct approach:** Supplement the `LastModifiedDate` delta query with one of:
1. CDC `DELETE` event subscription (preferred — real-time, record-specific)
2. A periodic `queryAll()` REST API call scoped to `isDeleted = true AND SystemModstamp > :lastRun` to find recently tombstoned records, then mark them deleted in the external system.
