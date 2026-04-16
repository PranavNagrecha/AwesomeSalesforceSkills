# LLM Anti-Patterns — Sandbox Refresh Data Strategies

Common mistakes AI coding assistants make when generating sandbox data strategies and post-copy scripts.

---

## Anti-Pattern 1: Implementing Large DML Directly in SandboxPostCopy runApexClass

**What the LLM generates:** A `SandboxPostCopy` implementation that inserts thousands of records in a for-loop directly inside `runApexClass()`.

**Why it happens:** LLMs generate straightforward Apex patterns without checking the execution context constraints of `SandboxPostCopy`.

**The correct pattern:** `runApexClass()` runs synchronously as the Automated Process user with standard governor limits. Large DML must be delegated to a Queueable chain. The `runApexClass()` method should only enqueue the first Queueable job; each Queueable handles one batch and chains to the next.

**Detection hint:** Any `SandboxPostCopy` implementation with a DML loop that inserts more than a few hundred records directly in `runApexClass()` will fail governor limits on production sandbox sizes.

---

## Anti-Pattern 2: Recommending Production Data Copy to Developer Sandboxes for Testing

**What the LLM generates:** "Copy your production data to the Developer sandbox so developers can test with realistic data."

**Why it happens:** LLMs suggest production data for realism without distinguishing sandbox copy types or noting PII implications.

**The correct pattern:** Developer sandboxes contain only metadata — they cannot receive a production data copy. Even for Partial sandboxes where production data copy is possible, PII must be anonymized. Use synthetic data generation (Data Seeding, Faker libraries) for Developer sandboxes.

**Detection hint:** Any recommendation to put production data into a Developer or Developer Pro sandbox is impossible by platform design and ignores PII concerns.

---

## Anti-Pattern 3: Using Data Seeding for Big Objects or Files

**What the LLM generates:** "Add ContentDocument as a child node in your Data Seeding template to auto-generate file attachments."

**Why it happens:** LLMs apply Data Seeding as a universal sandbox population tool without knowing its object exclusions.

**The correct pattern:** Native Data Seeding does not support Big Objects, Files (ContentDocument/ContentVersion), Chatter content, external objects, or AgentWork. These object types require a separate data load mechanism (SFDMU, Data Loader, or custom Apex).

**Detection hint:** Any Data Seeding template design that includes ContentDocument or a Big Object is using an unsupported object type and will fail or produce no records.

---

## Anti-Pattern 4: Treating All Sandbox Data the Same Category

**What the LLM generates:** "Export all your production data, anonymize it, and load it into the sandbox after each refresh."

**Why it happens:** LLMs apply a single bulk export/import pattern without recognizing that different data types have different refresh frequency needs and sourcing methods.

**The correct pattern:** Classify sandbox data into (1) reference data (static lookup tables — automate via SandboxPostCopy), (2) scenario data (synthetic test records — use Data Seeding or scripts), and (3) live-like data (production subset — use Partial sandbox). This reduces post-refresh manual effort dramatically.

**Detection hint:** Any sandbox data strategy that treats all object types with the same export/import mechanism is likely inefficient and brittle.

---

## Anti-Pattern 5: Assuming SandboxPostCopy Script Failure Blocks Sandbox Access

**What the LLM generates:** "If your SandboxPostCopy script fails, the sandbox won't be accessible until the script is fixed and the refresh is rerun."

**Why it happens:** LLMs assume a post-refresh script failure is a blocking error similar to a deployment failure.

**The correct pattern:** A SandboxPostCopy script failure does NOT prevent sandbox access. The sandbox is fully provisioned and accessible. The failure is logged in the sandbox refresh history and optionally emailed to the org admin. The sandbox is in a partial data state but is not locked.

**Detection hint:** Any response suggesting a SandboxPostCopy failure blocks sandbox availability is incorrect. Diagnose script failures separately from sandbox availability.

---

## Anti-Pattern 6: Omitting PII Masking Step for Partial Sandbox Data

**What the LLM generates:** "Use a Partial sandbox to copy 10,000 Account records from production for testing. Developers will have realistic customer data."

**Why it happens:** LLMs optimize for testing realism without accounting for data privacy regulations.

**The correct pattern:** Partial sandbox copies include real production data, which may contain PII (customer names, emails, phone numbers, financial data). Before QA/dev personnel access the sandbox, PII must be masked using Salesforce Data Mask, Shield Platform Encryption in place, or an external anonymization step. Check applicable data privacy regulations (GDPR, CCPA) for your org.

**Detection hint:** Any sandbox strategy that puts production customer data into a non-Full sandbox without a PII masking step is a data privacy risk.
