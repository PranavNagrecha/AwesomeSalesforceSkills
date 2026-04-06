# LLM Anti-Patterns — SF-to-LLM Data Pipelines

Common mistakes AI coding assistants make when generating or advising on Salesforce-to-external-LLM data pipelines.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending REST API Pagination for Large-Volume Extraction

**What the LLM generates:** Code or guidance that uses the standard REST query API (`/services/data/vXX.0/query?q=SELECT...`) with `nextRecordsUrl` pagination to extract large Salesforce object populations for an LLM pipeline.

**Why it happens:** The REST query API is the most commonly documented Salesforce API and appears heavily in training data. The LLM generalizes from small-volume use cases where REST pagination is appropriate to large-volume extraction scenarios where it is not.

**Correct pattern:**

```
For any extraction exceeding ~10,000 records, use Bulk API v2 query jobs:
1. POST to /services/data/vXX.0/jobs/query with the SOQL and contentType=CSV
2. Poll job status until state == "JobComplete"
3. GET /services/data/vXX.0/jobs/query/{jobId}/results with Sfdclocator cursor
4. Follow cursor until response body is empty

Bulk API v2 uses a separate daily byte quota from the standard API call limit,
is asynchronous with native retry, and supports cursor-based pagination.
```

**Detection hint:** Look for `nextRecordsUrl` in the extraction code. If it appears alongside record counts above 10,000, the pattern is wrong.

---

## Anti-Pattern 2: Applying PII Scrubbing After Transmission to the External Service

**What the LLM generates:** Code that transmits raw Salesforce records to an external embedding API or vector store, then attempts to delete or update PII-containing documents after the fact. Sometimes described as "we'll filter out PII in the vector store after ingestion."

**Why it happens:** The LLM treats the pipeline as a data transformation problem and optimizes for pipeline simplicity, not security boundary. It does not model the legal significance of data transiting a network boundary to a third-party service.

**Correct pattern:**

```python
# WRONG — PII transmitted to external service, then "cleaned up"
raw_text = row["Description"]  # may contain email, phone
embed_and_upsert(raw_text, vector_store)  # PII already transmitted
# ...later...
update_record_to_remove_pii(vector_store)  # too late

# CORRECT — scrub in-process before any outbound call
raw_text = row["Description"]
clean_text = scrub_pii(raw_text)  # NER or regex before network call
embed_and_upsert(clean_text, vector_store)  # PII never leaves org
```

**Detection hint:** Any code where `scrub_pii`, `strip_pii`, `remove_pii`, or equivalent is called after the variable is passed to an HTTP client or vector store SDK call is wrong.

---

## Anti-Pattern 3: Using `LastModifiedDate` as the Incremental Extraction Watermark

**What the LLM generates:** Incremental extraction code with SOQL using `WHERE LastModifiedDate >= :last_sync` as the change detection predicate.

**Why it happens:** `LastModifiedDate` is the semantically obvious choice — it says "last modified date" — and it is user-visible in the Salesforce UI. `SystemModstamp` is less prominent and less commonly mentioned in tutorial-level content.

**Correct pattern:**

```sql
-- WRONG
SELECT Id, Name, Description, LastModifiedDate
FROM Account
WHERE LastModifiedDate >= 2026-04-05T00:00:00Z

-- CORRECT
SELECT Id, Name, Description, SystemModstamp
FROM Account
WHERE SystemModstamp >= 2026-04-05T00:00:00Z

-- Reason: LastModifiedDate can be frozen by Data Loader imports with
-- setbulkheader. SystemModstamp is always updated by the platform on
-- any write, including system-initiated changes.
```

**Detection hint:** Search the generated SOQL for `LastModifiedDate` in WHERE clauses of incremental extraction queries. Flag any occurrence for review.

---

## Anti-Pattern 4: Treating Bulk API v2 Result Download as Synchronous with Processing

**What the LLM generates:** A pipeline loop that downloads a Bulk API v2 result batch, immediately runs each record through the embedding model, writes to the vector store, and then fetches the next result batch — all in sequence, with potential sleep/retry between steps.

**Why it happens:** The LLM generates "natural" pipeline code that processes records one batch at a time, treating the download and processing as a unified streaming operation. It does not model the Salesforce-specific 10-minute cursor expiry.

**Correct pattern:**

```python
# WRONG — download and processing interleaved; cursor may expire during embedding
for batch in iter_bulk_api_batches(job_id):
    for row in batch:
        embedding = embed(row["text"])  # may be slow; risks cursor timeout
        upsert(embedding, vector_store)

# CORRECT — download all batches first, then process
all_rows = []
for batch in iter_bulk_api_batches(job_id):
    all_rows.extend(batch)  # fast download loop; no processing delays
# Cursor is fully consumed; no expiry risk

for row in all_rows:
    embedding = embed(row["text"])
    upsert(embedding, vector_store)
```

**Detection hint:** Look for embedding model calls or vector store writes inside the same loop that calls the Bulk API v2 results endpoint. This is the anti-pattern.

---

## Anti-Pattern 5: Omitting `PublishStatus = 'Online'` Filter on KnowledgeArticleVersion Queries

**What the LLM generates:** SOQL for Knowledge article extraction that queries `KnowledgeArticleVersion` without a `PublishStatus` filter, or uses `PublishStatus != 'Archived'` instead of `= 'Online'`.

**Why it happens:** The LLM may not be aware that `KnowledgeArticleVersion` returns all version states by default. It generates a query that "looks right" but captures draft and archived articles in addition to published ones.

**Correct pattern:**

```sql
-- WRONG — includes Draft and Archived versions
SELECT Id, Title, Body FROM KnowledgeArticleVersion
WHERE Language = 'en_US'

-- ALSO WRONG — excludes Archived but includes Draft
SELECT Id, Title, Body FROM KnowledgeArticleVersion
WHERE PublishStatus != 'Archived' AND Language = 'en_US'

-- CORRECT — only published, live articles
SELECT Id, Title, Body FROM KnowledgeArticleVersion
WHERE PublishStatus = 'Online' AND Language = 'en_US'
```

**Detection hint:** Any SOQL against `KnowledgeArticleVersion` that lacks `PublishStatus = 'Online'` should be flagged. Also check for single-language orgs using multi-language orgs' query patterns (missing `Language` filter causes duplicate articles indexed for each language).

---

## Anti-Pattern 6: Using Username/Password OAuth for the Extraction Connected App

**What the LLM generates:** Extraction pipeline authentication code that uses the Resource Owner Password Credentials (ROPC) OAuth flow — submitting a username, password, and security token to obtain an access token.

**Why it happens:** Username/password OAuth is the simplest Salesforce authentication pattern and appears in the majority of introductory API tutorials. LLMs reproduce it without flagging that it is unsuitable for production pipeline authentication.

**Correct pattern:**

```
# WRONG — username/password credentials embedded in pipeline config
auth_payload = {
    "grant_type": "password",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "username": SF_USERNAME,      # credential in config
    "password": SF_PASSWORD + SECURITY_TOKEN,
}

# CORRECT — JWT Bearer flow with certificate
# 1. Create a connected app with a certificate uploaded (not a client secret)
# 2. Sign a JWT assertion with the private key (never transmitted)
# 3. POST the signed JWT to the token endpoint — no password required
jwt_assertion = sign_jwt(private_key, issuer=CLIENT_ID, subject=SF_USERNAME, audience=TOKEN_URL)
auth_payload = {
    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
    "assertion": jwt_assertion,
}
```

**Detection hint:** Look for `grant_type: password` or `grant_type=password` in authentication code. Any occurrence is the anti-pattern for production pipeline use.
