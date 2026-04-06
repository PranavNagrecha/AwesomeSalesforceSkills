# Examples — SF-to-LLM Data Pipelines

## Example 1: Bulk API v2 Knowledge Article Extraction with HTML Stripping

**Context:** A team is building an external chatbot backed by LangChain and Pinecone. The knowledge base is Salesforce Knowledge with approximately 80,000 published articles. The pipeline runs nightly and must be refreshable within an hour for urgent content updates.

**Problem:** A naive implementation uses the REST API to GET each `KnowledgeArticleVersion` record individually. At 80,000 records and a 5-request-per-second sustainable rate, the extraction takes over 4 hours and consumes ~80,000 of the org's daily API call quota. Additionally, the `Body` field is returned with raw HTML, so chunks stored in Pinecone contain `<p>`, `<li>`, and `&nbsp;` tokens that degrade embedding quality.

**Solution:**

```python
import re
import html
import requests
import csv
import io
import time

# 1. Authenticate via JWT Bearer flow (not shown — use connected app certificate)
access_token = get_jwt_bearer_token(instance_url, client_id, key_file)
headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

# 2. Submit Bulk API v2 query job
job_payload = {
    "operation": "query",
    "query": (
        "SELECT Id, Title, Summary, Body, ArticleNumber, LastPublishedDate, SystemModstamp "
        "FROM KnowledgeArticleVersion "
        "WHERE PublishStatus = 'Online' AND Language = 'en_US'"
    ),
    "contentType": "CSV",
}
job_resp = requests.post(
    f"{instance_url}/services/data/v60.0/jobs/query",
    json=job_payload,
    headers=headers,
)
job_id = job_resp.json()["id"]

# 3. Poll until JobComplete
while True:
    status = requests.get(
        f"{instance_url}/services/data/v60.0/jobs/query/{job_id}",
        headers=headers,
    ).json()["state"]
    if status == "JobComplete":
        break
    if status in ("Failed", "Aborted"):
        raise RuntimeError(f"Bulk job failed: {status}")
    time.sleep(30)

# 4. Download all result batches following the Sfdclocator cursor
locator = None
all_rows = []
while True:
    params = {"maxRecords": 50000}
    if locator:
        params["locator"] = locator
    result = requests.get(
        f"{instance_url}/services/data/v60.0/jobs/query/{job_id}/results",
        headers={**headers, "Accept": "text/csv"},
        params=params,
    )
    reader = csv.DictReader(io.StringIO(result.text))
    batch = list(reader)
    all_rows.extend(batch)
    locator = result.headers.get("Sfdclocator")
    if not locator or locator == "null":
        break

# 5. Strip HTML from Body before chunking
TAG_RE = re.compile(r"<[^>]+>")

def strip_html(raw: str) -> str:
    clean = TAG_RE.sub(" ", raw or "")
    return html.unescape(clean).strip()

def chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> list[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        start += chunk_size - overlap
    return chunks

# 6. Build vector store documents
docs = []
for row in all_rows:
    plain_body = strip_html(row["Body"])
    text = f"{row['Title']}: {plain_body}"
    for i, chunk in enumerate(chunk_text(text)):
        docs.append({
            "id": f"{row['Id']}_chunk_{i}",
            "text": chunk,
            "metadata": {
                "record_id": row["Id"],
                "article_number": row["ArticleNumber"],
                "title": row["Title"],
                "last_modified": row["SystemModstamp"],
            },
        })
# docs is now ready for upsert into Pinecone or equivalent
```

**Why it works:** Bulk API v2 submits a single asynchronous job that returns all 80,000 records as paginated CSV batches, consuming one bulk job slot rather than 80,000 API calls. HTML stripping removes markup tokens before the text reaches the tokenizer, so the embedding model encodes semantic content rather than tag structure.

---

## Example 2: Incremental Case Extraction with PII Scrubbing

