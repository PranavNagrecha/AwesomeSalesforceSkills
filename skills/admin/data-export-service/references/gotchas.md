# Gotchas — Salesforce Data Export Service

Non-obvious platform behaviors that cause real production problems.

**Grounding note.** Gotchas 1, 2, 4, 6, 7 and 8 describe the Setup → Data Export UI, which is documented only on help.salesforce.com and cannot be fetched — each carries an inline UNVERIFIED (2026-09-05) marker below. Gotchas 3, 5 and 9–14 are platform behaviours that hold whichever export tool you use, and each is cited to a line range in the Salesforce developer PDFs.

## Gotcha 1: the 48-hour expiration window is rigid

**What happens:** The download links in the notification email expire 48 hours after the export ZIPs are generated. After that, the files are deleted from Salesforce-managed storage and the next manual export cannot be requested until the next 7-day eligibility window opens. UNVERIFIED (2026-09-05): the 48-hour and 7-day figures are help-only; no grounding PDF states either.

**When it occurs:** Any time the operator misses the email (vacation, holiday, weekend rollover, Friday-evening completion, mis-filtered email rule).

**How to avoid:** Treat each export as a delivery, not a store. Notify a distribution list with rotation/redundancy. Set the schedule so generation completes during business hours. Build monitoring on the notification email (e.g., a transport rule that alerts an ops channel if no download has been recorded within 24 hours).

---

## Gotcha 2: Big Objects are silently skipped

**What happens:** The export completes successfully, the email reports no error, but Big Object data is absent from the ZIP set. There is no warning surfaced to the admin. UNVERIFIED (2026-09-05): the Big Object exclusion and its silence are help-only; the Metadata API guide text contains no `BigObject` token at all.

**When it occurs:** Any org that uses Big Objects for archival or telemetry storage and assumed the weekly/monthly export covers them.

**How to avoid:** Inventory Big Objects (`SELECT QualifiedApiName FROM EntityDefinition WHERE IsCustomizable = TRUE AND ...` filter or look at Setup → Big Objects). Document the gap in the runbook. Cover Big Objects via Async SOQL → Bulk API CSV pipeline, or by treating Big Object data as immutable telemetry that's re-derivable from upstream.

---

## Gotcha 3: encrypted (Shield) field values export in clear

**What happens:** Fields encrypted via Shield Platform Encryption appear in the CSVs as plaintext for any user whose FLS allows read on those fields. The encryption is at-rest and in-flight inside Salesforce; the export is a read operation, so it decrypts.

**When it occurs:** Any org with Shield Platform Encryption that exports to a destination less protected than the encrypted source — local laptops, unencrypted shared drives, generic S3 buckets without object encryption.

**How to avoid:** The export ZIPs must land on storage with at-rest encryption equal-or-greater than Shield's controls. S3 with SSE-KMS, Azure Blob with CMK, on-prem with FDE. Treat the ZIP as in-scope for the same compliance framework that drove the Shield purchase. Record the destination encryption posture in the runbook.

---

## Gotcha 4: file-content checkboxes inflate generation by orders of magnitude

**What happens:** A 5-million-row Account/Contact/Opportunity org with 100 GB of Salesforce Files goes from a 20-minute export to a 4–8-hour export when "Include Salesforce Files" is checked. The ZIP set balloons from 1 GB to 80–100 GB. UNVERIFIED (2026-09-05): the checkbox, and these timing and size figures, are help-only and field-observed rather than documented. What is grounded is the direction of the effect: file bodies travel as base64, which "increases the document size by approximately 37%" (`object_reference.txt:79772–79773`).

**When it occurs:** When the export's purpose is structured-data evidence and the operator reflexively checks all boxes "to be safe."

**How to avoid:** Default file-content checkboxes to OFF. Include binary content only when the consumer explicitly needs it (legal evidence of attached PDFs, full BI replication including ContentVersion). For evidence archive of structured records, files are out of scope and belong on a separate cadence with separate tooling.

---

## Gotcha 5: schema drift breaks downstream consumers

**What happens:** A custom field is added in March; the April export includes it; an automated S3-to-Snowflake loader fails because the CSV column count no longer matches the staged schema.

**When it occurs:** Any org with active customization plus a downstream automated consumer that pinned to a fixed schema.

**How to avoid:** Loaders downstream of Data Export must be schema-tolerant — either dynamically diff column lists per file or version-pin the loader to a known-good export schema and update the schema as part of the change-management process when fields are added.

---

## Gotcha 6: there is no API to start, monitor, or download exports

