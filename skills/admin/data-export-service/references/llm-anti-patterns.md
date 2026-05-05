# LLM Anti-Patterns — Salesforce Data Export Service

Common mistakes AI assistants make when advising on Data Export Service. Each pattern lists what the LLM produces, why, the correct framing, and how to spot it.

## Anti-Pattern 1: equating Data Export Service with "backup"

**What the LLM generates:** "Salesforce provides backup via the Data Export Service. Schedule a weekly export under Setup → Data Export to satisfy your backup requirements."

**Why it happens:** The Setup page literally has the word "Export" and the help docs call it "Export Backup Data." Training data conflates "export" with "backup" without disambiguating restore semantics.

**Correct pattern:** Distinguish *export* (snapshot delivery) from *backup* (managed product with restore). State explicitly: "Data Export Service produces a CSV snapshot but has no restore path. For a regulated backup obligation, license Salesforce Backup and Restore or a third-party tool. Data Export can serve as evidence archive only."

**Detection hint:** any mention of Data Export with the word "backup" that does not also mention "no restore," "evidence archive only," or "Salesforce Backup and Restore (separate paid product)."

---

## Anti-Pattern 2: claiming a programmatic / API trigger for Data Export

**What the LLM generates:** "Use the Salesforce CLI / REST API to trigger a Data Export and fetch the resulting ZIP."

**Why it happens:** LLMs over-generalize from Bulk API and Metadata API to assume every Setup feature has an API. Data Export Service does not.

**Correct pattern:** Data Export is UI-only — there is no SOAP, REST, CLI, Tooling API, or Metadata API endpoint to start it or fetch its output. For programmatic extracts, use Bulk API 2.0.

**Detection hint:** any code snippet that imports a "DataExport" client, calls a `/services/data/.../dataExports/` URL, or claims `sf data export run`. None of these exist.

---

## Anti-Pattern 3: omitting the 48-hour expiry warning

**What the LLM generates:** "Schedule the export and download the ZIP set when convenient."

**Why it happens:** Help docs mention 48 hours in passing; LLMs lose the constraint when summarizing.

**Correct pattern:** Always surface the 48-hour download window when describing the runbook. The export ZIPs are deleted 48 hours after generation; missed downloads cannot be recovered until the next 7-day eligibility window.

**Detection hint:** any answer about scheduling or operating Data Export that does not mention 48 hours.

---

## Anti-Pattern 4: assuming "Include all data" includes Big Objects, External Objects, and metadata

**What the LLM generates:** "Check 'Include all data' to capture every object including Big Objects."

**Why it happens:** "All" is a strong word in training data. The actual scope of "all" in Data Export is "all standard and custom sObjects accessible via SOQL except Big Objects and External Objects, plus optional binary content; never metadata."

**Correct pattern:** Be explicit about exclusions: Big Objects (skipped), External Objects via Salesforce Connect (skipped), metadata (use Metadata API / Git), Recycle Bin records past their retention window (gone), Chatter feed history (limited).

**Detection hint:** any answer claiming Data Export captures "everything" or "the entire org."

---

## Anti-Pattern 5: defaulting binary-content checkboxes to ON

**What the LLM generates:** "Configure the export to include images, documents, attachments, Salesforce Files, and Chatter Files."

**Why it happens:** Maximalist defaults read as "thorough" in training data. The operational and security cost of binary inclusion is not in most documentation excerpts.

**Correct pattern:** Default binary checkboxes to OFF. Include only when the specific consumer (legal discovery, full BI replication) has named the requirement. Binary inclusion turns a 20-minute job into multi-hour multi-gigabyte work and amplifies destination-encryption obligations.

**Detection hint:** any answer that recommends checking all binary boxes without naming a specific consumer requirement that justifies them.

---

## Anti-Pattern 6: treating Field Audit Trail or Recycle Bin as substitutable for Data Export

**What the LLM generates:** "If you need to recover a deleted record, use the Recycle Bin or Field Audit Trail."

**Why it happens:** These features exist and look adjacent. They are not — Recycle Bin retains for 15 days; Field Audit Trail is a Shield-licensed feature for *field-level history*, not record bodies; Data Export is for snapshot delivery.

**Correct pattern:** Match feature to obligation. Recycle Bin for short-window oops; Field Audit Trail for long-retention field-history compliance (Shield required); Salesforce Backup and Restore for record-level restore; Data Export for evidence archive. None substitute for the others.

**Detection hint:** any answer that conflates "data recovery" with one of these features without naming the others' scopes.
