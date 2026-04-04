# Gotchas — Bulk API Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: `concurrencyMode: Parallel` in Bulk API 2.0 Is Reserved — Serial Mode Does Not Exist in v2.0

**What happens:** Developers who read Bulk API v1 documentation expect to set `concurrencyMode: Serial` in their Bulk API 2.0 job creation request to avoid lock contention. In Bulk API 2.0, `concurrencyMode` is a reserved field for future use and always returns `Parallel`. Passing `concurrencyMode: Serial` may silently be ignored, or in some API versions may return a validation error.

**When it occurs:** Any time a developer migrates from legacy Bulk API v1 serial mode to Bulk API 2.0 and attempts to carry the serial mode configuration forward. Also occurs when developers read v1 documentation and apply it to v2.0 implementations.

**How to avoid:**
- Accept that Bulk API 2.0 supports parallel mode only.
- If serial mode is genuinely required (to prevent `UNABLE_TO_LOCK_ROW` on objects with complex triggers), use legacy Bulk API v1 with `concurrencyMode: Serial` and SOAP-based authentication.
- For Bulk API 2.0, mitigate lock contention by sorting the CSV by parent ID before upload so related records land in the same internal batch, reducing inter-batch lock collisions.

---

## Gotcha 2: `Sforce-Locator: null` Is a Literal String — Not JSON null, Not Empty String, Not Absent Header

**What happens:** When paginating query job results, the `Sforce-Locator` response header contains the literal string `"null"` to indicate there are no more pages. Code that checks `if locator is None`, `if not locator`, or `if locator == ""` will not detect the last page and will loop indefinitely, re-fetching the last page forever. This is a common bug in locator-based pagination implementations.

**When it occurs:** Any Bulk API 2.0 query job result pagination loop. Occurs in Python, JavaScript, Java, and any language where null-checking idioms behave differently from string equality.

**How to avoid:**
- Always compare with string equality: `if locator == "null"` (Python) or `"null".equals(locator)` (Java).
- Treat the presence of the `Sforce-Locator` header with the value `"null"` as the explicit end-of-results signal.
- Do not rely on the header being absent — it is always present and always has a value (either a locator string or the string `"null"`).

---

## Gotcha 3: Empty CSV Cell Sets Empty String, Not Null — Use `#N/A` to Null a Field

**What happens:** In Bulk API 2.0 CSV uploads, an empty cell (`,,` between two commas, or a trailing comma on a row) sets the field to an empty string. For text fields this may be acceptable, but for required fields, number/currency fields, date/time fields, and lookup fields, an empty string causes a type mismatch or required-field validation error. Developers expecting that leaving a cell blank will "not touch" the field are surprised to find their records failing with unexpected errors.

**When it occurs:**
- Upsert jobs where some records have no value for an optional field and the developer leaves the cell blank.
- Migration jobs where the source system exports nulls as empty strings.
- Any job where the intention is to clear an existing field value rather than set an empty string.

**How to avoid:**
- Use `#N/A` as the cell value to explicitly set a field to null.
- For fields you want to leave unchanged during an upsert, omit the column from the CSV entirely (Salesforce will not touch fields not present in the CSV header).
- For fields you want to clear, include the column and set the cell to `#N/A`.
- Pre-process source CSVs to replace null/empty representations with `#N/A` before uploading.

---

## Gotcha 4: Multipart Job Auto-Completes UploadComplete — Sending a Second PATCH Causes an Error

**What happens:** When a job is created using the multipart endpoint, it transitions directly to `UploadComplete` state on creation. If the integration code then sends the standard `PATCH {"state": "UploadComplete"}` as part of a shared pipeline function, Salesforce returns an error because the job is already past the `Open` state and the state transition is invalid.

**When it occurs:** Integration pipelines that abstract the ingest job lifecycle into a shared function that always sends the `UploadComplete` PATCH, without checking whether the job was created via standard or multipart creation. Occurs when developers add multipart support to an existing integration without updating the state transition logic.

**How to avoid:**
- Check the `state` field in the job creation response before deciding whether to send the `UploadComplete` PATCH.
- If `state == "Open"` in the creation response: this is a standard job — send the PATCH after uploading all chunks.
- If `state == "UploadComplete"` in the creation response: this is a multipart job — skip the PATCH and proceed directly to polling.
- Structure the pipeline to branch on the initial state rather than always sending the PATCH unconditionally.

---

## Gotcha 5: `lineEnding` Mismatch Between Job Declaration and Actual CSV Causes Silent Parse Failures

**What happens:** Bulk API 2.0 requires the `lineEnding` field in the job creation request to match the actual line endings used in the uploaded CSV. If the CSV was generated on Windows (CRLF) but the job was created with `lineEnding: LF`, Salesforce may misparse the CSV — treating the `\r` as part of the field value or misidentifying row boundaries. The result is records that fail with unexpected field-value errors, or rows that are silently split or merged during parsing.

**When it occurs:**
- CSV files generated on Windows machines and uploaded by integrations created by developers on Unix/macOS who did not inspect the file line endings.
- Source systems that change their export line endings between environments (e.g., dev exports with LF, prod exports with CRLF).
- Any pipeline that does not explicitly normalize line endings before upload.

**How to avoid:**
- Inspect the actual line endings in your CSV before creating the job. Most text editors and tools (`file`, `hexdump`) can confirm LF vs CRLF.
- Normalize line endings to LF during CSV generation or pre-processing.
- Explicitly set `lineEnding` in the job creation request — do not rely on the default (LF) unless you have verified the CSV uses LF.
- If using CRLF, declare `"lineEnding": "CRLF"` in the job creation body.
