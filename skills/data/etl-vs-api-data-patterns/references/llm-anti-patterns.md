# LLM Anti-Patterns: ETL vs API Data Patterns

Common mistakes AI coding assistants make when advising on ETL vs API integration for Salesforce.

---

## Anti-Pattern 1: Conflating one-time migration with an ongoing ETL pipeline

**What the LLM generates:** "Use Data Loader or SFDMU for your ongoing daily sync pipeline."

**Why it happens:** The model suggests familiar Salesforce data tools without separating migration from steady state.

**The correct pattern:** Ongoing pipelines need scheduling, a control table, restart values, error tables, and change detection. Data Loader and SFDMU fit one-time or occasional moves.

**Detection hint:** Data Loader or SFDMU named as the engine for a recurring pipeline.

---

## Anti-Pattern 2: Meeting a real-time requirement with a shorter batch interval

**What the LLM generates:** "Schedule your ETL job every 5 minutes for near-real-time sync."

**Why it happens:** The model tunes the schedule instead of changing the pattern.

**The correct pattern:** Per-record latency calls for Remote Call-In, Platform Events, or Change Data Capture. Integration Patterns says timeliness is not the goal of Batch Data Synchronization.

**Detection hint:** A sub-minute requirement answered with an ETL schedule.

---

## Anti-Pattern 3: Single-record REST calls for volume

**What the LLM generates:** A loop that calls `POST /services/data/vXX.0/sobjects/Account` for each row.

**Why it happens:** It is the most common REST example in training data.

**The correct pattern:** Under 2,000 records, batch into sObject Collections (up to 200 records per call) or Composite. Above 2,000, use a Bulk API 2.0 job.

**Detection hint:** `/sobjects/<Object>` inside a loop over thousands of rows.

---

## Anti-Pattern 4: Inventing Bulk API 2.0 limits from Bulk API (1.0)

**What the LLM generates:** "Set the batch size to 10,000 records" or "request JSON results from the Bulk API 2.0 query job."

**Why it happens:** The model blends the two Bulk APIs.

**The correct pattern:** Bulk API 2.0 creates batches for you (one per 10,000 records) and accepts only CSV for ingest and query. The client-side limit is 150 MB per job upload.

**Detection hint:** A batch-size setting or a JSON `contentType` on a `/jobs/ingest` or `/jobs/query` request.

---

## Anti-Pattern 5: Claiming Bulk API 2.0 does not use API requests

**What the LLM generates:** "Bulk API 2.0 has its own budget, so it won't touch your daily API limit."

**Why it happens:** The 150,000,000-record ceiling looks like a separate allocation.

**The correct pattern:** Bulk API 2.0 calls count toward the org's API request allocation. Plan polling and result calls.

**Detection hint:** Any statement that Bulk calls are exempt from the API request allocation.

---

## Anti-Pattern 6: Treating MuleSoft and Informatica as interchangeable

**What the LLM generates:** "Use either MuleSoft or Informatica; pick whichever you already license."

**Why it happens:** The model sees two integration platforms and flattens the distinction.

**The correct pattern:** The Salesforce Architects "Better Together" page assigns real-time application connectivity to MuleSoft and large-scale ETL, data quality, lineage, and MDM to Informatica. The requirement picks the platform; complex architectures can use both.

**Detection hint:** A platform choice with no mention of latency, governance, or MDM.

---

## Anti-Pattern 7: Upserting without an External ID or a parent sort

**What the LLM generates:** A Bulk API 2.0 upsert job with no `externalIdFieldName`, or a child load in source order.

**Why it happens:** The model writes the happy-path call and skips the data design.

**The correct pattern:** Upsert requires `externalIdFieldName`, and the field must exist on the object and in the CSV. Sort child rows by parent key because Bulk API 2.0 runs batches in parallel only.

**Detection hint:** `"operation": "upsert"` without `externalIdFieldName`, or no sort step before a child load.

---

## Anti-Pattern 8: Presenting vendor-tool criteria as Salesforce guidance

**What the LLM generates:** Specific Jitterbit or Informatica feature claims presented as Salesforce Architects guidance.

**Why it happens:** The model mixes vendor marketing into platform guidance.

**The correct pattern:** Cite Salesforce sources for Salesforce behavior and vendor documentation for vendor features. Mark vendor claims that were not checked.

**Detection hint:** A tool feature claim with no source, attributed to Salesforce.
