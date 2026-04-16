# LLM Anti-Patterns — ETL vs API Data Patterns

Common mistakes AI coding assistants make when generating or advising on ETL vs API integration selection.

---

## Anti-Pattern 1: Conflating One-Time Migration with Ongoing ETL Pipeline

**What the LLM generates:** "Use Data Loader or SFDMU for your ongoing daily sync pipeline."

**Why it happens:** LLMs suggest familiar Salesforce data tools without distinguishing migration tools from pipeline tools.

**The correct pattern:** Data Loader and SFDMU are appropriate for one-time or infrequent migrations. Ongoing ETL pipelines require tools with scheduling, error retry, lineage, and change detection — Informatica Cloud, MuleSoft Batch, or similar platforms.

**Detection hint:** Any recommendation of Data Loader or SFDMU for a recurring ongoing pipeline is likely incorrect.

---

## Anti-Pattern 2: Recommending ETL for Real-Time Scenarios

**What the LLM generates:** "Schedule your ETL job to run every 5 minutes for near-real-time sync."

**Why it happens:** LLMs attempt to satisfy a latency requirement by reducing batch interval, without recognizing the architectural mismatch.

**The correct pattern:** If the latency requirement is < 5 minutes for individual record changes, event-driven API integration (MuleSoft, direct REST API with webhooks) is required. ETL batch processing has inherent overhead regardless of scheduling frequency.

**Detection hint:** If the use case requires sub-minute latency and the response suggests ETL with short intervals, the approach is architecturally inappropriate.

---

## Anti-Pattern 3: Using REST API sObjects Endpoint for Bulk ETL

**What the LLM generates:** Code that calls `POST /services/data/vXX.0/sobjects/Account` for each record in a bulk ETL pipeline.

**Why it happens:** LLMs generate the most familiar REST API pattern without considering the volume implications.

**The correct pattern:** Bulk ETL operations must use Bulk API 2.0. Using the REST API CRUD endpoint for bulk loads consumes one API call per record, rapidly exhausting the daily limit.

**Detection hint:** Any bulk ETL code using standard CRUD REST endpoints (not Bulk API 2.0 jobs) for more than 200 records is architecturally incorrect.

---

## Anti-Pattern 4: Presenting Informatica and MuleSoft as Competing Alternatives for Every Use Case

**What the LLM generates:** "You can use either MuleSoft or Informatica for this integration — choose based on your existing licenses."

**Why it happens:** LLMs present tools as interchangeable when the official Salesforce Architects framework treats them as complementary tools for different integration types.

**The correct pattern:** The selection axis is application integration (MuleSoft) vs. data integration (Informatica). Real-time API connectivity → MuleSoft. Bulk ETL with data quality and lineage → Informatica. The decision is driven by the integration type, not purely by existing licenses.

**Detection hint:** Any recommendation that treats Informatica and MuleSoft as interchangeable for any use case is ignoring the official Salesforce Architects complementary-tool framing.

---

## Anti-Pattern 5: Jitterbit Selection Criteria From Training Memory

**What the LLM generates:** Specific Jitterbit selection criteria or comparisons without citing official Salesforce sources.

**Why it happens:** LLMs generate plausible-sounding tool comparisons from training data.

**The correct pattern:** Only Informatica and MuleSoft have formal treatment in official Salesforce Architects documentation (architect.salesforce.com). Jitterbit selection criteria should be sourced from vendor documentation, not from Salesforce official sources.

**Detection hint:** Any Jitterbit-specific selection criteria presented as Salesforce Architects guidance should be verified against official sources.