**Context:** A customer success team runs an external LLM that summarizes resolved case patterns. The vector store must reflect resolved cases within 30 minutes. Cases contain customer email addresses and phone numbers in the `Description` field that must not leave the org.

**Problem:** Without PII scrubbing, the `Description` field may contain verbatim customer emails and phone numbers typed by support agents or pasted from customer correspondence. Transmitting these to the external LLM violates the applicable data processing agreement.

**Solution:**

```python
import re
import hmac
import hashlib
import os

# Scrubbing patterns for incidental PII in free-text fields
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(\+?1[\s\-.]?)?\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4}")

def scrub_free_text(text: str) -> str:
    """Replace detected email and phone patterns with placeholder tokens."""
    text = EMAIL_RE.sub("[EMAIL]", text or "")
    text = PHONE_RE.sub("[PHONE]", text)
    return text

# Pseudonymize the Salesforce record ID for use as the vector store document key
PSEUDONYM_SECRET = os.environ["PSEUDONYM_SECRET"].encode()

def pseudonymize_id(sf_id: str) -> str:
    return hmac.new(PSEUDONYM_SECRET, sf_id.encode(), hashlib.sha256).hexdigest()

# Incremental SOQL using SystemModstamp watermark
last_sync = load_watermark()  # e.g., "2026-04-05T14:00:00.000Z"
soql = (
    f"SELECT Id, CaseNumber, Subject, Description, Resolution__c, SystemModstamp "
    f"FROM Case "
    f"WHERE SystemModstamp >= {last_sync} AND Status = 'Closed'"
)

# Submit Bulk API v2 job, poll, download (same pattern as Example 1)
rows = run_bulk_query(instance_url, access_token, soql)

# Scrub and build documents
docs = []
for row in rows:
    pseudo_id = pseudonymize_id(row["Id"])
    subject = row["Subject"] or ""
    description = scrub_free_text(row["Description"])
    resolution = scrub_free_text(row["Resolution__c"])
    text = f"{subject}\n{description}\n{resolution}".strip()
    docs.append({
        "id": f"{pseudo_id}_chunk_0",
        "text": text,
        "metadata": {
            "record_id": pseudo_id,  # pseudonymized — no raw SF ID transmitted
            "case_number": row["CaseNumber"],
            "last_modified": row["SystemModstamp"],
        },
    })

# Upsert docs to external vector store
upsert_to_vector_store(docs)

# Advance watermark ONLY after successful upsert
save_watermark(pipeline_run_start_time)
```

**Why it works:** The `scrub_free_text` function removes detectable PII patterns before the record is assembled into the document sent to the external store. The raw Salesforce ID is replaced with a deterministic HMAC pseudonym, severing the linkage to individual records in the external store while preserving the ability to delete vectors by record when required. The watermark is advanced only after a successful write, ensuring no records are dropped on retry.

---

## Anti-Pattern: Using REST API Record-by-Record Extraction for Large Objects

**What practitioners do:** They iterate over a SOQL result using the REST API's query endpoint (`/services/data/vXX.0/query?q=...`) and follow `nextRecordsUrl` to page through all records, processing each page as it is returned.

**What goes wrong:** The REST query API consumes one API call per request (typically 2,000 records per page). For a 500,000-record object, this is 250 API calls just for extraction — manageable in isolation, but it competes with all other REST API consumers in the org (integrations, automations, connected apps) within the same 24-hour rolling limit. At high data volumes or during shared org peak hours, this pattern causes API limit exhaustion and degrades other integrations. It also provides no native asynchronous retry mechanism; a network error mid-pagination requires restarting from the beginning or implementing custom cursor state.

**Correct approach:** Use Bulk API v2 query jobs for any extraction that exceeds ~10,000 records. The Bulk API v2 has a separate daily byte-based quota from the standard API call limit, is asynchronous with native job state management, and supports cursor-based result pagination that is resumable (within the 10-minute cursor expiry window).
