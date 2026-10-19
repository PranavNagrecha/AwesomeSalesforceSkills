# Gotchas — Bulk API Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: `concurrencyMode` Is for Future Use — Bulk API 2.0 Is Parallel Only

**What happens:** Developers migrating from Bulk API v1 carry `concurrencyMode: Serial` into a Bulk API 2.0 job to avoid lock contention, and nothing about processing changes.

**When it occurs:** The Bulk API 2.0 job resources describe `concurrencyMode` as "For future use... Currently only parallel mode is supported," and say that when other modes arrive they "will be chosen automatically by the API and will not be user configurable."

**How to avoid:** Plan for parallel processing. The guide's lock-contention advice for Bulk API 2.0 is to sort records by parent so children of the same parent are not spread across jobs (its example: organize AccountTeamMember files by AccountId), and to be aware that creating users, changing ownership under private sharing, updating roles, and updating territory hierarchies are likely to cause contention. Use Bulk API v1 serial mode only when that is not enough.

---

## Gotcha 2: `Sforce-Locator: null` Is a String

**What happens:** A pagination loop checks `if locator is None` or `if not locator`, never sees the end, and re-requests forever.

**When it occurs:** The guide's rules for query results: "If there are no more results, the Sforce-Locator header's value is the string 'null'." It also says to use only the value from the header and not to guess it, because how the parameter is evaluated is subject to change.

**How to avoid:** Compare with string equality (`locator == "null"`), pass the header value back unchanged as `locator`, and stop on `"null"`.

---

## Gotcha 3: Empty Cells Are Ignored on Update — `#N/A` Clears a Field

**What happens:** A migration intends to blank out fields by leaving cells empty. The update succeeds and the old values remain.

**When it occurs:** The CSV rules: "Empty field values are ignored when you update records. To set a field value to null, use a field value of #N/A." Fields not present in the CSV header are also ignored during an update.

**How to avoid:** Decide the null policy per field. Use `#N/A` where a value must be cleared; leave the cell empty (or drop the column) where the existing value must be kept.

---

## Gotcha 4: Multipart Jobs Are Already Upload-Complete

**What happens:** A shared pipeline function sends `PATCH {"state": "UploadComplete"}` after every job creation, including multipart ones, and the step for multipart jobs is at best redundant.

**When it occurs:** The guide: "After you create a multipart job, the upload is completed for you automatically. You don't need to manually set the job state to UploadComplete for a multipart job."

**How to avoid:** Branch on the `state` returned by job creation: send the PATCH only when the job is `Open`.

---

## Gotcha 5: `lineEnding` Must Match the File

**What happens:** A CSV written on Windows (CRLF) is uploaded to a job declared with the default `LF`, and rows fail with unexpected field values.

**When it occurs:** The guide asks for a `lineEnding` "that matches the line ending used to create the CSV file"; LF is the default, and the text editor's setting can override the operating system's convention.

**How to avoid:** Inspect the bytes (`file`, `od -c`) before creating the job, normalize to LF, or declare `"lineEnding": "CRLF"`.

---

## Gotcha 6: 150 MB Is a Per-Job Ceiling, Not Per Request

**What happens:** An integration splits an 800 MB file into eight 100 MB uploads to the same job and the job rejects the data.

**When it occurs:** The guide's quick start says "You can upload up to 150 MB per job (after base64 encoding)," and the limits guide lists 150 MB per job for Bulk API 2.0. Base64 adds about 50%, hence the advice to upload no more than 100 MB of raw data.

**How to avoid:** Split large files into separate jobs of about 100 MB raw each, and track every job Id for reconciliation.

---

## Gotcha 7: Field Values Aren't Trimmed

**What happens:** Upserts by external ID create duplicates because `" ACME-001"` does not match `"ACME-001"`, or rows fail outright.

**When it occurs:** The CSV rules: a space before or after a delimiter is part of the field value, and a space before or after a double quote generates an error for the row (`"John", "Smith"` isn't valid).

**How to avoid:** Trim every value in the export step and never put spaces around quotes.

---

## Gotcha 8: Unprocessed Records Exist Only for Failed or Aborted Jobs

**What happens:** A reconciliation script expects an unprocessed-records file for every job and reports errors for `JobComplete` jobs, or a script that only reads `failedResults` misses the rows a failed job never touched.

**When it occurs:** The unprocessed-records resource "Retrieves a list of unprocessed records for failed or aborted jobs" at `/jobs/ingest/jobID/unprocessedrecords/`. A batch that still fails after 20 retries moves the whole job to `Failed`, and the remaining data isn't processed. Results are retrievable for 7 days.

**How to avoid:** For `JobComplete`, reconcile successful plus failed against the upload. For `Failed` or `Aborted`, add unprocessed records, then create a new job for failed and unprocessed rows.
