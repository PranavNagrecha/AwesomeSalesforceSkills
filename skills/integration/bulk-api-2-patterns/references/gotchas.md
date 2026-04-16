# Gotchas — Bulk API 2.0 Patterns (Integration)

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: UploadComplete is mandatory (except multipart)

**What happens:** Job remains in **Open** indefinitely; no `InProgress` or `JobComplete` transitions occur even though all `PUT` uploads returned HTTP 201.

**When it occurs:** Any standard ingest flow where the client omits the `PATCH` that sets `"state":"UploadComplete"` after the final data upload.

**How to avoid:** After the final successful `PUT`, always issue the `PATCH`. If you switched to multipart job creation, remember Salesforce auto-completes the upload phase—do not send a redundant manual close that conflicts with your client library assumptions.

---

## Gotcha 2: JobComplete still means row-level failures

**What happens:** Orchestration marks the pipeline “green” because `state == JobComplete`, while thousands of rows failed validation and never inserted.

**When it occurs:** Teams equate job state with business success instead of reading `numberRecordsFailed` and downloading `failedResults`.

**How to avoid:** Gate downstream checkpoints on **record counts and error files**, not on job state alone. Treat `failedResults` as first-class output to ticketing or replay queues.

---

## Gotcha 3: Locator `null` is a literal string sentinel

**What happens:** Client code treats missing `Sforce-Locator` header the same as the documented terminal value, or compares case-insensitively against JSON `null`.

**When it occurs:** Query job pagination loops written against informal REST examples instead of the official header contract.

**How to avoid:** Compare the header value to the documented literal string form and only advance while Salesforce returns a non-terminal locator. Never fabricate locator values between calls.

---

## Gotcha 4: Successful batches are not rolled back on later failure

**What happens:** A later internal batch times out or exhausts retries; operators assume the entire job rolled back, but earlier batches already committed.

**When it occurs:** High-volume jobs with heterogeneous row quality or lock-heavy objects processed in parallel internal batches.

**How to avoid:** Model compensating actions in the external system. Use idempotent upserts and keep external-side cursor files aligned with downloaded `successfulResults`.