**What happens:** Teams that try to fully automate the runbook discover the service is UI-only — no SOAP, REST, or CLI to start an export or fetch the link. UNVERIFIED (2026-09-05): the absence of an API is a negative result — no Data Export resource appears in the REST, Bulk or Metadata API guides — not a positive statement in any of them.

**When it occurs:** When CI/CD or operations teams treat Data Export the way they treat Bulk API or Metadata API (programmable). It is not.

**How to avoid:** Don't promise full automation. The runbook should accept that human operators are part of the loop — the value-add is monitoring, alerting, and post-download archival, not click-elimination. Bulk API is the answer when full automation is required.

---

## Gotcha 7: the 7-day weekly cooldown applies even when the prior export expired

**What happens:** An operator misses a download window; the file expires; they request a fresh "Export Now" the next Monday and get blocked because the prior export still occupies the 7-day cooldown slot. UNVERIFIED (2026-09-05): the cooldown and its behaviour after an expired file are help-only.

**When it occurs:** Any time recovery from a missed download is attempted before the cooldown elapses.

**How to avoid:** Plan for the missed-export case in the runbook — the recovery is to either wait for the next eligible window or fall back to Bulk API for the urgent slice of data. Don't promise stakeholders a same-week recovery from a missed download.

---

## Gotcha 8: monthly cadence on Pro/Essentials cannot be promoted to weekly without an edition upgrade

**What happens:** A team on Professional Edition asks to "switch to weekly" after a compliance review and discovers the cadence is edition-gated. UNVERIFIED (2026-09-05): edition-to-cadence eligibility is help-only.

**When it occurs:** When edition was selected without considering data-export cadence as a procurement input.

**How to avoid:** Surface edition-cadence eligibility in the runbook AND in any "we have backups" claim. If weekly is required and the org is on Pro/Essentials, the path is licensing (edition upgrade or Backup and Restore add-on), not configuration.

---

## Gotcha 9: an incremental export watermarked on `LastModifiedDate` silently drops trigger-driven changes

**What happens:** A monthly delta job filters on `LastModifiedDate >= <last run>`. Rows changed by roll-up summaries, standard-functionality triggers and other automated processes never appear in any delta file, and never appear in the full file either, because the full file was retired the moment the delta job "worked."

**When it occurs:** Any org where records are mutated by platform automation rather than by a human clicking Save — which is every org past year one. The two fields diverge quietly: `LastModifiedDate` is "date and time when a user last modified this record" (object_reference.txt:2530–2531), while `SystemModstamp` is "date and time when a user **or automated process (such as a trigger)** last modified this record. In this context, 'trigger' refers to Salesforce code that runs to implement standard functionality, and not an Apex trigger" (object_reference.txt:2533–2540).

**How to avoid:** Watermark on `SystemModstamp`, always, and encode that as a rule the checker enforces rather than a convention. Then know the residual hole: the guide's own caveat is that `SystemModstamp` "doesn't capture every field change. For example, if object A retrieves values from object B, then the changes to field values in records on object B are reflected in the `SystemModstamp` field for records on object B, but not on object A" (object_reference.txt:2540–2548) — cross-object derived values still need a full refresh on some cadence. Note also that `systemModstamp` is the one audit field you can never set on import (object_reference.txt:2556–2563), so it cannot be forged during a restore drill.

---

## Gotcha 10: adding `ORDER BY` or `LIMIT` to a Bulk API 2.0 export query turns off PK chunking

**What happens:** An operator adds `ORDER BY CreatedDate` to make the CSV tidy, or `LIMIT 5000000` as a safety valve. The job that ran in eight minutes yesterday now runs for an hour or times out. Nothing in the request is rejected and no warning is returned — the job simply loses its parallelism.

**When it occurs:** Whenever someone tidies or "bounds" a working export query. Bulk API 2.0 "is optimized to chunk large query jobs if the object being queried supports chunking" (api_asynch.txt:2880–2886), but "LIMIT and ORDER BY disable PKChunking for SOQL queries. With PKChunking disabled, queries take longer to execute, and potentially result in query timeouts" (api_asynch.txt:2888–2891).

**How to avoid:** Never sort or cap in the export query — sort downstream, where it is free. Bound the job with a `WHERE` clause on an indexed field instead. Confirm the object is chunkable by reading `isPkChunkingSupported` in the Get Information About a Query Job response (api_asynch.txt:1138, 2883–2884) before assuming an export is parallel at all.

---

## Gotcha 11: the incremental window widens until the `SystemModstamp` index stops being used

**What happens:** A delta export starts as `SystemModstamp >= <last successful run>` with no upper bound. Runs are missed, the gap grows, and one week the query that always took two minutes goes to full-scan and times out. The filter is on an indexed field the whole time, so no one looks at the index.

