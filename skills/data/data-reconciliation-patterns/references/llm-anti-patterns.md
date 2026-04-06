# LLM Anti-Patterns — Data Reconciliation Patterns

Common mistakes AI coding assistants make when generating or advising on data reconciliation in Salesforce integrations. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Generating a Native Checksum or Hash API Call

**What the LLM generates:** Code that calls a non-existent Salesforce native checksum or `getHash()` method, or queries a `CHECKSUM` field on sObject records, as if Salesforce exposes a built-in record hash similar to PostgreSQL's `md5()` function.

**Why it happens:** LLMs trained on multi-database content conflate database-native hash functions (PostgreSQL `md5()`, MySQL `MD5()`) with Salesforce's platform capabilities. Salesforce has no native per-record checksum API.

**Correct pattern:**

```apex
// All hashing is client-side via Apex Crypto class
String raw = acc.BillingStreet + '|' + acc.BillingCity;
Blob digest = Crypto.generateDigest('SHA-256', Blob.valueOf(raw));
String hash = EncodingUtil.convertToHex(digest);
```

**Detection hint:** Look for calls to `CHECKSUM`, `getHash`, `sObject.hash()`, or any SOQL aggregate function that sounds like a hash. None of these exist on the Salesforce platform.

---

## Anti-Pattern 2: Using `SELECT ... WHERE LastModifiedDate > :lastRun` as the Complete Delete Detection Strategy

**What the LLM generates:** A delta load query that relies solely on `LastModifiedDate` and claims this covers all changes including deletions.

**Why it happens:** LLMs generalize from database CDC patterns where a `deleted_at` column or soft-delete flag is updated on deletion. Salesforce hard deletes move records to the recycle bin — they do not update `LastModifiedDate` and do not appear in standard SOQL.

**Correct pattern:**

```soql
-- Standard delta (misses hard deletes):
SELECT Id, Name FROM Account WHERE LastModifiedDate > :lastRun

-- Deleted record detection requires queryAll() REST endpoint or ALL ROWS:
-- REST: GET /queryAll?q=SELECT+Id+FROM+Account+WHERE+isDeleted=true+AND+SystemModstamp>:lastRun
-- Or subscribe to CDC DELETE events via Pub/Sub API
```

**Detection hint:** Any integration spec that claims `LastModifiedDate` delta covers "all changes" without mentioning tombstone logic or CDC DELETE events is incomplete.

---

## Anti-Pattern 3: Assuming CDC Replay Is Unlimited

**What the LLM generates:** Code or documentation stating that `replayId = -2` can recover all historical CDC events, or that the subscriber can replay from any past point in time.

**Why it happens:** LLMs trained on Apache Kafka documentation associate event log replay with unlimited retention. Salesforce CDC has a fixed 72-hour (3-day) retention window — events older than 3 days are permanently deleted from the stream.

**Correct pattern:**

```python
# Correct: document the retention limit and the fallback
RETENTION_HOURS = 72  # Salesforce CDC retention window

def get_replay_strategy(hours_since_last_process: float) -> str:
    if hours_since_last_process <= RETENTION_HOURS:
        return "replay_from_stored_id"
    else:
        return "full_reconciliation_required"
```

**Detection hint:** Any claim that CDC replay is unlimited or "as far back as needed" is incorrect. Look for missing retention window handling in subscriber reconnect logic.

---

## Anti-Pattern 4: Using a Non-Unique External ID Field for Upsert Without Validation

**What the LLM generates:** A Bulk API 2.0 upsert job spec that targets a custom External ID field without verifying the Unique constraint, often because the LLM assumes "External ID" implies uniqueness.

**Why it happens:** The External ID and Unique field properties are independent checkboxes in Salesforce field setup. LLMs trained on integration guides often conflate the two, assuming that marking a field as an External ID automatically makes it unique.

**Correct pattern:**

```soql
-- Run before enabling upsert on any External ID field
-- If this returns rows, duplicates exist and must be resolved
SELECT HR_Employee_Id__c, COUNT(Id) cnt
FROM Contact
GROUP BY HR_Employee_Id__c
HAVING COUNT(Id) > 1
```

```
Field definition checklist:
- [x] External ID checkbox: checked
- [x] Unique checkbox: checked  <-- required for safe upsert
- [ ] Case-sensitive: consider source data casing
```

**Detection hint:** Any External ID field used in an upsert job spec where the Unique constraint is not verified or documented should be flagged.

---

## Anti-Pattern 5: Treating Bulk API 2.0 "JobComplete" as Full Success

**What the LLM generates:** Integration code that checks `job.state == "JobComplete"` and proceeds without checking `numberRecordsFailed` or fetching `failedResults`.

**Why it happens:** LLMs model job status as binary (success/failure) because that is the common pattern in most job queue systems. Bulk API 2.0 uses a partial-success model where `JobComplete` means "the job finished processing" — not "all rows succeeded."

**Correct pattern:**

```python
def verify_bulk_job(job_id: str, sf_client) -> None:
    status = sf_client.get_job_status(job_id)
    assert status["state"] == "JobComplete", f"Job not complete: {status['state']}"

    # Critical: check partial failures
    if status["numberRecordsFailed"] > 0:
        failed = sf_client.get_failed_results(job_id)
        for row in csv.DictReader(failed.splitlines()):
            log_failure(row["sf__Id"], row["sf__Error"], row)
        raise IntegrationError(
            f"{status['numberRecordsFailed']} rows failed in job {job_id}"
        )
```

**Detection hint:** Any integration code that checks only `job.state` or `job.status` without also reading `numberRecordsFailed` and `failedResults` is incomplete. Look for the absence of `failedResults` in post-job verification logic.

---

## Anti-Pattern 6: Performing Record-Level Reconciliation Without Normalizing the Join Key

**What the LLM generates:** A join between Salesforce records and source records using an External ID field without normalizing case or trimming whitespace, producing false mismatches.

**Why it happens:** LLMs generate straightforward equality joins from SQL training data. Platform-specific casing and whitespace behaviors are not encoded in generic SQL knowledge.

**Correct pattern:**

```python
# Wrong: direct equality join
sf_records = {r["HR_Employee_Id__c"]: r for r in sf_export}
mismatches = [r for r in source_export if r["employee_id"] not in sf_records]

# Correct: normalize both sides before joining
sf_records = {r["HR_Employee_Id__c"].strip().upper(): r for r in sf_export}
mismatches = [
    r for r in source_export
    if r["employee_id"].strip().upper() not in sf_records
]
```

**Detection hint:** Any reconciliation join that does not normalize the key column (strip, lowercase/uppercase) before comparison will produce false mismatches when case or whitespace inconsistencies exist between systems.
