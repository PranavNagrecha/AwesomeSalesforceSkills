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
3. GET /services/data/vXX.0/jobs/query/{jobId}/results?locator={Sforce-Locator value}
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

---

## Anti-Pattern: Reading Bulk API 2.0 Pagination From a Fabricated `Sfdclocator` Header

**What the LLM generates:**
```python
locator = result.headers.get("Sfdclocator")     # WRONG — always None
while True:
    ...
    if not batch:            # WRONG termination condition
        break
```
Variants: `Sfdc-Locator`, `SForceLocator`, `X-Sforce-Locator`, and stopping when the response body is empty rather than when the header reads `null`.

**Why it happens:** Salesforce uses `Sfdc` as a namespace prefix in dozens of places (`sfdc`, `sfdcinternal`, the `Sfdc_` metadata prefixes), so the model reaches for the more familiar token. The header is also read once at the bottom of a loop, far from any documentation the model would have anchored on.

**Why this one is dangerous:** it is a **silent data-loss** bug. `headers.get()` on a wrong name returns `None`, the loop breaks after the first page, and the pipeline reports success. A 4-million-record extract quietly becomes whatever fitted in page one, and every downstream artefact — embeddings, vector index, evaluation set — is built on the truncated data with no error anywhere in the run.

**Correct pattern:**
```python
locator = None
while True:
    params = {"maxRecords": 50000}          # explicit; there is NO published default
    if locator:
        params["locator"] = locator
    r = requests.get(results_url, headers=hdrs, params=params)
    rows.extend(csv.DictReader(io.StringIO(r.text)))
    locator = r.headers.get("Sforce-Locator")       # canonical name
    if not locator or locator == "null":            # literal string "null"
        break
```
`Sforce-NumberOfRecords` carries the count for the current set and is a cheap assertion target.

**Detection hint:** grep the pipeline for `Sforce-Locator`; any *other* casing or spelling of a locator header is wrong. Two mechanical smells accompany it: a `headers.get(...)` result used as a loop condition without a `None` check, and a loop that terminates on an empty body instead of the literal string `"null"`. A cheap runtime assertion is to fail the job when the row count equals `maxRecords` exactly and the locator was falsy — that combination means the header name was wrong, not that the data ended.

---

## Anti-Pattern: Quoting a Published Default for Bulk API 2.0 `maxRecords`

**What the LLM generates:** "Each call returns up to `maxRecords` rows (default 50,000)." Also seen as 10,000 and 100,000.

**Why it happens:** 50,000 is a real, very familiar Salesforce number — it is the SOQL rows-per-transaction governor limit — so it is available and plausible. The documentation's actual wording ("the server uses a default value based on the service") is a non-answer, and models rarely reproduce a non-answer when a confident number is available.

**Correct pattern:**
```
maxRecords has NO published default. Salesforce reserves discretion.
Always pass maxRecords explicitly if page size matters to your consumer,
and never size memory, checkpoint intervals or progress estimates around
an assumed default.
```

**Detection hint:** any sentence pairing `maxRecords` with the word "default" and a number is unsupported by the documentation. In code, a consumer that pre-allocates or checkpoints on a hardcoded page size *without* also sending `maxRecords` in the request is relying on the invented default.

---

## Anti-Pattern: Claiming Bulk API 2.0 Query Jobs Cannot Traverse to Parent Fields

**What the LLM generates:** "`SELECT Account.Name FROM Contact` is not supported in Bulk API v2 — denormalise the parent value into a formula field, or join client-side."

**Why it happens:** Bulk API 2.0 genuinely does restrict SOQL, and *parent-to-child subqueries* are on the unsupported list. The model recalls "relationship queries are restricted" and inverts which direction is blocked, because the child-to-parent direction is the one it sees written most often.

**Why it matters:** the remedy is expensive and irreversible-ish. Teams add denormalising formula fields to production schema (which carry their own per-object limits and recalculation cost) to route around a restriction that was never there, and they slow every extract by issuing a second parent query and joining in the client.

**Correct pattern:**
```
SUPPORTED:   child-to-parent traversal — SELECT Id, Account.Name FROM Contact
UNSUPPORTED: GROUP BY, OFFSET, TYPEOF
             aggregate functions (COUNT(), etc.)
             date functions inside GROUP BY
             compound address / compound geolocation fields
             parent-to-child subqueries — SELECT Id, (SELECT Id FROM Contacts) FROM Account

Also: LIMIT and ORDER BY disable PKChunking, which can push a large
extract past the retrieval timeout. Avoid both on extraction queries.
```

**Detection hint:** a proposal to create a formula field whose only purpose is to expose a parent value to a Bulk API extract is the tell — the dotted path works directly. Conversely, a Bulk query string containing `(SELECT` is a real, checkable violation.

---

## Anti-Pattern: Stating the Bulk API 2.0 Record Ceiling as 100 Million Per Connected App

**What the LLM generates:** "Bulk API v2 supports up to 100 million records per 24-hour rolling window per connected app" — often paired with the architectural suggestion to shard work across several connected apps for more headroom.

**Why it happens:** 100 million is a rounder, more memorable number than 150,000,000, and "per connected app" is the scoping unit for API-request limits in several other Salesforce contexts, so the model transplants it.

**Why it matters:** the per-connected-app half is the damaging part. It licenses a capacity plan built on horizontal sharding that delivers exactly zero additional throughput, and the team discovers this only when the org-level allocation is exhausted mid-migration.

**Correct pattern:**
```
Ingest:  150,000,000 records per rolling 24 hours — ORG-LEVEL, not per app
         150 MB max file per job; keep uploads under 100 MB (base64 inflation)
Query:   10,000 query jobs per rolling 24 hours
         1 TB total query results per rolling 24 hours
         1 GB max retrieved file size per batch
         20-minute retrieval timeout
```
Note the 100 MB figure belongs to the *ingest* upload side. Attaching it to query result batches (whose ceiling is 1 GB) conflates two different limits.

**Detection hint:** the phrase `per connected app` adjacent to a Bulk API record volume is always wrong. `100 million` / `100,000,000` as a Bulk record ceiling is always wrong — the number is 150,000,000. `100 MB` described as a *query result* batch limit is the relabelled ingest figure.
