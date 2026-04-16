# LLM Anti-Patterns — Bulk API 2.0 Patterns (Integration)

Common mistakes AI coding assistants make when generating or advising on Bulk API 2.0 integration orchestration.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating upload HTTP success as job completion

**What the LLM generates:** Code that returns `"success"` immediately after the final CSV `PUT` returns `201 Created`, with no `PATCH UploadComplete` and no job polling.

**Why it happens:** Other REST APIs finalize resources on the last content upload; LLMs transfer that mental model to Bulk API 2.0 ingest.

**Correct pattern:**

```
After final PUT succeeds, PATCH /jobs/ingest/{jobId}/ with {"state":"UploadComplete"},
then poll GET /jobs/ingest/{jobId}/ until state is terminal before reading results.
```

**Detection hint:** Search for `PUT` on `contentUrl` without a nearby `UploadComplete` string or multipart boundary setup.

---

## Anti-Pattern 2: Conflating `JobComplete` with “all rows succeeded”

**What the LLM generates:** Branch logic like `if state == "JobComplete": mark_dataset_synced()` with no inspection of `numberRecordsFailed` or result endpoints.

**Why it happens:** Natural language equates “complete” with success; the platform uses `JobComplete` to mean processing finished.

**Correct pattern:**

```
On JobComplete, always compare processed vs source counts and download failedResults
before advancing external checkpoints.
```

**Detection hint:** Look for `JobComplete` checks paired with zero references to `failedResults` / `numberRecordsFailed`.

---

## Anti-Pattern 3: Inventing locator values for query pagination

**What the LLM generates:** Loops that increment an integer page parameter or hash the job ID to fabricate the next locator.

**Why it happens:** Training data shows generic REST `page=` patterns; Bulk API 2.0 uses opaque locators.

**Correct pattern:**

```
Read Sforce-Locator from each GET .../results response; pass that exact value as ?locator= on the next GET; stop when the header value is the literal string null.
```

**Detection hint:** Locator arithmetic, string concatenation with job IDs, or `page++` near `jobs/query`.

---

## Anti-Pattern 4: Issuing `UploadComplete` after multipart create

**What the LLM generates:** Redundant `PATCH` after a documented multipart ingest example, sometimes causing client errors or confusing idempotent retry logic.

**Why it happens:** The standard non-multipart flow is over-generalized to every ingest path.

**Correct pattern:**

```
If using multipart job creation, rely on Salesforce to finish the upload phase automatically; only apply manual UploadComplete for create+PUT flows.
```

**Detection hint:** Multipart `Content-Type` headers combined with unconditional `UploadComplete` helpers.

---

## Anti-Pattern 5: Parallel parent and child bulk jobs without gates

**What the LLM generates:** Two `POST /jobs/ingest/` calls fired from asyncio/goroutines with no ordering constraint between related objects.

**Why it happens:** LLMs optimize for throughput and may not model Salesforce foreign-key validation ordering across separate jobs.

**Correct pattern:**

```
Await parent job JobComplete and reconcile failures before creating the child ingest job; persist the parent job id as a prerequisite token.
```

**Detection hint:** Multiple ingest job creations in one function without reading prior job status objects.