**When it occurs:** On large objects, once the widening window crosses the optimizer's selectivity threshold. `SystemModstamp` carries a standard index (ldv.txt:309, ldv.txt:404), and a standard index is used only "if the filter matches less than 30% of the first million records and less than 15% of additional records" (ldv.txt:462–465). Crossing that line is a cliff, not a slope.

**How to avoid:** Bound both ends of every incremental window — `>= start AND < end` — and re-run a missed window as its own job rather than merging it into the next one. When a backlog genuinely must be caught up in one pass, treat it as a full export with chunking, not as a very wide delta.

---

## Gotcha 12: SOQL that works in the Developer Console fails in a Data Loader export

**What happens:** An export SOQL is drafted and tested in the Developer Console, pasted into `sfdc.extractionSOQL`, and the batch job errors — or worse, the operator strips the offending field and ships a CSV missing a column nobody notices for a quarter.

**When it occurs:** Data Loader's extract path is narrower than the platform's query engine in four documented ways (salesforce_data_loader.txt:895–920). It "doesn't support nested queries or querying child objects" (:897), so no `(SELECT … FROM OpportunityLineItems)`. It "doesn't support queries that use polymorphic relationships" — the guide's own failing example is `SELECT Id, Owner.Name, Owner.Type, Owner.Id, Subject FROM Case` (:904–906). Compound fields "cause error messages. To export values, use individual field components" (:918–920). And "the fully specified field names are case-sensitive. For example, using `ACCOUNT.NAME` instead of `Account.Name` does not work" (:895–896).

**How to avoid:** Test export SOQL through the tool that will run it, not through the Console. Decompose compound fields into components (`BillingStreet`, `BillingCity`, … rather than `BillingAddress`) in the inventory's `soql` field. Where a child collection is genuinely needed, run it as a second job keyed on the parent Ids and join downstream.

---

## Gotcha 13: a full-org Bulk API export can exhaust a 24-hour ceiling most teams have never read

**What happens:** A "replace the UI export with Bulk API" migration fans out one query job per object across 200+ objects, runs nightly, and starts failing partway through a month later as data grows — with no single job at fault.

**When it occurs:** Two rolling-window ceilings apply to Bulk API 2.0 query jobs and neither is the familiar batch allocation. "In Bulk API 2.0, only ingest jobs consume batches. Query jobs don't" (salesforce_app_limits_cheatsheet.txt:740–741), so the 15,000-batches-per-rolling-24-hours allocation (:737) is a red herring here. What binds instead is 10,000 query jobs per 24-hour rolling window and 1 TB of total query results per 24-hour rolling window (:921–932). A 200-object nightly export that also serves ad-hoc pulls and a BI replication job shares both ceilings across all three consumers.

**How to avoid:** Read the live figures rather than guessing: both are exposed in the `/vXX.X/limits/` REST response as `DailyBulkV2QueryJobs` and `DailyBulkV2QueryFileStorageMB` (:923–932). Stagger the export across the window, and treat the 1 TB figure as the reason to exclude binary bodies from the structured export rather than as a target to fill.

---

## Gotcha 14: the delete-log reconciliation you built to prove nothing was missed has a 15-day floor and errors rather than truncates

**What happens:** A quarterly audit tries to prove the archive captured every deletion by calling `sObject Get Deleted` for the quarter. The call returns `EXCEEDED_ID_LIMIT` — not a partial list — or returns a window that silently starts later than the one requested.

**When it occurs:** The delete log is not an archive. "A background process that runs every two hours purges records that have been in an organization's delete log for more than two hours if the number of records is above a certain limit… Starting with the oldest records, the process purges delete log entries until the delete log is back below the limit" (api_rest.txt:8335–8344). On top of that, "results are returned for no more than 15 days previous to the day the call is executed (or earlier if an administrator has purged the Recycle Bin)" and "there is a limit of 600,000 IDs returned from this resource. If more than 600,000 IDs are found, `EXCEEDED_ID_LIMIT` is returned" (api_rest.txt:8346–8349).

**How to avoid:** Read `earliestDateAvailable` out of every response and compare it to the window you asked for (api_rest.txt:3532–3533) — that field, not the request, tells you what was actually covered. Run the reconciliation on a cadence well inside the 15-day floor, split wide ranges into narrower start/end pairs before they can hit the ID cap, and capture deletions in the export itself via `queryAll` plus `IsDeleted` (api_asynch.txt:2959–2961) rather than relying on the log to reconstruct them later.
