# Gotchas — Salesforce Data Export Service

Non-obvious platform behaviors that cause real production problems.

## Gotcha 1: the 48-hour expiration window is rigid

**What happens:** The download links in the notification email expire 48 hours after the export ZIPs are generated. After that, the files are deleted from Salesforce-managed storage and the next manual export cannot be requested until the next 7-day eligibility window opens.

**When it occurs:** Any time the operator misses the email (vacation, holiday, weekend rollover, Friday-evening completion, mis-filtered email rule).

**How to avoid:** Treat each export as a delivery, not a store. Notify a distribution list with rotation/redundancy. Set the schedule so generation completes during business hours. Build monitoring on the notification email (e.g., a transport rule that alerts an ops channel if no download has been recorded within 24 hours).

---

## Gotcha 2: Big Objects are silently skipped

**What happens:** The export completes successfully, the email reports no error, but Big Object data is absent from the ZIP set. There is no warning surfaced to the admin.

**When it occurs:** Any org that uses Big Objects for archival or telemetry storage and assumed the weekly/monthly export covers them.

**How to avoid:** Inventory Big Objects (`SELECT QualifiedApiName FROM EntityDefinition WHERE IsCustomizable = TRUE AND ...` filter or look at Setup → Big Objects). Document the gap in the runbook. Cover Big Objects via Async SOQL → Bulk API CSV pipeline, or by treating Big Object data as immutable telemetry that's re-derivable from upstream.

---

## Gotcha 3: encrypted (Shield) field values export in clear

**What happens:** Fields encrypted via Shield Platform Encryption appear in the CSVs as plaintext for any user whose FLS allows read on those fields. The encryption is at-rest and in-flight inside Salesforce; the export is a read operation, so it decrypts.

**When it occurs:** Any org with Shield Platform Encryption that exports to a destination less protected than the encrypted source — local laptops, unencrypted shared drives, generic S3 buckets without object encryption.

**How to avoid:** The export ZIPs must land on storage with at-rest encryption equal-or-greater than Shield's controls. S3 with SSE-KMS, Azure Blob with CMK, on-prem with FDE. Treat the ZIP as in-scope for the same compliance framework that drove the Shield purchase. Record the destination encryption posture in the runbook.

---

## Gotcha 4: file-content checkboxes inflate generation by orders of magnitude

**What happens:** A 5-million-row Account/Contact/Opportunity org with 100 GB of Salesforce Files goes from a 20-minute export to a 4–8-hour export when "Include Salesforce Files" is checked. The ZIP set balloons from 1 GB to 80–100 GB.

**When it occurs:** When the export's purpose is structured-data evidence and the operator reflexively checks all boxes "to be safe."

**How to avoid:** Default file-content checkboxes to OFF. Include binary content only when the consumer explicitly needs it (legal evidence of attached PDFs, full BI replication including ContentVersion). For evidence archive of structured records, files are out of scope and belong on a separate cadence with separate tooling.

---

## Gotcha 5: schema drift breaks downstream consumers

**What happens:** A custom field is added in March; the April export includes it; an automated S3-to-Snowflake loader fails because the CSV column count no longer matches the staged schema.

**When it occurs:** Any org with active customization plus a downstream automated consumer that pinned to a fixed schema.

**How to avoid:** Loaders downstream of Data Export must be schema-tolerant — either dynamically diff column lists per file or version-pin the loader to a known-good export schema and update the schema as part of the change-management process when fields are added.

---

## Gotcha 6: there is no API to start, monitor, or download exports

**What happens:** Teams that try to fully automate the runbook discover the service is UI-only — no SOAP, REST, or CLI to start an export or fetch the link.

**When it occurs:** When CI/CD or operations teams treat Data Export the way they treat Bulk API or Metadata API (programmable). It is not.

**How to avoid:** Don't promise full automation. The runbook should accept that human operators are part of the loop — the value-add is monitoring, alerting, and post-download archival, not click-elimination. Bulk API is the answer when full automation is required.

---

## Gotcha 7: the 7-day weekly cooldown applies even when the prior export expired

**What happens:** An operator misses a download window; the file expires; they request a fresh "Export Now" the next Monday and get blocked because the prior export still occupies the 7-day cooldown slot.

**When it occurs:** Any time recovery from a missed download is attempted before the cooldown elapses.

**How to avoid:** Plan for the missed-export case in the runbook — the recovery is to either wait for the next eligible window or fall back to Bulk API for the urgent slice of data. Don't promise stakeholders a same-week recovery from a missed download.

---

## Gotcha 8: monthly cadence on Pro/Essentials cannot be promoted to weekly without an edition upgrade

**What happens:** A team on Professional Edition asks to "switch to weekly" after a compliance review and discovers the cadence is edition-gated.

**When it occurs:** When edition was selected without considering data-export cadence as a procurement input.

**How to avoid:** Surface edition-cadence eligibility in the runbook AND in any "we have backups" claim. If weekly is required and the org is on Pro/Essentials, the path is licensing (edition upgrade or Backup and Restore add-on), not configuration.
