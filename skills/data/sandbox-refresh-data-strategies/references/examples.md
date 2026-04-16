# Examples — Sandbox Refresh Data Strategies

## Example 1: SandboxPostCopy Governor Limit Failure on Large Reference Data Load

**Scenario:** A team implements `SandboxPostCopy` to auto-populate 50,000 reference data records (price lists, territory hierarchies) after every sandbox refresh. The implementation performs DML in a loop directly in the `runApexClass()` method. The sandbox refresh completes but the post-copy script times out and the sandbox is left with incomplete data.

**Problem:** SandboxPostCopy runs as the `Automated Process` user in a single synchronous Apex execution context. Governor limits apply: 10,000 DML rows per transaction, 30,000 SOQL rows, and a 60-second CPU limit. Attempting to insert 50,000 records in one synchronous call hits these limits.

**Solution:** Restructure the `runApexClass()` method to enqueue a chain of Queueable jobs. The first Queueable loads the first batch (e.g., 5,000 rows), then chains to the next Queueable for the subsequent batch. Each Queueable job runs in its own fresh governor limit context.

**Why it works:** Queueable jobs each receive their own governor limit allocation. Chained Queueables can process arbitrarily large datasets across multiple async transactions. This pattern is explicitly supported for SandboxPostCopy in Salesforce documentation.

---

## Example 2: Using Native Data Seeding to Populate UAT Sandbox

**Scenario:** A retail org wants to give its UAT sandbox realistic Account, Contact, and Order data so testers can run through end-to-end Order Management scenarios without manually creating data.

**Problem:** The team previously relied on a manual SFDMU export/import runbook that took 4+ hours per refresh and was error-prone. After each sandbox refresh, the runbook had to be re-run.

**Solution:** Use the native Data Seeding feature (Setup > Data Seeding). Create a Data Seeding Template by selecting Account (as the root node), Contact and Order as child levels, and set the generation count to 500 Accounts. Generate the template, review the preview, and click Apply to run the seeding job.

**Why it works:** Data Seeding is a native Salesforce feature that generates synthetic relational data respecting your org's schema, validation rules, and required fields. It runs post-refresh automatically if the template is associated with the sandbox definition. It eliminates the manual SFDMU runbook.

---

## Example 3: Classifying Data by Refresh Category to Minimize Post-Refresh Effort

**Scenario:** A financial services org has a 50-table data model. After every sandbox refresh, the QA team spends two days loading data before testing can start. They want to reduce this to under 2 hours.

**Problem:** All data is treated identically: export from production, anonymize PII, load to sandbox. This does not distinguish between data that rarely changes (reference data), data that changes monthly (customer segments), and data that should not come from production at all (synthetic test records).

**Solution:** Classify data into three categories: (1) Reference data — load once via SandboxPostCopy Queueable; (2) Scenario data — generate synthetically using Data Seeding templates; (3) Live-like data — use Partial sandbox copy for a production data subset. Each category has its own load mechanism and only reference data needs a full post-refresh reload every time.

**Why it works:** The three-category model is the standard sandbox data strategy pattern from Salesforce Architects guidance. It reduces the post-refresh manual effort to loading only the small reference data layer (which SandboxPostCopy automates anyway), cutting manual effort dramatically.
